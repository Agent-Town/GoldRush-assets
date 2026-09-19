"""Re-sculpt Twin Banks as a TRUE two-channel braid that agrees with the mask.

The water-mask engine merge made authored water masks first-class contract data
(`ContractWaterMask`, consumed by `src/world/Terrain.ts`). Twin Banks' published
mask -- `twin-banks-true-braid-dev`, mirrored into this map's terrain contract
under `maskTruth.waterMask` -- declares two polyline channels, two ford rects,
and a west source box. This script reads THAT table and derives every metre of
relief and paint from it, so mask agreement is structural rather than eyeballed:

  * the sim mask is the truth; the sculpt conforms (never the reverse);
  * water regions are cut BELOW the water plane, banks stay above it;
  * ford rects are one shallow gravel crossing, not a continuation of the cuts;
  * the plait between the cuts is dry, walkable-looking ground, because the
    mask classifies it `bank`.

Nothing here is simulation. The mesh is render-only and feeds `Terrain.visualY`.
Landmark mount X/Z are sim truth (`landmark-collision-contract.json`) and are
never moved by this script -- only their terrain-conform Y is re-derived, by the
landmark pack builder, after this relief lands.

Usage:
  blender -b --factory-startup --python build_twin_banks_braid.py
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

sys.dont_write_bytecode = True

claim_spec = importlib.util.spec_from_file_location("braid_claim_helpers", OUT / "build_the_claim_terrain.py")
claim = importlib.util.module_from_spec(claim_spec)
claim_spec.loader.exec_module(claim)
claim.mathutils = mathutils

state_spec = importlib.util.spec_from_file_location("braid_state_helpers", OUT / "render_contract_theme_states.py")
state = importlib.util.module_from_spec(state_spec)
state_spec.loader.exec_module(state)
state.claim = claim

unique_spec = importlib.util.spec_from_file_location("braid_unique_helpers", OUT / "build_unique_contract_terrains.py")
unique = importlib.util.module_from_spec(unique_spec)
unique_spec.loader.exec_module(unique)
unique.claim = claim
unique.state = state

HALF = 32.0
# 0.4 m cells. The braid's channels are 3 m wide and their bank lips are the
# edge the run camera actually reads, so the extra rows buy silhouette where it
# counts. Still one mesh, one material, one atlas, well inside the 60k budget.
SEGMENTS = 160
ATLAS_SIZE = 2048
WATER_Y = 0.025  # src/world/Terrain.ts WATER_Y -- the plane the sculpt is judged against.

STEM = "twin-banks-terrain"
CONTRACT_PATH = OUT / f"{STEM}-contract.json"
OBJECT_NAME = "TwinBanksTerrain"
MESH_NAME = "TwinBanksTerrainMesh"
MATERIAL_NAME = "TwinBanksPaintedTerrainMaterial"
ATLAS_NAME = "TwinBanksPaintedTerrainAtlas"

# Unit vector from a surface TOWARD the key light, in game X/Y/Z. Kept in step with
# src/world/LightRig.ts: a directional at (-28, 18, -22) aimed at (4, 0, 8).
SUN_DIRECTION = tuple(component / math.dist((-28.0, 18.0, -22.0), (4.0, 0.0, 8.0)) for component in (-32.0, 18.0, -30.0))

WATER_MASK_PROP = "authored braid mask twin-banks-true-braid-dev: two polyline channels halfWidth=1.5, west source box"
FORD_MASK_PROP = "authored braid mask ford rects x=-19..-13 and x=13..19, z=-5.5..5.5"

smoothstep = unique.smoothstep
gaussian = unique.gaussian
rotated_gaussian = unique.rotated_gaussian


# --------------------------------------------------------------------------
# THE MASK -- read from the contract, never retyped.
# --------------------------------------------------------------------------

def load_mask() -> dict:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    mask = contract["maskTruth"]["waterMask"]
    manifest = json.loads((ROOT / "assets/contracts/epoch-1-frontier/manifest.json").read_text(encoding="utf-8"))
    published = next(
        tile["waterMask"]
        for tile in manifest["devTiles"]
        if tile["id"] == "gt-water-mask-braid"
    )
    if json.dumps(published, sort_keys=True) != json.dumps(mask, sort_keys=True):
        raise SystemExit("mask drift: the pilot contract's maskTruth no longer matches the shipped manifest mask")
    contracts = json.loads((ROOT / "assets/contracts/epoch-1-frontier/contracts.json").read_text(encoding="utf-8"))
    production = next(item for item in contracts["contracts"] if item["id"] == "e1-twin-banks")
    if production["tileParams"].get("waterMask") != mask:
        raise SystemExit("mask drift: production Twin Banks and its sculpt no longer share the authored mask")
    return mask


def region(mask: dict, identifier: str) -> dict:
    return next(item for item in mask["regions"] if item["id"] == identifier)


def polyline_sd(x, z, points, half_width):
    """Signed distance to a polyline band; matches Terrain.distanceToWaterMaskRegion."""
    distance = np.full(np.shape(x), np.inf, dtype=np.float32)
    for index in range(1, len(points)):
        start = points[index - 1]
        end = points[index]
        dx = end["x"] - start["x"]
        dz = end["z"] - start["z"]
        length_squared = dx * dx + dz * dz
        t = np.clip(((x - start["x"]) * dx + (z - start["z"]) * dz) / length_squared, 0.0, 1.0)
        distance = np.minimum(distance, np.hypot(x - (start["x"] + dx * t), z - (start["z"] + dz * t)))
    return distance - half_width


def rect_sd(x, z, rect):
    """Signed rect distance. Outside matches the engine; inside is negative for shaping."""
    dx = np.maximum(rect["minX"] - x, x - rect["maxX"])
    dz = np.maximum(rect["minZ"] - z, z - rect["maxZ"])
    outside = np.hypot(np.maximum(dx, 0.0), np.maximum(dz, 0.0))
    inside = np.minimum(np.maximum(dx, dz), 0.0)
    return outside + inside


class Braid:
    """Every distance field the relief and the atlas are allowed to know about."""

    def __init__(self, mask: dict):
        self.mask = mask
        self.north = region(mask, "north-channel")
        self.south = region(mask, "south-channel")
        self.west_ford = region(mask, "west-ford")
        self.east_ford = region(mask, "east-ford")
        self.source = region(mask, "west-source-box")

    def fields(self, x, z) -> dict:
        x = np.asarray(x, dtype=np.float32)
        z = np.asarray(z, dtype=np.float32)
        north = polyline_sd(x, z, self.north["points"], self.north["halfWidth"])
        south = polyline_sd(x, z, self.south["points"], self.south["halfWidth"])
        source = rect_sd(x, z, self.source)
        ford = np.minimum(rect_sd(x, z, self.west_ford), rect_sd(x, z, self.east_ford))
        cut = np.minimum(np.minimum(north, south), source)
        return {
            "north": north,
            "south": south,
            "source": source,
            "ford": ford,
            "cut": cut,
            "wet": np.minimum(cut, ford),
            "centre": self.channel_centre(x),
        }

    def channel_centre(self, x):
        """Game z of the north channel centreline at x (the south is its mirror)."""
        points = self.north["points"]
        centre = np.zeros(np.shape(x), dtype=np.float32)
        first = points[0]
        last = points[-1]
        centre = np.where(x <= first["x"], first["z"], centre)
        centre = np.where(x >= last["x"], last["z"], centre)
        for index in range(1, len(points)):
            start = points[index - 1]
            end = points[index]
            span = end["x"] - start["x"]
            t = np.clip((x - start["x"]) / span, 0.0, 1.0)
            inside = (x > start["x"]) & (x <= end["x"])
            centre = np.where(inside, start["z"] + (end["z"] - start["z"]) * t, centre)
        return centre

    def classify(self, x, z) -> np.ndarray:
        """0 = bank, 1 = river, 2 = ford, in Terrain.sample's first-match order."""
        fields = self.fields(x, z)
        zone = np.zeros(np.shape(x), dtype=np.int8)
        river = (np.minimum(fields["north"], fields["south"]) <= 0.0) | (fields["source"] <= 0.0)
        zone = np.where(river, 1, zone)
        zone = np.where(fields["ford"] <= 0.0, 2, zone)
        return zone


BRAID = Braid(load_mask())


# --------------------------------------------------------------------------
# THE RELIEF
# --------------------------------------------------------------------------

LANDMARK_PADS = (
    (13.5, 14.2, 4.6),
    (-13.0, -14.0, 4.4),
    (-16.0, 10.7, 3.0),
    (16.0, -10.7, 3.0),
)
_PAD_LEVELS: dict[tuple[float, float], float] = {}


def pad_level(pad_x, pad_z):
    """The unpadded ground at a mount -- what the pad levels the site to."""
    key = (pad_x, pad_z)
    if key not in _PAD_LEVELS:
        _PAD_LEVELS[key] = float(braid_height(np.float32(pad_x), np.float32(pad_z), with_pads=False)) + 0.02
    return _PAD_LEVELS[key]


def braid_height(x, z, with_pads=True):
    """Twin Banks re-cut: two channels, one plait, two crossings, two settlements."""
    x = np.asarray(x, dtype=np.float32)
    z = np.asarray(z, dtype=np.float32)
    ax = np.abs(x)
    az = np.abs(z)
    fields = BRAID.fields(x, z)
    sd_north = fields["north"]
    sd_south = fields["south"]
    sd_source = fields["source"]
    sd_ford = fields["ford"]
    sd_cut = fields["cut"]
    sd_wet = fields["wet"]
    centre = fields["centre"]

    grain = np.sin(x * 0.16 + z * 0.09) * 0.035 + np.cos(x * 0.09 - z * 0.24) * 0.025

    # 1. THE DRY GROUND. Everything starts as land that lifts away from whatever
    #    water is nearest, so no bank can ever sit below the water plane.
    shore = np.clip(sd_wet, 0.0, None)
    land = (
        WATER_Y
        + 0.035
        + smoothstep(0.0, 1.7, shore) * 0.27
        + smoothstep(1.5, 7.5, shore) * 0.20
    )

    # The two settlements rhyme without mirroring: a long worked shelf north,
    # damp broken hummocks south. Inherited from the shipped composition.
    north_shelf = rotated_gaussian(x, z, -3.0, 18.0, 22.0, 5.2, -0.04) * 0.34
    north_cut = rotated_gaussian(x, z, 11.5, 17.0, 8.5, 1.8, 0.12) * -0.16
    south_hummocks = (
        gaussian(x, z, -18.0, -17.0, 7.0, 4.8) * 0.34
        + gaussian(x, z, 9.0, -20.0, 8.5, 5.4) * 0.25
        + gaussian(x, z, 24.0, -15.0, 4.8, 6.0) * 0.31
    )
    outer = smoothstep(22.0, 32.0, az) * 0.52 + smoothstep(26.0, 32.0, ax) * 0.30
    # Macro relief only past the wet corridor, so the cuts keep their own read.
    macro_gate = smoothstep(1.2, 5.0, shore)
    land = land + (north_shelf + north_cut + south_hummocks + outer + grain) * macro_gate

    # 2. THE PLAIT. Between the two cuts the mask says bank, so the braid's
    #    island has to be honest dry gravel -- the map's dominant new landform.
    between = 1.0 - smoothstep(-0.25, 0.35, az - centre)
    plait = (
        between
        * smoothstep(0.02, 0.85, sd_north)
        * smoothstep(0.02, 0.85, sd_south)
        * smoothstep(0.0, 1.1, sd_ford)
    )
    # The two named mid-channel bars from the shipped water truth survive as the
    # high points of the plait: same story object, grown into a braid island.
    bar_crowns = (
        gaussian(x, z, -7.5, 0.2, 4.6, 1.15) * 0.16
        + gaussian(x, z, 7.4, -0.25, 4.1, 1.05) * 0.15
        + gaussian(x, z, -21.0, 0.0, 2.6, 0.9) * 0.10
        + gaussian(x, z, 20.5, 0.0, 2.4, 0.85) * 0.09
    )
    drag = (np.sin(x * 0.62 + z * 0.9) * 0.5 + 0.5) ** 3 * 0.045
    land = land + plait * (0.175 + bar_crowns + drag)

    # 3. THE CUTS. North runs deep and fast (it is why the fords exist); south
    #    runs shallower over riffles. Depth is driven by the mask's own signed
    #    distance, so the waterline lands exactly on the mask boundary.
    def bed(signed, depth, half_width):
        u = np.clip(-signed / half_width, 0.0, 1.0)
        return WATER_Y - 0.02 - depth * smoothstep(0.0, 0.82, u)

    riffle = np.sin(x * 0.55) * 0.018 + np.sin(x * 1.31 + 0.7) * 0.011
    bed_north = bed(sd_north, 0.46, BRAID.north["halfWidth"]) + grain * 0.10
    bed_south = bed(sd_south, 0.33, BRAID.south["halfWidth"]) + riffle + grain * 0.14
    bed_source = bed(sd_source, 0.28, 2.0) + grain * 0.08

    deep = np.full_like(land, 9.0)
    deep = np.minimum(deep, np.where(sd_north < 0.45, bed_north, 9.0))
    deep = np.minimum(deep, np.where(sd_south < 0.45, bed_south, 9.0))
    deep = np.minimum(deep, np.where(sd_source < 0.45, bed_source, 9.0))
    cut_weight = 1.0 - smoothstep(-0.28, 0.30, sd_cut)
    height = land * (1.0 - cut_weight) + np.where(deep < 8.0, deep, land) * cut_weight

    # 4. THE CROSSINGS. A ford rect is classified ford EVERYWHERE inside it, so
    #    it is one shallow gravel pan spanning both cuts and the plait between
    #    them -- the only place the map lets anything walk across.
    cobble = (np.sin(x * 2.3 + z * 1.7) * 0.5 + 0.5) ** 2 * 0.030
    ford_shelf = WATER_Y - 0.075 + cobble + grain * 0.16
    ford_weight = 1.0 - smoothstep(-0.60, 0.34, sd_ford)
    height = height * (1.0 - ford_weight) + ford_shelf * ford_weight

    # Everything past this point shapes DRY ground only. Nothing may lift the
    # inside of a mask region back above the water plane.
    dry_gate = smoothstep(-0.05, 0.75, sd_wet)

    # 4b. THE NATURAL LEVEE. Braided rivers build a low lip of their own coarse
    #     spoil along every edge they hold. It is also what draws the mask
    #     boundary for the eye: a lit line exactly where the water stops.
    levee_lip = np.exp(-((sd_wet - 0.85) / 0.62) ** 2) * 0.085 * dry_gate
    height = height + levee_lip

    # 5. THE WORKED SHELVES. Both build zones (|z| >= 7) stay visually flat
    #    enough to explain placement; the drama lives at the map's rim.
    north_apron = gaussian(x, z, 0.0, 15.0, 17.0, 7.0)
    south_apron = gaussian(x, z, 0.0, -14.5, 15.5, 6.5)
    calm = np.clip((north_apron + south_apron) * smoothstep(6.4, 9.0, az) * 0.72, 0.0, 0.82) * dry_gate
    calm_height = 0.50 + smoothstep(21.0, 30.0, az) * 0.18
    height = height * (1.0 - calm) + calm_height * calm

    # 6. THE RIM. Levees and terrace lips frame the settlements without turning
    #    either shelf into a uniform mound.
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
    height = height + (levees * smoothstep(14.0, 22.0, ax) + terrace_edges) * dry_gate

    # 6b. THE GROUND REMEMBERS. Two abandoned braid scars -- ground the river
    #     held before it moved -- give both empty shelves a reason to exist.
    #     They are dry: the guard below can only ever cut toward the water
    #     plane, never through it.
    scars = np.clip(
        rotated_gaussian(x, z, -9.0, 11.5, 13.0, 1.55, 0.20) * 0.30
        + rotated_gaussian(x, z, 14.0, 9.5, 9.0, 1.30, -0.26) * 0.24
        + rotated_gaussian(x, z, -6.0, -10.8, 11.5, 1.40, -0.18) * 0.26
        + rotated_gaussian(x, z, 17.0, -12.5, 8.0, 1.20, 0.22) * 0.21,
        0.0,
        0.40,
    )
    # 6c. EVERYTHING WALKS TO THE FORDS. Haul lanes, worn where the crossings
    #     force traffic together, with the spoil pushed to one side.
    def lane(cx, cz, fx, fz, width):
        return unique.segment_mask(x, z, cx, cz, fx, fz, width)

    lanes = np.clip(
        lane(-16.0, 10.7, -16.0, 5.9, 2.4) * 0.9
        + lane(-16.0, 5.9, -22.0, 15.5, 2.2) * 0.7
        + lane(16.0, -10.7, 16.0, -5.9, 2.4) * 0.9
        + lane(16.0, -5.9, 21.0, -16.0, 2.2) * 0.7
        + lane(-13.0, -14.0, -16.0, -5.9, 2.0) * 0.6,
        0.0,
        1.0,
    )
    cut_depth = scars * 0.9 + lanes * 0.075
    height = height - np.minimum(cut_depth, np.maximum(height - (WATER_Y + 0.075), 0.0))
    # Spoil berms alongside the lanes read the traffic from the run camera.
    height = height + lanes * 0.035 * dry_gate * (np.sin(x * 1.9 + z * 1.3) * 0.5 + 0.5)

    # 6d. PREPARED GROUND. Every mounted landmark stands on a made pad, never
    #     on raw slope (their X/Z are simulation truth and never move). The pad
    #     levels toward the ground the sculpt already has at that mount, so it
    #     reads as cut-and-filled work rather than an invented mound.
    if with_pads:
        for pad_x, pad_z, radius in LANDMARK_PADS:
            pad = gaussian(x, z, pad_x, pad_z, radius, radius * 0.74) * dry_gate
            pad = np.clip((pad - 0.34) / 0.52, 0.0, 1.0)
            height = height * (1.0 - pad * 0.62) + pad_level(pad_x, pad_z) * pad * 0.62

    # 7. THE ENDS. The mask's water stops at x=+/-28, so the sculpt stops it
    #    too: the braid spends itself in gravel plugs instead of running off the
    #    tile as a river the simulation does not have.
    plug = smoothstep(26.0, 31.0, ax) * (1.0 - smoothstep(3.5, 7.0, az)) * 0.22
    height = height + plug * dry_gate

    return np.clip(height, -0.58, 2.45)


# --------------------------------------------------------------------------
# THE PAINT
# --------------------------------------------------------------------------

def salt_gravel(rock, clean):
    """Pale dry river gravel: the crown of a bar, and the mineral lip above a waterline."""
    return rock * np.array((0.74, 0.70, 0.58), dtype=np.float32) + clean * np.array((0.52, 0.49, 0.41), dtype=np.float32)


def braid_atlas():
    bank_a = claim.image_pixels(claim.BANK_A)
    bank_b = claim.image_pixels(claim.BANK_B)
    bank_c = claim.image_pixels(claim.BANK_C)
    river = claim.image_pixels(claim.RIVER)

    axis = np.linspace(0.0, 1.0, ATLAS_SIZE, dtype=np.float32)
    u, v = np.meshgrid(axis, axis)
    x = (u - 0.5) * HALF * 2.0
    z = (v - 0.5) * HALF * 2.0
    ax = np.abs(x)
    az = np.abs(z)
    fields = BRAID.fields(x, z)
    sd_wet = fields["wet"]
    sd_cut = fields["cut"]
    sd_ford = fields["ford"]
    sd_north = fields["north"]
    sd_south = fields["south"]
    centre = fields["centre"]

    clean = claim.tiled_sample(bank_b, u, v, 3.25, 0.17, 0.31)
    rock = claim.tiled_sample(bank_c, u, v, 3.55, 0.61, 0.08)
    wash = claim.tiled_sample(bank_a, u, v, 2.25, 0.27, 0.49)
    macro = (np.sin(x * 0.15 + z * 0.10) * 0.5 + 0.5)[..., None]
    land = wash * (0.40 + macro * 0.06) + clean * 0.30 + rock * (0.30 - macro * 0.04)
    land *= np.array((1.01, 0.86, 0.67), dtype=np.float32)

    water = claim.tiled_sample(river, u, v, 2.55, 0.41, 0.13)
    water *= np.array((0.48, 0.43, 0.31), dtype=np.float32)
    water *= 1.0 - claim.engraved_ink(river, u, v, 2.55, 0.41, 0.13)[..., None] * 0.24

    # BED DEPTH READS AS BED (beauty U2). A render-only water surface now covers both cuts
    # (src/world/Terrain3dClaimPilot.ts channel ribbons) and the shallow channel's sheet is the
    # more transparent of the two, so the paint under it is what a player actually sees. The
    # contract calls the SOUTH channel shallow (waterTruth.southChannelDepth 0.35 against the
    # north's 0.48): give it a pale wet-gravel floor and leave the north bed dark, and the pair
    # teaches which channel is deep without a word of UI. Before this, the shallow channel
    # measured DARKER than the deep one, because transparency over a black bed inverts depth.
    #
    # KEPT DELIBERATELY SMALL, and this is the interesting part: claim.apply_grit_grade closes
    # this atlas by re-normalising on ITS OWN 4th/96th luminance percentiles, and a channel bed
    # is in the darkest 4% of the tile. Lifting the bed hard (0.52 blend, measured) moved the
    # black point and re-graded the ENTIRE map ~8% darker on the banks — to buy +2 luminance
    # under a 73%-opaque water sheet. Any paint aimed at this tile's darkest pixels is spending
    # a GLOBAL budget; spend it where the camera actually sees it.
    shallow_bed = 1.0 - smoothstep(-1.35, -0.10, sd_south)
    shallow_bed *= smoothstep(-0.2, 1.4, sd_north)  # never at the confluence, where both run deep
    gravel_bed = claim.tiled_sample(bank_c, u, v, 4.10, 0.53, 0.37) * np.array((0.92, 0.84, 0.66), dtype=np.float32)
    water = water * (1.0 - shallow_bed[..., None] * 0.20) + gravel_bed * shallow_bed[..., None] * 0.20
    # Foam follows each cut's own axis instead of a single straight band.
    foam = np.clip((np.sin(x * 0.62 + sd_cut * 5.2 + np.sin(x * 0.17) * 1.2) - 0.74) / 0.26, 0.0, 1.0) ** 2
    foam *= 1.0 - smoothstep(0.0, 1.2, np.abs(sd_cut))
    foam_color = rock * np.array((0.58, 0.53, 0.41), dtype=np.float32)
    water = water * (1.0 - foam[..., None] * 0.16) + foam_color * foam[..., None] * 0.16

    # Damp ground hugs the whole braid corridor, not a rectangle.
    damp = 1.0 - smoothstep(0.0, 9.0, np.clip(sd_wet, 0.0, None))
    damp_land = land * np.array((0.62, 0.78, 0.54), dtype=np.float32)
    land = land * (1.0 - damp[..., None] * 0.34) + damp_land * damp[..., None] * 0.34

    # The opposed furrow fields keep the two-settlement read on the dry shelves.
    field_envelope = np.clip(
        gaussian(x, z, -13.0, 19.0, 10.5, 4.8) + gaussian(x, z, 13.0, -18.0, 9.5, 4.4),
        0.0,
        1.0,
    )
    furrows = (np.sin((x + z * 0.16) * 1.32) * 0.5 + 0.5) ** 5
    furrow_color = land * np.array((0.67, 0.57, 0.39), dtype=np.float32)
    furrow_mask = field_envelope * furrows * smoothstep(2.0, 5.5, np.clip(sd_wet, 0.0, None))
    land = land * (1.0 - furrow_mask[..., None] * 0.24) + furrow_color * furrow_mask[..., None] * 0.24

    # The plait first: it is dry gravel between two cuts and must read as the
    # brightest thing in the corridor, or the braid collapses into one river.
    between = 1.0 - smoothstep(-0.25, 0.35, az - centre)
    plait = between * smoothstep(0.02, 0.9, sd_north) * smoothstep(0.02, 0.9, sd_south) * smoothstep(0.0, 1.1, sd_ford)
    gravel = rock * np.array((1.34, 1.24, 0.98), dtype=np.float32)
    cobbles = (np.sin(x * 3.1 + z * 2.4) * np.sin(x * 1.7 - z * 3.3) * 0.5 + 0.5) ** 3
    gravel = gravel * (1.0 - cobbles[..., None] * 0.30)

    # Flood drag: stains parallel to each cut, on the ground the water takes
    # back -- but never on the plait, whose whole job is to stay legible.
    flood_drag = np.clip((1.0 - smoothstep(0.35, 3.4, np.clip(sd_cut, 0.0, None))) * 0.9, 0.0, 1.0)
    flood_drag *= 1.0 - plait
    bank_stain = wash * np.array((0.36, 0.31, 0.20), dtype=np.float32)
    land = land * (1.0 - flood_drag[..., None] * 0.42) + bank_stain * flood_drag[..., None] * 0.42
    land = land * (1.0 - plait[..., None] * 0.72) + gravel * plait[..., None] * 0.72

    # DAMP SHOULDERS (beauty U2): the plait's edges are where the braid laps it. Dry crown,
    # damp shoulders — otherwise the island reads as a flat cut-out laid between two rivers.
    shoulder = plait * (1.0 - smoothstep(0.05, 1.5, np.minimum(sd_north, sd_south)))
    damp_gravel = gravel * np.array((0.66, 0.71, 0.66), dtype=np.float32)
    land = land * (1.0 - shoulder[..., None] * 0.46) + damp_gravel * shoulder[..., None] * 0.46

    # THE GRAVEL BARS ARE AFFORDANCE, NOT DECORATION (beauty U2). tileParams.water.gravelBars
    # puts two mid-channel bars at (-7.5, 0.2) and (7.4, -0.25) and the briefing card sells them
    # ("gravel bars"); they are the crossings a player reads before stepping. Each gets a bright
    # dry crown inside a damp ring, so "wet but passable" survives 390 px.
    bar_crown = np.clip(
        rotated_gaussian(x, z, -7.5, 0.2, 2.55, 0.62, -0.12)
        + rotated_gaussian(x, z, 7.4, -0.25, 2.25, 0.55, 0.16),
        0.0,
        1.0,
    )
    bar_halo = np.clip(
        rotated_gaussian(x, z, -7.5, 0.2, 3.45, 1.05, -0.12)
        + rotated_gaussian(x, z, 7.4, -0.25, 3.10, 0.95, 0.16),
        0.0,
        1.0,
    )
    bar_ring = np.clip(bar_halo - bar_crown, 0.0, 1.0)
    dry_bar = salt_gravel(rock, clean)
    land = land * (1.0 - bar_ring[..., None] * 0.40) + damp_gravel * bar_ring[..., None] * 0.40
    land = land * (1.0 - bar_crown[..., None] * 0.55) + dry_bar * bar_crown[..., None] * 0.55

    # The ground remembers: abandoned braid scars and the haul lanes that every
    # crossing forces together. Same coordinates as the relief.
    scars = np.clip(
        rotated_gaussian(x, z, -9.0, 11.5, 13.0, 1.55, 0.20)
        + rotated_gaussian(x, z, 14.0, 9.5, 9.0, 1.30, -0.26)
        + rotated_gaussian(x, z, -6.0, -10.8, 11.5, 1.40, -0.18)
        + rotated_gaussian(x, z, 17.0, -12.5, 8.0, 1.20, 0.22),
        0.0,
        1.0,
    )
    silt = wash * np.array((0.52, 0.47, 0.34), dtype=np.float32)
    salt = clean * np.array((1.18, 1.10, 0.88), dtype=np.float32)
    land = land * (1.0 - scars[..., None] * 0.40) + silt * scars[..., None] * 0.40
    crust = np.clip((scars - 0.30) * 2.2, 0.0, 1.0) * (1.0 - np.clip(scars * 1.4, 0.0, 1.0))
    land = land * (1.0 - crust[..., None] * 0.34) + salt * crust[..., None] * 0.34

    lanes = np.clip(
        unique.segment_mask(x, z, -16.0, 10.7, -16.0, 5.9, 2.4) * 0.9
        + unique.segment_mask(x, z, -16.0, 5.9, -22.0, 15.5, 2.2) * 0.7
        + unique.segment_mask(x, z, 16.0, -10.7, 16.0, -5.9, 2.4) * 0.9
        + unique.segment_mask(x, z, 16.0, -5.9, 21.0, -16.0, 2.2) * 0.7
        + unique.segment_mask(x, z, -13.0, -14.0, -16.0, -5.9, 2.0) * 0.6,
        0.0,
        1.0,
    )
    rut = np.clip((np.sin((x * 0.4 + z) * 2.4) * 0.5 + 0.5) ** 4 + 0.35, 0.0, 1.0)
    lane_color = wash * np.array((0.74, 0.60, 0.40), dtype=np.float32)
    land = land * (1.0 - (lanes * rut)[..., None] * 0.34) + lane_color * (lanes * rut)[..., None] * 0.34

    wet_mask = 1.0 - smoothstep(-0.30, 0.22, sd_wet)
    atlas = land * (1.0 - wet_mask[..., None]) + water * wet_mask[..., None]

    # Ford pans: pale wet gravel, the only crossable water on the map.
    ford_paint = 1.0 - smoothstep(-0.45, 0.25, sd_ford)
    ford_color = clean * np.array((0.86, 0.80, 0.62), dtype=np.float32)
    atlas = atlas * (1.0 - ford_paint[..., None] * 0.46) + ford_color * ford_paint[..., None] * 0.46

    # WET MARGINS (beauty U2). The metre outside the waterline is the metre the run camera reads
    # as "is that water or a hole?" — it used to be plain bank paint carrying one dark stroke, and
    # the cut's own shading (a 0.45 m slope turned away from a low warm sun) took it the rest of
    # the way to black. Damp sand under a pale mineral lip gives the eye a wet edge to land on,
    # and unlike the stroke it is a GRADE of the ground already there, so the engraving survives.
    outside = np.clip(sd_wet, 0.0, None)
    # Dry side only: inside the mask the bed is already water paint under a water surface, and
    # grading it damp as well only muddied the channels.
    margin = (1.0 - smoothstep(0.0, 1.05, outside)) * smoothstep(-0.08, 0.06, sd_wet)
    damp_sand = atlas * np.array((0.74, 0.76, 0.71), dtype=np.float32)
    atlas = atlas * (1.0 - margin[..., None] * 0.44) + damp_sand * margin[..., None] * 0.44
    lip = np.exp(-(outside / 0.17) ** 2) * smoothstep(-0.06, 0.02, sd_wet)
    atlas = atlas * (1.0 - lip[..., None] * 0.26) + salt_gravel(rock, clean) * lip[..., None] * 0.26

    # One dark waterline stroke along the mask boundary -- the engraved lip.
    bank_line = np.exp(-(sd_wet / 0.40) ** 2)[..., None]
    atlas *= 1.0 - bank_line * 0.09

    # SKYLIGHT ON THE FACES THE SUN CANNOT REACH (beauty U2, and the single biggest reason the
    # braid read as two ink slots). The rig's key is one low warm directional from the north-west
    # -- src/world/LightRig.ts sun (-28,18,-22) aimed at (4,0,8) -- so every SOUTH-facing wall of
    # a cut takes a negative Lambert term and crushes to black no matter what is painted on it.
    # Those walls are exactly the north lip of each channel and the plait's south shoulder: the
    # two edges the run camera reads first. A shaded face still needs something to shade, so the
    # paint lifts them, cool, like the sky fill they would really catch. Corridor-scoped: the
    # macro relief keeps its own contrast.
    cell = HALF * 2.0 / (ATLAS_SIZE - 1)
    height = braid_height(x, z)
    d_dz, d_dx = np.gradient(height, cell)
    normal_scale = 1.0 / np.sqrt(d_dx * d_dx + d_dz * d_dz + 1.0)
    lambert = (-d_dx * SUN_DIRECTION[0] + SUN_DIRECTION[1] - d_dz * SUN_DIRECTION[2]) * normal_scale
    shade = smoothstep(0.34, 0.02, lambert) * (1.0 - smoothstep(1.2, 6.5, np.clip(sd_wet, 0.0, None)))
    sky_fill = np.array((0.93, 0.99, 1.09), dtype=np.float32)

    edge = smoothstep(28.0, 31.8, np.maximum(ax, az))[..., None]
    parchment = claim.tiled_sample(wash, u, v, 1.42, 0.31, 0.18) * np.array((0.75, 0.60, 0.41), dtype=np.float32)
    atlas = atlas * (1.0 - edge * 0.68) + parchment * edge * 0.68
    atlas = claim.apply_grit_grade(atlas, bank_a, u, v, "twin-banks")

    # AFTER the grade, deliberately. apply_grit_grade re-normalises on the atlas's own 4th/96th
    # luminance percentiles, so paint that lifts the darkest pixels moves the black point and
    # re-grades the whole tile: inside the grade, this lift cost the dry banks ~5-8% of their
    # value to buy the corridor. Outside it, the same lift is local. It is a lighting repair
    # rather than paint, so it also has no business being palette-matched to the contract plate.
    atlas = np.clip(atlas * (1.0 + shade[..., None] * 0.52 * sky_fill), 0.008, 0.94)

    rgba = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    rgba[:, :, :3] = atlas
    path = OUT / f"{STEM}-atlas.png"
    image = bpy.data.images.new(ATLAS_NAME, ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image


# --------------------------------------------------------------------------
# THE MESH
# --------------------------------------------------------------------------

def make_terrain(material):
    axis = np.linspace(-HALF, HALF, SEGMENTS + 1, dtype=np.float32)
    grid_x, grid_z = np.meshgrid(axis, axis)
    heights = braid_height(grid_x, grid_z)
    vertices = []
    uvs = []
    for zi in range(SEGMENTS + 1):
        for xi in range(SEGMENTS + 1):
            vertices.append((float(axis[xi]), float(-axis[zi]), float(heights[zi, xi])))
            uvs.append((xi / SEGMENTS, zi / SEGMENTS))
    faces = []
    row = SEGMENTS + 1
    for zi in range(SEGMENTS):
        for xi in range(SEGMENTS):
            a = zi * row + xi
            b = a + 1
            c = a + row
            d = c + 1
            faces.extend(((a, d, b), (a, c, d)))
    mesh = bpy.data.meshes.new(MESH_NAME)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        polygon.use_smooth = True
        for loop_index in polygon.loop_indices:
            uv_layer.data[loop_index].uv = uvs[mesh.loops[loop_index].vertex_index]
    terrain = bpy.data.objects.new(OBJECT_NAME, mesh)
    bpy.context.collection.objects.link(terrain)
    mesh.materials.append(material)
    terrain["render_only"] = True
    terrain["sim_surface"] = "planar"
    terrain["height_socket"] = "Terrain.visualY"
    terrain["contract_id"] = "e1-twin-banks"
    terrain["tile_id"] = "e1-twin-banks"
    terrain["water_mask"] = WATER_MASK_PROP
    terrain["ford_mask"] = FORD_MASK_PROP
    terrain["regional_family"] = "Epoch 1 frontier river county"
    terrain["identity_rule"] = "unique mesh, atlas, macro silhouette, and landmark composition"
    return terrain


# --------------------------------------------------------------------------
# THE PREVIEW (owner verdict only; never exported)
# --------------------------------------------------------------------------

def make_mask_water(material, samples=352):
    """A water surface cut to the mask itself -- the braid's agreement, in 3D."""
    step = HALF * 2.0 / samples
    axis = np.linspace(-HALF, HALF, samples + 1, dtype=np.float32)
    grid_x, grid_z = np.meshgrid(axis, axis)
    inside = BRAID.fields(grid_x, grid_z)["wet"] <= 0.0
    vertices = []
    faces = []
    index_of: dict[tuple[int, int], int] = {}

    def vertex(xi, zi):
        key = (xi, zi)
        if key not in index_of:
            index_of[key] = len(vertices)
            vertices.append((float(axis[xi]), float(-axis[zi]), WATER_Y))
        return index_of[key]

    centre_x = grid_x[:-1, :-1] + step * 0.5
    centre_z = grid_z[:-1, :-1] + step * 0.5
    cell = BRAID.fields(centre_x, centre_z)["wet"] <= 0.0
    for zi in range(samples):
        for xi in range(samples):
            if not cell[zi, xi]:
                continue
            a = vertex(xi, zi)
            b = vertex(xi + 1, zi)
            c = vertex(xi, zi + 1)
            d = vertex(xi + 1, zi + 1)
            faces.extend(((a, d, b), (a, c, d)))
    mesh = bpy.data.meshes.new("RenderHelperBraidWaterMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    water = bpy.data.objects.new("RenderHelperBraidWater", mesh)
    bpy.context.collection.objects.link(water)
    mesh.materials.append(material)
    del inside
    return water


def scatter_bar_stones(name, x, game_z, length, width, yaw, materials, count=9):
    objects = []
    for index in range(count):
        along = (index - (count - 1) * 0.5) / max(count - 1, 1) * length
        cross = (-0.32 if index % 2 else 0.30) * width
        rx = x + math.cos(yaw) * along - math.sin(yaw) * cross
        rz = game_z + math.sin(yaw) * along + math.cos(yaw) * cross
        ground = float(braid_height(np.float32(rx), np.float32(rz)))
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=(rx, -rz, ground + 0.03))
        stone = bpy.context.object
        stone.name = f"{name}.stone.{index}"
        stone.scale = (0.42 + (index % 3) * 0.13, 0.30 + (index % 2) * 0.10, 0.13)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        stone.data.materials.append(materials["gravel"])
        objects.append(stone)
    return objects


def make_preview(terrain_material):
    materials = unique.regional_materials("TwinBanksBraid")
    materials["water"] = claim.make_water_material("RenderHelperBraidRiverWater")
    materials["gravel"] = claim.make_render_material("TwinBanksBraidGravel", (0.27, 0.30, 0.24))
    materials["furrow"] = claim.make_render_material("TwinBanksBraidFurrowSoil", (0.22, 0.105, 0.035))
    claim.terrain_height = lambda x, z: float(braid_height(np.float32(x), np.float32(z)))

    objects = [make_mask_water(materials["water"])]
    objects.extend(state.make_ford_stones(-16.0, terrain_material))
    objects.extend(state.make_ford_stones(16.0, terrain_material))
    objects.extend(scatter_bar_stones("RenderHelperBraidWestBar", -7.5, 0.2, 4.6, 1.1, -0.10, materials))
    objects.extend(scatter_bar_stones("RenderHelperBraidEastBar", 7.4, -0.25, 4.2, 1.0, 0.14, materials))
    objects.extend(state.make_stake("RenderHelperBraidSouthStake", 0.0, -12.0, {"timber": materials["timber"], "board": materials["fresh"]}))
    objects.extend(state.make_stake("RenderHelperBraidNorthMarker", 0.0, 12.0, {"timber": materials["timber"], "board": materials["fresh"]}))

    objects.extend(unique.add_winch_tower("RenderHelperBraidNorthWinch", -16.0, 10.7, 1.0, materials))
    objects.extend(unique.add_winch_tower("RenderHelperBraidSouthWinch", 16.0, -10.7, -1.0, materials))
    objects.extend(unique.add_simple_shed("RenderHelperBraidNorthShed", 13.5, 14.2, 8.5, 5.8, materials, -0.10))
    objects.extend(unique.add_simple_shed("RenderHelperBraidNorthOutbuilding", 22.0, 16.0, 4.4, 3.2, materials, 0.14))
    objects.extend(unique.add_simple_shed("RenderHelperBraidSouthShed", -13.0, -14.0, 8.0, 5.4, materials, 0.14))
    objects.extend(unique.add_simple_shed("RenderHelperBraidSouthOutbuilding", -22.0, -16.5, 4.1, 3.1, materials, -0.12))
    objects.extend(unique.add_irrigation_rows("RenderHelperBraidNorthFurrows", -12.0, 20.0, 15.0, 6, -0.08, materials))
    objects.extend(unique.add_irrigation_rows("RenderHelperBraidSouthFurrows", 12.0, -19.0, 14.0, 5, 0.12, materials))
    objects.extend(unique.add_fence("RenderHelperBraidNorthParcel", [(-23, 14), (-16, 15), (-9, 15)], materials))
    objects.extend(unique.add_fence("RenderHelperBraidNorthParcelEast", [(9, 16), (17, 15), (24, 14)], materials))
    objects.extend(unique.add_fence("RenderHelperBraidSouthParcel", [(-24, -15), (-17, -16), (-9, -16)], materials))
    objects.extend(unique.add_fence("RenderHelperBraidSouthParcelEast", [(9, -15), (17, -16), (24, -15)], materials))

    # Reeds stand on the braid's own edges now: outer banks and plait heads.
    reed_positions = [
        (-26.5, 2.6), (-24.0, -2.9), (-20.5, 3.6), (-11.5, -4.6), (-9.0, 5.2),
        (-3.5, -3.4), (2.5, 3.4), (8.5, -5.0), (11.0, 5.1), (20.5, -3.4),
        (24.5, 2.8), (27.0, -2.4),
    ]
    for index, (x, z) in enumerate(reed_positions):
        objects.extend(claim.make_reed_cluster(f"RenderHelperBraidReed.{index}", x, z, 0.9 + (index % 3) * 0.12, materials))
    objects.extend(unique.add_regional_rocks("twin-banks", materials, 9, 9.0))
    return objects


# --------------------------------------------------------------------------
# BOARDS
# --------------------------------------------------------------------------

def render_boards(terrain, preview_water, preview_objects):
    backdrop = claim.make_backdrop()
    panorama = claim.link_panorama("twin-banks")
    for obj in panorama:
        obj.hide_render = True
    run_camera = claim.add_camera("TwinBanksBraidRunCamera", (0.0, -30.3, 26.26), (0.0, -8.65, 0.51), 42.0)
    overview = claim.add_camera("TwinBanksBraidOverview", (0.0, -38.0, 50.0), (0.0, -1.0, 0.42), 46.0)
    low = claim.add_camera("TwinBanksBraidLowCamera", (-28.0, 23.0, 11.0), (5.0, -0.4, 0.38), 46.0)
    ford_camera = claim.add_camera("TwinBanksBraidFordCamera", (-16.0, -18.0, 9.4), (-14.0, -1.0, 0.1), 40.0)
    plait_camera = claim.add_camera("TwinBanksBraidPlaitCamera", (-2.0, -13.5, 5.2), (6.0, 0.6, 0.05), 44.0)

    ortho_data = bpy.data.cameras.new("TwinBanksBraidOrtho")
    ortho_data.type = "ORTHO"
    ortho_data.ortho_scale = HALF * 2.0
    ortho_data.clip_start = 1.0
    ortho_data.clip_end = 400.0
    ortho = bpy.data.objects.new("TwinBanksBraidOrtho", ortho_data)
    bpy.context.collection.objects.link(ortho)
    ortho.location = (0.0, 0.0, 120.0)
    ortho.rotation_euler = (0.0, 0.0, 0.0)

    lights = claim.add_lighting(sunset=False)
    terrain.hide_render = False
    for obj in preview_objects:
        obj.hide_render = False

    claim.render(run_camera, ARTIFACTS / "twin-banks-braid-run-camera.png")
    claim.render(overview, ARTIFACTS / "twin-banks-braid-layout.png")
    claim.render(ford_camera, ARTIFACTS / "twin-banks-braid-west-ford.png")
    claim.render(plait_camera, ARTIFACTS / "twin-banks-braid-plait.png")

    # Bare relief: the sculpt alone, no dressing, no preview water.
    for obj in preview_objects:
        obj.hide_render = True
    claim.render(run_camera, ARTIFACTS / "twin-banks-braid-run-camera-bare.png")

    scene = bpy.context.scene
    resolution = (scene.render.resolution_x, scene.render.resolution_y)
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    claim.render(ortho, ARTIFACTS / "twin-banks-braid-ortho-relief.png")
    preview_water.hide_render = False
    claim.render(ortho, ARTIFACTS / "twin-banks-braid-ortho-mask.png")
    scene.render.resolution_x, scene.render.resolution_y = resolution

    for obj in preview_objects:
        obj.hide_render = False
    claim.remove_objects(lights)
    low_lights = claim.add_lighting(sunset=True)
    claim.render(low, ARTIFACTS / "twin-banks-braid-low-angle.png")
    for obj in panorama:
        obj.hide_render = False
    claim.render(low, ARTIFACTS / "twin-banks-braid-panorama-mounted.png")
    claim.remove_objects(low_lights + [run_camera, overview, low, ford_camera, plait_camera, ortho, backdrop] + panorama)


# --------------------------------------------------------------------------
# MASK AGREEMENT REPORT
# --------------------------------------------------------------------------

def mask_agreement_report(samples=641):
    """The gate: no dry ground inside the mask, no water outside it."""
    axis = np.linspace(-HALF, HALF, samples, dtype=np.float32)
    grid_x, grid_z = np.meshgrid(axis, axis)
    heights = braid_height(grid_x, grid_z)
    fields = BRAID.fields(grid_x, grid_z)
    zone = BRAID.classify(grid_x, grid_z)
    edge = np.abs(fields["wet"]) < 0.45  # the lip itself is allowed to straddle

    river = (zone == 1) & ~edge
    ford = (zone == 2) & ~edge
    bank = (zone == 0) & ~edge
    wet = river | ford

    def stats(selection):
        values = heights[selection]
        return {
            "samples": int(selection.sum()),
            "minHeight": round(float(values.min()), 4),
            "meanHeight": round(float(values.mean()), 4),
            "maxHeight": round(float(values.max()), 4),
        }

    dry_in_mask = int((heights[wet] > WATER_Y).sum())
    wet_outside_mask = int((heights[bank] < WATER_Y).sum())
    build_zone = bank & (np.abs(grid_z) >= 7.0) & (np.abs(grid_z) <= 30.0) & (np.abs(grid_x) <= 28.0)
    build_heights = heights[build_zone]
    plait = bank & (np.abs(grid_z) < 5.0) & (np.abs(grid_x) < 27.0)

    return {
        "maskId": BRAID.mask["id"],
        "waterPlaneY": WATER_Y,
        "gridSamples": int(samples * samples),
        "transitionBandMetres": 0.45,
        "dryGroundInsideMask": dry_in_mask,
        "waterOutsideMask": wet_outside_mask,
        "zones": {
            "river": stats(river),
            "ford": stats(ford),
            "bank": stats(bank),
            "plaitIsland": stats(plait),
        },
        "channelSeparation": {
            # Sampled on the separated reach only (|x| < 12), where the two cuts
            # are genuinely independent rather than merged at the confluences.
            "northBedMinY": round(float(heights[(fields["north"] <= -1.2) & (np.abs(grid_x) < 12.0)].min()), 4),
            "southBedMinY": round(float(heights[(fields["south"] <= -1.2) & (np.abs(grid_x) < 12.0)].min()), 4),
            "fordMeanY": round(float(heights[zone == 2].mean()), 4),
            "plaitMeanY": round(float(heights[plait].mean()), 4),
        },
        "buildZoneFlatness": {
            "minY": round(float(build_heights.min()), 4),
            "maxY": round(float(build_heights.max()), 4),
            "meanY": round(float(build_heights.mean()), 4),
            "p95AbsSlopePerMetre": round(float(np.percentile(np.abs(np.gradient(heights, axis=1)[build_zone]) / (HALF * 2.0 / (samples - 1)), 95)), 4),
        },
        "mountGround": {
            mount["id"]: {
                "x": mount["position"][0],
                "z": mount["position"][2],
                "zone": ["bank", "river", "ford"][int(BRAID.classify(np.float32(mount["position"][0]), np.float32(mount["position"][2])))],
                "terrainY": round(float(braid_height(np.float32(mount["position"][0]), np.float32(mount["position"][2]))), 4),
            }
            for mount in json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))["landmarkMounts"]
        },
    }


# --------------------------------------------------------------------------
# CONTRACT + EXPORT
# --------------------------------------------------------------------------

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def preview_stats(objects):
    meshes = [obj for obj in objects if obj.type == "MESH"]
    curves = [obj for obj in objects if obj.type == "CURVE"]
    triangles = sum(sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons) for obj in meshes)
    return {
        "exported": False,
        "purpose": "owner composition verdict only; simulation and production fixtures remain code-owned",
        "theme": "true-two-channel-braid-floodplain",
        "landmarks": [
            "opposing_bank_homesteads",
            "paired_winch_towers",
            "two_ford_pans",
            "braid_plait_island",
            "channel_edge_reeds",
        ],
        "objects": len(objects),
        "meshObjects": len(meshes),
        "curveObjects": len(curves),
        "approxTrianglesBeforeCurveTessellation": triangles,
    }


def write_contract(terrain, owner_preview, agreement):
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    coords = np.asarray([vertex.co[:] for vertex in terrain.data.vertices], dtype=np.float32)
    triangles = sum(len(polygon.vertices) - 2 for polygon in terrain.data.polygons)
    contract["boundsMeters"] = {
        "min": [round(float(value), 4) for value in coords.min(axis=0)],
        "max": [round(float(value), 4) for value in coords.max(axis=0)],
    }
    contract["vertices"] = len(terrain.data.vertices)
    contract["triangles"] = triangles
    contract["meshCount"] = 1
    contract["primitiveCount"] = 1
    contract["materialCount"] = 1
    contract["texture"] = {"count": 1, "width": ATLAS_SIZE, "height": ATLAS_SIZE, "embedded": True}
    contract["maskTruth"]["status"] = (
        f"Production Twin Banks and this sculpt share {BRAID.mask['id']}; "
        "gameplay water classification and visible braid ribbons use the authored mask."
    )
    contract["waterTruth"] = {
        "kind": "true_two_channel_braid",
        "maskId": BRAID.mask["id"],
        "channelHalfWidth": BRAID.north["halfWidth"],
        "northChannelDepth": 0.48,
        "southChannelDepth": 0.35,
        "fordPans": [
            {"id": "west-ford", "minX": -19.0, "maxX": -13.0, "minZ": -5.5, "maxZ": 5.5},
            {"id": "east-ford", "minX": 13.0, "maxX": 19.0, "minZ": -5.5, "maxZ": 5.5},
        ],
        "plaitCrowns": [{"x": -7.5, "z": 0.2}, {"x": 7.4, "z": -0.25}],
        "sourcePool": {"minX": -30.0, "maxX": -26.0, "minZ": -2.0, "maxZ": 2.0},
        "agreementLaw": "every metre of this relief is derived from maskTruth.waterMask; the sim mask is the truth",
    }
    contract["maskAgreement"] = agreement
    contract["ownerPreview"] = owner_preview
    contract["sculptRecipe"] = "build_twin_banks_braid.py"
    return contract


def export_asset(terrain, contract):
    blend = OUT / f"{STEM}.blend"
    glb = OUT / f"{STEM}.glb"
    atlas = OUT / f"{STEM}-atlas.png"
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
    CONTRACT_PATH.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    agreement = mask_agreement_report()
    print(json.dumps(agreement, indent=2))
    if agreement["dryGroundInsideMask"] or agreement["waterOutsideMask"]:
        raise SystemExit("mask agreement failed; refusing to export a sculpt that fights the sim")

    claim.reset_scene()
    atlas = braid_atlas()
    material = claim.make_material(atlas)
    material.name = MATERIAL_NAME
    terrain = make_terrain(material)

    preview = make_preview(material)
    owner_preview = preview_stats(preview)
    render_boards(terrain, preview[0], preview)

    claim.remove_objects(preview)
    terrain.hide_render = False
    bpy.context.scene.world = None
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    contract = write_contract(terrain, owner_preview, agreement)
    export_asset(terrain, contract)
    (ARTIFACTS / "twin-banks-braid-mask-agreement.json").write_text(json.dumps(agreement, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: contract[key] for key in ("boundsMeters", "vertices", "triangles", "files")}, indent=2))


if __name__ == "__main__":
    main()
