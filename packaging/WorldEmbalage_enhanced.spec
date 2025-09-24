# Enhanced PyInstaller spec for World Embalage
# Target: Windows (primary) but works cross-platform
# Build modes:
#   pyinstaller packaging/WorldEmbalage_enhanced.spec          (one-folder, recommended for writable DB)
#   pyinstaller --onefile packaging/WorldEmbalage_enhanced.spec  (single exe; SQLite DB becomes read-only inside bundle)
#
# Notes:
# - Keeps application window maximized at startup (handled in code: main.py, no change here)
# - Bundles templates, logo assets, optional .env, and initial SQLite dev DB if present.
# - Preserves extra runtime flexibility with runtime_hook setting working directory.

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, Tree

block_cipher = None

# Entry script
entry_script = str(Path('src') / 'main.py')

# Hidden imports: PyQt6 (all), reportlab, Pillow (PIL), SQLAlchemy dialects, PyPDF2, dotenv
hiddenimports = []
for pkg in [
    'PyQt6',
    'reportlab',
    'PIL',
    'sqlalchemy.dialects',
]:
    hiddenimports.extend(collect_submodules(pkg))
# Explicit extras sometimes not auto-detected
hiddenimports.extend([
    'PyPDF2',
    'dotenv',
])

# Data files (individual files)
root = Path('.')
file_datas = []
for fname in ['LOGO.jpg', 'LOGO.ico', '.env', 'world_embalage_dev.db']:
    if Path(fname).exists():
        file_datas.append((str(Path(fname)), '.'))
# Also include fallback DB inside src if that's where it's located
if Path('src/world_embalage_dev.db').exists():
    file_datas.append(('src/world_embalage_dev.db', '.'))

# Directory trees (templates, optional config for reference)
# Code for config is frozen anyway, but templates must be accessible at runtime.
extra_trees = [
    Tree('template', prefix='template') if Path('template').exists() else None,
]
extra_trees = [t for t in extra_trees if t is not None]

# Runtime hooks (resource path adjustments)
runtime_hooks = ['packaging/runtime_hook.py'] if Path('packaging/runtime_hook.py').exists() else []

# Analysis
a = Analysis(
    [entry_script],
    pathex=['src'],
    binaries=[],
    datas=file_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    excludes=[],
    noarchive=False,
    runtime_hooks=runtime_hooks,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WorldEmbalage',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI app, suppress console window on Windows
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='LOGO.ico' if Path('LOGO.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    *extra_trees,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WorldEmbalage'
)

# Usage examples (one-folder build recommended):
#   pyinstaller packaging/WorldEmbalage_enhanced.spec
#   dist/WorldEmbalage/WorldEmbalage.exe  (Windows)
# To build one-file (DB inside bundle becomes read-only / ephemeral):
#   pyinstaller --onefile packaging/WorldEmbalage_enhanced.spec
