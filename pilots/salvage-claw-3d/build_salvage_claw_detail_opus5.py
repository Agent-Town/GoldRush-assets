"""THE BOSS DETAIL DUEL — Opus 5 entry: the Salvage King's Claw, high-detail sibling.

Produces `salvage-claw-detail-opus5.glb` beside the shipped `salvage-claw.glb`.
The shipped pack is READ-ONLY; nothing here writes to it.

Follows the shipped dialect idiom: the Dredge Queen detail builder is imported as the
shared library and its module globals are patched before the atlas call, exactly as
`build_salvage_claw.py` does to `build_dredge_queen.py`.

Drop-in contract preserved (rubric: CRAFT LEGALITY):
  nodes          winch, anchor_feet, crown
  meshes         <node>Mesh, one primitive each, all material 0
  morphs         Landing_SprungWinch / Landing_SettledAnchorFeet / Landing_DarkCrown,
                 exactly one per node, default weight 0
  transforms     identity · material one, metallic 0, roughness 0.9, double-sided
  bounds         X span 11.4, base on z=0, centred in X and Y

Raised for the duel: <=45,000 triangles (shipped 10,164) and one 2048 atlas.
"""

from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
QUEEN = ROOT / "assets/pilots/dredge-queen-3d"
REFERENCE = ROOT / "assets/raw/boss-salvage-claw.png"
LANDING_REFERENCE = ROOT / "assets/raw/boss-salvage-claw-damage.png"
BLEND = HERE / "salvage-claw-detail-opus5.blend"
GLB = HERE / "salvage-claw-detail-opus5.glb"

ATLAS_SIZE = 2048
MODEL_DIAMETER = 11.4
TRIANGLE_CEILING = 45_000


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


queen = load("sc_detail_shared_builder", QUEEN / "build_dredge_queen_detail_opus5.py")
kit = queen.kit
REGIONS = queen.REGIONS


def tune_plate_atlas(image: bpy.types.Image) -> None:
    """Keep the source engraving but restore E8's cold silver-teal boss value range.

    Palette law, `specs/epoch-saga/e8-orbital-bundle.md`: silver-and-teal over parchment,
    warm-grey regolith, suit brass, honey habitat warmth — never the Queen's storm oxblood.
    """
    size = image.size[0]
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(size, size, 4)
    tuning = {
        "soot": (0.68, np.array((0.008, 0.014, 0.015))),
        "iron": (0.60, np.array((0.016, 0.032, 0.034))),
        "plate": (0.58, np.array((0.018, 0.038, 0.040))),
        "brass": (0.74, np.array((0.030, 0.014, 0.003))),
        "deck": (0.67, np.array((0.018, 0.014, 0.008))),
        "rope": (0.70, np.array((0.018, 0.010, 0.003))),
        "damage": (0.76, np.array((0.014, 0.004, 0.002))),
        "cargo": (0.72, np.array((0.026, 0.018, 0.006))),
    }
    for name, (factor, tint) in tuning.items():
        u0, v0, u1, v1 = REGIONS[name]
        x0, y0, x1, y1 = (int(value * size) for value in (u0, v0, u1, v1))
        pixels[y0:y1, x0:x1, :3] = np.clip(pixels[y0:y1, x0:x1, :3] * factor + tint, 0.006, 0.62)
    u0, v0, u1, v1 = REGIONS["teal"]
    x0, y0, x1, y1 = (int(value * size) for value in (u0, v0, u1, v1))
    pixels[y0:y1, x0:x1, :3] = np.clip(pixels[y0:y1, x0:x1, :3] * 1.18 + (0.0, 0.018, 0.020), 0.008, 0.72)
    image.pixels.foreach_set(pixels.ravel())
    image.update()
    image.pack()


# --------------------------------------------------------------------------------------
# shared ornament
# --------------------------------------------------------------------------------------


def minaret(
    parts: list[bpy.types.Object],
    name: str,
    at: tuple[float, float],
    base_z: float,
    height: float,
    radius: float,
    material: bpy.types.Material,
    damage_group: str | None = None,
    glow_group: str | None = None,
) -> None:
    """One gothic spire: shaft, banded bulb, spike, teal orb.

    The plate's crown is a skyline of these. The shipped model abstracts them into
    four cones, which is the single biggest fidelity gap on this boss.
    """
    x, y = at
    parts.append(kit.cylinder(f"{name} shaft", radius, height * 0.52, (x, y, base_z + height * 0.26), "iron", material, vertices=8, damage_group=damage_group))
    parts.append(kit.torus(f"{name} shaft ring", radius * 1.22, radius * 0.26, (x, y, base_z + height * 0.52), "brass", material, major_segments=8, damage_group=damage_group))
    parts.append(kit.ico_sphere(f"{name} bulb", radius * 1.34, (x, y, base_z + height * 0.66), "iron", material, damage_group, scale=(1.0, 1.0, 1.15), subdivisions=1))
    parts.append(kit.cone(f"{name} spike", radius * 0.92, 0.01, height * 0.34, (x, y, base_z + height * 0.88), "brass", material, vertices=8, damage_group=damage_group))
    parts.append(
        kit.ico_sphere(
            f"{name} orb",
            radius * 0.44,
            (x, y, base_z + height * 0.60),
            "teal",
            material,
            glow_group or damage_group,
            subdivisions=1,
        )
    )


def pictogram_pendant(
    parts: list[bpy.types.Object],
    name: str,
    angle: float,
    radius: float,
    top_z: float,
    material: bpy.types.Material,
    mark: int,
    damage_group: str | None = None,
) -> None:
    """A hanging claim plaque with a pictogram mark. Pictograms only — never letters.

    Canon: `specs/enemy-rosters-e6-e10.md` — "blank claw-stamp tags; no letters".
    """
    x, y = math.cos(angle) * radius, math.sin(angle) * radius
    facing = (0, 0, angle + math.pi / 2)
    parts.append(kit.beam(f"{name} hanger", (x, y, top_z), (x, y, top_z - 0.26), 0.045, "brass", material, damage_group))
    parts.append(kit.box(f"{name} plaque", (0.62, 0.10, 0.86), (x, y, top_z - 0.72), "brass", material, 0.020, rotation=facing, damage_group=damage_group))
    parts.append(kit.torus(f"{name} plaque ring", 0.10, 0.030, (x, y, top_z - 0.30), "brass", material, rotation=(math.pi / 2, 0, angle), damage_group=damage_group))
    normal = Vector((math.cos(angle), math.sin(angle), 0.0))
    face = normal * 0.075
    tangent = Vector((-math.sin(angle), math.cos(angle), 0.0))
    centre = Vector((x, y, top_z - 0.72)) + face
    if mark % 4 == 0:  # anchor
        parts.append(kit.beam(f"{name} mark stem", tuple(centre + Vector((0, 0, 0.24))), tuple(centre - Vector((0, 0, 0.22))), 0.048, "iron", material, damage_group))
        parts.append(kit.beam(f"{name} mark stock", tuple(centre + tangent * 0.20 + Vector((0, 0, 0.12))), tuple(centre - tangent * 0.20 + Vector((0, 0, 0.12))), 0.042, "iron", material, damage_group))
        parts.append(kit.torus(f"{name} mark fluke", 0.17, 0.036, tuple(centre - Vector((0, 0, 0.16))), "iron", material, rotation=(math.pi / 2, 0, angle), damage_group=damage_group, major_segments=8))
    elif mark % 4 == 1:  # crossed tools
        parts.append(kit.beam(f"{name} mark cross a", tuple(centre + tangent * 0.20 + Vector((0, 0, 0.22))), tuple(centre - tangent * 0.20 - Vector((0, 0, 0.22))), 0.046, "iron", material, damage_group))
        parts.append(kit.beam(f"{name} mark cross b", tuple(centre - tangent * 0.20 + Vector((0, 0, 0.22))), tuple(centre + tangent * 0.20 - Vector((0, 0, 0.22))), 0.046, "iron", material, damage_group))
    elif mark % 4 == 2:  # claw stamp
        parts.append(kit.torus(f"{name} mark stamp", 0.20, 0.042, tuple(centre), "iron", material, rotation=(math.pi / 2, 0, angle), damage_group=damage_group, major_segments=10))
        parts.append(kit.beam(f"{name} mark stamp bar", tuple(centre + tangent * 0.16), tuple(centre - tangent * 0.16), 0.042, "iron", material, damage_group))
    else:  # ledger rule
        for line in range(3):
            z = 0.16 - line * 0.16
            parts.append(kit.beam(f"{name} mark rule {line}", tuple(centre + tangent * 0.19 + Vector((0, 0, z))), tuple(centre - tangent * 0.19 + Vector((0, 0, z))), 0.036, "iron", material, damage_group))


# --------------------------------------------------------------------------------------
# crown — the descending city-crown
# --------------------------------------------------------------------------------------

# The four legs sit at 45 degrees, so the crown — not the feet — sets the X extent
# the normaliser scales by. The vertical stack is tuned against that so the exported
# height lands on the shipped 10.031203 rather than towering over its own footprint.
PROMENADE_R = 4.42
BELLY_Z = 3.10
DECK_Z = 4.20


def build_crown(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    glow = "LandingCrownGlow"
    upper = "LandingCrownUpper"

    # Saucer read first, palace second — the plate is a disc seen from below.
    parts.append(kit.cone("Armoured crown belly", 3.36, 1.20, 1.34, (0, 0, BELLY_Z - 0.30), "plate", material, vertices=28))
    parts.append(kit.cylinder("Crown hull drum", 4.06, 0.62, (0, 0, DECK_Z - 0.62), "iron", material, vertices=32))
    parts.append(kit.cone("Crown flare", PROMENADE_R, 4.06, 0.42, (0, 0, DECK_Z - 0.90), "plate", material, vertices=32))
    parts.append(kit.cylinder("Promenade deck", PROMENADE_R, 0.20, (0, 0, DECK_Z), "deck", material, vertices=32))
    parts.append(kit.torus("Promenade brass rim", PROMENADE_R, 0.11, (0, 0, DECK_Z + 0.04), "brass", material, major_segments=32))
    parts.append(kit.torus("Lower brass belt", 4.02, 0.13, (0, 0, DECK_Z - 0.70), "brass", material, major_segments=30))
    parts.append(kit.torus("Belly brass belt", 3.06, 0.10, (0, 0, BELLY_Z - 0.62), "brass", material, major_segments=26))

    # Hull ribs and rivet courses: the plate's saucer is plated, not smooth.
    for rib in range(24):
        angle = math.tau * rib / 24
        x, y = math.cos(angle), math.sin(angle)
        parts.append(kit.beam(f"Crown hull rib {rib}", (x * 3.30, y * 3.30, BELLY_Z - 0.86), (x * 4.04, y * 4.04, DECK_Z - 0.30), 0.070, "brass", material))
    for rivet in range(30):
        angle = math.tau * rivet / 30
        parts.append(kit.cylinder(f"Crown belt rivet {rivet}", 0.045, 0.10, (math.cos(angle) * 4.06, math.sin(angle) * 4.06, DECK_Z - 0.44), "brass", material, vertices=6, rotation=(math.pi / 2, 0, angle), bevel=0))

    # Promenade rail.
    rail = kit.arc_points((0, 0, 0), PROMENADE_R - 0.10, 0, math.tau, 32, plane="xy")
    rail = [(p[0], p[1], DECK_Z + 0.52) for p in rail]
    kit.polyline(parts, "Promenade rail", rail, 0.055, "brass", material)
    for post in range(24):
        angle = math.tau * post / 24
        x, y = math.cos(angle) * (PROMENADE_R - 0.10), math.sin(angle) * (PROMENADE_R - 0.10)
        parts.append(kit.beam(f"Promenade post {post}", (x, y, DECK_Z + 0.10), (x, y, DECK_Z + 0.54), 0.042, "brass", material))

    # Palace: window drum, tracery, steep roof, lantern.
    parts.append(kit.cylinder("Crown armoured base", 2.34, 0.66, (0, 0, DECK_Z + 0.44), "iron", material, vertices=24, damage_group=upper))
    parts.append(kit.cylinder("Crown teal window drum", 2.16, 0.92, (0, 0, DECK_Z + 1.30), "teal", material, vertices=24, damage_group=glow))
    for mullion in range(20):
        angle = math.tau * mullion / 20
        x, y = math.cos(angle) * 2.20, math.sin(angle) * 2.20
        parts.append(kit.beam(f"Crown mullion {mullion}", (x, y, DECK_Z + 0.82), (x, y, DECK_Z + 1.78), 0.052, "brass", material, upper))
    parts.append(kit.torus("Crown lower tracery", 2.24, 0.10, (0, 0, DECK_Z + 0.82), "brass", material, major_segments=24, damage_group=upper))
    parts.append(kit.torus("Crown upper tracery", 2.24, 0.10, (0, 0, DECK_Z + 1.78), "brass", material, major_segments=24, damage_group=upper))
    parts.append(kit.cone("Crown steep roof", 2.30, 0.34, 1.20, (0, 0, DECK_Z + 2.38), "plate", material, vertices=24, damage_group=upper))
    for rib in range(12):
        angle = math.tau * rib / 12
        parts.append(
            kit.beam(
                f"Crown gothic rib {rib}",
                (math.cos(angle) * 2.26, math.sin(angle) * 2.26, DECK_Z + 1.82),
                (math.cos(angle) * 0.30, math.sin(angle) * 0.30, DECK_Z + 2.90),
                0.062,
                "brass",
                material,
                upper,
            )
        )
    parts.append(kit.cylinder("Crown lantern", 0.46, 0.50, (0, 0, DECK_Z + 3.10), "teal", material, vertices=14, damage_group=glow))
    parts.append(kit.torus("Crown lantern cage", 0.50, 0.055, (0, 0, DECK_Z + 3.10), "brass", material, major_segments=14, damage_group=upper))
    parts.append(kit.cone("Crown lantern cap", 0.52, 0.02, 0.46, (0, 0, DECK_Z + 3.45), "brass", material, vertices=14, damage_group=upper))

    # The front gable the plate centres its face on.
    parts.append(kit.triangle_panel("Front crown gable", ((-0.98, -2.26, DECK_Z + 0.82), (0.98, -2.26, DECK_Z + 0.82), (0.0, -2.26, DECK_Z + 2.42)), 0.14, "iron", material, upper))
    parts.append(kit.cylinder("Front gable teal eye", 0.34, 0.10, (0, -2.36, DECK_Z + 1.52), "teal", material, vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=glow))
    parts.append(kit.torus("Front gable eye rim", 0.38, 0.045, (0, -2.36, DECK_Z + 1.52), "brass", material, rotation=(math.pi / 2, 0, 0), major_segments=12, damage_group=upper))

    # Perimeter spire skyline — the plate's defining silhouette. Density is the whole
    # point: the plate reads as a cathedral horizon, so an alternating tall/short ring
    # of eighteen plus an inner ring of slender ones beats a handful of fatter cones.
    # Everything here sits inside the promenade radius, so it cannot disturb the
    # X extent the normaliser scales by.
    for turret in range(18):
        angle = math.tau * turret / 18
        radius = 3.58 if turret % 2 == 0 else 3.96
        height = 1.94 if turret % 2 == 0 else 1.38
        minaret(
            parts,
            f"Perimeter turret {turret}",
            (math.cos(angle) * radius, math.sin(angle) * radius),
            DECK_Z + 0.10,
            height,
            0.21 if turret % 2 == 0 else 0.165,
            material,
            damage_group=upper,
            glow_group=glow,
        )
    for inner in range(8):
        angle = math.tau * inner / 8 + math.radians(22.5)
        minaret(parts, f"Inner spire {inner}", (math.cos(angle) * 3.06, math.sin(angle) * 3.06), DECK_Z + 0.34, 1.14, 0.135, material, damage_group=upper, glow_group=glow)
    for corner in range(4):
        angle = math.tau * corner / 4 + math.radians(45)
        minaret(parts, f"Corner spire {corner}", (math.cos(angle) * 2.62, math.sin(angle) * 2.62), DECK_Z + 0.66, 2.42, 0.25, material, damage_group=upper, glow_group=glow)

    # Roof dormers and tracery: the plate's roof is broken by gabled lights, not smooth.
    for dormer in range(6):
        angle = math.tau * dormer / 6 + math.radians(30)
        x, y = math.cos(angle) * 1.42, math.sin(angle) * 1.42
        parts.append(kit.box(f"Roof dormer {dormer}", (0.44, 0.36, 0.42), (x, y, DECK_Z + 2.16), "iron", material, 0.014, rotation=(0, 0, angle), damage_group=upper))
        parts.append(kit.cone(f"Roof dormer cap {dormer}", 0.30, 0.02, 0.30, (x, y, DECK_Z + 2.50), "brass", material, vertices=6, damage_group=upper))
        parts.append(kit.cylinder(f"Roof dormer light {dormer}", 0.13, 0.08, (math.cos(angle) * 1.60, math.sin(angle) * 1.60, DECK_Z + 2.16), "teal", material, vertices=8, rotation=(math.pi / 2, 0, angle), bevel=0, damage_group=glow))
    for ring, (radius, z) in enumerate(((2.02, DECK_Z + 2.02), (1.34, DECK_Z + 2.62))):
        parts.append(kit.torus(f"Roof tracery ring {ring}", radius, 0.055, (0, 0, z), "brass", material, major_segments=20, damage_group=upper))

    # Hanging claim pendants. They must hang in open air BELOW the rim, not tucked
    # against the hull — on the plate this row of plaques is a signature read, and
    # the first pass lost it entirely behind the saucer's own silhouette.
    for pendant in range(8):
        angle = math.tau * pendant / 8 + math.radians(22.5)
        pictogram_pendant(parts, f"Claim pendant {pendant}", angle, 4.16, BELLY_Z + 0.16, material, pendant)

    # Central keel eye and finial hanging under the belly.
    parts.append(kit.ico_sphere("Central keel dome", 1.02, (0, 0, BELLY_Z - 1.06), "iron", material, scale=(1.0, 1.0, 0.74), subdivisions=2))
    parts.append(kit.torus("Central keel ring", 1.00, 0.090, (0, 0, BELLY_Z - 0.94), "brass", material, major_segments=18))
    parts.append(kit.cylinder("Central keel eye", 0.40, 0.30, (0, 0, BELLY_Z - 1.52), "teal", material, vertices=14, damage_group=glow))
    parts.append(kit.cone("Keel brass finial", 0.34, 0.02, 0.86, (0, 0, BELLY_Z - 2.06), "brass", material, vertices=12))

    # Hidden: shutters inside the glass drum, and the two rope ladders the crew
    # descends in good order at the warm quit.
    for shutter in range(8):
        angle = math.tau * shutter / 8
        x, y = math.cos(angle) * 1.72, math.sin(angle) * 1.72
        parts.append(kit.box(f"Hidden crown shutter {shutter}", (0.52, 0.12, 0.74), (x, y, DECK_Z + 1.30), "soot", material, 0.004, rotation=(0, 0, angle + math.pi / 2), damage_group=f"LandingShutter{shutter}"))
    for ladder in range(2):
        side = -1 if ladder == 0 else 1
        x = side * 2.30
        for rail_index, offset in enumerate((-0.22, 0.22)):
            parts.append(kit.beam(f"Hidden ladder rail {ladder} {rail_index}", (x + offset, 0.30, BELLY_Z - 0.20), (x + offset, 0.30, BELLY_Z - 2.10), 0.045, "rope", material, f"LandingLadder{ladder}"))
        for rung in range(6):
            z = BELLY_Z - 0.40 - rung * 0.32
            parts.append(kit.beam(f"Hidden ladder rung {ladder} {rung}", (x - 0.22, 0.30, z), (x + 0.22, 0.30, z), 0.036, "rope", material, f"LandingLadder{ladder}"))
    return parts


# --------------------------------------------------------------------------------------
# winch — the paired cable drums
# --------------------------------------------------------------------------------------


def build_winch(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    # Below the belly cone's skirt, so the drum band reads in open space the way the
    # plate stages it — flanking the central pendant, not swallowed by the hull.
    drum_z = BELLY_Z - 0.90

    parts.append(kit.box("Winch armoured gantry", (5.40, 1.34, 0.44), (0, 0, drum_z + 0.86), "iron", material, 0.045))
    parts.append(kit.box("Winch lower brace", (5.00, 1.10, 0.26), (0, 0, drum_z - 0.74), "iron", material, 0.035))
    for side, label in ((-1, "Port"), (1, "Starboard")):
        group = f"LandingWinch{label}"
        centre_x = side * 1.66
        parts.append(kit.cylinder(f"{label} rope drum", 0.62, 1.86, (centre_x, 0, drum_z), "plate", material, vertices=18, rotation=(0, math.pi / 2, 0), bevel=0, damage_group=group))
        for collar in range(5):
            x = centre_x - 0.82 + collar * 0.41
            parts.append(kit.torus(f"{label} drum collar {collar}", 0.66, 0.065, (x, 0, drum_z), "brass", material, rotation=(0, math.pi / 2, 0), major_segments=16, damage_group=group))
        # Spooled cable, drawn as courses rather than a smooth cylinder.
        for course in range(7):
            x = centre_x - 0.72 + course * 0.24
            parts.append(kit.torus(f"{label} drum cable {course}", 0.70, 0.048, (x, 0, drum_z), "rope", material, rotation=(0, math.pi / 2, 0), major_segments=14, damage_group=group))
        parts.append(kit.cylinder(f"{label} winch hub", 0.24, 2.06, (centre_x, 0, drum_z), "teal", material, vertices=12, rotation=(0, math.pi / 2, 0), bevel=0, damage_group=group))
        for leg in (-1, 1):
            parts.append(kit.beam(f"{label} A-frame {leg}", (centre_x + leg * 0.30, 0, drum_z + 0.82), (centre_x + leg * 0.96, 0, drum_z - 0.66), 0.13, "iron", material, group))
        parts.append(kit.torus(f"{label} drum flange outer", 0.74, 0.085, (centre_x + side * 1.00, 0, drum_z), "brass", material, rotation=(0, math.pi / 2, 0), major_segments=16, damage_group=group))
        parts.append(kit.cylinder(f"{label} brake wheel", 0.40, 0.14, (centre_x + side * 1.14, 0, drum_z), "brass", material, vertices=14, rotation=(0, math.pi / 2, 0), damage_group=group))
        for spoke in range(6):
            angle = math.tau * spoke / 6
            parts.append(kit.beam(f"{label} brake spoke {spoke}", (centre_x + side * 1.16, 0, drum_z), (centre_x + side * 1.16, math.cos(angle) * 0.38, drum_z + math.sin(angle) * 0.38), 0.040, "brass", material, group))

    parts.append(kit.box("Winch central gearbox", (1.10, 1.02, 1.06), (0, 0, drum_z), "iron", material, 0.040))
    parts.append(kit.torus("Winch central gauge rim", 0.36, 0.055, (0, -0.54, drum_z + 0.16), "brass", material, rotation=(math.pi / 2, 0, 0), major_segments=14))
    parts.append(kit.cylinder("Winch central gauge glass", 0.31, 0.10, (0, -0.55, drum_z + 0.16), "teal", material, vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0))
    for pipe, x in enumerate((-0.62, 0.62)):
        parts.append(kit.cylinder(f"Winch feed pipe {pipe}", 0.11, 1.28, (x, 0.46, drum_z - 0.10), "soot", material, vertices=8, rotation=(0, math.pi / 2, 0)))
    for shard, at in enumerate(((-0.34, 0.0, drum_z - 0.10), (0.30, 0.10, drum_z - 0.14), (0.02, -0.12, drum_z - 0.18))):
        parts.append(kit.box(f"Hidden sprung winch part {shard}", (0.34, 0.09, 0.12), at, "damage", material, 0.003, damage_group=f"LandingWinchShard{shard}"))
    return parts


# --------------------------------------------------------------------------------------
# anchor feet — four grapple legs with curved talons
# --------------------------------------------------------------------------------------


def build_anchor_feet(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    for foot in range(4):
        angle = math.tau * foot / 4 + math.radians(45)
        dx, dy = math.cos(angle), math.sin(angle)
        group = f"LandingFoot{foot}"
        attach = Vector((dx * 3.10, dy * 3.10, BELLY_Z - 0.42))
        elbow = Vector((dx * 3.78, dy * 3.78, 1.86))
        hub = Vector((dx * 4.12, dy * 4.12, 1.10))

        parts.append(kit.ico_sphere(f"Anchor gearbox {foot}", 0.70, tuple(attach), "iron", material, group, subdivisions=2))
        parts.append(kit.torus(f"Anchor gearbox rim {foot}", 0.72, 0.085, tuple(attach), "brass", material, rotation=(math.pi / 2, 0, angle), damage_group=group, major_segments=14))
        parts.append(kit.swept_tube(f"Anchor armoured arm {foot}", [tuple(attach), tuple(attach.lerp(elbow, 0.5)), tuple(elbow), tuple(hub)], [0.34, 0.31, 0.29, 0.33], "iron", material, sides=8, damage_group=group))
        parts.append(kit.beam(f"Anchor arm brass edge {foot}", tuple(attach + Vector((0, 0, -0.24))), tuple(elbow + Vector((0, 0, -0.20))), 0.11, "brass", material, group))
        parts.append(kit.ico_sphere(f"Anchor elbow {foot}", 0.36, tuple(elbow), "brass", material, group, subdivisions=1))
        parts.append(kit.cylinder(f"Anchor hub {foot}", 0.44, 0.62, tuple(hub), "iron", material, vertices=14, damage_group=group))
        parts.append(kit.torus(f"Anchor hub collar {foot}", 0.47, 0.070, tuple(hub + Vector((0, 0, 0.20))), "brass", material, major_segments=14, damage_group=group))
        kit.lens(parts, f"Anchor bearing {foot}", 0.20, tuple(hub + Vector((-dy * 0.46, dx * 0.46, 0.06))), material, rotation=(math.pi / 2, 0, angle), damage_group=group)

        # Long suspension cables from the promenade rim down to the hub. On the plate
        # these run the full height of the machine and are most of what says "hanging".
        for rig, offset in enumerate((-0.52, 0.52)):
            top = Vector((dx * 4.24 - dy * offset, dy * 4.24 + dx * offset, DECK_Z + 0.16))
            parts.append(kit.beam(f"Anchor high rig {foot} {rig}", tuple(top), tuple(hub + Vector((-dy * offset, dx * offset, 0.30))), 0.048, "rope", material, group))
            parts.append(kit.torus(f"Anchor rig eye {foot} {rig}", 0.11, 0.032, tuple(top), "brass", material, rotation=(math.pi / 2, 0, angle), damage_group=group, major_segments=8))
        kit.chain_run(parts, f"Anchor haul chain {foot}", tuple(Vector((dx * 2.94, dy * 2.94, BELLY_Z - 0.86))), tuple(hub + Vector((0, 0, 0.44))), 8, 0.082, "rope", material, group)
        kit.chain_run(parts, f"Anchor slack chain {foot}", tuple(hub + Vector((-dy * 0.30, dx * 0.30, 0.24))), tuple(hub + Vector((dx * 0.52 - dy * 0.30, dy * 0.52 + dx * 0.30, -0.42))), 5, 0.075, "rope", material, group)

        # Three curved talons per foot. Swept tubes, so they read as grapples that
        # could actually close on regolith rather than as flippers.
        for toe in range(3):
            spread = (toe - 1) * math.radians(34)
            tdx, tdy = math.cos(angle + spread), math.sin(angle + spread)
            reach = 1.0 if toe == 1 else 0.94
            talon = (
                (0.30, 1.02, 0.185),
                (0.72, 0.74, 0.170),
                (1.10, 0.42, 0.148),
                (1.36, 0.16, 0.118),
                (1.50, 0.02, 0.074),
                (1.58, 0.00, 0.024),
            )
            points = [
                (hub.x + tdx * out * reach, hub.y + tdy * out * reach, max(0.0, hub.z - (1.10 - z)))
                for out, z, _ in talon
            ]
            radii = [radius for _, _, radius in talon]
            parts.append(kit.swept_tube(f"Anchor talon {foot} {toe}", points, radii, "iron", material, sides=8, damage_group=group))
            for band, station in enumerate((1, 3)):
                out, z, radius = talon[station]
                nxt = talon[station + 1]
                centre = points[station]
                direction = Vector((tdx * (nxt[0] - out), tdy * (nxt[0] - out), -(z - nxt[1])))
                parts.append(
                    kit.torus(
                        f"Anchor talon band {foot} {toe} {band}",
                        radius * 1.24,
                        radius * 0.30,
                        centre,
                        "brass",
                        material,
                        rotation=tuple(direction.to_track_quat("Z", "Y").to_euler()),
                        damage_group=group,
                        major_segments=8,
                    )
                )
    return parts


# --------------------------------------------------------------------------------------
# morphs — the landed civic-salvage state
# --------------------------------------------------------------------------------------


def group_center(obj: bpy.types.Object, group_name: str) -> Vector:
    points = [obj.data.vertices[index].co for index in kit.group_vertex_indices(obj, group_name)]
    assert points, f"missing group {obj.name}:{group_name}"
    return sum(points, Vector()) / len(points)


def add_landing_shapes(winch, anchor_feet, crown) -> None:
    winch.shape_key_add(name="Basis")
    sprung = winch.shape_key_add(name="Landing_SprungWinch")
    for group_name, angle, shift in (
        ("LandingWinchPort", math.radians(-11), Vector((-0.08, -0.06, -0.22))),
        ("LandingWinchStarboard", math.radians(13), Vector((0.10, 0.04, -0.14))),
    ):
        pivot = group_center(winch, group_name)
        for index in kit.group_vertex_indices(winch, group_name):
            co = sprung.data[index].co
            kit.rotate_y(co, pivot, angle)
            co += shift
    for shard, movement in enumerate((Vector((-1.05, -0.52, -0.72)), Vector((1.12, -0.44, -0.58)), Vector((0.22, -0.78, -0.90)))):
        for index in kit.group_vertex_indices(winch, f"LandingWinchShard{shard}"):
            sprung.data[index].co += movement

    anchor_feet.shape_key_add(name="Basis")
    settled = anchor_feet.shape_key_add(name="Landing_SettledAnchorFeet")
    for foot in range(4):
        group_name = f"LandingFoot{foot}"
        centre = group_center(anchor_feet, group_name)
        direction = Vector((centre.x, centre.y, 0)).normalized()
        for index in kit.group_vertex_indices(anchor_feet, group_name):
            co = settled.data[index].co
            falloff = max(0.0, min(1.0, (2.80 - co.z) / 2.80))
            co.x += direction.x * 0.48 * falloff
            co.y += direction.y * 0.48 * falloff
            co.z = max(0.0, co.z - 0.22 * falloff)

    crown.shape_key_add(name="Basis")
    dark = crown.shape_key_add(name="Landing_DarkCrown")
    for index in kit.group_vertex_indices(crown, "LandingCrownGlow"):
        co = dark.data[index].co
        co.x *= 0.80
        co.y *= 0.80
        co.z -= 0.10
    for index in kit.group_vertex_indices(crown, "LandingCrownUpper"):
        dark.data[index].co.z -= 0.12
    for shutter in range(8):
        group_name = f"LandingShutter{shutter}"
        centre = group_center(crown, group_name)
        direction = Vector((centre.x, centre.y, 0)).normalized()
        for index in kit.group_vertex_indices(crown, group_name):
            dark.data[index].co += direction * 0.47
    for ladder in range(2):
        for index in kit.group_vertex_indices(crown, f"LandingLadder{ladder}"):
            dark.data[index].co += Vector((0, -0.32, -1.98))

    for obj in (winch, anchor_feet, crown):
        obj.active_shape_key_index = 0
        for key in obj.data.shape_keys.key_blocks:
            key.value = 0.0


def strip_micro_bevels(parts: list[bpy.types.Object]) -> None:
    """Spend triangles on silhouette, not on edge loops the run camera cannot resolve."""
    detail_words = ("post", "mullion", "rail", "brace", "edge", "cable", "rung", "mark", "rib", "rig", "rivet", "spoke", "hanger", "collar")
    for part in parts:
        if not any(word in part.name.lower() for word in detail_words):
            continue
        for modifier in list(part.modifiers):
            if modifier.type == "BEVEL":
                part.modifiers.remove(modifier)


def main() -> None:
    kit.reset_scene()

    # Shipped dialect idiom: patch the shared builder's globals before the atlas call.
    queen.REFERENCE = REFERENCE
    queen.DAMAGE_REFERENCE = LANDING_REFERENCE
    queen.ATLAS_SIZE = ATLAS_SIZE
    atlas, source_hashes = queen.create_atlas()
    atlas.name = "SalvageClawDetailOpus5Atlas"
    tune_plate_atlas(atlas)
    material = kit.create_material("SalvageClawDetailOpus5Material", atlas)

    groups = {
        "winch": build_winch(material),
        "anchor_feet": build_anchor_feet(material),
        "crown": build_crown(material),
    }
    for parts in groups.values():
        strip_micro_bevels(parts)
    part_counts = {name: len(parts) for name, parts in groups.items()}

    winch = kit.join_component("winch", groups["winch"], material, REGIONS)
    anchor_feet = kit.join_component("anchor_feet", groups["anchor_feet"], material, REGIONS)
    crown = kit.join_component("crown", groups["crown"], material, REGIONS)
    objects = (winch, anchor_feet, crown)

    kit.normalize_base_center(objects, 0, MODEL_DIAMETER)
    add_landing_shapes(*objects)

    minimum, maximum = kit.world_bounds(objects)
    triangles = kit.triangle_count(objects)
    per_component = {obj.name: sum(len(p.vertices) - 2 for p in obj.data.polygons) for obj in objects}
    assert triangles <= TRIANGLE_CEILING, f"triangle budget exceeded: {triangles}"
    assert abs((maximum.x - minimum.x) - MODEL_DIAMETER) < 0.01
    assert abs((maximum.x + minimum.x) * 0.5) < 0.001
    assert abs((maximum.y + minimum.y) * 0.5) < 0.001
    assert abs(minimum.z) < 0.001
    assert len({slot.material.name for obj in objects for slot in obj.material_slots if slot.material}) == 1
    kit.export(objects, BLEND, GLB)

    print(json.dumps({
        "blend": str(BLEND),
        "glb": str(GLB),
        "sha256": hashlib.sha256(GLB.read_bytes()).hexdigest(),
        "sourcePlates": {
            str(REFERENCE.relative_to(ROOT)): source_hashes["intact"],
            str(LANDING_REFERENCE.relative_to(ROOT)): source_hashes["damage"],
        },
        "stateLaw": "intact descending body morphs to a landed civic-salvage state; no people are included",
        "components": [obj.name for obj in objects],
        "landingMorphs": [obj.data.shape_keys.key_blocks[1].name for obj in objects],
        "atlas": ATLAS_SIZE,
        "parts": part_counts,
        "triangles": triangles,
        "trianglesPerComponent": per_component,
        "triangleCeiling": TRIANGLE_CEILING,
        "boundsBlender": {
            "min": [round(value, 6) for value in minimum],
            "max": [round(value, 6) for value in maximum],
        },
    }, indent=2))


if __name__ == "__main__":
    main()
