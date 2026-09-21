"""
Silnik Piper — w pełni lokalny, offline neural TTS (VITS w ONNX), uruchamiany
W PROCESIE aplikacji przez bibliotekę `piper-tts` (z wbudowanym espeak-ng),
więc nie trzeba niczego instalować osobno — także w samodzielnym .exe.

Model wybranego głosu jest pobierany raz (przy pierwszym użyciu) z Hugging Face
i trzymany na dysku. Lista głosów pochodzi z papuga/data/voices.json.
"""
from __future__ import annotations

import os
import shutil
import sys
import threading
import uuid
import wave
from pathlib import Path

import requests
from platformdirs import user_data_dir

from papuga import APP_NAME, voices
from papuga.i18n import t
from papuga.tts.base import TTSEngine, TTSError

VOICES_DIR = Path(user_data_dir(APP_NAME, appauthor=False)) / "piper_voices"
HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

_voice_cache: dict[str, object] = {}  # ścieżka modelu -> załadowany PiperVoice
_voice_lock = threading.Lock()


class PiperTTSEngine(TTSEngine):
    name = "piper"

    def __init__(self, voice_id: str = "") -> None:
        self.voice_id = voice_id

    def _voice_info(self) -> dict:
        if not self.voice_id:
            raise TTSError(t("err_piper_no_voice"))
        info = voices.find_piper_voice(self.voice_id)
        if info is None:
            raise TTSError(t("err_piper_unknown_voice", voice=self.voice_id))
        return info

    def _paths(self) -> tuple[Path, Path]:
        return VOICES_DIR / f"{self.voice_id}.onnx", VOICES_DIR / f"{self.voice_id}.onnx.json"

    def needs_download(self) -> bool:
        model, cfg = self._paths()
        return not (model.exists() and cfg.exists())

    def download_size_mb(self) -> int:
        return round(self._voice_info().get("size", 0) / 1_000_000)

    def synthesize(self, text: str, out_dir: Path, speed: float = 1.0) -> Path:
        info = self._voice_info()
        model_path, config_path = self._ensure_voice(info)

        try:
            from piper import SynthesisConfig

            piper_voice = self._load(model_path, config_path)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"papuga_{uuid.uuid4().hex}.wav"
            # length_scale > 1.0 = wolniej, < 1.0 = szybciej (odwrotność speed)
            syn_config = SynthesisConfig(length_scale=1.0 / max(speed, 0.1))
            with wave.open(str(out_path), "wb") as wav_file:
                piper_voice.synthesize_wav(text, wav_file, syn_config=syn_config)
        except TTSError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise TTSError(t("err_piper_failed", error=exc)) from exc

        if not out_path.exists() or out_path.stat().st_size <= 44:  # sam nagłówek WAV
            raise TTSError(t("err_piper_failed", error="no audio"))
        return out_path

    def list_voices(self) -> list[str]:
        return [v["id"] for verts in voices.catalog()["piper"].values() for v in verts]

    @staticmethod
    def _load(model_path: Path, config_path: Path):
        from piper import PiperVoice

        key = str(model_path)
        with _voice_lock:
            if key not in _voice_cache:
                _voice_cache[key] = PiperVoice.load(
                    model_path, config_path=config_path, espeak_data_dir=_safe_espeak_data_dir()
                )
            return _voice_cache[key]

    def _ensure_voice(self, info: dict) -> tuple[Path, Path]:
        VOICES_DIR.mkdir(parents=True, exist_ok=True)
        model_path, config_path = self._paths()
        base = f"{HF_BASE}/{info['dir']}/{self.voice_id}"
        if not config_path.exists():
            _download(f"{base}.onnx.json", config_path)
        if not model_path.exists():
            _download(f"{base}.onnx", model_path, expected_size=info.get("size"))
        return model_path, config_path


_espeak_dir_cache: Path | None = None


def _safe_espeak_data_dir() -> Path:
    """Ścieżka do danych espeak-ng zawierająca WYŁĄCZNIE znaki ASCII.

    Biblioteka C espeak-ng nie radzi sobie z nie-ASCII w ścieżce do swoich danych (cofa się
    do ścieżki wkompilowanej na maszynie budującej i pada). W samodzielnym .exe dane
    rozpakowują się do TEMP, a ten zawiera nazwę konta — np. „C:\\Users\\Łukasz\\…".
    """
    global _espeak_dir_cache
    if _espeak_dir_cache is not None:
        return _espeak_dir_cache

    from piper.phonemize_espeak import ESPEAK_DATA_DIR

    src = Path(ESPEAK_DATA_DIR)
    if str(src).isascii():
        _espeak_dir_cache = src
        return src

    short = _short_path(src)  # nazwa 8.3, o ile wolumin je tworzy
    if short and short.isascii() and (Path(short) / "phontab").exists():
        _espeak_dir_cache = Path(short)
        return _espeak_dir_cache

    # Kopia (ok. 18 MB, robiona raz) w katalogu o ASCII-owej ścieżce.
    for base in (os.environ.get("ProgramData"), os.environ.get("PUBLIC"), r"C:\Users\Public"):
        if not base or not base.isascii():
            continue
        dest = Path(base) / "Papuga" / "espeak-ng-data"
        try:
            if not (dest / "phontab").exists():
                tmp = dest.with_name(dest.name + ".tmp")
                shutil.rmtree(tmp, ignore_errors=True)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src, tmp)
                shutil.rmtree(dest, ignore_errors=True)
                os.replace(tmp, dest)
            _espeak_dir_cache = dest
            return dest
        except OSError:
            continue

    return src  # ostatnia deska ratunku — może się nie udać przy nie-ASCII


def _short_path(path: Path) -> str:
    if sys.platform != "win32":
        return ""
    try:
        import ctypes

        buf = ctypes.create_unicode_buffer(1024)
        n = ctypes.windll.kernel32.GetShortPathNameW(str(path), buf, len(buf))
        return buf.value if 0 < n < len(buf) else ""
    except Exception:  # noqa: BLE001
        return ""


def _download(url: str, dest: Path, expected_size: int | None = None) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with requests.get(url, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1 << 16):
                    f.write(chunk)
        if expected_size and tmp.stat().st_size != expected_size:
            raise OSError(f"incomplete download ({tmp.stat().st_size} of {expected_size} bytes)")
        tmp.replace(dest)
    except Exception as exc:  # noqa: BLE001
        tmp.unlink(missing_ok=True)
        raise TTSError(t("err_piper_download", error=exc)) from exc
