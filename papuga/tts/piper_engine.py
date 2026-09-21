"""
Silnik Piper — w pełni lokalny, offline neural TTS (VITS wyeksportowany
do ONNX). Nie wysyła nic do internetu podczas czytania; model głosu
jest pobierany raz (przy pierwszym użyciu) i trzymany na dysku.

Uruchamiamy oficjalny plik wykonywalny `piper` (instalowany razem
z pakietem pip `piper-tts`) jako podproces — to najbardziej stabilny
sposób działania niezależnie od wersji biblioteki.
"""
from __future__ import annotations

import shutil
import subprocess
import uuid
from pathlib import Path

import requests
from platformdirs import user_data_dir

from papuga import APP_NAME
from papuga.tts.base import TTSEngine, TTSError

VOICES_DIR = Path(user_data_dir(APP_NAME, appauthor=False)) / "piper_voices"

HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

# Znane, sprawdzone polskie głosy Pipera: {voice_id: (folder_na_HF, jakość)}
POLISH_VOICES = {
    "pl_PL-darkman-medium": "pl/pl_PL/darkman/medium",
    "pl_PL-gosia-medium": "pl/pl_PL/gosia/medium",
    "pl_PL-mc_speech-medium": "pl/pl_PL/mc_speech/medium",
}


class PiperTTSEngine(TTSEngine):
    name = "piper"

    def __init__(self, voice_id: str = "pl_PL-darkman-medium") -> None:
        self.voice_id = voice_id

    def synthesize(self, text: str, out_dir: Path, speed: float = 1.0) -> Path:
        model_path, config_path = self._ensure_voice(self.voice_id)

        piper_bin = shutil.which("piper")
        if not piper_bin:
            raise TTSError(
                "Nie znaleziono programu 'piper'. Zainstaluj pakiet piper-tts "
                "(pip install piper-tts) i upewnij się, że jest w PATH."
            )

        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"papuga_{uuid.uuid4().hex}.wav"

        # length_scale > 1.0 = wolniej, < 1.0 = szybciej (odwrotność speed)
        length_scale = 1.0 / max(speed, 0.1)

        try:
            subprocess.run(
                [
                    piper_bin,
                    "--model", str(model_path),
                    "--config", str(config_path),
                    "--length_scale", str(length_scale),
                    "--output_file", str(out_path),
                ],
                input=text.encode("utf-8"),
                check=True,
                capture_output=True,
                timeout=120,
            )
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode("utf-8", errors="ignore") if exc.stderr else ""
            raise TTSError(f"Piper: błąd generowania mowy: {stderr[:300]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise TTSError("Piper: przekroczono czas generowania mowy") from exc

        if not out_path.exists() or out_path.stat().st_size == 0:
            raise TTSError("Piper: nie wygenerowano pliku audio")

        return out_path

    def list_voices(self) -> list[str]:
        return list(POLISH_VOICES.keys())

    def _ensure_voice(self, voice_id: str) -> tuple[Path, Path]:
        if voice_id not in POLISH_VOICES:
            raise TTSError(f"Piper: nieznany głos '{voice_id}'")

        remote_dir = POLISH_VOICES[voice_id]
        VOICES_DIR.mkdir(parents=True, exist_ok=True)
        model_path = VOICES_DIR / f"{voice_id}.onnx"
        config_path = VOICES_DIR / f"{voice_id}.onnx.json"

        if not model_path.exists():
            _download(f"{HF_BASE}/{remote_dir}/{voice_id}.onnx", model_path)
        if not config_path.exists():
            _download(f"{HF_BASE}/{remote_dir}/{voice_id}.onnx.json", config_path)

        return model_path, config_path


def _download(url: str, dest: Path) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with requests.get(url, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1 << 16):
                    f.write(chunk)
        tmp.rename(dest)
    except Exception as exc:  # noqa: BLE001
        tmp.unlink(missing_ok=True)
        raise TTSError(
            f"Piper: nie udało się pobrać modelu głosu ({exc}). "
            "Pobranie głosu wymaga jednorazowo internetu."
        ) from exc
