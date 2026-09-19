from pathlib import Path
import hashlib
import json
import math

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REFERENCE = ROOT / "assets/raw/plate-e2-boss-component.png"
BLEND = OUT / "railcar.blend"
GLB = OUT / "railcar.glb"
ATLAS_SIZE = 1024
RAIL_GAUGE = 0.78
MODEL_LENGTH = 3.30

# Native material tiles follow the E2 plate's mottled iron, etched brass and lamps.
SURFACE_REFERENCE = ROOT / "assets/raw/railcar-atlas-fidelity-e2.png"
REGIONS = {
    "dark": (0.02, 0.515, 0.24, 0.98),
    "brass": (0.265, 0.515, 0.49, 0.98),
    "teal": (0.515, 0.515, 0.74, 0.98),
    "soot": (0.765, 0.515, 0.98, 0.98),
    "iron": (0.02, 0.02, 0.24, 0.49),
    "edge": (0.265, 0.02, 0.49, 0.49),
    "glass": (0.515, 0.02, 0.74, 0.49),
    "damage": (0.765, 0.02, 0.98, 0.49),
}

WHEEL_AXLES = ((-0.70, 0.18), (-0.37, 0.18), (-0.04, 0.18), (0.74, 0.15), (1.05, 0.15))



def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.length_unit = "METERS"


def create_atlas() -> tuple[bpy.types.Image, str]:
    atlas = bpy.data.images.load(str(SURFACE_REFERENCE), check_existing=False)
    atlas.name = "ArmoredRailcarNativeSurfaceAtlas"
    atlas.colorspace_settings.name = "sRGB"
    atlas.scale(ATLAS_SIZE, ATLAS_SIZE)
    atlas.pack()
    return atlas, hashlib.sha256(REFERENCE.read_bytes()).hexdigest()


def create_material(image: bpy.types.Image) -> bpy.types.Material:
    material = bpy.data.materials.new("ArmoredRailcarPlateMaterial")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Linear"
    texture.extension = "REPEAT"
    shader.inputs["Metallic"].default_value = 0.32
    shader.inputs["Roughness"].default_value = 0.66
    shader.inputs["Emission Color"].default_value = (0, 0, 0, 1)
    shader.inputs["Emission Strength"].default_value = 0
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def mark_all(obj: bpy.types.Object, group_name: str | None) -> None:
    if not group_name:
        return
    group = obj.vertex_groups.new(name=group_name)
    group.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")


def tag(obj: bpy.types.Object, region: str, material: bpy.types.Material, bevel: float = 0.008, damage_group: str | None = None, smooth: bool = False) -> bpy.types.Object:
    obj["atlas_region"] = region
    obj.data.materials.append(material)
    mark_all(obj, damage_group)
    if bevel > 0:
        modifier = obj.modifiers.new("Painted iron edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        modifier.limit_method = "ANGLE"
    if smooth:
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    return obj


def box(name: str, size: tuple[float, float, float], at: tuple[float, float, float], region: str, material: bpy.types.Material, bevel: float = 0.008, rotation: tuple[float, float, float] = (0, 0, 0), damage_group: str | None = None) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=at, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = tuple(value * 0.5 for value in size)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return tag(obj, region, material, bevel, damage_group)


def cylinder(name: str, radius: float, depth: float, at: tuple[float, float, float], region: str, material: bpy.types.Material, vertices: int = 12, rotation: tuple[float, float, float] = (0, 0, 0), bevel: float = 0.006, damage_group: str | None = None) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=at, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return tag(obj, region, material, bevel, damage_group, smooth=True)


def cone(name: str, radius1: float, radius2: float, depth: float, at: tuple[float, float, float], region: str, material: bpy.types.Material, vertices: int = 12, rotation: tuple[float, float, float] = (0, 0, 0), damage_group: str | None = None) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=at, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return tag(obj, region, material, 0.006, damage_group, smooth=True)


def torus(name: str, major_radius: float, minor_radius: float, at: tuple[float, float, float], region: str, material: bpy.types.Material, rotation: tuple[float, float, float] = (0, 0, 0), damage_group: str | None = None) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(major_segments=12, minor_segments=4, location=at, major_radius=major_radius, minor_radius=minor_radius, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return tag(obj, region, material, 0, damage_group, smooth=True)


def steam_puff(name: str, radius: float, at: tuple[float, float, float], region: str, material: bpy.types.Material, damage_group: str) -> bpy.types.Object:
    # Fixed ring topology avoids Blender's nondeterministic sphere face ordering.
    vertices = [(0, 0, radius)]
    for ring in range(1, 4):
        phi = math.pi * ring / 4
        vertices.extend((radius * math.sin(phi) * math.cos(math.tau * i / 8), radius * math.sin(phi) * math.sin(math.tau * i / 8), radius * math.cos(phi)) for i in range(8))
    vertices.append((0, 0, -radius))
    faces = [(0, 1 + i, 1 + (i + 1) % 8) for i in range(8)]
    for start in (1, 9):
        faces.extend((start + i, start + 8 + i, start + 8 + (i + 1) % 8, start + (i + 1) % 8) for i in range(8))
    faces.extend((25, 17 + (i + 1) % 8, 17 + i) for i in range(8))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    uv = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        x, y, _ = vertices[loop.vertex_index]
        uv.data[loop.index].uv = (x / (2 * radius) + 0.5, y / (2 * radius) + 0.5)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = at
    obj["keep_authored_uv"] = True
    return tag(obj, region, material, 0, damage_group, smooth=True)


def subdivide(obj: bpy.types.Object, cuts: int = 2) -> bpy.types.Object:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.subdivide(number_cuts=cuts)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)
    return obj


def beam(name: str, start: tuple[float, float, float], end: tuple[float, float, float], width: float, region: str, material: bpy.types.Material, damage_group: str | None = None) -> bpy.types.Object:
    a, b = Vector(start), Vector(end)
    direction = b - a
    obj = box(name, (width, width, direction.length), tuple((a + b) * 0.5), region, material, bevel=min(0.006, width * 0.18), damage_group=damage_group)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    obj.select_set(False)
    return obj


def lantern(name: str, at: tuple[float, float, float], material: bpy.types.Material, group: str | None = None) -> list[bpy.types.Object]:
    x, y, z = at
    parts = [
        cylinder(f"{name} glass", 0.050, 0.20, at, "teal", material, vertices=8, bevel=0, damage_group=group),
        cylinder(f"{name} base", 0.065, 0.025, (x, y, z - 0.115), "brass", material, vertices=8, bevel=0, damage_group=group),
        cylinder(f"{name} cap", 0.065, 0.035, (x, y, z + 0.115), "brass", material, vertices=8, bevel=0, damage_group=group),
        box(f"{name} bracket", (0.09, 0.035, 0.035), (x + 0.04, y, z + 0.14), "edge", material, bevel=0, damage_group=group),
    ]
    for dx, dy in ((-0.05, 0), (0.05, 0), (0, -0.05), (0, 0.05)):
        parts.append(box(f"{name} cage {dx} {dy}", (0.014, 0.014, 0.22), (x + dx, y + dy, z), "brass", material, bevel=0, damage_group=group))
    for part in parts:
        mark_all(part, f"RoundX:{name}")
    return parts


def add_rivets(parts: list[bpy.types.Object], prefix: str, xs: tuple[float, ...], y: float, z: float, material: bpy.types.Material, group: str | None = None) -> None:
    side = 1 if y > 0 else -1
    for index, x in enumerate(xs):
        parts.append(cylinder(f"{prefix} rivet {index}", 0.026, 0.035, (x, y, z), "brass", material, vertices=6, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=group))


def build_wheels(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    parts.append(box("Black iron underframe", (2.12, 0.72, 0.20), (0.02, 0, 0.43), "dark", material, 0.016))
    parts.append(box("Left armored sill", (2.02, 0.10, 0.11), (0.02, -0.35, 0.51), "iron", material, 0.007))
    parts.append(box("Right armored sill", (2.02, 0.10, 0.11), (0.02, 0.35, 0.51), "iron", material, 0.007))
    parts.append(box("Front armor block", (0.16, 0.78, 0.24), (-0.87, 0, 0.49), "dark", material, 0.012))
    parts.append(box("Rear armored buffer", (0.14, 0.72, 0.18), (1.08, 0, 0.43), "iron", material, 0.008))
    parts.append(beam("Rear coupling", (1.08, 0, 0.35), (1.24, 0, 0.28), 0.075, "dark", material))
    parts.append(box("Rear service platform", (0.28, 0.62, 0.055), (1.32, 0, 0.43), "iron", material, bevel=0))
    for x in (1.21, 1.43):
        for y in (-0.27, 0.27):
            parts.append(box(f"Platform rail post {x} {y}", (0.02, 0.02, 0.22), (x, y, 0.55), "edge", material, bevel=0))
    for y in (-0.27, 0.27):
        parts.append(box(f"Platform side rail {y}", (0.24, 0.02, 0.02), (1.32, y, 0.66), "brass", material, bevel=0))
    parts.append(box("Platform end rail", (0.02, 0.56, 0.02), (1.43, 0, 0.66), "brass", material, bevel=0))

    for axle, (x, radius) in enumerate(WHEEL_AXLES):
        damage = "DamageBent" if axle == 0 else None
        center_z = radius + 0.025
        parts.append(cylinder(f"Axle {axle}", 0.050, 0.82, (x, 0, center_z), "dark", material, vertices=8, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=damage))
        for side in (-1, 1):
            y = side * 0.39
            parts.append(torus(f"Heavy wheel rim {axle} {side}", radius - 0.035, 0.043, (x, y, center_z), "edge", material, rotation=(math.pi / 2, 0, 0), damage_group=damage))
            parts.append(cylinder(f"Armored wheel hub {axle} {side}", 0.043, 0.055, (x, y, center_z), "brass", material, vertices=10, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=damage))
            parts.append(box(f"Suspension armor {axle} {side}", (0.15, 0.075, 0.20), (x, side * 0.39, 0.43), "iron", material, 0.006, damage_group=damage))
            for spoke in range(4):
                angle = math.radians(spoke * 45)
                reach = radius - 0.045
                dx, dz = math.cos(angle) * reach, math.sin(angle) * reach
                parts.append(beam(f"Wheel spoke {axle} {side} {spoke}", (x - dx, y, center_z - dz), (x + dx, y, center_z + dz), 0.026, "edge", material, damage))
    for side in (-1, 1):
        y = side * 0.445
        parts.append(beam(f"Leading drive rod {side}", (-0.70, y, 0.18), (-0.04, y, 0.18), 0.042, "brass", material, "DamageBent"))
        parts.append(beam(f"Rear drive rod {side}", (0.74, y, 0.14), (1.05, y, 0.14), 0.042, "brass", material))
        parts.append(beam(f"Upper suspension rail {side}", (-0.75, y, 0.45), (0.96, y, 0.45), 0.040, "edge", material, "DamageBent"))

    for side in (-1, 1):
        parts.append(cylinder(f"Banded underbody reservoir {side}", 0.13, 0.43, (0.45, side * 0.27, 0.28), "iron", material, vertices=12, rotation=(0, math.pi / 2, 0), bevel=0))
        for x in (0.29, 0.61):
            parts.append(cylinder(f"Reservoir band {side} {x}", 0.14, 0.026, (x, side * 0.27, 0.28), "brass", material, vertices=12, rotation=(0, math.pi / 2, 0), bevel=0))

    # Deep armored wedge: the reference's most important boss silhouette cue.
    tine_ys = (-0.56, -0.38, -0.19, 0.0, 0.19, 0.38, 0.56)
    for index, y in enumerate(tine_ys):
        parts.append(beam(f"Cowcatcher blade {index}", (-0.83, y * 0.50, 0.54), (-1.38, y, 0.10), 0.058, "edge", material))
    parts.append(beam("Cowcatcher cutting edge", (-1.38, -0.58, 0.10), (-1.38, 0.58, 0.10), 0.070, "dark", material))
    parts.append(beam("Cowcatcher armored brow", (-0.84, -0.34, 0.55), (-0.84, 0.34, 0.55), 0.075, "iron", material))
    parts.append(beam("Cowcatcher left cheek", (-0.84, -0.34, 0.55), (-1.38, -0.58, 0.10), 0.082, "dark", material))
    parts.append(beam("Cowcatcher right cheek", (-0.84, 0.34, 0.55), (-1.38, 0.58, 0.10), 0.082, "dark", material))
    parts.append(beam("Cowcatcher central armored ram", (-0.83, 0, 0.57), (-1.38, 0, 0.12), 0.14, "iron", material))
    parts.append(beam("Cowcatcher left ram brace", (-0.87, -0.29, 0.51), (-1.34, -0.16, 0.15), 0.085, "brass", material))
    parts.append(beam("Cowcatcher right ram brace", (-0.87, 0.29, 0.51), (-1.34, 0.16, 0.15), 0.085, "brass", material))
    parts.append(box("Cowcatcher left armored blade", (0.66, 0.16, 0.16), (-1.11, -0.31, 0.33), "iron", material, 0.008, rotation=(0, math.radians(-39), 0)))
    parts.append(box("Cowcatcher right armored blade", (0.66, 0.16, 0.16), (-1.11, 0.31, 0.33), "iron", material, 0.008, rotation=(0, math.radians(-39), 0)))
    for x, scale in ((-1.20, 0.82), (-1.03, 0.62)):
        parts.append(beam(f"Cowcatcher cross rail {x}", (x, -0.58 * scale, 0.24 + (x + 1.20) * 0.60), (x, 0.58 * scale, 0.24 + (x + 1.20) * 0.60), 0.045, "brass", material))
    add_rivets(parts, "Left frame", (-0.72, -0.42, -0.12, 0.18, 0.48, 0.78), -0.475, 0.51, material)
    add_rivets(parts, "Right frame", (-0.72, -0.42, -0.12, 0.18, 0.48, 0.78), 0.475, 0.51, material)
    return parts


def build_boiler(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    parts.append(cylinder("Blackened riveted boiler", 0.275, 1.48, (-0.06, 0, 0.70), "iron", material, vertices=16, rotation=(0, math.pi / 2, 0), bevel=0))
    parts.append(box("Armored smokebox shroud", (0.17, 0.62, 0.58), (-0.88, 0, 0.70), "dark", material, 0.018))
    parts.append(cylinder("Smokebox face", 0.285, 0.07, (-0.98, 0, 0.70), "soot", material, vertices=16, rotation=(0, math.pi / 2, 0), bevel=0))
    parts.append(torus("Smokebox armored ring", 0.248, 0.032, (-1.02, 0, 0.70), "brass", material, rotation=(0, math.pi / 2, 0)))
    parts.extend(lantern("Front lantern", (-1.08, 0, 0.88), material))
    for index in range(10):
        angle = math.radians(index * 36)
        parts.append(cylinder(f"Smokebox face rivet {index}", 0.021, 0.025, (-1.045, math.cos(angle) * 0.218, 0.70 + math.sin(angle) * 0.218), "brass", material, vertices=6, rotation=(0, math.pi / 2, 0), bevel=0))
    for index, x in enumerate((-0.74, -0.47, -0.18, 0.11, 0.42)):
        parts.append(torus(f"Boiler armor band {index}", 0.277, 0.024, (x, 0, 0.70), "brass", material, rotation=(0, math.pi / 2, 0), damage_group="DamageVent" if index == 4 else None))
    # Tall, flanged stack and squat pressure domes match the concept rather than
    # a friendly toy-locomotive profile.
    parts.append(cylinder("Stack throat", 0.090, 0.20, (-0.62, 0, 1.00), "dark", material, vertices=12))
    parts.append(torus("Stack lower flange", 0.105, 0.022, (-0.62, 0, 1.04), "brass", material))
    parts.append(cone("Stack flare", 0.132, 0.100, 0.12, (-0.62, 0, 1.13), "edge", material, vertices=12))
    parts.append(torus("Stack crown", 0.118, 0.024, (-0.62, 0, 1.195), "brass", material))
    parts.append(cylinder("Steam dome", 0.088, 0.14, (-0.12, 0, 0.99), "brass", material, vertices=12))
    parts.append(cone("Steam dome crown", 0.100, 0.055, 0.07, (-0.12, 0, 1.075), "brass", material, vertices=12))
    parts.append(cylinder("Rear pressure dome", 0.065, 0.12, (0.33, 0, 0.975), "edge", material, vertices=10))
    parts.append(cone("Rear pressure cap", 0.078, 0.042, 0.06, (0.33, 0, 1.055), "brass", material, vertices=10))
    parts.append(box("Boiler armored spine", (1.18, 0.14, 0.07), (-0.06, 0, 0.965), "dark", material, 0.008))
    parts.append(cylinder("Safety valve left", 0.038, 0.14, (0.47, -0.11, 0.97), "brass", material, vertices=8, damage_group="DamageVent"))
    parts.append(cylinder("Safety valve right", 0.038, 0.14, (0.47, 0.11, 0.97), "brass", material, vertices=8, damage_group="DamageVent"))
    parts.append(box("Left rupture hatch", (0.24, 0.045, 0.13), (0.42, -0.25, 0.84), "damage", material, 0.004, damage_group="DamageVent"))
    parts.append(box("Right rupture hatch", (0.24, 0.045, 0.13), (0.42, 0.25, 0.84), "damage", material, 0.004, damage_group="DamageVent"))
    parts.append(box("Hidden left boiler rupture", (0.20, 0.025, 0.10), (0.42, -0.23, 0.84), "soot", material, 0, damage_group="DamageVentHole"))
    parts.append(box("Hidden right boiler rupture", (0.20, 0.025, 0.10), (0.42, 0.23, 0.84), "soot", material, 0, damage_group="DamageVentHole"))
    parts.append(steam_puff("Hidden steam puff small", 0.065, (0.37, 0, 0.74), "glass", material, "DamageSteamSmall"))
    parts.append(steam_puff("Hidden steam puff medium", 0.085, (0.29, 0, 0.72), "glass", material, "DamageSteamMedium"))
    parts.append(steam_puff("Hidden steam puff large", 0.105, (0.21, 0, 0.70), "glass", material, "DamageSteamLarge"))
    for side in (-1, 1):
        y = side * 0.305
        parts.append(box(f"Boiler flank armor {side}", (1.18, 0.055, 0.16), (-0.08, side * 0.28, 0.62), "dark", material, 0.008))
        parts.append(beam(f"Boiler lower pipe {side}", (-0.78, side * 0.32, 0.54), (0.58, side * 0.32, 0.52), 0.042, "brass", material))
        parts.append(beam(f"Boiler upper pipe {side}", (-0.54, side * 0.31, 0.84), (0.54, side * 0.31, 0.81), 0.030, "edge", material))
        for gauge, (x, z, radius) in enumerate(((-0.42, 0.74, 0.065), (-0.16, 0.64, 0.050), (0.14, 0.79, 0.058))):
            parts.append(torus(f"Gauge collar {side} {gauge}", radius, 0.016, (x, side * 0.326, z), "brass", material, rotation=(math.pi / 2, 0, 0)))
            parts.append(cylinder(f"Teal gauge {side} {gauge}", radius * 0.70, 0.020, (x, side * 0.342, z), "teal", material, vertices=10, rotation=(math.pi / 2, 0, 0), bevel=0))
        parts.append(cylinder(f"Side pressure cylinder {side}", 0.065, 0.34, (0.30, side * 0.35, 0.61), "iron", material, vertices=8, rotation=(0, math.pi / 2, 0), bevel=0))
        add_rivets(parts, f"Boiler {side}", (-0.76, -0.59, -0.42, -0.25, -0.08, 0.09, 0.26, 0.43, 0.58), side * 0.325, 0.54, material)
    return parts


def build_cabin(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    parts.append(box("Cab black armored base", (0.68, 0.78, 0.36), (0.88, 0, 0.62), "iron", material, 0.012))
    parts.append(box("Cab far riveted wall", (0.60, 0.06, 0.42), (0.88, -0.37, 0.84), "dark", material, 0.010))
    parts.append(subdivide(box("Cab near caving wall", (0.60, 0.06, 0.42), (0.88, 0.37, 0.84), "dark", material, 0.008, damage_group="DamageCabWall"), 2))
    parts.append(box("Cab front bulkhead", (0.07, 0.70, 0.43), (0.55, 0, 0.84), "iron", material, 0.010))
    parts.append(box("Cab rear bulkhead", (0.08, 0.70, 0.45), (1.20, 0, 0.83), "iron", material, 0.010, damage_group="DamageDent"))
    # Two sloped roof plates create the armored bunker silhouette in the plate.
    parts.append(box("Cab roof left slope", (0.70, 0.48, 0.09), (0.88, -0.205, 1.075), "dark", material, 0.012, rotation=(math.radians(16), 0, 0), damage_group="DamageCabRoof"))
    parts.append(box("Cab roof right slope", (0.70, 0.48, 0.09), (0.88, 0.205, 1.075), "dark", material, 0.012, rotation=(math.radians(-16), 0, 0), damage_group="DamageCabRoof"))
    parts.append(box("Cab roof crown", (0.70, 0.22, 0.070), (0.88, 0, 1.155), "dark", material, 0.008, damage_group="DamageCabRoof"))
    # A raised perimeter rail leaves open air above the armored roof.
    for side in (-1, 1):
        parts.append(beam(f"Roof guard long {side}", (0.62, side * 0.30, 1.245), (1.15, side * 0.30, 1.245), 0.028, "brass", material, "DamageCabRoof"))
        for x in (0.63, 1.14):
            parts.append(beam(f"Roof guard post {side} {x}", (x, side * 0.30, 1.085), (x, side * 0.30, 1.245), 0.026, "edge", material, "DamageCabRoof"))
    parts.append(beam("Roof guard front", (0.62, -0.30, 1.245), (0.62, 0.30, 1.245), 0.028, "brass", material, "DamageCabRoof"))
    parts.append(beam("Roof guard rear", (1.15, -0.30, 1.245), (1.15, 0.30, 1.245), 0.028, "brass", material, "DamageCabRoof"))
    parts.append(box("Rear armor plate", (0.10, 0.72, 0.56), (1.23, 0, 0.75), "dark", material, 0.01, damage_group="DamageDent"))
    for side in (-1, 1):
        y = side * 0.392
        damage = "DamageDent" if side > 0 else None
        parts.append(box(f"Cab narrow window {side}", (0.36, 0.025, 0.13), (0.88, y, 0.91), "soot", material, 0.004, damage_group=damage))
        parts.append(box(f"Cab window top guard {side}", (0.45, 0.035, 0.050), (0.88, side * 0.414, 0.995), "brass", material, 0.004, damage_group=damage))
        parts.append(box(f"Cab window lower guard {side}", (0.45, 0.035, 0.050), (0.88, side * 0.414, 0.825), "brass", material, 0.004, damage_group=damage))
        for z in (0.875, 0.945):
            parts.append(box(f"Cab window louver {side} {z}", (0.36, 0.020, 0.018), (0.88, side * 0.425, z), "edge", material, bevel=0, damage_group=damage))
        parts.append(box(f"Cab window vertical bar {side}", (0.050, 0.035, 0.20), (0.88, side * 0.418, 0.91), "edge", material, 0.004, damage_group=damage))
        parts.append(box(f"Cab corner brace front {side}", (0.060, 0.045, 0.44), (0.60, side * 0.414, 0.84), "brass", material, 0.004, damage_group=damage))
        parts.append(box(f"Cab corner brace rear {side}", (0.060, 0.045, 0.44), (1.16, side * 0.414, 0.84), "brass", material, 0.004, damage_group=damage))
        # Faceted outer plates turn the cabin from an upright box into an armored bunker.
        parts.append(box(f"Cab forward cheek plate {side}", (0.28, 0.045, 0.24), (0.70, side * 0.404, 0.71), "iron", material, 0.005, rotation=(0, math.radians(-12), 0), damage_group=damage))
        parts.append(box(f"Cab rear cheek plate {side}", (0.28, 0.045, 0.24), (1.06, side * 0.404, 0.71), "iron", material, 0.005, rotation=(0, math.radians(12), 0), damage_group=damage))
        add_rivets(parts, f"Cab {side}", (0.62, 0.75, 0.88, 1.01, 1.14), side * 0.425, 0.62, material, damage)
        parts.extend(lantern(f"Cab lantern {side}", (1.18, side * 0.48, 0.82), material, damage))
    # A torn outline replaces broad diagonal crack strips across the windows.
    breach_outline = ((0.70, 0.68), (0.78, 0.73), (0.77, 0.83), (0.90, 0.78), (1.04, 0.81), (1.01, 0.67), (1.08, 0.57), (0.92, 0.60), (0.84, 0.53), (0.82, 0.63))
    rupture = bpy.data.meshes.new("Jagged cabin breach")
    rupture.from_pydata([(x, 0.18, z) for x, z in breach_outline], [], [tuple(range(10))])
    breach = bpy.data.objects.new("Hidden cabin rupture void", rupture)
    bpy.context.collection.objects.link(breach)
    parts.append(tag(breach, "soot", material, 0, "DamageCabVoid"))
    for edge, (start, end) in enumerate(zip(breach_outline, breach_outline[1:] + breach_outline[:1])):
        a, b = Vector((start[0], 0.195, start[1])), Vector((end[0], 0.195, end[1]))
        direction = b - a
        torn = box(f"Hidden torn metal edge {edge}", (0.014, 0.012, direction.length), tuple((a + b) * 0.5), "brass", material, bevel=0, damage_group="DamageCabVoid")
        torn.rotation_mode = "QUATERNION"
        torn.rotation_quaternion = direction.to_track_quat("Z", "Y")
        parts.append(torn)
    parts.append(box("Rear teal firing slit", (0.025, 0.24, 0.08), (1.285, 0, 0.88), "soot", material, 0.004, damage_group="DamageDent"))
    parts.append(beam("Cab rear ladder left", (1.28, -0.31, 0.44), (1.28, -0.31, 0.76), 0.034, "brass", material))
    parts.append(beam("Cab rear ladder right", (1.28, 0.31, 0.44), (1.28, 0.31, 0.76), 0.034, "brass", material))
    for z in (0.50, 0.62, 0.74):
        parts.append(beam(f"Cab ladder rung {z}", (1.28, -0.31, z), (1.28, 0.31, z), 0.03, "brass", material))
    return parts


def prepare_part(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    for modifier in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    # Steam has explicit topology and UVs; automatic unwrap varies across rebuilds.
    if not obj.get("keep_authored_uv", False):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.025)
        bpy.ops.object.mode_set(mode="OBJECT")
    uv = obj.data.uv_layers.active.data
    coords = np.array([[loop.uv.x, loop.uv.y] for loop in uv], dtype=np.float32)
    low = coords.min(axis=0)
    span = np.maximum(coords.max(axis=0) - low, 1e-6)
    u0, v0, u1, v1 = REGIONS[obj["atlas_region"]]
    for loop, coord in zip(uv, coords):
        normalized = (coord - low) / span
        loop.uv = (u0 + normalized[0] * (u1 - u0), v0 + normalized[1] * (v1 - v0))
    obj.select_set(False)


def join_component(name: str, parts: list[bpy.types.Object], material: bpy.types.Material) -> bpy.types.Object:
    for part in parts:
        if part.name.startswith(("Heavy wheel rim", "Armored wheel hub", "Wheel spoke", "Gauge collar", "Teal gauge", "Stack", "Steam dome", "Rear pressure", "Safety valve")):
            mark_all(part, f"RoundX:{part.name}")
        prepare_part(part)
    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    component = bpy.context.object
    component.name = name
    component.data.name = f"{name}Mesh"
    component.data.materials.clear()
    component.data.materials.append(material)
    for polygon in component.data.polygons:
        polygon.material_index = 0
    component.data.uv_layers.active.name = "UVMap"
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    component.select_set(False)
    return component


def group_vertex_indices(obj: bpy.types.Object, group_name: str) -> set[int]:
    group = obj.vertex_groups.get(group_name)
    if group is None:
        return set()
    index = group.index
    return {vertex.index for vertex in obj.data.vertices if any(item.group == index for item in vertex.groups)}


def add_damage_shapes(wheels: bpy.types.Object, boiler: bpy.types.Object, cabin: bpy.types.Object) -> None:
    wheels.shape_key_add(name="Basis")
    bent = wheels.shape_key_add(name="Damage_BentWheels")
    marked = group_vertex_indices(wheels, "DamageBent")
    for index in marked:
        co = bent.data[index].co
        side = 1 if co.y >= 0 else -1
        center = Vector((WHEEL_AXLES[0][0], side * 0.39, WHEEL_AXLES[0][1] + 0.008))
        local = co - center
        angle = math.radians(42 * side)
        new_y = local.y * math.cos(angle) - local.z * math.sin(angle)
        new_z = local.y * math.sin(angle) + local.z * math.cos(angle)
        co.y = center.y + new_y + side * 0.11
        co.x += (co.z - center.z) * 0.16
        derail_lift = max(0.0, min(1.0, (-co.x - 0.12) / 0.62)) * (0.25 if side > 0 else 0.10)
        co.x -= derail_lift * 0.45
        co.z = max(0.0, center.z + new_z + derail_lift)

    boiler.shape_key_add(name="Basis")
    venting = boiler.shape_key_add(name="Damage_VentingBoiler")
    marked = group_vertex_indices(boiler, "DamageVent")
    for index in marked:
        co = venting.data[index].co
        side = 1 if co.y >= 0 else -1
        co.y += side * 0.20
        co.z += 0.18 + max(0.0, co.x - 0.08) * 0.24
        co.x += side * 0.025
    for index in group_vertex_indices(boiler, "DamageVentHole"):
        co = venting.data[index].co
        co.y += (1 if co.y >= 0 else -1) * 0.085
    steam_moves = {
        "DamageSteamSmall": Vector((0.08, 0.31, 0.31)),
        "DamageSteamMedium": Vector((0.12, 0.37, 0.46)),
        "DamageSteamLarge": Vector((0.18, 0.44, 0.64)),
    }
    for group_name, movement in steam_moves.items():
        for index in group_vertex_indices(boiler, group_name):
            venting.data[index].co += movement

    cabin.shape_key_add(name="Basis")
    cracked = cabin.shape_key_add(name="Damage_CrackedCabin")
    dents = group_vertex_indices(cabin, "DamageDent")
    caving_wall = group_vertex_indices(cabin, "DamageCabWall")
    caving_roof = group_vertex_indices(cabin, "DamageCabRoof")
    for index in dents:
        co = cracked.data[index].co
        co.x -= 0.085 + max(0.0, co.z - 0.82) * 0.10
        co.z -= 0.035 + max(0.0, co.x - 0.60) * 0.13
        if co.y > 0:
            co.y -= 0.065
    for index in caving_wall:
        co = cracked.data[index].co
        u = (co.x - 0.88) / 0.30
        v = (co.z - 0.84) / 0.21
        influence = max(0.0, 1.0 - min(1.0, math.sqrt(u * u + v * v)))
        co.y -= 0.19 * influence
        co.x -= 0.045 * influence
        co.z -= 0.055 * influence
    for index in group_vertex_indices(cabin, "DamageCabVoid"):
        cracked.data[index].co.y += 0.23
    for index in caving_roof:
        co = cracked.data[index].co
        near = max(0.0, min(1.0, (co.y + 0.02) / 0.46))
        rear = max(0.0, min(1.0, (co.x - 0.45) / 0.72))
        collapse = near * (0.45 + rear * 0.55)
        co.y -= 0.08 * collapse
        co.x -= 0.045 * collapse
        co.z -= 0.18 * collapse

    for obj in (wheels, boiler, cabin):
        obj.active_shape_key_index = 0
        for key in obj.data.shape_keys.key_blocks:
            key.value = 0.0


def triangle_count(objects: tuple[bpy.types.Object, ...]) -> int:
    return sum(sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons) for obj in objects)


def world_bounds(objects: tuple[bpy.types.Object, ...]) -> tuple[Vector, Vector]:
    points = [obj.matrix_world @ vertex.co for obj in objects for vertex in obj.data.vertices]
    return Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points))), Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))


def normalize_base_center(objects: tuple[bpy.types.Object, ...]) -> None:
    minimum, maximum = world_bounds(objects)
    center_x = (minimum.x + maximum.x) * 0.5
    center_y = (minimum.y + maximum.y) * 0.5
    scale_x = MODEL_LENGTH / (maximum.x - minimum.x)
    for obj in objects:
        # Lengthen the chassis without turning round wheels, gauges and lamps into ovals.
        round_centers = {}
        round_profiles = []
        for group in obj.vertex_groups:
            if group.name.startswith("RoundX:"):
                indices = group_vertex_indices(obj, group.name)
                center = (min(obj.data.vertices[i].co.x for i in indices) + max(obj.data.vertices[i].co.x for i in indices)) * 0.5
                span = max(obj.data.vertices[i].co.x for i in indices) - min(obj.data.vertices[i].co.x for i in indices)
                round_profiles.append((indices, span))
                round_centers.update({i: center for i in indices})
        for vertex in obj.data.vertices:
            pivot = round_centers.get(vertex.index, vertex.co.x)
            vertex.co.x = (pivot - center_x) * scale_x + vertex.co.x - pivot
            vertex.co.y -= center_y
            vertex.co.z -= minimum.z
        for indices, span in round_profiles:
            actual = max(obj.data.vertices[i].co.x for i in indices) - min(obj.data.vertices[i].co.x for i in indices)
            assert abs(actual - span) < 1e-6, "round profile stretched with chassis"
        obj.data.update()


def export(objects: tuple[bpy.types.Object, ...]) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.export_scene.gltf(
        filepath=str(GLB.with_suffix("")),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_materials="EXPORT",
        export_morph=True,
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    reset_scene()
    bpy.context.preferences.filepaths.save_version = 0
    atlas, source_sha = create_atlas()
    material = create_material(atlas)
    wheels = join_component("Railcar_Wheels", build_wheels(material), material)
    boiler = join_component("Railcar_Boiler", build_boiler(material), material)
    cabin = join_component("Railcar_Cabin", build_cabin(material), material)
    objects = (wheels, boiler, cabin)
    normalize_base_center(objects)
    add_damage_shapes(*objects)

    minimum, maximum = world_bounds(objects)
    tris = triangle_count(objects)
    assert tris <= 12_000, f"triangle budget exceeded: {tris}"
    assert abs((maximum.x - minimum.x) - MODEL_LENGTH) < 0.01, f"length bounds {minimum.x:.4f}..{maximum.x:.4f}"
    assert abs((maximum.x + minimum.x) * 0.5) < 0.001
    assert abs((maximum.y + minimum.y) * 0.5) < 0.001
    assert abs(minimum.z) < 0.001
    assert len({slot.material.name for obj in objects for slot in obj.material_slots if slot.material}) == 1
    export(objects)
    print(json.dumps({
        "blend": str(BLEND),
        "glb": str(GLB),
        "sha256": hashlib.sha256(GLB.read_bytes()).hexdigest(),
        "sourcePlateSha256": source_sha,
        "surfaceSource": str(SURFACE_REFERENCE.relative_to(ROOT)),
        "surfaceSha256": hashlib.sha256(SURFACE_REFERENCE.read_bytes()).hexdigest(),
        "objects": [obj.name for obj in objects],
        "damageMorphs": [obj.data.shape_keys.key_blocks[1].name for obj in objects],
        "triangles": tris,
        "boundsBlender": {"min": [round(value, 6) for value in minimum], "max": [round(value, 6) for value in maximum]},
        "lengthGaugeRatio": round((maximum.x - minimum.x) / RAIL_GAUGE, 4),
    }, indent=2))


if __name__ == "__main__":
    main()
