"""Build the render-only E5 Regatta sea-floor terrain.

The exported mesh is bathymetry only. Runtime remains the sole owner of the
sea surface, fast-water state, Claim-Boat, race checkpoints, spawns, movement,
placement, and combat.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"
FACTORY = ROOT / "assets/contracts/epoch-5-deepwater/contracts.json"
TABLE = ROOT / "assets/contracts/epoch-5-deepwater/mask-tables/e5-regatta.json"
KIT = ROOT / "assets/processed/kit-era-5.png"
SHELF_ATLAS = ROOT / "assets/raw/ter-shelf-atlas.png"
CONTRACT_ID = "e5-regatta"
KEY = "regatta"
STEM = "regatta-terrain"
WIDTH = HEIGHT = 128.0
ATLAS_SIZE = 2048


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_module("e5_regatta_base", OUT / "build_e5_deepwater_terrain.py")
claim = base.claim
e3 = base.e3
claim.CONTRACT_PLATES[KEY] = SHELF_ATLAS
claim.GRIT_PROFILES[KEY] = {
    "black": 0.006,
    "white": 0.43,
    "gamma": 1.20,
    "ink": 0.47,
    "palette": 0.17,
    "saturation": 0.56,
}

PROFILE = {
    "contractId": CONTRACT_ID,
    "stem": STEM,
    "object": "RegattaTerrain",
    "mesh": "RegattaTerrainMesh",
    "material": "RegattaPaintedBathymetryMaterial",
    "atlas": "RegattaPaintedBathymetryAtlas",
    "width": WIDTH,
    "height": HEIGHT,
    "theme": "an open-water storm race over a bent scoured course, five submerged beacon rises, and a dark fast-water shelf",
    "epoch": "Epoch 5 post-flood harbor chain",
    "shared": [
        "blue-green parchment depth",
        "tar-dark working water shadows",
        "brass course scars",
        "charcoal storm fronts",
        "tea-coloured open-sea distance",
        "warm lantern persistence",
    ],
}


def smoothstep(edge0, edge1, value):
    value = np.asarray(value, dtype=np.float32)
    t = np.clip((value - edge0) / max(edge1 - edge0, 0.0001), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def gaussian(x, z, cx, cz, sx, sz):
    return np.exp(-(((x - cx) / sx) ** 2 + ((z - cz) / sz) ** 2) * 0.5)


def rectangle_mask(x, z, zone, feather=1.0):
    return (
        smoothstep(zone["minX"] - feather, zone["minX"] + feather, x)
        * (1.0 - smoothstep(zone["maxX"] - feather, zone["maxX"] + feather, x))
        * smoothstep(zone["minZ"] - feather, zone["minZ"] + feather, z)
        * (1.0 - smoothstep(zone["maxZ"] - feather, zone["maxZ"] + feather, z))
    )


def segment_mask(x, z, start, end, half_width):
    ax, az = start["x"], start["z"]
    bx, bz = end["x"], end["z"]
    dx, dz = bx - ax, bz - az
    length_sq = max(dx * dx + dz * dz, 0.0001)
    t = np.clip(((x - ax) * dx + (z - az) * dz) / length_sq, 0.0, 1.0)
    distance = np.hypot(x - (ax + t * dx), z - (az + t * dz))
    return 1.0 - smoothstep(half_width * 0.72, half_width, distance)


def documents():
    factory = json.loads(FACTORY.read_text(encoding="utf-8"))
    matches = [entry for entry in factory["contracts"] if entry["id"] == CONTRACT_ID]
    if len(matches) != 1:
        raise ValueError(f"expected one factory contract for {CONTRACT_ID}")
    table = json.loads(TABLE.read_text(encoding="utf-8"))
    if table["maskTruth"]["tileId"] != CONTRACT_ID:
        raise ValueError("Regatta mask table tile id changed")
    return matches[0], table


def course_masks(x, z, truth):
    beacons = truth["raceCourse"]["beacons"]
    core = np.zeros_like(np.asarray(x, dtype=np.float32))
    shoulder = np.zeros_like(core)
    for start, end in zip(beacons, beacons[1:]):
        core = np.maximum(core, segment_mask(x, z, start, end, 2.2))
        shoulder = np.maximum(shoulder, segment_mask(x, z, start, end, 6.2))
    return core, shoulder


def height_function(table):
    truth = table["maskTruth"]
    fast = truth["raceCourse"]["fastWaterZone"]
    beacons = truth["raceCourse"]["beacons"]

    def height(x, z):
        xx = np.asarray(x, dtype=np.float32)
        zz = np.asarray(z, dtype=np.float32)
        grain = np.sin(xx * 0.18 + zz * 0.10) * 0.10 + np.sin(xx * 0.47 - zz * 0.31) * 0.05
        floor = -3.35 + grain
        floor -= gaussian(xx, zz, -42.0, -24.0, 17.0, 13.0) * 0.38
        floor -= gaussian(xx, zz, 39.0, 20.0, 18.0, 14.0) * 0.30

        fast_mask = rectangle_mask(xx, zz, fast, 3.0)
        storm_scars = np.maximum.reduce([
            gaussian(xx, zz, -36.0, 44.0, 17.0, 4.0),
            gaussian(xx, zz, 0.0, 46.0, 19.0, 4.6),
            gaussian(xx, zz, 37.0, 43.0, 16.0, 3.8),
        ])
        fast_floor = -5.10 - storm_scars * 0.48 + np.sin(xx * 0.23) * 0.09
        floor = floor * (1.0 - fast_mask) + fast_floor * fast_mask
        floor += np.exp(-(((zz - fast["minZ"]) / 1.55) ** 2)) * 0.48

        core, shoulder = course_masks(xx, zz, truth)
        floor += shoulder * 0.28
        floor -= core * 0.48
        for index, beacon in enumerate(beacons):
            rise = gaussian(xx, zz, beacon["x"], beacon["z"], 5.3, 5.3)
            ring = np.exp(-(((np.hypot(xx - beacon["x"], zz - beacon["z"]) - 3.3) / 0.62) ** 2))
            floor += rise * (1.25 + (index % 2) * 0.12) + ring * 0.26

        perimeter = smoothstep(0.94, 1.0, np.maximum(np.abs(xx) / 64.0, np.abs(zz) / 64.0))
        floor = floor * (1.0 - perimeter) + (-3.7 + np.sin(xx * 0.13 - zz * 0.09) * 0.08) * perimeter
        return np.clip(floor, -5.75, -0.42)

    return height


def make_atlas(table):
    source = claim.image_pixels(SHELF_ATLAS)
    half_y, half_x = source.shape[0] // 2, source.shape[1] // 2
    kelp = source[:half_y, :half_x]
    sand = source[half_y:, half_x:]
    reef = source[half_y:, :half_x]
    kit = claim.image_pixels(KIT)
    axis = np.linspace(0.0, 1.0, ATLAS_SIZE, dtype=np.float32)
    u, v = np.meshgrid(axis, axis)
    x, z = (u - 0.5) * WIDTH, (v - 0.5) * HEIGHT
    warped_u = u + np.sin(v * math.tau * 3.1) * 0.013
    warped_v = v + np.sin(u * math.tau * 4.2 + 0.4) * 0.011
    kelp_sample = claim.tiled_sample(kelp, warped_u, warped_v, 5.2, 0.18, 0.57)
    sand_sample = claim.tiled_sample(sand, warped_u, warped_v, 4.1, 0.62, 0.13)
    reef_sample = claim.tiled_sample(reef, warped_u, warped_v, 6.4, 0.31, 0.46)
    kit_sample = claim.tiled_sample(kit, u, v, 4.5, 0.39, 0.17)
    macro = (np.sin(x * 0.071 + z * 0.047) * 0.5 + 0.5)[..., None]
    atlas = kelp_sample * (0.44 + macro * 0.08) + sand_sample * (0.25 - macro * 0.05) + reef_sample * 0.16 + kit_sample * 0.15
    atlas *= np.asarray((0.46, 0.65, 0.67), dtype=np.float32)

    truth = table["maskTruth"]
    fast = truth["raceCourse"]["fastWaterZone"]
    fast_mask = rectangle_mask(x, z, fast, 2.4)
    storm_ink = kelp_sample * np.asarray((0.18, 0.28, 0.30), dtype=np.float32)
    storm_breakup = np.clip(0.64 + np.sin(x * 0.29 + z * 0.13) * 0.22, 0.22, 0.90)
    atlas = atlas * (1.0 - fast_mask[..., None] * 0.62) + storm_ink * fast_mask[..., None] * 0.62
    atlas *= 1.0 - (fast_mask * storm_breakup)[..., None] * 0.18

    core, shoulder = course_masks(x, z, truth)
    brass = sand_sample * np.asarray((0.55, 0.43, 0.20), dtype=np.float32)
    teal = reef_sample * np.asarray((0.25, 0.55, 0.55), dtype=np.float32)
    atlas = atlas * (1.0 - shoulder[..., None] * 0.18) + teal * shoulder[..., None] * 0.18
    atlas = atlas * (1.0 - core[..., None] * 0.31) + brass * core[..., None] * 0.31
    for beacon in truth["raceCourse"]["beacons"]:
        radius = np.hypot(x - beacon["x"], z - beacon["z"])
        ring = np.exp(-(((radius - beacon["radius"]) / 0.36) ** 2))
        atlas = atlas * (1.0 - ring[..., None] * 0.55) + brass * ring[..., None] * 0.55

    atlas = claim.apply_grit_grade(atlas, source, u, v, KEY)
    rgba = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    rgba[..., :3] = np.clip(atlas, 0.004, 0.70)
    path = OUT / f"{STEM}-atlas.png"
    image = bpy.data.images.new(PROFILE["atlas"], ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image, path


def add_course_preview(table, materials):
    truth = table["maskTruth"]
    objects = []
    beacons = truth["raceCourse"]["beacons"]
    for index, beacon in enumerate(beacons):
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.44, depth=1.8, location=(beacon["x"], -beacon["z"], 0.34))
        marker = bpy.context.object
        marker.name = f"RenderHelperRaceBeacon.{beacon['id']}"
        marker.data.materials.append(materials["teal"] if index % 2 else materials["brass"])
        objects.append(marker)
    route = [(beacon["x"], beacon["z"], 0.18) for beacon in beacons]
    objects.append(claim.add_curve("RenderHelperRaceCourse", route, 0.13, materials["brass"]))
    return objects


def rectangle_points(zone, lift):
    return [
        (zone["minX"], zone["minZ"], lift),
        (zone["maxX"], zone["minZ"], lift),
        (zone["maxX"], zone["maxZ"], lift),
        (zone["minX"], zone["maxZ"], lift),
        (zone["minX"], zone["minZ"], lift),
    ]


def add_mask_overlay(table, materials):
    truth = table["maskTruth"]
    objects = []
    build = truth["buildZones"][0]
    fast = truth["raceCourse"]["fastWaterZone"]
    objects.append(claim.add_curve(f"RenderHelperBuildZone.{build['id']}", rectangle_points(build, 0.86), 0.24, materials["reef"]))
    objects.append(claim.add_curve(f"RenderHelperRegion.{fast['id']}", rectangle_points(fast, 0.68), 0.20, materials["trench"]))
    for beacon in truth["raceCourse"]["beacons"]:
        points = []
        for index in range(25):
            angle = index / 24 * math.tau
            points.append((beacon["x"] + math.cos(angle) * beacon["radius"], beacon["z"] + math.sin(angle) * beacon["radius"], 0.74))
        objects.append(claim.add_curve(f"RenderHelperBeaconMask.{beacon['id']}", points, 0.16, materials["shelf"]))
    for spawn in truth["spawnGates"]:
        objects.append(claim.add_box_game(f"RenderHelperSpawn.{spawn['edge']}", spawn["x"], spawn["z"], 0.18, (1.1, 4.0, 1.2), materials["trench"], bevel=0.04))
    return objects


def add_lighting(table):
    world = bpy.data.worlds.new("RegattaVerdictWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.030, 0.042, 0.044, 1.0)
    background.inputs["Strength"].default_value = 0.52
    sun_data = bpy.data.lights.new("RegattaStormLullSun", "SUN")
    sun_data.energy = 2.0
    sun_data.color = (0.59, 0.68, 0.64)
    sun_data.angle = math.radians(24)
    sun = bpy.data.objects.new("RegattaStormLullSun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.location = (-58.0, 25.0, 46.0)
    claim.aim_at(sun, (0.0, 8.0, -2.8))
    anchor = table["maskTruth"]["deepwater"]["claimBoat"]["anchors"][0]
    lights = [sun]
    for index, dx in enumerate((-3.8, 3.8)):
        data = bpy.data.lights.new(f"RegattaBoatLantern.{index}", "POINT")
        data.energy = 480.0
        data.color = (1.0, 0.40, 0.08)
        data.shadow_soft_size = 3.3
        light = bpy.data.objects.new(f"RegattaBoatLantern.{index}", data)
        bpy.context.collection.objects.link(light)
        light.location = (anchor["x"] + dx, -anchor["z"], 2.1)
        lights.append(light)
    return lights


def render_verdicts(table, terrain, sea, preview, overlay):
    panorama = claim.link_panorama(KEY)
    for obj in panorama:
        obj.visible_shadow = False
        obj.hide_render = True
    run = claim.add_camera("RegattaRunCamera", (-3.0, 49.0, 42.0), (0.0, 13.0, -2.4), 48.0)
    overview = claim.add_camera("RegattaOverview", (0.0, 94.0, 120.0), (0.0, 8.0, -2.8), 49.0)
    low = claim.add_camera("RegattaLowWeather", (-55.0, 47.0, 11.0), (9.0, 19.0, -1.7), 50.0)
    top = claim.add_camera("RegattaMaskCamera", (0.0, 0.0, 155.0), (0.0, 0.0, -2.8), 52.0)
    horizon = claim.add_camera("RegattaHorizon", (0.0, 0.0, 3.4), (-148.0, 84.0, 4.2), 53.0)
    for camera in (run, overview, low, top, horizon):
        camera.data.clip_end = 430.0
    lights = add_lighting(table)
    bpy.context.scene.view_settings.exposure = 1.06
    for obj in preview + overlay:
        obj.hide_render = True
    sea.hide_render = True
    saved = [vertex.co.z for vertex in terrain.data.vertices]
    for vertex in terrain.data.vertices:
        vertex.co.z = -3.35
    terrain.data.update()
    claim.render(run, ARTIFACTS / "regatta-flat-tile-identical-camera.png")
    for vertex, value in zip(terrain.data.vertices, saved):
        vertex.co.z = value
    terrain.data.update()
    claim.render(run, ARTIFACTS / "regatta-sculpted-tile-identical-camera.png")
    sea.hide_render = False
    for obj in preview:
        obj.hide_render = False
    claim.render(low, ARTIFACTS / "regatta-panorama-before.png")
    sea.hide_render = True
    for obj in overlay:
        obj.hide_render = False
    claim.render(top, ARTIFACTS / "regatta-mask-agreement.png")
    for obj in overlay:
        obj.hide_render = True
    sea.hide_render = False
    for obj in panorama:
        obj.hide_render = False
    claim.render(run, ARTIFACTS / "regatta-run-camera.png")
    claim.render(overview, ARTIFACTS / "regatta-overview.png")
    claim.render(low, ARTIFACTS / "regatta-low-sunset.png")
    claim.render(low, ARTIFACTS / "regatta-panorama-mounted.png")
    claim.render(horizon, ARTIFACTS / "regatta-panorama-horizon.png")
    bpy.context.scene.view_settings.exposure = 0.0
    claim.remove_objects(lights + [run, overview, low, top, horizon] + panorama)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_contract(table, terrain, atlas_path):
    coords = np.asarray([vertex.co[:] for vertex in terrain.data.vertices], dtype=np.float32)
    triangles = sum(len(poly.vertices) - 2 for poly in terrain.data.polygons)
    return {
        "asset": f"{STEM}.glb",
        "contractId": CONTRACT_ID,
        "tileId": CONTRACT_ID,
        "renderOnly": True,
        "simulation": "planar movement, collision, spawns, race checkpoints, fast-water state, Claim-Boat placement, and combat remain unchanged",
        "heightSocket": "Terrain.visualY",
        "waterSurface": {"owner": "runtime DeepwaterClaimTile", "includedInTerrainGLB": False, "reason": "sea surface, swell, fast-water state, and water classification stay code-owned"},
        "theme": PROFILE["theme"],
        "regionalFamily": {"epoch": PROFILE["epoch"], "shared": PROFILE["shared"], "unique": ["bent beacon-course bathymetry", "five submerged beacon rises", "storm-front scarp", "open-sea panorama"]},
        "boundsMeters": {"min": [round(float(v), 4) for v in coords.min(axis=0)], "max": [round(float(v), 4) for v in coords.max(axis=0)]},
        "meshCount": 1,
        "primitiveCount": 1,
        "materialCount": 1,
        "vertices": len(terrain.data.vertices),
        "triangles": triangles,
        "triangleBudget": 60000,
        "texture": {"count": 1, "width": ATLAS_SIZE, "height": ATLAS_SIZE, "embedded": True},
        "maskTable": str(TABLE.relative_to(ROOT)),
        "maskTruth": table["maskTruth"],
        "maskAgreement": {
            "openWater": "surface and travel classification remain runtime-owned",
            "fastWater": "dark submerged storm shelf follows the published x=-54..54 z=34..54 race zone without claiming water speed",
            "beacons": "five submerged foundation rises follow the published checkpoint centers and radii",
            "claimBoatDeck": "delegated to the separate runtime Claim-Boat body; no terrain deck is baked",
        },
        "landmarkMounts": [],
        "panoramaMount": claim.panorama_mount(KEY),
        "evidenceRig": "runtime-water proxy, warm Claim-Boat lanterns, five course beacons, and course trace; all helpers removed before terrain save/export",
        "sourceArt": [str(path.relative_to(ROOT)) for path in (KIT, SHELF_ATLAS)],
        "atlas": atlas_path.name,
    }


def export_asset(terrain, contract):
    blend = OUT / f"{STEM}.blend"
    glb = OUT / f"{STEM}.glb"
    atlas = OUT / f"{STEM}-atlas.png"
    contract_path = OUT / f"{STEM}-contract.json"
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
    print(json.dumps({"asset": glb.name, "triangles": contract["triangles"], "waterSurfaceIncluded": False}, indent=2))


def main():
    factory, table = documents()
    if factory["tileParams"]["dimensions"] != {"width": 128, "height": 128}:
        raise ValueError("Regatta authored dimensions changed")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    claim.reset_scene()
    atlas, atlas_path = make_atlas(table)
    material = claim.make_material(atlas)
    material.name = PROFILE["material"]
    height_at = height_function(table)
    claim.terrain_height = height_at
    terrain = e3.make_terrain(PROFILE, table, TABLE, height_at, material)
    terrain["water_surface_owner"] = "runtime; absent from this GLB"
    terrain["bathymetry_only"] = True
    materials = base.helper_materials()
    sea = base.make_sea_proxy(base.sea_material())
    preview = base.add_claim_boat_proxy(table, materials) + add_course_preview(table, materials)
    overlay = add_mask_overlay(table, materials)
    render_verdicts(table, terrain, sea, preview, overlay)
    claim.remove_objects([sea] + preview + overlay)
    bpy.context.scene.world = None
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    contract = make_contract(table, terrain, atlas_path)
    if contract["triangles"] > contract["triangleBudget"]:
        raise AssertionError("Regatta terrain triangle budget exceeded")
    export_asset(terrain, contract)


if __name__ == "__main__":
    main()
