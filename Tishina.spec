# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_all

datas = [
    ("tishina/presets", "tishina/presets"),
    ("tishina/vendor/PYRNNOISE_LICENSE.txt", "tishina/vendor"),
    ("tishina/vendor/RNNOISE_LICENSE.txt", "tishina/vendor"),
]
binaries = [
    ("tishina/vendor/rnnoise.dll", "tishina/vendor"),
]
hiddenimports = []

sd_datas, sd_binaries, sd_hidden = collect_all("sounddevice")
datas += sd_datas
binaries += sd_binaries
hiddenimports += sd_hidden

a = Analysis(
    ["app.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pytest", "IPython", "notebook"],
    noarchive=False,
)

pyz = PYZ(a.pure)

icon = "app.ico" if os.path.exists("app.ico") else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Tishina",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Tishina",
)
