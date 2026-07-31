# -*- mode: python ; coding: utf-8 -*-
# Spec de PyInstaller para Sábatoxd.
# Se usa desde el workflow de GitHub Actions (o localmente con: pyinstaller build.spec)

import sys

if sys.platform == "win32":
    app_icon = "static/icon.ico"
elif sys.platform == "darwin":
    app_icon = "static/icon.icns"
else:
    app_icon = "static/icon.png"

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("templates", "templates"),
        ("static", "static"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Sabatoxd",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # sin ventana de terminal negra
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=app_icon,
)
