"""Build the unique E8 campaign terrain/panorama pair.

Low Orbit is a render-only orbital scaffold/debris landform.  The published
mask table remains authoritative for zero-G movement, collision, placement,
spawns, projectiles, debris semantics, and the handhold route.  Far Side and
Eclipse deliberately reuse the accepted Mare Claim tile and require no sculpt.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

import bpy
import mathutils
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"
FACTORY = ROOT / "assets/contracts/epoch-8-orbital/contracts.json"
TABLE_PATH = ROOT / "assets/contracts/epoch-8-orbital/mask-tables/e8-low-orbit.json"
KIT = ROOT / "assets/processed/kit-era-8.png"
PLATE = ROOT / "assets/raw/plate-e8-bld-set.png"
MARE_ATLAS = OUT / "mare-claim-terrain-atlas.png"
CLAW = ROOT / "assets/pilots/salvage-claw-3d/salvage-claw.glb"
WIDTH = HEIGHT = 128.0
SEGMENTS = 128
ATLAS_SIZE = 2048
PANORAMA_SEGMENTS = 192
PANORAMA_ROWS = 8


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


e3 = load_module("e8_extra_e3_helpers", OUT / "build_e3_contract_terrains.py")
claim = e3.claim
claim.mathutils = mathutils

PROFILE = {
    "contractId": "e8-low-orbit",
    "stem": "low-orbit-terrain",
    "object": "LowOrbitTerrain",
    "mesh": "LowOrbitTerrainMesh",
    "material": "LowOrbitPaintedScaffoldMaterial",
    "atlas": "LowOrbitPaintedScaffoldAtlas",
    "width": WIDTH,
    "height": HEIGHT,
    "theme": "the Salvage King's Claw rebuilt as three battered orbital decks joined by a handhold spine between two drifting debris fields",
    "epoch": "Epoch 8 orbital claim",
    "shared": [
        "silver-and-teal over parchment",
        "warm grey stippled engraving, never cold photoreal",
        "suit brass and glass",
        "honey-gold work light",
        "vacuum negative space drawn rather than filled",
    ],
    "unique": [
        "non-ground three-deck silhouette",
        "central claw carcass yard",
        "load-bearing handhold spine",
        "opposed north and south debris fields",
    ],
}

LANDMARK_MOUNTS = [
    {"id": "west-scaffold-handhold-frame", "position": [-48.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0], "asset": ""},
    {"id": "claw-carcass-rig", "position": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0], "asset": ""},
    {"id": "east-scaffold-handhold-frame", "position": [48.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0], "asset": ""},
    {"id": "north-debris-catcher", "position": [-28.0, 0.0, 43.0], "rotation": [0.0, 0.22, 0.0], "scale": [1.0, 1.0, 1.0], "asset": ""},
    {"id": "south-return-beacon", "position": [31.0, 0.0, -43.0], "rotation": [0.0, -0.18, 0.0], "scale": [1.0, 1.0, 1.0], "asset": ""},
]


def smoothstep(edge0, edge1, value):
    value = np.asarray(value, dtype=np.float32)
    t = np.clip((value - edge0) / max(edge1 - edge0, 0.0001), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def gaussian(x, z, cx, cz, sx, sz):
    return np.exp(-0.5 * (((x - cx) / sx) ** 2 + ((z - cz) / sz) ** 2))


def rectangle_mask(x, z, zone, feather=1.0, margin=0.0):
    return (
        smoothstep(zone["minX"] - margin - feather, zone["minX"] - margin, x)
        * (1.0 - smoothstep(zone["maxX"] + margin, zone["maxX"] + margin + feather, x))
        * smoothstep(zone["minZ"] - margin - feather, zone["minZ"] - margin, z)
        * (1.0 - smoothstep(zone["maxZ"] + margin, zone["maxZ"] + margin + feather, z))
    )


def segment_mask(x, z, start, end, radius):
    ax, az = float(start["x"]), float(start["z"])
    bx, bz = float(end["x"]), float(end["z"])
    dx, dz = bx - ax, bz - az
    denom = max(dx * dx + dz * dz, 1e-6)
    amount = np.clip(((x - ax) * dx + (z - az) * dz) / denom, 0.0, 1.0)
    distance = np.hypot(x - (ax + amount * dx), z - (az + amount * dz))
    return 1.0 - smoothstep(radius * 0.72, radius, distance)


def documents():
    contracts = json.loads(FACTORY.read_text(encoding="utf-8"))["contracts"]
    matches = [entry for entry in contracts if entry["id"] == PROFILE["contractId"]]
    if len(matches) != 1:
        raise ValueError("expected exactly one Low Orbit factory contract")
    table = json.loads(TABLE_PATH.read_text(encoding="utf-8"))
    truth = table["maskTruth"]
    if truth["tileId"] != PROFILE["contractId"] or truth["dimensions"] != {"width": 128, "height": 128}:
        raise ValueError("Low Orbit authored identity or dimensions changed")
    return matches[0], table


def height_function(table):
    truth = table["maskTruth"]
    zones = {zone["id"]: zone for zone in truth["buildZones"]}
    route = truth["handholdRoutes"][0]["points"]
    cell_guard = math.hypot(WIDTH / SEGMENTS, HEIGHT / SEGMENTS) + 0.12
    targets = {"west-scaffold-deck": 0.72, "claw-carcass-yard": 0.24, "east-scaffold-deck": 1.08}

    def height(x, z):
        xx = np.asarray(x, dtype=np.float32)
        zz = np.asarray(z, dtype=np.float32)
        # The whole tile is an illustrated debris web, not literal walkable
        # ground. Runtime remains planar; this is the render-height socket.
        grain = np.sin(xx * 0.23 + zz * 0.17) * 0.10 + np.sin(xx * 0.51 - zz * 0.29) * 0.045
        surface = -5.35 + grain
        surface += gaussian(xx, zz, -43.0, 42.0, 13.0, 9.0) * 1.75
        surface += gaussian(xx, zz, -7.0, 38.0, 18.0, 10.0) * 1.10
        surface += gaussian(xx, zz, 38.0, 44.0, 11.0, 8.0) * 2.05
        surface += gaussian(xx, zz, -36.0, -43.0, 12.0, 9.0) * 1.35
        surface += gaussian(xx, zz, 8.0, -39.0, 18.0, 10.0) * 1.72
        surface += gaussian(xx, zz, 45.0, -45.0, 10.0, 7.0) * 1.10
        surface -= gaussian(xx, zz, 0.0, 0.0, 46.0, 20.0) * 0.48
        # The authored route becomes a readable permanent spine. Its semantic
        # use remains code-owned; here it only joins the three visual decks.
        spine = np.zeros_like(surface)
        for start, end in zip(route, route[1:]):
            spine = np.maximum(spine, segment_mask(xx, zz, start, end, 4.0))
        spine_target = 0.44 + 0.10 * np.sin(xx * 0.065)
        surface = surface * (1.0 - spine * 0.92) + spine_target * spine * 0.92
        # One-cell guard bands ensure every triangle crossing a published
        # rectangle stays flat under independent barycentric surface sampling.
        for identifier, target in targets.items():
            zone = zones[identifier]
            shoulder = rectangle_mask(xx, zz, zone, feather=2.4, margin=cell_guard)
            surface = surface * (1.0 - shoulder) + target * shoulder
            exact = (
                (xx >= zone["minX"] - cell_guard)
                & (xx <= zone["maxX"] + cell_guard)
                & (zz >= zone["minZ"] - cell_guard)
                & (zz <= zone["maxZ"] + cell_guard)
            )
            surface = np.where(exact, target, surface)
        edge = smoothstep(57.0, 64.0, np.maximum(np.abs(xx), np.abs(zz)))
        surface = surface * (1.0 - edge * 0.55) + (-5.85) * edge * 0.55
        return np.clip(surface, -6.1, 2.25)

    return height


def make_atlas(table):
    kit = claim.image_pixels(KIT)
    plate = claim.image_pixels(PLATE)
    mare = claim.image_pixels(MARE_ATLAS) if MARE_ATLAS.is_file() else kit
    axis = np.linspace(0.0, 1.0, ATLAS_SIZE, dtype=np.float32)
    u, v = np.meshgrid(axis, axis)
    x, z = (u - 0.5) * WIDTH, (v - 0.5) * HEIGHT
    paper = claim.tiled_sample(kit, u, v, 3.4, 0.18, 0.41)
    stamped = claim.tiled_sample(plate, 1.0 - v, u, 4.1, 0.31, 0.17)
    lunar = claim.tiled_sample(mare, u + np.sin(v * math.tau * 2.0) * 0.008, v, 2.5, 0.47, 0.13)
    luma = claim.luminance(stamped)
    ink = np.clip((np.mean(luma) - luma) * 5.0, 0.0, 1.0)
    macro = np.clip(0.64 + np.sin(x * 0.061 + z * 0.047) * 0.12 + np.sin(x * 0.13 - z * 0.071) * 0.06, 0.35, 0.88)
    warm_grey = np.asarray((0.325, 0.338, 0.322), dtype=np.float32)
    atlas = warm_grey[None, None, :] * macro[..., None]
    atlas = atlas * 0.66 + lunar * np.asarray((0.32, 0.34, 0.32), dtype=np.float32) * 0.34
    atlas *= 1.0 - ink[..., None] * 0.18
    hatch_a = smoothstep(0.80, 0.96, np.sin(x * 1.18 + z * 0.72 + np.sin(z * 0.15)) * 0.5 + 0.5)
    hatch_b = smoothstep(0.87, 0.98, np.sin(x * 0.63 - z * 1.51 + np.sin(x * 0.22)) * 0.5 + 0.5)
    atlas *= 1.0 - (hatch_a * 0.052 + hatch_b * 0.034)[..., None]

    truth = table["maskTruth"]
    deck_tone = paper * np.asarray((0.30, 0.39, 0.38), dtype=np.float32)
    teal = np.asarray((0.050, 0.235, 0.225), dtype=np.float32)
    brass = np.asarray((0.43, 0.245, 0.085), dtype=np.float32)
    soot = stamped * np.asarray((0.085, 0.090, 0.090), dtype=np.float32)
    for zone in truth["orbitalScaffoldZones"]:
        pad = rectangle_mask(x, z, zone, 1.3)
        edge = np.clip(rectangle_mask(x, z, zone, 2.0) - rectangle_mask(x, z, zone, 0.28), 0.0, 1.0)
        scuff = pad * np.clip(0.58 + np.sin(x * 0.73 - z * 0.31) * 0.24, 0.16, 0.92)
        atlas = atlas * (1.0 - scuff[..., None] * 0.42) + deck_tone * scuff[..., None] * 0.42
        atlas = atlas * (1.0 - edge[..., None] * 0.44) + soot * edge[..., None] * 0.44
        weld = pad * smoothstep(0.88, 0.98, np.sin(x * 1.93 + z * 0.57) * 0.5 + 0.5)
        atlas = atlas * (1.0 - weld[..., None] * 0.16) + teal[None, None, :] * weld[..., None] * 0.16
    route = truth["handholdRoutes"][0]["points"]
    route_core = np.zeros_like(x)
    route_shoulder = np.zeros_like(x)
    for start, end in zip(route, route[1:]):
        route_core = np.maximum(route_core, segment_mask(x, z, start, end, 0.64))
        route_shoulder = np.maximum(route_shoulder, segment_mask(x, z, start, end, 2.4))
    atlas = atlas * (1.0 - route_shoulder[..., None] * 0.20) + teal[None, None, :] * route_shoulder[..., None] * 0.20
    atlas = atlas * (1.0 - route_core[..., None] * 0.72) + brass[None, None, :] * route_core[..., None] * 0.72
    debris_union = np.zeros_like(x)
    debris_breakup = np.zeros_like(x)
    for index, field in enumerate(truth["debrisFields"]):
        region = rectangle_mask(x, z, field, 2.2)
        broken = region * np.clip(0.50 + np.sin(x * (0.41 + index * 0.07) + z * 0.53) * 0.30, 0.05, 0.96)
        debris_union = np.maximum(debris_union, region)
        debris_breakup = np.maximum(debris_breakup, broken)
        atlas = atlas * (1.0 - broken[..., None] * 0.44) + soot * broken[..., None] * 0.44
    impacts = ((-46, 42, 4.0), (-12, 34, 2.4), (38, 45, 3.6), (-33, -43, 3.1), (7, -39, 4.4), (46, -46, 2.2))
    for cx, cz, radius in impacts:
        distance = np.hypot(x - cx, z - cz)
        pit = np.exp(-((distance / (radius * 0.56)) ** 2))
        lip = np.exp(-(((distance - radius) / 0.42) ** 2))
        atlas = atlas * (1.0 - pit[..., None] * 0.38) + soot * pit[..., None] * 0.38
        atlas = atlas * (1.0 - lip[..., None] * 0.20) + brass[None, None, :] * lip[..., None] * 0.20
    deck_union = np.zeros_like(x)
    for zone in truth["orbitalScaffoldZones"]:
        deck_union = np.maximum(deck_union, rectangle_mask(x, z, zone, 3.2))
    structure = np.clip(
        deck_union + route_shoulder * 0.72 + debris_union * 0.28 + debris_breakup * 0.58,
        0.0,
        1.0,
    )
    # Everything outside the three decks, connecting spine, and two broken
    # debris fields is painted vacuum-black. The heightfield still covers the
    # planar tile, but at run scale that non-structure disappears into space.
    void = 1.0 - structure
    void_tone = np.asarray((0.006, 0.009, 0.010), dtype=np.float32)
    atlas = atlas * (1.0 - void[..., None] * 0.92) + void_tone[None, None, :] * void[..., None] * 0.92
    atlas = np.clip(atlas * 0.96 + np.asarray((0.003, 0.004, 0.004), dtype=np.float32), 0.003, 0.66)
    rgba = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    rgba[..., :3] = atlas
    path = OUT / "low-orbit-terrain-atlas.png"
    image = bpy.data.images.new(PROFILE["atlas"], ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image, path


def make_terrain(table, height_at, material):
    vertices, uvs, faces = [], [], []
    for zi in range(SEGMENTS + 1):
        game_z = -HEIGHT * 0.5 + HEIGHT * zi / SEGMENTS
        for xi in range(SEGMENTS + 1):
            x = -WIDTH * 0.5 + WIDTH * xi / SEGMENTS
            vertices.append((x, -game_z, float(height_at(x, game_z))))
            uvs.append((xi / SEGMENTS, zi / SEGMENTS))
    row = SEGMENTS + 1
    for zi in range(SEGMENTS):
        for xi in range(SEGMENTS):
            a = zi * row + xi
            faces.extend(((a, a + row + 1, a + 1), (a, a + row, a + row + 1)))
    mesh = bpy.data.meshes.new(PROFILE["mesh"])
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        polygon.use_smooth = False
        for loop_index in polygon.loop_indices:
            uv.data[loop_index].uv = uvs[mesh.loops[loop_index].vertex_index]
    terrain = bpy.data.objects.new(PROFILE["object"], mesh)
    bpy.context.collection.objects.link(terrain)
    mesh.materials.append(material)
    terrain["render_only"] = True
    terrain["sim_authority"] = "published mask table and planar simulation; unchanged"
    terrain["height_socket"] = "Terrain.visualY"
    terrain["contract_id"] = PROFILE["contractId"]
    terrain["tile_id"] = table["maskTruth"]["tileId"]
    terrain["mask_table"] = str(TABLE_PATH.relative_to(ROOT))
    terrain["load_bearing_sites_flat"] = True
    terrain["landmarks_frozen"] = False
    terrain["landmark_mount_ids"] = json.dumps([mount["id"] for mount in LANDMARK_MOUNTS])
    terrain["runtime_zero_g_absent"] = True
    return terrain


def preview_materials():
    return {
        "iron": claim.make_render_material("LowOrbitVerdictIron", (0.12, 0.14, 0.14), 0.72, 0.35),
        "silver": claim.make_render_material("LowOrbitVerdictSilver", (0.38, 0.41, 0.39), 0.58, 0.48),
        "teal": claim.make_render_material("LowOrbitVerdictTeal", (0.035, 0.35, 0.33), 0.48, 0.22),
        "brass": claim.make_render_material("LowOrbitVerdictBrass", (0.46, 0.25, 0.075), 0.56, 0.38),
        "mask": claim.make_render_material("LowOrbitBuildMask", (0.035, 0.88, 0.78), 0.48, 0.08),
        "danger": claim.make_render_material("LowOrbitDebrisMask", (0.93, 0.17, 0.045), 0.48, 0.08),
        "route": claim.make_render_material("LowOrbitRouteMask", (0.98, 0.64, 0.12), 0.42, 0.12),
    }


def rectangle_points(zone, height_at, lift=0.48):
    return [(x, z, float(height_at(x, z)) + lift) for x, z in (
        (zone["minX"], zone["minZ"]), (zone["maxX"], zone["minZ"]),
        (zone["maxX"], zone["maxZ"]), (zone["minX"], zone["maxZ"]),
        (zone["minX"], zone["minZ"]),
    )]


def import_claw_preview(height_at):
    if not CLAW.is_file():
        return []
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(CLAW))
    imported = [obj for obj in bpy.data.objects if obj not in before]
    meshes = [obj for obj in imported if obj.type == "MESH"]
    if not meshes:
        return imported
    corners = [obj.matrix_world @ mathutils.Vector(corner) for obj in meshes for corner in obj.bound_box]
    min_x, max_x = min(point.x for point in corners), max(point.x for point in corners)
    min_y, max_y = min(point.y for point in corners), max(point.y for point in corners)
    min_z = min(point.z for point in corners)
    span = max(max_x - min_x, max_y - min_y, 0.001)
    scale = 24.0 / span
    center = mathutils.Vector(((min_x + max_x) * 0.5, (min_y + max_y) * 0.5, min_z))
    target = mathutils.Vector((0.0, 0.0, float(height_at(0.0, 0.0)) + 0.18))
    for obj in imported:
        obj.scale *= scale
        obj.location = target + (obj.location - center) * scale
        obj.rotation_euler.z += math.radians(7.0)
        obj.name = f"RenderHelperClaw.{obj.name}"
    return imported


def add_preview(table, height_at, materials):
    objects = import_claw_preview(height_at)
    for zone in table["maskTruth"]["orbitalScaffoldZones"]:
        x, z = (zone["minX"] + zone["maxX"]) * 0.5, (zone["minZ"] + zone["maxZ"]) * 0.5
        base = float(height_at(x, z)) + 0.08
        width, depth = zone["maxX"] - zone["minX"], zone["maxZ"] - zone["minZ"]
        objects.append(claim.add_box_game(f"RenderHelperDeck.{zone['id']}", x, z, base, (width * 0.88, depth * 0.82, 0.28), materials["iron"], bevel=0.04))
        for side in (-1.0, 1.0):
            objects.append(claim.add_box_game(f"RenderHelperDeckRail.{zone['id']}.{side}", x, z + side * depth * 0.38, base + 0.30, (width * 0.82, 0.16, 0.52), materials["silver"], bevel=0.025))
    route = table["maskTruth"]["handholdRoutes"][0]["points"]
    points = [(point["x"], point["z"], float(height_at(point["x"], point["z"])) + 1.0) for point in route]
    objects.append(claim.add_curve("RenderHelperHandholdSpine", points, 0.18, materials["brass"]))
    rng = np.random.default_rng(8008)
    for field_index, field in enumerate(table["maskTruth"]["debrisFields"]):
        for index in range(18):
            x = float(rng.uniform(field["minX"] + 2, field["maxX"] - 2))
            z = float(rng.uniform(field["minZ"] + 2, field["maxZ"] - 2))
            size = float(rng.uniform(0.28, 1.10))
            objects.append(claim.add_rock(f"RenderHelperOrbitalDebris.{field_index}.{index}", x, z, (size * rng.uniform(0.8, 2.1), size * rng.uniform(0.5, 1.4), size * rng.uniform(0.3, 0.9)), materials["iron" if index % 3 else "brass"], yaw=float(rng.uniform(-math.pi, math.pi))))
    return objects


def add_overlay(table, height_at, materials):
    objects = []
    for zone in table["maskTruth"]["buildZones"]:
        objects.append(claim.add_curve(f"RenderHelperBuildMask.{zone['id']}", rectangle_points(zone, height_at, 0.72), 0.20, materials["mask"]))
    for field in table["maskTruth"]["debrisFields"]:
        objects.append(claim.add_curve(f"RenderHelperDebrisMask.{field['id']}", rectangle_points(field, height_at, 0.88), 0.16, materials["danger"]))
    route = table["maskTruth"]["handholdRoutes"][0]["points"]
    points = [(point["x"], point["z"], float(height_at(point["x"], point["z"])) + 1.16) for point in route]
    objects.append(claim.add_curve("RenderHelperRouteMask.claw-yard-handhold-spine", points, 0.24, materials["route"]))
    return objects


def add_lighting(height_at):
    world = bpy.data.worlds.new("LowOrbitVacuumWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.006, 0.008, 0.010, 1.0)
    background.inputs["Strength"].default_value = 0.16
    lights = []
    sun_data = bpy.data.lights.new("LowOrbitParchmentRake", "SUN")
    sun_data.energy = 3.2
    sun_data.color = (0.76, 0.72, 0.61)
    sun_data.angle = math.radians(5.0)
    sun = bpy.data.objects.new("LowOrbitParchmentRake", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.location = (-48.0, -26.0, 54.0)
    claim.aim_at(sun, (0.0, 0.0, 0.0))
    lights.append(sun)
    fill_data = bpy.data.lights.new("LowOrbitTealFill", "AREA")
    fill_data.energy = 420
    fill_data.color = (0.08, 0.30, 0.31)
    fill_data.shape = "DISK"
    fill_data.size = 34.0
    fill = bpy.data.objects.new("LowOrbitTealFill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = (42.0, 36.0, 23.0)
    claim.aim_at(fill, (12.0, 0.0, 0.0))
    lights.append(fill)
    for index, (x, z) in enumerate(((-37, 0), (0, -2), (37, 0))):
        data = bpy.data.lights.new(f"LowOrbitWorkLight.{index}", "POINT")
        data.energy = 580 if index == 1 else 390
        data.color = (1.0, 0.58, 0.19) if index == 1 else (0.08, 0.70, 0.67)
        data.shadow_soft_size = 0.9
        light = bpy.data.objects.new(f"LowOrbitWorkLight.{index}", data)
        bpy.context.collection.objects.link(light)
        light.location = (x, -z, float(height_at(x, z)) + 3.0)
        lights.append(light)
    return lights


def make_panorama_atlas():
    kit = claim.image_pixels(KIT)
    plate = claim.image_pixels(PLATE)
    axis = np.linspace(0.0, 1.0, ATLAS_SIZE, dtype=np.float32)
    u, v = np.meshgrid(axis, axis)
    stamped = claim.tiled_sample(plate, u, v, 3.3, 0.29, 0.44)
    kit_sample = claim.tiled_sample(kit, 1.0 - v, u, 2.7, 0.17, 0.23)
    plate_ink = np.clip((np.mean(claim.luminance(stamped)) - claim.luminance(stamped)) * 4.8, 0.0, 1.0)
    horizon = smoothstep(0.64, 0.98, v)
    zenith_color = np.asarray((0.008, 0.011, 0.013), dtype=np.float32)
    horizon_color = np.asarray((0.075, 0.078, 0.074), dtype=np.float32)
    atlas = zenith_color[None, None, :] * (1.0 - horizon[..., None]) + horizon_color[None, None, :] * horizon[..., None]
    atlas *= 1.0 - plate_ink[..., None] * (smoothstep(0.70, 0.94, v) * 0.055)[..., None]
    # Vacuum is drawn emptiness: sparse stipple, four unequal debris edits,
    # and one large soft Earth limb. No cloud ceiling and no repeated strip.
    noise = np.random.default_rng(808).random((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
    stars = smoothstep(0.99982, 0.99998, noise) * (1.0 - smoothstep(0.70, 0.90, v))
    star_tone = np.asarray((0.46, 0.46, 0.39), dtype=np.float32)
    atlas = atlas * (1.0 - stars[..., None] * 0.38) + star_tone[None, None, :] * stars[..., None] * 0.38
    debris = np.zeros_like(v)
    for center_u, center_v, width_u, width_v in ((0.07, 0.77, 0.045, 0.025), (0.31, 0.70, 0.026, 0.038), (0.59, 0.82, 0.055, 0.022), (0.88, 0.73, 0.032, 0.030)):
        du = np.abs(np.mod(u - center_u + 0.5, 1.0) - 0.5)
        debris = np.maximum(debris, np.exp(-((du / width_u) ** 4) - (((v - center_v) / width_v) ** 2)))
    debris_tone = np.asarray((0.045, 0.052, 0.052), dtype=np.float32)
    atlas = atlas * (1.0 - debris[..., None] * 0.72) + debris_tone[None, None, :] * debris[..., None] * 0.72
    earth_du = np.abs(np.mod(u - 0.76 + 0.5, 1.0) - 0.5)
    # Angular u is visually magnified on the cylinder. This intentionally
    # narrow atlas ellipse projects as a restrained round comfort cameo.
    earth_radius = np.sqrt((earth_du / 0.0115) ** 2 + ((v - 0.50) / 0.070) ** 2)
    earth_disk = 1.0 - smoothstep(0.90, 1.02, earth_radius)
    earth_land = np.clip(np.sin((u - 0.76) * 84 + v * 31) * 0.35 + np.sin((u - 0.76) * 41 - v * 47) * 0.25 + 0.48, 0.0, 1.0) * earth_disk
    ocean = np.asarray((0.10, 0.30, 0.34), dtype=np.float32)
    land = np.asarray((0.34, 0.46, 0.35), dtype=np.float32)
    earth = ocean[None, None, :] * (1.0 - earth_land[..., None] * 0.58) + land[None, None, :] * earth_land[..., None] * 0.58
    atlas = atlas * (1.0 - earth_disk[..., None] * 0.94) + earth * earth_disk[..., None] * 0.94
    ground = smoothstep(0.82, 0.99, v)[..., None]
    ground_detail = stamped * np.asarray((0.14, 0.16, 0.15), dtype=np.float32) + kit_sample * np.asarray((0.05, 0.07, 0.065), dtype=np.float32)
    atlas = atlas * (1.0 - ground * 0.78) + ground_detail * ground * 0.78
    rgba = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    rgba[..., :3] = np.clip(atlas, 0.003, 0.70)
    path = OUT / "low-orbit-panorama-atlas.png"
    image = bpy.data.images.new("LowOrbitPanoramaAtlas", ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image, path


def make_panorama_material(atlas):
    material = bpy.data.materials.new("LowOrbitPanoramaPaintedMaterial")
    material.use_nodes = True
    material.use_backface_culling = False
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = atlas
    texture.extension = "REPEAT"
    texture.interpolation = "Linear"
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Roughness"].default_value = 1.0
    shader.inputs["Metallic"].default_value = 0.0
    emission_color = shader.inputs.get("Emission Color") or shader.inputs.get("Emission")
    emission_strength = shader.inputs.get("Emission Strength")
    if emission_strength:
        emission_strength.default_value = 1.0
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    if emission_color:
        material.node_tree.links.new(texture.outputs["Color"], emission_color)
    material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def boundary_radius(angle):
    cos_angle, sin_angle = math.cos(angle), math.sin(angle)
    hit_x = 64.0 / max(abs(cos_angle), 1e-6)
    hit_z = 64.0 / max(abs(sin_angle), 1e-6)
    return min(hit_x, hit_z)


def ridge_height(angle):
    u = angle / math.tau
    return 2.8 + 3.0 * (0.50 + 0.25 * math.sin(angle * 3.0 + 0.7) + 0.16 * math.sin(angle * 7.0 - 0.4) + 0.09 * math.sin(angle * 13.0 + 1.2)) + (1.6 if 0.54 < u < 0.68 else 0.0)


def make_panorama(height_at, material):
    vertices, uvs, faces = [], [], []
    for row in range(PANORAMA_ROWS):
        for index in range(PANORAMA_SEGMENTS + 1):
            angle = math.tau * index / PANORAMA_SEGMENTS
            boundary = boundary_radius(angle)
            if row == 0:
                radius = boundary
                x, game_z = math.cos(angle) * radius, -math.sin(angle) * radius
                height, tex_v = float(height_at(x, game_z)) - 0.04, 0.985
            elif row == 1:
                radius, height, tex_v = 106.0, -4.5, 0.925
            elif row == 2:
                radius, height, tex_v = 158.0, -2.1, 0.855
            elif row == 3:
                radius, height, tex_v = 178.0, ridge_height(angle), 0.79
            elif row == 4:
                radius, height, tex_v = 190.0, ridge_height(angle) + 2.0, 0.72
            elif row == 5:
                radius, height, tex_v = 190.0, 34.0, 0.54
            elif row == 6:
                radius, height, tex_v = 190.0, 82.0, 0.28
            else:
                radius, height, tex_v = 190.0, 132.0, 0.0
            vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, height))
            uvs.append((index / PANORAMA_SEGMENTS, tex_v))
    columns = PANORAMA_SEGMENTS + 1
    for row in range(PANORAMA_ROWS - 1):
        for index in range(PANORAMA_SEGMENTS):
            a = row * columns + index
            faces.extend(((a, a + columns, a + columns + 1), (a, a + columns + 1, a + 1)))
    mesh = bpy.data.meshes.new("LowOrbitPanoramaMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        polygon.use_smooth = True
        for loop_index in polygon.loop_indices:
            uv.data[loop_index].uv = uvs[mesh.loops[loop_index].vertex_index]
    ring = bpy.data.objects.new("LowOrbitPanorama", mesh)
    bpy.context.collection.objects.link(ring)
    mesh.materials.append(material)
    ring["render_only"] = True
    ring["panorama"] = True
    ring["panorama_law"] = "PANORAMA LAW v2"
    ring["sim_authority"] = "none; mounted scenery only"
    ring["tile_id"] = "e8-low-orbit"
    return ring


def render_verdicts(table, terrain, panorama, preview, overlay, height_at):
    backdrop = claim.make_backdrop()
    backdrop.location.z = -4.25
    nodes = backdrop.active_material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBackground")
    shader.inputs["Color"].default_value = (0.014, 0.016, 0.016, 1.0)
    shader.inputs["Strength"].default_value = 1.0
    backdrop.active_material.node_tree.links.new(shader.outputs[0], output.inputs[0])
    panorama.hide_render = True
    cameras = {
        # Exact runtime rig at a hero target in the centre yard.  Runtime Y is
        # Blender Z and runtime Z is -Blender Y, so Balance.camera's
        # (0, 26.2, 18.3) offset and 42 degree FOV become this camera/target.
        "run": claim.add_camera("LowOrbitRun", (0.0, -18.3, 26.2), (0.0, 3.35, 0.45), 42.0),
        "composition": claim.add_camera("LowOrbitComposition", (0.0, 70.0, 49.0), (0.0, -3.0, -0.1), 48.0),
        "overview": claim.add_camera("LowOrbitOverview", (0.0, 102.0, 106.0), (0.0, 0.0, -0.4), 47.0),
        "low": claim.add_camera("LowOrbitLow", (-57.0, 69.0, 23.0), (0.0, -1.0, 0.2), 53.0),
        "top": claim.add_camera("LowOrbitMask", (0.0, 0.0, 158.0), (0.0, 0.0, 0.0), 52.0),
        "horizon": claim.add_camera("LowOrbitHorizon", (0.0, 0.0, 4.0), (95.0, -168.0, 18.0), 54.0),
    }
    for camera in cameras.values():
        camera.data.clip_end = 440.0
    lights = add_lighting(height_at)
    bpy.context.scene.view_settings.exposure = 1.12
    for obj in preview + overlay:
        obj.hide_render = True
    saved = [vertex.co.z for vertex in terrain.data.vertices]
    for vertex in terrain.data.vertices:
        vertex.co.z = 0.0
    terrain.data.update()
    claim.render(cameras["composition"], ARTIFACTS / "low-orbit-flat-tile-identical-camera.png")
    for vertex, value in zip(terrain.data.vertices, saved):
        vertex.co.z = value
    terrain.data.update()
    claim.render(cameras["composition"], ARTIFACTS / "low-orbit-sculpted-tile-identical-camera.png")
    for obj in preview:
        obj.hide_render = False
    claim.render(cameras["low"], ARTIFACTS / "low-orbit-panorama-before.png")
    for obj in overlay:
        obj.hide_render = False
    claim.render(cameras["top"], ARTIFACTS / "low-orbit-mask-agreement.png")
    for obj in overlay:
        obj.hide_render = True
    backdrop.hide_render = True
    panorama.hide_render = False
    claim.render(cameras["run"], ARTIFACTS / "low-orbit-run-camera.png")
    claim.render(cameras["composition"], ARTIFACTS / "low-orbit-composition.png")
    claim.render(cameras["overview"], ARTIFACTS / "low-orbit-overview.png")
    claim.render(cameras["low"], ARTIFACTS / "low-orbit-low-sunset.png")
    claim.render(cameras["low"], ARTIFACTS / "low-orbit-panorama-mounted.png")
    for obj in preview:
        obj.hide_render = True
    claim.render(cameras["horizon"], ARTIFACTS / "low-orbit-panorama-horizon.png")
    bpy.context.scene.view_settings.exposure = 0.0
    claim.remove_objects(lights + list(cameras.values()) + [backdrop])


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_zone_flatness(table, height_at):
    results = []
    for zone in table["maskTruth"]["buildZones"]:
        samples = [float(height_at(x, z)) for x in np.linspace(zone["minX"], zone["maxX"], 65) for z in np.linspace(zone["minZ"], zone["maxZ"], 33)]
        results.append({"id": zone["id"], "bounds": [zone["minX"], zone["maxX"], zone["minZ"], zone["maxZ"]], "sampledSurfacePoints": len(samples), "maxDeviationMeters": round(max(samples) - min(samples), 6)})
    return results


def export_asset(stem, obj, contract):
    blend, glb = OUT / f"{stem}.blend", OUT / f"{stem}.glb"
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", use_selection=True, export_apply=True, export_cameras=False, export_lights=False, export_animations=False, export_extras=True)
    atlas = OUT / f"{stem}-atlas.png"
    contract["files"] = {
        "blend": {"bytes": blend.stat().st_size, "sha256": sha256(blend)},
        "glb": {"bytes": glb.stat().st_size, "sha256": sha256(glb)},
        "atlas": {"bytes": atlas.stat().st_size, "sha256": sha256(atlas)},
    }
    (OUT / f"{stem}-contract.json").write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")


def build():
    factory, table = documents()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    claim.reset_scene()
    terrain_atlas, terrain_atlas_path = make_atlas(table)
    terrain_material = claim.make_material(terrain_atlas)
    terrain_material.name = PROFILE["material"]
    height_at = height_function(table)
    claim.terrain_height = height_at
    terrain = make_terrain(table, height_at, terrain_material)
    panorama_atlas, panorama_atlas_path = make_panorama_atlas()
    panorama_material = make_panorama_material(panorama_atlas)
    panorama = make_panorama(height_at, panorama_material)
    materials = preview_materials()
    preview = add_preview(table, height_at, materials)
    overlay = add_overlay(table, height_at, materials)
    render_verdicts(table, terrain, panorama, preview, overlay, height_at)
    claim.remove_objects(preview + overlay)
    panorama.hide_render = False
    bpy.context.scene.world = None
    triangle_count = sum(len(poly.vertices) - 2 for poly in terrain.data.polygons)
    terrain_contract = {
        "asset": "low-orbit-terrain.glb",
        "contractId": PROFILE["contractId"],
        "tileId": table["maskTruth"]["tileId"],
        "renderOnly": True,
        "simulation": "planar; zero-G movement, collision, placement, spawns, orbital-return projectiles, debris semantics, and handhold routing remain code-owned and unchanged",
        "heightSocket": "Terrain.visualY",
        "theme": PROFILE["theme"],
        "regionalFamily": {"epoch": PROFILE["epoch"], "shared": PROFILE["shared"], "unique": PROFILE["unique"]},
        "meshCount": 1,
        "primitiveCount": 1,
        "materialCount": 1,
        "vertices": len(terrain.data.vertices),
        "triangles": triangle_count,
        "triangleBudget": 60000,
        "texture": {"count": 1, "width": ATLAS_SIZE, "height": ATLAS_SIZE, "embedded": True},
        "maskTable": str(TABLE_PATH.relative_to(ROOT)),
        "maskTruth": table["maskTruth"],
        "waterAgreement": table["waterAgreement"],
        "buildZoneFlatness": build_zone_flatness(table, height_at),
        "landmarkMounts": LANDMARK_MOUNTS,
        "landmarkMountSpace": claim.landmark_mount_space(),
        "panoramaMount": claim.panorama_mount("low-orbit"),
        "runtimeVisualsAbsent": ["zero-G movement", "orbital-return projectiles", "drifting debris", "handhold interaction", "spawn gates"],
        "verdictPreviewOnly": {"assets": [str(CLAW.relative_to(ROOT))], "excludedFromBlendAndGlb": True, "reason": "the accepted Salvage Claw establishes scale without baking runtime art, collision, or placement authority into the terrain"},
        "sourceArt": [str(KIT.relative_to(ROOT)), str(PLATE.relative_to(ROOT)), str(MARE_ATLAS.relative_to(ROOT))],
        "atlas": terrain_atlas_path.name,
    }
    if triangle_count != 32768 or any(item["maxDeviationMeters"] > 0.001 for item in terrain_contract["buildZoneFlatness"]):
        raise AssertionError("Low Orbit terrain geometry or flatness contract failed")
    claim.remove_objects([panorama])
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    export_asset("low-orbit-terrain", terrain, terrain_contract)

    # Rebuild a clean scene containing the panorama only so its .blend and GLB
    # remain independently mountable and byte-identical on re-export.
    claim.reset_scene()
    panorama_atlas = bpy.data.images.load(str(panorama_atlas_path), check_existing=False)
    panorama_atlas.pack()
    panorama_material = make_panorama_material(panorama_atlas)
    panorama = make_panorama(height_at, panorama_material)
    panorama_triangles = sum(len(poly.vertices) - 2 for poly in panorama.data.polygons)
    panorama_contract = {
        "asset": "low-orbit-panorama.glb",
        "contractId": PROFILE["contractId"],
        "tileId": table["maskTruth"]["tileId"],
        "renderOnly": True,
        "lawVersion": "PANORAMA LAW v2",
        "style": "drawn vacuum negative space with a soft blue-green Earth limb, four asymmetric debris edits, and an irregular scaffold-wreck rim",
        "meshCount": 1,
        "primitiveCount": 1,
        "materialCount": 1,
        "triangles": panorama_triangles,
        "triangleBudget": 4000,
        "texture": {"count": 1, "width": ATLAS_SIZE, "height": ATLAS_SIZE, "embedded": True},
        "mount": claim.panorama_mount("low-orbit"),
        "nonInterference": {"playfieldBounds": "unchanged", "spawnEdges": "unchanged", "fogGating": "unchanged", "waterBuildSpawnMasks": "unchanged"},
        "projection": {"groundSkirtRole": "submerged scenery apron from the rectangular visual boundary into the distant orbital wreck rim", "groundSkirtOuterRadiusMeters": 190.0, "zenith": "quiet near-black engraving"},
        "sourceArt": [str(KIT.relative_to(ROOT)), str(PLATE.relative_to(ROOT))],
        "atlas": panorama_atlas_path.name,
    }
    if panorama_triangles > 4000:
        raise AssertionError("Low Orbit panorama triangle budget exceeded")
    export_asset("low-orbit-panorama", panorama, panorama_contract)
    print(json.dumps({"terrainTriangles": triangle_count, "panoramaTriangles": panorama_triangles, "buildZoneFlatness": terrain_contract["buildZoneFlatness"]}, indent=2))


if __name__ == "__main__":
    build()
