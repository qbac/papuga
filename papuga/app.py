"""
Rdzeń aplikacji Papuga — spina ze sobą: globalny skrót klawiszowy,
pobranie zaznaczonego tekstu, wybrany silnik TTS, odtwarzanie audio
oraz ikonę w zasobniku systemowym (tray).
"""
from __future__ import annotations

import logging
import queue
import re
import tempfile
import threading
from pathlib import Path

import pystray
from PIL import Image, ImageDraw

from papuga import APP_NAME
from papuga import config as cfg
from papuga import hotkey as hk
from papuga import player
from papuga import selection
from papuga.tts import build_engine, TTSError

logger = logging.getLogger("papuga.app")

TEMP_DIR = Path(tempfile.gettempdir()) / "papuga_audio"

ICON_IDLE = "idle"
ICON_BUSY = "busy"
ICON_ERROR = "error"

# Pierwszy kawałek krótki (szybki start mowy), kolejne dłuższe (mniej przerw).
FIRST_CHUNK_CHARS = 160
NEXT_CHUNK_CHARS = 500


def _remove_quietly(path: Path) -> None:
    """Sprzątanie pliku tymczasowego nie może przerywać czytania."""
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.debug("Nie udało się usunąć %s", path)


def _split_text(text: str, first: int = FIRST_CHUNK_CHARS, rest: int = NEXT_CHUNK_CHARS) -> list[str]:
    """Dzieli tekst na kawałki na granicach zdań/akapitów."""
    sentences: list[str] = []
    for part in re.split(r"(?<=[.!?…])\s+|\n+", text):
        part = part.strip()
        if part:
            sentences.append(part)

    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        limit = first if not chunks else rest
        # zbyt długie zdanie tnij po słowach
        while len(sentence) > limit:
            cut = sentence.rfind(" ", 0, limit)
            cut = cut if cut > 0 else limit
            if current:
                chunks.append(current)
                current = ""
                limit = rest
            chunks.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
            limit = rest
        if not sentence:
            continue
        if current and len(current) + 1 + len(sentence) > limit:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
        # pierwszy kawałek zamykamy od razu, żeby mowa ruszyła jak najszybciej
        if not chunks and current:
            chunks.append(current)
            current = ""
    if current:
        chunks.append(current)
    return chunks


class PapugaApp:
    def __init__(self) -> None:
        self.settings = cfg.load()
        self.hotkeys = hk.HotkeyManager()
        self._busy_lock = threading.Lock()
        self._is_speaking = False
        self._cancel = threading.Event()
        threading.Thread(target=self._warm_up, daemon=True).start()

        self._icons = {
            ICON_IDLE: _make_icon((46, 125, 50)),   # zielony — gotowa
            ICON_BUSY: _make_icon((251, 140, 0)),   # pomarańczowy — czyta
            ICON_ERROR: _make_icon((198, 40, 40)),  # czerwony — błąd
        }

        self.tray: pystray.Icon = pystray.Icon(
            APP_NAME,
            icon=self._icons[ICON_IDLE],
            title=self._tray_title(),
            menu=self._build_menu(),
        )

        self._register_hotkeys()

    # ------------------------------------------------------------------ #
    # Uruchomienie / zamknięcie
    # ------------------------------------------------------------------ #
    def run(self) -> None:
        self.tray.run()

    def quit(self, *_args) -> None:
        self.hotkeys.stop()
        player.stop()
        self.tray.stop()

    # ------------------------------------------------------------------ #
    # Skróty klawiszowe
    # ------------------------------------------------------------------ #
    def _register_hotkeys(self) -> None:
        bindings = {
            self.settings.hotkey_read: self._trigger_read,
            self.settings.hotkey_stop: self._trigger_stop,
        }
        try:
            self.hotkeys.start(bindings)
        except Exception:
            logger.exception("Rejestracja skrótów nie powiodła się")
            self._notify("Papuga", "Nie udało się zarejestrować skrótów klawiszowych.")

    def reload_settings(self) -> None:
        """Wywoływane po zapisaniu ustawień w oknie konfiguracji."""
        self.settings = cfg.load()
        self._register_hotkeys()
        self.tray.title = self._tray_title()

    # ------------------------------------------------------------------ #
    # Czytanie zaznaczenia
    # ------------------------------------------------------------------ #
    def _trigger_read(self) -> None:
        threading.Thread(target=self._read_selection, daemon=True).start()

    def _trigger_stop(self) -> None:
        self._cancel.set()
        player.stop()
        self._set_icon(ICON_IDLE)

    def _warm_up(self) -> None:
        """Rozgrzewka przy starcie, żeby pierwsze czytanie nie płaciło za zimny start."""
        try:
            player.warm_up()
            if self.settings.engine == "edge":
                import edge_tts  # noqa: F401
        except Exception:
            logger.exception("Rozgrzewka nie powiodła się (pomijam)")

    def _read_selection(self) -> None:
        if not self._busy_lock.acquire(blocking=False):
            # Już coś czytamy — drugie wciśnięcie hotkeya traktujemy jako "stop"
            self._trigger_stop()
            return

        try:
            self._cancel.clear()
            self._is_speaking = True
            self._set_icon(ICON_BUSY)

            text = selection.get_selected_text()
            if not text:
                self._notify(APP_NAME, "Nie zaznaczono żadnego tekstu.")
                return

            self._speak(text)

        except TTSError as exc:
            logger.warning("Błąd TTS: %s", exc)
            self._set_icon(ICON_ERROR)
            self._notify(APP_NAME, str(exc))
        except Exception:
            logger.exception("Nieoczekiwany błąd podczas czytania")
            self._set_icon(ICON_ERROR)
            self._notify(APP_NAME, "Wystąpił nieoczekiwany błąd. Sprawdź logi.")
        finally:
            self._is_speaking = False
            self._set_icon(ICON_IDLE)
            self._busy_lock.release()

    def _speak(self, text: str) -> None:
        """Potok: wątek w tle syntezuje kolejne kawałki, a tu odtwarzamy je po kolei,
        więc mowa rusza po wygenerowaniu pierwszego, krótkiego kawałka."""
        engine = build_engine(self.settings)
        speed = self.settings.speed
        ready: queue.Queue = queue.Queue(maxsize=2)

        def put(item) -> bool:
            while not self._cancel.is_set():
                try:
                    ready.put(item, timeout=0.2)
                    return True
                except queue.Full:
                    continue
            return False

        def producer() -> None:
            try:
                for chunk in _split_text(text):
                    if self._cancel.is_set():
                        break
                    path = engine.synthesize(chunk, TEMP_DIR, speed=speed)
                    if not put(path):
                        _remove_quietly(path)
                        break
            except Exception as exc:  # noqa: BLE001
                put(exc)
            finally:
                put(None)

        threading.Thread(target=producer, daemon=True).start()

        while True:
            try:
                item = ready.get(timeout=0.2)
            except queue.Empty:
                if self._cancel.is_set():
                    return
                continue
            if item is None:
                return
            if isinstance(item, Exception):
                raise item
            try:
                if not self._cancel.is_set():
                    player.play(str(item), block=True)
            finally:
                _remove_quietly(item)
            if self._cancel.is_set():
                return

    # ------------------------------------------------------------------ #
    # Tray UI
    # ------------------------------------------------------------------ #
    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(f"Czytaj zaznaczenie  ({self.settings.hotkey_read})", lambda: self._trigger_read()),
            pystray.MenuItem(f"Zatrzymaj  ({self.settings.hotkey_stop})", lambda: self._trigger_stop()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Ustawienia...", self._open_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Zakończ", self.quit),
        )

    def _open_settings(self, *_args) -> None:
        from papuga.ui.settings_window import open_settings_window

        threading.Thread(target=open_settings_window, args=(self,), daemon=True).start()

    def _set_icon(self, state: str) -> None:
        self.tray.icon = self._icons[state]

    def _notify(self, title: str, message: str) -> None:
        try:
            self.tray.notify(message, title)
        except Exception:
            logger.info("%s: %s", title, message)

    def _tray_title(self) -> str:
        engine_names = {"edge": "Edge TTS", "piper": "Piper (offline)", "api": "API"}
        return f"{APP_NAME} — {engine_names.get(self.settings.engine, self.settings.engine)}"


def _make_icon(rgb: tuple[int, int, int]) -> Image.Image:
    """Rysuje prostą, rozpoznawalną ikonkę (kropka/głośnik) na przezroczystym tle."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((4, 4, size - 4, size - 4), fill=rgb)
    # prosty symbol "fali dźwiękowej"
    draw.arc((18, 14, 46, 50), start=300, end=60, fill="white", width=4)
    draw.arc((10, 8, 54, 56), start=300, end=60, fill="white", width=4)
    draw.ellipse((size // 2 - 5, size // 2 - 5, size // 2 + 5, size // 2 + 5), fill="white")
    return img
