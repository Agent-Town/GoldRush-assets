from __future__ import annotations

from pathlib import Path
import hashlib
import json
import math
import sys

sys.dont_write_bytecode = True

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/ark-long-table-hall-e10"
BLEND = HERE / "ark-long-table-hall-e10.blend"
GLB = HERE / "ark-long-table-hall-e10.glb"
TEMP_ATLAS = HERE / ".ark-long-table-hall-e10-atlas.png"

BASE_SHA = "101c0d97e9527b26cc5c94fdafab5b4f77aa33c0"
ARK_PLAZA_TIP = "e8128c260a3ee62ef836ec33e92b1d8459cecce1"
ATLAS_SIZE = 2048
TRIANGLE_BUDGET = 20_000

SOURCES = (
    ROOT / "assets/raw/plate-e10-long-table.png",
    ROOT / "assets/raw/plate-e10-pan-shrine.png",
    ROOT / "assets/raw/plate-e10-charter-press-hall.png",
    ROOT / "assets/raw/kit-era-10.png",
    ROOT / "assets/raw/kit-the-ark.png",
    ROOT / "assets/pilots/plaza-props-3d/build_plaza_props.py",
    ROOT / "specs/epoch-saga/e10-deepsky-bundle.md",
)

PALETTE = (
    (0.045, 0.032, 0.024, 1.0),  # deep ink
    (0.105, 0.070, 0.040, 1.0),  # tarred timber
    (0.225, 0.125, 0.060, 1.0),  # dark timber
    (0.410, 0.235, 0.105, 1.0),  # warm timber
    (0.650, 0.400, 0.165, 1.0),  # rubbed timber
    (0.865, 0.650, 0.315, 1.0),  # brass light
    (0.430, 0.250, 0.070, 1.0),  # old brass
    (0.075, 0.235, 0.230, 1.0),  # teal shadow
    (0.190, 0.565, 0.550, 1.0),  # ship teal
    (0.760, 0.650, 0.440, 1.0),  # parchment
    (0.310, 0.095, 0.055, 1.0),  # cushion red
    (0.335, 0.400, 0.155, 1.0),  # elder leaf
    (0.150, 0.205, 0.085, 1.0),  # elder leaf shadow
    (0.300, 0.315, 0.285, 1.0),  # tin
    (0.535, 0.520, 0.440, 1.0),  # worn silver
    (0.930, 0.755, 0.380, 1.0),  # ship-light gold
)

PARTS: list[bpy.types.Object] = []


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.render.engine = "BLENDER_EEVEE"


def swatch_uv(index: int) -> tuple[float, float]:
    column = index % 4
    row = index // 4
    return ((column + 0.5) / 4.0, (row + 0.5) / 4.0)


def make_atlas() -> bpy.types.Image:
    image = bpy.data.images.new("Ark Long Table Hall painted atlas", ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    axis = np.arange(ATLAS_SIZE, dtype=np.float32)
    xx, yy = np.meshgrid(axis, axis)
    pixels = np.zeros((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    cell = ATLAS_SIZE // 4
    grain = (
        np.sin(xx * 0.092 + yy * 0.021)
        + np.sin(xx * 0.017 - yy * 0.073)
        + np.sin((xx + yy) * 0.011)
    ) / 3.0
    for index, color in enumerate(PALETTE):
        row, column = divmod(index, 4)
        y0, y1 = row * cell, (row + 1) * cell
        x0, x1 = column * cell, (column + 1) * cell
        factor = 0.91 + grain[y0:y1, x0:x1, None] * 0.055
        pixels[y0:y1, x0:x1, :3] = np.clip(np.asarray(color[:3], dtype=np.float32) * factor, 0.0, 1.0)
        pixels[y0:y1, x0:x1, 3] = 1.0
    image.pixels.foreach_set(pixels.ravel())
    image.filepath_raw = str(TEMP_ATLAS)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image


def make_material(atlas: bpy.types.Image) -> bpy.types.Material:
    material = bpy.data.materials.new("Ark Long Table Hall painted wrap")
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = 0.84
    shader.inputs["Metallic"].default_value = 0.055
    texture = material.node_tree.nodes.new("ShaderNodeTexImage")
    texture.image = atlas
    texture.interpolation = "Linear"
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    return material


def assign_uv(obj: bpy.types.Object, swatch: int) -> None:
    uv = swatch_uv(swatch)
    layer = obj.data.uv_layers.get("UVMap") or obj.data.uv_layers.new(name="UVMap")
    for loop in layer.data:
        loop.uv = uv


def finish(obj: bpy.types.Object, material: bpy.types.Material, swatch: int) -> bpy.types.Object:
    if not obj.data.materials:
        obj.data.materials.append(material)
    assign_uv(obj, swatch)
    PARTS.append(obj)
    return obj


def box(name: str, at: tuple[float, float, float], size: tuple[float, float, float], material,
        swatch: int, rotation: float = 0.0, bevel: float = 0.0) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=at, rotation=(0.0, 0.0, rotation))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # Keep production topology stable across Blender builds; the painted atlas,
    # layered rails, and hardware carry the worn-edge read without modifiers.
    return finish(obj, material, swatch)


def cylinder(name: str, at: tuple[float, float, float], radius: float, depth: float, material,
             swatch: int, vertices: int = 12, rotation=(0.0, 0.0, 0.0)) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=at, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    return finish(obj, material, swatch)


def torus(name: str, at: tuple[float, float, float], major: float, minor: float, material,
          swatch: int, major_segments: int = 16, minor_segments: int = 4,
          rotation=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0)) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major, minor_radius=minor,
        major_segments=major_segments, minor_segments=minor_segments,
        location=at, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, material, swatch)


def ico(name: str, at: tuple[float, float, float], radius: float, material, swatch: int,
        scale=(1.0, 1.0, 1.0)) -> bpy.types.Object:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=radius, location=at)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, material, swatch)


def cone(name: str, at: tuple[float, float, float], r1: float, r2: float, depth: float,
         material, swatch: int, vertices: int = 10, rotation=(0.0, 0.0, 0.0)) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices, radius1=r1, radius2=r2, depth=depth, location=at, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    return finish(obj, material, swatch)


def beam(name: str, start: tuple[float, float, float], end: tuple[float, float, float],
         radius: float, material, swatch: int, vertices: int = 7) -> bpy.types.Object:
    start_v = Vector(start)
    end_v = Vector(end)
    direction = end_v - start_v
    obj = cylinder(name, tuple((start_v + end_v) * 0.5), radius, direction.length,
                   material, swatch, vertices)
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return obj


def mesh_object(name: str, vertices, faces, material, swatch: int) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return finish(obj, material, swatch)


def add_hall_shell(material) -> None:
    box("Hall:Deck", (0.0, 0.0, -0.10), (18.0, 22.0, 0.20), material, 2, bevel=0.035)
    # Three-sided room: the south wall stays open to the plaza portal and gameplay camera.
    box("Hall:BackWall", (0.0, 10.55, 3.75), (18.0, 0.32, 7.50), material, 1, bevel=0.05)
    for side in (-1.0, 1.0):
        box(f"Hall:SideWall:{side}", (side * 8.82, 1.0, 3.45), (0.32, 19.2, 6.90), material, 1, bevel=0.05)

    # Floor boards, repaired seams, and a central brass memory line.
    for index in range(-8, 9):
        x = index * 1.02
        box(f"Deck:BoardSeam:{index}", (x, 0.0, 0.018), (0.025, 21.2, 0.025), material, 6)
    for y in (-9.0, -5.3, -1.6, 2.1, 5.8, 9.1):
        box(f"Deck:CrossBrace:{y}", (0.0, y, 0.022), (17.4, 0.055, 0.035), material, 6)
    box("Deck:CarryLine", (0.0, 0.15, 0.022), (0.12, 19.6, 0.040), material, 15)
    for index, (x, y, sx, sy) in enumerate(((-6.7, -6.9, 1.9, 1.1), (6.3, -1.5, 2.2, 1.0),
                                             (-5.8, 7.6, 1.6, 0.8), (5.9, 7.0, 1.8, 0.9)), 1):
        box(f"Deck:RepairPatch:{index}", (x, y, 0.025), (sx, sy, 0.040), material, 3, bevel=0.025)

    # Ship ribs carry the warm frontier room inside a very old machine.
    for rib_index, y in enumerate((-8.9, -5.0, -1.1, 2.8, 6.7, 9.9), 1):
        points = []
        for step in range(13):
            angle = math.pi - step / 12.0 * math.pi
            points.append((math.cos(angle) * 8.45, y, 5.55 + math.sin(angle) * 2.45))
        for part, (start, end) in enumerate(zip(points, points[1:]), 1):
            beam(f"Hall:Rib:{rib_index}:{part}", start, end, 0.14, material, 6, 8)
        for side in (-1.0, 1.0):
            beam(f"Hall:RibPost:{rib_index}:{side}", (side * 8.45, y, 0.12),
                 (side * 8.45, y, 5.56), 0.14, material, 6, 8)


def add_portholes(material) -> None:
    for side in (-1.0, 1.0):
        for index, y in enumerate((-5.9, 1.1, 7.2), 1):
            x = side * 8.61
            torus(f"Porthole:{side}:{index}:rim", (x, y, 3.55), 1.12, 0.14, material, 6,
                  20, 5, (0.0, math.pi / 2.0, 0.0), (1.0, 1.15, 1.0))
            cylinder(f"Porthole:{side}:{index}:glass", (x - side * 0.08, y, 3.55), 0.92, 0.08,
                     material, 7, 20, (0.0, math.pi / 2.0, 0.0))
            for spoke in range(4):
                angle = spoke / 4.0 * math.pi
                start = (x - side * 0.14, y - math.cos(angle) * 0.82, 3.55 - math.sin(angle) * 0.82)
                end = (x - side * 0.14, y + math.cos(angle) * 0.82, 3.55 + math.sin(angle) * 0.82)
                beam(f"Porthole:{side}:{index}:spoke:{spoke}", start, end, 0.025, material, 8, 5)


def add_portrait_wall(material) -> list[tuple[float, float, float]]:
    box("PortraitWall:Field", (0.0, 10.32, 4.25), (15.4, 0.22, 5.65), material, 2, bevel=0.06)
    anchors = []
    for row, z in enumerate((5.65, 2.85)):
        for column, x in enumerate((-5.6, -2.8, 0.0, 2.8, 5.6)):
            index = row * 5 + column + 1
            cylinder(f"Portrait:{index:02d}:blank", (x, 10.16, z), 0.88, 0.055,
                     material, 9, 20, (math.pi / 2.0, 0.0, 0.0))
            torus(f"Portrait:{index:02d}:frame", (x, 10.10, z), 0.98, 0.115,
                  material, 6, 20, 5, (math.pi / 2.0, 0.0, 0.0), (1.0, 1.0, 1.18))
            cylinder(f"Portrait:{index:02d}:crest", (x, 10.02, z - 1.05), 0.10, 0.08,
                     material, 15, 8, (math.pi / 2.0, 0.0, 0.0))
            anchors.append((x, 10.02, z))
    box("PortraitWall:LowerRail", (0.0, 10.02, 1.22), (15.8, 0.24, 0.28), material, 6, bevel=0.04)
    return anchors


def add_chair(material, index: int, x: float, y: float, facing: float) -> None:
    box(f"Chair:{index}:seat", (x, y, 0.78), (1.05, 1.0, 0.17), material, 3, facing, 0.04)
    direction = 1.0 if x < 0.0 else -1.0
    back_x = x - direction * 0.43
    box(f"Chair:{index}:back", (back_x, y, 1.35), (0.16, 1.0, 1.35), material, 2, facing, 0.04)
    for sx in (-0.36, 0.36):
        for sy in (-0.34, 0.34):
            box(f"Chair:{index}:leg:{sx}:{sy}", (x + sx, y + sy, 0.37),
                (0.10, 0.10, 0.72), material, 2, facing)


def add_table_life(material) -> None:
    box("LongTable:Top", (0.0, -0.75, 1.25), (4.15, 12.9, 0.30), material, 4, bevel=0.09)
    box("LongTable:Underframe", (0.0, -0.75, 0.92), (3.25, 11.9, 0.28), material, 2, bevel=0.04)
    for y in (-5.8, -2.45, 0.95, 4.2):
        for x in (-1.55, 1.55):
            box(f"LongTable:Leg:{x}:{y}", (x, y, 0.55), (0.27, 0.34, 1.05), material, 2, bevel=0.035)
        box(f"LongTable:Foot:{y}", (0.0, y, 0.16), (3.85, 0.28, 0.22), material, 2, bevel=0.04)

    chair_index = 0
    for x, facing in ((-3.0, -math.pi / 2.0), (3.0, math.pi / 2.0)):
        for y in (-5.5, -3.35, -1.2, 0.95, 3.1, 5.25):
            chair_index += 1
            add_chair(material, chair_index, x, y - 0.75, facing)

    # A table that looks used: lanterns, bowls, plates, mugs, bread, and a folded map.
    for lamp_index, y in enumerate((-4.4, -0.75, 2.9), 1):
        cylinder(f"Table:Lamp:{lamp_index}:base", (0.0, y, 1.54), 0.26, 0.16, material, 6, 12)
        cylinder(f"Table:Lamp:{lamp_index}:glow", (0.0, y, 1.88), 0.20, 0.55, material, 15, 10)
        torus(f"Table:Lamp:{lamp_index}:cage", (0.0, y, 1.88), 0.23, 0.035, material, 6, 12, 4)
        cylinder(f"Table:Lamp:{lamp_index}:cap", (0.0, y, 2.20), 0.14, 0.12, material, 6, 10)
    for place_index, (x, y) in enumerate(((-1.25, -5.5), (1.25, -5.1), (-1.2, -3.1), (1.2, -2.8),
                                          (-1.25, -0.3), (1.25, 0.1), (-1.15, 2.0), (1.2, 2.3),
                                          (-1.2, 4.5), (1.2, 4.2)), 1):
        cylinder(f"Table:Plate:{place_index}", (x, y, 1.45), 0.42, 0.07, material, 14, 16)
        torus(f"Table:PlateRim:{place_index}", (x, y, 1.50), 0.38, 0.035, material, 6, 14, 3)
        mug_x = x + (0.52 if x < 0 else -0.52)
        cylinder(f"Table:Mug:{place_index}", (mug_x, y + 0.15, 1.66), 0.15, 0.34, material, 13, 10)
    for bowl_index, (x, y, radius) in enumerate(((-0.7, -2.0, 0.55), (0.8, 1.2, 0.62), (-0.7, 4.1, 0.50)), 1):
        cylinder(f"Table:SharedBowl:{bowl_index}", (x, y, 1.57), radius, 0.23, material, 3, 14)
        for bite in range(5):
            angle = bite / 5.0 * math.tau
            ico(f"Table:Food:{bowl_index}:{bite}",
                (x + math.cos(angle) * radius * 0.45, y + math.sin(angle) * radius * 0.45, 1.79),
                0.13, material, 4 if bite % 2 else 10, (1.0, 0.85, 0.7))
    box("Table:FoldedChart", (1.05, -4.0, 1.50), (1.15, 1.05, 0.045), material, 9, 0.12)
    beam("Table:ChartLine", (0.65, -4.25, 1.535), (1.45, -3.75, 1.535), 0.014, material, 8, 5)


def add_pan_bowl(material, center: tuple[float, float, float]) -> None:
    cx, cy, cz = center
    segments = 20
    rings = ((0.0, -0.18), (0.24, -0.13), (0.46, -0.04), (0.62, 0.035))
    vertices = [(cx, cy, cz + rings[0][1])]
    for radius, height in rings[1:]:
        vertices.extend((cx + math.cos(i / segments * math.tau) * radius,
                         cy + math.sin(i / segments * math.tau) * radius,
                         cz + height) for i in range(segments))
    faces = [(0, 1 + i, 1 + (i + 1) % segments) for i in range(segments)]
    for ring_index in range(1, len(rings) - 1):
        inner = 1 + (ring_index - 1) * segments
        outer = 1 + ring_index * segments
        for i in range(segments):
            faces.append((inner + i, outer + i, outer + (i + 1) % segments, inner + (i + 1) % segments))
    mesh_object("PanShrine:OriginalE1Pan:Bowl", vertices, faces, material, 6)
    torus("PanShrine:OriginalE1Pan:Rim", (cx, cy, cz + 0.04), 0.62, 0.055, material, 6, 20, 5)
    cylinder("PanShrine:OriginalE1Pan:HandleCollar", (cx + 0.54, cy, cz + 0.055),
             0.14, 0.24, material, 6, 10, (0.0, math.pi / 2.0, 0.0))
    beam("PanShrine:OriginalE1Pan:Handle", (cx + 0.52, cy, cz + 0.055),
         (cx + 1.55, cy, cz + 0.055), 0.095, material, 6, 9)
    box("PanShrine:OriginalE1Pan:HandleGrip", (cx + 1.72, cy, cz + 0.055),
        (0.46, 0.26, 0.21), material, 3, bevel=0.04)
    for riffle, y in enumerate((-0.10, 0.03), 1):
        beam(f"PanShrine:OriginalE1Pan:Riffle:{riffle}", (cx - 0.23, cy + y, cz - 0.10),
             (cx + 0.23, cy + y, cz - 0.10), 0.018, material, 15, 5)


def add_pan_shrine(material) -> tuple[float, float, float]:
    cx, cy = -6.15, 4.65
    box("PanShrine:Plinth", (cx, cy, 0.34), (3.65, 3.0, 0.68), material, 2, bevel=0.07)
    box("PanShrine:Cushion", (cx, cy, 0.80), (2.75, 2.15, 0.25), material, 10, bevel=0.10)
    pan_center = (cx - 0.25, cy, 1.18)
    add_pan_bowl(material, pan_center)
    for x_index, x in enumerate((cx - 1.62, cx + 1.62), 1):
        for y_index, y in enumerate((cy - 1.30, cy + 1.30), 1):
            beam(f"PanShrine:CasePost:{x_index}:{y_index}", (x, y, 0.65), (x, y, 3.35), 0.065, material, 6, 8)
    for y_index, y in enumerate((cy - 1.30, cy + 1.30), 1):
        beam(f"PanShrine:CanopyRail:{y_index}:left", (cx - 1.62, y, 3.35), (cx + 1.62, y, 3.35),
             0.085, material, 6, 8)
    for x_index, x in enumerate((cx - 1.62, cx + 1.62), 1):
        beam(f"PanShrine:CanopyRail:{x_index}:side", (x, cy - 1.30, 3.35), (x, cy + 1.30, 3.35),
             0.085, material, 6, 8)
    box("PanShrine:Canopy", (cx, cy, 3.48), (3.75, 3.10, 0.25), material, 2, bevel=0.08)
    box("PanShrine:WarmBacking", (cx, cy + 1.39, 2.08), (3.2, 0.06, 2.25), material, 9, bevel=0.03)
    torus("PanShrine:CaseShipLight", (cx, cy + 1.34, 2.10), 0.95, 0.045, material, 15,
          20, 4, (math.pi / 2.0, 0.0, 0.0), (1.35, 1.0, 1.0))
    return (cx, cy, 1.2)


def add_elder_tree(material) -> tuple[float, float, float]:
    cx, cy = 6.05, 4.75
    cylinder("ElderTree:Tin", (cx, cy, 0.72), 1.05, 1.35, material, 13, 16)
    torus("ElderTree:TinRim", (cx, cy, 1.38), 1.04, 0.09, material, 14, 16, 4)
    for z in (0.25, 0.62, 1.02):
        torus(f"ElderTree:TinBand:{z}", (cx, cy, z), 1.02, 0.055, material, 14, 16, 3)
    cylinder("ElderTree:Soil", (cx, cy, 1.40), 0.90, 0.08, material, 1, 16)
    beam("ElderTree:Trunk", (cx, cy, 1.38), (cx + 0.08, cy, 4.25), 0.22, material, 2, 9)
    branches = (
        ((cx + 0.02, cy, 2.60), (cx - 1.05, cy + 0.15, 3.65)),
        ((cx + 0.05, cy, 2.90), (cx + 1.15, cy - 0.20, 3.85)),
        ((cx + 0.07, cy, 3.25), (cx - 0.55, cy - 0.85, 4.45)),
        ((cx + 0.08, cy, 3.45), (cx + 0.70, cy + 0.75, 4.65)),
    )
    for index, (start, end) in enumerate(branches, 1):
        beam(f"ElderTree:Branch:{index}", start, end, 0.12, material, 2, 7)
    leaves = (
        (-1.05, 0.15, 3.95, 0.85), (1.10, -0.20, 4.15, 0.95), (-0.55, -0.82, 4.65, 0.78),
        (0.72, 0.70, 4.85, 0.82), (0.0, 0.0, 4.95, 1.05), (-0.85, 0.70, 4.55, 0.70),
        (0.95, 0.55, 4.45, 0.72),
    )
    for index, (dx, dy, z, radius) in enumerate(leaves, 1):
        ico(f"ElderTree:LeafCluster:{index}", (cx + dx, cy + dy, z), radius,
            material, 11 if index % 2 else 12, (1.0, 0.78, 0.84))
    box("ElderTree:TinPatch", (cx + 0.88, cy, 0.72), (0.05, 0.72, 0.44), material, 6, bevel=0.015)
    return (cx, cy, 2.7)


def add_service_grit(material) -> None:
    for side in (-1.0, 1.0):
        x = side * 8.25
        for z, swatch in ((0.55, 6), (1.02, 8)):
            beam(f"ServiceRun:{side}:{z}", (x, -8.7, z), (x, 8.9, z), 0.095, material, swatch, 8)
        for y in (-7.5, -2.3, 3.0, 8.2):
            torus(f"ServiceRun:Collar:{side}:{y}", (x, y, 0.78), 0.20, 0.055,
                  material, 6, 12, 4, (math.pi / 2.0, 0.0, 0.0))
    for index, (x, y) in enumerate(((-7.6, -8.0), (7.5, -7.4), (-7.5, 0.1), (7.45, 0.8)), 1):
        box(f"ServiceConsole:{index}:body", (x, y, 1.00), (1.1, 0.65, 1.65), material, 1, bevel=0.06)
        box(f"ServiceConsole:{index}:face", (x - (0.57 if x > 0 else -0.57), y, 1.12),
            (0.04, 0.48, 0.82), material, 7, bevel=0.02)
        for lamp, z in enumerate((0.92, 1.20, 1.48), 1):
            cylinder(f"ServiceConsole:{index}:lamp:{lamp}",
                     (x - (0.60 if x > 0 else -0.60), y, z), 0.06, 0.05,
                     material, 8 if lamp == 2 else 15, 8, (0.0, math.pi / 2.0, 0.0))


def add_working_hall_life(material) -> None:
    # Ship lanterns and their exposed feed cable keep this a working mess hall.
    beam("HallLife:CeilingFeed", (0.0, -8.4, 6.05), (0.0, 8.2, 6.05), 0.045, material, 1, 6)
    for index, y in enumerate((-6.2, -2.6, 1.0, 4.6, 8.0), 1):
        beam(f"HallLife:HangingLamp:{index}:drop", (0.0, y, 6.05), (0.0, y, 4.65),
             0.035, material, 1, 6)
        cone(f"HallLife:HangingLamp:{index}:shade", (0.0, y, 4.57), 0.38, 0.18, 0.28,
             material, 6, 12)
        cylinder(f"HallLife:HangingLamp:{index}:globe", (0.0, y, 4.30), 0.17, 0.32,
                 material, 15, 10)
        torus(f"HallLife:HangingLamp:{index}:cage", (0.0, y, 4.30), 0.21, 0.035,
              material, 6, 12, 4)

    # Maintenance storage is deliberately irregular and parcel-local.
    crates = ((-7.55, -6.4, 1.05, 0.78, 0.70), (-6.95, -6.0, 0.72, 0.62, 0.56),
              (7.40, -5.6, 0.92, 0.72, 0.64), (7.05, 6.9, 0.78, 0.58, 0.52))
    for index, (x, y, sx, sy, sz) in enumerate(crates, 1):
        box(f"HallLife:Crate:{index}", (x, y, sz * 0.5), (sx, sy, sz), material,
            3 if index % 2 else 2, rotation=(index - 2.5) * 0.08)
        box(f"HallLife:CrateBand:{index}", (x, y, sz * 0.55), (sx + 0.03, 0.08, sz * 0.72),
            material, 6, rotation=(index - 2.5) * 0.08)

    # A tool board and coiled spare cable echo the frontier workshop ancestry.
    box("HallLife:ToolBoard", (-8.56, -1.8, 3.05), (0.10, 3.2, 2.35), material, 3)
    for index, (y, z) in enumerate(((-2.7, 3.55), (-2.0, 2.85), (-1.2, 3.30), (-0.6, 2.60)), 1):
        beam(f"HallLife:Tool:{index}", (-8.42, y, z - 0.38), (-8.42, y, z + 0.38),
             0.045, material, 14 if index % 2 else 6, 6)
        box(f"HallLife:ToolHead:{index}", (-8.40, y, z + 0.42), (0.14, 0.35, 0.16),
            material, 6)
    torus("HallLife:CableCoil:1", (8.42, -0.8, 2.9), 0.72, 0.075, material, 1,
          18, 5, (0.0, math.pi / 2.0, 0.0))
    torus("HallLife:CableCoil:2", (8.35, -0.8, 2.9), 0.52, 0.065, material, 8,
          16, 4, (0.0, math.pi / 2.0, 0.0))


def join_parts(material) -> bpy.types.Object:
    bpy.ops.object.select_all(action="DESELECT")
    for part in PARTS:
        part.select_set(True)
    bpy.context.view_layer.objects.active = PARTS[0]
    bpy.ops.object.join()
    hall = bpy.context.object
    hall.name = "ArkLongTableHallE10"
    hall.data.name = "ArkLongTableHallE10Mesh"
    hall.data.materials.clear()
    hall.data.materials.append(material)
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    return hall


def add_anchor(name: str, at: tuple[float, float, float]) -> bpy.types.Object:
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.35
    empty.location = at
    bpy.context.collection.objects.link(empty)
    return empty


def triangle_count(obj: bpy.types.Object) -> int:
    return sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons)


def export(hall: bpy.types.Object, anchors: list[bpy.types.Object]) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    hall.select_set(True)
    for anchor in anchors:
        anchor.select_set(True)
    bpy.context.view_layer.objects.active = hall
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.export_scene.gltf(
        filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False,
        export_materials="EXPORT",
    )


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    reset_scene()
    atlas = make_atlas()
    material = make_material(atlas)
    add_hall_shell(material)
    add_portholes(material)
    portrait_positions = add_portrait_wall(material)
    add_table_life(material)
    pan_position = add_pan_shrine(material)
    tree_position = add_elder_tree(material)
    add_service_grit(material)
    add_working_hall_life(material)
    hall = join_parts(material)
    triangles = triangle_count(hall)
    if triangles > TRIANGLE_BUDGET:
        raise RuntimeError(f"Long Table Hall exceeds {TRIANGLE_BUDGET} triangles: {triangles}")
    anchors = [
        *[add_anchor(f"portrait_anchor_{index:02d}", at) for index, at in enumerate(portrait_positions, 1)],
        add_anchor("pan_shrine_anchor", pan_position),
        add_anchor("elder_tree_anchor", tree_position),
    ]
    export(hall, anchors)
    TEMP_ATLAS.unlink(missing_ok=True)
    contract = {
        "wave": "THE LONG TABLE HALL (E10)",
        "baseSha": BASE_SHA,
        "unmergedDependency": {"wave": "Ark Plaza E10 plate", "tip": ARK_PLAZA_TIP},
        "production": {
            "blend": str(BLEND.relative_to(ROOT)), "glb": str(GLB.relative_to(ROOT)),
            "triangles": triangles, "triangleBudget": TRIANGLE_BUDGET,
            "mesh": hall.name, "materials": 1, "atlas": [ATLAS_SIZE, ATLAS_SIZE],
            "lights": 0, "cameras": 0, "origin": "base-center; open south portal faces Ark plaza",
        },
        "identity": {
            "longTable": "twelve chairs, place settings, shared food, lamps, folded chart",
            "portraitWall": "ten blank production fields; profile-history compositor owns likenesses",
            "panShrine": "handled concave E1 pan in a small warm case",
            "elderTree": "living tree survivor in patched ribbed tin",
            "grit": ["deck patches", "exposed service runs", "rubbed timber", "ship ribs"],
        },
        "anchors": [anchor.name for anchor in anchors],
        "sources": {str(path.relative_to(ROOT)): sha256(path) for path in SOURCES},
    }
    (ARTIFACTS / "ark-long-table-hall-build-contract.json").write_text(json.dumps(contract, indent=2) + "\n")
    print(json.dumps({"triangles": triangles, "sha256": sha256(GLB), "anchors": len(anchors),
                      "baseSha": BASE_SHA}, indent=2))


if __name__ == "__main__":
    main()
