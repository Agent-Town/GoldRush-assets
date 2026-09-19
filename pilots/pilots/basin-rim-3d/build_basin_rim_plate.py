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
ARTIFACTS = ROOT / "artifacts/basin-rim-e9"
BLEND = OUT / "basin-rim-plate.blend"
GLB = OUT / "basin-rim-plate.glb"
TEMP_ATLAS = OUT / ".basin-rim-atlas.png"
TOWN_BUILDER = ROOT / "assets/pilots/town-plate-3d/build_town_plate.py"
TOWN_LAYOUT = ROOT / "src/town/townLayout.ts"
TOWN_SCENE = ROOT / "src/town/TownScene.ts"
DYNAMO_MANIFEST = ROOT / "assets/contracts/epoch-2-steamworks/manifest.json"
E9_KIT = ROOT / "assets/raw/kit-era-9.png"
E9_BUNDLE = ROOT / "specs/epoch-saga/e9-redfields-bundle.md"

BASE_SHA = "c272d3a8ba9c36ee2550c7bb55c3fb05edab087e"
ATLAS_SIZE = 2048
TRIANGLE_BUDGET = 20_000
RINGS = 56
SEGMENTS = 112
GROUND_RADIUS = 24.8
PLAZA_CLEAR_RADIUS = 3.1
PATH_SAFE_RADIUS = 1.05
PATH_RELIEF_LIMIT = 0.05
SIDE_V_MAX = 0.16
E1_GREEN_HEX = "#50674c"
E1_GREEN = np.array([0x50, 0x67, 0x4C], dtype=np.float32) / 255.0

PINNED_SOURCES = {
    TOWN_BUILDER: "d46c3799bf395387ac62c22074fa9bc5b2cc2c0be9549c8382ca4395b4e286ce",
    TOWN_LAYOUT: "6d000feac3c0e2e14051f287205e5450b3b701bec4c44e513613a34ea39017d0",
    TOWN_SCENE: "88f0dcfd3daca9626883176b857fe6b7db289fd223908d0f13bf68803c885cd7",
    DYNAMO_MANIFEST: "5e0f6a5b4f850553e560fceac2ef325d47a71826b98bbb8ebbb4b6c1c17e6a20",
    E9_KIT: "88712877e83751d18de297b47fda26e85662de4ca1a0c314d5419d2688b955df",
    E9_BUNDLE: "91a7e4ee14bbb28c6c7ccaa2a4d5eb4a76ea89de72a30259069138c31f26646a",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sources() -> None:
    for path, expected in PINNED_SOURCES.items():
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(f"{path.relative_to(ROOT)} drifted from {BASE_SHA}: {actual} != {expected}")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


verify_sources()
town = load_module("basin_rim_town_layout", TOWN_BUILDER)
Point = town.Point
Slot = town.Slot
CANONICAL_SLOTS = [*town.SLOTS, town.DYNAMO_SLOT]
CANONICAL_ROUTES = town.RADIAL_ROUTES
RING_ROUTE = town.RING_ROUTE


@dataclass(frozen=True)
class BasinPad:
    id: str
    position: Point
    shape: str
    width: float
    depth: float
    role: str


BASIN_PADS = (
    BasinPad("ice-quarry-pad", Point(-7.4, -16.6), "rectangle", 5.6, 3.8, "E9 ice-quarry head"),
    BasinPad("ark-yard-pad", Point(7.0, -16.7), "circle", 6.2, 6.2, "E9 Ark scaffold yard"),
)

CANAL = [
    Point(-22.0, -14.5), Point(-16.0, -12.2), Point(-11.0, -8.0), Point(-7.0, -3.0),
    Point(-3.0, 1.2), Point(1.0, 4.2), Point(7.0, 7.0), Point(13.0, 10.8), Point(22.0, 13.0),
]


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    t = min(1.0, max(0.0, (value - edge0) / max(1e-9, edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def distance_to_polyline(x: float, y: float, points: list[Point], closed: bool = False) -> float:
    return town.distance_to_polyline(x, y, points, closed)


def route_distance(x: float, y: float) -> float:
    radial = min(distance_to_polyline(x, y, route) for route in CANONICAL_ROUTES.values())
    return min(radial, abs(math.hypot(x, y) - 6.0))


def pad_outside_distance(x: float, y: float, pad: BasinPad, margin: float = 0.0) -> float:
    dx, dy = abs(x - pad.position.x), abs(y - pad.position.y)
    if pad.shape == "circle":
        return max(0.0, math.hypot(dx, dy) - pad.width * 0.5 - margin)
    return math.hypot(
        max(0.0, dx - pad.width * 0.5 - margin),
        max(0.0, dy - pad.depth * 0.5 - margin),
    )


def flat_mask(x: float, y: float) -> float:
    mask = smoothstep(PATH_SAFE_RADIUS, PATH_SAFE_RADIUS + 0.8, route_distance(x, y))
    mask = min(mask, smoothstep(PLAZA_CLEAR_RADIUS, PLAZA_CLEAR_RADIUS + 0.8, math.hypot(x, y)))
    for slot in CANONICAL_SLOTS:
        mask = min(mask, smoothstep(0.0, 1.2, town.rectangle_outside_distance(x, y, slot, margin=1.1)))
    for pad in BASIN_PADS:
        mask = min(mask, smoothstep(0.0, 1.2, pad_outside_distance(x, y, pad, margin=1.1)))
    return mask


def terrain_height(x: float, y: float) -> float:
    radius = math.hypot(x, y)
    relief = (
        0.22 * math.sin(x * 0.34 + y * 0.10)
        + 0.15 * math.cos(y * 0.37 - x * 0.08)
        + 0.06 * math.sin((x - y) * 0.83)
    ) * smoothstep(7.5, 17.0, radius)
    basin_distance = math.hypot(x - 14.0, y - 12.0)
    basin = -1.52 * (1.0 - smoothstep(5.0, 12.0, basin_distance))
    quarry_distance = math.hypot(x + 18.0, y + 13.0)
    quarry_scarp = 1.35 * (1.0 - smoothstep(4.0, 9.5, quarry_distance))
    rim = 0.36 * smoothstep(18.0, 24.5, radius)
    canal = -0.045 * math.exp(-((distance_to_polyline(x, y, CANAL) / 1.05) ** 4))
    height = (relief + basin + quarry_scarp + rim + canal) * flat_mask(x, y)
    height += -0.007 * math.exp(-((route_distance(x, y) / 0.58) ** 4))
    return height


def distance_field(world_x: np.ndarray, world_y: np.ndarray, points: list[Point]) -> np.ndarray:
    result = np.full(world_x.shape, np.inf, dtype=np.float32)
    for start, end in zip(points, points[1:]):
        dx, dy = end.x - start.x, end.y - start.y
        length_sq = max(1e-9, dx * dx + dy * dy)
        t = np.clip(((world_x - start.x) * dx + (world_y - start.y) * dy) / length_sq, 0.0, 1.0)
        result = np.minimum(result, np.hypot(world_x - (start.x + dx * t), world_y - (start.y + dy * t)))
    return result


def make_atlas() -> bpy.types.Image:
    top_start = int(ATLAS_SIZE * SIDE_V_MAX)
    height = ATLAS_SIZE - top_start
    x_axis = np.linspace(-GROUND_RADIUS, GROUND_RADIUS, ATLAS_SIZE, dtype=np.float32)
    y_axis = np.linspace(-GROUND_RADIUS, GROUND_RADIUS, height, dtype=np.float32)
    world_x, world_y = np.meshgrid(x_axis, y_axis)
    radius = np.hypot(world_x, world_y)
    noise = (
        0.035 * np.sin(world_x * 0.22 + world_y * 0.09)
        + 0.022 * np.cos(world_y * 0.43 - world_x * 0.11)
        + 0.014 * np.sin((world_x + world_y) * 1.7)
    )
    red = np.array([0.48, 0.17, 0.075], dtype=np.float32)
    rgb = red[None, None, :] + noise[:, :, None]
    hatch = np.mod(np.sin(world_x * 12.9898 + world_y * 78.233) * 43758.5453, 1.0)
    stipple = (hatch > 0.992).astype(np.float32)
    rgb *= 1.0 - stipple[:, :, None] * 0.30

    canal_distance = distance_field(world_x, world_y, CANAL)
    cut = np.exp(-((canal_distance / 1.15) ** 4))
    channel = np.array([0.24, 0.11, 0.065], dtype=np.float32)
    rgb = rgb * (1.0 - cut[:, :, None] * 0.55) + channel[None, None, :] * cut[:, :, None] * 0.55
    # The first persisted green is deliberately short; later growth belongs to tile persistence.
    first_green = cut * np.clip((-world_x - 8.0) / 9.0, 0.0, 1.0)
    rgb = rgb * (1.0 - first_green[:, :, None]) + E1_GREEN[None, None, :] * first_green[:, :, None]
    wet = cut * np.clip((world_x + 3.0) / 14.0, 0.0, 0.82)
    wet_color = np.array([0.10, 0.34, 0.33], dtype=np.float32)
    rgb = rgb * (1.0 - wet[:, :, None] * 0.54) + wet_color[None, None, :] * wet[:, :, None] * 0.54

    route_fields = [distance_field(world_x, world_y, route) for route in CANONICAL_ROUTES.values()]
    road_distance = np.minimum.reduce([*route_fields, np.abs(radius - 6.0)])
    road = np.exp(-((road_distance / 0.67) ** 4))
    rgb *= 1.0 - road[:, :, None] * 0.17
    edge = np.clip((radius - 18.0) / 8.0, 0.0, 1.0)
    rgb *= 1.0 - edge[:, :, None] * 0.14
    # Keep a literal swatch core after all wear/edge grading. The callback is a
    # color contract, not merely a visually similar green.
    rgb[first_green >= 0.985] = E1_GREEN

    pixels = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    pixels[top_start:, :, :3] = np.clip(rgb, 0.025, 0.92)
    side_y = np.linspace(0.0, 1.0, top_start, dtype=np.float32)[:, None]
    side_x = np.linspace(0.0, math.tau, ATLAS_SIZE, dtype=np.float32)[None, :]
    bands = 0.04 * np.sin(side_y * 12.0 * math.pi + np.sin(side_x * 4.0))
    side = np.array([0.27, 0.085, 0.035], dtype=np.float32)[None, None, :] + bands[:, :, None]
    pixels[:top_start, :, :3] = np.clip(side, 0.025, 0.55)

    image = bpy.data.images.new("BasinRimPaintedAtlas", ATLAS_SIZE, ATLAS_SIZE, alpha=False)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(pixels.ravel())
    image.filepath_raw = str(TEMP_ATLAS)
    image.file_format = "PNG"
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.image_settings.color_mode = "RGB"
    bpy.context.scene.render.image_settings.color_depth = "8"
    image.save()
    image.pack()
    TEMP_ATLAS.unlink(missing_ok=True)
    return image


def make_material(atlas: bpy.types.Image) -> bpy.types.Material:
    material = bpy.data.materials.new("BasinRimPaintedMaterial")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = atlas
    texture.extension = "REPEAT"
    texture.interpolation = "Linear"
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Roughness"].default_value = 0.93
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def top_uv(x: float, y: float) -> tuple[float, float]:
    return ((x / (GROUND_RADIUS * 2.0)) + 0.5, SIDE_V_MAX + ((y / (GROUND_RADIUS * 2.0)) + 0.5) * (1.0 - SIDE_V_MAX))


def build_plate(material: bpy.types.Material) -> bpy.types.Object:
    vertices = [(0.0, 0.0, terrain_height(0.0, 0.0))]
    for ring in range(1, RINGS + 1):
        fraction = ring / RINGS
        for segment in range(SEGMENTS):
            angle = segment / SEGMENTS * math.tau
            radius = GROUND_RADIUS * fraction * (1.0 + 0.012 * math.sin(angle * 5.0 + 0.3))
            x, y = math.cos(angle) * radius, math.sin(angle) * radius
            vertices.append((x, y, terrain_height(x, y)))

    faces: list[tuple[int, ...]] = []
    uvs: list[list[tuple[float, float]]] = []
    for segment in range(SEGMENTS):
        face = (0, 1 + segment, 1 + (segment + 1) % SEGMENTS)
        faces.append(face)
        uvs.append([top_uv(*vertices[index][:2]) for index in face])
    for ring in range(1, RINGS):
        inner, outer = 1 + (ring - 1) * SEGMENTS, 1 + ring * SEGMENTS
        for segment in range(SEGMENTS):
            following = (segment + 1) % SEGMENTS
            face = (inner + segment, outer + segment, outer + following, inner + following)
            faces.append(face)
            uvs.append([top_uv(*vertices[index][:2]) for index in face])

    outer = 1 + (RINGS - 1) * SEGMENTS
    bottom = len(vertices)
    for segment in range(SEGMENTS):
        x, y, _ = vertices[outer + segment]
        vertices.append((x, y, -2.05))
    for segment in range(SEGMENTS):
        following = (segment + 1) % SEGMENTS
        face = (outer + segment, bottom + segment, bottom + following, outer + following)
        u0, u1 = segment / SEGMENTS, (segment + 1) / SEGMENTS
        faces.append(face)
        uvs.append([(u0, SIDE_V_MAX), (u0, 0.0), (u1, 0.0), (u1, SIDE_V_MAX)])

    mesh = bpy.data.meshes.new("BasinRimPlateMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    plate = bpy.data.objects.new("BasinRimPlate", mesh)
    bpy.context.collection.objects.link(plate)
    mesh.materials.append(material)
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for polygon, face_uvs in zip(mesh.polygons, uvs):
        polygon.use_smooth = polygon.index < SEGMENTS * RINGS
        for loop_index, uv in zip(polygon.loop_indices, face_uvs):
            uv_layer.data[loop_index].uv = uv
    plate["base_sha"] = BASE_SHA
    plate["layout_owner"] = "src/town/townLayout.ts"
    plate["e1_green_hex"] = E1_GREEN_HEX
    plate["heritage"] = "Pan Monument mounts separately, dry at the basin rim"
    return plate


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0


def save_and_export(plate: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    plate.select_set(True)
    bpy.context.view_layer.objects.active = plate
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.export_scene.gltf(
        filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT",
    )


def write_contract(triangles: int) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    document = {
        "baseSha": BASE_SHA,
        "site": "E9 Basin Rim fresh red-world town plate",
        "sources": {str(path.relative_to(ROOT)): digest for path, digest in PINNED_SOURCES.items()},
        "production": {
            "blend": str(BLEND.relative_to(ROOT)), "glb": str(GLB.relative_to(ROOT)),
            "triangles": triangles, "triangleBudget": TRIANGLE_BUDGET,
            "materialCount": 1, "atlas": [ATLAS_SIZE, ATLAS_SIZE], "e1GreenHex": E1_GREEN_HEX,
        },
        "canonicalSlots": [
            {"id": slot.id, "position": [slot.position.x, slot.position.y], "footprint": [slot.width, slot.depth]}
            for slot in CANONICAL_SLOTS
        ],
        "basinPads": [
            {"id": pad.id, "position": [pad.position.x, pad.position.y], "shape": pad.shape,
             "footprint": [pad.width, pad.depth], "role": pad.role}
            for pad in BASIN_PADS
        ],
        "laws": {
            "flatWalkLimit": PATH_RELIEF_LIMIT,
            "greenPersistenceBoundary": "plate shows only the first short E1-green seam; later spread is tile-persistence-owned",
            "panMonument": "unchanged independent heritage GLB; dry until open-sky canal water arrives",
        },
    }
    (ARTIFACTS / "basin-rim-layout-contract.json").write_text(json.dumps(document, indent=2) + "\n")


def main() -> None:
    reset_scene()
    material = make_material(make_atlas())
    plate = build_plate(material)
    triangles = sum(len(polygon.vertices) - 2 for polygon in plate.data.polygons)
    if triangles > TRIANGLE_BUDGET:
        raise RuntimeError(f"Basin Rim uses {triangles} triangles; budget is {TRIANGLE_BUDGET}")
    save_and_export(plate)
    write_contract(triangles)
    print(json.dumps({"glb": str(GLB), "triangles": triangles, "baseSha": BASE_SHA}, indent=2))


if __name__ == "__main__":
    main()
