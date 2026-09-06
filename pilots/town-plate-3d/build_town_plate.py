from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import math
import re
import sys

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/town-plate-3d"
RENDERS = OUT / "renders"
LAYOUT_SOURCE = ROOT / "src/town/townLayout.ts"
TOWN_SCENE_SOURCE = ROOT / "src/town/TownScene.ts"
DYNAMO_SOURCE = ROOT / "assets/contracts/epoch-2-steamworks/manifest.json"
PAINTED_GROUND = ROOT / "assets/raw/ter-plaza-ground.png"
BLEND = OUT / "town-plate.blend"
GLB = OUT / "town-plate.glb"
TEMP_ATLAS = OUT / ".town-plate-atlas.png"

ATLAS_SIZE = 2048
HALF_EXTENT = 22.0
GRID_CELLS = 64
GRID_STEP = (HALF_EXTENT * 2.0) / GRID_CELLS
PLAZA_CLEAR_RADIUS = 3.1
PATH_SAFE_RADIUS = 1.05
PATH_RELIEF_LIMIT = 0.05
GROUND_UV_MAX = 0.915
DECOR_PALETTE_V_START = 0.93
DECOR_PALETTE_COLUMNS = 4
DECOR_PALETTE = (
    (0.16, 0.065, 0.022),  # dark timber
    (0.36, 0.15, 0.045),   # timber
    (0.57, 0.29, 0.085),   # sun-warmed timber
    (0.08, 0.30, 0.29),    # restrained teal
    (0.63, 0.35, 0.075),   # brass
    (0.82, 0.56, 0.18),    # warm gold
    (0.29, 0.21, 0.14),    # dark stone / iron
    (0.56, 0.43, 0.28),    # warm stone
    (0.72, 0.56, 0.33),    # canvas / sack
    (0.095, 0.075, 0.055), # iron
    (0.49, 0.15, 0.055),   # painted red
    (0.19, 0.34, 0.13),    # scrub green
    (0.73, 0.41, 0.13),    # flower orange
    (0.50, 0.18, 0.16),    # flower red
    (0.78, 0.70, 0.52),    # chalk / linen
    (0.045, 0.13, 0.14),   # teal shadow
)


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class Slot:
    id: str
    position: Point
    approach: Point
    width: float
    depth: float


@dataclass(frozen=True)
class Prop:
    id: str
    kind: str
    position: Point
    rotation: float
    scale: float


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_layout() -> tuple[list[Slot], list[Prop]]:
    text = LAYOUT_SOURCE.read_text()
    slots_block = text.split("slots: [", 1)[1].split("],\n  actorOffsets", 1)[0]
    raw_slots: dict[str, tuple[Point, Point]] = {}
    slot_pattern = re.compile(
        r"\{ id: '([^']+)', position: \{ x: ([-\d.]+), z: ([-\d.]+) \}, "
        r"approach: \{ x: ([-\d.]+), z: ([-\d.]+) \} \}",
    )
    for match in slot_pattern.finditer(slots_block):
        raw_slots[match.group(1)] = (
            Point(float(match.group(2)), float(match.group(3))),
            Point(float(match.group(4)), float(match.group(5))),
        )

    buildings_block = text.split("export const townBuildings", 1)[1].split("as const;", 1)[0]
    footprints = {
        match.group(1): (float(match.group(2)), float(match.group(3)))
        for match in re.finditer(
            r"id: '([^']+)'[\s\S]*?footprint: \{ w: ([-\d.]+), d: ([-\d.]+) \}",
            buildings_block,
        )
    }
    stamp_match = re.search(
        r"STAMP_MILL_TOWN_SITE = \{ \.\.\.townPlazaSlot\('stamp-mill'\)\.position, w: ([-\d.]+), d: ([-\d.]+) \}",
        TOWN_SCENE_SOURCE.read_text(),
    )
    if not stamp_match:
        raise RuntimeError("Could not read the canonical Stamp Mill footprint")
    footprints["stamp-mill"] = (float(stamp_match.group(1)), float(stamp_match.group(2)))

    slots = [
        Slot(slot_id, position, approach, *footprints[slot_id])
        for slot_id, (position, approach) in raw_slots.items()
    ]
    if len(slots) != 7:
        raise RuntimeError(f"Expected seven Town slots, parsed {len(slots)}")

    props_block = text.split("props: [", 1)[1].split("] satisfies readonly TownPropDescriptor[]", 1)[0]
    prop_pattern = re.compile(
        r"\{ id: '([^']+)', kind: '([^']+)', position: \{ x: ([-\d.]+), z: ([-\d.]+) \}, "
        r"rotation: ([-\d.]+)(?:, scale: ([-\d.]+))? \}",
    )
    props = [
        Prop(
            match.group(1),
            match.group(2),
            Point(float(match.group(3)), float(match.group(4))),
            float(match.group(5)),
            float(match.group(6) or 1.0),
        )
        for match in prop_pattern.finditer(props_block)
    ]
    props.append(Prop("pan_monument", "pan_monument", Point(0.0, 0.0), 0.0, 1.0))
    if len(props) != 18:
        raise RuntimeError(f"Expected seventeen prop descriptors plus Pan Monument, parsed {len(props)}")
    return slots, props


def read_dynamo_slot() -> Slot:
    document = json.loads(DYNAMO_SOURCE.read_text())
    manifest = next(item for item in document["megaprojects"] if item["id"] == "dynamo-hall")
    site = manifest["siteFootprint"]
    position = Point(float(site["x"]), float(site["z"]))
    return Slot("dynamo-hall", position, Point(position.x, position.y - 3.0), float(site["w"]), float(site["d"]))


SLOTS, PROPS = parse_layout()
DYNAMO_SLOT = read_dynamo_slot()


def quadratic_point(start: Point, control: Point, end: Point, t: float) -> Point:
    return Point(
        (1 - t) ** 2 * start.x + 2 * (1 - t) * t * control.x + t**2 * end.x,
        (1 - t) ** 2 * start.y + 2 * (1 - t) * t * control.y + t**2 * end.y,
    )


def radial_trail(destination: Point, index: int) -> list[Point]:
    start = Point(0.0, 0.0)
    dx = destination.x
    dy = destination.y
    length = max(1.0, math.hypot(dx, dy))
    bend = (1.0 if index % 2 == 0 else -1.0) * 0.34
    control = Point(
        destination.x * 0.5 + (-dy / length) * bend,
        destination.y * 0.5 + (dx / length) * bend,
    )
    return [quadratic_point(start, control, destination, point_index / 6.0) for point_index in range(7)]


RADIAL_ROUTES = {
    slot.id: radial_trail(slot.approach, index)
    for index, slot in enumerate(SLOTS)
}
RADIAL_ROUTES["gate"] = radial_trail(Point(0.0, 14.5), len(SLOTS))
RING_ROUTE = [
    Point(math.sin(index / 16.0 * math.tau) * 6.0, math.cos(index / 16.0 * math.tau) * 6.0)
    for index in range(16)
]


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 1.0 if value >= edge1 else 0.0
    t = min(1.0, max(0.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def distance_to_segment(x: float, y: float, start: Point, end: Point) -> float:
    dx = end.x - start.x
    dy = end.y - start.y
    length_sq = dx * dx + dy * dy
    if length_sq <= 1e-12:
        return math.hypot(x - start.x, y - start.y)
    t = min(1.0, max(0.0, ((x - start.x) * dx + (y - start.y) * dy) / length_sq))
    return math.hypot(x - (start.x + dx * t), y - (start.y + dy * t))


def distance_to_polyline(x: float, y: float, points: list[Point], closed: bool = False) -> float:
    pairs = list(zip(points, points[1:]))
    if closed:
        pairs.append((points[-1], points[0]))
    return min(distance_to_segment(x, y, start, end) for start, end in pairs)


def route_distance(x: float, y: float) -> float:
    radial = min(distance_to_polyline(x, y, route) for route in RADIAL_ROUTES.values())
    ring = abs(math.hypot(x, y) - 6.0)
    return min(radial, ring)


def slot_angle(slot: Slot) -> float:
    return math.atan2(slot.approach.x - slot.position.x, slot.approach.y - slot.position.y)


def rectangle_outside_distance(x: float, y: float, slot: Slot, margin: float = 0.0) -> float:
    theta = slot_angle(slot)
    dx = x - slot.position.x
    dy = y - slot.position.y
    local_x = math.cos(theta) * dx - math.sin(theta) * dy
    local_y = math.sin(theta) * dx + math.cos(theta) * dy
    outside_x = max(0.0, abs(local_x) - slot.width * 0.5 - margin)
    outside_y = max(0.0, abs(local_y) - slot.depth * 0.5 - margin)
    return math.hypot(outside_x, outside_y)


def prop_radius(prop: Prop) -> float:
    base = {
        "covered_wagon": 1.35,
        "fence": 0.72,
        "cactus": 0.48,
        "water_trough": 1.0,
        "lantern_post": 0.38,
        "pony_express_plot": 1.7,
        "pan_monument": 0.78,
    }[prop.kind]
    return base * prop.scale


def flat_feature_mask(x: float, y: float) -> float:
    path_mask = smoothstep(PATH_SAFE_RADIUS, PATH_SAFE_RADIUS + 0.9, route_distance(x, y))
    center_mask = smoothstep(PLAZA_CLEAR_RADIUS, PLAZA_CLEAR_RADIUS + 0.8, math.hypot(x, y))
    mask = min(path_mask, center_mask)
    for slot in [*SLOTS, DYNAMO_SLOT]:
        mask = min(mask, smoothstep(0.0, 0.85, rectangle_outside_distance(x, y, slot, margin=0.45)))
    for prop in PROPS:
        distance = math.hypot(x - prop.position.x, y - prop.position.y)
        mask = min(mask, smoothstep(prop_radius(prop), prop_radius(prop) + 0.6, distance))
    return mask


def pad_mask(x: float, y: float) -> float:
    mask = 1.0
    for slot in [*SLOTS, DYNAMO_SLOT]:
        mask = min(mask, smoothstep(0.0, 0.5, rectangle_outside_distance(x, y, slot, margin=GRID_STEP * 1.25)))
    for prop in PROPS:
        distance = math.hypot(x - prop.position.x, y - prop.position.y)
        mask = min(mask, smoothstep(prop_radius(prop) + GRID_STEP * 0.8, prop_radius(prop) + GRID_STEP * 1.5, distance))
    return mask


def terrain_height(x: float, y: float) -> float:
    radius = math.hypot(x, y)
    inner_relief = (
        0.24 * math.sin(x * 0.43 + y * 0.17)
        + 0.15 * math.cos(y * 0.51 - x * 0.13)
        + 0.07 * math.sin((x + y) * 0.91)
    ) * smoothstep(3.7, 9.0, radius)
    side_berm = 0.58 * smoothstep(15.2, 21.5, abs(x))
    outer_undulation = smoothstep(14.0, 21.5, max(abs(x), abs(y))) * (
        0.24 * math.sin(x * 0.24 + y * 0.08) + 0.13 * math.cos(y * 0.3 - x * 0.07)
    )
    riverbank = -1.34 * smoothstep(15.2, 19.6, -y)
    bank_lip = 0.18 * math.exp(-(((-y - 15.35) / 0.72) ** 2))
    base = (inner_relief + side_berm + outer_undulation + riverbank + bank_lip) * flat_feature_mask(x, y)

    path_distance = route_distance(x, y)
    wagon_bed = -0.007 * math.exp(-((path_distance / 0.58) ** 4))
    wheel_ruts = -0.031 * math.exp(-(((path_distance - 0.34) / 0.13) ** 2))
    well_mound = 0.032 * math.exp(-(((radius - 1.32) / 0.42) ** 2))
    return (base + wagon_bed + wheel_ruts + well_mound) * pad_mask(x, y)


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0


def bilinear_sample(source: np.ndarray, u: np.ndarray, v: np.ndarray) -> np.ndarray:
    height, width, _ = source.shape
    fx = np.clip(u, 0.0, 1.0) * (width - 1)
    fy = np.clip(v, 0.0, 1.0) * (height - 1)
    x0 = np.floor(fx).astype(np.int32)
    y0 = np.floor(fy).astype(np.int32)
    x1 = np.minimum(width - 1, x0 + 1)
    y1 = np.minimum(height - 1, y0 + 1)
    tx = (fx - x0)[:, :, None]
    ty = (fy - y0)[:, :, None]
    top = source[y0, x0, :3] * (1.0 - tx) + source[y0, x1, :3] * tx
    bottom = source[y1, x0, :3] * (1.0 - tx) + source[y1, x1, :3] * tx
    return top * (1.0 - ty) + bottom * ty


def polyline_distance_field(
    world_x: np.ndarray,
    world_y: np.ndarray,
    points: list[Point],
    closed: bool,
) -> np.ndarray:
    result = np.full(world_x.shape, np.inf, dtype=np.float32)
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


def road_wear_masks(world_x: np.ndarray, world_y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # Vary width and opacity around the unchanged canonical centerlines. E4's
    # southern boulevard remains separate geometry and therefore reads above this
    # quieter inherited dirt network.
    angle = np.arctan2(world_x, world_y)
    ring_distance = polyline_distance_field(world_x, world_y, RING_ROUTE, True)
    ring_width = 0.70 + 0.11 * np.sin(angle * 3.0 - 0.35) + 0.05 * np.sin(angle * 7.0 + 0.8)
    ring_road = np.exp(-((ring_distance / ring_width) ** 2))
    ring_rut_offset = 0.33 + 0.025 * np.sin(angle * 5.0 + 0.5)
    ring_ruts = np.exp(-(((ring_distance - ring_rut_offset) / 0.105) ** 2))

    radial_road = np.zeros(world_x.shape, dtype=np.float32)
    radial_ruts = np.zeros(world_x.shape, dtype=np.float32)
    strengths = (0.88, 0.48, 0.22, 0.66, 0.30, 0.72, 0.26, 0.58)
    for index, points in enumerate(RADIAL_ROUTES.values()):
        distance = polyline_distance_field(world_x, world_y, points, False)
        phase = index * 0.83
        width = 0.46 + 0.16 * (0.5 + 0.5 * np.sin(world_x * 0.20 + world_y * 0.14 + phase))
        strength = strengths[index % len(strengths)]
        radial_road = np.maximum(radial_road, strength * np.exp(-((distance / width) ** 2)))
        rut_offset = 0.28 + 0.02 * np.sin(world_x * 0.16 - world_y * 0.11 + phase)
        radial_ruts = np.maximum(
            radial_ruts,
            strength * 0.82 * np.exp(-(((distance - rut_offset) / 0.105) ** 2)),
        )

    road = np.maximum(ring_road, radial_road)
    ruts = np.maximum(ring_ruts, radial_ruts)
    breakup = 0.88 + 0.12 * (
        0.5 + 0.5 * np.sin(world_x * 0.57 + world_y * 0.31) * np.cos(world_y * 0.41 - world_x * 0.18)
    )
    road *= breakup
    ruts *= 0.90 + 0.10 * np.sin(world_x * 0.44 - world_y * 0.27 + 1.1)

    local_wear = np.zeros(world_x.shape, dtype=np.float32)
    for point, spread in ((Point(0.0, 11.2), 2.4), (RING_ROUTE[5], 1.8), (RING_ROUTE[11], 2.0)):
        local_wear = np.maximum(
            local_wear,
            np.exp(-(((world_x - point.x) ** 2 + (world_y - point.y) ** 2) / (spread * spread))),
        )
    local_wear *= np.maximum(road * 0.72, ruts)
    return road, ruts, local_wear


def make_atlas() -> bpy.types.Image:
    source_image = bpy.data.images.load(str(PAINTED_GROUND), check_existing=False)
    source_pixels = np.empty(source_image.size[0] * source_image.size[1] * 4, dtype=np.float32)
    source_image.pixels.foreach_get(source_pixels)
    source = source_pixels.reshape(source_image.size[1], source_image.size[0], 4)

    axis = np.linspace(-HALF_EXTENT, HALF_EXTENT, ATLAS_SIZE, dtype=np.float32)
    world_x, world_y = np.meshgrid(axis, axis)
    radius = np.hypot(world_x, world_y)

    patch_size = min(source.shape[0], source.shape[1]) // 3
    quiet_a = source[:patch_size, :patch_size]
    quiet_b = source[-patch_size:, -patch_size:]
    sample_a = bilinear_sample(
        quiet_a,
        np.mod(world_x / 8.5 + world_y / 17.0 + 0.13, 1.0),
        np.mod(world_y / 8.5 - world_x / 19.0 + 0.31, 1.0),
    )
    sample_b = bilinear_sample(
        quiet_b,
        np.mod(world_x / 15.5 - world_y / 23.0 + 0.57, 1.0),
        np.mod(world_y / 14.0 + world_x / 21.0 + 0.19, 1.0),
    )
    painted_earth = sample_a * 0.64 + sample_b * 0.36

    edge = max(1, source.shape[0] // 11)
    edge_pixels = np.concatenate((
        source[:edge, :, :3].reshape(-1, 3),
        source[-edge:, :, :3].reshape(-1, 3),
        source[:, :edge, :3].reshape(-1, 3),
        source[:, -edge:, :3].reshape(-1, 3),
    ))
    earth = np.median(edge_pixels, axis=0) * 1.035
    broad = (
        0.031 * np.sin(world_x * 0.17 + world_y * 0.06)
        + 0.022 * np.cos(world_y * 0.23 - world_x * 0.09)
        + 0.013 * np.sin((world_x + world_y) * 0.71)
    )
    grain = 0.009 * np.sin(world_x * 2.1 + world_y * 0.9) * np.cos(world_y * 1.6 - world_x * 0.35)
    procedural_tint = np.clip(earth[None, None, :] + (broad + grain)[:, :, None], 0.04, 0.96)
    rgb = np.clip(painted_earth * 0.82 + procedural_tint * 0.18, 0.04, 0.96)
    civic = np.clip((radius - 3.2) / 8.0, 0.0, 1.0)
    rgb *= (0.035 * civic[:, :, None] + 1.015)

    road, ruts, local_wear = road_wear_masks(world_x, world_y)
    rgb *= (
        1.0
        - 0.076 * road[:, :, None]
        - 0.102 * ruts[:, :, None]
        - 0.060 * local_wear[:, :, None]
    )

    for slot in [*SLOTS, DYNAMO_SLOT]:
        theta = slot_angle(slot)
        dx = world_x - slot.position.x
        dy = world_y - slot.position.y
        local_x = np.abs(math.cos(theta) * dx - math.sin(theta) * dy)
        local_y = np.abs(math.sin(theta) * dx + math.cos(theta) * dy)
        outside_x = np.maximum(0.0, local_x - slot.width * 0.5)
        outside_y = np.maximum(0.0, local_y - slot.depth * 0.5)
        outside = np.hypot(outside_x, outside_y)
        inside = np.minimum(np.maximum(0.0, slot.width * 0.5 - local_x), np.maximum(0.0, slot.depth * 0.5 - local_y))
        boundary = np.where((outside_x == 0.0) & (outside_y == 0.0), inside, outside)
        collar = np.exp(-((boundary / 0.34) ** 2))
        rgb *= 1.0 - 0.055 * collar[:, :, None]

    water = np.clip((-world_y - 16.0) / 2.8, 0.0, 1.0)
    water_tint = np.array([0.22, 0.36, 0.35], dtype=np.float32)
    water_mix = water[:, :, None] * 0.62
    rgb = rgb * (1.0 - water_mix) + water_tint[None, None, :] * water_mix
    ripple = 1.0 + water * (0.018 * np.sin(world_x * 1.45 + world_y * 0.31))
    rgb *= ripple[:, :, None]
    shore = np.exp(-(((-world_y - 15.75) / 0.48) ** 2))
    rgb *= 1.0 - 0.18 * shore[:, :, None]
    rgb = np.clip(rgb * 1.035 + 0.006, 0.025, 0.97)

    atlas_pixels = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    atlas_pixels[:, :, :3] = rgb
    palette_start = int(ATLAS_SIZE * DECOR_PALETTE_V_START)
    palette_height = ATLAS_SIZE - palette_start
    palette_cell_width = ATLAS_SIZE // DECOR_PALETTE_COLUMNS
    palette_cell_height = max(1, palette_height // DECOR_PALETTE_COLUMNS)
    for index, color in enumerate(DECOR_PALETTE):
        column = index % DECOR_PALETTE_COLUMNS
        row = index // DECOR_PALETTE_COLUMNS
        x0 = column * palette_cell_width
        x1 = ATLAS_SIZE if column == DECOR_PALETTE_COLUMNS - 1 else (column + 1) * palette_cell_width
        y0 = palette_start + row * palette_cell_height
        y1 = ATLAS_SIZE if row == DECOR_PALETTE_COLUMNS - 1 else palette_start + (row + 1) * palette_cell_height
        atlas_pixels[y0:y1, x0:x1, :3] = color
    atlas = bpy.data.images.new("TownPlatePaintedAtlas", ATLAS_SIZE, ATLAS_SIZE, alpha=False)
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


def make_plate_material(atlas: bpy.types.Image) -> bpy.types.Material:
    material = bpy.data.materials.new("TownPlatePaintedMaterial")
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
    shader.inputs["Roughness"].default_value = 0.9
    shader.inputs["Emission Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    shader.inputs["Emission Strength"].default_value = 0.0
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def build_plate(material: bpy.types.Material) -> bpy.types.Object:
    coordinates = np.linspace(-HALF_EXTENT, HALF_EXTENT, GRID_CELLS + 1)
    vertices = [
        (float(x), float(y), terrain_height(float(x), float(y)))
        for y in coordinates
        for x in coordinates
    ]
    width = len(coordinates)
    faces = []
    for row in range(width - 1):
        for column in range(width - 1):
            a = row * width + column
            faces.append((a, a + 1, a + width + 1, a + width))

    mesh = bpy.data.meshes.new("TownPlateMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    plate = bpy.data.objects.new("TownPlate", mesh)
    bpy.context.collection.objects.link(plate)
    mesh.materials.append(material)
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            point = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            uv_layer.data[loop_index].uv = (
                (point.x + HALF_EXTENT) / (HALF_EXTENT * 2.0),
                (point.y + HALF_EXTENT) / (HALF_EXTENT * 2.0) * GROUND_UV_MAX,
            )
        polygon.use_smooth = False
    plate["layout_owner"] = "src/town/townLayout.ts"
    plate["flat_walk_law"] = "all routes and plaza center within +/-0.05m"
    plate["plate_extent_m"] = HALF_EXTENT * 2.0
    plate["grid_cells"] = GRID_CELLS
    return plate


@dataclass
class DecorCluster:
    id: str
    parcel: str
    x: float
    y: float
    rotation: float
    radius: float
    vocabulary: tuple[str, ...]
    ground: float

    def point(self, local_x: float, local_y: float, z: float) -> tuple[float, float, float]:
        cosine = math.cos(self.rotation)
        sine = math.sin(self.rotation)
        return (
            self.x + cosine * local_x - sine * local_y,
            self.y + sine * local_x + cosine * local_y,
            self.ground + z,
        )


DECOR_CLUSTERS: list[DecorCluster] = []
DECOR_PARTS: list[bpy.types.Object] = []


def decor_cluster(
    cluster_id: str,
    parcel: str,
    local_x: float,
    local_y: float,
    radius: float,
    vocabulary: tuple[str, ...],
) -> DecorCluster:
    slot = next(slot for slot in [*SLOTS, DYNAMO_SLOT] if slot.id == parcel)
    theta = slot_angle(slot)
    world_x = slot.position.x + math.cos(theta) * local_x + math.sin(theta) * local_y
    world_y = slot.position.y - math.sin(theta) * local_x + math.cos(theta) * local_y
    cluster = DecorCluster(
        cluster_id,
        parcel,
        world_x,
        world_y,
        -theta,
        radius,
        vocabulary,
        terrain_height(world_x, world_y),
    )
    DECOR_CLUSTERS.append(cluster)
    return cluster


def register_decor(
    obj: bpy.types.Object,
    cluster: DecorCluster,
    material: bpy.types.Material,
    palette_index: int,
) -> bpy.types.Object:
    obj.data.materials.append(material)
    obj["decor_cluster"] = cluster.id
    obj["palette_index"] = palette_index
    DECOR_PARTS.append(obj)
    return obj


def decor_box(
    cluster: DecorCluster,
    material: bpy.types.Material,
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    palette_index: int,
    rotation: float = 0.0,
    bevel: float = 0.025,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(
        location=cluster.point(*location),
        rotation=(0.0, 0.0, cluster.rotation + rotation),
    )
    obj = bpy.context.object
    obj.name = f"{cluster.id}:{name}"
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0.0:
        modifier = obj.modifiers.new("Painted edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
    return register_decor(obj, cluster, material, palette_index)


def decor_cylinder(
    cluster: DecorCluster,
    material: bpy.types.Material,
    name: str,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    palette_index: int,
    vertices: int = 10,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        location=cluster.point(*location),
        rotation=(rotation[0], rotation[1], cluster.rotation + rotation[2]),
    )
    obj = bpy.context.object
    obj.name = f"{cluster.id}:{name}"
    return register_decor(obj, cluster, material, palette_index)


def decor_sphere(
    cluster: DecorCluster,
    material: bpy.types.Material,
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    palette_index: int,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=cluster.point(*location))
    obj = bpy.context.object
    obj.name = f"{cluster.id}:{name}"
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return register_decor(obj, cluster, material, palette_index)


def decor_torus(
    cluster: DecorCluster,
    material: bpy.types.Material,
    name: str,
    location: tuple[float, float, float],
    major_radius: float,
    minor_radius: float,
    palette_index: int,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=12,
        minor_segments=5,
        location=cluster.point(*location),
        rotation=(rotation[0], rotation[1], cluster.rotation + rotation[2]),
    )
    obj = bpy.context.object
    obj.name = f"{cluster.id}:{name}"
    return register_decor(obj, cluster, material, palette_index)


def decor_beam(
    cluster: DecorCluster,
    material: bpy.types.Material,
    name: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    radius: float,
    palette_index: int,
    vertices: int = 8,
) -> bpy.types.Object:
    start_point = Vector(cluster.point(*start))
    end_point = Vector(cluster.point(*end))
    direction = end_point - start_point
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=direction.length,
        location=(start_point + end_point) * 0.5,
    )
    obj = bpy.context.object
    obj.name = f"{cluster.id}:{name}"
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return register_decor(obj, cluster, material, palette_index)


def add_barrel(cluster: DecorCluster, material: bpy.types.Material, x: float, y: float, scale: float = 1.0) -> None:
    decor_cylinder(cluster, material, "barrel body", (x, y, .32 * scale), .22 * scale, .64 * scale, 1, 10)
    for z in (.07, .31, .56):
        decor_torus(cluster, material, "barrel hoop", (x, y, z * scale), .225 * scale, .019 * scale, 9)
    decor_cylinder(cluster, material, "barrel lid", (x, y, .645 * scale), .18 * scale, .024 * scale, 2, 10)
    decor_beam(
        cluster,
        material,
        "barrel lid stave",
        (x - .15 * scale, y, .665 * scale),
        (x + .15 * scale, y, .665 * scale),
        .014 * scale,
        0,
        5,
    )


def add_bucket(cluster: DecorCluster, material: bpy.types.Material, x: float, y: float, scale: float = 1.0) -> None:
    decor_cylinder(cluster, material, "bucket", (x, y, .18 * scale), .17 * scale, .34 * scale, 6, 10)
    decor_torus(cluster, material, "bucket rim", (x, y, .35 * scale), .17 * scale, .016 * scale, 9)
    decor_torus(cluster, material, "bucket handle", (x, y, .39 * scale), .18 * scale, .012 * scale, 9, (math.pi / 2, 0, 0))


def add_crate(
    cluster: DecorCluster,
    material: bpy.types.Material,
    x: float,
    y: float,
    z: float = .23,
    size: float = .24,
) -> None:
    decor_box(cluster, material, "crate body", (x, y, z), (size, size, z), 2, bevel=.018)
    for offset in (-size * .72, size * .72):
        decor_box(cluster, material, "crate slat", (x + offset, y, z), (.030, size * 1.04, z * .92), 0, bevel=.006)


def add_sack(cluster: DecorCluster, material: bpy.types.Material, x: float, y: float, scale: float = 1.0) -> None:
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=12,
        ring_count=6,
        radius=1.0,
        location=cluster.point(x, y, .23 * scale),
    )
    body = bpy.context.object
    body.name = f"{cluster.id}:provision sack"
    body.scale = (.21 * scale, .16 * scale, .27 * scale)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    register_decor(body, cluster, material, 8)
    decor_cylinder(cluster, material, "cinched sack neck", (x, y, .49 * scale), .060 * scale, .12 * scale, 8, 8)
    decor_torus(cluster, material, "sack neck tie", (x, y, .44 * scale), .067 * scale, .012 * scale, 0)
    decor_beam(cluster, material, "sack tie", (x - .05 * scale, y, .45 * scale), (x + .05 * scale, y, .45 * scale), .014, 0, 6)


def add_rope_coil(cluster: DecorCluster, material: bpy.types.Material, x: float, y: float, scale: float = 1.0) -> None:
    for index in range(3):
        decor_torus(
            cluster,
            material,
            "rope coil",
            (x, y, .045 + index * .028),
            (.20 - index * .032) * scale,
            .025 * scale,
            (1, 8, 0)[index],
        )


def add_plank_stack(cluster: DecorCluster, material: bpy.types.Material, x: float, y: float, rotation: float = 0.0) -> None:
    for index in range(4):
        decor_box(
            cluster,
            material,
            "stacked plank",
            (x, y + (index % 2) * .08, .055 + index * .08),
            (.48, .085, .045),
            1 if index < 3 else 2,
            rotation=rotation + (index % 2) * .05,
            bevel=.012,
        )


def add_lantern_post(cluster: DecorCluster, material: bpy.types.Material, x: float, y: float, height: float = 1.30) -> None:
    decor_beam(cluster, material, "unlit lantern post", (x, y, .02), (x, y, height), .040, 0, 7)
    decor_beam(cluster, material, "lantern arm", (x, y, height), (x + .22, y, height), .030, 0, 7)
    decor_box(cluster, material, "lantern cage", (x + .24, y, height - .11), (.085, .085, .13), 4, bevel=.018)
    decor_box(cluster, material, "unlit teal panes", (x + .24, y, height - .11), (.060, .060, .09), 3, bevel=.010)


def add_planter(cluster: DecorCluster, material: bpy.types.Material, x: float, y: float) -> None:
    decor_box(cluster, material, "small planter", (x, y, .14), (.30, .21, .14), 1, bevel=.020)
    decor_box(cluster, material, "planter soil", (x, y, .28), (.26, .17, .020), 6, bevel=0.0)
    for index, offset in enumerate((-.16, 0.0, .16)):
        decor_beam(cluster, material, "flower stem", (x + offset, y, .28), (x + offset, y, .49 + .05 * (index % 2)), .012, 11, 5)
        decor_sphere(
            cluster,
            material,
            "painted flower",
            (x + offset, y, .52 + .05 * (index % 2)),
            (.05, .05, .04),
            12 if index % 2 == 0 else 13,
        )


def build_tavern_decor(material: bpy.types.Material) -> None:
    cluster = decor_cluster("tavern-workyard", "tavern", -3.68, -.20, .91, ("hitching-posts", "kegs", "bucket", "rope-coil", "feed-sack"))
    for y in (-.48, .48):
        decor_beam(cluster, material, "hitching post", (-.48, y, .02), (-.48, y, .80), .052, 0)
    decor_beam(cluster, material, "straight hitching rail", (-.48, -.53, .68), (-.48, .53, .68), .064, 1)
    for y in (-.28, .28):
        decor_torus(cluster, material, "brass tie ring", (-.48, y, .64), .075, .018, 4, (0, math.pi / 2, 0))
    add_rope_coil(cluster, material, -.54, -.46, .78)
    rope_loop = (
        (-.48, -.18, .66),
        (-.48, -.22, .46),
        (-.48, -.15, .28),
        (-.48, 0.0, .20),
        (-.48, .15, .28),
        (-.48, .22, .46),
        (-.48, .18, .66),
    )
    for index, (start, end) in enumerate(zip(rope_loop, rope_loop[1:])):
        decor_beam(cluster, material, f"hanging rope loop {index + 1}", start, end, .025, 8, 6)

    add_barrel(cluster, material, .20, -.34, .68)
    add_barrel(cluster, material, .20, 0, .72)
    add_barrel(cluster, material, .20, .34, .66)
    add_bucket(cluster, material, .48, .43, .70)
    add_sack(cluster, material, .48, -.43, .84)


def build_claim_decor(material: bpy.types.Material) -> None:
    cluster = decor_cluster("claim-notice-yard", "claim_office", 3.32, -.24, .90, ("notice-board", "crates", "rope-coils"))
    for x in (-.40, .40):
        decor_beam(cluster, material, "notice post", (x, .20, .02), (x, .20, 1.30), .042, 0, 7)
    decor_box(cluster, material, "pictogram notice board", (0, .20, .96), (.52, .055, .32), 1, bevel=.028)
    decor_beam(cluster, material, "crossed claim mark", (-.18, .13, .85), (.18, .13, 1.08), .022, 4, 6)
    decor_beam(cluster, material, "crossed claim mark", (-.18, .13, 1.08), (.18, .13, .85), .022, 4, 6)
    decor_cylinder(cluster, material, "round claim pictogram", (0, .13, .97), .085, .025, 3, 10, (math.pi / 2, 0, 0))
    add_crate(cluster, material, -.50, -.35, .22, .22)
    add_rope_coil(cluster, material, .42, -.35, .95)


def build_store_decor(material: bpy.types.Material) -> None:
    cluster = decor_cluster("store-delivery-yard", "general_store", 3.56, -.30, .94, ("crates", "sacks", "barrels", "planks"))
    add_crate(cluster, material, -.44, -.28, .25, .25)
    add_crate(cluster, material, -.36, -.22, .69, .20)
    add_sack(cluster, material, .20, -.33, .95)
    add_sack(cluster, material, .48, -.20, .76)
    add_barrel(cluster, material, .50, .35, .78)
    add_plank_stack(cluster, material, -.26, .43, .04)


def build_school_decor(material: bpy.types.Material) -> None:
    cluster = decor_cluster("school-garden-yard", "schoolhouse", 3.30, -.16, .86, ("planters", "buckets", "lantern-post"))
    add_planter(cluster, material, -.34, .18)
    add_planter(cluster, material, .34, .18)
    add_bucket(cluster, material, -.48, -.38, .88)
    add_lantern_post(cluster, material, .48, -.32, 1.22)


def build_assay_decor(material: bpy.types.Material) -> None:
    cluster = decor_cluster("assay-sample-yard", "assay_office", 3.42, -.15, .91, ("crates", "buckets", "rope-coils", "lantern-post"))
    add_crate(cluster, material, -.33, -.24, .25, .25)
    add_crate(cluster, material, -.24, -.15, .68, .19)
    add_bucket(cluster, material, .31, -.30, .90)
    add_rope_coil(cluster, material, -.28, .42, .90)
    add_lantern_post(cluster, material, .42, .28, 1.30)


def build_chapel_decor(material: bpy.types.Material) -> None:
    cluster = decor_cluster("chapel-flower-yard", "chapel", 3.24, -.18, .87, ("planters", "lantern-post", "bucket"))
    add_planter(cluster, material, -.34, .18)
    add_planter(cluster, material, .34, .18)
    add_bucket(cluster, material, -.42, -.34, .82)
    add_lantern_post(cluster, material, .40, -.30, 1.30)


def build_stamp_decor(material: bpy.types.Material) -> None:
    cluster = decor_cluster("stamp-mill-supply-yard", "stamp-mill", .60, -2.06, .73, ("planks", "barrels", "crates", "rope-coils"))
    add_plank_stack(cluster, material, -.18, -.26, .02)
    add_barrel(cluster, material, .34, .22, .82)
    add_crate(cluster, material, -.35, .32, .22, .21)
    add_rope_coil(cluster, material, .32, -.32, .82)


def build_dynamo_decor(material: bpy.types.Material) -> None:
    cluster = decor_cluster("dynamo-utility-yard", "dynamo-hall", -3.94, -.12, .92, ("crates", "rope-coils", "lantern-post", "planks"))
    add_crate(cluster, material, -.40, -.25, .27, .27)
    add_crate(cluster, material, -.34, -.18, .76, .20)
    add_rope_coil(cluster, material, .30, -.30, 1.12)
    add_plank_stack(cluster, material, -.20, .38, -.05)
    add_lantern_post(cluster, material, .47, .29, 1.48)


def decor_palette_uv(obj: bpy.types.Object, index: int) -> None:
    uv_layer = obj.data.uv_layers.get("UVMap") or obj.data.uv_layers.new(name="UVMap")
    column = index % DECOR_PALETTE_COLUMNS
    row = index // DECOR_PALETTE_COLUMNS
    u = (column + .5) / DECOR_PALETTE_COLUMNS
    v = DECOR_PALETTE_V_START + (row + .5) / DECOR_PALETTE_COLUMNS * (1.0 - DECOR_PALETTE_V_START)
    for loop in uv_layer.data:
        loop.uv = (u, v)


def decoration_clearance_report() -> dict:
    existing_props = [prop for prop in PROPS if prop.kind != "pan_monument"]
    clusters = []
    for cluster in DECOR_CLUSTERS:
        route_clearance = route_distance(cluster.x, cluster.y) - cluster.radius
        pad_clearance = min(
            rectangle_outside_distance(cluster.x, cluster.y, slot) - cluster.radius
            for slot in [*SLOTS, DYNAMO_SLOT]
        )
        prop_clearance = min(
            math.hypot(cluster.x - prop.position.x, cluster.y - prop.position.y)
            - cluster.radius
            - prop_radius(prop)
            for prop in existing_props
        )
        stage_clearance = math.hypot(cluster.x, cluster.y) - cluster.radius - PLAZA_CLEAR_RADIUS
        clusters.append({
            "id": cluster.id,
            "parcel": cluster.parcel,
            "center": [round(cluster.x, 4), round(cluster.y, 4), round(cluster.ground, 6)],
            "rotation": round(cluster.rotation, 6),
            "footprintRadius": cluster.radius,
            "routeClearance": round(route_clearance, 4),
            "padClearance": round(pad_clearance, 4),
            "existingPropClearance": round(prop_clearance, 4),
            "plazaStageClearance": round(stage_clearance, 4),
            "vocabulary": list(cluster.vocabulary),
        })

    pair_clearances = sorted(
        (
            math.hypot(left.x - right.x, left.y - right.y) - left.radius - right.radius,
            left.id,
            right.id,
        )
        for index, left in enumerate(DECOR_CLUSTERS)
        for right in DECOR_CLUSTERS[index + 1:]
    )
    report = {
        "law": "decor geometry stays inside audited circular footprints; pads, routes, shipped props, and plaza stage remain clear",
        "layoutSource": str(LAYOUT_SOURCE.relative_to(ROOT)),
        "layoutSha256": sha256(LAYOUT_SOURCE),
        "clusterCount": len(DECOR_CLUSTERS),
        "partCountBeforeJoin": len(DECOR_PARTS),
        "minimumRouteClearance": min(item["routeClearance"] for item in clusters),
        "minimumPadClearance": min(item["padClearance"] for item in clusters),
        "minimumExistingPropClearance": min(item["existingPropClearance"] for item in clusters),
        "minimumPlazaStageClearance": min(item["plazaStageClearance"] for item in clusters),
        "minimumPairClearance": pair_clearances[0][0],
        "closestPairs": [
            {"clearance": round(clearance, 4), "left": left, "right": right}
            for clearance, left, right in pair_clearances[:6]
        ],
        "clusters": clusters,
    }
    assert report["minimumRouteClearance"] >= .20, report
    assert report["minimumPadClearance"] >= .12, report
    assert report["minimumExistingPropClearance"] >= .12, report
    assert report["minimumPlazaStageClearance"] >= 1.0, report
    assert report["minimumPairClearance"] >= .12, report
    return report


def build_decorations(material: bpy.types.Material) -> tuple[list[bpy.types.Object], dict]:
    DECOR_CLUSTERS.clear()
    DECOR_PARTS.clear()
    build_tavern_decor(material)
    build_claim_decor(material)
    build_store_decor(material)
    build_school_decor(material)
    build_assay_decor(material)
    build_chapel_decor(material)
    build_stamp_decor(material)
    build_dynamo_decor(material)
    return DECOR_PARTS, decoration_clearance_report()


def join_plate_and_decor(
    plate: bpy.types.Object,
    parts: list[bpy.types.Object],
    material: bpy.types.Material,
) -> bpy.types.Object:
    converted = []
    for part in parts:
        bpy.ops.object.select_all(action="DESELECT")
        part.select_set(True)
        bpy.context.view_layer.objects.active = part
        bpy.ops.object.convert(target="MESH")
        decor_palette_uv(part, int(part["palette_index"]))
        converted.append(part)

    bpy.ops.object.select_all(action="DESELECT")
    plate.select_set(True)
    for part in converted:
        part.select_set(True)
    bpy.context.view_layer.objects.active = plate
    bpy.ops.object.join()
    plate.name = "TownPlate"
    plate.data.materials.clear()
    plate.data.materials.append(material)
    plate["decoration_wave"] = 2
    plate["decoration_clusters"] = len(DECOR_CLUSTERS)
    plate["plaza_center"] = "open stage; no Wave 2 decoration"
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    return plate


def sample_segment(start: Point, end: Point, spacing: float = 0.08) -> list[Point]:
    count = max(1, math.ceil(math.hypot(end.x - start.x, end.y - start.y) / spacing))
    return [
        Point(start.x + (end.x - start.x) * index / count, start.y + (end.y - start.y) * index / count)
        for index in range(count + 1)
    ]


def route_sample_points(points: list[Point], closed: bool) -> list[Point]:
    pairs = list(zip(points, points[1:]))
    if closed:
        pairs.append((points[-1], points[0]))
    samples: list[Point] = []
    for start, end in pairs:
        dx = end.x - start.x
        dy = end.y - start.y
        length = max(1e-9, math.hypot(dx, dy))
        normal = Point(-dy / length, dx / length)
        for point in sample_segment(start, end):
            for offset in (-0.45, 0.0, 0.45):
                samples.append(Point(point.x + normal.x * offset, point.y + normal.y * offset))
    return samples


def flat_walk_report() -> dict:
    route_reports = {}
    all_route_heights: list[float] = []
    for route_id, points, closed in [
        ("ring-road", RING_ROUTE, True),
        *[(route_id, points, False) for route_id, points in RADIAL_ROUTES.items()],
    ]:
        heights = [terrain_height(point.x, point.y) for point in route_sample_points(points, closed)]
        all_route_heights.extend(heights)
        route_reports[route_id] = {
            "samples": len(heights),
            "min": min(heights),
            "max": max(heights),
            "maxAbs": max(abs(value) for value in heights),
        }

    plaza_points = [
        Point(x, y)
        for x in np.arange(-PLAZA_CLEAR_RADIUS, PLAZA_CLEAR_RADIUS + 0.001, 0.2)
        for y in np.arange(-PLAZA_CLEAR_RADIUS, PLAZA_CLEAR_RADIUS + 0.001, 0.2)
        if math.hypot(float(x), float(y)) <= PLAZA_CLEAR_RADIUS
    ]
    plaza_heights = [terrain_height(point.x, point.y) for point in plaza_points]

    pad_reports = {}
    for slot in [*SLOTS, DYNAMO_SLOT]:
        theta = slot_angle(slot)
        heights = []
        for local_x in np.linspace(-slot.width * 0.5, slot.width * 0.5, 9):
            for local_y in np.linspace(-slot.depth * 0.5, slot.depth * 0.5, 7):
                world_x = slot.position.x + math.cos(theta) * local_x + math.sin(theta) * local_y
                world_y = slot.position.y - math.sin(theta) * local_x + math.cos(theta) * local_y
                heights.append(terrain_height(world_x, world_y))
        pad_reports[slot.id] = {
            "samples": len(heights),
            "maxAbs": max(abs(value) for value in heights),
        }

    report = {
        "law": f"walk routes and plaza remain within +/-{PATH_RELIEF_LIMIT:.2f}m",
        "layoutSource": str(LAYOUT_SOURCE.relative_to(ROOT)),
        "layoutSha256": sha256(LAYOUT_SOURCE),
        "routeSamples": len(all_route_heights),
        "routeMaxAbs": max(abs(value) for value in all_route_heights),
        "plazaSamples": len(plaza_heights),
        "plazaMaxAbs": max(abs(value) for value in plaza_heights),
        "routes": route_reports,
        "pads": pad_reports,
    }
    if report["routeMaxAbs"] > PATH_RELIEF_LIMIT or report["plazaMaxAbs"] > PATH_RELIEF_LIMIT:
        raise RuntimeError(f"Flat-walk law failed: {report}")
    if any(item["maxAbs"] > 0.005 for item in pad_reports.values()):
        raise RuntimeError(f"A building pad is not flat: {pad_reports}")
    return report


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


def make_reference_material() -> bpy.types.Material:
    image = bpy.data.images.load(str(PAINTED_GROUND), check_existing=False)
    material = bpy.data.materials.new("PaintedGroundBaselineMaterial")
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    texture = material.node_tree.nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Linear"
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Roughness"].default_value = 0.9
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    return material


def make_baseline_plane(material: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_plane_add(size=30.0, location=(0.0, 0.0, -0.01))
    plane = bpy.context.object
    plane.name = "PaintedGroundBaseline"
    plane.data.materials.append(material)
    uv = plane.data.uv_layers.active
    for loop in uv.data:
        loop.uv = loop.uv
    return plane


def import_model(path: Path, name: str, position: Point, rotation: float = 0.0, scale: float = 1.0) -> bpy.types.Object:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported = [obj for obj in bpy.data.objects if obj not in before]
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    for obj in imported:
        if obj.parent is None:
            obj.parent = root
        if obj.type == "MESH":
            obj.visible_shadow = True
    root.location = (position.x, position.y, 0.0)
    root.rotation_euler[2] = -rotation
    root.scale = (scale, scale, scale)
    return root


def add_render_models() -> list[bpy.types.Object]:
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
    for slot in [*SLOTS, DYNAMO_SLOT]:
        path = model_paths[slot.id]
        if path.exists():
            roots.append(import_model(path, f"RenderBuilding:{slot.id}", slot.position, slot_angle(slot)))

    prop_paths = {
        "covered_wagon": ROOT / "assets/pilots/plaza-props-3d/covered_wagon.glb",
        "water_trough": ROOT / "assets/pilots/plaza-props-3d/water_trough.glb",
        "pan_monument": ROOT / "assets/pilots/plaza-props-3d/pan_monument.glb",
    }
    for prop in PROPS:
        path = prop_paths.get(prop.kind)
        if path and path.exists():
            roots.append(import_model(path, f"RenderProp:{prop.id}", prop.position, prop.rotation, prop.scale))
    return roots


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_render_scene() -> bpy.types.Object:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.world = bpy.data.worlds.new("EvidenceWorld")
    scene.world.color = (0.81, 0.66, 0.44)
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.81, 0.66, 0.44, 1.0)
    background.inputs["Strength"].default_value = 1.05
    scene.view_settings.look = "AgX - Medium Low Contrast"

    bpy.ops.object.camera_add(location=(0.0, 18.3, 26.2))
    camera = bpy.context.object
    camera.name = "EvidenceCameraTS04"
    camera.data.sensor_fit = "VERTICAL"
    camera.data.lens = camera.data.sensor_height / (2.0 * math.tan(math.radians(42.0) * 0.5))
    camera.data.clip_end = 120.0
    look_at(camera, Vector((0.0, -3.35, 0.51)))
    scene.camera = camera

    bpy.ops.object.light_add(type="SUN", location=(-22.0, -18.0, 28.0))
    sun = bpy.context.object
    sun.name = "EvidenceSun"
    sun.data.energy = 2.35
    sun.data.color = (1.0, 0.84, 0.63)
    sun.data.angle = math.radians(12.0)
    look_at(sun, Vector((0.0, 0.0, 0.0)))

    bpy.ops.object.light_add(type="AREA", location=(8.0, 4.0, 24.0))
    fill = bpy.context.object
    fill.name = "EvidenceFill"
    fill.data.energy = 1120.0
    fill.data.shape = "DISK"
    fill.data.size = 18.0
    fill.data.color = (1.0, 0.95, 0.82)
    look_at(fill, Vector((0.0, 0.0, 0.0)))
    return camera


def set_visible(obj: bpy.types.Object, visible: bool) -> None:
    obj.hide_render = not visible
    obj.hide_viewport = not visible


def render(path: Path) -> None:
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def emission_material(name: str, color: tuple[float, float, float, float], strength: float) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Roughness"].default_value = 0.72
    shader.inputs["Emission Color"].default_value = color
    shader.inputs["Emission Strength"].default_value = strength
    return material


def curve_object(name: str, points: list[Point], material: bpy.types.Material, closed: bool, height: float = 0.075) -> bpy.types.Object:
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = 0.075
    curve.bevel_resolution = 1
    polyline = curve.splines.new("POLY")
    polyline.points.add(len(points) - 1)
    for control, point in zip(polyline.points, points):
        control.co = (point.x, point.y, height, 1.0)
    polyline.use_cyclic_u = closed
    curve.materials.append(material)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    return obj


def pad_outline(slot: Slot) -> list[Point]:
    theta = slot_angle(slot)
    corners = [
        (-slot.width * 0.5, -slot.depth * 0.5),
        (slot.width * 0.5, -slot.depth * 0.5),
        (slot.width * 0.5, slot.depth * 0.5),
        (-slot.width * 0.5, slot.depth * 0.5),
    ]
    return [
        Point(
            slot.position.x + math.cos(theta) * x + math.sin(theta) * y,
            slot.position.y - math.sin(theta) * x + math.cos(theta) * y,
        )
        for x, y in corners
    ]


def add_walk_overlay() -> list[bpy.types.Object]:
    route_material = emission_material("FlatWalkRouteOverlay", (0.09, 0.78, 0.76, 1.0), 1.8)
    pad_material = emission_material("FlatPadOverlay", (1.0, 0.54, 0.08, 1.0), 1.4)
    decor_material = emission_material("DecorFootprintOverlay", (0.88, 0.08, 0.46, 1.0), 1.6)
    overlay = [curve_object("WalkLoop:ring-road", RING_ROUTE, route_material, True)]
    overlay.extend(
        curve_object(f"HeroPath:{route_id}", points, route_material, False)
        for route_id, points in RADIAL_ROUTES.items()
    )
    overlay.extend(
        curve_object(f"FlatPad:{slot.id}", pad_outline(slot), pad_material, True, 0.085)
        for slot in [*SLOTS, DYNAMO_SLOT]
    )
    overlay.extend(
        curve_object(
            f"DecorFootprint:{cluster.id}",
            [
                Point(
                    cluster.x + math.sin(index / 24.0 * math.tau) * cluster.radius,
                    cluster.y + math.cos(index / 24.0 * math.tau) * cluster.radius,
                )
                for index in range(24)
            ],
            decor_material,
            True,
            cluster.ground + .12,
        )
        for cluster in DECOR_CLUSTERS
    )
    return overlay


def render_focus(
    camera: bpy.types.Object,
    target: Vector,
    distance: float,
    path: Path,
    resolution: tuple[int, int],
) -> None:
    original_location = camera.location.copy()
    original_rotation = camera.rotation_euler.copy()
    original_resolution = (bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y)
    locked_offset = Vector((0.0, 18.3, 26.2)) - Vector((0.0, -3.35, .51))
    camera.location = target + locked_offset.normalized() * distance
    look_at(camera, target)
    bpy.context.scene.render.resolution_x = resolution[0]
    bpy.context.scene.render.resolution_y = resolution[1]
    render(path)
    bpy.context.scene.render.resolution_x = original_resolution[0]
    bpy.context.scene.render.resolution_y = original_resolution[1]
    camera.location = original_location
    camera.rotation_euler = original_rotation


def combine_ab(left_path: Path, right_path: Path, output_path: Path) -> None:
    left_image = bpy.data.images.load(str(left_path), check_existing=False)
    right_image = bpy.data.images.load(str(right_path), check_existing=False)
    width, height = left_image.size
    if tuple(right_image.size) != (width, height):
        raise RuntimeError("A/B render sizes differ")
    left = np.empty(width * height * 4, dtype=np.float32)
    right = np.empty(width * height * 4, dtype=np.float32)
    left_image.pixels.foreach_get(left)
    right_image.pixels.foreach_get(right)
    combined = np.concatenate((left.reshape(height, width, 4), right.reshape(height, width, 4)), axis=1)
    image = bpy.data.images.new("TownPlateAB", width * 2, height, alpha=True)
    image.pixels.foreach_set(combined.ravel())
    image.filepath_raw = str(output_path)
    image.file_format = "PNG"
    image.save()


def mesh_triangles(obj: bpy.types.Object) -> int:
    return sum(max(0, len(polygon.vertices) - 2) for polygon in obj.data.polygons)


def write_layout_contract(report: dict, decoration_report: dict, triangles: int) -> None:
    contract = {
        "layoutSource": str(LAYOUT_SOURCE.relative_to(ROOT)),
        "layoutSha256": sha256(LAYOUT_SOURCE),
        "stampFootprintSource": str(TOWN_SCENE_SOURCE.relative_to(ROOT)),
        "dynamoFootprintSource": str(DYNAMO_SOURCE.relative_to(ROOT)),
        "plateExtent": [HALF_EXTENT * 2.0, HALF_EXTENT * 2.0],
        "grid": [GRID_CELLS + 1, GRID_CELLS + 1],
        "triangles": triangles,
        "slots": [
            {
                "id": slot.id,
                "position": [slot.position.x, slot.position.y],
                "approach": [slot.approach.x, slot.approach.y],
                "footprint": [slot.width, slot.depth],
            }
            for slot in [*SLOTS, DYNAMO_SLOT]
        ],
        "routes": {
            "ringRoad": [[point.x, point.y] for point in RING_ROUTE],
            "radial": {route_id: [[point.x, point.y] for point in points] for route_id, points in RADIAL_ROUTES.items()},
        },
        "flatWalk": report,
        "decoration": decoration_report,
    }
    (ARTIFACTS / "layout-contract.json").write_text(json.dumps(contract, indent=2) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    reset_scene()
    atlas = make_atlas()
    material = make_plate_material(atlas)
    plate = build_plate(material)
    decoration_parts, decoration_report = build_decorations(material)
    plate = join_plate_and_decor(plate, decoration_parts, material)
    report = flat_walk_report()
    triangles = mesh_triangles(plate)
    if triangles > 30_000:
        raise RuntimeError(f"Wave 2 Town plate exceeds 30k triangle budget: {triangles}")
    write_layout_contract(report, decoration_report, triangles)
    (ARTIFACTS / "flat-walk-report.json").write_text(json.dumps(report, indent=2) + "\n")
    (ARTIFACTS / "decoration-clearance.json").write_text(json.dumps(decoration_report, indent=2) + "\n")
    save_and_export(plate)

    if "--asset-only" in sys.argv:
        print(json.dumps({
            "blend": str(BLEND), "glb": str(GLB), "glbSha256": sha256(GLB),
            "triangles": triangles, "routeMaxAbs": report["routeMaxAbs"],
            "plazaMaxAbs": report["plazaMaxAbs"], "evidence": "render_current_references.py",
        }, indent=2))
        return

    render_roots = add_render_models()
    camera = setup_render_scene()
    for root in render_roots:
        set_visible(root, True)

    baseline_path = RENDERS / "town-plate-ts04.png"
    if not baseline_path.exists():
        raise RuntimeError(f"Wave 1 locked-camera baseline is missing: {baseline_path}")
    candidate_path = RENDERS / "town-plate-wave2-ts04.png"
    overlay_path = RENDERS / "town-plate-wave2-clearance-overlay-ts04.png"
    render(candidate_path)
    overlay = add_walk_overlay()
    render(overlay_path)
    for item in overlay:
        set_visible(item, False)

    center_detail = RENDERS / "town-plate-wave2-pan-detail-ts04.png"
    commerce_detail = RENDERS / "town-plate-wave2-tavern-workyard-detail-ts04.png"
    civic_detail = RENDERS / "town-plate-wave2-civic-detail-ts04.png"
    render_focus(camera, Vector((0.0, 0.0, .85)), 10.5, center_detail, (820, 720))
    render_focus(camera, Vector((-8.4, -5.5, 1.0)), 9.2, commerce_detail, (980, 720))
    render_focus(camera, Vector((4.0, 6.6, 1.0)), 14.5, civic_detail, (1080, 720))
    ab_path = RENDERS / "town-plate-wave2-ab-ts04.png"
    combine_ab(baseline_path, candidate_path, ab_path)

    print(json.dumps({
        "blend": str(BLEND),
        "glb": str(GLB),
        "glbSha256": sha256(GLB),
        "glbBytes": GLB.stat().st_size,
        "triangles": triangles,
        "atlas": [ATLAS_SIZE, ATLAS_SIZE],
        "decorationClusters": len(DECOR_CLUSTERS),
        "minimumRouteClearance": decoration_report["minimumRouteClearance"],
        "minimumPadClearance": decoration_report["minimumPadClearance"],
        "minimumPlazaStageClearance": decoration_report["minimumPlazaStageClearance"],
        "routeMaxAbs": report["routeMaxAbs"],
        "plazaMaxAbs": report["plazaMaxAbs"],
        "renders": [
            str(path)
            for path in (baseline_path, candidate_path, ab_path, overlay_path, center_detail, commerce_detail, civic_detail)
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
