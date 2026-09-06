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
REFERENCE = ROOT / "assets/raw/plate-e6-boss-homemaker-9000.png"
BLEND = HERE / "homemaker-9000.blend"
GLB = HERE / "homemaker-9000.glb"
MODEL_LENGTH = 7.2


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


dq = load("homemaker_shared_builder", ROOT / "assets/pilots/dredge-queen-3d/build_dredge_queen.py")


def create_atomic_atlas() -> bpy.types.Image:
    source = bpy.data.images.load(str(REFERENCE), check_existing=False)
    colors = np.array(source.pixels[:], dtype=np.float32).reshape(source.size[1], source.size[0], 4)[:, :, :3]
    atlas = np.ones((dq.ATLAS_SIZE, dq.ATLAS_SIZE, 4), dtype=np.float32)
    rng = np.random.default_rng(9000)
    palette = {
        "soot": np.array((0.035, 0.042, 0.038)),
        "iron": np.array((0.38, 0.41, 0.38)),
        "brass": np.array((0.55, 0.29, 0.055)),
        "deck": np.array((0.22, 0.34, 0.31)),
        "teal": np.array((0.035, 0.44, 0.45)),
        "damage": np.array((0.42, 0.10, 0.035)),
        "plate": np.array((0.52, 0.54, 0.49)),
        "sail": np.array((0.62, 0.52, 0.30)),
        "rope": np.array((0.47, 0.26, 0.08)),
        "cargo": np.array((0.43, 0.58, 0.53)),
    }
    atlas[:, :, :3] = palette["soot"]

    # Carry the plate's ink, chrome, amber, and teal into the dominant wrap tile.
    x0, y0, x1, y1 = dq.region_pixels(dq.REGIONS["plate"])
    crop = colors[int(source.size[1] * 0.035):int(source.size[1] * 0.96), :int(source.size[0] * 0.57)]
    painted = dq.resized_nearest(dq.resized_nearest(crop, 360, 420), y1 - y0, x1 - x0)
    luminance = painted.mean(axis=2)
    ink = np.clip((0.68 - luminance) / 0.58, 0.0, 1.0)
    block = palette["plate"][None, None, :] * (1.10 - ink[:, :, None] * 0.48) + 0.025
    amber = (painted[:, :, 0] > painted[:, :, 2] * 1.32) & (painted[:, :, 0] > 0.18)
    teal = (painted[:, :, 1] > painted[:, :, 0] * 1.10) & (painted[:, :, 2] > painted[:, :, 0] * 1.04)
    block[amber] = block[amber] * 0.50 + palette["brass"] * 0.50
    block[teal] = block[teal] * 0.38 + palette["teal"] * 0.62
    block += rng.normal(0, 0.007, (y1 - y0, x1 - x0, 1))
    atlas[y0:y1, x0:x1, :3] = np.clip(block, 0.015, 0.72)

    for name, region in dq.REGIONS.items():
        if name == "plate":
            continue
        x0, y0, x1, y1 = dq.region_pixels(region)
        base = palette[name]
        noise = rng.normal(0, 0.006, (y1 - y0, x1 - x0, 1))
        atlas[y0:y1, x0:x1, :3] = np.clip(base + noise, 0.012, 0.72)
        if name in {"iron", "brass", "deck", "damage", "sail", "cargo"}:
            for offset in range(-(y1 - y0), x1 - x0, 19 if name in {"iron", "brass"} else 27):
                for yy in range(y0, y1):
                    xx = x0 + offset + (yy - y0)
                    if x0 <= xx < x1:
                        atlas[yy, xx:min(xx + 2, x1), :3] *= 0.64
        if name in {"iron", "brass", "deck"}:
            for yy in range(y0 + 12, y1, 30):
                for xx in range(x0 + 12, x1, 30):
                    atlas[yy - 2:yy + 3, xx - 2:xx + 3, :3] *= 0.48
        if name == "teal":
            for yy in range(y0 + 6, y1, 14):
                atlas[yy:yy + 2, x0:x1, :3] = np.clip(base * 1.28, 0, 0.78)

    image = bpy.data.images.new("Homemaker9000PlateAtlas", dq.ATLAS_SIZE, dq.ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(atlas.ravel())
    image.pack()
    return image


def build_vac(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    upper, hose, head = "VacUpperArm", "VacHose", "VacHead"
    shoulder = Vector((-1.72, -0.12, 4.35))
    elbow = Vector((-2.60, -0.24, 3.72))
    wrist = Vector((-2.78, -0.38, 2.58))
    parts.append(dq.cylinder("VAC shoulder bearing", 0.48, 0.52, tuple(shoulder), "brass", material,
                             vertices=14, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=upper))
    parts.append(dq.torus("VAC shoulder teal seal", 0.40, 0.07, tuple(shoulder), "teal", material,
                          rotation=(math.pi / 2, 0, 0), damage_group=upper, major_segments=14))
    parts.append(dq.beam("VAC upper service arm", tuple(shoulder), tuple(elbow), 0.34, "plate", material, upper))
    parts.append(dq.cylinder("VAC elbow joint", 0.34, 0.48, tuple(elbow), "brass", material,
                             vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=upper))
    parts.append(dq.beam("VAC lower service arm", tuple(elbow), tuple(wrist), 0.30, "iron", material, upper))
    parts.append(dq.cylinder("VAC wrist coupling", 0.26, 0.42, tuple(wrist), "brass", material,
                             vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=upper))

    hose_points = [
        Vector((-1.42, -1.04, 3.36)), Vector((-1.70, -1.18, 3.10)), Vector((-1.88, -1.24, 2.72)),
        Vector((-2.06, -1.26, 2.25)), Vector((-2.20, -1.22, 1.78)), Vector((-2.34, -1.14, 1.32)),
        Vector((-2.50, -1.02, 0.92)), Vector((-2.62, -0.84, 0.66)),
    ]
    for index, (start, end) in enumerate(zip(hose_points, hose_points[1:])):
        parts.append(dq.beam(f"VAC corrugated hose {index}", tuple(start), tuple(end),
                             0.38 if index < 3 else 0.34, "soot", material, hose))
        parts.append(dq.torus(f"VAC hose ring {index}", 0.24 if index < 3 else 0.20, 0.045,
                              tuple((start + end) * 0.5), "brass", material,
                              rotation=(math.pi / 2, 0, 0), damage_group=hose, major_segments=10))

    parts.append(dq.box("VAC floor head", (2.10, 1.38, 0.46), (-2.72, -0.52, 0.32),
                        "plate", material, 0.10, damage_group=head))
    parts.append(dq.box("VAC mint bumper", (2.24, 1.48, 0.18), (-2.72, -0.52, 0.16),
                        "cargo", material, 0.035, damage_group=head))
    parts.append(dq.box("VAC teal starburst pane", (0.82, 0.06, 0.42), (-2.72, -1.23, 0.43),
                        "teal", material, 0.02, damage_group=head))
    parts.append(dq.cylinder("VAC amber intake", 0.22, 0.12, (-2.72, -1.27, 0.25), "brass", material,
                             vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=head))
    for x in (-3.48, -1.96):
        parts.append(dq.cylinder(f"VAC caster {x}", 0.18, 0.22, (x, -0.42, 0.13), "soot", material,
                                 vertices=10, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=head))
    for shard, at in enumerate(((-2.65, -0.62, 0.32), (-2.58, -0.54, 0.30), (-2.72, -0.58, 0.28))):
        parts.append(dq.box(f"Hidden VAC scrap {shard}", (0.18, 0.10, 0.08), at,
                            "damage", material, 0.002, damage_group=f"VacShard{shard}"))
    return parts


def bread_slice(parts: list[bpy.types.Object], index: int, x: float, material: bpy.types.Material) -> None:
    group = "RackUpper"
    parts.append(dq.box(f"RACK toast lower {index}", (0.56, 1.28, 0.72), (x, 0, 6.08),
                        "sail", material, 0.10, damage_group=group))
    parts.append(dq.ico_sphere(f"RACK toast crown {index}", 0.39, (x, 0, 6.47),
                               "sail", material, group, scale=(0.72, 1.48, 0.72)))
    parts.append(dq.beam(f"RACK toast amber edge {index}", (x - 0.25, -0.65, 5.82),
                         (x - 0.25, -0.65, 6.52), 0.055, "brass", material, group))


def build_rack(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    group = "RackUpper"
    parts.append(dq.box("RACK battery sill", (4.04, 2.10, 0.30), (0, 0, 5.62),
                        "iron", material, 0.05, damage_group=group))
    parts.append(dq.box("RACK amber rail front", (4.18, 0.10, 0.16), (0, -1.02, 5.76),
                        "brass", material, 0.015, damage_group=group))
    parts.append(dq.box("RACK amber rail rear", (4.18, 0.10, 0.16), (0, 1.02, 5.76),
                        "brass", material, 0.015, damage_group=group))
    for index, x in enumerate(np.linspace(-1.58, 1.58, 7)):
        bread_slice(parts, index, float(x), material)
        parts.append(dq.beam(f"RACK cage bow {index}", (float(x), -1.04, 5.72),
                             (float(x), 1.04, 5.72), 0.055, "brass", material, group))
    parts.append(dq.cylinder("RACK left terminal", 0.24, 0.42, (-2.00, 0, 6.05), "teal", material,
                             vertices=12, bevel=0, damage_group=group))
    parts.append(dq.cylinder("RACK right terminal", 0.24, 0.42, (2.00, 0, 6.05), "teal", material,
                             vertices=12, bevel=0, damage_group=group))
    for shard, at in enumerate(((-1.2, 0, 5.96), (0.1, 0, 5.92), (1.1, 0, 5.94))):
        parts.append(dq.box(f"Hidden toast shard {shard}", (0.24, 0.12, 0.10), at,
                            "damage", material, 0.002, damage_group=f"RackShard{shard}"))
    return parts


def build_core(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    body, left_leg, right_leg, broom, chair = "ChairBody", "ChairLeftLeg", "ChairRightLeg", "ChairBroom", "ChairDebris"
    parts.append(dq.box("CORE house body", (3.70, 2.68, 3.02), (0, 0, 3.78),
                        "plate", material, 0.16, damage_group=body))
    parts.append(dq.box("CORE mint lower apron", (3.18, 2.76, 1.06), (0, -0.02, 2.52),
                        "cargo", material, 0.10, damage_group=body))
    parts.append(dq.box("CORE cream dust ruffle", (3.34, 2.86, 0.28), (0, -0.02, 2.05),
                        "sail", material, 0.06, damage_group=body))
    parts.append(dq.cylinder("CORE polished front", 0.92, 0.42, (0, -1.42, 4.02),
                             "brass", material, vertices=18, rotation=(math.pi / 2, 0, 0),
                             bevel=0, damage_group=body))
    parts.append(dq.torus("CORE amber lens cage", 0.94, 0.09, (0, -1.64, 4.02),
                          "iron", material, rotation=(math.pi / 2, 0, 0),
                          damage_group=body, major_segments=18))
    parts.append(dq.cylinder("CORE amber lens", 0.68, 0.10, (0, -1.69, 4.02),
                             "brass", material, vertices=18, rotation=(math.pi / 2, 0, 0),
                             bevel=0, damage_group=body))
    # This cold shutter begins hidden inside the body and moves over the amber
    # core only in the final chair morph: powered down must read without light.
    parts.append(dq.cylinder("CORE hidden shutdown shutter", 0.66, 0.12, (0, 0, 4.02),
                             "soot", material, vertices=18, rotation=(math.pi / 2, 0, 0),
                             bevel=0, damage_group="CoreShutdownShutter"))
    for x, z in ((-1.12, 4.38), (1.10, 4.42), (-0.78, 3.50), (0.78, 3.48)):
        parts.append(dq.cylinder(f"CORE teal dial {x} {z}", 0.24, 0.10, (x, -1.51, z),
                                 "teal", material, vertices=12, rotation=(math.pi / 2, 0, 0),
                                 bevel=0, damage_group=body))
        parts.append(dq.torus(f"CORE dial cage {x} {z}", 0.26, 0.035, (x, -1.57, z),
                              "brass", material, rotation=(math.pi / 2, 0, 0),
                              damage_group=body, major_segments=12))
    for side in (-1, 1):
        x = side * 1.80
        parts.append(dq.beam(f"CORE side grab rail {side}", (x, -1.05, 3.10), (x, -1.05, 4.74),
                             0.08, "brass", material, body))
        for z in (2.82, 3.30, 3.78, 4.26, 4.74):
            parts.append(dq.cylinder(f"CORE rivet {side} {z}", 0.045, 0.06, (x, -1.38, z),
                                     "brass", material, vertices=8, rotation=(math.pi / 2, 0, 0),
                                     bevel=0, damage_group=body))

    for side, group in ((-1, left_leg), (1, right_leg)):
        x = side * 0.94
        parts.append(dq.cylinder(f"CORE hip {side}", 0.38, 0.56, (x, 0, 2.05),
                                 "brass", material, vertices=12, rotation=(math.pi / 2, 0, 0),
                                 bevel=0, damage_group=group))
        parts.append(dq.beam(f"CORE leg {side}", (x, 0, 1.94), (x, -0.06, 0.72),
                             0.46, "iron", material, group))
        parts.append(dq.ico_sphere(f"CORE foot {side}", 0.58, (x, -0.28, 0.38),
                                   "plate", material, group, scale=(1.15, 1.35, 0.65)))
        parts.append(dq.cylinder(f"CORE foot teal cap {side}", 0.18, 0.12,
                                 (x, -0.92, 0.42), "teal", material, vertices=10,
                                 rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=group))

    shoulder = Vector((1.78, 0.0, 4.32))
    elbow = Vector((2.58, -0.18, 3.58))
    hand = Vector((2.86, -0.44, 2.42))
    parts.append(dq.cylinder("CORE broom shoulder", 0.42, 0.48, tuple(shoulder), "brass", material,
                             vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=broom))
    parts.append(dq.beam("CORE broom upper arm", tuple(shoulder), tuple(elbow), 0.30,
                         "plate", material, broom))
    parts.append(dq.cylinder("CORE broom elbow", 0.28, 0.38, tuple(elbow), "brass", material,
                             vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=broom))
    parts.append(dq.beam("CORE broom forearm", tuple(elbow), tuple(hand), 0.25,
                         "iron", material, broom))
    parts.append(dq.beam("CORE broom handle", tuple(hand), (3.20, -0.60, 0.72),
                         0.12, "rope", material, broom))
    for index, x in enumerate(np.linspace(2.74, 3.60, 9)):
        parts.append(dq.beam(f"CORE broom bristle {index}", (float(x), -0.62, 0.72),
                             (float(x) + (x - 3.16) * 0.18, -0.66, 0.18),
                             0.10, "sail", material, broom))

    parts.append(dq.cylinder("CORE crown mast", 0.10, 0.84, (0, 0, 5.68),
                             "brass", material, vertices=10, damage_group=body))
    parts.append(dq.ico_sphere("CORE crown hub", 0.16, (0, 0, 6.14), "brass", material, body))
    for ray in range(8):
        angle = ray * math.tau / 8
        start = Vector((math.cos(angle) * 0.12, 0, 6.14 + math.sin(angle) * 0.12))
        end = Vector((math.cos(angle) * 0.58, 0, 6.14 + math.sin(angle) * 0.58))
        parts.append(dq.beam(f"CORE starburst ray {ray}", tuple(start), tuple(end),
                             0.055, "brass", material, body))
        parts.append(dq.ico_sphere(f"CORE starburst pip {ray}", 0.09, tuple(end),
                                   "brass", material, body))

    # Act 3 chair is production geometry carried by CORE. It is collapsed into
    # the floor in the basis and expands only under Damage_ChairPose.
    parts.append(dq.box("Chair debris seat", (4.18, 2.36, 0.32), (0, 0.52, 1.12),
                        "deck", material, 0.07, damage_group=chair))
    parts.append(dq.box("Chair debris back", (4.12, 0.34, 3.34), (0, 1.54, 2.46),
                        "plate", material, 0.07, rotation=(math.radians(-8), 0, 0), damage_group=chair))
    for side in (-1, 1):
        x = side * 1.82
        parts.append(dq.beam(f"Chair rear leg {side}", (x, 1.30, 1.08), (x, 1.48, 0.10),
                             0.20, "iron", material, chair))
        parts.append(dq.beam(f"Chair front leg {side}", (x, -0.46, 1.08), (x, -0.62, 0.10),
                             0.20, "iron", material, chair))
        parts.append(dq.beam(f"Chair arm {side}", (x, -0.30, 1.78), (x, 1.18, 1.78),
                             0.18, "brass", material, chair))
        parts.append(dq.ico_sphere(f"Chair arm finial {side}", 0.16, (x, -0.34, 1.80),
                                   "brass", material, chair))
    parts.append(dq.beam("Chair back brace one", (-1.82, 1.64, 1.28), (1.82, 1.64, 3.62),
                         0.14, "brass", material, chair))
    parts.append(dq.beam("Chair back brace two", (1.82, 1.64, 1.28), (-1.82, 1.64, 3.62),
                         0.14, "brass", material, chair))
    return parts


def group_bounds(obj: bpy.types.Object, group_name: str) -> tuple[Vector, Vector]:
    points = [obj.data.vertices[index].co for index in dq.group_vertex_indices(obj, group_name)]
    assert points, f"missing group {obj.name}:{group_name}"
    return (
        Vector(tuple(min(point[axis] for point in points) for axis in range(3))),
        Vector(tuple(max(point[axis] for point in points) for axis in range(3))),
    )


def group_center(obj: bpy.types.Object, group_name: str) -> Vector:
    minimum, maximum = group_bounds(obj, group_name)
    return (minimum + maximum) * 0.5


def rotate_x(co: Vector, pivot: Vector, angle: float) -> None:
    local = co - pivot
    y = local.y * math.cos(angle) - local.z * math.sin(angle)
    z = local.y * math.sin(angle) + local.z * math.cos(angle)
    co.y = pivot.y + y
    co.z = pivot.z + z


def add_damage_shapes(vac: bpy.types.Object, rack: bpy.types.Object, core: bpy.types.Object) -> None:
    vac.shape_key_add(name="Basis")
    dropped = vac.shape_key_add(name="Damage_DroppedVac")
    pivot = group_center(vac, "VacUpperArm")
    for index in dq.group_vertex_indices(vac, "VacUpperArm"):
        co = dropped.data[index].co
        dq.rotate_y(co, pivot, math.radians(-28))
        co += Vector((-0.18, -0.18, -0.46))
    for index in dq.group_vertex_indices(vac, "VacHose"):
        co = dropped.data[index].co
        co += Vector((-0.18, -0.20, -0.55 - max(0.0, co.z - 0.8) * 0.12))
    for index in dq.group_vertex_indices(vac, "VacHead"):
        dropped.data[index].co += Vector((-0.68, -0.88, 0.02))
    for shard, move in enumerate((Vector((-1.1, -1.0, -0.10)), Vector((-0.2, -1.35, -0.18)), Vector((0.45, -0.82, -0.12)))):
        for index in dq.group_vertex_indices(vac, f"VacShard{shard}"):
            dropped.data[index].co += move

    rack.shape_key_add(name="Basis")
    spent = rack.shape_key_add(name="Damage_SpentRack")
    minimum, maximum = group_bounds(rack, "RackUpper")
    pivot = Vector((minimum.x, (minimum.y + maximum.y) * 0.5, minimum.z))
    for index in dq.group_vertex_indices(rack, "RackUpper"):
        co = spent.data[index].co
        rotate_x(co, pivot, math.radians(18))
        dq.rotate_y(co, pivot, math.radians(-14))
        co += Vector((2.18, 0.78, -4.70))
    for shard, move in enumerate((Vector((-1.35, -1.15, -5.65)), Vector((0.15, -1.55, -5.60)), Vector((1.18, -0.82, -5.60)))):
        for index in dq.group_vertex_indices(rack, f"RackShard{shard}"):
            spent.data[index].co += move

    core.shape_key_add(name="Basis")
    chair_pose = core.shape_key_add(name="Damage_ChairPose")
    body_pivot = group_center(core, "ChairBody")
    for index in dq.group_vertex_indices(core, "ChairBody"):
        co = chair_pose.data[index].co
        rotate_x(co, body_pivot, math.radians(-12))
        co += Vector((0.0, 0.72, -1.30))
    for index in dq.group_vertex_indices(core, "CoreShutdownShutter"):
        co = chair_pose.data[index].co
        rotate_x(co, body_pivot, math.radians(-12))
        co += Vector((0.0, -1.02, -1.30))
    for group_name, x_move in (("ChairLeftLeg", -0.22), ("ChairRightLeg", 0.22)):
        pivot = group_center(core, group_name)
        for index in dq.group_vertex_indices(core, group_name):
            co = chair_pose.data[index].co
            rotate_x(co, pivot, math.radians(-42))
            co += Vector((x_move, -0.90, -0.03))
    broom_pivot = group_center(core, "ChairBroom")
    for index in dq.group_vertex_indices(core, "ChairBroom"):
        co = chair_pose.data[index].co
        dq.rotate_y(co, broom_pivot, math.radians(18))
        co += Vector((-0.38, 0.48, 0.04))

    # Keep the target's full chair coordinates, but make the intact basis a
    # near-zero bundle under the body. At weight 1 the debris chair builds.
    anchor = Vector((0.0, 0.55, 0.12))
    basis = core.data.shape_keys.key_blocks["Basis"]
    for index in dq.group_vertex_indices(core, "ChairDebris"):
        basis.data[index].co = anchor + (basis.data[index].co - anchor) * 0.006

    for obj in (vac, rack, core):
        obj.active_shape_key_index = 0
        for key in obj.data.shape_keys.key_blocks:
            key.value = 0.0
        obj.data.update()


def recenter_shape_keyed_basis(objects: tuple[bpy.types.Object, ...]) -> None:
    """Re-center the basis after the hidden chair bundle changes its bounds.

    Apply the same translation to every key block so the authored damage
    deltas remain unchanged while the exported intact basis stays base-center.
    """
    points = [
        point.co
        for obj in objects
        for point in obj.data.shape_keys.key_blocks["Basis"].data
    ]
    minimum = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    maximum = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    offset = Vector(((minimum.x + maximum.x) * 0.5, (minimum.y + maximum.y) * 0.5, minimum.z))
    for obj in objects:
        keys = obj.data.shape_keys
        assert keys is not None
        for key in keys.key_blocks:
            for point in key.data:
                point.co -= offset
        obj.data.update()


def shape_basis_bounds(objects: tuple[bpy.types.Object, ...]) -> tuple[Vector, Vector]:
    points = [
        point.co
        for obj in objects
        for point in obj.data.shape_keys.key_blocks["Basis"].data
    ]
    return (
        Vector(tuple(min(point[axis] for point in points) for axis in range(3))),
        Vector(tuple(max(point[axis] for point in points) for axis in range(3))),
    )


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    dq.reset_scene()
    atlas = create_atomic_atlas()
    material = dq.create_material(atlas)
    material.name = "Homemaker9000PaintedMaterial"
    vac = dq.join_component("vac", build_vac(material), material)
    rack = dq.join_component("rack", build_rack(material), material)
    core = dq.join_component("core", build_core(material), material)
    objects = (vac, rack, core)
    dq.MODEL_LENGTH = MODEL_LENGTH
    dq.normalize_base_center(objects)
    add_damage_shapes(*objects)
    recenter_shape_keyed_basis(objects)

    triangles = dq.triangle_count(objects)
    minimum, maximum = shape_basis_bounds(objects)
    assert triangles <= 12_000
    assert abs(maximum.x - minimum.x - MODEL_LENGTH) < 0.01
    assert abs(minimum.z) < 0.001
    assert abs((maximum.x + minimum.x) * 0.5) < 0.001
    assert abs((maximum.y + minimum.y) * 0.5) < 0.001
    dq.BLEND, dq.GLB = BLEND, GLB
    dq.export(objects)
    print(json.dumps({
        "blend": str(BLEND), "glb": str(GLB), "sha256": hashlib.sha256(GLB.read_bytes()).hexdigest(),
        "sourcePlate": {str(REFERENCE.relative_to(ROOT)): hashlib.sha256(REFERENCE.read_bytes()).hexdigest()},
        "components": [obj.name for obj in objects],
        "damageMorphs": [obj.data.shape_keys.key_blocks[1].name for obj in objects],
        "triangles": triangles,
        "boundsBlender": {"min": [round(v, 6) for v in minimum], "max": [round(v, 6) for v in maximum]},
    }, indent=2))


if __name__ == "__main__":
    main()
