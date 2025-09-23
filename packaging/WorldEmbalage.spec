# PyInstaller spec file for building the World Embalage desktop app
# Target: Windows executable (also works cross-platform)

import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Entry point
entry_script = os.path.join('src', 'main.py')

# Include all PyQt6 modules (defensive for hook edge-cases)
hiddenimports = collect_submodules('PyQt6')

# Data files to bundle with the executable
# - Project logo at repository root
# - All PDF templates under template/
datas = [
    ('LOGO.jpg', '.'),
    ('template' + os.sep + '*', 'template'),
]

a = Analysis(
    [entry_script],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    excludes=[],
    noarchive=False,
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
    console=False,  # GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WorldEmbalage'
)
