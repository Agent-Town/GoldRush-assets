"""Build the three unique E9 campaign-extra render terrains.

Every height is visual-only and feeds the existing Terrain.visualY seam. The
published masks remain the authority for movement, collision, placement,
spawns, persistence, dust-devil motion, and future water state.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"
CONTRACTS = ROOT / "assets/contracts/epoch-9-redfields/contracts.json"
TABLE_DIR = ROOT / "assets/contracts/epoch-9-redfields/mask-tables"
KIT = ROOT / "assets/processed/kit-era-9.png"
CANAL_PLATE = ROOT / "assets/raw/plate-e9-bld-canal-works.png"
DEVIL_PLATE = ROOT / "assets/raw/plate-e9-enemy-dust-devil.png"
SEGMENTS = 128
ATLAS_SIZE = 2048
E1_GREEN = np.asarray((80 / 255, 103 / 255, 76 / 255), dtype=np.float32)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_module("e9_extra_base", OUT / "build_e3_contract_terrains.py")
claim = base.claim
e2 = base.e2

PROFILES = {
    "seed-run": {
        "contractId": "e9-seed-run",
        "stem": "seed-run-terrain",
        "object": "SeedRunTerrain",
        "mesh": "SeedRunTerrainMesh",
        "material": "SeedRunPaintedTerrainMaterial",
        "atlas": "SeedRunPaintedTerrainAtlas",
        "width": 128.0,
        "height": 128.0,
        "theme": "a rising caravan road crossing three permanent green waypoints between dead red dune shelves",
        "sourcePlate": CANAL_PLATE,
        "unique": "five-level seed-road composition with three sheltered waypoint bays",
    },
    "devils-alley": {
        "contractId": "e9-devils-alley",
        "stem": "devils-alley-terrain",
        "object": "DevilsAlleyTerrain",
        "mesh": "DevilsAlleyTerrainMesh",
        "material": "DevilsAlleyPaintedTerrainMaterial",
        "atlas": "DevilsAlleyPaintedTerrainAtlas",
        "width": 128.0,
        "height": 128.0,
        "theme": "three east-west dust-devil sweep corridors divided by hard red dune walls and anchored refuge bays",
        "sourcePlate": DEVIL_PLATE,
        "unique": "three dominant wind lanes with transverse shelter cuts",
    },
    "old-canal": {
        "contractId": "e9-old-canal",
        "stem": "old-canal-terrain",
        "object": "OldCanalTerrain",
        "mesh": "OldCanalTerrainMesh",
        "material": "OldCanalPaintedTerrainMaterial",
        "atlas": "OldCanalPaintedTerrainAtlas",
        "width": 128.0,
        "height": 128.0,
        "theme": "a dry wrong-survey canal cut through three inherited decision basins between survey and outflow yards",
        "sourcePlate": CANAL_PLATE,
        "unique": "sunken crooked canal segments with broken spoil shoulders",
    },
}

TARGET_HEIGHTS = {
    "seed-run": {
        "south-caravan-yard": 0.25,
        "west-green-waypoint": 0.45,
        "center-green-waypoint": 0.70,
        "east-green-waypoint": 0.95,
        "north-basin-approach": 1.20,
    },
    "devils-alley": {
        "south-anchor-yard": 0.30,
        "west-anchor-bay": 0.42,
        "center-anchor-bay": 0.18,
        "east-anchor-bay": 0.56,
        "north-anchor-yard": 0.34,
    },
    "old-canal": {
        "south-survey-yard": 0.35,
        "old-canal-segment-a": -1.10,
        "old-canal-segment-b": -1.42,
        "old-canal-segment-c": -1.18,
        "north-outflow-yard": 0.24,
    },
}

LANDMARK_MOUNTS = {
    "seed-run": (
        ("south-seed-caravan-gate", 0.0, -48.0, 0.0, 0.0, 1.0),
        ("west-seed-vault", -34.0, -21.0, 0.0, 0.18, 1.0),
        ("center-seed-vault", 0.0, 3.0, 0.0, 0.0, 1.0),
        ("east-seed-vault", 34.0, 27.0, 0.0, -0.20, 1.0),
        ("north-basin-waygate", 0.0, 48.0, 0.0, math.pi, 1.0),
    ),
    "devils-alley": (
        ("south-anchor-gate", 0.0, -48.0, 0.0, 0.0, 1.0),
        ("west-wind-anchor", -40.0, -10.0, 0.0, 0.08, 1.0),
        ("center-wind-anchor", 0.0, 0.0, 0.0, 0.0, 1.0),
        ("east-wind-anchor", 40.0, 10.0, 0.0, -0.08, 1.0),
        ("north-anchor-gate", 0.0, 48.0, 0.0, math.pi, 1.0),
    ),
    "old-canal": (
        ("south-survey-rig", 0.0, -48.0, 0.0, 0.0, 1.0),
        ("canal-segment-a-marker", -30.0, -23.0, 0.0, 0.12, 1.0),
        ("canal-segment-b-marker", 2.0, 0.0, 0.0, -0.08, 1.0),
        ("canal-segment-c-marker", 32.0, 23.0, 0.0, 0.15, 1.0),
        ("north-outflow-gate", 0.0, 48.0, 0.0, math.pi, 1.0),
    ),
}

claim.CONTRACT_PLATES.update({key: profile["sourcePlate"] for key, profile in PROFILES.items()})
claim.GRIT_PROFILES.update({
    "seed-run": {"black": 0.008, "white": 0.58, "gamma": 1.15, "ink": 0.43, "palette": 0.19, "saturation": 0.53},
    "devils-alley": {"black": 0.007, "white": 0.54, "gamma": 1.17, "ink": 0.46, "palette": 0.20, "saturation": 0.57},
    "old-canal": {"black": 0.008, "white": 0.50, "gamma": 1.21, "ink": 0.48, "palette": 0.18, "saturation": 0.49},
})


def documents(key):
    contracts = json.loads(CONTRACTS.read_text(encoding="utf-8"))["contracts"]
    profile = PROFILES[key]
    matches = [entry for entry in contracts if entry["id"] == profile["contractId"]]
    if len(matches) != 1:
        raise ValueError(f"expected one E9 factory contract for {key}")
    table_path = TABLE_DIR / f"{profile['contractId']}.json"
    table = json.loads(table_path.read_text(encoding="utf-8"))
    identities = {matches[0]["tileParams"]["tileId"], table["maskTruth"]["tileId"], profile["contractId"]}
    if len(identities) != 1:
        raise ValueError(f"E9 identity mismatch for {key}")
    return matches[0], table, table_path


def smoothstep(edge0, edge1, value):
    return base.smoothstep(edge0, edge1, value)


def gaussian(x, z, cx, cz, sx, sz):
    return base.gaussian(x, z, cx, cz, sx, sz)


def rectangle_mask(x, z, zone, feather=1.0):
    return base.rectangle_mask(x, z, zone, feather)


def route_mask(x, z, points, radius):
    result = np.zeros_like(np.asarray(x, dtype=np.float32))
    for start, end in zip(points, points[1:]):
        result = np.maximum(result, e2.segment_mask(x, z, start, end, radius))
    return result


def exact_zone_write(sculpted, xx, zz, zones, targets):
    diagonal = math.hypot(128.0 / SEGMENTS, 128.0 / SEGMENTS)
    for zone in zones:
        exact = (
            (xx >= zone["minX"] - diagonal)
            & (xx <= zone["maxX"] + diagonal)
            & (zz >= zone["minZ"] - diagonal)
            & (zz <= zone["maxZ"] + diagonal)
        )
        sculpted = np.where(exact, targets[zone["id"]], sculpted)
    return sculpted


def height_function(key, table):
    truth = table["maskTruth"]
    targets = TARGET_HEIGHTS[key]

    if key == "seed-run":
        route = truth["caravanRoute"]

        def height(x, z):
            xx, zz = np.asarray(x, dtype=np.float32), np.asarray(z, dtype=np.float32)
            climb = 0.25 + smoothstep(-55.0, 55.0, zz) * 0.95
            dunes = (
                gaussian(xx, zz, 47.0, -28.0, 13.0, 27.0) * 2.35
                + gaussian(xx, zz, -49.0, 14.0, 12.0, 31.0) * 2.75
                + gaussian(xx, zz, 45.0, 47.0, 18.0, 11.0) * 1.55
                + gaussian(xx, zz, -42.0, -49.0, 16.0, 10.0) * 1.30
            )
            grain = np.sin(xx * 0.24 + zz * 0.15) * 0.075 + np.sin(xx * 0.09 - zz * 0.41) * 0.040
            road = route_mask(xx, zz, route, 4.8)
            shoulders = route_mask(xx, zz, route, 8.0) - road
            sculpted = climb + dunes + grain + shoulders * 0.34
            road_height = 0.27 + smoothstep(-50.0, 50.0, zz) * 0.90
            sculpted = sculpted * (1.0 - road * 0.92) + road_height * road * 0.92
            sculpted = exact_zone_write(sculpted, xx, zz, truth["buildZones"], targets)
            edge = smoothstep(0.94, 1.0, np.maximum(np.abs(xx), np.abs(zz)) / 64.0)
            return sculpted * (1.0 - edge) - 0.14 * edge

        return height

    if key == "devils-alley":
        corridors = truth["dustDevilCorridors"]

        def height(x, z):
            xx, zz = np.asarray(x, dtype=np.float32), np.asarray(z, dtype=np.float32)
            sculpted = 0.38 + np.sin(xx * 0.17 + zz * 0.11) * 0.060 + np.sin(xx * 0.37 - zz * 0.09) * 0.035
            # Four hard dune walls make the three authored wind lanes the
            # dominant landform instead of decorative stripes.
            for index, wall_z in enumerate((-40.0, -13.0, 13.0, 40.0)):
                broken = 1.0 + np.sin(xx * (0.12 + index * 0.01) + index) * 0.22
                sculpted += np.exp(-(((zz - wall_z) / 6.0) ** 2)) * (2.20 + index * 0.18) * broken
            for index, corridor in enumerate(corridors):
                lane = rectangle_mask(xx, zz, corridor, 2.6)
                floor = 0.06 + index * 0.12 + np.sin(xx * 0.23 + index) * 0.030
                sculpted = sculpted * (1.0 - lane * 0.86) + floor * lane * 0.86
                sculpted -= np.exp(-(((zz - (-26.0 + index * 26.0)) / 1.55) ** 2)) * 0.22
            sculpted += gaussian(xx, zz, -55.0, 0.0, 7.0, 33.0) * 1.2
            sculpted += gaussian(xx, zz, 55.0, 3.0, 8.0, 30.0) * 1.4
            sculpted = exact_zone_write(sculpted, xx, zz, truth["buildZones"], targets)
            edge = smoothstep(0.94, 1.0, np.maximum(np.abs(xx), np.abs(zz)) / 64.0)
            return sculpted * (1.0 - edge) - 0.14 * edge

        return height

    route = truth["inheritedCanalRoute"]["points"]

    def height(x, z):
        xx, zz = np.asarray(x, dtype=np.float32), np.asarray(z, dtype=np.float32)
        grain = np.sin(xx * 0.19 + zz * 0.13) * 0.075 + np.sin(xx * 0.07 - zz * 0.39) * 0.042
        shelves = (
            1.95 * gaussian(xx, zz, -50.0, 3.0, 11.0, 34.0)
            + 2.35 * gaussian(xx, zz, 51.0, -9.0, 10.0, 32.0)
            + 1.20 * gaussian(xx, zz, -10.0, 53.0, 28.0, 9.0)
        )
        canal = route_mask(xx, zz, route, 4.0)
        spoil = np.clip(route_mask(xx, zz, route, 7.8) - route_mask(xx, zz, route, 5.0), 0.0, 1.0)
        scar = route_mask(xx, zz, route, 1.8)
        sculpted = 0.45 + shelves + grain + spoil * (0.78 + np.sin(xx * 0.33 + zz * 0.19) * 0.16)
        sculpted = sculpted * (1.0 - canal * 0.92) + (-1.30 + np.sin(xx * 0.11 - zz * 0.08) * 0.05) * canal * 0.92
        sculpted -= scar * 0.22
        sculpted = exact_zone_write(sculpted, xx, zz, truth["buildZones"], targets)
        edge = smoothstep(0.94, 1.0, np.maximum(np.abs(xx), np.abs(zz)) / 64.0)
        return sculpted * (1.0 - edge) - 0.14 * edge

    return height


def make_atlas(key, profile, table):
    source = claim.image_pixels(profile["sourcePlate"])
    kit = claim.image_pixels(KIT)
    dirt = claim.image_pixels(claim.BANK_A)
    rock = claim.image_pixels(claim.BANK_C)
    axis = np.linspace(0.0, 1.0, ATLAS_SIZE, dtype=np.float32)
    u, v = np.meshgrid(axis, axis)
    x, z = (u - 0.5) * 128.0, (v - 0.5) * 128.0
    plate = claim.tiled_sample(source, u, v, 3.6, 0.17, 0.43)
    paper = claim.tiled_sample(kit, u, v, 4.0, 0.53, 0.11)
    stain = claim.tiled_sample(dirt, u, v, 7.2, 0.27, 0.61)
    shale = claim.tiled_sample(rock, u, v, 8.5, 0.08, 0.36)
    macro = (np.sin(x * 0.085 + z * 0.061) * 0.5 + 0.5)[..., None]
    atlas = (
        plate * 0.26
        + paper * (0.20 + macro * 0.05)
        + stain * (0.33 - macro * 0.04)
        + shale * 0.17
    ) * np.asarray((0.72, 0.38, 0.27), dtype=np.float32)
    truth = table["maskTruth"]

    if key == "seed-run":
        route = route_mask(x, z, truth["caravanRoute"], 5.0)
        road = paper * np.asarray((0.37, 0.20, 0.13), dtype=np.float32)
        atlas = atlas * (1.0 - route[..., None] * 0.46) + road * route[..., None] * 0.46
        for zone in truth["permanentGreenWaypointZones"]:
            green = rectangle_mask(x, z, zone, 2.0)
            hatch = np.clip(0.72 + np.sin(x * 0.71 + z * 0.33) * 0.18, 0.35, 0.92)
            weight = green * hatch
            atlas = atlas * (1.0 - weight[..., None] * 0.78) + E1_GREEN[None, None, :] * weight[..., None] * 0.78
    elif key == "devils-alley":
        for index, corridor in enumerate(truth["dustDevilCorridors"]):
            lane = rectangle_mask(x, z, corridor, 2.2)
            spiral = np.sin(x * (0.30 + index * 0.03) + np.sin(z * 0.41 + index)) * 0.5 + 0.5
            dust = paper * np.asarray((0.54, 0.31, 0.15), dtype=np.float32)
            weight = lane * (0.34 + spiral * 0.24)
            atlas = atlas * (1.0 - weight[..., None]) + dust * weight[..., None]
    else:
        route = route_mask(x, z, truth["inheritedCanalRoute"]["points"], 4.2)
        shoulder = np.clip(route_mask(x, z, truth["inheritedCanalRoute"]["points"], 7.5) - route, 0.0, 1.0)
        canal_ink = shale * np.asarray((0.30, 0.20, 0.17), dtype=np.float32)
        atlas = atlas * (1.0 - route[..., None] * 0.62) + canal_ink * route[..., None] * 0.62
        atlas *= 1.0 - shoulder[..., None] * 0.16

    # Pockmarks, dragged survey scars, and deep edge shadow keep the atlas in
    # the Grit Law while the E1 green remains the one tended exception.
    pocks = np.zeros_like(x)
    for index in range(17):
        cx = -54.0 + (index * 37 % 109)
        cz = -52.0 + (index * 53 % 105)
        pocks = np.maximum(pocks, gaussian(x, z, cx, cz, 0.8 + index % 3, 0.6 + (index + 1) % 3))
    atlas *= 1.0 - pocks[..., None] * 0.18
    edge = smoothstep(0.90, 1.0, np.maximum(np.abs(x), np.abs(z)) / 64.0)[..., None]
    atlas = atlas * (1.0 - edge * 0.72) + shale * np.asarray((0.31, 0.22, 0.19), dtype=np.float32) * edge * 0.72
    atlas = claim.apply_grit_grade(atlas, source, u, v, key)

    rgba = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    rgba[:, :, :3] = np.clip(atlas, 0.004, 0.72)
    path = OUT / f"{profile['stem']}-atlas.png"
    image = bpy.data.images.new(profile["atlas"], ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image, path


def zone_outline(zone, height_at, lift=0.84):
    points = []
    corners = (
        (zone["minX"], zone["minZ"]),
        (zone["maxX"], zone["minZ"]),
        (zone["maxX"], zone["maxZ"]),
        (zone["minX"], zone["maxZ"]),
        (zone["minX"], zone["minZ"]),
    )
    for start, end in zip(corners, corners[1:]):
        for amount in np.linspace(0.0, 1.0, 13, endpoint=False):
            x = start[0] + (end[0] - start[0]) * amount
            z = start[1] + (end[1] - start[1]) * amount
            points.append((x, z, float(height_at(x, z)) + lift))
    points.append(points[0])
    return points


def add_preview(key, table, height_at, materials):
    truth = table["maskTruth"]
    objects = []
    route = truth.get("caravanRoute") or truth.get("inheritedCanalRoute", {}).get("points")
    if route:
        points = [(point["x"], point["z"], float(height_at(point["x"], point["z"])) + 0.55) for point in route]
        objects.append(claim.add_curve(f"RenderHelper.{key}.Route", points, 0.18, materials["brass"]))
    for marker in truth["stakeMarkers"]:
        h = float(height_at(marker["x"], marker["z"]))
        objects.append(claim.add_box_game(f"RenderHelper.{key}.{marker['id']}", marker["x"], marker["z"], h, (1.8, 1.8, 1.15), materials["warm"], bevel=0.08))
        objects.append(claim.add_cylinder_between(f"RenderHelper.{key}.{marker['id']}.Post", (marker["x"], marker["z"], h), (marker["x"], marker["z"], h + 3.2), 0.14, materials["brass"]))
    if key == "devils-alley":
        for index, z in enumerate((-26.0, 0.0, 26.0)):
            points = []
            for step in range(80):
                t = step / 79
                radius = 3.8 * (1.0 - t * 0.54)
                angle = t * math.tau * 4.4 + index * 1.7
                x = (-30.0 + index * 30.0) + math.cos(angle) * radius
                gz = z + math.sin(angle) * radius
                points.append((x, gz, float(height_at(x, gz)) + 0.5 + t * 12.0))
            objects.append(claim.add_curve(f"RenderHelper.DustDevil.{index}", points, 0.14, materials["danger"]))
    # Mount bodies stay proxies; only the transforms export in the contract.
    for mount_id, x, z, _y, yaw, scale in LANDMARK_MOUNTS[key]:
        h = float(height_at(x, z))
        objects.append(claim.add_box_game(f"RenderHelper.Mount.{mount_id}", x, z, h, (1.2 * scale, 1.2 * scale, 0.18), materials["brass"], yaw=yaw, bevel=0.03))
    rng = np.random.default_rng({"seed-run": 1901, "devils-alley": 1907, "old-canal": 1913}[key])
    placed = 0
    for _ in range(260):
        if placed >= 54:
            break
        x, z = float(rng.uniform(-60, 60)), float(rng.uniform(-60, 60))
        if any(zone["minX"] - 2 <= x <= zone["maxX"] + 2 and zone["minZ"] - 2 <= z <= zone["maxZ"] + 2 for zone in truth["buildZones"]):
            continue
        h0 = float(height_at(x, z))
        if max(abs(float(height_at(x + dx, z + dz)) - h0) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))) > 0.45:
            continue
        size = float(rng.uniform(0.35, 1.1))
        objects.append(claim.add_rock(f"RenderHelper.{key}.Rubble.{placed:02d}", x, z, (size, size * 0.7, size * 0.55), materials["stone"], float(rng.uniform(-math.pi, math.pi))))
        placed += 1
    return objects


def add_overlay(key, table, height_at, materials):
    truth = table["maskTruth"]
    objects = [claim.add_curve(f"RenderHelper.Mask.Build.{zone['id']}", zone_outline(zone, height_at), 0.18, materials["mask"]) for zone in truth["buildZones"]]
    for marker in truth["stakeMarkers"]:
        h = float(height_at(marker["x"], marker["z"]))
        objects.append(claim.add_curve(f"RenderHelper.Mask.Stake.{marker['id']}", [(marker["x"] - 1.2, marker["z"], h + 1.0), (marker["x"] + 1.2, marker["z"], h + 1.0)], 0.18, materials["warm"]))
    special = truth.get("permanentGreenWaypointZones") or truth.get("dustDevilCorridors") or truth.get("canalDecisionZones") or []
    for zone in special:
        objects.append(claim.add_curve(f"RenderHelper.Mask.Special.{zone['id']}", zone_outline(zone, height_at, 1.10), 0.13, materials["danger"]))
    return objects


def add_lighting(key, table, height_at):
    lights = claim.add_lighting(sunset=True)
    for index, marker in enumerate(table["maskTruth"]["stakeMarkers"]):
        data = bpy.data.lights.new(f"{key}.Warm.{index}", "POINT")
        data.energy = 480 if key == "seed-run" else 330
        data.color = (1.0, 0.36, 0.07)
        data.shadow_soft_size = 2.4
        obj = bpy.data.objects.new(f"{key}.Warm.{index}", data)
        bpy.context.collection.objects.link(obj)
        obj.location = (marker["x"], -marker["z"], float(height_at(marker["x"], marker["z"])) + 3.0)
        lights.append(obj)
    return lights


def render_verdicts(key, profile, table, terrain, panorama, preview, overlay, height_at):
    backdrop = claim.make_backdrop()
    backdrop.location.z = -2.8
    nodes = backdrop.active_material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBackground")
    shader.inputs["Color"].default_value = (0.055, 0.017, 0.010, 1.0)
    shader.inputs["Strength"].default_value = 1.0
    backdrop.active_material.node_tree.links.new(shader.outputs[0], output.inputs[0])
    panorama.hide_render = True
    cameras = {
        "run": claim.add_camera(f"{profile['object']}Run", (0.0, -18.3, 26.2), (0.0, 3.35, 0.45), 42.0),
        "composition": claim.add_camera(f"{profile['object']}Composition", (0.0, 68.0, 48.0), (0.0, -2.0, 0.6), 48.0),
        "overview": claim.add_camera(f"{profile['object']}Overview", (0.0, 102.0, 106.0), (0.0, 0.0, 0.5), 47.0),
        "low": claim.add_camera(f"{profile['object']}Low", (-56.0, 68.0, 22.0), (0.0, -2.0, 0.8), 52.0),
        "top": claim.add_camera(f"{profile['object']}Mask", (0.0, 0.0, 158.0), (0.0, 0.0, 0.0), 52.0),
        "horizon": claim.add_camera(f"{profile['object']}Horizon", (0.0, 0.0, 5.0), (98.0, -170.0, 13.0), 54.0),
    }
    for camera in cameras.values():
        camera.data.clip_end = 440.0
    lights = add_lighting(key, table, height_at)
    bpy.context.scene.view_settings.exposure = 0.55
    for obj in preview + overlay:
        obj.hide_render = True
    saved = [vertex.co.z for vertex in terrain.data.vertices]
    for vertex in terrain.data.vertices:
        vertex.co.z = 0.0
    terrain.data.update()
    claim.render(cameras["composition"], ARTIFACTS / f"{key}-flat-tile-identical-camera.png")
    for vertex, value in zip(terrain.data.vertices, saved):
        vertex.co.z = value
    terrain.data.update()
    claim.render(cameras["composition"], ARTIFACTS / f"{key}-sculpted-tile-identical-camera.png")
    for obj in preview:
        obj.hide_render = False
    claim.render(cameras["low"], ARTIFACTS / f"{key}-panorama-before.png")
    for obj in overlay:
        obj.hide_render = False
    claim.render(cameras["top"], ARTIFACTS / f"{key}-mask-agreement.png")
    for obj in overlay:
        obj.hide_render = True
    backdrop.hide_render = True
    panorama.hide_render = False
    claim.render(cameras["run"], ARTIFACTS / f"{key}-run-camera.png")
    claim.render(cameras["composition"], ARTIFACTS / f"{key}-composition.png")
    claim.render(cameras["overview"], ARTIFACTS / f"{key}-overview.png")
    claim.render(cameras["low"], ARTIFACTS / f"{key}-low-sunset.png")
    claim.render(cameras["low"], ARTIFACTS / f"{key}-panorama-mounted.png")
    for obj in preview:
        obj.hide_render = True
    claim.render(cameras["horizon"], ARTIFACTS / f"{key}-panorama-horizon.png")
    bpy.context.scene.view_settings.exposure = 0.0
    claim.remove_objects(lights + list(cameras.values()) + [backdrop, panorama])


def build_zone_flatness(table, height_at):
    results = []
    for zone in table["maskTruth"]["buildZones"]:
        samples = [float(height_at(x, z)) for x in np.linspace(zone["minX"], zone["maxX"], 65) for z in np.linspace(zone["minZ"], zone["maxZ"], 33)]
        results.append({"id": zone["id"], "bounds": [zone["minX"], zone["maxX"], zone["minZ"], zone["maxZ"]], "sampledSurfacePoints": len(samples), "maxDeviationMeters": round(max(samples) - min(samples), 6)})
    return results


def mounts(key, height_at):
    records = []
    for mount_id, x, z, y, yaw, scale in LANDMARK_MOUNTS[key]:
        records.append({
            "id": mount_id,
            "asset": "",
            "position": [x, round(float(height_at(x, z)) + y, 4), z],
            "rotation": [0.0, round(yaw, 4), 0.0],
            "scale": [scale, scale, scale],
        })
    return records


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_terrain(key, profile, table, table_path, terrain, atlas_path, height_at):
    blend, glb = OUT / f"{profile['stem']}.blend", OUT / f"{profile['stem']}.glb"
    triangle_count = sum(len(poly.vertices) - 2 for poly in terrain.data.polygons)
    landmark_mounts = mounts(key, height_at)
    terrain["landmarks_frozen"] = False
    terrain["landmark_mount_ids"] = json.dumps([mount["id"] for mount in landmark_mounts])
    terrain["runtime_owned_visuals_absent"] = True
    bpy.ops.object.select_all(action="DESELECT")
    terrain.select_set(True)
    bpy.context.view_layer.objects.active = terrain
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", use_selection=True, export_apply=True, export_cameras=False, export_lights=False, export_animations=False, export_extras=True)
    contract = {
        "asset": glb.name,
        "contractId": profile["contractId"],
        "tileId": table["maskTruth"]["tileId"],
        "renderOnly": True,
        "simulation": "planar; movement, collision, placement, spawns, persistence, water, and event mechanics remain code-owned and unchanged",
        "heightSocket": "Terrain.visualY",
        "theme": profile["theme"],
        "regionalFamily": {"epoch": "Epoch 9 redfields heart-era", "shared": ["rust-red engraved dunes", "parchment abrasion", "deep survey shadow", "warm dome-work light", "literal E1 green only where authored"], "unique": profile["unique"]},
        "meshCount": 1,
        "primitiveCount": 1,
        "materialCount": 1,
        "vertices": len(terrain.data.vertices),
        "triangles": triangle_count,
        "triangleBudget": 60000,
        "texture": {"count": 1, "width": ATLAS_SIZE, "height": ATLAS_SIZE, "embedded": True},
        "maskTable": str(table_path.relative_to(ROOT)),
        "maskTruth": table["maskTruth"],
        "waterAgreement": table["waterAgreement"],
        "buildZoneFlatness": build_zone_flatness(table, height_at),
        "landmarkMounts": landmark_mounts,
        "landmarkMountSpace": claim.landmark_mount_space(),
        "panoramaMount": claim.panorama_mount(key),
        "runtimeVisualsAbsent": ["persistent green state", "moving dust devils", "building relocation", "canal choices", "future water flow", "spawn gates"],
        "verdictPreviewOnly": {"excludedFromBlendAndGlb": True, "reason": "route lines, dust columns, rubble, mount proxies, mask overlays, and lights are evidence helpers only"},
        "sourceArt": [str(KIT.relative_to(ROOT)), str(profile["sourcePlate"].relative_to(ROOT)), str(claim.BANK_A.relative_to(ROOT)), str(claim.BANK_C.relative_to(ROOT))],
        "atlas": atlas_path.name,
    }
    if triangle_count != 32768 or any(zone["maxDeviationMeters"] > 0.001 for zone in contract["buildZoneFlatness"]):
        raise AssertionError(f"{key} terrain geometry or build-zone flatness failed")
    contract["files"] = {
        "blend": {"bytes": blend.stat().st_size, "sha256": sha256(blend)},
        "glb": {"bytes": glb.stat().st_size, "sha256": sha256(glb)},
        "atlas": {"bytes": atlas_path.stat().st_size, "sha256": sha256(atlas_path)},
    }
    (OUT / f"{profile['stem']}-contract.json").write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    return contract


def build(key):
    profile = PROFILES[key]
    _factory, table, table_path = documents(key)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    claim.reset_scene()
    atlas, atlas_path = make_atlas(key, profile, table)
    material = claim.make_material(atlas)
    material.name = profile["material"]
    height_at = height_function(key, table)
    claim.terrain_height = height_at
    terrain = base.make_terrain(profile, table, table_path, height_at, material)
    panorama_objects = claim.link_panorama(key)
    if len(panorama_objects) != 1:
        raise AssertionError(f"expected one separate Panorama v2 object for {key}")
    panorama = panorama_objects[0]
    materials = base.preview_materials(key)
    preview = add_preview(key, table, height_at, materials)
    overlay = add_overlay(key, table, height_at, materials)
    render_verdicts(key, profile, table, terrain, panorama, preview, overlay, height_at)
    claim.remove_objects(preview + overlay)
    bpy.context.scene.world = None
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    contract = export_terrain(key, profile, table, table_path, terrain, atlas_path, height_at)
    print(json.dumps({"key": key, "triangles": contract["triangles"], "buildZoneFlatness": contract["buildZoneFlatness"]}, indent=2))


def main():
    keys = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else list(PROFILES)
    for key in keys:
        if key not in PROFILES:
            raise ValueError(f"unsupported E9 terrain: {key}")
        build(key)


if __name__ == "__main__":
    main()
