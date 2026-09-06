"""Build the three E9 campaign-extra Panorama v2 rings."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("e9_panorama_base", OUT / "build_contract_panoramas.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

ROOT = OUT.parents[2]
KIT = ROOT / "assets/processed/kit-era-9.png"
CANAL = ROOT / "assets/raw/plate-e9-bld-canal-works.png"
DEVIL = ROOT / "assets/raw/plate-e9-enemy-dust-devil.png"

PROFILES = {
    "seed-run": {
        "contract": "seed-run",
        "kit": KIT,
        "sourcePlate": CANAL,
        "epoch": "Epoch 9 redfields heart-era",
        "tint": (0.58, 0.31, 0.22),
        "dark": (0.080, 0.026, 0.018),
        "phase": 0.17,
        "strength": 0.82,
        "dust": (0.52, 0.22, 0.12),
        "signature": "a rising seed road between unequal rust-red dune shelves and one thin green promise at the basin rim",
    },
    "devils-alley": {
        "contract": "devils-alley",
        "kit": KIT,
        "sourcePlate": DEVIL,
        "epoch": "Epoch 9 redfields heart-era",
        "tint": (0.63, 0.34, 0.22),
        "dark": (0.085, 0.024, 0.014),
        "phase": 0.53,
        "strength": 0.88,
        "dust": (0.66, 0.31, 0.14),
        "signature": "three wind corridors disappearing between asymmetric red dune walls and distant drawn devil columns",
    },
    "old-canal": {
        "contract": "old-canal",
        "kit": KIT,
        "sourcePlate": CANAL,
        "epoch": "Epoch 9 redfields heart-era",
        "tint": (0.50, 0.28, 0.21),
        "dark": (0.060, 0.024, 0.018),
        "phase": 0.81,
        "strength": 0.78,
        "dust": (0.44, 0.18, 0.12),
        "signature": "a dry inherited canal vanishing through broken survey shelves toward a low outflow notch",
    },
}

base.PROFILES.update(PROFILES)
base.LAYERED_PANORAMAS.update(PROFILES)
base.FAR_RIDGE_PANORAMAS.update(PROFILES)
_base_playfield_half_extents = base.playfield_half_extents


def playfield_half_extents(key):
    return (64.0, 64.0) if key in PROFILES else _base_playfield_half_extents(key)


base.playfield_half_extents = playfield_half_extents


def main():
    keys = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else list(PROFILES)
    for key in keys:
        if key not in PROFILES:
            raise ValueError(f"unsupported E9 panorama: {key}")
        base.build(key)


if __name__ == "__main__":
    main()
