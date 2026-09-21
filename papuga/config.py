"""
Konfiguracja Papugi — wczytywanie/zapis ustawień w pliku JSON
w standardowym katalogu konfiguracyjnym systemu (platformdirs).
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field, asdict
from pathlib import Path

from platformdirs import user_config_dir

from papuga import APP_NAME
from papuga import voices

CONFIG_DIR = Path(user_config_dir(APP_NAME, appauthor=False))
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_HOTKEY_READ = "<ctrl>+<alt>+r"
DEFAULT_HOTKEY_STOP = "<ctrl>+<alt>+s"

DEFAULTS = {
    "engine": "edge",  # "edge" | "piper" | "api"
    "language": "",  # kod języka czytania (np. "pl", "en"); pusty = język systemu
    "ui_language": "auto",  # "auto" | "pl" | "en"
    "recent_languages": [],  # ostatnio używane języki czytania (do szybkiego wyboru w trayu)
    "hotkey_read": DEFAULT_HOTKEY_READ,
    "hotkey_stop": DEFAULT_HOTKEY_STOP,
    "speed": 1.0,  # mnożnik prędkości mowy (0.5 - 2.0)
    "start_with_system": False,
    # Edge TTS (pusty głos = domyślny dla języka)
    "edge_voice": "",
    # Piper (lokalny, offline; pusty głos = domyślny dla języka)
    "piper_voice_id": "",
    # Generyczny silnik API (OpenAI-compatible speech endpoint / ElevenLabs)
    "api_provider": "openai",  # "openai" | "elevenlabs" | "custom"
    "api_base_url": "https://api.openai.com/v1/audio/speech",
    "api_key": "",
    "api_model": "tts-1",
    "api_voice": "alloy",
}

_lock = threading.RLock()  # re-entrant: load() wywołuje save() pod tym samym zamkiem


@dataclass
class Settings:
    engine: str = DEFAULTS["engine"]
    language: str = DEFAULTS["language"]
    ui_language: str = DEFAULTS["ui_language"]
    recent_languages: list = field(default_factory=list)
    hotkey_read: str = DEFAULTS["hotkey_read"]
    hotkey_stop: str = DEFAULTS["hotkey_stop"]
    speed: float = DEFAULTS["speed"]
    start_with_system: bool = DEFAULTS["start_with_system"]
    edge_voice: str = DEFAULTS["edge_voice"]
    piper_voice_id: str = DEFAULTS["piper_voice_id"]
    api_provider: str = DEFAULTS["api_provider"]
    api_base_url: str = DEFAULTS["api_base_url"]
    api_key: str = DEFAULTS["api_key"]
    api_model: str = DEFAULTS["api_model"]
    api_voice: str = DEFAULTS["api_voice"]

    def to_dict(self) -> dict:
        return asdict(self)


def normalize(settings: Settings) -> Settings:
    """Domyka język i głosy: język z systemu (lub z zapisanego głosu), głos musi
    należeć do wybranego języka — inaczej dostaje domyślny dla tego języka."""
    if not voices.is_known_language(settings.language):
        inferred = settings.edge_voice.split("-")[0].lower() if settings.edge_voice else ""
        settings.language = inferred if voices.is_known_language(inferred) else voices.system_language()

    lang = settings.language
    if settings.edge_voice not in {v["id"] for v in voices.edge_voices(lang)}:
        settings.edge_voice = voices.default_edge_voice(lang)
    if settings.piper_voice_id not in {v["id"] for v in voices.piper_voices(lang)}:
        settings.piper_voice_id = voices.default_piper_voice(lang)
    return settings


def load() -> Settings:
    with _lock:
        if not CONFIG_FILE.exists():
            settings = normalize(Settings())
            save(settings)
            return settings
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return normalize(Settings())
        merged = {**DEFAULTS, **data}
        # odfiltruj nieznane klucze, żeby stare configi nie wywalały aplikacji
        known = {f: merged[f] for f in DEFAULTS if f in merged}
        return normalize(Settings(**known))


def save(settings: Settings) -> None:
    with _lock:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(
            json.dumps(settings.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
