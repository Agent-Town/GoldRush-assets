"""THE BOSS DETAIL DUEL — Opus 5 entry: the Dredge Queen, high-detail sibling.

Produces `dredge-queen-detail-opus5.glb` beside the shipped `dredge-queen.glb`.
The shipped pack is READ-ONLY; nothing here writes to it.

Drop-in contract preserved from the shipped model (rubric: CRAFT LEGALITY):
  nodes, in order          claw, paddle_port, paddle_starboard, hold
  meshes                   <node>Mesh, one primitive each, all material 0
  morphs                   exactly one per node, default weight 0, shipped names
  node transforms          identity (vertex-level normalisation, never obj.scale)
  material                 one, metallic 0, roughness 0.9, double-sided, non-emissive
  images                   one embedded PNG
  bounds                   X span 8.0, base on z=0, centred in X and Y

Raised for the duel: <=45,000 triangles (shipped 11,832) and one 2048 atlas
(shipped 1024) — 4x the texel area at the same one-material/one-image binding,
so the engraved house style gets finer line density without a second draw call.
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
REFERENCE = ROOT / "assets/raw/boss-dredge-queen.png"
DAMAGE_REFERENCE = ROOT / "assets/raw/boss-dredge-queen-damage.png"
BLEND = HERE / "dredge-queen-detail-opus5.blend"
GLB = HERE / "dredge-queen-detail-opus5.glb"

ATLAS_SIZE = 2048
MODEL_LENGTH = 8.0
TRIANGLE_CEILING = 45_000


def load_kit():
    path = HERE / "detail_opus5_kit.py"
    spec = importlib.util.spec_from_file_location("dq_detail_kit", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["dq_detail_kit"] = module
    spec.loader.exec_module(module)
    return module


kit = load_kit()

REGIONS = {
    "soot": (0.02, 0.02, 0.20, 0.47),
    "iron": (0.23, 0.02, 0.41, 0.47),
    "brass": (0.44, 0.02, 0.61, 0.47),
    "deck": (0.64, 0.02, 0.78, 0.47),
    "teal": (0.81, 0.02, 0.89, 0.47),
    "damage": (0.92, 0.02, 0.98, 0.47),
    "plate": (0.02, 0.52, 0.53, 0.98),
    "sail": (0.56, 0.52, 0.78, 0.98),
    "rope": (0.81, 0.52, 0.89, 0.98),
    "cargo": (0.92, 0.52, 0.98, 0.98),
}


# --------------------------------------------------------------------------------------
# atlas — sampled from the owner-ratified plate, painted at 2048
# --------------------------------------------------------------------------------------


def region_pixels(region: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return tuple(int(value * ATLAS_SIZE) for value in region)


def create_atlas() -> tuple[bpy.types.Image, dict[str, str]]:
    source = bpy.data.images.load(str(REFERENCE), check_existing=False)
    pixels = np.array(source.pixels[:], dtype=np.float32).reshape(source.size[1], source.size[0], 4)
    colors = pixels[:, :, :3]
    luminance = colors.mean(axis=2)
    saturation = colors.max(axis=2) - colors.min(axis=2)
    dark = kit.sampled_color(colors, (luminance > 0.015) & (luminance < 0.14), (0.035, 0.030, 0.022))
    warm = kit.sampled_color(
        colors,
        (colors[:, :, 0] > colors[:, :, 1] * 1.08)
        & (colors[:, :, 1] > colors[:, :, 2] * 1.12)
        & (luminance > 0.12)
        & (luminance < 0.48),
        (0.34, 0.20, 0.07),
    )
    rust = kit.sampled_color(
        colors,
        (colors[:, :, 0] > colors[:, :, 1] * 1.30) & (colors[:, :, 1] > colors[:, :, 2] * 1.05) & (saturation > 0.09),
        (0.34, 0.075, 0.028),
    )
    teal = kit.sampled_color(
        colors,
        (colors[:, :, 1] > colors[:, :, 0] * 1.18) & (colors[:, :, 2] > colors[:, :, 0] * 1.18) & (saturation > 0.06),
        (0.025, 0.36, 0.38),
    )
    palette = {
        "soot": np.clip(dark * 0.50, 0.010, 0.060),
        "iron": np.clip(dark * 0.58 + warm * 0.34 + 0.015, 0.035, 0.22),
        "brass": np.clip(warm * 0.88 + 0.025, 0.09, 0.55),
        "deck": np.clip(warm * 0.54 + rust * 0.26 + 0.045, 0.06, 0.36),
        "teal": np.clip(teal * 1.12, 0.02, 0.62),
        "damage": np.clip(rust * 0.72 + np.array((0.16, 0.025, 0.012)), 0.03, 0.48),
        "sail": np.clip(rust * 0.74 + np.array((0.08, 0.012, 0.008)), 0.03, 0.40),
        "rope": np.clip(warm * 0.54 + np.array((0.10, 0.055, 0.012)), 0.05, 0.50),
        "cargo": np.clip(rust * 0.42 + warm * 0.42 + 0.018, 0.05, 0.44),
    }
    atlas = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    atlas[:, :, :3] = palette["soot"]
    rng = np.random.default_rng(517)

    # The plate tile is a real crop of the approved engraving. At 2048 the quantiser can
    # carry 600x840 of the plate's own line density instead of the shipped 300x420.
    x0, y0, x1, y1 = region_pixels(REGIONS["plate"])
    crop = colors[
        int(source.size[1] * 0.09):int(source.size[1] * 0.88),
        int(source.size[0] * 0.08):int(source.size[0] * 0.95),
    ]
    painted = kit.resized_nearest(kit.resized_nearest(crop, 600, 840), y1 - y0, x1 - x0)
    ink = 1.0 - np.clip((painted.mean(axis=2) - 0.025) / 0.40, 0.0, 1.0)
    plate_base = palette["iron"] * 0.76 + palette["brass"] * 0.24
    engraved = plate_base[None, None, :] * (1.08 - ink[:, :, None] * 0.55)
    warm_mask = (painted[:, :, 0] > painted[:, :, 2] * 1.28) & (ink > 0.20)
    engraved[warm_mask] = engraved[warm_mask] * 0.75 + palette["brass"] * 0.17
    engraved += rng.normal(0, 0.008, (y1 - y0, x1 - x0, 1))
    atlas[y0:y1, x0:x1, :3] = np.clip(engraved, 0.008, 0.34)

    # Mark spacings are doubled with the atlas so the engraving reads at the same
    # world scale as the shipped model rather than becoming twice as fine.
    for name, region in REGIONS.items():
        if name == "plate":
            continue
        x0, y0, x1, y1 = region_pixels(region)
        base = palette[name]
        noise = rng.normal(0, 0.008 if name != "teal" else 0.004, (y1 - y0, x1 - x0, 1))
        atlas[y0:y1, x0:x1, :3] = np.clip(base + noise, 0.008, 0.72)
        if name in {"soot", "iron", "brass", "deck", "damage", "sail", "cargo"}:
            height = y1 - y0
            spacing = 34 if name in {"iron", "brass"} else 46
            for offset in range(-height, x1 - x0, spacing):
                for yy in range(y0, y1):
                    xx = x0 + offset + (yy - y0)
                    if x0 <= xx < x1:
                        atlas[yy, xx:min(xx + 4, x1), :3] *= 0.58
        if name in {"iron", "brass", "deck"}:
            for yy in range(y0 + 24, y1, 58):
                for xx in range(x0 + 24, x1, 58):
                    atlas[yy - 4:yy + 6, xx - 4:xx + 6, :3] *= 0.46
        if name == "sail":
            for yy in range(y0 + 36, y1, 52):
                atlas[yy:yy + 4, x0:x1, :3] *= 0.62
        if name == "teal":
            for yy in range(y0 + 14, y1, 30):
                atlas[yy:yy + 4, x0:x1, :3] = np.clip(base * 1.35, 0, 0.78)

    # The source plate is storm-dark. Lift its baked albedo, not the material,
    # so engraved detail survives the high gameplay camera without emission.
    atlas[:, :, :3] = np.clip(atlas[:, :, :3] * 1.34 + 0.012, 0.008, 0.78)

    image = bpy.data.images.new("DredgeQueenDetailOpus5Atlas", ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(atlas.ravel())
    image.pack()
    return image, {
        "intact": hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
        "damage": hashlib.sha256(DAMAGE_REFERENCE.read_bytes()).hexdigest(),
    }


# --------------------------------------------------------------------------------------
# hull stations — one armoured corsair sheer, split at the component seam
# --------------------------------------------------------------------------------------

BOW_STATIONS = [
    (-4.32, 0.13, 0.44, 1.36),
    (-4.02, 0.52, 0.28, 1.33),
    (-3.58, 1.05, 0.16, 1.30),
    (-3.02, 1.52, 0.07, 1.27),
    (-2.36, 1.83, 0.02, 1.24),
    (-1.66, 1.99, 0.00, 1.23),
    (-1.02, 2.05, 0.00, 1.22),
]
AFT_STATIONS = [
    (-1.10, 2.04, 0.00, 1.22),
    (-0.30, 2.07, 0.00, 1.22),
    (0.52, 2.06, 0.00, 1.24),
    (1.34, 2.02, 0.00, 1.27),
    (2.14, 1.95, 0.02, 1.31),
    (2.86, 1.86, 0.07, 1.35),
    (3.46, 1.74, 0.14, 1.39),
    (3.92, 1.62, 0.24, 1.42),
]


def sheer_at(x: float) -> float:
    """Deck height along the hull, interpolated from the station table."""
    table = BOW_STATIONS + AFT_STATIONS[1:]
    for (xa, _, _, da), (xb, _, _, db) in zip(table, table[1:]):
        if xa <= x <= xb:
            t = (x - xa) / (xb - xa)
            return da + (db - da) * t
    return table[-1][3]


def half_beam_at(x: float) -> float:
    table = BOW_STATIONS + AFT_STATIONS[1:]
    for (xa, ba, _, _), (xb, bb, _, _) in zip(table, table[1:]):
        if xa <= x <= xb:
            t = (x - xa) / (xb - xa)
            return ba + (bb - ba) * t
    return table[-1][1]


def add_bulwark(
    parts: list[bpy.types.Object],
    prefix: str,
    xs: list[float],
    material: bpy.types.Material,
    height: float = 0.34,
    damage_group: str | None = None,
) -> None:
    """Rail cap, mid-rail and balusters following the sheer — the plate's deck edge."""
    for side in (-1, 1):
        top = [(x, side * (half_beam_at(x) * 0.86 + 0.03), sheer_at(x) + height) for x in xs]
        mid = [(x, side * (half_beam_at(x) * 0.86 + 0.03), sheer_at(x) + height * 0.52) for x in xs]
        kit.polyline(parts, f"{prefix} rail cap {side}", top, 0.070, "brass", material, damage_group)
        kit.polyline(parts, f"{prefix} rail mid {side}", mid, 0.042, "brass", material, damage_group)
        for index, x in enumerate(xs):
            y = side * (half_beam_at(x) * 0.86 + 0.03)
            parts.append(
                kit.beam(
                    f"{prefix} baluster {side} {index}",
                    (x, y, sheer_at(x)),
                    (x, y, sheer_at(x) + height),
                    0.046,
                    "brass",
                    material,
                    damage_group,
                )
            )


def add_belt(
    parts: list[bpy.types.Object],
    prefix: str,
    xs: list[float],
    material: bpy.types.Material,
    heights: tuple[float, ...],
    damage_group: str | None = None,
) -> None:
    """Armour strakes with rivet lines — the plate's banded hull side."""
    for side in (-1, 1):
        for band, height in enumerate(heights):
            points = [(x, side * (half_beam_at(x) * 0.99 + 0.02), sheer_at(x) * height) for x in xs]
            kit.polyline(parts, f"{prefix} strake {side} {band}", points, 0.070, "iron", material, damage_group)
            for index, (start, end) in enumerate(zip(points, points[1:])):
                kit.rivet_line(
                    parts,
                    f"{prefix} strake {side} {band} {index}",
                    start,
                    end,
                    2,
                    0.030,
                    material,
                    damage_group=damage_group,
                )


# --------------------------------------------------------------------------------------
# claw — armoured bow, lattice derrick, four-tine grab
# --------------------------------------------------------------------------------------


def build_claw(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    arm = "DamageClawArm"

    parts.append(kit.hull_loft("Fore armoured hull", BOW_STATIONS, "plate", material))
    xs = [-4.02, -3.58, -3.02, -2.36, -1.66, -1.02]
    add_belt(parts, "Bow", xs, material, (0.42, 0.72))
    add_bulwark(parts, "Bow", xs, material)

    # Ram bow and cutwater: the plate's prow is a weapon of salvage, not a hull end.
    parts.append(kit.beam("Bow cutwater", (-4.46, 0, 0.30), (-4.10, 0, 1.34), 0.19, "iron", material))
    parts.append(kit.beam("Bow ram spur", (-4.62, 0, 0.62), (-4.02, 0, 0.86), 0.23, "iron", material))
    parts.append(kit.cone("Bow ram tip", 0.15, 0.02, 0.34, (-4.76, 0, 0.66), "brass", material, vertices=8, rotation=(0, -math.pi / 2, 0)))
    for side in (-1, 1):
        parts.append(kit.beam(f"Bow knee {side}", (-4.28, side * 0.16, 1.30), (-3.66, side * 0.72, 1.28), 0.10, "brass", material))
    kit.lens(parts, "Bow eye port", 0.13, (-4.16, -0.30, 1.02), material)
    kit.lens(parts, "Bow eye starboard", 0.13, (-4.16, 0.30, 1.02), material)

    # Fore working deck with plank seams.
    parts.append(kit.box("Fore working deck", (3.10, 3.30, 0.14), (-2.62, 0, 1.29), "deck", material, 0.020))
    for index, y in enumerate(np.linspace(-1.42, 1.42, 9)):
        parts.append(kit.beam(f"Fore deck seam {index}", (-4.06, float(y), 1.37), (-1.06, float(y), 1.37), 0.032, "deck", material))
    for index, x in enumerate((-3.74, -3.10, -2.46, -1.82, -1.24)):
        kit.lens(parts, f"Fore deck lamp {index}", 0.075, (x, -1.62, 1.52), material, rotation=(0, 0, 0))
        kit.lens(parts, f"Fore deck lamp starboard {index}", 0.075, (x, 1.62, 1.52), material, rotation=(0, 0, 0))

    # Crane bed: turntable, king post, winch drum.
    parts.append(kit.cylinder("Crane turntable ring", 0.86, 0.16, (-1.52, 0, 1.44), "iron", material, vertices=20, bevel=0.02))
    parts.append(kit.torus("Crane turntable race", 0.88, 0.070, (-1.52, 0, 1.50), "brass", material, major_segments=20))
    kit.rivet_line(parts, "Crane race", (-2.38, 0, 1.56), (-0.66, 0, 1.56), 8, 0.034, material, rotation=(0, 0, 0))
    parts.append(kit.cylinder("Crane king post", 0.30, 0.62, (-1.52, 0, 1.80), "iron", material, vertices=14))
    parts.append(kit.cylinder("Winch drum", 0.34, 1.06, (-1.06, 0, 1.86), "plate", material, vertices=16, rotation=(math.pi / 2, 0, 0), bevel=0))
    for index, y in enumerate((-0.44, -0.15, 0.15, 0.44)):
        parts.append(kit.torus(f"Winch drum flange {index}", 0.36, 0.045, (-1.06, y, 1.86), "brass", material, rotation=(math.pi / 2, 0, 0), major_segments=14))
    parts.append(kit.beam("Winch pawl", (-0.72, 0.42, 1.72), (-0.72, 0.62, 2.06), 0.08, "brass", material))

    # The derrick itself: a real lattice, which is what the plate shows and the
    # shipped model abstracts into two bare struts.
    kit.truss(parts, "Derrick main", (-1.62, 0, 1.72), (-3.06, 0, 4.62), 1.02, 0.17, 7, "iron", "brass", material, arm)
    kit.truss(parts, "Derrick jib", (-3.06, 0, 4.62), (-3.94, 0, 5.06), 0.74, 0.13, 3, "iron", "brass", material, arm)
    for side in (-1, 1):
        parts.append(kit.beam(f"Derrick back stay {side}", (-1.30, side * 0.50, 1.66), (-2.72, side * 0.42, 4.10), 0.075, "rope", material, arm))
        parts.append(kit.beam(f"Derrick foot gusset {side}", (-1.70, side * 0.51, 1.62), (-2.06, side * 0.51, 2.34), 0.13, "iron", material, arm))

    # Head sheaves and the load chain the grab hangs from.
    parts.append(kit.cylinder("Derrick head sheave", 0.44, 0.36, (-3.06, 0, 4.66), "brass", material, vertices=16, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=arm))
    parts.append(kit.torus("Derrick head rim", 0.47, 0.060, (-3.06, 0, 4.66), "brass", material, rotation=(math.pi / 2, 0, 0), damage_group=arm, major_segments=16))
    parts.append(kit.cylinder("Jib nose sheave", 0.33, 0.32, (-3.98, 0, 5.08), "brass", material, vertices=14, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=arm))
    parts.append(kit.torus("Jib nose rim", 0.36, 0.050, (-3.98, 0, 5.08), "brass", material, rotation=(math.pi / 2, 0, 0), damage_group=arm, major_segments=14))
    kit.chain_run(parts, "Grab hoist chain", (-3.98, 0, 4.92), (-4.44, 0, 3.42), 9, 0.098, "rope", material, arm)
    kit.chain_run(parts, "Derrick tackle chain", (-3.10, -0.30, 4.36), (-3.86, -0.24, 5.00), 5, 0.070, "rope", material, arm)
    parts.append(kit.beam("Grab hoist guy port", (-3.94, -0.28, 5.02), (-4.34, -0.34, 3.58), 0.042, "rope", material, arm))
    parts.append(kit.beam("Grab hoist guy starboard", (-3.94, 0.28, 5.02), (-4.34, 0.34, 3.58), 0.042, "rope", material, arm))

    # Grab head: brass housing, teal sight, knuckled tines.
    parts.append(kit.cylinder("Grab housing", 0.54, 0.94, (-4.46, 0, 3.24), "plate", material, vertices=16, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=arm))
    parts.append(kit.torus("Grab housing collar upper", 0.57, 0.075, (-4.46, -0.34, 3.24), "brass", material, rotation=(math.pi / 2, 0, 0), damage_group=arm, major_segments=16))
    parts.append(kit.torus("Grab housing collar lower", 0.57, 0.075, (-4.46, 0.34, 3.24), "brass", material, rotation=(math.pi / 2, 0, 0), damage_group=arm, major_segments=16))
    parts.append(kit.cylinder("Grab crown cap", 0.30, 0.30, (-4.46, 0, 3.70), "brass", material, vertices=14, damage_group=arm))
    kit.rivet_line(parts, "Grab housing", (-4.90, 0, 3.24), (-4.02, 0, 3.24), 6, 0.038, material, damage_group=arm, rotation=(0, math.pi / 2, 0))
    kit.lens(parts, "Grab sight port", 0.21, (-4.46, -0.50, 3.28), material, damage_group=arm)
    kit.lens(parts, "Grab sight starboard", 0.21, (-4.46, 0.50, 3.28), material, damage_group=arm)
    parts.append(kit.cylinder("Grab tine hub", 0.42, 0.30, (-4.46, 0, 2.86), "iron", material, vertices=16, damage_group=arm))

    # Four talons, each a swept tube on a curve that reaches out, then curls back
    # under itself. The plate's grab closes like a hand; a straight fork does not
    # read as the Dredge Queen's claw at any distance.
    talon = (
        (0.30, 2.88, 0.205),
        (0.66, 2.44, 0.196),
        (0.94, 1.94, 0.176),
        (1.05, 1.44, 0.150),
        (0.96, 1.02, 0.118),
        (0.70, 0.72, 0.078),
        (0.40, 0.58, 0.034),
        (0.20, 0.56, 0.010),
    )
    for finger, angle in enumerate((math.radians(40), math.radians(140), math.radians(220), math.radians(320))):
        dx, dy = math.cos(angle), math.sin(angle)
        points = [(-4.46 + dx * reach, dy * reach, z) for reach, z, _ in talon]
        radii = [radius for _, _, radius in talon]
        parts.append(kit.swept_tube(f"Grab talon {finger}", points, radii, "iron", material, sides=8, damage_group=arm))
        # Brass knuckle bands where the plate shows the talon's hinged segments.
        for band, station in enumerate((1, 3, 5)):
            reach, z, radius = talon[station]
            centre = (-4.46 + dx * reach, dy * reach, z)
            nxt = talon[station + 1]
            direction = Vector((dx * (nxt[0] - reach), dy * (nxt[0] - reach), nxt[1] - z))
            parts.append(
                kit.torus(
                    f"Grab talon band {finger} {band}",
                    radius * 1.22,
                    radius * 0.30,
                    centre,
                    "brass",
                    material,
                    rotation=tuple(direction.to_track_quat("Z", "Y").to_euler()),
                    damage_group=arm,
                    major_segments=8,
                )
            )
        # The inner cutting ridge that makes the talon read as a tool, not a tentacle.
        ridge = [
            (-4.46 + dx * (reach - radius * 0.55), dy * (reach - radius * 0.55), z)
            for reach, z, radius in talon[1:6]
        ]
        kit.polyline(parts, f"Grab talon ridge {finger}", ridge, 0.045, "brass", material, arm)
        parts.append(
            kit.beam(
                f"Grab talon ram {finger}",
                (-4.46 + dx * 0.30, dy * 0.30, 3.02),
                (-4.46 + dx * 0.72, dy * 0.72, 2.44),
                0.080,
                "brass",
                material,
                arm,
            )
        )

    # Damage-only scrap, hidden inside the intact housing until Act 3.
    for shard, at in enumerate(((-4.34, -0.10, 3.08), (-4.28, 0.08, 3.04), (-4.38, 0.0, 2.96))):
        parts.append(kit.box(f"Hidden claw chain scrap {shard}", (0.24, 0.07, 0.06), at, "damage", material, 0.002, damage_group=f"DamageClawShard{shard}"))
    return parts


# --------------------------------------------------------------------------------------
# paddlewheels — full spoked wheels with shipped blades and armoured arches
# --------------------------------------------------------------------------------------


def build_paddle(material: bpy.types.Material, side: int) -> list[bpy.types.Object]:
    label = "Port" if side < 0 else "Starboard"
    group = f"Damage{label}Paddle"
    centre = Vector((1.32, side * 2.44, 1.66))
    parts: list[bpy.types.Object] = []

    parts.append(kit.box(f"{label} wheel sponson", (3.42, 0.40, 0.86), (1.20, side * 2.06, 0.70), "plate", material, 0.050))
    parts.append(kit.box(f"{label} wheel sill", (3.60, 0.48, 0.16), (1.20, side * 2.16, 1.06), "brass", material, 0.022))
    kit.rivet_line(parts, f"{label} sponson", (-0.42, side * 1.86, 0.66), (2.82, side * 1.86, 0.66), 10, 0.034, material)

    parts.append(kit.torus(f"{label} outer rim", 1.42, 0.100, tuple(centre), "iron", material, rotation=(math.pi / 2, 0, 0), damage_group=group, major_segments=22, minor_segments=5))
    parts.append(kit.torus(f"{label} outer rim inner", 1.24, 0.062, tuple(centre), "brass", material, rotation=(math.pi / 2, 0, 0), damage_group=group, major_segments=22))
    parts.append(kit.torus(f"{label} inner rim", 0.84, 0.068, tuple(centre), "brass", material, rotation=(math.pi / 2, 0, 0), damage_group=group, major_segments=18))
    parts.append(kit.cylinder(f"{label} hub", 0.30, 0.56, tuple(centre), "brass", material, vertices=16, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=group))
    parts.append(kit.torus(f"{label} hub collar", 0.33, 0.055, (centre.x, centre.y - side * 0.26, centre.z), "brass", material, rotation=(math.pi / 2, 0, 0), damage_group=group, major_segments=14))
    for bolt in range(8):
        angle = math.tau * bolt / 8
        parts.append(
            kit.cylinder(
                f"{label} hub bolt {bolt}",
                0.040,
                0.60,
                (centre.x + math.cos(angle) * 0.20, centre.y, centre.z + math.sin(angle) * 0.20),
                "brass",
                material,
                vertices=6,
                rotation=(math.pi / 2, 0, 0),
                bevel=0,
                damage_group=group,
            )
        )

    for spoke in range(16):
        angle = math.tau * spoke / 16
        dx, dz = math.cos(angle) * 1.36, math.sin(angle) * 1.36
        parts.append(
            kit.beam(
                f"{label} spoke {spoke}",
                (centre.x + math.cos(angle) * 0.26, centre.y, centre.z + math.sin(angle) * 0.26),
                (centre.x + dx, centre.y, centre.z + dz),
                0.058,
                "brass",
                material,
                group,
            )
        )

    # Blades sit on backing brackets, which is what gives the plate's wheel its
    # heavy read at distance instead of a thin disc.
    for blade in range(18):
        angle = math.tau * blade / 18
        x = centre.x + math.cos(angle) * 1.48
        z = centre.z + math.sin(angle) * 1.48
        parts.append(kit.box(f"{label} blade {blade}", (0.50, 0.44, 0.15), (x, centre.y, z), "plate", material, 0.006, rotation=(0, -angle, 0), damage_group=group))
        parts.append(
            kit.beam(
                f"{label} blade bracket {blade}",
                (centre.x + math.cos(angle) * 1.24, centre.y + side * 0.20, centre.z + math.sin(angle) * 1.24),
                (x, centre.y + side * 0.20, z),
                0.046,
                "brass",
                material,
                group,
            )
        )

    arch = kit.arc_points((centre.x, centre.y, centre.z), 1.70, math.radians(14), math.radians(166), 9)
    kit.polyline(parts, f"{label} wheel arch", arch, 0.15, "plate", material, group)
    for index, point in enumerate(arch[1:-1]):
        parts.append(
            kit.beam(
                f"{label} arch rib {index}",
                (point[0], centre.y - 0.24, point[2]),
                (point[0], centre.y + 0.24, point[2]),
                0.070,
                "iron",
                material,
                group,
            )
        )
    parts.append(kit.beam(f"{label} forward stay", (-0.36, centre.y, 0.92), (-0.16, centre.y, 2.38), 0.13, "brass", material))
    parts.append(kit.beam(f"{label} rear stay", (2.94, centre.y, 0.92), (2.84, centre.y, 2.44), 0.13, "brass", material, group))
    kit.lens(parts, f"{label} running lantern", 0.13, (-0.02, side * 2.34, 2.66), material)
    for shard, at in enumerate(((centre.x, centre.y, 1.54), (centre.x - 0.07, centre.y, 1.50), (centre.x + 0.07, centre.y, 1.48))):
        parts.append(kit.box(f"Hidden {label} paddle shard {shard}", (0.34, 0.19, 0.11), at, "damage", material, 0.003, damage_group=f"Damage{label}Shard{shard}"))
    return parts


# --------------------------------------------------------------------------------------
# hold — central hull, domed wheelhouse, funnels, loot hold, corsair sail
# --------------------------------------------------------------------------------------


def build_hold(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []

    parts.append(kit.hull_loft("Central armoured hull", AFT_STATIONS, "plate", material))
    xs = [-0.30, 0.52, 1.34, 2.14, 2.86, 3.46, 3.92]
    add_belt(parts, "Main", xs, material, (0.40, 0.70))
    add_bulwark(parts, "Main", xs, material)
    parts.append(kit.box("Aft transom", (0.52, 3.30, 1.20), (3.94, 0, 0.78), "iron", material, 0.08, damage_group="DamageHoldRear"))
    kit.rivet_line(parts, "Transom", (3.98, -1.44, 0.78), (3.98, 1.44, 0.78), 8, 0.036, material, damage_group="DamageHoldRear", rotation=(0, math.pi / 2, 0))

    parts.append(kit.box("Main working deck", (4.90, 3.72, 0.14), (1.42, 0, 1.29), "deck", material, 0.020))
    for index, y in enumerate(np.linspace(-1.62, 1.62, 11)):
        parts.append(kit.beam(f"Main deck seam {index}", (-1.02, float(y), 1.37), (3.84, float(y), 1.37), 0.032, "deck", material))

    # Domed corsair wheelhouse: ribbed copper dome, arched amber lights, lens finial.
    parts.append(kit.box("Wheelhouse armoured base", (1.92, 2.52, 1.48), (-0.42, 0, 2.06), "iron", material, 0.050))
    parts.append(kit.box("Wheelhouse cornice", (2.14, 2.74, 0.16), (-0.42, 0, 2.86), "brass", material, 0.020))
    kit.rivet_line(parts, "Wheelhouse cornice port", (-1.38, -1.34, 2.86), (0.54, -1.34, 2.86), 7, 0.030, material)
    kit.rivet_line(parts, "Wheelhouse cornice starboard", (-1.38, 1.34, 2.86), (0.54, 1.34, 2.86), 7, 0.030, material)
    parts.append(kit.ico_sphere("Wheelhouse copper dome", 0.82, (-0.42, 0, 3.02), "plate", material, scale=(1.0, 1.22, 0.62), subdivisions=2))
    for rib in range(12):
        angle = math.tau * rib / 12
        parts.append(
            kit.beam(
                f"Wheelhouse dome rib {rib}",
                (-0.42 + math.cos(angle) * 0.80, math.sin(angle) * 0.98, 2.96),
                (-0.42 + math.cos(angle) * 0.20, math.sin(angle) * 0.24, 3.50),
                0.048,
                "brass",
                material,
            )
        )
    parts.append(kit.torus("Wheelhouse dome base ring", 0.84, 0.060, (-0.42, 0, 2.96), "brass", material, major_segments=18))
    parts.append(kit.cylinder("Wheelhouse lantern drum", 0.20, 0.34, (-0.42, 0, 3.60), "teal", material, vertices=12, bevel=0))
    parts.append(kit.torus("Wheelhouse lantern cage", 0.22, 0.035, (-0.42, 0, 3.60), "brass", material, major_segments=12))
    parts.append(kit.cone("Wheelhouse finial", 0.17, 0.02, 0.40, (-0.42, 0, 3.94), "brass", material, vertices=10))
    for side in (-1, 1):
        y = side * 1.28
        for index, x in enumerate((-1.12, -0.42, 0.28)):
            parts.append(kit.box(f"Wheelhouse pane {side} {index}", (0.46, 0.05, 0.42), (x, y, 2.16), "cargo", material, 0.005))
            parts.append(kit.beam(f"Wheelhouse mullion {side} {index}", (x, y * 1.02, 1.92), (x, y * 1.02, 2.42), 0.036, "brass", material))
            parts.append(kit.cone(f"Wheelhouse pane arch {side} {index}", 0.24, 0.02, 0.20, (x, y * 1.01, 2.48), "brass", material, vertices=6, rotation=(math.pi / 2, 0, 0)))
        parts.append(kit.beam(f"Wheelhouse belt {side}", (-1.36, y * 1.03, 2.52), (0.52, y * 1.03, 2.52), 0.050, "brass", material))
    parts.append(kit.box("Wheelhouse forward amber pane", (0.05, 1.36, 0.46), (-1.40, 0, 2.16), "cargo", material, 0.006))
    parts.append(kit.beam("Wheelhouse forward mullion", (-1.43, 0, 1.90), (-1.43, 0, 2.44), 0.038, "brass", material))

    # Two funnels, banded, with soot crowns — the plate's twin stacks.
    for index, (x, y) in enumerate(((-0.94, -0.66), (-0.94, 0.66))):
        parts.append(kit.cylinder(f"Funnel {index}", 0.21, 1.14, (x, y, 3.36), "soot", material, vertices=14))
        for band, z in enumerate((2.98, 3.36, 3.74)):
            parts.append(kit.torus(f"Funnel band {index} {band}", 0.235, 0.038, (x, y, z), "brass", material, major_segments=14))
        parts.append(kit.torus(f"Funnel crown {index}", 0.25, 0.050, (x, y, 3.93), "brass", material, major_segments=14))
        parts.append(kit.beam(f"Funnel stay {index}", (x, y, 3.80), (x + 0.46, y * 1.5, 2.92), 0.034, "rope", material))

    # Fat aft loot hold: armoured bin, split lids, strapped, with a visible cargo mound.
    parts.append(kit.box("Loot hold armoured bin", (2.68, 3.22, 1.66), (2.16, 0, 2.16), "iron", material, 0.055, damage_group="DamageHoldRear"))
    kit.rivet_line(parts, "Loot hold port", (0.86, -1.62, 2.10), (3.46, -1.62, 2.10), 9, 0.034, material, damage_group="DamageHoldRear")
    kit.rivet_line(parts, "Loot hold starboard", (0.86, 1.62, 2.10), (3.46, 1.62, 2.10), 9, 0.034, material, damage_group="DamageHoldRear")
    for index, x in enumerate((0.90, 1.52, 2.14, 2.76, 3.38)):
        parts.append(kit.beam(f"Loot hold corner post {index}", (x, -1.64, 1.36), (x, -1.64, 2.98), 0.070, "brass", material, "DamageHoldRear"))
        parts.append(kit.beam(f"Loot hold corner post starboard {index}", (x, 1.64, 1.36), (x, 1.64, 2.98), 0.070, "brass", material, "DamageHoldRear"))
    parts.append(kit.box("Loot hold port lid", (2.60, 1.58, 0.20), (2.14, -0.80, 3.04), "plate", material, 0.022, rotation=(math.radians(-8), 0, 0), damage_group="DamageHoldPortLid"))
    parts.append(kit.box("Loot hold starboard lid", (2.60, 1.58, 0.20), (2.14, 0.80, 3.04), "plate", material, 0.022, rotation=(math.radians(8), 0, 0), damage_group="DamageHoldStarboardLid"))
    for index, x in enumerate((1.10, 1.62, 2.14, 2.66, 3.16)):
        lid = "DamageHoldPortLid" if x < 2.14 else "DamageHoldStarboardLid"
        parts.append(kit.beam(f"Hold lid strap {index}", (x, -1.56, 3.08), (x, 1.56, 3.08), 0.065, "brass", material, lid))
    # Slatted lids and a heaped, visible cargo mound: the plate's hold is full,
    # and a full hold is what makes Act 3's spill legible.
    for index in range(7):
        y = -1.44 + index * 0.48
        lid = "DamageHoldPortLid" if y < 0 else "DamageHoldStarboardLid"
        z = 3.15 + (0.055 if y < 0 else -0.055) * (abs(y) / 1.44) * 2.2
        parts.append(kit.beam(f"Hold lid slat {index}", (0.90, y, z), (3.38, y, z), 0.055, "deck", material, lid))
    mound = (
        (1.30, -0.90, 3.34, 0.50), (1.94, -0.34, 3.44, 0.56), (2.58, -0.78, 3.32, 0.46),
        (1.62, 0.72, 3.36, 0.52), (2.34, 0.88, 3.30, 0.44), (3.02, 0.24, 3.28, 0.42),
        (2.20, 0.10, 3.62, 0.40),
    )
    for index, (x, y, z, size) in enumerate(mound):
        lid = "DamageHoldPortLid" if y < 0 else "DamageHoldStarboardLid"
        if index % 3 == 1:
            parts.append(kit.cylinder(f"Hold cargo drum {index}", size * 0.44, size * 0.86, (x, y, z), "cargo", material, vertices=10, rotation=(0, math.pi / 2, 0), bevel=0, damage_group=lid))
        else:
            parts.append(kit.box(f"Hold cargo crate {index}", (size, size * 0.92, size * 0.78), (x, y, z), "cargo", material, 0.012, rotation=(0, 0, index * 0.34), damage_group=lid))
    for index, (x, y) in enumerate(((1.36, -0.94), (2.30, 0.90), (3.00, -0.86))):
        parts.append(kit.box(f"Deck cargo crate {index}", (0.46, 0.44, 0.36), (x, y, 3.30), "cargo", material, 0.010, damage_group="DamageHoldPortLid" if y < 0 else "DamageHoldStarboardLid"))
    parts.append(kit.torus("Hold rope coil port", 0.36, 0.058, (3.06, -1.66, 2.82), "rope", material, rotation=(math.pi / 2, 0, 0), damage_group="DamageHoldPortLid", major_segments=12))
    parts.append(kit.torus("Hold rope coil starboard", 0.31, 0.052, (1.20, 1.66, 2.80), "rope", material, rotation=(math.pi / 2, 0, 0), damage_group="DamageHoldStarboardLid", major_segments=12))

    # Masts, yard, and the oxblood corsair sail with its ghosted crossed pickaxes.
    parts.append(kit.cylinder("Main mast", 0.13, 4.86, (0.56, 0, 3.56), "brass", material, vertices=12))
    for band, z in enumerate((2.20, 3.44, 4.68)):
        parts.append(kit.torus(f"Main mast band {band}", 0.155, 0.032, (0.56, 0, z), "brass", material, major_segments=10))
    parts.append(kit.cone("Main mast finial", 0.19, 0.03, 0.44, (0.56, 0, 6.18), "brass", material, vertices=10))
    parts.append(kit.cylinder("Main mast top", 0.19, 0.16, (0.56, 0, 5.90), "brass", material, vertices=10))
    parts.append(kit.cylinder("Aft mast", 0.10, 3.62, (3.14, 0, 3.38), "brass", material, vertices=10, damage_group="DamageFlag"))
    parts.append(kit.cone("Aft mast finial", 0.14, 0.03, 0.32, (3.14, 0, 5.40), "brass", material, vertices=8, damage_group="DamageFlag"))
    parts.append(kit.beam("Main yard", (0.60, 0, 5.78), (3.86, 0, 5.42), 0.085, "brass", material, "DamageFlag"))
    parts.append(
        kit.quad_panel(
            "Oxblood main corsair sail",
            ((0.70, 0.02, 5.74), (3.82, 0.02, 5.40), (3.46, 0.02, 3.06), (0.78, 0.02, 2.70)),
            0.060,
            "sail",
            material,
            "DamageFlag",
        )
    )
    parts.append(kit.triangle_panel("Oxblood aft sail", ((3.10, 0.03, 4.68), (3.92, 0.03, 4.20), (3.14, 0.03, 3.16)), 0.050, "sail", material, "DamageFlag"))
    for index, z in enumerate((4.62, 4.10, 3.58)):
        parts.append(kit.beam(f"Sail reef line {index}", (0.78, -0.04, z), (3.58, -0.04, z - 0.12), 0.030, "rope", material, "DamageFlag"))
    # Crossed pickaxes: handle plus head per axe. Tools, never arms (ADR-001).
    for axe, (start, end) in enumerate(((((1.32), -0.05, 3.62), ((2.42), -0.05, 4.42)), (((1.36), -0.07, 4.44), ((2.42), -0.07, 3.58)))):
        parts.append(kit.beam(f"Ghost pickaxe handle {axe}", start, end, 0.062, "brass", material, "DamageFlag"))
        head_x = end[0] + (end[0] - start[0]) * 0.10
        head_z = end[2] + (end[2] - start[2]) * 0.10
        parts.append(kit.beam(f"Ghost pickaxe head {axe}", (head_x - 0.26, end[1], head_z + 0.16), (head_x + 0.26, end[1], head_z - 0.16), 0.055, "brass", material, "DamageFlag"))
    for index, (start, end) in enumerate((
        ((0.56, -0.05, 5.52), (-3.30, -1.72, 1.52)),
        ((0.56, 0.05, 5.52), (3.36, 1.68, 1.54)),
        ((3.14, -0.03, 4.92), (0.60, -1.72, 1.52)),
        ((3.14, 0.03, 4.92), (3.42, 1.66, 1.54)),
        ((0.56, -0.05, 4.30), (-1.02, -1.70, 1.50)),
        ((0.56, 0.05, 4.30), (-1.02, 1.70, 1.50)),
    )):
        parts.append(kit.beam(f"Rigging line {index}", start, end, 0.030, "rope", material, "DamageFlag" if index in {2, 3} else None))

    for index, (x, y) in enumerate(((-0.88, -1.58), (-0.88, 1.58), (0.76, -1.58), (0.76, 1.58), (2.76, -1.58), (2.76, 1.58))):
        kit.lens(parts, f"Deck lantern {index}", 0.095, (x, y, 1.86), material, rotation=(0, 0, 0))
        parts.append(kit.beam(f"Deck lantern post {index}", (x, y, 1.42), (x, y, 1.82), 0.046, "brass", material))
    for index, x in enumerate((-0.60, 0.30, 1.20, 2.10, 3.00)):
        kit.lens(parts, f"Hull porthole port {index}", 0.085, (x, -half_beam_at(x) * 1.00, 0.86), material)
        kit.lens(parts, f"Hull porthole starboard {index}", 0.085, (x, half_beam_at(x) * 1.00, 0.86), material)

    # Deck machinery. The plate's deck is a working yard, not a clear platform;
    # this clutter is most of what separates "boat shape" from "the Dredge Queen".
    parts.append(kit.cylinder("Capstan drum", 0.30, 0.46, (0.06, -1.12, 1.58), "brass", material, vertices=12))
    parts.append(kit.torus("Capstan collar", 0.32, 0.048, (0.06, -1.12, 1.74), "brass", material, major_segments=12))
    for bar in range(6):
        angle = math.tau * bar / 6
        parts.append(kit.beam(f"Capstan bar {bar}", (0.06, -1.12, 1.76), (0.06 + math.cos(angle) * 0.46, -1.12 + math.sin(angle) * 0.46, 1.74), 0.038, "brass", material))
    parts.append(kit.cylinder("Deck boiler", 0.36, 1.02, (0.10, 1.16, 1.86), "iron", material, vertices=14, rotation=(0, math.pi / 2, 0)))
    for band, x in enumerate((-0.28, 0.10, 0.48)):
        parts.append(kit.torus(f"Deck boiler band {band}", 0.385, 0.040, (x, 1.16, 1.86), "brass", material, rotation=(0, math.pi / 2, 0), major_segments=12))
    parts.append(kit.cylinder("Deck boiler pipe", 0.075, 0.72, (0.62, 1.16, 2.10), "soot", material, vertices=8))
    for index, (x, y) in enumerate(((-0.66, -1.70), (-0.66, 1.70), (1.90, -1.70), (1.90, 1.70), (3.44, -1.66), (3.44, 1.66))):
        parts.append(kit.cylinder(f"Deck bollard {index}", 0.085, 0.34, (x, y, 1.52), "brass", material, vertices=8))
        parts.append(kit.torus(f"Deck bollard cap {index}", 0.098, 0.030, (x, y, 1.68), "brass", material, major_segments=8))
    for index, (x, y) in enumerate(((1.10, -1.24), (1.72, 1.30), (3.20, -1.18))):
        parts.append(kit.torus(f"Deck rope coil {index}", 0.26, 0.052, (x, y, 1.44), "rope", material, rotation=(math.pi / 2, 0, 0), major_segments=12))
    parts.append(kit.box("Companion hatch", (0.62, 0.72, 0.24), (-1.02, 0.86, 1.48), "deck", material, 0.016))
    parts.append(kit.box("Companion hatch lid", (0.66, 0.34, 0.07), (-1.02, 0.68, 1.66), "brass", material, 0.008, rotation=(math.radians(-26), 0, 0)))

    # Damage-only cargo, hidden inside the intact hold until the lids split.
    hidden = ((2.20, 0.0, 1.70), (2.06, 0.12, 1.66), (2.30, -0.10, 1.60), (2.08, -0.08, 1.64))
    for index, at in enumerate(hidden):
        if index % 2:
            parts.append(kit.cylinder(f"Hidden cargo drum {index}", 0.19, 0.36, at, "cargo", material, vertices=10, rotation=(0, math.pi / 2, 0), bevel=0, damage_group=f"DamageCargo{index}"))
        else:
            parts.append(kit.box(f"Hidden cargo crate {index}", (0.36, 0.32, 0.30), at, "cargo", material, 0.008, damage_group=f"DamageCargo{index}"))
    parts.append(kit.box("Hidden hold rupture", (0.68, 0.09, 0.50), (3.10, 0.0, 1.62), "damage", material, 0.004, damage_group="DamageHoldBreach"))
    return parts


# --------------------------------------------------------------------------------------
# morphs — the Act-3 plate, as silhouette events
# --------------------------------------------------------------------------------------


def add_damage_shapes(claw, paddle_port, paddle_starboard, hold) -> None:
    claw.shape_key_add(name="Basis")
    slack = claw.shape_key_add(name="Damage_SlackClaw")
    pivot = Vector((-1.40, 0.0, 1.30))
    for index in kit.group_vertex_indices(claw, "DamageClawArm"):
        co = slack.data[index].co
        kit.rotate_y(co, pivot, math.radians(-30))
        co.z -= 0.34
        co.y *= 1.06
    shard_moves = (Vector((-0.36, -0.40, -0.22)), Vector((-0.22, 0.44, -0.35)), Vector((0.10, 0.56, -0.46)))
    for shard, movement in enumerate(shard_moves):
        for index in kit.group_vertex_indices(claw, f"DamageClawShard{shard}"):
            slack.data[index].co += movement

    for paddle, side, label in ((paddle_port, -1, "Port"), (paddle_starboard, 1, "Starboard")):
        paddle.shape_key_add(name="Basis")
        broken = paddle.shape_key_add(name=f"Damage_Broken{label}Paddle")
        centre = Vector((1.32, side * 2.44, 1.66))
        for index in kit.group_vertex_indices(paddle, f"Damage{label}Paddle"):
            co = broken.data[index].co
            radial_x = co.x - centre.x
            radial_z = co.z - centre.z
            upper = max(0.0, radial_z)
            co.y += side * (0.30 + upper * 0.46)
            co.x += radial_z * (0.18 if side > 0 else -0.18)
            co.z -= 0.42 + abs(radial_x) * 0.18
        moves = (
            Vector((-0.56, side * 0.46, -0.18)),
            Vector((0.16, side * 0.62, -0.44)),
            Vector((0.62, side * 0.40, 0.08)),
        )
        for shard, movement in enumerate(moves):
            for index in kit.group_vertex_indices(paddle, f"Damage{label}Shard{shard}"):
                broken.data[index].co += movement

    hold.shape_key_add(name="Basis")
    cracked = hold.shape_key_add(name="Damage_CrackedLootHold")
    for index in kit.group_vertex_indices(hold, "DamageHoldPortLid"):
        co = cracked.data[index].co
        co.y -= 0.58
        co.z += max(0.0, 2.50 - co.z) * 0.15 + 0.28
    for index in kit.group_vertex_indices(hold, "DamageHoldStarboardLid"):
        co = cracked.data[index].co
        co.y += 0.62
        co.z += max(0.0, 2.50 - co.z) * 0.12 - 0.18
        co.x += 0.18
    for index in kit.group_vertex_indices(hold, "DamageHoldRear"):
        co = cracked.data[index].co
        rear = max(0.0, min(1.0, (co.x - 1.55) / 1.80))
        co.x += rear * 0.20
        co.z -= rear * 0.50
        co.y *= 1.0 + rear * 0.08
    for index in kit.group_vertex_indices(hold, "DamageFlag"):
        co = cracked.data[index].co
        mast_x = 0.52 if co.x < 2.60 else 3.00
        co.x = mast_x + (co.x - mast_x) * 0.30
        co.z = 2.42 + (co.z - 2.42) * 0.25
        co.y *= 0.60
    cargo_moves = (
        Vector((1.86, -2.08, -0.94)),
        Vector((1.58, 2.16, -0.86)),
        Vector((2.22, -1.12, -1.02)),
        Vector((2.00, 1.28, -0.92)),
    )
    for cargo, movement in enumerate(cargo_moves):
        for index in kit.group_vertex_indices(hold, f"DamageCargo{cargo}"):
            cracked.data[index].co += movement
    for index in kit.group_vertex_indices(hold, "DamageHoldBreach"):
        cracked.data[index].co += Vector((0.68, 1.68, -0.34))

    for obj in (claw, paddle_port, paddle_starboard, hold):
        obj.active_shape_key_index = 0
        for key in obj.data.shape_keys.key_blocks:
            key.value = 0.0


def strip_micro_bevels(parts: list[bpy.types.Object]) -> None:
    """Spend triangles on silhouette, not on edge loops the run camera cannot resolve."""
    detail_words = ("seam", "baluster", "rivet", "mullion", "strap", "stay", "rigging", "reef", "bracket", "bolt", "rib", "bracket")
    for part in parts:
        if not any(word in part.name.lower() for word in detail_words):
            continue
        for modifier in list(part.modifiers):
            if modifier.type == "BEVEL":
                part.modifiers.remove(modifier)


def main() -> None:
    kit.reset_scene()
    atlas, source_hashes = create_atlas()
    material = kit.create_material("DredgeQueenDetailOpus5Material", atlas)

    groups = {
        "claw": build_claw(material),
        "paddle_port": build_paddle(material, -1),
        "paddle_starboard": build_paddle(material, 1),
        "hold": build_hold(material),
    }
    for parts in groups.values():
        strip_micro_bevels(parts)
    part_counts = {name: len(parts) for name, parts in groups.items()}

    claw = kit.join_component("claw", groups["claw"], material, REGIONS)
    paddle_port = kit.join_component("paddle_port", groups["paddle_port"], material, REGIONS)
    paddle_starboard = kit.join_component("paddle_starboard", groups["paddle_starboard"], material, REGIONS)
    hold = kit.join_component("hold", groups["hold"], material, REGIONS)
    objects = (claw, paddle_port, paddle_starboard, hold)

    kit.normalize_base_center(objects, 0, MODEL_LENGTH)
    add_damage_shapes(*objects)

    minimum, maximum = kit.world_bounds(objects)
    triangles = kit.triangle_count(objects)
    per_component = {obj.name: sum(len(p.vertices) - 2 for p in obj.data.polygons) for obj in objects}
    assert triangles <= TRIANGLE_CEILING, f"triangle budget exceeded: {triangles}"
    assert abs((maximum.x - minimum.x) - MODEL_LENGTH) < 0.01
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
            str(DAMAGE_REFERENCE.relative_to(ROOT)): source_hashes["damage"],
        },
        "objects": [obj.name for obj in objects],
        "damageMorphs": [obj.data.shape_keys.key_blocks[1].name for obj in objects],
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
