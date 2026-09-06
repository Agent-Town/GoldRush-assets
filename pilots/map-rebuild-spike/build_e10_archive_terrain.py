"""Build the Archive World render-only terrain.

The published table remains the authority for every gameplay system. Heights
feed Terrain.visualY only; Static/re-ink states remain code-owned.
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
TABLE_PATH = ROOT / "assets/contracts/epoch-10-deepsky/mask-tables/e10-archive-world.json"
KIT = ROOT / "assets/processed/kit-era-10.png"
WORLDS = ROOT / "assets/raw/plate-e10-worlds.png"
SEGMENTS = 128
ATLAS_SIZE = 2048


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_module("archive_terrain_base", OUT / "build_e3_contract_terrains.py")
claim = base.claim
e2 = base.e2
PROFILE = {
    "contractId": "e10-archive-world",
    "stem": "archive-world-terrain",
    "object": "ArchiveWorldTerrain",
    "mesh": "ArchiveWorldTerrainMesh",
    "material": "ArchiveWorldPaintedTerrainMaterial",
    "atlas": "ArchiveWorldPaintedTerrainAtlas",
    "width": 128.0,
    "height": 128.0,
    "theme": "a prior civilization's library un-inked mid-sentence, with three exact restoration wings around a broken central memory cut",
}
TARGETS = {
    "archive-entry": 0.18,
    "west-stacks-wing": 0.56,
    "east-stacks-wing": 0.78,
    "warning-shelf-wing": 1.08,
}
MOUNTS = (
    ("archive-entry-gate", 0.0, -46.0, 0.0, 1.0),
    ("west-stack-ruin", -28.0, -6.0, 0.10, 1.0),
    ("east-stack-ruin", 28.0, -6.0, -0.10, 1.0),
    ("warning-shelf-ruin", -14.0, 40.0, 0.08, 1.0),
    ("ours-unless-marker", 0.0, 46.0, 0.0, 0.74),
)

claim.CONTRACT_PLATES["archive-world"] = WORLDS
claim.GRIT_PROFILES["archive-world"] = {
    "black": 0.004,
    "white": 0.43,
    "gamma": 1.28,
    "ink": 0.54,
    "palette": 0.18,
    "saturation": 0.46,
}


def smoothstep(edge0, edge1, value):
    return base.smoothstep(edge0, edge1, value)


def gaussian(x, z, cx, cz, sx, sz):
    return base.gaussian(x, z, cx, cz, sx, sz)


def rectangle_mask(x, z, zone, feather=1.0):
    return base.rectangle_mask(x, z, zone, feather)


def documents():
    factory = base.factory_contract("e10-archive-world")
    table = json.loads(TABLE_PATH.read_text(encoding="utf-8"))
    identities = {factory["id"], factory["tileParams"]["tileId"], table["maskTruth"]["tileId"]}
    if identities != {"e10-archive-world"}:
        raise ValueError(f"Archive World identity mismatch: {sorted(identities)}")
    return factory, table


def height_function(table):
    truth = table["maskTruth"]
    cell_diagonal = math.hypot(PROFILE["width"] / SEGMENTS, PROFILE["height"] / SEGMENTS)

    def height(x, z):
        xx, zz = np.asarray(x, dtype=np.float32), np.asarray(z, dtype=np.float32)
        grain = np.sin(xx * 0.21 + zz * 0.14) * 0.060 + np.sin(xx * 0.08 - zz * 0.39) * 0.035
        perimeter = (
            gaussian(xx, zz, -55.0, -4.0, 8.0, 37.0) * 2.8
            + gaussian(xx, zz, 55.0, 2.0, 9.0, 34.0) * 3.2
            + gaussian(xx, zz, -33.0, 57.0, 25.0, 8.0) * 2.1
            + gaussian(xx, zz, 38.0, -57.0, 22.0, 7.0) * 1.4
        )
        # The missing central sentence is a broken, aged-paper cut between the
        # two stack wings, not a gameplay trench or a collision barrier.
        central_cut = np.exp(-((xx / 4.0) ** 4)) * (
            smoothstep(-34.0, -28.0, zz) * (1.0 - smoothstep(19.0, 25.0, zz))
        )
        broken_aisles = (
            np.exp(-(((xx + 53.0) / 2.2) ** 2)) * smoothstep(-31.0, -24.0, zz) * (1.0 - smoothstep(18.0, 25.0, zz))
            + np.exp(-(((xx - 53.0) / 2.4) ** 2)) * smoothstep(-29.0, -22.0, zz) * (1.0 - smoothstep(17.0, 24.0, zz))
            + np.exp(-(((zz - 57.0) / 2.5) ** 2)) * smoothstep(-30.0, -23.0, xx) * (1.0 - smoothstep(28.0, 35.0, xx))
        )
        sculpted = 0.34 + grain + perimeter - central_cut * 1.48 - broken_aisles * 0.55
        # Broad shoulders make the exact playable wings feel excavated from
        # one ruined library instead of four floating rectangular plinths.
        for zone in truth["buildZones"]:
            shoulder = {
                "minX": zone["minX"] - 4.0,
                "maxX": zone["maxX"] + 4.0,
                "minZ": zone["minZ"] - 4.0,
                "maxZ": zone["maxZ"] + 4.0,
            }
            shelf = rectangle_mask(xx, zz, shoulder, 3.4)
            sculpted = sculpted * (1.0 - shelf * 0.58) + TARGETS[zone["id"]] * shelf * 0.58
        # One-cell diagonal guard makes every exported triangle crossing a
        # build boundary constant across the authored rectangle.
        for zone in truth["buildZones"]:
            exact = (
                (xx >= zone["minX"] - cell_diagonal)
                & (xx <= zone["maxX"] + cell_diagonal)
                & (zz >= zone["minZ"] - cell_diagonal)
                & (zz <= zone["maxZ"] + cell_diagonal)
            )
            sculpted = np.where(exact, TARGETS[zone["id"]], sculpted)
        edge = smoothstep(0.94, 1.0, np.maximum(np.abs(xx), np.abs(zz)) / 64.0)
        return sculpted * (1.0 - edge) + 0.10 * edge

    return height


def make_atlas(table):
    kit = claim.image_pixels(KIT)
    worlds = claim.image_pixels(WORLDS)
    stone = claim.image_pixels(claim.BANK_C)
    dirt = claim.image_pixels(claim.BANK_A)
    axis = np.linspace(0.0, 1.0, ATLAS_SIZE, dtype=np.float32)
    u, v = np.meshgrid(axis, axis)
    x, z = (u - 0.5) * 128.0, (v - 0.5) * 128.0
    ink = claim.tiled_sample(kit, u, v, 4.2, 0.19, 0.43)
    plate = claim.tiled_sample(worlds, u, v, 4.8, 0.57, 0.17)
    shale = claim.tiled_sample(stone, u, v, 8.4, 0.11, 0.37)
    soil = claim.tiled_sample(dirt, u, v, 7.0, 0.34, 0.62)
    macro = (np.sin(x * 0.071 + z * 0.053) * 0.5 + 0.5)[..., None]
    atlas = (
        ink * (0.31 + macro * 0.04)
        + plate * 0.18
        + shale * (0.31 - macro * 0.04)
        + soil * 0.16
    ) * np.asarray((0.52, 0.37, 0.25), dtype=np.float32)

    truth = table["maskTruth"]
    # Each restoration wing carries a different surviving ink density. The
    # warning shelf is intentionally quieter, aged parchment—not clean white.
    wing_tints = (
        np.asarray((0.22, 0.16, 0.10), dtype=np.float32),
        np.asarray((0.28, 0.20, 0.11), dtype=np.float32),
        np.asarray((0.36, 0.27, 0.15), dtype=np.float32),
    )
    for zone, tint in zip(truth["archiveWingZones"], wing_tints):
        weight = rectangle_mask(x, z, zone, 2.0)
        hatch = np.clip(0.63 + np.sin(x * 0.63 + z * 0.31 + zone["order"]) * 0.20, 0.28, 0.92)
        weight *= hatch
        archive_tone = ink * tint[None, None, :] + plate * 0.10
        atlas = atlas * (1.0 - weight[..., None] * 0.54) + archive_tone * weight[..., None] * 0.54

    cut = np.exp(-((x / 4.0) ** 4)) * smoothstep(-34.0, -28.0, z) * (1.0 - smoothstep(19.0, 25.0, z))
    uninked = soil * np.asarray((0.58, 0.48, 0.34), dtype=np.float32)
    atlas = atlas * (1.0 - cut[..., None] * 0.62) + uninked * cut[..., None] * 0.62
    empty = rectangle_mask(x, z, truth["emptyShelfZone"], 0.9)
    atlas *= 1.0 - empty[..., None] * 0.48
    # Scattered erased flecks and dragged page scars keep the surface brutal,
    # worked, and old without baking any runtime Static state into the asset.
    scars = np.zeros_like(x)
    for index in range(23):
        cx = -56.0 + (index * 37 % 113)
        cz = -54.0 + (index * 53 % 109)
        scars = np.maximum(scars, gaussian(x, z, cx, cz, 0.7 + index % 3, 0.5 + (index + 1) % 3))
    atlas *= 1.0 - scars[..., None] * 0.24
    edge = smoothstep(0.90, 1.0, np.maximum(np.abs(x), np.abs(z)) / 64.0)[..., None]
    atlas = atlas * (1.0 - edge * 0.70) + shale * np.asarray((0.20, 0.16, 0.13), dtype=np.float32) * edge * 0.70
    atlas = claim.apply_grit_grade(atlas, worlds, u, v, "archive-world")

    rgba = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    rgba[:, :, :3] = np.clip(atlas, 0.003, 0.66)
    path = OUT / "archive-world-terrain-atlas.png"
    image = bpy.data.images.new(PROFILE["atlas"], ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image, path


def zone_outline(zone, height_at, lift=0.86):
    corners = ((zone["minX"], zone["minZ"]), (zone["maxX"], zone["minZ"]), (zone["maxX"], zone["maxZ"]), (zone["minX"], zone["maxZ"]), (zone["minX"], zone["minZ"]))
    points = []
    for start, end in zip(corners, corners[1:]):
        for amount in np.linspace(0.0, 1.0, 14, endpoint=False):
            x = start[0] + (end[0] - start[0]) * amount
            z = start[1] + (end[1] - start[1]) * amount
            points.append((x, z, float(height_at(x, z)) + lift))
    points.append(points[0])
    return points


def add_preview(table, height_at, materials):
    objects = []
    for mount_id, x, z, yaw, scale in MOUNTS:
        h = float(height_at(x, z))
        objects.append(claim.add_box_game(f"RenderHelper.Mount.{mount_id}", x, z, h, (1.4 * scale, 1.4 * scale, 0.20), materials["brass"], yaw=yaw, bevel=0.04))
    for marker in table["maskTruth"]["stakeMarkers"]:
        h = float(height_at(marker["x"], marker["z"]))
        objects.append(claim.add_cylinder_between(f"RenderHelper.Light.{marker['id']}", (marker["x"], marker["z"], h), (marker["x"], marker["z"], h + 4.0), 0.18, materials["brass"]))
        objects.append(claim.add_box_game(f"RenderHelper.Glow.{marker['id']}", marker["x"], marker["z"], h + 4.0, (0.7, 0.7, 0.7), materials["warm"], bevel=0.12))
    # Larger verdict-only ruins show what the empty mount records are composed
    # to receive. They never enter the terrain blend or GLB.
    ruins = (
        ("Entry", 0.0, -46.0, 16.0, 4.0, 5.2),
        ("WestStacks", -28.0, -6.0, 11.0, 8.0, 6.8),
        ("EastStacks", 28.0, -6.0, 11.0, 8.0, 7.6),
        ("WarningShelf", -14.0, 40.0, 13.0, 6.0, 8.2),
    )
    for name, x, z, width, depth, height in ruins:
        ground = float(height_at(x, z))
        for index, (dx, dz, scale) in enumerate(((-0.48, -0.46, 1.0), (0.48, -0.46, 0.72), (-0.48, 0.46, 0.84), (0.48, 0.46, 0.54))):
            objects.append(claim.add_box_game(
                f"RenderHelper.ArchiveRuin.{name}.Pier.{index}",
                x + dx * width,
                z + dz * depth,
                ground,
                (0.52, 0.52, height * scale),
                materials["archive"],
                yaw=(index - 1.5) * 0.025,
                bevel=0.06,
            ))
        objects.append(claim.add_box_game(f"RenderHelper.ArchiveRuin.{name}.LintelA", x, z - depth * 0.46, ground + height * 0.76, (width, 0.46, 0.48), materials["brass"], yaw=0.018, bevel=0.05))
        objects.append(claim.add_box_game(f"RenderHelper.ArchiveRuin.{name}.LintelB", x - width * 0.48, z, ground + height * 0.54, (0.44, depth, 0.44), materials["brass"], yaw=-0.022, bevel=0.05))
        objects.append(claim.add_box_game(f"RenderHelper.ArchiveRuin.{name}.BackSlab", x, z + depth * 0.34, ground, (width * 0.72, 0.66, height * 0.46), materials["archive"], yaw=-0.014, bevel=0.06))
        for shelf_index, shelf_y in enumerate((0.62, 1.64, 2.66)):
            shelf_width = width * (0.62 if shelf_index < 2 else 0.34)
            shelf_x = x if shelf_index < 2 else x + width * 0.15
            objects.append(claim.add_box_game(f"RenderHelper.ArchiveRuin.{name}.Shelf.{shelf_index}", shelf_x, z + depth * 0.30, ground + shelf_y, (shelf_width, 0.72, 0.22), materials["brass"], yaw=(shelf_index - 1) * 0.012, bevel=0.035))
    marker_ground = float(height_at(0.0, 46.0))
    objects.append(claim.add_box_game("RenderHelper.ArchiveRuin.OursUnless.Left", -1.45, 46.0, marker_ground, (1.2, 0.9, 3.4), materials["archive"], yaw=-0.04, bevel=0.08))
    objects.append(claim.add_box_game("RenderHelper.ArchiveRuin.OursUnless.Right", 1.45, 46.0, marker_ground, (1.2, 0.9, 2.5), materials["archive"], yaw=0.06, bevel=0.08))
    objects.append(claim.add_box_game("RenderHelper.ArchiveRuin.OursUnless.Mark", 0.0, 45.4, marker_ground + 2.1, (0.72, 0.44, 0.72), materials["warm"], bevel=0.12))
    rng = np.random.default_rng(2110)
    placed = 0
    for _ in range(260):
        if placed >= 58:
            break
        x, z = float(rng.uniform(-61, 61)), float(rng.uniform(-61, 61))
        if any(zone["minX"] - 2 <= x <= zone["maxX"] + 2 and zone["minZ"] - 2 <= z <= zone["maxZ"] + 2 for zone in table["maskTruth"]["buildZones"]):
            continue
        h = float(height_at(x, z))
        if max(abs(float(height_at(x + dx, z + dz)) - h) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))) > 0.55:
            continue
        size = float(rng.uniform(0.35, 1.15))
        objects.append(claim.add_rock(f"RenderHelper.ArchiveRubble.{placed:02d}", x, z, (size, size * 0.7, size * 0.55), materials["stone"], float(rng.uniform(-math.pi, math.pi))))
        placed += 1
    return objects


def add_overlay(table, height_at, materials):
    objects = [claim.add_curve(f"RenderHelper.Mask.Build.{zone['id']}", zone_outline(zone, height_at), 0.18, materials["mask"]) for zone in table["maskTruth"]["buildZones"]]
    objects.append(claim.add_curve("RenderHelper.Mask.EmptyShelf", zone_outline(table["maskTruth"]["emptyShelfZone"], height_at, 1.08), 0.14, materials["danger"]))
    return objects


def add_lighting(table, height_at):
    lights = claim.add_lighting(sunset=True)
    world = bpy.context.scene.world.node_tree.nodes.get("Background")
    world.inputs["Color"].default_value = (0.009, 0.007, 0.012, 1.0)
    world.inputs["Strength"].default_value = 0.52
    fill_data = bpy.data.lights.new("ArchiveReadableFill", "AREA")
    fill_data.energy = 980
    fill_data.color = (0.31, 0.39, 0.50)
    fill_data.shape = "DISK"
    fill_data.size = 54.0
    fill = bpy.data.objects.new("ArchiveReadableFill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = (8.0, 2.0, 42.0)
    claim.aim_at(fill, (0.0, 0.0, 0.0))
    lights.append(fill)
    for index, marker in enumerate(table["maskTruth"]["stakeMarkers"]):
        data = bpy.data.lights.new(f"ArchiveWarm.{index}", "POINT")
        data.energy = 520
        data.color = (1.0, 0.38, 0.075)
        data.shadow_soft_size = 2.8
        obj = bpy.data.objects.new(f"ArchiveWarm.{index}", data)
        bpy.context.collection.objects.link(obj)
        obj.location = (marker["x"], -marker["z"], float(height_at(marker["x"], marker["z"])) + 3.5)
        lights.append(obj)
    return lights


def render_verdicts(table, terrain, panorama, preview, overlay, height_at):
    backdrop = claim.make_backdrop()
    backdrop.location.z = -2.7
    nodes = backdrop.active_material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBackground")
    shader.inputs["Color"].default_value = (0.009, 0.006, 0.005, 1.0)
    shader.inputs["Strength"].default_value = 1.0
    backdrop.active_material.node_tree.links.new(shader.outputs[0], output.inputs[0])
    panorama.hide_render = True
    cameras = {
        "run": claim.add_camera("ArchiveWorldRun", (0.0, 42.0, 31.0), (0.0, -4.0, 0.7), 43.0),
        "composition": claim.add_camera("ArchiveWorldComposition", (0.0, 69.0, 49.0), (0.0, -3.0, 0.7), 49.0),
        "overview": claim.add_camera("ArchiveWorldOverview", (0.0, 103.0, 109.0), (0.0, 0.0, 0.8), 47.0),
        "low": claim.add_camera("ArchiveWorldLow", (-56.0, 69.0, 21.0), (0.0, -3.0, 1.0), 52.0),
        "top": claim.add_camera("ArchiveWorldMask", (0.0, 0.0, 156.0), (0.0, 0.0, 0.0), 52.0),
        "horizon": claim.add_camera("ArchiveWorldHorizon", (0.0, 0.0, 5.0), (132.0, -126.0, 9.0), 53.0),
    }
    for camera in cameras.values():
        camera.data.clip_end = 440.0
    lights = add_lighting(table, height_at)
    bpy.context.scene.view_settings.exposure = 1.34
    for obj in preview + overlay:
        obj.hide_render = True
    saved = [vertex.co.z for vertex in terrain.data.vertices]
    for vertex in terrain.data.vertices:
        vertex.co.z = 0.0
    terrain.data.update()
    claim.render(cameras["composition"], ARTIFACTS / "archive-world-flat-tile-identical-camera.png")
    for vertex, value in zip(terrain.data.vertices, saved):
        vertex.co.z = value
    terrain.data.update()
    claim.render(cameras["composition"], ARTIFACTS / "archive-world-sculpted-tile-identical-camera.png")
    for obj in preview:
        obj.hide_render = False
    claim.render(cameras["low"], ARTIFACTS / "archive-world-panorama-before.png")
    for obj in overlay:
        obj.hide_render = False
    claim.render(cameras["top"], ARTIFACTS / "archive-world-mask-agreement.png")
    for obj in overlay:
        obj.hide_render = True
    backdrop.hide_render = True
    panorama.hide_render = False
    claim.render(cameras["run"], ARTIFACTS / "archive-world-run-camera.png")
    claim.render(cameras["composition"], ARTIFACTS / "archive-world-composition.png")
    claim.render(cameras["overview"], ARTIFACTS / "archive-world-overview.png")
    claim.render(cameras["low"], ARTIFACTS / "archive-world-low-sunset.png")
    claim.render(cameras["low"], ARTIFACTS / "archive-world-panorama-mounted.png")
    for obj in preview:
        obj.hide_render = True
    claim.render(cameras["horizon"], ARTIFACTS / "archive-world-panorama-horizon.png")
    bpy.context.scene.view_settings.exposure = 0.0
    claim.remove_objects(lights + list(cameras.values()) + [backdrop, panorama])


def build_zone_flatness(table, height_at):
    return [
        {
            "id": zone["id"],
            "bounds": [zone["minX"], zone["maxX"], zone["minZ"], zone["maxZ"]],
            "sampledSurfacePoints": 2145,
            "maxDeviationMeters": round(max(samples) - min(samples), 6),
        }
        for zone in table["maskTruth"]["buildZones"]
        for samples in [[float(height_at(x, z)) for x in np.linspace(zone["minX"], zone["maxX"], 65) for z in np.linspace(zone["minZ"], zone["maxZ"], 33)]]
    ]


def landmark_mounts(height_at):
    return [
        {
            "id": mount_id,
            "asset": "",
            "position": [x, round(float(height_at(x, z)), 4), z],
            "rotation": [0.0, round(yaw, 4), 0.0],
            "scale": [scale, scale, scale],
        }
        for mount_id, x, z, yaw, scale in MOUNTS
    ]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_asset(table, terrain, atlas_path, height_at):
    blend = OUT / "archive-world-terrain.blend"
    glb = OUT / "archive-world-terrain.glb"
    contract_path = OUT / "archive-world-terrain-contract.json"
    triangles = sum(len(poly.vertices) - 2 for poly in terrain.data.polygons)
    mounts = landmark_mounts(height_at)
    terrain["landmarks_frozen"] = False
    terrain["landmark_mount_ids"] = json.dumps([mount["id"] for mount in mounts])
    terrain["runtime_owned_visuals_absent"] = True
    bpy.ops.object.select_all(action="DESELECT")
    terrain.select_set(True)
    bpy.context.view_layer.objects.active = terrain
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", use_selection=True, export_apply=True, export_cameras=False, export_lights=False, export_animations=False, export_extras=True)
    coords = np.asarray([vertex.co[:] for vertex in terrain.data.vertices], dtype=np.float32)
    flatness = build_zone_flatness(table, height_at)
    contract = {
        "asset": glb.name,
        "contractId": "e10-archive-world",
        "tileId": "e10-archive-world",
        "renderOnly": True,
        "simulation": "planar; movement, collision, placement, spawns, persistence, Static squalls, re-ink progression, and lore unlocks remain code-owned",
        "heightSocket": "Terrain.visualY",
        "theme": PROFILE["theme"],
        "regionalFamily": {
            "epoch": "Epoch 10 Deep Sky archive world",
            "shared": ["deep-ink basalt", "parchment-gold memory light", "teal salvage glass", "engraved star stipple", "aged un-inked paper", "preserve-contract warmth"],
            "unique": "four integrated archive terraces divided by a broken central memory cut and an empty warning shelf",
        },
        "boundsMeters": {"min": [round(float(v), 4) for v in coords.min(axis=0)], "max": [round(float(v), 4) for v in coords.max(axis=0)]},
        "meshCount": 1,
        "primitiveCount": 1,
        "materialCount": 1,
        "vertices": len(terrain.data.vertices),
        "triangles": triangles,
        "triangleBudget": 60000,
        "texture": {"count": 1, "width": ATLAS_SIZE, "height": ATLAS_SIZE, "embedded": True},
        "maskTable": str(TABLE_PATH.relative_to(ROOT)),
        "maskTruth": table["maskTruth"],
        "waterAgreement": table["waterAgreement"],
        "buildZoneFlatness": flatness,
        "landmarkMounts": mounts,
        "landmarkMountSpace": claim.landmark_mount_space(),
        "panoramaMount": claim.panorama_mount("archive-world"),
        "runtimeVisualsAbsent": ["Static squalls", "staged re-ink state", "lore-page unlocks", "spawn gates", "light-hold progression"],
        "verdictPreviewOnly": {"excludedFromBlendAndGlb": True, "reason": "light posts, rubble, mount proxies, mask overlays, panorama, and evidence lighting are review helpers only"},
        "variantDecisions": [
            {"contractId": "e10-last-claim", "tileId": "ark-plaza-e10", "terrainMesh": "off", "decision": "reuse Ark deck; no sculpt"},
            {"contractId": "e10-river", "tileId": "frontier-river-claim", "terrainMesh": "off", "decision": "reuse The Claim at dawn; no sculpt"},
        ],
        "sourceArt": [str(path.relative_to(ROOT)) for path in (KIT, WORLDS, claim.BANK_A, claim.BANK_C)],
        "atlas": atlas_path.name,
    }
    if triangles != 32768 or any(zone["maxDeviationMeters"] > 0.001 for zone in flatness):
        raise AssertionError("Archive World geometry or build-zone flatness failed")
    contract["files"] = {
        "blend": {"bytes": blend.stat().st_size, "sha256": sha256(blend)},
        "glb": {"bytes": glb.stat().st_size, "sha256": sha256(glb)},
        "atlas": {"bytes": atlas_path.stat().st_size, "sha256": sha256(atlas_path)},
    }
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    return contract


def main():
    _factory, table = documents()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    claim.reset_scene()
    atlas, atlas_path = make_atlas(table)
    material = claim.make_material(atlas)
    material.name = PROFILE["material"]
    height_at = height_function(table)
    claim.terrain_height = height_at
    terrain = base.make_terrain(PROFILE, table, TABLE_PATH, height_at, material)
    panorama_objects = claim.link_panorama("archive-world")
    if len(panorama_objects) != 1:
        raise AssertionError("expected one separate Archive World Panorama v2 object")
    materials = base.preview_materials("archive-world")
    materials["archive"] = claim.make_render_material("ArchiveRuinedStone", (0.115, 0.072, 0.035), 0.76, 0.12)
    preview = add_preview(table, height_at, materials)
    overlay = add_overlay(table, height_at, materials)
    render_verdicts(table, terrain, panorama_objects[0], preview, overlay, height_at)
    claim.remove_objects(preview + overlay)
    bpy.context.scene.world = None
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    contract = export_asset(table, terrain, atlas_path, height_at)
    print(json.dumps({"asset": contract["asset"], "triangles": contract["triangles"], "buildZoneFlatness": contract["buildZoneFlatness"]}, indent=2))


if __name__ == "__main__":
    main()
