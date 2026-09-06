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
REFERENCE = ROOT / "assets/raw/boss-salvage-claw.png"
LANDING_REFERENCE = ROOT / "assets/raw/boss-salvage-claw-damage.png"
BLEND = HERE / "salvage-claw.blend"
GLB = HERE / "salvage-claw.glb"
MODEL_DIAMETER = 11.4


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


dq = load("salvage_claw_shared_builder", ROOT / "assets/pilots/dredge-queen-3d/build_dredge_queen.py")
dq.REFERENCE = REFERENCE
dq.DAMAGE_REFERENCE = LANDING_REFERENCE


def tune_plate_atlas(image: bpy.types.Image) -> None:
    """Keep the source engraving but restore its cold silver-teal boss value range."""
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
    }
    for name, (factor, tint) in tuning.items():
        u0, v0, u1, v1 = dq.REGIONS[name]
        x0, y0, x1, y1 = (int(value * size) for value in (u0, v0, u1, v1))
        pixels[y0:y1, x0:x1, :3] = np.clip(pixels[y0:y1, x0:x1, :3] * factor + tint, 0.006, 0.62)
    u0, v0, u1, v1 = dq.REGIONS["teal"]
    x0, y0, x1, y1 = (int(value * size) for value in (u0, v0, u1, v1))
    pixels[y0:y1, x0:x1, :3] = np.clip(pixels[y0:y1, x0:x1, :3] * 1.18 + (0.0, 0.018, 0.020), 0.008, 0.72)
    image.pixels.foreach_set(pixels.ravel())
    image.update()
    image.pack()


def radial_beam(parts, name: str, radius: float, z0: float, z1: float, angle: float, width: float, region: str, material, group: str | None = None) -> None:
    x, y = math.cos(angle) * radius, math.sin(angle) * radius
    parts.append(dq.beam(name, (x, y, z0), (x, y, z1), width, region, material, group))


def build_crown(material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    upper = "LandingCrownUpper"
    glow = "LandingCrownGlow"

    # The plate's broad descending city-crown: a readable saucer first, palace second.
    parts.append(dq.cylinder("Armored crown belly", 3.34, 0.78, (0, 0, 3.05), "iron", material, vertices=20, bevel=0.03))
    parts.append(dq.cone("Faceted lower cup", 0.72, 2.36, 1.34, (0, 0, 2.15), "plate", material, vertices=16))
    parts.append(dq.cylinder("Promenade deck", 3.58, 0.24, (0, 0, 3.52), "deck", material, vertices=20, bevel=0.02))
    parts.append(dq.torus("Lower brass belt", 3.18, 0.10, (0, 0, 2.70), "brass", material, major_segments=20))
    parts.append(dq.torus("Promenade brass rim", 3.53, 0.11, (0, 0, 3.61), "brass", material, major_segments=20))
    parts.append(dq.cylinder("Central keel eye", 0.56, 0.52, (0, 0, 1.30), "teal", material, vertices=12, bevel=0.01))
    parts.append(dq.cone("Keel brass finial", 0.30, 0.04, 0.48, (0, 0, 0.82), "brass", material, vertices=10))

    # Upper glass-and-iron crown, deliberately taller than a toy saucer at run distance.
    parts.append(dq.cylinder("Crown armored base", 2.15, 0.72, (0, 0, 4.02), "plate", material, vertices=16, bevel=0.035, damage_group=upper))
    parts.append(dq.cylinder("Crown teal window drum", 1.72, 0.72, (0, 0, 4.65), "teal", material, vertices=16, bevel=0.015, damage_group=glow))
    parts.append(dq.torus("Crown lower tracery", 1.78, 0.075, (0, 0, 4.30), "brass", material, damage_group=upper, major_segments=16))
    parts.append(dq.torus("Crown upper tracery", 1.78, 0.075, (0, 0, 5.01), "brass", material, damage_group=upper, major_segments=16))
    parts.append(dq.cone("Crown steep roof", 1.74, 0.20, 1.58, (0, 0, 5.62), "iron", material, vertices=16, damage_group=upper))
    parts.append(dq.cylinder("Crown lantern", 0.38, 0.66, (0, 0, 6.66), "teal", material, vertices=12, bevel=0.012, damage_group=glow))
    parts.append(dq.cone("Crown lantern cap", 0.53, 0.05, 0.66, (0, 0, 7.31), "brass", material, vertices=12, damage_group=upper))
    for index in range(16):
        angle = math.tau * index / 16
        radial_beam(parts, f"Crown mullion {index}", 1.74, 4.29, 5.04, angle, 0.065, "brass", material, upper)
    for index in range(8):
        angle = math.tau * index / 8
        start = (math.cos(angle) * 1.62, math.sin(angle) * 1.62, 5.00)
        parts.append(dq.beam(f"Crown gothic rib {index}", start, (0, 0, 6.48), 0.075, "brass", material, upper))
    parts.append(dq.triangle_panel(
        "Front crown gable",
        ((-1.30, -1.74, 4.95), (0.0, -1.74, 6.54), (1.30, -1.74, 4.95)),
        0.09, "iron", material, upper,
    ))
    parts.append(dq.beam("Front gable port rib", (-1.30, -1.80, 4.95), (0, -1.80, 6.54), 0.075, "brass", material, upper))
    parts.append(dq.beam("Front gable starboard rib", (1.30, -1.80, 4.95), (0, -1.80, 6.54), 0.075, "brass", material, upper))
    parts.append(dq.ico_sphere("Front gable teal eye", 0.22, (0, -1.81, 5.68), "teal", material, glow, scale=(1, 0.28, 1.22)))

    # Palace spires and the promenade rail carry the source's corsair-gothic silhouette.
    for index in range(10):
        angle = math.tau * index / 10 + math.pi / 10
        radius = 2.62 if index % 2 == 0 else 2.88
        x, y = math.cos(angle) * radius, math.sin(angle) * radius
        parts.append(dq.cylinder(f"Perimeter turret {index}", 0.18, 1.38, (x, y, 4.22), "brass", material, vertices=10, bevel=0.006, damage_group=upper))
        parts.append(dq.cone(f"Perimeter turret cap {index}", 0.29, 0.035, 0.52, (x, y, 5.14), "brass", material, vertices=10, damage_group=upper))
        parts.append(dq.ico_sphere(f"Perimeter teal orb {index}", 0.14, (x, y, 4.78), "teal", material, glow, scale=(1, 1, 1.18)))
    parts.append(dq.torus("Promenade rail", 3.18, 0.045, (0, 0, 4.02), "brass", material, damage_group=upper, major_segments=20))
    for index in range(20):
        angle = math.tau * index / 20
        radial_beam(parts, f"Promenade post {index}", 3.18, 3.58, 4.06, angle, 0.045, "brass", material, upper)

    # Pictogram-only claim pendants: anchor and crossed-tool silhouettes, no letters.
    for index, angle in enumerate((-0.72, -0.36, 0.0, 0.36, 0.72)):
        x, y = math.sin(angle) * 2.65, -math.cos(angle) * 2.65
        parts.append(dq.box(f"Claim pendant {index}", (0.58, 0.10, 0.92), (x, y, 2.44), "brass", material, 0.015, rotation=(0, 0, -angle)))
        parts.append(dq.beam(f"Pendant mark stem {index}", (x - 0.14, y - 0.06, 2.23), (x + 0.14, y - 0.06, 2.66), 0.050, "soot", material))
        parts.append(dq.beam(f"Pendant mark cross {index}", (x + 0.14, y - 0.06, 2.23), (x - 0.14, y - 0.06, 2.66), 0.050, "soot", material))

    # Landing-state shutters begin inside the glass; rope ladders begin inside the belly.
    for index in range(8):
        angle = math.tau * index / 8
        x, y = math.cos(angle) * 1.30, math.sin(angle) * 1.30
        parts.append(dq.box(f"Hidden crown shutter {index}", (0.38, 0.10, 0.54), (x, y, 4.64), "soot", material, 0.004,
                            rotation=(0, 0, angle + math.pi / 2), damage_group=f"LandingShutter{index}"))
    for ladder, x in enumerate((-0.70, 0.70)):
        group = f"LandingLadder{ladder}"
        parts.append(dq.beam(f"Hidden ladder rail {ladder} port", (x - 0.16, -2.42, 2.35), (x - 0.16, -2.42, 3.30), 0.035, "rope", material, group))
        parts.append(dq.beam(f"Hidden ladder rail {ladder} starboard", (x + 0.16, -2.42, 2.35), (x + 0.16, -2.42, 3.30), 0.035, "rope", material, group))
        for rung, z in enumerate((2.45, 2.68, 2.91, 3.14)):
            parts.append(dq.beam(f"Hidden ladder rung {ladder} {rung}", (x - 0.16, -2.42, z), (x + 0.16, -2.42, z), 0.030, "rope", material, group))
    return parts


def build_winch(material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    parts.append(dq.box("Winch armored gantry", (4.55, 1.05, 0.42), (0, -2.48, 3.70), "plate", material, 0.035))
    parts.append(dq.beam("Winch lower brace", (-2.20, -2.50, 3.44), (2.20, -2.50, 3.44), 0.10, "brass", material))
    for side, x in ((-1, -1.25), (1, 1.25)):
        group = "LandingWinchPort" if side < 0 else "LandingWinchStarboard"
        parts.append(dq.cylinder(f"{'Port' if side < 0 else 'Starboard'} rope drum", 0.56, 1.72, (x, -2.62, 4.12), "rope", material,
                                 vertices=16, rotation=(0, math.pi / 2, 0), bevel=0.006, damage_group=group))
        for offset in (-0.78, -0.56, 0.56, 0.78):
            px = x + offset * 0.50
            parts.append(dq.torus(f"Drum collar {side} {offset}", 0.59, 0.065, (px, -2.62, 4.12), "brass", material,
                                  rotation=(0, math.pi / 2, 0), damage_group=group, major_segments=14))
        parts.append(dq.cylinder(f"Winch teal hub {side}", 0.22, 0.14, (x + side * 0.90, -2.62, 4.12), "teal", material,
                                 vertices=12, rotation=(0, math.pi / 2, 0), bevel=0, damage_group=group))
        parts.append(dq.beam(f"Winch A-frame outer {side}", (x + side * 0.80, -2.55, 3.62), (x + side * 1.00, -2.55, 4.72), 0.12, "iron", material, group))
        parts.append(dq.beam(f"Winch A-frame inner {side}", (x - side * 0.72, -2.55, 3.62), (x - side * 0.86, -2.55, 4.72), 0.12, "iron", material, group))
    parts.append(dq.cylinder("Winch central gearbox", 0.47, 0.80, (0, -2.63, 4.16), "iron", material,
                             vertices=14, rotation=(math.pi / 2, 0, 0), bevel=0.012))
    parts.append(dq.torus("Winch central gauge rim", 0.31, 0.055, (0, -3.05, 4.16), "brass", material,
                          rotation=(math.pi / 2, 0, 0), major_segments=12))
    parts.append(dq.ico_sphere("Winch central gauge glass", 0.25, (0, -3.08, 4.16), "teal", material, scale=(1, 0.26, 1)))
    for shard, at in enumerate(((-1.20, -2.62, 4.12), (1.20, -2.62, 4.12), (0, -2.62, 4.16))):
        parts.append(dq.box(f"Hidden sprung winch part {shard}", (0.34, 0.08, 0.11), at, "damage", material, 0.003,
                            damage_group=f"LandingWinchShard{shard}"))
    return parts


def build_anchor_feet(material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    for foot in range(4):
        angle = math.pi * 0.25 + math.tau * foot / 4
        direction = Vector((math.cos(angle), math.sin(angle), 0))
        tangent = Vector((-direction.y, direction.x, 0))
        group = f"LandingFoot{foot}"
        attach = direction * 3.10 + Vector((0, 0, 3.30))
        elbow = direction * 3.72 + Vector((0, 0, 1.70))
        hub = direction * 4.05 + Vector((0, 0, 1.06))
        parts.append(dq.ico_sphere(f"Anchor gearbox {foot}", 0.68, tuple(hub), "plate", material, group, scale=(1.0, 0.78, 1.0)))
        parts.append(dq.torus(f"Anchor gearbox brass rim {foot}", 0.62, 0.090, tuple(hub), "brass", material,
                              damage_group=group, major_segments=14))
        parts.append(dq.beam(f"Anchor armored arm {foot}", tuple(attach), tuple(elbow), 0.17, "iron", material, group))
        parts.append(dq.beam(f"Anchor arm brass edge {foot}", tuple(attach + tangent * 0.10), tuple(elbow + tangent * 0.10), 0.065, "brass", material, group))
        parts.append(dq.beam(f"Anchor cable port {foot}", tuple(attach + tangent * 0.20 + Vector((0, 0, 0.14))), tuple(hub + tangent * 0.25), 0.050, "rope", material, group))
        parts.append(dq.beam(f"Anchor cable starboard {foot}", tuple(attach - tangent * 0.20 + Vector((0, 0, 0.14))), tuple(hub - tangent * 0.25), 0.050, "rope", material, group))
        high_rig = direction * 2.68 + Vector((0, 0, 4.95))
        parts.append(dq.beam(f"Anchor high rig port {foot}", tuple(high_rig + tangent * 0.14), tuple(hub + tangent * 0.34), 0.055, "rope", material, group))
        parts.append(dq.beam(f"Anchor high rig starboard {foot}", tuple(high_rig - tangent * 0.14), tuple(hub - tangent * 0.34), 0.055, "rope", material, group))
        parts.append(dq.ico_sphere(f"Anchor teal bearing {foot}", 0.18, tuple(hub + tangent * 0.49), "teal", material, group, scale=(1, 0.34, 1)))
        for toe in range(3):
            sign = toe - 1
            shoulder = hub + direction * 0.08 + tangent * sign * 0.18 - Vector((0, 0, 0.20))
            if sign == 0:
                knee = hub + direction * 0.58 - Vector((0, 0, 0.62))
                tip = hub + direction * 1.02 - Vector((0, 0, 1.02))
                upper_width, lower_width = 0.22, 0.18
            else:
                knee = hub + direction * 0.46 + tangent * sign * 0.64 - Vector((0, 0, 0.48))
                tip = hub + direction * 0.82 + tangent * sign * 1.02 - Vector((0, 0, 1.04))
                upper_width, lower_width = 0.30, 0.24
            parts.append(dq.beam(f"Anchor toe upper {foot} {toe}", tuple(shoulder), tuple(knee), upper_width, "iron", material, group))
            parts.append(dq.beam(f"Anchor toe brass edge {foot} {toe}", tuple(knee), tuple(tip), lower_width, "brass", material, group))
            parts.append(dq.cone(f"Anchor toe point {foot} {toe}", 0.17, 0.025, 0.45, tuple(tip + direction * 0.12), "iron", material,
                                 vertices=8, rotation=(0, math.pi / 2, angle), damage_group=group))
    return parts


def group_center(obj: bpy.types.Object, group_name: str) -> Vector:
    points = [obj.data.vertices[index].co for index in dq.group_vertex_indices(obj, group_name)]
    assert points, f"missing group {obj.name}:{group_name}"
    return sum(points, Vector()) / len(points)


def strip_micro_bevels(parts: list[bpy.types.Object]) -> None:
    """Spend triangles on the silhouette, not tiny rail and cable edge loops."""
    detail_words = ("post", "mullion", "rail", "brace", "edge", "cable", "toe", "arm", "rung", "mark", "rib", "rig")
    for part in parts:
        if not any(word in part.name.lower() for word in detail_words):
            continue
        for modifier in list(part.modifiers):
            if modifier.type == "BEVEL":
                part.modifiers.remove(modifier)


def add_landing_shapes(winch: bpy.types.Object, anchor_feet: bpy.types.Object, crown: bpy.types.Object) -> None:
    winch.shape_key_add(name="Basis")
    sprung = winch.shape_key_add(name="Landing_SprungWinch")
    for group_name, angle, shift in (
        ("LandingWinchPort", math.radians(-11), Vector((-0.08, -0.06, -0.22))),
        ("LandingWinchStarboard", math.radians(13), Vector((0.10, 0.04, -0.14))),
    ):
        pivot = group_center(winch, group_name)
        for index in dq.group_vertex_indices(winch, group_name):
            co = sprung.data[index].co
            dq.rotate_y(co, pivot, angle)
            co += shift
    for shard, movement in enumerate((Vector((-1.05, -0.52, -0.72)), Vector((1.12, -0.44, -0.58)), Vector((0.22, -0.78, -0.90)))):
        for index in dq.group_vertex_indices(winch, f"LandingWinchShard{shard}"):
            sprung.data[index].co += movement

    anchor_feet.shape_key_add(name="Basis")
    settled = anchor_feet.shape_key_add(name="Landing_SettledAnchorFeet")
    for foot in range(4):
        group_name = f"LandingFoot{foot}"
        center = group_center(anchor_feet, group_name)
        direction = Vector((center.x, center.y, 0)).normalized()
        for index in dq.group_vertex_indices(anchor_feet, group_name):
            co = settled.data[index].co
            falloff = max(0.0, min(1.0, (2.80 - co.z) / 2.80))
            co.x += direction.x * 0.48 * falloff
            co.y += direction.y * 0.48 * falloff
            co.z = max(0.0, co.z - 0.22 * falloff)

    crown.shape_key_add(name="Basis")
    dark = crown.shape_key_add(name="Landing_DarkCrown")
    for index in dq.group_vertex_indices(crown, "LandingCrownGlow"):
        co = dark.data[index].co
        co.x *= 0.80
        co.y *= 0.80
        co.z -= 0.10
    for index in dq.group_vertex_indices(crown, "LandingCrownUpper"):
        dark.data[index].co.z -= 0.12
    for shutter in range(8):
        group_name = f"LandingShutter{shutter}"
        center = group_center(crown, group_name)
        direction = Vector((center.x, center.y, 0)).normalized()
        for index in dq.group_vertex_indices(crown, group_name):
            dark.data[index].co += direction * 0.47
    for ladder in range(2):
        for index in dq.group_vertex_indices(crown, f"LandingLadder{ladder}"):
            dark.data[index].co += Vector((0, -0.32, -1.98))

    for obj in (winch, anchor_feet, crown):
        obj.active_shape_key_index = 0
        for key in obj.data.shape_keys.key_blocks:
            key.value = 0.0


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    dq.reset_scene()
    atlas, source_hashes = dq.create_atlas()
    atlas.name = "SalvageClawPaintedAtlas"
    tune_plate_atlas(atlas)
    material = dq.create_material(atlas)
    material.name = "SalvageClawPaintedMaterial"
    winch_parts = build_winch(material)
    anchor_parts = build_anchor_feet(material)
    crown_parts = build_crown(material)
    for parts in (winch_parts, anchor_parts, crown_parts):
        strip_micro_bevels(parts)
    winch = dq.join_component("winch", winch_parts, material)
    anchor_feet = dq.join_component("anchor_feet", anchor_parts, material)
    crown = dq.join_component("crown", crown_parts, material)
    objects = (winch, anchor_feet, crown)
    dq.MODEL_LENGTH = MODEL_DIAMETER
    dq.normalize_base_center(objects)
    add_landing_shapes(*objects)

    triangles = dq.triangle_count(objects)
    minimum, maximum = dq.world_bounds(objects)
    assert triangles <= 12_000, triangles
    assert abs(maximum.x - minimum.x - MODEL_DIAMETER) < 0.01
    assert abs(minimum.z) < 0.001
    assert abs((maximum.x + minimum.x) * 0.5) < 0.001
    assert abs((maximum.y + minimum.y) * 0.5) < 0.001
    dq.BLEND, dq.GLB = BLEND, GLB
    dq.export(objects)
    print(json.dumps({
        "blend": str(BLEND),
        "glb": str(GLB),
        "sha256": hashlib.sha256(GLB.read_bytes()).hexdigest(),
        "sourcePlates": {
            str(REFERENCE.relative_to(ROOT)): source_hashes["intact"],
            str(LANDING_REFERENCE.relative_to(ROOT)): source_hashes["damage"],
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
