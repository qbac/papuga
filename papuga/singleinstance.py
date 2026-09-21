"""
Prosta blokada jednej instancji aplikacji — oparta o plik blokady
w katalogu tymczasowym systemu. Działa na Windows/Linux/macOS.
"""
from __future__ import annotations

import atexit
import os
import sys
import tempfile
from pathlib import Path


class SingleInstance:
    def __init__(self, name: str) -> None:
        self._name = name
        self._lock_path = Path(tempfile.gettempdir()) / f"{name.lower()}.lock"
        self._fh = None
        self._mutex = None

    def acquire(self) -> bool:
        if sys.platform == "win32":
            return self._acquire_windows()
        return self._acquire_posix()

    def _acquire_windows(self) -> bool:
        # Nazwany mutex: system zwalnia go sam, gdy proces ginie (także po awarii
        # czy Stop-Process), więc nie ma nieaktualnych blokad. NIE używać
        # os.kill(pid, 0) — na Windows to kończy proces o tym PID, a nie go sprawdza.
        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
        handle = kernel32.CreateMutexW(None, False, f"Local\\{self._name}_SingleInstance")
        if not handle:
            return True  # nie udało się utworzyć mutexa — lepiej uruchomić niż zablokować
        if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
            kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
            kernel32.CloseHandle(handle)
            return False
        self._mutex = handle  # trzymamy uchwyt do końca życia procesu
        return True

    def _acquire_posix(self) -> bool:
        import fcntl

        self._fh = open(self._lock_path, "w")
        try:
            fcntl.flock(self._fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self._fh.close()
            self._fh = None
            return False
        self._fh.write(str(os.getpid()))
        self._fh.flush()
        atexit.register(self.release)
        return True

    def release(self) -> None:
        try:
            if self._mutex:
                import ctypes

                ctypes.WinDLL("kernel32").CloseHandle(ctypes.c_void_p(self._mutex))
                self._mutex = None
            if self._fh:
                self._fh.close()
                if self._lock_path.exists():
                    self._lock_path.unlink()
        except OSError:
            pass
