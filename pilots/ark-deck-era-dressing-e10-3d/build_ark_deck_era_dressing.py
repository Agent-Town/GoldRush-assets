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
ARTIFACTS = ROOT / "artifacts/ark-deck-era-dressing-e10"
BLEND = HERE / "ark-deck-era-dressing-e10.blend"
GLB = HERE / "ark-deck-era-dressing-e10.glb"
ATLAS_FILE = HERE / "ark-deck-era-dressing-e10-atlas.png"
BASE_SHA = "d46554ffde058afca2eb7966e48ac5629300ff98"
ATLAS_SIZE = 1024
TRIANGLE_BUDGET = 8_000
DECK_RADIUS = 23.0

ERA_SOURCES = tuple(ROOT / f"assets/raw/kit-era-{era}.png" for era in range(1, 11))
ARK_PLATE = ROOT / "assets/pilots/ark-plaza-e10-3d/ark-plaza-e10.glb"
E10_BUNDLE = ROOT / "specs/epoch-saga/e10-deepsky-bundle.md"

# The first ten swatches are the accepted Ark deck palette. The remaining
# swatches are shared working-ship materials. Every stripe receives engraved
# value variation sampled from the shipped era art rather than a flat color.
PALETTE = (
    (0.43, 0.25, 0.10),  # E1 earth / timber
    (0.34, 0.17, 0.06),  # E2 steam bronze
    (0.09, 0.40, 0.41),  # E3 voltage teal
    (0.46, 0.16, 0.055), # E4 motor red
    (0.15, 0.31, 0.35),  # E5 deepwater blue
    (0.31, 0.46, 0.31),  # E6 atomic mint
    (0.24, 0.18, 0.34),  # E7 signal violet
    (0.54, 0.56, 0.55),  # E8 orbital silver
    (0.314, 0.404, 0.298), # E9 exact E1-green family
    (0.12, 0.09, 0.075), # E10 deep ink
    (0.055, 0.15, 0.16), # hull shadow
    (0.34, 0.18, 0.075), # worn timber
    (0.72, 0.44, 0.12),  # brass
    (0.08, 0.65, 0.65),  # ship-light teal
    (0.92, 0.60, 0.18),  # warm signal gold
    (0.68, 0.56, 0.36),  # charter paper / rope
)

ERA_READS = (
    "E1 sluice cradle and bucket",
    "E2 cold boiler and gear",
    "E3 insulator fork and wire drop",
    "E4 tire rack, fuel drum, and road marker",
    "E5 tide board, bollard, and rope coil",
    "E6 friendly appliance pen",
    "E7 relay mast and tape reels",
    "E8 helmet and survey dish",
    "E9 canal gate and living green bed",
    "E10 ten-era ribbon and charter seal",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0


def source_array(path: Path) -> np.ndarray:
    image = bpy.data.images.load(str(path), check_existing=False)
    width, height = image.size
    values = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(values)
    array = values.reshape(height, width, 4)
    bpy.data.images.remove(image)
    return array


def make_atlas() -> bpy.types.Image:
    pixels = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    sources = [source_array(path) for path in ERA_SOURCES]
    stripe_width = ATLAS_SIZE // len(PALETTE)
    for index, color in enumerate(PALETTE):
        source = sources[min(index, 9)]
        luminance = np.mean(source[:, :, :3], axis=2)
        x0 = index * stripe_width
        x1 = ATLAS_SIZE if index == len(PALETTE) - 1 else (index + 1) * stripe_width
        sx = np.linspace(0, luminance.shape[1] - 1, x1 - x0).astype(np.int32)
        sy = np.linspace(0, luminance.shape[0] - 1, ATLAS_SIZE).astype(np.int32)
        grain = luminance[np.ix_(sy, sx)]
        engraved = 0.018 * np.sin(np.linspace(0.0, math.tau * 31.0, ATLAS_SIZE, dtype=np.float32))[:, None]
        variation = np.clip((grain - 0.43) * 0.12 + engraved, -0.050, 0.060)
        pixels[:, x0:x1, :3] = np.clip(np.array(color)[None, None, :] + variation[:, :, None], 0.02, 0.96)
    image = bpy.data.images.new("ArkDeckEraDressingAtlas", ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.pixels.foreach_set(pixels.ravel())
    image.filepath_raw = str(ATLAS_FILE)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image


def make_material(atlas: bpy.types.Image) -> bpy.types.Material:
    material = bpy.data.materials.new("ArkDeckEraDressingPaintedMaterial")
    material.use_nodes = True
    material.diffuse_color = (0.28, 0.18, 0.09, 1.0)
    material.surface_render_method = "DITHERED"
    material.use_transparency_overlap = False
    material.use_backface_culling = False
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = 0.86
    shader.inputs["Metallic"].default_value = 0.06
    texture = material.node_tree.nodes.new("ShaderNodeTexImage")
    texture.image = atlas
    texture.interpolation = "Linear"
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    return material


PARTS: list[bpy.types.Object] = []


def swatch_uv(index: int) -> tuple[float, float]:
    return ((index + 0.5) / len(PALETTE), 0.50)


def paint(obj: bpy.types.Object, material: bpy.types.Material, swatch: int) -> bpy.types.Object:
    if not obj.data.materials:
        obj.data.materials.append(material)
    layer = obj.data.uv_layers.get("UVMap") or obj.data.uv_layers.new(name="UVMap")
    uv = swatch_uv(swatch)
    for loop in layer.data:
        loop.uv = uv
    PARTS.append(obj)
    return obj


def box(name: str, location, size, material, swatch: int, rotation: float = 0.0, bevel: float = 0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=(0.0, 0.0, rotation))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        modifier = obj.modifiers.new("Painted edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    return paint(obj, material, swatch)


def cylinder(name: str, location, radius: float, depth: float, material, swatch: int,
             vertices: int = 10, rotation=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    return paint(obj, material, swatch)


def sphere(name: str, location, scale, material, swatch: int, segments: int = 10, rings: int = 5):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return paint(obj, material, swatch)


def torus(name: str, location, major: float, minor: float, material, swatch: int,
          major_segments: int = 12, minor_segments: int = 4, rotation=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major, minor_radius=minor, major_segments=major_segments,
        minor_segments=minor_segments, location=location, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    return paint(obj, material, swatch)


def cone(name: str, location, radius1: float, radius2: float, depth: float, material, swatch: int,
         vertices: int = 10, rotation=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices, radius1=radius1, radius2=radius2, depth=depth,
        location=location, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    return paint(obj, material, swatch)


def beam(name: str, start, end, radius: float, material, swatch: int, vertices: int = 7):
    start_v, end_v = Vector(start), Vector(end)
    direction = end_v - start_v
    obj = cylinder(name, tuple((start_v + end_v) * 0.5), radius, direction.length,
                   material, swatch, vertices)
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return obj


def station_center(index: int) -> tuple[float, float, float]:
    if index == 0:
        # E1 shifts east of the north portal so the Long Table walk stays open.
        x, y = 3.0, 18.55
        return math.atan2(y, x), math.hypot(x, y), 0.0
    if index == 5:
        # E6 mirrors E1 beside the world-window bridge approach.
        x, y = -3.0, -18.55
        return math.atan2(y, x), math.hypot(x, y), 0.0
    angle = math.radians(90.0) - index * math.tau / 10.0
    return angle, 18.95, 0.0


def point(angle: float, radius: float, tangent: float, radial: float, z: float) -> tuple[float, float, float]:
    return (
        math.cos(angle) * (radius + radial) - math.sin(angle) * tangent,
        math.sin(angle) * (radius + radial) + math.cos(angle) * tangent,
        z,
    )


def local_box(name: str, angle: float, radius: float, tangent: float, radial: float, z: float,
              size, material, swatch: int, bevel=0.0):
    return box(name, point(angle, radius, tangent, radial, z), size, material, swatch,
               angle + math.pi / 2.0, bevel)


def local_beam(name: str, angle: float, radius: float, start, end, thickness: float,
               material, swatch: int, vertices=7):
    return beam(name, point(angle, radius, *start), point(angle, radius, *end),
                thickness, material, swatch, vertices)


def local_cylinder(name: str, angle: float, radius: float, tangent: float, radial: float, z: float,
                   part_radius: float, depth: float, material, swatch: int, vertices=10,
                   orientation="vertical"):
    rotation = (0.0, 0.0, 0.0)
    if orientation == "radial":
        rotation = (0.0, math.pi / 2.0, angle)
    elif orientation == "tangent":
        rotation = (math.pi / 2.0, 0.0, angle)
    return cylinder(name, point(angle, radius, tangent, radial, z), part_radius, depth,
                    material, swatch, vertices, rotation)


def local_torus(name: str, angle: float, radius: float, tangent: float, radial: float, z: float,
                major: float, minor: float, material, swatch: int, vertical=False):
    rotation = (0.0, math.pi / 2.0, angle) if vertical else (0.0, 0.0, 0.0)
    return torus(name, point(angle, radius, tangent, radial, z), major, minor,
                 material, swatch, 12, 4, rotation)


def add_station_base(index: int, angle: float, radius: float, material) -> None:
    prefix = f"EraStation:{index + 1:02d}"
    local_box(f"{prefix}:HullPlinth", angle, radius, 0.0, 0.0, 0.09,
              (2.45, 0.82, 0.18), material, 10, 0.035)
    local_box(f"{prefix}:EraInlay", angle, radius, 0.0, -0.02, 0.195,
              (2.04, 0.55, 0.035), material, index, 0.015)
    for tangent in (-0.92, 0.92):
        local_cylinder(f"{prefix}:Rivet:{tangent}", angle, radius, tangent, -0.23, 0.225,
                       0.045, 0.045, material, 12, 7)


def add_e1(angle: float, radius: float, material) -> None:
    p = "EraStation:01:E1Sluice"
    for tangent in (-0.34, 0.34):
        local_box(f"{p}:rail:{tangent}", angle, radius, tangent, -0.03, 0.48,
                  (0.12, 0.78, 0.16), material, 11, 0.02)
    for radial in (-0.26, 0.0, 0.26):
        local_box(f"{p}:riffle:{radial}", angle, radius, 0.0, radial - 0.03, 0.51,
                  (0.80, 0.09, 0.12), material, 12)
    local_cylinder(f"{p}:bucket", angle, radius, 0.79, 0.04, 0.46,
                   0.24, 0.42, material, 0, 10)
    local_torus(f"{p}:bucket-handle", angle, radius, 0.79, 0.04, 0.72,
                0.24, 0.025, material, 12, True)


def add_e2(angle: float, radius: float, material) -> None:
    p = "EraStation:02:E2ColdBoiler"
    local_beam(f"{p}:boiler", angle, radius, (-0.56, 0.0, 0.63), (0.48, 0.0, 0.63),
               0.29, material, 1, 12)
    for tangent in (-0.48, 0.40):
        local_torus(f"{p}:band:{tangent}", angle, radius, tangent, 0.0, 0.63,
                    0.30, 0.045, material, 12, True)
    local_cylinder(f"{p}:cold-stack", angle, radius, 0.30, 0.0, 1.05,
                   0.16, 0.66, material, 10, 10)
    local_torus(f"{p}:gear", angle, radius, -0.73, -0.03, 0.66,
                0.28, 0.055, material, 12, True)
    for spoke in range(4):
        a = spoke * math.pi / 4.0
        start = (-0.73 + math.cos(a) * -0.23, -0.03, 0.66 + math.sin(a) * -0.23)
        end = (-0.73 + math.cos(a) * 0.23, -0.03, 0.66 + math.sin(a) * 0.23)
        local_beam(f"{p}:gear-spoke:{spoke}", angle, radius, start, end, 0.025, material, 12, 5)


def add_e3(angle: float, radius: float, material) -> None:
    p = "EraStation:03:E3InsulatorFork"
    local_beam(f"{p}:mast", angle, radius, (0.0, 0.0, 0.24), (0.0, 0.0, 1.48),
               0.075, material, 10)
    local_beam(f"{p}:crossarm", angle, radius, (-0.82, 0.0, 1.22), (0.82, 0.0, 1.22),
               0.075, material, 12)
    for tangent in (-0.58, 0.0, 0.58):
        local_cylinder(f"{p}:insulator:{tangent}", angle, radius, tangent, 0.0, 1.39,
                       0.11, 0.28, material, 2, 9)
        for z in (1.30, 1.42, 1.54):
            local_cylinder(f"{p}:disc:{tangent}:{z}", angle, radius, tangent, 0.0, z,
                           0.15, 0.04, material, 13, 9)
    local_beam(f"{p}:wire-left", angle, radius, (-0.58, -0.02, 1.56), (0.0, 0.08, 1.48),
               0.025, material, 14, 5)
    local_beam(f"{p}:wire-right", angle, radius, (0.0, 0.08, 1.48), (0.58, -0.02, 1.56),
               0.025, material, 14, 5)


def add_e4(angle: float, radius: float, material) -> None:
    p = "EraStation:04:E4MotorStop"
    for tangent in (-0.52, 0.12):
        local_torus(f"{p}:tire:{tangent}", angle, radius, tangent, -0.02, 0.56,
                    0.33, 0.075, material, 9, True)
    local_cylinder(f"{p}:fuel-drum", angle, radius, 0.67, 0.02, 0.52,
                   0.27, 0.62, material, 3, 12)
    for z in (0.30, 0.72):
        local_torus(f"{p}:drum-band:{z}", angle, radius, 0.67, 0.02, z,
                    0.275, 0.03, material, 12)
    local_beam(f"{p}:marker-post", angle, radius, (0.96, 0.02, 0.22), (0.96, 0.02, 1.35),
               0.055, material, 12)
    local_box(f"{p}:marker", angle, radius, 0.96, 0.02, 1.33,
              (0.48, 0.14, 0.48), material, 14, 0.03)


def add_e5(angle: float, radius: float, material) -> None:
    p = "EraStation:05:E5TideStop"
    local_cylinder(f"{p}:bollard", angle, radius, -0.74, 0.02, 0.58,
                   0.22, 0.72, material, 10, 10)
    local_cylinder(f"{p}:bollard-cap", angle, radius, -0.74, 0.02, 0.97,
                   0.30, 0.10, material, 12, 10)
    local_torus(f"{p}:rope-coil-outer", angle, radius, -0.20, -0.02, 0.30,
                0.38, 0.07, material, 15)
    local_torus(f"{p}:rope-coil-inner", angle, radius, -0.20, -0.02, 0.31,
                0.22, 0.055, material, 15)
    local_beam(f"{p}:tide-post", angle, radius, (0.63, 0.02, 0.22), (0.63, 0.02, 1.48),
               0.055, material, 10)
    local_box(f"{p}:tide-board", angle, radius, 0.63, 0.02, 0.94,
              (0.48, 0.12, 0.88), material, 4, 0.025)
    for z in (0.70, 0.94, 1.18):
        local_box(f"{p}:tide-mark:{z}", angle, radius, 0.63, -0.075, z,
                  (0.36, 0.035, 0.045), material, 14)


def add_e6(angle: float, radius: float, material) -> None:
    p = "EraStation:06:E6AppliancePen"
    for tangent in (-0.88, 0.88):
        local_beam(f"{p}:pen-side:{tangent}", angle, radius, (tangent, -0.28, 0.25),
                   (tangent, 0.28, 0.25), 0.045, material, 12)
    local_beam(f"{p}:pen-back", angle, radius, (-0.88, 0.28, 0.25), (0.88, 0.28, 0.25),
               0.045, material, 12)
    local_box(f"{p}:toaster", angle, radius, 0.0, -0.02, 0.58,
              (0.92, 0.52, 0.58), material, 7, 0.08)
    local_box(f"{p}:teal-face", angle, radius, 0.0, -0.295, 0.60,
              (0.42, 0.045, 0.22), material, 13, 0.02)
    for tangent in (-0.22, 0.22):
        local_box(f"{p}:toast:{tangent}", angle, radius, tangent, 0.02, 1.01,
                  (0.28, 0.16, 0.46), material, 14, 0.06)
    for tangent in (-0.28, 0.28):
        local_cylinder(f"{p}:wheel:{tangent}", angle, radius, tangent, -0.02, 0.27,
                       0.13, 0.16, material, 9, 8, "radial")


def add_e7(angle: float, radius: float, material) -> None:
    p = "EraStation:07:E7RelayTape"
    local_box(f"{p}:deck", angle, radius, -0.30, 0.0, 0.54,
              (1.20, 0.56, 0.62), material, 6, 0.05)
    for tangent in (-0.56, -0.04):
        local_torus(f"{p}:reel:{tangent}", angle, radius, tangent, -0.30, 0.65,
                    0.21, 0.045, material, 12, True)
    local_beam(f"{p}:tape", angle, radius, (-0.38, -0.34, 0.65), (-0.22, -0.34, 0.65),
               0.022, material, 13, 5)
    local_beam(f"{p}:mast", angle, radius, (0.62, 0.05, 0.22), (0.62, 0.05, 1.55),
               0.06, material, 10)
    for z, reach in ((1.15, 0.32), (1.42, 0.48)):
        local_beam(f"{p}:signal-l:{z}", angle, radius, (0.62, 0.05, z),
                   (0.62 - reach, 0.05, z + 0.18), 0.032, material, 13, 5)
        local_beam(f"{p}:signal-r:{z}", angle, radius, (0.62, 0.05, z),
                   (0.62 + reach, 0.05, z + 0.18), 0.032, material, 13, 5)


def add_e8(angle: float, radius: float, material) -> None:
    p = "EraStation:08:E8SurveyStop"
    local_box(f"{p}:moon-crate", angle, radius, -0.40, 0.02, 0.45,
              (0.86, 0.58, 0.46), material, 7, 0.05)
    sphere(f"{p}:helmet", point(angle, radius, -0.40, 0.0, 0.94),
           (0.39, 0.39, 0.34), material, 7, 12, 6)
    sphere(f"{p}:visor", point(angle, radius, -0.40, -0.31, 0.94),
           (0.28, 0.10, 0.20), material, 13, 10, 5)
    local_beam(f"{p}:dish-mast", angle, radius, (0.60, 0.10, 0.24), (0.60, 0.10, 1.12),
               0.055, material, 12)
    cone(f"{p}:dish", point(angle, radius, 0.60, -0.03, 1.24),
         0.36, 0.07, 0.26, material, 7, 12, (0.0, math.pi / 2.0, angle))
    local_beam(f"{p}:dish-feed", angle, radius, (0.60, -0.02, 1.24), (0.60, -0.36, 1.24),
               0.03, material, 13, 5)


def add_e9(angle: float, radius: float, material) -> None:
    p = "EraStation:09:E9CanalGarden"
    local_box(f"{p}:canal", angle, radius, -0.40, 0.0, 0.32,
              (1.10, 0.52, 0.20), material, 4, 0.02)
    for tangent in (-0.85, 0.05):
        local_beam(f"{p}:gate-post:{tangent}", angle, radius, (tangent, -0.02, 0.22),
                   (tangent, -0.02, 1.12), 0.055, material, 12)
    local_beam(f"{p}:gate-top", angle, radius, (-0.85, -0.02, 1.08), (0.05, -0.02, 1.08),
               0.055, material, 12)
    local_torus(f"{p}:gate-wheel", angle, radius, -0.40, -0.30, 0.73,
                0.25, 0.045, material, 12, True)
    local_box(f"{p}:green-bed", angle, radius, 0.66, 0.02, 0.34,
              (0.64, 0.54, 0.22), material, 8, 0.035)
    for tangent in (0.46, 0.66, 0.86):
        local_beam(f"{p}:sprout:{tangent}", angle, radius, (tangent, -0.02, 0.43),
                   (tangent, -0.02, 0.76), 0.025, material, 8, 5)
        sphere(f"{p}:leaf:{tangent}", point(angle, radius, tangent + 0.07, -0.02, 0.70),
               (0.12, 0.06, 0.07), material, 8, 8, 4)


def add_e10(angle: float, radius: float, material) -> None:
    p = "EraStation:10:E10TenEraRibbon"
    for tangent in (-0.93, 0.93):
        local_beam(f"{p}:frame:{tangent}", angle, radius, (tangent, 0.02, 0.22),
                   (tangent, 0.02, 1.58), 0.06, material, 10)
    local_beam(f"{p}:header", angle, radius, (-0.93, 0.02, 1.58), (0.93, 0.02, 1.58),
               0.06, material, 12)
    local_beam(f"{p}:ribbon", angle, radius, (-0.82, -0.02, 1.14), (0.82, -0.02, 1.14),
               0.025, material, 15, 5)
    for index in range(10):
        tangent = -0.78 + index * (1.56 / 9.0)
        sphere(f"{p}:era-bead:{index + 1:02d}", point(angle, radius, tangent, -0.03, 1.14),
               (0.075, 0.075, 0.075), material, index, 8, 4)
    local_box(f"{p}:charter", angle, radius, 0.0, 0.03, 0.65,
              (0.88, 0.10, 0.64), material, 15, 0.04)
    local_torus(f"{p}:seal", angle, radius, 0.0, -0.09, 0.66,
                0.22, 0.045, material, 12, True)
    for ray in range(5):
        a = math.pi / 2.0 + ray * math.tau / 5.0
        local_beam(f"{p}:seal-ray:{ray}", angle, radius,
                   (math.cos(a) * -0.18, -0.15, 0.66 + math.sin(a) * -0.18),
                   (math.cos(a) * 0.18, -0.15, 0.66 + math.sin(a) * 0.18),
                   0.018, material, 14, 5)


BUILDERS = (add_e1, add_e2, add_e3, add_e4, add_e5, add_e6, add_e7, add_e8, add_e9, add_e10)


def add_all_stations(material) -> list[dict]:
    records = []
    for index, builder in enumerate(BUILDERS):
        angle, radius, _ = station_center(index)
        add_station_base(index, angle, radius, material)
        builder(angle, radius, material)
        center = point(angle, radius, 0.0, 0.0, 0.0)
        records.append({
            "era": index + 1,
            "read": ERA_READS[index],
            "center": [round(center[0], 6), round(center[1], 6)],
            "angleDegrees": round(math.degrees(angle), 6),
            "radius": round(radius, 6),
        })
    return records


def join_parts(material) -> bpy.types.Object:
    bpy.ops.object.select_all(action="DESELECT")
    for part in PARTS:
        part.select_set(True)
    bpy.context.view_layer.objects.active = PARTS[0]
    bpy.ops.object.join()
    result = bpy.context.object
    result.name = "ArkDeckEraDressingE10"
    for polygon in result.data.polygons:
        polygon.material_index = 0
    while len(result.data.materials) > 1:
        result.data.materials.pop(index=1)
    if not result.data.materials:
        result.data.materials.append(material)
    # The active E1 plinth is not at the world origin. Bake its join transform
    # so every station keeps its world placement while the mount resets to 0.
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return result


def triangle_count(obj: bpy.types.Object) -> int:
    return sum(max(0, len(polygon.vertices) - 2) for polygon in obj.data.polygons)


def save_and_export(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.export_scene.gltf(
        filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT",
    )


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    reset_scene()
    atlas = make_atlas()
    material = make_material(atlas)
    stations = add_all_stations(material)
    dressing = join_parts(material)
    triangles = triangle_count(dressing)
    if triangles > TRIANGLE_BUDGET:
        raise RuntimeError(f"Ark deck dressing exceeds {TRIANGLE_BUDGET}: {triangles}")
    save_and_export(dressing)
    contract = {
        "wave": "ARK-DECK ERA DRESSING",
        "baseSha": BASE_SHA,
        "production": {
            "blend": str(BLEND.relative_to(ROOT)),
            "glb": str(GLB.relative_to(ROOT)),
            "atlas": str(ATLAS_FILE.relative_to(ROOT)),
            "triangles": triangles,
            "triangleBudget": TRIANGLE_BUDGET,
            "materials": 1,
            "atlasSize": [ATLAS_SIZE, ATLAS_SIZE],
            "origin": "Ark plaza origin; mount at [0,0,0] without transform",
        },
        "design": {
            "purpose": "ten memory stations turn the accepted color fields into tactile era stories while keeping the medallions and portals visible",
            "ownershipBoundary": "separate mount; accepted 19,676-triangle Ark plaza GLB remains byte-for-byte untouched",
            "stations": stations,
        },
        "sources": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in [*ERA_SOURCES, ARK_PLATE, E10_BUNDLE]
        },
    }
    (ARTIFACTS / "ark-deck-era-dressing-build-contract.json").write_text(json.dumps(contract, indent=2) + "\n")
    print(json.dumps({
        "glb": str(GLB), "sha256": sha256(GLB), "triangles": triangles,
        "stations": stations, "baseSha": BASE_SHA,
    }, indent=2))


if __name__ == "__main__":
    main()
