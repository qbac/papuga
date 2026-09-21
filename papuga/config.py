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

CONFIG_DIR = Path(user_config_dir(APP_NAME, appauthor=False))
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_HOTKEY_READ = "<ctrl>+<alt>+r"
DEFAULT_HOTKEY_STOP = "<ctrl>+<alt>+s"

DEFAULTS = {
    "engine": "edge",  # "edge" | "piper" | "api"
    "hotkey_read": DEFAULT_HOTKEY_READ,
    "hotkey_stop": DEFAULT_HOTKEY_STOP,
    "speed": 1.0,  # mnożnik prędkości mowy (0.5 - 2.0)
    "start_with_system": False,
    # Edge TTS
    "edge_voice": "pl-PL-MarekNeural",
    # Piper (lokalny, offline)
    "piper_voice_id": "pl_PL-darkman-medium",
    "piper_model_path": "",  # ścieżka do .onnx (uzupełniana po pobraniu głosu)
    "piper_config_path": "",  # ścieżka do .onnx.json
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
    hotkey_read: str = DEFAULTS["hotkey_read"]
    hotkey_stop: str = DEFAULTS["hotkey_stop"]
    speed: float = DEFAULTS["speed"]
    start_with_system: bool = DEFAULTS["start_with_system"]
    edge_voice: str = DEFAULTS["edge_voice"]
    piper_voice_id: str = DEFAULTS["piper_voice_id"]
    piper_model_path: str = DEFAULTS["piper_model_path"]
    piper_config_path: str = DEFAULTS["piper_config_path"]
    api_provider: str = DEFAULTS["api_provider"]
    api_base_url: str = DEFAULTS["api_base_url"]
    api_key: str = DEFAULTS["api_key"]
    api_model: str = DEFAULTS["api_model"]
    api_voice: str = DEFAULTS["api_voice"]

    def to_dict(self) -> dict:
        return asdict(self)


def load() -> Settings:
    with _lock:
        if not CONFIG_FILE.exists():
            settings = Settings()
            save(settings)
            return settings
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return Settings()
        merged = {**DEFAULTS, **data}
        # odfiltruj nieznane klucze, żeby stare configi nie wywalały aplikacji
        known = {f: merged[f] for f in DEFAULTS if f in merged}
        return Settings(**known)


def save(settings: Settings) -> None:
    with _lock:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(
            json.dumps(settings.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
