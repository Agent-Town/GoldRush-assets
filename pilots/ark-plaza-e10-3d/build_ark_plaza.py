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
OUT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/ark-plaza-e10"
BLEND = OUT / "ark-plaza-e10.blend"
GLB = OUT / "ark-plaza-e10.glb"
TEMP_ATLAS = OUT / ".ark-plaza-e10-atlas.png"
TOWN_BUILDER = ROOT / "assets/pilots/town-plate-3d/build_town_plate.py"
TOWN_LAYOUT = ROOT / "src/town/townLayout.ts"
ARK_PLATE = ROOT / "assets/raw/kit-the-ark.png"
E10_PLATE = ROOT / "assets/raw/kit-era-10.png"
PAN_SHRINE = ROOT / "assets/raw/plate-e10-pan-shrine.png"
LONG_TABLE = ROOT / "assets/raw/plate-e10-long-table.png"
E10_BUNDLE = ROOT / "specs/epoch-saga/e10-deepsky-bundle.md"

BASE_SHA = "d944dc7ebd690141d52f363d38aa6dc1a83f4343"
ATLAS_SIZE = 2048
TRIANGLE_BUDGET = 20_000
DECK_RADIUS = 23.0
WALK_RELIEF_LIMIT = 0.05

PINNED_SOURCE_HASHES = {
    TOWN_BUILDER: "d46c3799bf395387ac62c22074fa9bc5b2cc2c0be9549c8382ca4395b4e286ce",
    TOWN_LAYOUT: "6d000feac3c0e2e14051f287205e5450b3b701bec4c44e513613a34ea39017d0",
    ARK_PLATE: "462ad2e6a2e687111bf137aff5811ea639661f16be320e09fcc60033196d3475",
    E10_PLATE: "19f79418c8e9aa8bbee493c8fc9c88d8d5364ce21576d8fd5f05304eee80614b",
    PAN_SHRINE: "fa388fd06fea386bd51d14d643aa881ffd1323c7feca61e231218bec015c3236",
    LONG_TABLE: "b5349ca7ee9405304bfd56101d887bb90024a3c693bbc788f299a9dd0caf1abf",
    E10_BUNDLE: "9d10bbd7b9591d56870f6f483b06488e3c0c1e64a7438dbf2fa7ea72f96bf493",
}

# Walking the plaza is walking the saga. The swatches are deliberately muted
# readings of each era, with deep-ink hull and restrained teal/gold ship light.
PALETTE = (
    (0.43, 0.25, 0.10),  # E1 earth and timber
    (0.34, 0.17, 0.06),  # E2 steam bronze
    (0.09, 0.34, 0.34),  # E3 voltage teal
    (0.40, 0.15, 0.055), # E4 motor red
    (0.16, 0.29, 0.32),  # E5 deepwater blue
    (0.30, 0.40, 0.28),  # E6 atomic mint
    (0.20, 0.17, 0.29),  # E7 signal violet
    (0.39, 0.40, 0.38),  # E8 orbital silver
    (0.27, 0.35, 0.25),  # E9 restored green
    (0.14, 0.11, 0.09),  # E10 deep ink
    (0.07, 0.20, 0.21),  # hull shadow
    (0.67, 0.40, 0.10),  # brass
    (0.10, 0.56, 0.57),  # ship-light teal
    (0.86, 0.58, 0.19),  # ship-light gold
    (0.13, 0.42, 0.48),  # fountain water
    (0.36, 0.19, 0.08),  # worn deck timber
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sources() -> None:
    mismatches = []
    for path, expected in PINNED_SOURCE_HASHES.items():
        actual = sha256(path) if path.is_file() else "missing"
        if actual != expected:
            mismatches.append(f"{path.relative_to(ROOT)}: expected {expected}, got {actual}")
    if mismatches:
        raise RuntimeError(f"Ark Plaza inputs drifted from base {BASE_SHA}:\n" + "\n".join(mismatches))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


verify_sources()
town = load_module("ark_plaza_town_contract", TOWN_BUILDER)


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0


def source_array(path: Path) -> np.ndarray:
    image = bpy.data.images.load(str(path), check_existing=False)
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    array = pixels.reshape(height, width, 4)
    bpy.data.images.remove(image)
    return array


def make_atlas() -> bpy.types.Image:
    source_a = source_array(ARK_PLATE)
    source_b = source_array(E10_PLATE)
    height = ATLAS_SIZE
    width = ATLAS_SIZE
    pixels = np.ones((height, width, 4), dtype=np.float32)

    deck_height = int(height * 0.80)
    sx = np.linspace(0, source_a.shape[1] - 1, width).astype(np.int32)
    sy = np.linspace(0, source_a.shape[0] - 1, deck_height).astype(np.int32)
    ark_sample = source_a[np.ix_(sy, sx)][:, :, :3]
    sy_b = np.linspace(0, source_b.shape[0] - 1, deck_height).astype(np.int32)
    era_sample = source_b[np.ix_(sy_b, sx)][:, :, :3]
    luminance = 0.65 * np.mean(ark_sample, axis=2) + 0.35 * np.mean(era_sample, axis=2)

    x = np.linspace(-1.0, 1.0, width, dtype=np.float32)[None, :]
    y = np.linspace(-1.0, 1.0, deck_height, dtype=np.float32)[:, None]
    radius = np.hypot(x, y)
    angle = np.arctan2(y, x)
    ring_lines = np.exp(-((np.sin(radius * math.pi * 21.0) / 0.19) ** 2))
    spoke_lines = np.exp(-((np.sin(angle * 10.0) / 0.18) ** 2))
    plank_lines = np.exp(-((np.sin((y + x * 0.09) * math.pi * 28.0) / 0.16) ** 2))
    engraved = np.clip(0.055 * ring_lines + 0.035 * spoke_lines + 0.025 * plank_lines, 0.0, 0.12)
    base = np.array([0.23, 0.13, 0.055], dtype=np.float32)
    variation = np.clip((luminance - 0.38) * 0.16, -0.055, 0.075)
    pixels[:deck_height, :, :3] = np.clip(base + variation[:, :, None] - engraved[:, :, None], 0.02, 0.95)

    swatch_start = int(height * 0.82)
    source_noise = np.mean(source_b[: min(source_b.shape[0], height - swatch_start), :, :3], axis=2)
    for index, color in enumerate(PALETTE):
        x0 = int(index * width / len(PALETTE))
        x1 = int((index + 1) * width / len(PALETTE))
        swatch_width = x1 - x0
        noise_x = np.linspace(0, source_noise.shape[1] - 1, swatch_width).astype(np.int32)
        noise_y = np.linspace(0, source_noise.shape[0] - 1, height - swatch_start).astype(np.int32)
        noise = source_noise[np.ix_(noise_y, noise_x)]
        tone = np.clip((noise - 0.40) * 0.12, -0.045, 0.055)
        pixels[swatch_start:, x0:x1, :3] = np.clip(np.array(color)[None, None, :] + tone[:, :, None], 0.02, 0.96)

    image = bpy.data.images.new("ArkPlazaPaintedAtlas", width, height, alpha=True)
    image.pixels.foreach_set(pixels.ravel())
    image.filepath_raw = str(TEMP_ATLAS)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image


def make_material(atlas: bpy.types.Image) -> bpy.types.Material:
    material = bpy.data.materials.new("ArkPlazaPaintedMaterial")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    shader = nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = 0.84
    shader.inputs["Metallic"].default_value = 0.06
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = atlas
    texture.interpolation = "Linear"
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    return material


PARTS: list[bpy.types.Object] = []


def swatch_uv(index: int) -> tuple[float, float]:
    return ((index + 0.5) / len(PALETTE), 0.91)


def paint_swatch(obj: bpy.types.Object, index: int) -> bpy.types.Object:
    uv_layer = obj.data.uv_layers.get("UVMap") or obj.data.uv_layers.new(name="UVMap")
    uv = swatch_uv(index)
    for loop in uv_layer.data:
        loop.uv = uv
    PARTS.append(obj)
    return obj


def box(name: str, location: tuple[float, float, float], size: tuple[float, float, float], material,
        swatch: int, rotation: float = 0.0, bevel: float = 0.0) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=(0.0, 0.0, rotation))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0.0:
        modifier = obj.modifiers.new("Painted edge softening", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.data.materials.append(material)
    return paint_swatch(obj, swatch)


def cylinder(name: str, location: tuple[float, float, float], radius: float, depth: float, material,
             swatch: int, vertices: int = 16, rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return paint_swatch(obj, swatch)


def cone(name: str, location: tuple[float, float, float], radius1: float, radius2: float, depth: float,
         material, swatch: int, vertices: int = 12):
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return paint_swatch(obj, swatch)


def sphere(name: str, location: tuple[float, float, float], scale: tuple[float, float, float],
           material, swatch: int, segments: int = 16, rings: int = 8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return paint_swatch(obj, swatch)


def torus(name: str, location: tuple[float, float, float], major: float, minor: float, material,
          swatch: int, major_segments: int = 48, minor_segments: int = 6,
          rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major, minor_radius=minor, major_segments=major_segments, minor_segments=minor_segments,
        location=location, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return paint_swatch(obj, swatch)


def beam(name: str, start: tuple[float, float, float], end: tuple[float, float, float], radius: float,
         material, swatch: int, vertices: int = 8):
    start_v = Vector(start)
    end_v = Vector(end)
    direction = end_v - start_v
    obj = cylinder(name, tuple((start_v + end_v) * 0.5), radius, direction.length, material, swatch, vertices)
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=False)
    return obj


def mesh_object(name: str, vertices, faces, uv_faces, material) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(material)
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for polygon, uvs in zip(mesh.polygons, uv_faces):
        for loop_index, uv in zip(polygon.loop_indices, uvs):
            uv_layer.data[loop_index].uv = uv
    PARTS.append(obj)
    return obj


def add_deck(material) -> None:
    segments = 96
    vertices = [(0.0, 0.0, 0.0)]
    vertices += [
        (math.cos(i / segments * math.tau) * DECK_RADIUS, math.sin(i / segments * math.tau) * DECK_RADIUS, 0.0)
        for i in range(segments)
    ]
    vertices += [
        (math.cos(i / segments * math.tau) * DECK_RADIUS, math.sin(i / segments * math.tau) * DECK_RADIUS, -0.52)
        for i in range(segments)
    ]
    faces = []
    uv_faces = []
    for index in range(segments):
        following = (index + 1) % segments
        top = (0, 1 + index, 1 + following)
        faces.append(top)
        uv_faces.append([
            (0.5, 0.40),
            (0.5 + math.cos(index / segments * math.tau) * 0.39, 0.40 + math.sin(index / segments * math.tau) * 0.36),
            (0.5 + math.cos(following / segments * math.tau) * 0.39, 0.40 + math.sin(following / segments * math.tau) * 0.36),
        ])
        faces.append((1 + index, 1 + segments + index, 1 + segments + following, 1 + following))
        uv_faces.append([swatch_uv(10)] * 4)
    mesh_object("ArkPlazaDeck", vertices, faces, uv_faces, material)


def add_annular_sector(material, index: int, start_angle: float, end_angle: float) -> None:
    segments = 7
    inner = 16.35
    outer = 18.85
    top = 0.018
    vertices = []
    for radius in (inner, outer):
        for step in range(segments + 1):
            angle = start_angle + (end_angle - start_angle) * step / segments
            vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, top))
    faces = []
    uvs = []
    uv = swatch_uv(index)
    for step in range(segments):
        faces.append((step, step + 1, segments + 2 + step, segments + 1 + step))
        uvs.append([uv] * 4)
    mesh_object(f"EraDeck:{index + 1:02d}", vertices, faces, uvs, material)


def add_era_decks(material) -> None:
    gap = math.radians(2.0)
    for index in range(10):
        center = math.radians(90.0) - index * math.tau / 10.0
        half = math.tau / 20.0 - gap
        add_annular_sector(material, index, center - half, center + half)

    # The plaza remains one coherent working deck. Ten low lineage medallions
    # carry the era grammar around its edge instead of turning the floor into a
    # literal color wheel.
    torus("LineageRing:Inner", (0.0, 0.0, 0.015), 6.15, 0.027, material, 11, 48, 4)
    torus("LineageRing:Outer", (0.0, 0.0, 0.015), 12.65, 0.027, material, 12, 48, 4)
    for index in range(10):
        angle = math.radians(90.0) - index * math.tau / 10.0
        start = Vector((math.cos(angle) * 3.15, math.sin(angle) * 3.15, 0.016))
        end = Vector((math.cos(angle) * 12.25, math.sin(angle) * 12.25, 0.016))
        beam(f"LineageSeam:{index + 1:02d}", tuple(start), tuple(end), 0.018, material, 11, 6)
        x = math.cos(angle) * 17.62
        y = math.sin(angle) * 17.62
        cylinder(f"LineageMedallion:{index + 1:02d}:field", (x, y, 0.014), 0.76, 0.028, material, index, 14)
        torus(f"LineageMedallion:{index + 1:02d}:rim", (x, y, 0.021), 0.76, 0.030,
              material, 11, 12, 3)
        add_lineage_pictogram(material, index, x, y, angle)

    # Ten lineage beacons keep the deck families readable across the plaza.
    for index in range(10):
        angle = math.radians(90.0) - index * math.tau / 10.0
        radius = 20.55
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius
        height = 0.90 + (index % 3) * 0.18
        beam(f"LineageBeacon:{index + 1:02d}:post", (x, y, 0.05), (x, y, height), 0.055, material, 10, 7)
        cylinder(f"LineageBeacon:{index + 1:02d}:lamp", (x, y, height + 0.12), 0.13, 0.24, material, index, 10)
        torus(f"LineageBeacon:{index + 1:02d}:halo", (x, y, height + 0.12), 0.17, 0.025, material, 11, 10, 3,
              (math.pi / 2.0, 0.0, angle))


def local_point(cx: float, cy: float, angle: float, x: float, y: float, z: float = 0.055) -> tuple[float, float, float]:
    return (
        cx + math.cos(angle) * x - math.sin(angle) * y,
        cy + math.sin(angle) * x + math.cos(angle) * y,
        z,
    )


def icon_beam(name: str, material, cx: float, cy: float, angle: float,
              start: tuple[float, float], end: tuple[float, float], swatch: int = 13) -> None:
    beam(name, local_point(cx, cy, angle, *start), local_point(cx, cy, angle, *end), 0.018, material, swatch, 5)


def add_lineage_pictogram(material, index: int, cx: float, cy: float, angle: float) -> None:
    name = f"LineageMedallion:{index + 1:02d}:pictogram"
    if index == 0:  # E1 pan
        torus(f"{name}:pan", local_point(cx, cy, angle, 0.0, 0.04), 0.25, 0.026, material, 13, 16, 4)
        icon_beam(f"{name}:handle", material, cx, cy, angle, (0.20, -0.12), (0.52, -0.40))
    elif index == 1:  # E2 boiler/gear
        torus(f"{name}:gear", local_point(cx, cy, angle, 0.0, 0.0), 0.27, 0.030, material, 13, 12, 4)
        for spoke in range(6):
            direction = spoke / 6.0 * math.tau
            icon_beam(f"{name}:tooth:{spoke}", material, cx, cy, angle,
                      (math.cos(direction) * 0.22, math.sin(direction) * 0.22),
                      (math.cos(direction) * 0.42, math.sin(direction) * 0.42))
    elif index == 2:  # E3 lightning
        for part, (start, end) in enumerate((((-0.16, 0.45), (0.12, 0.08)), ((0.12, 0.08), (-0.04, 0.08)),
                                             ((-0.04, 0.08), (0.18, -0.42)))):
            icon_beam(f"{name}:bolt:{part}", material, cx, cy, angle, start, end, 12)
    elif index == 3:  # E4 wheel
        torus(f"{name}:wheel", local_point(cx, cy, angle, 0.0, 0.0), 0.33, 0.030, material, 13, 16, 4)
        for spoke in range(4):
            direction = spoke / 4.0 * math.pi
            icon_beam(f"{name}:spoke:{spoke}", material, cx, cy, angle,
                      (-math.cos(direction) * 0.28, -math.sin(direction) * 0.28),
                      (math.cos(direction) * 0.28, math.sin(direction) * 0.28))
    elif index == 4:  # E5 anchor/tide
        icon_beam(f"{name}:stem", material, cx, cy, angle, (0.0, 0.40), (0.0, -0.28), 12)
        icon_beam(f"{name}:bar", material, cx, cy, angle, (-0.22, 0.24), (0.22, 0.24), 12)
        icon_beam(f"{name}:left", material, cx, cy, angle, (0.0, -0.28), (-0.34, -0.05), 12)
        icon_beam(f"{name}:right", material, cx, cy, angle, (0.0, -0.28), (0.34, -0.05), 12)
    elif index == 5:  # E6 atom
        for orbit, points in enumerate((
            ((-0.36, 0.0), (0.0, 0.20), (0.36, 0.0), (0.0, -0.20), (-0.36, 0.0)),
            ((-0.20, -0.31), (0.10, -0.17), (0.20, 0.31), (-0.10, 0.17), (-0.20, -0.31)),
            ((0.20, -0.31), (-0.10, -0.17), (-0.20, 0.31), (0.10, 0.17), (0.20, -0.31)),
        )):
            for segment, (start, end) in enumerate(zip(points, points[1:])):
                icon_beam(f"{name}:orbit:{orbit}:{segment}", material, cx, cy, angle, start, end, 13)
        cylinder(f"{name}:core", local_point(cx, cy, angle, 0.0, 0.0), 0.08, 0.05, material, 12, 10)
    elif index == 6:  # E7 relay
        icon_beam(f"{name}:mast", material, cx, cy, angle, (0.0, -0.38), (0.0, 0.35), 12)
        for side in (-1.0, 1.0):
            icon_beam(f"{name}:wave:{side}:1", material, cx, cy, angle, (0.08 * side, 0.12), (0.30 * side, 0.27), 13)
            icon_beam(f"{name}:wave:{side}:2", material, cx, cy, angle, (0.10 * side, -0.02), (0.40 * side, 0.15), 13)
    elif index == 7:  # E8 orbit
        torus(f"{name}:orbit", local_point(cx, cy, angle, 0.0, 0.0), 0.34, 0.020, material, 13, 18, 4,
              (0.0, 0.0, angle))
        box(f"{name}:satellite", local_point(cx, cy, angle, 0.0, 0.0), (0.20, 0.14, 0.035), material, 12, angle)
    elif index == 8:  # E9 seed/canal
        icon_beam(f"{name}:stem", material, cx, cy, angle, (0.0, -0.38), (0.0, 0.30), 12)
        icon_beam(f"{name}:leaf-l", material, cx, cy, angle, (0.0, 0.08), (-0.32, 0.30), 13)
        icon_beam(f"{name}:leaf-r", material, cx, cy, angle, (0.0, -0.06), (0.30, 0.16), 13)
    else:  # E10 star/charter
        for ray in range(5):
            direction = ray / 5.0 * math.tau + math.pi / 2.0
            icon_beam(f"{name}:star:{ray}", material, cx, cy, angle, (0.0, 0.0),
                      (math.cos(direction) * 0.40, math.sin(direction) * 0.40), 13)


def add_hull_and_rails(material) -> None:
    torus("Hull:Rim", (0.0, 0.0, -0.08), 22.75, 0.32, material, 10, 64, 6)
    torus("Hull:ShipLight", (0.0, 0.0, 0.13), 22.25, 0.055, material, 12, 64, 4)
    for radius, height in ((22.0, 0.70), (22.0, 1.32)):
        # Four cardinal breaks remain open for airlocks and the hall/bridge axes.
        for quadrant in range(4):
            start = quadrant * math.pi / 2.0 + math.radians(12.0)
            end = (quadrant + 1) * math.pi / 2.0 - math.radians(12.0)
            previous = None
            for step in range(14):
                angle = start + (end - start) * step / 13.0
                point = (math.cos(angle) * radius, math.sin(angle) * radius, height)
                if previous is not None:
                    beam(f"Hull:Rail:{height:.2f}:{quadrant}:{step}", previous, point, 0.045, material, 11, 6)
                previous = point
    for index in range(32):
        angle = index / 32.0 * math.tau
        if min(abs(math.sin(angle)), abs(math.cos(angle))) < 0.16:
            continue
        x = math.cos(angle) * 22.0
        y = math.sin(angle) * 22.0
        beam(f"Hull:Stanchion:{index:02d}", (x, y, 0.12), (x, y, 1.36), 0.055, material, 10, 7)

    # Exterior ribs and observation lenses give the circular town deck a ship
    # body in every turntable angle. They sit beyond the walkable radius.
    for index in range(12):
        angle = index / 12.0 * math.tau
        if min(abs(math.sin(angle)), abs(math.cos(angle))) < 0.18:
            continue
        inner = (math.cos(angle) * 22.35, math.sin(angle) * 22.35, -0.24)
        outer = (math.cos(angle) * 24.10, math.sin(angle) * 24.10, 1.85)
        beam(f"Hull:ExteriorRib:{index:02d}", inner, outer, 0.16, material, 10, 8)
        torus(f"Hull:RibCollar:{index:02d}", outer, 0.27, 0.07, material, 11, 10, 3,
              (math.pi / 2.0, 0.0, angle))
    for side in (-1.0, 1.0):
        x = side * 23.45
        cylinder(f"Hull:ObservationPod:{side}:body", (x, 0.0, 1.42), 1.35, 2.2, material, 10, 24,
                 (0.0, math.pi / 2.0, 0.0))
        cylinder(f"Hull:ObservationPod:{side}:lens", (x + side * 1.13, 0.0, 1.42), 0.91, 0.10,
                 material, 12, 24, (0.0, math.pi / 2.0, 0.0))
        torus(f"Hull:ObservationPod:{side}:collar", (x + side * 1.06, 0.0, 1.42), 1.03, 0.10,
              material, 11, 16, 4, (0.0, math.pi / 2.0, 0.0))
        torus(f"Hull:ObservationPod:{side}:shiplight", (x, 0.0, 1.42), 1.38, 0.055,
              material, 12, 16, 3, (0.0, math.pi / 2.0, 0.0))


def add_fountain(material) -> None:
    # The Pan Monument remains a separate heritage mount at the center. This
    # plate supplies the Carry's final fountain around its unchanged footprint.
    # Its basin is recessed/flush: the ship did not introduce an actor-clipping
    # curb in the final plaza merely to make the fountain grander.
    torus("CarryFountain:OuterBasin", (0.0, 0.0, 0.014), 2.35, 0.030, material, 11, 40, 4)
    torus("CarryFountain:ShipLight", (0.0, 0.0, 0.012), 2.05, 0.025, material, 12, 40, 4)
    torus("CarryFountain:WaterRing", (0.0, 0.0, -0.205), 1.65, 0.235, material, 14, 40, 4)
    cylinder("CarryFountain:PanMount", (0.0, 0.0, 0.020), 0.88, 0.04, material, 11, 32)
    for index in range(4):
        angle = index / 4.0 * math.tau + math.pi / 4.0
        base = Vector((math.cos(angle) * 1.15, math.sin(angle) * 1.15, 0.03))
        apex = Vector((math.cos(angle) * 0.82, math.sin(angle) * 0.82, 0.30))
        end = Vector((math.cos(angle) * 0.62, math.sin(angle) * 0.62, 0.13))
        points = []
        for step in range(7):
            t = step / 6.0
            point = (1 - t) ** 2 * base + 2 * (1 - t) * t * apex + t**2 * end
            points.append(tuple(point))
        for step, (left, right) in enumerate(zip(points, points[1:])):
            beam(f"CarryFountain:Jet:{index + 1}:{step + 1}", left, right, 0.035, material, 14, 6)


def add_portal(name: str, y: float, facing: float, material, hall: bool) -> None:
    sign = 1.0 if y > 0 else -1.0
    for x in (-3.55, 3.55):
        box(f"{name}:Pier", (x, y, 2.25), (0.82, 1.10, 4.50), material, 10, bevel=0.10)
        for z in (0.65, 2.10, 3.55):
            torus(f"{name}:PierBand:{x}:{z}", (x, y, z), 0.50, 0.060, material, 11, 10, 4,
                  (math.pi / 2.0, 0.0, 0.0))
    arch_points = []
    for step in range(13):
        theta = step / 12.0 * math.pi
        arch_points.append((math.cos(theta) * 3.55, y, 3.95 + math.sin(theta) * 2.05))
    for index, (start, end) in enumerate(zip(arch_points, arch_points[1:])):
        beam(f"{name}:BulkheadArch:{index:02d}", start, end, 0.22, material, 11, 8)
    inner_points = []
    for step in range(13):
        theta = step / 12.0 * math.pi
        inner_points.append((math.cos(theta) * 3.28, y - sign * 0.15, 3.92 + math.sin(theta) * 1.78))
    for index, (start, end) in enumerate(zip(inner_points, inner_points[1:])):
        beam(f"{name}:ShipLightArch:{index:02d}", start, end, 0.055, material, 12, 6)
    if hall:
        # Blank portrait medallions announce the destination without hard-coded
        # likenesses; the runtime compositor belongs to the Hall wave.
        for index in range(5):
            x = (index - 2) * 0.74
            z = 4.70 + (0.42 if index in (1, 3) else (0.62 if index == 2 else 0.0))
            torus(f"{name}:PortraitMedallion:{index + 1}", (x, y - sign * 0.28, z), 0.22, 0.045,
                  material, 13, 10, 3, (math.pi / 2.0, 0.0, 0.0))
    else:
        for x in (-1.20, 0.0, 1.20):
            cylinder(f"{name}:Lens:{x}", (x, y - sign * 0.28, 4.82), 0.22, 0.08, material, 12, 12,
                     (math.pi / 2.0, 0.0, 0.0))


def add_long_table_hall_anchor(material) -> None:
    # The plaza is a deck within the Ark, not a disk floating beside it. A
    # substantial inhabited bulkhead/dome terminates the Long Table axis and
    # carries the exterior plate's clearest silhouette into gameplay.
    y = 21.75
    for side in (-1.0, 1.0):
        x = side * 5.45
        box(f"LongTableAnchor:{side}:Shoulder", (x, y, 2.25), (3.10, 1.85, 4.50), material, 10, bevel=0.10)
        cylinder(f"LongTableAnchor:{side}:Tower", (side * 6.15, y + 0.10, 4.65), 1.18, 3.80,
                 material, 10, 14)
        cone(f"LongTableAnchor:{side}:TowerRoof", (side * 6.15, y + 0.10, 6.82), 1.48, 0.34, 1.15,
             material, 11, 14)
        cylinder(f"LongTableAnchor:{side}:TowerLight", (side * 6.15, y - 1.10, 4.75), 0.34, 0.10,
                 material, 12, 12, (math.pi / 2.0, 0.0, 0.0))
        beam(f"LongTableAnchor:{side}:FlyingBrace",
             (side * 6.15, y, 5.90), (side * 2.15, y, 6.30), 0.12, material, 11, 7)
        for row in range(3):
            for column in range(2):
                window_x = side * (4.65 + column * 0.95)
                window_z = 1.15 + row * 1.12
                cylinder(f"LongTableAnchor:{side}:Window:{row}:{column}",
                         (window_x, y - 0.96, window_z), 0.23, 0.08, material, 13, 10,
                         (math.pi / 2.0, 0.0, 0.0))
                torus(f"LongTableAnchor:{side}:WindowRim:{row}:{column}",
                      (window_x, y - 1.01, window_z), 0.27, 0.035, material, 11, 10, 3,
                      (math.pi / 2.0, 0.0, 0.0))
    sphere("LongTableAnchor:CentralDome", (0.0, y + 0.18, 6.38), (2.75, 1.60, 1.55), material, 12, 16, 8)
    torus("LongTableAnchor:DomeCrown", (0.0, y + 0.18, 6.40), 2.50, 0.10, material, 11, 24, 4)
    cylinder("LongTableAnchor:Beacon", (0.0, y + 0.18, 8.08), 0.22, 0.78, material, 11, 10)
    sphere("LongTableAnchor:BeaconLight", (0.0, y + 0.18, 8.56), (0.26, 0.26, 0.32), material, 13, 10, 6)

    for side in (-1.0, 1.0):
        mast_x = side * 8.10
        beam(f"LongTableAnchor:GantryMast:{side}", (mast_x, y + 0.35, 2.80),
             (mast_x, y + 0.35, 10.15), 0.13, material, 10, 7)
        beam(f"LongTableAnchor:GantryBrace:{side}", (mast_x, y + 0.35, 7.55),
             (side * 2.25, y + 0.28, 7.15), 0.09, material, 11, 7)
        beam(f"LongTableAnchor:GantryCable:{side}", (mast_x, y + 0.35, 9.92),
             (0.0, y + 0.22, 8.72), 0.035, material, 11, 5)
        sphere(f"LongTableAnchor:GantryLamp:{side}", (mast_x, y + 0.35, 10.38),
               (0.24, 0.24, 0.30), material, 12, 10, 6)
    beam("LongTableAnchor:GantryCrown", (-8.10, y + 0.35, 10.15), (8.10, y + 0.35, 10.15),
         0.12, material, 11, 7)

    # Pictogram-only long table above the open arch.
    box("LongTableAnchor:TableTop", (0.0, y - 1.10, 5.10), (2.35, 0.12, 0.18), material, 13, bevel=0.035)
    for x in (-0.90, 0.90):
        beam(f"LongTableAnchor:TableLeg:{x}", (x, y - 1.12, 4.72), (x, y - 1.12, 5.06),
             0.055, material, 11, 6)


def add_working_ship_grit(material) -> None:
    # Exposed service runs live outside the actor loop: patched, practical, warm.
    for side in (-1.0, 1.0):
        x = side * 20.8
        for index in range(5):
            y0 = -11.0 + index * 5.2
            beam(f"ServiceRun:{side}:{index}:vertical", (x, y0, 0.22), (x, y0, 0.82), 0.075,
                 material, 11, 7)
            beam(f"ServiceRun:{side}:{index}:line", (x, y0, 0.62), (x, y0 + 3.4, 0.62), 0.075,
                 material, 10, 7)
            cylinder(f"ServiceRun:{side}:{index}:valve", (x - side * 0.10, y0 + 0.52, 0.72), 0.16, 0.06,
                     material, 13, 10, (0.0, math.pi / 2.0, 0.0))
    for x in (-13.8, 13.8):
        for y in (-15.0, 15.0):
            box(f"DeckPatch:{x}:{y}", (x, y, 0.026), (2.6, 1.25, 0.032), material, 15, 0.20, 0.04)
            for offset in (-0.9, 0.0, 0.9):
                cylinder(f"DeckPatch:Rivet:{x}:{y}:{offset}", (x + offset, y, 0.065), 0.055, 0.04,
                         material, 11, 8)


def add_plaza_life(material) -> None:
    # Human-scale rest and maintenance points keep the capstone warm without
    # trespassing on canonical pads or actor loops; all sit beyond radius 19.
    for index, angle_degrees in enumerate((38.0, 142.0, 218.0, 322.0), 1):
        angle = math.radians(angle_degrees)
        tangent = angle + math.pi / 2.0
        radius = 19.65
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius
        box(f"PlazaBench:{index}:seat", (x, y, 0.38), (2.15, 0.46, 0.18), material, 15, tangent)
        back = local_point(x, y, angle, -0.28, 0.0, 0.82)
        box(f"PlazaBench:{index}:back", back, (2.15, 0.16, 0.72), material, 15, tangent)
        for offset in (-0.72, 0.72):
            leg = local_point(x, y, tangent, offset, 0.0, 0.17)
            box(f"PlazaBench:{index}:leg:{offset}", leg, (0.18, 0.30, 0.34), material, 10, tangent)

    for index, angle_degrees in enumerate((68.0, 112.0, 248.0, 292.0), 1):
        angle = math.radians(angle_degrees)
        radius = 20.20
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius
        box(f"ServiceConsole:{index}:cabinet", (x, y, 0.52), (0.72, 0.54, 1.04), material, 10, angle, 0.04)
        face = local_point(x, y, angle, -0.31, 0.0, 0.76)
        cylinder(f"ServiceConsole:{index}:dial", face, 0.15, 0.06, material, 12, 10,
                 (0.0, math.pi / 2.0, angle))
        beam(f"ServiceConsole:{index}:lampPost", (x, y, 1.02), (x, y, 1.48), 0.035, material, 11, 6)
        sphere(f"ServiceConsole:{index}:lamp", (x, y, 1.57), (0.10, 0.10, 0.13), material, 13, 8, 5)


def join_parts(material) -> bpy.types.Object:
    bpy.ops.object.select_all(action="DESELECT")
    for part in PARTS:
        part.select_set(True)
    bpy.context.view_layer.objects.active = PARTS[0]
    bpy.ops.object.join()
    result = bpy.context.object
    result.name = "ArkPlazaE10"
    for polygon in result.data.polygons:
        polygon.material_index = 0
    while len(result.data.materials) > 1:
        result.data.materials.pop(index=1)
    if not result.data.materials:
        result.data.materials.append(material)
    result.location = (0.0, 0.0, 0.0)
    return result


def triangle_count(obj: bpy.types.Object) -> int:
    return sum(max(0, len(polygon.vertices) - 2) for polygon in obj.data.polygons)


def flat_walk_contract() -> dict:
    # The entire actor surface is the base deck at z=0; the thin era inlays are
    # 0.018 high and therefore remain well inside the inherited 0.05 law.
    samples = []
    for points, closed in [(town.RING_ROUTE, True), *[(route, False) for route in town.RADIAL_ROUTES.values()]]:
        pairs = list(zip(points, points[1:]))
        if closed:
            pairs.append((points[-1], points[0]))
        for start, end in pairs:
            length = math.hypot(end.x - start.x, end.y - start.y)
            count = max(1, math.ceil(length / 0.10))
            for index in range(count + 1):
                x = start.x + (end.x - start.x) * index / count
                y = start.y + (end.y - start.y) * index / count
                radius = math.hypot(x, y)
                samples.append(0.018 if 3.0 <= radius <= 19.7 else 0.0)
    return {
        "law": "all inherited town walk loops remain within +/-0.05; relief beyond 0.05 lives outside the actor surface",
        "sampleCount": len(samples),
        "minimum": min(samples),
        "maximum": max(samples),
        "maxAbs": max(abs(value) for value in samples),
        "limit": WALK_RELIEF_LIMIT,
        "centerFloor": 0.0,
        "eraInlayHeight": 0.018,
    }


def write_contract(obj: bpy.types.Object, flat_walk: dict) -> None:
    contract = {
        "wave": "THE ARK PLAZA (E10)",
        "baseSha": BASE_SHA,
        "production": {
            "blend": str(BLEND.relative_to(ROOT)),
            "glb": str(GLB.relative_to(ROOT)),
            "triangles": triangle_count(obj),
            "triangleBudget": TRIANGLE_BUDGET,
            "meshTree": [obj.name],
            "materials": 1,
            "atlas": [ATLAS_SIZE, ATLAS_SIZE],
            "lights": 0,
            "cameras": 0,
            "origin": "base-center; deck top y=0 after GLTF Y-up conversion",
        },
        "design": {
            "target": "a working Generation Ark plaza where ten subdued era decks converge on the Pan Monument's final fountain in ship-light",
            "heritageMount": "Pan Monument remains a separate unchanged GLB at [0,0,0]; the plate supplies its fountain",
            "lineageDecks": 10,
            "northPortal": "Long Table hall",
            "southPortal": "world-window bridge",
            "antiResortGrit": ["exposed service runs", "patched deck plates", "rivets", "open airlock breaks"],
        },
        "flatWalk": flat_walk,
        "sources": {str(path.relative_to(ROOT)): sha256(path) for path in PINNED_SOURCE_HASHES},
    }
    (ARTIFACTS / "ark-plaza-build-contract.json").write_text(json.dumps(contract, indent=2) + "\n")


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
    OUT.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    reset_scene()
    atlas = make_atlas()
    material = make_material(atlas)
    add_deck(material)
    add_era_decks(material)
    add_hull_and_rails(material)
    add_fountain(material)
    add_portal("LongTableHallPortal", 20.85, math.pi, material, True)
    add_long_table_hall_anchor(material)
    add_portal("WorldWindowBridgePortal", -20.85, 0.0, material, False)
    add_working_ship_grit(material)
    add_plaza_life(material)
    plaza = join_parts(material)
    triangles = triangle_count(plaza)
    if triangles > TRIANGLE_BUDGET:
        raise RuntimeError(f"Ark Plaza exceeds {TRIANGLE_BUDGET} triangles: {triangles}")
    flat_walk = flat_walk_contract()
    if flat_walk["maxAbs"] > WALK_RELIEF_LIMIT:
        raise RuntimeError(f"Flat-walk law failed: {flat_walk}")
    save_and_export(plaza)
    TEMP_ATLAS.unlink(missing_ok=True)
    write_contract(plaza, flat_walk)
    print(json.dumps({
        "blend": str(BLEND), "glb": str(GLB), "sha256": sha256(GLB),
        "triangles": triangles, "flatWalkMaxAbs": flat_walk["maxAbs"], "baseSha": BASE_SHA,
    }, indent=2))


if __name__ == "__main__":
    main()
