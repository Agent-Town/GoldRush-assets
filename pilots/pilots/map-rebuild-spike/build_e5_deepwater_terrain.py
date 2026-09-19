"""Build the render-only Deepwater Claim sea-floor terrain.

The exported mesh is only the submerged shelf, reefs, bars, and trench.  The
runtime owns the sea surface, water classification, Claim-Boat, movement,
spawns, and placement.  Verdict-only sea, boat, wreck, and mask helpers are
removed before the .blend is saved and the GLB is exported.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

import bpy
import mathutils
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"
FACTORY = ROOT / "assets/contracts/epoch-5-deepwater/contracts.json"
TABLE = ROOT / "assets/contracts/epoch-5-deepwater/mask-tables/e5-deepwater-claim.json"
KIT = ROOT / "assets/processed/kit-era-5.png"
SHELF_ATLAS = ROOT / "assets/raw/ter-shelf-atlas.png"
WRECK_PLATE = ROOT / "assets/raw/prop-wrecks.png"
CLAIM_BOAT_PLATE = ROOT / "assets/raw/plate-e5-bld-claimboat.png"
E4_TOWN_MOUNTS = (
    {
        "id": "drowned-claim-office",
        "asset": "assets/pilots/claim-office-3d/claim-office.e4.glb",
        "position": [-32.0, -0.28, -24.0],
        "rotation": [0.62, -0.34, -0.22],
        "scale": [0.98, 0.98, 0.98],
    },
    {
        "id": "drowned-chapel",
        "asset": "assets/pilots/chapel-3d/chapel.e4.glb",
        "position": [-12.0, -0.22, -27.0],
        "rotation": [0.44, 0.26, 0.35],
        "scale": [0.78, 0.78, 0.78],
    },
    {
        "id": "drowned-general-store",
        "asset": "assets/pilots/general-store-3d/general-store.e4.glb",
        "position": [10.0, -0.25, -23.0],
        "rotation": [0.72, -0.18, -0.30],
        "scale": [1.02, 1.02, 1.02],
    },
    {
        "id": "drowned-stamp-mill",
        "asset": "assets/pilots/stamp-mill-3d/stamp-mill.e4.glb",
        "position": [31.0, -0.30, -28.0],
        "rotation": [0.50, 0.31, 0.42],
        "scale": [0.92, 0.92, 0.92],
    },
)
SEGMENTS = 128
ATLAS_SIZE = 2048
WIDTH = 128.0
HEIGHT = 128.0
KEY = "deepwater-claim"
CONTRACT_ID = "e5-deepwater-claim"
STEM = "deepwater-claim-terrain"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


e3 = load_module("e5_e3_helpers", OUT / "build_e3_contract_terrains.py")
claim = e3.claim
claim.mathutils = mathutils
claim.CONTRACT_PLATES[KEY] = SHELF_ATLAS
claim.GRIT_PROFILES[KEY] = {
    "black": 0.006,
    "white": 0.42,
    "gamma": 1.21,
    "ink": 0.46,
    "palette": 0.16,
    "saturation": 0.56,
}

PROFILE = {
    "contractId": CONTRACT_ID,
    "stem": STEM,
    "object": "DeepwaterClaimTerrain",
    "mesh": "DeepwaterClaimTerrainMesh",
    "material": "DeepwaterClaimPaintedShelfMaterial",
    "atlas": "DeepwaterClaimPaintedShelfAtlas",
    "width": WIDTH,
    "height": HEIGHT,
    "theme": "post-flood working harbor claim over a broken shelf reef, five drowned-era wreck beds, and a sealed trench edge",
    "epoch": "Epoch 5 post-flood harbor chain",
    "shared": [
        "blue-green parchment depth",
        "tar-dark working water shadows",
        "rope-trim harbor timber",
        "brass salvage scars",
        "quiet tea-coloured weather horizon",
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


def documents():
    factory = json.loads(FACTORY.read_text(encoding="utf-8"))
    matches = [entry for entry in factory["contracts"] if entry["id"] == CONTRACT_ID]
    if len(matches) != 1:
        raise ValueError(f"expected one factory contract for {CONTRACT_ID}")
    table = json.loads(TABLE.read_text(encoding="utf-8"))
    if table["maskTruth"]["tileId"] != CONTRACT_ID:
        raise ValueError("Deepwater mask table tile id changed")
    return matches[0], table


def region(table, identifier):
    matches = [item for item in table["maskTruth"]["deepwater"]["waterTile"]["regions"] if item["id"] == identifier]
    if len(matches) != 1:
        raise ValueError(f"expected one Deepwater region named {identifier}")
    return matches[0]


def height_function(table):
    lagoon = region(table, "lagoon-shallows")
    reef = region(table, "reef-ring")
    gap = region(table, "reef-gap")
    shelf = region(table, "wreck-shelf")
    trench = region(table, "trench-edge")
    wrecks = table["maskTruth"]["deepwater"]["wrecks"]

    def height(x, z):
        xx = np.asarray(x, dtype=np.float32)
        zz = np.asarray(z, dtype=np.float32)
        grain = np.sin(xx * 0.18 + zz * 0.11) * 0.075 + np.sin(xx * 0.43 - zz * 0.27) * 0.035
        floor = -3.05 + grain
        floor += gaussian(xx, zz, -48.0, 28.0, 14.0, 10.0) * 0.34
        floor += gaussian(xx, zz, 52.0, 15.0, 12.0, 17.0) * 0.27
        floor -= gaussian(xx, zz, 38.0, -4.0, 10.0, 20.0) * 0.22

        lagoon_warp_z = zz + np.sin(xx * 0.17) * 1.8 + np.sin(xx * 0.41 + 0.7) * 0.55
        lagoon_mask = rectangle_mask(xx, lagoon_warp_z, lagoon, 2.8)
        lagoon_bars = np.maximum.reduce([
            gaussian(xx, zz, -31.0, 27.5, 10.0, 4.2),
            gaussian(xx, zz, -14.0, 35.0, 8.5, 4.7),
            gaussian(xx, zz, 4.0, 29.5, 11.0, 5.0),
            gaussian(xx, zz, 27.0, 26.5, 9.0, 4.0),
        ])
        lagoon_scours = gaussian(xx, zz, -21.0, 22.0, 7.0, 3.2) + gaussian(xx, zz, 20.0, 37.0, 8.0, 3.0)
        lagoon_floor = -1.72 + lagoon_bars * 1.12 - lagoon_scours * 0.24
        lagoon_floor += np.sin(xx * 0.11 - zz * 0.07) * 0.065
        floor = floor * (1.0 - lagoon_mask) + lagoon_floor * lagoon_mask

        reef_mask = rectangle_mask(xx, zz, reef, 1.25)
        reef_masses = np.maximum.reduce([
            gaussian(xx, zz, -42.0, -1.5, 6.8, 4.0),
            gaussian(xx, zz, -30.0, 2.0, 7.0, 4.6),
            gaussian(xx, zz, -18.0, -2.3, 6.2, 3.8),
            gaussian(xx, zz, -8.0, 1.1, 4.3, 3.1),
            gaussian(xx, zz, 8.5, -1.2, 4.2, 3.0),
            gaussian(xx, zz, 19.0, 2.4, 6.0, 3.9),
            gaussian(xx, zz, 31.5, -1.6, 7.2, 4.4),
            gaussian(xx, zz, 43.0, 1.2, 6.0, 3.7),
        ])
        reef_break = np.sin(xx * 0.31 + zz * 0.24) * 0.18 + np.sin(xx * 0.71 - zz * 0.33) * 0.085
        reef_notches = gaussian(xx, zz, -35.0, 4.8, 3.0, 2.4) + gaussian(xx, zz, 27.0, -4.8, 3.4, 2.2)
        # Sharper, broken coral crowns avoid the soft chain-of-pillows read.
        reef_crowns = np.power(np.clip(reef_masses, 0.0, 1.0), 1.62)
        reef_floor = -2.18 + reef_crowns * 1.92 - reef_notches * 0.44
        reef_floor += reef_break * (0.24 + reef_crowns * 1.08)
        floor = floor * (1.0 - reef_mask) + reef_floor * reef_mask

        # The mask-authored ten-metre passage remains open through the whole
        # reef band.  Its shoulders start outside x=+/-5, so the visual cut
        # agrees with the travel-class override instead of merely tinting it.
        gap_mask = rectangle_mask(xx, zz, gap, 0.70)
        gap_floor = -2.85 + np.sin(zz * 0.43) * 0.06
        floor = floor * (1.0 - gap_mask) + gap_floor * gap_mask

        shelf_warp_z = zz + np.sin(xx * 0.13 + 0.4) * 2.1 + np.sin(xx * 0.31) * 0.65
        shelf_mask = rectangle_mask(xx, shelf_warp_z, shelf, 2.4)
        shelf_floor = -4.32 + np.sin(xx * 0.16 + zz * 0.09) * 0.16
        shelf_floor += gaussian(xx, zz, -38.0, -25.0, 8.0, 5.0) * 0.92
        shelf_floor += gaussian(xx, zz, -14.0, -34.0, 10.0, 5.4) * 0.74
        shelf_floor += gaussian(xx, zz, 12.0, -24.0, 8.0, 4.7) * 0.86
        shelf_floor += gaussian(xx, zz, 37.0, -33.0, 9.0, 5.0) * 0.78
        shelf_floor -= gaussian(xx, zz, 1.0, -37.0, 7.0, 3.2) * 0.45
        floor = floor * (1.0 - shelf_mask) + shelf_floor * shelf_mask
        shelf_lip = np.exp(-(((zz + 14.0) / 1.55) ** 2)) * (1.0 - smoothstep(47.0, 51.0, np.abs(xx)))
        floor += shelf_lip * 0.56

        # Drowned machinery is mounted later.  The terrain records only the
        # worked depressions and silt wakes around the published anchors.
        for index, wreck in enumerate(wrecks):
            wake = gaussian(xx, zz, wreck["x"] + 1.8, wreck["z"] - 0.8, 5.5 + index * 0.35, 2.4)
            floor -= wake * (0.18 + index * 0.018)

        # The reused E4 buildings are heavy drowned ruins, not water-column
        # props. Local foundation hollows put their full-size bodies on the
        # sea floor while their small mount offsets only bite into the silt.
        for mount in E4_TOWN_MOUNTS:
            mount_x, _mount_y, mount_z = mount["position"]
            floor -= gaussian(xx, zz, mount_x, mount_z, 4.8, 3.9) * 2.08

        trench_warp_z = zz + np.sin(xx * 0.12 + 0.8) * 1.35 + np.sin(xx * 0.29) * 0.42
        trench_mask = rectangle_mask(xx, trench_warp_z, trench, 2.2)
        trench_floor = -7.92 + np.sin(xx * 0.12) * 0.12
        floor = floor * (1.0 - trench_mask) + trench_floor * trench_mask
        trench_lip = np.exp(-(((zz + 49.2) / 1.35) ** 2)) * 0.54
        floor += trench_lip

        # Never create a second sea surface. Even the highest exposed bars
        # stay visibly below runtime water truth.
        return np.clip(floor, -8.15, -0.34)

    return height


def make_atlas(table):
    shelf_source = claim.image_pixels(SHELF_ATLAS)
    half_y, half_x = shelf_source.shape[0] // 2, shelf_source.shape[1] // 2
    kelp = shelf_source[:half_y, :half_x]
    deck = shelf_source[:half_y, half_x:]
    reef_art = shelf_source[half_y:, :half_x]
    sand = shelf_source[half_y:, half_x:]
    kit = claim.image_pixels(KIT)
    wreck_plate = claim.image_pixels(WRECK_PLATE)
    magenta = (wreck_plate[..., 0] > 0.80) & (wreck_plate[..., 1] < 0.22) & (wreck_plate[..., 2] > 0.80)
    wreck_pixels = wreck_plate[~magenta]
    wreck_tone = np.median(wreck_pixels, axis=0) if wreck_pixels.size else np.array((0.28, 0.19, 0.09))

    axis = np.linspace(0.0, 1.0, ATLAS_SIZE, dtype=np.float32)
    u, v = np.meshgrid(axis, axis)
    x = (u - 0.5) * WIDTH
    z = (v - 0.5) * HEIGHT
    lagoon = region(table, "lagoon-shallows")
    reef = region(table, "reef-ring")
    gap = region(table, "reef-gap")
    shelf = region(table, "wreck-shelf")
    trench = region(table, "trench-edge")

    warp_u = u + np.sin(v * math.tau * 2.7 + 0.4) * 0.014 + np.sin(v * math.tau * 7.1) * 0.004
    warp_v = v + np.sin(u * math.tau * 3.3 - 0.6) * 0.012 + np.sin(u * math.tau * 8.7) * 0.003
    kelp_sample = claim.tiled_sample(kelp, warp_u, warp_v, 3.7, 0.18, 0.61) * 0.62
    kelp_sample += claim.tiled_sample(kelp, warp_u, warp_v, 6.15, 0.47, 0.19) * 0.38
    sand_sample = claim.tiled_sample(sand, warp_u, warp_v, 3.35, 0.63, 0.12) * 0.66
    sand_sample += claim.tiled_sample(sand, warp_u, warp_v, 5.8, 0.21, 0.53) * 0.34
    reef_sample = claim.tiled_sample(reef_art, warp_u, warp_v, 3.15, 0.31, 0.46) * 0.58
    reef_sample += claim.tiled_sample(reef_art, warp_u, warp_v, 5.45, 0.72, 0.08) * 0.42
    deck_sample = claim.tiled_sample(deck, warp_u, warp_v, 4.2, 0.08, 0.28) * 0.64
    deck_sample += claim.tiled_sample(deck, warp_u, warp_v, 7.1, 0.39, 0.66) * 0.36
    kit_sample = claim.tiled_sample(kit, u, v, 4.2, 0.39, 0.17)
    macro = (np.sin(x * 0.075 + z * 0.052) * 0.5 + 0.5)[..., None]
    atlas = kelp_sample * (0.43 + macro * 0.08) + sand_sample * (0.34 - macro * 0.06) + kit_sample * 0.15 + reef_sample * 0.08
    atlas *= np.array((0.52, 0.69, 0.70), dtype=np.float32)

    lagoon_warp_z = z + np.sin(x * 0.17) * 1.8 + np.sin(x * 0.41 + 0.7) * 0.55
    lagoon_mask = rectangle_mask(x, lagoon_warp_z, lagoon, 2.8)
    lagoon_bars = np.maximum.reduce([
        gaussian(x, z, -28.0, 29.0, 12.0, 5.2),
        gaussian(x, z, -2.0, 34.0, 17.0, 6.4),
        gaussian(x, z, 27.0, 27.0, 11.0, 5.4),
    ])
    lagoon_color = sand_sample * np.array((0.83, 0.78, 0.58), dtype=np.float32) + kelp_sample * 0.16
    lagoon_paint = lagoon_mask * (0.36 + lagoon_bars * 0.64)
    atlas = atlas * (1.0 - lagoon_paint[..., None]) + lagoon_color * lagoon_paint[..., None]

    reef_mask = rectangle_mask(x, z, reef, 1.2)
    reef_masses = np.maximum.reduce([
        gaussian(x, z, -40.0, -0.8, 8.5, 5.0),
        gaussian(x, z, -24.0, 1.1, 9.0, 5.8),
        gaussian(x, z, -9.0, -1.6, 7.0, 4.7),
        gaussian(x, z, 10.0, 1.6, 7.0, 4.7),
        gaussian(x, z, 25.0, -0.7, 9.5, 5.7),
        gaussian(x, z, 41.0, 1.0, 8.0, 4.9),
    ])
    reef_color = reef_sample * np.array((0.76, 0.82, 0.60), dtype=np.float32) + kelp_sample * 0.16
    reef_paint = reef_mask * (0.26 + reef_masses * 0.74)
    atlas = atlas * (1.0 - reef_paint[..., None]) + reef_color * reef_paint[..., None]
    gap_mask = rectangle_mask(x, z, gap, 0.62)
    gap_color = kelp_sample * np.array((0.40, 0.61, 0.66), dtype=np.float32)
    atlas = atlas * (1.0 - gap_mask[..., None] * 0.76) + gap_color * gap_mask[..., None] * 0.76

    shelf_warp_z = z + np.sin(x * 0.13 + 0.4) * 2.1 + np.sin(x * 0.31) * 0.65
    shelf_mask = rectangle_mask(x, shelf_warp_z, shelf, 2.4)
    shelf_patches = np.clip(gaussian(x, z, -33.0, -27.0, 15.0, 9.0) + gaussian(x, z, 25.0, -31.0, 19.0, 8.0), 0.0, 1.0)
    shelf_color = kelp_sample * np.array((0.38, 0.53, 0.52), dtype=np.float32) + sand_sample * 0.12
    shelf_paint = shelf_mask * (0.54 + shelf_patches * 0.38)
    atlas = atlas * (1.0 - shelf_paint[..., None]) + shelf_color * shelf_paint[..., None]
    for index, wreck in enumerate(table["maskTruth"]["deepwater"]["wrecks"]):
        stain = gaussian(x, z, wreck["x"], wreck["z"], 5.3 + index * 0.35, 3.1)
        tone = wreck_tone * np.array((0.62, 0.66, 0.62), dtype=np.float32)
        atlas = atlas * (1.0 - stain[..., None] * 0.38) + tone[None, None, :] * stain[..., None] * 0.38
        drag = gaussian(x, z, wreck["x"] + 4.0, wreck["z"] - 1.0, 7.5, 1.1)
        atlas *= 1.0 - drag[..., None] * 0.16

    trench_mask = rectangle_mask(x, z, trench, 1.2)
    trench_color = kelp_sample * np.array((0.12, 0.24, 0.26), dtype=np.float32)
    atlas = atlas * (1.0 - trench_mask[..., None]) + trench_color * trench_mask[..., None]

    # The Claim-Boat remains a separate runtime body. This only adds the
    # anchor-chain shadow on the lagoon floor, not deck planking to terrain.
    anchor = table["maskTruth"]["deepwater"]["claimBoat"]["anchors"][0]
    anchor_shadow = gaussian(x, z, anchor["x"], anchor["z"], 5.2, 4.0)
    rope_ink = deck_sample * np.array((0.19, 0.18, 0.14), dtype=np.float32)
    atlas = atlas * (1.0 - anchor_shadow[..., None] * 0.12) + rope_ink * anchor_shadow[..., None] * 0.12

    atlas = claim.apply_grit_grade(atlas, shelf_source, u, v, KEY)
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


def sea_material():
    material = bpy.data.materials.new("RenderHelperCodeOwnedSeaMaterial")
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (0.012, 0.145, 0.18, 1.0)
    shader.inputs["Roughness"].default_value = 0.72
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Alpha"].default_value = 0.22
    if "Transmission Weight" in shader.inputs:
        shader.inputs["Transmission Weight"].default_value = 0.02
    layer_weight = material.node_tree.nodes.new("ShaderNodeLayerWeight")
    layer_weight.inputs["Blend"].default_value = 0.34
    multiply = material.node_tree.nodes.new("ShaderNodeMath")
    multiply.operation = "MULTIPLY"
    multiply.inputs[1].default_value = -0.64
    add = material.node_tree.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    add.inputs[1].default_value = 0.90
    add.use_clamp = True
    material.node_tree.links.new(layer_weight.outputs["Facing"], multiply.inputs[0])
    material.node_tree.links.new(multiply.outputs[0], add.inputs[0])
    material.node_tree.links.new(add.outputs[0], shader.inputs["Alpha"])
    noise = material.node_tree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.16
    noise.inputs["Detail"].default_value = 3.0
    noise.inputs["Roughness"].default_value = 0.58
    bump = material.node_tree.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.16
    bump.inputs["Distance"].default_value = 0.12
    material.node_tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    material.node_tree.links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    try:
        material.surface_render_method = "DITHERED"
    except Exception:
        pass
    return material


def make_sea_proxy(material):
    segments = 128
    rings = 32
    # A round evidence surface ends beneath the 190 m sky cylinder. The old
    # square plane extended behind it and produced stacked ruler-straight bands.
    radius = 189.4
    vertices = [(0.0, 0.0, 0.04)]
    faces = []
    for ring in range(1, rings + 1):
        distance = radius * ring / rings
        for index in range(segments):
            angle = index / segments * math.tau
            x = math.cos(angle) * distance
            game_z = math.sin(angle) * distance
            swell = 0.07 * math.sin(x * 0.105 + game_z * 0.052) + 0.035 * math.sin(x * 0.033 - game_z * 0.17)
            vertices.append((x, -game_z, 0.04 + swell))
    for index in range(segments):
        faces.append((0, 1 + (index + 1) % segments, 1 + index))
    for ring in range(1, rings):
        inner = 1 + (ring - 1) * segments
        outer = 1 + ring * segments
        for index in range(segments):
            next_index = (index + 1) % segments
            faces.extend(((inner + index, outer + next_index, inner + next_index), (inner + index, outer + index, outer + next_index)))
    mesh = bpy.data.meshes.new("RenderHelperCodeOwnedSeaMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("RenderHelperCodeOwnedSea", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(material)
    obj["verdict_only"] = True
    obj["runtime_owner"] = "DeepwaterClaimTile water surface and weather swell"
    obj.visible_shadow = False
    return obj


def helper_materials():
    return {
        "reef": claim.make_render_material("DeepwaterMaskReef", (0.08, 0.78, 0.70), 0.65, 0.02),
        "shelf": claim.make_render_material("DeepwaterMaskShelf", (0.88, 0.26, 0.07), 0.62, 0.02),
        "trench": claim.make_render_material("DeepwaterMaskTrench", (0.34, 0.12, 0.52), 0.70, 0.02),
        "deck": claim.make_render_material("DeepwaterProxyDeck", (0.28, 0.16, 0.06), 0.91, 0.00),
        "hull": claim.make_render_material("DeepwaterProxyTarredHull", (0.045, 0.050, 0.044), 0.92, 0.00),
        "brass": claim.make_render_material("DeepwaterProxyBrass", (0.42, 0.23, 0.055), 0.78, 0.02),
        "teal": claim.make_render_material("DeepwaterProxyTeal", (0.045, 0.42, 0.43), 0.74, 0.04),
        "wreck": claim.make_render_material("DeepwaterProxyWreck", (0.23, 0.115, 0.042), 0.92, 0.00),
    }


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
    zone = truth["buildZones"][0]
    objects.append(claim.add_curve(f"RenderHelperBuildZone.{zone['id']}", rectangle_points(zone, 0.86), 0.24, materials["reef"]))
    for identifier, material_key in (("lagoon-shallows", "reef"), ("reef-ring", "reef"), ("reef-gap", "deck"), ("wreck-shelf", "shelf"), ("trench-edge", "trench")):
        item = region(table, identifier)
        objects.append(claim.add_curve(f"RenderHelperRegion.{identifier}", rectangle_points(item, 0.64), 0.16, materials[material_key]))
    for wreck in truth["deepwater"]["wrecks"]:
        points = []
        for index in range(25):
            angle = index / 24 * math.tau
            points.append((wreck["x"] + math.cos(angle) * 2.1, wreck["z"] + math.sin(angle) * 2.1, 0.70))
        objects.append(claim.add_curve(f"RenderHelperWreckAnchor.{wreck['id']}", points, 0.16, materials["shelf"]))
    spawn = truth["enemyRoster"][0]["spawnGates"][0]
    objects.append(claim.add_box_game("RenderHelperWestSpawnGate", spawn["x"], spawn["z"], 0.18, (1.1, 4.0, 1.2), materials["trench"], bevel=0.04))
    return objects


def add_claim_boat_hull(name, x, game_z, material):
    """Tapered verdict hull; the actual Claim-Boat remains runtime-owned."""
    outline = ((-8.8, -4.0), (4.8, -4.7), (9.2, -2.4), (9.2, 2.4), (4.8, 4.7), (-8.8, 4.0))
    bottom, top = -1.18, -0.08
    vertices = [(x + lx, -(game_z + lz), bottom) for lx, lz in outline]
    vertices += [(x + lx, -(game_z + lz), top) for lx, lz in outline]
    count = len(outline)
    faces = [tuple(range(count - 1, -1, -1)), tuple(range(count, count * 2))]
    for index in range(count):
        next_index = (index + 1) % count
        faces.append((index, next_index, count + next_index, count + index))
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return claim.finish_helper(obj, material, 0.08)


def add_claim_boat_proxy(table, materials):
    anchor = table["maskTruth"]["deepwater"]["claimBoat"]["anchors"][0]
    x, z = anchor["x"], anchor["z"]
    objects = [
        add_claim_boat_hull("RenderHelperClaimBoat.Hull", x, z, materials["hull"]),
        claim.add_box_game("RenderHelperClaimBoat.Deck", x - 0.5, z, -0.08, (14.8, 7.7, 0.40), materials["deck"], bevel=0.10),
        claim.add_box_game("RenderHelperClaimBoat.Wheelhouse", x - 4.7, z + 1.4, 0.32, (4.0, 3.2, 2.45), materials["deck"], bevel=0.10),
        claim.add_box_game("RenderHelperClaimBoat.CraneBase", x + 3.1, z - 0.5, 0.52, (1.2, 1.2, 1.5), materials["brass"], bevel=0.06),
        claim.add_beam("RenderHelperClaimBoat.CraneMast", (x + 3.1, z - 0.5, 1.6), (x + 3.1, z - 0.5, 5.8), 0.30, materials["brass"]),
        claim.add_beam("RenderHelperClaimBoat.CraneJib", (x + 3.1, z - 0.5, 5.5), (x + 6.8, z - 2.2, 4.4), 0.25, materials["brass"]),
        claim.add_beam("RenderHelperClaimBoat.PortRail", (x - 7.0, z + 3.7, 0.60), (x + 5.5, z + 3.7, 0.60), 0.14, materials["brass"]),
        claim.add_beam("RenderHelperClaimBoat.StarboardRail", (x - 7.0, z - 3.7, 0.60), (x + 5.5, z - 3.7, 0.60), 0.14, materials["brass"]),
        claim.add_box_game("RenderHelperClaimBoat.CargoA", x - 1.0, z + 1.8, 0.32, (1.7, 1.3, 1.1), materials["wreck"], yaw=0.12, bevel=0.05),
        claim.add_box_game("RenderHelperClaimBoat.CargoB", x + 1.0, z + 2.0, 0.32, (1.2, 1.1, 0.8), materials["brass"], yaw=-0.18, bevel=0.05),
    ]
    for index, pad in enumerate(table["maskTruth"]["deepwater"]["claimBoat"]["pads"]):
        px, pz = x + pad["x"], z + pad["z"]
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.42, depth=0.22, location=(px, -pz, 0.66))
        marker = bpy.context.object
        marker.name = f"RenderHelperClaimBoat.Pad.{pad['id']}"
        marker.data.materials.append(materials["teal"])
        objects.append(marker)
    return objects


def add_wreck_proxies(table, height_at, materials):
    objects = []
    for index, wreck in enumerate(table["maskTruth"]["deepwater"]["wrecks"]):
        base = float(height_at(wreck["x"], wreck["z"])) + 0.10
        yaw = (-0.22, 0.12, -0.48, 0.31, -0.08)[index]
        width = (5.5, 7.4, 6.3, 7.0, 6.0)[index]
        depth = (2.8, 2.4, 3.3, 2.9, 2.5)[index]
        objects.append(claim.add_box_game(f"RenderHelperWreck.{wreck['id']}", wreck["x"], wreck["z"], base, (width, depth, 0.78), materials["wreck"], yaw=yaw, tilt=(0.10, -0.08), bevel=0.12))
        objects.append(claim.add_beam(f"RenderHelperWreck.{wreck['id']}.rib", (wreck["x"] - width * 0.35, wreck["z"], base + 0.7), (wreck["x"] + width * 0.35, wreck["z"], base + 1.4 + index * 0.06), 0.18, materials["brass"]))
    return objects


def add_working_claim_preview(table, height_at, materials):
    """Verdict-only salvage network that makes the claim's work legible."""
    objects = []

    # The published reef gap stays a clean ten-metre channel.  Paired buoys sit
    # just outside it, making the route visible without changing the mask.
    for side in (-1.0, 1.0):
        for index, game_z in enumerate((-6.0, 0.0, 6.0)):
            x = side * 6.2
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=12,
                radius=0.34,
                depth=1.65,
                location=(x, -game_z, 0.34),
            )
            buoy = bpy.context.object
            buoy.name = f"RenderHelperChannelBuoy.{side:+.0f}.{index}"
            buoy.data.materials.append(materials["teal"] if index % 2 else materials["brass"])
            objects.append(buoy)

    # Rough shelf derricks and scattered timbers turn the wreck beds into a
    # desperate working claim, while remaining absent from the exported GLB.
    for index, (x, game_z) in enumerate(((-27.0, -27.0), (26.0, -30.0))):
        floor = float(height_at(x, game_z))
        objects.extend(
            [
                claim.add_beam(f"RenderHelperShelfDerrick.{index}.left", (x - 1.7, game_z, floor), (x, game_z, floor + 4.1), 0.24, materials["wreck"]),
                claim.add_beam(f"RenderHelperShelfDerrick.{index}.right", (x + 1.7, game_z, floor), (x, game_z, floor + 4.1), 0.24, materials["wreck"]),
                claim.add_beam(f"RenderHelperShelfDerrick.{index}.jib", (x, game_z, floor + 4.0), (x + 3.0, game_z - 1.4, floor + 3.0), 0.20, materials["brass"]),
            ]
        )
        for rubble_index in range(5):
            dx = (-3.4, -1.7, 1.4, 2.9, 0.2)[rubble_index]
            dz = (-2.0, 2.3, -2.8, 1.4, 3.4)[rubble_index]
            objects.append(
                claim.add_box_game(
                    f"RenderHelperShelfRubble.{index}.{rubble_index}",
                    x + dx,
                    game_z + dz,
                    floor,
                    (1.0 + rubble_index * 0.12, 0.52, 0.36),
                    materials["wreck" if rubble_index % 2 else "brass"],
                    yaw=index * 0.6 + rubble_index * 0.73,
                    tilt=(0.12, -0.09),
                    bevel=0.03,
                )
            )
    # Short, locally anchored salvage lines keep the working network readable
    # without slicing across the whole tile or appearing detached from depth.
    wrecks = table["maskTruth"]["deepwater"]["wrecks"]
    for index, (derrick, wreck_indices) in enumerate((((-27.0, -27.0), (0, 1)), ((26.0, -30.0), (3, 4)))):
        dx, dz = derrick
        head_floor = float(height_at(dx, dz))
        for wreck_index in wreck_indices:
            wreck = wrecks[wreck_index]
            wreck_floor = float(height_at(wreck["x"], wreck["z"]))
            midpoint = ((dx + wreck["x"]) * 0.5, (dz + wreck["z"]) * 0.5, max(head_floor, wreck_floor) + 1.1)
            objects.append(
                claim.add_curve(
                    f"RenderHelperLocalSalvageLine.{index}.{wreck['id']}",
                    [(dx, dz, head_floor + 3.8), midpoint, (wreck["x"], wreck["z"], wreck_floor + 0.8)],
                    0.075,
                    materials["brass"],
                )
            )
    return objects


def add_drowned_town_preview(height_at, materials):
    """Mount existing E4 bodies for verdicts without baking them into terrain."""
    objects = []
    for mount in E4_TOWN_MOUNTS:
        source = ROOT / mount["asset"]
        if not source.is_file():
            raise FileNotFoundError(f"mounted E4 town source is missing: {source}")
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(source))
        imported = [obj for obj in bpy.data.objects if obj not in before]
        imported_set = set(imported)
        root = bpy.data.objects.new(f"RenderHelperMount.{mount['id']}", None)
        bpy.context.collection.objects.link(root)
        for obj in imported:
            obj["verdict_only"] = True
            obj["mounted_source"] = mount["asset"]
            if obj.parent not in imported_set:
                obj.parent = root
        x, y_offset, game_z = mount["position"]
        y = float(height_at(x, game_z)) + y_offset
        rx, ry, rz = mount["rotation"]
        root.location = (x, -game_z, y)
        root.rotation_euler = (rx, -rz, ry)
        root.scale = mount["scale"]
        root["verdict_only"] = True
        root["mount_id"] = mount["id"]
        objects.extend(imported)
        objects.append(root)
        # Loose timbers join the tipped bodies to the shelf instead of leaving
        # four isolated model cards. They remain evidence-only like the mounts.
        for index, (ox, oz, ex, ez) in enumerate(((-3.0, -1.8, 1.4, -0.4), (-1.2, 2.1, 2.8, 1.2))):
            objects.append(
                claim.add_beam(
                    f"RenderHelperMountDebris.{mount['id']}.{index}",
                    (x + ox, game_z + oz, y + 0.28),
                    (x + ex, game_z + ez, y + 0.55 + index * 0.15),
                    0.18,
                    materials["wreck"],
                )
            )
    return objects


def add_lighting(table):
    world = bpy.data.worlds.new("DeepwaterVerdictWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.032, 0.044, 0.042, 1.0)
    background.inputs["Strength"].default_value = 0.48

    sun_data = bpy.data.lights.new("DeepwaterStormLullSun", "SUN")
    sun_data.energy = 1.9
    sun_data.color = (0.56, 0.69, 0.67)
    sun_data.angle = math.radians(28)
    sun = bpy.data.objects.new("DeepwaterStormLullSun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.location = (-55.0, 30.0, 42.0)
    claim.aim_at(sun, (0.0, 0.0, -2.0))

    fill_data = bpy.data.lights.new("DeepwaterUnderGlassFill", "AREA")
    fill_data.energy = 980.0
    fill_data.color = (0.18, 0.38, 0.39)
    fill_data.shape = "DISK"
    fill_data.size = 54.0
    fill = bpy.data.objects.new("DeepwaterUnderGlassFill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = (0.0, 22.0, 27.0)
    claim.aim_at(fill, (0.0, 0.0, -2.4))
    lights = [sun, fill]

    ruin_data = bpy.data.lights.new("DeepwaterDrownedTownFill", "AREA")
    ruin_data.energy = 3600.0
    ruin_data.color = (0.20, 0.36, 0.32)
    ruin_data.shape = "DISK"
    ruin_data.size = 48.0
    ruin_fill = bpy.data.objects.new("DeepwaterDrownedTownFill", ruin_data)
    bpy.context.collection.objects.link(ruin_fill)
    ruin_fill.location = (0.0, 48.0, 16.0)
    claim.aim_at(ruin_fill, (0.0, 30.0, -5.8))
    lights.append(ruin_fill)

    anchor = table["maskTruth"]["deepwater"]["claimBoat"]["anchors"][0]
    for index, dx in enumerate((-3.8, 3.8)):
        data = bpy.data.lights.new(f"ClaimBoatLantern.{index}", "POINT")
        data.energy = 440.0
        data.color = (1.0, 0.38, 0.07)
        data.shadow_soft_size = 3.6
        light = bpy.data.objects.new(f"ClaimBoatLantern.{index}", data)
        bpy.context.collection.objects.link(light)
        light.location = (anchor["x"] + dx, -anchor["z"], 2.1)
        lights.append(light)
    return lights


def render_verdicts(table, terrain, sea, preview, overlay):
    panorama = claim.link_panorama(KEY)
    for obj in panorama:
        obj.visible_shadow = False
        obj.hide_render = True
    run = claim.add_camera("DeepwaterClaimRunCamera", (0.0, 48.0, 38.0), (0.0, -9.0, -1.5), 48.0)
    overview = claim.add_camera("DeepwaterClaimOverview", (0.0, 92.0, 118.0), (0.0, 0.0, -2.2), 49.0)
    low = claim.add_camera("DeepwaterClaimLowWeather", (-48.0, 43.0, 12.0), (8.0, -18.0, -1.1), 50.0)
    top = claim.add_camera("DeepwaterClaimMaskCamera", (0.0, 0.0, 155.0), (0.0, 0.0, -2.0), 52.0)
    horizon = claim.add_camera("DeepwaterClaimHorizon", (0.0, 0.0, 3.6), (-145.0, 88.0, 4.1), 53.0)
    contact = claim.add_camera("DeepwaterClaimRuinContact", (0.0, 58.0, 13.0), (0.0, 25.0, -5.8), 58.0)
    for camera in (run, overview, low, top, horizon, contact):
        camera.data.clip_end = 430.0

    lights = add_lighting(table)
    bpy.context.scene.view_settings.exposure = 1.10
    for obj in preview + overlay:
        obj.hide_render = True
    saved = [vertex.co.z for vertex in terrain.data.vertices]
    for vertex in terrain.data.vertices:
        vertex.co.z = -3.05
    terrain.data.update()
    claim.render(run, ARTIFACTS / "deepwater-claim-flat-tile-identical-camera.png")
    for vertex, value in zip(terrain.data.vertices, saved):
        vertex.co.z = value
    terrain.data.update()
    claim.render(run, ARTIFACTS / "deepwater-claim-sculpted-tile-identical-camera.png")

    for obj in preview:
        obj.hide_render = False
    claim.render(low, ARTIFACTS / "deepwater-claim-panorama-before.png")
    sea.hide_render = True
    for obj in overlay:
        obj.hide_render = False
    claim.render(top, ARTIFACTS / "deepwater-claim-mask-agreement.png")
    for obj in overlay:
        obj.hide_render = True
    sea.hide_render = False

    for obj in panorama:
        obj.hide_render = False
    sea.hide_render = True
    claim.render(contact, ARTIFACTS / "deepwater-claim-ruin-seabed-contact.png")
    sea.hide_render = False
    claim.render(contact, ARTIFACTS / "deepwater-claim-ruin-submerged.png")
    claim.render(run, ARTIFACTS / "deepwater-claim-run-camera.png")
    claim.render(overview, ARTIFACTS / "deepwater-claim-overview.png")
    claim.render(low, ARTIFACTS / "deepwater-claim-low-sunset.png")
    claim.render(low, ARTIFACTS / "deepwater-claim-panorama-mounted.png")
    claim.render(horizon, ARTIFACTS / "deepwater-claim-panorama-horizon.png")
    bpy.context.scene.view_settings.exposure = 0.0
    claim.remove_objects(lights + [run, overview, low, top, horizon, contact] + panorama)


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
        "simulation": "planar movement, collision, spawns, Claim-Boat placement, travel classes, weather, and combat remain unchanged",
        "heightSocket": "Terrain.visualY",
        "waterSurface": {"owner": "runtime DeepwaterClaimTile", "includedInTerrainGLB": False, "reason": "sea surface, swell, and water classification stay code-owned"},
        "theme": PROFILE["theme"],
        "regionalFamily": {"epoch": PROFILE["epoch"], "shared": PROFILE["shared"], "unique": ["shelf-reef bathymetry", "ten-metre reef gap", "five drowned-era work beds", "sealed eight-metre trench", "open-sea panorama"]},
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
            "lagoonShallows": "submerged floor follows published x=-42..42 z=18..44 region",
            "reefRing": "raised shelf follows published x=-48..48 z=-8..8 region",
            "reefGap": "open ten-metre passage follows published x=-5..5 override",
            "wreckShelf": "worked floor and five depressions follow published z=-42..-14 shelf and anchors",
            "trenchEdge": "drop follows published z=-64..-50 sealed region",
            "claimBoatDeck": "delegated to separate runtime Claim-Boat body; no terrain deck baked",
        },
        "landmarkFreeze": "preserved: no landmark mesh was edited or authored; existing E4 town bodies are reuse-only mounted candidates",
        "landmarkMountSpace": claim.landmark_mount_space(),
        "landmarkMounts": list(E4_TOWN_MOUNTS),
        "mountedRuinsPolicy": "four existing E4 GLBs are tipped and partly embedded as separate drowned-town mounts; they are absent from the terrain GLB and may be enabled, swapped, or removed without touching masks",
        "mountedRuinsContact": "each mount resolves Terrain.visualY inside its local drowned foundation hollow and applies only a small negative silt-bite offset; the complete heavy body rests on the submerged shelf instead of floating in the water column",
        "panoramaMount": claim.panorama_mount(KEY),
        "evidenceRig": "storm-lull sea proxy, warm Claim-Boat lanterns, separate collapsed E4 drowned-town mounts, channel buoys, locally anchored salvage lines, and shelf derricks; all scene helpers and mounts removed before terrain save/export",
        "sourceArt": [str(path.relative_to(ROOT)) for path in (KIT, SHELF_ATLAS, WRECK_PLATE, CLAIM_BOAT_PLATE)],
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
        raise ValueError("Deepwater authored dimensions changed")
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
    materials = helper_materials()
    sea = make_sea_proxy(sea_material())
    preview = (
        add_claim_boat_proxy(table, materials)
        + add_wreck_proxies(table, height_at, materials)
        + add_working_claim_preview(table, height_at, materials)
        + add_drowned_town_preview(height_at, materials)
    )
    overlay = add_mask_overlay(table, materials)
    render_verdicts(table, terrain, sea, preview, overlay)
    claim.remove_objects([sea] + preview + overlay)
    bpy.context.scene.world = None
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    contract = make_contract(table, terrain, atlas_path)
    if contract["triangles"] > contract["triangleBudget"]:
        raise AssertionError("Deepwater terrain triangle budget exceeded")
    export_asset(terrain, contract)


if __name__ == "__main__":
    main()
