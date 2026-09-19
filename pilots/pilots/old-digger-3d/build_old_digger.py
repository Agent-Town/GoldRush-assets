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
REFERENCE = ROOT / "assets/raw/boss-old-digger.png"
GENTLE_REFERENCE = ROOT / "assets/raw/boss-old-digger-gentle.png"
BLEND = HERE / "old-digger.blend"
GLB = HERE / "old-digger.glb"
MODEL_LENGTH = 12.4


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


dq = load("old_digger_shared_builder", ROOT / "assets/pilots/dredge-queen-3d/build_dredge_queen.py")
dq.REFERENCE = REFERENCE
dq.DAMAGE_REFERENCE = GENTLE_REFERENCE


def tune_plate_atlas(image: bpy.types.Image) -> None:
    """Turn the shared boss bake toward E9 rust-red iron without losing its engraving."""
    size = image.size[0]
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(size, size, 4)
    tuning = {
        "soot": (0.72, np.array((0.016, 0.006, 0.002))),
        "iron": (0.66, np.array((0.042, 0.013, 0.003))),
        "plate": (0.64, np.array((0.050, 0.016, 0.004))),
        "brass": (0.82, np.array((0.036, 0.016, 0.003))),
        "deck": (0.78, np.array((0.032, 0.012, 0.004))),
        "rope": (0.76, np.array((0.028, 0.012, 0.003))),
        "cargo": (0.82, np.array((0.045, 0.018, 0.002))),
    }
    for name, (factor, tint) in tuning.items():
        u0, v0, u1, v1 = dq.REGIONS[name]
        x0, y0, x1, y1 = (int(value * size) for value in (u0, v0, u1, v1))
        pixels[y0:y1, x0:x1, :3] = np.clip(pixels[y0:y1, x0:x1, :3] * factor + tint, 0.006, 0.64)
    u0, v0, u1, v1 = dq.REGIONS["teal"]
    x0, y0, x1, y1 = (int(value * size) for value in (u0, v0, u1, v1))
    pixels[y0:y1, x0:x1, :3] = np.clip(pixels[y0:y1, x0:x1, :3] * 1.22 + (0.0, 0.018, 0.012), 0.008, 0.72)
    image.pixels.foreach_set(pixels.ravel())
    image.update()
    image.pack()


def build_wheel(parts: list[bpy.types.Object], label: str, center: Vector, radius: float, buckets: int, material) -> None:
    group = f"Redemption{label}Wheel"
    parts.append(dq.cylinder(f"{label} bucket wheel drum", radius, 0.72, tuple(center), "iron", material,
                             vertices=20, rotation=(math.pi / 2, 0, 0), bevel=0.012, damage_group=group))
    parts.append(dq.torus(f"{label} outer worked rim", radius * 0.92, radius * 0.075, tuple(center), "plate", material,
                          rotation=(math.pi / 2, 0, 0), damage_group=group, major_segments=20))
    parts.append(dq.torus(f"{label} inner brass rim", radius * 0.58, radius * 0.055, tuple(center), "brass", material,
                          rotation=(math.pi / 2, 0, 0), damage_group=group, major_segments=18))
    parts.append(dq.cylinder(f"{label} wheel hub", radius * 0.18, 0.98, tuple(center), "brass", material,
                             vertices=14, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=group))
    parts.append(dq.ico_sphere(f"{label} teal bearing", radius * 0.12, tuple(center + Vector((0, -0.52, 0))), "teal", material,
                               group, scale=(1, 0.28, 1)))
    for index in range(10):
        angle = math.tau * index / 10
        edge = center + Vector((math.cos(angle) * radius * 0.84, 0, math.sin(angle) * radius * 0.84))
        parts.append(dq.beam(f"{label} spoke {index}", tuple(center), tuple(edge), radius * 0.045, "brass", material, group))
    for index in range(buckets):
        angle = math.tau * index / buckets
        radial = Vector((math.cos(angle), 0, math.sin(angle)))
        at = center + radial * radius * 0.96
        parts.append(dq.box(
            f"{label} bucket tooth {index}",
            (radius * 0.36, 1.04, radius * 0.17),
            tuple(at),
            "plate", material, 0.012,
            rotation=(0, -angle, 0),
            damage_group=group,
        ))
    # A teal service cap is hidden behind each hub until the gentle program is live.
    parts.append(dq.cylinder(f"Hidden {label} gentle hub cap", radius * 0.16, 0.06, tuple(center + Vector((0, 0.02, 0))), "teal", material,
                             vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=f"Redemption{label}HubCap"))


def build_bucket_wheels(material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    build_wheel(parts, "Port", Vector((-4.55, 0, 2.20)), 2.10, 14, material)
    build_wheel(parts, "Starboard", Vector((4.72, 0, 1.58)), 1.46, 11, material)
    return parts


def build_gantry(material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    # Long open truss bridge, readable from above and from either side.
    for side in (-1, 1):
        y = side * 0.83
        parts.append(dq.beam(f"Gantry lower chord {side}", (-4.25, y, 2.52), (4.25, y, 2.52), 0.14, "iron", material))
        parts.append(dq.beam(f"Gantry upper chord {side}", (-4.00, y, 3.72), (3.98, y, 3.22), 0.14, "plate", material))
        for index in range(9):
            x0 = -4.0 + index * 0.94
            x1 = min(4.0, x0 + 0.94)
            z0 = 3.72 + (3.22 - 3.72) * ((x0 + 4.0) / 8.0)
            z1 = 3.72 + (3.22 - 3.72) * ((x1 + 4.0) / 8.0)
            parts.append(dq.beam(f"Gantry diagonal {side} {index}", (x0, y, 2.56), (x1, y, z1), 0.075, "brass", material))
            parts.append(dq.beam(f"Gantry upright {side} {index}", (x0, y, 2.52), (x0, y, z0), 0.060, "brass", material))
    for index, x in enumerate(np.linspace(-3.8, 3.8, 9)):
        z = 3.72 + (3.22 - 3.72) * ((x + 4.0) / 8.0)
        parts.append(dq.beam(f"Gantry cross tie {index}", (float(x), -0.86, float(z)), (float(x), 0.86, float(z)), 0.075, "brass", material))

    # Tall port-side dig tower and its load cables.
    parts.append(dq.beam("Tower port leg", (-3.78, -0.68, 2.62), (-3.18, -0.45, 6.42), 0.18, "iron", material))
    parts.append(dq.beam("Tower starboard leg", (-3.78, 0.68, 2.62), (-3.18, 0.45, 6.42), 0.18, "iron", material))
    parts.append(dq.beam("Tower rear rake", (-2.56, 0, 2.66), (-3.18, 0, 6.42), 0.16, "plate", material))
    for rung, z in enumerate(np.linspace(3.0, 6.15, 8)):
        t = (z - 2.62) / (6.42 - 2.62)
        x = -3.78 + (-3.18 + 3.78) * t
        parts.append(dq.beam(f"Tower rung {rung}", (float(x), -0.72, float(z)), (float(x), 0.72, float(z)), 0.060, "brass", material))
    parts.append(dq.cylinder("Tower crown pulley", 0.42, 0.42, (-3.18, 0, 6.42), "brass", material,
                             vertices=14, rotation=(math.pi / 2, 0, 0), bevel=0))
    parts.append(dq.torus("Tower crown pulley rim", 0.46, 0.06, (-3.18, 0, 6.42), "plate", material,
                          rotation=(math.pi / 2, 0, 0), major_segments=14))
    for cable, y in enumerate((-0.20, 0.20)):
        parts.append(dq.beam(f"Port wheel lifting cable {cable}", (-3.18, y, 6.36), (-4.56, y, 3.46), 0.050, "rope", material))
        parts.append(dq.beam(f"Long counter cable {cable}", (-3.18, y, 6.36), (4.72, y, 2.62), 0.045, "rope", material))

    # Gentle-only safety rail and boarding steps begin hidden inside the bridge.
    safe_group = "RedemptionSafeRail"
    for side in (-1, 1):
        y = side * 0.72
        parts.append(dq.beam(f"Hidden safe rail {side}", (-2.2, y, 2.70), (1.80, y, 2.70), 0.060, "brass", material, safe_group))
        for index, x in enumerate((-2.1, -1.45, -0.80, -0.15, 0.50, 1.15, 1.75)):
            parts.append(dq.beam(f"Hidden safe post {side} {index}", (x, y, 2.46), (x, y, 2.76), 0.045, "brass", material, safe_group))
    step_group = "RedemptionBoardingSteps"
    for side, x in ((-1, -1.45), (1, 1.45)):
        parts.append(dq.beam(f"Hidden step rail {side} port", (x - 0.20, -0.70, 1.15), (x - 0.20, -0.70, 2.22), 0.045, "brass", material, step_group))
        parts.append(dq.beam(f"Hidden step rail {side} starboard", (x + 0.20, -0.70, 1.15), (x + 0.20, -0.70, 2.22), 0.045, "brass", material, step_group))
        for rung, z in enumerate((1.30, 1.54, 1.78, 2.02)):
            parts.append(dq.beam(f"Hidden boarding rung {side} {rung}", (x - 0.20, -0.70, z), (x + 0.20, -0.70, z), 0.038, "brass", material, step_group))
    return parts


def build_tape_deck(material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    # Central tracked machine body stays intact in both programs.
    parts.append(dq.box("Digger undercarriage", (4.20, 2.62, 0.72), (0.15, 0, 0.62), "soot", material, 0.08))
    for side in (-1, 1):
        y = side * 1.34
        parts.append(dq.box(f"Crawler track bed {side}", (3.85, 0.46, 0.88), (0.15, y, 0.66), "iron", material, 0.07))
        for index, x in enumerate(np.linspace(-1.55, 1.85, 10)):
            parts.append(dq.box(f"Crawler pad {side} {index}", (0.30, 0.56, 0.13), (float(x), y + side * 0.08, 0.16), "plate", material, 0.008))
        for x in (-1.45, 1.75):
            parts.append(dq.cylinder(f"Crawler end wheel {side} {x}", 0.34, 0.55, (x, y + side * 0.05, 0.70), "brass", material,
                                     vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0))
    parts.append(dq.box("Central machine hall", (3.25, 2.72, 1.62), (0.20, 0, 1.76), "plate", material, 0.08))
    parts.append(dq.box("Worked upper deck", (3.72, 2.98, 0.22), (0.15, 0, 2.68), "deck", material, 0.025))
    parts.append(dq.ico_sphere("Survey dome", 0.82, (0.74, 0.20, 3.46), "iron", material, scale=(1.0, 1.08, 0.62)))
    parts.append(dq.torus("Survey dome brass cage", 0.78, 0.055, (0.74, -0.70, 3.44), "brass", material,
                          rotation=(math.pi / 2, 0, 0), major_segments=14))
    for index, (x, y, height) in enumerate(((-0.80, -0.62, 1.65), (0.15, 0.72, 1.35), (1.35, -0.45, 1.72))):
        parts.append(dq.cylinder(f"Digger stack {index}", 0.16, height, (x, y, 3.25 + height * 0.35), "soot", material, vertices=10, bevel=0.008))
        parts.append(dq.torus(f"Digger stack crown {index}", 0.20, 0.036, (x, y, 3.25 + height * 0.85), "brass", material, major_segments=10))

    # The old crossed-pickaxes crest is heritage: dirty, visible, and never replaced.
    crest = (0.20, -1.52, 3.45)
    parts.append(dq.cylinder("Ghost crest backplate", 0.70, 0.12, crest, "iron", material, vertices=16,
                             rotation=(math.pi / 2, 0, 0), bevel=0.01))
    parts.append(dq.torus("Ghost crest brass rim", 0.66, 0.055, (crest[0], crest[1] - 0.07, crest[2]), "brass", material,
                          rotation=(math.pi / 2, 0, 0), major_segments=16))
    parts.append(dq.beam("Ghost pickaxe one", (-0.15, -1.62, 3.12), (0.55, -1.62, 3.78), 0.075, "brass", material))
    parts.append(dq.beam("Ghost pickaxe two", (0.55, -1.64, 3.12), (-0.15, -1.64, 3.78), 0.075, "brass", material))

    # Amber working tape deck and its hidden teal redemption face occupy the same heart.
    parts.append(dq.box("Tape deck armored frame", (1.46, 0.16, 0.86), (0.18, -1.49, 2.38), "brass", material, 0.025))
    parts.append(dq.box("Working amber tape window", (1.12, 0.08, 0.58), (0.18, -1.59, 2.38), "cargo", material, 0.010,
                        damage_group="RedemptionAmberHeart"))
    for x in (-0.15, 0.50):
        parts.append(dq.torus(f"Working tape reel {x}", 0.18, 0.040, (x, -1.65, 2.38), "soot", material,
                              rotation=(math.pi / 2, 0, 0), damage_group="RedemptionAmberHeart", major_segments=12))
    parts.append(dq.box("Hidden teal tape window", (1.12, 0.08, 0.58), (0.18, -1.13, 2.38), "teal", material, 0.010,
                        damage_group="RedemptionTealHeart"))
    for x in (-0.15, 0.50):
        parts.append(dq.torus(f"Hidden teal tape reel {x}", 0.18, 0.040, (x, -1.17, 2.38), "brass", material,
                              rotation=(math.pi / 2, 0, 0), damage_group="RedemptionTealHeart", major_segments=12))

    for index, (x, y) in enumerate(((-1.35, -1.24), (-1.35, 1.24), (1.65, -1.24), (1.65, 1.24))):
        parts.append(dq.cylinder(f"Maintenance lantern {index}", 0.11, 0.38, (x, y, 2.98), "teal", material, vertices=10, bevel=0))
        parts.append(dq.torus(f"Maintenance lantern cage {index}", 0.13, 0.025, (x, y, 2.98), "brass", material,
                              rotation=(math.pi / 2, 0, 0), major_segments=10))
    return parts


def strip_micro_bevels(parts: list[bpy.types.Object]) -> None:
    detail_words = ("spoke", "chord", "diagonal", "upright", "tie", "leg", "rake", "rung", "cable", "rail", "post", "pickaxe")
    for part in parts:
        if not any(word in part.name.lower() for word in detail_words):
            continue
        for modifier in list(part.modifiers):
            if modifier.type == "BEVEL":
                part.modifiers.remove(modifier)


def group_center(obj: bpy.types.Object, group_name: str) -> Vector:
    points = [obj.data.vertices[index].co for index in dq.group_vertex_indices(obj, group_name)]
    assert points, f"missing group {obj.name}:{group_name}"
    return sum(points, Vector()) / len(points)


def add_redemption_shapes(bucket_wheels: bpy.types.Object, gantry: bpy.types.Object, tape_deck: bpy.types.Object) -> None:
    bucket_wheels.shape_key_add(name="Basis")
    gentle_buckets = bucket_wheels.shape_key_add(name="Redemption_GentleBuckets")
    for label, angle in (("Port", math.radians(7)), ("Starboard", math.radians(-9))):
        group = f"Redemption{label}Wheel"
        pivot = group_center(bucket_wheels, group)
        for index in dq.group_vertex_indices(bucket_wheels, group):
            dq.rotate_y(gentle_buckets.data[index].co, pivot, angle)
        for index in dq.group_vertex_indices(bucket_wheels, f"Redemption{label}HubCap"):
            gentle_buckets.data[index].co.y -= 0.62

    gantry.shape_key_add(name="Basis")
    safe = gantry.shape_key_add(name="Redemption_SafeGantry")
    for index in dq.group_vertex_indices(gantry, "RedemptionSafeRail"):
        safe.data[index].co.z += 0.66
    for index in dq.group_vertex_indices(gantry, "RedemptionBoardingSteps"):
        safe.data[index].co += Vector((0, -1.02, -0.76))

    tape_deck.shape_key_add(name="Basis")
    teal_heart = tape_deck.shape_key_add(name="Redemption_TealTapeDeck")
    for index in dq.group_vertex_indices(tape_deck, "RedemptionAmberHeart"):
        teal_heart.data[index].co.y += 0.52
    for index in dq.group_vertex_indices(tape_deck, "RedemptionTealHeart"):
        teal_heart.data[index].co.y -= 0.52

    for obj in (bucket_wheels, gantry, tape_deck):
        obj.active_shape_key_index = 0
        for key in obj.data.shape_keys.key_blocks:
            key.value = 0.0


def split_wheels(source):
    wheels = []
    for label in ('Port', 'Starboard'):
        obj = source.copy()
        obj.data = source.data.copy()
        bpy.context.collection.objects.link(obj)
        obj.name = 'bucket_wheel_' + label.lower()
        cap = obj.vertex_groups['Redemption' + label + 'HubCap'].index
        points = [v.co.copy() for v in obj.data.vertices if any(g.group == cap and g.weight > .5 for g in v.groups)]
        assert points
        pivot = sum(points, Vector()) / len(points)
        keep = {obj.vertex_groups['Redemption' + label + 'Wheel'].index, cap}
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        for vertex in obj.data.vertices:
            vertex.select = not any(g.group in keep and g.weight > .5 for g in vertex.groups)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.object.mode_set(mode='OBJECT')
        for key in obj.data.shape_keys.key_blocks:
            for vertex in key.data:
                vertex.co -= pivot
        assert len(obj.data.vertices) > 600 and len(obj.data.polygons) > 600
        obj.location = pivot
        wheels.append(obj)
    bpy.data.objects.remove(source, do_unlink=True)
    return wheels


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    dq.reset_scene()
    atlas, source_hashes = dq.create_atlas()
    atlas.name = "OldDiggerPaintedAtlas"
    tune_plate_atlas(atlas)
    material = dq.create_material(atlas)
    material.name = "OldDiggerPaintedMaterial"

    wheel_parts = build_bucket_wheels(material)
    gantry_parts = build_gantry(material)
    heart_parts = build_tape_deck(material)
    for parts in (wheel_parts, gantry_parts, heart_parts):
        strip_micro_bevels(parts)
    bucket_wheels = dq.join_component("bucket_wheels", wheel_parts, material)
    gantry = dq.join_component("gantry", gantry_parts, material)
    tape_deck = dq.join_component("tape_deck", heart_parts, material)
    objects = (bucket_wheels, gantry, tape_deck)
    dq.MODEL_LENGTH = MODEL_LENGTH
    dq.normalize_base_center(objects)
    add_redemption_shapes(*objects)

    triangles = dq.triangle_count(objects)
    minimum, maximum = dq.world_bounds(objects)
    assert triangles <= 12_000, triangles
    assert abs(maximum.x - minimum.x - MODEL_LENGTH) < 0.01
    assert abs(minimum.z) < 0.001
    assert abs((maximum.x + minimum.x) * 0.5) < 0.001
    assert abs((maximum.y + minimum.y) * 0.5) < 0.001
    dq.BLEND, dq.GLB = BLEND, GLB
    objects = (*split_wheels(bucket_wheels), gantry, tape_deck)
    dq.export(objects)
    print(json.dumps({
        "blend": str(BLEND),
        "glb": str(GLB),
        "sha256": hashlib.sha256(GLB.read_bytes()).hexdigest(),
        "sourcePlates": {
            str(REFERENCE.relative_to(ROOT)): source_hashes["intact"],
            str(GENTLE_REFERENCE.relative_to(ROOT)): source_hashes["damage"],
        },
        "components": [obj.name for obj in objects],
        "redemptionMorphs": [obj.data.shape_keys.key_blocks[1].name for obj in objects],
        "triangles": triangles,
        "boundsBlender": {
            "min": [round(value, 6) for value in minimum],
            "max": [round(value, 6) for value in maximum],
        },
    }, indent=2))


if __name__ == "__main__":
    main()
