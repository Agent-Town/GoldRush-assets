"""Build the unique E6 campaign terrain pair.

Showroom and Half-Life Hollow receive distinct render-only landforms. Runtime
code keeps all movement, collision, placement, spawns, wake sequencing, decay
timers, glow bridges, causeways, and extraction semantics on the planar sim.
Verdict-only houses, glowing spans, clutter, lights, and mask marks are removed
before each one-mesh terrain is saved and exported.
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
FACTORY = ROOT / "assets/contracts/epoch-6-atomic/contracts.json"
MASK_DIR = ROOT / "assets/contracts/epoch-6-atomic/mask-tables"
KIT = ROOT / "assets/processed/kit-era-6.png"
PLATE = OUT / "glow-mesa-terrain-atlas.png"
ATLAS_SIZE = 2048
WIDTH = 128.0
HEIGHT = 128.0


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


e3 = load_module("e6_extra_e3_helpers", OUT / "build_e3_contract_terrains.py")
claim = e3.claim
claim.mathutils = mathutils

PROFILES = {
    "showroom": {
        "contractId": "e6-showroom",
        "stem": "showroom-terrain",
        "object": "ShowroomTerrain",
        "mesh": "ShowroomTerrainMesh",
        "material": "ShowroomPaintedAtomicMaterial",
        "atlas": "ShowroomPaintedAtomicAtlas",
        "width": WIDTH,
        "height": HEIGHT,
        "theme": "an abandoned three-step catalog village: broad model-home display, scuffed southern approach, raised goods yard, and eroded atomic-desert perimeter",
        "epoch": "Epoch 6 atomic homestead",
        "shared": [
            "chrome and pastel enamel over parchment warmth",
            "soft teal starstone cues",
            "amber Combine work scars",
            "engraved fade steps rather than corrosion",
            "hard desert grit outside polished effort",
        ],
        "unique": ["three-step showroom grade", "five display-home scars", "raised catalog yard", "empty-village perimeter berms"],
    },
    "half-life-hollow": {
        "contractId": "e6-half-life-hollow",
        "stem": "half-life-hollow-terrain",
        "object": "HalfLifeHollowTerrain",
        "mesh": "HalfLifeHollowTerrainMesh",
        "material": "HalfLifeHollowPaintedAtomicMaterial",
        "atlas": "HalfLifeHollowPaintedAtomicAtlas",
        "width": WIDTH,
        "height": HEIGHT,
        "theme": "a deep expiring hollow with four permanent abutment shelves and three empty runtime-owned crossings winding south to north",
        "epoch": "Epoch 6 atomic homestead",
        "shared": [
            "chrome and pastel enamel over parchment warmth",
            "soft teal starstone cues",
            "amber Combine work scars",
            "engraved fade steps rather than corrosion",
            "hard desert grit outside polished effort",
        ],
        "unique": ["deep countdown hollow", "four offset shelf abutments", "three empty crossing sockets", "north extraction notch"],
    },
}

LANDMARK_MOUNTS = {
    "showroom": [
        {"id": "showroom-entrance-arch", "position": [0.0, 0.0, -59.0], "rotation": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0], "asset": ""},
        {"id": "west-starburst-billboard", "position": [-56.0, 0.0, -19.0], "rotation": [0.0, 0.18, 0.0], "scale": [1.0, 1.0, 1.0], "asset": ""},
        {"id": "east-starburst-billboard", "position": [56.0, 0.0, -15.0], "rotation": [0.0, -0.16, 0.0], "scale": [0.94, 0.94, 0.94], "asset": ""},
        {"id": "abandoned-catalog-office", "position": [-49.0, 0.0, 45.0], "rotation": [0.0, 0.13, 0.0], "scale": [1.0, 1.0, 1.0], "asset": ""},
        {"id": "catalog-sorting-gantry", "position": [42.0, 0.0, 46.0], "rotation": [0.0, -0.10, 0.0], "scale": [1.0, 1.0, 1.0], "asset": ""},
    ],
    "half-life-hollow": [
        {"id": "south-countdown-gate", "position": [0.0, 0.0, -59.0], "rotation": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0], "asset": ""},
        {"id": "west-hollow-warning-pylon", "position": [-52.0, 0.0, -17.0], "rotation": [0.0, 0.12, 0.0], "scale": [1.0, 1.0, 1.0], "asset": ""},
        {"id": "east-hollow-warning-pylon", "position": [52.0, 0.0, 20.0], "rotation": [0.0, -0.14, 0.0], "scale": [0.96, 0.96, 0.96], "asset": ""},
        {"id": "expired-appliance-convoy", "position": [-48.0, 0.0, 43.0], "rotation": [0.0, 0.22, 0.0], "scale": [1.0, 1.0, 1.0], "asset": ""},
        {"id": "north-extraction-gantry", "position": [36.0, 0.0, 50.0], "rotation": [0.0, -0.08, 0.0], "scale": [1.0, 1.0, 1.0], "asset": ""},
    ],
}

for key in PROFILES:
    claim.CONTRACT_PLATES[key] = PLATE
    claim.GRIT_PROFILES[key] = {
        "black": 0.009,
        "white": 0.62 if key == "showroom" else 0.54,
        "gamma": 1.10 if key == "showroom" else 1.16,
        "ink": 0.34 if key == "showroom" else 0.42,
        "palette": 0.25,
        "saturation": 0.61,
    }


def smoothstep(edge0, edge1, value):
    value = np.asarray(value, dtype=np.float32)
    t = np.clip((value - edge0) / max(edge1 - edge0, 0.0001), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def gaussian(x, z, cx, cz, sx, sz):
    return np.exp(-((((x - cx) / sx) ** 2 + ((z - cz) / sz) ** 2) * 0.5))


def rectangle_mask(x, z, zone, feather=1.0, margin=0.0):
    return (
        smoothstep(zone["minX"] - margin - feather, zone["minX"] - margin, x)
        * (1.0 - smoothstep(zone["maxX"] + margin, zone["maxX"] + margin + feather, x))
        * smoothstep(zone["minZ"] - margin - feather, zone["minZ"] - margin, z)
        * (1.0 - smoothstep(zone["maxZ"] + margin, zone["maxZ"] + margin + feather, z))
    )


def documents(key):
    profile = PROFILES[key]
    contracts = json.loads(FACTORY.read_text(encoding="utf-8"))["contracts"]
    matches = [entry for entry in contracts if entry["id"] == profile["contractId"]]
    if len(matches) != 1:
        raise ValueError(f"expected one factory contract for {profile['contractId']}")
    table_path = MASK_DIR / f"{profile['contractId']}.json"
    table = json.loads(table_path.read_text(encoding="utf-8"))
    if table["maskTruth"]["tileId"] != profile["contractId"]:
        raise ValueError(f"{key} mask table tile id changed")
    if table["maskTruth"]["dimensions"] != {"width": 128, "height": 128}:
        raise ValueError(f"{key} authored dimensions changed")
    return matches[0], table, table_path


def height_function(key, table):
    truth = table["maskTruth"]
    cell_diagonal = math.hypot(WIDTH / e3.SEGMENTS, HEIGHT / e3.SEGMENTS)
    zones = {zone["id"]: zone for zone in truth["buildZones"]}

    def blend_plateau(surface, x, z, zone, target, feather=2.3):
        mask = rectangle_mask(x, z, zone, feather=feather, margin=cell_diagonal + 0.08)
        return surface * (1.0 - mask) + target * mask

    if key == "showroom":
        def height(x, z):
            xx = np.asarray(x, dtype=np.float32)
            zz = np.asarray(z, dtype=np.float32)
            ax, az = np.abs(xx), np.abs(zz)
            grain = np.sin(xx * 0.20 + zz * 0.09) * 0.065 + np.sin(xx * 0.47 - zz * 0.31) * 0.028
            outer = 0.12 + grain
            outer += smoothstep(49.0, 63.0, ax) * 2.15
            outer += smoothstep(55.0, 64.0, az) * 0.74
            outer += gaussian(xx, zz, -55.0, 31.0, 9.0, 16.0) * 1.12
            outer += gaussian(xx, zz, 56.0, -22.0, 8.0, 17.0) * 1.34
            outer -= gaussian(xx, zz, -51.0, -39.0, 7.0, 10.0) * 0.42
            outer -= gaussian(xx, zz, 48.0, 44.0, 8.0, 9.0) * 0.36
            # Three permanent display grades. Their transitions sit wholly
            # outside the authored build rectangles.
            outer = blend_plateau(outer, xx, zz, zones["south-showroom-approach"], 0.18, 2.0)
            outer = blend_plateau(outer, xx, zz, zones["model-home-village"], 0.82, 2.0)
            outer = blend_plateau(outer, xx, zz, zones["catalog-goods-yard"], 1.52, 2.0)
            return np.clip(outer, -0.55, 3.45)

        return height

    def height(x, z):
        xx = np.asarray(x, dtype=np.float32)
        zz = np.asarray(z, dtype=np.float32)
        ax = np.abs(xx)
        grain = np.sin(xx * 0.17 + zz * 0.13) * 0.075 + np.sin(xx * 0.53 - zz * 0.21) * 0.035
        # The permanent earth is a deep, asymmetric bowl. Runtime crossings
        # later span it; the exported mesh never promises that they exist.
        surface = 2.18 + grain + smoothstep(43.0, 62.0, ax) * 1.05
        surface -= gaussian(xx, zz, 0.0, 0.0, 34.0, 62.0) * 3.62
        surface -= gaussian(xx, zz, -18.0, -13.0, 24.0, 22.0) * 0.64
        surface -= gaussian(xx, zz, 20.0, 19.0, 22.0, 25.0) * 0.58
        surface += gaussian(xx, zz, -47.0, 23.0, 10.0, 18.0) * 0.90
        surface += gaussian(xx, zz, 47.0, -26.0, 10.0, 17.0) * 0.82
        for zone in truth["glowBridges"] + truth["causeways"]:
            socket = rectangle_mask(xx, zz, zone, feather=2.4, margin=-cell_diagonal * 0.35)
            socket_floor = -2.36 + np.sin(xx * 0.31 - zz * 0.17) * 0.05
            surface = surface * (1.0 - socket) + socket_floor * socket
        extraction_notch = gaussian(xx, zz, 0.0, 59.0, 8.0, 5.0)
        surface -= extraction_notch * 0.52
        shelf_heights = {
            "south-launch-shelf": 0.16,
            "west-countdown-ground": 0.46,
            "east-countdown-ground": 0.76,
            "north-extraction-shelf": 1.18,
        }
        for identifier, target in shelf_heights.items():
            surface = blend_plateau(surface, xx, zz, zones[identifier], target, 2.2)
        return np.clip(surface, -2.55, 4.10)

    return height


def make_atlas(key, table):
    source = claim.image_pixels(PLATE)
    half_y, half_x = source.shape[0] // 2, source.shape[1] // 2
    inset_y0, inset_y1 = int(half_y * 0.24), int(half_y * 0.88)
    inset_x0, inset_x1 = int(half_x * 0.24), int(half_x * 0.88)
    # Blender loads rows bottom-up. These inset lower-desert crops exclude the
    # shipped tile's dark outer border as well as its central ring and arrows.
    neutral_a = source[inset_y0:inset_y1, half_x + inset_x0:half_x + inset_x1]
    neutral_b = source[inset_y0:inset_y1, inset_x0:inset_x1]
    kit = claim.image_pixels(KIT)
    axis = np.linspace(0.0, 1.0, ATLAS_SIZE, dtype=np.float32)
    u, v = np.meshgrid(axis, axis)
    x, z = (u - 0.5) * WIDTH, (v - 0.5) * HEIGHT
    warped_u = u + np.sin(v * math.tau * 3.3) * 0.012
    warped_v = v + np.sin(u * math.tau * 4.7 + 0.5) * 0.010
    # Reuse the painted earth language, never Glow Mesa's composition. The
    # neutral crops are interleaved at unequal scales to avoid tile echoes.
    painted_a = claim.tiled_sample(neutral_a, warped_u, warped_v, 1.7, 0.17, 0.53)
    painted_b = claim.tiled_sample(neutral_b, 1.0 - warped_v, warped_u, 2.3, 0.48, 0.22)
    grit = claim.tiled_sample(neutral_a, warped_u + warped_v * 0.11, warped_v, 4.7, 0.29, 0.64)
    kit_sample = claim.tiled_sample(kit, u, v, 4.4, 0.37, 0.16)
    macro = (np.sin(x * 0.067 + z * 0.043) * 0.5 + 0.5)[..., None]
    atlas = painted_a * (0.47 + macro * 0.08) + painted_b * (0.28 - macro * 0.04) + grit * 0.17 + kit_sample * 0.08
    atlas *= np.asarray((0.78, 0.74, 0.61), dtype=np.float32)
    truth = table["maskTruth"]

    if key == "showroom":
        approach = rectangle_mask(x, z, next(zone for zone in truth["buildZones"] if zone["id"] == "south-showroom-approach"), 2.0)
        village = rectangle_mask(x, z, next(zone for zone in truth["buildZones"] if zone["id"] == "model-home-village"), 2.2)
        yard = rectangle_mask(x, z, next(zone for zone in truth["buildZones"] if zone["id"] == "catalog-goods-yard"), 1.8)
        pale_enamel = painted_b * np.asarray((0.76, 0.86, 0.74), dtype=np.float32)
        atlas = atlas * (1.0 - village[..., None] * 0.46) + pale_enamel * village[..., None] * 0.46
        atlas *= 1.0 - approach[..., None] * (0.08 + (np.sin(x * 0.41) * 0.5 + 0.5)[..., None] * 0.06)
        yard_amber = grit * np.asarray((0.70, 0.48, 0.22), dtype=np.float32)
        atlas = atlas * (1.0 - yard[..., None] * 0.31) + yard_amber * yard[..., None] * 0.31
        for house in truth["showroomHouses"]:
            cx = (house["minX"] + house["maxX"]) * 0.5
            cz = (house["minZ"] + house["maxZ"]) * 0.5
            radius = np.hypot(x - cx, z - cz)
            scar = np.exp(-(((radius - 7.4) / 0.48) ** 2))
            atomic_glint = kit_sample * np.asarray((0.30, 0.82, 0.72), dtype=np.float32)
            atlas = atlas * (1.0 - scar[..., None] * 0.28) + atomic_glint * scar[..., None] * 0.28
    else:
        bowl = gaussian(x, z, 0.0, 0.0, 36.0, 61.0)
        dark_hollow = grit * np.asarray((0.34, 0.47, 0.43), dtype=np.float32)
        atlas = atlas * (1.0 - bowl[..., None] * 0.48) + dark_hollow * bowl[..., None] * 0.48
        for index, zone in enumerate(truth["glowBridges"] + truth["causeways"]):
            region = rectangle_mask(x, z, zone, 1.5)
            hatch = (np.sin((x + z * (0.35 + index * 0.08)) * 0.72) * 0.5 + 0.5) * region
            faded = kit_sample * np.asarray((0.38, 0.84, 0.77), dtype=np.float32)
            atlas = atlas * (1.0 - hatch[..., None] * 0.32) + faded * hatch[..., None] * 0.32
        for index, zone in enumerate(truth["buildZones"]):
            edge = rectangle_mask(x, z, zone, 1.8) - rectangle_mask(x, z, zone, 0.35)
            tone = kit_sample if index % 2 else painted_b
            atlas = atlas * (1.0 - edge[..., None] * 0.30) + tone * edge[..., None] * 0.30

    atlas = claim.apply_grit_grade(atlas, source, u, v, key)
    rgba = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    rgba[..., :3] = np.clip(atlas, 0.004, 0.74)
    path = OUT / f"{PROFILES[key]['stem']}-atlas.png"
    image = bpy.data.images.new(PROFILES[key]["atlas"], ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image, path


def rectangle_points(zone, height_at, lift=0.38):
    points = []
    for x, z in (
        (zone["minX"], zone["minZ"]),
        (zone["maxX"], zone["minZ"]),
        (zone["maxX"], zone["maxZ"]),
        (zone["minX"], zone["maxZ"]),
        (zone["minX"], zone["minZ"]),
    ):
        points.append((x, z, float(height_at(x, z)) + lift))
    return points


def preview_materials(key):
    materials = e3.preview_materials(key)
    materials["mint"] = claim.make_render_material(f"{key}FadedMintEnamel", (0.24, 0.43, 0.34), 0.72, 0.18)
    materials["cream"] = claim.make_render_material(f"{key}SunBleachedEnamel", (0.60, 0.50, 0.31), 0.78, 0.10)
    materials["teal"] = claim.make_render_material(f"{key}StarstoneTeal", (0.035, 0.46, 0.42), 0.48, 0.16)
    materials["violet"] = claim.make_render_material(f"{key}CountdownViolet", (0.25, 0.16, 0.46), 0.62, 0.10)
    return materials


def add_showroom_preview(table, height_at, materials):
    objects = []
    for index, zone in enumerate(table["maskTruth"]["showroomHouses"]):
        x = (zone["minX"] + zone["maxX"]) * 0.5
        z = (zone["minZ"] + zone["maxZ"]) * 0.5
        base = float(height_at(x, z)) + 0.04
        yaw = (-0.18, 0.10, 0.0, -0.10, 0.18)[index]
        objects.append(claim.add_box_game(f"RenderHelperShowroomHome.{zone['id']}.body", x, z, base, (7.4, 5.8, 2.8), materials["mint"] if index % 2 else materials["cream"], yaw=yaw, bevel=0.08))
        objects.append(claim.add_roof_prism(f"RenderHelperShowroomHome.{zone['id']}.roof", x, z, base + 2.78, 8.2, 6.6, 1.45, materials["iron"], yaw=yaw))
        objects.append(claim.add_box_game(f"RenderHelperShowroomHome.{zone['id']}.porch", x, z - 3.4, base + 0.02, (4.0, 1.4, 0.18), materials["teal"], yaw=yaw, bevel=0.03))
    for index, anchor in enumerate(table["maskTruth"]["catalogGoods"]):
        base = float(height_at(anchor["x"], anchor["z"])) + 0.05
        objects.append(claim.add_box_game(f"RenderHelperCatalogGoods.{index}", anchor["x"], anchor["z"], base, (1.4, 1.1, 1.0), materials["brass"], yaw=index * 0.41, bevel=0.05))
    return objects


def add_hollow_preview(table, height_at, materials):
    objects = []
    truth = table["maskTruth"]
    runtime_surfaces = truth["glowBridges"] + truth["causeways"]
    bases = (0.32, 0.92, 0.62)
    for index, zone in enumerate(runtime_surfaces):
        x = (zone["minX"] + zone["maxX"]) * 0.5
        z = (zone["minZ"] + zone["maxZ"]) * 0.5
        dimensions = (zone["maxX"] - zone["minX"], zone["maxZ"] - zone["minZ"], 0.13)
        objects.append(claim.add_box_game(f"RenderHelperRuntimeCrossing.{zone['id']}", x, z, bases[index], dimensions, materials["teal"] if index < 2 else materials["violet"], bevel=0.03))
    route = [(point["x"], point["z"], max(float(height_at(point["x"], point["z"])) + 0.42, 0.74)) for point in truth["extractionRoute"]]
    objects.append(claim.add_curve("RenderHelperExtractionRoute", route, 0.12, materials["brass"]))
    extraction = truth["stakeMarkers"][0]
    base = float(height_at(extraction["x"], extraction["z"]))
    objects.append(claim.add_box_game("RenderHelperHollowExtraction", extraction["x"], extraction["z"], base + 0.05, (3.4, 2.2, 1.2), materials["cream"], bevel=0.08))
    return objects


def add_mask_overlay(key, table, height_at, materials):
    objects = []
    truth = table["maskTruth"]
    for zone in truth["buildZones"]:
        objects.append(claim.add_curve(f"RenderHelperBuildMask.{zone['id']}", rectangle_points(zone, height_at, 0.52), 0.18, materials["mask"]))
    if key == "showroom":
        for zone in truth["showroomHouses"]:
            objects.append(claim.add_curve(f"RenderHelperHomeMask.{zone['id']}", rectangle_points(zone, height_at, 0.62), 0.13, materials["brass"]))
        for index, anchor in enumerate(truth["harvestAnchors"]):
            z = float(height_at(anchor["x"], anchor["z"])) + 0.74
            bpy.ops.mesh.primitive_torus_add(major_radius=1.05, minor_radius=0.12, major_segments=16, minor_segments=6, location=(anchor["x"], -anchor["z"], z))
            marker = bpy.context.object
            marker.name = f"RenderHelperGoodsMask.{index}"
            marker.data.materials.append(materials["danger"])
            objects.append(marker)
    else:
        for zone in truth["glowBridges"]:
            objects.append(claim.add_curve(f"RenderHelperGlowBridgeMask.{zone['id']}", rectangle_points(zone, height_at, 0.72), 0.19, materials["violet"]))
        for zone in truth["causeways"]:
            objects.append(claim.add_curve(f"RenderHelperCausewayMask.{zone['id']}", rectangle_points(zone, height_at, 0.76), 0.19, materials["brass"]))
    return objects


def add_clutter(key, table, height_at, materials):
    rng = np.random.default_rng(1606 if key == "showroom" else 1619)
    truth = table["maskTruth"]
    avoid = list(truth["buildZones"])
    avoid += truth.get("showroomHouses", []) + truth.get("glowBridges", []) + truth.get("causeways", [])
    objects = []
    for candidate in range(220):
        if len(objects) >= (46 if key == "showroom" else 54):
            break
        x, z = float(rng.uniform(-61.0, 61.0)), float(rng.uniform(-61.0, 61.0))
        if any(zone["minX"] - 1.5 <= x <= zone["maxX"] + 1.5 and zone["minZ"] - 1.5 <= z <= zone["maxZ"] + 1.5 for zone in avoid):
            continue
        local = [float(height_at(x + dx, z + dz)) for dx, dz in ((-0.8, 0), (0.8, 0), (0, -0.8), (0, 0.8))]
        if max(local) - min(local) > 0.48:
            continue
        size = float(rng.uniform(0.26, 0.88))
        objects.append(claim.add_rock(f"RenderHelperE6Rubble.{candidate}", x, z, (size * rng.uniform(0.9, 1.8), size * rng.uniform(0.7, 1.2), size * rng.uniform(0.42, 0.86)), materials["stone"], yaw=float(rng.uniform(-math.pi, math.pi))))
    cactus_specs = ((-58.0, -6.0, 0.56, 1.0, 0.5), (57.0, 45.0, 0.62, -1.0, -0.4)) if key == "showroom" else ((-56.0, 36.0, 0.54, 1.0, 0.8), (57.0, -35.0, 0.59, -1.0, -0.5))
    for index, (x, z, scale, flip, yaw) in enumerate(cactus_specs):
        objects.extend(claim.make_cactus(f"RenderHelperE6Cactus.{index}", x, z, scale, materials, flip, yaw, height_at))
    return objects


def add_lighting(key, table, height_at):
    world = bpy.data.worlds.new(f"{key}VerdictWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.036, 0.047, 0.043, 1.0)
    background.inputs["Strength"].default_value = 0.56
    sun_data = bpy.data.lights.new(f"{key}AtomicSun", "SUN")
    sun_data.energy = 2.15
    sun_data.color = (0.72, 0.73, 0.58)
    sun_data.angle = math.radians(18)
    sun = bpy.data.objects.new(f"{key}AtomicSun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.location = (-52.0, 31.0, 54.0)
    claim.aim_at(sun, (0.0, 4.0, 0.0))
    lights = [sun]
    anchors = table["maskTruth"].get("harvestAnchors", []) if key == "showroom" else table["maskTruth"]["extractionRoute"][1:-1]
    for index, anchor in enumerate(anchors):
        data = bpy.data.lights.new(f"{key}AtomicCue.{index}", "POINT")
        data.energy = 270.0 if key == "showroom" else 390.0
        data.color = (0.09, 0.76, 0.68) if index % 2 == 0 else (1.0, 0.45, 0.12)
        data.shadow_soft_size = 1.7
        light = bpy.data.objects.new(f"{key}AtomicCue.{index}", data)
        bpy.context.collection.objects.link(light)
        light.location = (anchor["x"], -anchor["z"], float(height_at(anchor["x"], anchor["z"])) + 3.2)
        lights.append(light)
    return lights


def render_verdicts(key, profile, table, terrain, preview, overlay, height_at):
    backdrop = claim.make_backdrop()
    panorama = claim.link_panorama(key)
    for obj in panorama:
        obj.visible_shadow = False
        obj.hide_render = True
    cameras = {
        "showroom": ((0.0, 52.0, 39.0), (0.0, 2.0, 0.7), (0.0, 98.0, 104.0), (-48.0, 55.0, 17.0), (132.0, -122.0, 5.0)),
        "half-life-hollow": ((0.0, 48.0, 38.0), (0.0, 3.0, -0.2), (0.0, 96.0, 103.0), (-50.0, 52.0, 16.0), (-118.0, 128.0, 5.0)),
    }
    run_location, run_target, overview_location, low_location, horizon_target = cameras[key]
    run = claim.add_camera(f"{profile['object']}Run", run_location, run_target, 47.0)
    overview = claim.add_camera(f"{profile['object']}Overview", overview_location, (0.0, 0.0, 0.6), 47.0)
    low = claim.add_camera(f"{profile['object']}Low", low_location, (0.0, -3.0, 0.8), 49.0)
    top = claim.add_camera(f"{profile['object']}Mask", (0.0, 0.0, 155.0), (0.0, 0.0, 0.0), 52.0)
    horizon = claim.add_camera(f"{profile['object']}Horizon", (0.0, 0.0, 3.8), horizon_target, 52.0)
    for camera in (run, overview, low, top, horizon):
        camera.data.clip_end = 430.0
    lights = add_lighting(key, table, height_at)
    bpy.context.scene.view_settings.exposure = 0.92 if key == "showroom" else 1.06
    for obj in preview + overlay:
        obj.hide_render = True
    saved = [vertex.co.z for vertex in terrain.data.vertices]
    for vertex in terrain.data.vertices:
        vertex.co.z = 0.0
    terrain.data.update()
    claim.render(run, ARTIFACTS / f"{key}-flat-tile-identical-camera.png")
    for vertex, value in zip(terrain.data.vertices, saved):
        vertex.co.z = value
    terrain.data.update()
    claim.render(run, ARTIFACTS / f"{key}-sculpted-tile-identical-camera.png")
    for obj in preview:
        obj.hide_render = False
    claim.render(low, ARTIFACTS / f"{key}-panorama-before.png")
    for obj in overlay:
        obj.hide_render = False
    claim.render(top, ARTIFACTS / f"{key}-mask-agreement.png")
    for obj in overlay:
        obj.hide_render = True
    backdrop.hide_render = True
    for obj in panorama:
        obj.hide_render = False
    claim.render(run, ARTIFACTS / f"{key}-run-camera.png")
    claim.render(overview, ARTIFACTS / f"{key}-overview.png")
    claim.render(low, ARTIFACTS / f"{key}-low-sunset.png")
    claim.render(low, ARTIFACTS / f"{key}-panorama-mounted.png")
    for obj in preview:
        obj.hide_render = True
    claim.render(horizon, ARTIFACTS / f"{key}-panorama-horizon.png")
    bpy.context.scene.view_settings.exposure = 0.0
    claim.remove_objects(lights + [run, overview, low, top, horizon, backdrop] + panorama)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_contract(key, profile, table, table_path, terrain, height_at, atlas_path):
    coords = np.asarray([vertex.co[:] for vertex in terrain.data.vertices], dtype=np.float32)
    triangles = sum(len(poly.vertices) - 2 for poly in terrain.data.polygons)
    runtime = {
        "showroom": "house-family wake order, catalog goods, stealth, movement, collision, placement, and spawns",
        "half-life-hollow": "glow bridges, causeway expiry, countdown-safe state, route recalculation, extraction, movement, collision, placement, and spawns",
    }[key]
    return {
        "asset": f"{profile['stem']}.glb",
        "contractId": profile["contractId"],
        "tileId": profile["contractId"],
        "renderOnly": True,
        "simulation": f"planar; {runtime} remain code-owned and unchanged",
        "heightSocket": "Terrain.visualY",
        "theme": profile["theme"],
        "regionalFamily": {"epoch": profile["epoch"], "shared": profile["shared"], "unique": profile["unique"]},
        "boundsMeters": {"min": [round(float(value), 4) for value in coords.min(axis=0)], "max": [round(float(value), 4) for value in coords.max(axis=0)]},
        "meshCount": 1,
        "primitiveCount": 1,
        "materialCount": 1,
        "vertices": len(terrain.data.vertices),
        "triangles": triangles,
        "triangleBudget": 60_000,
        "texture": {"count": 1, "width": ATLAS_SIZE, "height": ATLAS_SIZE, "embedded": True},
        "maskTable": str(table_path.relative_to(ROOT)),
        "maskTruth": table["maskTruth"],
        "waterAgreement": table["waterAgreement"],
        "buildZoneFlatness": e3.build_zone_flatness(table, height_at),
        "runtimeVisualsAbsent": ["showroom houses and catalog goods"] if key == "showroom" else ["south glow bridge", "north glow bridge", "center dial causeway"],
        "landmarkMounts": LANDMARK_MOUNTS[key],
        "landmarkMountSpace": claim.landmark_mount_space(),
        "panoramaMount": claim.panorama_mount(key),
        "evidenceRig": "E6 point-light cues plus contract-specific runtime proxies, rubble, cacti, and masks; all helpers removed before save/export",
        "sourceArt": [str(path.relative_to(ROOT)) for path in (KIT, PLATE)],
        "atlas": atlas_path.name,
    }


def export_asset(profile, terrain, contract):
    blend = OUT / f"{profile['stem']}.blend"
    glb = OUT / f"{profile['stem']}.glb"
    atlas = OUT / f"{profile['stem']}-atlas.png"
    contract_path = OUT / f"{profile['stem']}-contract.json"
    bpy.ops.object.select_all(action="DESELECT")
    terrain.select_set(True)
    bpy.context.view_layer.objects.active = terrain
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", use_selection=True, export_apply=True, export_cameras=False, export_lights=False, export_animations=False, export_extras=True)
    contract["files"] = {
        "blend": {"bytes": blend.stat().st_size, "sha256": sha256(blend)},
        "glb": {"bytes": glb.stat().st_size, "sha256": sha256(glb)},
        "atlas": {"bytes": atlas.stat().st_size, "sha256": sha256(atlas)},
    }
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"asset": glb.name, "triangles": contract["triangles"], "runtimeVisualsAbsent": contract["runtimeVisualsAbsent"]}, indent=2))


def build(key):
    profile = PROFILES[key]
    factory, table, table_path = documents(key)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    claim.reset_scene()
    atlas, atlas_path = make_atlas(key, table)
    material = claim.make_material(atlas)
    material.name = profile["material"]
    height_at = height_function(key, table)
    claim.terrain_height = height_at
    terrain = e3.make_terrain(profile, table, table_path, height_at, material)
    terrain["sim_surface"] = "planar"
    terrain["runtime_owned_visuals_absent"] = True
    terrain["landmarks_frozen"] = False
    terrain["landmark_mount_ids"] = json.dumps([mount["id"] for mount in LANDMARK_MOUNTS[key]])
    materials = preview_materials(key)
    preview = add_showroom_preview(table, height_at, materials) if key == "showroom" else add_hollow_preview(table, height_at, materials)
    preview += add_clutter(key, table, height_at, materials)
    overlay = add_mask_overlay(key, table, height_at, materials)
    render_verdicts(key, profile, table, terrain, preview, overlay, height_at)
    claim.remove_objects(preview + overlay)
    bpy.context.scene.world = None
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    contract = make_contract(key, profile, table, table_path, terrain, height_at, atlas_path)
    if contract["triangles"] > contract["triangleBudget"]:
        raise AssertionError(f"{key} terrain triangle budget exceeded")
    if any(entry["maxDeviationMeters"] > 0.001 for entry in contract["buildZoneFlatness"]):
        raise AssertionError(f"{key} build zone is not flat")
    export_asset(profile, terrain, contract)


def main():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    keys = args or list(PROFILES)
    for key in keys:
        if key not in PROFILES:
            raise ValueError(f"unsupported E6 extra terrain profile: {key}")
        build(key)


if __name__ == "__main__":
    main()
