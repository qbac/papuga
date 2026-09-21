"""
Globalne skróty klawiszowe działające w całym systemie (niezależnie od
tego, która aplikacja jest aktywna), oparte o pynput.GlobalHotKeys.
"""
from __future__ import annotations

import logging
from typing import Callable

from pynput import keyboard

logger = logging.getLogger("papuga.hotkey")


class HotkeyManager:
    def __init__(self) -> None:
        self._listener: keyboard.GlobalHotKeys | None = None

    def start(self, bindings: dict[str, Callable[[], None]]) -> None:
        """bindings: mapa {"<ctrl>+<alt>+r": callback, ...}"""
        self.stop()
        try:
            self._listener = keyboard.GlobalHotKeys(bindings)
            self._listener.start()
        except Exception:
            logger.exception("Nie udało się zarejestrować skrótów klawiszowych")
            raise

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def restart(self, bindings: dict[str, Callable[[], None]]) -> None:
        self.start(bindings)


_MODIFIERS = {
    keyboard.Key.ctrl: "ctrl", keyboard.Key.ctrl_l: "ctrl", keyboard.Key.ctrl_r: "ctrl",
    keyboard.Key.alt: "alt", keyboard.Key.alt_l: "alt", keyboard.Key.alt_r: "alt",
    keyboard.Key.alt_gr: "alt",
    keyboard.Key.shift: "shift", keyboard.Key.shift_l: "shift", keyboard.Key.shift_r: "shift",
    keyboard.Key.cmd: "cmd", keyboard.Key.cmd_l: "cmd", keyboard.Key.cmd_r: "cmd",  # cmd = klawisz Windows
}
_MODIFIER_ORDER = ("ctrl", "alt", "shift", "cmd")


def _key_token(key) -> str | None:
    """Zamienia naciśnięty klawisz (nie-modyfikator) na token formatu pynput."""
    if isinstance(key, keyboard.Key):
        return f"<{key.name}>"
    vk = getattr(key, "vk", None)
    if vk and (0x41 <= vk <= 0x5A):
        return chr(vk).lower()
    if vk and (0x30 <= vk <= 0x39):
        return chr(vk)
    char = getattr(key, "char", None)
    if char and char.isprintable():
        return char.lower()
    if vk:
        return f"<{vk}>"
    return None


def prettify(hotkey: str) -> str:
    """'<ctrl>+<cmd>+r' -> 'Ctrl + Win + R'."""
    names = {"<ctrl>": "Ctrl", "<alt>": "Alt", "<shift>": "Shift", "<cmd>": "Win"}
    parts = []
    for token in hotkey.split("+"):
        token = token.strip()
        if token in names:
            parts.append(names[token])
        else:
            parts.append(token.strip("<>").upper() if len(token.strip("<>")) > 1 else token.upper())
    return " + ".join(parts)


class HotkeyCapture:
    """Nasłuchuje klawiatury i zamienia wciśnięte klawisze na skrót w formacie pynput,
    np. '<ctrl>+<alt>+r' (z obsługą klawisza Windows jako <cmd>).

    Bezpieczne dla wątku Tk: wywołania zwrotne pynput tylko zapisują stan,
    a UI odczytuje go przez `preview`, `done`, `result`, `cancelled`, `error`."""

    def __init__(self) -> None:
        self._mods: set[str] = set()
        self._listener: keyboard.Listener | None = None
        self.result: str | None = None
        self.cancelled = False
        self.error: str | None = None

    @property
    def done(self) -> bool:
        return self.result is not None or self.cancelled

    @property
    def preview(self) -> str:
        return " + ".join(m.capitalize() if m != "cmd" else "Win" for m in _MODIFIER_ORDER if m in self._mods)

    def start(self) -> None:
        self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _on_press(self, key):
        mod = _MODIFIERS.get(key)
        if mod:
            self._mods.add(mod)
            return None
        token = _key_token(key)
        if token is None:
            return None
        if token == "<esc>" and not self._mods:
            self.cancelled = True
            return False
        if not self._mods and not (token.startswith("<f") and token[2:-1].isdigit()):
            self.error = "Dodaj modyfikator (Ctrl, Alt, Shift lub Win)."
            return None
        self.error = None
        ordered = [f"<{m}>" for m in _MODIFIER_ORDER if m in self._mods]
        self.result = "+".join(ordered + [token])
        return False

    def _on_release(self, key):
        mod = _MODIFIERS.get(key)
        if mod:
            self._mods.discard(mod)
        return None
