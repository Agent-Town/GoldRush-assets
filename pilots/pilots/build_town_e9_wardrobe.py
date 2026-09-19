"""Dress the town for Epoch 9, "The Red Fields" — the full eight-building cast.

The town is era-dressed E2-E8 at full cast and then stops: every one of the eight
core buildings has an .e8 variant and no .e9 one. `TownTavernPilot.eraCandidates`
walks DOWN from the active era, so at era 9 the square silently serves era 8 —
the town does not break, it just stops evolving for two whole eras.

This closes E9. Each variant is the SAME building wearing the era, per the
factory's ratified transform law: an era transform is an image-EDIT of existing
art, never a repaint from scratch. So each .e9 keeps its .e8 shell, footprint and
UV layout, and re-dresses it:

  * the atlas is transformed, not replaced -- a luminance-preserving rust remap
    that keeps every painted panel line, porthole and rivet the E8 wave authored,
    while turning the Orbital silver/teal into Red Fields regolith crust;
  * the ice/glass reads are protected, because a dead red world still needs its
    water to be legible as water;
  * an E9 sub-palette is painted into atlas space this building provably does not
    use, so the era's new vocabulary shares the one existing atlas;
  * THE GREEN is the E1 riverbank swatch, #50674c, laid down as exact pixels with
    an inset core so a verifier can prove the callback survived engraving. The
    bundle's palette note is explicit that this is the same swatch, literally --
    "the point IS the callback". `build_era_props_e9.py` already treats it as a
    swatch contract; this honours the same contract.

Wiring is filename-only: `TownTavernPilot` binds variants through
`import.meta.glob('../../assets/pilots/*-3d/*.e*.glb')`, so landing
`<building>.e9.glb` beside its siblings is the whole integration. Zero code.

Usage:
  blender -b --factory-startup --python build_town_e9_wardrobe.py
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
import mathutils
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PILOTS = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/town-e9"

sys.dont_write_bytecode = True

ERA = 9
SOURCE_ERA = 8  # the coat this era is re-dressed from; E10 re-dresses E9
TRIANGLE_CAP = 15000  # Town's live cap, measured by the E8 wave
GRID = 16             # atlas cells per axis when hunting for unused space

# The E1 riverbank green. Not "a" green -- the swatch the saga calls back to.
E1_GREEN = (0x50 / 255.0, 0x67 / 255.0, 0x4C / 255.0)

# The Red Fields sub-palette, painted into free atlas space on every building.
# Index order is fixed; recipes address these by name.
SUB_PALETTE = {
    "green": E1_GREEN,             # the callback
    "regolith": (0.55, 0.22, 0.09),  # rust crust
    "ice": (0.32, 0.53, 0.55),       # quarried ice / canal water
    "dome": (0.80, 0.72, 0.58),      # warm-lit dome glass
    "brass": (0.62, 0.45, 0.18),     # fittings
    "iron": (0.26, 0.18, 0.14),      # shadow / ironwork (warm, never a void)
}
SUB_ORDER = list(SUB_PALETTE)


# --------------------------------------------------------------------------
# THE RECIPES -- one per building, each grounded in the bundle's §A language
# --------------------------------------------------------------------------

RECIPES = {
    "tavern": {
        "role": "DomeCommons",
        "why": "bundle §A transform: Orbital Canteen -> Dome Commons annex; 'the biggest interior yet -- the town increasingly lives indoors together'",
        "parts": [
            {"kind": "dome", "name": "Commons dome", "radius": 1.62, "height": 1.06, "at": (0.0, 0.0, "top"), "embed": 0.30, "colour": "dome"},
            {"kind": "ring", "name": "Dome collar", "radius": 1.66, "thickness": 0.14, "at": (0.0, 0.0, "top"), "embed": 0.34, "colour": "brass"},
            {"kind": "box", "name": "Annex hall", "size": (1.30, 0.94, 0.92), "at": (-1.62, 1.16, 0.46), "colour": "regolith"},
            {"kind": "box", "name": "Annex roof", "size": (1.44, 1.06, 0.10), "at": (-1.62, 1.16, 0.96), "colour": "iron"},
            {"kind": "planter", "name": "Commons planter", "at": (1.44, 1.22, 0.0), "colour": "green"},
        ],
    },
    "schoolhouse": {
        "role": "AreologyHall",
        "why": "bundle §A transform: Mission Archive -> the Areology Hall",
        "parts": [
            {"kind": "rack", "name": "Core sample rack", "at": (1.30, 1.24, 0.0), "count": 5, "colour": "regolith"},
            {"kind": "mast", "name": "Survey mast", "at": (-1.42, 1.26, 0.0), "height": 2.30, "colour": "iron"},
            {"kind": "box", "name": "Areology reading board", "size": (1.10, 0.10, 0.62), "at": (0.0, 1.70, 1.05), "colour": "brass"},
            {"kind": "planter", "name": "School planter", "at": (-1.28, -1.40, 0.0), "colour": "green"},
        ],
    },
    "claim-office": {
        "role": "CanalReeve",
        "why": "bundle §A townsfolk: 'canal reeve (water law returns! the E1 claim office's oldest job reborn)' -- the claim office IS the water-law lineage",
        "parts": [
            {"kind": "gate", "name": "Reeve canal gate", "at": (1.78, 0.0, 0.0), "width": 1.34, "height": 1.46, "colour": "brass"},
            {"kind": "channel", "name": "Reeve measuring channel", "at": (1.78, 0.0, 0.0), "length": 1.20, "width": 0.86, "colour": "ice"},
            {"kind": "box", "name": "Water ledger case", "size": (0.72, 0.42, 0.78), "at": (-1.58, 1.12, 0.39), "colour": "regolith"},
            {"kind": "planter", "name": "Reeve planter", "at": (-1.66, -1.10, 0.0), "colour": "green"},
        ],
    },
    "stamp-mill": {
        "role": "CanalWorks",
        "why": "bundle §A buildings: 'canal works (THE building: sluice lineage's apotheosis -- gates, locks, a water-wheel waiting dry for the day it turns)'",
        "parts": [
            {"kind": "wheel", "name": "Dry water wheel", "at": (2.62, 0.0, 0.78), "radius": 0.66, "colour": "brass"},
            {"kind": "gate", "name": "Lock gate upper", "at": (-1.10, 0.0, 0.0), "width": 1.02, "height": 1.22, "colour": "brass"},
            {"kind": "channel", "name": "Lock chamber", "at": (-0.10, 0.0, 0.0), "length": 2.20, "width": 0.72, "colour": "ice"},
            {"kind": "planter", "name": "Lockside planter", "at": (-2.42, 0.62, 0.0), "colour": "green"},
        ],
    },
    "assay-office": {
        "role": "IceQuarryRig",
        "why": "bundle §A buildings: 'ice quarry rig' -- assay is the extraction/analysis lineage, and E9's ore is water",
        "parts": [
            {"kind": "derrick", "name": "Ice cutting derrick", "at": (1.62, -1.06, 0.0), "height": 2.55, "colour": "iron"},
            {"kind": "icestack", "name": "Cut ice stack", "at": (-1.58, -1.10, 0.0), "colour": "ice"},
            {"kind": "box", "name": "Melt sump housing", "size": (0.86, 0.66, 0.52), "at": (-1.60, 1.06, 0.26), "colour": "regolith"},
            {"kind": "planter", "name": "Assay planter", "at": (1.66, 1.14, 0.0), "colour": "green"},
        ],
    },
    "general-store": {
        "role": "SeedVault",
        "why": "bundle §A buildings: 'seed vault (green economy)' -- the store lineage is goods, and E9's currency is seed",
        "parts": [
            {"kind": "silo", "name": "Seed silo west", "at": (-1.72, -1.16, 0.0), "radius": 0.46, "height": 1.76, "colour": "regolith"},
            {"kind": "silo", "name": "Seed silo east", "at": (-1.72, 0.10, 0.0), "radius": 0.38, "height": 1.42, "colour": "regolith"},
            {"kind": "bed", "name": "Vault seed beds", "at": (1.42, 0.0, 0.0), "rows": 3, "colour": "green"},
            {"kind": "box", "name": "Vault door frame", "size": (0.16, 1.18, 1.30), "at": (2.30, 0.0, 0.65), "colour": "iron"},
        ],
    },
    "dynamo-hall": {
        "role": "WeatherSpire",
        "why": "bundle §A buildings: 'weather spire (E4/E5 weather tech's endgame: you begin to CONTROL fronts)' -- the power lineage becomes the weather lineage",
        "parts": [
            {"kind": "mast", "name": "Weather spire", "at": (0.0, 0.0, "top"), "embed": 0.85, "height": 1.95, "colour": "iron"},
            {"kind": "vane", "name": "Front vane upper", "at": (0.0, 0.0, "top"), "embed": 0.85, "lift": 1.62, "radius": 0.42, "colour": "brass"},
            {"kind": "vane", "name": "Front vane lower", "at": (0.0, 0.0, "top"), "embed": 0.85, "lift": 1.05, "radius": 0.66, "colour": "regolith"},
            {"kind": "planter", "name": "Spire planter", "at": (-2.16, 1.14, 0.0), "colour": "green"},
        ],
    },
    "chapel": {
        "role": "ArkYard",
        "why": "bundle §A buildings: 'the Ark yards (megaproject site, visible growing for the whole era)' -- the chapel lineage is the place you depart from (E8 made it the Launch Pad)",
        "parts": [
            {"kind": "scaffold", "name": "Ark yard scaffold", "at": (1.34, 0.0, 0.0), "height": 2.90, "colour": "iron"},
            {"kind": "box", "name": "Keel section", "size": (0.52, 1.46, 0.44), "at": (1.34, 0.0, 0.22), "colour": "brass"},
            {"kind": "box", "name": "Yard stores", "size": (0.74, 0.62, 0.56), "at": (-1.34, 1.06, 0.28), "colour": "regolith"},
            {"kind": "planter", "name": "Yard planter", "at": (-1.30, -1.06, 0.0), "colour": "green"},
        ],
    },
}


# --------------------------------------------------------------------------
# THE ATLAS TRANSFORM (an image-EDIT, per the consistency law)
# --------------------------------------------------------------------------

def rust_remap(pixels: np.ndarray) -> np.ndarray:
    """Orbital silver/teal -> Red Fields regolith, keeping every painted mark.

    Luminance carries the E8 wave's engraving; only chroma is re-authored. Ice and
    glass keep a cooled read, because water must stay legible as water on a world
    whose whole story is water.
    """
    rgb = pixels[..., :3]
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)

    # A three-stop warm ramp: shadowed crust -> lit regolith -> dust-pale rim.
    stops = np.array([
        [0.12, 0.045, 0.028],
        [0.52, 0.245, 0.115],
        [0.90, 0.82, 0.62],
    ], dtype=np.float32)
    t = np.clip(lum, 0.0, 1.0)
    low = np.clip(t * 2.0, 0.0, 1.0)[..., None]
    high = np.clip((t - 0.5) * 2.0, 0.0, 1.0)[..., None]
    rust = stops[0] * (1.0 - low) + stops[1] * low
    rust = rust * (1.0 - high) + stops[2] * high

    # Where E8 painted something distinctly cool (teal glass, ice, instrument
    # glow), keep it cool -- pushed toward Red Fields ice rather than erased.
    coolness = np.clip((rgb[..., 2] - rgb[..., 0]) * 3.2, 0.0, 1.0)[..., None]
    ice = np.array([0.34, 0.62, 0.63], dtype=np.float32) * (0.45 + 0.75 * t)[..., None]

    out = rust * (1.0 - coolness) + ice * coolness
    # Keep a share of the original engraving's own value so the wash cannot
    # flatten the range E8 painted: rust carries the hue, luminance the relief.
    out = out * 0.78 + (out * (0.55 + 0.9 * lum[..., None])) * 0.22
    result = pixels.copy()
    result[..., :3] = np.clip(out, 0.0, 1.0)
    return result


def free_cells(obj) -> set[tuple[int, int]]:
    """Atlas cells this mesh provably does not touch -- triangle coverage, not points.

    Point sampling would miss a face that spans a cell without a vertex inside it,
    which is exactly how a "free" cell later turns out to be someone's roof.
    """
    mesh = obj.data
    mesh.calc_loop_triangles()
    layer = mesh.uv_layers.active
    count = len(layer.data)
    flat = np.empty(count * 2, dtype=np.float32)
    layer.data.foreach_get("uv", flat)
    uv = flat.reshape(count, 2)

    used: set[tuple[int, int]] = set()
    for tri in mesh.loop_triangles:
        corners = uv[list(tri.loops)]
        u0, v0 = corners.min(axis=0)
        u1, v1 = corners.max(axis=0)
        c0 = max(0, min(GRID - 1, int(math.floor(u0 * GRID))))
        c1 = max(0, min(GRID - 1, int(math.floor(u1 * GRID))))
        r0 = max(0, min(GRID - 1, int(math.floor(v0 * GRID))))
        r1 = max(0, min(GRID - 1, int(math.floor(v1 * GRID))))
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                used.add((r, c))
    return {(r, c) for r in range(GRID) for c in range(GRID)} - used


def choose_palette_cells(free: set[tuple[int, int]]) -> dict[str, tuple[int, int]]:
    """Six unused cells for the era's new vocabulary, preferring a tidy run."""
    ordered = sorted(free)
    if len(ordered) < len(SUB_ORDER):
        raise SystemExit("atlas has no room for the E9 sub-palette")
    # Prefer six cells sharing a row, so the sub-palette reads as one strip.
    by_row: dict[int, list[int]] = {}
    for r, c in ordered:
        by_row.setdefault(r, []).append(c)
    for row in sorted(by_row):
        cols = sorted(by_row[row])
        for start in range(len(cols) - len(SUB_ORDER) + 1):
            run = cols[start:start + len(SUB_ORDER)]
            if run[-1] - run[0] == len(SUB_ORDER) - 1:
                return {name: (row, run[index]) for index, name in enumerate(SUB_ORDER)}
    return {name: ordered[index] for index, name in enumerate(SUB_ORDER)}


def paint_sub_palette(pixels: np.ndarray, cells: dict[str, tuple[int, int]], seed: int) -> np.ndarray:
    """Lay the era's colours into unused atlas space, engraved like their siblings."""
    size = pixels.shape[0]
    cell = size // GRID
    rng = np.random.default_rng(seed)
    out = pixels.copy()
    for name, (row, col) in cells.items():
        colour = np.array(SUB_PALETTE[name], dtype=np.float32)
        y0, x0 = row * cell, col * cell
        block = colour + rng.normal(0, 0.009, (cell, cell, 1)).astype(np.float32)
        out[y0:y0 + cell, x0:x0 + cell, :3] = np.clip(block, 0.015, 0.95)
        # The same engraved hatch the props pack uses, so new parts match.
        for x in range(x0 + 9, x0 + cell, 17):
            out[y0:y0 + cell, x:x + 1, :3] *= 0.80
        for y in range(y0 + 13, y0 + cell, 23):
            out[y:y + 1, x0:x0 + cell, :3] *= 0.86
    # The swatch contract: an exact #50674c core that survives all engraving.
    row, col = cells["green"]
    y0, x0 = row * cell, col * cell
    inset = max(6, cell // 5)
    out[y0 + inset:y0 + cell - inset, x0 + inset:x0 + cell - inset, :3] = np.array(E1_GREEN, dtype=np.float32)
    return out


def atlas_image(obj):
    """The image the material actually samples.

    Not "the first image in the file": after a few imports bpy.data can hold
    strays, and picking one by position is how a build cheerfully edits an atlas
    nobody renders.
    """
    material = obj.data.materials[0]
    nodes = [n for n in material.node_tree.nodes if n.type == "TEX_IMAGE" and n.image]
    if len(nodes) != 1:
        raise SystemExit(f"expected exactly one texture image, found {len(nodes)}")
    return nodes[0].image


def replace_atlas(obj, pixels: np.ndarray, name: str, scratch: Path):
    """Bind the transformed atlas to the material as genuinely new image data.

    Editing the imported image in place does not work: it arrives from the GLB
    packed, with its original file bytes as the source of truth, so save() and
    export() both re-emit the ORIGINAL atlas and discard the edit. The build then
    reports success while delivering the previous era's paint.

    So the transformed pixels become a NEW image (GENERATED source, where the
    buffer IS the data), which is written to a real PNG, reloaded and packed. The
    old atlas is dropped so exactly one image ships.
    """
    height, width = pixels.shape[:2]
    fresh = bpy.data.images.new(name, width=width, height=height, alpha=True)
    fresh.colorspace_settings.name = "sRGB"
    fresh.pixels.foreach_set(pixels.reshape(-1).astype(np.float32))
    fresh.filepath_raw = str(scratch)
    fresh.file_format = "PNG"
    fresh.save()
    fresh.source = "FILE"
    fresh.filepath = str(scratch)
    fresh.reload()
    fresh.pack()
    scratch.unlink(missing_ok=True)

    material = obj.data.materials[0]
    stale = []
    for node in material.node_tree.nodes:
        if node.type == "TEX_IMAGE" and node.image:
            if node.image is not fresh:
                stale.append(node.image)
            node.image = fresh
    for image in stale:
        bpy.data.images.remove(image)
    return fresh


def cell_rect(cells: dict[str, tuple[int, int]], name: str) -> tuple[float, float, float, float]:
    """UV rect for a sub-palette cell, inset so no part can bleed into a neighbour."""
    row, col = cells[name]
    pad = 0.16 / GRID
    return (col / GRID + pad, row / GRID + pad, (col + 1) / GRID - pad, (row + 1) / GRID - pad)


# --------------------------------------------------------------------------
# THE NEW VOCABULARY
# --------------------------------------------------------------------------

def _finish(obj, rect, project=True):
    """Send a fresh part's UVs into its palette cell."""
    mesh = obj.data
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    layer = mesh.uv_layers.active
    count = len(layer.data)
    flat = np.empty(count * 2, dtype=np.float32)
    layer.data.foreach_get("uv", flat)
    uv = flat.reshape(count, 2)
    if project and uv.size:
        span_u = uv[:, 0].max() - uv[:, 0].min()
        span_v = uv[:, 1].max() - uv[:, 1].min()
        norm_u = (uv[:, 0] - uv[:, 0].min()) / (span_u if span_u > 1e-6 else 1.0)
        norm_v = (uv[:, 1] - uv[:, 1].min()) / (span_v if span_v > 1e-6 else 1.0)
    else:
        norm_u = np.full(count, 0.5, dtype=np.float32)
        norm_v = np.full(count, 0.5, dtype=np.float32)
    u0, v0, u1, v1 = rect
    uv[:, 0] = u0 + norm_u * (u1 - u0)
    uv[:, 1] = v0 + norm_v * (v1 - v0)
    layer.data.foreach_set("uv", uv.reshape(-1))
    return obj


def _new_box(name, size, location):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def _new_cyl(name, radius, depth, location, vertices=12, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, vertices=vertices, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    return obj


def build_part(spec, top_z, rect):
    """One era part. Every branch returns objects already UV'd into the atlas."""
    kind = spec["kind"]
    name = spec["name"]
    at = spec.get("at", (0.0, 0.0, 0.0))
    x, y, z = at
    if z == "top":
        # "top" is the bounding box lid, which sits above chimneys and finials --
        # anchoring a mast there leaves it visibly hovering over its own roof.
        # embed sinks the part back into the structure it is supposed to stand on.
        z = top_z - spec.get("embed", 0.0)
    made = []

    if kind == "box":
        made.append(_new_box(name, spec["size"], (x, y, z)))

    elif kind == "dome":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=spec["radius"], location=(x, y, z), segments=20, ring_count=8)
        obj = bpy.context.object
        obj.name = name
        obj.scale = (1.0, 1.0, spec["height"] / spec["radius"])
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        # Cut the lower hemisphere: a dome sits ON the roof, it does not swallow it.
        mesh = obj.data
        verts = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
        mesh.vertices.foreach_get("co", verts)
        co = verts.reshape(-1, 3)
        co[:, 2] = np.maximum(co[:, 2], 0.0)
        mesh.vertices.foreach_set("co", co.reshape(-1))
        made.append(obj)

    elif kind == "ring":
        obj = _new_cyl(name, spec["radius"], spec["thickness"], (x, y, z + spec["thickness"] * 0.5), vertices=20)
        made.append(obj)

    elif kind == "mast":
        height = spec["height"]
        made.append(_new_cyl(name, 0.085, height, (x, y, z + height * 0.5), vertices=8))

    elif kind == "vane":
        lift = spec["lift"]
        obj = _new_cyl(name, spec["radius"], 0.055, (x, y, z + lift), vertices=16)
        made.append(obj)

    elif kind == "wheel":
        obj = _new_cyl(name, spec["radius"], 0.16, (x, y, z), vertices=16, rotation=(0.0, math.pi / 2, 0.0))
        made.append(obj)
        for index in range(6):
            angle = index * math.pi / 3
            spoke = _new_box(
                f"{name} paddle {index}",
                (0.20, 0.16, spec["radius"] * 0.92),
                (x, y + math.cos(angle) * spec["radius"] * 0.5, z + math.sin(angle) * spec["radius"] * 0.5),
            )
            spoke.rotation_euler = (angle, 0.0, 0.0)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            made.append(spoke)

    elif kind == "gate":
        width, height = spec["width"], spec["height"]
        made.append(_new_box(f"{name} post west", (0.13, 0.13, height), (x, y - width * 0.5, z + height * 0.5)))
        made.append(_new_box(f"{name} post east", (0.13, 0.13, height), (x, y + width * 0.5, z + height * 0.5)))
        made.append(_new_box(f"{name} head", (0.15, width + 0.26, 0.15), (x, y, z + height)))
        made.append(_new_box(f"{name} leaf", (0.07, width - 0.06, height * 0.62), (x, y, z + height * 0.34)))

    elif kind == "channel":
        length, width = spec["length"], spec["width"]
        made.append(_new_box(f"{name} bed", (length, width, 0.045), (x, y, z + 0.022)))
        made.append(_new_box(f"{name} kerb north", (length, 0.10, 0.17), (x, y + width * 0.5, z + 0.085)))
        made.append(_new_box(f"{name} kerb south", (length, 0.10, 0.17), (x, y - width * 0.5, z + 0.085)))

    elif kind == "rack":
        for index in range(spec["count"]):
            offset = (index - (spec["count"] - 1) * 0.5) * 0.20
            made.append(_new_cyl(f"{name} core {index}", 0.058, 0.86, (x, y + offset, z + 0.43), vertices=8))
        made.append(_new_box(f"{name} sill", (0.26, spec["count"] * 0.20 + 0.14, 0.09), (x, y, z + 0.045)))

    elif kind == "derrick":
        height = spec["height"]
        for dx, dy in ((-0.28, -0.28), (0.28, -0.28), (-0.28, 0.28), (0.28, 0.28)):
            leg = _new_box(f"{name} leg {dx}{dy}", (0.075, 0.075, height), (x + dx * 0.62, y + dy * 0.62, z + height * 0.5))
            made.append(leg)
        made.append(_new_box(f"{name} head", (0.60, 0.60, 0.13), (x, y, z + height)))
        made.append(_new_box(f"{name} brace", (0.52, 0.52, 0.09), (x, y, z + height * 0.52)))

    elif kind == "icestack":
        for index, (dx, dy, dz, scale) in enumerate((
            (0.0, 0.0, 0.0, 1.0), (0.34, 0.06, 0.0, 0.86), (0.15, 0.30, 0.30, 0.78), (-0.20, -0.05, 0.0, 0.72),
        )):
            made.append(_new_box(
                f"{name} block {index}",
                (0.42 * scale, 0.38 * scale, 0.30 * scale),
                (x + dx, y + dy, z + dz + 0.15 * scale),
            ))

    elif kind == "silo":
        radius, height = spec["radius"], spec["height"]
        made.append(_new_cyl(name, radius, height, (x, y, z + height * 0.5), vertices=14))
        made.append(_new_cyl(f"{name} cap", radius * 1.08, 0.10, (x, y, z + height + 0.05), vertices=14))

    elif kind == "scaffold":
        height = spec["height"]
        for dy in (-0.62, 0.62):
            made.append(_new_box(f"{name} upright {dy}", (0.09, 0.09, height), (x, y + dy, z + height * 0.5)))
        for level in range(1, 4):
            made.append(_new_box(f"{name} rail {level}", (0.11, 1.36, 0.08), (x, y, z + height * level / 4.0)))

    elif kind in ("planter", "bed"):
        rows = spec.get("rows", 1)
        for index in range(rows):
            offset = (index - (rows - 1) * 0.5) * 0.34
            made.append(_new_box(f"{name} soil {index}", (0.62, 0.26, 0.11), (x, y + offset, z + 0.055)))
            made.append(_new_box(f"{name} shoots {index}", (0.50, 0.17, 0.16), (x, y + offset, z + 0.155)))

    else:
        raise SystemExit(f"unknown part kind: {kind}")

    return [_finish(obj, rect) for obj in made]


# --------------------------------------------------------------------------
# BUILD ONE BUILDING
# --------------------------------------------------------------------------

def triangles(obj) -> int:
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def bounds(obj) -> dict:
    pts = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
    return {
        "min": [round(min(p[i] for p in pts), 4) for i in range(3)],
        "max": [round(max(p[i] for p in pts), 4) for i in range(3)],
    }


def fit_inside(obj, shell: dict, margin: float = 0.05) -> None:
    """Keep a part within the shell's plan, in X and Y (Blender's ground axes).

    TownTavernPilot validates every candidate model and silently falls to the
    previous era when one fails, so an oversized part does not look wrong -- it
    makes the whole building disappear back into E8. Two of its rules bind here:
    width/depth must stay inside the parcel, and the bounding box must stay
    CENTRED on the origin within 0.06 m, which any asymmetric addition breaks.

    Both are satisfied by construction if no part ever pushes the model's ground
    footprint past the shell that already passed: the merged bounds stay exactly
    the shell's, so the centre never moves. Height is deliberately not clamped --
    the runtime does not cap it, and the era's domes and spires live up there.
    """
    for axis in (0, 1):
        low = shell["min"][axis] + margin
        high = shell["max"][axis] - margin
        span = high - low
        if span <= 0:
            continue
        pts = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
        lo = min(p[axis] for p in pts)
        hi = max(p[axis] for p in pts)
        size = hi - lo
        if size > span:  # too big to fit: shrink about its own centre first
            factor = span / size
            centre = (hi + lo) * 0.5
            obj.scale[axis] *= factor
            bpy.context.view_layer.update()
            pts = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
            lo = min(p[axis] for p in pts)
            hi = max(p[axis] for p in pts)
            obj.location[axis] += centre - (hi + lo) * 0.5
            bpy.context.view_layer.update()
            pts = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
            lo = min(p[axis] for p in pts)
            hi = max(p[axis] for p in pts)
        if lo < low:
            obj.location[axis] += low - lo
        elif hi > high:
            obj.location[axis] -= hi - high
        bpy.context.view_layer.update()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def studly(name: str) -> str:
    return "".join(piece.capitalize() for piece in name.replace("_", "-").split("-"))


def build(name: str, recipe: dict) -> dict:
    folder = PILOTS / f"{name}-3d"
    source = folder / f"{name}.e{SOURCE_ERA}.glb"
    target = folder / f"{name}.e{ERA}.glb"
    blend = folder / f"{name}.e{ERA}.blend"
    if not source.exists():
        raise SystemExit(f"missing source: {source}")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    shell = next(o for o in bpy.data.objects if o.type == "MESH")
    base_tris = triangles(shell)
    base_bounds = bounds(shell)

    image = atlas_image(shell)
    width, height = image.size
    buffer = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(buffer)
    pixels = buffer.reshape(height, width, 4)

    free = free_cells(shell)
    cells = choose_palette_cells(free)
    pixels = rust_remap(pixels)
    pixels = paint_sub_palette(pixels, cells, seed=909 + len(name))
    identity = f"{studly(name)}E{ERA}{recipe['role']}"
    image = replace_atlas(shell, pixels, f"{identity}Atlas", Path(f"/tmp/{name}.e{ERA}.atlas.png"))
    material = shell.data.materials[0]
    material.name = f"{identity}Material"

    top_z = base_bounds["max"][2]
    parts = []
    for spec in recipe["parts"]:
        made = build_part(spec, top_z, cell_rect(cells, spec["colour"]))
        for part in made:
            fit_inside(part, base_bounds)
        parts.extend(made)

    for part in parts:
        part.data.materials.clear()
        part.data.materials.append(material)

    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
    shell.select_set(True)
    bpy.context.view_layer.objects.active = shell
    bpy.ops.object.join()

    merged = bpy.context.object
    merged.name = identity
    merged.data.name = f"{identity}Mesh"

    # The runtime's own validity rules, enforced here rather than discovered as a
    # town that quietly wears last era's clothes.
    merged_check = bounds(merged)
    drift_x = abs((merged_check["max"][0] + merged_check["min"][0]) * 0.5)
    drift_y = abs((merged_check["max"][1] + merged_check["min"][1]) * 0.5)
    grew_x = merged_check["max"][0] - merged_check["min"][0] - (base_bounds["max"][0] - base_bounds["min"][0])
    grew_y = merged_check["max"][1] - merged_check["min"][1] - (base_bounds["max"][1] - base_bounds["min"][1])
    if drift_x > 0.06 or drift_y > 0.06:
        raise SystemExit(f"{name}: bounds centre drifted ({drift_x:.3f}, {drift_y:.3f}); the town would fall back to E8")
    if grew_x > 0.001 or grew_y > 0.001:
        raise SystemExit(f"{name}: footprint grew ({grew_x:+.3f}, {grew_y:+.3f}) beyond its .e8 shell")
    if abs(merged_check["min"][2]) > 0.06:
        raise SystemExit(f"{name}: not grounded (min z {merged_check['min'][2]:.3f})")

    total = triangles(merged)
    # Read everything off the object BEFORE the re-export proof: reopening the
    # .blend invalidates every Python reference into the old scene.
    merged_bounds = bounds(merged)
    if total > TRIANGLE_CAP:
        raise SystemExit(f"{name}: {total} triangles exceeds the {TRIANGLE_CAP} cap")

    # The .blend is the authoring artifact, so the DELIVERY must come out of it,
    # not out of the live session. An in-memory edited atlas re-encodes its PNG
    # differently from the same image round-tripped through packed .blend data,
    # which is real drift even though the geometry is identical -- and it is the
    # delivered bytes that have to be reproducible, not the session's.
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    export_kwargs = dict(export_format="GLB", export_yup=True, use_selection=False)

    bpy.ops.wm.open_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(filepath=str(target), **export_kwargs)
    first = sha256(target)

    proof = Path(f"/tmp/{name}.e{ERA}.reexport.glb")
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(filepath=str(proof), **export_kwargs)
    second = sha256(proof)
    proof.unlink(missing_ok=True)

    # Did the era actually ship? Re-open the DELIVERED file and look for the
    # swatch. This build once reported eight successes while emitting eight
    # untouched E8 atlases, so success is now defined as the edit being present
    # in the bytes, not as the edit having been requested.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(target))
    delivered = next(o for o in bpy.data.objects if o.type == "MESH")
    check_image = atlas_image(delivered)
    check = np.empty(check_image.size[0] * check_image.size[1] * 4, dtype=np.float32)
    check_image.pixels.foreach_get(check)
    bytes8 = np.clip(np.rint(check.reshape(-1, 4)[:, :3] * 255.0), 0, 255).astype(np.int16)
    green_pixels = int(np.all(bytes8 == np.array([0x50, 0x67, 0x4C], dtype=np.int16), axis=-1).sum())
    if green_pixels < 1000:
        raise SystemExit(
            f"{name}: delivered atlas carries {green_pixels} exact #50674c pixels -- "
            "the era transform did not reach the file"
        )

    return {
        "building": name,
        "role": recipe["role"],
        "why": recipe["why"],
        "derivedFrom": str(source.relative_to(ROOT)),
        "output": str(target.relative_to(ROOT)),
        "sourceEra": SOURCE_ERA,
        "baseTriangles": base_tris,
        "triangles": total,
        "addedTriangles": total - base_tris,
        "triangleCap": TRIANGLE_CAP,
        "atlas": [width, height],
        "subPaletteCells": {k: list(v) for k, v in cells.items()},
        "footprintPreserved": {
            "e8": base_bounds,
            "e9": merged_bounds,
        },
        "reExportByteIdentical": first == second,
        "deliveredGreenPixels": green_pixels,
        "sha256": first,
        "bytes": target.stat().st_size,
    }


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    report = []
    for name, recipe in RECIPES.items():
        row = build(name, recipe)
        report.append(row)
        print(f"  {name:<15} {row['role']:<15} {row['triangles']:>6} tris "
              f"(+{row['addedTriangles']:>4})  re-export {'OK' if row['reExportByteIdentical'] else 'DRIFT'}")
    (ARTIFACTS / "town-e9-wardrobe.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    drift = [r["building"] for r in report if not r["reExportByteIdentical"]]
    if drift:
        raise SystemExit(f"re-export drift, asset is not reproducible: {drift}")
    print(f"\nE9 wardrobe complete: {len(report)} variants")


if __name__ == "__main__":
    main()
