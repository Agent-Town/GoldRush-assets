"""Build the three remaining unique Epoch 1 contract terrain pilots.

The five maps share one regional art language, but never one terrain mesh.
This script authors Twin Banks, Night Shift, and the Baron as separate visual
heightfields with separate atlases and landmark compositions. Simulation,
collision, placement, water masks, and spawns remain planar and code-owned.
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

claim_spec = importlib.util.spec_from_file_location("unique_claim_helpers", OUT / "build_the_claim_terrain.py")
claim = importlib.util.module_from_spec(claim_spec)
claim_spec.loader.exec_module(claim)
claim.mathutils = mathutils

state_spec = importlib.util.spec_from_file_location("unique_state_helpers", OUT / "render_contract_theme_states.py")
state = importlib.util.module_from_spec(state_spec)
state_spec.loader.exec_module(state)
state.claim = claim

HALF = 32.0
SEGMENTS = 128
ATLAS_SIZE = 2048

# The baron beauty shift adds a lot of dark ink (blast pads, wreck margin, cold
# far bank), and the Grit Law grade normalises luminance GLOBALLY — so the
# player's own bank paid for the far bank going cold. Lifting only this
# contract's white point puts the home half back without softening the split.
# Scoped here on purpose: the shared GRIT_PROFILES table stays byte-identical.
claim.GRIT_PROFILES["baron"] = {**claim.GRIT_PROFILES["baron"], "white": 0.57}

PROFILES = {
    "twin-banks": {
        "stem": "twin-banks-terrain",
        "contractId": "e1-twin-banks",
        "tileId": "e1-twin-banks",
        "object": "TwinBanksTerrain",
        "mesh": "TwinBanksTerrainMesh",
        "material": "TwinBanksPaintedTerrainMaterial",
        "atlas": "TwinBanksPaintedTerrainAtlas",
        "theme": "broad-twin-settlement-floodplain",
        "waterMask": "z=-7.8..7.8 visual river; runtime water remains descriptor-owned",
        "fordMask": "two fords centered x=-16 and x=16, each halfWidth=3",
        "landmarks": ["opposing_bank_homesteads", "paired_winch_towers", "two_fords", "gravel_bars", "reed_corridor"],
        "mounts": [
            claim.landmark_mount("north_bank_homestead", 13.5, 14.2, -0.10),
            claim.landmark_mount("south_bank_homestead", -13.0, -14.0, 0.14),
            claim.landmark_mount("north_bank_winch", -16.0, 10.7),
            claim.landmark_mount("south_bank_winch", 16.0, -10.7),
            claim.landmark_mount("floodplain_dressing_pack", 0.0, 0.0),
        ],
    },
    "night-shift": {
        "stem": "night-shift-terrain",
        "contractId": "e1-night-shift",
        "tileId": "frontier-river-claim",
        "object": "NightShiftTerrain",
        "mesh": "NightShiftTerrainMesh",
        "material": "NightShiftPaintedTerrainMaterial",
        "atlas": "NightShiftPaintedTerrainAtlas",
        "theme": "dark-rock-lantern-work-corridor",
        "waterMask": "z=-5..5; shallows to +/-6.25",
        "fordMask": "x=-3..3 inside water band",
        "landmarks": ["seven_lantern_terraces", "lampworks_yard", "dark_rock_shoulders", "central_ford", "night_work_road"],
        "mounts": [
            claim.landmark_mount("seven_lantern_terraces", 0.0, 0.0),
            claim.landmark_mount("lampworks_yard", 8.0, 18.0, -0.12),
            claim.landmark_mount("dark_rock_shoulders", 0.0, 0.0),
            claim.landmark_mount("central_ford", 0.0, 0.0),
            claim.landmark_mount("night_work_road", 0.0, 0.0),
        ],
    },
    "baron": {
        "stem": "baron-terrain",
        "contractId": "e1-baron",
        "tileId": "frontier-river-claim",
        "object": "BaronTerrain",
        "mesh": "BaronTerrainMesh",
        "material": "BaronPaintedTerrainMaterial",
        "atlas": "BaronPaintedTerrainAtlas",
        "theme": "occupied-river-fortress",
        "waterMask": "z=-5..5; shallows to +/-6.25",
        "fordMask": "x=-3..3 inside water band",
        "landmarks": ["fortified_far_bank", "seized_headframe", "rocket_cart", "siege_line", "oxblood_banners"],
        "mounts": [
            claim.landmark_mount("fortified_far_bank", 0.0, -10.8),
            claim.landmark_mount("seized_headframe", -13.0, 13.0, 0.06, 1.20),
            claim.landmark_mount("rocket_cart", 12.5, 14.0),
            claim.landmark_mount("siege_line", 0.0, -7.4),
            claim.landmark_mount("oxblood_banners", 0.0, 0.0),
        ],
    },
}


def smoothstep(edge0, edge1, value):
    value = np.asarray(value, dtype=np.float32)
    t = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def gaussian(x, z, cx, cz, sx, sz):
    return np.exp(-(((x - cx) / sx) ** 2 + ((z - cz) / sz) ** 2) * 0.5)


def rotated_gaussian(x, z, cx, cz, sx, sz, angle):
    dx = x - cx
    dz = z - cz
    along = dx * math.cos(angle) + dz * math.sin(angle)
    across = -dx * math.sin(angle) + dz * math.cos(angle)
    return np.exp(-((along / sx) ** 2 + (across / sz) ** 2) * 0.5)


def segment_mask(x, z, ax, az, bx, bz, width):
    vx = bx - ax
    vz = bz - az
    length_squared = vx * vx + vz * vz
    t = np.clip(((x - ax) * vx + (z - az) * vz) / length_squared, 0.0, 1.0)
    distance = np.hypot(x - (ax + t * vx), z - (az + t * vz))
    return 1.0 - smoothstep(width * 0.55, width, distance)


def twin_height(x, z):
    """Wide floodplain with opposed, asymmetric settlement terraces."""
    x = np.asarray(x, dtype=np.float32)
    z = np.asarray(z, dtype=np.float32)
    ax = np.abs(x)
    az = np.abs(z)
    grain = np.sin(x * 0.16 + z * 0.09) * 0.035 + np.cos(x * 0.09 - z * 0.24) * 0.025

    water = 1.0 - smoothstep(7.55, 8.35, az)
    bank_step = 0.30 + smoothstep(8.0, 12.5, az) * 0.22
    outer = smoothstep(22.0, 32.0, az) * 0.52 + smoothstep(26.0, 32.0, ax) * 0.30

    # The banks rhyme, but one is a long agricultural shelf while the other
    # is divided into smaller damp hummocks. This is not a mirrored plate.
    north_shelf = rotated_gaussian(x, z, -3.0, 18.0, 22.0, 5.2, -0.04) * 0.34
    north_cut = rotated_gaussian(x, z, 11.5, 17.0, 8.5, 1.8, 0.12) * -0.16
    south_hummocks = (
        gaussian(x, z, -18.0, -17.0, 7.0, 4.8) * 0.34
        + gaussian(x, z, 9.0, -20.0, 8.5, 5.4) * 0.25
        + gaussian(x, z, 24.0, -15.0, 4.8, 6.0) * 0.31
    )
    land = bank_step + outer + north_shelf + north_cut + south_hummocks + grain

    # The only raised river crossings are the descriptor-owned twin fords.
    bars = (
        gaussian(x, z, -7.5, 0.2, 5.4, 1.35) * 0.17
        + gaussian(x, z, 7.4, -0.25, 4.8, 1.2) * 0.16
    )
    river_floor = -0.32 + bars + np.sin(x * 0.18) * 0.018
    west_ford = 1.0 - smoothstep(2.15, 3.0, np.abs(x + 16.0))
    east_ford = 1.0 - smoothstep(2.15, 3.0, np.abs(x - 16.0))
    ford = np.maximum(west_ford, east_ford) * water
    river_floor = river_floor * (1.0 - ford) + (-0.060 + grain * 0.2) * ford
    height = land * (1.0 - water) + river_floor * water

    # Broad calm shelves keep both build zones visually honest.
    north_apron = gaussian(x, z, 0.0, 15.0, 17.0, 7.0)
    south_apron = gaussian(x, z, 0.0, -14.5, 15.5, 6.5)
    calm = np.clip((north_apron + south_apron) * smoothstep(8.1, 10.5, az) * 0.72, 0.0, 0.82)
    calm_height = 0.48 + smoothstep(21.0, 30.0, az) * 0.18
    height = height * (1.0 - calm) + calm_height * calm

    # Two unmistakable levee families frame the settlements without turning
    # either build shelf into a uniform mound.
    levees = (
        rotated_gaussian(x, z, -23.0, 19.0, 4.8, 10.5, -0.14) * 0.92
        + rotated_gaussian(x, z, 24.0, 16.0, 4.4, 8.5, 0.11) * 0.70
        + rotated_gaussian(x, z, -24.0, -15.0, 4.6, 8.0, 0.13) * 0.66
        + rotated_gaussian(x, z, 21.0, -20.0, 5.4, 10.0, -0.16) * 0.98
    )
    terrace_edges = (
        np.exp(-((z - 21.0) / 1.35) ** 2) * 0.24
        + np.exp(-((z + 20.0) / 1.55) ** 2) * 0.20
    ) * (1.0 - smoothstep(22.0, 29.0, ax))
    height += levees * smoothstep(14.0, 22.0, ax) + terrace_edges
    return np.clip(height, -0.42, 2.42)


def night_height(x, z):
    """A narrow lantern corridor framed by old dark-rock workings."""
    x = np.asarray(x, dtype=np.float32)
    z = np.asarray(z, dtype=np.float32)
    ax = np.abs(x)
    az = np.abs(z)
    water = 1.0 - smoothstep(4.75, 6.25, az)
    grain = np.sin(x * 0.19 + z * 0.08) * 0.035 + np.cos(x * 0.11 - z * 0.26) * 0.024

    bank = 0.38 + smoothstep(6.0, 12.0, az) * 0.22
    side_shoulders = smoothstep(10.5, 25.0, ax) * 1.58
    hooked_ridges = (
        rotated_gaussian(x, z, -20.0, 9.0, 4.8, 13.0, -0.12) * 1.34
        + rotated_gaussian(x, z, 19.5, -8.0, 5.0, 14.0, 0.16) * 1.42
        + gaussian(x, z, -10.0, -27.0, 7.0, 4.5) * 0.72
        + gaussian(x, z, 11.0, -26.0, 7.0, 4.2) * 0.64
    )
    work_road = np.maximum(
        segment_mask(x, z, 0.0, 8.0, 0.0, 27.0, 2.8),
        np.maximum(
            segment_mask(x, z, -22.0, -12.0, -10.0, -24.0, 2.2),
            segment_mask(x, z, 22.0, -12.0, 10.0, -24.0, 2.2),
        ),
    )
    far_cut = rotated_gaussian(x, z, -1.0, -18.5, 17.0, 4.2, 0.02) * 0.56
    land = bank + side_shoulders + hooked_ridges + far_cut + grain - work_road * 0.10

    river_floor = -0.34 - (1.0 - smoothstep(1.7, 3.7, az)) * 0.13
    ford = (1.0 - smoothstep(2.15, 3.0, ax)) * water
    river_floor = river_floor * (1.0 - ford) + (-0.105 + grain * 0.18) * ford
    height = land * (1.0 - water) + river_floor * water

    # Each fixed lantern owns a small work terrace without creating a ledge in
    # the simulation. The terrain rhythm follows the contract's seven lights.
    lanterns = [(0, 16), (-16, 18), (16, 18), (-22, -12), (22, -12), (-10, -24), (10, -24)]
    terrace = np.zeros_like(height)
    for lx, lz in lanterns:
        terrace = np.maximum(terrace, gaussian(x, z, lx, lz, 3.2, 3.0))
    terrace *= smoothstep(6.4, 8.0, az)
    terrace_height = 0.54 + smoothstep(20.0, 30.0, ax) * 0.15
    height = height * (1.0 - terrace * 0.68) + terrace_height * terrace * 0.68
    return np.clip(height, -0.50, 3.18)


def baron_height(x, z):
    """Occupied river ground cut into a fortified far-bank hierarchy."""
    x = np.asarray(x, dtype=np.float32)
    z = np.asarray(z, dtype=np.float32)
    ax = np.abs(x)
    az = np.abs(z)
    water = 1.0 - smoothstep(4.75, 6.25, az)
    grain = np.sin(x * 0.15 + z * 0.10) * 0.04 + np.cos(x * 0.08 - z * 0.23) * 0.025

    bank = 0.37 + smoothstep(6.0, 12.0, az) * 0.25
    far_bank = smoothstep(7.0, 10.5, -z) * 0.48 + smoothstep(14.0, 18.0, -z) * 0.72
    far_plateau = rotated_gaussian(x, z, -2.0, -18.0, 24.0, 7.0, 0.02) * 0.76
    bastions = (
        gaussian(x, z, -23.0, -12.5, 5.5, 6.5) * 0.92
        + gaussian(x, z, 22.0, -13.0, 5.8, 6.2) * 0.88
        + gaussian(x, z, -15.0, -25.0, 8.0, 4.5) * 0.62
        + gaussian(x, z, 16.0, -25.0, 8.0, 4.5) * 0.66
    )
    siege_trench = np.exp(-((z + 9.5) / 1.1) ** 2) * (1.0 - smoothstep(20.0, 28.0, ax)) * 0.27
    near_scars = (
        rotated_gaussian(x, z, -13.0, 16.0, 8.0, 1.4, -0.22) * 0.12
        + rotated_gaussian(x, z, 12.0, 20.0, 7.0, 1.2, 0.18) * 0.10
    )
    land = bank + far_bank + far_plateau + bastions + grain - siege_trench - near_scars

    river_floor = -0.31 - (1.0 - smoothstep(1.65, 3.6, az)) * 0.17
    ford = (1.0 - smoothstep(2.15, 3.0, ax)) * water
    river_floor = river_floor * (1.0 - ford) + (-0.10 + grain * 0.15) * ford
    height = land * (1.0 - water) + river_floor * water

    # The heroine's approach remains a calm visual apron. The intimidating
    # relief belongs to the occupied far bank, not to an unreachable sniper perch.
    approach = gaussian(x, z, 0.0, 15.0, 10.0, 8.0) * smoothstep(6.4, 8.4, az)
    height = height * (1.0 - approach * 0.72) + (0.46 + grain * 0.3) * approach * 0.72
    return np.clip(height, -0.50, 3.46)


HEIGHT_FUNCTIONS = {"twin-banks": twin_height, "night-shift": night_height, "baron": baron_height}

EXTERIOR_PROFILES = {
    "twin-banks": {
        "halfWidth": 7.8,
        "cacti": [
            (-48.0, 15.0, 1.18, 1.0, 0.2),
            (-58.0, -17.0, 0.94, -1.0, -0.4),
            (-88.0, 32.0, 1.28, 1.0, 0.7),
            (46.0, 17.0, 1.12, -1.0, 0.5),
            (65.0, -19.0, 0.98, 1.0, -0.6),
            (91.0, -35.0, 1.24, -1.0, 0.9),
        ],
        "mesas": [(-112.0, 74.0, 15.0, 4.8), (118.0, 69.0, 17.0, 5.2), (-126.0, -72.0, 18.0, 5.6), (105.0, -80.0, 14.0, 4.6)],
        "outcrops": [(-48.0, 30.0, (2.4, 1.6, 1.1)), (52.0, -31.0, (2.7, 1.8, 1.2)), (79.0, 27.0, (1.8, 1.3, 0.9))],
        "signature": ["extra-wide floodplain", "paired outer-bank winches", "low opposed settlement shelves"],
    },
    "night-shift": {
        "halfWidth": 6.25,
        "cacti": [
            (-44.0, 15.0, 1.02, 1.0, 0.1),
            (-61.0, -22.0, 0.86, -1.0, -0.7),
            (47.0, 16.0, 1.08, -1.0, 0.5),
            (67.0, -24.0, 0.92, 1.0, -0.4),
        ],
        "mesas": [(-72.0, 46.0, 14.0, 8.0), (76.0, 44.0, 15.0, 8.8), (-102.0, -48.0, 17.0, 10.5), (104.0, -52.0, 18.0, 11.0)],
        "outcrops": [(-43.0, 25.0, (3.4, 2.2, 2.0)), (44.0, -25.0, (3.8, 2.5, 2.2)), (-67.0, -34.0, (4.2, 2.8, 2.5))],
        "signature": ["dark rock corridor", "outer lantern road", "distant lampworks stack"],
    },
    "baron": {
        "halfWidth": 6.25,
        "cacti": [
            (-46.0, 19.0, 1.06, 1.0, 0.3),
            (-64.0, 28.0, 0.88, -1.0, -0.5),
            (49.0, 18.0, 1.12, -1.0, 0.6),
            (72.0, 30.0, 0.94, 1.0, -0.8),
        ],
        "mesas": [(-88.0, -72.0, 19.0, 8.6), (91.0, -78.0, 21.0, 9.4), (-128.0, -42.0, 17.0, 7.5), (124.0, -45.0, 18.0, 8.0)],
        "outcrops": [(-45.0, 30.0, (2.8, 1.8, 1.4)), (47.0, 29.0, (3.0, 2.0, 1.5)), (-72.0, -31.0, (4.0, 2.7, 2.1))],
        "signature": ["fortified far-bank horizon", "paired outer watchtowers", "occupied extraction ridge"],
    },
}


def county_river_center(key, x):
    outside = max(0.0, abs(x) - HALF)
    if outside == 0.0:
        return 0.0
    side = -1.0 if x < 0.0 else 1.0
    delta = x - side * HALF
    ramp = float(smoothstep(0.0, 20.0, outside))
    if key == "twin-banks":
        return ramp * (math.sin(delta * 0.048) * 1.5 + math.sin(delta * 0.12) * 0.45)
    if key == "night-shift":
        return ramp * (math.sin(delta * 0.055) * 0.85 + math.sin(delta * 0.14) * 0.25)
    return ramp * (math.sin(delta * 0.050) * 1.2 + math.sin(delta * 0.105 + 0.8) * 0.42)


def county_half_width(key, x):
    base = EXTERIOR_PROFILES[key]["halfWidth"]
    outside = max(0.0, abs(x) - HALF)
    return base + float(smoothstep(12.0, 82.0, outside)) * math.sin(x * 0.075 + len(key)) * (0.7 if key == "twin-banks" else 0.42)


def county_height(key, x, game_z):
    """Contract-specific county relief blended from the fixed playable edge."""
    local = float(HEIGHT_FUNCTIONS[key](x, game_z))
    outside = max(0.0, abs(x) - HALF, abs(game_z) - HALF)
    if outside <= 0.0:
        return local

    center = county_river_center(key, x)
    distance = abs(game_z - center)
    half_width = county_half_width(key, x)
    river = 1.0 - float(smoothstep(half_width - 0.65, half_width + 1.05, distance))
    rolling = math.sin(x * 0.063 + game_z * 0.039) * 0.20 + math.sin(x * 0.131 - game_z * 0.051 + 0.7) * 0.11

    if key == "twin-banks":
        land = 0.38 + float(smoothstep(half_width, 29.0, distance)) * 0.78 + rolling
        land += float(smoothstep(76.0, 150.0, max(abs(x), abs(game_z)))) * 2.2
        land += float(gaussian(x, game_z, -92.0, 62.0, 26.0, 18.0)) * 1.1
        land += float(gaussian(x, game_z, 96.0, -67.0, 28.0, 19.0)) * 1.2
        bed = -0.34 + math.sin(x * 0.09) * 0.025
    elif key == "night-shift":
        land = 0.40 + float(smoothstep(half_width, 26.0, distance)) * 1.45 + rolling
        land += float(smoothstep(44.0, 128.0, abs(x))) * 4.2
        land += float(gaussian(x, game_z, -72.0, 43.0, 21.0, 18.0)) * 2.8
        land += float(gaussian(x, game_z, 78.0, -46.0, 23.0, 19.0)) * 3.1
        bed = -0.43 + math.sin(x * 0.12) * 0.02
    else:
        far_bank = float(smoothstep(8.0, 34.0, -game_z)) * 2.4
        land = 0.38 + float(smoothstep(half_width, 28.0, distance)) * 0.92 + far_bank + rolling
        land += float(gaussian(x, game_z, -88.0, -68.0, 31.0, 22.0)) * 2.4
        land += float(gaussian(x, game_z, 93.0, -74.0, 32.0, 23.0)) * 2.7
        bed = -0.39 + math.sin(x * 0.10) * 0.025

    target = land * (1.0 - river) + bed * river
    jitter = math.sin(x * 0.09 + game_z * 0.13) * 7.0 + math.sin(x * 0.20 - game_z * 0.07 + 1.2) * 3.5
    blend = float(smoothstep(5.0, 48.0, outside + jitter))
    return local * (1.0 - blend) + target * blend


def lattice_hash(cell_x, cell_z, seed):
    """Deterministic per-cell value noise in [0,1).

    No RNG anywhere in this file's paint path: the atlas has to re-export from
    the same source to the same picture, or the contract-equality gate becomes
    a coin toss (see reviews/beauty-baron.md, "the re-export is stable to +/-1 LSB").
    """
    value = np.sin(cell_x * 12.9898 + cell_z * 78.233 + seed) * 43758.5453
    return value - np.floor(value)


def scatter_dots(x, z, cell, seed, density, radius=0.34):
    """Round marks on a jittered lattice — stumps, embers, cut ends."""
    cell_x = np.floor(x / cell)
    cell_z = np.floor(z / cell)
    live = (lattice_hash(cell_x, cell_z, seed) < density).astype(np.float32)
    offset_x = 0.2 + lattice_hash(cell_x, cell_z, seed + 17.3) * 0.6
    offset_z = 0.2 + lattice_hash(cell_x, cell_z, seed + 41.7) * 0.6
    distance = np.hypot(x / cell - cell_x - offset_x, z / cell - cell_z - offset_z)
    return live * np.clip(1.0 - distance / radius, 0.0, 1.0)


def scatter_stakes(x, z, cell, seed, density, length=0.42, width=0.075):
    """Short leaning dashes — cut stakes and splinters, engraved not blobbed."""
    cell_x = np.floor(x / cell)
    cell_z = np.floor(z / cell)
    live = (lattice_hash(cell_x, cell_z, seed) < density).astype(np.float32)
    offset_x = 0.25 + lattice_hash(cell_x, cell_z, seed + 5.1) * 0.5
    offset_z = 0.25 + lattice_hash(cell_x, cell_z, seed + 9.7) * 0.5
    angle = lattice_hash(cell_x, cell_z, seed + 23.9) * math.pi
    local_x = x / cell - cell_x - offset_x
    local_z = z / cell - cell_z - offset_z
    along = local_x * np.cos(angle) + local_z * np.sin(angle)
    across = -local_x * np.sin(angle) + local_z * np.cos(angle)
    inside = np.clip(1.0 - np.abs(along) / length, 0.0, 1.0) * np.clip(1.0 - np.abs(across) / width, 0.0, 1.0)
    return live * np.clip(inside * 2.4, 0.0, 1.0)


def segment_frame(x, z, ax, az, bx, bz):
    """(metres along, metres across) for a segment, so a lane can carry its own ruts."""
    vx = bx - ax
    vz = bz - az
    length = math.hypot(vx, vz)
    t = np.clip(((x - ax) * vx + (z - az) * vz) / (length * length), 0.0, 1.0)
    across = (x - (ax + t * vx)) * (-vz / length) + (z - (az + t * vz)) * (vx / length)
    return t * length, across


# The finale's ground story, in map coordinates. Every number here is picture, not
# simulation: spawns, lanes, fords and the 22/22 battery never read this file.
BARON_CART_LANES = (
    (-15.5, -12.6, -2.7, -6.4),
    (2.4, -14.2, 0.5, -6.2),
    (14.5, -11.4, 2.7, -6.6),
)
# Rocket-impact pads on the PLAYER's bank — his volleys have landed here before,
# so wave 1 opens on ground that already lost an argument. Kept clear of the
# seized_headframe (-13,13) and rocket_cart (12.5,14) mounts.
BARON_IMPACT_PADS = (
    (-16.2, 8.2, 0.20),
    (-4.2, 16.4, -0.14),
    (8.8, 7.6, 0.08),
    (18.2, 19.4, -0.22),
    (-10.8, 24.6, 0.16),
    (4.6, 27.2, -0.10),
)


def paint_baron_ground(atlas, x, z, wash, rock, clean):
    """The Baron's finale plays on ground he already fought over once.

    Engraved, not airbrushed (Grit Law): every mark is a cut, a churn, a scorch
    or a stain, and the parchment warmth stays underneath all of it. Splinters,
    dust and embers at the impacts — never remains (ADR-001, brief section 3).
    Texture only; the heightfield, the water mask and the ford are untouched.
    """
    ax = np.abs(x)
    az = np.abs(z)
    char = rock * np.array((0.36, 0.26, 0.20), dtype=np.float32)
    soot = rock * np.array((0.20, 0.16, 0.14), dtype=np.float32)
    ash = wash * np.array((0.54, 0.48, 0.40), dtype=np.float32)
    ember = np.array((0.86, 0.44, 0.17), dtype=np.float32)
    mud = wash * np.array((0.42, 0.34, 0.25), dtype=np.float32)

    # The occupied far bank keeps its company rust and its siege trench.
    occupied = smoothstep(7.0, 24.0, -z)
    rust = wash * np.array((0.70, 0.39, 0.23), dtype=np.float32)
    atlas = atlas * (1.0 - occupied[..., None] * 0.34) + rust * occupied[..., None] * 0.34
    trench = np.exp(-((z + 9.5) / 1.18) ** 2) * (1.0 - smoothstep(20.0, 28.0, ax))
    atlas = atlas * (1.0 - trench[..., None] * 0.55) + char * trench[..., None] * 0.55

    # 1. CART-CHURNED LANES — the siege line feeds the ford. Three of them, each
    #    with its own wheel ruts, because an outfit this size does not march single
    #    file; they converge on the one crossing, which is the whole point of a ford.
    for index, (ax0, az0, bx0, bz0) in enumerate(BARON_CART_LANES):
        span = math.hypot(bx0 - ax0, bz0 - az0)
        along, across = segment_frame(x, z, ax0, az0, bx0, bz0)
        wander = np.sin(along * 0.62 + index * 2.4) * 0.55
        offset = across - wander
        body = np.clip(1.0 - np.abs(offset) / 1.85, 0.0, 1.0)
        body *= smoothstep(0.0, 1.4, along) * (1.0 - smoothstep(0.0, 1.8, along - span + 1.8))
        churn = np.clip((np.sin(along * 3.1 + offset * 1.5 + index) * 0.5 + 0.5) ** 2, 0.0, 1.0)
        lane = np.clip(body, 0.0, 1.0) ** 0.55 * (0.70 + churn * 0.30)
        atlas = atlas * (1.0 - lane[..., None] * 0.50) + mud * lane[..., None] * 0.50
        for side in (-1.0, 1.0):
            rut = np.clip(1.0 - np.abs(offset - side * 0.82) / 0.19, 0.0, 1.0) * body
            atlas *= 1.0 - rut[..., None] * 0.34
        hoof = scatter_dots(x, z, 0.72, 401.0 + index * 31.0, 0.26, 0.30) * body
        atlas *= 1.0 - hoof[..., None] * 0.18

    # 2. ROCKET-IMPACT PADS — a scoured core, a hard rim, ejecta rays thrown
    #    DOWNRANGE (away from the fort, so the direction reads as HIS shot), an
    #    ash lip and live embers. Struck, not smudged: the rim and the rays carry
    #    the read, the soft core only seats them in the dirt.
    for index, (pad_x, pad_z, yaw) in enumerate(BARON_IMPACT_PADS):
        dx = x - pad_x
        dz = z - pad_z
        radius = np.hypot(dx, dz)
        bearing = np.arctan2(dz, dx) - (math.pi * 0.5 + yaw)
        downrange = np.clip((np.cos(bearing) - 0.10) / 0.90, 0.0, 1.0)

        # A blast does not leave a compass rose. The rim wanders with bearing and
        # the whole pad is dragged downrange, so no two read as the same stamp.
        wobble = 1.0 + np.sin(bearing * 3.0 + index * 1.7) * 0.20 + np.sin(bearing * 7.0 - index) * 0.09
        scoured = radius / np.maximum(wobble, 0.4)
        core = np.clip(1.0 - smoothstep(0.72, 1.78, scoured), 0.0, 1.0)
        fan = np.clip(1.0 - smoothstep(1.4, 5.8, radius), 0.0, 1.0) * downrange ** 1.9
        atlas = atlas * (1.0 - core[..., None] * 0.74) + soot * core[..., None] * 0.74
        atlas = atlas * (1.0 - fan[..., None] * 0.40) + soot * fan[..., None] * 0.40

        rim = np.clip(1.0 - np.abs(scoured - 1.82) / 0.24, 0.0, 1.0) ** 0.7
        atlas *= 1.0 - rim[..., None] * 0.38
        # The thrown lip only banks up on the downrange side — the side the
        # charge pushed the dirt toward.
        lip = np.clip(1.0 - np.abs(scoured - 2.22) / 0.40, 0.0, 1.0) * (0.22 + downrange * 0.78)
        atlas = atlas * (1.0 - lip[..., None] * 0.58) + ash * lip[..., None] * 0.58

        for streak in range(5):
            angle = -0.95 + streak * 0.475 + math.sin(index * 2.3 + streak) * 0.16
            reach = 3.1 + math.sin(index * 1.9 + streak * 2.7) * 1.25
            offset = np.abs(np.mod(bearing - angle + math.pi, math.tau) - math.pi)
            ray = np.clip(1.0 - offset / (0.075 + radius * 0.012), 0.0, 1.0)
            ray *= smoothstep(1.7, 2.4, radius) * (1.0 - smoothstep(reach - 1.1, reach, radius))
            atlas = atlas * (1.0 - ray[..., None] * 0.44) + char * ray[..., None] * 0.44

        splinters = scatter_stakes(x, z, 0.95, 311.0 + index * 13.0, 0.34, 0.40, 0.075)
        splinters *= np.clip(1.0 - np.abs(radius - 3.3) / 2.6, 0.0, 1.0) * (0.25 + downrange * 0.75)
        atlas = atlas * (1.0 - splinters[..., None] * 0.48) + char * splinters[..., None] * 0.48

        heat = np.clip(core * 1.2 + fan * 0.9, 0.0, 1.0)
        speck = scatter_dots(x, z, 0.48, 907.0 + index * 29.0, 0.085, 0.34) * heat
        atlas = atlas * (1.0 - speck[..., None] * 0.62) + ember * speck[..., None] * 0.62

    # 3. THE WRECK MARGIN — where the fort ate the far bank: stumps cut at the
    #    knee and a scatter of driven stakes, thickest right behind the siege line.
    margin = np.clip(np.exp(-((z + 11.4) / 4.2) ** 2) * (1.0 - smoothstep(22.0, 29.0, ax)), 0.0, 1.0)
    margin = np.clip(margin * 1.35, 0.0, 1.0)
    stumps = scatter_dots(x, z, 1.55, 137.0, 0.30, 0.32) * margin
    atlas = atlas * (1.0 - stumps[..., None] * 0.60) + char * stumps[..., None] * 0.60
    cut_tops = scatter_dots(x, z, 1.55, 137.0, 0.30, 0.16) * margin
    atlas = atlas * (1.0 - cut_tops[..., None] * 0.52) + ash * cut_tops[..., None] * 0.52
    stakes = scatter_stakes(x, z, 1.10, 613.0, 0.34) * margin
    atlas = atlas * (1.0 - stakes[..., None] * 0.54) + char * stakes[..., None] * 0.54
    drag = np.clip(1.0 - np.abs(np.sin((z + 11.4) * 1.15 + np.sin(x * 0.21) * 0.9)) / 0.16, 0.0, 1.0) * margin
    atlas *= 1.0 - drag[..., None] * 0.16

    # 4. BANNER SHADOWS — his brand is printed on the dirt in front of the siege
    #    line long before you get close enough to read the cloth. Uneven lengths:
    #    a shadow rank that measures out evenly reads as a fence, not a company.
    banner_x = np.floor((x + 1.7) / 3.45)
    banner_len = 0.70 + lattice_hash(banner_x, np.zeros_like(banner_x), 71.0) * 0.95
    banner_lean = (lattice_hash(banner_x, np.zeros_like(banner_x), 133.0) - 0.5) * 0.55
    banner_row = np.clip(1.0 - np.abs(z + 6.35 - banner_lean * (x - banner_x * 3.45)) / banner_len, 0.0, 1.0)
    banner_row *= 1.0 - smoothstep(12.5, 14.4, ax)
    banner_beat = np.clip((np.sin((x + 1.7) * (math.tau / 3.45)) - 0.30) / 0.55, 0.0, 1.0) ** 1.3
    stain = banner_row * banner_beat
    atlas = atlas * (1.0 - stain[..., None] * 0.42) + soot * stain[..., None] * 0.42

    # 5. TWO SIDES, TWO LIGHTS — the duel has to be readable in one glance from
    #    the run camera: warm home parchment on the player's bank against cold
    #    company iron on his. The split is VALUE plus TEMPERATURE, never a second
    #    curtain of dark; the far bank still has to show what is standing on it.
    home = smoothstep(6.5, 15.0, z) * (1.0 - smoothstep(24.0, 30.0, az))
    # A multiply, not a mix: mixing toward a warm swatch DARKENED the home bank
    # (measured 51/73/66/63 -> 47/61/60/56 across the fresh-eye frame). Warm is a
    # direction, not a colour to average with.
    atlas *= 1.0 + home[..., None] * np.array((0.15, 0.075, -0.015), dtype=np.float32)

    company = smoothstep(5.8, 13.0, -z) * (1.0 - smoothstep(26.0, 31.5, ax))
    iron = wash * np.array((0.56, 0.62, 0.63), dtype=np.float32)
    atlas = atlas * (1.0 - company[..., None] * 0.34) + iron * company[..., None] * 0.34
    atlas *= 1.0 - (company * smoothstep(9.0, 22.0, -z))[..., None] * 0.06

    # 6. THE RIVER STOPS BEING A VOID. Measured before the change: the band paints
    #    at luminance 21/255 against banks at 107, so a quarter of every run frame
    #    was a black slab that swallowed the crossing the whole fight is about.
    #    Lifted toward READABLE DARK WATER with a cold bed under it, in the family
    #    of the Claim's bed treatment — bed detail and shallows, not a second live
    #    water surface. Runtime water classification is code-owned and untouched.
    river = 1.0 - smoothstep(5.0, 6.25, az)
    atlas = atlas * (1.0 + river[..., None] * 1.05)
    bed = rock * np.array((0.33, 0.35, 0.32), dtype=np.float32)
    atlas = atlas * (1.0 - river[..., None] * 0.28) + bed * river[..., None] * 0.28
    shallows = smoothstep(2.4, 4.9, az) * river
    pebbles = rock * np.array((0.54, 0.54, 0.43), dtype=np.float32)
    atlas = atlas * (1.0 - shallows[..., None] * 0.34) + pebbles * shallows[..., None] * 0.34
    # Engraved current, so the band reads as moving water at a glance.
    drift = np.clip((np.sin(x * 0.62 + np.sin(z * 0.9 + x * 0.11) * 1.5) - 0.55) / 0.45, 0.0, 1.0)
    drift *= river * (1.0 - smoothstep(3.6, 5.2, az))
    atlas = atlas * (1.0 - drift[..., None] * 0.20) + pebbles * drift[..., None] * 0.20
    # The crossing is wet SAND, not poured stone: the ford has to stay the one
    # warm thing in the cold band, because it is the only way across.
    crossing = (1.0 - smoothstep(2.2, 3.1, ax)) * (1.0 - smoothstep(4.6, 5.6, az))
    wet_sand = clean * np.array((0.86, 0.68, 0.44), dtype=np.float32)
    atlas = atlas * (1.0 - crossing[..., None] * 0.46) + wet_sand * crossing[..., None] * 0.46
    return atlas


# U5, night-shift beauty round 2. The seven lantern posts this map's style anchor is about,
# read straight off the landmark pack's authoredFixturePositions so the trampled pads cannot
# drift away from the fixtures they belong to.
NIGHT_LANTERNS = ((0.0, 16.0), (-16.0, 18.0), (16.0, 18.0), (-22.0, -12.0), (22.0, -12.0), (-10.0, -24.0), (10.0, -24.0))
# The mounted night_work_road body spans z -29.675..29.675 at |x| <= 2.1 (its GLB bounds), plus
# the two southern spurs the shipped paint already had. The shipped ribbon only covered z 8..27,
# so most of the mounted road lay on unprepared mud -- the "landmarks on a smear" the brief names.
NIGHT_ROAD_SEGMENTS = (
    ((0.0, -29.4), (0.0, 29.4), 2.7),
    ((-22.0, -12.0), (-10.0, -24.0), 2.2),
    ((22.0, -12.0), (10.0, -24.0), 2.2),
    ((-16.0, 18.0), (-2.0, 16.6), 1.9),
    ((16.0, 18.0), (2.0, 16.6), 1.9),
    ((-10.0, -24.0), (-1.6, -25.6), 1.8),
    ((10.0, -24.0), (1.6, -25.6), 1.8),
)
COAL_SEED = 20260803


def segment_fields(x, z, a, b):
    """Distance to a segment, and how far along it the nearest point lies, in metres."""
    (ax, az_), (bx, bz) = a, b
    vx, vz = bx - ax, bz - az_
    length = math.hypot(vx, vz)
    t = np.clip(((x - ax) * vx + (z - az_) * vz) / (length * length), 0.0, 1.0)
    return np.hypot(x - (ax + t * vx), z - (az_ + t * vz)), t * length


def worked_ground(atlas, x, z, az, clean, slate):
    """U5: put worked ground under the lanterns.

    The brief's read of this map was that the seven_lantern_terraces, the lampworks_yard and
    the night_work_road were "landmarks on a smear": the shipped atlas gave the road a soft
    brown wash over a fifth of its mounted length and gave the terraces nothing at all, so the
    seven amber pools of the style anchor landed on undifferentiated mud. This paints the use:
    a compacted pale ribbon with hatched shoulders along the whole mounted road, boot-trampled
    pads under each of the seven posts, and oil and coal at the lampworks.

    Everything here is atlas paint on the existing UVs -- the heightfield, its 16641 vertices
    and its bounds are untouched, so the runtime contract-equality gate never comes due.

    Two shipped things are deliberately protected. The dark_rock_shoulders stay the map's value
    anchors, so every mark is attenuated by the slate mask. And the river keeps its own paint:
    marks fade out across the water band and let the shipped ford own the crossing.
    """
    dry = smoothstep(5.0, 6.4, az)                       # river keeps its own paint
    anchored = (1.0 - slate * 0.66) * dry                # shoulders stay true value anchors

    # 1. THE RIBBON. A firm compacted core, a softer verge, and short perpendicular hatch ticks
    #    on the shoulders -- the engraved mark-making the brief asked for, not another airbrush.
    core = np.zeros_like(x)
    verge = np.zeros_like(x)
    hatch = np.zeros_like(x)
    for (start, end, width) in NIGHT_ROAD_SEGMENTS:
        distance, along = segment_fields(x, z, start, end)
        core = np.maximum(core, 1.0 - smoothstep(width * 0.62, width * 0.80, distance))
        verge = np.maximum(verge, 1.0 - smoothstep(width * 0.80, width * 1.45, distance))
        # Ticks live only just outside the core, and only where the road actually runs.
        band = (1.0 - smoothstep(width * 0.86, width * 1.30, distance)) * smoothstep(width * 0.74, width * 0.88, distance)
        # A ruler-regular tick every 1.25 m reads as machine work; drift the spacing and the
        # weight slowly along the road so it reads as a hand that got tired.
        drift = np.sin(along * 0.21 + 1.7) * 0.16
        ticks = np.clip((np.sin(along * (math.tau / 1.25) + drift * 6.0) - 0.42) / 0.58, 0.0, 1.0) ** 2
        hatch = np.maximum(hatch, band * ticks * (0.72 + np.sin(along * 0.37) * 0.28))
    core *= anchored
    verge *= anchored
    hatch *= anchored
    # Compaction is what makes a road read: boots and barrows press the ochre soil paler and
    # flatter than the ground beside it, so the ribbon is a LIFT, not another brown wash. The
    # shipped road only reached 82 against 54 off-road; this takes the core to about 100. A
    # first cut at 119 was reverted: chalk-white ground is the wrong answer on the map whose
    # standing complaint is that its amber pools already wash out to cream in the middle.
    compacted = clean * np.array((1.34, 1.22, 1.02), dtype=np.float32)
    atlas = atlas * (1.0 - verge[..., None] * 0.18) + compacted * verge[..., None] * 0.18
    atlas = atlas * (1.0 - core[..., None] * 0.45) + compacted * core[..., None] * 0.45
    atlas *= 1.0 - hatch[..., None] * 0.30

    # 2. THE PADS. Boot-trampled ground under each post: a pale scuffed disc with a darker
    #    kicked rim, so the amber pool has something deliberate to land on.
    pad = np.zeros_like(x)
    rim = np.zeros_like(x)
    for index, (px, pz) in enumerate(NIGHT_LANTERNS):
        distance = np.hypot(x - px, z - pz)
        radius = 2.45 + (index % 3) * 0.28                # the row was trodden by people, not stamped
        pad = np.maximum(pad, 1.0 - smoothstep(radius * 0.62, radius, distance))
        rim = np.maximum(rim, np.exp(-(((distance - radius * 0.94) / (radius * 0.20)) ** 2)))
    scuff = (np.sin(x * 2.9 + z * 1.7) * np.sin(z * 3.3 - x * 1.1) * 0.5 + 0.5) ** 2
    # Weight the pads toward their scuff rather than their value, so they read as ground that
    # was trodden rather than as a second coat of paint at the end of every spur.
    pad = pad * anchored * (0.55 + scuff * 0.45)
    rim = rim * anchored
    trodden = clean * np.array((1.32, 1.21, 1.00), dtype=np.float32)
    atlas = atlas * (1.0 - pad[..., None] * 0.40) + trodden * pad[..., None] * 0.40
    # A light kicked rim only. Weight it any harder and the pad reads as a ring, not as ground.
    atlas *= 1.0 - rim[..., None] * 0.13

    # 3. THE LAMPWORKS at (8, 18): what a lamp yard leaves on the ground. Oil goes on as a few
    #    unmatched slicks rather than one blob (the Echo law), coal as scattered chips downwind.
    oil = np.clip(
        rotated_gaussian(x, z, 6.4, 19.6, 1.9, 0.72, 0.42)
        + rotated_gaussian(x, z, 10.2, 16.8, 1.5, 0.60, -0.30)
        + rotated_gaussian(x, z, 8.9, 20.4, 1.1, 0.46, 0.95),
        0.0,
        1.0,
    ) * anchored
    slick = np.asarray((0.115, 0.108, 0.098), dtype=np.float32)
    atlas = atlas * (1.0 - oil[..., None] * 0.42) + slick[None, None, :] * oil[..., None] * 0.42

    # Coal is stamped into local patches, not evaluated over the whole 2048^2 grid per chip:
    # 240 full-atlas exponentials is a billion needless operations for marks 10 px across.
    rng = np.random.default_rng(COAL_SEED)
    coal = np.zeros_like(x)
    pixels_per_metre = ATLAS_SIZE / (HALF * 2.0)
    for _ in range(150):
        # A fan blown south-west off the yard: chips thin out with distance, never a tidy ring.
        angle = float(rng.normal(math.radians(215.0), 0.55))
        reach = float(abs(rng.normal(0.0, 3.6))) + 0.6
        cx = 8.0 + math.cos(angle) * reach
        cz = 18.0 + math.sin(angle) * reach
        radius = 0.10 + float(rng.random()) ** 2 * 0.20
        centre_col = (cx / (HALF * 2.0) + 0.5) * ATLAS_SIZE
        centre_row = (cz / (HALF * 2.0) + 0.5) * ATLAS_SIZE
        span = int(math.ceil(radius * pixels_per_metre * 2.6)) + 1
        col0, col1 = max(0, int(centre_col) - span), min(ATLAS_SIZE, int(centre_col) + span + 1)
        row0, row1 = max(0, int(centre_row) - span), min(ATLAS_SIZE, int(centre_row) + span + 1)
        if col0 >= col1 or row0 >= row1:
            continue
        patch_x = x[row0:row1, col0:col1]
        patch_z = z[row0:row1, col0:col1]
        chip_mask = np.exp(-(((patch_x - cx) ** 2 + (patch_z - cz) ** 2) / (radius * radius)))
        np.maximum(coal[row0:row1, col0:col1], chip_mask, out=coal[row0:row1, col0:col1])
    chip = np.asarray((0.085, 0.078, 0.074), dtype=np.float32)
    coal *= anchored
    atlas = atlas * (1.0 - coal[..., None] * 0.55) + chip[None, None, :] * coal[..., None] * 0.55
    return atlas


def shared_atlas_sources():
    return (
        claim.image_pixels(claim.BANK_A),
        claim.image_pixels(claim.BANK_B),
        claim.image_pixels(claim.BANK_C),
        claim.image_pixels(claim.RIVER),
    )


def make_atlas(key, profile):
    bank_a, bank_b, bank_c, river = shared_atlas_sources()
    axis = np.linspace(0.0, 1.0, ATLAS_SIZE, dtype=np.float32)
    u, v = np.meshgrid(axis, axis)
    x = (u - 0.5) * HALF * 2.0
    z = (v - 0.5) * HALF * 2.0
    ax = np.abs(x)
    az = np.abs(z)

    clean = claim.tiled_sample(bank_b, u, v, 3.25, 0.17, 0.31)
    rock = claim.tiled_sample(bank_c, u, v, 3.55, 0.61, 0.08)
    wash = claim.tiled_sample(bank_a, u, v, 2.25, 0.27, 0.49)
    macro = (np.sin(x * 0.15 + z * 0.10) * 0.5 + 0.5)[..., None]
    land = wash * (0.40 + macro * 0.06) + clean * 0.30 + rock * (0.30 - macro * 0.04)
    # This tint is shared by the whole region: ochre soil, rust, dusty umber.
    land *= np.array((1.01, 0.86, 0.67), dtype=np.float32)

    water = claim.tiled_sample(river, u, v, 2.55, 0.41, 0.13)
    water *= np.array((0.48, 0.43, 0.31), dtype=np.float32)
    water *= 1.0 - claim.engraved_ink(river, u, v, 2.55, 0.41, 0.13)[..., None] * 0.24
    foam = np.clip((np.sin(x * 0.40 + z * 1.34 + np.sin(x * 0.13) * 1.1) - 0.76) / 0.24, 0.0, 1.0) ** 2
    foam_color = rock * np.array((0.58, 0.53, 0.41), dtype=np.float32)
    water = water * (1.0 - foam[..., None] * 0.12) + foam_color * foam[..., None] * 0.12

    if key == "twin-banks":
        damp = 1.0 - smoothstep(7.5, 17.0, az)
        damp_land = land * np.array((0.62, 0.78, 0.54), dtype=np.float32)
        land = land * (1.0 - damp[..., None] * 0.34) + damp_land * damp[..., None] * 0.34
        # Broad, opposed furrow fields make the two-bank settlement visible
        # even before the temporary buildings are added. They are regional
        # ochre soil marks, not a new biome or a gameplay surface.
        field_envelope = np.clip(
            gaussian(x, z, -13.0, 19.0, 10.5, 4.8)
            + gaussian(x, z, 13.0, -18.0, 9.5, 4.4),
            0.0,
            1.0,
        )
        furrows = (np.sin((x + z * 0.16) * 1.32) * 0.5 + 0.5) ** 5
        furrow_color = land * np.array((0.67, 0.57, 0.39), dtype=np.float32)
        furrow_mask = field_envelope * furrows * smoothstep(9.0, 12.5, az)
        land = land * (1.0 - furrow_mask[..., None] * 0.24) + furrow_color * furrow_mask[..., None] * 0.24
        flood_drag = np.clip(
            rotated_gaussian(x, z, -4.0, 10.0, 22.0, 0.28, 0.04)
            + rotated_gaussian(x, z, 5.0, -10.2, 20.0, 0.25, -0.05),
            0.0,
            1.0,
        )
        bank_stain = wash * np.array((0.36, 0.31, 0.20), dtype=np.float32)
        land = land * (1.0 - flood_drag[..., None] * 0.40) + bank_stain * flood_drag[..., None] * 0.40
        bars = np.clip(
            gaussian(x, z, -7.5, 0.2, 5.4, 1.35) + gaussian(x, z, 7.4, -0.25, 4.8, 1.2),
            0.0,
            1.0,
        )
        wet_gravel = rock * np.array((0.75, 0.78, 0.62), dtype=np.float32)
        water = water * (1.0 - bars[..., None] * 0.58) + wet_gravel * bars[..., None] * 0.58
        water_mask = 1.0 - smoothstep(7.55, 8.25, az)
        atlas = land * (1.0 - water_mask[..., None]) + water * water_mask[..., None]
        ford_x = np.maximum(1.0 - smoothstep(2.2, 3.0, np.abs(x + 16.0)), 1.0 - smoothstep(2.2, 3.0, np.abs(x - 16.0)))
        ford = ford_x * (1.0 - smoothstep(7.2, 7.75, az))
        atlas = atlas * (1.0 - ford[..., None] * 0.35) + clean * ford[..., None] * 0.35
        bank_line = np.exp(-((az - 7.8) / 0.44) ** 2)[..., None]
        atlas *= 1.0 - bank_line * 0.15
    else:
        water_mask = 1.0 - smoothstep(5.0, 6.25, az)
        deep = 1.0 - smoothstep(1.6, 3.7, az)
        water = water * (1.0 - deep[..., None] * 0.48) + water * np.array((0.39, 0.40, 0.30)) * deep[..., None] * 0.48
        atlas = land * (1.0 - water_mask[..., None]) + water * water_mask[..., None]
        ford = (1.0 - smoothstep(2.15, 3.0, ax)) * (1.0 - smoothstep(4.8, 5.35, az))
        atlas = atlas * (1.0 - ford[..., None] * 0.36) + clean * ford[..., None] * 0.36
        bank_line = np.exp(-((az - 5.5) / 0.42) ** 2)[..., None]
        atlas *= 1.0 - bank_line * 0.16

        if key == "night-shift":
            slate = np.clip(
                smoothstep(15.0, 28.0, ax)
                + gaussian(x, z, -10.0, -27.0, 7.5, 4.5)
                + gaussian(x, z, 11.0, -26.0, 7.0, 4.2),
                0.0,
                1.0,
            )
            slate_land = wash * np.array((0.32, 0.34, 0.35), dtype=np.float32)
            atlas = atlas * (1.0 - slate[..., None] * 0.54) + slate_land * slate[..., None] * 0.54
            road = np.maximum(
                segment_mask(x, z, 0.0, 8.0, 0.0, 27.0, 2.8),
                np.maximum(
                    segment_mask(x, z, -22.0, -12.0, -10.0, -24.0, 2.2),
                    segment_mask(x, z, 22.0, -12.0, 10.0, -24.0, 2.2),
                ),
            )
            road_color = wash * np.array((0.66, 0.52, 0.34), dtype=np.float32)
            atlas = atlas * (1.0 - road[..., None] * 0.32) + road_color * road[..., None] * 0.32
            soot_pockets = np.clip(
                gaussian(x, z, -16.0, 18.0, 4.5, 3.8)
                + gaussian(x, z, 16.0, 18.0, 4.5, 3.8)
                + gaussian(x, z, -10.0, -24.0, 4.0, 3.4)
                + gaussian(x, z, 10.0, -24.0, 4.0, 3.4),
                0.0,
                1.0,
            )
            atlas *= 1.0 - soot_pockets[..., None] * 0.30
            atlas = worked_ground(atlas, x, z, az, clean, slate)
        else:
            atlas = paint_baron_ground(atlas, x, z, wash, rock, clean)

    edge = smoothstep(28.0, 31.8, np.maximum(ax, az))[..., None]
    parchment = claim.tiled_sample(wash, u, v, 1.42, 0.31, 0.18) * np.array((0.75, 0.60, 0.41), dtype=np.float32)
    atlas = atlas * (1.0 - edge * 0.68) + parchment * edge * 0.68
    atlas = claim.apply_grit_grade(atlas, bank_a, u, v, key)

    rgba = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    rgba[:, :, :3] = atlas
    path = OUT / f"{profile['stem']}-atlas.png"
    image = bpy.data.images.new(profile["atlas"], ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image


def make_terrain(key, profile, material):
    height_function = HEIGHT_FUNCTIONS[key]
    vertices = []
    uvs = []
    faces = []
    for zi in range(SEGMENTS + 1):
        game_z = -HALF + HALF * 2.0 * zi / SEGMENTS
        for xi in range(SEGMENTS + 1):
            x = -HALF + HALF * 2.0 * xi / SEGMENTS
            vertices.append((x, -game_z, float(height_function(x, game_z))))
            uvs.append((xi / SEGMENTS, zi / SEGMENTS))
    row = SEGMENTS + 1
    for zi in range(SEGMENTS):
        for xi in range(SEGMENTS):
            a = zi * row + xi
            b = a + 1
            c = a + row
            d = c + 1
            faces.extend(((a, d, b), (a, c, d)))
    mesh = bpy.data.meshes.new(profile["mesh"])
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        polygon.use_smooth = True
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = uvs[vertex_index]
    terrain = bpy.data.objects.new(profile["object"], mesh)
    bpy.context.collection.objects.link(terrain)
    mesh.materials.append(material)
    terrain["render_only"] = True
    terrain["sim_surface"] = "planar"
    terrain["height_socket"] = "Terrain.visualY"
    terrain["contract_id"] = profile["contractId"]
    terrain["tile_id"] = profile["tileId"]
    terrain["water_mask"] = profile["waterMask"]
    terrain["ford_mask"] = profile["fordMask"]
    terrain["regional_family"] = "Epoch 1 frontier river county"
    terrain["identity_rule"] = "unique mesh, atlas, macro silhouette, and landmark composition"
    return terrain


def regional_materials(prefix):
    return {
        "timber": claim.make_render_material(f"{prefix}DarkTimber", (0.18, 0.085, 0.03)),
        "wood": claim.make_render_material(f"{prefix}WeatheredWood", (0.30, 0.14, 0.045)),
        "fresh": claim.make_render_material(f"{prefix}ExposedWood", (0.44, 0.23, 0.065)),
        "rust": claim.make_render_material(f"{prefix}RustIron", (0.29, 0.14, 0.055), 0.72, 0.24),
        "iron": claim.make_render_material(f"{prefix}DarkIron", (0.075, 0.065, 0.052), 0.66, 0.40),
        "stone": claim.make_render_material(f"{prefix}FrontierStone", (0.24, 0.23, 0.18)),
        "canvas": claim.make_render_material(f"{prefix}StainedCanvas", (0.43, 0.30, 0.14)),
        "reed": claim.make_render_material(f"{prefix}Reeds", (0.30, 0.39, 0.10)),
        "cactus": claim.make_render_material(f"{prefix}Cactus", (0.075, 0.22, 0.07)),
        "cactus_light": claim.make_render_material(f"{prefix}CactusSun", (0.14, 0.32, 0.10)),
    }


def add_county_a_frame(name, x, game_z, height_at, materials, scale=1.0):
    base = height_at(x, game_z)
    objects = [
        claim.add_beam(f"{name}.legWest", (x - 1.8 * scale, game_z, base), (x - 0.65 * scale, game_z, base + 5.0 * scale), 0.22 * scale, materials["timber"]),
        claim.add_beam(f"{name}.legEast", (x + 1.8 * scale, game_z, base), (x + 0.65 * scale, game_z, base + 5.0 * scale), 0.22 * scale, materials["timber"]),
        claim.add_beam(f"{name}.crossbar", (x - 0.85 * scale, game_z, base + 4.85 * scale), (x + 0.85 * scale, game_z, base + 4.85 * scale), 0.20 * scale, materials["wood"]),
    ]
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.62 * scale,
        minor_radius=0.09 * scale,
        major_segments=14,
        minor_segments=5,
        location=(x, -game_z, base + 3.95 * scale),
        rotation=(math.pi / 2.0, 0.0, 0.0),
    )
    wheel = bpy.context.object
    wheel.name = f"{name}.wheel"
    wheel.data.materials.append(materials["iron"])
    objects.append(wheel)
    return objects


def add_county_watchtower(name, x, game_z, height_at, materials, scale=1.0):
    base = height_at(x, game_z)
    objects = []
    for index, (dx, dz) in enumerate([(-1.0, -0.9), (1.0, -0.9), (-1.0, 0.9), (1.0, 0.9)]):
        objects.append(
            claim.add_beam(
                f"{name}.leg.{index}",
                (x + dx * scale, game_z + dz * scale, base),
                (x + dx * 0.62 * scale, game_z + dz * 0.62 * scale, base + 4.2 * scale),
                0.20 * scale,
                materials["timber"],
            )
        )
    objects.append(claim.add_box_game(f"{name}.deck", x, game_z, base + 3.8 * scale, (3.0 * scale, 2.7 * scale, 0.28 * scale), materials["wood"]))
    return objects


def add_county_horizon(key, height_at, materials):
    objects = []
    if key == "twin-banks":
        objects.extend(add_county_a_frame("RenderHelperTwinCountyWinch.north", -62.0, 23.0, height_at, materials, 0.95))
        objects.extend(add_county_a_frame("RenderHelperTwinCountyWinch.south", 64.0, -22.0, height_at, materials, 0.88))
    elif key == "night-shift":
        lens = state.make_emissive_material("RenderHelperNightCountyLens", (0.12, 0.27, 0.66), 3.2)
        for index, (x, game_z) in enumerate([(-27.0, -47.0), (0.0, -52.0), (29.0, -48.0)]):
            base = height_at(x, game_z)
            objects.append(claim.add_beam(f"RenderHelperNightCountyLamp.{index}.post", (x, game_z, base), (x, game_z, base + 4.2), 0.12, materials["iron"]))
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.34, location=(x, -game_z, base + 4.2))
            bulb = bpy.context.object
            bulb.name = f"RenderHelperNightCountyLamp.{index}.lens"
            bulb.data.materials.append(lens)
            objects.append(bulb)
        stack_x, stack_z = 61.0, 31.0
        stack_base = height_at(stack_x, stack_z)
        objects.append(claim.add_cylinder_between("RenderHelperNightCountyStack", (stack_x, stack_z, stack_base), (stack_x, stack_z, stack_base + 7.2), 0.46, materials["rust"], vertices=12))
    else:
        objects.extend(add_county_watchtower("RenderHelperBaronCountyTower.west", -58.0, -39.0, height_at, materials, 1.05))
        objects.extend(add_county_watchtower("RenderHelperBaronCountyTower.east", 59.0, -41.0, height_at, materials, 1.12))
        for index, x in enumerate(np.linspace(-42.0, 42.0, 9)):
            base = height_at(float(x), -42.0)
            objects.append(claim.add_box_game(f"RenderHelperBaronCountyPalisade.{index}", float(x), -42.0, base, (0.42, 0.42, 3.2 + (index % 3) * 0.35), materials["timber"]))
    return objects


def make_county_surround(key, atlas):
    profile = EXTERIOR_PROFILES[key]
    prefix = PROFILES[key]["object"]
    height_at = lambda x, game_z: county_height(key, x, game_z)
    materials = regional_materials(f"{prefix}County")
    ground_material = claim.make_claim_county_material(atlas, f"RenderHelper{prefix}CountyPaint")
    if key == "night-shift":
        water_material = claim.make_water_material(
            f"RenderHelper{prefix}CountyWater",
            dark=(0.008, 0.007, 0.005),
            light=(0.045, 0.032, 0.016),
            roughness=0.50,
        )
    else:
        water_material = claim.make_water_material(f"RenderHelper{prefix}CountyWater")
    objects = [claim.make_county_ground(f"RenderHelper{prefix}CountyGround", height_at, ground_material)]
    objects.extend(
        claim.make_county_water_ribbon(
            f"RenderHelper{prefix}CountyRiver",
            lambda x: county_river_center(key, x),
            profile["halfWidth"],
            water_material,
            half_width_at=lambda x: county_half_width(key, x),
        )
    )
    for index, (x, game_z, scale, flip, yaw) in enumerate(profile["cacti"]):
        objects.extend(claim.make_cactus(f"RenderHelper{prefix}CountyCactus.{index}", x, game_z, scale, materials, flip, yaw, height_at=height_at))
    for index, (x, game_z, radius, depth) in enumerate(profile["mesas"]):
        objects.extend(
            claim.add_county_mesa(
                f"RenderHelper{prefix}CountyMesa.{index}",
                x,
                game_z,
                radius,
                depth,
                materials["stone"],
                7 + index % 2,
                height_at=height_at,
            )
        )
    for index, (x, game_z, scale) in enumerate(profile["outcrops"]):
        objects.append(claim.add_county_rock(f"RenderHelper{prefix}CountyOutcrop.{index}", x, game_z, scale, materials["stone"], index * 0.57, height_at=height_at))
    objects.extend(add_county_horizon(key, height_at, materials))
    meshes = [obj for obj in objects if obj.type == "MESH"]
    triangles = sum(sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons) for obj in meshes)
    return objects, {
        "exported": False,
        "purpose": "owner exterior verdict only; runtime vista remains code-owned",
        "radiusMeters": claim.COUNTY_RADIUS,
        "objects": len(objects),
        "approxTriangles": triangles,
        "regionalGrammar": ["ochre river county", "faceted desert geology", "cacti only", "hard-used extraction scars"],
        "contractSignature": profile["signature"],
    }


def add_fence(name, points, materials):
    objects = []
    for index, (x, z) in enumerate(points):
        ground = float(claim.terrain_height(x, z))
        objects.append(claim.add_box_game(f"{name}.post.{index}", x, z, ground, (0.16, 0.16, 1.25), materials["timber"]))
    for index, ((ax, az), (bx, bz)) in enumerate(zip(points, points[1:])):
        ah = float(claim.terrain_height(ax, az)) + 0.68
        bh = float(claim.terrain_height(bx, bz)) + 0.68
        objects.append(claim.add_beam(f"{name}.rail.{index}", (ax, az, ah), (bx, bz, bh), 0.12, materials["wood"]))
    return objects


def add_winch_tower(name, x, z, face, materials):
    objects = []
    ground = float(claim.terrain_height(x, z))
    for index, dx in enumerate((-1.0, 1.0)):
        objects.append(claim.add_beam(f"{name}.leg.{index}", (x + dx * 2.15, z, ground), (x + dx * 1.04, z, ground + 6.65), 0.36, materials["timber"]))
    objects.append(claim.add_beam(f"{name}.cross", (x - 1.75, z, ground + 6.48), (x + 1.75, z, ground + 6.48), 0.38, materials["wood"]))
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=1.28,
        depth=0.58,
        location=(x, -z, ground + 2.00),
        rotation=(math.pi / 2.0, 0.0, 0.0),
    )
    drum = bpy.context.object
    drum.name = f"{name}.drum"
    drum.data.materials.append(materials["rust"])
    objects.append(drum)
    objects.append(claim.add_box_game(f"{name}.handle", x + 1.48 * face, z, ground + 1.96, (1.55, 0.15, 0.15), materials["iron"]))
    bpy.ops.mesh.primitive_torus_add(major_radius=1.12, minor_radius=0.14, major_segments=20, minor_segments=6, location=(x, -z, ground + 5.08), rotation=(math.pi / 2.0, 0.0, 0.0))
    pulley = bpy.context.object
    pulley.name = f"{name}.pulley"
    pulley.data.materials.append(materials["iron"])
    objects.append(pulley)
    return objects


def add_irrigation_rows(name, center_x, center_z, width, row_count, yaw, materials):
    """Low earthen furrows: readable parcel rhythm, never exported collision."""
    objects = []
    direction_x, direction_z = math.cos(yaw), math.sin(yaw)
    across_x, across_z = -direction_z, direction_x
    for row in range(row_count):
        offset = (row - (row_count - 1) * 0.5) * 1.15
        for segment in range(4):
            start_t = -width * 0.5 + segment * width / 4.0
            end_t = -width * 0.5 + (segment + 1) * width / 4.0
            ax = center_x + direction_x * start_t + across_x * offset
            az = center_z + direction_z * start_t + across_z * offset
            bx = center_x + direction_x * end_t + across_x * offset
            bz = center_z + direction_z * end_t + across_z * offset
            ah = float(claim.terrain_height(ax, az)) + 0.08
            bh = float(claim.terrain_height(bx, bz)) + 0.08
            objects.append(claim.add_beam(f"{name}.{row}.{segment}", (ax, az, ah), (bx, bz, bh), 0.10, materials["furrow"]))
    return objects


def add_wet_gravel_bar(name, x, z, length, width, yaw, materials):
    """Irregular wet stones inside the water mask, never a fake dry island."""
    objects = []
    for index, offset in enumerate((-0.34, 0.0, 0.31)):
        local_x = math.cos(yaw) * length * offset
        local_z = math.sin(yaw) * length * offset
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=2,
            radius=1.0,
            location=(x + local_x, -(z + local_z), 0.018 + index * 0.006),
            rotation=(0.12, -0.08, yaw + index * 0.21),
        )
        bar = bpy.context.object
        bar.name = f"{name}.mass.{index}"
        bar.scale = (length * (0.26 if index != 1 else 0.34), width * (0.58 if index != 1 else 0.72), 0.10)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bar.data.materials.append(materials["gravel"])
        objects.append(bar)
    for index in range(7):
        along = (index - 3) / 3.0
        cross = (-0.34 if index % 2 else 0.28) * width
        rx = x + math.cos(yaw) * along * length * 0.42 - math.sin(yaw) * cross
        rz = z + math.sin(yaw) * along * length * 0.42 + math.cos(yaw) * cross
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=(rx, -rz, 0.10 + (index % 3) * 0.025))
        stone = bpy.context.object
        stone.name = f"{name}.stone.{index}"
        stone.scale = (0.48 + (index % 2) * 0.18, 0.34 + (index % 3) * 0.08, 0.20)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        stone.data.materials.append(materials["stone"])
        objects.append(stone)
    return objects


def add_simple_shed(name, x, z, width, depth, materials, yaw=0.0):
    ground = float(claim.terrain_height(x, z))
    objects = [
        claim.add_box_game(f"{name}.foundation", x, z, ground - 0.02, (width + 0.24, depth + 0.24, 0.20), materials["timber"], yaw=yaw, bevel=0.01),
        claim.add_box_game(f"{name}.body", x, z, ground, (width, depth, 1.75), materials["wood"], yaw=yaw, tilt=(0.0, 0.018)),
    ]
    roof = claim.add_roof_prism(f"{name}.roof", x, z, ground + 1.75, width + 0.45, depth + 0.35, 0.85, materials["rust"], yaw)
    roof.rotation_euler.y += 0.025
    objects.append(roof)

    front_z = depth * 0.5 + 0.07
    for index, offset in enumerate((-0.38, -0.12, 0.16, 0.39)):
        local_x = offset * width
        board_x, board_z = claim.local_point(x, z, local_x, front_z, yaw)
        height = 1.50 - (index % 3) * 0.13
        lean = (-0.045, 0.025, -0.018, 0.055)[index]
        objects.append(claim.add_box_game(f"{name}.repair.{index}", board_x, board_z, ground + 0.10, (0.15, 0.10, height), materials["timber"], yaw=yaw + lean, tilt=(0.0, lean), bevel=0.006))

    door_x, door_z = claim.local_point(x, z, width * 0.18, front_z + 0.02, yaw)
    objects.append(claim.add_box_game(f"{name}.door", door_x, door_z, ground + 0.08, (width * 0.24, 0.11, 1.42), materials["timber"], yaw=yaw - 0.035, tilt=(0.0, -0.035), bevel=0.01))
    brace_a = claim.local_point(x, z, -width * 0.42, front_z + 0.04, yaw)
    brace_b = claim.local_point(x, z, width * 0.05, front_z + 0.04, yaw)
    objects.append(claim.add_beam(f"{name}.brokenBrace", (brace_a[0], brace_a[1], ground + 0.22), (brace_b[0], brace_b[1], ground + 1.45), 0.10, materials["timber"]))

    patch_x, patch_z = claim.local_point(x, z, -width * 0.20, -depth * 0.08, yaw)
    objects.append(claim.add_box_game(f"{name}.roofPatch", patch_x, patch_z, ground + 2.02, (width * 0.24, depth * 0.38, 0.06), materials["iron"], yaw=yaw + 0.06, tilt=(0.0, -0.38), bevel=0.005))
    for index, local_x in enumerate((-width * 0.31, width * 0.30)):
        seam_x, seam_z = claim.local_point(x, z, local_x, 0.0, yaw)
        objects.append(claim.add_box_game(f"{name}.roofSeam.{index}", seam_x, seam_z, ground + 2.00, (0.10, depth + 0.20, 0.06), materials["timber"], yaw=yaw, tilt=(0.0, -0.37 if local_x < 0 else 0.37), bevel=0.004))
    for index, (local_x, local_z) in enumerate([(-width * 0.58, depth * 0.20), (width * 0.52, -depth * 0.32)]):
        debris_x, debris_z = claim.local_point(x, z, local_x, local_z, yaw)
        debris_ground = float(claim.terrain_height(debris_x, debris_z))
        objects.append(claim.add_box_game(f"{name}.debris.{index}", debris_x, debris_z, debris_ground + 0.03, (width * 0.20, 0.12, 0.10), materials["wood"], yaw=yaw + (0.32 if index else -0.24), bevel=0.004))
    return objects


def add_regional_rocks(key, materials, count, avoid_water):
    seed = {"twin-banks": 71411, "night-shift": 71412, "baron": 71413}[key]
    rng = np.random.default_rng(seed)
    objects = []
    placed = []
    while len(placed) < count:
        x = float(rng.uniform(-28.5, 28.5))
        z = float(rng.uniform(-27.5, 27.5))
        if abs(z) < avoid_water or abs(x) < 8.0 and z > 8.0:
            continue
        if any((x - px) ** 2 + (z - pz) ** 2 < 3.0**2 for px, pz in placed):
            continue
        placed.append((x, z))
        scale = float(rng.uniform(0.35, 0.95))
        objects.append(claim.add_rock(f"RenderHelper{key}Rock.{len(placed):02d}", x, z, (scale, scale * 0.72, scale * 0.58), materials["stone"], float(rng.uniform(-1.0, 1.0))))
    return objects


def make_twin_preview(terrain_material):
    materials = regional_materials("TwinBanks")
    materials["water"] = claim.make_water_material()
    materials["gravel"] = claim.make_render_material("TwinBanksWetGravel", (0.25, 0.30, 0.23))
    materials["furrow"] = claim.make_render_material("TwinBanksFurrowSoil", (0.22, 0.105, 0.035))
    objects = [state.make_water_surface(7.8, materials["water"])]
    objects.extend(state.make_ford_stones(-16.0, terrain_material))
    objects.extend(state.make_ford_stones(16.0, terrain_material))
    objects.extend(add_wet_gravel_bar("RenderHelperTwinBanksWestBar", -7.5, 0.2, 5.4, 1.35, -0.12, materials))
    objects.extend(add_wet_gravel_bar("RenderHelperTwinBanksEastBar", 7.4, -0.25, 4.8, 1.2, 0.16, materials))
    objects.extend(state.make_stake("RenderHelperTwinBanksSouthStake", 0.0, -12.0, {"timber": materials["timber"], "board": materials["fresh"]}))
    objects.extend(state.make_stake("RenderHelperTwinBanksNorthMarker", 0.0, 12.0, {"timber": materials["timber"], "board": materials["fresh"]}))

    objects.extend(add_winch_tower("RenderHelperTwinBanksNorthWinch", -16.0, 10.7, 1.0, materials))
    objects.extend(add_winch_tower("RenderHelperTwinBanksSouthWinch", 16.0, -10.7, -1.0, materials))
    objects.extend(add_simple_shed("RenderHelperTwinBanksNorthShed", 13.5, 14.2, 8.5, 5.8, materials, -0.10))
    objects.extend(add_simple_shed("RenderHelperTwinBanksNorthOutbuilding", 22.0, 16.0, 4.4, 3.2, materials, 0.14))
    objects.extend(add_simple_shed("RenderHelperTwinBanksSouthShed", -13.0, -14.0, 8.0, 5.4, materials, 0.14))
    objects.extend(add_simple_shed("RenderHelperTwinBanksSouthOutbuilding", -22.0, -16.5, 4.1, 3.1, materials, -0.12))
    objects.extend(add_irrigation_rows("RenderHelperTwinBanksNorthFurrows", -12.0, 20.0, 15.0, 6, -0.08, materials))
    objects.extend(add_irrigation_rows("RenderHelperTwinBanksSouthFurrows", 12.0, -19.0, 14.0, 5, 0.12, materials))
    objects.extend(add_fence("RenderHelperTwinBanksNorthParcel", [(-23, 14), (-16, 15), (-9, 15)], materials))
    objects.extend(add_fence("RenderHelperTwinBanksNorthParcelEast", [(9, 16), (17, 15), (24, 14)], materials))
    objects.extend(add_fence("RenderHelperTwinBanksSouthParcel", [(-24, -15), (-17, -16), (-9, -16)], materials))
    objects.extend(add_fence("RenderHelperTwinBanksSouthParcelEast", [(9, -15), (17, -16), (24, -15)], materials))

    reed_positions = [(-28, -8.5), (-24, 8.4), (-19, -8.4), (-13, 8.5), (-5, -8.3), (4, 8.4), (11, -8.5), (19, 8.4), (24, -8.4), (28, 8.5)]
    for index, (x, z) in enumerate(reed_positions):
        objects.extend(claim.make_reed_cluster(f"RenderHelperTwinBanksReed.{index}", x, z, 0.9 + (index % 3) * 0.12, materials))
    for index, (x, z, scale, flip, yaw) in enumerate(
        [(-27, 12, 1.05, 1.0, 0.2), (25, -12, 0.92, -1.0, -0.4), (22, 18, 0.82, 1.0, 0.7), (-22, -19, 0.88, -1.0, -0.6)]
    ):
        objects.extend(claim.make_cactus(f"RenderHelperTwinBanksCactus.{index}", x, z, scale, materials, flip, yaw))
    objects.extend(add_regional_rocks("twin-banks", materials, 9, 9.0))
    return objects


def add_lampworks_yard(materials):
    objects = []
    x, z = 8.0, 18.0
    ground = float(claim.terrain_height(x, z))
    objects.append(claim.add_box_game("RenderHelperNightLampworks.deck", x, z, ground, (8.4, 5.4, 0.24), materials["timber"], yaw=-0.12))
    objects.extend(add_simple_shed("RenderHelperNightLampworks.shed", x + 0.8, z + 0.3, 6.2, 3.8, materials, -0.12))
    # Tall lamp-oil condenser gives the contract one readable industrial
    # silhouette instead of asking seven tiny posts to carry the whole scene.
    stack_x, stack_z = x - 2.8, z + 0.4
    stack_ground = float(claim.terrain_height(stack_x, stack_z))
    objects.append(claim.add_cylinder_between("RenderHelperNightLampworks.stack", (stack_x, stack_z, stack_ground), (stack_x, stack_z, stack_ground + 5.8), 0.42, materials["rust"], vertices=12))
    objects.append(claim.add_box_game("RenderHelperNightLampworks.stackCap", stack_x, stack_z, stack_ground + 5.62, (1.05, 1.05, 0.30), materials["iron"]))
    objects.append(claim.add_beam("RenderHelperNightLampworks.pipe", (stack_x, stack_z, stack_ground + 3.7), (x + 0.2, z, ground + 2.2), 0.18, materials["iron"]))
    for index, (dx, dz) in enumerate([(-2.2, -1.4), (-1.5, -1.6), (2.3, -1.2), (2.7, 1.4)]):
        base = float(claim.terrain_height(x + dx, z + dz))
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.34, depth=0.72, location=(x + dx, -(z + dz), base + 0.36))
        barrel = bpy.context.object
        barrel.name = f"RenderHelperNightLampworks.oilDrum.{index}"
        barrel.data.materials.append(materials["rust"])
        objects.append(barrel)
    return objects


def add_night_rock_walls(materials):
    objects = []
    clusters = [
        (-21.0, 15.0, (4.8, 3.4, 2.6), 0.2),
        (-19.0, 8.0, (3.9, 3.0, 2.2), -0.4),
        (21.0, 13.0, (4.5, 3.2, 2.5), -0.2),
        (19.0, -12.0, (4.8, 3.6, 2.8), 0.3),
        (-20.5, -14.0, (4.3, 3.3, 2.4), -0.3),
        (-9.0, -26.0, (3.6, 2.7, 2.2), 0.1),
        (10.0, -25.0, (3.8, 2.8, 2.3), -0.1),
    ]
    for index, (x, z, scale, yaw) in enumerate(clusters):
        objects.append(claim.add_rock(f"RenderHelperNightWallRock.{index}", x, z, scale, materials["stone"], yaw))
    return objects


def make_night_preview(terrain_material):
    materials = regional_materials("NightShift")
    materials.update({
        "brass": claim.make_render_material("NightShiftColdBrass", (0.16, 0.13, 0.07), 0.55, 0.35),
        "cold_lens": state.make_emissive_material("NightShiftColdLens", (0.025, 0.06, 0.11), 1.8),
        "warm_lens": state.make_emissive_material("NightShiftWarmLens", (1.0, 0.22, 0.025), 8.0),
    })
    # State helpers expect this exact key name for lantern posts.
    materials["iron"] = claim.make_render_material("NightShiftLanternIron", (0.035, 0.055, 0.075), 0.62, 0.42)
    night_water = claim.make_water_material(
        "NightShiftWorkingWater",
        dark=(0.010, 0.008, 0.006),
        light=(0.050, 0.038, 0.020),
        roughness=0.48,
    )
    objects = [claim.make_water_surface(night_water)]
    objects.extend(claim.make_ford_stones(terrain_material))
    objects.extend(add_lampworks_yard(materials))
    objects.extend(add_night_rock_walls(materials))

    lanterns = [(0, 16), (-16, 18), (16, 18), (-22, -12), (22, -12), (-10, -24), (10, -24)]
    for index, (x, z) in enumerate(lanterns):
        lantern, lens = state.make_lantern_post(f"RenderHelperNightShiftLantern.{index}", x, z, materials)
        if index == 0:
            lens.data.materials.clear()
            lens.data.materials.append(materials["warm_lens"])
        objects.extend(lantern)
        light_data = bpy.data.lights.new(f"RenderHelperNightShiftPoolData.{index}", "POINT")
        light_data.energy = 920.0 if index == 0 else 260.0
        light_data.color = (1.0, 0.25, 0.035) if index == 0 else (0.10, 0.24, 0.62)
        light_data.shadow_soft_size = 3.6 if index == 0 else 2.2
        light = bpy.data.objects.new(f"RenderHelperNightShiftPool.{index}", light_data)
        bpy.context.collection.objects.link(light)
        light.location = (x + 0.54, -z, float(claim.terrain_height(x, z)) + 1.75)
        objects.append(light)

    # The central relight is gameplay-critical, so give it a broad readable
    # ground pool rather than relying on a tiny physically plausible point.
    pool_data = bpy.data.lights.new("RenderHelperNightShiftCentralPoolData", "AREA")
    pool_data.energy = 720.0
    pool_data.color = (1.0, 0.25, 0.035)
    pool_data.shape = "DISK"
    pool_data.size = 6.4
    pool = bpy.data.objects.new("RenderHelperNightShiftCentralPool", pool_data)
    bpy.context.collection.objects.link(pool)
    pool.location = (0.54, -16.0, float(claim.terrain_height(0.0, 16.0)) + 5.2)
    claim.aim_at(pool, (0.54, -16.0, float(claim.terrain_height(0.0, 16.0))))
    objects.append(pool)

    objects.extend(add_fence("RenderHelperNightShiftWorkRoadWest", [(-8, 11), (-12, 14), (-16, 17)], materials))
    objects.extend(add_fence("RenderHelperNightShiftWorkRoadEast", [(8, 11), (12, 14), (16, 17)], materials))
    objects.extend(add_regional_rocks("night-shift", materials, 20, 7.0))
    return objects


def add_seized_headframe(materials):
    objects = []
    cx, cz = -14.0, -17.0
    ground = float(claim.terrain_height(cx, cz))
    for index, (dx, dz) in enumerate([(-1.5, -1.2), (1.5, -1.2), (-1.15, 1.1), (1.15, 1.1)]):
        objects.append(claim.add_beam(f"RenderHelperBaronHeadframe.leg.{index}", (cx + dx, cz + dz, ground), (cx + dx * 0.62, cz + dz * 0.62, ground + 5.4), 0.25, materials["timber"]))
    objects.append(claim.add_beam("RenderHelperBaronHeadframe.top", (cx - 1.2, cz, ground + 5.25), (cx + 1.2, cz, ground + 5.25), 0.28, materials["wood"]))
    objects.append(claim.add_box_game("RenderHelperBaronHeadframe.deck", cx, cz, ground + 3.2, (3.8, 2.6, 0.28), materials["wood"], yaw=0.04))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.68, minor_radius=0.10, major_segments=16, minor_segments=6, location=(cx, -cz, ground + 4.45), rotation=(math.pi / 2.0, 0.0, 0.0))
    wheel = bpy.context.object
    wheel.name = "RenderHelperBaronHeadframe.wheel"
    wheel.data.materials.append(materials["iron"])
    objects.append(wheel)
    return objects


def add_baron_guard_tower(name, x, z, materials, yaw=0.0):
    objects = []
    ground = float(claim.terrain_height(x, z))
    for index, (dx, dz) in enumerate([(-1.15, -1.0), (1.15, -1.0), (-1.15, 1.0), (1.15, 1.0)]):
        objects.append(
            claim.add_beam(
                f"{name}.leg.{index}",
                (x + dx * 1.18, z + dz * 1.18, ground),
                (x + dx * 0.72, z + dz * 0.72, ground + 3.8),
                0.22,
                materials["timber"],
            )
        )
    objects.append(claim.add_box_game(f"{name}.deck", x, z, ground + 3.45, (3.2, 2.9, 0.30), materials["wood"], yaw=yaw))
    roof = claim.add_roof_prism(f"{name}.roof", x, z, ground + 3.75, 3.5, 3.2, 1.0, materials["rust"], yaw)
    roof.rotation_euler.y += 0.035
    objects.append(roof)
    objects.append(claim.add_box_game(f"{name}.banner", x + 1.35, z, ground + 4.15, (0.08, 0.95, 1.45), materials["oxblood"], yaw=yaw))
    objects.append(claim.add_beam(f"{name}.salvageBrace", (x - 1.30, z + 1.05, ground + 0.35), (x + 0.78, z + 0.72, ground + 3.48), 0.11, materials["wood"]))
    return objects


def add_baron_supply_cache(materials):
    objects = []
    for index, (x, z, dimensions, yaw) in enumerate([
        (6.5, 15.0, (1.5, 1.15, 0.95), 0.10),
        (8.0, 14.4, (1.1, 0.95, 0.72), -0.14),
        (7.2, 16.4, (1.25, 0.85, 0.62), 0.22),
        (10.0, 16.0, (1.65, 0.55, 0.46), -0.08),
    ]):
        ground = float(claim.terrain_height(x, z))
        objects.append(claim.add_box_game(f"RenderHelperBaronSupply.{index}", x, z, ground, dimensions, materials["wood"], yaw=yaw))
    # Broken anti-cart barricades read as battle damage, not a walkable wall.
    for index, (ax, az, bx, bz) in enumerate([(-13, 14, -9, 16), (-6, 19, -2, 18), (12, 20, 16, 17)]):
        ah = float(claim.terrain_height(ax, az)) + 0.18
        bh = float(claim.terrain_height(bx, bz)) + 0.28
        objects.append(claim.add_beam(f"RenderHelperBaronBrokenBarricade.{index}", (ax, az, ah), (bx, bz, bh), 0.22, materials["timber"]))
    return objects


def add_baron_fortress(materials):
    """Dominant far-bank compound with a ford-aligned open gate."""
    objects = []
    wall_z = -10.8
    for side, center_x in (("west", -15.0), ("east", 15.0)):
        ground = float(claim.terrain_height(center_x, wall_z))
        objects.append(claim.add_box_game(f"RenderHelperBaronFortress.wall.{side}", center_x, wall_z, ground, (20.0, 1.25, 2.45), materials["dark_timber"]))
        for index, x in enumerate(np.linspace(center_x - 8.5, center_x + 8.5, 6)):
            if index == (1 if side == "west" else 4):
                continue
            cap_ground = float(claim.terrain_height(float(x), wall_z))
            objects.append(claim.add_box_game(f"RenderHelperBaronFortress.crenel.{side}.{index}", float(x), wall_z, cap_ground + 2.35, (1.15, 1.55, 0.72), materials["wood"]))
        for index, offset in enumerate((-7.0, -2.8, 2.4, 6.9)):
            x = center_x + offset
            patch_ground = float(claim.terrain_height(x, wall_z))
            lean = (-0.045, 0.025, -0.018, 0.055)[index]
            objects.append(claim.add_box_game(f"RenderHelperBaronFortress.wallRepair.{side}.{index}", x, wall_z + 0.69, patch_ground + 0.14, (0.28, 0.11, 2.05 - index * 0.12), materials["wood"], yaw=lean, tilt=(0.0, lean), bevel=0.008))
        scar_x = center_x + (4.5 if side == "west" else -4.0)
        scar_ground = float(claim.terrain_height(scar_x, wall_z))
        objects.append(claim.add_box_game(f"RenderHelperBaronFortress.impactPatch.{side}", scar_x, wall_z + 0.70, scar_ground + 0.50, (1.25, 0.10, 0.82), materials["rust"], yaw=0.08 if side == "west" else -0.06, bevel=0.0))
        objects.append(claim.add_beam(f"RenderHelperBaronFortress.impactBrace.{side}", (scar_x - 0.62, wall_z + 0.76, scar_ground + 0.54), (scar_x + 0.58, wall_z + 0.76, scar_ground + 1.18), 0.10, materials["wood"]))

    tower_positions = [(-4.6, wall_z), (4.6, wall_z), (-25.5, wall_z - 1.5), (25.5, wall_z - 1.5)]
    for index, (x, z) in enumerate(tower_positions):
        ground = float(claim.terrain_height(x, z))
        objects.append(claim.add_box_game(f"RenderHelperBaronFortress.tower.{index}", x, z, ground, (3.7, 3.5, 4.65), materials["timber"]))
        objects.append(claim.add_roof_prism(f"RenderHelperBaronFortress.towerRoof.{index}", x, z, ground + 4.65, 4.25, 4.05, 1.25, materials["oxblood"], -0.04 if index % 2 else 0.04))
        front_z = z + 1.82
        objects.append(claim.add_beam(f"RenderHelperBaronFortress.towerBrace.{index}", (x - 1.25, front_z, ground + 0.35), (x + 1.05, front_z, ground + 3.95), 0.14, materials["wood"]))
    left_ground = float(claim.terrain_height(-3.0, wall_z))
    right_ground = float(claim.terrain_height(3.0, wall_z))
    objects.append(claim.add_beam("RenderHelperBaronFortress.gateLintel", (-3.0, wall_z, left_ground + 4.0), (3.0, wall_z, right_ground + 4.0), 0.44, materials["iron"]))
    objects.append(claim.add_box_game("RenderHelperBaronFortress.gateBanner", 0.0, wall_z - 0.1, (left_ground + right_ground) * 0.5 + 3.85, (2.5, 0.12, 1.25), materials["oxblood"]))
    return objects


def make_baron_preview(terrain_material):
    materials = regional_materials("Baron")
    materials.update({
        "dark_timber": materials["timber"],
        "oxblood": claim.make_render_material("BaronOxbloodBanner", (0.31, 0.018, 0.020)),
        "enemy_canvas": claim.make_render_material("BaronEnemyCanvas", (0.13, 0.055, 0.035)),
    })
    objects = [claim.make_water_surface(claim.make_water_material())]
    objects.extend(claim.make_ford_stones(terrain_material))
    objects.extend(add_baron_fortress(materials))
    objects.extend(add_seized_headframe(materials))
    objects.extend(add_baron_guard_tower("RenderHelperBaronNearTower", -16.5, 16.5, materials, 0.08))
    objects.extend(add_baron_guard_tower("RenderHelperBaronEastTower", 19.0, 13.5, materials, -0.10))
    objects.extend(add_baron_supply_cache(materials))
    objects.extend(state.make_banner("RenderHelperBaronBanner.center", 0.0, -8.0, materials))
    objects.extend(state.make_banner("RenderHelperBaronBanner.west", -22.0, -10.5, materials, yaw=0.12))
    objects.extend(state.make_banner("RenderHelperBaronBanner.east", 22.0, -10.5, materials, yaw=-0.10))
    objects.extend(state.make_enemy_tent("RenderHelperBaronCamp.west", -5.5, -17.0, 1.0, materials, yaw=0.12))
    objects.extend(state.make_enemy_tent("RenderHelperBaronCamp.east", 6.5, -18.0, 0.90, materials, yaw=-0.18))
    objects.extend(state.make_rocket_cart(materials))
    objects.extend(state.make_siege_line(materials))
    objects.extend(add_fence("RenderHelperBaronFarRampartWest", [(-27, -11), (-22, -9), (-17, -9), (-12, -8)], materials))
    objects.extend(add_fence("RenderHelperBaronFarRampartEast", [(12, -8), (17, -9), (22, -9), (27, -11)], materials))
    objects.extend(add_fence("RenderHelperBaronApproachWreck", [(-17, 15), (-12, 17), (-7, 16)], materials))
    objects.extend(state.make_banner("RenderHelperBaronBanner.nearWest", -23.0, 17.0, materials, yaw=0.10))
    objects.extend(state.make_banner("RenderHelperBaronBanner.nearEast", 23.0, 17.0, materials, yaw=-0.10))
    objects.extend(add_regional_rocks("baron", materials, 15, 7.0))
    return objects


def make_preview(key, terrain_material):
    if key == "twin-banks":
        return make_twin_preview(terrain_material)
    if key == "night-shift":
        return make_night_preview(terrain_material)
    return make_baron_preview(terrain_material)


def preview_stats(objects, profile):
    meshes = [obj for obj in objects if obj.type == "MESH"]
    curves = [obj for obj in objects if obj.type == "CURVE"]
    triangles = sum(sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons) for obj in meshes)
    return {
        "exported": False,
        "purpose": "owner composition verdict only; simulation and production fixtures remain code-owned",
        "theme": profile["theme"],
        "landmarks": profile["landmarks"],
        "objects": len(objects),
        "meshObjects": len(meshes),
        "curveObjects": len(curves),
        "approxTrianglesBeforeCurveTessellation": triangles,
    }


def render_preview(key, profile, terrain, preview_water, county):
    backdrop = claim.make_backdrop()
    panorama = claim.link_panorama(key)
    for obj in panorama:
        obj.hide_render = True
    run_camera = claim.add_camera(f"{profile['object']}RunCamera", (0.0, -30.3, 26.26), (0.0, -8.65, 0.51), 42.0)
    edge_camera = claim.add_camera(f"{profile['object']}EastEdge", (24.0, -30.3, 26.26), (24.0, -8.65, 0.51), 42.0)
    overview = claim.add_camera(f"{profile['object']}Overview", (0.0, -38.0, 50.0), (0.0, -1.0, 0.42), 46.0)
    county_overview = claim.add_camera(f"{profile['object']}CountyOverview", (0.0, -78.0, 88.0), (0.0, -5.0, 1.1), 52.0)
    low = claim.add_camera(f"{profile['object']}LowCamera", (-28.0, 23.0, 11.0), (5.0, -0.4, 0.38), 46.0)
    horizon_target = (120.0, 0.0, 8.0) if key == "baron" else (0.0, 120.0, 8.0)
    horizon = claim.add_camera(f"{profile['object']}PanoramaHorizon", (0.0, 0.0, 3.8), horizon_target, 52.0)
    if key == "night-shift":
        bpy.context.scene.view_settings.exposure = 0.90
        lights = state.add_night_lighting()
        bpy.context.scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.15
        lights[0].data.energy = 4700.0
        moon_data = bpy.data.lights.new("NightShiftMoon", "SUN")
        moon_data.energy = 0.58
        moon_data.color = (0.20, 0.32, 0.72)
        moon_data.angle = math.radians(18.0)
        moon = bpy.data.objects.new("NightShiftMoon", moon_data)
        bpy.context.collection.objects.link(moon)
        moon.location = (-36.0, -28.0, 30.0)
        claim.aim_at(moon, (0.0, 0.0, 0.0))
        lights.append(moon)
    else:
        lights = claim.add_lighting(sunset=False)

    # Acceptance renders prove the exported terrain, not the temporary county
    # helper. Keep the panorama off so the terrain and backdrop remain separate
    # verdicts.
    terrain.hide_render = False
    preview_water.hide_render = False
    for obj in county:
        obj.hide_render = True
    claim.render(run_camera, ARTIFACTS / f"{key}-run-camera-unique.png")
    claim.render(overview, ARTIFACTS / f"{key}-layout-unique.png")

    # Same edge camera, same lighting: prove what the county adds without
    # comparing against a different composition or flattering angle.
    claim.render(edge_camera, ARTIFACTS / f"{key}-exterior-before-edge.png")
    terrain.hide_render = True
    preview_water.hide_render = True
    for obj in county:
        obj.hide_render = False

    claim.render(edge_camera, ARTIFACTS / f"{key}-run-camera-east-edge.png")
    claim.render(county_overview, ARTIFACTS / f"{key}-county-overview.png")
    claim.remove_objects(lights)
    if key == "night-shift":
        low_lights = state.add_night_lighting()
        bpy.context.scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.15
        low_lights[0].data.energy = 4700.0
    else:
        low_lights = claim.add_lighting(sunset=True)
    claim.render(low, ARTIFACTS / f"{key}-low-angle-unique.png")
    claim.render(low, ARTIFACTS / f"{key}-panorama-before.png")
    for obj in panorama:
        obj.hide_render = False
    claim.render(low, ARTIFACTS / f"{key}-panorama-mounted.png")
    claim.render(horizon, ARTIFACTS / f"{key}-panorama-horizon.png")
    claim.remove_objects(low_lights + [run_camera, edge_camera, overview, county_overview, low, horizon, backdrop] + panorama)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def carry_forward_mount_records(profile, mounts):
    """Keep the fields a LATER pipeline step wrote onto each mount.

    This builder authors mount ids and planar positions; `build_landmark_packs.py`
    / `apply_mounts_sweep.py` then backfill the runtime-critical `asset` path and
    the terrain-conformed Y. A plain re-export used to DROP both, and the runtime
    reads `mount.asset` to find the GLB (Terrain3dClaimPilot.ts:605) — so an atlas
    repaint would silently un-mount every landmark and fall back to painted ground
    with no error anywhere (CLAUDE.md Mistake #10). Measured on the e1-baron
    beauty shift, 2026-08-02.

    Preservation only, never invention: extras are carried over ONLY when the
    rebuilt mount sits at the same planar X/Z, so a genuinely moved or renamed
    mount still re-derives from scratch.
    """
    path = OUT / f"{profile['stem']}-contract.json"
    if not path.exists():
        return mounts, None
    previous = json.loads(path.read_text(encoding="utf-8"))
    known = {entry.get("id"): entry for entry in previous.get("landmarkMounts", [])}
    merged = []
    for mount in mounts:
        prior = known.get(mount.get("id"))
        if prior and prior.get("position", [None, None, None])[0::2] == mount["position"][0::2]:
            mount = dict(mount)
            mount["position"] = list(prior["position"])
            for field in ("asset", "terrainConformOffsetY"):
                if field in prior:
                    mount[field] = prior[field]
        merged.append(mount)
    return merged, previous.get("landmarkPack")


def make_contract(key, profile, terrain, owner_preview):
    coords = np.asarray([vertex.co[:] for vertex in terrain.data.vertices], dtype=np.float32)
    triangles = sum(len(polygon.vertices) - 2 for polygon in terrain.data.polygons)
    if key == "twin-banks":
        water_truth = {
            "kind": "braided_visual_river",
            "visualHalfWidth": 7.8,
            "fords": [{"x": -16.0, "halfWidth": 3.0}, {"x": 16.0, "halfWidth": 3.0}],
            "gravelBars": [{"x": -7.5, "z": 0.2}, {"x": 7.4, "z": -0.25}],
        }
    else:
        water_truth = {
            "river": {"minZ": -5.0, "maxZ": 5.0},
            "shallowsWidth": 1.25,
            "ford": {"minX": -3.0, "maxX": 3.0},
        }
    mounts, landmark_pack = carry_forward_mount_records(profile, profile["mounts"])
    contract = {
        "asset": f"{profile['stem']}.glb",
        "contractId": profile["contractId"],
        "tileId": profile["tileId"],
        "renderOnly": True,
        "simulation": "planar and unchanged",
        "heightSocket": "Terrain.visualY",
        "regionalFamily": {
            "epoch": "Epoch 1 frontier river county",
            "shared": ["painted ochre-rust palette", "river stone", "weathered timber", "sparse dusty vegetation", "warm frontier light"],
            "unique": ["terrain mesh", "atlas treatment", "macro silhouette", "spatial rhythm", "landmark composition"],
        },
        "boundsMeters": {
            "min": [round(float(value), 4) for value in coords.min(axis=0)],
            "max": [round(float(value), 4) for value in coords.max(axis=0)],
        },
        "meshCount": 1,
        "primitiveCount": 1,
        "materialCount": 1,
        "vertices": len(terrain.data.vertices),
        "triangles": triangles,
        "triangleBudget": 60000,
        "texture": {"count": 1, "width": ATLAS_SIZE, "height": ATLAS_SIZE, "embedded": True},
        "waterTruth": water_truth,
        "landmarkMountSpace": claim.landmark_mount_space(),
        "landmarkMounts": mounts,
        "panoramaMount": claim.panorama_mount(key),
        "ownerPreview": owner_preview,
        "sourceArt": [
            str(path.relative_to(ROOT))
            for path in (
                claim.BANK_A,
                claim.BANK_B,
                claim.BANK_C,
                claim.RIVER,
                claim.KIT_ERA,
                claim.CONTRACT_PLATES[key],
            )
        ],
    }
    if landmark_pack is not None:
        contract["landmarkPack"] = landmark_pack
    return contract


def export_asset(profile, terrain, contract):
    blend = OUT / f"{profile['stem']}.blend"
    glb = OUT / f"{profile['stem']}.glb"
    atlas = OUT / f"{profile['stem']}-atlas.png"
    contract_path = OUT / f"{profile['stem']}-contract.json"
    bpy.ops.object.select_all(action="DESELECT")
    terrain.select_set(True)
    bpy.context.view_layer.objects.active = terrain
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(
        filepath=str(glb),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_extras=True,
    )
    contract["files"] = {
        "blend": {"bytes": blend.stat().st_size, "sha256": sha256(blend)},
        "glb": {"bytes": glb.stat().st_size, "sha256": sha256(glb)},
        "atlas": {"bytes": atlas.stat().st_size, "sha256": sha256(atlas)},
    }
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(contract, indent=2))


def main():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    key = args[0] if args else "twin-banks"
    if key not in PROFILES:
        raise ValueError(f"unsupported unique terrain profile: {key}")
    profile = PROFILES[key]
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    claim.reset_scene()
    atlas = make_atlas(key, profile)
    material = claim.make_material(atlas)
    material.name = profile["material"]
    terrain = make_terrain(key, profile, material)

    claim.terrain_height = HEIGHT_FUNCTIONS[key]
    state.claim = claim
    preview = make_preview(key, material)
    owner_preview = preview_stats(preview, profile)
    county, county_stats = make_county_surround(key, atlas)
    owner_preview["exteriorSurround"] = county_stats
    terrain.hide_render = True
    preview[0].hide_render = True
    render_preview(key, profile, terrain, preview[0], county)

    claim.remove_objects(preview + county)
    terrain.hide_render = False
    bpy.context.scene.world = None
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    contract = make_contract(key, profile, terrain, owner_preview)
    export_asset(profile, terrain, contract)


if __name__ == "__main__":
    main()
