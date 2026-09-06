"""Build the authored E2 terrain/panorama verdicts.

The factory contract JSON is the only coordinate source. Terrain is a mounted
render asset; gameplay masks, collision, spawns, placement, and rail authority
remain code-owned. Preview landmarks are removed before export.
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
FACTORY_CONTRACTS = ROOT / "assets/contracts/epoch-2-steamworks/contracts.json"
MASK_TABLES = ROOT / "assets/contracts/epoch-2-steamworks/mask-tables"
KIT = ROOT / "assets/processed/kit-era-2.png"
HILL_PLATE = ROOT / "assets/raw/plate-contract-hill-mine.png"
RAIL_PLATE = ROOT / "assets/processed/ter-rail-elements-r0c2.png"
HALF = 48.0
SEGMENTS = 128
ATLAS_SIZE = 2048
SIM_RIVER_HALF_WIDTH = 5.0
SIM_SHALLOWS_HALF_WIDTH = 6.25

claim_spec = importlib.util.spec_from_file_location("e2_claim_helpers", OUT / "build_the_claim_terrain.py")
claim = importlib.util.module_from_spec(claim_spec)
claim_spec.loader.exec_module(claim)
claim.mathutils = mathutils

# The E2 grading still goes through the accepted grit implementation, but its
# palette target and ink source are the shipped E2 plate/kit rather than E1.
claim.CONTRACT_PLATES.update({
    "hill-mine": HILL_PLATE,
    "trestle": KIT,
    "pressure-garden": KIT,
    "incline": KIT,
})
claim.GRIT_PROFILES.update({
    "hill-mine": {"black": 0.022, "white": 0.48, "gamma": 1.24, "ink": 0.43, "palette": 0.15, "saturation": 0.61},
    "trestle": {"black": 0.026, "white": 0.52, "gamma": 1.20, "ink": 0.40, "palette": 0.13, "saturation": 0.58},
    "pressure-garden": {"black": 0.020, "white": 0.49, "gamma": 1.22, "ink": 0.44, "palette": 0.16, "saturation": 0.56},
    "incline": {"black": 0.018, "white": 0.47, "gamma": 1.25, "ink": 0.46, "palette": 0.14, "saturation": 0.57},
})

PROFILES = {
    "hill-mine": {
        "contractId": "e2-hill-mine",
        "stem": "hill-mine-terrain",
        "object": "HillMineTerrain",
        "mesh": "HillMineTerrainMesh",
        "material": "HillMinePaintedTerrainMaterial",
        "atlas": "HillMinePaintedTerrainAtlas",
        "theme": "scarred terraced hillside above a flooded rail cut",
        "sourcePlate": HILL_PLATE,
        "mounts": [
            claim.landmark_mount("mine-mouth-and-ruined-headframe", -6, 41, -0.08, 1.35),
            claim.landmark_mount("boiler-house-site", 0, 12, 0, 1.25),
            claim.landmark_mount("flooded-gallery", 0, 0, 0, 1.15),
            claim.landmark_mount("switchback-rail-kit", 0, 25, 0, 1.25),
            claim.landmark_mount("tailings-and-scree-pack", 35, 34, 0.15, 1.25),
        ],
    },
    "trestle": {
        "contractId": "e2-trestle",
        "stem": "trestle-terrain",
        "object": "TrestleTerrain",
        "mesh": "TrestleTerrainMesh",
        "material": "TrestlePaintedTerrainMaterial",
        "atlas": "TrestlePaintedTerrainAtlas",
        "theme": "long rail crossing pinched between defended gorge approaches",
        "sourcePlate": KIT,
        "mounts": [
            claim.landmark_mount("trestle-crossing", 0, 0),
            claim.landmark_mount("south-boiler-site", 12, -12, 0.08),
            claim.landmark_mount("north-boiler-site", -12, 12, -0.06),
            claim.landmark_mount("south-approach-kit", 0, -22),
            claim.landmark_mount("north-approach-kit", 0, 22),
            claim.landmark_mount("mine-spur-kit", -14, -18, -0.10),
        ],
    },
    "pressure-garden": {
        "contractId": "e2-pressure-garden",
        "stem": "pressure-garden-terrain",
        "object": "PressureGardenTerrain",
        "mesh": "PressureGardenTerrainMesh",
        "material": "PressureGardenPaintedTerrainMaterial",
        "atlas": "PressureGardenPaintedTerrainAtlas",
        "theme": "four hard-worked geothermal terraces rising from three boiler beds to a coal seam",
        "sourcePlate": KIT,
        "mounts": [
            claim.landmark_mount("garden-pressure-manifold", 0, 4),
            claim.landmark_mount("west-terrace-pipe-header", -50, 24, 0.18),
            claim.landmark_mount("east-terrace-pipe-header", 50, 24, -0.18),
            claim.landmark_mount("coal-seam-service-winch", -42, 40, 0.12),
            claim.landmark_mount("water-band-pump-station", 42, -6, -0.12),
        ],
    },
    "incline": {
        "contractId": "e2-incline",
        "stem": "incline-terrain",
        "object": "InclineTerrain",
        "mesh": "InclineTerrainMesh",
        "material": "InclinePaintedTerrainMaterial",
        "atlas": "InclinePaintedTerrainAtlas",
        "theme": "twin funicular cuts climbing from one wet lower yard to broken ore benches",
        "sourcePlate": KIT,
        "mounts": [
            claim.landmark_mount("lower-yard-engine-crane", 2, 21.8, 0.14, 1.05),
            claim.landmark_mount("west-line-brake-tower", -34, 36.5, 0.18, 1.0),
            claim.landmark_mount("east-line-brake-tower", 34, 35, -0.16, 1.0),
            claim.landmark_mount("upper-ore-cable-house", 22, 29, -0.1, 1.0),
            claim.landmark_mount("ford-service-pump", 25, 21.5, -0.12, 0.78),
        ],
    },
}


SUN_DIRECTION = np.array((-32.0, 18.0, -30.0), dtype=np.float32)
SUN_DIRECTION = SUN_DIRECTION / np.linalg.norm(SUN_DIRECTION)
TRESTLE_SKY_FILL = np.array((0.90, 0.98, 1.12), dtype=np.float32)
TRESTLE_WATER_DROP = 0.006


def smoothstep(edge0, edge1, value):
    value = np.asarray(value, dtype=np.float32)
    if edge0 == edge1:
        return np.where(value < edge0, 0.0, 1.0)
    t = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def gaussian(x, z, cx, cz, sx, sz):
    return np.exp(-(((x - cx) / sx) ** 2 + ((z - cz) / sz) ** 2) * 0.5)


def segment_mask(x, z, a, b, width):
    vx = b["x"] - a["x"]
    vz = b["z"] - a["z"]
    length_squared = max(vx * vx + vz * vz, 0.001)
    t = np.clip(((x - a["x"]) * vx + (z - a["z"]) * vz) / length_squared, 0.0, 1.0)
    distance = np.hypot(x - (a["x"] + t * vx), z - (a["z"] + t * vz))
    return 1.0 - smoothstep(width * 0.55, width, distance)


def rut_track(x, z, z0, z1, x0, x1, half_gauge, width=0.46):
    """A cart's two wheel ruts running from (x0, z0) to (x1, z1), faded in at both ends.

    Ruts are the cheapest way to say a slope is USED, and the craftbook's rule is ruts where
    traffic runs — so every call site here is keyed to a route the sim actually forces.
    """
    span = z1 - z0
    t = np.clip((z - z0) / span, 0.0, 1.0) if span else np.zeros_like(z)
    centre = x0 + (x1 - x0) * t
    low, high = (z0, z1) if span > 0 else (z1, z0)
    window = smoothstep(low - 1.4, low + 1.1, z) * (1.0 - smoothstep(high - 1.1, high + 1.4, z))
    left = np.exp(-((x - (centre - half_gauge)) / width) ** 2)
    right = np.exp(-((x - (centre + half_gauge)) / width) ** 2)
    return np.maximum(left, right) * window


def ring_mask(x, z, cx, cz, radius, width):
    """A worked-stone ring: a hard-standing that has been swept round by years of use."""
    return np.exp(-((np.hypot(x - cx, z - cz) - radius) / width) ** 2)


def rectangle_mask(x, z, zone, feather=0.7):
    return (
        smoothstep(zone["minX"] - feather, zone["minX"] + feather, x)
        * (1.0 - smoothstep(zone["maxX"] - feather, zone["maxX"] + feather, x))
        * smoothstep(zone["minZ"] - feather, zone["minZ"] + feather, z)
        * (1.0 - smoothstep(zone["maxZ"] - feather, zone["maxZ"] + feather, z))
    )


def authored_contract(contract_id):
    document = json.loads(FACTORY_CONTRACTS.read_text(encoding="utf-8"))
    matches = [entry for entry in document["contracts"] if entry["id"] == contract_id]
    if len(matches) != 1:
        raise ValueError(f"expected one authored factory contract for {contract_id}; found {len(matches)}")
    return matches[0]


def authored_mask(key, factory):
    path = MASK_TABLES / f"e2-{key}.json"
    if path.is_file():
        document = json.loads(path.read_text(encoding="utf-8"))
        if document["maskTruth"]["tileId"] != factory["id"]:
            raise ValueError(f"{path.name} does not describe {factory['id']}")
        return document
    return {
        "maskTruth": derived_mask_truth(factory),
        "waterAgreement": {
            "deepBand": {"minZ": -SIM_RIVER_HALF_WIDTH, "maxZ": SIM_RIVER_HALF_WIDTH},
            "shallowsEnd": {"minZ": -SIM_SHALLOWS_HALF_WIDTH, "maxZ": SIM_SHALLOWS_HALF_WIDTH},
            "placeableBankStartsBeyondAbsZ": SIM_SHALLOWS_HALF_WIDTH,
            "factoryVisualHalfWidth": factory["tileParams"]["water"]["visualHalfWidth"],
        },
    }


def hill_sim_height(x, z, analytic):
    creek = analytic.get("creekHeight", -0.5)
    rail = analytic.get("railHeight", 0.0)
    t1 = analytic.get("t1Height", 1.5)
    t2 = analytic.get("t2Height", 3.0)
    t3 = analytic.get("t3Height", 4.5)
    height = np.zeros_like(np.asarray(x, dtype=np.float32)) + rail
    height += (creek - rail) * (1.0 - smoothstep(analytic.get("creekBlendStart", -12), analytic.get("creekBlendEnd", -5), z))
    height += (t1 - rail) * smoothstep(analytic.get("t1RampStart", 5), analytic.get("t1RampEnd", 14), z)
    height += (t2 - t1) * smoothstep(analytic.get("t2RampStart", 18), analytic.get("t2RampEnd", 26), z)
    height += (t3 - t2) * smoothstep(analytic.get("t3RampStart", 32), analytic.get("t3RampEnd", 40), z)
    feather = max(0.001, analytic.get("cliffFeather", 1.0))
    cliff = (
        smoothstep(analytic.get("cliffMinX", -16) - feather, analytic.get("cliffMinX", -16), x)
        * (1.0 - smoothstep(analytic.get("cliffMaxX", 16), analytic.get("cliffMaxX", 16) + feather, x))
        * smoothstep(analytic.get("cliffMinZ", 18) - feather, analytic.get("cliffMinZ", 18), z)
        * (1.0 - smoothstep(analytic.get("cliffMaxZ", 23), analytic.get("cliffMaxZ", 23) + feather, z))
    )
    height += analytic.get("cliffAmp", 0.0) * cliff
    radius = max(0.001, analytic.get("mineMouthRadius", 1.0))
    mouth = gaussian(x, z, analytic.get("mineMouthX", 0), analytic.get("mineMouthZ", 40), radius, radius)
    return height + analytic.get("mineMouthCrown", 0.0) * mouth


def trestle_sim_height(x, z, analytic):
    radius = max(0.001, analytic.get("bowlRadius", 12.0))
    bowl = -analytic.get("bowlDepth", 0.0) * gaussian(
        x, z, analytic.get("bowlCenterX", 0.0), analytic.get("bowlCenterZ", 0.0), radius, radius
    )
    ridge = analytic.get("ridgeAmp", 0.0) * gaussian(
        x,
        z,
        analytic.get("ridgeX", 0.0),
        analytic.get("ridgeZ", 0.0),
        max(0.001, analytic.get("ridgeWidth", 1.0)),
        max(0.001, analytic.get("ridgeLength", 1.0)),
    )
    return bowl + ridge


def height_function(key, factory):
    analytic = factory["tileParams"]["elevation"]["analytic"]

    def height(x, z):
        x_array = np.asarray(x, dtype=np.float32)
        z_array = np.asarray(z, dtype=np.float32)
        if key == "hill-mine":
            base = hill_sim_height(x_array, z_array, analytic)
            grain = np.sin(x_array * 0.37 + z_array * 0.21) * 0.035 + np.sin(x_array * 0.13 - z_array * 0.43) * 0.022
            calm = np.zeros_like(base)
            for zone in factory["tileParams"]["buildZones"]:
                zone_mask = (
                    smoothstep(zone["minX"] - 1.0, zone["minX"] + 0.8, x_array)
                    * (1.0 - smoothstep(zone["maxX"] - 0.8, zone["maxX"] + 1.0, x_array))
                    * smoothstep(zone["minZ"] - 1.0, zone["minZ"] + 0.8, z_array)
                    * (1.0 - smoothstep(zone["maxZ"] - 0.8, zone["maxZ"] + 1.0, z_array))
                )
                calm = np.maximum(calm, zone_mask)
            water = 1.0 - smoothstep(4.8, SIM_SHALLOWS_HALF_WIDTH, np.abs(z_array))
            return base - water * 0.18 + grain * (1.0 - calm * 0.82) * (1.0 - water)

        if key in {"pressure-garden", "incline"}:
            base = hill_sim_height(x_array, z_array, analytic)
            # Only sub-decimetre erosion is added to the exact authored steps;
            # the impassable cliff and every build terrace remain sim-shaped.
            grain_scale = {"pressure-garden": 0.72, "incline": 0.88}[key]
            grain = (np.sin(x_array * 0.37 + z_array * 0.21) * 0.035 + np.sin(x_array * 0.13 - z_array * 0.43) * 0.022) * grain_scale
            calm = np.zeros_like(base)
            for zone in factory["tileParams"]["buildZones"]:
                zone_mask = rectangle_mask(x_array, z_array, zone, 1.0)
                calm = np.maximum(calm, zone_mask)
            water = 1.0 - smoothstep(4.8, SIM_SHALLOWS_HALF_WIDTH, np.abs(z_array))
            relief = np.zeros_like(base)
            if key == "pressure-garden":
                relief = (
                    gaussian(x_array, z_array, -42, 28, 7, 20)
                    + gaussian(x_array, z_array, 42, 31, 8, 18)
                ) * 0.10
            elif key == "incline":
                rail_calm = np.maximum(
                    1.0 - smoothstep(1.1, 3.2, np.abs(x_array + 12.0)),
                    1.0 - smoothstep(1.1, 3.2, np.abs(x_array - 12.0)),
                )
                calm = np.maximum(calm, rail_calm)
                relief = (
                    gaussian(x_array, z_array, -43, 30, 6, 18)
                    + gaussian(x_array, z_array, 40, 35, 7, 15)
                ) * 0.14
            return base - water * 0.18 + (grain + relief) * (1.0 - calm * 0.88) * (1.0 - water)

        base = trestle_sim_height(x_array, z_array, analytic)
        az = np.abs(z_array)
        gorge = (1.0 - smoothstep(4.6, SIM_RIVER_HALF_WIDTH, az)) * -0.34
        bank_relief = factory["tileParams"]["heightfield"]["bankRelief"]
        shoulders = smoothstep(SIM_RIVER_HALF_WIDTH, bank_relief["width"] + SIM_RIVER_HALF_WIDTH, az)
        shoulders *= 1.0 - smoothstep(21.0, 31.0, az)
        asymmetric = 0.72 + 0.28 * smoothstep(-18.0, 32.0, x_array)
        grain = (np.sin(x_array * 0.31 + z_array * 0.19) * 0.030 + np.sin(x_array * 0.12 - z_array * 0.41) * 0.018)
        sculpted = base + gorge + shoulders * bank_relief["amount"] * asymmetric + grain
        water = 1.0 - smoothstep(4.8, SIM_SHALLOWS_HALF_WIDTH, az)
        river_bed = np.minimum(sculpted, -0.20 - (1.0 - smoothstep(0.0, 4.8, az)) * 0.12)
        return sculpted * (1.0 - water) + river_bed * water

    return height


def paint_trestle_gorge(atlas, factory, x, z, az, wash, dirt, rock):
    """Paint the Trestle gorge and prepared approaches from the recipe's own height."""
    height = height_function("trestle", factory)(x, z)
    cell = HALF * 2.0 / (ATLAS_SIZE - 1)
    d_dz, d_dx = np.gradient(height, cell)
    slope = np.hypot(d_dx, d_dz)
    normal_scale = 1.0 / np.sqrt(d_dx * d_dx + d_dz * d_dz + 1.0)
    lambert = (-d_dx * SUN_DIRECTION[0] + SUN_DIRECTION[1] - d_dz * SUN_DIRECTION[2]) * normal_scale

    centreline = height_function("trestle", factory)(
        np.arange(-HALF + 1.0, HALF - 0.5, 0.5, dtype=np.float32),
        np.zeros(int((HALF * 2.0 - 2.0) / 0.5) + 1, dtype=np.float32),
    )
    waterline = float(np.quantile(centreline, 0.8)) - TRESTLE_WATER_DROP

    wall = smoothstep(0.10, 0.30, slope) * (1.0 - smoothstep(12.0, 20.0, az))
    strata = (np.sin(height * 118.0 + np.sin(x * 0.09) * 1.1) * 0.5 + 0.5) * 0.62
    strata += (np.sin(height * 263.0 + np.sin(z * 0.21) * 0.7) * 0.5 + 0.5) * 0.38
    stone = rock * np.array((0.55, 0.44, 0.34), dtype=np.float32)
    atlas = atlas * (1.0 - wall[..., None] * 0.26) + stone * wall[..., None] * 0.26
    atlas *= 1.0 - (wall * (1.0 - strata))[..., None] * 0.16

    stain = np.exp(-((height - waterline) / 0.075) ** 2) * (1.0 - smoothstep(11.0, 17.0, az))
    stain_tone = dirt * np.array((0.30, 0.31, 0.26), dtype=np.float32)
    atlas = atlas * (1.0 - stain[..., None] * 0.42) + stain_tone * stain[..., None] * 0.42

    silt = (
        smoothstep(waterline - 0.01, waterline + 0.03, height)
        * (1.0 - smoothstep(waterline + 0.11, waterline + 0.36, height))
        * (1.0 - smoothstep(10.0, 15.0, az))
    )
    silt_tone = wash * np.array((0.44, 0.46, 0.40), dtype=np.float32)
    atlas = atlas * (1.0 - silt[..., None] * 0.32) + silt_tone * silt[..., None] * 0.32

    ruts = np.zeros_like(height)
    for a, b in (
        ({"x": -26.0, "z": -24.0}, {"x": -6.0, "z": -12.0}),
        ({"x": -6.0, "z": -12.0}, {"x": -1.5, "z": -7.4}),
        ({"x": 23.0, "z": -23.0}, {"x": 5.0, "z": -11.0}),
        ({"x": 5.0, "z": -11.0}, {"x": 1.5, "z": -7.4}),
        ({"x": -22.0, "z": 25.0}, {"x": -5.0, "z": 12.0}),
        ({"x": -5.0, "z": 12.0}, {"x": -1.4, "z": 7.4}),
        ({"x": 24.0, "z": 22.0}, {"x": 6.0, "z": 11.0}),
        ({"x": 6.0, "z": 11.0}, {"x": 1.4, "z": 7.4}),
    ):
        run_x, run_z = b["x"] - a["x"], b["z"] - a["z"]
        length = max(math.hypot(run_x, run_z), 0.001)
        off_x, off_z = -run_z / length * 0.78, run_x / length * 0.78
        for sign in (-1.0, 1.0):
            track_a = {"x": a["x"] + off_x * sign, "z": a["z"] + off_z * sign}
            track_b = {"x": b["x"] + off_x * sign, "z": b["z"] + off_z * sign}
            ruts = np.maximum(ruts, segment_mask(x, z, track_a, track_b, 0.62))
    ruts *= smoothstep(5.8, 7.6, az)
    atlas *= 1.0 - ruts[..., None] * 0.13

    pads = np.zeros_like(height)
    rubble = np.zeros_like(height)
    for mount_x, mount_z, sx, sz in (
        (-14.0, -18.0, 7.6, 5.6),
        (0.0, -22.0, 5.4, 3.8),
        (0.0, 22.0, 5.4, 3.8),
        (12.0, -12.0, 4.8, 3.8),
        (-12.0, 12.0, 4.8, 3.8),
    ):
        radial = np.hypot((x - mount_x) / sx, (z - mount_z) / sz)
        pads = np.maximum(pads, 1.0 - smoothstep(0.70, 1.0, radial))
        rubble = np.maximum(rubble, (1.0 - smoothstep(0.98, 1.55, radial)) * smoothstep(0.66, 1.0, radial))
    pad_tone = dirt * np.array((0.46, 0.42, 0.36), dtype=np.float32)
    atlas = atlas * (1.0 - pads[..., None] * 0.55) + pad_tone * pads[..., None] * 0.55
    atlas *= 1.0 - pads[..., None] * 0.07
    rubble_tone = rock * np.array((0.74, 0.63, 0.49), dtype=np.float32)
    atlas = atlas * (1.0 - rubble[..., None] * 0.46) + rubble_tone * rubble[..., None] * 0.46

    service = np.zeros_like(height)
    for a, b in (
        ({"x": -14.0, "z": -18.0}, {"x": -4.5, "z": -21.0}),
        ({"x": -4.5, "z": -21.0}, {"x": 0.0, "z": -22.0}),
    ):
        run_x, run_z = b["x"] - a["x"], b["z"] - a["z"]
        length = max(math.hypot(run_x, run_z), 0.001)
        off_x, off_z = -run_z / length * 0.78, run_x / length * 0.78
        for sign in (-1.0, 1.0):
            service = np.maximum(service, segment_mask(
                x, z,
                {"x": a["x"] + off_x * sign, "z": a["z"] + off_z * sign},
                {"x": b["x"] + off_x * sign, "z": b["z"] + off_z * sign},
                0.62,
            ))
    atlas *= 1.0 - service[..., None] * 0.11

    shade = smoothstep(0.34, 0.02, lambert) * (1.0 - smoothstep(13.0, 25.0, az))
    return atlas, shade


def make_atlas(key, profile, factory, mask_document):
    bank_a = claim.image_pixels(claim.BANK_A)
    bank_b = claim.image_pixels(claim.BANK_B)
    bank_c = claim.image_pixels(claim.BANK_C)
    river = claim.image_pixels(claim.RIVER)
    rail_plate = claim.image_pixels(RAIL_PLATE)
    axis = np.linspace(0.0, 1.0, ATLAS_SIZE, dtype=np.float32)
    u, v = np.meshgrid(axis, axis)
    x = (u - 0.5) * HALF * 2.0
    z = (v - 0.5) * HALF * 2.0
    ax = np.abs(x)
    az = np.abs(z)

    wash = claim.tiled_sample(bank_a, u, v, 7.1, 0.17, 0.39)
    dirt = claim.tiled_sample(bank_b, u, v, 8.6, 0.53, 0.11)
    rock = claim.tiled_sample(bank_c, u, v, 9.7, 0.08, 0.67)
    macro = (np.sin(x * 0.095 + z * 0.071) * 0.5 + 0.5)[..., None]
    land = wash * (0.34 + macro * 0.08) + dirt * 0.31 + rock * (0.35 - macro * 0.08)
    land *= np.array((0.88, 0.66, 0.42), dtype=np.float32)

    water = claim.tiled_sample(river, u, v, 3.4, 0.43, 0.19) * np.array((0.33, 0.37, 0.28), dtype=np.float32)
    water *= 1.0 - claim.engraved_ink(river, u, v, 3.4, 0.43, 0.19)[..., None] * 0.31
    water_mask = 1.0 - smoothstep(SIM_RIVER_HALF_WIDTH, SIM_SHALLOWS_HALF_WIDTH, az)
    atlas = land * (1.0 - water_mask[..., None]) + water * water_mask[..., None]
    atlas *= 1.0 - np.exp(-((az - SIM_RIVER_HALF_WIDTH) / 0.48) ** 2)[..., None] * 0.22

    rail_mask = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
    for rail in factory["tileParams"]["rails"]:
        for a, b in zip(rail["points"], rail["points"][1:]):
            rail_mask = np.maximum(rail_mask, segment_mask(x, z, a, b, 0.95))
    rail_ink = claim.tiled_sample(rail_plate, u, v, 7.0, 0.24, 0.63) * np.array((0.36, 0.25, 0.16), dtype=np.float32)
    atlas = atlas * (1.0 - rail_mask[..., None] * 0.28) + rail_ink * rail_mask[..., None] * 0.28

    post_grade_shade = None
    if key == "hill-mine":
        analytic = factory["tileParams"]["elevation"]["analytic"]
        upper = smoothstep(17.0, 42.0, z)
        scree = rock * np.array((0.52, 0.43, 0.33), dtype=np.float32)
        atlas = atlas * (1.0 - upper[..., None] * 0.36) + scree * upper[..., None] * 0.36

        # ------------------------------------------------------------------------------------
        # U2 — THE TERRACES READ AS CUT GROUND (docs/beauty/e2-hill-mine-brief.md).
        #
        # What was here: one 0.28 darkening at z 14 / 23 / 39.5. Those are the ramp TOPS, so the
        # paint put a soft black smear across the very faces the sim uses to block bolts, and it
        # missed the t2 lip (26) entirely. A face that stops a bolt should look like cut rock.
        #
        # Every number below is READ from the tile's own analytic elevation table rather than
        # typed, so a rules change to a ramp moves its paint with it. Rendering only: this is the
        # colour map, not the mesh, and `hill_sim_height` is untouched.
        # ------------------------------------------------------------------------------------
        ramps = (
            (analytic["t1RampStart"], analytic["t1RampEnd"]),
            (analytic["t2RampStart"], analytic["t2RampEnd"]),
            (analytic["t3RampStart"], analytic["t3RampEnd"]),
        )
        face = np.zeros_like(z)
        lip = np.zeros_like(z)
        under_lip = np.zeros_like(z)
        toe = np.zeros_like(z)
        for start, end in ramps:
            ramp_t = np.clip((z - start) / (end - start), 0.0, 1.0)
            face = np.maximum(face, np.where((z > start) & (z < end), 4.0 * ramp_t * (1.0 - ramp_t), 0.0))
            # A LIT LINE WITH A DARK ONE UNDER IT is the only cut-edge read that survives this
            # camera. The map is seen at a shallow angle, so a 9 m ramp rising 1.5 m is nearly
            # edge-on and strata alone spread too thin to say anything; a hard value STEP at the
            # top of the bench reads from any angle, which is what an edge actually is.
            lip = np.maximum(lip, np.exp(-((z - end) / 0.34) ** 2))
            under_lip = np.maximum(under_lip, np.exp(-((z - (end - 0.78)) / 0.40) ** 2))
            toe = np.maximum(toe, np.exp(-((z - start) / 0.70) ** 2))
        # The cliff is its own bench: impassable in the sim, so it gets the same grammar.
        cliff_top = analytic["cliffMaxZ"]
        cliff_face = (
            smoothstep(analytic["cliffMinX"] - 1.6, analytic["cliffMinX"] + 0.6, x)
            * (1.0 - smoothstep(analytic["cliffMaxX"] - 0.6, analytic["cliffMaxX"] + 1.6, x))
        )
        lip = np.maximum(lip, np.exp(-((z - cliff_top) / 0.34) ** 2) * cliff_face)
        under_lip = np.maximum(under_lip, np.exp(-((z - (cliff_top - 0.78)) / 0.40) ** 2) * cliff_face)
        face = np.maximum(face, np.exp(-((z - (analytic["cliffMinZ"] + cliff_top) * 0.5) / 2.2) ** 2) * cliff_face)

        # Bedding planes. The wobble comes from x so the strata are not a comb, and the square
        # keeps them as thin dark partings between thick pale beds rather than a stripe pattern.
        strata = (np.sin(z * 3.7 + np.sin(x * 0.085) * 1.9 + macro[..., 0] * 2.1) * 0.5 + 0.5) ** 2
        hatch = strata * face
        cut_rock = rock * np.array((0.58, 0.47, 0.36), dtype=np.float32)
        atlas = atlas * (1.0 - hatch[..., None] * 0.18) + cut_rock * hatch[..., None] * 0.18
        # A cut has a lit top edge and a shaded foot; without both it stays a gradient.
        lit_lip = wash * np.array((0.96, 0.80, 0.55), dtype=np.float32)
        atlas = atlas * (1.0 - lip[..., None] * 0.20) + lit_lip * lip[..., None] * 0.20
        atlas *= 1.0 - under_lip[..., None] * 0.18
        atlas *= 1.0 - toe[..., None] * 0.15

        # Timber cribbing along the lips (bundle §A5 vocabulary): short ticks, not a fence.
        crib = (np.sin(x * 2.3) * 0.5 + 0.5) ** 3 * lip * (1.0 - smoothstep(30.0, 40.0, ax))
        atlas *= 1.0 - crib[..., None] * 0.17

        # Cart ruts, only where the sim forces traffic. On t1 the whole base bench funnels down to
        # the one declared ford at x 0; on t2 the cliff (x -16..16) is impassable so the routes go
        # round its shoulders; on t3 the spur runs to the mine mouth crown.
        ruts = np.zeros_like(z)
        for top_x in (-22.0, -11.0, 0.0, 11.0, 22.0):
            ruts = np.maximum(ruts, rut_track(x, z, ramps[0][1], ramps[0][0], top_x, 0.0, 0.62))
        for shoulder, pad in ((-19.0, -29.0), (19.0, 29.0)):
            ruts = np.maximum(ruts, rut_track(x, z, ramps[1][0], ramps[1][1], shoulder * 0.74, pad, 0.62))
        for start_x, end_x in ((-22.0, -7.0), (26.0, 11.0)):
            ruts = np.maximum(ruts, rut_track(x, z, ramps[2][0], ramps[2][1], start_x, end_x, 0.62))
        atlas *= 1.0 - ruts[..., None] * 0.16

        # Scree spilling DOWN off the cliff band, and the tailings fan below the mine-mouth crown.
        # Both widen as they fall, because that is what spoil does.
        cliff_drop = np.clip((analytic["cliffMinZ"] - z) / 6.0, 0.0, 1.0)
        spill = (1.0 - smoothstep(0.55, 1.0, cliff_drop)) * np.where(z < analytic["cliffMinZ"], 1.0, 0.0)
        spill *= (1.0 - smoothstep(analytic["cliffMaxX"] * 0.55, analytic["cliffMaxX"] + 2.0, ax))
        spill *= (np.sin(x * 1.1 + z * 0.7) * 0.5 + 0.5) * 0.55 + 0.45
        spill_tone = rock * np.array((0.62, 0.53, 0.42), dtype=np.float32)
        atlas = atlas * (1.0 - spill[..., None] * 0.19) + spill_tone * spill[..., None] * 0.19

        mouth_x = analytic["mineMouthX"]
        mouth_z = analytic["mineMouthZ"]
        fan_drop = np.clip((mouth_z - z) / 7.0, 0.0, 1.0)
        fan = (1.0 - smoothstep(0.6, 1.0, fan_drop)) * np.where(z < mouth_z, 1.0, 0.0)
        fan *= 1.0 - smoothstep(0.0, 1.0, np.abs(x - mouth_x) / (2.4 + fan_drop * 7.0))
        tailings_tone = dirt * np.array((0.66, 0.55, 0.40), dtype=np.float32)
        atlas = atlas * (1.0 - fan[..., None] * 0.20) + tailings_tone * fan[..., None] * 0.20

        # Worked-stone rings on the premium pads: hard standing swept round by years of use.
        pads = np.zeros_like(z)
        for zone in factory["tileParams"]["buildZones"]:
            if not zone["id"].startswith(("t2-", "t3-")):
                continue
            cx = (zone["minX"] + zone["maxX"]) * 0.5
            cz = (zone["minZ"] + zone["maxZ"]) * 0.5
            pads = np.maximum(pads, ring_mask(x, z, cx, cz, 4.4, 0.70))
            pads = np.maximum(pads, ring_mask(x, z, cx, cz, 2.3, 0.42) * 0.62)
        atlas *= 1.0 - pads[..., None] * 0.14

        soot = np.clip(gaussian(x, z, -6, 41, 8, 5) + gaussian(x, z, 0, 12, 7, 5), 0.0, 1.0)
        atlas *= 1.0 - soot[..., None] * 0.22
        flooded_gallery = (1.0 - smoothstep(2.0, 5.0, az)) * (1.0 - smoothstep(31.0, 44.0, ax))
        atlas *= 1.0 - flooded_gallery[..., None] * 0.13
    elif key == "trestle":
        damp = 1.0 - smoothstep(5.0, 14.0, az)
        damp_land = dirt * np.array((0.42, 0.50, 0.42), dtype=np.float32)
        atlas = atlas * (1.0 - damp[..., None] * 0.37) + damp_land * damp[..., None] * 0.37
        approach_ruts = np.maximum(segment_mask(x, z, {"x": 0, "z": -46}, {"x": 0, "z": -7}, 2.1), segment_mask(x, z, {"x": 0, "z": 7}, {"x": 0, "z": 46}, 2.1))
        atlas *= 1.0 - approach_ruts[..., None] * 0.13
        west_scar = gaussian(x, z, -34, 4, 11, 25)
        atlas = atlas * (1.0 - west_scar[..., None] * 0.17) + rock * west_scar[..., None] * 0.17
        atlas, post_grade_shade = paint_trestle_gorge(atlas, factory, x, z, az, wash, dirt, rock)
    elif key == "pressure-garden":
        zones = {zone["id"]: zone for zone in factory["tileParams"]["buildZones"]}
        growing = np.maximum(
            rectangle_mask(x, z, zones["west-growing-terrace"]),
            rectangle_mask(x, z, zones["east-growing-terrace"]),
        )
        crop_tone = dirt * np.array((0.46, 0.58, 0.31), dtype=np.float32)
        furrows = (np.sin(x * 1.75 + np.sin(z * 0.18) * 0.5) * 0.5 + 0.5) * growing
        atlas = atlas * (1.0 - growing[..., None] * 0.30) + crop_tone * growing[..., None] * 0.30
        atlas *= 1.0 - furrows[..., None] * 0.12
        boiler_scars = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        for marker in factory["tileParams"]["stakeMarkers"]:
            boiler_scars = np.maximum(boiler_scars, gaussian(x, z, marker["x"], marker["z"], 4.8, 3.2))
        coal = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        for seam in mask_document["maskTruth"].get("coalSeams", []):
            coal = np.maximum(coal, gaussian(x, z, seam["x"], seam["z"], 3.8, 2.4))
        mineral = np.clip(gaussian(x, z, 0, 17, 38, 6) + gaussian(x, z, 0, 34, 31, 4), 0.0, 1.0)
        mineral_tone = wash * np.array((0.78, 0.62, 0.34), dtype=np.float32)
        atlas = atlas * (1.0 - mineral[..., None] * 0.18) + mineral_tone * mineral[..., None] * 0.18
        atlas *= 1.0 - boiler_scars[..., None] * 0.31
        coal_tone = rock * np.array((0.20, 0.19, 0.17), dtype=np.float32)
        atlas = atlas * (1.0 - coal[..., None] * 0.62) + coal_tone * coal[..., None] * 0.62

        # U2: damp sluice lip, worked boiler paths, combed terraces, and a coal-dark top band.
        damp_lip = np.exp(-((z - 7.6) / 2.1) ** 2)
        silt_tone = dirt * np.array((0.52, 0.47, 0.36), dtype=np.float32)
        atlas = atlas * (1.0 - damp_lip[..., None] * 0.26) + silt_tone * damp_lip[..., None] * 0.26
        sluice_wear = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        for sample in mask_document["waterAgreement"].get("sluiceSamples", []):
            sluice_wear = np.maximum(sluice_wear, gaussian(x, z, sample["x"], sample["z"] + 0.8, 2.6, 1.5))
        worn_tone = wash * np.array((0.86, 0.72, 0.50), dtype=np.float32)
        atlas = atlas * (1.0 - sluice_wear[..., None] * 0.24) + worn_tone * sluice_wear[..., None] * 0.24

        beds = sorted(factory["tileParams"]["stakeMarkers"], key=lambda marker: marker["x"])
        service = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        for first, second in zip(beds, beds[1:]):
            service = np.maximum(service, segment_mask(x, z, first, second, 1.7))
        service = np.maximum(service, segment_mask(x, z, {"x": beds[len(beds) // 2]["x"], "z": 12}, {"x": 0, "z": 7.6}, 1.4))
        service = np.maximum(service, segment_mask(x, z, {"x": beds[0]["x"], "z": 12}, {"x": -24, "z": 21}, 1.3))
        service = np.maximum(service, segment_mask(x, z, {"x": beds[-1]["x"], "z": 12}, {"x": 24, "z": 21}, 1.3))
        rut = (np.sin(x * 0.9 + z * 2.7) * 0.5 + 0.5) * 0.35 + 0.65
        atlas *= 1.0 - (service * rut)[..., None] * 0.17

        comb = np.abs(np.sin(x * 2.3 + np.sin(z * 0.19) * 0.75))
        rows = ((1.0 - comb) ** 2.4) * growing
        atlas *= 1.0 - rows[..., None] * 0.19
        headland = growing * np.exp(-((z - 20.6) / 1.1) ** 2) + growing * np.exp(-((z - 28.4) / 1.1) ** 2)
        atlas *= 1.0 - np.clip(headland, 0.0, 1.0)[..., None] * 0.10
        parchment = wash * np.array((0.94, 0.79, 0.55), dtype=np.float32)
        atlas = atlas * (1.0 - growing[..., None] * 0.18) + parchment * growing[..., None] * 0.18

        analytic = factory["tileParams"]["elevation"]["analytic"]
        crests = [analytic["t1RampEnd"], analytic["t2RampEnd"], analytic["t3RampEnd"]]
        step_cut = np.maximum.reduce([np.exp(-((z - (crest - 0.5)) / 0.62) ** 2) for crest in crests])
        atlas *= 1.0 - step_cut[..., None] * 0.14
        step_top = np.maximum.reduce([np.exp(-((z - (crest + 0.9)) / 0.55) ** 2) for crest in crests])
        atlas = atlas * (1.0 - step_top[..., None] * 0.12) + parchment * step_top[..., None] * 0.12

        coal_zone = rectangle_mask(x, z, zones["coal-bed-terrace"], feather=2.2)
        soot_grain = 0.55 + 0.45 * (np.sin(x * 0.23 + z * 0.31) * np.sin(x * 0.11 - z * 0.19) * 0.5 + 0.5)
        atlas *= 1.0 - (coal_zone * soot_grain)[..., None] * 0.17
        anchors = [anchor for anchor in factory["tileParams"]["harvestAnchors"] if anchor["z"] >= zones["coal-bed-terrace"]["minZ"]]
        haulage = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        for anchor in anchors:
            for seam in mask_document["maskTruth"].get("coalSeams", []):
                haulage = np.maximum(haulage, segment_mask(x, z, anchor, seam, 1.5))
        atlas *= 1.0 - haulage[..., None] * 0.20
        glitter = (np.sin(x * 37.3 + z * 11.7) * np.sin(x * 13.1 - z * 29.9) * 0.5 + 0.5)
        specks = (glitter > 0.985).astype(np.float32) * np.clip(coal_zone + coal, 0.0, 1.0)
        atlas = np.clip(atlas + specks[..., None] * np.array((0.16, 0.155, 0.15), dtype=np.float32), 0.0, None)

        clearing = gaussian(x, z, -42.0, 40.0, 5.0, 3.6)
        swept = wash * np.array((0.88, 0.74, 0.52), dtype=np.float32)
        atlas = atlas * (1.0 - clearing[..., None] * 0.22) + swept * clearing[..., None] * 0.22
    else:
        bench_cuts = np.maximum.reduce([np.exp(-((z - cut) / 0.82) ** 2) for cut in (13.0, 27.5, 41.0)])
        twin_cuts = np.maximum(
            np.exp(-((x + 12.0) / 2.4) ** 2),
            np.exp(-((x - 12.0) / 2.4) ** 2),
        )
        cut_tone = rock * np.array((0.48, 0.38, 0.29), dtype=np.float32)
        atlas = atlas * (1.0 - twin_cuts[..., None] * 0.18) + cut_tone * twin_cuts[..., None] * 0.18
        atlas *= 1.0 - bench_cuts[..., None] * 0.30
        upper_tailings = np.clip(gaussian(x, z, -29, 40, 11, 5) + gaussian(x, z, 27, 39, 9, 6), 0.0, 1.0)
        atlas = atlas * (1.0 - upper_tailings[..., None] * 0.34) + rock * upper_tailings[..., None] * 0.34
        lower_oil = gaussian(x, z, -24, -18, 8, 6)
        atlas *= 1.0 - lower_oil[..., None] * 0.25

        # U2: the yards and benches earn the haul. Coordinates come from the factory contract.
        analytic = factory["tileParams"]["elevation"]["analytic"]
        ramps = (
            (analytic["t1RampStart"], analytic["t1RampEnd"]),
            (analytic["t2RampStart"], analytic["t2RampEnd"]),
            (analytic["t3RampStart"], analytic["t3RampEnd"]),
        )
        line_xs = [rail["points"][0]["x"] for rail in factory["tileParams"]["rails"]]
        zones = {zone["id"]: zone for zone in factory["tileParams"]["buildZones"]}

        service = np.maximum.reduce([
            np.exp(-((np.abs(x - line_x) - 3.4) / 1.9) ** 2) for line_x in line_xs
        ])
        service_tone = dirt * np.array((0.44, 0.35, 0.27), dtype=np.float32)
        atlas = atlas * (1.0 - service[..., None] * 0.19) + service_tone * service[..., None] * 0.19

        spill = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        for ramp_start, ramp_end in ramps:
            for line_x in line_xs:
                spill = np.maximum(spill, gaussian(
                    x, z, line_x, ramp_start + (ramp_end - ramp_start) * 0.34,
                    4.6, (ramp_end - ramp_start) * 0.30))
        spill_tone = rock * np.array((0.40, 0.32, 0.24), dtype=np.float32)
        atlas = atlas * (1.0 - spill[..., None] * 0.24) + spill_tone * spill[..., None] * 0.24

        lips = np.maximum.reduce([np.exp(-((z - (cut + 1.15)) / 0.5) ** 2) for cut in (13.0, 27.5, 41.0)])
        lip_tone = wash * np.array((0.95, 0.78, 0.52), dtype=np.float32)
        atlas = atlas * (1.0 - lips[..., None] * 0.22) + lip_tone * lips[..., None] * 0.22
        strata = np.maximum.reduce([
            np.exp(-((z - cut) / 1.6) ** 2) * (np.sin((z - cut) * 5.4) * 0.5 + 0.5)
            for cut in (13.0, 27.5, 41.0)
        ])
        atlas *= 1.0 - strata[..., None] * 0.11

        pressure = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        for line_x in line_xs:
            for offset in (-9.0, -3.5, 3.5, 9.0):
                pressure = np.maximum(pressure, segment_mask(
                    x, z, {"x": line_x + offset, "z": -46.0}, {"x": line_x, "z": -7.5}, 2.4))
        pressure *= 1.0 - smoothstep(-9.5, -7.0, z)
        atlas *= 1.0 - pressure[..., None] * 0.17

        engine = next(m for m in factory["tileParams"]["stakeMarkers"] if m["id"] == "lower-engine-house")
        apron = gaussian(x, z, engine["x"], engine["z"], 7.5, 5.6)
        apron_tone = wash * np.array((0.86, 0.71, 0.50), dtype=np.float32)
        atlas = atlas * (1.0 - apron[..., None] * 0.22) + apron_tone * apron[..., None] * 0.22
        sleepers = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        sleeper_lips = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        for index, (jitter, length) in enumerate(((0.0, 4.2), (0.35, 3.6), (-0.25, 4.5), (0.15, 3.9), (-0.4, 4.3), (0.2, 3.4))):
            near_z = engine["z"] - 3.0 + index * 1.2
            start = {"x": engine["x"] + 6.4 + jitter, "z": near_z}
            end = {"x": engine["x"] + 6.4 + jitter + length, "z": near_z + jitter * 0.2}
            sleepers = np.maximum(sleepers, segment_mask(x, z, start, end, 0.58))
            sleeper_lips = np.maximum(sleeper_lips, segment_mask(
                x, z, {**start, "z": start["z"] - 0.34}, {**end, "z": end["z"] - 0.34}, 0.3))
        atlas *= 1.0 - sleepers[..., None] * 0.14
        sleeper_tone = wash * np.array((0.90, 0.75, 0.53), dtype=np.float32)
        atlas = atlas * (1.0 - sleeper_lips[..., None] * 0.16) + sleeper_tone * sleeper_lips[..., None] * 0.16

        upper_zone = zones["upper-ore-yard"]
        coal = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        for anchor in factory["tileParams"]["harvestAnchors"]:
            if anchor["z"] < upper_zone["minZ"]:
                continue
            coal = np.maximum(coal, gaussian(x, z, anchor["x"], anchor["z"], 4.2, 2.8))
        coal_tone = rock * np.array((0.22, 0.20, 0.18), dtype=np.float32)
        atlas = atlas * (1.0 - coal[..., None] * 0.44) + coal_tone * coal[..., None] * 0.44
        glitter = coal * (claim.tiled_sample(bank_c, u, v, 41.0, 0.31, 0.77)[..., 0] > 0.66)
        atlas = atlas + glitter[..., None] * np.array((0.10, 0.09, 0.07), dtype=np.float32)

        pads = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        for mount in profile["mounts"]:
            pads = np.maximum(pads, gaussian(x, z, mount["position"][0], mount["position"][2], 4.2, 3.4))
        pad_tone = rock * np.array((0.70, 0.60, 0.46), dtype=np.float32)
        atlas = atlas * (1.0 - pads[..., None] * 0.24) + pad_tone * pads[..., None] * 0.24
        atlas = np.clip(atlas, 0.0, 1.0)

    edge = smoothstep(43.0, 48.0, np.maximum(ax, az))[..., None]
    edge_tone = rock * np.array((0.60, 0.49, 0.36), dtype=np.float32)
    atlas = atlas * (1.0 - edge * 0.42) + edge_tone * edge * 0.42
    atlas = claim.apply_grit_grade(atlas, rail_plate, u, v, key)

    if post_grade_shade is not None:
        atlas = np.clip(atlas * (1.0 + post_grade_shade[..., None] * 0.52 * TRESTLE_SKY_FILL), 0.008, 0.94)

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
    return image, path


def make_terrain(key, profile, factory, height_at, material):
    vertices = []
    uvs = []
    faces = []
    for zi in range(SEGMENTS + 1):
        game_z = -HALF + HALF * 2.0 * zi / SEGMENTS
        for xi in range(SEGMENTS + 1):
            x = -HALF + HALF * 2.0 * xi / SEGMENTS
            vertices.append((x, -game_z, float(height_at(x, game_z))))
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
            uv_layer.data[loop_index].uv = uvs[mesh.loops[loop_index].vertex_index]
    terrain = bpy.data.objects.new(profile["object"], mesh)
    bpy.context.collection.objects.link(terrain)
    mesh.materials.append(material)
    terrain["render_only"] = True
    terrain["sim_authority"] = "factory contract tables and TileHeight; unchanged"
    terrain["height_socket"] = "Terrain.visualY"
    terrain["contract_id"] = profile["contractId"]
    terrain["tile_id"] = factory["tileParams"]["tileId"]
    terrain["water_mask"] = "deep z=-5..5; shallows to +/-6.25; banks remain visible/placeable beyond"
    terrain["landmark_ownership"] = "mounted separately; preview proxies excluded from GLB"
    return terrain


def make_water_surface(material):
    vertices = []
    uvs = []
    faces = []
    segments = 96
    for xi in range(segments + 1):
        x = -HALF + HALF * 2.0 * xi / segments
        for game_z in (-SIM_SHALLOWS_HALF_WIDTH, SIM_SHALLOWS_HALF_WIDTH):
            vertices.append((x, -game_z, 0.035))
            uvs.append(((x + HALF) / (HALF * 2.0), (game_z + HALF) / (HALF * 2.0)))
    for xi in range(segments):
        a = xi * 2
        b = a + 2
        c = a + 1
        d = b + 1
        faces.extend(((a, d, b), (a, c, d)))
    mesh = bpy.data.meshes.new("RenderHelperE2WaterMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("RenderHelperE2Water", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(material)
    return obj


def preview_materials(key):
    prefix = key.title().replace("-", "")
    return {
        "timber": claim.make_render_material(f"{prefix}TarredTimber", (0.13, 0.075, 0.035)),
        "wood": claim.make_render_material(f"{prefix}SplitWood", (0.29, 0.15, 0.055)),
        "rust": claim.make_render_material(f"{prefix}FlakedRust", (0.29, 0.105, 0.035), 0.72, 0.30),
        "iron": claim.make_render_material(f"{prefix}SootIron", (0.055, 0.050, 0.043), 0.64, 0.42),
        "stone": claim.make_render_material(f"{prefix}SootStone", (0.19, 0.17, 0.13)),
        "dark": claim.make_render_material(f"{prefix}MineDark", (0.012, 0.010, 0.008)),
        "cactus": claim.make_render_material(f"{prefix}Cactus", (0.055, 0.14, 0.045)),
        "cactus_light": claim.make_render_material(f"{prefix}CactusEdge", (0.10, 0.22, 0.065)),
        "crop": claim.make_render_material(f"{prefix}HardyCrop", (0.12, 0.20, 0.055)),
        "coal": claim.make_render_material(f"{prefix}Coal", (0.018, 0.016, 0.014), 0.88, 0.05),
        "steam": claim.make_render_material(f"{prefix}Steam", (0.46, 0.43, 0.34), 0.96, 0.0),
        "mask": claim.make_render_material(f"{prefix}MaskTeal", (0.035, 0.52, 0.49), 0.55, 0.08),
        "danger": claim.make_render_material(f"{prefix}MaskRust", (0.58, 0.085, 0.025), 0.55, 0.08),
    }


def rail_height(key, height_at, x, z):
    base = float(height_at(x, z)) + 0.13
    if key == "trestle" and abs(x) < 1.8 and abs(z) <= 7.2:
        return max(base, 0.72)
    if key == "hill-mine" and abs(z) <= 4.0:
        return max(base, 0.42)
    if key == "incline" and abs(abs(x) - 12.0) < 1.8 and abs(z) <= 7.2:
        return max(base, 0.56)
    return base


def add_rails(key, factory, height_at, materials):
    objects = []
    for route_index, rail in enumerate(factory["tileParams"]["rails"]):
        points = rail["points"]
        left = []
        right = []
        for index, point in enumerate(points):
            if index == len(points) - 1:
                other = points[index - 1]
                dx, dz = point["x"] - other["x"], point["z"] - other["z"]
            else:
                other = points[index + 1]
                dx, dz = other["x"] - point["x"], other["z"] - point["z"]
            length = max(math.hypot(dx, dz), 0.001)
            ox, oz = -dz / length * 0.43, dx / length * 0.43
            h = rail_height(key, height_at, point["x"], point["z"])
            left.append((point["x"] + ox, point["z"] + oz, h))
            right.append((point["x"] - ox, point["z"] - oz, h))
        objects.append(claim.add_curve(f"RenderHelperRail.{route_index}.L", left, 0.055, materials["iron"]))
        objects.append(claim.add_curve(f"RenderHelperRail.{route_index}.R", right, 0.055, materials["iron"]))
        sleeper_index = 0
        for a, b in zip(points, points[1:]):
            dx, dz = b["x"] - a["x"], b["z"] - a["z"]
            length = math.hypot(dx, dz)
            count = max(1, int(length / 2.4))
            yaw = math.atan2(dz, dx)
            for step in range(count):
                t = (step + 0.5) / count
                x, z = a["x"] + dx * t, a["z"] + dz * t
                h = rail_height(key, height_at, x, z) - 0.10
                objects.append(claim.add_box_game(f"RenderHelperSleeper.{route_index}.{sleeper_index}", x, z, h, (1.65, 0.22, 0.11), materials["timber"], yaw=yaw, bevel=0.015))
                sleeper_index += 1
    return objects


def add_hill_landmarks(height_at, materials):
    objects = []
    mouth_x, mouth_z = -6.0, 41.0
    base = float(height_at(mouth_x, mouth_z))
    objects.append(claim.add_box_game("RenderHelperMineMouth", mouth_x, mouth_z, base + 0.15, (6.2, 1.1, 3.1), materials["dark"], bevel=0.10))
    for side in (-2.8, 2.8):
        objects.append(claim.add_beam(f"RenderHelperHeadframeLeg.{side}", (mouth_x + side, mouth_z - 1.1, base), (mouth_x + side * 0.72, mouth_z - 1.1, base + 6.4), 0.34, materials["timber"]))
    objects.append(claim.add_beam("RenderHelperHeadframeTop", (mouth_x - 2.2, mouth_z - 1.1, base + 6.2), (mouth_x + 2.2, mouth_z - 1.1, base + 6.2), 0.38, materials["timber"]))
    objects.append(claim.add_beam("RenderHelperHeadframeBrokenBrace", (mouth_x - 2.3, mouth_z - 1.0, base + 0.6), (mouth_x + 1.7, mouth_z - 1.2, base + 5.7), 0.20, materials["wood"]))
    boiler_base = float(height_at(0, 12))
    objects.append(claim.add_box_game("RenderHelperBoilerRuin", 0, 12, boiler_base, (5.6, 4.0, 1.4), materials["rust"], yaw=0.08, tilt=(0.06, -0.03), bevel=0.08))
    for index, (x, z, scale) in enumerate(((35, 34, (3.2, 2.3, 1.7)), (39, 29, (2.5, 1.8, 1.2)), (-39, 31, (2.9, 2.1, 1.4)), (-31, 43, (2.1, 1.5, 1.1)))):
        objects.append(claim.add_rock(f"RenderHelperHillScree.{index}", x, z, scale, materials["stone"], yaw=index * 0.7))
    for index, (x, z, scale, flip, yaw) in enumerate(((-41, 13, 0.82, 1, 0.2), (42, 18, 0.96, -1, -0.4), (-43, -24, 0.72, -1, 0.8))):
        objects.extend(claim.make_cactus(f"RenderHelperHillCactus.{index}", x, z, scale, materials, flip, yaw, height_at))
    return objects


def add_trestle_landmarks(height_at, materials):
    objects = []
    deck = 0.64
    for z in (-6.0, -2.0, 2.0, 6.0):
        ground = float(height_at(0, z))
        for x in (-1.45, 1.45):
            objects.append(claim.add_beam(f"RenderHelperTrestleLeg.{x}.{z}", (x, z, ground + 0.05), (x * 0.78, z, deck), 0.26, materials["timber"]))
        objects.append(claim.add_beam(f"RenderHelperTrestleCross.{z}", (-1.7, z, deck), (1.7, z, deck), 0.24, materials["wood"]))
    objects.append(claim.add_box_game("RenderHelperTrestleDeck", 0, 0, deck - 0.16, (2.6, 14.6, 0.22), materials["timber"], bevel=0.025))
    for index, (x, z, yaw) in enumerate(((12, -12, 0.08), (-12, 12, -0.06))):
        base = float(height_at(x, z))
        objects.append(claim.add_box_game(f"RenderHelperBoilerSite.{index}", x, z, base, (5.0, 4.0, 0.55), materials["stone"], yaw=yaw, bevel=0.10))
        objects.append(claim.add_box_game(f"RenderHelperBoilerScrap.{index}", x + 0.6, z - 0.3, base + 0.45, (2.4, 1.5, 1.0), materials["rust"], yaw=yaw - 0.12, tilt=(0.08, 0.02), bevel=0.06))
    for index, (x, z, scale) in enumerate(((-38, -3, (3.2, 2.2, 1.6)), (39, 6, (3.6, 2.4, 1.8)), (-34, 16, (2.2, 1.5, 1.1)), (35, -20, (2.5, 1.7, 1.2)))):
        objects.append(claim.add_rock(f"RenderHelperGorgeRock.{index}", x, z, scale, materials["stone"], yaw=index * 0.55))
    for index, (x, z, scale, flip, yaw) in enumerate(((-43, 22, 0.78, 1, 0.3), (44, -25, 0.86, -1, -0.4), (41, 30, 0.68, 1, 0.8))):
        objects.extend(claim.make_cactus(f"RenderHelperTrestleCactus.{index}", x, z, scale, materials, flip, yaw, height_at))
    return objects


def add_pressure_garden_preview(factory, mask_document, height_at, materials):
    objects = []
    for index, marker in enumerate(factory["tileParams"]["stakeMarkers"]):
        x, z = marker["x"], marker["z"]
        base = float(height_at(x, z))
        objects.append(claim.add_cylinder_between(
            f"RenderHelperPressureBoiler.{index}",
            (x - 1.55, z, base + 0.85),
            (x + 1.55, z, base + 0.85),
            0.82,
            materials["rust"],
            vertices=10,
        ))
        objects.append(claim.add_cylinder_between(
            f"RenderHelperPressureStack.{index}",
            (x + 1.05, z + 0.25, base + 1.25),
            (x + 1.05, z + 0.25, base + 3.7 - index * 0.18),
            0.20,
            materials["iron"],
            vertices=8,
        ))
        objects.append(claim.add_beam(
            f"RenderHelperPressurePipe.{index}",
            (x - 1.1, z - 0.6, base + 0.35),
            (x - 4.0 + index * 4.0, z - 2.0, base + 0.28),
            0.12,
            materials["iron"],
        ))
    for zone_index, zone_id in enumerate(("west-growing-terrace", "east-growing-terrace")):
        zone = next(zone for zone in factory["tileParams"]["buildZones"] if zone["id"] == zone_id)
        for row_index, x in enumerate(np.linspace(zone["minX"] + 2.0, zone["maxX"] - 2.0, 6)):
            z = (zone["minZ"] + zone["maxZ"]) * 0.5
            base = float(height_at(float(x), z))
            objects.append(claim.add_box_game(
                f"RenderHelperGardenFurrow.{zone_index}.{row_index}",
                float(x), z, base + 0.035, (0.34, zone["maxZ"] - zone["minZ"] - 1.2, 0.07),
                materials["crop"], yaw=0.0, bevel=0.01,
            ))
    for index, seam in enumerate(mask_document["maskTruth"].get("coalSeams", [])):
        for piece in range(5):
            angle = piece * 2.399 + index * 0.7
            x = seam["x"] + math.cos(angle) * (0.65 + piece * 0.21)
            z = seam["z"] + math.sin(angle) * (0.45 + piece * 0.16)
            objects.append(claim.add_rock(
                f"RenderHelperCoalSeam.{index}.{piece}", x, z,
                (0.55 + piece * 0.06, 0.42 + piece * 0.04, 0.30 + piece * 0.03),
                materials["coal"], yaw=angle,
            ))
    for index, (x, z, scale, flip, yaw) in enumerate(((-43, 31, 0.72, 1, 0.2), (43, 27, 0.82, -1, -0.5), (-40, -25, 0.66, -1, 0.8))):
        objects.extend(claim.make_cactus(f"RenderHelperGardenCactus.{index}", x, z, scale, materials, flip, yaw, height_at))
    return objects


def add_incline_preview(factory, height_at, materials):
    objects = []
    lower = next(marker for marker in factory["tileParams"]["stakeMarkers"] if marker["id"] == "lower-engine-house")
    lower_base = float(height_at(lower["x"], lower["z"]))
    objects.append(claim.add_box_game("RenderHelperLowerEngineFoundation", lower["x"], lower["z"], lower_base, (7.0, 5.0, 0.65), materials["stone"], yaw=-0.08, bevel=0.08))
    objects.append(claim.add_box_game("RenderHelperLowerEngineScrap", lower["x"] + 0.4, lower["z"] - 0.2, lower_base + 0.58, (4.2, 2.8, 1.65), materials["rust"], yaw=0.06, tilt=(0.04, -0.03), bevel=0.06))
    upper = next(marker for marker in factory["tileParams"]["stakeMarkers"] if marker["id"] == "upper-winch-house")
    upper_base = float(height_at(upper["x"], upper["z"]))
    for side in (-2.4, 2.4):
        objects.append(claim.add_beam(
            f"RenderHelperUpperWinchLeg.{side}",
            (upper["x"] + side, upper["z"], upper_base),
            (upper["x"] + side * 0.72, upper["z"], upper_base + 4.8),
            0.28, materials["timber"],
        ))
    objects.append(claim.add_beam("RenderHelperUpperWinchTop", (-1.8, upper["z"], upper_base + 4.6), (1.8, upper["z"], upper_base + 4.6), 0.32, materials["timber"]))
    for route_index, x in enumerate((-12.0, 12.0)):
        for cart_index, z in enumerate((-22.0 + route_index * 6.0, 25.0 + route_index * 7.0)):
            base = rail_height("incline", height_at, x, z)
            objects.append(claim.add_box_game(
                f"RenderHelperInclineCart.{route_index}.{cart_index}", x, z, base + 0.02,
                (2.2, 3.2, 1.15), materials["rust"], yaw=math.pi / 2, tilt=(0.03, -0.04), bevel=0.05,
            ))
    for index, (x, z, scale) in enumerate(((-42, 35, (3.6, 2.5, 1.8)), (40, 41, (3.1, 2.2, 1.5)), (-39, 18, (2.7, 2.0, 1.3)), (38, -23, (2.4, 1.8, 1.2)))):
        objects.append(claim.add_rock(f"RenderHelperInclineScree.{index}", x, z, scale, materials["stone"], yaw=index * 0.63))
    for index, (x, z, scale, flip, yaw) in enumerate(((-43, -28, 0.72, 1, 0.3), (43, 22, 0.78, -1, -0.4))):
        objects.extend(claim.make_cactus(f"RenderHelperInclineCactus.{index}", x, z, scale, materials, flip, yaw, height_at))
    return objects


def add_frontier_clutter(key, factory, height_at, materials):
    """Mounted-pack preview only; keep build pads and water visibly clear."""
    rng = np.random.default_rng({"hill-mine": 214, "trestle": 322, "pressure-garden": 451, "incline": 587}[key])
    objects = []

    def clear(x, z):
        if abs(z) <= SIM_SHALLOWS_HALF_WIDTH + 1.0:
            return False
        for rail in factory["tileParams"]["rails"]:
            for a, b in zip(rail["points"], rail["points"][1:]):
                if float(segment_mask(np.asarray(x), np.asarray(z), a, b, 2.2)) > 0.12:
                    return False
        return not any(
            zone["minX"] - 1.4 <= x <= zone["maxX"] + 1.4
            and zone["minZ"] - 1.4 <= z <= zone["maxZ"] + 1.4
            for zone in factory["tileParams"]["buildZones"]
        )

    placed = 0
    for _attempt in range(220):
        if placed >= 34:
            break
        x = float(rng.uniform(-45.0, 45.0))
        z = float(rng.uniform(-44.0, 45.0))
        if not clear(x, z):
            continue
        scale = float(rng.uniform(0.28, 0.78))
        objects.append(
            claim.add_rock(
                f"RenderHelperFrontierRubble.{placed}",
                x,
                z,
                (scale * rng.uniform(0.9, 1.55), scale * rng.uniform(0.7, 1.2), scale * rng.uniform(0.55, 0.95)),
                materials["stone"] if placed % 4 else materials["rust"],
                yaw=float(rng.uniform(-math.pi, math.pi)),
            )
        )
        if placed % 5 == 0:
            ground = float(height_at(x, z))
            objects.append(
                claim.add_box_game(
                    f"RenderHelperBrokenTimber.{placed}",
                    x + 0.5,
                    z - 0.3,
                    ground + 0.02,
                    (float(rng.uniform(1.2, 2.4)), 0.18, 0.16),
                    materials["wood"],
                    yaw=float(rng.uniform(-math.pi, math.pi)),
                    tilt=(float(rng.uniform(-0.10, 0.10)), float(rng.uniform(-0.08, 0.08))),
                    bevel=0.015,
                )
            )
        placed += 1
    return objects


def add_mask_overlay(factory, mask_document, height_at, materials):
    objects = []
    for zone in factory["tileParams"]["buildZones"]:
        corners = [
            (zone["minX"], zone["minZ"]),
            (zone["maxX"], zone["minZ"]),
            (zone["maxX"], zone["maxZ"]),
            (zone["minX"], zone["maxZ"]),
            (zone["minX"], zone["minZ"]),
        ]
        points = [(x, z, float(height_at(x, z)) + 0.28) for x, z in corners]
        objects.append(claim.add_curve(f"RenderHelperBuildZone.{zone['id']}", points, 0.13, materials["mask"]))
    for marker in factory["tileParams"]["stakeMarkers"]:
        base = float(height_at(marker["x"], marker["z"]))
        objects.append(claim.add_box_game(f"RenderHelperStake.{marker['id']}", marker["x"], marker["z"], base, (1.0, 1.0, 2.2), materials["danger"], bevel=0.04))
    for index, seam in enumerate(mask_document["maskTruth"].get("coalSeams", [])):
        base = float(height_at(seam["x"], seam["z"]))
        objects.append(claim.add_box_game(
            f"RenderHelperCoalMask.{index}", seam["x"], seam["z"], base + 0.05,
            (1.25, 1.25, 0.22), materials["danger"], yaw=index * 0.42, bevel=0.04,
        ))
    return objects


def render_verdicts(key, profile, factory, terrain, water, preview, mask_overlay):
    backdrop = claim.make_backdrop()
    panorama = claim.link_panorama(key)
    for obj in panorama:
        obj.hide_render = True
    if key == "hill-mine":
        run = claim.add_camera(f"{profile['object']}RunCamera", (0.0, 35.0, 29.0), (0.0, -12.0, 1.5), 42.0)
    elif key == "trestle":
        run = claim.add_camera(f"{profile['object']}RunCamera", (0.0, 36.0, 28.0), (0.0, 12.0, 0.3), 42.0)
    elif key == "pressure-garden":
        run = claim.add_camera(f"{profile['object']}RunCamera", (0.0, 38.0, 30.0), (0.0, -12.0, 1.35), 42.0)
    else:
        run = claim.add_camera(f"{profile['object']}RunCamera", (28.0, 40.0, 31.0), (0.0, -12.0, 1.55), 43.0)
    low_locations = {
        "hill-mine": (-43.0, 34.0, 13.5),
        "trestle": (-43.0, 34.0, 13.5),
        "pressure-garden": (-45.0, 37.0, 14.0),
        "incline": (-46.0, 31.0, 15.0),
    }
    low_targets = {
        "hill-mine": (3.0, -4.0, 1.0),
        "trestle": (3.0, -4.0, 1.0),
        "pressure-garden": (4.0, -12.0, 1.4),
        "incline": (2.0, -15.0, 1.7),
    }
    low = claim.add_camera(f"{profile['object']}LowCamera", low_locations[key], low_targets[key], 48.0)
    top = claim.add_camera(f"{profile['object']}MaskCamera", (0.0, 0.0, 103.0), (0.0, 0.0, 0.0), 52.0)
    overview_y = 62.0 if key in {"hill-mine", "pressure-garden", "incline"} else -62.0
    overview = claim.add_camera(f"{profile['object']}OverviewCamera", (0.0, overview_y, 68.0), (0.0, -4.0, 1.8), 47.0)
    horizon_target = {
        "hill-mine": (110.0, -120.0, 8.0),
        "trestle": (118.0, -70.0, 8.0),
        "pressure-garden": (-105.0, -125.0, 8.0),
        "incline": (125.0, -108.0, 10.0),
    }[key]
    horizon = claim.add_camera(f"{profile['object']}HorizonCamera", (0.0, 0.0, 3.4), horizon_target, 52.0)
    # Panorama radius is 190 m.  The off-centre sunset camera can be more than
    # 240 m from the far quadrant, so the generic helper's clip plane cuts a
    # purple world-colour dome through the ring.  This is evidence-camera only.
    low.data.clip_end = 420.0
    horizon.data.clip_end = 420.0

    lights = claim.add_lighting(sunset=False)
    for obj in preview + mask_overlay:
        obj.hide_render = True
    original_heights = [vertex.co.z for vertex in terrain.data.vertices]
    for vertex in terrain.data.vertices:
        vertex.co.z = 0.0
    terrain.data.update()
    claim.render(run, ARTIFACTS / f"{key}-flat-tile-identical-camera.png")
    for vertex, height in zip(terrain.data.vertices, original_heights):
        vertex.co.z = height
    terrain.data.update()
    claim.render(run, ARTIFACTS / f"{key}-sculpted-tile-identical-camera.png")

    for obj in preview:
        obj.hide_render = False
    claim.render(run, ARTIFACTS / f"{key}-run-camera.png")
    claim.render(overview, ARTIFACTS / f"{key}-overview.png")
    for obj in mask_overlay:
        obj.hide_render = False
    claim.render(top, ARTIFACTS / f"{key}-mask-agreement.png")
    for obj in mask_overlay:
        obj.hide_render = True

    claim.remove_objects(lights)
    low_lights = claim.add_lighting(sunset=True)
    bpy.context.scene.view_settings.exposure = 0.9
    claim.render(low, ARTIFACTS / f"{key}-panorama-before.png")
    for obj in panorama:
        obj.hide_render = False
    claim.render(low, ARTIFACTS / f"{key}-low-sunset.png")
    claim.render(low, ARTIFACTS / f"{key}-panorama-mounted.png")
    claim.render(horizon, ARTIFACTS / f"{key}-panorama-horizon.png")
    bpy.context.scene.view_settings.exposure = 0.0
    claim.remove_objects(low_lights + [run, low, top, overview, horizon, backdrop] + panorama)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def derived_mask_truth(factory):
    params = factory["tileParams"]
    twist = factory["twist"]
    return {
        "source": str(FACTORY_CONTRACTS.relative_to(ROOT)),
        "tileId": params["tileId"],
        "size": params["size"],
        "river": params["river"],
        "ford": params["ford"],
        "fords": params["fords"],
        "buildZones": params["buildZones"],
        "stakeMarkers": params["stakeMarkers"],
        "rails": params["rails"],
        "waterSources": params["waterSources"],
        "harvestAnchors": params["harvestAnchors"],
        "elevation": params["elevation"],
        "heightfield": params["heightfield"],
        "water": params["water"],
        "lanes": params["lanes"],
        "spawnGates": [gate for enemy in twist["enemyRoster"] for gate in enemy.get("spawnGates", [])],
    }


def carry_forward_mount_records(profile, mounts):
    """Keep the fields a LATER pipeline step wrote onto each mount.

    Ported verbatim in intent from `build_unique_contract_terrains.py:1404` (the e1-baron beauty
    shift's fix) because the same trap is armed here: this builder authors mount ids and planar
    positions from its own PROFILES table, and `build_landmark_packs.py` / `apply_mounts_sweep.py`
    then backfill the runtime-critical `asset` path, the terrain-conformed Y and the top-level
    `landmarkPack` block. The runtime resolves each body through `mount.asset`
    (Terrain3dClaimPilot.ts `mounts.filter((mount) => mount.asset)`), so a faithful atlas re-export
    used to silently un-mount every landmark and fall back to painted ground with no error anywhere
    — every gate green, five buildings gone (CLAUDE.md Mistake #10). e2-hill-mine ships five mounts
    all carrying `asset`, one carrying `terrainConformOffsetY`, and a `landmarkPack` block.

    Preservation only, never invention: extras carry over ONLY when the rebuilt mount sits at the
    same planar X/Z, so a genuinely moved or renamed mount still re-derives from scratch.
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


def make_contract(key, profile, factory, mask_document, terrain, atlas_path):
    coords = np.asarray([vertex.co[:] for vertex in terrain.data.vertices], dtype=np.float32)
    triangles = sum(len(poly.vertices) - 2 for poly in terrain.data.polygons)
    mounts, landmark_pack = carry_forward_mount_records(profile, profile["mounts"])
    # Prove it by DATASET, not by rc=0: a re-export that drops an `asset` is the one failure mode
    # this whole function exists to stop, so it is also the one the builder refuses to ship.
    carried = sum(1 for entry in mounts if entry.get("asset"))
    if profile["mounts"] and carried != len(profile["mounts"]):
        raise ValueError(
            f"{key}: {carried}/{len(profile['mounts'])} landmark mounts carry an asset path — "
            "refusing to write a contract that would un-mount landmarks (CLAUDE.md Mistake #10)"
        )
    contract = {
        "asset": f"{profile['stem']}.glb",
        "contractId": profile["contractId"],
        "tileId": factory["tileParams"]["tileId"],
        "renderOnly": True,
        "simulation": "factory masks, collision, movement, spawns, placement, and TileHeight remain unchanged",
        "heightSocket": "Terrain.visualY",
        "theme": profile["theme"],
        "regionalFamily": {
            "epoch": "Epoch 2 steamworks county",
            "shared": ["ochre-rust earth", "soot iron", "tarred timber", "murky working water", "sparse cacti", "engraved frontier grit"],
            "unique": ["authored height silhouette", "rail geometry", "build-zone rhythm", "landmark mounts", "panorama quadrant composition"],
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
        "maskTruth": mask_document["maskTruth"],
        "waterAgreement": mask_document["waterAgreement"],
        "waterVisualRuling": "render bank seam follows the gameplay mask so sluice-placeable banks do not look submerged",
        "landmarkMountSpace": claim.landmark_mount_space(),
        "landmarkMounts": mounts,
        "panoramaMount": claim.panorama_mount(key),
        "sourceArt": list(dict.fromkeys(str(path.relative_to(ROOT)) for path in (claim.BANK_A, claim.BANK_B, claim.BANK_C, claim.RIVER, RAIL_PLATE, KIT, profile["sourcePlate"]))),
        "atlas": atlas_path.name,
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


def build(key):
    profile = PROFILES[key]
    factory = authored_contract(profile["contractId"])
    mask_document = authored_mask(key, factory)
    if factory["tileParams"]["size"] != HALF * 2:
        raise ValueError(f"{key} authored size changed; review the terrain bounds before rebuilding")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    claim.reset_scene()
    atlas, atlas_path = make_atlas(key, profile, factory, mask_document)
    material = claim.make_material(atlas)
    material.name = profile["material"]
    height_at = height_function(key, factory)
    claim.terrain_height = height_at
    terrain = make_terrain(key, profile, factory, height_at, material)
    water_material = claim.make_water_material(
        f"RenderHelper{profile['object']}Water",
        (0.018, 0.023, 0.020),
        (0.11, 0.13, 0.09),
        0.82,
    )
    # The E2 run camera is shallow enough that the default verdict material can
    # catch the full key light as a white disk.  Keep the shipped-water read
    # murky and workmanlike; this helper never enters the terrain GLB.
    water_shader = water_material.node_tree.nodes.get("Principled BSDF")
    if water_shader:
        specular = water_shader.inputs.get("Specular IOR Level")
        if specular:
            specular.default_value = 0.18
        coat = water_shader.inputs.get("Coat Weight")
        if coat:
            coat.default_value = 0.0
    water = make_water_surface(water_material)
    materials = preview_materials(key)
    preview = add_rails(key, factory, height_at, materials)
    if key == "hill-mine":
        preview.extend(add_hill_landmarks(height_at, materials))
    elif key == "trestle":
        preview.extend(add_trestle_landmarks(height_at, materials))
    elif key == "pressure-garden":
        preview.extend(add_pressure_garden_preview(factory, mask_document, height_at, materials))
    else:
        preview.extend(add_incline_preview(factory, height_at, materials))
    preview.extend(add_frontier_clutter(key, factory, height_at, materials))
    mask_overlay = add_mask_overlay(factory, mask_document, height_at, materials)
    render_verdicts(key, profile, factory, terrain, water, preview, mask_overlay)
    claim.remove_objects([water] + preview + mask_overlay)
    bpy.context.scene.world = None
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    contract = make_contract(key, profile, factory, mask_document, terrain, atlas_path)
    export_asset(profile, terrain, contract)


def main():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    keys = args or list(PROFILES)
    for key in keys:
        if key not in PROFILES:
            raise ValueError(f"unsupported authored E2 terrain: {key}")
        build(key)


if __name__ == "__main__":
    main()
