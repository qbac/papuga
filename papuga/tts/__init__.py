"""Fabryka silników TTS — tworzy odpowiedni silnik na podstawie ustawień."""
from __future__ import annotations

from papuga.config import Settings
from papuga.tts.base import TTSEngine, TTSError
from papuga.tts.edge_engine import EdgeTTSEngine
from papuga.tts.piper_engine import PiperTTSEngine
from papuga.tts.api_engine import ApiTTSEngine

__all__ = ["TTSEngine", "TTSError", "build_engine"]


def build_engine(settings: Settings) -> TTSEngine:
    if settings.engine == "edge":
        return EdgeTTSEngine(voice=settings.edge_voice)
    if settings.engine == "piper":
        return PiperTTSEngine(voice_id=settings.piper_voice_id)
    if settings.engine == "api":
        return ApiTTSEngine(
            provider=settings.api_provider,
            base_url=settings.api_base_url,
            api_key=settings.api_key,
            model=settings.api_model,
            voice=settings.api_voice,
        )
    raise TTSError(f"Nieznany silnik: {settings.engine}")
