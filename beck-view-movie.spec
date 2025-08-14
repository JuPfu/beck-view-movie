# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
from PyInstaller.building.datastruct import TOC
from PyInstaller.utils.hooks import collect_dynamic_libs

# Path to your project
project_dir = Path.cwd()
dist_dir = Path("./dist")

object_files = "*.pyd" if os.name == "nt" else "*.so"

# Collect all .so files from the dist/ directory
cython_so_files = [
    (str(f), '.') for f in dist_dir.glob(object_files)
]
print(f"Found following {object_files} files {cython_so_files}")

a = Analysis(
    ['main.py'],  # your stub that imports main
    pathex=[str(project_dir)],
    binaries=cython_so_files,
    datas=[],
    hiddenimports=['numpy', 'cv2', 'concurrent.futures', 'tqdm'],
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
    name='beck-view-movie',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
