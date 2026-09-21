"""Autostart Papugi z systemem — jednym wywołaniem włącz/wyłącz.

Windows: wpis w HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run (bez uprawnień administratora).
Linux:   plik ~/.config/autostart/papuga.desktop (XDG; jeszcze nieprzetestowane na żywo).
macOS:   nieobsługiwane (supported() == False).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from papuga import APP_NAME

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def supported() -> bool:
    return sys.platform == "win32" or sys.platform.startswith("linux")


def _command_parts() -> list[str]:
    """Polecenie uruchamiające TĘ instalację: zbudowany plik albo skrypt deweloperski."""
    if getattr(sys, "frozen", False):
        return [sys.executable]
    script = Path(__file__).resolve().parent.parent / "scripts" / "run_dev.py"
    python = Path(sys.executable)
    if sys.platform == "win32":
        pythonw = python.with_name("pythonw.exe")  # bez okna konsoli
        python = pythonw if pythonw.exists() else python
    return [str(python), str(script)]


def _quoted(parts: list[str]) -> str:
    return " ".join(f'"{p}"' for p in parts)


def is_enabled() -> bool:
    if sys.platform == "win32":
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
                winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
    if sys.platform.startswith("linux"):
        return _desktop_file().exists()
    return False


def set_enabled(enabled: bool) -> None:
    """Włącza/wyłącza autostart. Rzuca OSError, jeśli system odmówi."""
    if sys.platform == "win32":
        import winreg

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            if enabled:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _quoted(_command_parts()))
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
        return

    if sys.platform.startswith("linux"):
        path = _desktop_file()
        if enabled:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "[Desktop Entry]\n"
                "Type=Application\n"
                f"Name={APP_NAME}\n"
                f"Exec={_quoted(_command_parts())}\n"
                "Terminal=false\n"
                "X-GNOME-Autostart-enabled=true\n",
                encoding="utf-8",
            )
        else:
            path.unlink(missing_ok=True)
        return

    raise OSError("autostart is not supported on this platform")


def _desktop_file() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "autostart" / f"{APP_NAME.lower()}.desktop"
