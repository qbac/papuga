"""
Silnik edge-tts — darmowe, neuronowe głosy Microsoft (ten sam mechanizm,
co "Czytaj na głos" w przeglądarce Edge). Wymaga internetu, nie wymaga
klucza API. Działa identycznie na Windows, Linux i macOS — to zwykłe
zapytania HTTP do publicznego endpointu Microsoftu, więc mimo nazwy nie
jest potrzebna zainstalowana przeglądarka Edge.
"""
from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from papuga.tts.base import TTSEngine, TTSError

# Kilka sensownych polskich głosów do wyboru w UI.
POLISH_VOICES = [
    "pl-PL-MarekNeural",     # męski
    "pl-PL-ZofiaNeural",     # żeński
    "pl-PL-AgnieszkaNeural", # żeński (starszy głos, wciąż wspierany)
]


class EdgeTTSEngine(TTSEngine):
    name = "edge"

    def __init__(self, voice: str = "pl-PL-MarekNeural") -> None:
        self.voice = voice

    def synthesize(self, text: str, out_dir: Path, speed: float = 1.0) -> Path:
        import edge_tts  # import lokalny — nieużywany silnik nie ciągnie zależności

        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"papuga_{uuid.uuid4().hex}.mp3"

        rate = _speed_to_rate(speed)

        async def _run() -> None:
            communicate = edge_tts.Communicate(text, self.voice, rate=rate)
            await communicate.save(str(out_path))

        try:
            asyncio.run(_run())
        except Exception as exc:  # noqa: BLE001
            raise TTSError(f"edge-tts: nie udało się wygenerować mowy ({exc})") from exc

        if not out_path.exists() or out_path.stat().st_size == 0:
            raise TTSError("edge-tts: nie otrzymano audio (sprawdź połączenie z internetem)")

        return out_path

    def list_voices(self) -> list[str]:
        return POLISH_VOICES


def _speed_to_rate(speed: float) -> str:
    """Konwertuje mnożnik (1.0 = normalnie) na format edge-tts, np. '+20%'."""
    percent = round((speed - 1.0) * 100)
    sign = "+" if percent >= 0 else ""
    return f"{sign}{percent}%"
