from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

sys.dont_write_bytecode = True

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REFERENCE = ROOT / "assets/raw/boss-land-yacht.png"
DAMAGE_REFERENCE = ROOT / "assets/raw/boss-land-yacht-damage.png"
BLEND = HERE / "land-yacht.blend"
GLB = HERE / "land-yacht.glb"
MODEL_LENGTH = 9.4


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


dq = load("land_yacht_shared_builder", ROOT / "assets/pilots/dredge-queen-3d/build_dredge_queen.py")
dq.REFERENCE = REFERENCE
dq.DAMAGE_REFERENCE = DAMAGE_REFERENCE


def wheel(parts, name: str, x: float, side: int, material, damaged: bool = False) -> None:
    y, z = side * 1.82, 1.02
    group = f"DamageWheel_{name}"
    parts.append(dq.cylinder(f"{name} armored tire", 0.94, 0.38, (x, y, z), "iron", material,
                             vertices=16, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=group))
    parts.append(dq.torus(f"{name} outer band", 0.76, 0.11, (x, y + side * 0.20, z), "plate", material,
                          rotation=(math.pi / 2, 0, 0), damage_group=group, major_segments=16))
    parts.append(dq.torus(f"{name} brass rim", 0.48, 0.075, (x, y + side * 0.215, z), "brass", material,
                          rotation=(math.pi / 2, 0, 0), damage_group=group, major_segments=16))
    parts.append(dq.cylinder(f"{name} hub", 0.20, 0.52, (x, y + side * 0.11, z), "brass", material,
                             vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=group))
    for index in range(8):
        angle = index * math.tau / 8
        start = (x + math.cos(angle) * 0.20, y + side * 0.30, z + math.sin(angle) * 0.20)
        end = (x + math.cos(angle) * 0.68, y + side * 0.30, z + math.sin(angle) * 0.68)
        parts.append(dq.beam(f"{name} spoke {index}", start, end, 0.065, "brass", material, group))
    if damaged:
        parts.append(dq.box(f"Hidden {name} broken band", (0.52, 0.14, 0.12), (x, y, z),
                            "damage", material, 0.003, damage_group=f"DamageShard_{name}"))


def build_wheels(material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    parts.append(dq.box("Land-yacht armored keel", (7.75, 3.20, 0.92), (0.10, 0, 0.82), "plate", material, 0.10))
    parts.append(dq.box("Land-yacht iron belly", (6.86, 2.92, 0.60), (0.24, 0, 0.30), "soot", material, 0.07))
    parts.append(dq.box("Land-yacht working deck", (7.50, 3.44, 0.20), (0.02, 0, 1.38), "deck", material, 0.025))
    parts.append(dq.cone("Low armored prow", 1.48, 1.08, 1.45, (-4.00, 0, 0.91), "plate", material,
                         vertices=6, rotation=(0, math.pi / 2, 0), damage_group="DamageHullNose"))
    parts.append(dq.ico_sphere("Prow teal search eye", 0.24, (-4.60, -0.02, 0.96), "teal", material,
                               scale=(0.35, 1.0, 1.0)))
    parts.append(dq.torus("Prow search eye cage", 0.27, 0.045, (-4.61, -0.02, 0.96), "brass", material,
                          rotation=(0, math.pi / 2, 0), major_segments=14))
    for side in (-1, 1):
        y = side * 1.70
        parts.append(dq.beam(f"Chassis rail {side}", (-3.65, y, 1.54), (3.78, y, 1.54), 0.10, "brass", material))
        for x in (-3.55, -2.70, -1.85, -1.0, -0.15, 0.70, 1.55, 2.40, 3.25, 3.68):
            parts.append(dq.beam(f"Chassis post {side} {x}", (x, y, 1.36), (x, y, 1.76), 0.07, "brass", material))
        for axle, x in enumerate((-2.25, 0.05, 2.38)):
            wheel(parts, f"{'port' if side < 0 else 'starboard'} wheel {axle + 1}", x, side, material, damaged=axle != 1)
    for x in (-2.25, 0.05, 2.38):
        parts.append(dq.cylinder(f"Axle {x}", 0.13, 3.72, (x, 0, 1.02), "soot", material,
                                 vertices=10, rotation=(math.pi / 2, 0, 0), bevel=0))
    for x in (-3.25, -2.55, -1.85, -1.15, -0.45, 0.25, 0.95, 1.65, 2.35, 3.05):
        for side in (-1, 1):
            parts.append(dq.cylinder(f"Hull rivet {x} {side}", 0.045, 0.055, (x, side * 1.63, 0.88),
                                     "brass", material, vertices=8, rotation=(math.pi / 2, 0, 0), bevel=0))
    parts.append(dq.box("Hidden beached hull tear", (0.72, 0.10, 0.50), (-2.95, 0, 0.62),
                        "damage", material, 0.003, damage_group="DamageHullTear"))
    return parts


def build_crane(material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    arm = "DamageCraneArm"
    parts.append(dq.cylinder("Crane armored turntable", 0.62, 1.42, (-1.65, 0, 1.72), "plate", material,
                             vertices=16, rotation=(math.pi / 2, 0, 0), bevel=0))
    parts.append(dq.torus("Crane turntable collar", 0.66, 0.075, (-1.65, 0, 1.72), "brass", material,
                          rotation=(math.pi / 2, 0, 0), major_segments=16))
    parts.append(dq.box("Crane gearbox", (0.94, 1.16, 0.84), (-1.72, 0, 2.15), "iron", material, 0.05))
    for side in (-1, 1):
        y = side * 0.43
        parts.append(dq.beam(f"Crane boom lower {side}", (-1.70, y, 2.18), (-3.28, y, 4.68),
                             0.18, "iron", material, arm))
        parts.append(dq.beam(f"Crane boom upper {side}", (-3.28, y, 4.68), (-4.16, y, 5.10),
                             0.16, "plate", material, arm))
        parts.append(dq.beam(f"Crane boom brass edge {side}", (-1.62, y, 2.24), (-4.10, y, 5.14),
                             0.07, "brass", material, arm))
    for index in range(8):
        t = index / 7
        x = -1.70 + (-3.28 + 1.70) * t
        z = 2.18 + (4.68 - 2.18) * t
        parts.append(dq.beam(f"Crane ladder rung {index}", (x, -0.46, z), (x, 0.46, z),
                             0.06, "brass", material, arm))
    parts.append(dq.cylinder("Crane crown pulley", 0.46, 0.34, (-3.30, 0, 4.72), "brass", material,
                             vertices=14, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=arm))
    parts.append(dq.torus("Crane crown rim", 0.49, 0.055, (-3.30, 0, 4.72), "brass", material,
                          rotation=(math.pi / 2, 0, 0), damage_group=arm, major_segments=14))
    parts.append(dq.cylinder("Crane tip pulley", 0.33, 0.30, (-4.18, 0, 5.11), "brass", material,
                             vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=arm))
    for cable, y in enumerate((-0.13, 0.13)):
        parts.append(dq.beam(f"Crane cable {cable}", (-4.18, y, 5.04), (-4.18, y, 2.95),
                             0.045, "rope", material, arm))
    parts.append(dq.cylinder("Crane grab gearbox", 0.38, 0.66, (-4.18, 0, 2.78), "plate", material,
                             vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=arm))
    for finger, side in enumerate((-1, 1)):
        points = [(-4.18, side * 0.22, 2.63), (-4.42, side * 0.48, 2.22),
                  (-4.50, side * 0.62, 1.72), (-4.22, side * 0.48, 1.46)]
        for segment, (start, end) in enumerate(zip(points, points[1:])):
            parts.append(dq.beam(f"Crane grab finger {finger} {segment}", start, end, 0.15,
                                 "brass" if segment == 2 else "iron", material, arm))
    for shard, at in enumerate(((-3.86, 0, 4.75), (-4.08, 0.04, 2.78), (-4.12, -0.04, 2.70))):
        parts.append(dq.box(f"Hidden crane shard {shard}", (0.28, 0.08, 0.08), at, "damage", material,
                            0.002, damage_group=f"DamageCraneShard{shard}"))
    return parts


def build_wheelhouse(material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    upper = "DamageWheelhouseUpper"
    parts.append(dq.box("Midships armored works", (3.65, 2.92, 1.24), (0.78, 0, 2.02), "iron", material, 0.08))
    parts.append(dq.box("Wheelhouse octagonal base", (2.55, 2.68, 1.62), (1.45, 0, 3.08),
                        "plate", material, 0.08, damage_group=upper))
    parts.append(dq.cylinder("Wheelhouse glazed drum", 1.42, 0.88, (1.45, 0, 4.04), "teal", material,
                             vertices=10, bevel=0.02, damage_group=upper))
    parts.append(dq.cylinder("Wheelhouse brass window cage", 1.47, 0.16, (1.45, 0, 3.61), "brass", material,
                             vertices=10, bevel=0.01, damage_group=upper))
    parts.append(dq.cylinder("Wheelhouse crown rail", 1.50, 0.16, (1.45, 0, 4.48), "brass", material,
                             vertices=10, bevel=0.01, damage_group=upper))
    parts.append(dq.cone("Wheelhouse armored roof", 1.58, 0.56, 0.55, (1.45, 0, 4.82), "plate", material,
                         vertices=10, damage_group=upper))
    parts.append(dq.cylinder("Wheelhouse cupola", 0.48, 0.54, (1.45, 0, 5.28), "teal", material,
                             vertices=10, bevel=0.015, damage_group=upper))
    parts.append(dq.cone("Wheelhouse cupola cap", 0.58, 0.10, 0.35, (1.45, 0, 5.72), "brass", material,
                         vertices=10, damage_group=upper))
    for index in range(10):
        angle = index * math.tau / 10
        x, y = 1.45 + math.cos(angle) * 1.44, math.sin(angle) * 1.44
        parts.append(dq.beam(f"Wheelhouse mullion {index}", (x, y, 3.60), (x, y, 4.48),
                             0.075, "brass", material, upper))
    parts.append(dq.cylinder("Main soot stack", 0.28, 2.22, (-0.48, -0.56, 3.28), "soot", material,
                             vertices=14, bevel=0.02))
    parts.append(dq.torus("Main stack crown", 0.34, 0.055, (-0.48, -0.56, 4.42), "brass", material,
                          major_segments=14))
    parts.append(dq.cylinder("Auxiliary brass stack", 0.16, 1.24, (3.10, 0.90, 2.96), "brass", material,
                             vertices=10, bevel=0.01))
    for side in (-1, 1):
        y = side * 1.48
        parts.append(dq.beam(f"Upper promenade rail {side}", (-0.80, y, 2.85), (3.35, y, 2.85),
                             0.07, "brass", material))
        for x in (-0.72, 0.0, 0.72, 2.12, 2.82, 3.30):
            parts.append(dq.beam(f"Upper promenade post {side} {x}", (x, y, 2.55), (x, y, 2.90),
                                 0.055, "brass", material))
        parts.append(dq.cylinder(f"Wheelhouse teal lantern {side}", 0.12, 0.36, (2.78, side * 1.58, 3.32),
                                 "teal", material, vertices=10, bevel=0))
        parts.append(dq.torus(f"Wheelhouse lantern cage {side}", 0.14, 0.028,
                              (2.78, side * 1.58, 3.32), "brass", material,
                              rotation=(math.pi / 2, 0, 0), major_segments=10))
    parts.append(dq.box("Wheelhouse forward wheel emblem", (0.10, 0.82, 0.82), (0.14, 0, 3.98),
                        "brass", material, 0.02, damage_group=upper))
    for shard, at in enumerate(((1.45, 0, 3.92), (1.50, 0.04, 3.90), (1.38, -0.03, 3.88))):
        parts.append(dq.box(f"Hidden glass shard {shard}", (0.24, 0.06, 0.18), at, "damage", material,
                            0.002, damage_group=f"DamageGlassShard{shard}"))
    parts.append(dq.box("Hidden wheelhouse breach", (0.08, 0.58, 0.66), (0.15, 0, 3.92),
                        "damage", material, 0.002, damage_group="DamageWheelhouseBreach"))
    return parts


def add_damage_shapes(wheels, crane, wheelhouse) -> None:
    def group_bounds(obj: bpy.types.Object, group_name: str) -> tuple[Vector, Vector]:
        points = [obj.data.vertices[index].co for index in dq.group_vertex_indices(obj, group_name)]
        assert points, f"missing damage group {obj.name}:{group_name}"
        return (
            Vector(tuple(min(point[axis] for point in points) for axis in range(3))),
            Vector(tuple(max(point[axis] for point in points) for axis in range(3))),
        )

    def group_center(obj: bpy.types.Object, group_name: str) -> Vector:
        minimum, maximum = group_bounds(obj, group_name)
        return (minimum + maximum) * 0.5

    wheels.shape_key_add(name="Basis")
    beached = wheels.shape_key_add(name="Damage_BeachedWheels")
    wheel_names = tuple(f"{side} wheel {axle}" for side in ("port", "starboard") for axle in (1, 2, 3))
    # All pivots are derived from the normalized production geometry.  Hard-coded
    # construction-space centers become stale after the required base-center pass.
    wheel_centers = {name: group_center(wheels, f"DamageWheel_{name}") for name in wheel_names}
    for name, center in wheel_centers.items():
        for index in dq.group_vertex_indices(wheels, f"DamageWheel_{name}"):
            co = beached.data[index].co
            dq.rotate_y(co, center, math.radians(24 if "wheel 1" in name else -15 if "wheel 3" in name else 7))
            co.z -= 0.46 if "wheel 1" in name else 0.25 if "wheel 3" in name else 0.16
            co.y += -0.38 if "port" in name else 0.38
    for index in dq.group_vertex_indices(wheels, "DamageHullNose"):
        beached.data[index].co.z -= 0.26
    for index in dq.group_vertex_indices(wheels, "DamageHullTear"):
        beached.data[index].co += Vector((-0.60, -1.55, -0.34))
    for name, center in wheel_centers.items():
        if "wheel 2" in name:
            continue
        for index in dq.group_vertex_indices(wheels, f"DamageShard_{name}"):
            beached.data[index].co += Vector((-0.25 if "wheel 1" in name else 0.35,
                                             -1.45 if "port" in name else 1.45, -0.55))

    crane.shape_key_add(name="Basis")
    slack = crane.shape_key_add(name="Damage_SlackCrane")
    crane_minimum, crane_maximum = group_bounds(crane, "DamageCraneArm")
    pivot = Vector((crane_maximum.x, (crane_minimum.y + crane_maximum.y) * 0.5, crane_minimum.z))
    for index in dq.group_vertex_indices(crane, "DamageCraneArm"):
        co = slack.data[index].co
        dq.rotate_y(co, pivot, math.radians(-26))
        co.z -= 0.30
    for shard, move in enumerate((Vector((-0.35, -0.40, -0.40)), Vector((-0.55, 0.45, -0.52)), Vector((0.10, 0.70, -0.66)))):
        for index in dq.group_vertex_indices(crane, f"DamageCraneShard{shard}"):
            slack.data[index].co += move

    wheelhouse.shape_key_add(name="Basis")
    cracked = wheelhouse.shape_key_add(name="Damage_CrackedWheelhouse")
    house_minimum, house_maximum = group_bounds(wheelhouse, "DamageWheelhouseUpper")
    pivot = Vector(((house_minimum.x + house_maximum.x) * 0.5,
                    (house_minimum.y + house_maximum.y) * 0.5,
                    house_minimum.z))
    for index in dq.group_vertex_indices(wheelhouse, "DamageWheelhouseUpper"):
        co = cracked.data[index].co
        dq.rotate_y(co, pivot, math.radians(14))
        co.x += max(0.0, co.z - 3.0) * 0.12
        co.z -= max(0.0, co.x - 1.0) * 0.10
    for shard, move in enumerate((Vector((-1.20, -1.55, -1.10)), Vector((-0.45, 1.75, -1.20)), Vector((0.95, -1.30, -1.02)))):
        for index in dq.group_vertex_indices(wheelhouse, f"DamageGlassShard{shard}"):
            cracked.data[index].co += move
    for index in dq.group_vertex_indices(wheelhouse, "DamageWheelhouseBreach"):
        cracked.data[index].co += Vector((-0.18, -1.42, -0.16))

    for obj in (wheels, crane, wheelhouse):
        obj.active_shape_key_index = 0
        for key in obj.data.shape_keys.key_blocks:
            key.value = 0.0


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    dq.reset_scene()
    atlas, source_hashes = dq.create_atlas()
    atlas.name = "LandYachtPaintedAtlas"
    material = dq.create_material(atlas)
    material.name = "LandYachtPaintedMaterial"
    wheels = dq.join_component("wheels", build_wheels(material), material)
    crane = dq.join_component("crane", build_crane(material), material)
    wheelhouse = dq.join_component("wheelhouse", build_wheelhouse(material), material)
    objects = (wheels, crane, wheelhouse)
    dq.MODEL_LENGTH = MODEL_LENGTH
    dq.normalize_base_center(objects)
    add_damage_shapes(*objects)
    triangles = dq.triangle_count(objects)
    minimum, maximum = dq.world_bounds(objects)
    assert triangles <= 12_000
    assert abs(maximum.x - minimum.x - MODEL_LENGTH) < 0.01
    assert abs(minimum.z) < 0.001
    assert abs((maximum.x + minimum.x) * 0.5) < 0.001
    assert abs((maximum.y + minimum.y) * 0.5) < 0.001
    dq.BLEND, dq.GLB = BLEND, GLB
    dq.export(objects)
    print(json.dumps({
        "blend": str(BLEND), "glb": str(GLB), "sha256": hashlib.sha256(GLB.read_bytes()).hexdigest(),
        "sourcePlates": {str(REFERENCE.relative_to(ROOT)): source_hashes["intact"],
                         str(DAMAGE_REFERENCE.relative_to(ROOT)): source_hashes["damage"]},
        "components": [obj.name for obj in objects],
        "damageMorphs": [obj.data.shape_keys.key_blocks[1].name for obj in objects],
        "triangles": triangles,
        "boundsBlender": {"min": [round(v, 6) for v in minimum], "max": [round(v, 6) for v in maximum]},
    }, indent=2))


if __name__ == "__main__":
    main()
