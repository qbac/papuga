"""Katalog języków i głosów (Edge TTS + Piper) z dołączonej migawki data/voices.json.

Odświeżanie migawki: scripts/update_voice_catalogs.py.
"""
from __future__ import annotations

import ctypes
import json
import locale
import sys
from functools import lru_cache
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent / "data" / "voices.json"
FALLBACK_LANGUAGE = "en"

# Piper: im wyżej, tym lepiej (kompromis jakość/rozmiar modelu) — do wyboru domyślnego głosu.
_QUALITY_ORDER = {"medium": 0, "high": 1, "low": 2, "x_low": 3}


@lru_cache(maxsize=1)
def catalog() -> dict:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def language_codes() -> list[str]:
    """Kody języków posortowane po angielskiej nazwie."""
    return list(catalog()["languages"].keys())


def language_label(code: str) -> str:
    """'Polski (Polish)'; dla języków, w których nazwa natywna = angielska, samo 'English'."""
    info = catalog()["languages"].get(code)
    if not info:
        return code
    native, english = info["native"], info["english"]
    return native if native.casefold() == english.casefold() else f"{native} ({english})"


def is_known_language(code: str) -> bool:
    return code in catalog()["languages"]


def edge_voices(lang: str) -> list[dict]:
    return catalog()["edge"].get(lang, [])


def piper_voices(lang: str) -> list[dict]:
    return catalog()["piper"].get(lang, [])


def find_piper_voice(voice_id: str) -> dict | None:
    for voices in catalog()["piper"].values():
        for v in voices:
            if v["id"] == voice_id:
                return v
    return None


# Odmiana regionalna preferowana przy wyborze domyślnego głosu (gdy nie jest to "xx-XX").
_PREFERRED_LOCALE = {"en": "en-US", "pt": "pt-BR", "zh": "zh-CN", "ar": "ar-SA", "sw": "sw-KE"}


def _locale_rank(lang: str, locale_code: str) -> int:
    """0 = najbardziej „główna” odmiana języka (np. es-ES, en-US), większe = dalsza."""
    loc = locale_code.replace("_", "-")
    preferred = _PREFERRED_LOCALE.get(lang, f"{lang}-{lang.upper()}")
    return 0 if loc == preferred else 1


# Znane, sprawdzone głosy Edge (dorosłe, neutralne) — używane jako domyślne, jeśli są w katalogu.
_PREFERRED_EDGE_VOICE = {
    "en": "en-US-AriaNeural", "es": "es-ES-ElviraNeural", "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural", "it": "it-IT-ElsaNeural", "pt": "pt-BR-FranciscaNeural",
    "ru": "ru-RU-SvetlanaNeural", "pl": "pl-PL-ZofiaNeural",
}


def default_edge_voice(lang: str) -> str:
    voices = edge_voices(lang)
    if not voices:
        return ""
    preferred = _PREFERRED_EDGE_VOICE.get(lang)
    if preferred and any(v["id"] == preferred for v in voices):
        return preferred
    return min(voices, key=lambda v: (_locale_rank(lang, v["locale"]), v["multilingual"]))["id"]


def default_piper_voice(lang: str) -> str:
    voices = piper_voices(lang)
    if not voices:
        return ""
    return min(
        voices,
        key=lambda v: (_locale_rank(lang, v["locale"]), _QUALITY_ORDER.get(v["quality"], 9)),
    )["id"]


def edge_voice_label(v: dict) -> str:
    extra = ", multilingual" if v.get("multilingual") else ""
    return f"{v['name']} — {v['locale']}, {v['gender']}{extra}"


def piper_voice_label(v: dict) -> str:
    size = f", {round(v['size'] / 1_000_000)} MB" if v.get("size") else ""
    return f"{v['name']} — {v['locale']}, {v['quality']}{size}"


def system_language() -> str:
    """Język systemu (kod 2-literowy) jeśli mamy dla niego głosy, inaczej angielski."""
    code = _system_locale_code()
    fam = code.replace("_", "-").split("-")[0].lower() if code else ""
    fam = "no" if fam == "nb" else fam
    return fam if fam and is_known_language(fam) else FALLBACK_LANGUAGE


def _system_locale_code() -> str:
    try:
        if sys.platform == "win32":
            lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            buf = ctypes.create_unicode_buffer(85)
            if ctypes.windll.kernel32.LCIDToLocaleName(lcid, buf, 85, 0):
                return buf.value  # np. 'pl-PL'
        return locale.getlocale()[0] or ""
    except Exception:  # noqa: BLE001
        return ""
