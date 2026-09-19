"""Build separate render-only panorama rings for the authored map families.

Panoramas are mounted scenery, never terrain. They carry no gameplay bounds,
water, spawn, fog, or placement authority.

NOT FOR EPOCH 1. This script began as the five-map E1 panorama builder and was
generalised in place for E2..E10; its shared paint and ring code has been retuned
since the E1 art shipped at 9e0dcf98, so it no longer reproduces it. The E1 keys
remain in PROFILES only because map_index = list(PROFILES).index(key) places every
later map's cloud edits off this ordering. main() refuses them; build the five E1
panoramas with build_e1_contract_panoramas.py and guard them with
verify_e1_panoramas.py.
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
KIT = ROOT / "assets/processed/kit-era-1.png"
ATLAS_SIZE = 2048
RADIUS = 190.0
RIDGE_FOOT_RADIUS = 161.5
RIDGE_CREST_RADIUS = 174.0
FAR_RIDGE_FOOT_RADIUS = 177.0
FAR_RIDGE_CREST_RADIUS = 184.0
SEGMENTS = 192
ROWS = 5
SKY_BOTTOM = -10.0
SKY_TOP = 130.0
RIDGE_TOP_BASE = 5.0
RIDGE_TOP_SCALE = 55.0
QUADRANT_PHASE_OFFSETS = (0.00, 0.37, 0.81, 1.29)
QUADRANT_VERTICAL_OFFSETS = (-0.025, 0.035, -0.045, 0.015)
LAYERED_PANORAMAS = {"canyon-works", "moth-season", "blackout-ridge", "dust-flats", "fairground", "glow-mesa", "relay-valley", "echo-canyon", "mare-claim", "ember-shore"}
FAR_RIDGE_PANORAMAS = LAYERED_PANORAMAS - {"dust-flats", "glow-mesa"}
NIGHT_PANORAMAS = {"night-shift", "canyon-works", "moth-season", "blackout-ridge", "fairground", "glow-mesa", "relay-valley", "echo-canyon", "ember-shore"}
# Shipped by build_e1_contract_panoramas.py at 9e0dcf98; kept in PROFILES for map_index only.
E1_PANORAMAS = {"the-claim", "dry-gulch", "twin-banks", "night-shift", "baron"}
OPEN_SEA_PANORAMAS = {"deepwater-claim", "regatta"}

claim_spec = importlib.util.spec_from_file_location("panorama_claim_helpers", OUT / "build_the_claim_terrain.py")
claim = importlib.util.module_from_spec(claim_spec)
claim_spec.loader.exec_module(claim)

PROFILES = {
    "the-claim": {
        "contract": "claim",
        "tint": (0.86, 0.70, 0.49),
        "dark": (0.19, 0.085, 0.028),
        "phase": 0.03,
        "strength": 0.48,
        "dust": (0.90, 0.17, 0.34),
        "signature": "open wind-scoured valley holding against a bruised outer rim",
    },
    "dry-gulch": {
        "contract": "dry-gulch",
        "tint": (1.00, 0.66, 0.31),
        "dark": (0.22, 0.075, 0.022),
        "phase": 0.29,
        "strength": 0.54,
        "dust": (0.57, 0.15, 0.08),
        "signature": "bleached enclosed basin beneath stepped dry mesas",
    },
    "twin-banks": {
        "contract": "twin-banks",
        "tint": (0.66, 0.66, 0.54),
        "dark": (0.16, 0.075, 0.035),
        "phase": 0.51,
        "strength": 0.47,
        "dust": (0.16, 0.22, 0.16),
        "signature": "low opposed shelves opening around a broad river county",
    },
    "night-shift": {
        "contract": "night-shift",
        "tint": (0.28, 0.38, 0.70),
        "dark": (0.025, 0.040, 0.075),
        "phase": 0.73,
        "strength": 0.42,
        "dust": (0.70, 0.13, 0.12),
        "signature": "cold enclosing rock corridor with one stubborn warm horizon break",
    },
    "baron": {
        "contract": "baron",
        "tint": (0.78, 0.42, 0.25),
        "dark": (0.16, 0.035, 0.025),
        "phase": 0.91,
        "strength": 0.50,
        "dust": (0.88, 0.16, 0.32),
        "signature": "occupied wind-cut ridge rhythm against a darker fevered rim",
    },
    "hill-mine": {
        "contract": "hill-mine",
        "kit": ROOT / "assets/processed/kit-era-2.png",
        "sourcePlate": ROOT / "assets/raw/plate-contract-hill-mine.png",
        "epoch": "Epoch 2 steamworks county",
        "tint": (0.72, 0.58, 0.39),
        "dark": (0.105, 0.064, 0.036),
        "phase": 0.18,
        "strength": 0.45,
        "dust": (0.77, 0.13, 0.24),
        "signature": "scarred mine terraces beneath broken high-country ridges and a smoke-dim rim",
    },
    "trestle": {
        "contract": "trestle",
        "kit": ROOT / "assets/processed/kit-era-2.png",
        "sourcePlate": ROOT / "assets/processed/kit-era-2.png",
        "epoch": "Epoch 2 steamworks county",
        "tint": (0.67, 0.59, 0.47),
        "dark": (0.075, 0.070, 0.058),
        "phase": 0.64,
        "strength": 0.43,
        "dust": (0.31, 0.18, 0.19),
        "signature": "a low river corridor vanishing between mismatched gorge shoulders and rail-cut distance",
    },
    "pressure-garden": {
        "contract": "pressure-garden",
        "kit": ROOT / "assets/processed/kit-era-2.png",
        "sourcePlate": ROOT / "assets/processed/kit-era-2.png",
        "epoch": "Epoch 2 steamworks county",
        "tint": (0.69, 0.61, 0.43),
        "dark": (0.082, 0.064, 0.038),
        "phase": 0.36,
        "strength": 0.44,
        "dust": (0.48, 0.15, 0.22),
        "signature": "heat-scoured garden steps opening beneath a broken steam haze and unequal dry ridges",
    },
    "incline": {
        "contract": "incline",
        "kit": ROOT / "assets/processed/kit-era-2.png",
        "sourcePlate": ROOT / "assets/processed/kit-era-2.png",
        "epoch": "Epoch 2 steamworks county",
        "tint": (0.61, 0.57, 0.48),
        "dark": (0.060, 0.055, 0.048),
        "phase": 0.79,
        "strength": 0.42,
        "dust": (0.82, 0.12, 0.25),
        "signature": "a high split cut pinched between mismatched ore shoulders with one distant haul notch",
    },
    "canyon-works": {
        "contract": "canyon-works",
        "kit": ROOT / "assets/processed/kit-era-3.png",
        "sourcePlate": ROOT / "assets/raw/ter-canyon-atlas.png",
        "epoch": "Epoch 3 voltage canyon",
        "tint": (0.31, 0.39, 0.52),
        "dark": (0.018, 0.030, 0.055),
        "phase": 0.41,
        "strength": 1.56,
        "dust": (0.74, 0.11, 0.18),
        "signature": "a cold split gorge closing around two copper gallery rims with one warm works glow",
    },
    "moth-season": {
        "contract": "moth-season",
        "kit": ROOT / "assets/processed/kit-era-3.png",
        "sourcePlate": ROOT / "assets/raw/plate-e3-mothswarm.png",
        "epoch": "Epoch 3 voltage canyon",
        "tint": (0.38, 0.42, 0.55),
        "dark": (0.020, 0.024, 0.043),
        "phase": 0.86,
        "strength": 1.44,
        "dust": (0.22, 0.14, 0.15),
        "signature": "a narrow black migration corridor between two low lamp-lit yard horizons",
    },
    "blackout-ridge": {
        "contract": "blackout-ridge",
        "kit": ROOT / "assets/processed/kit-era-3.png",
        "sourcePlate": ROOT / "assets/processed/kit-era-3.png",
        "epoch": "Epoch 3 voltage canyon",
        "tint": (0.29, 0.37, 0.50),
        "dark": (0.014, 0.025, 0.050),
        "phase": 0.57,
        "strength": 1.48,
        "dust": (0.54, 0.12, 0.17),
        "signature": "a climbing blackout shelf under broken storm strata with one failing copper horizon line",
    },
    "fairground": {
        "contract": "fairground",
        "kit": ROOT / "assets/processed/kit-era-3.png",
        "sourcePlate": ROOT / "assets/processed/kit-era-3.png",
        "epoch": "Epoch 3 voltage canyon",
        "tint": (0.38, 0.39, 0.48),
        "dark": (0.018, 0.024, 0.043),
        "phase": 0.32,
        "strength": 1.26,
        "dust": (0.62, 0.13, 0.17),
        "signature": "a low festival bowl ringed by unequal voltage-county shoulders, one gate notch, and a bruised lamp-haze horizon",
    },
    "dust-flats": {
        "contract": "dust-flats",
        "kit": ROOT / "assets/processed/kit-era-4.png",
        "sourcePlate": ROOT / "assets/processed/kit-era-4.png",
        "epoch": "Epoch 4 motor frontier",
        "tint": (0.77, 0.61, 0.38),
        "dark": (0.105, 0.068, 0.034),
        "phase": 0.24,
        "strength": 0.76,
        "dust": (0.70, 0.19, 0.31),
        "signature": "a vast wheel-scoured motor plain fading through unequal storm banks and a low railhead notch",
    },
    "deepwater-claim": {
        "contract": "deepwater-claim",
        "kit": ROOT / "assets/processed/kit-era-5.png",
        "sourcePlate": ROOT / "assets/raw/ter-shelf-atlas.png",
        "epoch": "Epoch 5 post-flood harbor chain",
        "tint": (0.34, 0.55, 0.52),
        "dark": (0.020, 0.055, 0.062),
        "phase": 0.68,
        "strength": 0.94,
        "dust": (0.78, 0.18, 0.22),
        "signature": "an open drowned horizon with unequal weather cells, low wreck-mast suggestions, and no confirming coast",
    },
    "regatta": {
        "contract": "regatta",
        "kit": ROOT / "assets/processed/kit-era-5.png",
        "sourcePlate": ROOT / "assets/raw/ter-shelf-atlas.png",
        "epoch": "Epoch 5 post-flood harbor chain",
        "tint": (0.31, 0.52, 0.51),
        "dark": (0.018, 0.046, 0.056),
        "phase": 0.43,
        "strength": 0.96,
        "dust": (0.74, 0.21, 0.31),
        "signature": "an open racing sea with one low charcoal weather bank, unequal mast cues, and no confirming coast",
    },
    "glow-mesa": {
        "contract": "glow-mesa",
        "kit": ROOT / "assets/processed/kit-era-6.png",
        "sourcePlate": ROOT / "assets/processed/kit-era-6.png",
        "epoch": "Epoch 6 atomic homestead",
        "tint": (0.46, 0.66, 0.64),
        "dark": (0.018, 0.060, 0.066),
        "phase": 0.47,
        "strength": 1.08,
        "dust": (0.76, 0.045, 0.14),
        "signature": "high mesa distance opening toward a low inland-water gleam in one quadrant and dust-dark plains in the opposite quadrant",
    },
    "relay-valley": {
        "contract": "relay-valley",
        "kit": ROOT / "assets/processed/kit-era-7.png",
        "sourcePlate": ROOT / "assets/raw/plate-e7-bld-relay-tower.png",
        "epoch": "Epoch 7 signal frontier",
        "tint": (0.49, 0.62, 0.57),
        "dark": (0.030, 0.055, 0.050),
        "phase": 0.62,
        "strength": 1.12,
        "dust": (0.58, 0.080, 0.16),
        "signature": "a split relay county opening through one broad dead-zone notch, with unequal shale rims and distant outward-facing mast marks",
    },
    "echo-canyon": {
        "contract": "echo-canyon",
        "kit": ROOT / "assets/processed/kit-era-7.png",
        "sourcePlate": ROOT / "assets/raw/plate-e7-bld-relay-tower.png",
        "epoch": "Epoch 7 signal frontier",
        "tint": (0.47, 0.60, 0.55),
        "dark": (0.026, 0.048, 0.044),
        "phase": 0.19,
        "strength": 1.10,
        "dust": (0.71, 0.070, 0.15),
        "signature": "a long signal canyon escaping north and south between unequal distant shale gates, with one broken broadcast-cloud quadrant",
    },
    "mare-claim": {
        "contract": "mare-claim",
        "kit": ROOT / "assets/processed/kit-era-8.png",
        "sourcePlate": ROOT / "assets/raw/plate-e8-bld-set.png",
        "epoch": "Epoch 8 orbital claim",
        "tint": (0.56, 0.58, 0.55),
        "dark": (0.018, 0.022, 0.024),
        "phase": 0.74,
        "strength": 0.92,
        "dust": (0.50, 0.10, 0.0),
        "signature": "a quiet lunar crater county beneath one soft blue-green Earth cameo on the near side, with the far side left empty",
    },
    "ember-shore": {
        "contract": "ember-shore",
        "kit": ROOT / "assets/processed/kit-era-10.png",
        "sourcePlate": ROOT / "assets/raw/plate-e10-worlds.png",
        "epoch": "Epoch 10 Deep Sky first world",
        "tint": (0.55, 0.30, 0.16),
        "dark": (0.018, 0.012, 0.010),
        "phase": 0.91,
        "strength": 0.98,
        "dust": (0.68, 0.12, 0.18),
        "signature": "low cooled volcanic shelves beneath deep-ink star stipple and unequal parchment-gold nebula veils",
    },
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def smoothstep(edge0, edge1, value):
    value = np.asarray(value, dtype=np.float32)
    t = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def mirrored_coordinates(values, size, repeats, phase):
    wrapped = np.mod(values * repeats + phase, 2.0)
    mirrored = np.where(wrapped <= 1.0, wrapped, 2.0 - wrapped)
    return mirrored * (size - 1)


def bilinear_sample(source, x, y):
    x0 = np.floor(x).astype(np.int32)
    x1 = np.minimum(x0 + 1, source.shape[1] - 1)
    y0 = np.floor(y).astype(np.int32)
    y1 = np.minimum(y0 + 1, source.shape[0] - 1)
    wx = (x - x0)[None, :, None]
    wy = (y - y0)[..., None]
    top = source[y0, x0[None, :]] * (1.0 - wx) + source[y0, x1[None, :]] * wx
    bottom = source[y1, x0[None, :]] * (1.0 - wx) + source[y1, x1[None, :]] * wx
    return top * (1.0 - wy) + bottom * wy


def circular_bump(u, center, width):
    distance = np.abs(np.mod(u - center + 0.5, 1.0) - 0.5)
    return np.exp(-((distance / width) ** 2))


def ridge_height(key, u):
    angle = u * math.tau
    jagged = np.sin(angle * 13.0 + 0.6) * 0.018 + np.sin(angle * 17.0 - 0.4) * 0.010
    if key == "the-claim":
        return 0.17 + np.sin(angle * 2.0 + 0.2) * 0.030 + np.sin(angle * 5.0) * 0.016 + np.sin(angle * 9.0 + 0.4) * 0.008 + jagged
    if key == "dry-gulch":
        mesas = np.abs(np.sin(angle * 2.0 - 0.8)) ** 5
        return 0.18 + mesas * 0.070 + np.sin(angle * 6.0) * 0.012 + np.sin(angle * 11.0 + 0.3) * 0.006 + jagged
    if key == "twin-banks":
        opening = circular_bump(u, 0.25, 0.11)
        return 0.14 + (1.0 - np.abs(np.sin(angle))) * 0.055 + np.sin(angle * 5.0 + 0.2) * 0.012 + jagged - opening * 0.180
    if key == "night-shift":
        shoulders = np.maximum(np.exp(-((u - 0.18) / 0.10) ** 2), np.exp(-((u - 0.78) / 0.11) ** 2))
        opening = circular_bump(u, 0.25, 0.085)
        return 0.18 + shoulders * 0.080 + np.sin(angle * 5.0) * 0.014 + np.sin(angle * 9.0) * 0.006 + jagged - opening * 0.290
    if key == "hill-mine":
        mine_mass = circular_bump(u, 0.70, 0.16) * 0.090
        broken_cut = circular_bump(u, 0.24, 0.065) * 0.052
        return 0.16 + mine_mass + broken_cut + np.sin(angle * 3.0 + 0.5) * 0.020 + jagged
    if key == "trestle":
        west = circular_bump(u, 0.08, 0.12) * 0.052
        east = circular_bump(u, 0.56, 0.08) * 0.076
        opening = circular_bump(u, 0.31, 0.09) * 0.095
        return 0.145 + west + east - opening + np.sin(angle * 4.0 - 0.6) * 0.012 + jagged
    if key == "pressure-garden":
        west_step = circular_bump(u, 0.10, 0.15) * 0.052
        east_step = circular_bump(u, 0.63, 0.11) * 0.050
        steam_gap = circular_bump(u, 0.38, 0.07) * 0.105
        broken = np.sin(angle * 19.0 - 0.3) * 0.017 + np.sin(angle * 23.0 + 0.8) * 0.010
        return 0.132 + west_step + east_step - steam_gap + np.sin(angle * 4.0 + 0.4) * 0.015 + jagged + broken
    if key == "incline":
        west_wall = circular_bump(u, 0.16, 0.12) * 0.080
        east_wall = circular_bump(u, 0.66, 0.10) * 0.092
        haul_notch = circular_bump(u, 0.42, 0.055) * 0.135
        broken = np.sin(angle * 18.0 + 0.2) * 0.019 + np.sin(angle * 25.0 - 0.9) * 0.011
        return 0.158 + west_wall + east_wall - haul_notch + np.sin(angle * 5.0 - 0.5) * 0.017 + jagged + broken
    if key == "canyon-works":
        west = circular_bump(u, 0.10, 0.13) * 0.105
        east = circular_bump(u, 0.58, 0.11) * 0.135
        cut = circular_bump(u, 0.32, 0.075) * 0.120
        broken = np.sin(angle * 7.0 + 0.3) * 0.026 + np.sin(angle * 11.0 - 0.7) * 0.016
        return 0.18 + west + east - cut + np.sin(angle * 5.0 + 0.3) * 0.014 + jagged + broken
    if key == "moth-season":
        north = circular_bump(u, 0.24, 0.15) * 0.045
        south = circular_bump(u, 0.74, 0.12) * 0.060
        corridor = circular_bump(u, 0.49, 0.075) * 0.085
        broken = np.sin(angle * 6.0 - 0.2) * 0.020 + np.sin(angle * 10.0 + 0.8) * 0.013
        return 0.135 + north + south - corridor + np.sin(angle * 3.0 - 0.4) * 0.010 + jagged + broken
    if key == "blackout-ridge":
        trunk_mass = circular_bump(u, 0.13, 0.14) * 0.060
        switch_mass = circular_bump(u, 0.61, 0.10) * 0.115
        cut = circular_bump(u, 0.36, 0.065) * 0.090
        broken = np.sin(angle * 8.0 + 0.4) * 0.022 + np.sin(angle * 15.0 - 0.6) * 0.014
        return 0.155 + trunk_mass + switch_mass - cut + np.sin(angle * 4.0) * 0.012 + jagged + broken
    if key == "fairground":
        west_shoulder = circular_bump(u, 0.12, 0.13) * 0.052
        east_shoulder = circular_bump(u, 0.61, 0.10) * 0.068
        gate_notch = circular_bump(u, 0.30, 0.070) * 0.120
        north_break = circular_bump(u, 0.78, 0.055) * 0.072
        broken = np.sin(angle * 7.0 - 0.3) * 0.021 + np.sin(angle * 12.0 + 0.8) * 0.013
        return 0.102 + west_shoulder + east_shoulder - gate_notch - north_break + np.sin(angle * 4.0 + 0.2) * 0.012 + jagged + broken
    if key == "dust-flats":
        storm_bank = circular_bump(u, 0.68, 0.16) * 0.130
        west_bank = circular_bump(u, 0.06, 0.09) * 0.075
        rail_notch = circular_bump(u, 0.25, 0.052) * 0.100
        low_pan = np.sin(angle * 3.0 + 0.4) * 0.018 + np.sin(angle * 9.0 - 0.7) * 0.013
        return 0.095 + storm_bank + west_bank - rail_notch + low_pan + jagged * 0.85
    if key in OPEN_SEA_PANORAMAS:
        # Almost no landform: a low weather/wreck silhouette only. The sea and
        # its swell remain runtime-owned, so this belt sits at the far rim.
        mast_a = circular_bump(u, 0.17, 0.009) * 0.045
        mast_b = circular_bump(u, 0.71, 0.007) * 0.034
        weather_bank = circular_bump(u, 0.46, 0.16) * 0.012
        return -0.090 + mast_a + mast_b + weather_bank + np.sin(angle * 4.0 + 0.4) * 0.003
    if key == "glow-mesa":
        # One distant, strongly broken silhouette is enough here. A second
        # nearly level belt made the repaired homestead read as an arena set.
        inland_cut = circular_bump(u, 0.24, 0.105) * 0.068
        dust_plain = circular_bump(u, 0.73, 0.18) * 0.010
        butte_a = circular_bump(u, 0.47, 0.048) * 0.078
        butte_b = circular_bump(u, 0.86, 0.030) * 0.052
        broken = np.sin(angle * 7.0 + 0.3) * 0.011 + np.sin(angle * 14.0 - 0.7) * 0.006
        return 0.022 + butte_a + butte_b + dust_plain - inland_cut + np.sin(angle * 2.0 - 0.2) * 0.008 + broken
    if key == "relay-valley":
        west_chain = circular_bump(u, 0.10, 0.13) * 0.074
        east_chain = circular_bump(u, 0.61, 0.12) * 0.092
        dead_notch = circular_bump(u, 0.34, 0.082) * 0.154
        side_notch = circular_bump(u, 0.82, 0.050) * 0.060
        broken = np.sin(angle * 8.0 + 0.2) * 0.020 + np.sin(angle * 15.0 - 0.8) * 0.010
        return 0.128 + west_chain + east_chain - dead_notch - side_notch + np.sin(angle * 3.0 + 0.4) * 0.012 + jagged + broken
    if key == "echo-canyon":
        west_gate = circular_bump(u, 0.08, 0.14) * 0.095
        east_gate = circular_bump(u, 0.58, 0.13) * 0.084
        north_mouth = circular_bump(u, 0.25, 0.070) * 0.168
        south_mouth = circular_bump(u, 0.75, 0.082) * 0.142
        broken = np.sin(angle * 7.0 - 0.2) * 0.022 + np.sin(angle * 13.0 + 0.7) * 0.012
        return 0.136 + west_gate + east_gate - north_mouth - south_mouth + np.sin(angle * 3.0 + 0.1) * 0.010 + jagged + broken
    if key == "mare-claim":
        low_mare = circular_bump(u, 0.08, 0.12) * 0.052
        crater_break = circular_bump(u, 0.57, 0.075) * 0.118
        secondary_rim = circular_bump(u, 0.73, 0.100) * 0.205
        secondary_notch = circular_bump(u, 0.80, 0.036) * 0.072
        far_notch = circular_bump(u, 0.29, 0.060) * 0.066
        broken = (
            np.sin(angle * 7.0 + 0.3) * 0.026
            + np.sin(angle * 13.0 - 0.6) * 0.014
            + np.maximum(np.sin(angle * 5.0 + 0.8), 0.0) ** 4 * 0.092
        )
        return 0.074 + low_mare + crater_break + secondary_rim - secondary_notch - far_notch + np.sin(angle * 3.0 - 0.2) * 0.014 + jagged * 0.86 + broken
    if key == "ember-shore":
        cooled_shelf = circular_bump(u, 0.14, 0.13) * 0.078
        broken_mass = circular_bump(u, 0.61, 0.10) * 0.118
        preserve_notch = circular_bump(u, 0.36, 0.075) * 0.105
        black_teeth = np.sin(angle * 9.0 + 0.2) * 0.024 + np.sin(angle * 17.0 - 0.7) * 0.014
        return 0.108 + cooled_shelf + broken_mass - preserve_notch + np.sin(angle * 4.0 - 0.4) * 0.014 + black_teeth
    occupied = np.maximum(np.sin(angle * 6.0 + 0.4), 0.0) ** 3
    return 0.17 + occupied * 0.060 + np.sin(angle * 2.0) * 0.018 + np.sin(angle * 9.0 + 0.7) * 0.008 + jagged


def distant_ridge_height(key, u):
    """A lower, broader silhouette that never echoes the nearer mesh ridge."""
    angle = u * math.tau
    if key == "the-claim":
        return 0.105 + circular_bump(u, 0.34, 0.055) * 0.060 + circular_bump(u, 0.17, 0.11) * 0.025 + np.sin(angle * 3.0 + 0.7) * 0.008
    if key == "dry-gulch":
        return 0.115 + circular_bump(u, 0.43, 0.038) * 0.085 + circular_bump(u, 0.56, 0.082) * 0.035 + np.sin(angle * 7.0) * 0.006
    if key == "twin-banks":
        return 0.085 + circular_bump(u, 0.15, 0.075) * 0.052 + circular_bump(u, 0.37, 0.11) * 0.035 + np.sin(angle * 4.0 - 0.5) * 0.006
    if key == "night-shift":
        return 0.120 + circular_bump(u, 0.16, 0.062) * 0.080 + circular_bump(u, 0.38, 0.045) * 0.038 + np.sin(angle * 5.0 + 0.8) * 0.006
    if key == "hill-mine":
        return 0.105 + circular_bump(u, 0.73, 0.075) * 0.080 + circular_bump(u, 0.44, 0.12) * 0.030 + np.sin(angle * 5.0 + 0.2) * 0.007
    if key == "trestle":
        return 0.082 + circular_bump(u, 0.13, 0.065) * 0.050 + circular_bump(u, 0.61, 0.11) * 0.035 + np.sin(angle * 3.0 - 0.8) * 0.006
    if key == "pressure-garden":
        return 0.090 + circular_bump(u, 0.08, 0.085) * 0.042 + circular_bump(u, 0.54, 0.060) * 0.058 + np.sin(angle * 5.0 + 0.7) * 0.006
    if key == "incline":
        return 0.108 + circular_bump(u, 0.21, 0.055) * 0.072 + circular_bump(u, 0.73, 0.080) * 0.050 - circular_bump(u, 0.46, 0.038) * 0.045 + np.sin(angle * 4.0 - 0.3) * 0.007
    if key == "canyon-works":
        broken = np.sin(angle * 9.0 + 0.4) * 0.024 + np.sin(angle * 14.0 - 0.3) * 0.014
        return 0.112 + circular_bump(u, 0.06, 0.070) * 0.070 + circular_bump(u, 0.67, 0.095) * 0.052 + np.sin(angle * 4.0 + 0.5) * 0.006 + broken
    if key == "moth-season":
        broken = np.sin(angle * 8.0 - 0.5) * 0.022 + np.sin(angle * 13.0 + 0.7) * 0.013
        return 0.078 + circular_bump(u, 0.18, 0.090) * 0.038 + circular_bump(u, 0.59, 0.038) * 0.055 + circular_bump(u, 0.82, 0.070) * 0.046 + np.sin(angle * 5.0 - 0.9) * 0.005 + broken
    if key == "blackout-ridge":
        broken = np.sin(angle * 10.0 - 0.2) * 0.019 + np.sin(angle * 16.0 + 0.5) * 0.011
        return 0.095 + circular_bump(u, 0.17, 0.085) * 0.050 + circular_bump(u, 0.72, 0.055) * 0.062 + np.sin(angle * 4.0 + 0.6) * 0.006 + broken
    if key == "fairground":
        broken = np.sin(angle * 9.0 + 0.2) * 0.018 + np.sin(angle * 15.0 - 0.6) * 0.010
        return 0.084 + circular_bump(u, 0.08, 0.085) * 0.045 + circular_bump(u, 0.36, 0.055) * 0.092 + circular_bump(u, 0.69, 0.060) * 0.056 + np.sin(angle * 5.0 - 0.4) * 0.006 + broken
    if key == "dust-flats":
        return 0.042 + circular_bump(u, 0.80, 0.12) * 0.052 + circular_bump(u, 0.41, 0.060) * 0.038 - circular_bump(u, 0.24, 0.040) * 0.038 + np.sin(angle * 5.0 - 0.3) * 0.006
    if key in OPEN_SEA_PANORAMAS:
        return 0.012 + circular_bump(u, 0.16, 0.012) * 0.035 + circular_bump(u, 0.72, 0.009) * 0.026 + np.sin(angle * 3.0) * 0.003
    if key == "glow-mesa":
        inland_shore = circular_bump(u, 0.24, 0.15) * -0.062
        far_butte = circular_bump(u, 0.51, 0.055) * 0.070
        dust_bank = circular_bump(u, 0.76, 0.18) * 0.038
        return 0.072 + inland_shore + far_butte + dust_bank + np.sin(angle * 5.0 + 0.4) * 0.006
    if key == "relay-valley":
        far_west = circular_bump(u, 0.16, 0.085) * 0.052
        far_east = circular_bump(u, 0.70, 0.070) * 0.064
        open_gap = circular_bump(u, 0.36, 0.055) * 0.072
        broken = np.sin(angle * 9.0 - 0.3) * 0.014 + np.sin(angle * 16.0 + 0.5) * 0.008
        return 0.082 + far_west + far_east - open_gap + np.sin(angle * 4.0 - 0.6) * 0.006 + broken
    if key == "echo-canyon":
        far_west = circular_bump(u, 0.13, 0.090) * 0.058
        far_east = circular_bump(u, 0.63, 0.075) * 0.050
        north_gap = circular_bump(u, 0.26, 0.052) * 0.090
        south_gap = circular_bump(u, 0.76, 0.060) * 0.076
        broken = np.sin(angle * 8.0 + 0.4) * 0.015 + np.sin(angle * 15.0 - 0.2) * 0.008
        return 0.086 + far_west + far_east - north_gap - south_gap + np.sin(angle * 4.0 + 0.2) * 0.006 + broken
    if key == "mare-claim":
        far_crater = circular_bump(u, 0.18, 0.070) * 0.070
        distant_shelf = circular_bump(u, 0.68, 0.120) * 0.050
        open_void = circular_bump(u, 0.42, 0.090) * 0.048
        broken = (
            np.sin(angle * 8.0 - 0.3) * 0.019
            + np.sin(angle * 17.0 + 0.5) * 0.010
            + np.maximum(np.sin(angle * 6.0 - 0.5), 0.0) ** 5 * 0.052
        )
        return 0.046 + far_crater + distant_shelf - open_void + np.sin(angle * 4.0 + 0.4) * 0.010 + broken
    if key == "ember-shore":
        old_caldera = circular_bump(u, 0.22, 0.090) * 0.074
        far_shelf = circular_bump(u, 0.72, 0.13) * 0.060
        warm_gap = circular_bump(u, 0.43, 0.060) * 0.055
        broken = np.sin(angle * 8.0 - 0.2) * 0.018 + np.sin(angle * 15.0 + 0.5) * 0.010
        return 0.060 + old_caldera + far_shelf - warm_gap + np.sin(angle * 3.0 + 0.6) * 0.008 + broken
    return 0.105 + circular_bump(u, 0.94, 0.047) * 0.075 + circular_bump(u, 0.075, 0.085) * 0.032 + np.sin(angle * 5.0 - 0.3) * 0.007


def playfield_half_extents(key):
    """Read the rectangular playfield footprint without importing sim code."""
    contract = OUT / f"{key}-terrain-contract.json"
    if contract.is_file():
        bounds = json.loads(contract.read_text(encoding="utf-8"))["boundsMeters"]
        half_x = max(abs(float(bounds["min"][0])), abs(float(bounds["max"][0])))
        half_z = max(abs(float(bounds["min"][1])), abs(float(bounds["max"][1])))
        return half_x, half_z
    if key in {"pressure-garden", "incline"}:
        return 48.0, 48.0
    if key == "blackout-ridge":
        return 40.0, 48.0
    if key == "fairground":
        return 44.0, 44.0
    if key == "dust-flats":
        return 80.0, 80.0
    if key in OPEN_SEA_PANORAMAS:
        return 64.0, 64.0
    if key in {"glow-mesa", "relay-valley", "echo-canyon", "mare-claim", "ember-shore"}:
        return 64.0, 64.0
    # The largest granted tile is Canyon Works (96 x 112). This fallback is
    # used only when a terrain contract has not yet been generated.
    return 48.0, 56.0


def make_atlas(key, profile):
    # Blender image pixels are bottom-up. Work top-down so the selected strip
    # is the kit plate's actual engraved clouds and distant ridge, then flip
    # back before packing the texture. Crop out the town tower and right-edge
    # tree silhouettes; the panorama may contain no desert trees.
    kit = profile.get("kit", KIT)
    source = np.flipud(claim.image_pixels(kit))
    y0, y1 = int(source.shape[0] * 0.015), int(source.shape[0] * 0.145)
    x0, x1 = int(source.shape[1] * 0.36), int(source.shape[1] * 0.74)
    source = source[y0:y1, x0:x1, :]
    u = np.linspace(0.0, 1.0, ATLAS_SIZE, endpoint=False, dtype=np.float32)
    v = np.linspace(0.0, 1.0, ATLAS_SIZE, dtype=np.float32)
    uu, vv = np.meshgrid(u, v)

    # Sample four shifted areas of the shipped kit plate. The result is only a
    # source for paper colour and engraved ink; enlarging its painted cloud
    # masses directly was the v1 "Ceiling" failure.
    plate_sample = np.zeros((ATLAS_SIZE, ATLAS_SIZE, 3), dtype=np.float32)
    weight_total = np.zeros((ATLAS_SIZE, ATLAS_SIZE, 1), dtype=np.float32)
    for quadrant, (phase_offset, vertical_offset) in enumerate(zip(QUADRANT_PHASE_OFFSETS, QUADRANT_VERTICAL_OFFSETS)):
        center = 0.125 + quadrant * 0.25
        distance = np.abs(np.mod(u - center + 0.5, 1.0) - 0.5)
        weight = np.exp(-((distance / 0.19) ** 4)).astype(np.float32)
        x = mirrored_coordinates(u, source.shape[1], 2.0, profile["phase"] + phase_offset)
        warped_v = np.clip(vv + vertical_offset * smoothstep(0.14, 0.78, vv), 0.0, 1.0)
        y = warped_v * (source.shape[0] - 1)
        plate_sample += bilinear_sample(source, x, y) * weight[None, :, None]
        weight_total += weight[None, :, None]
    plate_sample /= weight_total

    tint = np.asarray(profile["tint"], dtype=np.float32)
    plate_luma = claim.luminance(plate_sample)
    surround = (
        np.roll(plate_luma, 3, axis=0)
        + np.roll(plate_luma, -3, axis=0)
        + np.roll(plate_luma, 3, axis=1)
        + np.roll(plate_luma, -3, axis=1)
    ) * 0.25
    plate_ink = np.clip((surround - plate_luma) * 8.0, 0.0, 1.0)
    # Long horizontal averaging removes the tree-like vertical combing that a
    # literal crop introduced while preserving the plate's eroded ink values.
    horizontal_ink = sum(np.roll(plate_ink, shift, axis=1) for shift in (-42, -28, -14, 0, 14, 28, 42)) / 7.0

    # PANORAMA LAW v2 / Ceiling: preserve dense engraving at the horizon but
    # quiet it continuously into near-plain parchment at the top of the ring.
    source_paper = np.mean(source[: max(1, source.shape[0] // 3)], axis=(0, 1))
    paper_value = float(claim.luminance(source_paper[None, None, :])[0, 0])
    # Keep the shipped plate's parchment value without multiplying its warm
    # chroma twice. The previous orange-on-orange treatment romanticised the
    # county into a holiday sunset instead of a hard, dusty working frontier.
    paper = paper_value * (0.56 + tint * 0.44)
    zenith = np.clip(paper * 1.08, 0.0, 0.92)
    lower_sky = np.clip(paper * 0.78, 0.0, 0.92)
    atlas = zenith[None, None, :] * (1.0 - vv[..., None]) + lower_sky[None, None, :] * vv[..., None]
    horizon_density = smoothstep(0.50, 0.83, vv)
    horizon_ink_strength = 0.020 if key in NIGHT_PANORAMAS - {"night-shift"} else 0.075
    atlas *= 1.0 - horizontal_ink[..., None] * (horizon_ink_strength * horizon_density[..., None])

    # PANORAMA LAW v2 / Echo: one deliberately different, horizontally quiet
    # cloud edit per quadrant. These use ink extracted from the shipped plate,
    # while their positions and silhouettes are map-specific edit decisions.
    map_index = list(PROFILES).index(key)
    cloud_heights = (0.47, 0.62, 0.53, 0.68)
    cloud_widths = (0.105, 0.135, 0.090, 0.120)
    cloud_mask = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
    for quadrant in range(4):
        center_u = (0.105 + quadrant * 0.25 + ((map_index * 2 + quadrant) % 5 - 2) * 0.009) % 1.0
        center_v = cloud_heights[(quadrant + map_index) % 4] + (map_index - 2) * 0.008
        width_u = cloud_widths[(quadrant * 3 + map_index) % 4]
        width_v = 0.032 + ((quadrant + map_index) % 3) * 0.009
        du = np.abs(np.mod(uu - center_u + 0.5, 1.0) - 0.5)
        primary = np.exp(-((du / width_u) ** 4) - (((vv - center_v) / width_v) ** 2))
        shoulder_u = (center_u + width_u * (0.28 if quadrant % 2 else -0.32)) % 1.0
        shoulder_du = np.abs(np.mod(uu - shoulder_u + 0.5, 1.0) - 0.5)
        shoulder = np.exp(-((shoulder_du / (width_u * 0.56)) ** 4) - (((vv - center_v + width_v * 0.42) / (width_v * 0.72)) ** 2))
        cloud_mask = np.maximum(cloud_mask, np.maximum(primary * 0.82, shoulder * 0.58))
    cloud_density = cloud_mask * smoothstep(0.29, 0.50, vv) * (1.0 - smoothstep(0.73, 0.84, vv))
    cloud_engraving = cloud_density * (0.24 + horizontal_ink * 0.76)
    cloud_strength = 0.46 if key in NIGHT_PANORAMAS - {"night-shift"} else 0.080
    atlas *= 1.0 - cloud_engraving[..., None] * cloud_strength
    if key == "dust-flats":
        # The E4 plate has strong rectangular value blocks. At panorama scale
        # they read as a stitched ceiling, so keep only a whisper of its ink
        # over a continuous parchment gradient; the asymmetric dust feature
        # below supplies the authored horizon character.
        atlas = zenith[None, None, :] * (1.0 - vv[..., None]) + lower_sky[None, None, :] * vv[..., None]
    if key in NIGHT_PANORAMAS - {"night-shift"}:
        # The E3 plate contains broad horizontal storm strata.  Literal use
        # turns a cylinder into stacked bands, so break them with four large,
        # deliberately unmatched weather masses before the calm zenith.
        weather = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        weather_outer = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        weather_features = (
            (0.08, 0.52, 0.105, 0.066),
            (0.34, 0.67, 0.078, 0.048),
            (0.61, 0.46, 0.125, 0.076),
            (0.87, 0.71, 0.086, 0.054),
        )
        shift = {"canyon-works": 0.0, "moth-season": 0.035, "blackout-ridge": -0.028, "fairground": 0.052, "glow-mesa": -0.046, "relay-valley": 0.074, "echo-canyon": -0.063, "ember-shore": -0.081}[key]
        for center_u, center_v, width_u, width_v in weather_features:
            du = np.abs(np.mod(uu - (center_u + shift) + 0.5, 1.0) - 0.5)
            weather = np.maximum(weather, np.exp(-((du / width_u) ** 4) - (((vv - center_v) / width_v) ** 2)))
            weather_outer = np.maximum(
                weather_outer,
                np.exp(-((du / (width_u * 1.16)) ** 4) - (((vv - center_v) / (width_v * 1.32)) ** 2)),
            )
        weather *= smoothstep(0.30, 0.47, vv) * (1.0 - smoothstep(0.76, 0.88, vv))
        weather_outer *= smoothstep(0.29, 0.45, vv) * (1.0 - smoothstep(0.78, 0.89, vv))
        weather_tone = np.clip(paper * 0.30 + np.asarray(profile["dark"], dtype=np.float32) * 0.92, 0.0, 0.92)
        weather_mix = 0.32 if key == "fairground" else 0.58
        atlas = atlas * (1.0 - weather[..., None] * weather_mix) + weather_tone[None, None, :] * weather[..., None] * weather_mix
        weather_rim = np.clip(weather_outer - weather * 0.86, 0.0, 1.0)
        weather_rim_tone = np.clip(paper * 1.16 + np.asarray(profile["tint"], dtype=np.float32) * 0.025, 0.0, 0.92)
        rim_mix = 0.16 if key == "fairground" else 0.28
        atlas = atlas * (1.0 - weather_rim[..., None] * rim_mix) + weather_rim_tone[None, None, :] * weather_rim[..., None] * rim_mix
    if key in {"relay-valley", "echo-canyon"}:
        # The E7 kit carries broad pale value bands that become a literal
        # ceiling when wrapped around a cylinder. Keep its walnut/teal signal
        # language, but rebuild the sky as a calm vertical gradient with four
        # small, unmatched horizon weather marks.
        zenith_color = np.asarray((0.050, 0.078, 0.076), dtype=np.float32)
        horizon_color = np.asarray((0.255, 0.190, 0.115), dtype=np.float32)
        atlas = zenith_color[None, None, :] * (1.0 - vv[..., None]) + horizon_color[None, None, :] * vv[..., None]
        atlas *= 1.0 - horizontal_ink[..., None] * (smoothstep(0.57, 0.84, vv) * 0.030)[..., None]
        relay_cloud = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        signal_clouds = (
            ((0.07, 0.77, 0.050, 0.020), (0.33, 0.72, 0.037, 0.016), (0.61, 0.80, 0.060, 0.022), (0.88, 0.74, 0.032, 0.015))
            if key == "relay-valley"
            else ((0.12, 0.75, 0.064, 0.018), (0.39, 0.81, 0.031, 0.014), (0.68, 0.70, 0.078, 0.024), (0.91, 0.79, 0.040, 0.016))
        )
        for center_u, center_v, width_u, width_v in signal_clouds:
            du = np.abs(np.mod(uu - center_u + 0.5, 1.0) - 0.5)
            centerline = center_v + np.sin((uu - center_u) * math.tau * 9.0) * 0.008
            relay_cloud = np.maximum(relay_cloud, np.exp(-((du / width_u) ** 4) - (((vv - centerline) / width_v) ** 2)))
        cloud_tone = np.asarray((0.025, 0.047, 0.046), dtype=np.float32)
        atlas = atlas * (1.0 - relay_cloud[..., None] * 0.46) + cloud_tone[None, None, :] * relay_cloud[..., None] * 0.46
    if key == "glow-mesa":
        # Panorama-only climate contrast: a thin inland-water gleam in one
        # quadrant, dust-dark plain in the opposite. Neither is a water mask
        # or a playable landform.
        zenith_color = np.asarray((0.075, 0.125, 0.140), dtype=np.float32)
        horizon_color = np.asarray((0.235, 0.185, 0.128), dtype=np.float32)
        atlas = zenith_color[None, None, :] * (1.0 - vv[..., None]) + horizon_color[None, None, :] * vv[..., None]
        atlas *= 1.0 - horizontal_ink[..., None] * (smoothstep(0.56, 0.84, vv) * 0.026)[..., None]
        cloud = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        for center_u, center_v, width_u, width_v in (
            (0.08, 0.79, 0.038, 0.016),
            (0.37, 0.75, 0.030, 0.014),
            (0.63, 0.82, 0.042, 0.017),
            (0.89, 0.77, 0.027, 0.013),
        ):
            du = np.abs(np.mod(uu - center_u + 0.5, 1.0) - 0.5)
            cloud = np.maximum(cloud, np.exp(-((du / width_u) ** 4) - (((vv - center_v) / width_v) ** 2)))
        cloud_tone = np.asarray((0.040, 0.068, 0.076), dtype=np.float32)
        atlas = atlas * (1.0 - cloud[..., None] * 0.25) + cloud_tone[None, None, :] * cloud[..., None] * 0.25
        inland_du = np.abs(np.mod(uu - 0.24 + 0.5, 1.0) - 0.5)
        inland = np.exp(-((inland_du / 0.038) ** 4) - (((vv - 0.80) / 0.012) ** 2))
        water_glint = np.asarray((0.26, 0.53, 0.52), dtype=np.float32)
        atlas = atlas * (1.0 - inland[..., None] * 0.24) + water_glint[None, None, :] * inland[..., None] * 0.24
        plain_du = np.abs(np.mod(uu - 0.74 + 0.5, 1.0) - 0.5)
        plain = np.exp(-((plain_du / 0.19) ** 4) - (((vv - 0.79) / 0.050) ** 2))
        dust_plain = np.asarray((0.095, 0.080, 0.070), dtype=np.float32)
        atlas = atlas * (1.0 - plain[..., None] * 0.34) + dust_plain[None, None, :] * plain[..., None] * 0.34
    if key == "mare-claim":
        # Vacuum negative space is an authored value field, not a cloud-filled
        # sky. Keep only a faint engraved horizon density and one Earth cameo
        # on the north / near-side quadrant (u=.75). The opposite u=.25 view
        # remains deliberately empty for the future Far Side contract.
        zenith_color = np.asarray((0.018, 0.020, 0.021), dtype=np.float32)
        horizon_color = np.asarray((0.068, 0.068, 0.064), dtype=np.float32)
        horizon_ramp = smoothstep(0.48, 0.92, vv)
        atlas = zenith_color[None, None, :] * (1.0 - horizon_ramp[..., None]) + horizon_color[None, None, :] * horizon_ramp[..., None]
        quiet_engraving = horizontal_ink * smoothstep(0.72, 0.91, vv)
        atlas *= 1.0 - quiet_engraving[..., None] * 0.055

        earth_du = np.abs(np.mod(uu - 0.75 + 0.5, 1.0) - 0.5)
        # The ring's horizontal coordinate is angular while v is linear height;
        # the narrow u radius projects as a round cameo from the playfield.
        earth_radius = np.sqrt((earth_du / 0.0105) ** 2 + ((vv - 0.52) / 0.064) ** 2)
        earth_disk = 1.0 - smoothstep(0.88, 1.02, earth_radius)
        earth_rim = np.exp(-(((earth_radius - 0.96) / 0.075) ** 2))
        earth_land = np.clip(
            np.sin((uu - 0.75) * 156.0 + vv * 27.0) * 0.38
            + np.sin((uu - 0.75) * 61.0 - vv * 43.0) * 0.28
            + 0.48,
            0.0,
            1.0,
        ) * earth_disk
        earth_ocean = np.asarray((0.14, 0.34, 0.38), dtype=np.float32)
        earth_land_tone = np.asarray((0.38, 0.50, 0.37), dtype=np.float32)
        earth_color = earth_ocean[None, None, :] * (1.0 - earth_land[..., None] * 0.58) + earth_land_tone[None, None, :] * earth_land[..., None] * 0.58
        atlas = atlas * (1.0 - earth_disk[..., None] * 0.96) + earth_color * earth_disk[..., None] * 0.96
        atlas = np.clip(atlas + earth_rim[..., None] * np.asarray((0.08, 0.16, 0.16), dtype=np.float32), 0.0, 0.92)
    if key == "ember-shore":
        # Deep Sky is still an engraved plate, not photoreal space. The sky is
        # mostly drawn emptiness: sparse stipple and four unequal warm nebula
        # edits fade into a quiet ink zenith rather than becoming a ceiling.
        zenith_color = np.asarray((0.010, 0.014, 0.017), dtype=np.float32)
        horizon_color = np.asarray((0.105, 0.050, 0.025), dtype=np.float32)
        horizon_ramp = smoothstep(0.44, 0.94, vv)
        atlas = zenith_color[None, None, :] * (1.0 - horizon_ramp[..., None]) + horizon_color[None, None, :] * horizon_ramp[..., None]
        star_noise = np.random.default_rng(1010).random((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        stars = smoothstep(0.99972, 0.99998, star_noise)
        stars = np.maximum.reduce((stars, np.roll(stars, 1, axis=0) * 0.52, np.roll(stars, 1, axis=1) * 0.52))
        stars *= 1.0 - smoothstep(0.58, 0.86, vv)
        star_tone = np.asarray((0.58, 0.48, 0.33), dtype=np.float32)
        atlas = atlas * (1.0 - stars[..., None] * 0.42) + star_tone[None, None, :] * stars[..., None] * 0.42
        nebula = np.zeros_like(vv)
        for center_u, center_v, width_u, width_v in (
            (0.08, 0.61, 0.072, 0.050),
            (0.34, 0.72, 0.110, 0.042),
            (0.63, 0.56, 0.058, 0.070),
            (0.89, 0.76, 0.086, 0.036),
        ):
            du = np.abs(np.mod(uu - center_u + 0.5, 1.0) - 0.5)
            broken_center = center_v + np.sin((uu - center_u) * math.tau * 7.0) * 0.016
            feature = np.exp(-((du / width_u) ** 4) - (((vv - broken_center) / width_v) ** 2))
            nebula = np.maximum(nebula, feature)
        nebula *= smoothstep(0.34, 0.50, vv) * (1.0 - smoothstep(0.84, 0.94, vv))
        nebula_tone = np.asarray((0.31, 0.15, 0.050), dtype=np.float32)
        atlas = atlas * (1.0 - nebula[..., None] * 0.48) + nebula_tone[None, None, :] * nebula[..., None] * 0.48
        nebula_ink = nebula * (0.36 + horizontal_ink * 0.64)
        atlas *= 1.0 - nebula_ink[..., None] * 0.16
    if key in OPEN_SEA_PANORAMAS:
        # Open sea has no mesa silhouettes to create depth. Four unmatched,
        # low wall-clouds carry the distance while the upper half stays calm.
        weather = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        for center_u, center_v, width_u, width_v in (
            (0.10, 0.70, 0.15, 0.045),
            (0.38, 0.61, 0.09, 0.032),
            (0.63, 0.73, 0.18, 0.052),
            (0.88, 0.64, 0.075, 0.028),
        ):
            du = np.abs(np.mod(uu - center_u + 0.5, 1.0) - 0.5)
            weather = np.maximum(weather, np.exp(-((du / width_u) ** 4) - (((vv - center_v) / width_v) ** 2)))
        weather *= smoothstep(0.48, 0.59, vv) * (1.0 - smoothstep(0.79, 0.88, vv))
        tea_storm = np.asarray((0.035, 0.065, 0.068), dtype=np.float32)
        atlas = atlas * (1.0 - weather[..., None] * 0.72) + tea_storm[None, None, :] * weather[..., None] * 0.72

    # One low, asymmetric wind-scoured dust feature per contract hardens the
    # frontier mood without adding a ceiling or a repeated 360-degree strip.
    dust_center, dust_width, dust_strength = profile["dust"]
    dust_distance = np.abs(np.mod(uu - dust_center + 0.5, 1.0) - 0.5)
    dust_centerline = (0.81 if key == "glow-mesa" else 0.69) + np.sin(uu * math.tau + profile["phase"] * math.tau) * (0.018 if key == "glow-mesa" else 0.038)
    dust_plume = np.exp(-((dust_distance / dust_width) ** 4) - (((vv - dust_centerline) / (0.030 if key == "glow-mesa" else 0.055)) ** 2))
    dust_plume *= 0.45 + horizontal_ink * 0.55
    dust_tone = np.clip(np.asarray(profile["dark"], dtype=np.float32) * 0.48 + paper * 0.38, 0.0, 0.92)
    atlas = atlas * (1.0 - dust_plume[..., None] * dust_strength) + dust_tone[None, None, :] * dust_plume[..., None] * dust_strength

    ridge = distant_ridge_height(key, uu)
    ridge_boundary = 1.0 - ridge
    ridge_mask = smoothstep(ridge_boundary - 0.010, ridge_boundary + 0.014, vv)
    if key in {"glow-mesa", "relay-valley", "echo-canyon", "mare-claim", "ember-shore"}:
        # These panoramas carry their depth in physical, independently broken
        # ridge silhouettes. Painting the same profile into the sky atlas made
        # a continuous bright cyclorama wall behind them.
        ridge_mask = np.zeros_like(ridge_mask)
    dark = np.asarray(profile["dark"], dtype=np.float32)
    ridge_base = dark * 0.46 + paper * 0.31
    # PANORAMA LAW v2 / Painted Wall: the physical foreground ridge hides the
    # sky-ring foot; this light dust band makes the remaining join atmospheric.
    above_ridge = ridge_boundary - vv
    haze = np.exp(-(((above_ridge - 0.045) / 0.055) ** 2)) * (1.0 - ridge_mask)
    haze_tone = np.clip(paper * 0.88 + tint * 0.07, 0.0, 0.92)
    if key == "glow-mesa":
        # The generic pale paper haze followed the hidden far-ridge profile
        # closely enough to read as a luminous painted ribbon.  E6 keeps only
        # a low, dust-coloured atmospheric trace; the physical broken ridge
        # and the one-way inland-water glint must carry the distance verdict.
        haze *= 0.10
        haze_tone = np.asarray((0.155, 0.125, 0.095), dtype=np.float32)
    elif key in {"relay-valley", "echo-canyon"}:
        haze *= 0.14
        haze_tone = np.asarray((0.105, 0.092, 0.068), dtype=np.float32)
    elif key == "mare-claim":
        # No atmosphere means no dusty transition band. The physical near and
        # far lunar ridges plus matched ground skirt carry the join.
        haze *= 0.0
        haze_tone = np.asarray((0.085, 0.085, 0.080), dtype=np.float32)
    elif key == "ember-shore":
        haze *= 0.08
        haze_tone = np.asarray((0.135, 0.066, 0.030), dtype=np.float32)
    broad_plate = sum(np.roll(plate_luma, shift, axis=1) for shift in (-64, -32, 0, 32, 64)) / 5.0
    ridge_variation = np.clip(0.96 + (broad_plate - np.mean(broad_plate)) * 0.22, 0.88, 1.04)
    ridge_depth = smoothstep(ridge_boundary - 0.004, ridge_boundary + 0.10, vv)
    ridge_base_weight = 0.18 + ridge_depth * 0.64
    ridge_tone = haze_tone[None, None, :] * (1.0 - ridge_base_weight[..., None]) + ridge_base[None, None, :] * ridge_base_weight[..., None]
    ridge_color = ridge_tone * ridge_variation[..., None]
    atlas = atlas * (1.0 - haze[..., None] * 0.78) + haze_tone[None, None, :] * haze[..., None] * 0.78
    atlas = atlas * (1.0 - ridge_mask[..., None]) + ridge_color * ridge_mask[..., None]

    # Reserve the atlas foot for the nearer occluding ridge. A dusty, eroded
    # midtone keeps this belt from becoming the matte black wall that a second
    # copy of the far-ridge ink produced in the first v2 build.
    near_band = smoothstep(0.83, 0.89, vv)
    near_depth = smoothstep(0.84, 1.0, vv)
    near_base = paper * 0.51 + dark * 0.22
    near_color = haze_tone[None, None, :] * (1.0 - near_depth[..., None]) + near_base[None, None, :] * near_depth[..., None]
    near_erosion = np.clip(0.91 + (broad_plate - np.mean(broad_plate)) * 0.72, 0.78, 1.07)
    near_color *= near_erosion[..., None]
    terrain_atlas_path = OUT / f"{key}-terrain-atlas.png"
    if terrain_atlas_path.is_file():
        terrain_source = claim.image_pixels(terrain_atlas_path)
        terrain_detail = claim.tiled_sample(terrain_source, uu, vv, 3.1, profile["phase"] + 0.13, 0.29)
        ground_scale = 0.36 if key == "blackout-ridge" else (0.70 if key == "dust-flats" else 0.56)
        near_color = near_color * 0.66 + terrain_detail * ground_scale * 0.34
        if key == "glow-mesa":
            # Beyond the one-metre seam transition this is dry county earth,
            # not teal water. Keep the terrain's engraved detail but restore
            # the E6 plate's parchment/soot value structure.
            dry_county = paper * np.asarray((0.58, 0.43, 0.30), dtype=np.float32) + dark * 0.34
            near_color = near_color * 0.42 + dry_county[None, None, :] * 0.58
        elif key == "echo-canyon":
            # The long north/south mouths expose far more apron than Relay
            # Valley. Keep that continuation in engraved walnut loam instead
            # of letting the dark signal sky texture read as a void.
            canyon_ground = np.asarray((0.245, 0.205, 0.150), dtype=np.float32)
            near_color = near_color * 0.34 + canyon_ground[None, None, :] * 0.66
        elif key == "mare-claim":
            lunar_ground = np.asarray((0.245, 0.250, 0.238), dtype=np.float32)
            near_color = near_color * 0.48 + lunar_ground[None, None, :] * 0.52
        elif key == "ember-shore":
            cooled_ground = np.asarray((0.078, 0.060, 0.050), dtype=np.float32)
            near_color = near_color * 0.48 + cooled_ground[None, None, :] * 0.52
        # The skirt's inner row traces the actual rectangular tile boundary.
        # Sample that same terrain-atlas boundary as a function of panorama
        # angle so the join preserves both value and local painted grit instead
        # of advertising the square footprint with a different material.
        half_x, half_z = playfield_half_extents(key)
        angle = uu * math.tau
        cos_angle, sin_angle = np.cos(angle), np.sin(angle)
        hit_x = half_x / np.maximum(np.abs(cos_angle), 1e-6)
        hit_z = half_z / np.maximum(np.abs(sin_angle), 1e-6)
        boundary_radius = np.minimum(hit_x, hit_z)
        boundary_x = cos_angle * boundary_radius
        boundary_z = (-sin_angle if key in OPEN_SEA_PANORAMAS or key in {"fairground", "glow-mesa", "relay-valley", "echo-canyon", "mare-claim", "ember-shore"} else sin_angle) * boundary_radius
        terrain_u = np.clip(boundary_x / (half_x * 2.0) + 0.5, 0.0, 1.0)
        terrain_v = np.clip(boundary_z / (half_z * 2.0) + 0.5, 0.0, 1.0)
        sample_x = np.clip((terrain_u * (terrain_source.shape[1] - 1)).astype(np.int32), 0, terrain_source.shape[1] - 1)
        sample_y = np.clip((terrain_v * (terrain_source.shape[0] - 1)).astype(np.int32), 0, terrain_source.shape[0] - 1)
        border_detail = terrain_source[sample_y, sample_x]
        # Keep only broad edge colour/ink continuity.  High-frequency pixels
        # stretched away from the boundary become radial spokes, which are as
        # artificial as the seam they replace.
        border_detail = sum(
            np.roll(border_detail, shift, axis=1)
            for shift in (-64, -40, -24, -12, 0, 12, 24, 40, 64)
        ) / 9.0
        # The panorama exposure is baked after this composition step.  Undo it
        # here so the final boundary retains the terrain atlas value instead of
        # becoming a bright night halo or a dark motor-era moat.
        border_detail /= max(float(profile["strength"]), 0.001)
        seam_weight = smoothstep(0.935, 0.985, vv)[..., None]
        near_color = near_color * (1.0 - seam_weight) + border_detail * seam_weight
    atlas = atlas * (1.0 - near_band[..., None]) + near_color * near_band[..., None]

    if key in NIGHT_PANORAMAS:
        center = {"night-shift": 0.58, "canyon-works": 0.46, "moth-season": 0.67, "blackout-ridge": 0.53, "fairground": 0.41, "glow-mesa": 0.76, "relay-valley": 0.31, "echo-canyon": 0.69, "ember-shore": 0.57}[key]
        width = 0.080 if key == "fairground" else (0.055 if key == "night-shift" else 0.040)
        strength = 0.07 if key == "glow-mesa" else (0.10 if key == "fairground" else (0.18 if key == "ember-shore" else (0.34 if key == "night-shift" else 0.22)))
        warm_break = np.exp(-((uu - center) / width) ** 2) * smoothstep(0.64, 0.84, vv) * (1.0 - ridge_mask)
        atlas = atlas * (1.0 - warm_break[..., None] * strength) + np.array((0.65, 0.20, 0.055))[None, None, :] * warm_break[..., None] * strength

    if key in OPEN_SEA_PANORAMAS:
        # The generic county treatment intentionally uses low ridge belts.
        # Deepwater has no confirming coast, so replace it with a clean sea-sky
        # gradient, four separate storm cells, one haze line, and two tiny
        # wreck-mast suggestions at mystery-law scale.
        zenith_color = np.asarray((0.36, 0.40, 0.37), dtype=np.float32)
        horizon_color = np.asarray((0.18, 0.24, 0.23), dtype=np.float32)
        atlas = zenith_color[None, None, :] * (1.0 - vv[..., None]) + horizon_color[None, None, :] * vv[..., None]
        atlas *= 1.0 - horizontal_ink[..., None] * (smoothstep(0.48, 0.82, vv) * 0.035)[..., None]
        weather = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        for center_u, center_v, width_u, width_v in (
            (0.09, 0.36, 0.082, 0.078),
            (0.34, 0.45, 0.061, 0.054),
            (0.62, 0.31, 0.071, 0.090),
            (0.88, 0.40, 0.064, 0.062),
        ):
            du = np.abs(np.mod(uu - center_u + 0.5, 1.0) - 0.5)
            broken_center = center_v + np.sin((uu - center_u) * math.tau * 7.0) * 0.014 + np.sin((uu + center_u) * math.tau * 13.0) * 0.006
            weather = np.maximum(weather, np.exp(-((du / width_u) ** 4) - (((vv - broken_center) / width_v) ** 2)))
        storm_tone = np.asarray((0.075, 0.115, 0.116), dtype=np.float32)
        atlas = atlas * (1.0 - weather[..., None] * 0.62) + storm_tone[None, None, :] * weather[..., None] * 0.62
        mast_mask = np.zeros_like(vv)
        for center_u, width, height in ((0.17, 0.0022, 0.045), (0.71, 0.0018, 0.034)):
            du = np.abs(np.mod(uu - center_u + 0.5, 1.0) - 0.5)
            mast_mask = np.maximum(mast_mask, np.exp(-((du / width) ** 2)) * smoothstep(0.82 - height, 0.82, vv) * (1.0 - smoothstep(0.84, 0.86, vv)))
        atlas *= 1.0 - mast_mask[..., None] * 0.62
        terrain_atlas_path = OUT / f"{key}-terrain-atlas.png"
        if terrain_atlas_path.is_file():
            terrain_source = claim.image_pixels(terrain_atlas_path)
            submerged_ground = claim.tiled_sample(terrain_source, uu, vv, 3.7, 0.41, 0.16)
            submerged_ground = np.clip(submerged_ground * np.asarray((0.48, 0.62, 0.62), dtype=np.float32), 0.006, 0.40)
            ground_band = smoothstep(0.80, 0.92, vv)
            atlas = atlas * (1.0 - ground_band[..., None]) + submerged_ground * ground_band[..., None]
            # The sea treatment replaces the generic atlas above; retain its terrain-edge match.
            atlas = atlas * (1.0 - seam_weight) + border_detail * seam_weight

    # Bake the map-specific panorama exposure into the pixels. Blender's glTF
    # exporter converts this material to KHR_materials_unlit, which deliberately
    # has no Background Strength socket; keeping the multiplier here makes the
    # authored value survive in the mounted GLB instead of only in .blend renders.
    atlas = np.flipud(np.clip(atlas * profile["strength"], 0.006, 0.92))
    rgba = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    rgba[:, :, :3] = atlas
    path = OUT / f"{key}-panorama-atlas.png"
    image = bpy.data.images.new(f"{key.title().replace('-', '')}PanoramaAtlas", ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image, path


def make_material(key, atlas, profile):
    material = bpy.data.materials.new(f"{key.title().replace('-', '')}PanoramaMaterial")
    material.use_nodes = True
    material.use_backface_culling = False
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    texture = nodes.new("ShaderNodeTexImage")
    vertex_color = nodes.new("ShaderNodeVertexColor")
    vertex_color.layer_name = "PanoramaTint"
    multiply = nodes.new("ShaderNodeMix")
    multiply.data_type = "RGBA"
    multiply.blend_type = "MULTIPLY"
    multiply.inputs["Factor"].default_value = 1.0
    texture.image = atlas
    texture.extension = "REPEAT"
    texture.interpolation = "Linear"
    material.node_tree.links.new(texture.outputs["Color"], multiply.inputs[6])
    material.node_tree.links.new(vertex_color.outputs["Color"], multiply.inputs[7])
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Roughness"].default_value = 1.0
    shader.inputs["Metallic"].default_value = 0.0
    emission_color = shader.inputs.get("Emission Color") or shader.inputs.get("Emission")
    emission_strength = shader.inputs.get("Emission Strength")
    if emission_strength:
        # Keep the sky ring unlit enough to avoid the five mesh rows becoming
        # horizontal lighting bands. Value matching now lives in the baked E6
        # atlas and dry ground skirt, not in scene-dependent cylinder shading.
        emission_strength.default_value = 1.0
    material.node_tree.links.new(multiply.outputs[2], shader.inputs["Base Color"])
    if emission_color:
        material.node_tree.links.new(multiply.outputs[2], emission_color)
    material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def make_ring(key, material):
    vertices = []
    uvs = []
    colors = []
    faces = []
    open_sea_height_at = None
    fairground_height_at = None
    glow_mesa_height_at = None
    relay_valley_height_at = None
    echo_canyon_height_at = None
    mare_claim_height_at = None
    ember_shore_height_at = None
    if key in OPEN_SEA_PANORAMAS:
        terrain_script = "build_e5_deepwater_terrain.py" if key == "deepwater-claim" else "build_e5_regatta_terrain.py"
        terrain_spec = importlib.util.spec_from_file_location(f"panorama_{key}_height", OUT / terrain_script)
        terrain_module = importlib.util.module_from_spec(terrain_spec)
        terrain_spec.loader.exec_module(terrain_module)
        _factory, open_sea_table = terrain_module.documents()
        open_sea_height_at = terrain_module.height_function(open_sea_table)
    elif key == "fairground":
        terrain_spec = importlib.util.spec_from_file_location("panorama_fairground_height", OUT / "build_e3_contract_terrains.py")
        terrain_module = importlib.util.module_from_spec(terrain_spec)
        terrain_spec.loader.exec_module(terrain_module)
        fairground_factory = terrain_module.factory_contract("e3-fairground")
        fairground_table, _table_path = terrain_module.mask_table("e3-fairground")
        fairground_height_at = terrain_module.height_function("fairground", fairground_factory, fairground_table)
    elif key == "glow-mesa":
        terrain_spec = importlib.util.spec_from_file_location("panorama_glow_mesa_height", OUT / "build_e3_contract_terrains.py")
        terrain_module = importlib.util.module_from_spec(terrain_spec)
        terrain_spec.loader.exec_module(terrain_module)
        glow_factory = terrain_module.factory_contract("e6-glow-mesa")
        glow_table, _table_path = terrain_module.mask_table("e6-glow-mesa")
        glow_mesa_height_at = terrain_module.height_function("glow-mesa", glow_factory, glow_table)
    elif key == "relay-valley":
        terrain_spec = importlib.util.spec_from_file_location("panorama_relay_valley_height", OUT / "build_e3_contract_terrains.py")
        terrain_module = importlib.util.module_from_spec(terrain_spec)
        terrain_spec.loader.exec_module(terrain_module)
        relay_factory = terrain_module.factory_contract("e7-relay-valley")
        relay_table, _table_path = terrain_module.mask_table("e7-relay-valley")
        relay_valley_height_at = terrain_module.height_function("relay-valley", relay_factory, relay_table)
    elif key == "echo-canyon":
        terrain_spec = importlib.util.spec_from_file_location("panorama_echo_canyon_height", OUT / "build_e3_contract_terrains.py")
        terrain_module = importlib.util.module_from_spec(terrain_spec)
        terrain_spec.loader.exec_module(terrain_module)
        echo_factory = terrain_module.factory_contract("e7-echo-canyon")
        echo_table, _table_path = terrain_module.mask_table("e7-echo-canyon")
        echo_canyon_height_at = terrain_module.height_function("echo-canyon", echo_factory, echo_table)
    elif key == "mare-claim":
        terrain_spec = importlib.util.spec_from_file_location("panorama_mare_claim_height", OUT / "build_e3_contract_terrains.py")
        terrain_module = importlib.util.module_from_spec(terrain_spec)
        terrain_spec.loader.exec_module(terrain_module)
        mare_factory = terrain_module.factory_contract("e8-mare-claim")
        mare_table, _table_path = terrain_module.mask_table("e8-mare-claim")
        mare_claim_height_at = terrain_module.height_function("mare-claim", mare_factory, mare_table)
    elif key == "ember-shore":
        terrain_spec = importlib.util.spec_from_file_location("panorama_ember_shore_height", OUT / "build_e3_contract_terrains.py")
        terrain_module = importlib.util.module_from_spec(terrain_spec)
        terrain_spec.loader.exec_module(terrain_module)
        ember_factory = terrain_module.factory_contract("e10-ember-shore")
        ember_table, _table_path = terrain_module.mask_table("e10-ember-shore")
        ember_shore_height_at = terrain_module.height_function("ember-shore", ember_factory, ember_table)
    for row in range(ROWS):
        v = row / (ROWS - 1)
        sky_bottom = -160.0 if key in OPEN_SEA_PANORAMAS else SKY_BOTTOM
        height = sky_bottom + v * (SKY_TOP - sky_bottom)
        # Open water exposes every horizontal change in the sky cylinder as a
        # false dome reflected on the sea. Keep this ring truly cylindrical;
        # county maps retain the subtle bulge behind their ridge belts.
        radius = RADIUS if key in OPEN_SEA_PANORAMAS else RADIUS + math.sin(v * math.pi) * 3.0
        for index in range(SEGMENTS + 1):
            u = index / SEGMENTS
            angle = u * math.tau
            vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, height))
            uvs.append((u, v))
            colors.append((1.0, 1.0, 1.0, 1.0))
    width = SEGMENTS + 1
    for row in range(ROWS - 1):
        for index in range(SEGMENTS):
            a = row * width + index
            b = a + 1
            c = (row + 1) * width + index + 1
            d = c - 1
            faces.extend([(a, c, b), (a, d, c)])

    # A lower, farther ridge uses the independent distant profile. It becomes
    # visible through cuts in the foreground belt, giving the center-horizon
    # gate real layer separation instead of one cylindrical wall.
    if key in FAR_RIDGE_PANORAMAS:
        far_start = len(vertices)
        for row in range(2):
            for index in range(SEGMENTS + 1):
                u = index / SEGMENTS
                angle = u * math.tau
                fraction = float(distant_ridge_height(key, np.asarray(u, dtype=np.float32)))
                # Echo Canyon's north/south openings expose this belt almost
                # down to the apron.  Sinking its foot to SKY_BOTTOM created
                # a tall black retaining wall instead of a distant ridge, so
                # meet the render-only ground skirt at county-floor height.
                height = (0.16 if key == "echo-canyon" else SKY_BOTTOM) if row == 0 else ((3.2 + fraction * 34.0) if key == "dust-flats" else ((6.0 + fraction * 52.0) if key == "fairground" else ((4.0 + fraction * 38.0) if key == "mare-claim" else ((3.4 + fraction * 42.0) if key == "ember-shore" else (8.0 + fraction * 55.0)))))
                radius = FAR_RIDGE_FOOT_RADIUS if row == 0 else FAR_RIDGE_CREST_RADIUS
                vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, height))
                uvs.append((u, (0.030 if row == 0 else 0.105) if key == "echo-canyon" else (0.0 if row == 0 else (0.075 if key == "mare-claim" else (0.24 if key == "relay-valley" else 0.72)))))
                if key == "echo-canyon":
                    colors.append((1.45, 1.18, 0.82, 1.0) if row == 0 else (1.10, 0.92, 0.70, 1.0))
                elif key == "relay-valley":
                    colors.append((0.11, 0.10, 0.08, 1.0) if row == 0 else (0.24, 0.21, 0.15, 1.0))
                elif key == "mare-claim":
                    colors.append((0.22, 0.23, 0.22, 1.0) if row == 0 else (0.62, 0.64, 0.60, 1.0))
                elif key == "ember-shore":
                    colors.append((0.12, 0.060, 0.035, 1.0) if row == 0 else (0.35, 0.16, 0.070, 1.0))
                else:
                    colors.append((0.74, 0.79, 0.90, 1.0) if row == 0 else (0.96, 0.92, 0.82, 1.0))
        for index in range(SEGMENTS):
            a = far_start + index
            b = a + 1
            d = far_start + width + index
            c = d + 1
            faces.extend([(a, c, b), (a, d, c)])

    # A closer irregular ridge belt occludes the sunk sky ring. It remains in
    # this one panorama mesh/material and carries no terrain or sim authority.
    ridge_start = len(vertices)
    for row in range(2):
        for index in range(SEGMENTS + 1):
            u = index / SEGMENTS
            angle = u * math.tau
            fraction = float(ridge_height(key, np.asarray(u, dtype=np.float32)))
            height = -80.0 if key in OPEN_SEA_PANORAMAS else (
                (0.18 if key == "echo-canyon" else SKY_BOTTOM)
                if row == 0
                else (
                    (2.8 + fraction * 38.0)
                    if key == "fairground"
                    else ((2.6 + fraction * 43.0) if key == "glow-mesa" else ((3.4 + fraction * 48.0) if key in {"relay-valley", "echo-canyon"} else ((3.0 + fraction * 44.0) if key == "mare-claim" else ((2.8 + fraction * 46.0) if key == "ember-shore" else RIDGE_TOP_BASE + fraction * RIDGE_TOP_SCALE))))
                )
            )
            radius = (RIDGE_FOOT_RADIUS if row == 0 else RIDGE_CREST_RADIUS) + math.sin(angle * 3.0 + 0.4) * 1.7
            vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, height))
            # The mesh silhouette owns the ridge shape; a constant texture band
            # avoids re-projecting the far ridge profile onto this nearer one.
            crest_sample = 0.070 if key == "mare-claim" else (0.20 if key in LAYERED_PANORAMAS else 0.12)
            uvs.append((u, (0.030 if row == 0 else 0.105) if key == "echo-canyon" else (0.0 if row == 0 else crest_sample)))
            if key in {"pressure-garden", "incline", "dust-flats"}:
                # E2 sunset lighting exaggerates blue vertex tint into a
                # holiday-purple dome.  Keep the steamworks county in dusty
                # umber and soot while the atlas still supplies the engraving.
                colors.append((0.31, 0.24, 0.17, 1.0) if row == 0 else (0.44, 0.33, 0.22, 1.0))
            elif key in OPEN_SEA_PANORAMAS:
                colors.append((0.18, 0.32, 0.34, 1.0) if row == 0 else (0.34, 0.48, 0.47, 1.0))
            elif key == "fairground":
                colors.append((0.30, 0.30, 0.35, 1.0) if row == 0 else (0.50, 0.47, 0.46, 1.0))
            elif key == "glow-mesa":
                # Read as far caprock against the dusty sky, never as the
                # inner edge of a teal water bowl.
                colors.append((0.15, 0.12, 0.095, 1.0) if row == 0 else (0.34, 0.28, 0.21, 1.0))
            elif key == "echo-canyon":
                colors.append((1.55, 1.22, 0.82, 1.0) if row == 0 else (1.18, 0.96, 0.72, 1.0))
            elif key == "relay-valley":
                colors.append((0.09, 0.09, 0.075, 1.0) if row == 0 else (0.22, 0.20, 0.15, 1.0))
            elif key == "mare-claim":
                colors.append((0.24, 0.25, 0.24, 1.0) if row == 0 else (0.68, 0.70, 0.66, 1.0))
            elif key == "ember-shore":
                colors.append((0.075, 0.050, 0.040, 1.0) if row == 0 else (0.31, 0.13, 0.055, 1.0))
            else:
                colors.append((0.40, 0.46, 0.58, 1.0) if row == 0 else (0.58, 0.64, 0.76, 1.0))
    for index in range(SEGMENTS):
        a = ridge_start + index
        b = a + 1
        d = ridge_start + width + index
        c = d + 1
        faces.extend([(a, c, b), (a, d, c)])

    # A low county-ground skirt removes the black void between a rectangular
    # playfield and the circular ridge. Its polar inner row traces an expanded
    # rectangle, so there is no circular moat and no scenery vertex enters the
    # playable footprint.
    skirt_start = len(vertices)
    skirt_segments = 96
    half_x, half_z = playfield_half_extents(key)
    # Meet the render tile at its exact footprint.  The previous one-metre
    # safety gap was legal for the simulation but exposed a black rectangular
    # moat in overview renders, making the tile look like a tabletop.  These
    # vertices remain scenery-only and never enter the playable footprint.
    skirt_margin = 0.01
    # The two close inner rows confine boundary-matched texture to a narrow
    # transition rather than stretching it across the whole county apron.
    skirt_rows = (
        ((0.0, 0.028), (0.022, 0.040), (0.30, 0.070), (0.66, 0.116), (1.0, 0.16))
        if key == "echo-canyon"
        else (((0.0, 0.028), (0.015, 0.036), (0.34, 0.064), (1.0, 0.094)) if key == "glow-mesa" else (((0.0, 0.028), (0.018, 0.038), (0.30, 0.070), (0.68, 0.120), (1.0, 0.16)) if key in {"mare-claim", "ember-shore"} else (((0.0, 0.028), (0.022, 0.040), (0.30, 0.070), (0.66, 0.116), (1.0, 0.16)) if key == "relay-valley" else ((0.0, 0.028), (0.035, 0.045), (0.28, 0.076), (0.64, 0.118), (1.0, 0.16)))))
    )
    for row, (outward, texture_v) in enumerate(skirt_rows):
        for index in range(skirt_segments + 1):
            u = index / skirt_segments
            angle = u * math.tau
            cos_angle, sin_angle = abs(math.cos(angle)), abs(math.sin(angle))
            hit_x = (half_x + skirt_margin) / max(cos_angle, 1e-6)
            hit_z = (half_z + skirt_margin) / max(sin_angle, 1e-6)
            inner_radius = min(hit_x, hit_z)
            skirt_outer_radius = RADIUS if key in OPEN_SEA_PANORAMAS else RIDGE_FOOT_RADIUS
            radius = inner_radius + (skirt_outer_radius - inner_radius) * outward
            if key in OPEN_SEA_PANORAMAS:
                game_z = -math.sin(angle) * inner_radius
                inner_height = float(open_sea_height_at(math.cos(angle) * inner_radius, game_z))
                outer_height = (
                    (-8.35 if inner_height < -6.0 else -6.15)
                    + math.sin(angle * 5.0 + 0.7) * 0.36
                    + math.sin(angle * 11.0 - 0.4) * 0.14
                )
            elif key == "fairground":
                game_x = math.cos(angle) * inner_radius
                game_z = -math.sin(angle) * inner_radius
                inner_height = float(fairground_height_at(game_x, game_z))
                outer_height = 0.16 + math.sin(angle * 3.0 + 0.6) * 0.16 + math.sin(angle * 8.0 - 0.4) * 0.07
            elif key == "glow-mesa":
                game_x = math.cos(angle) * inner_radius
                game_z = -math.sin(angle) * inner_radius
                inner_height = float(glow_mesa_height_at(game_x, game_z)) + 0.01
                outer_height = 0.42 + math.sin(angle * 4.0 + 0.7) * 0.20 + math.sin(angle * 9.0 - 0.3) * 0.08
            elif key == "relay-valley":
                game_x = math.cos(angle) * inner_radius
                game_z = -math.sin(angle) * inner_radius
                inner_height = float(relay_valley_height_at(game_x, game_z)) + 0.01
                outer_height = 0.24 + math.sin(angle * 3.0 + 0.5) * 0.22 + math.sin(angle * 9.0 - 0.2) * 0.09
            elif key == "echo-canyon":
                game_x = math.cos(angle) * inner_radius
                game_z = -math.sin(angle) * inner_radius
                inner_height = float(echo_canyon_height_at(game_x, game_z)) + 0.01
                outer_height = 0.20 + math.sin(angle * 4.0 - 0.3) * 0.20 + math.sin(angle * 11.0 + 0.5) * 0.08
            elif key == "mare-claim":
                game_x = math.cos(angle) * inner_radius
                game_z = -math.sin(angle) * inner_radius
                inner_height = float(mare_claim_height_at(game_x, game_z)) + 0.01
                outer_height = 0.18 + math.sin(angle * 4.0 + 0.5) * 0.12 + math.sin(angle * 11.0 - 0.2) * 0.05
            elif key == "ember-shore":
                game_x = math.cos(angle) * inner_radius
                game_z = -math.sin(angle) * inner_radius
                inner_height = float(ember_shore_height_at(game_x, game_z)) + 0.01
                outer_height = 0.10 + math.sin(angle * 4.0 + 0.7) * 0.10 + math.sin(angle * 11.0 - 0.4) * 0.05
            else:
                inner_height = 0.18 if key == "blackout-ridge" else (0.34 if key == "dust-flats" else -0.14)
                outer_height = -0.14 - (RIDGE_FOOT_RADIUS - 46.0) * 0.007
            # Several low, asymmetric county drifts break the old smooth
            # annulus without turning the panorama into collision terrain.
            drift = (
                math.sin(angle * 3.0 + 0.6) * 0.58
                + math.sin(angle * 7.0 - 0.9) * 0.31
                + math.sin(angle * 13.0 + 0.2) * 0.12
            ) * math.sin(outward * math.pi)
            if key == "blackout-ridge":
                drift += math.exp(-((u - 0.12) / 0.11) ** 2) * 0.92 * math.sin(outward * math.pi)
            elif key == "dust-flats":
                drift += math.exp(-((u - 0.69) / 0.15) ** 2) * 0.74 * math.sin(outward * math.pi)
            elif key == "fairground":
                drift = drift * 0.38 + (
                    math.exp(-((u - 0.16) / 0.10) ** 2) * 1.15
                    + math.exp(-((u - 0.68) / 0.13) ** 2) * 0.84
                ) * math.sin(outward * math.pi) * 0.34
            elif key == "glow-mesa":
                drift = drift * 0.78 + (
                    math.exp(-((u - 0.24) / 0.13) ** 2) * -0.64
                    + math.exp(-((u - 0.73) / 0.18) ** 2) * 0.66
                ) * math.sin(outward * math.pi)
            elif key in {"relay-valley", "echo-canyon"}:
                drift = drift * 0.70 + (
                    math.exp(-((u - 0.14) / 0.12) ** 2) * 0.74
                    - math.exp(-((u - 0.35) / 0.08) ** 2) * 0.68
                    + math.exp(-((u - 0.66) / 0.13) ** 2) * 0.58
                ) * math.sin(outward * math.pi)
            elif key == "mare-claim":
                drift = drift * 0.34 + (
                    math.exp(-((u - 0.11) / 0.09) ** 2) * 0.32
                    - math.exp(-((u - 0.42) / 0.07) ** 2) * 0.24
                    + math.exp(-((u - 0.69) / 0.12) ** 2) * 0.28
                ) * math.sin(outward * math.pi)
            elif key == "ember-shore":
                drift = drift * 0.40 + (
                    math.exp(-((u - 0.16) / 0.10) ** 2) * 0.34
                    - math.exp(-((u - 0.43) / 0.07) ** 2) * 0.26
                    + math.exp(-((u - 0.72) / 0.12) ** 2) * 0.30
                ) * math.sin(outward * math.pi)
            if key in OPEN_SEA_PANORAMAS:
                drift *= 0.55 + outward * 0.65
            height = inner_height * (1.0 - outward) + outer_height * outward + drift
            vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, height))
            uvs.append((u, texture_v))
            # The inner row must preserve the terrain atlas value at the seam;
            # colour grading only grows toward the distant ridge.
            if row == 0:
                colors.append((1.0, 1.0, 1.0, 1.0))
            elif key == "dust-flats":
                ground_tint = 0.88 + outward * 0.08
                colors.append((ground_tint * 0.70, ground_tint * 0.58, ground_tint * 0.42, 1.0))
            elif key == "blackout-ridge":
                ground_tint = 0.88 + outward * 0.08
                colors.append((ground_tint * 0.64, ground_tint * 0.72, ground_tint * 0.86, 1.0))
            elif key in OPEN_SEA_PANORAMAS:
                ground_tint = 0.86 + outward * 0.10
                colors.append((ground_tint * 0.42, ground_tint * 0.67, ground_tint * 0.68, 1.0))
            elif key == "fairground":
                ground_tint = 0.76 - outward * 0.13
                colors.append((ground_tint * 0.55, ground_tint * 0.57, ground_tint * 0.62, 1.0))
            elif key == "glow-mesa":
                # Move from the exact terrain boundary into dry parchment and
                # soot. The old teal grade looked like a circular water moat.
                ground_tint = 0.76 - outward * 0.16
                colors.append((ground_tint * 0.72, ground_tint * 0.60, ground_tint * 0.46, 1.0))
            elif key == "echo-canyon":
                ground_tint = 0.92 - outward * 0.08
                colors.append((ground_tint * 1.75, ground_tint * 1.38, ground_tint * 0.96, 1.0))
            elif key == "relay-valley":
                ground_tint = 0.80 - outward * 0.12
                colors.append((ground_tint * 0.64, ground_tint * 0.60, ground_tint * 0.48, 1.0))
            elif key == "mare-claim":
                ground_tint = 0.86 - outward * 0.14
                colors.append((ground_tint * 0.69, ground_tint * 0.70, ground_tint * 0.67, 1.0))
            elif key == "ember-shore":
                ground_tint = 0.78 - outward * 0.15
                colors.append((ground_tint * 0.26, ground_tint * 0.16, ground_tint * 0.11, 1.0))
            else:
                ground_tint = 0.88 + outward * 0.08
                colors.append((ground_tint * 0.82, ground_tint * 0.88, ground_tint, 1.0))
    skirt_width = skirt_segments + 1
    for row in range(len(skirt_rows) - 1):
        for index in range(skirt_segments):
            a = skirt_start + row * skirt_width + index
            b = a + 1
            d = skirt_start + (row + 1) * skirt_width + index
            c = d + 1
            faces.extend([(a, c, b), (a, d, c)])

    if key in OPEN_SEA_PANORAMAS:
        # Mystery-scale wreck masts are the open sea's only hard distance cues.
        # They live in the panorama mesh/material and never enter the playfield.
        for mast_index, (mast_u, mast_height, mast_width, yard_length) in enumerate(
            ((0.11, 8.5, 0.24, 2.8), (0.37, 5.8, 0.20, 1.9), (0.68, 10.2, 0.27, 3.4), (0.86, 6.7, 0.21, 2.2))
        ):
            angle = mast_u * math.tau
            radius = 178.0 + mast_index * 1.4
            center_x, center_y = math.cos(angle) * radius, math.sin(angle) * radius
            tangent_x, tangent_y = -math.sin(angle), math.cos(angle)
            dark_tint = (0.15, 0.23, 0.22, 1.0)

            start = len(vertices)
            half = mast_width * 0.5
            vertices.extend(
                (
                    (center_x - tangent_x * half, center_y - tangent_y * half, -1.2),
                    (center_x + tangent_x * half, center_y + tangent_y * half, -1.2),
                    (center_x + tangent_x * half, center_y + tangent_y * half, mast_height),
                    (center_x - tangent_x * half, center_y - tangent_y * half, mast_height),
                )
            )
            uvs.extend(((mast_u, 0.93), (mast_u + 0.002, 0.93), (mast_u + 0.002, 0.84), (mast_u, 0.84)))
            colors.extend((dark_tint,) * 4)
            faces.extend(((start, start + 2, start + 1), (start, start + 3, start + 2)))

            yard_z = mast_height * (0.66 + mast_index * 0.035)
            start = len(vertices)
            half_yard = yard_length * 0.5
            thickness = mast_width * 0.42
            vertices.extend(
                (
                    (center_x - tangent_x * half_yard, center_y - tangent_y * half_yard, yard_z - thickness),
                    (center_x + tangent_x * half_yard, center_y + tangent_y * half_yard, yard_z - thickness),
                    (center_x + tangent_x * half_yard, center_y + tangent_y * half_yard, yard_z + thickness),
                    (center_x - tangent_x * half_yard, center_y - tangent_y * half_yard, yard_z + thickness),
                )
            )
            uvs.extend(((mast_u, 0.93), (mast_u + 0.006, 0.93), (mast_u + 0.006, 0.91), (mast_u, 0.91)))
            colors.extend((dark_tint,) * 4)
            faces.extend(((start, start + 2, start + 1), (start, start + 3, start + 2)))

    if key in {"relay-valley", "echo-canyon"}:
        # Three mystery-scale, outward-facing relay marks give the horizon a
        # signal-era identity without implying build sites outside the map.
        mast_specs = (
            ((0.08, 8.4, 0.28, 3.0), (0.54, 11.2, 0.30, 3.8), (0.82, 7.0, 0.24, 2.6))
            if key == "relay-valley"
            else ((0.16, 9.6, 0.26, 3.4), (0.48, 7.2, 0.24, 2.8), (0.89, 10.8, 0.30, 3.9))
        )
        for mast_index, (mast_u, mast_height, mast_width, arm_length) in enumerate(mast_specs):
            angle = mast_u * math.tau
            radius = 179.0 + mast_index * 1.3
            center_x, center_y = math.cos(angle) * radius, math.sin(angle) * radius
            tangent_x, tangent_y = -math.sin(angle), math.cos(angle)
            dark_tint = (0.13, 0.19, 0.17, 1.0)
            start = len(vertices)
            half = mast_width * 0.5
            vertices.extend((
                (center_x - tangent_x * half, center_y - tangent_y * half, 1.0),
                (center_x + tangent_x * half, center_y + tangent_y * half, 1.0),
                (center_x + tangent_x * half, center_y + tangent_y * half, mast_height),
                (center_x - tangent_x * half, center_y - tangent_y * half, mast_height),
            ))
            uvs.extend(((mast_u, 0.93), (mast_u + 0.002, 0.93), (mast_u + 0.002, 0.84), (mast_u, 0.84)))
            colors.extend((dark_tint,) * 4)
            faces.extend(((start, start + 2, start + 1), (start, start + 3, start + 2)))
            arm_z = mast_height * 0.72
            start = len(vertices)
            half_arm = arm_length * 0.5
            thickness = mast_width * 0.52
            vertices.extend((
                (center_x - tangent_x * half_arm, center_y - tangent_y * half_arm, arm_z - thickness),
                (center_x + tangent_x * half_arm, center_y + tangent_y * half_arm, arm_z - thickness),
                (center_x + tangent_x * half_arm, center_y + tangent_y * half_arm, arm_z + thickness),
                (center_x - tangent_x * half_arm, center_y - tangent_y * half_arm, arm_z + thickness),
            ))
            uvs.extend(((mast_u, 0.93), (mast_u + 0.006, 0.93), (mast_u + 0.006, 0.91), (mast_u, 0.91)))
            colors.extend((dark_tint,) * 4)
            faces.extend(((start, start + 2, start + 1), (start, start + 3, start + 2)))

    mesh = bpy.data.meshes.new(f"{key.title().replace('-', '')}PanoramaMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    uv_layer = mesh.uv_layers.new(name="PanoramaUV")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            uv_layer.data[loop_index].uv = uvs[mesh.loops[loop_index].vertex_index]
    color_layer = mesh.color_attributes.new(name="PanoramaTint", type="FLOAT_COLOR", domain="POINT")
    for index, color in enumerate(colors):
        color_layer.data[index].color = color
    obj = bpy.data.objects.new(f"{key.title().replace('-', '')}Panorama", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(material)
    obj["render_only"] = True
    obj["panorama"] = True
    obj["affects_playfield"] = False
    obj["affects_masks"] = False
    obj["affects_spawn_edges"] = False
    obj["affects_fog_gating"] = False
    obj["mount_space"] = "game X/Y/Z at county origin"
    obj["panorama_law"] = "v2"
    obj.visible_shadow = False
    return obj


def contract_for(key, profile, obj, blend, glb, atlas_path):
    triangles = sum(len(poly.vertices) - 2 for poly in obj.data.polygons)
    return {
        "asset": glb.name,
        "map": key,
        "renderOnly": True,
        "style": f"engraved {profile.get('epoch', 'Epoch 1 frontier river county')} kit-plate horizon; " + ("open working sea against a tea-coloured weather rim" if key in OPEN_SEA_PANORAMAS else ("high convalescent mesa between inland-water gleam and dust-dark plains" if key == "glow-mesa" else ("walnut signal county beneath a teal-gray dusk and darker broadcast rim" if key in {"relay-valley", "echo-canyon"} else ("warm-grey stippled vacuum with one soft blue-green Earth cameo on the near side" if key == "mare-claim" else ("deep-ink star stipple over low cooled shelves and unequal parchment-gold nebula veils" if key == "ember-shore" else "warm valley against a darker fevered rim"))))),
        "signature": profile["signature"],
        "exposure": {
            "mode": "bakedIntoAtlas",
            "linearMultiplier": profile["strength"],
        },
        "lawVersion": "PANORAMA LAW v2",
        "namedCorrections": {
            "paintedWall": "deep-sunk cylindrical sky ring behind the code-owned sea; continuous tea gradient, no seam band" if key in OPEN_SEA_PANORAMAS else ("sunk vacuum ring behind independent irregular lunar ridges; terrain-matched ground skirt replaces atmospheric haze" if key == "mare-claim" else ("sunk star-stipple ring behind low independent cooled shelves; terrain-matched basalt skirt and restrained ember haze carry the join" if key == "ember-shore" else "sunk sky ring behind an irregular closer ridge belt with a dusty haze transition")),
            "ceiling": "engraving density grades from dense horizon to near-plain parchment zenith",
            "echo": (
                "asymmetric cloud and dust edits plus one strongly broken ridge profile avoid both mirrored repetition and a doubled arena wall"
                if key == "glow-mesa"
                else ("independent near/far lunar ridge profiles and one-sided Earth placement break repetition without filling the vacuum" if key == "mare-claim" else ("four unequal gold nebula edits and independent cooled-shelf profiles break repetition while preserving drawn emptiness" if key == "ember-shore" else "asymmetric cloud and dust edits plus independent near/far ridge profiles break mirrored repetition"))
            ),
        },
        "projection": {
            "skyRingRadiusMeters": RADIUS,
            "ridgeFootRadiusMeters": RIDGE_FOOT_RADIUS,
            "ridgeOccluderRadiusMeters": RIDGE_CREST_RADIUS,
            "farRidgeRadiusMeters": [FAR_RIDGE_FOOT_RADIUS, FAR_RIDGE_CREST_RADIUS] if key in FAR_RIDGE_PANORAMAS else None,
            "ridgeFootRadiusRangeMeters": [RIDGE_FOOT_RADIUS - 1.7, RIDGE_FOOT_RADIUS + 1.7],
            "ridgeOccluderRadiusRangeMeters": [RIDGE_CREST_RADIUS - 1.7, RIDGE_CREST_RADIUS + 1.7],
            "skyBottomMeters": -160.0 if key in OPEN_SEA_PANORAMAS else SKY_BOTTOM,
            "skyTopMeters": SKY_TOP,
            "ridgeTopFormulaMeters": (
                "-80.0; dormant belt far below code-owned sea"
                if key in OPEN_SEA_PANORAMAS
                else (
                    "2.8 + silhouetteFraction * 38.0"
                    if key == "fairground"
                    else ("2.6 + silhouetteFraction * 43.0" if key == "glow-mesa" else ("3.4 + silhouetteFraction * 48.0" if key in {"relay-valley", "echo-canyon"} else ("3.0 + silhouetteFraction * 44.0" if key == "mare-claim" else ("2.8 + silhouetteFraction * 46.0" if key == "ember-shore" else f"{RIDGE_TOP_BASE} + silhouetteFraction * {RIDGE_TOP_SCALE}"))))
                )
            ),
            "farRidgeTopFormulaMeters": ("6.0 + silhouetteFraction * 52.0" if key == "fairground" else ("4.0 + silhouetteFraction * 38.0" if key == "mare-claim" else ("3.4 + silhouetteFraction * 42.0" if key == "ember-shore" else "8.0 + silhouetteFraction * 55.0"))) if key in FAR_RIDGE_PANORAMAS else None,
            "groundSkirtInnerBoundaryMeters": {
                "shape": "expanded-playfield-rectangle",
                "halfExtents": [playfield_half_extents(key)[0], playfield_half_extents(key)[1]],
                "margin": 0.01,
            },
            "groundSkirtOuterRadiusMeters": RADIUS if key in OPEN_SEA_PANORAMAS else RIDGE_FOOT_RADIUS,
            "groundSkirtRole": "submerged scenery apron under the code-owned sea; no water or gameplay authority" if key in OPEN_SEA_PANORAMAS else "county ground scenery",
        },
        "mount": claim.panorama_mount(key),
        "earthSide": {
            "nearSideQuadrantU": 0.75,
            "farSideQuadrantU": 0.25,
            "nearSide": "one soft blue-green Earth cameo",
            "farSide": "no Earth",
            "rule": "Earth is the Mare comfort image; THE FAR SIDE alone removes it",
        } if key == "mare-claim" else None,
        "nonInterference": {
            "playfieldBounds": "unchanged",
            "spawnEdges": "unchanged",
            "fogGating": "unchanged",
            "waterBuildSpawnMasks": "unchanged",
        },
        "meshCount": 1,
        "primitiveCount": 1,
        "materialCount": 1,
        "vertices": len(obj.data.vertices),
        "triangles": triangles,
        "triangleBudget": 4000,
        "texture": {"count": 1, "width": ATLAS_SIZE, "height": ATLAS_SIZE, "embedded": True},
        "sourceArt": list(dict.fromkeys([
            str(profile.get("kit", KIT).relative_to(ROOT)),
            str(profile.get("sourcePlate", claim.CONTRACT_PLATES.get(profile["contract"], profile.get("kit", KIT))).relative_to(ROOT)),
        ])),
        "files": {
            "blend": {"bytes": blend.stat().st_size, "sha256": sha256(blend)},
            "glb": {"bytes": glb.stat().st_size, "sha256": sha256(glb)},
            "atlas": {"bytes": atlas_path.stat().st_size, "sha256": sha256(atlas_path)},
        },
    }


def build(key):
    profile = PROFILES[key]
    claim.reset_scene()
    atlas, atlas_path = make_atlas(key, profile)
    material = make_material(key, atlas, profile)
    ring = make_ring(key, material)
    blend = OUT / f"{key}-panorama.blend"
    glb = OUT / f"{key}-panorama.glb"
    contract_path = OUT / f"{key}-panorama-contract.json"
    bpy.ops.object.select_all(action="DESELECT")
    ring.select_set(True)
    bpy.context.view_layer.objects.active = ring
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
    contract = contract_for(key, profile, ring, blend, glb, atlas_path)
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(contract, indent=2))


def main():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    keys = args or [key for key in PROFILES if key not in E1_PANORAMAS]
    refused = [key for key in keys if key in E1_PANORAMAS]
    if refused:
        raise ValueError(
            f"{', '.join(refused)}: Epoch 1 panoramas are built by build_e1_contract_panoramas.py, "
            "not by this script. This script is the generalised descendant of the E1 builder and its "
            "shared paint and ring code has been retuned for E2..E10 since the E1 art shipped, so "
            "building an E1 key here silently replaces approved art with a newer generation. The E1 "
            "profiles stay here only because map_index = list(PROFILES).index(key) places every later "
            "map's cloud edits off this ordering. See verify_e1_panoramas.py."
        )
    for key in keys:
        if key not in PROFILES:
            raise ValueError(f"unsupported panorama profile: {key}")
        build(key)


if __name__ == "__main__":
    main()
