# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — Banc de test automatique
# Commande : pyinstaller BancTestAuto.spec

import sys

block_cipher = None

# Fichiers à inclure dans l'exécutable (extraction dans sys._MEIPASS au lancement)
# Format : (src, dest_dans_MEIPASS)
datas = [
    ("config/config.json", "config"),
    ("resources/themes/dark.qss", "resources/themes"),
    ("resources/themes/light.qss", "resources/themes"),
    ("docs/AIDE.md", "docs"),
]

# Modules PyQt6 / dépendances à ne pas manquer
hiddenimports = [
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "serial",
    "serial.tools.list_ports",
    "markdown",
    "pyqtgraph",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
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
    name="BancTestAuto",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Pas de fenêtre console (application GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Optionnel : ajouter icon="resources/icon.ico"
)
