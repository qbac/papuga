# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec dla Papugi.
# Buduj na docelowym systemie (Windows -> .exe, Linux -> binarka ELF):
#   pyinstaller papuga.spec
import sys
from pathlib import Path

block_cipher = None

root = Path(".").resolve()
icon_ico = str(root / "papuga" / "assets" / "icon.ico")

a = Analysis(
    ["papuga/main.py"],
    pathex=[str(root)],
    binaries=[],
    datas=[
        ("papuga/assets/icon.png", "papuga/assets"),
        ("papuga/assets/icon.ico", "papuga/assets"),
    ],
    hiddenimports=[
        "edge_tts",
        "pystray._win32" if sys.platform == "win32" else "pystray._xorg",
        "PIL._tkinter_finder",
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
