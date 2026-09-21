"""Odświeża papuga/data/voices.json — migawkę katalogów głosów Piper i Edge TTS.

Aplikacja czyta tylko ten plik (działa offline, nie zależy od zewnętrznych list).
Uruchom ręcznie, gdy chcesz dociągnąć nowe głosy:

    python scripts/update_voice_catalogs.py
"""
from __future__ import annotations

import asyncio
import json
import urllib.request
from datetime import date
from pathlib import Path

PIPER_VOICES_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/voices.json?download=true"
OUT = Path(__file__).resolve().parent.parent / "papuga" / "data" / "voices.json"

# Języki Pipera wymagające dodatkowych bibliotek (g2pW, OpenJTalk, tltk, hebrajski) —
# nie są dołączone do aplikacji. Edge TTS obsługuje je bez problemu.
PIPER_SKIP_FAMILIES = {"zh", "ja", "th", "he"}

# Natywne nazwy języków, których Piper nie opisuje (są tylko w Edge TTS).
NATIVE_NAMES = {
    "af": "Afrikaans", "am": "አማርኛ", "az": "Azərbaycanca", "bs": "Bosanski", "fil": "Filipino",
    "ga": "Gaeilge", "gl": "Galego", "gu": "ગુજરાતી", "hr": "Hrvatski", "iu": "ᐃᓄᒃᑎᑐᑦ",
    "jv": "Basa Jawa", "km": "ភាសាខ្មែរ", "kn": "ಕನ್ನಡ", "lo": "ລາວ", "mk": "Македонски",
    "mn": "Монгол", "ms": "Bahasa Melayu", "mt": "Malti", "my": "မြန်မာ", "ps": "پښتو",
    "si": "සිංහල", "so": "Soomaali", "su": "Basa Sunda", "ta": "தமிழ்", "uz": "Oʻzbekcha",
    "zu": "isiZulu", "zh": "中文", "ja": "日本語", "th": "ไทย", "he": "עברית", "ko": "한국어",
}


def family(code: str) -> str:
    fam = code.replace("_", "-").split("-")[0].lower()
    return "no" if fam == "nb" else fam  # bokmål scalamy z norweskim


def english_name(locale_name: str) -> str:
    return locale_name.split("(")[0].strip()


def build() -> dict:
    languages: dict[str, dict] = {}
    piper: dict[str, list] = {}
    edge: dict[str, list] = {}

    piper_raw = json.load(urllib.request.urlopen(PIPER_VOICES_URL, timeout=60))
    for key, v in piper_raw.items():
        lang = v["language"]
        fam = family(lang["family"])
        if fam in PIPER_SKIP_FAMILIES:
            continue
        onnx_size = next((f["size_bytes"] for p, f in v["files"].items() if p.endswith(".onnx")), 0)
        onnx_path = next(p for p in v["files"] if p.endswith(".onnx"))
        languages.setdefault(fam, {"native": lang["name_native"], "english": lang["name_english"]})
        piper.setdefault(fam, []).append({
            "id": key,
            "name": v["name"],
            "quality": v["quality"],
            "locale": lang["code"],
            "country": lang.get("country_english", ""),
            "dir": onnx_path.rsplit("/", 1)[0],
            "size": onnx_size,
        })

    import edge_tts

    for v in asyncio.run(edge_tts.list_voices()):
        fam = family(v["Locale"])
        eng = english_name(v["LocaleName"])
        languages.setdefault(fam, {"native": NATIVE_NAMES.get(fam, eng), "english": eng})
        short = v["ShortName"]
        name = short.split("-", 2)[-1].replace("Neural", "")
        edge.setdefault(fam, []).append({
            "id": short,
            "name": name,
            "gender": v["Gender"],
            "locale": v["Locale"],
            "multilingual": "Multilingual" in short,
        })

    for lst in (*piper.values(), *edge.values()):
        lst.sort(key=lambda x: (x["locale"], x["name"]))

    return {
        "generated": date.today().isoformat(),
        "languages": dict(sorted(languages.items(), key=lambda kv: kv[1]["english"])),
        "edge": dict(sorted(edge.items())),
        "piper": dict(sorted(piper.items())),
    }


if __name__ == "__main__":
    data = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Zapisano {OUT}: {len(data['languages'])} języków, "
          f"{sum(map(len, data['edge'].values()))} głosów Edge, "
          f"{sum(map(len, data['piper'].values()))} głosów Piper")
