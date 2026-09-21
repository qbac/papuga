"""
Silnik API — generyczne połączenie z zewnętrznym dostawcą TTS przez HTTP.
Wspiera od razu dwa najpopularniejsze warianty:
  - "openai"     — endpoint kompatybilny z OpenAI /v1/audio/speech
                    (działa też dla wielu innych dostawców, np. lokalnych
                    serwerów kompatybilnych z OpenAI)
  - "elevenlabs" — ElevenLabs Text-to-Speech API
  - "custom"     — dowolny endpoint OpenAI-compatible pod innym URL-em

Wymaga klucza API skonfigurowanego w ustawieniach.
"""
from __future__ import annotations

import uuid
from pathlib import Path

import requests

from papuga.tts.base import TTSEngine, TTSError


class ApiTTSEngine(TTSEngine):
    name = "api"

    def __init__(
        self,
        provider: str = "openai",
        base_url: str = "https://api.openai.com/v1/audio/speech",
        api_key: str = "",
        model: str = "tts-1",
        voice: str = "alloy",
    ) -> None:
        self.provider = provider
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.voice = voice

    def synthesize(self, text: str, out_dir: Path, speed: float = 1.0) -> Path:
        if not self.api_key:
            raise TTSError("Silnik API: brak klucza API w ustawieniach")

        out_dir.mkdir(parents=True, exist_ok=True)

        if self.provider == "elevenlabs":
            audio_bytes, ext = self._call_elevenlabs(text)
        else:
            audio_bytes, ext = self._call_openai_compatible(text, speed)

        out_path = out_dir / f"papuga_{uuid.uuid4().hex}.{ext}"
        out_path.write_bytes(audio_bytes)
        return out_path

    def _call_openai_compatible(self, text: str, speed: float) -> tuple[bytes, str]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "voice": self.voice,
            "input": text,
            "speed": max(0.25, min(4.0, speed)),
        }
        try:
            resp = requests.post(self.base_url, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise TTSError(f"Silnik API: błąd zapytania ({exc})") from exc
        return resp.content, "mp3"

    def _call_elevenlabs(self, text: str) -> tuple[bytes, str]:
        voice_id = self.voice or "21m00Tcm4TlvDq8ikWAM"  # domyślny głos ElevenLabs
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": self.model or "eleven_multilingual_v2",
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise TTSError(f"ElevenLabs: błąd zapytania ({exc})") from exc
        return resp.content, "mp3"
