from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

sys.dont_write_bytecode = True

import bpy
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REFERENCE = ROOT / "assets/raw/boss-land-yacht.png"
DAMAGE_REFERENCE = ROOT / "assets/raw/boss-land-yacht-damage.png"
BLEND = HERE / "land-yacht.blend"
GLB = HERE / "land-yacht.glb"
MODEL_LENGTH = 9.4
CRANE_TIP_X = -4.62
ATLAS_SOURCE = ROOT / "assets/raw/land-yacht-atlas-fidelity-e4.png"
REGIONS = {
    # Interior samples avoid atlas borders and limit broad metal streaks.
    "plate": (0.015, 0.690, 0.235, 0.830),
    "brass": (0.270, 0.620, 0.480, 0.830),
    "iron": (0.520, 0.620, 0.730, 0.830),
    "teal": (0.770, 0.620, 0.980, 0.830),
    "deck": (0.008, 0.008, 0.242, 0.492),
    "rope": (0.258, 0.008, 0.492, 0.492),
    "trim": (0.520, 0.120, 0.730, 0.330),
    "damage": (0.770, 0.120, 0.980, 0.330),
}
REGIONS["soot"] = REGIONS["iron"]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


dq = load("land_yacht_shared_kit", ROOT / "assets/pilots/dredge-queen-3d/detail_opus5_kit.py")


def create_atlas():
    atlas = bpy.data.images.load(str(ATLAS_SOURCE), check_existing=False)
    atlas.name = "LandYachtPaintedAtlas"
    atlas.colorspace_settings.name = "sRGB"
    atlas.scale(1024, 1024)
    atlas.pack()
    return atlas


def wheel(parts, name: str, x: float, side: int, material) -> None:
    y, z = side * 1.82, 1.15
    group = f"DamageWheel_{name}"
    parts.append(dq.cylinder(f"{name} armored tire", 1.10, 0.46, (x, y, z), "iron", material,
                             vertices=16, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=group))
    parts.append(dq.torus(f"{name} outer band", 0.92, 0.11, (x, y + side * 0.25, z), "plate", material,
                          rotation=(math.pi / 2, 0, 0), damage_group=group, major_segments=16, minor_segments=4))
    parts.append(dq.torus(f"{name} brass rim", 0.58, 0.065, (x, y + side * 0.265, z), "trim", material,
                          rotation=(math.pi / 2, 0, 0), damage_group=group, major_segments=16, minor_segments=4))
    for index in range(8):
        a, b = index * math.tau / 8 + 0.035, (index + 1) * math.tau / 8 - 0.035
        sector = [(x + math.cos(angle) * radius, y + side * depth, z + math.sin(angle) * radius)
                  for depth in (0.28, 0.36) for radius, angle in ((0.61, a), (0.89, a), (0.89, b), (0.61, b))]
        plate = dq.loft(f"{name} armored face sector {index}", [sector[:4], sector[4:]],
                        "plate", material, damage_group=group)
        if index == 1 and 'wheel 1' in name:
            dq.mark_all(plate, f"DamageWheelMissingArmor_{name}")
        parts.append(plate)
    parts.append(dq.cylinder(f"{name} hub flange", 0.35, 0.60, (x, y, z), "iron", material,
                             vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=group))
    parts.append(dq.cylinder(f"{name} stepped hub", 0.27, 0.68, (x, y, z), "brass", material,
                             vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=group))
    for index in range(16):
        angle = index * math.tau / 16
        parts.append(dq.box(f"{name} tread armor {index}", (0.18, 0.52, 0.34),
                            (x + math.cos(angle) * 1.08, y, z + math.sin(angle) * 1.08),
                            "plate", material, bevel=0, rotation=(0, -angle, 0), damage_group=group))
    parts.append(dq.cylinder(f"{name} hub", 0.20, 0.52, (x, y + side * 0.11, z), "brass", material,
                             vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=group))
    for index in range(8):
        angle = index * math.tau / 8
        start = (x + math.cos(angle) * 0.20, y + side * 0.30, z + math.sin(angle) * 0.20)
        end = (x + math.cos(angle) * 0.85, y + side * 0.30, z + math.sin(angle) * 0.85)
        parts.append(dq.beam(f"{name} spoke {index}", start, end, 0.065, "brass", material, group))


def build_wheels(material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    hull = dq.hull_loft("Land-yacht curved armored hull", [
        (-4.65, 0.20, 1.35, 3.00), (-4.05, 1.08, 0.78, 2.84),
        (-3.30, 1.72, 0.55, 2.72), (-1.70, 1.78, 0.50, 2.70),
        (1.80, 1.78, 0.50, 2.70), (3.40, 1.63, 0.75, 2.73),
        (3.90, 1.35, 1.02, 2.78),
    ], "plate", material, damage_group="DamageHullNose")
    parts.append(hull)
    edge = [(-4.68, 0.24, 3.06), (-4.10, 1.16, 2.92), (-3.30, 1.82, 2.82),
            (3.45, 1.82, 2.82), (4.02, 1.43, 2.85)]
    outline = edge + [(x, -y, z) for x, y, z in reversed(edge)]
    parts.append(dq.loft("Land-yacht shaped working deck", [
        [(x, y, z - 0.14) for x, y, z in outline], outline,
    ], "deck", material))
    dq.lens(parts, "Prow search eye", 0.25, (-4.61, 0, 1.96), material,
            rotation=(0, math.pi / 2, 0), damage_group="DamageHullNose")
    for side in (-1, 1):
        rail = [(x, side * y, z + 0.40) for x, y, z in edge]
        for index, (start, end) in enumerate(zip(rail, rail[1:])):
            parts.append(dq.beam(f"Curved deck rail {side} {index}", start, end, 0.055, "trim", material))
        for index, (x, y, z) in enumerate(rail):
            parts.append(dq.beam(f"Deck curve post {side} {index}", (x, y, z - 0.4), (x, y, z), 0.045, "brass", material))
        for x in (-2.70, -1.85, -1.0, -0.15, 0.70, 1.55, 2.40, 3.25):
            parts.append(dq.beam(f"Chassis post {side} {x}", (x, side * 1.82, 2.82),
                                 (x, side * 1.82, 3.22), 0.045, "brass", material))
        for axle, x in enumerate((-2.45, 0.05, 2.55)):
            wheel(parts, f"{'port' if side < 0 else 'starboard'} wheel {axle + 1}", x, side, material)
    for x in (-2.45, 0.05, 2.55):
        parts.append(dq.cylinder(f"Axle {x}", 0.13, 3.72, (x, 0, 1.15), "soot", material,
                                 vertices=10, rotation=(math.pi / 2, 0, 0), bevel=0))
    for x in (-3.25, -2.55, -1.85, -1.15, -0.45, 0.25, 0.95, 1.65, 2.35, 3.05):
        for side in (-1, 1):
            hit, at, normal, _ = hull.ray_cast(Vector((x, side * 3, 1.84)), Vector((0, -side, 0)))
            assert hit and normal.y * side > 0, f'missing outer hull at rivet {x}:{side}'
            parts.append(dq.cylinder(f"Hull rivet {x} {side}", 0.045, 0.055, tuple(at + normal * 0.018),
                                     "brass", material, vertices=6,
                                     rotation=tuple(normal.to_track_quat('Z', 'Y').to_euler()), bevel=0,
                                     damage_group="DamageHullNose"))
    return parts


def build_crane(material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    arm = "DamageCraneArm"
    parts.append(dq.cylinder("Crane armored turntable", 0.74, 0.44, (-1.65, 0, 1.61), "plate", material,
                             vertices=16, bevel=0))
    parts.append(dq.torus("Crane turntable collar", 0.78, 0.075, (-1.65, 0, 1.80), "brass", material,
                          major_segments=16, minor_segments=4))
    parts.append(dq.box("Crane gearbox", (0.94, 1.16, 0.84), (-1.72, 0, 2.15), "iron", material, 0.05))
    for side in (-1, 1):
        y = side * 0.43
        parts.append(dq.beam(f"Crane boom lower {side}", (-1.70, y, 2.18), (-3.28, y, 4.68),
                             0.18, "iron", material, arm))
        parts.append(dq.beam(f"Crane boom upper {side}", (-3.28, y, 4.68), (CRANE_TIP_X + 0.02, y, 5.10),
                             0.16, "plate", material, arm))
        parts.append(dq.beam(f"Crane boom brass edge {side}", (-1.62, y, 2.24), (CRANE_TIP_X + 0.08, y, 5.14),
                             0.07, "brass", material, arm))
    for index in range(8):
        t = index / 7
        x = -1.70 + (-3.28 + 1.70) * t
        z = 2.18 + (4.68 - 2.18) * t
        parts.append(dq.beam(f"Crane ladder rung {index}", (x, -0.46, z), (x, 0.46, z),
                             0.06, "brass", material, arm))
    parts.append(dq.cylinder("Crane crown pulley", 0.46, 0.34, (-3.30, 0, 4.72), "iron", material,
                             vertices=14, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=arm))
    parts.append(dq.torus("Crane crown rim", 0.49, 0.055, (-3.30, 0, 4.72), "brass", material,
                          rotation=(math.pi / 2, 0, 0), damage_group=arm, major_segments=14))
    parts.append(dq.cylinder("Crane tip pulley", 0.33, 0.30, (CRANE_TIP_X, 0, 5.11), "iron", material,
                             vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=arm))
    for name, x, z, radius, depth in (("crown", -3.30, 4.72, 0.16, 0.42), ("tip", CRANE_TIP_X, 5.11, 0.12, 0.38)):
        parts.append(dq.cylinder(f"Crane {name} brass hub", radius, depth, (x, 0, z), "trim", material,
                                 vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=arm))
    for side in (-1, 1):
        parts.append(dq.beam(f"Crane rear brace {side}", (-1.65, side * 0.34, 2.15),
                             (-1.0, side * 0.34, 4.08), 0.11, "iron", material, arm))
        start, end = Vector((-3.30, side * 0.35, 4.78)), Vector((-1.0, side * 0.35, 4.08))
        parts.append(dq.swept_tube(f"Crane tension cable {side}",
                                   [tuple(start.lerp(end, index / 6)) for index in range(7)],
                                   [0.022] * 7, "rope", material, sides=4,
                                   damage_group=f"DamageTensionCable{side}"))
    for cable, y in enumerate((-0.13, 0.13)):
        parts.append(dq.beam(f"Crane cable {cable}", (CRANE_TIP_X, y, 5.04), (CRANE_TIP_X, y, 3.65),
                             0.045, "rope", material, f"DamageHoistCable{cable}"))
    parts.append(dq.cylinder("Crane grab gearbox", 0.26, 0.40, (CRANE_TIP_X, 0, 3.47), "plate", material,
                             vertices=12, bevel=0, damage_group="DamageCraneGrab"))
    for finger in range(4):
        angle = finger * math.tau / 4 + math.pi / 4
        points = [(CRANE_TIP_X + math.cos(angle) * radius, math.sin(angle) * radius, z)
                  for radius, z in ((0.23, 3.35), (0.50, 3.10), (0.69, 2.79), (0.65, 2.58), (0.50, 2.45))]
        parts.append(dq.swept_tube(f"Crane grab finger {finger}", points,
                                   [0.10, 0.10, 0.085, 0.06, 0.018], "iron", material,
                                   sides=6, damage_group="DamageCraneGrab"))
    for part in parts:
        part.location.z += 1.43
    return parts


def build_wheelhouse(material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    upper = "DamageWheelhouseUpper"
    parts.append(dq.box("Midships armored works", (3.65, 2.92, 1.24), (0.78, 0, 2.02), "iron", material, 0.08))
    parts.append(dq.box("Wheelhouse promenade deck", (4.10, 3.25, 0.14), (1.03, 0, 2.67),
                        "plate", material, 0.02))
    parts.append(dq.box("Wheelhouse octagonal base", (2.55, 2.68, 0.98), (1.45, 0, 2.76),
                        "plate", material, 0.08, damage_group=upper))
    parts.append(dq.cylinder("Wheelhouse dark interior", 1.29, 1.30, (1.45, 0, 3.83), "damage", material,
                             vertices=10, bevel=0))
    for index in range(10):
        a, b = index * math.tau / 10, (index + 1) * math.tau / 10
        pane = [(1.45 + math.cos(angle) * 1.42, math.sin(angle) * 1.42, z)
                for angle, z in ((a, 3.18), (b, 3.18), (b, 4.48), (a, 4.48))]
        parts.append(dq.from_pydata(f"Wheelhouse glazed pane {index}", pane, [(0, 1, 2, 3)],
                                    "teal", material, damage_group="DamageMissingPane" if index == 4 else None))
        if index == 4:
            # This small remnant sits behind the intact pane and stays at the frame
            # when the damaged pane recedes into the dark interior.
            remnant = [Vector(pane[3]), Vector(pane[3]).lerp(Vector(pane[2]), 0.52),
                       Vector(pane[3]).lerp(Vector(pane[0]), 0.32)]
            parts.append(dq.from_pydata("Wheelhouse broken pane remnant",
                [(1.45 + (p.x - 1.45) * 0.995, p.y * 0.995, p.z) for p in remnant],
                [(0, 1, 2)], "teal", material))
    parts.append(dq.cylinder("Wheelhouse brass window cage", 1.47, 0.12, (1.45, 0, 3.19), "brass", material,
                             vertices=10, bevel=0.01, damage_group=upper))
    parts.append(dq.cylinder("Wheelhouse crown rail", 1.50, 0.16, (1.45, 0, 4.48), "brass", material,
                             vertices=10, bevel=0.01, damage_group=upper))
    parts.append(dq.cone("Wheelhouse armored roof", 1.60, 1.42, 0.12, (1.45, 0, 4.60), "plate", material,
                         vertices=10, damage_group=upper))
    parts.append(dq.cylinder("Wheelhouse cupola", 0.42, 0.46, (1.45, 0, 4.89), "teal", material,
                             vertices=10, bevel=0.015, damage_group=upper))
    parts.append(dq.cone("Wheelhouse cupola cap", 0.54, 0.10, 0.25, (1.45, 0, 5.245), "brass", material,
                         vertices=10, damage_group=upper))
    for index in range(10):
        angle = index * math.tau / 10
        x, y = 1.45 + math.cos(angle) * 1.44, math.sin(angle) * 1.44
        parts.append(dq.beam(f"Wheelhouse mullion {index}", (x, y, 3.18), (x, y, 4.48),
                             0.075, "brass", material, upper))
        parts.append(dq.beam(f"Wheelhouse roof rail post {index}", (x, y, 4.66), (x, y, 5.02),
                             0.045, "trim", material, upper))
    parts.append(dq.torus("Wheelhouse roof viewing rail", 1.44, 0.035, (1.45, 0, 5.02),
                          "trim", material, damage_group=upper, major_segments=10, minor_segments=4))
    parts.append(dq.cylinder("Main soot stack", 0.28, 2.22, (-0.48, -0.56, 3.28), "soot", material,
                             vertices=14, bevel=0.02))
    parts.append(dq.torus("Main stack crown", 0.34, 0.055, (-0.48, -0.56, 4.42), "brass", material,
                          major_segments=14))
    parts.append(dq.cylinder("Auxiliary brass stack", 0.16, 1.24, (3.10, 0.90, 2.96), "brass", material,
                             vertices=10, bevel=0.01))
    for side in (-1, 1):
        y = side * 1.48
        for x in (-0.25, 1.15):
            at = (x, side * 1.47, 2.12)
            parts.append(dq.cylinder(f"Lower deck porthole {side} {x}", 0.20, 0.035, at,
                                     "teal", material, vertices=8, rotation=(math.pi / 2, 0, 0), bevel=0))
            parts.append(dq.torus(f"Lower deck porthole frame {side} {x}", 0.23, 0.045, at,
                                  "trim", material, rotation=(math.pi / 2, 0, 0), major_segments=8, minor_segments=4))
        parts.append(dq.beam(f"Upper promenade rail {side}", (-0.80, y, 2.85), (3.35, y, 2.85),
                             0.07, "brass", material))
        for x in (-0.72, 0.0, 0.72, 2.12, 2.82, 3.30):
            parts.append(dq.beam(f"Upper promenade post {side} {x}", (x, y, 2.55), (x, y, 2.90),
                                 0.055, "brass", material))
        parts.append(dq.cylinder(f"Wheelhouse teal lantern {side}", 0.12, 0.36, (2.78, side * 1.58, 3.32),
                                 "teal", material, vertices=10, bevel=0))
        mullion = next(part for part in parts if part.name == f"Wheelhouse mullion {1 if side > 0 else 9}")
        bracket_end = (2.78, side * 1.58, mullion.location.z)
        parts.append(dq.beam(f"Lantern bracket {side}", tuple(mullion.location),
                             bracket_end, 0.055, "iron", material))
        parts.append(dq.beam(f"Lantern hanger {side}", bracket_end,
                             (2.78, side * 1.58, 3.48), 0.035, "brass", material))
        parts.append(dq.torus(f"Wheelhouse lantern cage {side}", 0.14, 0.028,
                              (2.78, side * 1.58, 3.32), "brass", material,
                              rotation=(math.pi / 2, 0, 0), major_segments=10))
    parts.append(dq.torus("Wheelhouse captain wheel", 0.35, 0.045, (-0.02, 0, 3.99),
                          "trim", material, rotation=(0, math.pi / 2, 0), major_segments=12,
                          minor_segments=4, damage_group=upper))
    for index in range(8):
        angle = index * math.tau / 8
        parts.append(dq.beam(f"Captain wheel spoke {index}", (-0.04, 0, 3.99),
                             (-0.04, math.cos(angle) * 0.43, 3.99 + math.sin(angle) * 0.43),
                             0.035, "brass", material, upper))
    for part in parts:
        if part.name.startswith(("Wheelhouse glazed pane", "Wheelhouse mullion")):
            dq.mark_all(part, "DamageWindowGlazing")
        part.location.z += 1.43
    return parts


def add_damage_shapes(wheels, crane, wheelhouse, source_scale: float) -> None:
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
        indices = dq.group_vertex_indices(wheels, f"DamageWheel_{name}")
        side = -1 if "port" in name else 1
        tilt = Matrix.Rotation(math.radians(side * 12), 3, 'X')
        for index in indices:
            co = beached.data[index].co
            dq.rotate_y(co, center, math.radians(24 if "wheel 1" in name else -15 if "wheel 3" in name else 7))
            co[:] = center + tilt @ (co - center)
            drop = 0.30 if "wheel 1" in name else 0.18 if "wheel 3" in name else 0.12
            # Crush the lower tread against the support plane; translating a
            # whole tire downward made the damaged wheels disappear underground.
            co.z = max(0.015 * source_scale, co.z - drop * source_scale)
            co.y += side * 0.14 * source_scale
        assert min(beached.data[index].co.z for index in indices) >= 0
        if 'wheel 1' in name:
            for index in dq.group_vertex_indices(wheels, f"DamageWheelMissingArmor_{name}"):
                co = beached.data[index].co
                co.x = center.x + (co.x - center.x) * 0.68
                co.z = center.z + (co.z - center.z) * 0.68
                co.y -= side * 0.30 * source_scale
    low, high = group_bounds(wheels, "DamageHullNose")
    for index in dq.group_vertex_indices(wheels, "DamageHullNose"):
        co = beached.data[index].co
        nose = max(0.0, 1.0 - (co.x - low.x) / ((high.x - low.x) * 0.28))
        co.z -= 0.26 * source_scale * nose

    crane.shape_key_add(name="Basis")
    slack = crane.shape_key_add(name="Damage_SlackCrane")
    for index in dq.group_vertex_indices(crane, "DamageCraneGrab"):
        slack.data[index].co.z -= 0.25 * source_scale
    for side in (-1, 1):
        name = f"DamageTensionCable{side}"
        low, high = group_bounds(crane, name)
        for index in dq.group_vertex_indices(crane, name):
            co = slack.data[index].co
            t = (co.x - low.x) / (high.x - low.x)
            co.z -= math.sin(math.pi * t) * 0.55 * source_scale
    for cable in range(2):
        name = f"DamageHoistCable{cable}"
        low, high = group_bounds(crane, name)
        for index in dq.group_vertex_indices(crane, name):
            co = slack.data[index].co
            bottom = (high.z - co.z) / (high.z - low.z)
            co.z -= bottom * (0.25 if cable == 0 else 0.75) * source_scale
            if cable == 1:
                co.y += bottom * 0.30 * source_scale

    wheelhouse.shape_key_add(name="Basis")
    cracked = wheelhouse.shape_key_add(name="Damage_CrackedWheelhouse")
    low, high = group_bounds(wheelhouse, "DamageWindowGlazing")
    center = (low + high) * 0.5
    for index in dq.group_vertex_indices(wheelhouse, "DamageWindowGlazing"):
        co = cracked.data[index].co
        front = max(0.0, min(1.0, (center.x - co.x) / (center.x - low.x)))
        co.x += 0.12 * source_scale * front
        co.z -= 0.06 * source_scale * front
    for index in dq.group_vertex_indices(wheelhouse, "DamageMissingPane"):
        co = cracked.data[index].co
        co.x = center.x + (co.x - center.x) * 0.75
        co.y = center.y + (co.y - center.y) * 0.75
        co.z -= 0.15 * source_scale

    for obj in (wheels, crane, wheelhouse):
        obj.active_shape_key_index = 0
        for key in obj.data.shape_keys.key_blocks:
            key.value = 0.0


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    dq.reset_scene()
    atlas = create_atlas()
    material = dq.create_material("LandYachtPaintedMaterial", atlas)
    shader = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    shader.inputs['Metallic'].default_value = 0.35
    shader.inputs['Roughness'].default_value = 0.65
    assemblies = {"wheels": build_wheels(material), "crane": build_crane(material),
                  "wheelhouse": build_wheelhouse(material)}
    bpy.context.view_layer.update()
    parts_by_name = {part.name: part for parts in assemblies.values() for part in parts}
    def points(name):
        obj = parts_by_name[name]
        return [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    deck = points('Land-yacht shaped working deck')
    deck_height = max(point.z for point in deck if -3.31 < point.x < 3.46)
    turntable_gap = min(point.z for point in points('Crane armored turntable')) - deck_height
    house_gap = min(point.z for point in points('Midships armored works')) - deck_height
    grab_clearance = min(point.z for name in parts_by_name if name.startswith('Crane grab')
                         for point in points(name)) - max(point.z for point in deck)
    assert abs(turntable_gap) < 0.01, f'turntable is not seated: {turntable_gap}'
    assert -0.01 <= house_gap <= 0.03, f'wheelhouse is not seated: {house_gap}'
    assert grab_clearance > 0.65, f'grab is not clear of the deck: {grab_clearance}'
    # Tiny rail/spoke bevels do not survive the game camera. Keep the larger worked
    # edges and spend the triangle budget on hull shape, wheel armor and machinery.
    for parts in assemblies.values():
        for part in parts:
            for modifier in list(part.modifiers):
                if modifier.type == 'BEVEL' and modifier.width <= 0.006001:
                    part.modifiers.remove(modifier)
    objects = tuple(dq.join_component(name, parts, material, REGIONS)
                    for name, parts in assemblies.items())
    initial_minimum, initial_maximum = dq.world_bounds(objects)
    source_scale = MODEL_LENGTH / (initial_maximum.x - initial_minimum.x)
    dq.normalize_base_center(objects, axis=0, target=MODEL_LENGTH)
    add_damage_shapes(*objects, source_scale)
    triangles = dq.triangle_count(objects)
    minimum, maximum = dq.world_bounds(objects)
    print(f"Candidate triangles before export: {triangles}")
    assert triangles <= 12_000, f"candidate exceeds triangle ceiling: {triangles}"
    assert abs(maximum.x - minimum.x - MODEL_LENGTH) < 0.01
    assert abs(minimum.z) < 0.001
    assert abs((maximum.x + minimum.x) * 0.5) < 0.001
    assert abs((maximum.y + minimum.y) * 0.5) < 0.001
    dq.export(objects, BLEND, GLB)
    print(json.dumps({
        "blend": str(BLEND), "glb": str(GLB), "sha256": hashlib.sha256(GLB.read_bytes()).hexdigest(),
        "sourcePlates": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in (REFERENCE, DAMAGE_REFERENCE, ATLAS_SOURCE)},
        "components": [obj.name for obj in objects],
        "damageMorphs": [obj.data.shape_keys.key_blocks[1].name for obj in objects],
        "triangles": triangles,
        "trianglesByComponent": {obj.name: dq.triangle_count((obj,)) for obj in objects},
        "constructionClearance": {"turntableGap": turntable_gap, "wheelhouseGap": house_gap,
                                  "grabAboveHighestDeck": grab_clearance},
        "boundsBlender": {"min": [round(v, 6) for v in minimum], "max": [round(v, 6) for v in maximum]},
    }, indent=2))


if __name__ == "__main__":
    main()
