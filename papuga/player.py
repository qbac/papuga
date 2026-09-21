"""
Odtwarzanie wygenerowanego audio + możliwość natychmiastowego przerwania.
Oparte o pygame.mixer — działa na Windows/Linux/macOS bez dodatkowych
zależności systemowych.
"""
from __future__ import annotations

import threading

import pygame

_lock = threading.Lock()
_initialized = False


def _ensure_init() -> None:
    global _initialized
    with _lock:
        if not _initialized:
            pygame.mixer.init()
            _initialized = True


def warm_up() -> None:
    """Inicjalizuje mixer z wyprzedzeniem (pierwsze odtwarzanie nie płaci za init)."""
    _ensure_init()


def play(file_path: str, block: bool = True) -> None:
    """Odtwarza plik audio (mp3/wav). Jeśli block=True, czeka do końca
    lub do wywołania stop()."""
    _ensure_init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    if block:
        try:
            clock = pygame.time.Clock()
            while pygame.mixer.music.get_busy():
                clock.tick(20)
        finally:
            # zwolnij uchwyt pliku — inaczej Windows nie pozwoli go usunąć
            pygame.mixer.music.unload()


def stop() -> None:
    if _initialized:
        pygame.mixer.music.stop()


def is_playing() -> bool:
    return _initialized and pygame.mixer.music.get_busy()
