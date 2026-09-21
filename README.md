# Papuga 🦜

[![Latest release](https://img.shields.io/github/v/release/qbac/papuga?label=release)](https://github.com/qbac/papuga/releases/latest)
[![License: GPL v3](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)

**English** · [Polski](README.pl.md)

Select text anywhere on your computer, press a shortcut, and listen to it.
Papuga lives in the system tray, reads **80 languages**, and works **fully offline** if you want it to.

## Download (Windows)

Get **`Papuga-vX.Y.Z-windows-x64.exe`** from the
[latest release](https://github.com/qbac/papuga/releases/latest). It is a single,
self-contained file: no installation, no Python, nothing else to set up. Run it and the
icon appears in the system tray (it may hide under the “show hidden icons” arrow).

A `.sha256` checksum sits next to the file:

```powershell
Get-FileHash .\Papuga-v0.2.0-windows-x64.exe -Algorithm SHA256
```

> **Windows SmartScreen** may warn about an “unknown publisher”, because the file is not
> code-signed. Choose *More info → Run anyway*. The source is in this repository and the file
> is built by a public workflow ([`release.yml`](.github/workflows/release.yml)).

## How it works

1. Select any text — in a browser, Word, a PDF, an e-mail, anywhere.
2. Press the global shortcut (default **Ctrl+Alt+R**).
3. Papuga copies the selection, turns it into speech and plays it. Long texts are split into
   sentences: speech starts after the first one while the rest is generated in the background.
4. **Ctrl+Alt+S** (default) stops reading at any moment.

The tray icon changes colour: green = ready, orange = reading, red = error.

## Languages (great for language learners)

Pick the **reading language** in the settings — Spanish, French, German, English, Japanese,
Polish and about 70 more — and Papuga reads the selected text with a voice for that language.
Learning a language? Right-click the tray icon → **Reading language** to switch between the
languages you use most, without opening the settings.

The list of languages and voices depends on the engine:

| Engine | Works offline? | Languages / voices | Notes |
|---|---|---|---|
| **Edge TTS** (default) | No (needs internet) | 75 languages, 300+ natural voices | Some voices are multilingual. Free, no key. |
| **Piper** | **Yes, fully** | 49 languages, 170 voices | Built in. The voice you choose is downloaded once (~60 MB) on first use, then works offline. |
| **API** | No | Whatever your provider offers | OpenAI-compatible endpoints, ElevenLabs, custom URL. Needs your own API key. |

> The settings only list languages the selected engine has voices for. If you switch to an
> engine that does not support your current language, Papuga selects English.

## Settings

Right-click the tray icon → *Settings...*:

- speech engine, reading language and voice,
- both keyboard shortcuts — click the field and **press the combination you want** (no typing
  needed); the **Windows** key is supported, Esc cancels. Shortcuts reserved by Windows
  (e.g. Win+R) are still handled by the system,
- speech speed (0.5×–2.0×),
- interface language (English or Polish; “Automatic” follows your system).

The config is saved automatically (`%APPDATA%\Papuga\config.json` on Windows). Logs:
`%LOCALAPPDATA%\Papuga\Logs\papuga.log`. Downloaded Piper voices:
`%LOCALAPPDATA%\Papuga\piper_voices`.

### Start with Windows

`Win+R` → `shell:startup` → put a shortcut to `Papuga.exe` there.

## Run from source

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python scripts\run_dev.py
# Linux/macOS:
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python scripts/run_dev.py
```

Ready-made releases are currently built for Windows only. On Linux run from source or build
it yourself (`./scripts/build_linux.sh` → `dist/Papuga`; not covered by automated releases).

## Build the .exe locally (Windows)

```powershell
.\scripts\build_windows.ps1
```

Result: `dist\Papuga.exe` — a single file. Build on Windows (PyInstaller does not cross-compile).
`Papuga.exe --selftest` checks the built file: it synthesizes speech with Piper, opens a Tk
window and loads the voice catalog (result in the log and the exit code).

## Versioning and releases

The app version has a single source of truth: `__version__` in
[`papuga/__init__.py`](papuga/__init__.py) ([SemVer](https://semver.org/)). To release:

```bash
# 1. bump __version__ in papuga/__init__.py and commit
# 2. tag the commit with the same version and push the tag
git tag v0.3.0
git push origin v0.3.0
```

The [`release.yml`](.github/workflows/release.yml) workflow checks that the tag matches
`__version__`, builds `Papuga.exe` on Windows, runs the self-test and publishes it under
*Releases* with a SHA-256 checksum and generated release notes.

## Project layout

```
papuga/
  __init__.py       version (__version__), name, author and repository links
  main.py           entry point (tray), --selftest
  app.py            wires hotkey + selection + TTS + playback + tray
  config.py         settings (JSON)
  i18n.py           interface translations (English, Polish)
  voices.py         language and voice catalog (reads data/voices.json)
  data/voices.json  snapshot of the Edge TTS and Piper voice catalogs
  selection.py      reads the selected text (simulated Ctrl+C)
  hotkey.py         global shortcuts + shortcut recorder for the UI (pynput)
  player.py         audio playback (pygame)
  singleinstance.py single running instance (Windows named mutex)
  tts/              speech engines (edge_engine, piper_engine, api_engine)
  ui/settings_window.py   settings window (customtkinter)
scripts/
  update_voice_catalogs.py   refreshes data/voices.json
  generate_icon.py, build_windows.ps1, build_linux.sh, run_dev.py
.github/workflows/release.yml   build + release on a vX.Y.Z tag
papuga.spec         PyInstaller configuration
```

To add a language interface translation, add a block to `STRINGS` in
[`papuga/i18n.py`](papuga/i18n.py) and register it in `UI_LANGUAGES`.
To add a speech engine, implement `papuga.tts.base.TTSEngine`
(`synthesize(text, out_dir, speed) -> Path`) and register it in `papuga/tts/__init__.py`.

## License

Papuga is free software under the **[GNU GPL v3 or later](LICENSE)** © 2026
[qbac](https://github.com/qbac). It bundles [Piper](https://github.com/OHF-Voice/piper1-gpl)
(GPL-3.0-or-later), which is why the whole program is GPL.
See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for all components and for the
**voice licenses** — each Piper voice has its own license, and Edge TTS is an unofficial
client of a Microsoft service (Papuga is not affiliated with Microsoft).
