# Third-party software / Oprogramowanie stron trzecich

Papuga is licensed under **GPL-3.0-or-later** (see [LICENSE](LICENSE)). The standalone
`Papuga.exe` bundles the components below; their licenses apply to them.
The complete source of Papuga is in this repository.

| Component | Purpose | License |
|---|---|---|
| [piper-tts](https://github.com/OHF-Voice/piper1-gpl) (incl. bundled `espeak-ng` data) | offline speech synthesis | GPL-3.0-or-later |
| [onnxruntime](https://github.com/microsoft/onnxruntime) | runs Piper's neural models | MIT |
| [edge-tts](https://github.com/rany2/edge-tts) | client for Microsoft's online voices | LGPL-3.0 |
| [pygame](https://www.pygame.org/) (SDL) | audio playback | LGPL-2.1 |
| [pystray](https://github.com/moses-palmer/pystray) | system tray icon | LGPL-3.0 |
| [pynput](https://github.com/moses-palmer/pynput) | global shortcuts, simulated keys | LGPL-3.0 |
| [customtkinter](https://github.com/TomSchimansky/CustomTkinter) | settings window | MIT |
| [Pillow](https://python-pillow.org/) | icons | MIT-CMU (HPND) |
| [requests](https://requests.readthedocs.io/) | HTTP | Apache-2.0 |
| [pyperclip](https://github.com/asweigart/pyperclip) | clipboard | BSD-3-Clause |
| [platformdirs](https://github.com/tox-dev/platformdirs) | config/data folders | MIT |
| [NumPy](https://numpy.org/) | used by onnxruntime | BSD-3-Clause |
| [PyInstaller](https://pyinstaller.org/) | builds the `.exe` | GPL-2.0-or-later with bootloader exception |

## Voices / Głosy

- **Piper voices are not bundled.** They are downloaded on first use from
  [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) on Hugging Face.
  **Each voice has its own license** (see the `MODEL_CARD` next to it in that repository);
  some voices are for non-commercial use only. Check it before using a voice commercially.
- **Edge TTS voices** come from Microsoft's online service through the unofficial
  `edge-tts` client. Papuga is not affiliated with or endorsed by Microsoft; the service
  may change or stop working at any time, and Microsoft's terms apply to its use.
- The voice list in `papuga/data/voices.json` is a snapshot of those two catalogs.
