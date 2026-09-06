from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

sys.dont_write_bytecode = True

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REFERENCE = ROOT / "assets/raw/plate-e9-bld-canal-works.png"
BASE_SHA = "b9df7e2127dadc1ea74859026459e32a2405af34"
PLATE_BRANCH_TIP = "440bb19e4058eded9be82b1faf4292e73808cb0a"
ASSETS = {
    "water-ledger-office": ROOT / "assets/pilots/water-ledger-office-3d",
    "greenkeeper": ROOT / "assets/pilots/greenkeeper-3d",
    "ice-quarry-head": ROOT / "assets/pilots/ice-quarry-head-3d",
    "weather-warden-spire": ROOT / "assets/pilots/weather-warden-spire-3d",
    "canal-packet-boat": ROOT / "assets/pilots/canal-packet-boat-3d",
}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


dq = load("e9_population_primitives", ROOT / "assets/pilots/dredge-queen-3d/build_dredge_queen.py")

# The source plate's rust-brass canal vocabulary, with E1 green reserved for
# living beds. Values are deliberately brighter than boss iron at town scale.
E9_PALETTE = {
    "soot": (0.055, 0.035, 0.022),
    "iron": (0.255, 0.155, 0.085),
    "brass": (0.56, 0.34, 0.085),
    "deck": (0.38, 0.18, 0.075),
    "teal": (0.040, 0.42, 0.40),
    "damage": (0.54, 0.16, 0.055),
    "sail": (0x50 / 255.0, 0x67 / 255.0, 0x4C / 255.0),
    "rope": (0.50, 0.35, 0.15),
    "cargo": (0.42, 0.24, 0.11),
    "plate": (0.44, 0.29, 0.17),
}


def create_e9_atlas():
    image, sources = dq.create_atlas()
    pixels = np.empty(dq.ATLAS_SIZE * dq.ATLAS_SIZE * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    atlas = pixels.reshape(dq.ATLAS_SIZE, dq.ATLAS_SIZE, 4)
    for name, region in dq.REGIONS.items():
        x0, y0, x1, y1 = dq.region_pixels(region)
        block = atlas[y0:y1, x0:x1, :3]
        target = np.asarray(E9_PALETTE[name], dtype=np.float32)
        if name == "sail":
            # The E9 callback is an exact swatch contract, not a near-green.
            atlas[y0:y1, x0:x1, :3] = target[None, None, :]
            continue
        luminance = block.mean(axis=2)
        low, high = np.percentile(luminance, (7, 93))
        normalized = np.clip((luminance - low) / max(0.001, high - low), 0.0, 1.0)
        tone = 0.68 + normalized[:, :, None] * 0.50
        atlas[y0:y1, x0:x1, :3] = np.clip(target[None, None, :] * tone, 0.01, 0.78)
    image.name = "BasinPopulationE9Atlas"
    image.pixels.foreach_set(atlas.ravel())
    image.update()
    image.pack()
    return image, sources


def b(name, size, at, region, mat, bevel=0.025, rotation=(0, 0, 0)):
    return dq.box(name, size, at, region, mat, bevel, rotation)


def c(name, radius, depth, at, region, mat, vertices=16, rotation=(0, 0, 0)):
    return dq.cylinder(name, radius, depth, at, region, mat, vertices, rotation, 0.008)


def t(name, major, minor, at, region, mat, rotation=(0, 0, 0), segments=16):
    return dq.torus(name, major, minor, at, region, mat, rotation, major_segments=segments)


def s(name, radius, at, region, mat, scale=(1, 1, 1)):
    return dq.ico_sphere(name, radius, at, region, mat, scale=scale)


def beam(name, start, end, width, region, mat):
    return dq.beam(name, start, end, width, region, mat)


def water_ledger_office(mat):
    parts = [
        b("Ledger office plinth", (4.18, 2.98, 0.34), (0, 0, 0.17), "iron", mat),
        b("Ledger office", (3.70, 2.52, 2.18), (0, 0.08, 1.39), "plate", mat, 0.06),
        s("Ledger dome", 1.28, (0, 0.08, 2.51), "brass", mat, (1.28, 1.0, 0.44)),
        b("Public water counter", (2.35, 0.52, 0.70), (0, -1.40, 0.76), "deck", mat),
        b("Ledger pictogram slate", (1.15, 0.08, 0.74), (0, -1.31, 1.64), "teal", mat, 0.01),
        c("Balance pivot", 0.13, 1.32, (0, -1.49, 2.74), "brass", mat, 12),
        beam("Balance arm", (-0.88, -1.49, 3.20), (0.88, -1.49, 3.20), 0.09, "brass", mat),
    ]
    for side in (-1, 1):
        x = side * 1.56
        parts += [
            c(f"Water meter {side}", 0.34, 1.55, (x, -0.98, 1.13), "teal", mat, 14),
            t(f"Meter seal {side}", 0.34, 0.06, (x, -0.98, 1.64), "brass", mat, segments=14),
            beam(f"Meter pipe {side}", (x, -0.98, 0.38), (side * 0.72, -0.78, 0.38), 0.09, "brass", mat),
            dq.cone(f"Balance pan {side}", 0.34, 0.18, 0.18, (side * 0.74, -1.49, 2.86), "deck", mat, 14),
            beam(f"Balance hanger {side}", (side * 0.74, -1.49, 3.18), (side * 0.74, -1.49, 2.95), 0.035, "rope", mat),
        ]
    return parts


def greenkeeper(mat):
    parts = [
        b("Greenkeeper foundation", (5.0, 3.18, 0.32), (0, 0, 0.16), "iron", mat),
        b("Seed vault", (2.05, 2.55, 2.15), (0.58, 0.13, 1.39), "plate", mat, 0.06),
        s("Seed vault glass", 1.15, (0.58, 0.13, 2.48), "teal", mat, (1.0, 1.05, 0.42)),
        c("Irrigation tank", 0.56, 2.35, (-1.72, 0.32, 1.42), "teal", mat, 16),
        t("Tank crown", 0.53, 0.08, (-1.72, 0.32, 2.36), "brass", mat, segments=16),
        b("Greenkeeper threshold", (1.35, 0.64, 0.18), (0.58, -1.43, 0.22), "deck", mat),
    ]
    for side in (-1, 1):
        y = side * 0.91
        parts += [
            b(f"Seed bed {side}", (2.08, 0.62, 0.34), (-0.60, y, 0.50), "cargo", mat, 0.04),
            b(f"E1 green row {side}", (1.82, 0.48, 0.17), (-0.60, y, 0.73), "sail", mat, 0.035),
            beam(f"Irrigation rail {side}", (-1.72, 0.32, 0.92), (-0.60, y, 0.90), 0.07, "brass", mat),
        ]
        for x in (-1.16, -0.60, -0.04):
            parts += [s(f"Seedling {side} {x}", 0.13, (x, y, 0.91), "sail", mat, (0.72, 0.72, 1.35))]
    return parts


def ice_quarry_head(mat):
    parts = [
        b("Quarry head base", (5.38, 3.58, 0.34), (0, 0, 0.17), "iron", mat),
        b("Winch house", (1.72, 2.25, 1.90), (-1.58, 0.35, 1.22), "plate", mat, 0.05),
        c("Quarry winch", 0.52, 1.30, (-1.58, -0.84, 1.48), "brass", mat, 16, (math.pi / 2, 0, 0)),
        b("Ice block", (1.10, 1.02, 1.18), (1.20, 0.12, 1.14), "teal", mat, 0.08, (0, 0, math.radians(5))),
        b("Ice pile port", (0.72, 0.66, 0.62), (1.95, 0.78, 0.55), "teal", mat, 0.06),
        b("Ice pile starboard", (0.62, 0.58, 0.50), (2.12, -0.74, 0.49), "teal", mat, 0.06),
    ]
    for x in (-2.30, 2.30):
        for y in (-1.35, 1.35):
            parts += [beam(f"Gantry upright {x} {y}", (x, y, 0.34), (x, y, 4.42), 0.11, "iron", mat)]
    for y in (-1.35, 1.35):
        parts += [beam(f"Gantry top {y}", (-2.30, y, 4.42), (2.30, y, 4.42), 0.13, "brass", mat)]
    for x in (-2.30, -0.76, 0.76, 2.30):
        parts += [beam(f"Gantry cross {x}", (x, -1.35, 4.42), (x, 1.35, 4.42), 0.09, "brass", mat)]
    parts += [
        beam("Crane trolley", (0.55, -1.35, 4.25), (0.55, 1.35, 4.25), 0.18, "deck", mat),
        beam("Hoist cable", (0.55, 0.12, 4.25), (1.20, 0.12, 1.78), 0.055, "rope", mat),
        t("Quarry signal", 0.25, 0.055, (-1.58, -1.22, 2.36), "teal", mat, (math.pi / 2, 0, 0), 12),
    ]
    return parts


def weather_warden_spire(mat):
    parts = [
        b("Spire pressure base", (3.78, 2.96, 0.34), (0, 0, 0.17), "iron", mat),
        c("Warden rotunda", 1.18, 1.82, (0, 0, 1.12), "plate", mat, 18),
        s("Storm lens", 0.76, (0, -0.98, 1.62), "teal", mat, (1.0, 0.40, 1.0)),
        c("Storm lance", 0.34, 3.55, (0, 0, 3.62), "brass", mat, 14),
        s("Weather globe", 0.53, (0, 0, 5.38), "teal", mat),
        dq.cone("Lightning crown", 0.36, 0.02, 1.14, (0, 0, 6.18), "brass", mat, 12),
        b("Warden threshold", (1.16, 0.64, 0.17), (0, -1.44, 0.21), "deck", mat),
    ]
    for z in (2.22, 3.22, 4.22):
        parts += [t(f"Spire seal {z}", 0.48, 0.075, (0, 0, z), "teal", mat, segments=14)]
    for angle in (0, 120, 240):
        rad = math.radians(angle)
        x, y = math.cos(rad) * 1.36, math.sin(rad) * 1.36
        parts += [
            beam(f"Storm brace {angle}", (x, y, 0.34), (0, 0, 4.68), 0.09, "iron", mat),
            s(f"Field node {angle}", 0.20, (x, y, 2.18), "teal", mat),
        ]
    parts += [beam("Wind vane", (-0.92, 0, 5.94), (0.92, 0, 5.94), 0.07, "brass", mat)]
    return parts


def canal_packet_boat(mat):
    parts = [
        b("Packet hull", (3.72, 1.72, 0.72), (0.38, 0, 0.42), "iron", mat, 0.12),
        dq.cone("Packet bow", 0.84, 0.10, 1.22, (-2.08, 0, 0.42), "iron", mat, 12, (0, math.pi / 2, 0)),
        b("Packet deck", (3.80, 1.46, 0.18), (0.18, 0, 0.86), "deck", mat),
        b("Packet cabin", (1.64, 1.28, 1.38), (0.62, 0, 1.56), "plate", mat, 0.06),
        s("Cabin dome", 0.76, (0.62, 0, 2.26), "brass", mat, (1.0, 0.86, 0.40)),
        b("Parcel crate", (0.72, 0.60, 0.58), (-0.84, 0.38, 1.18), "cargo", mat),
        b("Seed parcel", (0.62, 0.50, 0.45), (-0.86, -0.38, 1.12), "sail", mat),
        beam("Packet mast", (-0.26, 0, 0.92), (-0.26, 0, 3.25), 0.085, "brass", mat),
        b("Sun awning", (1.58, 1.52, 0.12), (-0.26, 0, 2.96), "rope", mat),
    ]
    for side in (-1, 1):
        y = side * 0.82
        parts += [
            b(f"Gunwale {side}", (3.98, 0.10, 0.32), (0.12, y, 1.05), "brass", mat),
            c(f"Packet paddle {side}", 0.48, 0.16, (1.56, side * 0.91, 1.02), "brass", mat, 14, (math.pi / 2, 0, 0)),
        ]
    for x in (0.18, 0.62, 1.06):
        parts += [c(f"Cabin porthole {x}", 0.15, 0.07, (x, -0.67, 1.70), "teal", mat, 12, (math.pi / 2, 0, 0))]
    parts += [s("Packet bow lamp", 0.18, (-2.18, 0, 1.20), "teal", mat)]
    return parts


BUILDERS = {
    "water-ledger-office": water_ledger_office,
    "greenkeeper": greenkeeper,
    "ice-quarry-head": ice_quarry_head,
    "weather-warden-spire": weather_warden_spire,
    "canal-packet-boat": canal_packet_boat,
}

FOOTPRINTS = {
    "water-ledger-office": {"assigned": "claim_office", "limit": [4.4, 3.2]},
    "greenkeeper": {"assigned": "tavern", "limit": [5.2, 3.4]},
    "ice-quarry-head": {"assigned": "ice-quarry-pad", "limit": [5.6, 3.8]},
    "weather-warden-spire": {"assigned": "chapel", "limit": [4.2, 3.2]},
    "canal-packet-boat": {"assigned": "canal-water mount", "limit": [5.2, 2.0]},
}

FOOTPRINT_NORMALIZATION = {
    "water-ledger-office": (1.0, 0.95),
    "greenkeeper": (1.0, 1.0),
    "ice-quarry-head": (1.0, 1.0),
    "weather-warden-spire": (1.0, 0.95),
    "canal-packet-boat": (1.0, 1.0),
}


def build_asset(asset_id: str) -> dict:
    dq.reset_scene()
    bpy.context.preferences.filepaths.save_version = 0
    dq.REFERENCE = REFERENCE
    dq.DAMAGE_REFERENCE = REFERENCE
    atlas, _ = create_e9_atlas()
    atlas.name = f"{asset_id}E9Atlas"
    material = dq.create_material(atlas)
    material.name = f"{asset_id}E9Material"
    mesh = dq.join_component(asset_id, BUILDERS[asset_id](material), material)
    scale_x, scale_y = FOOTPRINT_NORMALIZATION[asset_id]
    for vertex in mesh.data.vertices:
        vertex.co.x *= scale_x
        vertex.co.y *= scale_y
    mesh.data.update()
    minimum, maximum = dq.world_bounds((mesh,))
    offset = Vector(((minimum.x + maximum.x) * 0.5, (minimum.y + maximum.y) * 0.5, minimum.z))
    for vertex in mesh.data.vertices:
        vertex.co -= offset
    mesh.data.update()
    out = ASSETS[asset_id]
    out.mkdir(parents=True, exist_ok=True)
    dq.BLEND = out / f"{asset_id}.blend"
    dq.GLB = out / f"{asset_id}.glb"
    dq.export((mesh,))
    triangles = dq.triangle_count((mesh,))
    minimum, maximum = dq.world_bounds((mesh,))
    size = maximum - minimum
    limit = FOOTPRINTS[asset_id]["limit"]
    assert triangles <= 15_000
    assert size.x <= limit[0] + 0.001 and size.y <= limit[1] + 0.001, (
        f"{asset_id} footprint {size.x:.4f} x {size.y:.4f} exceeds {limit}"
    )
    assert abs(minimum.z) < 0.001
    return {
        "asset": str(dq.GLB.relative_to(ROOT)),
        "sha256": hashlib.sha256(dq.GLB.read_bytes()).hexdigest(),
        "triangles": triangles,
        "placement": FOOTPRINTS[asset_id],
        "boundsBlender": {"min": [round(v, 6) for v in minimum], "max": [round(v, 6) for v in maximum]},
    }


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    results = {asset_id: build_asset(asset_id) for asset_id in BUILDERS}
    (HERE / "build-contract.json").write_text(json.dumps({
        "baseSha": BASE_SHA,
        "basinPlateDependencyTip": PLATE_BRANCH_TIP,
        "sourcePlate": {str(REFERENCE.relative_to(ROOT)): hashlib.sha256(REFERENCE.read_bytes()).hexdigest()},
        "assets": results,
    }, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
