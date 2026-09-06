"""Build authored Voltage-through-Deep-Sky render terrains.

The published mask tables are copied verbatim into each asset contract.  All
geometry is render-only; gameplay remains planar and code-owned.  Preview
rails, lights, water, and mask overlays are removed before save/export.
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
FACTORIES = (
    ROOT / "assets/contracts/epoch-3-voltage/contracts.json",
    ROOT / "assets/contracts/epoch-4-motor/contracts.json",
    ROOT / "assets/contracts/epoch-6-atomic/contracts.json",
    ROOT / "assets/contracts/epoch-7-signal/contracts.json",
    ROOT / "assets/contracts/epoch-8-orbital/contracts.json",
    ROOT / "assets/contracts/epoch-10-deepsky/contracts.json",
)
TABLE_DIRS = (
    ROOT / "assets/contracts/epoch-3-voltage/mask-tables",
    ROOT / "assets/contracts/epoch-4-motor/mask-tables",
    ROOT / "assets/contracts/epoch-6-atomic/mask-tables",
    ROOT / "assets/contracts/epoch-7-signal/mask-tables",
    ROOT / "assets/contracts/epoch-8-orbital/mask-tables",
    ROOT / "assets/contracts/epoch-10-deepsky/mask-tables",
)
KIT_E3 = ROOT / "assets/processed/kit-era-3.png"
KIT_E4 = ROOT / "assets/processed/kit-era-4.png"
KIT_E6 = ROOT / "assets/processed/kit-era-6.png"
KIT_E7 = ROOT / "assets/processed/kit-era-7.png"
KIT_E8 = ROOT / "assets/processed/kit-era-8.png"
KIT_E10 = ROOT / "assets/processed/kit-era-10.png"
CANYON_ATLAS = ROOT / "assets/raw/ter-canyon-atlas.png"
MOTH_PLATE = ROOT / "assets/raw/plate-e3-mothswarm.png"
RELAY_PLATE = ROOT / "assets/raw/plate-e7-bld-relay-tower.png"
ORBITAL_PLATE = ROOT / "assets/raw/plate-e8-bld-set.png"
WORLDS_PLATE = ROOT / "assets/raw/plate-e10-worlds.png"
RAIL_PLATE = ROOT / "assets/processed/ter-rail-elements-r0c2.png"
SEGMENTS = 128
ATLAS_SIZE = 2048
DEEP_HALF_WIDTH = 5.0
SHALLOWS_HALF_WIDTH = 6.25


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


e2 = load_module("e3_e2_helpers", OUT / "build_e2_contract_terrains.py")
claim = e2.claim
claim.mathutils = mathutils
claim.CONTRACT_PLATES.update({
    "canyon-works": CANYON_ATLAS,
    "moth-season": MOTH_PLATE,
    "blackout-ridge": KIT_E3,
    "dust-flats": KIT_E4,
    "fairground": KIT_E3,
    "glow-mesa": KIT_E6,
    "relay-valley": RELAY_PLATE,
    "echo-canyon": RELAY_PLATE,
    "mare-claim": ORBITAL_PLATE,
    "ember-shore": WORLDS_PLATE,
})
claim.GRIT_PROFILES.update({
    "canyon-works": {"black": 0.010, "white": 0.35, "gamma": 1.28, "ink": 0.48, "palette": 0.14, "saturation": 0.50},
    "moth-season": {"black": 0.008, "white": 0.31, "gamma": 1.31, "ink": 0.50, "palette": 0.12, "saturation": 0.45},
    "blackout-ridge": {"black": 0.006, "white": 0.38, "gamma": 1.22, "ink": 0.48, "palette": 0.15, "saturation": 0.46},
    "dust-flats": {"black": 0.008, "white": 0.62, "gamma": 1.12, "ink": 0.37, "palette": 0.18, "saturation": 0.51},
    "fairground": {"black": 0.008, "white": 0.42, "gamma": 1.18, "ink": 0.46, "palette": 0.16, "saturation": 0.56},
    "glow-mesa": {"black": 0.010, "white": 0.64, "gamma": 1.08, "ink": 0.32, "palette": 0.24, "saturation": 0.62},
    "relay-valley": {"black": 0.009, "white": 0.49, "gamma": 1.18, "ink": 0.45, "palette": 0.22, "saturation": 0.58},
    "echo-canyon": {"black": 0.008, "white": 0.46, "gamma": 1.20, "ink": 0.48, "palette": 0.20, "saturation": 0.56},
    "mare-claim": {"black": 0.010, "white": 0.66, "gamma": 1.10, "ink": 0.39, "palette": 0.20, "saturation": 0.36},
    "ember-shore": {"black": 0.006, "white": 0.47, "gamma": 1.24, "ink": 0.52, "palette": 0.21, "saturation": 0.62},
})

PROFILES = {
    "canyon-works": {
        "contractId": "e3-canyon-works",
        "stem": "canyon-works-terrain",
        "object": "CanyonWorksTerrain",
        "mesh": "CanyonWorksTerrainMesh",
        "material": "CanyonWorksPaintedTerrainMaterial",
        "atlas": "CanyonWorksPaintedTerrainAtlas",
        "width": 96.0,
        "height": 112.0,
        "theme": "night-falling terraced dam gorge with paired flat pylon switchbacks",
        "kit": KIT_E3,
        "sourcePlate": CANYON_ATLAS,
        "epoch": "Epoch 3 voltage canyon",
        "shared": ["ink-blue canyon dusk", "stained copper earth", "deep engraved shadow", "restrained voltage teal", "sparse cacti", "lantern warmth"],
    },
    "moth-season": {
        "contractId": "e3-moth-season",
        "stem": "moth-season-terrain",
        "object": "MothSeasonTerrain",
        "mesh": "MothSeasonTerrainMesh",
        "material": "MothSeasonPaintedTerrainMaterial",
        "atlas": "MothSeasonPaintedTerrainAtlas",
        "width": 80.0,
        "height": 80.0,
        "theme": "two lamp-lit yards flanking a low black north-south migration corridor",
        "kit": KIT_E3,
        "sourcePlate": MOTH_PLATE,
        "epoch": "Epoch 3 voltage canyon",
        "shared": ["ink-blue canyon dusk", "stained copper earth", "deep engraved shadow", "restrained voltage teal", "sparse cacti", "lantern warmth"],
    },
    "blackout-ridge": {
        "contractId": "e3-blackout-ridge",
        "stem": "blackout-ridge-terrain",
        "object": "BlackoutRidgeTerrain",
        "mesh": "BlackoutRidgeTerrainMesh",
        "material": "BlackoutRidgePaintedTerrainMaterial",
        "atlas": "BlackoutRidgePaintedTerrainAtlas",
        "width": 80.0,
        "height": 96.0,
        "theme": "a failing diagonal trunk climb into a cold switch-house ridge with five exact load-bearing sites",
        "kit": KIT_E3,
        "sourcePlate": KIT_E3,
        "epoch": "Epoch 3 voltage canyon",
        "shared": ["ink-blue locked night", "stained copper earth", "deep engraved shadow", "restrained voltage teal", "sparse cacti", "lantern warmth"],
    },
    "dust-flats": {
        "contractId": "e4-dust-flats",
        "stem": "dust-flats-terrain",
        "object": "DustFlatsTerrain",
        "mesh": "DustFlatsTerrainMesh",
        "material": "DustFlatsPaintedTerrainMaterial",
        "atlas": "DustFlatsPaintedTerrainAtlas",
        "width": 160.0,
        "height": 160.0,
        "theme": "vast motor county organized by a wheel-cut orbit road, branching haul corridors, tar scars, and one dry wash",
        "kit": KIT_E4,
        "sourcePlate": KIT_E4,
        "epoch": "Epoch 4 motor frontier",
        "shared": ["dust-warm ochre", "tar-dark stains", "engraved wheel scars", "sun-cracked earth", "sparse cacti", "hazy motor distance"],
    },
    "fairground": {
        "contractId": "e3-fairground",
        "stem": "fairground-terrain",
        "object": "FairgroundTerrain",
        "mesh": "FairgroundTerrainMesh",
        "material": "FairgroundPaintedTerrainMaterial",
        "atlas": "FairgroundPaintedTerrainAtlas",
        "width": 88.0,
        "height": 88.0,
        "theme": "a bruised festival bowl organized by one exact wheel foundation, opposed pavilion shelves, and a wagon-worn south midway",
        "kit": KIT_E3,
        "sourcePlate": KIT_E3,
        "epoch": "Epoch 3 voltage canyon",
        "shared": ["ink-blue voltage dusk", "stained copper earth", "deep engraved shadow", "restrained voltage teal", "sparse cacti", "hard-won lantern warmth"],
    },
    "glow-mesa": {
        "contractId": "e6-glow-mesa",
        "stem": "glow-mesa-terrain",
        "object": "GlowMesaTerrain",
        "mesh": "GlowMesaTerrainMesh",
        "material": "GlowMesaPaintedTerrainMaterial",
        "atlas": "GlowMesaPaintedTerrainAtlas",
        "width": 128.0,
        "height": 128.0,
        "theme": "a true two-level caprock mesa with three legal herd paths, six teal night veins, and timed decay fields on the polished base",
        "kit": KIT_E6,
        "sourcePlate": KIT_E6,
        "epoch": "Epoch 6 atomic homestead",
        "shared": ["parchment warmth", "chrome-pastel enamel", "soft starstone teal", "amber Combine light", "engraved caprock", "fading hatch-step decay"],
    },
    "relay-valley": {
        "contractId": "e7-relay-valley",
        "stem": "relay-valley-terrain",
        "object": "RelayValleyTerrain",
        "mesh": "RelayValleyTerrainMesh",
        "material": "RelayValleyPaintedTerrainMaterial",
        "atlas": "RelayValleyPaintedTerrainAtlas",
        "width": 128.0,
        "height": 128.0,
        "theme": "two exposed h5 shale relay ridges split by a dead gap above a thick h0 teaching valley and three named fog pockets",
        "kit": KIT_E7,
        "sourcePlate": RELAY_PLATE,
        "epoch": "Epoch 7 signal frontier",
        "shared": ["walnut loam", "honey-glass warmth", "agent-teal signal", "engraved shale", "punch-tape scars", "dead-zone fog hatch"],
    },
    "echo-canyon": {
        "contractId": "e7-echo-canyon",
        "stem": "echo-canyon-terrain",
        "object": "EchoCanyonTerrain",
        "mesh": "EchoCanyonTerrainMesh",
        "material": "EchoCanyonPaintedTerrainMaterial",
        "atlas": "EchoCanyonPaintedTerrainAtlas",
        "width": 128.0,
        "height": 128.0,
        "theme": "a long h0 broadcast floor trapped between two exact h5 echo shelves, open only at the north and south enemy mouths",
        "kit": KIT_E7,
        "sourcePlate": RELAY_PLATE,
        "epoch": "Epoch 7 signal frontier",
        "shared": ["walnut loam", "honey-glass warmth", "agent-teal signal", "engraved shale", "punch-tape scars", "broadcast-echo hatch"],
    },
    "mare-claim": {
        "contractId": "e8-mare-claim",
        "stem": "mare-claim-terrain",
        "object": "MareClaimTerrain",
        "mesh": "MareClaimTerrainMesh",
        "material": "MareClaimPaintedTerrainMaterial",
        "atlas": "MareClaimPaintedTerrainAtlas",
        "width": 128.0,
        "height": 128.0,
        "theme": "a warm-grey crater claim held inside one exact h6 rim ring, with a black lava-tube mouth, landing scorch, and mass-driver scar across an intentionally empty mare",
        "kit": KIT_E8,
        "sourcePlate": ORBITAL_PLATE,
        "epoch": "Epoch 8 orbital claim",
        "shared": ["warm grey stippled engraving", "silver-and-teal over parchment", "brass work scars", "glass-dome honey light", "basalt shadow pockets", "drawn vacuum negative space"],
    },
    "ember-shore": {
        "contractId": "e10-ember-shore",
        "stem": "ember-shore-terrain",
        "object": "EmberShoreTerrain",
        "mesh": "EmberShoreTerrainMesh",
        "material": "EmberShorePaintedTerrainMaterial",
        "atlas": "EmberShorePaintedTerrainAtlas",
        "width": 128.0,
        "height": 128.0,
        "theme": "a preserve-contract shore divided by three exact cooling lava-vein bands, with one flat last-warm-vent footing and one flat cooled-titan machine mount",
        "kit": KIT_E10,
        "sourcePlate": WORLDS_PLATE,
        "epoch": "Epoch 10 Deep Sky first world",
        "shared": ["deep-ink basalt", "parchment-gold ember", "teal salvage glass", "engraved star stipple", "cooled machine shadow", "preserve-contract warmth"],
    },
}

LANDMARK_MOUNTS = {
    "echo-canyon": [
        {"id": "south-broadcast-gate", "position": [0.0, 0.0, -50.0], "rotation": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0], "asset": ""},
        {"id": "west-echo-array", "position": [-43.0, 0.0, 8.0], "rotation": [0.0, 0.18, 0.0], "scale": [1.0, 1.0, 1.0], "asset": ""},
        {"id": "east-echo-array", "position": [43.0, 0.0, -4.0], "rotation": [0.0, -0.16, 0.0], "scale": [1.0, 1.0, 1.0], "asset": ""},
        {"id": "mirror-observation-post", "position": [0.0, 0.0, 23.0], "rotation": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0], "asset": ""},
        {"id": "north-return-gate", "position": [0.0, 0.0, 50.0], "rotation": [0.0, 3.1416, 0.0], "scale": [1.0, 1.0, 1.0], "asset": ""},
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


def factory_contract(contract_id):
    matches = []
    for factory in FACTORIES:
        document = json.loads(factory.read_text(encoding="utf-8"))
        matches.extend(entry for entry in document["contracts"] if entry["id"] == contract_id)
    if len(matches) != 1:
        raise ValueError(f"expected one factory contract for {contract_id}; found {len(matches)}")
    return matches[0]


def mask_table(contract_id):
    matches = [directory / f"{contract_id}.json" for directory in TABLE_DIRS if (directory / f"{contract_id}.json").is_file()]
    if len(matches) != 1:
        raise FileNotFoundError(f"expected one authored table for {contract_id}; found {matches}")
    path = matches[0]
    return json.loads(path.read_text(encoding="utf-8")), path


def canyon_base_height(x, z, analytic):
    return e2.hill_sim_height(np.asarray(x, dtype=np.float32), np.asarray(z, dtype=np.float32), analytic)


def load_bearing_sites(table):
    truth = table["maskTruth"]
    return [("pylon", site) for site in truth.get("pylonSites", [])] + [("capacitor", site) for site in truth.get("capacitorSites", [])]


def height_function(key, factory, table):
    params = factory["tileParams"]

    if key == "canyon-works":
        analytic = table["maskTruth"]["elevation"]["analytic"]
        analytic_without_cliff = dict(analytic)
        analytic_without_cliff["cliffAmp"] = 0.0
        site_targets = [
            (site, float(canyon_base_height(site["x"], site["z"], analytic)))
            for site in table["maskTruth"]["pylonSites"]
        ]

        def height(x, z):
            xx = np.asarray(x, dtype=np.float32)
            zz = np.asarray(z, dtype=np.float32)
            terrace_warp = np.sin(xx * 0.15) * 0.75 + np.sin(xx * 0.37 + 0.8) * 0.34
            base = canyon_base_height(xx, zz + terrace_warp, analytic_without_cliff)
            # Keep the authored cliff footprint and amplitude, but erode its
            # render silhouette into a broken mesa instead of reproducing the
            # factory analytic as a rectangular plinth.  The simulation still
            # owns the original flat-plane height table.
            cliff_left = analytic["cliffMinX"] + 1.4 * np.sin(zz * 0.53) + 0.9 * np.sin(zz * 0.19 + 0.8)
            cliff_right = analytic["cliffMaxX"] + 1.2 * np.sin(zz * 0.47 + 1.9) - 0.8 * np.sin(zz * 0.23)
            cliff_x = (
                smoothstep(cliff_left - 3.4, cliff_left + 1.4, xx)
                * (1.0 - smoothstep(cliff_right - 1.4, cliff_right + 3.4, xx))
            )
            cliff_z = (
                smoothstep(analytic["cliffMinZ"] - 4.2, analytic["cliffMinZ"] + 1.8, zz)
                * (1.0 - smoothstep(analytic["cliffMaxZ"] - 1.8, analytic["cliffMaxZ"] + 4.6, zz))
            )
            cliff = cliff_x * cliff_z
            erosion = np.clip(
                1.0
                - gaussian(xx, zz, -9.0, 20.2, 3.1, 2.7) * 0.42
                - gaussian(xx, zz, 10.2, 24.7, 3.7, 2.5) * 0.34
                - gaussian(xx, zz, 1.7, 18.6, 2.2, 1.8) * 0.22,
                0.28,
                1.0,
            )
            base += analytic["cliffAmp"] * cliff * erosion
            talus = (
                gaussian(xx, zz, -8.5, 15.8, 6.8, 2.9) * 0.42
                + gaussian(xx, zz, 8.0, 29.1, 7.6, 3.4) * 0.34
            )
            base += talus * (1.0 - cliff)
            grain = np.sin(xx * 0.34 + zz * 0.19) * 0.040 + np.sin(xx * 0.12 - zz * 0.41) * 0.024
            calm = np.zeros_like(base)
            for zone in table["maskTruth"]["buildZones"]:
                calm = np.maximum(calm, rectangle_mask(xx, zz, zone, 1.2))
            sculpted = base + grain * (1.0 - calm * 0.88)
            water = 1.0 - smoothstep(DEEP_HALF_WIDTH, SHALLOWS_HALF_WIDTH, np.abs(zz))
            sculpted = sculpted * (1.0 - water) + np.minimum(sculpted, -0.34) * water
            # The exact straight water boundary is load-bearing mask truth.
            # Broken shoulders begin outside it so the view reads as a river
            # cut through terrain rather than a flat strip pasted on top.
            outside_water = smoothstep(SHALLOWS_HALF_WIDTH, SHALLOWS_HALF_WIDTH + 0.7, np.abs(zz))
            bank_shoulder = np.exp(-((np.abs(zz) - 7.45) / 1.45) ** 2)
            bank_break = 0.30 + 0.07 * np.sin(xx * 0.29 + zz * 0.18) + 0.05 * np.sin(xx * 0.61 - zz * 0.12)
            sculpted += outside_water * bank_shoulder * bank_break
            # Load-bearing pylon sites are exact flat disks with a soft visual
            # shoulder outside the authored build radius.  Extend the constant
            # plateau by one terrain-cell diagonal: without that guard band,
            # triangles whose vertices sit just outside the disk interpolate a
            # slope back into the load-bearing radius even though every vertex
            # sampled inside the circle is flat.
            cell_diagonal = math.hypot(
                PROFILES[key]["width"] / SEGMENTS,
                PROFILES[key]["height"] / SEGMENTS,
            )
            for site, target in site_targets:
                distance = np.hypot(xx - site["x"], zz - site["z"])
                plateau_edge = site["radius"] + cell_diagonal
                flat = 1.0 - smoothstep(plateau_edge, plateau_edge + 1.15, distance)
                sculpted = sculpted * (1.0 - flat) + target * flat
            return sculpted

        return height

    zones = table["maskTruth"]["buildZones"]

    if key == "moth-season":
        def height(x, z):
            xx = np.asarray(x, dtype=np.float32)
            zz = np.asarray(z, dtype=np.float32)
            ax = np.abs(xx)
            az = np.abs(zz)
            corridor = -0.55 * gaussian(xx, zz, 0.0, 0.0, 5.5, 34.0)
            west_rim = 2.75 * gaussian(xx, zz, -33.0, 4.0, 9.0, 28.0)
            east_rim = 3.35 * gaussian(xx, zz, 33.0, -5.0, 8.0, 25.0)
            endcaps = smoothstep(28.0, 40.0, az) * (0.85 + smoothstep(15.0, 36.0, ax) * 0.75)
            grain = np.sin(xx * 0.39 + zz * 0.21) * 0.055 + np.sin(xx * 0.17 - zz * 0.47) * 0.030
            sculpted = corridor + west_rim + east_rim + endcaps + grain
            calm = np.zeros_like(sculpted)
            for zone in zones:
                calm = np.maximum(calm, rectangle_mask(xx, zz, zone, 1.0))
            return sculpted * (1.0 - calm * 0.45)

        return height

    if key == "blackout-ridge":
        trunk_points = [(-40.0, -40.0)] + [(site["x"], site["z"]) for site in table["maskTruth"]["pylonSites"]] + [(24.0, 30.0)]

        def raw_height(xx, zz):
            climb = smoothstep(-38.0, 38.0, (xx + zz) * 0.5)
            ridge = 5.45 * climb
            cross_ridge = zz - xx - 2.0
            # A broken, stepped landform carries the pylon climb.  It must be
            # visible as geometry before the dark trunk paint is applied.
            diagonal_spine = np.exp(-((cross_ridge / 7.4) ** 2)) * smoothstep(-34.0, 34.0, zz) * 1.72
            diagonal_ledge = (
                smoothstep(-9.5, -3.0, cross_ridge)
                * (1.0 - smoothstep(3.0, 9.5, cross_ridge))
                * (0.48 + 0.16 * np.sin((xx + zz) * 0.24))
            )
            switch_shelf = gaussian(xx, zz, 24.0, 30.0, 14.0, 10.0) * 1.05
            west_cut = gaussian(xx, zz, -34.0, -8.0, 8.0, 29.0) * -0.55
            broken = np.sin(xx * 0.31 + zz * 0.19) * 0.065 + np.sin(xx * 0.13 - zz * 0.43) * 0.038
            trunk_center = np.zeros_like(xx)
            trunk_shoulder = np.zeros_like(xx)
            for start, end in zip(trunk_points, trunk_points[1:]):
                a, b = {"x": start[0], "z": start[1]}, {"x": end[0], "z": end[1]}
                trunk_center = np.maximum(trunk_center, e2.segment_mask(xx, zz, a, b, 0.62))
                trunk_shoulder = np.maximum(trunk_shoulder, e2.segment_mask(xx, zz, a, b, 2.55))
            return 0.22 + ridge + diagonal_spine + diagonal_ledge + switch_shelf + west_cut + broken + trunk_shoulder * 0.30 - trunk_center * 0.54

        targets = [(kind, site, float(raw_height(site["x"], site["z"]))) for kind, site in load_bearing_sites(table)]

        def height(x, z):
            xx = np.asarray(x, dtype=np.float32)
            zz = np.asarray(z, dtype=np.float32)
            sculpted = raw_height(xx, zz)
            calm = np.zeros_like(sculpted)
            for zone in zones:
                calm = np.maximum(calm, rectangle_mask(xx, zz, zone, 1.2))
            sculpted = sculpted * (1.0 - calm * 0.34) + (0.35 + 3.65 * smoothstep(-38.0, 38.0, (xx + zz) * 0.5)) * calm * 0.34
            cell_diagonal = math.hypot(PROFILES[key]["width"] / SEGMENTS, PROFILES[key]["height"] / SEGMENTS)
            for _kind, site, target in targets:
                distance = np.hypot(xx - site["x"], zz - site["z"])
                plateau_edge = site["radius"] + cell_diagonal
                flat = 1.0 - smoothstep(plateau_edge, plateau_edge + 1.15, distance)
                sculpted = sculpted * (1.0 - flat) + target * flat
            perimeter = smoothstep(0.88, 1.0, np.maximum(np.abs(xx) / 40.0, np.abs(zz) / 48.0))
            sculpted = sculpted * (1.0 - perimeter) + 0.18 * perimeter
            return sculpted

        return height

    if key == "dust-flats":
        truth = table["maskTruth"]
        wash = truth["dryWash"]
        road_segments = [(road["start"], road["end"]) for road in truth["roadCorridors"]]

        def height(x, z):
            xx = np.asarray(x, dtype=np.float32)
            zz = np.asarray(z, dtype=np.float32)
            radius = np.hypot(xx, zz)
            grain = np.sin(xx * 0.095 + zz * 0.071) * 0.055 + np.sin(xx * 0.19 - zz * 0.13) * 0.030
            edge_drift = smoothstep(55.0, 80.0, radius) * (0.34 + np.sin(np.arctan2(zz, xx) * 5.0) * 0.16)
            sculpted = 0.48 + grain + edge_drift

            dx, dz = xx - wash["x"], zz - wash["z"]
            cosine, sine = math.cos(wash["angle"]), math.sin(wash["angle"])
            along = dx * cosine + dz * sine
            across = -dx * sine + dz * cosine
            wash_mask = (1.0 - smoothstep(wash["length"] * 0.5, wash["length"] * 0.5 + 5.0, np.abs(along))) * (1.0 - smoothstep(wash["width"] * 0.5, wash["width"] * 0.5 + 3.0, np.abs(across)))
            sculpted -= wash_mask * 1.92

            orbit_radius = truth["orbitSpawn"]["radius"]
            angle = np.arctan2(zz, xx)
            # Wheel wear is never a compass-perfect target.  The sub-metre
            # wobble preserves the authored r=24 orbit while giving the road a
            # vehicle-cut, repaired-over-time silhouette.
            orbit_wobble = np.sin(angle * 3.0 + 0.4) * 0.62 + np.sin(angle * 7.0 - 0.8) * 0.28
            orbit_delta = radius - (orbit_radius + orbit_wobble)
            orbit_core = np.exp(-((orbit_delta / 3.8) ** 4))
            orbit_shoulders = np.exp(-(((np.abs(orbit_delta) - 5.1) / 1.20) ** 2))
            orbit_crown = np.exp(-((orbit_delta / 1.25) ** 2))
            orbit_ruts = np.maximum(
                np.exp(-(((orbit_delta - 1.65) / 0.48) ** 2)),
                np.exp(-(((orbit_delta + 1.65) / 0.48) ** 2)),
            )
            road_mask = orbit_core.copy()
            road_shoulders = np.zeros_like(xx)
            road_crowns = np.zeros_like(xx)
            road_ruts = np.zeros_like(xx)
            for start, end in road_segments:
                road_mask = np.maximum(road_mask, e2.segment_mask(xx, zz, start, end, 4.6))
                outer = e2.segment_mask(xx, zz, start, end, 7.2)
                inner = e2.segment_mask(xx, zz, start, end, 4.7)
                road_shoulders = np.maximum(road_shoulders, np.clip(outer - inner, 0.0, 1.0))
                road_crowns = np.maximum(road_crowns, e2.segment_mask(xx, zz, start, end, 1.45))
                vx, vz = end["x"] - start["x"], end["z"] - start["z"]
                length = max(math.hypot(vx, vz), 0.001)
                ox, oz = -vz / length * 1.55, vx / length * 1.55
                for sign in (-1.0, 1.0):
                    shifted_a = {"x": start["x"] + ox * sign, "z": start["z"] + oz * sign}
                    shifted_b = {"x": end["x"] + ox * sign, "z": end["z"] + oz * sign}
                    road_ruts = np.maximum(road_ruts, e2.segment_mask(xx, zz, shifted_a, shifted_b, 0.62))
            sculpted = sculpted * (1.0 - road_mask * 0.76) + 0.48 * road_mask * 0.76
            sculpted += orbit_shoulders * 0.72 + orbit_crown * 0.28 - orbit_ruts * 0.62
            sculpted += road_shoulders * 0.48 + road_crowns * 0.20 - road_ruts * 0.38

            calm = np.zeros_like(sculpted)
            for zone in zones:
                calm = np.maximum(calm, rectangle_mask(xx, zz, zone, 1.8))
            sculpted = sculpted * (1.0 - calm * 0.72) + 0.50 * calm * 0.72
            for seam in truth["tarSeams"]:
                sculpted -= gaussian(xx, zz, seam["x"], seam["z"], seam["radius"] * 0.85, seam["radius"] * 0.65) * 0.16
            perimeter = smoothstep(0.94, 1.0, np.maximum(np.abs(xx) / 80.0, np.abs(zz) / 80.0))
            sculpted = sculpted * (1.0 - perimeter) + 0.34 * perimeter
            return sculpted

        return height

    if key == "fairground":
        fixture = table["maskTruth"]["fixtureZones"][0]

        def raw_height(xx, zz):
            radius = np.hypot(xx, zz + 2.0)
            bowl = -0.76 * gaussian(xx, zz, 0.0, -1.0, 27.0, 25.0)
            rim = smoothstep(25.0, 43.5, radius) * (
                2.15
                + np.sin(np.arctan2(zz, xx) * 3.0 + 0.5) * 0.42
                + np.sin(np.arctan2(zz, xx) * 7.0 - 0.8) * 0.20
            )
            west_bank = 1.18 * gaussian(xx, zz, -38.5, 18.0, 7.5, 18.0)
            east_bank = 1.52 * gaussian(xx, zz, 39.0, 13.0, 6.8, 20.0)
            north_bank = 1.38 * gaussian(xx, zz, 8.0, 40.0, 22.0, 6.8)
            # Three broken ingress cuts preserve the authored west/east/north
            # spawn reading without granting any simulation authority.
            ingress = (
                1.05 * gaussian(xx, zz, -43.0, -2.0, 5.8, 8.5)
                + 1.15 * gaussian(xx, zz, 43.0, -3.0, 5.4, 8.0)
                + 1.10 * gaussian(xx, zz, 0.0, 43.0, 7.0, 5.0)
            )
            west_pavilion_terrace = rectangle_mask(
                xx, zz, {"minX": -32.0, "maxX": -10.0, "minZ": -1.0, "maxZ": 22.0}, 2.7
            )
            east_pavilion_terrace = rectangle_mask(
                xx, zz, {"minX": 10.0, "maxX": 32.0, "minZ": -1.0, "maxZ": 22.0}, 2.7
            )
            pavilion_shelves = west_pavilion_terrace * 1.30 + east_pavilion_terrace * 1.55
            midway_knuckles = (
                0.96 * gaussian(xx, zz, -16.0, -11.0, 8.2, 7.0)
                + 1.08 * gaussian(xx, zz, 15.0, -9.0, 8.0, 7.4)
            )
            worn_pockets = (
                0.58 * gaussian(xx, zz, -30.0, -15.0, 4.5, 5.5)
                + 0.52 * gaussian(xx, zz, 29.0, -17.0, 4.0, 5.0)
            )
            midway = e2.segment_mask(xx, zz, {"x": 0.0, "z": -38.0}, {"x": 0.0, "z": 8.0}, 7.0)
            midway_crown = e2.segment_mask(xx, zz, {"x": 0.0, "z": -38.0}, {"x": 0.0, "z": 8.0}, 3.2)
            wheel_radius = np.hypot(xx / 8.2, (zz - 8.0) / 6.2)
            wheel_foundation_berm = np.exp(-(((wheel_radius - 1.0) / 0.30) ** 2)) * 0.34
            guy_anchor_pads = (
                gaussian(xx, zz, -7.4, 5.2, 1.7, 1.5)
                + gaussian(xx, zz, 7.4, 5.2, 1.7, 1.5)
                + gaussian(xx, zz, -7.4, 11.0, 1.7, 1.5)
                + gaussian(xx, zz, 7.4, 11.0, 1.7, 1.5)
            ) * 0.32
            grain = np.sin(xx * 0.31 + zz * 0.19) * 0.060 + np.sin(xx * 0.12 - zz * 0.47) * 0.036
            return (
                0.42 + bowl + rim + west_bank + east_bank + north_bank - ingress
                + pavilion_shelves + midway_knuckles - worn_pockets
                - midway * 0.30 + midway_crown * 0.06
                + wheel_foundation_berm + guy_anchor_pads + grain
            )

        fixture_target = float(raw_height(np.asarray(0.0), np.asarray(8.0)))

        def height(x, z):
            xx = np.asarray(x, dtype=np.float32)
            zz = np.asarray(z, dtype=np.float32)
            sculpted = raw_height(xx, zz)
            calm = np.zeros_like(sculpted)
            for zone in zones:
                calm = np.maximum(calm, rectangle_mask(xx, zz, zone, 1.4))
            shelf = 0.18 + 0.20 * smoothstep(-20.0, 24.0, zz) + 0.12 * smoothstep(8.0, 35.0, np.abs(xx))
            sculpted = sculpted * (1.0 - calm * 0.14) + shelf * calm * 0.14

            cell_diagonal = math.hypot(PROFILES[key]["width"] / SEGMENTS, PROFILES[key]["height"] / SEGMENTS)
            guarded = {
                "minX": fixture["minX"] - cell_diagonal,
                "maxX": fixture["maxX"] + cell_diagonal,
                "minZ": fixture["minZ"] - cell_diagonal,
                "maxZ": fixture["maxZ"] + cell_diagonal,
            }
            shoulder = rectangle_mask(xx, zz, guarded, 1.15)
            sculpted = sculpted * (1.0 - shoulder) + fixture_target * shoulder
            exact = (
                (xx >= guarded["minX"])
                & (xx <= guarded["maxX"])
                & (zz >= guarded["minZ"])
                & (zz <= guarded["maxZ"])
            )
            sculpted = np.where(exact, fixture_target, sculpted)
            return sculpted

        return height

    if key == "glow-mesa":
        truth = table["maskTruth"]
        elevation = {zone["id"]: zone for zone in truth["elevationZones"]}
        base_zone = elevation["base-flat-h1"]
        top_zone = elevation["mesa-top-h5"]
        fixture_zones = truth["fixtureZones"]
        cell_diagonal = math.hypot(PROFILES[key]["width"] / SEGMENTS, PROFILES[key]["height"] / SEGMENTS)

        def raw_height(xx, zz):
            # Keep the authored mesa top exact while allowing the visible
            # scarp outside it to break into a natural caprock silhouette.
            west_edge = top_zone["minX"] - 2.8 + np.sin(zz * 0.31) * 1.6 + np.sin(zz * 0.73 + 0.4) * 0.7
            east_edge = top_zone["maxX"] + 2.4 + np.sin(zz * 0.27 + 1.1) * 1.4 - np.sin(zz * 0.61) * 0.6
            south_edge = top_zone["minZ"] - 3.2 + np.sin(xx * 0.25 - 0.6) * 1.5 + np.sin(xx * 0.67) * 0.6
            north_edge = top_zone["maxZ"] + 2.6 + np.sin(xx * 0.22 + 0.8) * 1.7 - np.sin(xx * 0.55) * 0.5
            mesa = (
                smoothstep(west_edge - 5.0, west_edge + 2.0, xx)
                * (1.0 - smoothstep(east_edge - 2.0, east_edge + 5.0, xx))
                * smoothstep(south_edge - 5.5, south_edge + 2.0, zz)
                * (1.0 - smoothstep(north_edge - 2.0, north_edge + 5.5, zz))
            )
            # Compress the transition into a legible caprock face.  The first
            # pass left a long, dark blur that read as a trench from the run
            # camera; this keeps the same h1/h5 contract while giving the
            # render mesh a clearer shoulder and top edge.
            mesa_profile = smoothstep(0.22, 0.72, mesa)
            shoulder = (
                gaussian(xx, zz, -34.0, 9.0, 7.0, 12.0) * 0.54
                + gaussian(xx, zz, 35.0, 25.0, 7.0, 13.0) * 0.62
                + gaussian(xx, zz, 10.0, 44.0, 18.0, 6.5) * 0.46
            ) * (1.0 - mesa_profile)
            grain = np.sin(xx * 0.28 + zz * 0.17) * 0.060 + np.sin(xx * 0.11 - zz * 0.43) * 0.034
            sculpted = 1.0 + mesa_profile * 4.0 + shoulder + grain * (1.0 - mesa_profile * 0.82)

            # The authored herd paths are the only gentle visual grades up the
            # scarp. They do not grant movement or elevation gameplay.
            for path in truth["herdPaths"]:
                path_mask = rectangle_mask(xx, zz, path, 1.5)
                if path["id"] == "west-scarp-herd-path":
                    ramp = 1.0 + 4.0 * smoothstep(path["minX"] + 2.0, path["maxX"] - 1.0, xx)
                elif path["id"] == "east-scarp-herd-path":
                    ramp = 5.0 - 4.0 * smoothstep(path["minX"] + 1.0, path["maxX"] - 2.0, xx)
                else:
                    ramp = 5.0 - 4.0 * smoothstep(path["minZ"] + 1.0, path["maxZ"] - 2.0, zz)
                sculpted = sculpted * (1.0 - path_mask * 0.94) + ramp * path_mask * 0.94
            return sculpted

        def height(x, z):
            xx = np.asarray(x, dtype=np.float32)
            zz = np.asarray(z, dtype=np.float32)
            sculpted = raw_height(xx, zz)

            # The gameplay-facing base and warehouse apron are truly flat;
            # their grit and decay story lives in the atlas, not geometry.
            # The warehouse is the north mesa origin in the authored E6
            # geography, so its approach stays at caprock height rather than
            # being cut into a contradictory lower shelf.
            base_guard = {
                "minX": base_zone["minX"] - cell_diagonal,
                "maxX": base_zone["maxX"] + cell_diagonal,
                "minZ": base_zone["minZ"] - cell_diagonal,
                "maxZ": base_zone["maxZ"] + cell_diagonal,
            }
            base_exact = (
                (xx >= base_guard["minX"]) & (xx <= base_guard["maxX"])
                & (zz >= base_guard["minZ"]) & (zz <= base_guard["maxZ"])
            )
            sculpted = np.where(base_exact, float(base_zone["height"]), sculpted)

            warehouse = next(zone for zone in truth["buildZones"] if zone["id"] == "warehouse-approach")
            warehouse_guard = {
                "minX": warehouse["minX"] - cell_diagonal,
                "maxX": warehouse["maxX"] + cell_diagonal,
                "minZ": warehouse["minZ"] - cell_diagonal,
                "maxZ": warehouse["maxZ"] + cell_diagonal,
            }
            warehouse_shoulder = rectangle_mask(xx, zz, warehouse_guard, 3.0)
            sculpted = sculpted * (1.0 - warehouse_shoulder) + float(top_zone["height"]) * warehouse_shoulder
            warehouse_exact = (
                (xx >= warehouse_guard["minX"]) & (xx <= warehouse_guard["maxX"])
                & (zz >= warehouse_guard["minZ"]) & (zz <= warehouse_guard["maxZ"])
            )
            sculpted = np.where(warehouse_exact, float(top_zone["height"]), sculpted)

            top_exact = (
                (xx >= top_zone["minX"]) & (xx <= top_zone["maxX"])
                & (zz >= top_zone["minZ"]) & (zz < top_zone["maxZ"])
            )
            sculpted = np.where(top_exact, float(top_zone["height"]), sculpted)

            # The two lore fixtures need an interpolation guard beyond their
            # authored rectangles so the exported triangles stay flat inside.
            for fixture in fixture_zones:
                guarded = {
                    "minX": fixture["minX"] - cell_diagonal,
                    "maxX": fixture["maxX"] + cell_diagonal,
                    "minZ": fixture["minZ"] - cell_diagonal,
                    "maxZ": fixture["maxZ"] + cell_diagonal,
                }
                exact = (
                    (xx >= guarded["minX"]) & (xx <= guarded["maxX"])
                    & (zz >= guarded["minZ"]) & (zz <= guarded["maxZ"])
                )
                sculpted = np.where(exact, float(top_zone["height"]), sculpted)

            perimeter = smoothstep(0.94, 1.0, np.maximum(np.abs(xx) / 64.0, np.abs(zz) / 64.0))
            return sculpted * (1.0 - perimeter) + 0.58 * perimeter

        return height

    if key == "echo-canyon":
        truth = table["maskTruth"]
        bands = truth["echoCanyonBands"]
        cell_diagonal = math.hypot(PROFILES[key]["width"] / SEGMENTS, PROFILES[key]["height"] / SEGMENTS)

        def height(x, z):
            xx = np.asarray(x, dtype=np.float32)
            zz = np.asarray(z, dtype=np.float32)

            # The authored h0/h5 strips are load-bearing mask truth. Broad
            # broken shoulders live outside them so the exact shelves read as
            # canyon walls instead of three disconnected slabs.
            west_wall = smoothstep(-36.0, -31.5, -xx)
            east_wall = smoothstep(31.5, 36.0, xx)
            wall = np.maximum(west_wall, east_wall)
            shoulder = np.clip(
                0.92
                + np.sin(zz * 0.19 + xx * 0.11) * 0.07
                + np.sin(zz * 0.47 - xx * 0.08) * 0.035,
                0.76,
                1.0,
            )
            sculpted = wall * 5.0 * shoulder

            # Two end-mouth fans and a shallow central broadcast scar keep the
            # exact floor flat while giving the long north/south axis a story.
            mouth_weather = smoothstep(43.0, 62.0, np.abs(zz))
            sculpted += wall * mouth_weather * (0.24 + np.sin(xx * 0.24 + zz * 0.31) * 0.08)

            for band in bands:
                exact = (
                    (xx >= band["minX"]) & (xx <= band["maxX"])
                    & (zz >= band["minZ"]) & (zz <= band["maxZ"])
                )
                sculpted = np.where(exact, float(band["height"]), sculpted)

            for zone in truth["buildZones"]:
                target = 0.0 if zone["id"] == "canyon-floor-yard" else 5.0
                guarded = {
                    "minX": zone["minX"] - cell_diagonal,
                    "maxX": zone["maxX"] + cell_diagonal,
                    "minZ": zone["minZ"] - cell_diagonal,
                    "maxZ": zone["maxZ"] + cell_diagonal,
                }
                exact = (
                    (xx >= guarded["minX"]) & (xx <= guarded["maxX"])
                    & (zz >= guarded["minZ"]) & (zz <= guarded["maxZ"])
                )
                sculpted = np.where(exact, target, sculpted)

            # Begin the render-only mouth descent immediately outside the
            # authored z=+/-54 bands.  A four-metre edge collapse produced an
            # almost vertical, unlit back face; this ten-metre shoulder reads
            # as ground receding toward the panorama apron.  The exact mask
            # rectangle still wins through its last authored coordinate.
            mouth_fade = smoothstep(54.0, 64.0, np.abs(zz))
            return sculpted * (1.0 - mouth_fade) + 0.10 * mouth_fade

        return height

    if key == "relay-valley":
        truth = table["maskTruth"]
        ridges = [zone for zone in truth["ridgeBands"] if zone["id"] != "valley-floor-h0"]
        cell_diagonal = math.hypot(PROFILES[key]["width"] / SEGMENTS, PROFILES[key]["height"] / SEGMENTS)

        def raw_height(xx, zz):
            ridge_soft = np.zeros_like(xx)
            for index, ridge in enumerate(ridges):
                # The published h5 rectangle stays exact, while a wider,
                # irregular shoulder outside it hides the slab edge from the
                # player camera. This shoulder is visual-only and never adds
                # placement or elevation authority.
                shoulder_zone = {
                    "minX": ridge["minX"] - 5.0,
                    "maxX": ridge["maxX"] + 5.0,
                    "minZ": ridge["minZ"] - 5.0,
                    "maxZ": ridge["maxZ"] + 5.0,
                }
                body = rectangle_mask(xx, zz, shoulder_zone, 3.2)
                breakup = np.clip(
                    0.94
                    + np.sin(xx * (0.19 + index * 0.03) + zz * 0.23) * 0.08
                    + np.sin(xx * 0.47 - zz * (0.13 + index * 0.02)) * 0.045,
                    0.78,
                    1.0,
                )
                ridge_soft = np.maximum(ridge_soft, body * breakup)
            valley_grain = np.sin(xx * 0.25 + zz * 0.16) * 0.050 + np.sin(xx * 0.10 - zz * 0.41) * 0.030
            north_broken_ground = smoothstep(18.0, 28.0, zz) * (0.22 + np.sin(xx * 0.31) * 0.08)
            sculpted = valley_grain + north_broken_ground + ridge_soft * 5.0

            # Named dead zones are shallow visual basins with quiet surfaces.
            # Their gameplay meaning remains entirely in the published masks.
            for index, pocket in enumerate(truth["fogPockets"]):
                pocket_mask = rectangle_mask(xx, zz, pocket, 2.8)
                depth = (0.72 if pocket["id"] == "ridge-dead-gap" else 0.34 + index * 0.04)
                sculpted -= pocket_mask * depth

            # Keep the two authored ridge bands visibly h5 and every tower pad
            # buildable-flat on the exported triangle surface.
            for ridge in ridges:
                exact = (
                    (xx >= ridge["minX"]) & (xx <= ridge["maxX"])
                    & (zz >= ridge["minZ"]) & (zz <= ridge["maxZ"])
                )
                sculpted = np.where(exact, float(ridge["height"]), sculpted)
            for zone in truth["buildZones"]:
                guarded = {
                    "minX": zone["minX"] - cell_diagonal,
                    "maxX": zone["maxX"] + cell_diagonal,
                    "minZ": zone["minZ"] - cell_diagonal,
                    "maxZ": zone["maxZ"] + cell_diagonal,
                }
                exact = (
                    (xx >= guarded["minX"]) & (xx <= guarded["maxX"])
                    & (zz >= guarded["minZ"]) & (zz <= guarded["maxZ"])
                )
                sculpted = np.where(exact, 5.0, sculpted)

            perimeter = smoothstep(0.94, 1.0, np.maximum(np.abs(xx) / 64.0, np.abs(zz) / 64.0))
            return sculpted * (1.0 - perimeter) + 0.08 * perimeter

        return raw_height

    if key == "mare-claim":
        truth = table["maskTruth"]
        rim_bands = truth["rimBands"]
        mare = truth["mareFlat"]
        mouth = truth["lavaTubeMouth"]
        cell_diagonal = math.hypot(PROFILES[key]["width"] / SEGMENTS, PROFILES[key]["height"] / SEGMENTS)

        def height(x, z):
            xx = np.asarray(x, dtype=np.float32)
            zz = np.asarray(z, dtype=np.float32)

            # The interior mare is authored h0. Its visual emptiness is carried
            # by stipple and work scars, not decorative terrain noise.
            sculpted = np.zeros_like(xx)

            # A broken shoulder makes the exact rectangular h6 mask read as a
            # crater rim rather than four stacked walls. The authored bands
            # themselves are written back at exactly six metres below.
            rim_shoulder = np.zeros_like(xx)
            for index, band in enumerate(rim_bands):
                shoulder = {
                    "minX": band["minX"] - 5.5,
                    "maxX": band["maxX"] + 5.5,
                    "minZ": band["minZ"] - 5.5,
                    "maxZ": band["maxZ"] + 5.5,
                }
                breakup = np.clip(
                    0.90
                    + np.sin(xx * (0.17 + index * 0.011) + zz * 0.21) * 0.08
                    + np.sin(xx * 0.43 - zz * (0.11 + index * 0.013)) * 0.045,
                    0.72,
                    1.0,
                )
                rim_shoulder = np.maximum(rim_shoulder, rectangle_mask(xx, zz, shoulder, 3.2) * breakup)
            sculpted = np.maximum(sculpted, rim_shoulder * 5.35)

            # The named lava-tube mouth is the single interruption in the h0
            # mare: a shallow render-only collapse and chipped lip, entirely
            # inside its published rectangle and outside every build zone.
            cx = (mouth["minX"] + mouth["maxX"]) * 0.5
            cz = (mouth["minZ"] + mouth["maxZ"]) * 0.5
            rx = (mouth["maxX"] - mouth["minX"]) * 0.5
            rz = (mouth["maxZ"] - mouth["minZ"]) * 0.5
            local_x = (xx - cx) / (rx * 0.68)
            local_z = (zz - cz) / rz
            radius = np.sqrt(local_x ** 2 + local_z ** 2)
            inside_mouth = radius <= 1.0
            # A long throat with a raised back crescent reads as a tunnel
            # entrance; a symmetric bowl was indistinguishable from an impact.
            throat = -3.4 * (1.0 - smoothstep(0.10, 0.84, radius))
            throat *= np.clip(0.90 + local_z * 0.16, 0.76, 1.0)
            lip = np.exp(-(((radius - 0.88) / 0.12) ** 2)) * (
                0.82 + 0.18 * np.sin(xx * 1.19 + zz * 0.73)
            )
            lip *= np.clip(0.24 + smoothstep(-0.18, 0.58, local_z) * 0.92, 0.20, 1.12)
            sculpted = np.where(inside_mouth, throat + lip, sculpted)

            # Exact mask heights win after all composition shaping.
            mare_exact = (
                (xx >= mare["minX"]) & (xx <= mare["maxX"])
                & (zz >= mare["minZ"]) & (zz <= mare["maxZ"])
                & ~inside_mouth
            )
            sculpted = np.where(mare_exact, float(mare["height"]), sculpted)
            for band in rim_bands:
                exact = (
                    (xx >= band["minX"]) & (xx <= band["maxX"])
                    & (zz >= band["minZ"]) & (zz <= band["maxZ"])
                )
                sculpted = np.where(exact, float(band["height"]), sculpted)

            # One-cell interpolation guards keep every published build zone
            # flat on the exported triangle surface, not merely at vertices.
            for zone in truth["buildZones"]:
                target = 6.0 if zone["id"].startswith("rim-premium") else 0.0
                guarded = {
                    "minX": zone["minX"] - cell_diagonal,
                    "maxX": zone["maxX"] + cell_diagonal,
                    "minZ": zone["minZ"] - cell_diagonal,
                    "maxZ": zone["maxZ"] + cell_diagonal,
                }
                exact = (
                    (xx >= guarded["minX"]) & (xx <= guarded["maxX"])
                    & (zz >= guarded["minZ"]) & (zz <= guarded["maxZ"])
                )
                sculpted = np.where(exact, target, sculpted)

            perimeter = smoothstep(0.93, 1.0, np.maximum(np.abs(xx) / 64.0, np.abs(zz) / 64.0))
            return sculpted * (1.0 - perimeter) + 0.12 * perimeter

        return height

    if key == "ember-shore":
        truth = table["maskTruth"]
        bands = truth["lavaVeinBands"]
        cell_diagonal = math.hypot(PROFILES[key]["width"] / SEGMENTS, PROFILES[key]["height"] / SEGMENTS)
        build_targets = {
            "last-warm-vent-site": 0.18,
            "cooled-titan-machine-mount": 0.82,
        }

        def raw_height(xx, zz):
            # Low cooled basalt keeps the two preserve sites readable. The
            # three authored hazard bands, not decorative peaks, organize the
            # traversal silhouette.
            sculpted = (
                0.34
                + np.sin(xx * 0.083 + zz * 0.061) * 0.105
                + np.sin(xx * 0.211 - zz * 0.127) * 0.052
                + gaussian(xx, zz, -31.0, 36.0, 19.0, 15.0) * 1.72
                + gaussian(xx, zz, 31.0, -38.0, 22.0, 13.0) * 1.16
                + gaussian(xx, zz, 50.0, 44.0, 10.0, 18.0) * 0.90
            )

            band_depths = (2.18, 1.72, 1.98)
            for index, band in enumerate(bands):
                shoulder = {
                    "minX": band["minX"] - 4.8,
                    "maxX": band["maxX"] + 4.8,
                    "minZ": band["minZ"] - 3.6,
                    "maxZ": band["maxZ"] + 3.6,
                }
                shoulder_mask = rectangle_mask(xx, zz, shoulder, 2.8)
                core = rectangle_mask(xx, zz, band, 1.35)
                breakline = np.clip(
                    0.78
                    + np.sin(zz * (0.22 + index * 0.025) + xx * 0.17) * 0.16
                    + np.sin(zz * 0.51 - xx * (0.09 + index * 0.017)) * 0.08,
                    0.34,
                    0.98,
                )
                cooled_floor = -band_depths[index] + (1.0 - breakline) * 0.34
                sculpted = sculpted * (1.0 - shoulder_mask * 0.42) + np.minimum(sculpted, cooled_floor + 1.08) * shoulder_mask * 0.42
                cooled_surface = np.minimum(sculpted, cooled_floor)
                sculpted = sculpted * (1.0 - core) + cooled_surface * core

                # Broken crust lips turn each rectangular authored band into a
                # natural cooling rift while remaining inside render authority.
                left_lip = np.exp(-(((xx - band["minX"]) / 1.10) ** 2))
                right_lip = np.exp(-(((xx - band["maxX"]) / 1.10) ** 2))
                z_window = rectangle_mask(xx, zz, {
                    "minX": band["minX"] - 2.0,
                    "maxX": band["maxX"] + 2.0,
                    "minZ": band["minZ"],
                    "maxZ": band["maxZ"],
                }, 1.4)
                sculpted += (left_lip + right_lip) * z_window * (0.72 + breakline * 0.52)

            # One broad cooled shelf supports the titan mount without making
            # the exact build rectangle a floating platform.
            titan = next(zone for zone in truth["buildZones"] if zone["id"] == "cooled-titan-machine-mount")
            titan_shoulder = {
                "minX": titan["minX"] - 5.0,
                "maxX": titan["maxX"] + 5.0,
                "minZ": titan["minZ"] - 5.0,
                "maxZ": titan["maxZ"] + 5.0,
            }
            titan_shelf = rectangle_mask(xx, zz, titan_shoulder, 3.4)
            sculpted = np.where(titan_shelf > 0.001, np.maximum(sculpted, titan_shelf * 0.72), sculpted)
            return sculpted

        def height(x, z):
            xx = np.asarray(x, dtype=np.float32)
            zz = np.asarray(z, dtype=np.float32)
            sculpted = raw_height(xx, zz)
            # Triangle-safe guards protect both the vent fixture and the large
            # cooled-titan machine mount across the exported surface.
            for zone in truth["buildZones"]:
                guarded = {
                    "minX": zone["minX"] - cell_diagonal,
                    "maxX": zone["maxX"] + cell_diagonal,
                    "minZ": zone["minZ"] - cell_diagonal,
                    "maxZ": zone["maxZ"] + cell_diagonal,
                }
                exact = (
                    (xx >= guarded["minX"]) & (xx <= guarded["maxX"])
                    & (zz >= guarded["minZ"]) & (zz <= guarded["maxZ"])
                )
                sculpted = np.where(exact, build_targets[zone["id"]], sculpted)
            perimeter = smoothstep(0.94, 1.0, np.maximum(np.abs(xx) / 64.0, np.abs(zz) / 64.0))
            return sculpted * (1.0 - perimeter) + 0.16 * perimeter

        return height

    raise ValueError(f"no height profile for {key}")


def make_atlas(key, profile, factory, table):
    source = claim.image_pixels(profile["sourcePlate"])
    if key == "ember-shore":
        # The E10 worlds plate contains three biome families; only its left
        # ember-world third may govern this map's painted substrate.
        source = source[:, : source.shape[1] // 3]
    kit = claim.image_pixels(profile["kit"])
    bank_a = claim.image_pixels(claim.BANK_A)
    bank_c = claim.image_pixels(claim.BANK_C)
    river = claim.image_pixels(claim.RIVER)
    rail_plate = claim.image_pixels(RAIL_PLATE)
    axis = np.linspace(0.0, 1.0, ATLAS_SIZE, dtype=np.float32)
    u, v = np.meshgrid(axis, axis)
    x = (u - 0.5) * profile["width"]
    z = (v - 0.5) * profile["height"]
    ax, az = np.abs(x), np.abs(z)

    repeats = {"canyon-works": 3.2, "moth-season": 2.6, "blackout-ridge": 3.4, "dust-flats": 5.2, "fairground": 3.0, "glow-mesa": 3.6, "relay-valley": 3.8, "echo-canyon": 4.1, "mare-claim": 4.2, "ember-shore": 3.4}[key]
    plate = claim.tiled_sample(source, u, v, repeats, 0.17, 0.43)
    paper = claim.tiled_sample(kit, u, v, 3.8, 0.51, 0.09)
    dirt = claim.tiled_sample(bank_a, u, v, 7.3, 0.28, 0.62)
    rock = claim.tiled_sample(bank_c, u, v, 8.8, 0.08, 0.37)
    macro = (np.sin(x * 0.091 + z * 0.067) * 0.5 + 0.5)[..., None]
    land = dirt * (0.25 + macro * 0.08) + rock * (0.42 - macro * 0.06) + plate * 0.23 + paper * 0.10

    if key == "canyon-works":
        land *= np.array((0.53, 0.43, 0.34), dtype=np.float32)
        water_art = claim.tiled_sample(river, u, v, 3.1, 0.31, 0.18) * np.array((0.16, 0.24, 0.27), dtype=np.float32)
        water_mask = 1.0 - smoothstep(DEEP_HALF_WIDTH, SHALLOWS_HALF_WIDTH, az)
        atlas = land * (1.0 - water_mask[..., None]) + water_art * water_mask[..., None]
        atlas *= 1.0 - np.exp(-((az - DEEP_HALF_WIDTH) / 0.52) ** 2)[..., None] * 0.28
        upper = smoothstep(15.0, 50.0, z)
        atlas = atlas * (1.0 - upper[..., None] * 0.24) + rock * np.array((0.31, 0.29, 0.28)) * upper[..., None] * 0.24
        cuts = np.maximum.reduce([np.exp(-((z - cut) / 0.82) ** 2) for cut in (7.0, 18.0, 28.0, 49.0)])
        atlas *= 1.0 - cuts[..., None] * 0.24
        for site in table["maskTruth"]["pylonSites"]:
            ring = np.exp(-((np.hypot(x - site["x"], z - site["z"]) - site["radius"]) / 0.35) ** 2)
            atlas *= 1.0 - ring[..., None] * 0.18
        rail_mask = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
        for rail in table["maskTruth"]["rails"]:
            for a, b in zip(rail["points"], rail["points"][1:]):
                rail_mask = np.maximum(rail_mask, e2.segment_mask(x, z, a, b, 0.95))
        rail_ink = claim.tiled_sample(rail_plate, u, v, 7.0, 0.24, 0.63) * np.array((0.25, 0.20, 0.17), dtype=np.float32)
        atlas = atlas * (1.0 - rail_mask[..., None] * 0.30) + rail_ink * rail_mask[..., None] * 0.30
    elif key == "moth-season":
        atlas = land * np.array((0.39, 0.39, 0.46), dtype=np.float32)
        dark_corridor = gaussian(x, z, 0.0, 0.0, 6.5, 35.0)
        atlas *= 1.0 - dark_corridor[..., None] * 0.24
        yard_glow = np.clip(gaussian(x, z, -20, 0, 13, 24) + gaussian(x, z, 20, 0, 13, 24), 0.0, 1.0)
        warm = paper * np.array((0.55, 0.38, 0.18), dtype=np.float32)
        atlas = atlas * (1.0 - yard_glow[..., None] * 0.18) + warm * yard_glow[..., None] * 0.18
        migration = np.sin(z * 0.66 + np.sin(x * 0.31)) * 0.5 + 0.5
        atlas *= 1.0 - (migration * dark_corridor)[..., None] * 0.12
        wing_scars = np.zeros_like(x)
        for index, mark_z in enumerate(np.linspace(-29.0, 29.0, 9)):
            mark_x = math.sin(index * 1.7) * 2.2
            left = gaussian(x, z, mark_x - 0.9, mark_z, 1.1, 0.42)
            right = gaussian(x, z, mark_x + 0.9, mark_z, 1.1, 0.42)
            wing_scars = np.maximum(wing_scars, np.maximum(left, right))
        scar_tone = paper * np.array((0.48, 0.42, 0.34), dtype=np.float32)
        atlas = atlas * (1.0 - wing_scars[..., None] * 0.52) + scar_tone * wing_scars[..., None] * 0.52
    elif key == "blackout-ridge":
        atlas = land * np.array((0.46, 0.47, 0.58), dtype=np.float32)
        climb_shadow = smoothstep(-32.0, 38.0, (x + z) * 0.5)
        atlas *= 1.0 - climb_shadow[..., None] * 0.12
        trunk = np.zeros_like(x)
        trunk_shoulder = np.zeros_like(x)
        trunk_points = [(-40.0, -40.0)] + [(site["x"], site["z"]) for site in table["maskTruth"]["pylonSites"]] + [(24.0, 30.0)]
        for start, end in zip(trunk_points, trunk_points[1:]):
            a, b = {"x": start[0], "z": start[1]}, {"x": end[0], "z": end[1]}
            trunk = np.maximum(trunk, e2.segment_mask(x, z, a, b, 0.48))
            trunk_shoulder = np.maximum(trunk_shoulder, e2.segment_mask(x, z, a, b, 2.35))
        shoulder_tone = paper * np.array((0.34, 0.39, 0.46), dtype=np.float32)
        atlas = atlas * (1.0 - trunk_shoulder[..., None] * 0.24) + shoulder_tone * trunk_shoulder[..., None] * 0.24
        trunk_ink = paper * np.array((0.20, 0.25, 0.31), dtype=np.float32)
        atlas = atlas * (1.0 - trunk[..., None] * 0.46) + trunk_ink * trunk[..., None] * 0.46
        for kind, site in load_bearing_sites(table):
            distance = np.hypot(x - site["x"], z - site["z"])
            ring = np.exp(-(((distance - site["radius"]) / 0.32) ** 2))
            tone = np.array((0.28, 0.20, 0.12) if kind == "capacitor" else (0.10, 0.16, 0.19), dtype=np.float32)
            atlas = atlas * (1.0 - ring[..., None] * 0.42) + tone * ring[..., None] * 0.42
        cold_scar = gaussian(x, z, -36.0, -42.0, 8.0, 5.0)
        atlas = atlas * (1.0 - cold_scar[..., None] * 0.22) + np.array((0.08, 0.20, 0.20))[None, None, :] * cold_scar[..., None] * 0.22
    elif key == "dust-flats":
        truth = table["maskTruth"]
        atlas = land * np.array((0.76, 0.57, 0.35), dtype=np.float32)
        radius = np.hypot(x, z)
        angle = np.arctan2(z, x)
        orbit_wobble = np.sin(angle * 3.0 + 0.4) * 0.62 + np.sin(angle * 7.0 - 0.8) * 0.28
        orbit_delta = radius - (truth["orbitSpawn"]["radius"] + orbit_wobble)
        orbit = np.exp(-((orbit_delta / 4.0) ** 4))
        roads = orbit.copy()
        for road in truth["roadCorridors"]:
            roads = np.maximum(roads, e2.segment_mask(x, z, road["start"], road["end"], 4.8))
        packed = atlas * 0.70 + paper * np.array((0.22, 0.17, 0.10), dtype=np.float32)
        atlas = atlas * (1.0 - roads[..., None] * 0.48) + packed * roads[..., None] * 0.48

        orbit_shoulders = np.exp(-(((np.abs(orbit_delta) - 5.1) / 1.15) ** 2))
        shoulder_tone = paper * np.array((0.70, 0.52, 0.31), dtype=np.float32)
        atlas = atlas * (1.0 - orbit_shoulders[..., None] * 0.30) + shoulder_tone * orbit_shoulders[..., None] * 0.30

        orbit_ruts = np.maximum(
            np.exp(-(((orbit_delta + 1.55) / 0.34) ** 2)),
            np.exp(-(((orbit_delta - 1.55) / 0.34) ** 2)),
        )
        road_scars = orbit_ruts
        for road in truth["roadCorridors"]:
            vx = road["end"]["x"] - road["start"]["x"]
            vz = road["end"]["z"] - road["start"]["z"]
            length = max(math.hypot(vx, vz), 0.001)
            ox, oz = -vz / length * 1.55, vx / length * 1.55
            for sign in (-1.0, 1.0):
                shifted_a = {"x": road["start"]["x"] + ox * sign, "z": road["start"]["z"] + oz * sign}
                shifted_b = {"x": road["end"]["x"] + ox * sign, "z": road["end"]["z"] + oz * sign}
                road_scars = np.maximum(road_scars, e2.segment_mask(x, z, shifted_a, shifted_b, 0.66))
        atlas *= 1.0 - road_scars[..., None] * 0.26

        for seam in truth["tarSeams"]:
            stain = gaussian(x, z, seam["x"], seam["z"], seam["radius"] * 1.10, seam["radius"] * 0.82)
            tar = plate * np.array((0.10, 0.075, 0.045), dtype=np.float32)
            atlas = atlas * (1.0 - stain[..., None] * 0.42) + tar * stain[..., None] * 0.42

        wash = truth["dryWash"]
        dx, dz = x - wash["x"], z - wash["z"]
        cosine, sine = math.cos(wash["angle"]), math.sin(wash["angle"])
        along = dx * cosine + dz * sine
        across = -dx * sine + dz * cosine
        wash_mask = (1.0 - smoothstep(wash["length"] * 0.5, wash["length"] * 0.5 + 4.0, np.abs(along))) * (1.0 - smoothstep(wash["width"] * 0.5, wash["width"] * 0.5 + 2.4, np.abs(across)))
        wash_ink = rock * np.array((0.40, 0.31, 0.22), dtype=np.float32)
        atlas = atlas * (1.0 - wash_mask[..., None] * 0.48) + wash_ink * wash_mask[..., None] * 0.48
        tar_spray = (np.sin(x * 0.42 + z * 0.31) * np.sin(x * 0.17 - z * 0.53) > 0.78).astype(np.float32)
        atlas *= 1.0 - tar_spray[..., None] * 0.065
    elif key == "glow-mesa":
        truth = table["maskTruth"]
        atlas = land * np.array((0.82, 0.70, 0.63), dtype=np.float32)
        top_zone = next(zone for zone in truth["elevationZones"] if zone["id"] == "mesa-top-h5")
        mesa_top = rectangle_mask(x, z, top_zone, 2.2)
        west_edge = top_zone["minX"] - 2.8 + np.sin(z * 0.31) * 1.6 + np.sin(z * 0.73 + 0.4) * 0.7
        east_edge = top_zone["maxX"] + 2.4 + np.sin(z * 0.27 + 1.1) * 1.4 - np.sin(z * 0.61) * 0.6
        south_edge = top_zone["minZ"] - 3.2 + np.sin(x * 0.25 - 0.6) * 1.5 + np.sin(x * 0.67) * 0.6
        north_edge = top_zone["maxZ"] + 2.6 + np.sin(x * 0.22 + 0.8) * 1.7 - np.sin(x * 0.55) * 0.5
        def array_smoothstep(edge0, edge1, value):
            amount = np.clip((value - edge0) / np.maximum(edge1 - edge0, 0.0001), 0.0, 1.0)
            return amount * amount * (3.0 - 2.0 * amount)
        natural_cap = (
            array_smoothstep(west_edge - 5.0, west_edge + 2.0, x)
            * (1.0 - array_smoothstep(east_edge - 2.0, east_edge + 5.0, x))
            * array_smoothstep(south_edge - 5.5, south_edge + 2.0, z)
            * (1.0 - array_smoothstep(north_edge - 2.0, north_edge + 5.5, z))
        )
        cap_mask = np.maximum(mesa_top, natural_cap)
        caprock = rock * np.array((0.72, 0.56, 0.53), dtype=np.float32)
        atlas = atlas * (1.0 - cap_mask[..., None] * 0.50) + caprock * cap_mask[..., None] * 0.50

        # Broken dark caprock just outside the exact top gives the first true
        # mesa a readable scarp without painting one clean rectangular wall.
        scarp = np.clip(4.2 * natural_cap * (1.0 - natural_cap), 0.0, 1.0)
        scarp_break = np.clip(0.72 + np.sin(x * 0.37 + z * 0.21) * 0.18 + np.sin(x * 0.13 - z * 0.53) * 0.11, 0.30, 0.98)
        scarp_ink = rock * np.array((0.48, 0.36, 0.27), dtype=np.float32)
        atlas = atlas * (1.0 - (scarp * scarp_break)[..., None] * 0.48) + scarp_ink * (scarp * scarp_break)[..., None] * 0.48
        scarp_hatch = np.clip(
            (np.sin(x * 1.18 + z * 0.34) * 0.5 + 0.5)
            * (np.sin(z * 0.76 - x * 0.19) * 0.5 + 0.5)
            * scarp,
            0.0,
            1.0,
        )
        atlas *= 1.0 - scarp_hatch[..., None] * 0.12
        strata = smoothstep(
            0.58,
            0.88,
            np.sin(natural_cap * math.tau * 5.2 + x * 0.10 - z * 0.06) * 0.5 + 0.5,
        ) * scarp
        strata_tone = rock * np.array((0.70, 0.52, 0.38), dtype=np.float32)
        atlas = atlas * (1.0 - strata[..., None] * 0.24) + strata_tone * strata[..., None] * 0.24

        # Chrome-pastel packed approaches are repaired homestead work, not a
        # pristine resort path. Two narrow ruts and hatch-step wear keep them
        # inside the Grit Law while preserving the convalescent-era brightness.
        for path in truth["herdPaths"]:
            path_mask = rectangle_mask(x, z, path, 1.5)
            enamel = paper * np.array((0.58, 0.69, 0.66), dtype=np.float32) + dirt * np.array((0.18, 0.12, 0.10), dtype=np.float32)
            wear = np.clip(0.68 + np.sin(x * 0.42 - z * 0.17) * 0.18 + np.sin(z * 0.31) * 0.09, 0.32, 0.94)
            weight = path_mask * wear
            atlas = atlas * (1.0 - weight[..., None] * 0.36) + enamel * weight[..., None] * 0.36

        # Broad, worn circulation lines connect the kitchen/base to the legal
        # herd-path mouths and the warehouse. They are paint-only visual
        # hierarchy and confer no movement or placement authority.
        circulation = np.maximum.reduce(
            (
                e2.segment_mask(x, z, {"x": 0.0, "z": -32.0}, {"x": -42.0, "z": 14.0}, 2.15),
                e2.segment_mask(x, z, {"x": 0.0, "z": -32.0}, {"x": 42.0, "z": 14.0}, 2.15),
                e2.segment_mask(x, z, {"x": -10.0, "z": 18.0}, {"x": -37.0, "z": 42.0}, 2.05),
            )
        )
        circulation *= np.clip(0.70 + np.sin(x * 0.31 - z * 0.17) * 0.18, 0.34, 0.92)
        trail_tone = paper * np.array((0.48, 0.59, 0.56), dtype=np.float32) + dirt * np.array((0.16, 0.10, 0.08), dtype=np.float32)
        atlas = atlas * (1.0 - circulation[..., None] * 0.16) + trail_tone * circulation[..., None] * 0.16

        base_flat = next(zone for zone in truth["buildZones"] if zone["id"] == "base-flat")
        base_mask = rectangle_mask(x, z, base_flat, 2.5)
        repaired_base = paper * np.array((0.60, 0.72, 0.67), dtype=np.float32) + dirt * np.array((0.20, 0.13, 0.11), dtype=np.float32)
        base_breakup = np.clip(0.68 + np.sin(x * 0.25 + z * 0.19) * 0.16 + np.sin(x * 0.57 - z * 0.11) * 0.10, 0.30, 0.94)
        repaired_weight = base_mask * base_breakup
        atlas = atlas * (1.0 - repaired_weight[..., None] * 0.22) + repaired_base * repaired_weight[..., None] * 0.22
        wagon_scars = np.maximum(
            e2.segment_mask(x, z, {"x": -18.0, "z": -51.0}, {"x": -4.0, "z": -12.0}, 1.35),
            e2.segment_mask(x, z, {"x": 18.0, "z": -49.0}, {"x": 5.0, "z": -12.0}, 1.35),
        )
        atlas *= 1.0 - (wagon_scars * base_mask)[..., None] * 0.035

        # Decay is fading glow through engraved hatch steps—never corrosion.
        for index, field in enumerate(truth["decayFields"]):
            center_x = (field["minX"] + field["maxX"]) * 0.5
            center_z = (field["minZ"] + field["maxZ"]) * 0.5
            field_mask = gaussian(
                x,
                z,
                center_x + math.sin(index * 1.7) * 1.2,
                center_z - math.cos(index * 1.3) * 0.8,
                (field["maxX"] - field["minX"]) * 0.43,
                (field["maxZ"] - field["minZ"]) * 0.40,
            )
            field_mask *= rectangle_mask(x, z, field, 2.4)
            field_mask *= np.clip(0.74 + np.sin(x * 0.43 + z * 0.27 + index) * 0.16 + np.sin(x * 0.17 - z * 0.61) * 0.10, 0.22, 0.98)
            phase = (x * (0.72 + index * 0.08) + z * (0.36 - index * 0.05))
            hatch = (np.sin(phase) * 0.5 + 0.5) * (np.sin(z * 1.05 - index) * 0.5 + 0.5)
            fade = np.clip(0.24 + hatch * 0.56 + smoothstep(field["minX"], field["maxX"], x) * 0.18, 0.0, 1.0)
            teal = paper * np.array((0.19, 0.57, 0.55), dtype=np.float32)
            weight = field_mask * fade
            decay_soot = rock * np.array((0.19, 0.15, 0.12), dtype=np.float32)
            soot_weight = field_mask * np.clip(0.58 + np.sin(x * 0.29 - z * 0.41 + index) * 0.24, 0.18, 0.92)
            atlas = atlas * (1.0 - soot_weight[..., None] * 0.34) + decay_soot * soot_weight[..., None] * 0.34
            atlas = atlas * (1.0 - weight[..., None] * 0.46) + teal * weight[..., None] * 0.46
            atlas *= 1.0 - (field_mask * (1.0 - fade))[..., None] * 0.18

        # Six soft-teal starstone scars are brightest after dark. Their
        # geometry remains ordinary walkable mesa top; only the atlas glows.
        anchors = truth["harvestAnchors"]
        ring_vein = np.zeros_like(x)
        for start, end in zip(anchors, anchors[1:] + anchors[:1]):
            ring_vein = np.maximum(ring_vein, e2.segment_mask(x, z, start, end, 0.52))
        vein_breakup = smoothstep(
            0.22,
            0.78,
            np.sin(x * 0.71 + z * 0.43) * 0.34
            + np.sin(x * 1.37 - z * 0.29) * 0.22
            + 0.50,
        )
        ring_vein *= vein_breakup
        ring_glow = paper * np.array((0.11, 0.66, 0.63), dtype=np.float32)
        atlas *= 1.0 - ring_vein[..., None] * 0.30
        atlas = atlas * (1.0 - ring_vein[..., None] * 0.18) + ring_glow * ring_vein[..., None] * 0.18
        for index, anchor in enumerate(anchors):
            node = gaussian(x, z, anchor["x"], anchor["z"], 1.15, 1.15)
            spoke_angle = index * math.tau / max(len(anchors), 1) + 0.25
            start = {"x": anchor["x"] - math.cos(spoke_angle) * 1.6, "z": anchor["z"] - math.sin(spoke_angle) * 1.6}
            end = {"x": anchor["x"] + math.cos(spoke_angle) * 1.6, "z": anchor["z"] + math.sin(spoke_angle) * 1.6}
            core = np.maximum(node, e2.segment_mask(x, z, start, end, 0.24))
            fracture = np.zeros_like(x)
            for branch, delta in enumerate((-0.72, 0.08, 0.83)):
                angle = spoke_angle + delta
                length = 3.0 + branch * 0.8
                branch_end = {
                    "x": anchor["x"] + math.cos(angle) * length,
                    "z": anchor["z"] + math.sin(angle) * length,
                }
                fracture = np.maximum(fracture, e2.segment_mask(x, z, anchor, branch_end, 0.18 + branch * 0.03))
            blast_halo = gaussian(x, z, anchor["x"], anchor["z"], 2.5, 2.1)
            atlas *= 1.0 - (fracture * 0.42 + blast_halo * 0.14)[..., None]
            atlas = atlas * (1.0 - core[..., None] * 0.42) + ring_glow * core[..., None] * 0.42
            atlas = np.clip(atlas + core[..., None] * np.array((0.012, 0.068, 0.064), dtype=np.float32), 0.0, 0.74)

        for fixture in truth["fixtureZones"]:
            fixture_mask = rectangle_mask(x, z, fixture, 0.55)
            fixture_edge = np.clip(rectangle_mask(x, z, fixture, 1.25) - rectangle_mask(x, z, fixture, 0.25), 0.0, 1.0)
            enamel_pad = paper * np.array((0.48, 0.66, 0.64), dtype=np.float32)
            atlas = atlas * (1.0 - fixture_mask[..., None] * 0.20) + enamel_pad * fixture_mask[..., None] * 0.20
            atlas *= 1.0 - fixture_edge[..., None] * 0.24
    elif key == "echo-canyon":
        truth = table["maskTruth"]
        atlas = land * np.array((0.54, 0.45, 0.34), dtype=np.float32)
        wall_mask = np.zeros_like(x)
        floor_mask = np.zeros_like(x)
        for band in truth["echoCanyonBands"]:
            mask = rectangle_mask(x, z, band, 2.4)
            if band["height"] == 5:
                wall_mask = np.maximum(wall_mask, mask)
            else:
                floor_mask = np.maximum(floor_mask, mask)
        shale = rock * np.array((0.47, 0.50, 0.47), dtype=np.float32) + plate * np.array((0.12, 0.12, 0.10), dtype=np.float32)
        wall_break = np.clip(0.70 + np.sin(z * 0.48 + x * 0.16) * 0.17 + np.sin(z * 1.13 - x * 0.07) * 0.09, 0.24, 0.97)
        atlas = atlas * (1.0 - wall_mask[..., None] * 0.58) + shale * wall_mask[..., None] * 0.58
        atlas *= 1.0 - (wall_mask * smoothstep(0.63, 0.88, wall_break))[..., None] * 0.17

        # The broadcast floor carries paired engraved echoes that never claim
        # collision or wave logic. Unequal spacing avoids a decorative carpet.
        floor_tone = dirt * np.array((0.58, 0.42, 0.28), dtype=np.float32)
        atlas = atlas * (1.0 - floor_mask[..., None] * 0.18) + floor_tone * floor_mask[..., None] * 0.18
        echo_ink = np.zeros_like(x)
        for center_z, radius in ((-27.0, 10.0), (-6.0, 17.0), (19.0, 13.0), (39.0, 22.0)):
            distance = np.hypot(x, z - center_z)
            echo_ink = np.maximum(echo_ink, np.exp(-(((distance - radius) / 0.48) ** 2)))
            echo_ink = np.maximum(echo_ink, np.exp(-(((distance - radius * 0.72) / 0.36) ** 2)) * 0.72)
        echo_ink *= floor_mask
        teal_ink = paper * np.array((0.08, 0.31, 0.29), dtype=np.float32)
        atlas = atlas * (1.0 - echo_ink[..., None] * 0.36) + teal_ink * echo_ink[..., None] * 0.36

        for zone in truth["buildZones"]:
            pad = rectangle_mask(x, z, zone, 1.0)
            edge = np.clip(rectangle_mask(x, z, zone, 1.9) - rectangle_mask(x, z, zone, 0.35), 0.0, 1.0)
            soot = paper * np.array((0.35, 0.25, 0.13), dtype=np.float32)
            atlas = atlas * (1.0 - pad[..., None] * 0.16) + soot * pad[..., None] * 0.16
            atlas *= 1.0 - edge[..., None] * 0.20
    elif key == "relay-valley":
        truth = table["maskTruth"]
        # Walnut loam and plate-derived shale keep the Signal era adjacent to
        # the established frontier while honey glass and agent teal mark the
        # outward-facing relay network as a new technological layer.
        atlas = land * np.array((0.58, 0.49, 0.38), dtype=np.float32)
        ridge_mask = np.zeros_like(x)
        for ridge in truth["ridgeBands"]:
            if ridge["id"] == "valley-floor-h0":
                continue
            ridge_mask = np.maximum(ridge_mask, rectangle_mask(x, z, ridge, 3.0))
        shale = rock * np.array((0.48, 0.51, 0.49), dtype=np.float32) + plate * np.array((0.11, 0.12, 0.11), dtype=np.float32)
        ridge_break = np.clip(0.72 + np.sin(x * 0.39 + z * 0.21) * 0.16 + np.sin(x * 0.14 - z * 0.67) * 0.10, 0.28, 0.96)
        ridge_weight = ridge_mask * ridge_break
        atlas = atlas * (1.0 - ridge_weight[..., None] * 0.54) + shale * ridge_weight[..., None] * 0.54
        strata = ridge_mask * smoothstep(0.58, 0.86, np.sin(x * 0.16 + z * 1.15) * 0.5 + 0.5)
        atlas *= 1.0 - strata[..., None] * 0.16

        # The four legal pad rectangles are work-scuffed but remain ordinary
        # ground; their exact placement authority belongs to the mask table.
        pad_centers = []
        for zone in truth["buildZones"]:
            pad_centers.append({"x": (zone["minX"] + zone["maxX"]) * 0.5, "z": (zone["minZ"] + zone["maxZ"]) * 0.5})
            pad = rectangle_mask(x, z, zone, 1.25)
            pad_edge = np.clip(rectangle_mask(x, z, zone, 2.15) - rectangle_mask(x, z, zone, 0.45), 0.0, 1.0)
            pad_wear = pad * np.clip(0.66 + np.sin(x * 0.63 - z * 0.29) * 0.18 + np.sin(z * 0.47) * 0.10, 0.24, 0.94)
            honey_soot = paper * np.array((0.48, 0.34, 0.17), dtype=np.float32) + dirt * np.array((0.12, 0.085, 0.055), dtype=np.float32)
            atlas = atlas * (1.0 - pad_wear[..., None] * 0.22) + honey_soot * pad_wear[..., None] * 0.22
            atlas *= 1.0 - pad_edge[..., None] * 0.22

        # Cable trenches connect only each line-of-sight pair. The authored
        # ridge dead gap remains a deliberate break rather than a false route.
        cable = np.maximum(
            e2.segment_mask(x, z, pad_centers[0], pad_centers[1], 0.72),
            e2.segment_mask(x, z, pad_centers[2], pad_centers[3], 0.72),
        )
        cable_shoulder = np.maximum(
            e2.segment_mask(x, z, pad_centers[0], pad_centers[1], 1.75),
            e2.segment_mask(x, z, pad_centers[2], pad_centers[3], 1.75),
        )
        atlas *= 1.0 - cable_shoulder[..., None] * 0.10
        cable_ink = paper * np.array((0.10, 0.18, 0.17), dtype=np.float32)
        atlas = atlas * (1.0 - cable[..., None] * 0.48) + cable_ink * cable[..., None] * 0.48

        # Named dead zones stay low-frequency and bruised. Engraved diagonal
        # hatch gives them readable identity without painting gameplay fog.
        for index, pocket in enumerate(truth["fogPockets"]):
            pocket_mask = rectangle_mask(x, z, pocket, 2.2)
            quiet = rock * np.array((0.34, 0.42, 0.42), dtype=np.float32)
            atlas = atlas * (1.0 - pocket_mask[..., None] * 0.34) + quiet * pocket_mask[..., None] * 0.34
            hatch = pocket_mask * smoothstep(0.64, 0.90, np.sin(x * 0.72 + z * (0.56 + index * 0.08)) * 0.5 + 0.5)
            atlas *= 1.0 - hatch[..., None] * 0.095

        # The teaching patrol is a battered punch-tape loop in the loam. It
        # records composition only and never changes movement or AI routing.
        patrol = truth["lanes"]["patrolRoutes"][0]["points"]
        route = np.zeros_like(x)
        for start, end in zip(patrol, patrol[1:]):
            route = np.maximum(route, e2.segment_mask(x, z, start, end, 0.54))
        perforation = smoothstep(0.64, 0.88, np.sin(x * 1.28 + z * 0.17) * 0.5 + 0.5)
        route *= perforation
        atlas = atlas * (1.0 - route[..., None] * 0.24) + paper * np.array((0.28, 0.24, 0.16), dtype=np.float32) * route[..., None] * 0.24
    elif key == "mare-claim":
        truth = table["maskTruth"]
        # Palette note: warm grey stippled engraving, never cold photoreal;
        # silver-and-teal over parchment. Broad quiet values are intentional.
        # Extract only engraved high-pass ink from the shipped plates. Literal
        # wrapped buildings read as giant ground decals at run-camera scale.
        plate_luma = claim.luminance(plate)
        kit_luma = claim.luminance(paper)
        plate_surround = sum(np.roll(plate_luma, shift, axis=1) for shift in (-18, -9, 9, 18)) * 0.25
        kit_surround = sum(np.roll(kit_luma, shift, axis=0) for shift in (-14, -7, 7, 14)) * 0.25
        shipped_ink = np.clip((plate_surround - plate_luma) * 4.8 + (kit_surround - kit_luma) * 2.6, 0.0, 1.0)
        lunar_value = 0.34 + macro[..., 0] * 0.035 + np.sin(x * 0.051 - z * 0.073) * 0.012
        lunar = lunar_value[..., None] * np.asarray((1.02, 1.02, 0.96), dtype=np.float32)
        # Keep the shipped plate's engraved hand, but never its literal layout.
        # The first E8 verdict pass exposed broad repeated circles as a wrapped
        # illustration. Confine the high-pass ink to several unequal, soft
        # patches so the mare reads as locally worked regolith instead.
        ink_patch = np.clip(
            0.12
            + gaussian(x, z, -39.0, 24.0, 23.0, 16.0) * 0.42
            + gaussian(x, z, 29.0, 13.0, 18.0, 25.0) * 0.34
            + gaussian(x, z, 8.0, -31.0, 31.0, 13.0) * 0.28,
            0.10,
            0.72,
        )
        ink_breakup = np.clip(
            0.62 + np.sin(x * 0.19 + z * 0.31) * 0.20 + np.sin(x * 0.47 - z * 0.13) * 0.12,
            0.18,
            0.92,
        )
        lunar *= 1.0 - shipped_ink[..., None] * (ink_patch * ink_breakup)[..., None] * 0.085
        # Unequal cross-hatched cuts make engraving the material language.
        # Avoid thresholded dot fields: at run scale they read as a repeated
        # stamp, not hand-worked regolith.
        hatch_a = smoothstep(
            0.78,
            0.94,
            np.sin(x * 1.42 + z * 0.91 + np.sin(z * 0.17) * 1.35) * 0.5 + 0.5,
        )
        hatch_b = smoothstep(
            0.86,
            0.975,
            np.sin(x * 0.83 - z * 1.77 + np.sin(x * 0.23) * 1.10) * 0.5 + 0.5,
        )
        hatch_patch = np.clip(
            0.28
            + gaussian(x, z, -32.0, 20.0, 30.0, 22.0) * 0.48
            + gaussian(x, z, 30.0, -18.0, 27.0, 30.0) * 0.37,
            0.22,
            0.80,
        )
        engraving = (hatch_a * 0.060 + hatch_b * 0.034) * hatch_patch
        atlas = lunar * (0.90 - engraving[..., None])

        rim_mask = np.zeros_like(x)
        for band in truth["rimBands"]:
            rim_mask = np.maximum(rim_mask, rectangle_mask(x, z, band, 3.0))
        rim_break = np.clip(0.76 + np.sin(x * 0.33 + z * 0.19) * 0.14 + np.sin(x * 0.11 - z * 0.57) * 0.08, 0.34, 0.96)
        rim_weight = rim_mask * rim_break
        rim_tone = rock * np.array((0.45, 0.46, 0.44), dtype=np.float32) + lunar * np.array((0.17, 0.17, 0.16), dtype=np.float32)
        atlas = atlas * (1.0 - rim_weight[..., None] * 0.52) + rim_tone * rim_weight[..., None] * 0.52
        rim_hatch = rim_mask * smoothstep(0.62, 0.89, np.sin(x * 0.41 + z * 1.16) * 0.5 + 0.5)
        atlas *= 1.0 - rim_hatch[..., None] * 0.12

        mouth = truth["lavaTubeMouth"]
        mouth_cx = (mouth["minX"] + mouth["maxX"]) * 0.5
        mouth_cz = (mouth["minZ"] + mouth["maxZ"]) * 0.5
        mouth_rx = (mouth["maxX"] - mouth["minX"]) * 0.5
        mouth_rz = (mouth["maxZ"] - mouth["minZ"]) * 0.5
        mouth_local_z = (z - mouth_cz) / mouth_rz
        mouth_radius = np.sqrt(((x - mouth_cx) / (mouth_rx * 0.68)) ** 2 + mouth_local_z ** 2)
        mouth_core = 1.0 - smoothstep(0.36, 0.88, mouth_radius)
        mouth_lip = np.exp(-(((mouth_radius - 0.88) / 0.11) ** 2))
        mouth_lip *= np.clip(0.20 + smoothstep(-0.18, 0.58, mouth_local_z) * 0.95, 0.16, 1.12)
        basalt = plate * np.array((0.085, 0.095, 0.10), dtype=np.float32)
        atlas = atlas * (1.0 - mouth_core[..., None] * 0.92) + basalt * mouth_core[..., None] * 0.92
        atlas *= 1.0 - mouth_lip[..., None] * 0.48

        # Build rectangles remain visually ordinary ground. Their scuffed
        # edges identify work history without turning masks into neon decals.
        for zone in truth["buildZones"]:
            pad = rectangle_mask(x, z, zone, 0.85)
            edge = np.clip(rectangle_mask(x, z, zone, 1.45) - rectangle_mask(x, z, zone, 0.22), 0.0, 1.0)
            wear = pad * np.clip(0.68 + np.sin(x * 0.71 - z * 0.37) * 0.16, 0.34, 0.90)
            work_tone = paper * np.array((0.39, 0.41, 0.38), dtype=np.float32)
            atlas = atlas * (1.0 - wear[..., None] * 0.12) + work_tone * wear[..., None] * 0.12
            atlas *= 1.0 - edge[..., None] * 0.15

        launch = next(zone for zone in truth["buildZones"] if zone["id"] == "launch-pad")
        launch_cx = (launch["minX"] + launch["maxX"]) * 0.5
        launch_cz = (launch["minZ"] + launch["maxZ"]) * 0.5
        scorch_radius = np.hypot((x - launch_cx) / 10.0, (z - launch_cz) / 8.2)
        scorch = np.exp(-(((scorch_radius - 0.72) / 0.30) ** 2))
        scorch *= np.clip(0.76 + np.sin(np.arctan2(z - launch_cz, x - launch_cx) * 9.0) * 0.18, 0.38, 0.94)
        soot = plate * np.array((0.12, 0.11, 0.095), dtype=np.float32)
        atlas = atlas * (1.0 - scorch[..., None] * 0.62) + soot * scorch[..., None] * 0.62

        rail = truth["rails"][0]["points"]
        rail_core = np.zeros_like(x)
        rail_shoulder = np.zeros_like(x)
        for start, end in zip(rail, rail[1:]):
            rail_core = np.maximum(rail_core, e2.segment_mask(x, z, start, end, 0.52))
            rail_shoulder = np.maximum(rail_shoulder, e2.segment_mask(x, z, start, end, 1.55))
        silver_teal = paper * np.array((0.22, 0.34, 0.33), dtype=np.float32)
        atlas = atlas * (1.0 - rail_shoulder[..., None] * 0.18) + silver_teal * rail_shoulder[..., None] * 0.18
        atlas *= 1.0 - rail_core[..., None] * 0.46

        for anchor in truth["harvestAnchors"]:
            radius = np.hypot(x - anchor["x"], z - anchor["z"])
            anchor_ring = np.exp(-(((radius - 1.25) / 0.24) ** 2))
            anchor_core = np.exp(-((radius / 0.48) ** 2))
            atlas = atlas * (1.0 - anchor_ring[..., None] * 0.36) + silver_teal * anchor_ring[..., None] * 0.36
            atlas *= 1.0 - anchor_core[..., None] * 0.24

        debris = truth["debrisArcLanes"][0]["points"]
        debris_trace = np.zeros_like(x)
        for start, end in zip(debris, debris[1:]):
            debris_trace = np.maximum(debris_trace, e2.segment_mask(x, z, start, end, 0.42))
        debris_trace *= smoothstep(0.64, 0.88, np.sin(x * 1.37 + z * 0.19) * 0.5 + 0.5)
        atlas *= 1.0 - debris_trace[..., None] * 0.24

        # Five small impacts are enough to draw the vacuum without filling it.
        impacts = ((-49.0, -14.0, 2.5), (-8.0, 34.0, 2.0), (47.0, 13.0, 2.8), (20.0, -18.0, 1.7), (3.0, 13.0, 1.3))
        for ix, iz, ir in impacts:
            radius = np.hypot(x - ix, z - iz)
            pit = np.exp(-((radius / (ir * 0.62)) ** 2))
            lip = np.exp(-(((radius - ir) / 0.31) ** 2))
            atlas *= 1.0 - pit[..., None] * 0.22
            atlas = atlas * (1.0 - lip[..., None] * 0.18) + paper * np.array((0.34, 0.35, 0.32), dtype=np.float32) * lip[..., None] * 0.18
    elif key == "ember-shore":
        truth = table["maskTruth"]
        # Plate-derived black basalt carries dense engraved labor. Ember is
        # confined to the three authored cooling bands so the whole map never
        # becomes a glowing holiday lava field.
        atlas = land * np.asarray((0.34, 0.25, 0.20), dtype=np.float32)
        plate_luma = claim.luminance(plate)
        surround = sum(np.roll(plate_luma, shift, axis=1) for shift in (-18, -9, 9, 18)) * 0.25
        shipped_ink = np.clip((surround - plate_luma) * 5.2, 0.0, 1.0)
        basalt = np.asarray((0.075, 0.064, 0.058), dtype=np.float32)
        basalt_value = np.clip(0.62 + macro[..., 0] * 0.10 + np.sin(x * 0.071 - z * 0.093) * 0.06, 0.38, 0.82)
        atlas = basalt[None, None, :] * basalt_value[..., None]
        ink_patch = np.clip(
            0.32
            + gaussian(x, z, -34.0, 24.0, 30.0, 28.0) * 0.45
            + gaussian(x, z, 31.0, -26.0, 28.0, 24.0) * 0.38,
            0.24,
            0.82,
        )
        atlas *= 1.0 - shipped_ink[..., None] * ink_patch[..., None] * 0.22
        hatch_a = smoothstep(0.76, 0.94, np.sin(x * 1.17 + z * 0.69 + np.sin(z * 0.15)) * 0.5 + 0.5)
        hatch_b = smoothstep(0.84, 0.97, np.sin(x * 0.61 - z * 1.43 + np.sin(x * 0.19)) * 0.5 + 0.5)
        atlas *= 1.0 - (hatch_a * 0.075 + hatch_b * 0.045)[..., None]

        ember_tone = paper * np.asarray((0.78, 0.29, 0.045), dtype=np.float32)
        ember_core_tone = np.asarray((0.74, 0.16, 0.022), dtype=np.float32)
        cooled_tone = plate * np.asarray((0.20, 0.18, 0.16), dtype=np.float32)
        for index, band in enumerate(truth["lavaVeinBands"]):
            core = rectangle_mask(x, z, band, 1.30)
            shoulder = rectangle_mask(x, z, {
                "minX": band["minX"] - 3.4,
                "maxX": band["maxX"] + 3.4,
                "minZ": band["minZ"] - 2.4,
                "maxZ": band["maxZ"] + 2.4,
            }, 2.1)
            cooled = shoulder * np.clip(0.72 + np.sin(x * 0.47 + z * 0.23) * 0.18, 0.28, 0.94)
            atlas = atlas * (1.0 - cooled[..., None] * 0.32) + cooled_tone * cooled[..., None] * 0.32
            # Cooled crust dominates. A few longitudinal, wandering fractures
            # disclose residual heat; transverse repeated bars looked like
            # painted traffic markings rather than geology.
            mid_x = (band["minX"] + band["maxX"]) * 0.5
            wandering = mid_x + np.sin(z * (0.13 + index * 0.011) + index * 1.4) * 1.45 + np.sin(z * 0.043 - index) * 0.72
            main_fissure = np.exp(-(((x - wandering) / 0.34) ** 2))
            branch_a = np.exp(-(((x - wandering - np.sin(z * 0.29 + index) * 2.0) / 0.24) ** 2)) * smoothstep(0.68, 0.94, np.sin(z * 0.23 + index * 1.7) * 0.5 + 0.5)
            branch_b = np.exp(-(((x - wandering + np.sin(z * 0.21 - index) * 2.4) / 0.22) ** 2)) * smoothstep(0.74, 0.96, np.sin(z * 0.19 - index * 1.3) * 0.5 + 0.5)
            fissure = core * np.clip(main_fissure * 0.82 + branch_a * 0.48 + branch_b * 0.40, 0.0, 1.0)
            residual = core * np.clip(0.18 + shipped_ink * 0.20, 0.12, 0.34)
            rift_floor = np.asarray((0.115, 0.052, 0.026), dtype=np.float32)
            floor_weight = core * np.clip(0.28 + shipped_ink * 0.12, 0.24, 0.42)
            atlas = atlas * (1.0 - floor_weight[..., None]) + rift_floor[None, None, :] * floor_weight[..., None]
            atlas = atlas * (1.0 - residual[..., None] * 0.20) + ember_tone * residual[..., None] * 0.20
            atlas = atlas * (1.0 - fissure[..., None] * 0.72) + ember_core_tone[None, None, :] * fissure[..., None] * 0.72
            crust = np.clip(shoulder - core * 0.72, 0.0, 1.0) * smoothstep(0.60, 0.90, np.sin(z * 0.83 - x * 0.55) * 0.5 + 0.5)
            atlas *= 1.0 - crust[..., None] * 0.22

        # The preserve sites remain ordinary, battered ground. Teal glass is
        # a restrained machine-age accent at the titan footing only.
        for zone in truth["buildZones"]:
            pad = rectangle_mask(x, z, zone, 1.0)
            edge = np.clip(rectangle_mask(x, z, zone, 1.8) - rectangle_mask(x, z, zone, 0.30), 0.0, 1.0)
            wear = pad * np.clip(0.66 + np.sin(x * 0.63 - z * 0.31) * 0.19, 0.25, 0.94)
            pad_tone = paper * np.asarray((0.28, 0.23, 0.17), dtype=np.float32)
            atlas = atlas * (1.0 - wear[..., None] * 0.18) + pad_tone * wear[..., None] * 0.18
            atlas *= 1.0 - edge[..., None] * 0.19
            if zone["id"] == "cooled-titan-machine-mount":
                teal_scuff = pad * smoothstep(0.80, 0.96, np.sin(x * 0.72 + z * 0.41) * 0.5 + 0.5)
                teal = np.asarray((0.075, 0.24, 0.24), dtype=np.float32)
                atlas = atlas * (1.0 - teal_scuff[..., None] * 0.13) + teal[None, None, :] * teal_scuff[..., None] * 0.13

        vent = truth["stakeMarkers"][0]
        vent_distance = np.hypot(x - vent["x"], z - vent["z"])
        vent_ring = np.exp(-(((vent_distance - 2.2) / 0.38) ** 2))
        vent_soot = gaussian(x, z, vent["x"], vent["z"], 3.4, 3.0)
        atlas *= 1.0 - vent_soot[..., None] * 0.21
        atlas = atlas * (1.0 - vent_ring[..., None] * 0.44) + ember_tone * vent_ring[..., None] * 0.44
    else:
        atlas = land * np.array((0.49, 0.43, 0.39), dtype=np.float32)
        midway = e2.segment_mask(x, z, {"x": 0.0, "z": -40.0}, {"x": 0.0, "z": 8.0}, 5.6)
        midway_core = e2.segment_mask(x, z, {"x": 0.0, "z": -40.0}, {"x": 0.0, "z": 8.0}, 1.45)
        packed = dirt * np.array((0.52, 0.41, 0.31), dtype=np.float32) + paper * np.array((0.10, 0.075, 0.05), dtype=np.float32)
        fair_packed = np.clip(packed * 1.34 + paper * np.array((0.12, 0.095, 0.070), dtype=np.float32), 0.0, 0.68)
        midway_breakup = np.clip(0.74 + np.sin(x * 0.27 + z * 0.13) * 0.16, 0.38, 0.94)
        midway_weight = midway * midway_breakup
        atlas = atlas * (1.0 - midway_weight[..., None] * 0.48) + fair_packed * midway_weight[..., None] * 0.48
        atlas *= 1.0 - midway_core[..., None] * 0.09
        cross_midway = e2.segment_mask(x, z, {"x": -34.0, "z": 8.0}, {"x": 34.0, "z": 8.0}, 5.0)
        cross_breakup = np.clip(0.72 + np.sin(x * 0.33 + z * 0.11) * 0.18, 0.34, 0.90)
        cross_weight = cross_midway * cross_breakup
        atlas = atlas * (1.0 - cross_weight[..., None] * 0.52) + fair_packed * cross_weight[..., None] * 0.52

        fair_loop_radius = np.hypot(x / 30.0, (z - 5.0) / 23.0)
        fair_loop = np.exp(-(((fair_loop_radius - 1.0) / 0.090) ** 2))
        loop_breakup = np.clip(0.70 + np.sin(np.arctan2(z - 5.0, x) * 11.0 - 0.5) * 0.17, 0.34, 0.90)
        fair_loop *= loop_breakup
        atlas = atlas * (1.0 - fair_loop[..., None] * 0.42) + fair_packed * fair_loop[..., None] * 0.42

        west_pad = rectangle_mask(x, z, {"minX": -31.0, "maxX": -10.0, "minZ": 0.0, "maxZ": 21.0}, 1.9)
        east_pad = rectangle_mask(x, z, {"minX": 10.0, "maxX": 31.0, "minZ": 0.0, "maxZ": 21.0}, 1.9)
        pavilion_pad = np.maximum(west_pad, east_pad)
        pad_scuff = np.clip(0.72 + np.sin(x * 0.61 - z * 0.19) * 0.16 + np.sin(z * 0.48) * 0.10, 0.28, 0.94)
        pavilion_work = pavilion_pad * pad_scuff
        pavilion_earth = np.clip(fair_packed * 0.88 + dirt * np.array((0.18, 0.13, 0.09), dtype=np.float32), 0.0, 0.64)
        atlas = atlas * (1.0 - pavilion_work[..., None] * 0.48) + pavilion_earth * pavilion_work[..., None] * 0.48

        # Two repaired wagon grooves, lamp-burned pavilion shelves, and an
        # iron-stained wheel foundation make this a desperate working fair,
        # not clean festival bunting laid over the voltage county.
        wagon_scars = np.maximum(
            e2.segment_mask(x, z, {"x": -1.65, "z": -38.0}, {"x": -1.65, "z": 5.6}, 0.52),
            e2.segment_mask(x, z, {"x": 1.65, "z": -38.0}, {"x": 1.65, "z": 5.6}, 0.52),
        )
        rut_breakup = np.clip(
            0.46 + 0.26 * np.sin(z * 0.51 + x * 0.09) + 0.19 * np.sin(z * 0.19 - x * 0.63),
            0.08,
            0.88,
        )
        atlas *= 1.0 - wagon_scars[..., None] * rut_breakup[..., None] * 0.11
        wheel_radius = np.hypot(x / 8.2, (z - 8.0) / 6.2)
        wheel_churn = np.exp(-(((wheel_radius - 1.0) / 0.14) ** 2))
        wheel_churn *= np.clip(0.72 + np.sin(np.arctan2(z - 8.0, x) * 7.0 + 0.4) * 0.18, 0.38, 0.92)
        wheel_shoulder = np.exp(-(((wheel_radius - 1.34) / 0.16) ** 2))
        wheel_shoulder *= np.clip(0.68 + np.sin(np.arctan2(z - 8.0, x) * 5.0 - 0.7) * 0.20, 0.30, 0.90)
        foundation_soot = plate * np.array((0.22, 0.16, 0.11), dtype=np.float32)
        foundation_dust = packed * np.array((1.10, 0.94, 0.78), dtype=np.float32)
        atlas = atlas * (1.0 - wheel_shoulder[..., None] * 0.34) + foundation_dust * wheel_shoulder[..., None] * 0.34
        atlas = atlas * (1.0 - wheel_churn[..., None] * 0.56) + foundation_soot * wheel_churn[..., None] * 0.56
        pavilion_burn = np.clip(
            gaussian(x, z, -20.0, 10.0, 10.5, 12.0)
            + gaussian(x, z, 20.0, 10.0, 10.0, 12.5),
            0.0,
            1.0,
        )
        soot = plate * np.array((0.18, 0.13, 0.095), dtype=np.float32)
        atlas = atlas * (1.0 - pavilion_burn[..., None] * 0.32) + soot * pavilion_burn[..., None] * 0.32
        fixture = table["maskTruth"]["fixtureZones"][0]
        fixture_zone = rectangle_mask(x, z, fixture, 0.42)
        fixture_edge = np.clip(rectangle_mask(x, z, fixture, 1.05) - rectangle_mask(x, z, fixture, 0.28), 0.0, 1.0)
        iron_stain = paper * np.array((0.19, 0.20, 0.22), dtype=np.float32)
        atlas = atlas * (1.0 - fixture_zone[..., None] * 0.24) + iron_stain * fixture_zone[..., None] * 0.24
        atlas *= 1.0 - fixture_edge[..., None] * 0.32
        foundation_sills = np.maximum(
            e2.segment_mask(x, z, {"x": -3.5, "z": 7.0}, {"x": 3.5, "z": 7.0}, 0.34),
            e2.segment_mask(x, z, {"x": -3.5, "z": 9.0}, {"x": 3.5, "z": 9.0}, 0.34),
        )
        anchor_stains = np.clip(
            gaussian(x, z, -7.4, 5.2, 1.1, 1.0)
            + gaussian(x, z, 7.4, 5.2, 1.1, 1.0)
            + gaussian(x, z, -7.4, 11.0, 1.1, 1.0)
            + gaussian(x, z, 7.4, 11.0, 1.1, 1.0),
            0.0,
            1.0,
        )
        atlas *= 1.0 - foundation_sills[..., None] * 0.24
        atlas = atlas * (1.0 - anchor_stains[..., None] * 0.30) + foundation_soot * anchor_stains[..., None] * 0.30
        trample = (
            np.sin(x * 0.47 + z * 0.31)
            * np.sin(x * 0.19 - z * 0.57)
            * np.sin(x * 0.83 + z * 0.11)
            > 0.48
        ).astype(np.float32)
        atlas *= 1.0 - (trample * np.clip(midway + pavilion_burn, 0.0, 1.0))[..., None] * 0.085

    edge_coordinate = np.maximum(ax / (profile["width"] * 0.5), az / (profile["height"] * 0.5))
    edge_break = np.sin(x * 0.17 + z * 0.09) * 0.010 + np.sin(x * 0.07 - z * 0.19) * 0.006
    edge = smoothstep(0.91, 1.0, edge_coordinate + edge_break)[..., None]
    # Fade the final few metres into the same weathered rock language sampled
    # by the panorama skirt.  This is an irregular material transition on the
    # render surface only; the rectangular simulation bounds remain exact.
    atlas = atlas * (1.0 - edge * 0.74) + rock * np.array((0.34, 0.31, 0.29)) * edge * 0.74
    if key != "mare-claim":
        atlas = claim.apply_grit_grade(atlas, source, u, v, key)
    else:
        # Preserve low-frequency lunar quiet while retaining plate-derived ink
        # and the procedural work scars above.
        atlas = np.clip(atlas * 0.94 + np.asarray((0.018, 0.018, 0.016), dtype=np.float32), 0.006, 0.68)
    if key == "glow-mesa":
        # E6 is bright because the town has repaired it. Preserve broad mint
        # and rose value families after the shared grit grade so texture grain
        # does not flatten every landform into the same visual frequency.
        top_zone = next(zone for zone in table["maskTruth"]["elevationZones"] if zone["id"] == "mesa-top-h5")
        top_mask = rectangle_mask(x, z, top_zone, 3.2)[..., None]
        base_zone = next(zone for zone in table["maskTruth"]["buildZones"] if zone["id"] == "base-flat")
        base_mask = rectangle_mask(x, z, base_zone, 3.0)[..., None]
        top_tone = np.asarray((0.38, 0.44, 0.42), dtype=np.float32)
        base_tone = np.asarray((0.26, 0.31, 0.29), dtype=np.float32)
        atlas = atlas * (1.0 - top_mask * 0.18) + top_tone[None, None, :] * top_mask * 0.18
        atlas = atlas * (1.0 - base_mask * 0.15) + base_tone[None, None, :] * base_mask * 0.15
    elif key == "echo-canyon":
        truth = table["maskTruth"]
        wall_mask = np.maximum.reduce([
            rectangle_mask(x, z, zone, 2.8)
            for zone in truth["echoCanyonBands"]
            if zone["height"] == 5
        ])[..., None]
        floor_mask = rectangle_mask(x, z, next(zone for zone in truth["echoCanyonBands"] if zone["height"] == 0), 3.4)[..., None]
        wall_tone = np.asarray((0.205, 0.225, 0.215), dtype=np.float32)
        floor_tone = np.asarray((0.255, 0.205, 0.145), dtype=np.float32)
        atlas = atlas * (1.0 - wall_mask * 0.18) + wall_tone[None, None, :] * wall_mask * 0.18
        atlas = atlas * (1.0 - floor_mask * 0.11) + floor_tone[None, None, :] * floor_mask * 0.11
    elif key == "relay-valley":
        truth = table["maskTruth"]
        ridge_mask = np.maximum.reduce([
            rectangle_mask(x, z, zone, 3.0)
            for zone in truth["ridgeBands"]
            if zone["id"] != "valley-floor-h0"
        ])[..., None]
        valley_mask = rectangle_mask(x, z, next(zone for zone in truth["ridgeBands"] if zone["id"] == "valley-floor-h0"), 4.0)[..., None]
        ridge_tone = np.asarray((0.225, 0.245, 0.232), dtype=np.float32)
        valley_tone = np.asarray((0.265, 0.225, 0.175), dtype=np.float32)
        atlas = atlas * (1.0 - ridge_mask * 0.16) + ridge_tone[None, None, :] * ridge_mask * 0.16
        atlas = atlas * (1.0 - valley_mask * 0.10) + valley_tone[None, None, :] * valley_mask * 0.10
    elif key == "mare-claim":
        # Pull the shared grit grade back toward the approved parchment-moon
        # family; this prevents frontier ochre from becoming the dominant read.
        lunar_tone = np.asarray((0.355, 0.358, 0.335), dtype=np.float32)
        atlas = atlas * 0.78 + lunar_tone[None, None, :] * 0.22
    elif key == "ember-shore":
        # Reassert the bundle's deep-ink / parchment-gold balance after the
        # shared grade, without turning cooling bands into neon emission.
        ink_tone = np.asarray((0.070, 0.060, 0.055), dtype=np.float32)
        atlas = atlas * 0.84 + ink_tone[None, None, :] * 0.16

    rgba = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    rgba[:, :, :3] = np.clip(atlas, 0.003, 0.72)
    path = OUT / f"{profile['stem']}-atlas.png"
    image = bpy.data.images.new(profile["atlas"], ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image, path


def make_terrain(profile, table, table_path, height_at, material):
    half_x, half_z = profile["width"] * 0.5, profile["height"] * 0.5
    vertices, uvs, faces = [], [], []
    for zi in range(SEGMENTS + 1):
        game_z = -half_z + profile["height"] * zi / SEGMENTS
        for xi in range(SEGMENTS + 1):
            x = -half_x + profile["width"] * xi / SEGMENTS
            vertices.append((x, -game_z, float(height_at(x, game_z))))
            uvs.append((xi / SEGMENTS, zi / SEGMENTS))
    row = SEGMENTS + 1
    for zi in range(SEGMENTS):
        for xi in range(SEGMENTS):
            a = zi * row + xi
            faces.extend(((a, a + row + 1, a + 1), (a, a + row, a + row + 1)))
    mesh = bpy.data.meshes.new(profile["mesh"])
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        # The E6 caprock must show chipped strata and hard planes. Smooth
        # shading turned its four-metre scarp into a rounded tabletop lip.
        polygon.use_smooth = profile["contractId"] not in {"e6-glow-mesa", "e7-relay-valley", "e7-echo-canyon"}
        for loop_index in polygon.loop_indices:
            uv.data[loop_index].uv = uvs[mesh.loops[loop_index].vertex_index]
    terrain = bpy.data.objects.new(profile["object"], mesh)
    bpy.context.collection.objects.link(terrain)
    mesh.materials.append(material)
    terrain["render_only"] = True
    terrain["sim_authority"] = "published mask table and planar simulation; unchanged"
    terrain["height_socket"] = "Terrain.visualY"
    terrain["contract_id"] = profile["contractId"]
    terrain["tile_id"] = table["maskTruth"]["tileId"]
    terrain["mask_table"] = str(table_path.relative_to(ROOT))
    terrain["load_bearing_sites_flat"] = bool(load_bearing_sites(table) or table["maskTruth"].get("fixtureZones") or profile["contractId"] in {"e7-relay-valley", "e7-echo-canyon", "e8-mare-claim", "e10-ember-shore"})
    terrain["landmarks_frozen"] = profile["contractId"] not in {"e3-fairground", "e6-glow-mesa", "e7-relay-valley", "e7-echo-canyon", "e10-ember-shore"}
    if profile["contractId"] == "e7-echo-canyon":
        terrain["landmark_mount_ids"] = json.dumps([mount["id"] for mount in LANDMARK_MOUNTS["echo-canyon"]])
        terrain["runtime_owned_visuals_absent"] = True
    return terrain


def make_water(profile, material, height=-0.075):
    # Verdict-only continuation: the exact playable bank width stays fixed,
    # while the working river carries beyond the rectangular tile into the
    # separate panorama ground. This helper is removed before terrain export.
    half_x = 162.0
    x_steps, z_steps = 64, 8
    vertices, faces = [], []
    for zi in range(z_steps + 1):
        game_z = -SHALLOWS_HALF_WIDTH + 2.0 * SHALLOWS_HALF_WIDTH * zi / z_steps
        for xi in range(x_steps + 1):
            x = -half_x + 2.0 * half_x * xi / x_steps
            ripple = 0.020 * math.sin(x * 0.24 + game_z * 0.71) + 0.010 * math.sin(x * 0.57 - game_z * 0.31)
            vertices.append((x, -game_z, height + ripple))
    row = x_steps + 1
    for zi in range(z_steps):
        for xi in range(x_steps):
            a = zi * row + xi
            faces.extend(((a, a + row + 1, a + 1), (a, a + row, a + row + 1)))
    mesh = bpy.data.meshes.new("RenderHelperE3WaterMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("RenderHelperE3Water", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(material)
    return obj


def preview_materials(key):
    materials = e2.preview_materials(key)
    materials["mask"] = claim.make_render_material(f"{key}MaskTealBright", (0.035, 0.88, 0.78), 0.48, 0.08)
    materials["danger"] = claim.make_render_material(f"{key}MaskRustBright", (0.96, 0.16, 0.025), 0.48, 0.08)
    materials["warm"] = claim.make_render_material(f"{key}LanternWarm", (0.88, 0.31, 0.045), 0.48, 0.10)
    materials["waterline"] = claim.make_render_material(f"{key}Waterline", (0.15, 0.085, 0.030), 0.84, 0.04)
    materials["flow"] = claim.make_render_material(f"{key}FlowInk", (0.035, 0.075, 0.070), 0.78, 0.04)
    materials["brass"] = claim.make_render_material(f"{key}ScuffedBrass", (0.48, 0.19, 0.038), 0.58, 0.34)
    materials["maskfill"] = claim.make_render_material(f"{key}MaskTealHatch", (0.025, 0.25, 0.24), 0.72, 0.02)
    return materials


def point_clear(key, x, z, table):
    if any(zone["minX"] - 1.4 <= x <= zone["maxX"] + 1.4 and zone["minZ"] - 1.4 <= z <= zone["maxZ"] + 1.4 for zone in table["maskTruth"]["buildZones"]):
        return False
    if key == "canyon-works":
        if abs(z) <= SHALLOWS_HALF_WIDTH + 1.0:
            return False
    if any(math.hypot(x - site["x"], z - site["z"]) <= site["radius"] + 1.4 for _kind, site in load_bearing_sites(table)):
        return False
    if any(zone["minX"] - 1.4 <= x <= zone["maxX"] + 1.4 and zone["minZ"] - 1.4 <= z <= zone["maxZ"] + 1.4 for zone in table["maskTruth"].get("fixtureZones", [])):
        return False
    if key == "dust-flats":
        truth = table["maskTruth"]
        if abs(math.hypot(x, z) - truth["orbitSpawn"]["radius"]) < 6.0:
            return False
        for road in truth["roadCorridors"]:
            if float(e2.segment_mask(np.asarray(x), np.asarray(z), road["start"], road["end"], 4.6)) > 0.1:
                return False
    if key == "glow-mesa":
        truth = table["maskTruth"]
        if any(field["minX"] - 1.0 <= x <= field["maxX"] + 1.0 and field["minZ"] - 1.0 <= z <= field["maxZ"] + 1.0 for field in truth["decayFields"]):
            return False
        if any(path["minX"] - 1.0 <= x <= path["maxX"] + 1.0 and path["minZ"] - 1.0 <= z <= path["maxZ"] + 1.0 for path in truth["herdPaths"]):
            return False
    if key == "relay-valley":
        truth = table["maskTruth"]
        if any(pocket["minX"] - 1.0 <= x <= pocket["maxX"] + 1.0 and pocket["minZ"] - 1.0 <= z <= pocket["maxZ"] + 1.0 for pocket in truth["fogPockets"]):
            return False
        patrol = truth["lanes"]["patrolRoutes"][0]["points"]
        for start, end in zip(patrol, patrol[1:]):
            if float(e2.segment_mask(np.asarray(x), np.asarray(z), start, end, 2.8)) > 0.1:
                return False
    if key == "mare-claim":
        truth = table["maskTruth"]
        mouth = truth["lavaTubeMouth"]
        if mouth["minX"] - 2.0 <= x <= mouth["maxX"] + 2.0 and mouth["minZ"] - 2.0 <= z <= mouth["maxZ"] + 2.0:
            return False
        if any(math.hypot(x - anchor["x"], z - anchor["z"]) <= 2.8 for anchor in truth["harvestAnchors"]):
            return False
        for rail in truth["rails"]:
            for start, end in zip(rail["points"], rail["points"][1:]):
                if float(e2.segment_mask(np.asarray(x), np.asarray(z), start, end, 2.4)) > 0.1:
                    return False
        for lane in truth["debrisArcLanes"]:
            for start, end in zip(lane["points"], lane["points"][1:]):
                if float(e2.segment_mask(np.asarray(x), np.asarray(z), start, end, 1.8)) > 0.1:
                    return False
    if key == "ember-shore":
        for band in table["maskTruth"]["lavaVeinBands"]:
            if band["minX"] - 1.4 <= x <= band["maxX"] + 1.4 and band["minZ"] - 1.4 <= z <= band["maxZ"] + 1.4:
                return False
    return True


def add_clutter(key, profile, table, height_at, materials):
    rng = np.random.default_rng({"canyon-works": 503, "moth-season": 619, "blackout-ridge": 733, "dust-flats": 887, "fairground": 991, "glow-mesa": 1103, "relay-valley": 1217, "echo-canyon": 1279, "mare-claim": 1301, "ember-shore": 1511}[key])
    objects = []
    half_x, half_z = profile["width"] * 0.5, profile["height"] * 0.5
    count = 0
    for _ in range(300):
        if count >= {"canyon-works": 54, "moth-season": 42, "blackout-ridge": 48, "dust-flats": 92, "fairground": 34, "glow-mesa": 64, "relay-valley": 58, "echo-canyon": 52, "mare-claim": 24, "ember-shore": 54}[key]:
            break
        x = float(rng.uniform(-half_x + 2, half_x - 2))
        z = float(rng.uniform(-half_z + 2, half_z - 2))
        if not point_clear(key, x, z, table):
            continue
        if key in {"glow-mesa", "relay-valley", "echo-canyon", "mare-claim", "ember-shore"}:
            local_heights = (
                float(height_at(x - 1.0, z)),
                float(height_at(x + 1.0, z)),
                float(height_at(x, z - 1.0)),
                float(height_at(x, z + 1.0)),
            )
            slope_limit = 0.34 if key == "glow-mesa" else (0.18 if key == "mare-claim" else (0.24 if key == "ember-shore" else 0.28))
            if max(local_heights) - min(local_heights) > slope_limit:
                continue
        size = float(rng.uniform(0.38, 1.22) if key == "glow-mesa" else (rng.uniform(0.22, 0.72) if key == "mare-claim" else (rng.uniform(0.30, 1.02) if key in {"relay-valley", "echo-canyon"} else (rng.uniform(0.30, 1.08) if key == "ember-shore" else rng.uniform(0.25, 0.90)))))
        objects.append(claim.add_rock(f"RenderHelperE3Rubble.{count}", x, z, (size * rng.uniform(0.8, 1.7), size * rng.uniform(0.7, 1.2), size * rng.uniform(0.45, 0.95)), materials["stone"], yaw=float(rng.uniform(-math.pi, math.pi))))
        count += 1
    cactus_sets = {
        "canyon-works": ((-44, -15, 0.72, 1, 0.2), (43, -18, 0.80, -1, -0.4), (-43, 45, 0.64, 1, 0.8)),
        "blackout-ridge": ((-35, 16, 0.62, 1, 0.4), (32, -30, 0.68, -1, -0.3), (-26, 38, 0.58, 1, 1.0)),
        "dust-flats": ((-71, 12, 0.72, 1, 0.2), (70, 34, 0.66, -1, -0.4), (-68, -70, 0.61, 1, 0.8), (72, -66, 0.70, -1, 0.6), (12, 74, 0.55, 1, -0.8)),
        "fairground": ((-40, -35, 0.50, 1, 1.0),),
        "glow-mesa": ((-59, -4, 0.58, 1, 0.6), (57, 47, 0.62, -1, -0.4)),
        "relay-valley": ((-58, -38, 0.48, 1, 0.6), (58, -29, 0.54, -1, -0.4), (-58, 14, 0.45, 1, 0.9)),
        "echo-canyon": ((-59, -39, 0.46, 1, 0.5), (58, 28, 0.52, -1, -0.4), (-57, 47, 0.43, 1, 1.0)),
    }
    for index, (x, z, scale, flip, yaw) in enumerate(cactus_sets.get(key, ())):
        if point_clear(key, x, z, table):
            objects.extend(claim.make_cactus(f"RenderHelperE3Cactus.{index}", x, z, scale, materials, flip, yaw, height_at))
    return objects


def add_water_engraving(profile, materials):
    # The water mask already owns its exact banks. Extra dark line helpers read
    # as rails and flatten the river, so the dusk verdict uses only the painted
    # water surface and sculpted shoulders outside the mask.
    return []


def add_fairground_preview(height_at, materials):
    """Verdict-only machinery; runtime owns the wheel and pavilion systems."""
    objects = []
    ground = float(height_at(0.0, 8.0))
    center_height = ground + 5.25
    radius = 4.0
    ring = []
    for index in range(49):
        angle = index / 48 * math.tau
        ring.append((math.cos(angle) * radius, 8.0, center_height + math.sin(angle) * radius))
    objects.append(claim.add_curve("RenderHelperFairWheel.Ring", ring, 0.20, materials["brass"]))
    for index in range(8):
        angle = index / 8 * math.tau
        x = math.cos(angle) * radius
        cabin_height = center_height + math.sin(angle) * radius
        objects.append(claim.add_beam(f"RenderHelperFairWheel.Spoke.{index}", (0.0, 8.0, center_height), (x, 8.0, cabin_height), 0.16, materials["brass"]))
        objects.append(claim.add_beam(f"RenderHelperFairWheel.Hanger.{index}", (x, 8.0, cabin_height), (x, 8.0, cabin_height - 0.70), 0.08, materials["iron"]))
        objects.append(claim.add_box_game(f"RenderHelperFairWheel.Cabin.{index}", x, 8.0, cabin_height - 1.20, (0.76, 0.62, 0.54), materials["wood"], bevel=0.04))
        objects.append(claim.add_box_game(f"RenderHelperFairWheel.Lamp.{index}", x, 7.66, cabin_height - 1.08, (0.50, 0.05, 0.26), materials["warm"], bevel=0.02))
    for index, foot_x in enumerate((-2.8, 2.8)):
        objects.append(claim.add_beam(f"RenderHelperFairWheel.Support.{index}", (foot_x, 8.0, ground + 0.18), (0.0, 8.0, center_height), 0.28, materials["timber"]))
        objects.append(claim.add_box_game(f"RenderHelperFairWheel.Foot.{index}", foot_x, 8.0, ground, (1.25, 1.10, 0.34), materials["stone"], bevel=0.06))
    objects.append(claim.add_cylinder_between("RenderHelperFairWheel.Axle", (0.0, 7.35, center_height), (0.0, 8.65, center_height), 0.42, materials["brass"], vertices=12))
    objects.append(claim.add_box_game("RenderHelperFairWheel.Foundation", 0.0, 8.0, ground, (7.4, 1.20, 0.28), materials["brass"], bevel=0.06))

    pavilion_roofs = []
    for pavilion_index, x in enumerate((-20.0, 20.0)):
        base = float(height_at(x, 10.0))
        for post_index, (ox, oz) in enumerate(((-3.5, -3.0), (3.5, -3.0), (-3.5, 3.0), (3.5, 3.0))):
            post_base = float(height_at(x + ox, 10.0 + oz))
            objects.append(claim.add_beam(f"RenderHelperPavilion.{pavilion_index}.Post.{post_index}", (x + ox, 10.0 + oz, post_base), (x + ox, 10.0 + oz, base + 3.4 + (0.10 if post_index % 2 else -0.08)), 0.18, materials["timber"]))
        ridge_a = (x, 7.0, base + 5.0)
        ridge_b = (x, 13.0, base + 4.8)
        objects.append(claim.add_beam(f"RenderHelperPavilion.{pavilion_index}.Ridge", ridge_a, ridge_b, 0.20, materials["rust"]))
        objects.append(claim.add_roof_prism(f"RenderHelperPavilion.{pavilion_index}.Canopy", x, 10.0, base + 3.25, 7.4, 6.4, 1.55, materials["wood"]))
        objects.append(claim.add_box_game(f"RenderHelperPavilion.{pavilion_index}.Counter", x, 8.0, base + 0.10, (6.2, 0.85, 1.15), materials["timber"], bevel=0.05))
        objects.append(claim.add_box_game(f"RenderHelperPavilion.{pavilion_index}.CounterCap", x, 8.0, base + 1.25, (6.6, 1.05, 0.16), materials["brass"], bevel=0.04))
        for side_index, side_x in enumerate((x - 3.5, x + 3.5)):
            objects.append(claim.add_beam(f"RenderHelperPavilion.{pavilion_index}.RoofA.{side_index}", (side_x, 7.0, base + 3.3), ridge_a, 0.16, materials["wood"]))
            objects.append(claim.add_beam(f"RenderHelperPavilion.{pavilion_index}.RoofB.{side_index}", (side_x, 13.0, base + 3.3), ridge_b, 0.16, materials["wood"]))
        pavilion_roofs.append((x, 10.0, base + 4.5))

    for index, (x, z, height) in enumerate(pavilion_roofs):
        wire_start = ground + 1.55
        sag = [(0.0, 8.0, wire_start), (x * 0.50, 9.0, height - 0.45), (x, z, height)]
        objects.append(claim.add_curve(f"RenderHelperFairWire.{index}", sag, 0.045, materials["iron"]))
        for bulb_index, amount in enumerate((0.22, 0.46, 0.70, 0.90)):
            bx = x * amount
            bz = 8.0 + (z - 8.0) * amount
            bh = wire_start * (1.0 - amount) + height * amount - math.sin(amount * math.pi) * 0.48
            objects.append(claim.add_box_game(f"RenderHelperFairWire.{index}.Bulb.{bulb_index}", bx, bz, bh - 0.10, (0.18, 0.18, 0.20), materials["warm"], bevel=0.03))

    return objects


def add_glow_mesa_preview(height_at, materials):
    """Verdict-only existing E6 bodies; excluded from terrain save/export."""
    objects = []
    placements = (
        ("IsotopeKitchen", ROOT / "assets/pilots/isotope-kitchen-3d/isotope-kitchen.glb", 0.0, -32.0, 1.04, 0.0),
        ("DecayClock", ROOT / "assets/pilots/decay-clock-3d/decay-clock.glb", -40.0, -43.0, 1.08, 0.10),
        ("CatalogWarehouse", ROOT / "assets/pilots/catalog-warehouse-3d/catalog-warehouse.glb", -34.0, 47.0, 1.22, math.pi),
        ("WestDefense", ROOT / "assets/pilots/run3d/turret.e6.glb", -23.0, 4.0, 1.48, -0.35),
        ("EastDefense", ROOT / "assets/pilots/run3d/turret.e6.glb", 23.0, 4.0, 1.48, 0.35),
    )
    for label, path, x, z, scale, yaw in placements:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(path))
        imported = [obj for obj in bpy.data.objects if obj not in before]
        root = bpy.data.objects.new(f"RenderHelperGlowMesa.{label}", None)
        bpy.context.collection.objects.link(root)
        for index, obj in enumerate(imported):
            obj.name = f"RenderHelperGlowMesa.{label}.{index}.{obj.name}"
            obj.parent = root
        root.location = (x, -z, float(height_at(x, z)))
        root.rotation_euler[2] = yaw
        root.scale = (scale, scale, scale)
        objects.extend([root, *imported])

    # Two exhausted timber barricades make the repaired homestead read as a
    # defended foothold. They are verdict-only scene context, deliberately
    # absent from the terrain GLB and from the runtime mount contract.
    for index, (x, z, yaw, width) in enumerate(((-16.0, -1.8, -0.12, 10.5), (16.0, -1.2, 0.15, 9.5))):
        ground = float(height_at(x, z))
        objects.append(claim.add_box_game(f"RenderHelperGlowMesa.Barricade.{index}.Rail", x, z, ground + 0.28, (width, 0.78, 0.72), materials["wood"], yaw=yaw, bevel=0.06))
        for post, offset in enumerate((-width * 0.38, width * 0.38)):
            px = x + math.cos(yaw) * offset
            pz = z + math.sin(yaw) * offset
            post_ground = float(height_at(px, pz))
            objects.append(claim.add_beam(f"RenderHelperGlowMesa.Barricade.{index}.Post.{post}", (px, pz, post_ground + 0.04), (px + (0.35 if post == 0 else -0.28), pz, post_ground + 2.25), 0.34, materials["wood"]))
        objects.append(claim.add_beam(f"RenderHelperGlowMesa.Barricade.{index}.Brace", (x - width * 0.32, z, ground + 0.20), (x + width * 0.24, z, ground + 1.58), 0.22, materials["iron"]))
        for stake, amount in enumerate((-0.40, -0.20, 0.0, 0.20, 0.40)):
            offset = width * amount
            px = x + math.cos(yaw) * offset
            pz = z + math.sin(yaw) * offset
            stake_ground = float(height_at(px, pz))
            objects.append(claim.add_beam(
                f"RenderHelperGlowMesa.Barricade.{index}.Stake.{stake}",
                (px, pz, stake_ground + 0.05),
                (px + math.sin(yaw) * 0.55, pz - math.cos(yaw) * 1.10, stake_ground + 2.55 + (stake % 2) * 0.22),
                0.28,
                materials["wood"],
            ))

    # Rubble collects at the toe of the scarp rather than floating on its face.
    for index, (x, z, size) in enumerate(((-35.5, -5.8, 1.35), (-27.0, -6.5, 0.92), (-9.0, -7.2, 1.08), (12.5, -6.8, 0.86), (30.5, -5.5, 1.28), (36.5, 0.5, 0.78))):
        objects.append(claim.add_rock(f"RenderHelperGlowMesa.ScarpFall.{index}", x, z, (size * 1.45, size, size * 0.72), materials["stone"], yaw=index * 0.73))

    return objects


def add_relay_valley_preview(height_at, table, materials):
    """Verdict-only existing tower bodies and LOS cues; no runtime mounts."""
    objects = []
    tower_path = ROOT / "assets/pilots/relay-tower-3d/relay-tower.glb"
    yaws = (-0.34, -0.12, 0.12, 0.34)
    centers = []
    for index, (zone, yaw) in enumerate(zip(table["maskTruth"]["buildZones"], yaws)):
        x = (zone["minX"] + zone["maxX"]) * 0.5
        z = (zone["minZ"] + zone["maxZ"]) * 0.5
        centers.append((x, z))
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(tower_path))
        imported = [obj for obj in bpy.data.objects if obj not in before]
        root = bpy.data.objects.new(f"RenderHelperRelayValley.Tower.{index}", None)
        bpy.context.collection.objects.link(root)
        for child_index, obj in enumerate(imported):
            obj.name = f"RenderHelperRelayValley.Tower.{index}.{child_index}.{obj.name}"
            obj.parent = root
        root.location = (x, -z, float(height_at(x, z)))
        root.rotation_euler[2] = yaw
        root.scale = (0.90, 0.90, 0.90)
        objects.extend([root, *imported])

    # Two short, exact ridge chains communicate the placement puzzle. The
    # central dead gap intentionally has no bridge, beam, or fake route.
    for pair_index, (start, end) in enumerate(((centers[0], centers[1]), (centers[2], centers[3]))):
        points = []
        for amount in np.linspace(0.0, 1.0, 25):
            x = start[0] + (end[0] - start[0]) * amount
            z = start[1] + (end[1] - start[1]) * amount
            lift = 8.8 + math.sin(amount * math.pi) * 0.45
            points.append((x, z, float(height_at(x, z)) + lift))
        objects.append(claim.add_curve(f"RenderHelperRelayValley.LOS.{pair_index}", points, 0.075, materials["mask"]))

    # Broken trench furniture gives the ridge chain a working frontier scale
    # without adding player-buildable machinery to the terrain export.
    for index, (x, z, yaw) in enumerate(((-35.0, 30.5, -0.08), (35.0, 30.5, 0.11), (-54.0, 28.0, -0.22), (54.0, 27.0, 0.25))):
        ground = float(height_at(x, z))
        objects.append(claim.add_box_game(f"RenderHelperRelayValley.CableCrate.{index}", x, z, ground + 0.06, (2.2, 1.25, 0.85), materials["wood"], yaw=yaw, bevel=0.05))
        objects.append(claim.add_beam(f"RenderHelperRelayValley.CableCrate.{index}.Brace", (x - 0.9, z, ground + 0.18), (x + 0.8, z, ground + 0.72), 0.14, materials["brass"]))
    return objects


def add_echo_canyon_preview(height_at, materials):
    """Verdict-only scale cues at the canonical mount records."""
    objects = []
    mounts = {mount["id"]: mount for mount in LANDMARK_MOUNTS["echo-canyon"]}
    for gate_id in ("south-broadcast-gate", "north-return-gate"):
        x, _y, z = mounts[gate_id]["position"]
        base = float(height_at(x, z))
        for side, offset in enumerate((-5.2, 5.2)):
            objects.append(claim.add_beam(f"RenderHelperEchoGate.{gate_id}.Post.{side}", (x + offset, z, base), (x + offset, z, base + 5.4), 0.28, materials["timber"]))
        objects.append(claim.add_beam(f"RenderHelperEchoGate.{gate_id}.Lintel", (x - 5.2, z, base + 5.2), (x + 5.2, z, base + 5.2), 0.34, materials["brass"]))
        objects.append(claim.add_curve(
            f"RenderHelperEchoGate.{gate_id}.Signal",
            [(x - 4.0, z, base + 5.75), (x, z, base + 7.0), (x + 4.0, z, base + 5.75)],
            0.12,
            materials["mask"],
        ))

    for array_id in ("west-echo-array", "east-echo-array"):
        x, _y, z = mounts[array_id]["position"]
        base = float(height_at(x, z))
        objects.append(claim.add_box_game(f"RenderHelperEchoArray.{array_id}.Foot", x, z, base, (3.4, 3.4, 0.55), materials["stone"], bevel=0.08))
        objects.append(claim.add_beam(f"RenderHelperEchoArray.{array_id}.Mast", (x, z, base + 0.25), (x, z, base + 7.8), 0.30, materials["iron"]))
        for ring_index, radius in enumerate((1.4, 2.3, 3.2)):
            points = []
            for step in range(25):
                angle = -math.pi * 0.70 + step / 24 * math.pi * 1.40
                points.append((x + math.cos(angle) * radius, z, base + 5.0 + math.sin(angle) * radius))
            objects.append(claim.add_curve(f"RenderHelperEchoArray.{array_id}.Arc.{ring_index}", points, 0.10, materials["mask"]))

    x, _y, z = mounts["mirror-observation-post"]["position"]
    base = float(height_at(x, z))
    objects.append(claim.add_box_game("RenderHelperEchoObservation.Deck", x, z, base, (7.0, 5.2, 0.42), materials["timber"], bevel=0.08))
    objects.append(claim.add_box_game("RenderHelperEchoObservation.Console", x, z, base + 0.32, (3.8, 1.2, 1.8), materials["brass"], bevel=0.10))
    objects.append(claim.add_box_game("RenderHelperEchoObservation.Glass", x, z - 0.72, base + 1.95, (3.2, 0.18, 0.78), materials["mask"], bevel=0.08))
    return objects


def add_mare_claim_preview(height_at, table, materials):
    """Verdict-only E8 context; removed before terrain save and export."""
    objects = []
    dome_path = ROOT / "assets/pilots/dome-commons-3d/dome-commons-plate.glb"
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(dome_path))
    imported = [obj for obj in bpy.data.objects if obj not in before]
    root = bpy.data.objects.new("RenderHelperMareClaim.DomeCommons", None)
    bpy.context.collection.objects.link(root)
    for index, obj in enumerate(imported):
        obj.name = f"RenderHelperMareClaim.DomeCommons.{index}.{obj.name}"
        obj.parent = root
    root.location = (0.0, 0.0, float(height_at(0.0, 0.0)))
    root.rotation_euler[2] = 0.06
    root.scale = (0.52, 0.52, 0.52)
    objects.extend([root, *imported])

    rail = table["maskTruth"]["rails"][0]["points"]
    for side_index, offset_z in enumerate((-0.62, 0.62)):
        for index, (start, end) in enumerate(zip(rail, rail[1:])):
            start_height = float(height_at(start["x"], start["z"] + offset_z)) + 0.28
            end_height = float(height_at(end["x"], end["z"] + offset_z)) + 0.28
            objects.append(claim.add_beam(
                f"RenderHelperMareClaim.MassDriver.Rail{side_index}.{index}",
                (start["x"], start["z"] + offset_z, start_height),
                (end["x"], end["z"] + offset_z, end_height),
                0.24,
                materials["brass"],
            ))
    for sleeper_index, sleeper_x in enumerate(np.linspace(rail[0]["x"], rail[-1]["x"], 15)):
        ground = float(height_at(float(sleeper_x), -34.0))
        objects.append(claim.add_box_game(
            f"RenderHelperMareClaim.MassDriver.Sleeper{sleeper_index}",
            float(sleeper_x), -34.0, ground + 0.05,
            (0.42, 2.05, 0.22), materials["iron"], bevel=0.035,
        ))
    for index, point in enumerate(rail):
        ground = float(height_at(point["x"], point["z"]))
        objects.append(claim.add_box_game(
            f"RenderHelperMareClaim.MassDriverFoot.{index}",
            point["x"], point["z"], ground + 0.04,
            (1.35, 1.05, 0.28), materials["iron"], bevel=0.04,
        ))

    launch_x, launch_z = -30.0, -31.0
    launch_ground = float(height_at(launch_x, launch_z))
    launch_ring = []
    for index in range(49):
        angle = index / 48.0 * math.tau
        launch_ring.append((launch_x + math.cos(angle) * 7.0, launch_z + math.sin(angle) * 6.1, launch_ground + 0.22))
    objects.append(claim.add_curve("RenderHelperMareClaim.LaunchRing", launch_ring, 0.20, materials["brass"]))
    for index, angle in enumerate((0.0, math.pi * 0.5, math.pi, math.pi * 1.5)):
        x = launch_x + math.cos(angle) * 6.2
        z = launch_z + math.sin(angle) * 5.3
        objects.append(claim.add_box_game(
            f"RenderHelperMareClaim.LaunchLamp.{index}", x, z, launch_ground + 0.10,
            (0.34, 0.34, 0.42), materials["warm"], bevel=0.04,
        ))
    return objects


def add_ember_shore_preview(height_at, table, materials):
    """Verdict-only cooled titan and last vent; never terrain or mounts."""
    objects = []
    truth = table["maskTruth"]
    titan = next(zone for zone in truth["buildZones"] if zone["id"] == "cooled-titan-machine-mount")
    tx = (titan["minX"] + titan["maxX"]) * 0.5
    tz = (titan["minZ"] + titan["maxZ"]) * 0.5
    ground = float(height_at(tx, tz))

    objects.append(claim.add_box_game("RenderHelperEmberShore.Titan.Foundation", tx, tz, ground, (18.0, 15.0, 0.62), materials["stone"], bevel=0.12))
    for index, (x, z) in enumerate(((18.0, 27.0), (34.0, 27.0), (18.0, 41.0), (34.0, 41.0))):
        objects.append(claim.add_box_game(f"RenderHelperEmberShore.Titan.Foot.{index}", x, z, ground + 0.20, (2.8, 2.8, 3.4), materials["iron"], bevel=0.16))
        objects.append(claim.add_box_game(f"RenderHelperEmberShore.Titan.FootGlass.{index}", x, z - 1.44, ground + 1.20, (1.05, 0.12, 0.72), materials["mask"], bevel=0.04))
    objects.append(claim.add_box_game("RenderHelperEmberShore.Titan.Body", tx, tz, ground + 3.25, (13.8, 9.8, 4.5), materials["iron"], bevel=0.34))
    objects.append(claim.add_box_game("RenderHelperEmberShore.Titan.Brib", tx, tz - 5.0, ground + 4.10, (9.0, 0.34, 1.4), materials["brass"], bevel=0.10))
    objects.append(claim.add_box_game("RenderHelperEmberShore.Titan.Eye", tx, tz - 5.18, ground + 5.35, (3.2, 0.20, 1.1), materials["mask"], bevel=0.14))
    for rib_index, rib_x in enumerate(np.linspace(tx - 5.2, tx + 5.2, 5)):
        objects.append(claim.add_beam(
            f"RenderHelperEmberShore.Titan.Rib.{rib_index}",
            (float(rib_x), tz - 3.8, ground + 4.6),
            (float(rib_x), tz + 3.8, ground + 6.9 - abs(rib_x - tx) * 0.16),
            0.24,
            materials["brass"],
        ))
    objects.append(claim.add_beam("RenderHelperEmberShore.Titan.Spine", (tx - 5.4, tz, ground + 6.2), (tx + 5.4, tz, ground + 7.2), 0.42, materials["iron"]))
    # A collapsed manipulator crosses the shelf like an archaeological find.
    objects.append(claim.add_beam("RenderHelperEmberShore.Titan.ArmUpper", (tx + 5.4, tz - 1.0, ground + 5.4), (41.0, 22.0, ground + 3.0), 0.62, materials["iron"]))
    objects.append(claim.add_beam("RenderHelperEmberShore.Titan.ArmLower", (41.0, 22.0, ground + 3.0), (46.0, 17.0, float(height_at(46.0, 17.0)) + 0.5), 0.48, materials["brass"]))

    vent = truth["stakeMarkers"][0]
    vx, vz = vent["x"], vent["z"]
    vent_ground = float(height_at(vx, vz))
    objects.append(claim.add_box_game("RenderHelperEmberShore.Vent.Foundation", vx, vz, vent_ground, (5.8, 5.8, 0.48), materials["stone"], bevel=0.10))
    objects.append(claim.add_cylinder_between("RenderHelperEmberShore.Vent.Stack", (vx, vz, vent_ground + 0.18), (vx, vz, vent_ground + 5.8), 1.05, materials["iron"], vertices=12))
    for ring_index, ring_height in enumerate((1.3, 3.0, 4.7)):
        objects.append(claim.add_box_game(f"RenderHelperEmberShore.Vent.Ring.{ring_index}", vx, vz, vent_ground + ring_height, (2.8, 2.8, 0.28), materials["brass"], bevel=0.10))
    objects.append(claim.add_box_game("RenderHelperEmberShore.Vent.Ember", vx, vz - 1.10, vent_ground + 3.2, (0.70, 0.18, 2.6), materials["warm"], bevel=0.08))
    return objects


def ring_points(x, z, radius, height_at, lift=0.88):
    points = []
    for index in range(33):
        angle = index / 32 * math.tau
        px, pz = x + math.cos(angle) * radius, z + math.sin(angle) * radius
        points.append((px, pz, float(height_at(px, pz)) + lift))
    return points


def zone_outline(zone, height_at, lift=0.82, steps=18):
    points = []
    edges = (
        ((zone["minX"], zone["minZ"]), (zone["maxX"], zone["minZ"])),
        ((zone["maxX"], zone["minZ"]), (zone["maxX"], zone["maxZ"])),
        ((zone["maxX"], zone["maxZ"]), (zone["minX"], zone["maxZ"])),
        ((zone["minX"], zone["maxZ"]), (zone["minX"], zone["minZ"])),
    )
    for edge_index, (start, end) in enumerate(edges):
        for step in range(steps + 1):
            if edge_index and step == 0:
                continue
            amount = step / steps
            x = start[0] + (end[0] - start[0]) * amount
            z = start[1] + (end[1] - start[1]) * amount
            points.append((x, z, float(height_at(x, z)) + lift))
    return points


def add_mask_overlay(key, table, height_at, materials):
    objects = []
    truth = table["maskTruth"]
    for zone in truth["buildZones"]:
        objects.append(claim.add_curve(f"RenderHelperBuildZone.{zone['id']}", zone_outline(zone, height_at), 0.24, materials["mask"]))
        for stripe_index, stripe_z in enumerate(np.linspace(zone["minZ"] + 2.0, zone["maxZ"] - 2.0, 5)):
            points = []
            for x in np.linspace(zone["minX"] + 1.0, zone["maxX"] - 1.0, 25):
                points.append((float(x), float(stripe_z), float(height_at(float(x), float(stripe_z))) + 0.76))
            objects.append(claim.add_curve(f"RenderHelperBuildZone.{zone['id']}.Hatch.{stripe_index}", points, 0.07, materials["maskfill"]))
    for marker in truth.get("stakeMarkers", []):
        objects.append(claim.add_box_game(f"RenderHelperStake.{marker['id']}", marker["x"], marker["z"], float(height_at(marker["x"], marker["z"])), (1.0, 1.0, 2.2), materials["danger"], bevel=0.04))
    for site in truth.get("pylonSites", []):
        objects.append(claim.add_curve(f"RenderHelperPylonSite.{site['id']}", ring_points(site["x"], site["z"], site["radius"], height_at), 0.28, materials["danger"]))
        center_height = float(height_at(site["x"], site["z"])) + 0.92
        objects.append(claim.add_curve(f"RenderHelperPylonSite.{site['id']}.CrossX", [(site["x"] - 0.8, site["z"], center_height), (site["x"] + 0.8, site["z"], center_height)], 0.18, materials["danger"]))
        objects.append(claim.add_curve(f"RenderHelperPylonSite.{site['id']}.CrossZ", [(site["x"], site["z"] - 0.8, center_height), (site["x"], site["z"] + 0.8, center_height)], 0.18, materials["danger"]))
    for site in truth.get("capacitorSites", []):
        objects.append(claim.add_curve(f"RenderHelperCapacitorSite.{site['id']}", ring_points(site["x"], site["z"], site["radius"], height_at), 0.28, materials["warm"]))
        center_height = float(height_at(site["x"], site["z"])) + 0.92
        objects.append(claim.add_curve(f"RenderHelperCapacitorSite.{site['id']}.CrossX", [(site["x"] - 0.8, site["z"], center_height), (site["x"] + 0.8, site["z"], center_height)], 0.18, materials["warm"]))
        objects.append(claim.add_curve(f"RenderHelperCapacitorSite.{site['id']}.CrossZ", [(site["x"], site["z"] - 0.8, center_height), (site["x"], site["z"] + 0.8, center_height)], 0.18, materials["warm"]))
    for fixture in truth.get("fixtureZones", []):
        center_x = (fixture["minX"] + fixture["maxX"]) * 0.5
        center_z = (fixture["minZ"] + fixture["maxZ"]) * 0.5
        fixture_height = float(height_at(center_x, center_z))
        objects.append(claim.add_box_game(f"RenderHelperFixture.{fixture['id']}.Fill", center_x, center_z, fixture_height + 0.72, (fixture["maxX"] - fixture["minX"], fixture["maxZ"] - fixture["minZ"], 0.08), materials["warm"], bevel=0.02))
        objects.append(claim.add_curve(f"RenderHelperFixture.{fixture['id']}", zone_outline(fixture, height_at, lift=0.88, steps=16), 0.28, materials["warm"]))
        lift = fixture_height + 0.92
        objects.append(claim.add_curve(f"RenderHelperFixture.{fixture['id']}.X1", [(fixture["minX"], fixture["minZ"], lift), (fixture["maxX"], fixture["maxZ"], lift)], 0.18, materials["warm"]))
        objects.append(claim.add_curve(f"RenderHelperFixture.{fixture['id']}.X2", [(fixture["minX"], fixture["maxZ"], lift), (fixture["maxX"], fixture["minZ"], lift)], 0.18, materials["warm"]))
    if key == "canyon-works":
        for z in (-SHALLOWS_HALF_WIDTH, SHALLOWS_HALF_WIDTH):
            points = [(float(x), z, float(height_at(float(x), z)) + 0.78) for x in np.linspace(-48, 48, 49)]
            objects.append(claim.add_curve(f"RenderHelperWaterBank.{z}", points, 0.13, materials["mask"]))
    elif key == "blackout-ridge":
        trunk_points = [(-40.0, -40.0)] + [(site["x"], site["z"]) for site in truth["pylonSites"]] + [(24.0, 30.0)]
        objects.append(claim.add_curve("RenderHelperBlackoutTrunk", [(x, z, float(height_at(x, z)) + 0.70) for x, z in trunk_points], 0.14, materials["flow"]))
    elif key == "dust-flats":
        for road in truth["roadCorridors"]:
            points = []
            for amount in np.linspace(0.0, 1.0, 33):
                x = road["start"]["x"] + (road["end"]["x"] - road["start"]["x"]) * amount
                z = road["start"]["z"] + (road["end"]["z"] - road["start"]["z"]) * amount
                points.append((x, z, float(height_at(x, z)) + 0.76))
            objects.append(claim.add_curve(f"RenderHelperRoad.{road['id']}", points, 0.16, materials["danger"]))
        orbit = truth["orbitSpawn"]
        objects.append(claim.add_curve("RenderHelperOrbitRoad", ring_points(orbit["center"]["x"], orbit["center"]["z"], orbit["radius"], height_at, 0.78), 0.20, materials["danger"]))
        for seam in truth["tarSeams"]:
            objects.append(claim.add_curve(f"RenderHelperTar.{seam['id']}", ring_points(seam["x"], seam["z"], seam["radius"], height_at, 0.80), 0.16, materials["warm"]))
    elif key == "glow-mesa":
        for field in truth["decayFields"]:
            objects.append(claim.add_curve(f"RenderHelperDecay.{field['id']}", zone_outline(field, height_at, lift=0.86, steps=18), 0.20, materials["danger"]))
        for path in truth["herdPaths"]:
            objects.append(claim.add_curve(f"RenderHelperHerdPath.{path['id']}", zone_outline(path, height_at, lift=0.82, steps=18), 0.18, materials["flow"]))
        for index, anchor in enumerate(truth["harvestAnchors"]):
            objects.append(claim.add_curve(f"RenderHelperStarstone.{index}", ring_points(anchor["x"], anchor["z"], 1.25, height_at, 0.84), 0.20, materials["warm"]))
    elif key == "echo-canyon":
        for band in truth["echoCanyonBands"]:
            objects.append(claim.add_curve(f"RenderHelperEchoBand.{band['id']}", zone_outline(band, height_at, lift=0.92, steps=28), 0.18, materials["flow"]))
        field = truth["broadcastMirrorZones"][0]
        objects.append(claim.add_curve(f"RenderHelperBroadcastField.{field['id']}", zone_outline(field, height_at, lift=1.00, steps=32), 0.22, materials["danger"]))
    elif key == "relay-valley":
        for ridge in truth["ridgeBands"]:
            objects.append(claim.add_curve(f"RenderHelperRelayRidge.{ridge['id']}", zone_outline(ridge, height_at, lift=0.90, steps=24), 0.17, materials["flow"]))
        for pocket in truth["fogPockets"]:
            objects.append(claim.add_curve(f"RenderHelperFogPocket.{pocket['id']}", zone_outline(pocket, height_at, lift=0.94, steps=24), 0.22, materials["danger"]))
        patrol = truth["lanes"]["patrolRoutes"][0]
        objects.append(claim.add_curve(
            f"RenderHelperPatrol.{patrol['id']}",
            [(point["x"], point["z"], float(height_at(point["x"], point["z"])) + 0.82) for point in patrol["points"]],
            0.18,
            materials["warm"],
        ))
        centers = [
            ((zone["minX"] + zone["maxX"]) * 0.5, (zone["minZ"] + zone["maxZ"]) * 0.5)
            for zone in truth["buildZones"]
        ]
        for index, (start, end) in enumerate(((centers[0], centers[1]), (centers[2], centers[3]))):
            objects.append(claim.add_curve(
                f"RenderHelperLOSAgreement.{index}",
                [(start[0], start[1], float(height_at(*start)) + 1.10), (end[0], end[1], float(height_at(*end)) + 1.10)],
                0.15,
                materials["mask"],
            ))
    elif key == "mare-claim":
        for band in truth["rimBands"]:
            objects.append(claim.add_curve(f"RenderHelperMareRim.{band['id']}", zone_outline(band, height_at, lift=0.96, steps=28), 0.18, materials["flow"]))
        mare = truth["mareFlat"]
        objects.append(claim.add_curve(f"RenderHelperMareFlat.{mare['id']}", zone_outline(mare, height_at, lift=0.82, steps=26), 0.15, materials["maskfill"]))
        mouth = truth["lavaTubeMouth"]
        objects.append(claim.add_curve(f"RenderHelperMareMouth.{mouth['id']}", zone_outline(mouth, height_at, lift=0.92, steps=20), 0.24, materials["danger"]))
        for rail_index, rail in enumerate(truth["rails"]):
            objects.append(claim.add_curve(
                f"RenderHelperMareRail.{rail_index}",
                [(point["x"], point["z"], float(height_at(point["x"], point["z"])) + 0.86) for point in rail["points"]],
                0.18,
                materials["warm"],
            ))
        for index, anchor in enumerate(truth["harvestAnchors"]):
            objects.append(claim.add_curve(f"RenderHelperMareHarvest.{index}", ring_points(anchor["x"], anchor["z"], 1.5, height_at, 0.86), 0.18, materials["mask"]))
        for lane in truth["debrisArcLanes"]:
            objects.append(claim.add_curve(
                f"RenderHelperMareDebris.{lane['id']}",
                [(point["x"], point["z"], float(height_at(point["x"], point["z"])) + 0.88) for point in lane["points"]],
                0.18,
                materials["danger"],
            ))
    elif key == "ember-shore":
        for band in truth["lavaVeinBands"]:
            objects.append(claim.add_curve(f"RenderHelperEmberVein.{band['id']}", zone_outline(band, height_at, lift=0.94, steps=28), 0.22, materials["danger"]))
        spawn_edges = truth["lanes"]["spawnEdges"]
        edge_specs = {
            "north": [(-64.0, 60.0), (64.0, 60.0)],
            "west": [(-60.0, -64.0), (-60.0, 64.0)],
            "east": [(60.0, -64.0), (60.0, 64.0)],
        }
        for edge in spawn_edges:
            start, end = edge_specs[edge]
            points = []
            for amount in np.linspace(0.0, 1.0, 33):
                x = start[0] + (end[0] - start[0]) * amount
                z = start[1] + (end[1] - start[1]) * amount
                points.append((x, z, float(height_at(x, z)) + 0.92))
            objects.append(claim.add_curve(f"RenderHelperEmberSpawnEdge.{edge}", points, 0.16, materials["flow"]))
    return objects


def add_night_lighting(key, table, height_at):
    if key == "dust-flats":
        return claim.add_lighting(sunset=False)
    if key == "ember-shore":
        world = bpy.data.worlds.new("ember-shore-InkWorld")
        bpy.context.scene.world = world
        world.use_nodes = True
        background = world.node_tree.nodes.get("Background")
        background.inputs["Color"].default_value = (0.005, 0.009, 0.012, 1.0)
        background.inputs["Strength"].default_value = 0.22
        sun_data = bpy.data.lights.new("ember-shore-ParchmentRake", "SUN")
        sun_data.energy = 3.05
        sun_data.color = (0.72, 0.55, 0.35)
        sun_data.angle = math.radians(9)
        sun = bpy.data.objects.new("ember-shore-ParchmentRake", sun_data)
        bpy.context.collection.objects.link(sun)
        sun.location = (-42.0, -28.0, 52.0)
        claim.aim_at(sun, (0.0, 0.0, 0.0))
        lights = [sun]
        fill_data = bpy.data.lights.new("ember-shore-TealFill", "AREA")
        fill_data.energy = 440
        fill_data.color = (0.08, 0.28, 0.30)
        fill_data.shape = "DISK"
        fill_data.size = 38.0
        fill = bpy.data.objects.new("ember-shore-TealFill", fill_data)
        bpy.context.collection.objects.link(fill)
        fill.location = (36.0, 38.0, 24.0)
        claim.aim_at(fill, (18.0, 10.0, 1.0))
        lights.append(fill)
        for index, (x, z, energy, color) in enumerate((
            (3.0, -10.0, 1750, (1.0, 0.30, 0.035)),
            (-46.0, -16.0, 520, (1.0, 0.18, 0.025)),
            (-13.0, -28.0, 460, (1.0, 0.16, 0.020)),
            (49.0, 13.0, 480, (1.0, 0.18, 0.024)),
            (26.0, 34.0, 360, (0.08, 0.72, 0.70)),
        )):
            data = bpy.data.lights.new(f"ember-shore-Work.{index}", "POINT")
            data.energy = energy
            data.color = color
            data.shadow_soft_size = 1.8 if index == 0 else 2.8
            light = bpy.data.objects.new(f"ember-shore-Work.{index}", data)
            bpy.context.collection.objects.link(light)
            light.location = (x, -z, float(height_at(x, z)) + (4.2 if index in {0, 4} else 1.8))
            lights.append(light)
        return lights
    world = bpy.data.worlds.new(f"{key}DuskWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (
        (0.025, 0.045, 0.085, 1.0)
        if key == "blackout-ridge"
        else ((0.012, 0.028, 0.038, 1.0) if key == "glow-mesa" else ((0.018, 0.034, 0.040, 1.0) if key in {"relay-valley", "echo-canyon"} else ((0.006, 0.007, 0.010, 1.0) if key == "mare-claim" else (0.008, 0.014, 0.030, 1.0))))
    )
    background.inputs["Strength"].default_value = {"canyon-works": 0.48, "moth-season": 0.42, "blackout-ridge": 0.65, "fairground": 0.50, "glow-mesa": 0.30, "relay-valley": 0.42, "echo-canyon": 0.40, "mare-claim": 0.18}[key]

    moon_data = bpy.data.lights.new(f"{key}Moon", "SUN")
    # This is a legibility rig, not daylight: enough cool raking light to keep
    # the engraved terrain readable while the warm work lamps own the scene.
    moon_data.energy = {"canyon-works": 2.70, "moth-season": 2.30, "blackout-ridge": 3.20, "fairground": 2.55, "glow-mesa": 2.45, "relay-valley": 2.85, "echo-canyon": 2.95, "mare-claim": 2.55}[key]
    moon_data.color = (0.44, 0.55, 0.60) if key == "glow-mesa" else ((0.60, 0.56, 0.46) if key in {"relay-valley", "echo-canyon"} else ((0.72, 0.70, 0.62) if key == "mare-claim" else (0.28, 0.44, 0.68)))
    moon_data.angle = math.radians(6 if key == "mare-claim" else (10 if key in {"relay-valley", "echo-canyon"} else (8 if key == "glow-mesa" else 18)))
    if key == "fairground":
        moon_data.use_shadow = False
    moon = bpy.data.objects.new(f"{key}Moon", moon_data)
    bpy.context.collection.objects.link(moon)
    moon.location = (-35, -20, 48)
    claim.aim_at(moon, (0, 0, 0))
    lights = [moon]

    fill_data = bpy.data.lights.new(f"{key}ColdFaceFill", "AREA")
    fill_data.energy = {"canyon-works": 650, "moth-season": 550, "blackout-ridge": 900, "fairground": 720, "glow-mesa": 360, "relay-valley": 520, "echo-canyon": 560, "mare-claim": 280}[key]
    fill_data.color = (0.10, 0.22, 0.28) if key == "glow-mesa" else ((0.13, 0.29, 0.28) if key in {"relay-valley", "echo-canyon"} else ((0.18, 0.34, 0.33) if key == "mare-claim" else (0.20, 0.31, 0.48)))
    fill_data.shape = "DISK"
    fill_data.size = 34.0
    if key == "fairground":
        fill_data.use_shadow = False
    fill = bpy.data.objects.new(f"{key}ColdFaceFill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = (0.0, 38.0, 19.0)
    claim.aim_at(fill, (0.0, 0.0, 0.5))
    lights.append(fill)

    positions = {
        "canyon-works": [(-32, 32), (32, 32)],
        "moth-season": [(-22, -10), (17, 9)],
        "blackout-ridge": [(12, 20), (24, 30)],
        "fairground": [(-20, 10), (0, 8), (20, 10)],
        "glow-mesa": [(-24, 18), (-14, 34), (4, 38), (24, 30), (26, 10), (4, 2), (0, -32)],
        "relay-valley": [(-45, 41), (-25, 41), (25, 41), (45, 41), (-24, -20), (24, -20)],
        "echo-canyon": [(-43, 8), (43, -4), (0, -50), (0, 23), (0, 50)],
        "mare-claim": [(-18, 0), (0, 0), (18, 0), (-30, -31), (16, -34), (46, -34)],
    }[key]
    for index, (x, z) in enumerate(positions):
        data = bpy.data.lights.new(f"{key}Lantern.{index}", "POINT")
        data.energy = {"canyon-works": 1550, "moth-season": 1320, "blackout-ridge": 1120, "fairground": 1580, "glow-mesa": (340 if index < 6 else 760), "relay-valley": (460 if index < 4 else 720), "echo-canyon": (520 if index < 2 else 760), "mare-claim": (440 if index < 4 else 260)}[key]
        data.color = (0.10, 0.82, 0.76) if (key == "glow-mesa" and index < 6) or (key == "relay-valley" and index < 4) or (key == "echo-canyon" and index < 2) or (key == "mare-claim" and index >= 4) else ((1.0, 0.62, 0.20) if key == "mare-claim" else ((1.0, 0.50, 0.13) if key in {"relay-valley", "echo-canyon"} else (1.0, 0.34, 0.075)))
        data.shadow_soft_size = 0.8 if key == "mare-claim" else (1.0 if key in {"glow-mesa", "relay-valley", "echo-canyon"} else (2.8 if key == "blackout-ridge" else 4.8))
        if key == "fairground":
            data.use_shadow = False
        light = bpy.data.objects.new(f"{key}Lantern.{index}", data)
        bpy.context.collection.objects.link(light)
        lift = (7.4 if (x, z) == (0, 8) else 6.4) if key == "fairground" else (3.4 if key == "mare-claim" and index < 3 else (2.4 if key == "mare-claim" else (4.2 if key in {"relay-valley", "echo-canyon"} and index < 4 else (2.8 if key in {"glow-mesa", "relay-valley", "echo-canyon"} else 2.2))))
        light.location = (x, -z, float(height_at(x, z)) + lift)
        lights.append(light)
    return lights


def render_verdicts(key, profile, factory, table, terrain, water, preview, overlay):
    backdrop = claim.make_backdrop()
    if key == "dust-flats":
        backdrop.location.z = -2.5
    # The evidence rig needs the same dusk-coloured ground continuation the
    # runtime supplies outside the playfield.  A warm default plane would read
    # as a literal painted strip between terrain and panorama.
    backdrop_nodes = backdrop.active_material.node_tree.nodes
    backdrop_nodes.clear()
    backdrop_output = backdrop_nodes.new("ShaderNodeOutputMaterial")
    backdrop_shader = backdrop_nodes.new("ShaderNodeBackground")
    backdrop_shader.inputs["Color"].default_value = (0.055, 0.033, 0.012, 1.0) if key == "dust-flats" else ((0.025, 0.022, 0.016, 1.0) if key in {"relay-valley", "echo-canyon"} else ((0.014, 0.014, 0.013, 1.0) if key == "mare-claim" else ((0.010, 0.007, 0.006, 1.0) if key == "ember-shore" else (0.004, 0.007, 0.012, 1.0))))
    backdrop_shader.inputs["Strength"].default_value = 1.0
    backdrop.active_material.node_tree.links.new(backdrop_shader.outputs["Background"], backdrop_output.inputs["Surface"])
    panorama = claim.link_panorama(key)
    for obj in panorama:
        obj.hide_render = True
    camera_profiles = {
        "canyon-works": ((0.0, 34.0, 27.0), (0.0, -6.0, 0.6), (0.0, 70.0, 74.0), (-30.0, 28.0, 13.5), 118.0, (-51.0, 108.0, 8.0), 42.0),
        "moth-season": ((0.0, 34.0, 27.0), (0.0, 0.0, 0.6), (0.0, 70.0, 74.0), (-30.0, 28.0, 13.5), 118.0, (-58.0, -108.0, 8.0), 42.0),
        "blackout-ridge": ((0.0, 42.0, 32.0), (4.0, 2.0, 1.2), (0.0, 78.0, 80.0), (-34.0, 36.0, 15.0), 132.0, (82.0, -112.0, 3.4), 44.0),
        "dust-flats": ((0.0, 61.0, 49.0), (0.0, 0.0, 0.4), (0.0, 112.0, 124.0), (-58.0, 62.0, 22.0), 192.0, (-118.0, 132.0, 10.0), 48.0),
        "fairground": ((0.0, 37.0, 29.0), (0.0, -1.0, 0.8), (0.0, 72.0, 76.0), (-33.0, 31.0, 14.0), 118.0, (-72.0, 112.0, 7.0), 43.0),
        "glow-mesa": ((0.0, 50.0, 39.0), (0.0, -4.0, 2.0), (0.0, 96.0, 102.0), (-46.0, 54.0, 17.0), 156.0, (12.0, 172.0, 6.4), 46.0),
        "relay-valley": ((0.0, 53.0, 40.0), (0.0, -13.0, 2.2), (0.0, 98.0, 104.0), (-48.0, 58.0, 18.0), 156.0, (0.0, -172.0, 8.0), 46.0),
        "echo-canyon": ((0.0, 55.0, 42.0), (0.0, -10.0, 1.8), (0.0, 100.0, 106.0), (-52.0, 60.0, 20.0), 156.0, (0.0, -174.0, 7.0), 46.0),
        "mare-claim": ((0.0, 69.0, 49.0), (0.0, -7.0, 1.8), (0.0, 100.0, 106.0), (-54.0, 70.0, 24.0), 156.0, (45.0, -172.0, 3.2), 54.0),
        "ember-shore": ((0.0, 68.0, 48.0), (2.0, -5.0, 0.8), (0.0, 103.0, 109.0), (-56.0, 69.0, 21.0), 156.0, (-139.0, -115.0, 8.0), 52.0),
    }
    run_location, run_target, overview_location, low_location, top_height, horizon_target, run_fov = camera_profiles[key]
    run = claim.add_camera(f"{profile['object']}RunCamera", run_location, run_target, run_fov)
    overview = claim.add_camera(f"{profile['object']}Overview", overview_location, (0.0, 0.0, 1.0), 47.0)
    low = claim.add_camera(f"{profile['object']}Low", low_location, (0.0, -4.0, 1.2), 56.0 if key == "mare-claim" else 48.0)
    top = claim.add_camera(f"{profile['object']}Mask", (0.0, 0.0, top_height), (0.0, 0.0, 0.0), 52.0)
    horizon_location = (0.0, 0.0, 7.2) if key == "glow-mesa" else ((0.0, 0.0, 16.0) if key == "mare-claim" else ((0.0, 0.0, 5.0) if key == "ember-shore" else ((0.0, 0.0, 3.8) if key in {"relay-valley", "echo-canyon"} else (0.0, 0.0, 3.2))))
    horizon = claim.add_camera(f"{profile['object']}Horizon", horizon_location, horizon_target, 52.0)
    far_side = claim.add_camera(f"{profile['object']}FarSide", horizon_location, (-45.0, 172.0, 3.2), 52.0) if key == "mare-claim" else None
    for camera in (run, overview, low, top, horizon, far_side):
        if camera is None:
            continue
        camera.data.clip_end = 420.0

    lights = add_night_lighting(key, table, claim.terrain_height)
    bpy.context.scene.view_settings.exposure = 0.45 if key == "dust-flats" else (1.55 if key == "blackout-ridge" else (1.38 if key == "fairground" else (0.88 if key == "glow-mesa" else (1.05 if key in {"relay-valley", "echo-canyon"} else (1.12 if key == "mare-claim" else (1.08 if key == "ember-shore" else 1.25))))))
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
    claim.render(run, ARTIFACTS / f"{key}-run-camera.png")
    claim.render(overview, ARTIFACTS / f"{key}-overview.png")
    for obj in overlay:
        obj.hide_render = False
    claim.render(top, ARTIFACTS / f"{key}-mask-agreement.png")
    for obj in overlay:
        obj.hide_render = True

    low_hidden = [obj for obj in preview if key == "glow-mesa" and "DecayClock" in obj.name]
    for obj in low_hidden:
        obj.hide_render = True
    claim.render(low, ARTIFACTS / f"{key}-panorama-before.png")
    backdrop.hide_render = True
    for obj in panorama:
        obj.hide_render = False
    claim.render(run, ARTIFACTS / f"{key}-run-camera.png")
    claim.render(overview, ARTIFACTS / f"{key}-overview.png")
    claim.render(low, ARTIFACTS / f"{key}-low-sunset.png")
    claim.render(low, ARTIFACTS / f"{key}-panorama-mounted.png")
    for obj in low_hidden:
        obj.hide_render = False
    if key in {"glow-mesa", "mare-claim", "ember-shore"}:
        for obj in preview:
            obj.hide_render = True
    claim.render(horizon, ARTIFACTS / f"{key}-panorama-horizon.png")
    if far_side is not None:
        claim.render(far_side, ARTIFACTS / f"{key}-panorama-far-side.png")
    bpy.context.scene.view_settings.exposure = 0.0
    claim.remove_objects(lights + [run, overview, low, top, horizon] + ([far_side] if far_side else []) + [backdrop] + panorama)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def site_flatness(table, height_at, field):
    results = []
    for site in table["maskTruth"].get(field, []):
        samples = []
        for angle in np.linspace(0.0, math.tau, 24, endpoint=False):
            for radius in (0.0, site["radius"] * 0.45, site["radius"] * 0.88):
                samples.append(float(height_at(site["x"] + math.cos(angle) * radius, site["z"] + math.sin(angle) * radius)))
        results.append({"id": site["id"], "position": [site["x"], site["z"]], "radius": site["radius"], "maxDeviationMeters": round(max(samples) - min(samples), 6)})
    return results


def fixture_flatness(table, height_at):
    results = []
    for zone in table["maskTruth"].get("fixtureZones", []):
        samples = [
            float(height_at(x, z))
            for x in np.linspace(zone["minX"], zone["maxX"], 33)
            for z in np.linspace(zone["minZ"], zone["maxZ"], 17)
        ]
        results.append({
            "id": zone["id"],
            "bounds": [zone["minX"], zone["maxX"], zone["minZ"], zone["maxZ"]],
            "sampledSurfacePoints": len(samples),
            "maxDeviationMeters": round(max(samples) - min(samples), 6),
        })
    return results


def build_zone_flatness(table, height_at):
    results = []
    for zone in table["maskTruth"].get("buildZones", []):
        samples = [
            float(height_at(x, z))
            for x in np.linspace(zone["minX"], zone["maxX"], 49)
            for z in np.linspace(zone["minZ"], zone["maxZ"], 25)
        ]
        results.append({
            "id": zone["id"],
            "bounds": [zone["minX"], zone["maxX"], zone["minZ"], zone["maxZ"]],
            "sampledSurfacePoints": len(samples),
            "maxDeviationMeters": round(max(samples) - min(samples), 6),
        })
    return results


def make_contract(key, profile, table, table_path, terrain, atlas_path, height_at):
    coords = np.asarray([vertex.co[:] for vertex in terrain.data.vertices], dtype=np.float32)
    triangles = sum(len(poly.vertices) - 2 for poly in terrain.data.polygons)
    unique_composition = {
        "dust-flats": "motor-road composition",
        "fairground": "wheel-bowl composition",
        "glow-mesa": "two-level caprock and herd-path composition",
        "relay-valley": "split relay ridges, exact LOS pairs, and named dead-zone composition",
        "echo-canyon": "opposed h5 echo shelves, one long h0 broadcast floor, and open north/south combat mouths",
        "mare-claim": "crater-rim, lava-mouth, landing-scorch, and mass-driver composition",
        "ember-shore": "three cooled hazard rifts, last-warm-vent preserve footing, and archaeological titan shelf composition",
    }.get(key, "night-light composition")
    return {
        "asset": f"{profile['stem']}.glb",
        "contractId": profile["contractId"],
        "tileId": table["maskTruth"]["tileId"],
        "renderOnly": True,
        "simulation": "planar masks, movement, collision, spawns, placement, and combat remain unchanged",
        "heightSocket": "Terrain.visualY",
        "theme": profile["theme"],
        "regionalFamily": {
            "epoch": profile["epoch"],
            "shared": profile["shared"],
            "unique": ["authored terrain silhouette", "mask rhythm", unique_composition, "panorama profile"],
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
        "pylonSiteFlatness": site_flatness(table, height_at, "pylonSites"),
        "capacitorSiteFlatness": site_flatness(table, height_at, "capacitorSites"),
        "fixtureZoneFlatness": fixture_flatness(table, height_at),
        "buildZoneFlatness": build_zone_flatness(table, height_at) if key in {"glow-mesa", "relay-valley", "echo-canyon", "mare-claim", "ember-shore"} else [],
        "pylonFlatnessLimitMeters": 0.02,
        "fixtureFlatnessLimitMeters": 0.02,
        "landmarkFreeze": "lifted; canonical empty-asset mounts ship with the campaign sculpt" if key == "echo-canyon" else ("lifted; no landmark assets or mounts authored in this terrain/panorama wave" if key in {"fairground", "glow-mesa", "relay-valley", "ember-shore"} else "no landmark assets or mounts authored in this wave"),
        "landmarkMounts": LANDMARK_MOUNTS.get(key, []),
        "landmarkMountSpace": {
            "coordinates": "game X/Y/Z",
            "positionY": "local offset added to Terrain.visualY at the mount X/Z",
            "rotation": "XYZ Euler radians",
            "scale": "XYZ multiplier",
            "ownership": "landmark assets mount at runtime and are never baked into terrain",
        } if key == "echo-canyon" else None,
        "verdictPreviewOnly": {
            "assets": [
                "assets/pilots/isotope-kitchen-3d/isotope-kitchen.glb",
                "assets/pilots/decay-clock-3d/decay-clock.glb",
                "assets/pilots/catalog-warehouse-3d/catalog-warehouse.glb",
                "assets/pilots/run3d/turret.e6.glb",
            ],
            "excludedFromBlendAndGlb": True,
            "reason": "existing E6 fixture and gameplay bodies establish scale and combat pressure without inventing landmark mounts or spawn authority",
        } if key == "glow-mesa" else ({
            "assets": ["assets/pilots/relay-tower-3d/relay-tower.glb"],
            "excludedFromBlendAndGlb": True,
            "reason": "existing relay tower bodies establish the exact four-pad LOS puzzle without authoring runtime mounts or placement authority",
        } if key == "relay-valley" else ({
            "assets": ["procedural verdict-only echo gates", "procedural verdict-only broadcast arrays", "procedural verdict-only observation post"],
            "excludedFromBlendAndGlb": True,
            "reason": "mount-aligned scale cues establish the long broadcast canyon without baking landmark bodies or mirror gameplay into the terrain",
        } if key == "echo-canyon" else ({
            "assets": ["assets/pilots/dome-commons-3d/dome-commons-plate.glb"],
            "excludedFromBlendAndGlb": True,
            "reason": "the existing E8 dome body and procedural launch/rail cues establish lunar scale without authoring landmark mounts, collision, or placement authority",
        } if key == "mare-claim" else ({
            "assets": ["procedural verdict-only cooled titan machine", "procedural verdict-only last-warm-vent fixture"],
            "excludedFromBlendAndGlb": True,
            "reason": "procedural scale cues demonstrate the two authored preserve sites without inventing a shipped landmark body, mount, collision, or placement authority",
        } if key == "ember-shore" else None)))),
        "preserveDesign": {
            "terrain": "one dry authored terrain mesh; planar simulation and mask authority remain code-owned",
            "coolingBands": "three mask-exact lava-vein rectangles sculpted as cooled landform rifts",
            "water": "none authored, rendered, or implied",
            "static": "code-owned staged desaturation/muting remains a runtime state and is not baked into the terrain",
            "sites": "last-warm-vent and cooled-titan machine footprints are triangle-safe and buildable-flat",
        } if key == "ember-shore" else None,
        "panoramaMount": claim.panorama_mount(key),
        "evidenceRig": "sun-hazed motor daylight" if key == "dust-flats" else ("teal starstone dusk with one amber kitchen anchor; all lights render-only" if key == "glow-mesa" else ("blue-hour signal dusk with honey work lamps and agent-teal broadcast cues; all lights render-only" if key == "echo-canyon" else ("blue-hour signal dusk with honey work lamps and agent-teal relay cues; all lights render-only" if key == "relay-valley" else ("vacuum-black orbital raking light with honey habitat warmth and restrained agent teal; all lights render-only" if key == "mare-claim" else ("deep-ink first-world night with parchment-gold vent warmth and restrained agent teal; all lights render-only" if key == "ember-shore" else "dusk/deep shadow with code-owned lamp positions represented by render-only warm lights"))))),
        "sourceArt": list(dict.fromkeys(str(path.relative_to(ROOT)) for path in ((claim.BANK_C, profile["kit"], profile["sourcePlate"]) if key in {"mare-claim", "ember-shore"} else ((claim.BANK_A, claim.BANK_C, profile["kit"], profile["sourcePlate"]) if key in {"glow-mesa", "relay-valley", "echo-canyon"} else (claim.BANK_A, claim.BANK_C, claim.RIVER, RAIL_PLATE, profile["kit"], profile["sourcePlate"]))))),
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
    print(json.dumps({"asset": glb.name, "triangles": contract["triangles"], "pylonSiteFlatness": contract["pylonSiteFlatness"]}, indent=2))


def build(key):
    profile = PROFILES[key]
    factory = factory_contract(profile["contractId"])
    table, table_path = mask_table(profile["contractId"])
    expected_width = table["maskTruth"].get("dimensions", {}).get("width", table["maskTruth"]["size"])
    expected_height = table["maskTruth"].get("dimensions", {}).get("height", table["maskTruth"]["size"])
    if (profile["width"], profile["height"]) != (expected_width, expected_height):
        raise ValueError(f"{key} authored dimensions changed")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    claim.reset_scene()
    atlas, atlas_path = make_atlas(key, profile, factory, table)
    material = claim.make_material(atlas)
    material.name = profile["material"]
    if key == "echo-canyon":
        # The long exact h5 shelves necessarily expose north/south faces that
        # point away from the dusk key. Preserve the shipped painted texture
        # in those shadow pockets with a restrained self-fill; this is not a
        # glow treatment and does not alter terrain height or sim authority.
        nodes = material.node_tree.nodes
        shader = next(node for node in nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
        texture = next(node for node in nodes if node.bl_idname == "ShaderNodeTexImage")
        emission_color = shader.inputs.get("Emission Color") or shader.inputs.get("Emission")
        emission_strength = shader.inputs.get("Emission Strength")
        if emission_color and emission_strength:
            material.node_tree.links.new(texture.outputs["Color"], emission_color)
            emission_strength.default_value = 0.22
    height_at = height_function(key, factory, table)
    claim.terrain_height = height_at
    terrain = make_terrain(profile, table, table_path, height_at, material)
    water = None
    if table["maskTruth"]["river"]:
        water_material = claim.make_water_material("RenderHelperCanyonWorkingWater", (0.008, 0.010, 0.009), (0.026, 0.040, 0.036), 0.64)
        for node in water_material.node_tree.nodes:
            if node.bl_idname == "ShaderNodeMixRGB":
                node.inputs[2].default_value = (0.050, 0.032, 0.016, 1.0)
        water = make_water(profile, water_material)
    materials = preview_materials(key)
    preview = [] if key == "mare-claim" else (e2.add_rails(key, factory, height_at, materials) if table["maskTruth"].get("rails") else [])
    if key == "canyon-works":
        preview.extend(add_water_engraving(profile, materials))
    if key == "fairground":
        preview.extend(add_fairground_preview(height_at, materials))
    if key == "glow-mesa":
        preview.extend(add_glow_mesa_preview(height_at, materials))
    if key == "relay-valley":
        preview.extend(add_relay_valley_preview(height_at, table, materials))
    if key == "echo-canyon":
        preview.extend(add_echo_canyon_preview(height_at, materials))
    if key == "mare-claim":
        preview.extend(add_mare_claim_preview(height_at, table, materials))
    if key == "ember-shore":
        preview.extend(add_ember_shore_preview(height_at, table, materials))
    preview.extend(add_clutter(key, profile, table, height_at, materials))
    overlay = add_mask_overlay(key, table, height_at, materials)
    render_verdicts(key, profile, factory, table, terrain, water, preview, overlay)
    claim.remove_objects(([water] if water else []) + preview + overlay)
    bpy.context.scene.world = None
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    contract = make_contract(key, profile, table, table_path, terrain, atlas_path, height_at)
    flatness = contract["pylonSiteFlatness"] + contract["capacitorSiteFlatness"] + contract["fixtureZoneFlatness"] + contract["buildZoneFlatness"]
    if any(site["maxDeviationMeters"] > contract["pylonFlatnessLimitMeters"] for site in flatness):
        raise AssertionError("load-bearing site is not buildable-flat")
    export_asset(profile, terrain, contract)


def main():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    keys = args or list(PROFILES)
    for key in keys:
        if key not in PROFILES:
            raise ValueError(f"unsupported terrain profile: {key}")
        build(key)


if __name__ == "__main__":
    main()
