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
REFERENCE = ROOT / "assets/raw/plate-e8-bld-set.png"
BASE_SHA = "a9be388a3fe95a3228c638ed4afaf8a6ec6a7f5a"
ASSETS = {
    "orbital-canteen": ROOT / "assets/pilots/orbital-canteen-3d",
    "suit-fitter": ROOT / "assets/pilots/suit-fitter-3d",
    "launch-works": ROOT / "assets/pilots/launch-works-3d",
    "he3-assay": ROOT / "assets/pilots/he3-assay-3d",
    "mass-driver-dispatch": ROOT / "assets/pilots/mass-driver-dispatch-3d",
}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


dq = load("e8_population_primitives", ROOT / "assets/pilots/dredge-queen-3d/build_dredge_queen.py")

E8_PALETTE = {
    "soot": (0.055, 0.062, 0.060),
    "iron": (0.255, 0.285, 0.280),
    "brass": (0.54, 0.34, 0.115),
    "deck": (0.34, 0.235, 0.125),
    "teal": (0.055, 0.43, 0.43),
    "damage": (0.40, 0.18, 0.075),
    "sail": (0.42, 0.35, 0.23),
    "rope": (0.50, 0.38, 0.19),
    "cargo": (0.39, 0.28, 0.15),
    "plate": (0.43, 0.455, 0.425),
}


def create_e8_atlas():
    """Retone the engraved source sampling into the E8 kit's light palette."""
    image, sources = dq.create_atlas()
    pixels = np.empty(dq.ATLAS_SIZE * dq.ATLAS_SIZE * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    atlas = pixels.reshape(dq.ATLAS_SIZE, dq.ATLAS_SIZE, 4)
    for name, region in dq.REGIONS.items():
        x0, y0, x1, y1 = dq.region_pixels(region)
        block = atlas[y0:y1, x0:x1, :3]
        luminance = block.mean(axis=2)
        low, high = np.percentile(luminance, (8, 92))
        normalized = np.clip((luminance - low) / max(0.001, high - low), 0.0, 1.0)
        tone = 0.72 + normalized[:, :, None] * 0.43
        target = np.asarray(E8_PALETTE[name], dtype=np.float32)
        atlas[y0:y1, x0:x1, :3] = np.clip(target[None, None, :] * tone, 0.01, 0.72)
    image.name = "DomePopulationE8Atlas"
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


def orbital_canteen(mat):
    parts = [
        b("Canteen pressure plinth", (4.9, 3.15, 0.42), (0, 0, 0.21), "iron", mat),
        b("Canteen body", (4.55, 2.82, 2.1), (0, 0.12, 1.40), "plate", mat, 0.06),
        b("Chrome counter band", (4.78, 0.24, 0.42), (0, -1.38, 1.16), "brass", mat),
        b("Public canopy", (4.75, 0.78, 0.18), (0, -1.45, 2.46), "deck", mat),
        s("Earth window bubble", 1.20, (0, 0.58, 2.65), "teal", mat, (1.42, 0.52, 0.92)),
        t("Earth window brass ring", 1.02, 0.11, (0, -0.02, 2.68), "brass", mat, (math.pi / 2, 0, 0), 20),
        c("Earth cameo", 0.78, 0.08, (0, -0.10, 2.68), "teal", mat, 20, (math.pi / 2, 0, 0)),
        b("Earth window seat", (2.25, 0.52, 0.48), (0, 0.76, 1.06), "deck", mat, 0.08),
    ]
    for x in (-1.75, -0.58, 0.58, 1.75):
        parts += [b(f"Front pane {x}", (0.72, 0.08, 0.76), (x, -1.34, 1.72), "teal", mat, 0.01)]
    for x in (-2.02, 2.02):
        parts += [c(f"Pressure post {x}", 0.13, 2.65, (x, -1.34, 1.36), "brass", mat, 10)]
    return parts


def suit_fitter(mat):
    parts = [
        b("Suit fitter base", (3.55, 3.0, 0.34), (0, 0, 0.17), "iron", mat),
        c("Fitter rotunda", 1.42, 2.15, (0, 0.14, 1.35), "plate", mat, 18),
        s("Helmet roof", 1.46, (0, 0.14, 2.45), "teal", mat, (1, 1, 0.42)),
        t("Helmet roof seal", 1.35, 0.10, (0, 0.14, 2.18), "brass", mat, segments=18),
        b("Fitting threshold", (1.18, 0.72, 0.18), (0, -1.62, 0.20), "deck", mat),
    ]
    for side in (-1, 1):
        x = side * 1.42
        parts += [
            c(f"Suit pod {side}", 0.48, 1.70, (x, -0.12, 1.14), "iron", mat, 14),
            s(f"Suit helmet {side}", 0.43, (x, -0.12, 2.02), "teal", mat, (1, 1, 0.82)),
            t(f"Suit collar {side}", 0.36, 0.07, (x, -0.12, 1.72), "brass", mat, segments=14),
            beam(f"Suit hose {side}", (side * 1.02, 0.48, 1.64), (x, -0.12, 1.18), 0.10, "teal", mat),
        ]
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        parts += [beam(f"Rotunda rib {angle}", (1.36 * math.cos(rad), 1.36 * math.sin(rad) + 0.14, 0.38), (1.12 * math.cos(rad), 1.12 * math.sin(rad) + 0.14, 2.36), 0.07, "brass", mat)]
    return parts


def launch_works(mat):
    parts = [
        c("Launch ring base", 2.72, 0.34, (0, 0, 0.17), "iron", mat, 24),
        t("Launch teal seal", 2.18, 0.13, (0, 0, 0.38), "teal", mat, segments=24),
        c("Rocket lower", 0.52, 2.65, (-0.72, 0.14, 1.78), "plate", mat, 16),
        dq.cone("Rocket nose", 0.52, 0.05, 1.45, (-0.72, 0.14, 3.83), "brass", mat, 16),
        c("Rocket window", 0.17, 0.08, (-0.72, -0.39, 2.55), "teal", mat, 12, (math.pi / 2, 0, 0)),
        b("Launch control", (1.05, 0.92, 1.18), (1.72, 0.88, 0.94), "plate", mat),
        s("Control cupola", 0.55, (1.72, 0.88, 1.58), "teal", mat, (1, 1, 0.48)),
    ]
    for side in (-1, 1):
        parts += [
            b(f"Rocket fin {side}", (0.16, 0.72, 0.95), (-0.72 + side * 0.50, 0.14, 0.78), "brass", mat, 0.01, (0, math.radians(side * 15), 0)),
        ]
    tower_x = 1.58
    for z in (0.5, 1.45, 2.40, 3.35, 4.30):
        parts += [b(f"Gantry deck {z}", (1.22, 1.18, 0.12), (tower_x, 0.02, z), "deck", mat)]
    for x in (1.05, 2.11):
        for y in (-0.48, 0.52):
            parts += [beam(f"Gantry upright {x} {y}", (x, y, 0.32), (x, y, 4.68), 0.09, "iron", mat)]
    for z in (0.8, 1.75, 2.70, 3.65):
        parts += [beam(f"Gantry cross {z}", (1.05, -0.48, z), (2.11, 0.52, z + 0.46), 0.07, "brass", mat)]
    parts += [beam("Umbilical arm", (1.58, 0.02, 3.62), (-0.20, 0.08, 3.12), 0.12, "teal", mat)]
    return parts


def he3_assay(mat):
    parts = [
        b("Assay pressure base", (4.4, 3.05, 0.34), (0, 0, 0.17), "iron", mat),
        b("Assay lab", (2.65, 2.45, 2.18), (-0.62, 0.22, 1.38), "plate", mat, 0.05),
        s("Assay glass roof", 1.22, (-0.62, 0.22, 2.52), "teal", mat, (1.05, 0.92, 0.46)),
        c("Sample tower", 0.47, 2.85, (1.28, 0.52, 1.64), "brass", mat, 14),
        s("Sample vial", 0.38, (1.28, 0.52, 3.10), "teal", mat, (0.78, 0.78, 1.12)),
        b("Assay counter", (2.58, 0.52, 0.72), (-0.62, -1.20, 0.82), "deck", mat),
    ]
    for x in (-1.30, -0.62, 0.06):
        parts += [c(f"Sample window {x}", 0.23, 0.08, (x, -1.27, 1.66), "teal", mat, 12, (math.pi / 2, 0, 0)), t(f"Sample ring {x}", 0.28, 0.05, (x, -1.31, 1.66), "brass", mat, (math.pi / 2, 0, 0), 12)]
    for i, x in enumerate((1.28, 1.88)):
        parts += [t(f"He3 pan rim {i}", 0.58, 0.08, (x, -0.88, 0.50), "brass", mat, segments=16), dq.cone(f"He3 pan {i}", 0.56, 0.20, 0.24, (x, -0.88, 0.39), "deck", mat, 16)]
    return parts


def mass_driver_dispatch(mat):
    parts = [
        b("Dispatch rail base", (5.45, 3.28, 0.30), (0, 0, 0.15), "iron", mat),
        b("Dispatch house", (1.52, 2.40, 2.05), (1.70, 0.22, 1.32), "plate", mat, 0.05),
        s("Dispatch cupola", 0.76, (1.70, 0.22, 2.38), "teal", mat, (1, 1, 0.48)),
        c("Driver barrel", 0.64, 3.70, (-0.60, 0.28, 1.46), "plate", mat, 18, (0, math.pi / 2, 0)),
        t("Driver muzzle", 0.66, 0.12, (-2.46, 0.28, 1.46), "teal", mat, (0, math.pi / 2, 0), 18),
        c("Driver bore", 0.48, 0.10, (-2.55, 0.28, 1.46), "soot", mat, 18, (0, math.pi / 2, 0)),
        b("Cargo sled", (1.05, 1.14, 0.44), (0.25, -0.82, 0.58), "deck", mat),
    ]
    for y in (-0.82, 1.02):
        parts += [b(f"Rail {y}", (5.15, 0.10, 0.12), (0, y, 0.42), "brass", mat)]
    for x in (-2.1, -1.2, -0.3, 0.6, 1.5, 2.25):
        parts += [b(f"Rail tie {x}", (0.12, 2.18, 0.10), (x, 0.10, 0.36), "deck", mat)]
    for x in (-1.72, -0.88, -0.04, 0.80):
        parts += [t(f"Coil {x}", 0.78, 0.07, (x, 0.28, 1.46), "brass", mat, (0, math.pi / 2, 0), 16)]
    parts += [beam("Dispatch signal", (2.25, -0.86, 0.44), (2.25, -0.86, 3.18), 0.10, "brass", mat), s("Dispatch signal lamp", 0.20, (2.25, -0.86, 3.28), "teal", mat)]
    return parts


BUILDERS = {
    "orbital-canteen": orbital_canteen,
    "suit-fitter": suit_fitter,
    "launch-works": launch_works,
    "he3-assay": he3_assay,
    "mass-driver-dispatch": mass_driver_dispatch,
}

# The population inherits the canonical Town parcels.  These small axis-only
# normalizations keep the concept-plate silhouettes while guaranteeing that no
# pressure shell, threshold, or assay fixture overhangs its assigned flat pad.
FOOTPRINT_NORMALIZATION = {
    "orbital-canteen": (1.0, 0.96),
    "suit-fitter": (1.0, 0.90),
    "launch-works": (1.0, 1.0),
    "he3-assay": (0.95, 1.0),
    "mass-driver-dispatch": (1.0, 1.0),
}


def build_asset(asset_id: str) -> dict:
    dq.reset_scene()
    dq.REFERENCE = REFERENCE
    dq.DAMAGE_REFERENCE = REFERENCE
    atlas, _ = create_e8_atlas()
    atlas.name = f"{asset_id}E8Atlas"
    material = dq.create_material(atlas)
    material.name = f"{asset_id}E8Material"
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
    assert triangles <= 15_000
    assert abs(minimum.z) < 0.001
    return {
        "asset": str(dq.GLB.relative_to(ROOT)),
        "sha256": hashlib.sha256(dq.GLB.read_bytes()).hexdigest(),
        "triangles": triangles,
        "boundsBlender": {"min": [round(v, 6) for v in minimum], "max": [round(v, 6) for v in maximum]},
    }


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    results = {asset_id: build_asset(asset_id) for asset_id in BUILDERS}
    (HERE / "build-contract.json").write_text(json.dumps({
        "baseSha": BASE_SHA,
        "sourcePlate": {str(REFERENCE.relative_to(ROOT)): hashlib.sha256(REFERENCE.read_bytes()).hexdigest()},
        "assets": results,
    }, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
