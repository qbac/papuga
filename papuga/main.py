"""Punkt wejścia Papugi — uruchamia ikonę w zasobniku systemowym."""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from platformdirs import user_log_dir

from papuga import APP_NAME
from papuga.singleinstance import SingleInstance


def _fix_tcl_paths() -> None:
    """Python z Laragona trzyma Tcl/Tk w <prefix>\\tcl zamiast <prefix>\\lib — wskaż go tkinterowi."""
    if getattr(sys, "frozen", False):
        return  # PyInstaller sam pakuje i wskazuje Tcl/Tk
    base = Path(sys.base_prefix)
    for var, name in (("TCL_LIBRARY", "tcl8.6"), ("TK_LIBRARY", "tk8.6")):
        if os.environ.get(var):
            continue
        for candidate in (base / "lib" / name, base / "tcl" / name):
            if (candidate / ("init.tcl" if name.startswith("tcl") else "tk.tcl")).exists():
                os.environ[var] = str(candidate)
                break


def _setup_logging() -> None:
    log_dir = Path(user_log_dir(APP_NAME, appauthor=False))
    log_dir.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [
        logging.FileHandler(log_dir / "papuga.log", encoding="utf-8"),
    ]
    if sys.stdout is not None:  # w buildzie z console=False stdout to None
        handlers.append(logging.StreamHandler(sys.stdout))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


def _selftest() -> int:
    """`Papuga.exe --selftest`: sprawdza w zbudowanym pliku to, czego nie widać na starcie
    (Piper offline, Tk/customtkinter, katalog głosów, Edge TTS). Wynik: log + kod wyjścia."""
    import tempfile
    import wave

    log = logging.getLogger("papuga.selftest")
    failures: list[str] = []

    def check(name: str, fn) -> None:
        try:
            log.info("SELFTEST %s: %s", name, fn() or "OK")
        except Exception as exc:  # noqa: BLE001
            log.exception("SELFTEST %s: BŁĄD", name)
            failures.append(f"{name}: {exc}")

    def catalog() -> str:
        from papuga import voices

        return f"{len(voices.language_codes())} języków"

    def piper() -> str:
        from papuga.tts.piper_engine import PiperTTSEngine

        out = Path(tempfile.gettempdir()) / "papuga_selftest"
        wav = PiperTTSEngine("en_US-lessac-low").synthesize("Papuga self test.", out)
        with wave.open(str(wav)) as w:
            seconds = w.getnframes() / w.getframerate()
        wav.unlink(missing_ok=True)
        if seconds < 0.5:
            raise RuntimeError(f"za krótkie audio ({seconds:.2f}s)")
        return f"wygenerowano {seconds:.1f}s audio"

    def edge_import() -> str:
        import edge_tts  # noqa: F401

    def tk_window() -> str:
        import customtkinter as ctk

        root = ctk.CTk()
        root.update()
        root.destroy()

    def settings_window() -> str:
        """Buduje PRAWDZIWE okno ustawień (wszystkie widgety, importy, katalog głosów) i od razu
        je zamyka — wyłapuje braki w zbudowanym pliku, których sam start Tk nie pokaże."""
        import customtkinter as ctk

        from papuga.ui import settings_window as sw

        class _Hotkeys:
            @staticmethod
            def stop() -> None:
                pass

        class _App:
            hotkeys = _Hotkeys()

            def _register_hotkeys(self) -> None:
                pass

            def reload_settings(self) -> None:
                pass

        original = ctk.CTk.mainloop
        ctk.CTk.mainloop = lambda self, *a, **k: (self.update(), self.destroy())
        try:
            sw.open_settings_window(_App())
        finally:
            ctk.CTk.mainloop = original

    def audio_mixer() -> str:
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")  # CI nie ma karty dźwiękowej
        from papuga import player

        player.warm_up()

    for name, fn in (("catalog", catalog), ("piper", piper), ("edge_import", edge_import),
                     ("tk_window", tk_window), ("settings_window", settings_window),
                     ("audio_mixer", audio_mixer)):
        check(name, fn)

    log.info("SELFTEST %s", "PASSED" if not failures else f"FAILED: {failures}")
    return 0 if not failures else 1


def main() -> None:
    _fix_tcl_paths()
    _setup_logging()
    logger = logging.getLogger("papuga.main")

    if "--selftest" in sys.argv:
        sys.exit(_selftest())

    lock = SingleInstance(APP_NAME)
    if not lock.acquire():
        logger.info("Papuga już działa — kończę ten proces.")
        return

    from papuga.app import PapugaApp

    logger.info("Uruchamiam Papugę...")
    app = PapugaApp()
    try:
        app.run()
    finally:
        lock.release()


if __name__ == "__main__":
    main()
