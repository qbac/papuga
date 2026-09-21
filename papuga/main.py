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


def main() -> None:
    _fix_tcl_paths()
    _setup_logging()
    logger = logging.getLogger("papuga.main")

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
