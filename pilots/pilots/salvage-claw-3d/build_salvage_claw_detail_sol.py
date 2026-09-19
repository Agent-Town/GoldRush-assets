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
BLEND = HERE / "salvage-claw-detail-sol.blend"
GLB = HERE / "salvage-claw-detail-sol.glb"
MODEL_DIAMETER = 11.4


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


base = load("salvage_claw_detail_sol_base", HERE / "build_salvage_claw.py")
dq = base.dq
original_cylinder = dq.cylinder
original_cone = dq.cone
original_torus = dq.torus


def raise_resolution() -> None:
    def cylinder(*args, **kwargs):
        kwargs["vertices"] = max(kwargs.get("vertices", 12), 24)
        return original_cylinder(*args, **kwargs)

    def cone(*args, **kwargs):
        kwargs["vertices"] = max(kwargs.get("vertices", 12), 20)
        return original_cone(*args, **kwargs)

    def torus(*args, **kwargs):
        kwargs["major_segments"] = max(kwargs.get("major_segments", 12), 24)
        return original_torus(*args, **kwargs)

    dq.cylinder = cylinder
    dq.cone = cone
    dq.torus = torus


def add_crown_detail(parts: list[bpy.types.Object], material: bpy.types.Material) -> None:
    upper = "LandingCrownUpper"
    glow = "LandingCrownGlow"

    # A layered truss cage and hanging city teeth carry the source plate at game distance.
    for level, radius in ((2.42, 2.48), (2.82, 3.02), (3.28, 3.36)):
        parts.append(dq.torus(f"Underslung truss ring {level}", radius, 0.055, (0, 0, level), "brass", material, major_segments=32))
    for index in range(24):
        angle = math.tau * index / 24
        next_angle = angle + math.tau / 24
        inner = Vector((math.cos(angle) * 2.48, math.sin(angle) * 2.48, 2.42))
        outer = Vector((math.cos(next_angle) * 3.36, math.sin(next_angle) * 3.36, 3.28))
        parts.append(dq.beam(f"Underslung diagonal {index}", tuple(inner), tuple(outer), 0.052, "iron", material))
        keel = Vector((math.cos(angle) * 0.62, math.sin(angle) * 0.62, 1.42))
        parts.append(dq.beam(f"Keel radial rib {index}", tuple(keel), tuple(inner), 0.048, "brass", material))

    for index in range(12):
        angle = math.tau * index / 12 + math.pi / 12
        direction = Vector((math.cos(angle), math.sin(angle), 0))
        tangent = Vector((-direction.y, direction.x, 0))
        root = direction * 2.72 + Vector((0, 0, 4.04))
        shoulder = direction * 2.18 + Vector((0, 0, 5.10))
        parts.append(dq.beam(f"Flying buttress outer {index}", tuple(root), tuple(shoulder), 0.080, "iron", material, upper))
        parts.append(dq.beam(f"Flying buttress brass edge {index}", tuple(root + tangent * 0.07), tuple(shoulder + tangent * 0.07), 0.036, "brass", material, upper))
        pendant = direction * 2.92 + Vector((0, 0, 2.18))
        parts.append(dq.cylinder(f"Hanging city tooth {index}", 0.12, 0.58, tuple(pendant), "iron", material, damage_group=upper))
        parts.append(dq.cone(f"Hanging city finial {index}", 0.18, 0.025, 0.48, tuple(pendant - Vector((0, 0, 0.50))), "brass", material, damage_group=upper))
        parts.append(dq.ico_sphere(f"Hanging teal eye {index}", 0.10, tuple(pendant + direction * 0.10), "teal", material, glow, scale=(1, 1, 1.25)))

    for tier, (radius, z) in enumerate(((1.34, 5.42), (0.92, 6.12))):
        parts.append(dq.torus(f"Crown window belt {tier}", radius, 0.045, (0, 0, z), "brass", material, damage_group=upper, major_segments=32))
        for index in range(16):
            angle = math.tau * index / 16
            x, y = math.cos(angle) * radius, math.sin(angle) * radius
            parts.append(dq.ico_sphere(f"Crown window jewel {tier} {index}", 0.075, (x, y, z), "teal", material, glow, scale=(1, 1, 1.4)))


def add_winch_detail(parts: list[bpy.types.Object], material: bpy.types.Material) -> None:
    for side, x in ((-1, -1.25), (1, 1.25)):
        group = "LandingWinchPort" if side < 0 else "LandingWinchStarboard"
        for groove in range(7):
            px = x + (groove - 3) * 0.20
            parts.append(dq.torus(
                f"Rope drum groove {side} {groove}", 0.565, 0.026, (px, -2.62, 4.12), "brass", material,
                rotation=(0, math.pi / 2, 0), damage_group=group, major_segments=24,
            ))
        hub_x = x + side * 0.96
        parts.append(dq.torus(
            f"Winch gearbox rim {side}", 0.38, 0.070, (hub_x, -2.65, 4.12), "brass", material,
            rotation=(0, math.pi / 2, 0), damage_group=group, major_segments=28,
        ))
        for tooth in range(12):
            angle = math.tau * tooth / 12
            y = -2.65 + math.sin(angle) * 0.45
            z = 4.12 + math.cos(angle) * 0.45
            parts.append(dq.box(
                f"Winch gear tooth {side} {tooth}", (0.10, 0.14, 0.18), (hub_x, y, z), "iron", material, 0.004,
                rotation=(angle, 0, 0), damage_group=group,
            ))
        parts.append(dq.beam(f"Winch hanging cable {side}", (x, -2.62, 3.72), (x, -2.62, 2.18), 0.045, "rope", material, group))
        parts.append(dq.ico_sphere(f"Winch cable weight {side}", 0.15, (x, -2.62, 2.06), "brass", material, group, scale=(0.7, 0.7, 1.2)))

    for side in (-1, 1):
        for brace in range(3):
            x0 = side * (1.92 + brace * 0.24)
            parts.append(dq.beam(
                f"Gantry lattice {side} {brace}", (x0, -2.50, 3.48), (side * (2.22 - brace * 0.12), -2.50, 4.52),
                0.065, "brass", material,
            ))


def add_anchor_detail(parts: list[bpy.types.Object], material: bpy.types.Material) -> None:
    for foot in range(4):
        angle = math.pi * 0.25 + math.tau * foot / 4
        direction = Vector((math.cos(angle), math.sin(angle), 0))
        tangent = Vector((-direction.y, direction.x, 0))
        group = f"LandingFoot{foot}"
        hub = direction * 4.05 + Vector((0, 0, 1.06))
        attach = direction * 3.10 + Vector((0, 0, 3.30))

        parts.append(dq.torus(
            f"Anchor outer bearing {foot}", 0.74, 0.090, tuple(hub), "brass", material,
            rotation=(math.pi / 2, 0, angle), damage_group=group, major_segments=28,
        ))
        for side in (-1, 1):
            piston_top = attach + tangent * side * 0.31 - direction * 0.04
            piston_bottom = hub + tangent * side * 0.38 + Vector((0, 0, 0.20))
            parts.append(dq.beam(f"Anchor piston sleeve {foot} {side}", tuple(piston_top), tuple(piston_bottom), 0.13, "plate", material, group))
            parts.append(dq.beam(
                f"Anchor piston rod {foot} {side}", tuple(piston_top * 0.42 + piston_bottom * 0.58), tuple(piston_bottom),
                0.065, "brass", material, group,
            ))

        for toe in range(3):
            sign = toe - 1
            if sign == 0:
                knee = hub + direction * 0.58 - Vector((0, 0, 0.62))
                tip = hub + direction * 1.02 - Vector((0, 0, 1.02))
            else:
                knee = hub + direction * 0.46 + tangent * sign * 0.64 - Vector((0, 0, 0.48))
                tip = hub + direction * 0.82 + tangent * sign * 1.02 - Vector((0, 0, 1.04))
            parts.append(dq.ico_sphere(
                f"Anchor toe knuckle {foot} {toe}", 0.22, tuple(knee), "plate", material, group,
                scale=(1.0, 0.75, 0.88),
            ))
            parts.append(dq.torus(
                f"Anchor toe knuckle rim {foot} {toe}", 0.24, 0.048, tuple(knee), "brass", material,
                rotation=(math.pi / 2, 0, angle), damage_group=group, major_segments=24,
            ))
            mid = (knee + tip) * 0.5 + Vector((0, 0, 0.09))
            parts.append(dq.box(
                f"Anchor toe armor {foot} {toe}", (0.34, 0.18, 0.56), tuple(mid), "plate", material, 0.018,
                rotation=(0, 0, angle), damage_group=group,
            ))


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    raise_resolution()
    dq.ATLAS_SIZE = 2048
    dq.reset_scene()
    atlas, source_hashes = dq.create_atlas()
    atlas.name = "SalvageClawDetailSolPaintedAtlas"
    base.tune_plate_atlas(atlas)
    material = dq.create_material(atlas)
    material.name = "SalvageClawDetailSolPaintedMaterial"

    winch_parts = base.build_winch(material)
    anchor_parts = base.build_anchor_feet(material)
    crown_parts = base.build_crown(material)
    add_winch_detail(winch_parts, material)
    add_anchor_detail(anchor_parts, material)
    add_crown_detail(crown_parts, material)
    for parts in (winch_parts, anchor_parts, crown_parts):
        base.strip_micro_bevels(parts)

    winch = dq.join_component("winch", winch_parts, material)
    anchor_feet = dq.join_component("anchor_feet", anchor_parts, material)
    crown = dq.join_component("crown", crown_parts, material)
    objects = (winch, anchor_feet, crown)
    dq.MODEL_LENGTH = MODEL_DIAMETER
    dq.normalize_base_center(objects)
    base.add_landing_shapes(*objects)

    triangles = dq.triangle_count(objects)
    minimum, maximum = dq.world_bounds(objects)
    assert 10_164 < triangles <= 45_000, triangles
    assert abs(maximum.x - minimum.x - MODEL_DIAMETER) < 0.01
    assert abs(minimum.z) < 0.001
    assert abs((maximum.x + minimum.x) * 0.5) < 0.001
    assert abs((maximum.y + minimum.y) * 0.5) < 0.001
    assert len({slot.material.name for obj in objects for slot in obj.material_slots if slot.material}) == 1

    bpy.context.preferences.filepaths.save_version = 0
    dq.BLEND, dq.GLB = BLEND, GLB
    dq.export(objects)
    print(json.dumps({
        "blend": str(BLEND),
        "glb": str(GLB),
        "sha256": hashlib.sha256(GLB.read_bytes()).hexdigest(),
        "sourcePlates": {
            str(base.REFERENCE.relative_to(ROOT)): source_hashes["intact"],
            str(base.LANDING_REFERENCE.relative_to(ROOT)): source_hashes["damage"],
        },
        "components": [obj.name for obj in objects],
        "landingMorphs": [obj.data.shape_keys.key_blocks[1].name for obj in objects],
        "triangles": triangles,
        "boundsBlender": {
            "min": [round(value, 6) for value in minimum],
            "max": [round(value, 6) for value in maximum],
        },
    }, indent=2))


if __name__ == "__main__":
    main()
