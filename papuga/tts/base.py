"""Wspólny interfejs dla wszystkich silników TTS w Papudze."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class TTSError(RuntimeError):
    """Błąd generowania mowy — pokazywany użytkownikowi w powiadomieniu."""


class TTSEngine(ABC):
    """Każdy silnik dostaje tekst i zwraca ścieżkę do pliku audio (mp3/wav),
    który papuga.player odtwarza."""

    name: str = "base"

    @abstractmethod
    def synthesize(self, text: str, out_dir: Path, speed: float = 1.0) -> Path:
        """Generuje mowę z tekstu i zwraca ścieżkę do zapisanego pliku audio."""
        raise NotImplementedError

    def list_voices(self) -> list[str]:
        """Lista dostępnych głosów (opcjonalnie nadpisywana przez podklasy)."""
        return []
