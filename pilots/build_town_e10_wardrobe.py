"""Dress the town for Epoch 10, "The Deep Sky" — the capstone cast, aboard the Ark.

E10's art law is preservation, not reinvention. The bundle is explicit: the Ark's
"deck sections per lineage — every deck keeps its era's grammar (walking the ship
is walking the saga)", and the final contracts "don't extract; they PRESERVE".

So this is deliberately NOT another palette wash. E9 turned the whole town rust;
doing that again in ink would erase the nine eras the Ark exists to carry. Instead
each building is re-dressed from its **E9** coat with a light Ark seam:

  * the deep values cool toward the void outside the hull, and only the deep
    values — space is "deep ink with engraved star-stipple";
  * the highlights warm toward "nebulae are parchment-gold veils";
  * the midtones, which carry every era's accumulated grammar, are left almost
    exactly alone. That restraint IS the era.

The E1 riverbank swatch rides along untouched, because a ship carrying the saga
carries the callback too.

Everything structural is inherited from the E9 builder rather than re-derived:
the atlas rebind (an imported GLB's image is packed, so editing pixels in place
silently ships the previous era), the footprint clamp (Town rejects an off-centre
model and quietly serves the older era), the delivery-from-reopened-.blend export,
and the swatch read-back gate.

Usage:
  blender -b --factory-startup --python build_town_e10_wardrobe.py
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import bpy
import numpy as np

PILOTS = Path(__file__).resolve().parent
sys.dont_write_bytecode = True

_spec = importlib.util.spec_from_file_location("town_e9_builder", PILOTS / "build_town_e9_wardrobe.py")
e9 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e9)

ARTIFACTS = e9.ROOT / "artifacts/town-e10"

e9.ERA = 10
e9.SOURCE_ERA = 9

# The Ark's own materials sit BESIDE the eras rather than over them.
e9.SUB_PALETTE = {
    "green": e9.E1_GREEN,            # the callback, still aboard
    "regolith": (0.44, 0.26, 0.16),  # carried-forward era crust, cooled a little
    "ice": (0.30, 0.50, 0.56),       # preserved water
    "dome": (0.86, 0.78, 0.55),      # nebula-gold veil light
    "brass": (0.66, 0.52, 0.24),     # the Press's brass-and-teal fittings
    "iron": (0.16, 0.16, 0.21),      # hull plate: ink, never black
}
e9.SUB_ORDER = list(e9.SUB_PALETTE)


def deepsky_remap(pixels: np.ndarray) -> np.ndarray:
    """A hull seam, not a repaint: cool the void, gild the highlight, keep the saga."""
    rgb = pixels[..., :3]
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)

    void = np.array([0.09, 0.10, 0.16], dtype=np.float32)   # deep ink
    nebula = np.array([0.93, 0.85, 0.63], dtype=np.float32)  # parchment gold

    # Only the darkest values become ship-and-space; only the brightest catch the
    # nebula. Everything between is the era grammar and is left to speak.
    to_void = np.clip((0.30 - lum) / 0.30, 0.0, 1.0)[..., None] * 0.72
    to_nebula = np.clip((lum - 0.72) / 0.28, 0.0, 1.0)[..., None] * 0.42

    out = rgb * (1.0 - to_void) + void * to_void
    out = out * (1.0 - to_nebula) + nebula * to_nebula

    result = pixels.copy()
    result[..., :3] = np.clip(out, 0.0, 1.0)
    return result


e9.rust_remap = deepsky_remap

# Roles are the bundle's own deck list. Two are deliberately NOT named for the
# existing plaza props `bridge-school.e10.glb` and `charter-press.e10.glb`: the
# props are the fixtures, these are the halls around them, and naming a building
# after a prop already standing in the same square would read as a duplicate.
e9.RECIPES = {
    "tavern": {
        "role": "LongTableDeck",
        "why": "bundle §A: 'the Long Table mess (tavern's final form; the portrait wall IS the family's actual playthrough history)'",
        "parts": [
            {"kind": "box", "name": "Long table", "size": (2.10, 0.52, 0.13), "at": (0.0, 0.0, 0.86), "colour": "brass"},
            {"kind": "box", "name": "Portrait wall", "size": (2.30, 0.10, 0.78), "at": (0.0, -1.30, 1.42), "colour": "dome"},
            {"kind": "ring", "name": "Deck ring", "radius": 1.70, "thickness": 0.10, "at": (0.0, 0.0, "top"), "embed": 0.26, "colour": "iron"},
            {"kind": "planter", "name": "Mess green", "at": (1.30, 1.10, 0.0), "colour": "green"},
        ],
    },
    "schoolhouse": {
        "role": "BridgeDeck",
        "why": "bundle §A: 'the Bridge School' — the schoolhouse lineage's berth on the Ark (named for the deck, not the existing bridge-school prop)",
        "parts": [
            {"kind": "box", "name": "Star chart board", "size": (1.20, 0.10, 0.66), "at": (0.0, 1.52, 1.16), "colour": "iron"},
            {"kind": "mast", "name": "Bridge sight", "at": (1.10, 1.05, 0.0), "height": 1.70, "colour": "brass"},
            {"kind": "rack", "name": "Charter tape rack", "at": (-1.20, 1.10, 0.0), "count": 4, "colour": "dome"},
            {"kind": "planter", "name": "Bridge green", "at": (-1.15, -1.25, 0.0), "colour": "green"},
        ],
    },
    "claim-office": {
        "role": "WorldWindow",
        "why": "bundle §B1: 'the world-window bridge where visited-world charters are chosen (the tavern contract board's final form)' — the claim lineage still issues the charters",
        "parts": [
            {"kind": "ring", "name": "World window", "radius": 0.86, "thickness": 0.12, "at": (0.0, 0.0, "top"), "embed": 0.30, "colour": "dome"},
            {"kind": "box", "name": "Charter desk", "size": (1.34, 0.46, 0.66), "at": (0.0, 0.90, 0.33), "colour": "brass"},
            {"kind": "box", "name": "Hull rib", "size": (0.12, 1.40, 1.20), "at": (-1.70, 0.0, 0.60), "colour": "iron"},
            {"kind": "planter", "name": "Window green", "at": (1.50, -1.00, 0.0), "colour": "green"},
        ],
    },
    "stamp-mill": {
        "role": "KeelWorks",
        "why": "the mill lineage builds the hull it now rides in; §B1 'engine decks aft' need a fabrication berth",
        "parts": [
            {"kind": "box", "name": "Keel beam", "size": (3.60, 0.30, 0.20), "at": (0.0, 0.0, 1.24), "colour": "iron"},
            {"kind": "gate", "name": "Frame gantry", "at": (-1.20, 0.0, 0.0), "width": 0.90, "height": 1.30, "colour": "brass"},
            {"kind": "icestack", "name": "Preserved stores", "at": (1.60, 0.0, 0.0), "colour": "ice"},
            {"kind": "planter", "name": "Keel green", "at": (-2.30, 0.0, 0.0), "colour": "green"},
        ],
    },
    "assay-office": {
        "role": "PressHall",
        "why": "bundle §A: 'the Charter Press hall (Assay lineage's endpoint: a great brass-and-teal press with tape-reels and a child-height lever — the lever is the point)' — the hall, not the press prop",
        "parts": [
            {"kind": "box", "name": "Press frame", "size": (1.06, 0.76, 1.30), "at": (0.90, 0.0, 0.65), "colour": "brass"},
            {"kind": "ring", "name": "Tape reel", "radius": 0.34, "thickness": 0.10, "at": (0.90, 0.0, 1.34), "colour": "iron"},
            {"kind": "box", "name": "Child-height lever", "size": (0.09, 0.09, 0.62), "at": (1.62, 0.44, 0.31), "colour": "dome"},
            {"kind": "planter", "name": "Press green", "at": (-1.50, 1.00, 0.0), "colour": "green"},
        ],
    },
    "general-store": {
        "role": "PreserveHold",
        "why": "bundle §A: the final contracts 'don't extract; they PRESERVE' — the store lineage becomes the Ark's preserve hold",
        "parts": [
            {"kind": "silo", "name": "Preserve cask west", "at": (-1.60, -1.00, 0.0), "radius": 0.40, "height": 1.42, "colour": "regolith"},
            {"kind": "silo", "name": "Preserve cask east", "at": (-1.60, 0.30, 0.0), "radius": 0.34, "height": 1.16, "colour": "iron"},
            {"kind": "bed", "name": "Seed bank beds", "at": (1.30, 0.0, 0.0), "rows": 3, "colour": "green"},
            {"kind": "box", "name": "Hold hatch", "size": (0.14, 1.05, 1.15), "at": (2.10, 0.0, 0.58), "colour": "brass"},
        ],
    },
    "dynamo-hall": {
        "role": "EngineDeck",
        "why": "bundle §B1: 'engine decks aft' — the power lineage's final berth, where the engine-glow states already live as props",
        "parts": [
            {"kind": "ring", "name": "Drive ring", "radius": 1.10, "thickness": 0.16, "at": (0.0, 0.0, "top"), "embed": 0.34, "colour": "brass"},
            {"kind": "box", "name": "Thrust housing", "size": (1.70, 0.90, 0.72), "at": (0.0, -1.00, 0.36), "colour": "iron"},
            {"kind": "mast", "name": "Coolant stack", "at": (1.70, 0.90, 0.0), "height": 1.60, "colour": "regolith"},
            {"kind": "planter", "name": "Engine green", "at": (-1.80, 0.95, 0.0), "colour": "green"},
        ],
    },
    "chapel": {
        "role": "PanShrine",
        "why": "bundle §A: 'the Pan Shrine (a small case: the original E1 pan; players who look close see it's the same sprite)'",
        "parts": [
            {"kind": "box", "name": "Shrine case", "size": (0.62, 0.62, 0.86), "at": (0.0, 0.90, 0.43), "colour": "dome"},
            {"kind": "ring", "name": "The pan", "radius": 0.22, "thickness": 0.07, "at": (0.0, 0.90, 0.90), "colour": "brass"},
            {"kind": "box", "name": "Hull rib", "size": (0.12, 1.20, 1.40), "at": (-1.30, 0.0, 0.70), "colour": "iron"},
            {"kind": "planter", "name": "Shrine green", "at": (1.20, -0.95, 0.0), "colour": "green"},
        ],
    },
}


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    report = []
    for name, recipe in e9.RECIPES.items():
        row = e9.build(name, recipe)
        report.append(row)
        print(f"  {name:<15} {row['role']:<16} {row['triangles']:>6} tris "
              f"(+{row['addedTriangles']:>4})  re-export {'OK' if row['reExportByteIdentical'] else 'DRIFT'}")
    (ARTIFACTS / "town-e10-wardrobe.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    drift = [r["building"] for r in report if not r["reExportByteIdentical"]]
    if drift:
        raise SystemExit(f"re-export drift, asset is not reproducible: {drift}")
    print(f"\nE10 wardrobe complete: {len(report)} variants")


if __name__ == "__main__":
    main()
