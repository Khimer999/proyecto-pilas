# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys

project_dir = Path(SPECPATH).resolve()
sys.path.insert(0, str(project_dir))
from proyecto_pilas import ASSETS

a = Analysis(
    [str(project_dir / 'proyecto_pilas.py')],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[(str(project_dir / filename), '.') for filename in ASSETS],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='proyecto_pilas',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
