# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec dla Papugi.
# Buduj na docelowym systemie (Windows -> .exe, Linux -> binarka ELF):
#   pyinstaller papuga.spec
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None

root = Path(".").resolve()
icon_ico = str(root / "papuga" / "assets" / "icon.ico")

# Piper działa W PROCESIE (biblioteka piper-tts z wbudowanym espeak-ng-data i onnxruntime),
# więc dołączamy je w całości: kod, dane (espeak-ng-data) i biblioteki natywne.
piper_datas, piper_binaries, piper_hidden = collect_all("piper")
ort_datas, ort_binaries, ort_hidden = collect_all("onnxruntime")

a = Analysis(
    ["papuga/main.py"],
    pathex=[str(root)],
    binaries=piper_binaries + ort_binaries,
    datas=[
        ("papuga/assets/icon.png", "papuga/assets"),
        ("papuga/assets/icon.ico", "papuga/assets"),
        ("papuga/data/voices.json", "papuga/data"),
        *piper_datas,
        *ort_datas,
    ],
    hiddenimports=[
        "edge_tts",
        "pystray._win32" if sys.platform == "win32" else "pystray._xorg",
        "PIL._tkinter_finder",
        *piper_hidden,
        *ort_hidden,
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Papuga",
    debug=False,
    strip=False,
    upx=True,
    console=False,  # bez czarnego okna konsoli — apka żyje tylko w trayu
    icon=icon_ico if sys.platform == "win32" else None,
)
