# Runtime hook for PyInstaller build of World Embalage
# Ensures the application can locate bundled resources (templates, DB, logo) when frozen.

import os
import sys
from pathlib import Path

# When bundled, sys._MEIPASS points to the temp extraction directory (onefile) or dist folder (onefolder)
base_path = Path(getattr(sys, '_MEIPASS', Path(sys.argv[0]).resolve().parent))

# Set CWD to the base path so relative paths in the code continue to work
try:
    os.chdir(base_path)
except Exception:
    pass

# Ensure template directory exists (defensive)
(template_dir := base_path / 'template').mkdir(exist_ok=True)

# If a writable copy of the dev DB is needed and we're in onefile mode, copy it out
# (Skipping automatic copy to avoid unintended overwrites; user can implement if desired.)

# Add base path to sys.path if not present
if str(base_path) not in sys.path:
    sys.path.insert(0, str(base_path))
