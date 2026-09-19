from __future__ import annotations

from dataclasses import dataclass
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
ARTIFACTS = ROOT / "artifacts/dome-commons-e8"
BLEND = OUT / "dome-commons-plate.blend"
GLB = OUT / "dome-commons-plate.glb"
TEMP_ATLAS = OUT / ".dome-commons-atlas.png"
E8_PLATE = ROOT / "assets/raw/plate-e8-bld-set.png"
E8_KIT = ROOT / "assets/raw/kit-era-8.png"
E8_BUNDLE = ROOT / "specs/epoch-saga/e8-orbital-bundle.md"
TOWN_BUILDER = ROOT / "assets/pilots/town-plate-3d/build_town_plate.py"
TOWN_LAYOUT = ROOT / "src/town/townLayout.ts"
TOWN_SCENE = ROOT / "src/town/TownScene.ts"
DYNAMO_MANIFEST = ROOT / "assets/contracts/epoch-2-steamworks/manifest.json"

BASE_SHA = "2736e176d69226d40603889ee3e1aa07db623784"
ATLAS_SIZE = 2048
TRIANGLE_BUDGET = 20_000
GROUND_RADIUS = 24.8
DOME_RADIUS = 21.65
DOME_HEIGHT = 12.6
GROUND_RINGS = 40
GROUND_SEGMENTS = 96
DOME_RINGS = 12
DOME_SEGMENTS = 48
PATH_RELIEF_LIMIT = 0.05
PATH_SAFE_RADIUS = 1.05
PLAZA_CLEAR_RADIUS = 3.1

GROUND_V_MIN = 0.02
GROUND_V_MAX = 0.72
SIDE_V_MIN = 0.74
SIDE_V_MAX = 0.82
SWATCH_V_MIN = 0.84
SWATCH_V_MAX = 0.90
GLASS_U_MIN = 0.42
GLASS_U_MAX = 0.82
GLASS_V_MIN = 0.91
GLASS_V_MAX = 0.965
WATER_V_MIN = 0.975
WATER_V_MAX = 0.995

PINNED_SOURCE_HASHES = {
    TOWN_BUILDER: "32efe0602388462fae9a1fbe47e799552176eb7fa18bac3e2c56dd08a1c46cf0",
    TOWN_LAYOUT: "6d000feac3c0e2e14051f287205e5450b3b701bec4c44e513613a34ea39017d0",
    TOWN_SCENE: "88f0dcfd3daca9626883176b857fe6b7db289fd223908d0f13bf68803c885cd7",
    DYNAMO_MANIFEST: "5e0f6a5b4f850553e560fceac2ef325d47a71826b98bbb8ebbb4b6c1c17e6a20",
    E8_PLATE: "4d2595ec304fc73e6317c0ec4ba46edc3a3af5e0b080b24b0ced43ed14ae81d5",
    E8_KIT: "107b3929f13dc5dfee336eb2a4d605a0ceaedfd1db3c8edc3c5817a1a48f19de",
    E8_BUNDLE: "94cc1a3cdda50dfcf1dcb02d79c0f0d5b7a952fcb7f7793d730d16fc675ea9ba",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_pinned_sources() -> None:
    mismatches = [
        f"{path.relative_to(ROOT)}: expected {expected}, got {sha256(path)}"
        for path, expected in PINNED_SOURCE_HASHES.items()
        if not path.is_file() or sha256(path) != expected
    ]
    if mismatches:
        raise RuntimeError(
            f"Dome Commons sources no longer match reviewed base {BASE_SHA}:\n" + "\n".join(mismatches)
        )


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


verify_pinned_sources()
town = load_module("dome_commons_layout", TOWN_BUILDER)
Point = town.Point
Slot = town.Slot
CANONICAL_SLOTS = [*town.SLOTS, town.DYNAMO_SLOT]
CANONICAL_ROUTES = town.RADIAL_ROUTES
RING_ROUTE = town.RING_ROUTE


@dataclass(frozen=True)
class OrbitalPad:
    id: str
    position: Point
    shape: str
    width: float
    depth: float
    role: str


ORBITAL_PADS = (
    OrbitalPad("orbital-pad-port", Point(-7.4, -16.6), "rectangle", 5.6, 3.8, "E8 outer-work pad"),
    OrbitalPad("orbital-pad-starboard", Point(7.0, -16.7), "circle", 6.2, 6.2, "E8 pressure-habitat pad"),
)


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 1.0 if value >= edge1 else 0.0
    t = min(1.0, max(0.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def distance_to_polyline(x: float, y: float, points: list[Point], closed: bool = False) -> float:
    return town.distance_to_polyline(x, y, points, closed)


def route_distance(x: float, y: float) -> float:
    radial = min(distance_to_polyline(x, y, route) for route in CANONICAL_ROUTES.values())
    ring = abs(math.hypot(x, y) - 6.0)
    return min(radial, ring)


def pad_outside_distance(x: float, y: float, pad: OrbitalPad) -> float:
    dx = abs(x - pad.position.x)
    dy = abs(y - pad.position.y)
    if pad.shape == "circle":
        return max(0.0, math.hypot(dx, dy) - pad.width * 0.5)
    return math.hypot(max(0.0, dx - pad.width * 0.5), max(0.0, dy - pad.depth * 0.5))


def flat_mask(x: float, y: float) -> float:
    mask = smoothstep(PATH_SAFE_RADIUS, PATH_SAFE_RADIUS + 0.75, route_distance(x, y))
    mask = min(mask, smoothstep(PLAZA_CLEAR_RADIUS, PLAZA_CLEAR_RADIUS + 0.8, math.hypot(x, y)))
    for slot in CANONICAL_SLOTS:
        mask = min(mask, smoothstep(0.0, 0.65, town.rectangle_outside_distance(x, y, slot, margin=0.42)))
    for pad in ORBITAL_PADS:
        mask = min(mask, smoothstep(0.0, 0.65, pad_outside_distance(x, y, pad)))
    return mask


CRATERS = (
    (-15.7, 11.7, 2.2, 0.16),
    (15.3, 12.4, 1.7, 0.13),
    (-16.6, -8.8, 1.9, 0.14),
    (16.8, -7.8, 2.4, 0.18),
    (-2.0, 18.4, 1.4, 0.10),
)


def terrain_height(x: float, y: float) -> float:
    radius = math.hypot(x, y)
    relief = 0.045 * math.sin(x * 0.35 + y * 0.13) + 0.028 * math.cos(y * 0.43 - x * 0.09)
    for cx, cy, crater_radius, depth in CRATERS:
        distance = math.hypot(x - cx, y - cy)
        bowl = math.exp(-((distance / crater_radius) ** 4))
        rim = math.exp(-(((distance - crater_radius * 1.18) / (crater_radius * 0.24)) ** 2))
        relief += -depth * bowl + depth * 0.34 * rim
    rim_height = 0.58 * smoothstep(DOME_RADIUS + 0.55, GROUND_RADIUS - 0.15, radius)
    height = (relief + rim_height) * flat_mask(x, y)
    height += -0.007 * math.exp(-((route_distance(x, y) / 0.58) ** 4))
    return height


class MeshBuilder:
    def __init__(self):
        self.vertices: list[tuple[float, float, float]] = []
        self.faces: list[tuple[int, ...]] = []
        self.uv_faces: list[list[tuple[float, float]]] = []

    def vertex(self, position: tuple[float, float, float]) -> int:
        self.vertices.append(position)
        return len(self.vertices) - 1

    def face(self, indices: tuple[int, ...], uvs: list[tuple[float, float]]) -> None:
        self.faces.append(indices)
        self.uv_faces.append(uvs)


def ground_uv(x: float, y: float) -> tuple[float, float]:
    u = (x / (GROUND_RADIUS * 2.0)) + 0.5
    v = GROUND_V_MIN + ((y / (GROUND_RADIUS * 2.0)) + 0.5) * (GROUND_V_MAX - GROUND_V_MIN)
    return (u, v)


def swatch_uv(column: int) -> tuple[float, float]:
    return ((column + 0.5) / 8.0, (SWATCH_V_MIN + SWATCH_V_MAX) * 0.5)


def add_tube(
    builder: MeshBuilder,
    start: Vector,
    end: Vector,
    radius: float,
    sides: int,
    uv: tuple[float, float],
    caps: bool = False,
) -> None:
    axis = end - start
    if axis.length <= 1e-8:
        return
    axis.normalize()
    reference = Vector((0.0, 0.0, 1.0)) if abs(axis.z) < 0.92 else Vector((1.0, 0.0, 0.0))
    tangent = axis.cross(reference).normalized()
    bitangent = axis.cross(tangent).normalized()
    first: list[int] = []
    second: list[int] = []
    for index in range(sides):
        angle = index / sides * math.tau
        offset = (tangent * math.cos(angle) + bitangent * math.sin(angle)) * radius
        first.append(builder.vertex(tuple(start + offset)))
        second.append(builder.vertex(tuple(end + offset)))
    for index in range(sides):
        following = (index + 1) % sides
        builder.face((first[index], second[index], second[following], first[following]), [uv] * 4)
    if caps:
        builder.face(tuple(reversed(first)), [uv] * sides)
        builder.face(tuple(second), [uv] * sides)


def add_ring_tube(
    builder: MeshBuilder,
    radius: float,
    height: float,
    thickness: float,
    segments: int,
    uv: tuple[float, float],
) -> None:
    for segment in range(segments):
        first = segment / segments * math.tau
        second = (segment + 1) / segments * math.tau
        add_tube(
            builder,
            Vector((math.cos(first) * radius, math.sin(first) * radius, height)),
            Vector((math.cos(second) * radius, math.sin(second) * radius, height)),
            thickness,
            4,
            uv,
        )


def add_ground(builder: MeshBuilder) -> None:
    center = builder.vertex((0.0, 0.0, terrain_height(0.0, 0.0)))
    rings: list[list[int]] = []
    for ring in range(1, GROUND_RINGS + 1):
        fraction = ring / GROUND_RINGS
        indices: list[int] = []
        for segment in range(GROUND_SEGMENTS):
            angle = segment / GROUND_SEGMENTS * math.tau
            radius = GROUND_RADIUS * fraction * (1.0 + 0.012 * math.sin(angle * 5.0 + 0.2))
            x = math.cos(angle) * radius
            y = math.sin(angle) * radius
            indices.append(builder.vertex((x, y, terrain_height(x, y))))
        rings.append(indices)
    for segment in range(GROUND_SEGMENTS):
        following = (segment + 1) % GROUND_SEGMENTS
        face = (center, rings[0][segment], rings[0][following])
        builder.face(face, [ground_uv(*builder.vertices[index][:2]) for index in face])
    for ring in range(len(rings) - 1):
        for segment in range(GROUND_SEGMENTS):
            following = (segment + 1) % GROUND_SEGMENTS
            face = (rings[ring][segment], rings[ring + 1][segment], rings[ring + 1][following], rings[ring][following])
            builder.face(face, [ground_uv(*builder.vertices[index][:2]) for index in face])

    bottom_ring: list[int] = []
    for segment in range(GROUND_SEGMENTS):
        angle = segment / GROUND_SEGMENTS * math.tau
        radius = GROUND_RADIUS * (1.0 + 0.012 * math.sin(angle * 5.0 + 0.2))
        bottom_ring.append(builder.vertex((math.cos(angle) * radius, math.sin(angle) * radius, -0.78)))
    for segment in range(GROUND_SEGMENTS):
        following = (segment + 1) % GROUND_SEGMENTS
        u0 = segment / GROUND_SEGMENTS
        u1 = (segment + 1) / GROUND_SEGMENTS
        builder.face(
            (rings[-1][segment], bottom_ring[segment], bottom_ring[following], rings[-1][following]),
            [(u0, SIDE_V_MAX), (u0, SIDE_V_MIN), (u1, SIDE_V_MIN), (u1, SIDE_V_MAX)],
        )


def add_glass_dome(builder: MeshBuilder) -> None:
    apex = builder.vertex((0.0, 0.0, DOME_HEIGHT))
    rings: list[list[int]] = []
    for ring in range(1, DOME_RINGS + 1):
        theta = ring / DOME_RINGS * math.pi * 0.5
        radial = DOME_RADIUS * math.sin(theta)
        height = DOME_HEIGHT * math.cos(theta)
        indices = [
            builder.vertex((math.cos(segment / DOME_SEGMENTS * math.tau) * radial,
                            math.sin(segment / DOME_SEGMENTS * math.tau) * radial, height))
            for segment in range(DOME_SEGMENTS)
        ]
        rings.append(indices)
    for segment in range(DOME_SEGMENTS):
        following = (segment + 1) % DOME_SEGMENTS
        u0 = GLASS_U_MIN + (segment / DOME_SEGMENTS) * (GLASS_U_MAX - GLASS_U_MIN)
        u1 = GLASS_U_MIN + ((segment + 1) / DOME_SEGMENTS) * (GLASS_U_MAX - GLASS_U_MIN)
        builder.face(
            (apex, rings[0][segment], rings[0][following]),
            [((u0 + u1) * 0.5, GLASS_V_MAX), (u0, GLASS_V_MAX - 0.004), (u1, GLASS_V_MAX - 0.004)],
        )
    for ring in range(len(rings) - 1):
        v0 = GLASS_V_MAX - ((ring + 1) / DOME_RINGS) * (GLASS_V_MAX - GLASS_V_MIN)
        v1 = GLASS_V_MAX - ((ring + 2) / DOME_RINGS) * (GLASS_V_MAX - GLASS_V_MIN)
        for segment in range(DOME_SEGMENTS):
            following = (segment + 1) % DOME_SEGMENTS
            u0 = GLASS_U_MIN + (segment / DOME_SEGMENTS) * (GLASS_U_MAX - GLASS_U_MIN)
            u1 = GLASS_U_MIN + ((segment + 1) / DOME_SEGMENTS) * (GLASS_U_MAX - GLASS_U_MIN)
            builder.face(
                (rings[ring][segment], rings[ring + 1][segment], rings[ring + 1][following], rings[ring][following]),
                [(u0, v0), (u0, v1), (u1, v1), (u1, v0)],
            )

    brass = swatch_uv(2)
    silver = swatch_uv(1)
    for meridian in range(12):
        angle = meridian / 12.0 * math.tau
        points = []
        for step in range(DOME_RINGS + 1):
            theta = step / DOME_RINGS * math.pi * 0.5
            points.append(Vector((math.cos(angle) * DOME_RADIUS * math.sin(theta),
                                  math.sin(angle) * DOME_RADIUS * math.sin(theta),
                                  DOME_HEIGHT * math.cos(theta))))
        for first, second in zip(points, points[1:]):
            add_tube(builder, first, second, 0.075, 4, brass)
    for latitude, uv in ((0.34, silver), (0.66, brass)):
        theta = latitude * math.pi * 0.5
        radial = DOME_RADIUS * math.sin(theta)
        height = DOME_HEIGHT * math.cos(theta)
        add_ring_tube(builder, radial, height, 0.065, DOME_SEGMENTS, uv)
    add_ring_tube(builder, DOME_RADIUS, 0.10, 0.16, DOME_SEGMENTS, brass)
    add_tube(builder, Vector((0, 0, DOME_HEIGHT - 0.05)), Vector((0, 0, DOME_HEIGHT + 0.62)), 0.17, 8, brass, True)

    for index in range(12):
        angle = index / 12.0 * math.tau
        x = math.cos(angle) * DOME_RADIUS
        y = math.sin(angle) * DOME_RADIUS
        add_tube(builder, Vector((x, y, 0.0)), Vector((x, y, 0.62)), 0.12, 6, silver, True)
        add_tube(builder, Vector((x, y, 0.39)), Vector((x, y, 0.60)), 0.155, 6, swatch_uv(3))


def add_airlock_frame(builder: MeshBuilder) -> None:
    dark = swatch_uv(0)
    brass = swatch_uv(2)
    y = DOME_RADIUS + 0.02
    for x in (-1.28, 1.28):
        add_tube(builder, Vector((x, y, 0.0)), Vector((x, y, 2.25)), 0.17, 6, dark, True)
        add_tube(builder, Vector((x * 0.86, y - 0.02, 0.0)), Vector((x * 0.86, y - 0.02, 2.25)), 0.085, 6, brass)
    center = Vector((0.0, y, 2.25))
    points = [center + Vector((math.cos(index / 12.0 * math.pi) * 1.28, 0.0,
                              math.sin(index / 12.0 * math.pi) * 1.28)) for index in range(13)]
    for first, second in zip(points, points[1:]):
        add_tube(builder, first, second, 0.17, 6, dark)
    inner = [center + Vector((math.cos(index / 12.0 * math.pi) * 1.10, -0.02,
                             math.sin(index / 12.0 * math.pi) * 1.10)) for index in range(13)]
    for first, second in zip(inner, inner[1:]):
        add_tube(builder, first, second, 0.085, 6, brass)
    add_tube(builder, Vector((-1.45, y, 0.025)), Vector((1.45, y, 0.025)), 0.045, 4, brass)


def add_reclaimed_water_ring(builder: MeshBuilder) -> None:
    segments = 64
    inner = 1.13
    outer = 1.88
    water_uv = ((0.5), (WATER_V_MIN + WATER_V_MAX) * 0.5)
    inner_indices: list[int] = []
    outer_indices: list[int] = []
    for segment in range(segments):
        angle = segment / segments * math.tau
        inner_indices.append(builder.vertex((math.cos(angle) * inner, math.sin(angle) * inner, 0.012)))
        outer_indices.append(builder.vertex((math.cos(angle) * outer, math.sin(angle) * outer, 0.012)))
    for segment in range(segments):
        following = (segment + 1) % segments
        builder.face(
            (inner_indices[segment], outer_indices[segment], outer_indices[following], inner_indices[following]),
            [water_uv] * 4,
        )
    brass = swatch_uv(2)
    # The first-water curb is a tactile seal, not a step: its crown stays below
    # the flat-walk ceiling so the plaza remains a genuinely walkable commons.
    add_ring_tube(builder, inner - 0.03, 0.018, 0.025, segments, brass)
    add_ring_tube(builder, outer + 0.03, 0.018, 0.025, segments, brass)


def make_atlas() -> bpy.types.Image:
    size = ATLAS_SIZE
    pixels = np.ones((size, size, 4), dtype=np.float32)
    y_axis = np.linspace(-GROUND_RADIUS, GROUND_RADIUS, int(size * (GROUND_V_MAX - GROUND_V_MIN)), dtype=np.float32)
    x_axis = np.linspace(-GROUND_RADIUS, GROUND_RADIUS, size, dtype=np.float32)
    world_x, world_y = np.meshgrid(x_axis, y_axis)
    base = np.array([0.50, 0.47, 0.39], dtype=np.float32)
    broad = 0.038 * np.sin(world_x * 0.19 + world_y * 0.07) + 0.024 * np.cos(world_y * 0.31 - world_x * 0.11)
    grain = np.mod(np.sin(world_x * 12.9898 + world_y * 78.233) * 43758.5453, 1.0)
    stipple = (grain > 0.987).astype(np.float32)
    rgb = base[None, None, :] + broad[:, :, None]
    rgb *= 1.0 - stipple[:, :, None] * 0.24

    routes = [(RING_ROUTE, True), *[(route, False) for route in CANONICAL_ROUTES.values()]]
    route_field = np.full(world_x.shape, np.inf, dtype=np.float32)
    for points, closed in routes:
        pairs = list(zip(points, points[1:]))
        if closed:
            pairs.append((points[-1], points[0]))
        for start, end in pairs:
            dx = end.x - start.x
            dy = end.y - start.y
            length_sq = max(1e-9, dx * dx + dy * dy)
            t = np.clip(((world_x - start.x) * dx + (world_y - start.y) * dy) / length_sq, 0.0, 1.0)
            distance = np.hypot(world_x - (start.x + dx * t), world_y - (start.y + dy * t))
            route_field = np.minimum(route_field, distance)
    walkway = np.exp(-((route_field / 0.72) ** 4))
    silver = np.array([0.58, 0.59, 0.55], dtype=np.float32)
    teal = np.array([0.07, 0.36, 0.36], dtype=np.float32)
    rgb = rgb * (1.0 - walkway[:, :, None] * 0.17) + silver[None, None, :] * walkway[:, :, None] * 0.17
    seal_line = np.exp(-(((route_field - 0.47) / 0.055) ** 2))
    rgb = rgb * (1.0 - seal_line[:, :, None] * 0.58) + teal[None, None, :] * seal_line[:, :, None] * 0.58

    # The moon-born child's first grass is a flush floor inlay: warmth under
    # glass, visible but incapable of tripping the planar cast.
    grass = ((np.abs(world_x + 2.9) < 0.78) & (np.abs(world_y - 3.0) < 0.58)).astype(np.float32)
    grass_border = (
        (np.abs(world_x + 2.9) < 0.86) & (np.abs(world_y - 3.0) < 0.66)
        & (grass < 0.5)
    ).astype(np.float32)
    green = np.array([0.22, 0.36, 0.22], dtype=np.float32)
    brass = np.array([0.53, 0.34, 0.10], dtype=np.float32)
    rgb = rgb * (1.0 - grass[:, :, None] * 0.78) + green[None, None, :] * grass[:, :, None] * 0.78
    rgb = rgb * (1.0 - grass_border[:, :, None] * 0.58) + brass[None, None, :] * grass_border[:, :, None] * 0.58

    for cx, cy, crater_radius, _depth in CRATERS:
        distance = np.hypot(world_x - cx, world_y - cy)
        ring = np.exp(-(((distance - crater_radius) / 0.10) ** 2))
        rgb *= 1.0 - ring[:, :, None] * 0.18

    radius = np.hypot(world_x, world_y)
    landing_scorch = np.exp(-(((world_x / 4.8) ** 2) + (((world_y - 17.0) / 2.2) ** 2)))
    rgb *= 1.0 - landing_scorch[:, :, None] * 0.17
    rim = np.clip((radius - DOME_RADIUS) / (GROUND_RADIUS - DOME_RADIUS), 0.0, 1.0)
    rgb *= 1.0 - rim[:, :, None] * 0.15
    rgb = np.clip(rgb * 1.10 + 0.014, 0.03, 0.96)

    y0 = int(size * GROUND_V_MIN)
    y1 = y0 + rgb.shape[0]
    pixels[y0:y1, :, :3] = rgb

    side0 = int(size * SIDE_V_MIN)
    side1 = int(size * SIDE_V_MAX)
    side_y = np.linspace(0.0, 1.0, side1 - side0, dtype=np.float32)[:, None]
    side_x = np.linspace(0.0, math.tau, size, dtype=np.float32)[None, :]
    side_rgb = np.array([0.27, 0.245, 0.19], dtype=np.float32)[None, None, :] + (
        0.035 * np.sin(side_y * 18.0 + side_x * 4.0)
    )[:, :, None]
    pixels[side0:side1, :, :3] = np.clip(side_rgb, 0.05, 0.6)

    swatches = (
        (0.09, 0.095, 0.085),
        (0.61, 0.62, 0.57),
        (0.54, 0.33, 0.09),
        (0.12, 0.39, 0.38),
        (0.22, 0.22, 0.19),
        (0.77, 0.69, 0.50),
        (0.29, 0.18, 0.08),
        (0.48, 0.49, 0.46),
    )
    sy0 = int(size * SWATCH_V_MIN)
    sy1 = int(size * SWATCH_V_MAX)
    for index, color in enumerate(swatches):
        x0 = int(index / len(swatches) * size)
        x1 = int((index + 1) / len(swatches) * size)
        pixels[sy0:sy1, x0:x1, :3] = color

    gx0 = int(size * GLASS_U_MIN)
    gx1 = int(size * GLASS_U_MAX)
    gy0 = int(size * GLASS_V_MIN)
    gy1 = int(size * GLASS_V_MAX)
    glass_x = np.linspace(0.0, math.tau * 6.0, gx1 - gx0, dtype=np.float32)[None, :]
    glass_y = np.linspace(0.0, math.pi * 5.0, gy1 - gy0, dtype=np.float32)[:, None]
    glass = np.zeros((gy1 - gy0, gx1 - gx0, 3), dtype=np.float32)
    glass[:, :, :] = np.array([0.19, 0.56, 0.58], dtype=np.float32)
    glass += (0.025 * np.sin(glass_x + glass_y))[:, :, None]
    pixels[gy0:gy1, gx0:gx1, :3] = np.clip(glass, 0.08, 0.82)
    # A macro screen-door follows the 48x12 panel grid: opaque teal edge/glint
    # strokes surround genuinely open pane centers. glTF MASK keeps depth writes
    # enabled for the shared one-material floor, ribs, and shell in Three.js.
    panel_u = np.mod(np.linspace(0.0, 48.0, gx1 - gx0, endpoint=False, dtype=np.float32), 1.0)[None, :]
    panel_v = np.mod(np.linspace(0.0, 12.0, gy1 - gy0, endpoint=False, dtype=np.float32), 1.0)[:, None]
    edge = (panel_u < 0.055) | (panel_u > 0.945) | (panel_v < 0.075) | (panel_v > 0.925)
    glint = np.abs(panel_u - (0.20 + panel_v * 0.34)) < 0.022
    pixels[gy0:gy1, gx0:gx1, 3] = (edge | glint).astype(np.float32)

    wy0 = int(size * WATER_V_MIN)
    wy1 = int(size * WATER_V_MAX)
    water_x = np.linspace(0.0, math.tau * 20.0, size, dtype=np.float32)[None, :]
    water = np.array([0.06, 0.46, 0.47], dtype=np.float32)[None, None, :] + (
        0.07 * (0.5 + 0.5 * np.sin(water_x))
    )[:, :, None]
    pixels[wy0:wy1, :, :3] = np.clip(water, 0.02, 0.85)
    pixels[wy0:wy1, :, 3] = 0.82

    atlas = bpy.data.images.new("DomeCommonsPaintedAtlas", size, size, alpha=True)
    atlas.colorspace_settings.name = "sRGB"
    atlas.pixels.foreach_set(pixels.ravel())
    atlas.filepath_raw = str(TEMP_ATLAS)
    atlas.file_format = "PNG"
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.image_settings.color_mode = "RGBA"
    bpy.context.scene.render.image_settings.color_depth = "8"
    atlas.save()
    atlas.pack()
    TEMP_ATLAS.unlink(missing_ok=True)
    return atlas


def make_material(atlas: bpy.types.Image) -> bpy.types.Material:
    material = bpy.data.materials.new("DomeCommonsPaintedMaterial")
    material.use_nodes = True
    material.surface_render_method = "DITHERED"
    material.use_transparency_overlap = False
    material.diffuse_color = (1.0, 1.0, 1.0, 1.0)
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = atlas
    texture.projection = "FLAT"
    texture.extension = "REPEAT"
    texture.interpolation = "Linear"
    alpha_clip = nodes.new("ShaderNodeMath")
    alpha_clip.operation = "ROUND"
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Roughness"].default_value = 0.90
    shader.inputs["Emission Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    shader.inputs["Emission Strength"].default_value = 0.0
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    material.node_tree.links.new(texture.outputs["Alpha"], alpha_clip.inputs[0])
    material.node_tree.links.new(alpha_clip.outputs[0], shader.inputs["Alpha"])
    material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0


def build_mesh(material: bpy.types.Material) -> bpy.types.Object:
    builder = MeshBuilder()
    add_ground(builder)
    add_glass_dome(builder)
    add_airlock_frame(builder)
    add_reclaimed_water_ring(builder)
    mesh = bpy.data.meshes.new("DomeCommonsPlateMesh")
    mesh.from_pydata(builder.vertices, [], builder.faces)
    mesh.update()
    obj = bpy.data.objects.new("DomeCommonsPlate", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(material)
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for polygon, uvs in zip(mesh.polygons, builder.uv_faces):
        polygon.use_smooth = polygon.index < GROUND_SEGMENTS * GROUND_RINGS
        for loop_index, uv in zip(polygon.loop_indices, uvs):
            uv_layer.data[loop_index].uv = uv
    obj["layout_owner"] = "src/town/townLayout.ts"
    obj["site_chain"] = "E8 Dome Commons fresh orbital site"
    obj["base_sha"] = BASE_SHA
    obj["heritage"] = "Pan Monument mounts separately; plate supplies its first reclaimed-water ring"
    obj["flat_walk_law"] = "canonical routes, plaza, and inherited pads stay within +/-0.05m"
    return obj


def save_and_export(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
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


def write_layout_contract(obj: bpy.types.Object) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    document = {
        "baseSha": BASE_SHA,
        "siteChain": "E8 Dome Commons fresh orbital site",
        "sources": {
            "layout": "src/town/townLayout.ts",
            "layoutSha256": sha256(ROOT / "src/town/townLayout.ts"),
            "townBuilder": str(TOWN_BUILDER.relative_to(ROOT)),
            "townBuilderSha256": sha256(TOWN_BUILDER),
            "townScene": str(TOWN_SCENE.relative_to(ROOT)),
            "townSceneSha256": sha256(TOWN_SCENE),
            "dynamoManifest": str(DYNAMO_MANIFEST.relative_to(ROOT)),
            "dynamoManifestSha256": sha256(DYNAMO_MANIFEST),
            "e8Plate": str(E8_PLATE.relative_to(ROOT)),
            "e8PlateSha256": sha256(E8_PLATE),
            "e8Kit": str(E8_KIT.relative_to(ROOT)),
            "e8KitSha256": sha256(E8_KIT),
            "e8Bundle": str(E8_BUNDLE.relative_to(ROOT)),
            "e8BundleSha256": sha256(E8_BUNDLE),
        },
        "production": {
            "blend": str(BLEND.relative_to(ROOT)),
            "glb": str(GLB.relative_to(ROOT)),
            "triangleBudget": TRIANGLE_BUDGET,
            "atlas": [ATLAS_SIZE, ATLAS_SIZE],
            "materialCount": 1,
            "transparency": "depth-writing glTF MASK screen-door; opaque plate and ribs share the material safely",
            "dome": {"radius": DOME_RADIUS, "height": DOME_HEIGHT},
        },
        "canonicalSlots": [
            {"id": slot.id, "position": [slot.position.x, slot.position.y],
             "approach": [slot.approach.x, slot.approach.y], "footprint": [slot.width, slot.depth],
             "targetHeight": 0.0}
            for slot in CANONICAL_SLOTS
        ],
        "orbitalPads": [
            {"id": pad.id, "position": [pad.position.x, pad.position.y], "shape": pad.shape,
             "footprint": [pad.width, pad.depth], "targetHeight": 0.0, "role": pad.role}
            for pad in ORBITAL_PADS
        ],
        "laws": {
            "canonicalFlatWalk": PATH_RELIEF_LIMIT,
            "plazaCenterOpen": PLAZA_CLEAR_RADIUS,
            "panMonument": "unchanged independent heritage GLB; reclaimed-water ring is flush plate geometry",
            "earthCameo": "evidence/sky-rig only; not baked into the production GLB",
            "freshSite": "no Mesa cliff, E7 relay hardware, drowned-square geometry, or prior-era buildings",
        },
        "mesh": obj.name,
    }
    (ARTIFACTS / "dome-commons-layout-contract.json").write_text(json.dumps(document, indent=2) + "\n")


def main() -> None:
    reset_scene()
    atlas = make_atlas()
    material = make_material(atlas)
    obj = build_mesh(material)
    save_and_export(obj)
    write_layout_contract(obj)
    triangles = sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons)
    if triangles > TRIANGLE_BUDGET:
        raise RuntimeError(f"Dome Commons uses {triangles} triangles; budget is {TRIANGLE_BUDGET}")
    print(json.dumps({"blend": str(BLEND), "glb": str(GLB), "triangles": triangles,
                      "baseSha": BASE_SHA, "domeRadius": DOME_RADIUS, "domeHeight": DOME_HEIGHT}, indent=2))


if __name__ == "__main__":
    main()
