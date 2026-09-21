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
        self._lock_path = Path(tempfile.gettempdir()) / f"{name.lower()}.lock"
        self._fh = None

    def acquire(self) -> bool:
        if sys.platform == "win32":
            return self._acquire_windows()
        return self._acquire_posix()

    def _acquire_windows(self) -> bool:
        try:
            # O_CREAT|O_EXCL zawiedzie, jeśli plik już istnieje i jest zablokowany
            if self._lock_path.exists():
                # sprawdź, czy proces z zapisanym PID-em wciąż żyje
                try:
                    pid = int(self._lock_path.read_text().strip())
                    os.kill(pid, 0)
                    return False  # proces żyje
                except (ValueError, OSError, ProcessLookupError):
                    pass  # martwy lock — nadpisz
            self._lock_path.write_text(str(os.getpid()))
            atexit.register(self.release)
            return True
        except OSError:
            return False

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
            if self._fh:
                self._fh.close()
            if self._lock_path.exists():
                self._lock_path.unlink()
        except OSError:
            pass
