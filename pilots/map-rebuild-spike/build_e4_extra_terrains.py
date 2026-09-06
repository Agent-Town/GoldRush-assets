"""Build the Long Road, Gusher County, and Boneyard render terrains.

The published E4 masks remain the only gameplay authority.  Terrain,
panoramas, props, and elevation in this script are render-only evidence for
the existing Terrain.visualY seam.
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
KIT = ROOT / "assets/processed/kit-era-4.png"
RAW_KIT = ROOT / "assets/raw/kit-era-4.png"
BUILDING_PLATE = ROOT / "assets/raw/plate-e4-bld-set.png"
YACHT_PLATE = ROOT / "assets/raw/plate-e4-boss-land-yacht.png"
SEGMENTS = 128
ATLAS_SIZE = 2048


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_module("e4_extra_terrain_base", OUT / "build_e3_contract_terrains.py")
claim = base.claim

PROFILES = {
    "long-road": {
        "contractId": "e4-long-road",
        "stem": "long-road-terrain",
        "object": "LongRoadTerrain",
        "mesh": "LongRoadTerrainMesh",
        "material": "LongRoadPaintedTerrainMaterial",
        "atlas": "LongRoadPaintedTerrainAtlas",
        "width": 400.0,
        "height": 96.0,
        "theme": "a four-hundred-metre graded road whose three exact way-station shelves punctuate a moving town's eastward march",
        "sourcePlate": RAW_KIT,
        "unique": "one extreme linear road landform, three alternating station shelves, and a hard eastern railhead cut",
    },
    "gusher-county": {
        "contractId": "e4-gusher-county",
        "stem": "gusher-county-terrain",
        "object": "GusherCountyTerrain",
        "mesh": "GusherCountyTerrainMesh",
        "material": "GusherCountyPaintedTerrainMaterial",
        "atlas": "GusherCountyPaintedTerrainAtlas",
        "width": 160.0,
        "height": 160.0,
        "theme": "a tar-scarred oil basin divided into three exact lease shelves around one battered county camp",
        "sourcePlate": BUILDING_PLATE,
        "unique": "three distinct lease shoulders, eight wild-well scars, and a crude-dark camp basin",
    },
    "boneyard": {
        "contractId": "e4-boneyard",
        "stem": "boneyard-terrain",
        "object": "BoneyardTerrain",
        "mesh": "BoneyardTerrainMesh",
        "material": "BoneyardPaintedTerrainMaterial",
        "atlas": "BoneyardPaintedTerrainAtlas",
        "width": 128.0,
        "height": 128.0,
        "theme": "a quiet salvage valley with two exact machine rows, a defended gate shelf, and one half-buried northern sleeper hollow",
        "sourcePlate": YACHT_PLATE,
        "unique": "paired salvage terraces, forked approach cuts, rust pockets, and a deliberately undisturbed sleeper hollow",
    },
}

TARGETS = {
    "long-road": {"west-way-station": 0.18, "middle-way-station": 0.34, "east-way-station": 0.52},
    "gusher-county": {"county-camp": 0.18, "west-lease": 0.44, "east-lease": 0.62, "north-lease": 0.78},
    "boneyard": {"gate-camp": 0.18, "west-rows": 0.48, "east-rows": 0.62},
}

MOUNTS = {
    "long-road": (
        ("west-way-station", -136.0, -14.0, 0.00, 1.00),
        ("middle-way-station", 0.0, 14.0, math.pi, 1.00),
        ("east-way-station", 136.0, -14.0, 0.00, 1.00),
        ("convoy-lead-hauler-start", -180.0, 0.0, -math.pi / 2.0, 1.00),
        ("east-railhead", 188.0, 0.0, math.pi / 2.0, 1.10),
    ),
    "gusher-county": tuple((f"derrick-{index:02d}", x, z, 0.0, 1.0) for index, (x, z) in enumerate(((-56, -36), (-40, -48), (40, -44), (56, -32), (-44, 44), (-16, 52), (20, 48), (48, 40)), 1))
    + (("outhouse-geyser", 14.0, -10.0, 0.12, 0.82), ("county-camp-rig", 0.0, -4.0, 0.0, 1.0)),
    "boneyard": (
        ("flivver-row-west-a", -48.0, -12.0, 0.18, 0.82),
        ("flivver-row-west-b", -36.0, 4.0, -0.10, 0.86),
        ("flivver-row-west-c", -24.0, 18.0, 0.08, 0.80),
        ("spent-boiler-west", -18.0, -8.0, 0.0, 0.90),
        ("spent-boiler-east", 18.0, -8.0, 0.0, 0.90),
        ("flivver-row-east-a", 24.0, 18.0, -0.12, 0.84),
        ("flivver-row-east-b", 36.0, 4.0, 0.14, 0.88),
        ("flivver-row-east-c", 48.0, -12.0, -0.06, 0.82),
        ("hauler-bed-north-a", -8.0, 34.0, 0.04, 1.00),
        ("hauler-bed-north-b", 8.0, 34.0, -0.05, 1.00),
        ("half-buried-sleeper", 34.0, 36.0, 0.22, 1.18),
        ("unmarked-wagon", -38.0, 30.0, -0.18, 0.92),
    ),
}

for map_key, profile in PROFILES.items():
    claim.CONTRACT_PLATES[map_key] = profile["sourcePlate"]
    claim.GRIT_PROFILES[map_key] = {
        "black": 0.007,
        "white": 0.56 if map_key == "long-road" else 0.50,
        "gamma": 1.17 if map_key == "long-road" else 1.23,
        "ink": 0.43 if map_key == "long-road" else 0.49,
        "palette": 0.18,
        "saturation": 0.50 if map_key == "gusher-county" else 0.46,
    }


def smoothstep(edge0, edge1, value):
    return base.smoothstep(edge0, edge1, value)


def gaussian(x, z, cx, cz, sx, sz):
    return base.gaussian(x, z, cx, cz, sx, sz)


def rectangle_mask(x, z, zone, feather=1.0):
    return base.rectangle_mask(x, z, zone, feather)


def documents(key):
    profile = PROFILES[key]
    factory = base.factory_contract(profile["contractId"])
    table, table_path = base.mask_table(profile["contractId"])
    identities = {factory["id"], factory["tileParams"]["tileId"], table["maskTruth"]["tileId"]}
    if identities != {profile["contractId"]}:
        raise ValueError(f"{key} identity mismatch: {sorted(identities)}")
    return factory, table, table_path


def guarded_flats(key, table, sculpted, xx, zz):
    profile = PROFILES[key]
    guard = math.hypot(profile["width"] / SEGMENTS, profile["height"] / SEGMENTS)
    for zone in table["maskTruth"]["buildZones"]:
        exact = (
            (xx >= zone["minX"] - guard) & (xx <= zone["maxX"] + guard)
            & (zz >= zone["minZ"] - guard) & (zz <= zone["maxZ"] + guard)
        )
        sculpted = np.where(exact, TARGETS[key][zone["id"]], sculpted)
    return sculpted


def height_function(key, table):
    truth = table["maskTruth"]
    half_x = PROFILES[key]["width"] * 0.5
    half_z = PROFILES[key]["height"] * 0.5

    def height(x, z):
        xx, zz = np.asarray(x, dtype=np.float32), np.asarray(z, dtype=np.float32)
        grain = np.sin(xx * 0.17 + zz * 0.13) * 0.052 + np.sin(xx * 0.071 - zz * 0.37) * 0.029
        if key == "long-road":
            along = smoothstep(-198.0, -190.0, xx) * (1.0 - smoothstep(190.0, 198.0, xx))
            road = np.exp(-((zz / 5.4) ** 4)) * along
            shoulder = np.exp(-(((np.abs(zz) - 6.4) / 1.65) ** 2)) * along
            ruts = np.maximum(np.exp(-(((zz - 1.65) / 0.52) ** 2)), np.exp(-(((zz + 1.65) / 0.52) ** 2))) * along
            verge = (
                gaussian(xx, zz, -105.0, 38.0, 52.0, 11.0) * 1.20
                + gaussian(xx, zz, 82.0, -40.0, 62.0, 10.0) * 1.42
                + gaussian(xx, zz, 177.0, 34.0, 23.0, 12.0) * 0.82
            )
            sculpted = 0.34 + grain + verge - road * 0.28 + shoulder * 0.44 - ruts * 0.18
            for corridor in truth["roadCorridors"][1:]:
                spur = base.e2.segment_mask(xx, zz, corridor["start"], corridor["end"], 2.8)
                sculpted = sculpted * (1.0 - spur * 0.55) + 0.27 * spur * 0.55
        elif key == "gusher-county":
            rim = (
                gaussian(xx, zz, -73.0, 8.0, 10.0, 49.0) * 2.45
                + gaussian(xx, zz, 73.0, -4.0, 11.0, 45.0) * 2.75
                + gaussian(xx, zz, -10.0, 75.0, 45.0, 9.5) * 1.84
            )
            basin = -gaussian(xx, zz, 0.0, -1.0, 43.0, 37.0) * 0.42
            sculpted = 0.42 + grain + rim + basin
            for road in truth["roadCorridors"]:
                road_mask = base.e2.segment_mask(xx, zz, road["start"], road["end"], 3.5)
                sculpted = sculpted * (1.0 - road_mask * 0.48) + 0.29 * road_mask * 0.48
            for seam in truth["tarSeams"]:
                sculpted -= gaussian(xx, zz, seam["x"], seam["z"], seam["radius"] * 1.15, seam["radius"] * 0.88) * 0.34
        else:
            walls = (
                gaussian(xx, zz, -59.0, 9.0, 7.5, 36.0) * 2.22
                + gaussian(xx, zz, 59.0, 5.0, 8.0, 34.0) * 2.52
                + gaussian(xx, zz, -8.0, 61.0, 37.0, 7.0) * 1.26
            )
            valley = -gaussian(xx, zz, 0.0, 4.0, 37.0, 33.0) * 0.38
            row_shoulders = gaussian(xx, zz, -35.0, 2.0, 18.0, 30.0) * 0.42 + gaussian(xx, zz, 35.0, 2.0, 18.0, 30.0) * 0.58
            sleeper = gaussian(xx, zz, 34.0, 36.0, 8.0, 7.0)
            wagon_cut = gaussian(xx, zz, -38.0, 30.0, 5.0, 4.0)
            sculpted = 0.36 + grain + walls + valley + row_shoulders - sleeper * 0.76 - wagon_cut * 0.28
            for road in truth["roadCorridors"]:
                road_mask = base.e2.segment_mask(xx, zz, road["start"], road["end"], 3.2)
                sculpted = sculpted * (1.0 - road_mask * 0.44) + 0.24 * road_mask * 0.44

        for zone in truth["buildZones"]:
            shoulder = {
                "minX": zone["minX"] - 3.2, "maxX": zone["maxX"] + 3.2,
                "minZ": zone["minZ"] - 3.2, "maxZ": zone["maxZ"] + 3.2,
            }
            shelf = rectangle_mask(xx, zz, shoulder, 2.6)
            sculpted = sculpted * (1.0 - shelf * 0.54) + TARGETS[key][zone["id"]] * shelf * 0.54
        sculpted = guarded_flats(key, table, sculpted, xx, zz)
        edge = smoothstep(0.94, 1.0, np.maximum(np.abs(xx) / half_x, np.abs(zz) / half_z))
        return sculpted * (1.0 - edge) - 0.14 * edge

    return height


def make_atlas(key, profile, table):
    kit = claim.image_pixels(KIT)
    plate = claim.image_pixels(profile["sourcePlate"])
    dirt = claim.image_pixels(claim.BANK_A)
    stone = claim.image_pixels(claim.BANK_C)
    axis = np.linspace(0.0, 1.0, ATLAS_SIZE, dtype=np.float32)
    u, v = np.meshgrid(axis, axis)
    x, z = (u - 0.5) * profile["width"], (v - 0.5) * profile["height"]
    paper = claim.tiled_sample(kit, u, v, 4.4, 0.13, 0.57)
    machinery = claim.tiled_sample(plate, u, v, 5.3, 0.41, 0.19)
    soil = claim.tiled_sample(dirt, u, v, 7.6, 0.27, 0.64)
    shale = claim.tiled_sample(stone, u, v, 8.8, 0.07, 0.35)
    macro = (np.sin(x * 0.081 + z * 0.057) * 0.5 + 0.5)[..., None]
    atlas = (paper * 0.23 + machinery * 0.18 + soil * (0.34 + macro * 0.05) + shale * (0.25 - macro * 0.05))
    atlas *= np.asarray((0.73, 0.54, 0.34) if key != "boneyard" else (0.62, 0.51, 0.40), dtype=np.float32)
    truth = table["maskTruth"]

    roads = np.zeros_like(x)
    for road in truth.get("roadCorridors", []):
        width = 5.5 if key == "long-road" and road["id"] == "the-long-road" else 3.8
        roads = np.maximum(roads, base.e2.segment_mask(x, z, road["start"], road["end"], width))
    packed = paper * np.asarray((0.38, 0.29, 0.19), dtype=np.float32) + machinery * 0.10
    atlas = atlas * (1.0 - roads[..., None] * 0.42) + packed * roads[..., None] * 0.42

    if key == "long-road":
        ruts = np.maximum(np.exp(-(((z - 1.65) / 0.42) ** 2)), np.exp(-(((z + 1.65) / 0.42) ** 2)))
        ruts *= smoothstep(-198.0, -190.0, x) * (1.0 - smoothstep(190.0, 198.0, x))
        atlas *= 1.0 - ruts[..., None] * 0.30
        for index, station in enumerate(truth["restStops"]):
            pad = rectangle_mask(x, z, station, 1.4)
            repair = paper * np.asarray((0.52, 0.39, 0.24), dtype=np.float32)
            atlas = atlas * (1.0 - pad[..., None] * 0.22) + repair * pad[..., None] * 0.22
            atlas *= 1.0 - pad[..., None] * (0.03 + index * 0.015)
    elif key == "gusher-county":
        for seam in truth["tarSeams"]:
            stain = gaussian(x, z, seam["x"], seam["z"], seam["radius"] * 1.4, seam["radius"] * 1.05)
            tar = machinery * np.asarray((0.105, 0.075, 0.045), dtype=np.float32)
            atlas = atlas * (1.0 - stain[..., None] * 0.62) + tar * stain[..., None] * 0.62
        for well in truth["wildDerricks"]:
            ring = np.exp(-(((np.hypot(x - well["x"], z - well["z"]) - 2.8) / 0.42) ** 2))
            atlas *= 1.0 - ring[..., None] * 0.32
    else:
        for index, hulk in enumerate(truth["salvageHulks"]):
            stain = gaussian(x, z, hulk["x"], hulk["z"], 2.9 + index % 3, 2.0 + (index + 1) % 2)
            rust = machinery * np.asarray((0.42, 0.20, 0.09), dtype=np.float32)
            atlas = atlas * (1.0 - stain[..., None] * 0.34) + rust * stain[..., None] * 0.34
        sleeper = truth["sleeper"]
        sleeper_shadow = gaussian(x, z, sleeper["x"], sleeper["z"], 8.0, 6.5)
        atlas *= 1.0 - sleeper_shadow[..., None] * 0.40

    scars = np.zeros_like(x)
    for index in range(31):
        cx = -profile["width"] * 0.46 + (index * 67 % 193) / 192.0 * profile["width"] * 0.92
        cz = -profile["height"] * 0.46 + (index * 43 % 181) / 180.0 * profile["height"] * 0.92
        scars = np.maximum(scars, gaussian(x, z, cx, cz, 0.8 + index % 4, 0.45 + (index + 1) % 3))
    atlas *= 1.0 - scars[..., None] * 0.15
    edge = smoothstep(0.90, 1.0, np.maximum(np.abs(x) / (profile["width"] * 0.5), np.abs(z) / (profile["height"] * 0.5)))[..., None]
    atlas = atlas * (1.0 - edge * 0.58) + shale * np.asarray((0.22, 0.17, 0.12), dtype=np.float32) * edge * 0.58
    atlas = claim.apply_grit_grade(atlas, plate, u, v, key)

    rgba = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    rgba[:, :, :3] = np.clip(atlas, 0.004, 0.68)
    path = OUT / f"{profile['stem']}-atlas.png"
    image = bpy.data.images.new(profile["atlas"], ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image, path


def add_preview(key, table, height_at, materials):
    objects = []
    for mount_id, x, z, yaw, scale in MOUNTS[key]:
        ground = float(height_at(x, z))
        objects.append(claim.add_box_game(f"RenderHelper.Mount.{mount_id}", x, z, ground, (1.3 * scale, 1.3 * scale, 0.18), materials["brass"], yaw=yaw, bevel=0.04))
        if key == "long-road" and "station" in mount_id:
            objects.append(claim.add_box_game(f"RenderHelper.Station.{mount_id}.Shed", x, z, ground + 0.1, (8.0, 5.0, 3.4), materials["timber"], yaw=yaw, bevel=0.10))
            objects.append(claim.add_roof_prism(f"RenderHelper.Station.{mount_id}.Roof", x, z, ground + 3.3, 8.8, 5.8, 1.5, materials["rust"]))
        elif key == "gusher-county" and mount_id.startswith("derrick"):
            apex = ground + 8.0
            for index, (ox, oz) in enumerate(((-1.5, -1.5), (1.5, -1.5), (-1.5, 1.5), (1.5, 1.5))):
                objects.append(claim.add_beam(f"RenderHelper.{mount_id}.Leg.{index}", (x + ox, z + oz, ground), (x, z, apex), 0.18, materials["iron"]))
            objects.append(claim.add_box_game(f"RenderHelper.{mount_id}.Cap", x, z, apex, (2.2, 2.2, 0.32), materials["brass"], bevel=0.05))
        elif key == "boneyard":
            length = 5.4 if "hauler" in mount_id or "sleeper" in mount_id else 3.8
            height = 1.15 if "boiler" not in mount_id else 1.8
            objects.append(claim.add_box_game(f"RenderHelper.Hulk.{mount_id}", x, z, ground - (0.38 if "sleeper" in mount_id else 0.04), (length * scale, 2.3 * scale, height * scale), materials["rust"], yaw=yaw, bevel=0.16))

    rng = np.random.default_rng({"long-road": 4041, "gusher-county": 4042, "boneyard": 4043}[key])
    half_x, half_z = PROFILES[key]["width"] * 0.5, PROFILES[key]["height"] * 0.5
    placed = 0
    for _ in range(360):
        if placed >= (74 if key == "long-road" else 56):
            break
        x, z = float(rng.uniform(-half_x + 2, half_x - 2)), float(rng.uniform(-half_z + 2, half_z - 2))
        if any(zone["minX"] - 2 <= x <= zone["maxX"] + 2 and zone["minZ"] - 2 <= z <= zone["maxZ"] + 2 for zone in table["maskTruth"]["buildZones"]):
            continue
        if key == "long-road" and abs(z) < 8.0:
            continue
        ground = float(height_at(x, z))
        if max(abs(float(height_at(x + dx, z + dz)) - ground) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))) > 0.58:
            continue
        size = float(rng.uniform(0.28, 1.05))
        objects.append(claim.add_rock(f"RenderHelper.E4Rubble.{placed:03d}", x, z, (size * rng.uniform(0.8, 1.7), size * rng.uniform(0.65, 1.1), size * rng.uniform(0.45, 0.85)), materials["stone"], float(rng.uniform(-math.pi, math.pi))))
        placed += 1
    return objects


def add_overlay(key, table, height_at, materials):
    objects = base.add_mask_overlay("e4-campaign-generic", table, height_at, materials)
    truth = table["maskTruth"]
    for road in truth.get("roadCorridors", []):
        points = []
        for amount in np.linspace(0.0, 1.0, 49):
            x = road["start"]["x"] + (road["end"]["x"] - road["start"]["x"]) * amount
            z = road["start"]["z"] + (road["end"]["z"] - road["start"]["z"]) * amount
            points.append((float(x), float(z), float(height_at(x, z)) + 0.82))
        objects.append(claim.add_curve(f"RenderHelper.Road.{road['id']}", points, 0.18, materials["danger"]))
    for seam in truth.get("tarSeams", []):
        objects.append(claim.add_curve(f"RenderHelper.Tar.{seam['id']}", base.ring_points(seam["x"], seam["z"], seam["radius"], height_at, 0.90), 0.19, materials["warm"]))
    for hulk in truth.get("salvageHulks", []):
        objects.append(claim.add_curve(f"RenderHelper.HulkMask.{hulk['id']}", base.ring_points(hulk["x"], hulk["z"], 1.45, height_at, 0.90), 0.17, materials["warm"]))
    if key == "boneyard":
        sleeper = truth["sleeper"]
        objects.append(claim.add_curve("RenderHelper.SleeperMask", base.ring_points(sleeper["x"], sleeper["z"], sleeper["radius"], height_at, 0.94), 0.23, materials["danger"]))
    return objects


def render_verdicts(key, profile, table, terrain, panorama, preview, overlay, height_at):
    backdrop = claim.make_backdrop()
    backdrop.location.z = -3.0
    panorama.hide_render = True
    if key == "long-road":
        camera_specs = {
            "run": ((0.0, 52.0, 35.0), (28.0, 0.0, 0.4), 44.0),
            "composition": ((0.0, 162.0, 245.0), (0.0, 0.0, 0.2), 50.0),
            "overview": ((0.0, 12.0, 340.0), (0.0, 0.0, 0.0), 51.0),
            "low": ((-145.0, 55.0, 20.0), (55.0, 0.0, 0.8), 54.0),
            "top": ((0.0, 0.0, 430.0), (0.0, 0.0, 0.0), 52.0),
        }
    else:
        camera_specs = {
            "run": ((0.0, 56.0, 38.0), (0.0, -6.0, 0.6), 43.0),
            "composition": ((0.0, 94.0, 73.0), (0.0, 0.0, 0.6), 48.0),
            "overview": ((0.0, 18.0, 182.0), (0.0, 0.0, 0.4), 49.0),
            "low": ((-68.0, 72.0, 21.0), (8.0, 0.0, 0.9), 53.0),
            "top": ((0.0, 0.0, 196.0), (0.0, 0.0, 0.0), 49.0),
        }
    cameras = {name: claim.add_camera(f"{key}.{name}", *spec) for name, spec in camera_specs.items()}
    cameras["horizon"] = claim.add_camera(f"{key}.horizon", (0.0, 0.0, 5.0), (145.0, -120.0, 10.0), 53.0)
    for camera in cameras.values():
        camera.data.clip_end = 520.0
    lights = claim.add_lighting(sunset=False)
    bpy.context.scene.view_settings.exposure = 0.58
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
        results.append({
            "id": zone["id"],
            "bounds": [zone["minX"], zone["maxX"], zone["minZ"], zone["maxZ"]],
            "sampledSurfacePoints": len(samples),
            "maxDeviationMeters": round(max(samples) - min(samples), 6),
        })
    return results


def landmark_mounts(key, height_at):
    return [
        {
            "id": mount_id,
            "asset": "",
            "position": [x, round(float(height_at(x, z)), 4), z],
            "rotation": [0.0, round(yaw, 4), 0.0],
            "scale": [scale, scale, scale],
        }
        for mount_id, x, z, yaw, scale in MOUNTS[key]
    ]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_asset(key, profile, table, table_path, terrain, atlas_path, height_at):
    blend = OUT / f"{profile['stem']}.blend"
    glb = OUT / f"{profile['stem']}.glb"
    contract_path = OUT / f"{profile['stem']}-contract.json"
    triangles = sum(len(poly.vertices) - 2 for poly in terrain.data.polygons)
    flatness = build_zone_flatness(table, height_at)
    mounts = landmark_mounts(key, height_at)
    terrain["landmark_mount_ids"] = json.dumps([mount["id"] for mount in mounts])
    terrain["runtime_owned_visuals_absent"] = True
    bpy.ops.object.select_all(action="DESELECT")
    terrain.select_set(True)
    bpy.context.view_layer.objects.active = terrain
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", use_selection=True, export_apply=True, export_cameras=False, export_lights=False, export_animations=False, export_extras=True)
    coords = np.asarray([vertex.co[:] for vertex in terrain.data.vertices], dtype=np.float32)
    contract = {
        "asset": glb.name,
        "contractId": profile["contractId"],
        "tileId": table["maskTruth"]["tileId"],
        "renderOnly": True,
        "simulation": "planar; movement, collision, placement, spawns, convoy, eruptions, salvage, wake triggers, weather, and combat remain code-owned",
        "heightSocket": "Terrain.visualY",
        "theme": profile["theme"],
        "regionalFamily": {
            "epoch": "Epoch 4 motor frontier",
            "shared": ["dust-warm ochre", "tar-dark stains", "engraved wheel scars", "sun-cracked earth", "sparse cacti", "hazy motor distance"],
            "unique": profile["unique"],
        },
        "boundsMeters": {"min": [round(float(v), 4) for v in coords.min(axis=0)], "max": [round(float(v), 4) for v in coords.max(axis=0)]},
        "meshCount": 1,
        "primitiveCount": 1,
        "materialCount": 1,
        "vertices": len(terrain.data.vertices),
        "triangles": triangles,
        "triangleBudget": 60000,
        "texture": {"count": 1, "width": ATLAS_SIZE, "height": ATLAS_SIZE, "embedded": True},
        "maskTable": str(table_path.relative_to(ROOT)),
        "maskTruth": table["maskTruth"],
        "waterAgreement": table["waterAgreement"],
        "buildZoneFlatness": flatness,
        "landmarkMounts": mounts,
        "landmarkMountSpace": claim.landmark_mount_space(),
        "panoramaMount": claim.panorama_mount(key),
        "runtimeVisualsAbsent": ["convoy movement", "anchorage windows", "wild-well eruptions", "tar sprites", "salvage race", "sleeper wake", "weather", "spawn gates"],
        "verdictPreviewOnly": {"excludedFromBlendAndGlb": True, "reason": "mount bodies, rubble, cacti, masks, panorama, and evidence lighting are review helpers only"},
        "sourceArt": [str(path.relative_to(ROOT)) for path in (KIT, profile["sourcePlate"], claim.BANK_A, claim.BANK_C)],
        "atlas": atlas_path.name,
    }
    if triangles != 32768 or any(zone["maxDeviationMeters"] > 0.001 for zone in flatness):
        raise AssertionError(f"{key} geometry or build-zone flatness failed")
    contract["files"] = {
        "blend": {"bytes": blend.stat().st_size, "sha256": sha256(blend)},
        "glb": {"bytes": glb.stat().st_size, "sha256": sha256(glb)},
        "atlas": {"bytes": atlas_path.stat().st_size, "sha256": sha256(atlas_path)},
    }
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
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
        raise AssertionError(f"expected one separate {key} Panorama v2 object")
    materials = base.preview_materials("dust-flats")
    preview = add_preview(key, table, height_at, materials)
    overlay = add_overlay(key, table, height_at, materials)
    render_verdicts(key, profile, table, terrain, panorama_objects[0], preview, overlay, height_at)
    claim.remove_objects(preview + overlay)
    bpy.context.scene.world = None
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    contract = export_asset(key, profile, table, table_path, terrain, atlas_path, height_at)
    print(json.dumps({"asset": contract["asset"], "triangles": contract["triangles"], "buildZoneFlatness": contract["buildZoneFlatness"], "mounts": len(contract["landmarkMounts"])}, indent=2))


def main():
    requested = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else list(PROFILES)
    for key in requested:
        if key not in PROFILES:
            raise ValueError(f"unsupported E4 campaign terrain: {key}")
        build(key)


if __name__ == "__main__":
    main()
