"""Puts lib/ on the import path, so the tests run from a checkout without
installing the package."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))
sys.dont_write_bytecode = True
