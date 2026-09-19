"""Verify the E10 Deep Sky wardrobe. Same gates as E9, re-pointed at era 10.

The E9 verifier is the harness; era is the only variable. Keeping one harness
means the capstone cast is judged by exactly the rules that caught E9's silent
no-op, rather than by a second, kinder copy.

Usage:
  blender -b --factory-startup --python verify_town_e10_wardrobe.py
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

PILOTS = Path(__file__).resolve().parent
sys.dont_write_bytecode = True

_spec = importlib.util.spec_from_file_location("town_e9_verifier", PILOTS / "verify_town_e9_wardrobe.py")
verify = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verify)

verify.ERA = 10
verify.SOURCE_ERA = 9
verify.ARTIFACTS = verify.ROOT / "artifacts/town-e10"

if __name__ == "__main__":
    verify.main()
