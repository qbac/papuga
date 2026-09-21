"""
Pobieranie aktualnie zaznaczonego tekstu w dowolnej aplikacji.

Metoda: symulujemy Ctrl+C (Cmd+C na macOS), czytamy schowek,
a na końcu przywracamy jego poprzednią zawartość, żeby nie
zaśmiecać użytkownikowi historii kopiowania.
"""
from __future__ import annotations

import sys
import time

import pyperclip
from pynput.keyboard import Controller, Key

_keyboard = Controller()

# Krótka przerwa potrzebna, żeby aktywna aplikacja zdążyła
# zareagować na symulowany skrót i zapisać coś do schowka.
_COPY_DELAY = 0.12


def get_selected_text(timeout: float = 1.0) -> str:
    """Zwraca aktualnie zaznaczony tekst albo pusty string, jeśli nic nie zaznaczono."""
    try:
        previous_clipboard = pyperclip.paste()
    except Exception:
        previous_clipboard = ""

    # Wyczyść schowek, żeby wiedzieć, czy Ctrl+C faktycznie coś skopiował
    sentinel = "\u0000__PAPUGA_EMPTY__\u0000"
    try:
        pyperclip.copy(sentinel)
    except Exception:
        pass

    _simulate_copy()

    deadline = time.monotonic() + timeout
    text = ""
    while time.monotonic() < deadline:
        try:
            current = pyperclip.paste()
        except Exception:
            current = ""
        if current and current != sentinel:
            text = current
            break
        time.sleep(0.03)

    # Przywróć to, co było w schowku wcześniej
    try:
        pyperclip.copy(previous_clipboard)
    except Exception:
        pass

    return text.strip()


def _wait_for_hotkey_release(timeout: float = 1.0) -> None:
    """Skrót (np. Ctrl+Alt+R) odpala się, gdy użytkownik jeszcze trzyma klawisze.
    Symulowane Ctrl+C z wciśniętym Altem to Ctrl+Alt+C — aplikacje go nie kopiują.
    Czekamy na puszczenie Alt/Shift/Win/R, a po timeoucie zwalniamy je wirtualnie."""
    if sys.platform != "win32":
        return
    import ctypes

    get_state = ctypes.windll.user32.GetAsyncKeyState
    # Alt, Shift, LWin, RWin, R
    vks = (0x12, 0x10, 0x5B, 0x5C, 0x52)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not any(get_state(vk) & 0x8000 for vk in vks):
            return
        time.sleep(0.02)
    for key in (Key.alt, Key.shift, Key.cmd, "r"):
        try:
            _keyboard.release(key)
        except Exception:
            pass


def _simulate_copy() -> None:
    _wait_for_hotkey_release()
    modifier = Key.cmd if sys.platform == "darwin" else Key.ctrl
    _keyboard.press(modifier)
    _keyboard.press("c")
    time.sleep(0.02)
    _keyboard.release("c")
    _keyboard.release(modifier)
    time.sleep(_COPY_DELAY)
