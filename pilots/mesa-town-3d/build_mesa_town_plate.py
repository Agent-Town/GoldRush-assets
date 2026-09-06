from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import subprocess
import sys

sys.dont_write_bytecode = True

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/mesa-town-3d"
RENDERS = OUT / "renders"
CURRENT_PLATE = ROOT / "assets/pilots/town-plate-3d/town-plate.glb"
MESA_SOURCE = ROOT / "assets/raw/ter-mesa-seamless.png"
E6_BUNDLE = ROOT / "specs/epoch-saga/e6-atomic-bundle.md"
BLEND = OUT / "mesa-town-plate.blend"
GLB = OUT / "mesa-town-plate.glb"
TEMP_ATLAS = OUT / ".mesa-town-atlas.png"

ATLAS_SIZE = 2048
CLIFF_V_MAX = 0.16
RINGS = 64
SEGMENTS = 128
CLIFF_MID_HEIGHT = -1.30
CLIFF_FOOT_HEIGHT = -2.82
APRON_HEIGHT = -3.02
BOTTOM_HEIGHT = -3.42
PLAZA_CLEAR_RADIUS = 3.1
PATH_SAFE_RADIUS = 1.05
PATH_RELIEF_LIMIT = 0.05
TRIANGLE_BUDGET = 20_000
BASE_SHA = "8d974f11911187136469fbd017c9598e5b2faf28"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


town = load_module("mesa_town_base", ROOT / "assets/pilots/town-plate-3d/build_town_plate.py")
Point = town.Point
Slot = town.Slot
CANONICAL_SLOTS = [*town.SLOTS, town.DYNAMO_SLOT]
CANONICAL_ROUTES = town.RADIAL_ROUTES
RING_ROUTE = town.RING_ROUTE


@dataclass(frozen=True)
class PremiumSite:
    id: str
    position: Point
    shape: str
    width: float
    depth: float
    height: float
    role: str


PREMIUM_SITES = (
    PremiumSite("reactor-dome-candidate", Point(7.0, -16.7), "circle", 6.2, 6.2, 1.18, "E6 A1 Reactor Dome premium mesa-top pad"),
    PremiumSite("catalog-warehouse-candidate", Point(-7.4, -16.6), "rectangle", 5.6, 3.8, 1.18, "E6 A1 Catalog Warehouse north-origin pad"),
)

MESA_ACCESS_PATHS = {
    "reactor-herd-ramp": [Point(11.0, -6.0), Point(13.0, -9.0), Point(11.0, -12.0), Point(7.0, -13.05)],
    "warehouse-herd-ramp": [Point(-11.0, -6.0), Point(-13.0, -9.0), Point(-11.0, -12.0), Point(-7.4, -14.15)],
}

STARSTONE_VEINS = (
    [Point(-20.5, -5.6), Point(-17.4, -4.3), Point(-15.4, -1.2), Point(-12.2, 0.8)],
    [Point(-19.0, 7.5), Point(-16.1, 6.2), Point(-14.0, 9.0), Point(-10.8, 10.8)],
    [Point(12.2, -12.6), Point(15.0, -9.8), Point(14.2, -6.4), Point(17.8, -3.8)],
    [Point(11.8, 11.7), Point(14.4, 9.0), Point(17.3, 9.8), Point(20.0, 6.8)],
    [Point(-4.2, -20.6), Point(-2.1, -18.8), Point(0.8, -20.1), Point(3.6, -18.3)],
    [Point(-20.2, 1.2), Point(-18.4, 2.9), Point(-19.1, 5.0), Point(-16.8, 6.1)],
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 1.0 if value >= edge1 else 0.0
    t = min(1.0, max(0.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def boundary_radius(angle: float) -> float:
    return 22.7 + 0.82 * math.sin(angle * 3.0 + 0.28) + 0.46 * math.sin(angle * 7.0 - 0.61) + 0.22 * math.cos(angle * 11.0 + 0.18)


def distance_to_segment(x: float, y: float, start: Point, end: Point) -> float:
    return town.distance_to_segment(x, y, start, end)


def distance_to_polyline(x: float, y: float, points: list[Point], closed: bool = False) -> float:
    return town.distance_to_polyline(x, y, points, closed)


def polyline_distance_progress(x: float, y: float, points: list[Point]) -> tuple[float, float]:
    lengths = [math.hypot(end.x - start.x, end.y - start.y) for start, end in zip(points, points[1:])]
    total = max(1e-9, sum(lengths))
    best_distance = math.inf
    best_progress = 0.0
    travelled = 0.0
    for (start, end), length in zip(zip(points, points[1:]), lengths):
        dx = end.x - start.x
        dy = end.y - start.y
        length_sq = max(1e-9, dx * dx + dy * dy)
        t = min(1.0, max(0.0, ((x - start.x) * dx + (y - start.y) * dy) / length_sq))
        projected_x = start.x + dx * t
        projected_y = start.y + dy * t
        distance = math.hypot(x - projected_x, y - projected_y)
        if distance < best_distance:
            best_distance = distance
            best_progress = (travelled + length * t) / total
        travelled += length
    return best_distance, best_progress


def route_distance(x: float, y: float) -> float:
    radial = min(distance_to_polyline(x, y, route) for route in CANONICAL_ROUTES.values())
    ring = abs(math.hypot(x, y) - 6.0)
    return min(radial, ring)


def rectangle_outside_distance(x: float, y: float, slot: Slot, margin: float = 0.0) -> float:
    return town.rectangle_outside_distance(x, y, slot, margin)


def site_outside_distance(x: float, y: float, site: PremiumSite) -> float:
    dx = abs(x - site.position.x)
    dy = abs(y - site.position.y)
    if site.shape == "circle":
        return max(0.0, math.hypot(dx, dy) - site.width * 0.5)
    return math.hypot(max(0.0, dx - site.width * 0.5), max(0.0, dy - site.depth * 0.5))


def site_inside_edge_distance(x: float, y: float, site: PremiumSite) -> float:
    dx = abs(x - site.position.x)
    dy = abs(y - site.position.y)
    if site.shape == "circle":
        return max(0.0, site.width * 0.5 - math.hypot(dx, dy))
    if dx <= site.width * 0.5 and dy <= site.depth * 0.5:
        return min(site.width * 0.5 - dx, site.depth * 0.5 - dy)
    return 0.0


def canonical_flat_mask(x: float, y: float) -> float:
    mask = smoothstep(PATH_SAFE_RADIUS, PATH_SAFE_RADIUS + 0.8, route_distance(x, y))
    mask = min(mask, smoothstep(PLAZA_CLEAR_RADIUS, PLAZA_CLEAR_RADIUS + 0.75, math.hypot(x, y)))
    for slot in CANONICAL_SLOTS:
        mask = min(mask, smoothstep(0.0, 0.72, rectangle_outside_distance(x, y, slot, margin=0.42)))
    return mask


def rear_shelf_height(y: float) -> float:
    return 1.18 * smoothstep(10.8, 16.0, -y)


def terrain_height(x: float, y: float) -> float:
    radius = math.hypot(x, y)
    relief = (
        0.43 * math.sin(x * 0.31 + y * 0.12)
        + 0.23 * math.cos(y * 0.39 - x * 0.08)
        + 0.11 * math.sin((x - y) * 0.77)
    ) * smoothstep(3.8, 12.0, radius)
    dry_wash = -0.34 * math.exp(-(((x + 14.8 + 0.11 * y) / 2.5) ** 2)) * smoothstep(5.0, 17.0, radius)
    caprock = 0.22 * smoothstep(14.0, 20.0, radius)
    base = rear_shelf_height(y) + relief + dry_wash + caprock

    # Canonical 2D cast routes, the open plaza, and every inherited building pad remain at y=0.
    height = base * canonical_flat_mask(x, y)
    route_bed = -0.012 * math.exp(-((route_distance(x, y) / 0.58) ** 4))
    height += route_bed

    for _path_name, points in MESA_ACCESS_PATHS.items():
        distance, progress = polyline_distance_progress(x, y, points)
        target_height = PREMIUM_SITES[0].height * progress
        blend = smoothstep(0.52, 1.18, distance)
        height = target_height * (1.0 - blend) + height * blend
    # The two upper pads are explicit candidates, not a hidden layout rewrite. Their collars
    # win over the access cuts so a future base-center model never inherits a ramped footprint.
    for site in PREMIUM_SITES:
        outside = site_outside_distance(x, y, site)
        blend = smoothstep(0.55, 1.28, outside)
        if site_inside_edge_distance(x, y, site) > 0.0:
            blend = 0.0
        height = site.height * (1.0 - blend) + height * blend
    return height


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0


def bilinear_sample(source: np.ndarray, u: np.ndarray, v: np.ndarray) -> np.ndarray:
    return town.bilinear_sample(source, u, v)


def distance_field(world_x: np.ndarray, world_y: np.ndarray, polylines: list[tuple[list[Point], bool]]) -> np.ndarray:
    result = np.full(world_x.shape, np.inf, dtype=np.float32)
    for points, closed in polylines:
        pairs = list(zip(points, points[1:]))
        if closed:
            pairs.append((points[-1], points[0]))
        for start, end in pairs:
            dx = end.x - start.x
            dy = end.y - start.y
            length_sq = max(1e-9, dx * dx + dy * dy)
            t = np.clip(((world_x - start.x) * dx + (world_y - start.y) * dy) / length_sq, 0.0, 1.0)
            distance = np.hypot(world_x - (start.x + dx * t), world_y - (start.y + dy * t))
            result = np.minimum(result, distance)
    return result


def make_atlas() -> bpy.types.Image:
    source_image = bpy.data.images.load(str(MESA_SOURCE), check_existing=False)
    pixels = np.empty(source_image.size[0] * source_image.size[1] * 4, dtype=np.float32)
    source_image.pixels.foreach_get(pixels)
    source = pixels.reshape(source_image.size[1], source_image.size[0], 4)

    top_start = int(ATLAS_SIZE * CLIFF_V_MAX)
    top_height = ATLAS_SIZE - top_start
    axis_x = np.linspace(-30.0, 30.0, ATLAS_SIZE, dtype=np.float32)
    axis_y = np.linspace(-30.0, 30.0, top_height, dtype=np.float32)
    world_x, world_y = np.meshgrid(axis_x, axis_y)
    radius = np.hypot(world_x, world_y)

    tiled_a = bilinear_sample(source, np.mod(world_x / 12.5 + world_y / 31.0 + 0.19, 1.0), np.mod(world_y / 12.0 - world_x / 27.0 + 0.37, 1.0))
    tiled_b = bilinear_sample(source, np.mod(world_x / 21.0 - world_y / 37.0 + 0.63, 1.0), np.mod(world_y / 19.0 + world_x / 33.0 + 0.11, 1.0))
    rgb = tiled_a * 0.76 + tiled_b * 0.24
    warm_earth = np.array([0.47, 0.305, 0.145], dtype=np.float32)
    rgb = rgb * 0.91 + warm_earth[None, None, :] * 0.09
    broad = 0.035 * np.sin(world_x * 0.15 + world_y * 0.05) + 0.020 * np.cos(world_y * 0.21 - world_x * 0.08)
    rgb = np.clip(rgb + broad[:, :, None], 0.035, 0.94)

    routes = [(RING_ROUTE, True), *[(route, False) for route in CANONICAL_ROUTES.values()]]
    road_distance = distance_field(world_x, world_y, routes)
    road = np.exp(-((road_distance / 0.68) ** 4))
    enamel_road = np.array([0.46, 0.31, 0.18], dtype=np.float32)
    rgb = rgb * (1.0 - road[:, :, None] * 0.10) + enamel_road[None, None, :] * road[:, :, None] * 0.10

    wash_center = -14.8 - world_y * 0.11
    wash = np.exp(-(((world_x - wash_center) / 2.25) ** 2)) * np.clip((radius - 7.0) / 10.0, 0.0, 1.0)
    wash_ripple = 0.5 + 0.5 * np.sin(world_y * 1.35 + world_x * 0.18)
    rgb *= 1.0 - (wash * (0.075 + wash_ripple * 0.035))[:, :, None]

    vein_distance = distance_field(world_x, world_y, [(list(points), False) for points in STARSTONE_VEINS])
    vein_shadow = np.exp(-((vein_distance / 0.25) ** 2))
    vein_core = np.exp(-((vein_distance / 0.052) ** 2))
    rgb *= 1.0 - vein_shadow[:, :, None] * 0.21
    teal = np.array([0.09, 0.40, 0.38], dtype=np.float32)
    rgb = rgb * (1.0 - vein_core[:, :, None] * 0.48) + teal[None, None, :] * vein_core[:, :, None] * 0.48

    hash_noise = np.mod(np.sin(world_x * 12.9898 + world_y * 78.233) * 43758.5453, 1.0)
    flecks = ((hash_noise > 0.9981) & (radius > 9.5) & (radius < 21.5)).astype(np.float32)
    rgb = rgb * (1.0 - flecks[:, :, None] * 0.58) + teal[None, None, :] * flecks[:, :, None] * 0.58

    rear_cap = np.clip((-world_y - 11.0) / 7.0, 0.0, 1.0)
    rgb *= (1.0 - rear_cap[:, :, None] * 0.06)
    edge = np.clip((radius - 18.5) / 9.0, 0.0, 1.0)
    rgb *= 1.0 - edge[:, :, None] * 0.14
    rgb = np.clip(rgb * 1.035 + 0.008, 0.025, 0.96)

    atlas_pixels = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    atlas_pixels[top_start:, :, :3] = rgb

    cliff_y = np.linspace(0.0, 1.0, top_start, dtype=np.float32)[:, None]
    cliff_x = np.linspace(0.0, math.tau, ATLAS_SIZE, dtype=np.float32)[None, :]
    cliff_base = np.array([0.29, 0.145, 0.055], dtype=np.float32)
    bands = (
        0.035 * np.sin(cliff_y * 9.0 * math.pi + 1.1 * np.sin(cliff_x * 3.0))
        + 0.017 * np.sin(cliff_y * 23.0 * math.pi + cliff_x * 5.0)
    )
    cuts = -0.025 * np.abs(np.sin(cliff_x * 17.0 + cliff_y * 7.0)) ** 7
    cliff_rgb = np.clip(cliff_base[None, None, :] + (bands + cuts)[:, :, None] + cliff_y[:, :, None] * 0.15, 0.045, 0.61)
    atlas_pixels[:top_start, :, :3] = cliff_rgb

    atlas = bpy.data.images.new("MesaTownPaintedAtlas", ATLAS_SIZE, ATLAS_SIZE, alpha=False)
    atlas.colorspace_settings.name = "sRGB"
    atlas.pixels.foreach_set(atlas_pixels.ravel())
    atlas.filepath_raw = str(TEMP_ATLAS)
    atlas.file_format = "PNG"
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.image_settings.color_mode = "RGB"
    bpy.context.scene.render.image_settings.color_depth = "8"
    atlas.save()
    atlas.pack()
    TEMP_ATLAS.unlink(missing_ok=True)
    return atlas


def make_material(atlas: bpy.types.Image) -> bpy.types.Material:
    material = bpy.data.materials.new("MesaTownPaintedMaterial")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = atlas
    texture.projection = "FLAT"
    texture.extension = "REPEAT"
    texture.interpolation = "Linear"
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Roughness"].default_value = 0.92
    shader.inputs["Emission Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    shader.inputs["Emission Strength"].default_value = 0.0
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def top_uv(x: float, y: float) -> tuple[float, float]:
    return ((x + 30.0) / 60.0, CLIFF_V_MAX + ((y + 30.0) / 60.0) * (1.0 - CLIFF_V_MAX))


def build_plate(material: bpy.types.Material) -> bpy.types.Object:
    vertices: list[tuple[float, float, float]] = [(0.0, 0.0, terrain_height(0.0, 0.0))]
    for ring in range(1, RINGS + 1):
        fraction = ring / RINGS
        for segment in range(SEGMENTS):
            angle = segment / SEGMENTS * math.tau
            radius = boundary_radius(angle) * fraction
            x = math.cos(angle) * radius
            y = math.sin(angle) * radius
            vertices.append((x, y, terrain_height(x, y)))

    faces: list[tuple[int, ...]] = []
    uv_faces: list[list[tuple[float, float]]] = []
    first_ring = 1
    for segment in range(SEGMENTS):
        current = first_ring + segment
        following = first_ring + (segment + 1) % SEGMENTS
        faces.append((0, current, following))
        uv_faces.append([top_uv(*vertices[index][:2]) for index in faces[-1]])

    for ring in range(1, RINGS):
        inner = 1 + (ring - 1) * SEGMENTS
        outer = 1 + ring * SEGMENTS
        for segment in range(SEGMENTS):
            next_segment = (segment + 1) % SEGMENTS
            face = (inner + segment, outer + segment, outer + next_segment, inner + next_segment)
            faces.append(face)
            uv_faces.append([top_uv(*vertices[index][:2]) for index in face])

    top_face_count = len(faces)
    outer_start = 1 + (RINGS - 1) * SEGMENTS
    mid_start = len(vertices)
    for segment in range(SEGMENTS):
        angle = segment / SEGMENTS * math.tau
        radius = boundary_radius(angle) + 0.82 + 0.14 * math.sin(angle * 5.0 + 0.2)
        height = CLIFF_MID_HEIGHT + 0.16 * math.sin(angle * 4.0 - 0.3)
        vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, height))
    foot_start = len(vertices)
    for segment in range(SEGMENTS):
        angle = segment / SEGMENTS * math.tau
        radius = boundary_radius(angle) + 2.55 + 0.22 * math.sin(angle * 6.0 + 0.4)
        height = CLIFF_FOOT_HEIGHT + 0.13 * math.sin(angle * 5.0 + 0.7)
        vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, height))
    apron_start = len(vertices)
    for segment in range(SEGMENTS):
        angle = segment / SEGMENTS * math.tau
        radius = boundary_radius(angle) + 5.35 + 0.28 * math.sin(angle * 4.0 - 0.5)
        height = APRON_HEIGHT + 0.11 * math.sin(angle * 7.0 + 0.1)
        vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, height))
    bottom_start = len(vertices)
    for segment in range(SEGMENTS):
        angle = segment / SEGMENTS * math.tau
        radius = boundary_radius(angle) + 5.35 + 0.28 * math.sin(angle * 4.0 - 0.5)
        bottom = BOTTOM_HEIGHT + 0.08 * math.sin(angle * 7.0 + 0.1)
        vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, bottom))

    def connect_rings(inner_start: int, outer_ring_start: int, inner_v: float, outer_v: float, use_top_uv: bool = False) -> None:
        for segment in range(SEGMENTS):
            next_segment = (segment + 1) % SEGMENTS
            face = (inner_start + segment, outer_ring_start + segment, outer_ring_start + next_segment, inner_start + next_segment)
            faces.append(face)
            if use_top_uv:
                uv_faces.append([top_uv(*vertices[index][:2]) for index in face])
            else:
                u0 = segment / SEGMENTS
                u1 = (segment + 1) / SEGMENTS
                uv_faces.append([(u0, inner_v), (u0, outer_v), (u1, outer_v), (u1, inner_v)])

    connect_rings(outer_start, mid_start, CLIFF_V_MAX, 0.095)
    connect_rings(mid_start, foot_start, 0.095, 0.018)
    connect_rings(foot_start, apron_start, CLIFF_V_MAX + 0.015, CLIFF_V_MAX + 0.015, use_top_uv=True)
    for segment in range(SEGMENTS):
        next_segment = (segment + 1) % SEGMENTS
        face = (apron_start + segment, bottom_start + segment, bottom_start + next_segment, apron_start + next_segment)
        faces.append(face)
        u0 = segment / SEGMENTS
        u1 = (segment + 1) / SEGMENTS
        uv_faces.append([(u0, 0.018), (u0, 0.0), (u1, 0.0), (u1, 0.018)])

    mesh = bpy.data.meshes.new("MesaTownPlateMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    plate = bpy.data.objects.new("MesaTownPlate", mesh)
    bpy.context.collection.objects.link(plate)
    mesh.materials.append(material)
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for polygon, face_uvs in zip(mesh.polygons, uv_faces):
        polygon.use_smooth = polygon.index < top_face_count
        for loop_index, uv in zip(polygon.loop_indices, face_uvs):
            uv_layer.data[loop_index].uv = uv
    plate["layout_owner"] = "src/town/townLayout.ts"
    plate["site_chain"] = "E6-E7 glow mesa"
    plate["base_sha"] = BASE_SHA
    plate["flat_walk_law"] = "canonical routes, plaza, and inherited pads stay within +/-0.05m"
    plate["premium_sites"] = ",".join(site.id for site in PREMIUM_SITES)
    return plate


def select_only(objects: list[bpy.types.Object]) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]


def save_and_export(plate: bpy.types.Object) -> None:
    select_only([plate])
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.export_scene.gltf(
        filepath=str(GLB),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_materials="EXPORT",
    )


def import_massing() -> list[bpy.types.Object]:
    model_paths = {
        "tavern": ROOT / "assets/pilots/tavern-3d/town-v3-tavern.glb",
        "general_store": ROOT / "assets/pilots/general-store-3d/general-store.glb",
        "claim_office": ROOT / "assets/pilots/claim-office-3d/claim-office.glb",
        "assay_office": ROOT / "assets/pilots/assay-office-3d/assay-office.glb",
        "chapel": ROOT / "assets/pilots/chapel-3d/chapel.glb",
        "schoolhouse": ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.glb",
        "stamp-mill": ROOT / "assets/pilots/stamp-mill-3d/stamp-mill.glb",
        "dynamo-hall": ROOT / "assets/pilots/dynamo-hall-3d/dynamo-hall.glb",
    }
    roots = []
    for slot in CANONICAL_SLOTS:
        roots.append(town.import_model(model_paths[slot.id], f"EvidenceMassing:{slot.id}", slot.position, town.slot_angle(slot)))
    pan = ROOT / "assets/pilots/plaza-props-3d/pan_monument.glb"
    roots.append(town.import_model(pan, "EvidenceHeritage:pan_monument", Point(0.0, 0.0)))
    return roots


def setup_render_scene() -> bpy.types.Object:
    camera = town.setup_render_scene()
    scene = bpy.context.scene
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.49, 0.34, 0.19, 1.0)
    background.inputs["Strength"].default_value = 0.9
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera.location = (0.0, 35.0, 43.5)
    camera.data.lens = camera.data.sensor_height / (2.0 * math.tan(math.radians(47.0) * 0.5))
    town.look_at(camera, Vector((0.0, -2.4, -0.45)))
    return camera


def curve3d(name: str, points: list[tuple[float, float, float]], material: bpy.types.Material, closed: bool, bevel: float = 0.085) -> bpy.types.Object:
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = bevel
    curve.bevel_resolution = 1
    polyline = curve.splines.new("POLY")
    polyline.points.add(len(points) - 1)
    for control, point in zip(polyline.points, points):
        control.co = (*point, 1.0)
    polyline.use_cyclic_u = closed
    curve.materials.append(material)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    return obj


def pad_points(slot: Slot, z: float = 0.11) -> list[tuple[float, float, float]]:
    return [(point.x, point.y, z) for point in town.pad_outline(slot)]


def premium_outline(site: PremiumSite) -> list[tuple[float, float, float]]:
    z = site.height + 0.13
    if site.shape == "circle":
        return [
            (site.position.x + math.cos(index / 48.0 * math.tau) * site.width * 0.5,
             site.position.y + math.sin(index / 48.0 * math.tau) * site.width * 0.5, z)
            for index in range(48)
        ]
    return [
        (site.position.x - site.width * 0.5, site.position.y - site.depth * 0.5, z),
        (site.position.x + site.width * 0.5, site.position.y - site.depth * 0.5, z),
        (site.position.x + site.width * 0.5, site.position.y + site.depth * 0.5, z),
        (site.position.x - site.width * 0.5, site.position.y + site.depth * 0.5, z),
    ]


def add_overlay() -> list[bpy.types.Object]:
    route_material = town.emission_material("CanonicalFlatWalk", (0.06, 0.75, 0.74, 1.0), 1.7)
    pad_material = town.emission_material("CanonicalFlatPads", (1.0, 0.53, 0.08, 1.0), 1.4)
    candidate_material = town.emission_material("CandidatePremiumSites", (0.74, 0.18, 0.82, 1.0), 1.5)
    ramp_material = town.emission_material("MesaAccessGrade", (0.38, 0.88, 0.20, 1.0), 1.4)
    overlays = [curve3d("Canonical:ring-road", [(p.x, p.y, 0.10) for p in RING_ROUTE], route_material, True)]
    overlays.extend(curve3d(f"Canonical:{name}", [(p.x, p.y, 0.10) for p in points], route_material, False) for name, points in CANONICAL_ROUTES.items())
    overlays.extend(curve3d(f"CanonicalPad:{slot.id}", pad_points(slot), pad_material, True) for slot in CANONICAL_SLOTS)
    overlays.extend(curve3d(f"Candidate:{site.id}", premium_outline(site), candidate_material, True) for site in PREMIUM_SITES)
    overlays.extend(
        curve3d(
            f"MesaAccess:{name}",
            [(point.x, point.y, terrain_height(point.x, point.y) + 0.12) for point in points],
            ramp_material,
            False,
        )
        for name, points in MESA_ACCESS_PATHS.items()
    )
    return overlays


def render_scene(plate_path: Path, path: Path, overlay: bool = False, angle: float | None = None) -> None:
    reset_scene()
    town.import_model(plate_path, "EvidencePlate", Point(0.0, 0.0))
    import_massing()
    camera = setup_render_scene()
    if angle is not None:
        radius = 52.0
        camera.location = (math.sin(angle) * radius, math.cos(angle) * radius, 36.5)
        town.look_at(camera, Vector((0.0, -2.4, -0.55)))
    if overlay:
        add_overlay()
    town.render(path)


def annotate(path: Path, label: str) -> None:
    temporary = path.with_name(f".{path.name}")
    subprocess.run(
        [
            "magick", str(path), "-font", "/System/Library/Fonts/Helvetica.ttc",
            "-background", "#17120d", "-gravity", "north", "-splice", "0x28",
            "-fill", "#f7df9d", "-pointsize", "14", "-annotate", "+0+7",
            f"{label} | base {BASE_SHA}", str(temporary),
        ],
        check=True,
    )
    temporary.replace(path)


def assemble_ab(left: Path, right: Path, output: Path, label: str) -> None:
    subprocess.run(["magick", str(left), str(right), "+append", str(output)], check=True)
    annotate(output, label)


def assemble_turntable(paths: list[Path], output: Path) -> None:
    subprocess.run(
        ["magick", "montage", "-font", "/System/Library/Fonts/Helvetica.ttc", *[str(path) for path in paths], "-tile", "2x2", "-geometry", "+0+0", str(output)],
        check=True,
    )
    annotate(output, "MESA PLATE FOUR-ANGLE MASSING | E1 MODELS ARE SCALE PROXIES ONLY")


def mesh_triangles(obj: bpy.types.Object) -> int:
    return sum(max(0, len(polygon.vertices) - 2) for polygon in obj.data.polygons)


def write_contract(triangles: int) -> None:
    contract = {
        "baseSha": BASE_SHA,
        "siteChain": "E6-E7 glow mesa",
        "status": "plate pilot; premium sites proposed for attended verdict before E6 building production",
        "sources": {
            "layout": str(town.LAYOUT_SOURCE.relative_to(ROOT)),
            "layoutSha256": sha256(town.LAYOUT_SOURCE),
            "stampFootprint": str(town.TOWN_SCENE_SOURCE.relative_to(ROOT)),
            "dynamoFootprint": str(town.DYNAMO_SOURCE.relative_to(ROOT)),
            "mesaTexture": str(MESA_SOURCE.relative_to(ROOT)),
            "mesaTextureSha256": sha256(MESA_SOURCE),
            "e6Bundle": str(E6_BUNDLE.relative_to(ROOT)),
            "e6BundleSha256": sha256(E6_BUNDLE),
        },
        "production": {
            "blend": str(BLEND.relative_to(ROOT)),
            "glb": str(GLB.relative_to(ROOT)),
            "glbSha256": sha256(GLB),
            "triangles": triangles,
            "triangleBudget": TRIANGLE_BUDGET,
            "atlas": [ATLAS_SIZE, ATLAS_SIZE],
            "materialCount": 1,
        },
        "canonicalSlots": [
            {
                "id": slot.id,
                "position": [slot.position.x, slot.position.y],
                "approach": [slot.approach.x, slot.approach.y],
                "footprint": [slot.width, slot.depth],
                "targetHeight": 0.0,
            }
            for slot in CANONICAL_SLOTS
        ],
        "premiumSiteCandidates": [
            {
                "id": site.id,
                "position": [site.position.x, site.position.y],
                "shape": site.shape,
                "footprint": [site.width, site.depth],
                "targetHeight": site.height,
                "role": site.role,
            }
            for site in PREMIUM_SITES
        ],
        "mesaAccessPaths": {name: [[point.x, point.y] for point in points] for name, points in MESA_ACCESS_PATHS.items()},
        "laws": {
            "canonicalFlatWalk": PATH_RELIEF_LIMIT,
            "plazaCenterOpen": PLAZA_CLEAR_RADIUS,
            "panMonument": "heritage asset stays independently mounted at canonical center; not duplicated in plate GLB",
            "freshSite": "no drowned-square geometry, water surface, E2-E5 street hardware, buildings, or people",
        },
    }
    (ARTIFACTS / "mesa-town-layout-contract.json").write_text(json.dumps(contract, indent=2) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    reset_scene()
    atlas = make_atlas()
    material = make_material(atlas)
    plate = build_plate(material)
    triangles = mesh_triangles(plate)
    if triangles > TRIANGLE_BUDGET:
        raise RuntimeError(f"Mesa Town plate exceeds {TRIANGLE_BUDGET} triangles: {triangles}")
    save_and_export(plate)
    write_contract(triangles)

    baseline = RENDERS / "current-square-massing.png"
    candidate = RENDERS / "mesa-town-plate-camera.png"
    overlay = RENDERS / "mesa-town-flat-walk-overlay.png"
    render_scene(CURRENT_PLATE, baseline)
    render_scene(GLB, candidate)
    render_scene(GLB, overlay, overlay=True)
    assemble_ab(baseline, candidate, RENDERS / "mesa-town-current-vs-pilot-ab.png", "CURRENT SQUARE / E6-E7 MESA PILOT | SAME CAMERA AND MASSING")
    annotate(candidate, "MESA TOWN PLATE PILOT | E1 MODELS ARE SCALE PROXIES ONLY")
    annotate(overlay, "FLAT-WALK PROOF | TEAL ROUTES | ORANGE CANON PADS | VIOLET CANDIDATES | GREEN RAMPS")

    angles = [0.0, math.pi * 0.5, math.pi, math.pi * 1.5]
    turntable_paths = []
    for index, angle in enumerate(angles):
        path = RENDERS / f"mesa-town-angle-{index + 1}.png"
        render_scene(GLB, path, angle=angle)
        turntable_paths.append(path)
    assemble_turntable(turntable_paths, RENDERS / "mesa-town-turntable.png")

    print(json.dumps({
        "baseSha": BASE_SHA,
        "blend": str(BLEND),
        "glb": str(GLB),
        "sha256": sha256(GLB),
        "triangles": triangles,
        "atlas": [ATLAS_SIZE, ATLAS_SIZE],
        "premiumSiteCandidates": [site.id for site in PREMIUM_SITES],
        "renders": [str(path) for path in [candidate, overlay, RENDERS / "mesa-town-current-vs-pilot-ab.png", RENDERS / "mesa-town-turntable.png"]],
    }, indent=2))


if __name__ == "__main__":
    main()
