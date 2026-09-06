from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

import bpy
from mathutils import Vector


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "build_dredge_queen.py"


def load_base():
    spec = importlib.util.spec_from_file_location("dredge_queen_detail_sol_base", BASE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


base = load_base()
base.BLEND = HERE / "dredge-queen-detail-sol.blend"
base.GLB = HERE / "dredge-queen-detail-sol.glb"
base.ATLAS_SIZE = 2048

original_cylinder = base.cylinder
original_cone = base.cone
original_torus = base.torus


def detailed_cylinder(*args, vertices=12, **kwargs):
    return original_cylinder(*args, vertices=max(vertices, 16), **kwargs)


def detailed_cone(*args, vertices=12, **kwargs):
    return original_cone(*args, vertices=max(vertices, 16), **kwargs)


def detailed_torus(
    name,
    major_radius,
    minor_radius,
    at,
    region,
    material,
    rotation=(0, 0, 0),
    damage_group=None,
    major_segments=12,
):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=max(major_segments, 20),
        minor_segments=6,
        location=at,
        major_radius=major_radius,
        minor_radius=minor_radius,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return base.tag(obj, region, material, 0, damage_group, smooth=True)


base.cylinder = detailed_cylinder
base.cone = detailed_cone
base.torus = detailed_torus


def disk(
    name: str,
    radius: float,
    depth: float,
    at: tuple[float, float, float],
    region: str,
    material,
    group: str | None = None,
):
    return base.cylinder(
        name,
        radius,
        depth,
        at,
        region,
        material,
        vertices=20,
        rotation=(math.pi / 2, 0, 0),
        bevel=0.004,
        damage_group=group,
    )


def add_claw_detail(parts: list[bpy.types.Object], material) -> None:
    group = "DamageClawArm"
    for side in (-1, 1):
        y = side * 0.48
        parts.extend([
            base.beam(f"Crane lattice outer {side}", (-1.66, y, 1.78), (-2.98, y, 4.55), 0.055, "brass", material, group),
            base.beam(f"Crane lattice diagonal A {side}", (-1.72, y, 2.12), (-2.56, y, 3.18), 0.048, "brass", material, group),
            base.beam(f"Crane lattice diagonal B {side}", (-2.02, y, 2.74), (-2.84, y, 3.82), 0.048, "brass", material, group),
        ])
    for x, z, radius in ((-1.42, 1.48, 0.31), (-2.86, 4.53, 0.28), (-3.60, 4.94, 0.22), (-4.25, 3.20, 0.35)):
        parts.append(disk(f"Claw worked gear {x}", radius, 0.42, (x, 0, z), "brass", material, group))
        parts.append(base.torus(f"Claw gear teeth {x}", radius * 1.12, 0.038, (x, 0, z), "iron", material, rotation=(math.pi / 2, 0, 0), damage_group=group))
    for finger, y in enumerate((-0.58, 0.0, 0.58)):
        for joint, (x, z) in enumerate(((-4.42, 2.72), (-4.68, 2.02), (-4.46, 1.34))):
            parts.append(disk(f"Claw finger {finger} joint {joint}", 0.145, 0.25, (x, y * (1.0 + joint * 0.12), z), "brass", material, group))
    for index, (start, end) in enumerate((
        ((-3.50, -0.31, 4.80), (-4.13, -0.31, 3.38)),
        ((-3.50, 0.31, 4.80), (-4.13, 0.31, 3.38)),
        ((-1.28, -0.58, 1.36), (-2.72, -0.58, 4.36)),
        ((-1.28, 0.58, 1.36), (-2.72, 0.58, 4.36)),
    )):
        parts.append(base.beam(f"Claw tension cable {index}", start, end, 0.034, "rope", material, group))
    for side in (-1, 1):
        y = side * 1.885
        for x in (-3.34, -2.90, -2.46, -2.02, -1.58, -1.14):
            parts.append(disk(f"Fore teal porthole {side} {x}", 0.085, 0.05, (x, y, 0.64), "teal", material))
            parts.append(base.torus(f"Fore porthole rim {side} {x}", 0.105, 0.018, (x, y, 0.64), "brass", material, rotation=(math.pi / 2, 0, 0)))
    for x in (-3.42, -2.92, -2.42, -1.92, -1.42):
        parts.append(base.beam(f"Fore deck rib {x}", (x, -1.64, 0.99), (x, 1.64, 0.99), 0.040, "brass", material))


def add_paddle_detail(parts: list[bpy.types.Object], material, side: int) -> None:
    label = "Port" if side < 0 else "Starboard"
    group = f"Damage{label}Paddle"
    center = Vector((1.35, side * 2.48, 1.64))
    parts.append(base.torus(f"{label} paddle gear ring", 1.13, 0.050, tuple(center), "brass", material, rotation=(math.pi / 2, 0, 0), damage_group=group, major_segments=28))
    parts.append(base.torus(f"{label} paddle hub collar", 0.38, 0.050, tuple(center), "iron", material, rotation=(math.pi / 2, 0, 0), damage_group=group))
    for spoke in range(10):
        angle = math.tau * (spoke + 0.5) / 10
        inner = center + Vector((math.cos(angle) * 0.38, 0, math.sin(angle) * 0.38))
        outer = center + Vector((math.cos(angle) * 1.12, 0, math.sin(angle) * 1.12))
        parts.append(base.beam(f"{label} secondary spoke {spoke}", tuple(inner), tuple(outer), 0.038, "iron", material, group))
    for paddle in range(14):
        angle = math.tau * paddle / 14
        x = center.x + math.cos(angle) * 1.46
        z = center.z + math.sin(angle) * 1.46
        parts.append(disk(f"{label} paddle pin {paddle}", 0.052, 0.44, (x, center.y, z), "brass", material, group))
    for step in range(9):
        angle = math.radians(10 + step * 20)
        x = center.x + math.cos(angle) * 1.64
        z = center.z + math.sin(angle) * 1.64
        parts.append(disk(f"{label} armor rivet {step}", 0.045, 0.42, (x, center.y, z), "brass", material, group))


def add_hold_detail(parts: list[bpy.types.Object], material) -> None:
    for side in (-1, 1):
        y = side * 2.105
        for x in (-0.70, -0.20, 0.30, 0.80, 1.30, 1.80, 2.30, 2.80):
            parts.append(disk(f"Main teal porthole {side} {x}", 0.085, 0.05, (x, y, 0.72), "teal", material, "DamageHoldRear" if x > 1.5 else None))
            parts.append(base.torus(f"Main porthole rim {side} {x}", 0.105, 0.018, (x, y, 0.72), "brass", material, rotation=(math.pi / 2, 0, 0), damage_group="DamageHoldRear" if x > 1.5 else None))
        for x in (-0.94, -0.34, 0.26, 0.86, 1.46, 2.06, 2.66):
            parts.append(base.beam(f"Main armor rib {side} {x}", (x, y, 0.22), (x, y, 1.05), 0.045, "brass", material, "DamageHoldRear" if x > 1.5 else None))
    for side in (-1, 1):
        y = side * 1.315
        for x in (-0.92, -0.48, -0.04):
            parts.append(base.beam(f"Wheelhouse mullion {side} {x}", (x, y, 1.88), (x, y, 2.32), 0.035, "brass", material))
    for index, angle in enumerate((0, math.pi / 4, math.pi / 2, 3 * math.pi / 4)):
        start = (-0.48 + math.cos(angle) * 0.72, math.sin(angle) * 0.88, 2.94)
        end = (-0.48 + math.cos(angle) * 0.30, math.sin(angle) * 0.38, 3.58)
        parts.append(base.beam(f"Wheelhouse dome rib {index}", start, end, 0.045, "brass", material))
    parts.extend([
        base.cylinder("Wheelhouse second stack", 0.14, 0.72, (-0.18, 0.62, 3.26), "soot", material, vertices=18),
        base.torus("Wheelhouse second stack crown", 0.18, 0.032, (-0.18, 0.62, 3.64), "brass", material),
        base.beam("Main mast yardarm", (0.52, -1.58, 4.90), (0.52, 1.58, 4.90), 0.075, "brass", material, "DamageFlag"),
    ])
    for side in (-1, 1):
        y = side * 1.64
        for x in (1.10, 1.54, 1.98, 2.42, 2.86):
            parts.append(base.beam(f"Hold lid rail {side} {x}", (x, y, 2.84), (x, y, 3.08), 0.032, "brass", material, "DamageHoldPortLid" if side < 0 else "DamageHoldStarboardLid"))
    for x in (1.02, 1.52, 2.02, 2.52, 3.00):
        parts.append(disk(f"Hold strap boss {x}", 0.055, 0.12, (x, -1.66, 2.97), "brass", material, "DamageHoldPortLid"))
        parts.append(disk(f"Hold strap boss rear {x}", 0.055, 0.12, (x, 1.66, 2.97), "brass", material, "DamageHoldStarboardLid"))


def build_claw(material):
    parts = base.build_claw(material)
    add_claw_detail(parts, material)
    return parts


def build_paddle(material, side: int):
    parts = base.build_paddle(material, side)
    add_paddle_detail(parts, material, side)
    return parts


def build_hold(material):
    parts = base.build_hold(material)
    add_hold_detail(parts, material)
    return parts


def main() -> None:
    base.reset_scene()
    bpy.context.preferences.filepaths.save_version = 0
    atlas, source_hashes = base.create_atlas()
    material = base.create_material(atlas)
    claw = base.join_component("claw", build_claw(material), material)
    paddle_port = base.join_component("paddle_port", build_paddle(material, -1), material)
    paddle_starboard = base.join_component("paddle_starboard", build_paddle(material, 1), material)
    hold_parts = build_hold(material)
    hold = base.join_component("hold", hold_parts, material)
    objects = (claw, paddle_port, paddle_starboard, hold)
    base.normalize_base_center(objects)
    base.add_damage_shapes(*objects)

    minimum, maximum = base.world_bounds(objects)
    triangles = base.triangle_count(objects)
    assert 12_000 < triangles <= 45_000, f"detail triangle budget failed: {triangles}"
    assert abs((maximum.x - minimum.x) - base.MODEL_LENGTH) < 0.01
    assert abs((maximum.x + minimum.x) * 0.5) < 0.001
    assert abs((maximum.y + minimum.y) * 0.5) < 0.001
    assert abs(minimum.z) < 0.001
    base.export(objects)
    print(json.dumps({
        "blend": str(base.BLEND),
        "glb": str(base.GLB),
        "sha256": hashlib.sha256(base.GLB.read_bytes()).hexdigest(),
        "sourcePlates": source_hashes,
        "objects": [obj.name for obj in objects],
        "damageMorphs": [obj.data.shape_keys.key_blocks[1].name for obj in objects],
        "triangles": triangles,
        "materials": 1,
        "atlas": [base.ATLAS_SIZE, base.ATLAS_SIZE],
        "boundsBlender": {
            "min": [round(value, 6) for value in minimum],
            "max": [round(value, 6) for value in maximum],
        },
    }, indent=2))


if __name__ == "__main__":
    main()
