"""
Silnik edge-tts — darmowe, neuronowe głosy Microsoft (ten sam mechanizm,
co "Czytaj na głos" w przeglądarce Edge). Wymaga internetu, nie wymaga
klucza API. Działa identycznie na Windows, Linux i macOS — to zwykłe
zapytania HTTP do publicznego endpointu Microsoftu, więc mimo nazwy nie
jest potrzebna zainstalowana przeglądarka Edge.

Lista głosów i języków: papuga/data/voices.json (patrz papuga/voices.py).
"""
from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from papuga import voices
from papuga.i18n import t
from papuga.tts.base import TTSEngine, TTSError


class EdgeTTSEngine(TTSEngine):
    name = "edge"

    def __init__(self, voice: str = "") -> None:
        self.voice = voice

    def synthesize(self, text: str, out_dir: Path, speed: float = 1.0) -> Path:
        import edge_tts  # import lokalny — nieużywany silnik nie ciągnie zależności

        if not self.voice:
            raise TTSError(t("err_edge_no_voice"))

        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"papuga_{uuid.uuid4().hex}.mp3"

        rate = _speed_to_rate(speed)

        async def _run() -> None:
            communicate = edge_tts.Communicate(text, self.voice, rate=rate)
            await communicate.save(str(out_path))

        try:
            asyncio.run(_run())
        except Exception as exc:  # noqa: BLE001
            raise TTSError(t("err_edge_failed", error=exc)) from exc

        if not out_path.exists() or out_path.stat().st_size == 0:
            raise TTSError(t("err_edge_no_audio"))

        return out_path

    def list_voices(self) -> list[str]:
        return [v["id"] for vs in voices.catalog()["edge"].values() for v in vs]


def _speed_to_rate(speed: float) -> str:
    """Konwertuje mnożnik (1.0 = normalnie) na format edge-tts, np. '+20%'."""
    percent = round((speed - 1.0) * 100)
    sign = "+" if percent >= 0 else ""
    return f"{sign}{percent}%"
