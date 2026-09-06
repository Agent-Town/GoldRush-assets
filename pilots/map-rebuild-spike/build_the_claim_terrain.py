"""Build the render-only Claim terrain spike.

The simulation remains planar. This file authors only a visual heightfield in
the game's X/Z coordinates (mapped to Blender X/-Y so Blender's glTF export
lands back on game X/Z), with the fixed Claim water mask and centre ford
preserved literally. The mesh is intended to feed the existing Terrain.visualY
render seam if an attended follow-up promotes it.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import math

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"

BLEND = OUT / "the-claim-terrain.blend"
GLB = OUT / "the-claim-terrain.glb"
ATLAS = OUT / "the-claim-terrain-atlas.png"
CONTRACT = OUT / "the-claim-terrain-contract.json"

BANK_A = ROOT / "assets/processed/terrain-bank-tile.png"
BANK_B = ROOT / "assets/processed/terrain-bank-tile-b.png"
BANK_C = ROOT / "assets/processed/terrain-bank-tile-c.png"
RIVER = ROOT / "assets/processed/terrain-river-tile.png"
KIT_ERA = ROOT / "assets/raw/kit-era-1.png"
CONTRACT_PLATES = {
    "claim": ROOT / "assets/raw/plate-contract-the-claim.png",
    "dry-gulch": ROOT / "assets/raw/plate-contract-dry-gulch.png",
    "twin-banks": ROOT / "assets/raw/plate-contract-twin-banks.png",
    "night-shift": ROOT / "assets/raw/plate-contract-night-shift.png",
    "baron": ROOT / "assets/raw/plate-contract-baron.png",
}
GRIT_PROFILES = {
    "claim": {"black": 0.045, "white": 0.60, "gamma": 1.18, "ink": 0.34, "palette": 0.12, "saturation": 0.68},
    "dry-gulch": {"black": 0.040, "white": 0.65, "gamma": 1.05, "ink": 0.37, "palette": 0.12, "saturation": 0.62},
    "twin-banks": {"black": 0.045, "white": 0.58, "gamma": 1.15, "ink": 0.35, "palette": 0.12, "saturation": 0.66},
    "night-shift": {"black": 0.012, "white": 0.34, "gamma": 1.25, "ink": 0.40, "palette": 0.10, "saturation": 0.64},
    "baron": {"black": 0.025, "white": 0.52, "gamma": 1.25, "ink": 0.42, "palette": 0.13, "saturation": 0.68},
}

CLAIM_HALF = 32.0
RIVER_MIN_Z = -5.0
RIVER_MAX_Z = 5.0
SHALLOWS_WIDTH = 1.25
FORD_MIN_X = -3.0
FORD_MAX_X = 3.0
SEGMENTS = 128
ATLAS_SIZE = 2048
RUN_WIDTH = 1280
RUN_HEIGHT = 720
COUNTY_RADIUS = 160.0
COUNTY_OUTER_SEGMENTS = 20
COUNTY_NEAR_SEGMENTS = 16
COUNTY_EDGE_SEGMENTS = 64


def smoothstep(edge0, edge1, value):
    t = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def gaussian(x, y, cx, cy, sx, sy):
    return np.exp(-(((x - cx) / sx) ** 2 + ((y - cy) / sy) ** 2) * 0.5)


def rotated_gaussian(x, y, cx, cy, sx, sy, angle):
    dx = x - cx
    dy = y - cy
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    along = dx * cos_angle + dy * sin_angle
    across = -dx * sin_angle + dy * cos_angle
    return np.exp(-((along / sx) ** 2 + (across / sy) ** 2) * 0.5)


def channel_center(x):
    # The outer sim-water band never moves. Only its deeper visual channel bends.
    return 1.15 * np.sin(x * 0.115) + 0.38 * np.sin(x * 0.245 + 0.7)


def terrain_height(x, y):
    """Visual Z height in metres; accepts scalars or NumPy arrays."""
    x = np.asarray(x, dtype=np.float32)
    y = np.asarray(y, dtype=np.float32)
    ax = np.abs(x)
    ay = np.abs(y)

    center = channel_center(x)
    channel_distance = np.abs(y - center)
    deep_channel = 1.0 - smoothstep(1.65, 3.5, channel_distance)
    water_band = 1.0 - smoothstep(4.75, 6.25, ay)

    # Gentle valley-floor land. The routing lane and the claim apron remain calm.
    bank_edge_shape = np.sin(x * 0.16 + 0.4) * np.exp(-((ay - 8.0) / 3.8) ** 2) * 0.10
    bank_rise = 0.42 + bank_edge_shape + smoothstep(6.0, 17.0, ay) * 0.48
    valley_walls = smoothstep(19.0, 32.0, ay) * 0.96
    side_walls = smoothstep(22.0, 32.0, ax) * 0.52
    broad_ridges = (
        gaussian(x, y, -26.0, -24.0, 8.5, 7.0) * 0.36
        + gaussian(x, y, 24.0, 25.0, 9.0, 7.5) * 0.32
        + gaussian(x, y, 25.0, -22.0, 7.5, 8.0) * 0.24
    )
    macro = (
        np.sin(x * 0.19 + y * 0.07) * 0.045
        + np.sin(x * 0.43 - y * 0.16 + 1.3) * 0.025
        + np.cos(x * 0.11 + y * 0.27 - 0.4) * 0.025
    )
    land = bank_rise + valley_walls + side_walls + broad_ridges + macro

    # Submerged bars enrich the river without claiming dry, walkable ground.
    wet_bars = (
        gaussian(x, y, -16.0, channel_center(-16.0) + 1.2, 5.0, 0.72) * 0.16
        + gaussian(x, y, 15.0, channel_center(15.0) - 1.15, 4.6, 0.68) * 0.14
    )
    river_floor = -0.29 - deep_channel * 0.22 + wet_bars

    # The declared ford is the only raised crossing in the water mask.
    ford_x = 1.0 - smoothstep(2.1, 3.0, ax)
    ford = ford_x * water_band
    river_floor = river_floor * (1.0 - ford) + (-0.105 + macro * 0.18) * ford

    height = land * (1.0 - water_band) + river_floor * water_band

    # Spawn/claim apron and ford approaches: visually grounded, placement-honest.
    claim_apron = gaussian(x, y, 0.0, 12.0, 10.5, 7.0) * smoothstep(6.25, 8.0, ay)
    approach = gaussian(x, y, 0.0, 0.0, 5.2, 10.0) * smoothstep(5.8, 8.6, ay)
    calm = np.clip(claim_apron * 0.88 + approach * 0.74, 0.0, 0.94)
    calm_height = 0.34 + smoothstep(15.0, 25.0, ay) * 0.20
    height = height * (1.0 - calm) + calm_height * calm

    # Local desert landforms create authored pockets rather than one broad,
    # smooth plate. They remain visual-only and fade before the water mask.
    dry_land = smoothstep(7.5, 9.5, ay)
    mine_tailings = gaussian(x, y, -13.5, -9.5, 4.8, 3.8) * 0.46
    mine_cut = rotated_gaussian(x, y, -8.0, -10.0, 6.5, 1.8, -0.08) * -0.28
    skeleton_wash = rotated_gaussian(x, y, -7.5, 12.0, 7.5, 1.9, 0.12) * -0.16
    farmhouse_rise = gaussian(x, y, 10.5, 14.5, 5.4, 4.6) * 0.28
    west_shelf = gaussian(x, y, -15.5, 14.5, 3.2, 4.5) * 0.90
    cactus_hummocks = (
        gaussian(x, y, 18.5, -3.0, 4.0, 4.8) * 0.25
        + gaussian(x, y, 18.5, 11.0, 3.8, 4.5) * 0.22
    )
    height += (mine_tailings + mine_cut + skeleton_wash + farmhouse_rise + west_shelf + cactus_hummocks) * dry_land

    # Meet the existing vista's 1.18 m inner-edge ceiling without flattening
    # the authored interior. River-floor values already sit below this cap.
    perimeter = smoothstep(27.5, 32.0, np.maximum(ax, ay))
    perimeter_capped = np.minimum(height, 1.10)
    height = height * (1.0 - perimeter) + perimeter_capped * perimeter

    return np.clip(height, -0.52, 2.42)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = RUN_WIDTH
    scene.render.resolution_y = RUN_HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 15
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    scene.view_settings.exposure = 0.28


def image_pixels(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    pixels = np.asarray(image.pixels[:], dtype=np.float32).reshape(image.size[1], image.size[0], 4)
    rgb = pixels[:, :, :3].copy()
    bpy.data.images.remove(image)
    return rgb


def mirrored_indices(values, size, repeats, phase=0.0):
    wrapped = np.mod((values * repeats + phase), 2.0)
    mirrored = np.where(wrapped <= 1.0, wrapped, 2.0 - wrapped)
    return np.clip((mirrored * (size - 1)).astype(np.int32), 0, size - 1)


def tiled_sample(source, u, v, repeats, phase_u=0.0, phase_v=0.0):
    ix = mirrored_indices(u, source.shape[1], repeats, phase_u)
    iy = mirrored_indices(v, source.shape[0], repeats, phase_v)
    return source[iy, ix]


def luminance(rgb):
    return rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722


def engraved_ink(source, u, v, repeats=2.45, phase_u=0.11, phase_v=0.37):
    """Extract dark engraved strokes from shipped paint without copying objects."""
    sampled = tiled_sample(source, u, v, repeats, phase_u, phase_v)
    gray = luminance(sampled)
    surround = (
        np.roll(gray, 2, axis=0)
        + np.roll(gray, -2, axis=0)
        + np.roll(gray, 2, axis=1)
        + np.roll(gray, -2, axis=1)
    ) * 0.25
    return np.clip((surround - gray) * 7.5, 0.0, 1.0)


def apply_grit_grade(atlas, ink_source, u, v, contract_key):
    """Match the contract plate's palette and restore hard engraved contrast."""
    profile = GRIT_PROFILES[contract_key]
    plate = image_pixels(CONTRACT_PLATES[contract_key])
    plate_luma = luminance(plate)
    low, high = np.percentile(plate_luma, (18.0, 78.0))
    useful = plate[(plate_luma >= low) & (plate_luma <= high)]
    plate_tone = np.median(useful, axis=0) if useful.size else np.array((0.42, 0.25, 0.10))
    tone_luma = max(float(luminance(plate_tone)), 0.001)
    chroma = np.clip(plate_tone / tone_luma, 0.58, 1.42)
    palette_mix = profile["palette"]
    atlas = atlas * (1.0 - palette_mix) + atlas * chroma[None, None, :] * palette_mix

    base_luma = luminance(atlas)
    base_low, base_high = np.percentile(base_luma, (4.0, 96.0))
    normalized = np.clip((base_luma - base_low) / max(base_high - base_low, 0.001), 0.0, 1.0)
    target = profile["black"] + (profile["white"] - profile["black"]) * normalized ** profile["gamma"]
    atlas *= np.clip(target / np.maximum(base_luma, 0.006), 0.42, 1.65)[..., None]

    ink = engraved_ink(ink_source, u, v)
    atlas *= 1.0 - ink[..., None] * profile["ink"]
    # Fine diagonal cuts turn the shipped tile's dark marks into engraved
    # strokes. They stay subordinate to the source image and concentrate in
    # shadowed, already-damaged ground instead of becoming a global overlay.
    hatch_a = np.clip((np.sin((u + v * 0.36) * math.tau * 92.0) - 0.80) / 0.20, 0.0, 1.0)
    hatch_b = np.clip((np.sin((u - v * 0.42) * math.tau * 71.0) - 0.86) / 0.14, 0.0, 1.0)
    shadow_bias = np.clip((0.82 - normalized) / 0.66, 0.0, 1.0)
    hatch = np.clip(hatch_a * 0.74 + hatch_b * 0.36, 0.0, 1.0) * (0.18 + ink * 0.82) * shadow_bias
    atlas *= 1.0 - hatch[..., None] * 0.13
    graded_luma = luminance(atlas)
    atlas = graded_luma[..., None] + (atlas - graded_luma[..., None]) * profile["saturation"]
    return np.clip(atlas, 0.008, 0.90)


def ring_mask(x, z, cx, cz, radius, width):
    return np.exp(-((np.hypot(x - cx, z - cz) - radius) / width) ** 2)


def landmark_mount(identifier, x, z, yaw=0.0, scale=1.0):
    return {
        "id": identifier,
        "position": [float(x), 0.0, float(z)],
        "rotation": [0.0, float(yaw), 0.0],
        "scale": [float(scale), float(scale), float(scale)],
    }


def landmark_mount_space():
    return {
        "coordinates": "game X/Y/Z",
        "positionY": "local offset added to Terrain.visualY at the mount X/Z",
        "rotation": "XYZ Euler radians",
        "scale": "XYZ multiplier",
        "ownership": "landmark assets mount at runtime and are never baked into terrain",
    }


def panorama_mount(map_key):
    stem = "the-claim" if map_key in {"claim", "the-claim"} else map_key
    return {
        "id": f"{stem}-panorama",
        "asset": f"{stem}-panorama.glb",
        "position": [0.0, 0.0, 0.0],
        "rotation": [0.0, 0.0, 0.0],
        "scale": [1.0, 1.0, 1.0],
        "renderOnly": True,
        "ownership": "separate mounted scenery; never terrain or gameplay bounds",
    }


def link_panorama(map_key):
    mount = panorama_mount(map_key)
    path = OUT / mount["asset"]
    if not path.is_file():
        raise FileNotFoundError(f"build panorama first: {path}")
    existing = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported = [obj for obj in bpy.data.objects if obj not in existing]
    for obj in imported:
        obj.location = mount["position"]
        obj.rotation_euler = mount["rotation"]
        obj.scale = mount["scale"]
        obj.visible_shadow = False
    return imported


def make_atlas():
    bank_a = image_pixels(BANK_A)
    bank_b = image_pixels(BANK_B)
    bank_c = image_pixels(BANK_C)
    river = image_pixels(RIVER)
    kit = image_pixels(KIT_ERA)

    axis = np.linspace(0.0, 1.0, ATLAS_SIZE, dtype=np.float32)
    u, v = np.meshgrid(axis, axis)
    x = (u - 0.5) * CLAIM_HALF * 2.0
    y = (v - 0.5) * CLAIM_HALF * 2.0
    ax = np.abs(x)
    ay = np.abs(y)

    bank_clean = tiled_sample(bank_b, u, v, 3.35, 0.17, 0.31)
    bank_pebbles = tiled_sample(bank_c, u, v, 3.05, 0.63, 0.08)
    bank_wash = tiled_sample(bank_a, u, v, 2.15, 0.24, 0.51)
    macro_mix = (np.sin(x * 0.17 + y * 0.11) * 0.5 + 0.5)[..., None]
    bank = bank_wash * (0.42 + 0.06 * macro_mix) + bank_clean * 0.28 + bank_pebbles * (0.30 - 0.04 * macro_mix)

    # The Claim is a living river valley, not Dry Gulch with a water strip.
    # Keep the existing painted bank source but cool the damp corridor.
    damp = 1.0 - smoothstep(6.0, 15.0, ay)
    damp_tint = np.array((0.48, 0.58, 0.36), dtype=np.float32)
    bank = bank * (1.0 - damp[..., None] * 0.24) + bank * damp_tint * damp[..., None] * 0.24

    water = tiled_sample(river, u, v, 2.55, 0.41, 0.13)
    water = water * np.array((0.48, 0.43, 0.30), dtype=np.float32)
    center = channel_center(x)
    deep = 1.0 - smoothstep(1.45, 3.55, np.abs(y - center))
    deep_tint = np.array((0.30, 0.31, 0.22), dtype=np.float32)
    water = water * (1.0 - deep[..., None] * 0.74) + water * deep_tint * deep[..., None] * 0.74
    shallow = smoothstep(2.8, 5.0, np.abs(y - center))[..., None]
    water = water * (1.0 - shallow * 0.30) + bank_pebbles * np.array((0.52, 0.55, 0.39)) * shallow * 0.30
    channel_edge = np.exp(-((np.abs(y - center) - 2.25) / 0.24) ** 2)[..., None]
    water = water * (1.0 - channel_edge * 0.18) + np.array((0.58, 0.53, 0.35)) * channel_edge * 0.18
    flow_ink = engraved_ink(river, u, v, 2.55, 0.41, 0.13)
    water *= 1.0 - flow_ink[..., None] * 0.24
    foam = np.clip((np.sin(x * 0.42 + y * 1.38 + np.sin(x * 0.14) * 1.2) - 0.76) / 0.24, 0.0, 1.0) ** 2
    foam_color = bank_pebbles * np.array((0.58, 0.53, 0.40), dtype=np.float32)
    water = water * (1.0 - foam[..., None] * 0.12) + foam_color * foam[..., None] * 0.12

    # Sandy, still-wet bars stay visibly inside the declared river band.
    bars = np.clip(
        gaussian(x, y, -16.0, channel_center(-16.0) + 1.2, 5.0, 0.72)
        + gaussian(x, y, 15.0, channel_center(15.0) - 1.15, 4.6, 0.68),
        0.0,
        1.0,
    )
    wet_gravel = bank_pebbles * np.array((0.73, 0.78, 0.69), dtype=np.float32)
    water = water * (1.0 - bars[..., None] * 0.52) + wet_gravel * bars[..., None] * 0.52

    water_mask = 1.0 - smoothstep(5.0, 6.25, ay)
    atlas = bank * (1.0 - water_mask[..., None]) + water * water_mask[..., None]

    # The exact -3..3 ford becomes sandy shallows, but remains inside the water band.
    ford_x = 1.0 - smoothstep(2.15, 3.0, ax)
    ford = ford_x * (1.0 - smoothstep(4.8, 5.35, ay))
    ford_color = bank_clean * np.array((0.86, 0.88, 0.76), dtype=np.float32)
    atlas = atlas * (1.0 - ford[..., None] * 0.34) + ford_color * ford[..., None] * 0.34

    # Seven wet stepping stones communicate "ford", not a dry road across water.
    for index, stone_y in enumerate(np.linspace(-4.25, 4.25, 7)):
        stone_x = -0.28 if index % 2 == 0 else 0.32
        stone = gaussian(x, y, stone_x, stone_y, 0.46, 0.62)
        stone = smoothstep(0.42, 0.78, stone)
        stone_color = bank_pebbles * np.array((0.68, 0.70, 0.61), dtype=np.float32)
        atlas = atlas * (1.0 - stone[..., None] * 0.74) + stone_color * stone[..., None] * 0.74

    # Dark engraved banks clarify the gameplay water boundary at normal zoom.
    bank_line = np.exp(-((ay - 5.5) / 0.42) ** 2)[..., None]
    atlas *= 1.0 - bank_line * 0.28

    # U2.3 -- a damp silt band along both bank lips, just OUTSIDE the declared water
    # band, so the ground reads as ground the river has been wetting. Cool-damp tint
    # rather than a value drop: the lip stays legible, the map stays calm.
    silt = np.exp(-((ay - 6.9) / 0.95) ** 2)[..., None]
    silt_tint = np.array((0.52, 0.58, 0.44), dtype=np.float32)
    atlas = atlas * (1.0 - silt * 0.19) + atlas * silt_tint * silt * 0.19

    # U2.4 -- one small gravel rubble patch downstream on the east bank: spoil a crew
    # dumped clear of the working ground. Lighter and cooler than the bank around it.
    rubble = np.clip(
        gaussian(x, y, 22.5, 8.6, 2.3, 1.05)
        + gaussian(x, y, 24.4, 9.5, 1.25, 0.72) * 0.8,
        0.0,
        1.0,
    )[..., None]
    rubble_color = bank_pebbles * np.array((0.78, 0.76, 0.63), dtype=np.float32)
    atlas = atlas * (1.0 - rubble * 0.34) + rubble_color * rubble * 0.34

    # THE BEAUTY SHIFT, U2 (docs/beauty/the-claim-brief.md; F-OP5-12 graded this map
    # WEAK for "empty space with no travel pressure"). Four marks, all worn-in rather
    # than fought-over -- the Claim stays the calmest map in the game.
    #
    # 1. Cart ruts converging from the south spawn edge (+z) onto the centre ford.
    #    Two wheel tracks that start ~4.5 m apart at the edge and close to the ford
    #    mouth, plus a fainter third from the claim-house side of the yard.
    ford_ruts = np.clip(
        rotated_gaussian(x, y, -3.7, 18.2, 9.0, 0.155, math.radians(96.3)) * 0.9
        + rotated_gaussian(x, y, 3.7, 18.2, 9.0, 0.155, math.radians(83.7)) * 0.9
        + rotated_gaussian(x, y, 6.5, 15.0, 7.0, 0.14, math.radians(63.4)) * 0.6,
        0.0,
        1.0,
    )
    # 2. A worn foot-ring around each build-pad circle: the ring the boots make when
    #    a crew works a pad from every side. Same three pads the pocks already mark.
    foot_rings = np.clip(
        ring_mask(x, y, -13.0, -9.0, 3.15, 0.62) * 0.85
        + ring_mask(x, y, 12.0, 17.0, 2.55, 0.55) * 0.85
        + ring_mask(x, y, -2.0, 14.0, 1.95, 0.48) * 0.75,
        0.0,
        1.0,
    )
    # Working-ground wear is composed around the camp and mine, not sprayed
    # uniformly across the valley.
    ruts = np.clip(
        rotated_gaussian(x, y, -7.0, 18.2, 10.0, 0.16, 0.10)
        + rotated_gaussian(x, y, -7.0, 19.0, 10.0, 0.16, 0.10)
        + rotated_gaussian(x, y, -9.0, -10.5, 8.0, 0.20, -0.18)
        + ford_ruts
        + foot_rings * 0.55,
        0.0,
        1.0,
    )
    pocks = np.clip(
        ring_mask(x, y, -13.0, -9.0, 2.1, 0.34)
        + ring_mask(x, y, 12.0, 17.0, 1.6, 0.28)
        + ring_mask(x, y, -2.0, 14.0, 1.1, 0.24),
        0.0,
        1.0,
    )
    stains = np.clip(gaussian(x, y, -10.0, -8.0, 8.0, 5.0) * 0.55 + ruts * 0.75 + pocks * 0.65, 0.0, 1.0)
    scar_color = bank_wash * np.array((0.33, 0.24, 0.13), dtype=np.float32)
    land_damage = stains * (1.0 - water_mask)
    atlas = atlas * (1.0 - land_damage[..., None] * 0.42) + scar_color * land_damage[..., None] * 0.42

    # Use the accepted kit-era plate as a palette/hatching anchor without baking
    # its tents, people, or structures into the land.
    kit_terrain = kit[: max(1, kit.shape[0] // 3), : max(1, kit.shape[1] // 3), :]
    kit_luma = np.mean(kit_terrain, axis=2)
    useful = kit_terrain[(kit_luma > 0.12) & (kit_luma < 0.82)]
    kit_tone = np.median(useful, axis=0) if useful.size else np.array((0.53, 0.36, 0.17))
    kit_tone = np.clip(kit_tone, 0.08, 0.78)
    atlas = atlas * 0.94 + kit_tone[None, None, :] * 0.06

    # The outer 4 m return to parchment so the tile does not read as a hard card.
    edge_distance = np.maximum(ax, ay)
    edge = smoothstep(27.5, 31.75, edge_distance)[..., None]
    parchment = tiled_sample(bank_wash, u, v, 1.45, 0.31, 0.17) * np.array((0.72, 0.58, 0.38), dtype=np.float32)
    atlas = atlas * (1.0 - edge * 0.74) + parchment * edge * 0.74

    atlas = apply_grit_grade(atlas, bank_a, u, v, "claim")
    rgba = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    rgba[:, :, :3] = atlas

    image = bpy.data.images.new("TheClaimPaintedTerrainAtlas", ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(ATLAS)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image


def make_material(atlas):
    material = bpy.data.materials.new("TheClaimPaintedTerrainMaterial")
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
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def make_claim_county_material(atlas, name="RenderHelperClaimCountyPaint"):
    """Blend shipped bank plates into a non-repeating verdict-only surround."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Roughness"].default_value = 0.9
    texcoord = nodes.new("ShaderNodeTexCoord")

    textures = []
    for index, (path, scale, rotation) in enumerate(
        [(BANK_A, 7.4, 0.0), (BANK_B, 10.8, 0.23), (BANK_C, 15.2, -0.17)]
    ):
        mapping = nodes.new("ShaderNodeMapping")
        mapping.name = f"CountyBankMapping{index}"
        mapping.inputs["Scale"].default_value = (scale, scale, 1.0)
        mapping.inputs["Rotation"].default_value[2] = rotation
        texture = nodes.new("ShaderNodeTexImage")
        texture.name = f"CountyBankPlate{index}"
        texture.image = bpy.data.images.load(str(path), check_existing=True)
        texture.extension = "REPEAT"
        texture.interpolation = "Linear"
        links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
        links.new(mapping.outputs["Vector"], texture.inputs["Vector"])
        textures.append(texture)

    broad_noise = nodes.new("ShaderNodeTexNoise")
    broad_noise.inputs["Scale"].default_value = 5.0
    broad_noise.inputs["Detail"].default_value = 2.2
    broad_noise.inputs["Roughness"].default_value = 0.68
    links.new(texcoord.outputs["Generated"], broad_noise.inputs["Vector"])
    first_mix = nodes.new("ShaderNodeMixRGB")
    first_mix.blend_type = "MIX"
    links.new(broad_noise.outputs["Fac"], first_mix.inputs["Fac"])
    links.new(textures[0].outputs["Color"], first_mix.inputs[1])
    links.new(textures[1].outputs["Color"], first_mix.inputs[2])

    fine_noise = nodes.new("ShaderNodeTexNoise")
    fine_noise.inputs["Scale"].default_value = 18.0
    fine_noise.inputs["Detail"].default_value = 3.0
    links.new(texcoord.outputs["Generated"], fine_noise.inputs["Vector"])
    second_mix = nodes.new("ShaderNodeMixRGB")
    second_mix.blend_type = "MIX"
    links.new(fine_noise.outputs["Fac"], second_mix.inputs["Fac"])
    links.new(first_mix.outputs["Color"], second_mix.inputs[1])
    links.new(textures[2].outputs["Color"], second_mix.inputs[2])

    grade = nodes.new("ShaderNodeHueSaturation")
    grade.inputs["Saturation"].default_value = 0.62
    grade.inputs["Value"].default_value = 0.42
    links.new(second_mix.outputs["Color"], grade.inputs["Color"])
    warm_grade = nodes.new("ShaderNodeMixRGB")
    warm_grade.blend_type = "MULTIPLY"
    warm_grade.inputs["Fac"].default_value = 0.52
    warm_grade.inputs[2].default_value = (0.68, 0.42, 0.22, 1.0)
    links.new(grade.outputs["Color"], warm_grade.inputs[1])
    terrain_texture = nodes.new("ShaderNodeTexImage")
    terrain_texture.name = "CountyPlayableEdgeTexture"
    terrain_texture.image = atlas
    terrain_texture.extension = "REPEAT"
    outer_detail = nodes.new("ShaderNodeMixRGB")
    outer_detail.blend_type = "MIX"
    outer_detail.inputs["Fac"].default_value = 0.22
    links.new(warm_grade.outputs["Color"], outer_detail.inputs[1])
    links.new(terrain_texture.outputs["Color"], outer_detail.inputs[2])
    edge_blend = nodes.new("ShaderNodeAttribute")
    edge_blend.attribute_name = "countyBlend"
    final_mix = nodes.new("ShaderNodeMixRGB")
    final_mix.blend_type = "MIX"
    links.new(edge_blend.outputs["Fac"], final_mix.inputs["Fac"])
    links.new(terrain_texture.outputs["Color"], final_mix.inputs[1])
    links.new(outer_detail.outputs["Color"], final_mix.inputs[2])
    links.new(final_mix.outputs["Color"], shader.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.08
    bump_strength = nodes.new("ShaderNodeMath")
    bump_strength.operation = "MULTIPLY"
    bump_strength.inputs[1].default_value = 0.18
    links.new(edge_blend.outputs["Fac"], bump_strength.inputs[0])
    links.new(bump_strength.outputs["Value"], bump.inputs["Strength"])
    links.new(fine_noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def make_terrain(material):
    vertices = []
    uvs = []
    faces = []
    for yi in range(SEGMENTS + 1):
        game_z = -CLAIM_HALF + (CLAIM_HALF * 2.0) * yi / SEGMENTS
        for xi in range(SEGMENTS + 1):
            x = -CLAIM_HALF + (CLAIM_HALF * 2.0) * xi / SEGMENTS
            height = float(terrain_height(x, game_z))
            # Blender glTF maps (X, Y, Z) to (X, Z, -Y). Author -gameZ here
            # so a normal GLTFLoader import preserves the game's north/south.
            vertices.append((x, -game_z, height))
            uvs.append((xi / SEGMENTS, yi / SEGMENTS))

    row = SEGMENTS + 1
    for yi in range(SEGMENTS):
        for xi in range(SEGMENTS):
            a = yi * row + xi
            b = a + 1
            c = a + row
            d = c + 1
            # The Blender Y axis runs opposite game Z, so keep top-facing
            # winding after the coordinate conversion above.
            faces.append((a, d, b))
            faces.append((a, c, d))

    mesh = bpy.data.meshes.new("TheClaimTerrainMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = uvs[vertex_index]

    obj = bpy.data.objects.new("TheClaimTerrain", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(material)
    obj["render_only"] = True
    obj["sim_surface"] = "planar"
    obj["height_socket"] = "Terrain.visualY"
    obj["tile_id"] = "frontier-river-claim"
    obj["water_mask"] = "z=-5..5; shallows to +/-6.25"
    obj["ford_mask"] = "x=-3..3 inside water band"
    obj["grid_segments"] = SEGMENTS
    obj["grid_step_m"] = (CLAIM_HALF * 2.0) / SEGMENTS
    obj["source_plates"] = "terrain-bank-tile a/b/c; terrain-river-tile; kit-era-1 palette"
    obj["owner_preview_landmarks"] = "render helpers only; excluded from GLB"
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return obj


def make_water_surface(material):
    """Render helper matching the shipped visual-water width; never exported."""
    vertices = []
    uvs = []
    faces = []
    segments = 64
    for xi in range(segments + 1):
        x = -CLAIM_HALF + (CLAIM_HALF * 2.0) * xi / segments
        for game_z in (-6.25, 6.25):
            vertices.append((x, -game_z, 0.025))
            uvs.append(((x + CLAIM_HALF) / (CLAIM_HALF * 2.0), (game_z + CLAIM_HALF) / (CLAIM_HALF * 2.0)))
    for xi in range(segments):
        a = xi * 2
        b = a + 2
        c = a + 1
        d = b + 1
        faces.extend(((a, d, b), (a, c, d)))
    mesh = bpy.data.meshes.new("RenderHelperWaterMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            uv_layer.data[loop_index].uv = uvs[mesh.loops[loop_index].vertex_index]
    obj = bpy.data.objects.new("RenderHelperWater", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(material)
    return obj


def make_water_material(
    name="RenderHelperRiverWater",
    dark=(0.030, 0.023, 0.013),
    light=(0.155, 0.105, 0.048),
    roughness=0.36,
):
    """Verdict-render water; the runtime remains the production water owner."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = 0.0
    if "IOR" in shader.inputs:
        shader.inputs["IOR"].default_value = 1.333
    if "Coat Weight" in shader.inputs:
        shader.inputs["Coat Weight"].default_value = 0.08

    texcoord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (7.0, 4.0, 1.0)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.7
    noise.inputs["Detail"].default_value = 2.8
    noise.inputs["Roughness"].default_value = 0.62
    noise.inputs["Distortion"].default_value = 0.18
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.24
    ramp.color_ramp.elements[0].color = (*dark, 1.0)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (*light, 1.0)
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.22
    bump.inputs["Distance"].default_value = 0.07

    links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    separate = nodes.new("ShaderNodeSeparateXYZ")
    links.new(texcoord.outputs["Generated"], separate.inputs["Vector"])
    centered = nodes.new("ShaderNodeMath")
    centered.operation = "SUBTRACT"
    centered.inputs[1].default_value = 0.5
    links.new(separate.outputs["Y"], centered.inputs[0])
    absolute = nodes.new("ShaderNodeMath")
    absolute.operation = "ABSOLUTE"
    links.new(centered.outputs[0], absolute.inputs[0])
    edge_ramp = nodes.new("ShaderNodeValToRGB")
    edge_ramp.color_ramp.elements[0].position = 0.34
    edge_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    edge_ramp.color_ramp.elements[1].position = 0.49
    edge_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    links.new(absolute.outputs[0], edge_ramp.inputs["Fac"])
    shallow_mix = nodes.new("ShaderNodeMixRGB")
    shallow_mix.blend_type = "MIX"
    shallow_mix.inputs[2].default_value = (0.18, 0.115, 0.045, 1.0)
    links.new(edge_ramp.outputs["Color"], shallow_mix.inputs["Fac"])
    links.new(ramp.outputs["Color"], shallow_mix.inputs[1])
    links.new(shallow_mix.outputs["Color"], shader.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return material


def make_ford_stones(material):
    """Render-only copies of the seven runtime ford stones for scale/readability."""
    stones = [
        (-0.35, -4.25, 0.85, 0.56, 0.10),
        (0.35, -2.90, 0.70, 0.50, -0.20),
        (-0.18, -1.45, 0.78, 0.52, 0.45),
        (0.32, -0.05, 0.74, 0.50, -0.35),
        (-0.28, 1.42, 0.82, 0.55, 0.20),
        (0.34, 2.88, 0.72, 0.50, -0.10),
        (-0.12, 4.20, 0.86, 0.58, 0.35),
    ]
    objects = []
    for index, (x, game_z, sx, sz, yaw) in enumerate(stones):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=9,
            radius=0.55,
            depth=0.08,
            location=(x, -game_z, 0.070),
            rotation=(0.0, 0.0, yaw),
        )
        obj = bpy.context.object
        obj.name = f"RenderHelperFordStone.{index + 1:02d}"
        obj.scale = (sx, sz, 1.0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.data.materials.append(material)
        objects.append(obj)
    return objects


def make_render_material(name, color, roughness=0.9, metallic=0.0):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic

    # Verdict-only proxy materials should read as stained frontier stock, not
    # freshly painted primitives. Generated coordinates keep the dirt stable
    # per object without adding another texture or changing the terrain export.
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.6
    noise.inputs["Detail"].default_value = 4.2
    noise.inputs["Roughness"].default_value = 0.76
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.24
    ramp.color_ramp.elements[0].color = (*(component * 0.42 for component in color), 1.0)
    ramp.color_ramp.elements[1].position = 0.76
    ramp.color_ramp.elements[1].color = (*(min(1.0, component * 1.04 + 0.012) for component in color), 1.0)
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    return material


def game_point(x, game_z, height):
    return mathutils.Vector((x, -game_z, height))


def local_point(cx, cz, local_x, local_z, yaw):
    cos_yaw = math.cos(yaw)
    sin_yaw = math.sin(yaw)
    return (
        cx + local_x * cos_yaw - local_z * sin_yaw,
        cz + local_x * sin_yaw + local_z * cos_yaw,
    )


def finish_helper(obj, material, bevel=0.0):
    obj.data.materials.append(material)
    if bevel > 0 and obj.type == "MESH":
        modifier = obj.modifiers.new("Painted edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
    return obj


def add_box_game(name, x, game_z, base, dimensions, material, yaw=0.0, tilt=(0.0, 0.0), bevel=0.025):
    width, depth, height = dimensions
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, -game_z, base + height * 0.5), rotation=(tilt[0], tilt[1], -yaw))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = (width, depth, height)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish_helper(obj, material, bevel)


def add_beam(name, start, end, width, material):
    start_point = game_point(*start)
    end_point = game_point(*end)
    direction = end_point - start_point
    midpoint = (start_point + end_point) * 0.5
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=midpoint)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = (width, width, direction.length)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish_helper(obj, material, min(0.035, width * 0.12))


def add_cylinder_between(name, start, end, radius, material, vertices=7):
    start_point = game_point(*start)
    end_point = game_point(*end)
    direction = end_point - start_point
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=direction.length, location=(start_point + end_point) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    return finish_helper(obj, material)


def add_rock(name, x, game_z, scale, material, yaw=0.0):
    ground = float(terrain_height(x, game_z))
    sx, sy, sz = scale
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=(x, -game_z, ground + sz * 0.58), rotation=(0.18, 0.11, yaw))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish_helper(obj, material)


def add_curve(name, points, radius, material):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = radius
    curve.bevel_resolution = 0
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for index, point in enumerate(points):
        spline.points[index].co = (*game_point(*point), 1.0)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    return finish_helper(obj, material)


def add_roof_prism(name, x, game_z, base, width, depth, rise, material, yaw=0.0):
    half_width = width * 0.5
    half_depth = depth * 0.5
    vertices = [
        (-half_width, -half_depth, 0.0),
        (half_width, -half_depth, 0.0),
        (0.0, -half_depth, rise),
        (-half_width, half_depth, 0.0),
        (half_width, half_depth, 0.0),
        (0.0, half_depth, rise),
    ]
    faces = [(0, 2, 1), (3, 4, 5), (0, 3, 5, 2), (1, 2, 5, 4), (0, 1, 4, 3)]
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (x, -game_z, base)
    obj.rotation_euler.z = -yaw
    return finish_helper(obj, material, 0.035)


def make_cactus(name, x, game_z, scale, materials, flip=1.0, yaw=0.0, height_at=terrain_height):
    objects = []
    ground = float(height_at(x, game_z))
    height = 1.75 * scale
    trunk_top = ground + height
    objects.append(add_cylinder_between(f"{name}.trunk", (x, game_z, ground - 0.04), (x, game_z, trunk_top), 0.16 * scale, materials["cactus"]))
    arm_x = x + math.cos(yaw) * flip * 0.52 * scale
    arm_z = game_z + math.sin(yaw) * flip * 0.52 * scale
    arm_height = ground + height * 0.58
    objects.append(add_cylinder_between(f"{name}.arm", (x, game_z, arm_height), (arm_x, arm_z, arm_height), 0.105 * scale, materials["cactus"]))
    objects.append(add_cylinder_between(f"{name}.armtip", (arm_x, arm_z, arm_height), (arm_x, arm_z, arm_height + 0.48 * scale), 0.105 * scale, materials["cactus_light"]))
    if scale > 0.92:
        small_x = x - math.cos(yaw) * flip * 0.34 * scale
        small_z = game_z - math.sin(yaw) * flip * 0.34 * scale
        small_height = ground + height * 0.72
        objects.append(add_cylinder_between(f"{name}.smallarm", (x, game_z, small_height), (small_x, small_z, small_height), 0.08 * scale, materials["cactus"]))
        objects.append(add_cylinder_between(f"{name}.smalltip", (small_x, small_z, small_height), (small_x, small_z, small_height + 0.30 * scale), 0.08 * scale, materials["cactus_light"]))
    return objects


def make_cactus_thicket(materials):
    objects = []
    placed = []
    rng = np.random.default_rng(71303)
    while len(placed) < 26:
        x = float(rng.uniform(14.8, 21.8))
        game_z = float(rng.uniform(-13.0, 15.0))
        if abs(game_z) < 7.0:
            continue
        if any((x - px) ** 2 + (game_z - pz) ** 2 < 1.15**2 for px, pz in placed):
            continue
        placed.append((x, game_z))
        scale = float(rng.uniform(0.72, 1.28))
        objects.extend(
            make_cactus(
                f"RenderHelperCactus.{len(placed):02d}",
                x,
                game_z,
                scale,
                materials,
                -1.0 if len(placed) % 2 else 1.0,
                float(rng.uniform(-0.85, 0.85)),
            )
        )
    return objects


def make_ruined_mine(materials):
    objects = []
    cx, cz = -13.0, -8.8
    ground = float(terrain_height(cx, cz))
    top = ground + 5.6
    legs = [(-1.9, -1.15, -1.15, -0.66), (1.9, -1.15, 1.15, -0.66), (-1.9, 1.15, -1.15, 0.66), (1.9, 1.15, 1.15, 0.66)]
    for index, (bx, bz, tx, tz) in enumerate(legs):
        bottom_x, bottom_z = cx + bx, cz + bz
        objects.append(
            add_beam(
                f"RenderHelperMine.leg.{index}",
                (bottom_x, bottom_z, float(terrain_height(bottom_x, bottom_z))),
                (cx + tx, cz + tz, top),
                0.27,
                materials["timber"],
            )
        )
    for game_z in (cz - 0.66, cz + 0.66):
        objects.append(add_beam("RenderHelperMine.top", (cx - 1.4, game_z, top), (cx + 1.4, game_z, top), 0.31, materials["timber"]))
    objects.append(add_beam("RenderHelperMine.ridge", (cx, cz - 1.0, top + 0.75), (cx, cz + 1.0, top + 0.75), 0.24, materials["timber"]))
    objects.append(add_beam("RenderHelperMine.roofA", (cx - 1.4, cz - 0.9, top), (cx, cz - 0.9, top + 0.75), 0.22, materials["timber"]))
    objects.append(add_beam("RenderHelperMine.roofB", (cx + 1.4, cz - 0.9, top), (cx, cz - 0.9, top + 0.75), 0.22, materials["timber"]))
    objects.append(add_beam("RenderHelperMine.braceA", (cx - 1.75, cz - 1.12, ground + 0.5), (cx + 1.0, cz - 0.65, top - 0.3), 0.15, materials["wood"]))
    objects.append(add_beam("RenderHelperMine.braceB", (cx + 1.75, cz + 1.12, ground + 0.5), (cx - 1.0, cz + 0.65, top - 0.3), 0.15, materials["wood"]))
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.58,
        minor_radius=0.075,
        major_segments=18,
        minor_segments=6,
        location=(cx, -cz, top + 0.1),
        rotation=(math.pi / 2, 0.0, 0.0),
    )
    wheel = bpy.context.object
    wheel.name = "RenderHelperMine.pulley"
    objects.append(finish_helper(wheel, materials["rust"]))
    for rail_z in (cz - 2.1, cz - 2.9):
        rail_height = float(terrain_height(-8.5, rail_z)) + 0.08
        objects.append(add_beam("RenderHelperMine.rail", (-12.5, rail_z, rail_height), (-5.0, rail_z, rail_height), 0.085, materials["rust"]))
    cart_x, cart_z = -6.7, cz - 2.5
    cart_ground = float(terrain_height(cart_x, cart_z))
    objects.append(add_box_game("RenderHelperMine.cart", cart_x, cart_z, cart_ground + 0.28, (1.35, 0.92, 0.62), materials["rust"], yaw=0.05, tilt=(0.0, 0.08)))
    for dx in (-0.48, 0.48):
        for dz in (-0.48, 0.48):
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=10,
                radius=0.23,
                depth=0.11,
                location=(cart_x + dx, -(cart_z + dz), cart_ground + 0.3),
                rotation=(math.pi / 2, 0.0, 0.0),
            )
            objects.append(finish_helper(bpy.context.object, materials["iron"]))
    shed_x, shed_z = cx - 3.8, cz - 2.0
    shed_ground = float(terrain_height(shed_x, shed_z))
    objects.append(add_box_game("RenderHelperMine.shedWall", shed_x, shed_z, shed_ground, (3.2, 0.18, 2.0), materials["wood"], yaw=-0.12, tilt=(0.08, 0.0)))
    objects.append(add_box_game("RenderHelperMine.shedRoof", shed_x + 0.2, shed_z - 0.1, shed_ground + 1.65, (3.8, 2.2, 0.16), materials["roof"], yaw=-0.18, tilt=(0.12, 0.05)))
    objects.append(add_box_game("RenderHelperMine.shedHole", shed_x - 0.55, shed_z - 0.10, shed_ground + 0.42, (0.72, 0.08, 0.82), materials["iron"], yaw=-0.12, tilt=(0.06, -0.05), bevel=0.0))
    for index, offset in enumerate((-1.20, 0.18, 1.06)):
        objects.append(
            add_box_game(
                f"RenderHelperMine.shedRepair.{index}",
                shed_x + offset,
                shed_z - 0.14,
                shed_ground + 0.12,
                (0.16, 0.10, 1.72 - index * 0.16),
                materials["timber"],
                yaw=-0.12 + (index - 1) * 0.035,
                tilt=(0.0, (index - 1) * 0.055),
                bevel=0.008,
            )
        )
    for index, (rx, rz, scale) in enumerate([(-17.2, -12.8, (1.4, 1.0, 0.8)), (-15.6, -13.4, (1.0, 0.8, 0.65)), (-11.0, -13.0, (1.2, 0.9, 0.7)), (-9.6, -11.8, (0.85, 0.65, 0.5))]):
        objects.append(add_rock(f"RenderHelperMine.tailings.{index}", rx, rz, scale, materials["stone"], index * 0.7))
    return objects


def make_farmhouse(materials, condition="working"):
    objects = []
    cx, cz, yaw = 10.5, 14.5, -0.12
    ground = float(terrain_height(cx, cz))
    width, depth, wall_height = 5.4, 3.9, 2.45
    objects.append(add_box_game("RenderHelperFarmhouse.foundation", cx, cz, ground - 0.02, (width + 0.34, depth + 0.34, 0.22), materials["timber"], yaw=yaw, bevel=0.015))
    objects.append(add_box_game("RenderHelperFarmhouse.walls", cx, cz, ground, (width, depth, wall_height), materials["wall"], yaw=yaw, tilt=(0.0, 0.018), bevel=0.035))
    roof = add_roof_prism("RenderHelperFarmhouse.roof", cx, cz, ground + wall_height, width + 0.65, depth + 0.65, 1.55, materials["roof"], yaw)
    roof.rotation_euler.y += 0.055 if condition == "abandoned" else 0.018
    objects.append(roof)
    porch_x, porch_z = local_point(cx, cz, 0.0, depth * 0.5 + 1.0, yaw)
    objects.append(add_box_game("RenderHelperFarmhouse.deck", porch_x, porch_z, ground + 0.05, (5.0, 1.65, 0.18), materials["timber"], yaw=yaw))
    canopy_width = 3.10 if condition == "abandoned" else 5.0
    canopy_shift = -0.82 if condition == "abandoned" else 0.0
    canopy_x, canopy_z = local_point(porch_x, porch_z, canopy_shift, 0.0, yaw)
    objects.append(add_box_game("RenderHelperFarmhouse.canopy", canopy_x, canopy_z, ground + (1.84 if condition == "abandoned" else 2.12), (canopy_width, 1.72, 0.16), materials["roof"], yaw=yaw - (0.08 if condition == "abandoned" else 0.0), tilt=(0.20 if condition == "abandoned" else 0.05, 0.0)))
    porch_posts = (-2.05,) if condition == "abandoned" else (-2.05, 2.05)
    for local_x in porch_posts:
        post_x, post_z = local_point(cx, cz, local_x, depth * 0.5 + 1.55, yaw)
        lean = -0.065 if local_x < 0 else 0.045
        objects.append(add_box_game("RenderHelperFarmhouse.post", post_x, post_z, ground + 0.18, (0.16, 0.16, 1.95), materials["timber"], yaw=yaw, tilt=(0.0, lean), bevel=0.015))
    door_x, door_z = local_point(cx, cz, 0.0, depth * 0.5 + 0.07, yaw)
    objects.append(add_box_game("RenderHelperFarmhouse.door", door_x, door_z, ground + 0.18, (1.0, 0.12, 1.85), materials["timber"], yaw=yaw, bevel=0.02))
    for index, local_x in enumerate((-1.65, 1.65)):
        window_x, window_z = local_point(cx, cz, local_x, depth * 0.5 + 0.09, yaw)
        objects.append(add_box_game(f"RenderHelperFarmhouse.window.{index}", window_x, window_z, ground + 1.05, (0.95, 0.10, 0.78), materials["window"], yaw=yaw, bevel=0.018))
        objects.append(add_box_game(f"RenderHelperFarmhouse.shutter.{index}", window_x + (0.62 if index else -0.62), window_z, ground + 0.98, (0.22, 0.10, 0.92), materials["wood"], yaw=yaw + (0.18 if index else -0.12), bevel=0.012))
        if index == 0:
            for board_index, board_height in enumerate((0.16, 0.48)):
                objects.append(add_box_game(f"RenderHelperFarmhouse.windowBoard.{board_index}", window_x, window_z - 0.03, ground + 1.00 + board_height, (1.18, 0.10, 0.13), materials["timber"], yaw=yaw + 0.035 * (board_index * 2 - 1), bevel=0.006))

    # Uneven repair battens and scavenged roof sheets break the showroom-box
    # silhouette while leaving the proxy footprint and mount transform intact.
    for index, (local_x, height, lean) in enumerate([(-2.38, 2.08, -0.05), (-0.92, 1.92, 0.04), (0.78, 2.18, -0.035), (2.34, 1.76, 0.07)]):
        board_x, board_z = local_point(cx, cz, local_x, depth * 0.5 + 0.12, yaw)
        objects.append(add_box_game(f"RenderHelperFarmhouse.wallRepair.{index}", board_x, board_z, ground + 0.12, (0.17, 0.11, height), materials["wood" if index % 2 else "timber"], yaw=yaw + lean, tilt=(0.0, lean), bevel=0.008))
    for index, (local_x, local_z, slope) in enumerate([(-1.55, -0.35, -0.47), (1.30, 0.48, 0.44)]):
        patch_x, patch_z = local_point(cx, cz, local_x, local_z, yaw)
        objects.append(add_box_game(f"RenderHelperFarmhouse.roofPatch.{index}", patch_x, patch_z, ground + wall_height + 0.62, (1.42, 1.28, 0.07), materials["iron" if index == 0 else "rust"], yaw=yaw + 0.04 * (index * 2 - 1), tilt=(0.0, slope), bevel=0.006))

    # Roof seams survive the high gameplay camera where wall detail cannot.
    for index, local_x in enumerate((-2.20, -1.05, 1.05, 2.20)):
        seam_x, seam_z = local_point(cx, cz, local_x, 0.0, yaw)
        slope = -0.48 if local_x < 0 else 0.48
        seam_base = ground + wall_height + (0.42 if abs(local_x) > 2.0 else 0.92)
        objects.append(add_box_game(f"RenderHelperFarmhouse.roofSeam.{index}", seam_x, seam_z, seam_base, (0.11, depth + 0.30, 0.06), materials["timber"], yaw=yaw, tilt=(0.0, slope), bevel=0.004))

    if condition == "abandoned":
        hole_x, hole_z = local_point(cx, cz, -0.68, 0.42, yaw)
        objects.append(add_box_game("RenderHelperFarmhouse.roofHole", hole_x, hole_z, ground + wall_height + 1.34, (1.48, 1.55, 0.055), materials["iron"], yaw=yaw - 0.05, tilt=(0.0, -0.48), bevel=0.0))
        for index, offset in enumerate((-0.28, 0.30)):
            rafter_x, rafter_z = local_point(cx, cz, -0.70 + offset, 0.42, yaw)
            objects.append(add_box_game(f"RenderHelperFarmhouse.exposedRafter.{index}", rafter_x, rafter_z, ground + wall_height + 1.13, (0.10, 1.62, 0.09), materials["wood"], yaw=yaw + 0.05 * (index * 2 - 1), tilt=(0.0, -0.48), bevel=0.005))
        fallen_a = local_point(cx, cz, 1.78, depth * 0.5 + 1.52, yaw)
        fallen_b = local_point(cx, cz, 3.20, depth * 0.5 + 2.38, yaw)
        objects.append(add_beam("RenderHelperFarmhouse.fallenPorchPost", (fallen_a[0], fallen_a[1], ground + 0.12), (fallen_b[0], fallen_b[1], ground + 0.28), 0.15, materials["timber"]))
        panel_x, panel_z = local_point(cx, cz, 3.25, 0.58, yaw)
        panel_ground = float(terrain_height(panel_x, panel_z))
        objects.append(add_box_game("RenderHelperFarmhouse.fallenRoofPanel", panel_x, panel_z, panel_ground + 0.05, (2.35, 1.72, 0.12), materials["roof"], yaw=yaw + 0.28, tilt=(0.11, -0.06), bevel=0.008))
        for index, offset in enumerate((-0.62, 0.58)):
            beam_x, beam_z = local_point(panel_x, panel_z, offset, 0.0, yaw + 0.28)
            objects.append(add_box_game(f"RenderHelperFarmhouse.fallenRoofRafter.{index}", beam_x, beam_z, panel_ground + 0.15, (0.11, 1.95, 0.10), materials["timber"], yaw=yaw + 0.28, tilt=(0.11, -0.06), bevel=0.004))

    for index, (local_x, local_z, length) in enumerate([(-3.05, 0.55, 1.35), (2.95, -0.70, 1.05), (0.80, 3.15, 1.55)]):
        debris_x, debris_z = local_point(cx, cz, local_x, local_z, yaw)
        debris_ground = float(terrain_height(debris_x, debris_z))
        objects.append(add_box_game(f"RenderHelperFarmhouse.debris.{index}", debris_x, debris_z, debris_ground + 0.03, (length, 0.13, 0.11), materials["wood"], yaw=yaw + 0.32 * (index - 1), tilt=(0.04 * index, 0.0), bevel=0.005))
    chimney_x, chimney_z = local_point(cx, cz, 1.65, -0.35, yaw)
    objects.append(add_box_game("RenderHelperFarmhouse.chimney", chimney_x, chimney_z, ground + wall_height + 0.62, (0.58, 0.58, 1.24 if condition == "abandoned" else 1.65), materials["chimney"], yaw=yaw, tilt=(0.0, 0.09 if condition == "abandoned" else 0.0), bevel=0.01))
    if condition != "abandoned":
        objects.append(add_box_game("RenderHelperFarmhouse.chimneyCap", chimney_x, chimney_z, ground + wall_height + 2.20, (0.76, 0.76, 0.14), materials["chimney"], yaw=yaw, bevel=0.01))
    for index, local_x in enumerate((-3.3, -4.9, -6.5)):
        post_x, post_z = local_point(cx, cz, local_x, 2.8 + index * 0.18, yaw)
        post_ground = float(terrain_height(post_x, post_z))
        objects.append(add_box_game(f"RenderHelperFarmhouse.fencePost.{index}", post_x, post_z, post_ground, (0.13, 0.13, 0.9 - index * 0.12), materials["wood"], yaw=yaw + index * 0.06, tilt=(0.0, index * 0.05)))
        if index:
            previous_x, previous_z = local_point(cx, cz, (-3.3, -4.9, -6.5)[index - 1], 2.8 + (index - 1) * 0.18, yaw)
            previous_ground = float(terrain_height(previous_x, previous_z))
            objects.append(add_beam(f"RenderHelperFarmhouse.fenceRail.{index}", (previous_x, previous_z, previous_ground + 0.55), (post_x, post_z, post_ground + 0.46), 0.10, materials["wood"]))
    return objects


def make_bison_skeleton(materials):
    objects = []
    cx, cz, yaw = -8.0, 12.5, 0.18
    ground = float(terrain_height(cx, cz)) + 0.05
    spine_points = []
    for index in range(7):
        local_x = -1.55 + index * 0.48
        x, game_z = local_point(cx, cz, local_x, 0.0, yaw)
        spine_points.append((x, game_z, ground + 0.24 + math.sin(index * 0.65) * 0.05))
    objects.append(add_curve("RenderHelperBison.spine", spine_points, 0.11, materials["bone"]))
    for index, spine in enumerate(spine_points[1:6]):
        for side in (-1.0, 1.0):
            outer_x, outer_z = local_point(cx, cz, -1.05 + index * 0.48, side * (0.78 + index * 0.05), yaw)
            tip_x, tip_z = local_point(cx, cz, -1.1 + index * 0.48, side * (1.25 + index * 0.04), yaw)
            objects.append(add_curve(f"RenderHelperBison.rib.{index}.{int(side)}", [spine, (outer_x, outer_z, ground + 0.52), (tip_x, tip_z, ground + 0.16)], 0.075, materials["bone"]))
    skull_x, skull_z = local_point(cx, cz, 2.0, 0.0, yaw)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.62, location=(skull_x, -skull_z, ground + 0.26), rotation=(0.0, 0.3, -yaw))
    skull = bpy.context.object
    skull.name = "RenderHelperBison.skull"
    skull.scale = (1.25, 0.72, 0.55)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    objects.append(finish_helper(skull, materials["bone"]))
    for side in (-1.0, 1.0):
        horn_mid_x, horn_mid_z = local_point(cx, cz, 2.05, side * 0.58, yaw)
        horn_tip_x, horn_tip_z = local_point(cx, cz, 1.72, side * 1.05, yaw)
        objects.append(add_curve(f"RenderHelperBison.horn.{int(side)}", [(skull_x, skull_z, ground + 0.34), (horn_mid_x, horn_mid_z, ground + 0.48), (horn_tip_x, horn_tip_z, ground + 0.28)], 0.065, materials["horn"]))
    for index, local_x in enumerate((-1.2, -0.25, 0.8)):
        leg_x, leg_z = local_point(cx, cz, local_x, -0.25 + index * 0.2, yaw)
        foot_x, foot_z = local_point(cx, cz, local_x + 0.45, -1.15 + index * 0.35, yaw)
        objects.append(add_beam(f"RenderHelperBison.leg.{index}", (leg_x, leg_z, ground + 0.2), (foot_x, foot_z, ground + 0.12), 0.12, materials["bone"]))
    return objects


def make_dry_gulch_landmark_preview():
    materials = {
        "timber": make_render_material("PreviewTimber", (0.18, 0.085, 0.032)),
        "wood": make_render_material("PreviewSplinteredWood", (0.28, 0.13, 0.045)),
        "wall": make_render_material("PreviewStainedFarmhouse", (0.34, 0.19, 0.065)),
        "roof": make_render_material("PreviewOxidizedRoof", (0.23, 0.055, 0.022)),
        "rust": make_render_material("PreviewRustIron", (0.34, 0.15, 0.055), 0.78, 0.18),
        "iron": make_render_material("PreviewDarkIron", (0.095, 0.072, 0.052), 0.72, 0.35),
        "cactus": make_render_material("PreviewCactus", (0.12, 0.25, 0.105)),
        "cactus_light": make_render_material("PreviewCactusLight", (0.20, 0.34, 0.14)),
        "bone": make_render_material("PreviewSunBleachedBone", (0.84, 0.72, 0.48)),
        "horn": make_render_material("PreviewHorn", (0.30, 0.22, 0.12)),
        "stone": make_render_material("PreviewDesertStone", (0.34, 0.29, 0.22)),
        "chimney": make_render_material("PreviewChimneyStone", (0.20, 0.12, 0.07)),
        "window": make_render_material("PreviewBoardedWindowShadow", (0.095, 0.052, 0.022)),
    }
    objects = []
    objects.extend(make_ruined_mine(materials))
    objects.extend(make_farmhouse(materials, condition="abandoned"))
    objects.extend(make_cactus_thicket(materials))
    objects.extend(make_bison_skeleton(materials))
    for index, (x, game_z, scale) in enumerate(
        [
            (-18.2, 16.5, (1.1, 0.8, 0.65)),
            (-15.7, 10.5, (0.8, 0.65, 0.5)),
            (-16.4, 14.8, (1.8, 1.2, 0.9)),
            (-14.4, 16.3, (1.2, 0.82, 0.68)),
            (-11.5, 22.0, (0.65, 0.52, 0.42)),
            (4.5, 23.5, (0.75, 0.52, 0.44)),
            (7.2, -10.5, (0.9, 0.72, 0.5)),
            (2.0, -8.5, (0.58, 0.48, 0.36)),
            (-24.2, -7.8, (0.72, 0.58, 0.42)),
            (-21.3, -5.4, (0.42, 0.34, 0.28)),
            (-18.7, -13.8, (0.62, 0.48, 0.35)),
            (-10.2, -15.4, (0.46, 0.38, 0.27)),
            (-25.2, 5.8, (0.76, 0.54, 0.38)),
            (-22.6, 9.2, (0.38, 0.31, 0.24)),
            (-24.0, 21.2, (0.68, 0.50, 0.36)),
            (-19.8, 24.0, (0.42, 0.33, 0.25)),
            (17.8, -13.8, (0.74, 0.54, 0.39)),
            (22.0, -9.8, (0.42, 0.34, 0.25)),
            (23.8, 5.6, (0.65, 0.50, 0.34)),
            (25.0, 10.2, (0.38, 0.31, 0.23)),
            (22.3, 18.8, (0.72, 0.54, 0.38)),
            (18.6, 23.8, (0.44, 0.35, 0.26)),
            (8.4, 26.0, (0.58, 0.44, 0.32)),
            (-7.0, 25.8, (0.38, 0.31, 0.23)),
            (-28.0, -24.6, (0.58, 0.44, 0.31)),
            (-26.1, -21.1, (0.34, 0.28, 0.21)),
            (-6.8, -20.2, (0.52, 0.40, 0.29)),
            (-3.9, -25.7, (0.31, 0.26, 0.20)),
            (8.0, -27.2, (0.48, 0.37, 0.27)),
            (12.2, -23.4, (0.29, 0.24, 0.18)),
            (26.4, -15.4, (0.54, 0.42, 0.30)),
            (24.0, -20.3, (0.32, 0.26, 0.20)),
            (-28.0, 27.2, (0.50, 0.39, 0.28)),
            (-26.8, 26.0, (0.30, 0.25, 0.19)),
            (14.2, 28.0, (0.52, 0.40, 0.29)),
            (15.4, 26.9, (0.31, 0.26, 0.19)),
        ]
    ):
        objects.append(add_rock(f"RenderHelperDesertRock.{index}", x, game_z, scale, materials["stone"], index * 0.73))

    # Small support rubble breaks up the outer dead zones without filling the
    # readable claim apron or the ford. These remain preview-only, like every
    # landmark above.
    for index, (start_x, start_z, end_x, end_z, width) in enumerate(
        [
            (-22.2, -11.6, -20.6, -10.7, 0.10),
            (-18.4, -5.5, -17.0, -6.8, 0.09),
            (-12.0, -13.0, -10.2, -12.7, 0.08),
            (15.6, 19.8, 17.2, 20.6, 0.09),
            (19.2, 13.5, 20.8, 12.7, 0.08),
            (-23.4, 19.4, -21.8, 18.5, 0.08),
            (12.8, -11.7, 14.5, -12.2, 0.08),
            (20.6, 23.8, 21.9, 22.6, 0.07),
        ]
    ):
        start_ground = float(terrain_height(start_x, start_z)) + width * 0.65
        end_ground = float(terrain_height(end_x, end_z)) + width * 0.65
        objects.append(
            add_beam(
                f"RenderHelperBrokenTimber.{index}",
                (start_x, start_z, start_ground),
                (end_x, end_z, end_ground),
                width,
                materials["wood"],
            )
        )
    objects.extend(make_cactus("RenderHelperCactus.isolatedA", -20.2, 18.4, 0.82, materials, 1.0, 0.45))
    objects.extend(make_cactus("RenderHelperCactus.isolatedB", 7.5, -8.0, 0.68, materials, -1.0, -0.35))
    return objects


def make_tree(name, x, game_z, scale, materials):
    ground = float(terrain_height(x, game_z))
    objects = [
        add_cylinder_between(
            f"{name}.trunk",
            (x, game_z, ground - 0.05),
            (x, game_z, ground + 2.8 * scale),
            0.22 * scale,
            materials["bark"],
            vertices=8,
        )
    ]
    for index, (dx, dz, height, radius) in enumerate(
        [(-0.35, 0.0, 2.65, 1.15), (0.45, 0.12, 3.15, 1.0), (0.0, -0.38, 3.55, 0.88)]
    ):
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=1,
            radius=radius * scale,
            location=(x + dx * scale, -(game_z + dz * scale), ground + height * scale),
        )
        canopy = bpy.context.object
        canopy.name = f"{name}.canopy.{index}"
        canopy.scale.z = 0.78
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        objects.append(finish_helper(canopy, materials["foliage_light" if index == 1 else "foliage"]))
    return objects


def make_reed_cluster(name, x, game_z, scale, materials):
    ground = float(terrain_height(x, game_z))
    objects = []
    for index, (dx, dz, height) in enumerate([(-0.18, 0.0, 0.90), (0.12, 0.12, 1.15), (0.28, -0.10, 0.78)]):
        objects.append(
            add_cylinder_between(
                f"{name}.{index}",
                (x + dx * scale, game_z + dz * scale, ground),
                (x + dx * scale, game_z + dz * scale, ground + height * scale),
                0.035 * scale,
                materials["reed"],
                vertices=5,
            )
        )
    return objects


def make_claim_camp(materials):
    objects = []
    cx, cz, yaw = -8.5, 16.5, 0.10
    ground = float(terrain_height(cx, cz))
    objects.append(add_box_game("RenderHelperClaimCamp.groundsheet", cx, cz, ground + 0.02, (4.5, 3.4, 0.10), materials["timber"], yaw=yaw))
    objects.append(add_roof_prism("RenderHelperClaimCamp.tent", cx, cz, ground + 0.10, 4.2, 3.2, 2.35, materials["canvas"], yaw))
    objects.append(add_box_game("RenderHelperClaimCamp.flap", cx, cz + 1.62, ground + 0.12, (1.15, 0.08, 1.65), materials["canvas_dark"], yaw=yaw))
    patch_x, patch_z = local_point(cx, cz, -1.10, -0.20, yaw)
    objects.append(add_box_game("RenderHelperClaimCamp.canvasPatch", patch_x, patch_z, ground + 0.86, (1.05, 1.20, 0.045), materials["canvas_dark"], yaw=yaw - 0.08, tilt=(0.0, -0.58), bevel=0.005))

    for index, (x, game_z, dimensions) in enumerate(
        [(-5.8, 17.2, (0.95, 0.75, 0.72)), (-5.4, 16.2, (0.72, 0.62, 0.58)), (-11.4, 15.7, (1.15, 0.45, 0.38))]
    ):
        base = float(terrain_height(x, game_z))
        objects.append(add_box_game(f"RenderHelperClaimCamp.crate.{index}", x, game_z, base, dimensions, materials["wood"], yaw=-0.12 + index * 0.18))

    for index, (x, game_z) in enumerate([(-11.0, 18.2), (-4.7, 18.0), (-15.5, -11.0)]):
        base = float(terrain_height(x, game_z))
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.42, depth=0.88, location=(x, -game_z, base + 0.44))
        barrel = bpy.context.object
        barrel.name = f"RenderHelperClaimCamp.barrel.{index}"
        objects.append(finish_helper(barrel, materials["barrel"], 0.02))

    stake_x, stake_z = 6.5, 10.5
    stake_ground = float(terrain_height(stake_x, stake_z))
    objects.append(add_box_game("RenderHelperClaimStake.post", stake_x, stake_z, stake_ground, (0.14, 0.14, 1.75), materials["timber"], yaw=0.08))
    objects.append(add_box_game("RenderHelperClaimStake.board", stake_x, stake_z, stake_ground + 1.25, (1.15, 0.12, 0.55), materials["fresh_wood"], yaw=0.08))
    objects.append(add_box_game("RenderHelperClaimStake.brass", stake_x, stake_z - 0.08, stake_ground + 1.38, (0.24, 0.05, 0.18), materials["brass"], yaw=0.08, bevel=0.01))
    return objects


def make_claim_preview_materials():
    return {
        "timber": make_render_material("ClaimDarkTimber", (0.19, 0.095, 0.035)),
        "wood": make_render_material("ClaimWeatheredWood", (0.33, 0.16, 0.052)),
        "fresh_wood": make_render_material("ClaimExposedWood", (0.46, 0.25, 0.075)),
        "wall": make_render_material("ClaimStainedAdobe", (0.38, 0.235, 0.095)),
        "roof": make_render_material("ClaimOxidizedRoof", (0.24, 0.062, 0.025)),
        "rust": make_render_material("ClaimWorkingIron", (0.30, 0.16, 0.065), 0.72, 0.22),
        "iron": make_render_material("ClaimDarkIron", (0.085, 0.075, 0.060), 0.68, 0.38),
        "stone": make_render_material("ClaimRiverStone", (0.22, 0.26, 0.21)),
        "county_rock": make_render_material("ClaimCountyOchreRock", (0.27, 0.14, 0.055)),
        "chimney": make_render_material("ClaimChimneyStone", (0.18, 0.17, 0.13)),
        "window": make_render_material("ClaimSootedWindow", (0.12, 0.065, 0.025)),
        "canvas": make_render_material("ClaimStainedCanvas", (0.47, 0.34, 0.16)),
        "canvas_dark": make_render_material("ClaimCanvasShadow", (0.34, 0.20, 0.08)),
        "barrel": make_render_material("ClaimBarrel", (0.30, 0.15, 0.045)),
        "brass": make_render_material("ClaimBrass", (0.72, 0.42, 0.08), 0.48, 0.55),
        "cactus": make_render_material("ClaimCactusDark", (0.075, 0.20, 0.075)),
        "cactus_light": make_render_material("ClaimCactusSun", (0.14, 0.32, 0.10)),
        "reed": make_render_material("ClaimReeds", (0.34, 0.43, 0.12)),
    }


def make_claim_landmark_preview(materials=None):
    materials = materials or make_claim_preview_materials()
    objects = []
    objects.extend(make_ruined_mine(materials))
    objects.extend(make_farmhouse(materials, condition="working"))
    objects.extend(make_claim_camp(materials))

    for index, (x, game_z, scale, flip, yaw) in enumerate(
        [(-24.0, 10.0, 1.15, 1.0, 0.15), (-20.5, 13.0, 0.88, -1.0, -0.28), (22.5, -10.5, 1.10, 1.0, 0.42), (25.0, -14.0, 0.82, -1.0, -0.52), (20.5, 12.5, 0.92, 1.0, 0.70)]
    ):
        objects.extend(make_cactus(f"RenderHelperClaimCactus.{index}", x, game_z, scale, materials, flip, yaw))

    for index, (x, game_z, scale) in enumerate(
        [(-25.0, 6.8, 0.85), (-21.5, 6.9, 1.0), (-17.0, -6.8, 0.9), (-12.0, 6.75, 0.8), (12.0, -6.8, 0.9), (16.5, 6.85, 1.0), (21.0, -6.75, 0.85), (25.0, 6.9, 0.95)]
    ):
        objects.extend(make_reed_cluster(f"RenderHelperClaimReeds.{index}", x, game_z, scale, materials))

    for index, (x, game_z, scale) in enumerate(
        [(-22.0, 8.2, (1.2, 0.85, 0.65)), (-18.2, 9.2, (0.72, 0.55, 0.42)), (18.0, -8.4, (1.0, 0.72, 0.52)), (23.0, 8.5, (0.82, 0.62, 0.45)), (-11.0, -13.0, (0.9, 0.68, 0.48)), (15.0, 16.0, (0.72, 0.55, 0.40))]
    ):
        objects.append(add_rock(f"RenderHelperClaimRiverRock.{index}", x, game_z, scale, materials["stone"], index * 0.67))
    return objects


def preview_contract(objects, theme):
    meshes = [obj for obj in objects if obj.type == "MESH"]
    curves = [obj for obj in objects if obj.type == "CURVE"]
    triangles = sum(sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons) for obj in meshes)
    materials = {slot.material.name for obj in objects for slot in obj.material_slots if slot.material}
    return {
        "exported": False,
        "purpose": "owner composition verdict only; production fixtures remain a later attended slice",
        "theme": theme,
        "landmarks": ["active_headframe", "maintained_claim_house", "working_tent_camp", "fresh_claim_stake", "riparian_edge"],
        "objects": len(objects),
        "meshObjects": len(meshes),
        "curveObjects": len(curves),
        "approxTrianglesBeforeCurveTessellation": triangles,
        "materials": len(materials),
        "supportClutter": {"riverRocks": 6, "reedClusters": 8, "cacti": 5},
    }


def make_backdrop():
    material = bpy.data.materials.new("RenderHelperParchment")
    material.diffuse_color = (0.17, 0.085, 0.025, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (0.17, 0.085, 0.025, 1.0)
    shader.inputs["Roughness"].default_value = 1.0
    vertices = [(-220.0, -220.0, -0.68), (220.0, -220.0, -0.68), (220.0, 220.0, -0.68), (-220.0, 220.0, -0.68)]
    mesh = bpy.data.meshes.new("RenderHelperBackdropMesh")
    mesh.from_pydata(vertices, [], [(0, 1, 2), (0, 2, 3)])
    mesh.update()
    obj = bpy.data.objects.new("RenderHelperBackdrop", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(material)
    return obj


def claim_county_river_center(x):
    """Continue the shipped straight river only after it leaves the sim tile."""
    side = -1.0 if x < 0.0 else 1.0
    outside = max(0.0, abs(x) - CLAIM_HALF)
    delta = x - side * CLAIM_HALF
    ramp = float(smoothstep(0.0, 18.0, outside))
    return ramp * (math.sin(delta * 0.065) * 2.6 + math.sin(delta * 0.137) * 0.8)


def claim_county_height(x, game_z):
    """Low-resolution verdict terrain outside the sacred 64 m simulation tile."""
    continued_height = float(terrain_height(x, game_z))
    outside = max(0.0, abs(x) - CLAIM_HALF, abs(game_z) - CLAIM_HALF)
    if outside <= 0.0:
        return continued_height

    river_center = claim_county_river_center(x)
    river_distance = abs(game_z - river_center)
    river_mask = 1.0 - float(smoothstep(5.15, 7.15, river_distance))
    valley_floor = 0.32 + float(smoothstep(7.0, 31.0, river_distance)) * 1.55
    valley_wall = float(smoothstep(39.0, 118.0, abs(game_z))) * 7.4
    shoulder = float(smoothstep(58.0, 142.0, abs(x))) * float(smoothstep(13.0, 54.0, river_distance)) * 1.65
    rolling = (
        math.sin(x * 0.071 + game_z * 0.031) * 0.24
        + math.sin(x * 0.143 - game_z * 0.057 + 1.1) * 0.13
        + math.cos(x * 0.039 + game_z * 0.097) * 0.11
    )
    # The Claim's county identity is an open river corridor with worked shoulders,
    # not a canyon wall immediately outside the playable rectangle.
    worked_ridges = (
        float(gaussian(x, game_z, 69.0, 37.0, 18.0, 12.0)) * 2.35
        + float(gaussian(x, game_z, -82.0, -52.0, 23.0, 16.0)) * 2.10
        + float(gaussian(x, game_z, 48.0, -67.0, 19.0, 14.0)) * 1.75
        + float(gaussian(x, game_z, 118.0, 58.0, 25.0, 17.0)) * 2.20
    )
    land = valley_floor + valley_wall + shoulder + rolling + worked_ridges
    river_bed = -0.44 + math.sin(x * 0.11) * 0.035
    target = land * (1.0 - river_mask) + river_bed * river_mask
    # Continue the exact playable height derivative before easing toward the
    # coarser county profile; clamping here creates a visible tabletop rim.
    height_jitter = math.sin(x * 0.09 + game_z * 0.13) * 3.0 + math.sin(x * 0.21 - game_z * 0.07 + 1.4) * 1.5
    blend = float(smoothstep(10.0, 42.0, outside + height_jitter))
    return continued_height * (1.0 - blend) + target * blend


def make_county_ground(name, height_at, material, half=CLAIM_HALF, radius=COUNTY_RADIUS):
    """Shared render-only welded tile plus county surface; never exported."""
    west_far = [-radius + (radius - 40.0) * index / COUNTY_OUTER_SEGMENTS for index in range(COUNTY_OUTER_SEGMENTS + 1)]
    west_near = [-40.0 + (40.0 - half) * index / COUNTY_NEAR_SEGMENTS for index in range(COUNTY_NEAR_SEGMENTS + 1)]
    west = west_far[:-1] + west_near
    inner = [-half + half * 2.0 * index / COUNTY_EDGE_SEGMENTS for index in range(COUNTY_EDGE_SEGMENTS + 1)]
    east_near = [half + (40.0 - half) * index / COUNTY_NEAR_SEGMENTS for index in range(COUNTY_NEAR_SEGMENTS + 1)]
    east_far = [40.0 + (radius - 40.0) * index / COUNTY_OUTER_SEGMENTS for index in range(COUNTY_OUTER_SEGMENTS + 1)]
    east = east_near[:-1] + east_far
    axis = west[:-1] + inner + east[1:]
    vertices = []
    uvs = []
    faces = []
    for game_z in axis:
        for x in axis:
            vertices.append((x, -game_z, height_at(x, game_z)))
            uvs.append(((x + half) / (half * 2.0), (game_z + half) / (half * 2.0)))
    row = len(axis)
    for zi in range(row - 1):
        for xi in range(row - 1):
            a = zi * row + xi
            b = a + 1
            c = a + row
            d = c + 1
            faces.extend(((a, d, b), (a, c, d)))
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    blend_attribute = mesh.attributes.new(name="countyBlend", type="FLOAT", domain="POINT")
    for index, (x, blender_y, _height) in enumerate(vertices):
        game_z = -blender_y
        signed_distance = max(abs(x), abs(game_z)) - half
        edge_jitter = math.sin(x * 0.31 + game_z * 0.17) * 2.2 + math.sin(x * 0.11 - game_z * 0.43 + 0.8) * 1.15
        # Break the integration boundary into a broad natural soil transition;
        # a ruler-straight blend advertises the original square tile.
        blend_attribute.data[index].value = float(smoothstep(-7.0, 17.0, signed_distance + edge_jitter))
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = uvs[vertex_index]
        polygon.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(material)
    obj["owner_preview_only"] = True
    obj["simulation"] = "none; outside playable bounds"
    return obj


def make_claim_county_ground(material):
    return make_county_ground("RenderHelperClaimCountyGround", claim_county_height, material)


def make_county_water_ribbon(
    name,
    center_at,
    half_width,
    material,
    radius=COUNTY_RADIUS,
    segments=96,
    across_segments=4,
    half_width_at=None,
    water_height_at=None,
):
    """Shared continuous water ribbon; the caller owns mask-compatible shape."""
    vertices = []
    uvs = []
    faces = []
    for row in range(across_segments + 1):
        for index in range(segments + 1):
            x = -radius + radius * 2.0 * index / segments
            local_half_width = half_width_at(x) if half_width_at else half_width
            across = -local_half_width + local_half_width * 2.0 * row / across_segments
            game_z = center_at(x) + across
            height = water_height_at(x, game_z, row / across_segments) if water_height_at else 0.025
            vertices.append((x, -game_z, height))
            uvs.append(((x + radius) / (radius * 2.0), row / across_segments))
    width = segments + 1
    for row in range(across_segments):
        for xi in range(segments):
            a = row * width + xi
            b = a + 1
            c = a + width
            d = c + 1
            faces.extend(((a, d, b), (a, c, d)))
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = uvs[vertex_index]
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(material)
    return [obj]


def make_claim_county_river(material):
    return make_county_water_ribbon(
        "RenderHelperClaimCountyRiver",
        claim_county_river_center,
        6.25,
        material,
    )


def add_county_rock(name, x, game_z, scale, material, yaw=0.0, height_at=claim_county_height):
    base = height_at(x, game_z)
    sx, sy, sz = scale
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=1,
        radius=1.0,
        location=(x, -game_z, base + sz * 0.55),
        rotation=(0.16, 0.10, yaw),
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish_helper(obj, material)


def add_county_mesa(name, x, game_z, radius, depth, material, vertices=7, height_at=claim_county_height):
    base = height_at(x, game_z) - 0.18
    objects = []
    for layer, (scale_x, scale_y, scale_z, height) in enumerate(
        [(1.0, 0.68, 0.44, 0.16), (0.66, 0.48, 0.34, 0.62), (0.38, 0.32, 0.22, 0.92)]
    ):
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=2 if layer == 0 else 1,
            radius=1.0,
            location=(x + layer * radius * 0.07, -game_z, base + depth * height),
            rotation=(0.08 * layer, 0.05, x * 0.013 + layer * 0.17),
        )
        rock = bpy.context.object
        rock.name = f"{name}.layer{layer}"
        rock.scale = (radius * scale_x, radius * scale_y, depth * scale_z)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        objects.append(finish_helper(rock, material))
    return objects


def make_distant_claim_works(materials):
    """Claim-specific county signature: another hard-used extraction scar."""
    objects = []
    x, game_z = 57.0, 24.0
    base = claim_county_height(x, game_z)
    objects.extend(
        [
            add_beam("RenderHelperCountyWorks.legWest", (x - 2.2, game_z, base), (x - 0.9, game_z, base + 5.5), 0.20, materials["timber"]),
            add_beam("RenderHelperCountyWorks.legEast", (x + 2.2, game_z, base), (x + 0.9, game_z, base + 5.5), 0.20, materials["timber"]),
            add_beam("RenderHelperCountyWorks.crossbar", (x - 1.05, game_z, base + 5.35), (x + 1.05, game_z, base + 5.35), 0.18, materials["timber"]),
            add_box_game("RenderHelperCountyWorks.oreBin", x + 3.1, game_z + 1.2, base, (2.6, 2.2, 1.25), materials["wood"], yaw=-0.16),
        ]
    )
    for index, (dx, dz, scale) in enumerate([(-4.2, -1.5, (2.5, 1.8, 1.1)), (4.9, 2.0, (3.1, 2.0, 1.35)), (1.8, -3.3, (2.0, 1.4, 0.8))]):
        objects.append(add_county_rock(f"RenderHelperCountyTailings.{index}", x + dx, game_z + dz, scale, materials["stone"], index * 0.7))
    return objects


def make_claim_county_surround(terrain_material, water_material, materials):
    objects = [make_claim_county_ground(terrain_material)]
    objects.extend(make_claim_county_river(water_material))
    for index, (x, game_z, scale, flip, yaw) in enumerate(
        [
            (-45.0, 8.4, 1.45, 1.0, 0.18),
            (-52.0, -8.8, 1.05, -1.0, -0.35),
            (-61.0, 15.5, 1.25, 1.0, 0.72),
            (44.0, 8.6, 1.50, -1.0, 0.46),
            (51.0, -8.3, 1.10, 1.0, -0.58),
            (66.0, 17.5, 1.30, -1.0, 0.94),
        ]
    ):
        objects.extend(
            make_cactus(
                f"RenderHelperClaimCountyCactus.{index}",
                x,
                game_z,
                scale,
                materials,
                flip,
                yaw,
                height_at=claim_county_height,
            )
        )
    for index, (x, game_z, radius, depth) in enumerate(
        [(-82.0, 52.0, 15.0, 6.2), (-118.0, 38.0, 12.0, 5.0), (79.0, 45.0, 16.0, 7.0), (116.0, 34.0, 13.0, 5.4), (70.0, -66.0, 13.0, 5.8), (132.0, 70.0, 18.0, 7.4)]
    ):
        objects.extend(add_county_mesa(f"RenderHelperClaimCountyMesa.{index}", x, game_z, radius, depth, materials["county_rock"], 7 + index % 2))
    for index, (x, game_z, scale) in enumerate(
        [(-42.0, 17.0, (1.8, 1.2, 1.0)), (-58.0, 13.0, (2.6, 1.7, 1.4)), (39.0, -17.0, (1.6, 1.1, 0.9)), (73.0, -20.0, (3.2, 2.1, 1.7))]
    ):
        objects.append(add_county_rock(f"RenderHelperClaimCountyOutcrop.{index}", x, game_z, scale, materials["county_rock"], index * 0.61))
    objects.extend(make_distant_claim_works(materials))
    meshes = [obj for obj in objects if obj.type == "MESH"]
    triangles = sum(sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons) for obj in meshes)
    return objects, {
        "exported": False,
        "purpose": "owner exterior verdict only; runtime vista remains code-owned",
        "radiusMeters": COUNTY_RADIUS,
        "groundSegments": {"far": COUNTY_OUTER_SEGMENTS, "near": COUNTY_NEAR_SEGMENTS, "edge": COUNTY_EDGE_SEGMENTS},
        "objects": len(objects),
        "approxTriangles": triangles,
        "regionalGrammar": ["open river valley", "faceted ochre mesas", "sparse cacti", "worked extraction scars"],
        "claimSignature": ["two meandering river exits", "distant headframe", "tailings shoulder"],
    }


def aim_at(obj, target):
    direction = mathutils.Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_camera(name, location, target, fov_degrees):
    data = bpy.data.cameras.new(name)
    camera = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(camera)
    camera.location = location
    data.lens = 50.0
    data.sensor_fit = "VERTICAL"
    data.angle_y = math.radians(fov_degrees)
    data.clip_start = 0.1
    data.clip_end = 240.0
    aim_at(camera, target)
    return camera


def add_lighting(sunset=False):
    world = bpy.data.worlds.new("TheClaimWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if sunset:
        background.inputs["Color"].default_value = (0.06, 0.025, 0.04, 1.0)
        background.inputs["Strength"].default_value = 0.55
    else:
        background.inputs["Color"].default_value = (0.18, 0.11, 0.045, 1.0)
        background.inputs["Strength"].default_value = 0.72

    sun_data = bpy.data.lights.new("PaintedSun", "SUN")
    sun_data.energy = 3.4 if sunset else 3.25
    sun_data.color = (1.0, 0.50, 0.20) if sunset else (1.0, 0.86, 0.66)
    sun_data.angle = math.radians(6.0 if sunset else 12.0)
    sun = bpy.data.objects.new("PaintedSun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.location = (-42.0, -46.0, 11.0) if sunset else (-42.0, -34.0, 32.0)
    aim_at(sun, (0.0, 0.0, 0.0))
    lights = [sun]
    if sunset:
        fill_data = bpy.data.lights.new("CoolSkyFill", "AREA")
        fill_data.energy = 520.0
        fill_data.color = (0.24, 0.34, 0.46)
        fill_data.shape = "DISK"
        fill_data.size = 28.0
        fill = bpy.data.objects.new("CoolSkyFill", fill_data)
        bpy.context.collection.objects.link(fill)
        fill.location = (22.0, -10.0, 18.0)
        aim_at(fill, (0.0, 0.0, 0.0))
        lights.append(fill)
    return lights


def render(camera, filepath):
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.filepath = str(filepath)
    bpy.ops.render.render(write_still=True)


def remove_objects(objects):
    for obj in objects:
        if obj and obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)


LANDMARK_PACK = OUT / "landmarks/the-claim/the-claim-landmark-pack-contract.json"


def landmark_records():
    """The shipped mount records, sourced from the landmark pack contract.

    The pack owns the asset paths and the terrain-conform Y offsets; the mounts
    sweep (apply_mounts_sweep.py) backfilled them into this terrain contract for
    other maps and a one-off did it here. A re-export that regenerated only the
    recipe's own literals therefore DROPPED `asset` from every mount, and the
    pilot -- which filters mounts on `asset` -- mounted zero landmarks while the
    map still reported state=ready. That is the Mistake #10 shape (a merge that
    looks green while the player loses the tent, the claim house and the
    headframe), and it is why the pack is read here instead: re-export is now
    complete on its own. Falls back to the recipe literals if the pack is absent.
    """
    fallback = [
        landmark_mount("active_headframe", -13.0, -8.8),
        landmark_mount("maintained_claim_house", 10.5, 14.5, -0.12),
        landmark_mount("working_camp", -8.5, 16.5, 0.10),
        landmark_mount("claim_stake", 6.5, 10.5, 0.08),
        landmark_mount("riparian_dressing_pack", 0.0, 0.0),
    ]
    if not LANDMARK_PACK.exists():
        return fallback, None
    pack = json.loads(LANDMARK_PACK.read_text(encoding="utf-8"))
    mounts = pack.get("mounts")
    if not mounts:
        return fallback, None
    records = [dict(mount) for mount in mounts]
    if any(not record.get("asset") for record in records):
        raise ValueError("landmark pack mount without an asset: re-export would hide a landmark")
    return records, {
        "contract": "landmarks/the-claim/the-claim-landmark-pack-contract.json",
        "atlas": pack["atlas"]["asset"],
        "era": pack["era"],
        "sourceLadder": "reuse > derive > build-new",
        "ownership": "separate mounted render-only GLBs; no simulation authority",
    }


def mesh_contract(obj, owner_preview):
    triangles = sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons)
    coords = np.asarray([vertex.co[:] for vertex in obj.data.vertices], dtype=np.float32)
    landmark_mounts, landmark_pack = landmark_records()
    return {
        "asset": GLB.name,
        "tileId": "frontier-river-claim",
        "renderOnly": True,
        "simulation": "planar and unchanged",
        "heightSocket": "Terrain.visualY",
        "coordinates": {
            "blender": "X/-gameZ with Blender Z as visual height",
            "glbAndGame": "X/Z with Y=Terrain.visualY",
        },
        "boundsMeters": {
            "min": [round(float(value), 4) for value in coords.min(axis=0)],
            "max": [round(float(value), 4) for value in coords.max(axis=0)],
        },
        "meshCount": 1,
        "primitiveCount": 1,
        "materialCount": 1,
        "texture": {"count": 1, "width": ATLAS_SIZE, "height": ATLAS_SIZE, "embedded": True},
        "vertices": len(obj.data.vertices),
        "triangles": triangles,
        "triangleBudget": 60000,
        "waterTruth": {
            "river": {"minZ": RIVER_MIN_Z, "maxZ": RIVER_MAX_Z},
            "shallowsWidth": SHALLOWS_WIDTH,
            "ford": {"minX": FORD_MIN_X, "maxX": FORD_MAX_X},
            "note": "The S-curve is a deeper visual channel inside the fixed river band; outer banks do not meander.",
        },
        "landmarkMountSpace": landmark_mount_space(),
        "landmarkMounts": landmark_mounts,
        **({"landmarkPack": landmark_pack} if landmark_pack else {}),
        "panoramaMount": panorama_mount("the-claim"),
        "ownerPreview": owner_preview,
        "sourceArt": [
            str(path.relative_to(ROOT))
            for path in (BANK_A, BANK_B, BANK_C, RIVER, KIT_ERA, CONTRACT_PLATES["claim"])
        ],
    }


def export_asset(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.export_scene.gltf(
        filepath=str(GLB),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_extras=True,
    )


def write_contract(contract):
    contract["files"] = {
        "blend": {"bytes": BLEND.stat().st_size, "sha256": sha256(BLEND)},
        "glb": {"bytes": GLB.stat().st_size, "sha256": sha256(GLB)},
        "atlas": {"bytes": ATLAS.stat().st_size, "sha256": sha256(ATLAS)},
    }
    CONTRACT.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    reset_scene()
    atlas = make_atlas()
    material = make_material(atlas)
    terrain = make_terrain(material)
    water_material = make_water_material()
    water_mapping = next(node for node in water_material.node_tree.nodes if node.type == "MAPPING")
    water_mapping.inputs["Scale"].default_value[0] = 24.5
    ford_stones = make_ford_stones(material)
    preview_materials = make_claim_preview_materials()
    landmarks = make_claim_landmark_preview(preview_materials)
    landmark_stats = preview_contract(landmarks, "living-working-claim")
    county_material = make_claim_county_material(atlas)
    county, county_stats = make_claim_county_surround(county_material, water_material, preview_materials)
    landmark_stats["exteriorSurround"] = county_stats
    backdrop = make_backdrop()
    panorama = link_panorama("the-claim")
    for obj in panorama:
        obj.hide_render = True
    for obj in county:
        obj.hide_render = True
    terrain.hide_render = False

    # Three.js run camera: hero target (0, .06, 12), offset (0, 26.2, 18.3),
    # look target z -= 3.35, vertical FOV 42 degrees.
    run_camera = add_camera(
        "ClaimRunCamera",
        (0.0, -30.3, 26.26),
        (0.0, -8.65, 0.51),
        42.0,
    )
    lights = add_lighting(sunset=False)
    render(run_camera, ARTIFACTS / "owner-run-camera-sculpted.png")
    edge_camera = add_camera(
        "ClaimRunCameraEastEdge",
        (24.0, -30.3, 26.26),
        (24.0, -8.65, 0.51),
        42.0,
    )
    render(edge_camera, ARTIFACTS / "owner-run-camera-east-edge.png")
    overview_camera = add_camera(
        "ClaimLayoutOverview",
        (0.0, -38.0, 50.0),
        (0.0, -1.0, 0.42),
        46.0,
    )
    render(overview_camera, ARTIFACTS / "owner-layout-overview.png")

    # Exterior evidence swaps in the welded render-only county surface only
    # after the exported terrain has received its own acceptance captures.
    terrain.hide_render = True
    for obj in county:
        obj.hide_render = False
    county_camera = add_camera(
        "ClaimCountyOverview",
        (0.0, -78.0, 88.0),
        (0.0, -5.0, 1.1),
        52.0,
    )
    render(county_camera, ARTIFACTS / "owner-county-overview.png")

    remove_objects(lights)
    low_camera = add_camera(
        "ClaimLowSunsetCamera",
        (-28.0, 23.0, 11.0),
        (5.0, -0.4, 0.38),
        46.0,
    )
    horizon_camera = add_camera(
        "ClaimPanoramaHorizon",
        (0.0, 0.0, 3.8),
        (0.0, 120.0, 8.0),
        52.0,
    )
    sunset_lights = add_lighting(sunset=True)
    for obj in county:
        obj.hide_render = True
    terrain.hide_render = False
    render(low_camera, ARTIFACTS / "the-claim-exterior-before-low.png")
    terrain.hide_render = True
    for obj in county:
        obj.hide_render = False
    render(low_camera, ARTIFACTS / "owner-low-sunset.png")
    render(low_camera, ARTIFACTS / "the-claim-panorama-before.png")
    for obj in panorama:
        obj.hide_render = False
    render(low_camera, ARTIFACTS / "the-claim-panorama-mounted.png")
    render(horizon_camera, ARTIFACTS / "the-claim-panorama-horizon.png")

    # No cameras or lights survive into the authoring file or GLB.
    remove_objects(
        sunset_lights
        + [run_camera, edge_camera, overview_camera, county_camera, low_camera, horizon_camera, backdrop]
        + ford_stones
        + landmarks
        + county
        + panorama
    )
    terrain.hide_render = False
    bpy.context.scene.world = None
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    contract = mesh_contract(terrain, landmark_stats)
    export_asset(terrain)
    write_contract(contract)
    print(json.dumps(contract, indent=2))


if __name__ == "__main__":
    import mathutils

    main()
