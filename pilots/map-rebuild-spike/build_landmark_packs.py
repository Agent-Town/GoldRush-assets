"""Build mounted landmark packs from the owner-ruled source ladder.

Existing GLBs supply reusable shape vocabulary. Exact shipped paintings supply
derived silhouettes. New geometry is limited to source-less landmarks. Every
asset is render-only, base-centred, under 3k triangles, and shares one atlas
with the other landmarks in its map pack.

Reproduce a current E3 atlas from the game checkout without altering reviewed geometry:
  Blender --background --python-exit-code 1 --python <this-file> -- \
    --atlas-only blackout-ridge --out <separate-output-root>
The output is <root>/<pack>/<pack>-landmarks-atlas.png. Atlas-only writes
never replace production files or update mount tables and pack hashes.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

import bpy
import mathutils
import numpy as np


# Atlas-only runs from the game checkout; source art now lives in the sibling store.
ROOT = Path.cwd() if "--atlas-only" in sys.argv else Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
LANDMARKS = OUT / "landmarks"
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"
ATLAS_SIZE = 1024
TILE_COUNT = 4

claim_spec = importlib.util.spec_from_file_location("landmark_claim_helpers", OUT / "build_the_claim_terrain.py")
claim = importlib.util.module_from_spec(claim_spec)
claim_spec.loader.exec_module(claim)
claim.mathutils = mathutils

e2_spec = importlib.util.spec_from_file_location("landmark_e2_helpers", OUT / "build_e2_contract_terrains.py")
e2 = importlib.util.module_from_spec(e2_spec)
e2_spec.loader.exec_module(e2)

RUN3D = ROOT / "assets/pilots/run3d"
PLAZA = ROOT / "assets/pilots/plaza-props-3d"
RAILCAR = ROOT / "assets/pilots/railcar-3d/railcar.glb"
CLAIM_OFFICE = ROOT / "assets/pilots/claim-office-3d/claim-office.glb"
STAMP_MILL = ROOT / "assets/pilots/stamp-mill-3d/stamp-mill.glb"
RAIL_ART = ROOT / "assets/processed/ter-rail-elements-r0c2.png"
E1_CONTRACTS = json.loads((ROOT / "assets/contracts/epoch-1-frontier/contracts.json").read_text(encoding="utf-8"))
NIGHT_LANTERN_FIXTURES = next(
    contract["tileParams"]["prePlacedBuildables"]
    for contract in E1_CONTRACTS["contracts"]
    if contract["id"] == "e1-night-shift"
)

SOURCE = {
    "boiler": RUN3D / "boiler-house.glb",
    "lantern": RUN3D / "lantern-post.glb",
    "palisade": RUN3D / "palisade.glb",
    "sluice": RUN3D / "sluice.glb",
    "stockpile": RUN3D / "stockpile.glb",
    "wagon": PLAZA / "covered_wagon.glb",
    "coal": PLAZA / "coal-bin.e2.glb",
    "pipe": PLAZA / "pipe-run.e2.glb",
    "incline_manifold": OUT / "landmarks/pressure-garden/garden-pressure-manifold.glb",
    "incline_pump": OUT / "landmarks/pressure-garden/water-band-pump-station.glb",
    "incline_winch": OUT / "landmarks/twin-banks/north_bank_winch.glb",
    "e4_wagon": PLAZA / "covered_wagon.e4.glb",
    "e4_filling_shed": PLAZA / "filling-shed.e4.glb",
    "e4_fuel_rack": PLAZA / "fuel-rack.e4.glb",
    "e4_road_marker": PLAZA / "road-marker.e4.glb",
    "e4_motor_roadway": PLAZA / "motor-roadway.e4.glb",
    "e4_wrecker_shed": OUT / "landmarks/dust-flats/west-road-wrecker-shed.glb",
    "e4_storm_tower": OUT / "landmarks/dust-flats/north-railhead-storm-tower.glb",
    "e4_recovery_gantry": OUT / "landmarks/dust-flats/dry-wash-recovery-gantry.glb",
    "e5_dinghy": PLAZA / "covered_wagon.e5.glb",
    "e5_lantern": PLAZA / "harbor-lantern.e5.glb",
    "e5_buoy_rack": PLAZA / "rope-buoy-rack.e5.glb",
    "e8_crater_rim": PLAZA / "crater-rim-set.e8.glb",
    "e8_lander_legs": PLAZA / "lander-legs.e8.glb",
    "e9_canal_gate": OUT / "landmarks/dome-basin/canal-gate-works.glb",
    "e9_dust_mast": OUT / "landmarks/dome-basin/dust-devil-warning-mast.glb",
    "e10_bridge_school": OUT / "landmarks/ember-shore/center-vein-bridge-school.glb",
    "e10_preserve_rack": OUT / "landmarks/ember-shore/shore-preserve-rack.glb",
    "e10_titan_shelf": OUT / "landmarks/ember-shore/cooled-titan-shelf.glb",
    "sentry_beacon": RUN3D / "sentry-beacon.glb",
}

PACKS = {
    "the-claim": {
        "era": 1,
        "contract": "the-claim-terrain-contract.json",
        "terrain": "the-claim-terrain.glb",
        "panorama": "the-claim-panorama.glb",
        "plate": ROOT / "assets/raw/plate-contract-the-claim.png",
        "camera": ((0.0, -30.3, 26.26), (0.0, -8.65, 0.51), 42.0),
    },
    "dry-gulch": {
        "era": 1,
        "contract": "dry-gulch-terrain-contract.json",
        "terrain": "dry-gulch-terrain.glb",
        "panorama": "dry-gulch-panorama.glb",
        "plate": ROOT / "assets/raw/plate-contract-dry-gulch.png",
        "camera": ((0.0, -30.3, 26.26), (0.0, -8.65, 0.51), 42.0),
    },
    "twin-banks": {
        "era": 1,
        "contract": "twin-banks-terrain-contract.json",
        "terrain": "twin-banks-terrain.glb",
        "panorama": "twin-banks-panorama.glb",
        "plate": ROOT / "assets/raw/plate-contract-twin-banks.png",
        "camera": ((0.0, -30.3, 26.26), (0.0, -8.65, 0.51), 42.0),
    },
    "night-shift": {
        "era": 1,
        "contract": "night-shift-terrain-contract.json",
        "terrain": "night-shift-terrain.glb",
        "panorama": "night-shift-panorama.glb",
        "plate": ROOT / "assets/raw/plate-contract-night-shift.png",
        "camera": ((0.0, -30.3, 26.26), (0.0, -8.65, 0.51), 42.0),
        "night": True,
    },
    "baron": {
        "era": 1,
        "contract": "baron-terrain-contract.json",
        "terrain": "baron-terrain.glb",
        "panorama": "baron-panorama.glb",
        "plate": ROOT / "assets/raw/plate-contract-baron.png",
        "camera": ((0.0, -30.3, 26.26), (0.0, -8.65, 0.51), 42.0),
    },
    "hill-mine": {
        "era": 2,
        "contract": "hill-mine-terrain-contract.json",
        "terrain": "hill-mine-terrain.glb",
        "panorama": "hill-mine-panorama.glb",
        "plate": ROOT / "assets/raw/plate-contract-hill-mine.png",
        "camera": ((0.0, 35.0, 29.0), (0.0, -12.0, 1.5), 42.0),
    },
    "trestle": {
        "era": 2,
        "contract": "trestle-terrain-contract.json",
        "terrain": "trestle-terrain.glb",
        "panorama": "trestle-panorama.glb",
        "plate": RAIL_ART,
        "camera": ((0.0, 36.0, 28.0), (0.0, 12.0, 0.3), 42.0),
    },
    "incline": {
        "era": 2,
        "contract": "incline-terrain-contract.json",
        "terrain": "incline-terrain.glb",
        "panorama": "incline-panorama.glb",
        "plate": ROOT / "assets/processed/kit-era-2.png",
        "camera": ((28.0, 40.0, 31.0), (0.0, -12.0, 1.55), 43.0),
        "overviewCamera": ((0.0, 62.0, 68.0), (0.0, -4.0, 1.8), 47.0),
        "bodies": [
            "lower-yard-engine-crane",
            "west-line-brake-tower",
            "east-line-brake-tower",
            "upper-ore-cable-house",
            "ford-service-pump",
        ],
        # Verdict-only placement proposal. 3D-D owns canonical mount records.
        "previewMounts": [
            {"id": "lower-yard-engine-crane", "position": [2.0, 0.0, 21.8], "rotation": [0.0, 0.14, 0.0], "scale": [1.05, 1.05, 1.05]},
            {"id": "west-line-brake-tower", "position": [-34.0, 0.0, 36.5], "rotation": [0.0, 0.18, 0.0], "scale": [1.0, 1.0, 1.0]},
            {"id": "east-line-brake-tower", "position": [34.0, 0.0, 35.0], "rotation": [0.0, -0.16, 0.0], "scale": [1.0, 1.0, 1.0]},
            {"id": "upper-ore-cable-house", "position": [22.0, 0.0, 29.0], "rotation": [0.0, -0.10, 0.0], "scale": [1.0, 1.0, 1.0]},
            {"id": "ford-service-pump", "position": [25.0, 0.0, 21.5], "rotation": [0.0, -0.12, 0.0], "scale": [0.78, 0.78, 0.78]},
        ],
    },
    "boneyard": {
        "era": 4,
        "contract": "boneyard-terrain-contract.json",
        "terrain": "boneyard-terrain.glb",
        "panorama": "boneyard-panorama.glb",
        "plate": ROOT / "assets/raw/plate-e4-bld-set.png",
        "camera": ((0.0, 56.0, 38.0), (0.0, -6.0, 0.6), 43.0),
        "overviewCamera": ((0.0, 94.0, 73.0), (0.0, 0.0, 0.6), 48.0),
    },
    "long-road": {
        "era": 4,
        "contract": "long-road-terrain-contract.json",
        "terrain": "long-road-terrain.glb",
        "panorama": "long-road-panorama.glb",
        "plate": ROOT / "assets/processed/kit-era-4.png",
        "camera": ((0.0, 52.0, 35.0), (28.0, 0.0, 0.4), 44.0),
        "overviewCamera": ((0.0, 12.0, 340.0), (0.0, 0.0, 0.0), 51.0),
    },
    "regatta": {
        "era": 5,
        "contract": "regatta-terrain-contract.json",
        "terrain": "regatta-terrain.glb",
        "panorama": "regatta-panorama.glb",
        "plate": ROOT / "assets/raw/plate-e5-bld-claimboat.png",
        "camera": ((-3.0, 49.0, 42.0), (0.0, 13.0, -2.4), 48.0),
        "overviewCamera": ((0.0, 94.0, 120.0), (0.0, 8.0, -2.8), 49.0),
        "bodies": [
            "start-line-rig",
            "finish-line-rig",
            "northwest-buoy-line-anchor",
            "midcourse-buoy-line-anchor",
            "northeast-buoy-line-anchor",
            "spectator-raft-port",
            "spectator-raft-starboard",
            "judges-tower",
        ],
        # Verdict-only composition until 3D-D backfills canonical mounts.
        "previewMounts": [
            {"id": "start-line-rig", "position": [-36.0, 0.0, -3.0], "rotation": [0.0, 0.18, 0.0], "scale": [1.0, 1.0, 1.0]},
            {"id": "finish-line-rig", "position": [36.0, 0.0, -3.0], "rotation": [0.0, -0.12, 0.0], "scale": [1.0, 1.0, 1.0]},
            {"id": "northwest-buoy-line-anchor", "position": [-28.0, 0.0, 38.0], "rotation": [0.0, 0.10, 0.0], "scale": [1.0, 1.0, 1.0]},
            {"id": "midcourse-buoy-line-anchor", "position": [0.0, 0.0, 18.0], "rotation": [0.0, -0.08, 0.0], "scale": [1.0, 1.0, 1.0]},
            {"id": "northeast-buoy-line-anchor", "position": [28.0, 0.0, 38.0], "rotation": [0.0, -0.16, 0.0], "scale": [1.0, 1.0, 1.0]},
            {"id": "spectator-raft-port", "position": [-13.0, 0.0, -18.0], "rotation": [0.0, 0.22, 0.0], "scale": [1.0, 1.0, 1.0]},
            {"id": "spectator-raft-starboard", "position": [17.0, 0.0, -18.0], "rotation": [0.0, -0.20, 0.0], "scale": [1.0, 1.0, 1.0]},
            {"id": "judges-tower", "position": [30.0, 0.0, -9.0], "rotation": [0.0, -0.10, 0.0], "scale": [1.0, 1.0, 1.0]},
        ],
    },
    "relay-valley": {
        "era": 7,
        "contract": "relay-valley-terrain-contract.json",
        "terrain": "relay-valley-terrain.glb",
        "panorama": "relay-valley-panorama.glb",
        "plate": ROOT / "assets/raw/kit-era-7.png",
        "camera": ((0.0, 53.0, 40.0), (0.0, -13.0, 2.2), 46.0),
        "overviewCamera": ((0.0, 98.0, 104.0), (0.0, 0.0, 1.5), 47.0),
        "bodies": [
            "west-ridge-dish-cluster",
            "east-ridge-dish-cluster",
            "dead-gap-charting-station",
            "valley-cable-drum-yard",
            "drone-recovery-beacon",
        ],
        # Verdict-only placement proposal. 3D-D owns canonical mount records.
        # Relay build pads, patrol loop, and the unbridged dead gap stay clear.
        "previewMounts": [
            {"id": "west-ridge-dish-cluster", "position": [-56.0, 0.0, 30.0], "rotation": [0.0, 0.16, 0.0], "scale": [1.0, 1.0, 1.0]},
            {"id": "east-ridge-dish-cluster", "position": [56.0, 0.0, 30.0], "rotation": [0.0, -0.14, 0.0], "scale": [1.0, 1.0, 1.0]},
            {"id": "dead-gap-charting-station", "position": [0.0, 0.0, 18.0], "rotation": [0.0, 0.0, 0.0], "scale": [1.08, 1.08, 1.08]},
            {"id": "valley-cable-drum-yard", "position": [-44.0, 0.0, -26.0], "rotation": [0.0, 0.22, 0.0], "scale": [1.0, 1.0, 1.0]},
            {"id": "drone-recovery-beacon", "position": [44.0, 0.0, -26.0], "rotation": [0.0, -0.20, 0.0], "scale": [1.08, 1.08, 1.08]},
        ],
    },
    "mare-claim": {
        "era": 8,
        "contract": "mare-claim-terrain-contract.json",
        "terrain": "mare-claim-terrain.glb",
        "panorama": "mare-claim-panorama.glb",
        "plate": ROOT / "assets/raw/plate-e8-bld-set.png",
        "camera": ((0.0, 69.0, 49.0), (0.0, -7.0, 1.8), 54.0),
        "overviewCamera": ((0.0, 100.0, 106.0), (0.0, 0.0, 1.0), 47.0),
        "bodies": [
            "earthrise-listening-array",
            "lava-tube-survey-gantry",
            "regolith-core-yard",
            "west-rim-debris-catcher",
            "east-rim-debris-catcher",
        ],
        "previewMounts": [
            {"id": "earthrise-listening-array", "position": [30.0, 0.0, 20.0], "rotation": [0.0, -0.42, 0.0], "scale": [1.34, 1.34, 1.34]},
            {"id": "lava-tube-survey-gantry", "position": [-44.0, 0.0, 12.0], "rotation": [0.0, 0.38, 0.0], "scale": [1.50, 1.50, 1.50]},
            {"id": "regolith-core-yard", "position": [0.0, 0.0, 14.0], "rotation": [0.0, 0.24, 0.0], "scale": [1.50, 1.50, 1.50]},
            {"id": "west-rim-debris-catcher", "position": [-52.0, 0.0, -12.0], "rotation": [0.0, 0.34, 0.0], "scale": [1.42, 1.42, 1.42]},
            {"id": "east-rim-debris-catcher", "position": [52.0, 0.0, -12.0], "rotation": [0.0, -0.34, 0.0], "scale": [1.42, 1.42, 1.42]},
        ],
    },
    "eclipse": {
        "era": 8,
        "contract": "eclipse-terrain-contract.json",
        "terrain": "mare-claim-terrain.glb",
        "panorama": "mare-claim-panorama.glb",
        "plate": ROOT / "assets/raw/plate-e8-bld-set.png",
        "camera": ((0.0, 69.0, 49.0), (0.0, -7.0, 1.8), 54.0),
        "overviewCamera": ((0.0, 100.0, 106.0), (0.0, 0.0, 1.0), 47.0),
        "bodies": [
            "eclipse-shadow-dial",
            "west-rim-solar-witness",
            "east-rim-solar-witness",
            "launch-shadow-gate",
            "mass-driver-eclipse-marker",
        ],
    },
    "devils-alley": {
        "era": 9,
        "contract": "devils-alley-terrain-contract.json",
        "terrain": "devils-alley-terrain.glb",
        "panorama": "devils-alley-panorama.glb",
        "plate": ROOT / "assets/raw/plate-e9-enemy-dust-devil.png",
        "camera": ((0.0, -18.3, 26.2), (0.0, 3.35, 0.45), 42.0),
        "overviewCamera": ((0.0, 102.0, 106.0), (0.0, 0.0, 0.5), 47.0),
    },
    "archive-world": {
        "era": 10,
        "contract": "archive-world-terrain-contract.json",
        "terrain": "archive-world-terrain.glb",
        "panorama": "archive-world-panorama.glb",
        "plate": ROOT / "assets/raw/plate-e10-worlds.png",
        "camera": ((0.0, -18.3, 26.2), (0.0, 3.35, 0.45), 42.0),
        "overviewCamera": ((0.0, 102.0, 106.0), (0.0, 0.0, 0.5), 47.0),
    },
}


def spec(kind, tier, *sources, **options):
    return {"kind": kind, "tier": tier, "sources": list(sources), **options}


SPECS = {
    "active_headframe": spec("headframe", "build-new", "assets/raw/plate-contract-the-claim.png", variant="active"),
    "maintained_claim_house": spec("house", "derive", "assets/pilots/claim-office-3d/claim-office.glb", "assets/processed/bld-claim-office.png", variant="maintained"),
    "working_camp": spec("camp", "reuse", "assets/pilots/plaza-props-3d/covered_wagon.glb", "assets/pilots/run3d/stockpile.glb", conform=True),
    "claim_stake": spec("stake", "build-new", "assets/raw/kit-era-1.png"),
    "riparian_dressing_pack": spec("riparian", "reuse", "assets/pilots/run3d/sluice.glb", conform=True),
    "ruined_mining_operation": spec("ruined-mine", "derive", "assets/pilots/stamp-mill-3d/stamp-mill.glb", "assets/processed/bld-stamp-mill.png"),
    "abandoned_farmhouse": spec("house", "derive", "assets/pilots/claim-office-3d/claim-office.glb", "assets/processed/bld-claim-office.png", variant="abandoned"),
    "cactus_thicket": spec("cactus", "build-new", "assets/raw/plate-contract-dry-gulch.png", conform=True),
    "bison_skeleton": spec("skeleton", "build-new", "assets/raw/plate-contract-dry-gulch.png"),
    "isolated_spring": spec("spring", "build-new", "assets/raw/plate-contract-dry-gulch.png"),
    "north_bank_homestead": spec("house", "derive", "assets/pilots/claim-office-3d/claim-office.glb", "assets/raw/plate-contract-twin-banks.png", variant="north"),
    "south_bank_homestead": spec("house", "derive", "assets/pilots/claim-office-3d/claim-office.glb", "assets/raw/plate-contract-twin-banks.png", variant="south"),
    "north_bank_winch": spec("winch", "build-new", "assets/raw/plate-contract-twin-banks.png", variant="north"),
    "south_bank_winch": spec("winch", "build-new", "assets/raw/plate-contract-twin-banks.png", variant="south"),
    "floodplain_dressing_pack": spec("floodplain", "reuse", "assets/pilots/run3d/sluice.glb", "assets/pilots/run3d/stockpile.glb", conform=True),
    "seven_lantern_terraces": spec("lanterns", "reuse", "assets/pilots/run3d/lantern-post.glb", conform=True),
    "lampworks_yard": spec("lampworks", "reuse", "assets/pilots/run3d/lantern-post.glb", "assets/pilots/run3d/boiler-house.glb", "assets/pilots/run3d/stockpile.glb"),
    "dark_rock_shoulders": spec("rock-shoulders", "build-new", "assets/raw/plate-contract-night-shift.png", conform=True),
    "central_ford": spec("ford", "reuse", "assets/pilots/run3d/sluice.glb"),
    "night_work_road": spec("road", "build-new", "assets/raw/plate-contract-night-shift.png", conform=True),
    "fortified_far_bank": spec("fortified", "reuse", "assets/pilots/run3d/palisade.glb", conform=True),
    "seized_headframe": spec("headframe", "build-new", "assets/raw/plate-contract-baron.png", variant="seized"),
    "rocket_cart": spec("rocket-cart", "reuse", "assets/pilots/railcar-3d/railcar.glb", select="Railcar_Cabin"),
    "siege_line": spec("siege", "reuse", "assets/pilots/run3d/palisade.glb", conform=True),
    "oxblood_banners": spec("banners", "build-new", "assets/raw/plate-contract-baron.png", conform=True),
    "mine-mouth-and-ruined-headframe": spec("headframe", "build-new", "assets/raw/plate-contract-hill-mine.png", variant="ruined"),
    "boiler-house-site": spec("boiler", "reuse", "assets/pilots/run3d/boiler-house.glb", variant="hill"),
    "flooded-gallery": spec("gallery", "derive", "assets/pilots/run3d/sluice.glb", "assets/processed/ter-rail-elements-r0c2.png"),
    "switchback-rail-kit": spec("rail-kit", "derive", "assets/processed/ter-rail-elements-r0c2.png", variant="switchback"),
    "tailings-and-scree-pack": spec("tailings", "reuse", "assets/pilots/run3d/stockpile.glb", conform=True),
    "trestle-crossing": spec("trestle", "derive", "assets/processed/ter-rail-elements-r0c2.png"),
    "south-boiler-site": spec("boiler", "reuse", "assets/pilots/run3d/boiler-house.glb", variant="south"),
    "north-boiler-site": spec("boiler", "reuse", "assets/pilots/run3d/boiler-house.glb", variant="north"),
    "south-approach-kit": spec("approach", "reuse", "assets/pilots/run3d/palisade.glb", "assets/pilots/plaza-props-3d/coal-bin.e2.glb", "assets/pilots/plaza-props-3d/pipe-run.e2.glb", variant="south", conform=True),
    "north-approach-kit": spec("approach", "reuse", "assets/pilots/run3d/palisade.glb", "assets/pilots/plaza-props-3d/coal-bin.e2.glb", "assets/pilots/plaza-props-3d/pipe-run.e2.glb", variant="north", conform=True),
    "mine-spur-kit": spec("mine-spur", "derive", "assets/processed/ter-rail-elements-r0c2.png", "assets/pilots/plaza-props-3d/coal-bin.e2.glb"),
    "lower-yard-engine-crane": spec("incline-worksite", "reuse", "assets/pilots/map-rebuild-spike/landmarks/pressure-garden/garden-pressure-manifold.glb", variant="engine-crane"),
    "west-line-brake-tower": spec("incline-worksite", "reuse", "assets/pilots/map-rebuild-spike/landmarks/twin-banks/north_bank_winch.glb", variant="west-brake"),
    "east-line-brake-tower": spec("incline-worksite", "reuse", "assets/pilots/map-rebuild-spike/landmarks/twin-banks/north_bank_winch.glb", variant="east-brake"),
    "upper-ore-cable-house": spec("incline-worksite", "reuse", "assets/pilots/map-rebuild-spike/landmarks/twin-banks/north_bank_winch.glb", "assets/pilots/plaza-props-3d/coal-bin.e2.glb", variant="cable-house"),
    "ford-service-pump": spec("incline-worksite", "reuse", "assets/pilots/map-rebuild-spike/landmarks/pressure-garden/water-band-pump-station.glb", variant="ford-pump"),
    "flivver-row-west-a": spec("boneyard-flivver", "derive", "assets/pilots/plaza-props-3d/covered_wagon.e4.glb", "assets/raw/plate-e4-enemy-motorgang.png", variant="west-a"),
    "flivver-row-west-b": spec("boneyard-flivver", "derive", "assets/pilots/plaza-props-3d/covered_wagon.e4.glb", "assets/raw/plate-e4-enemy-motorgang.png", variant="west-b"),
    "flivver-row-west-c": spec("boneyard-flivver", "derive", "assets/pilots/plaza-props-3d/covered_wagon.e4.glb", "assets/raw/plate-e4-enemy-motorgang.png", variant="west-c"),
    "spent-boiler-west": spec("boneyard-boiler", "reuse", "assets/pilots/run3d/boiler-house.glb", "assets/raw/plate-e4-bld-set.png", variant="west"),
    "spent-boiler-east": spec("boneyard-boiler", "reuse", "assets/pilots/run3d/boiler-house.glb", "assets/raw/plate-e4-bld-set.png", variant="east"),
    "flivver-row-east-a": spec("boneyard-flivver", "derive", "assets/pilots/plaza-props-3d/covered_wagon.e4.glb", "assets/raw/plate-e4-enemy-motorgang.png", variant="east-a"),
    "flivver-row-east-b": spec("boneyard-flivver", "derive", "assets/pilots/plaza-props-3d/covered_wagon.e4.glb", "assets/raw/plate-e4-enemy-motorgang.png", variant="east-b"),
    "flivver-row-east-c": spec("boneyard-flivver", "derive", "assets/pilots/plaza-props-3d/covered_wagon.e4.glb", "assets/raw/plate-e4-enemy-motorgang.png", variant="east-c"),
    "hauler-bed-north-a": spec("boneyard-hauler-bed", "derive", "assets/pilots/plaza-props-3d/covered_wagon.e4.glb", "assets/raw/boss-land-yacht.png", variant="north-a"),
    "hauler-bed-north-b": spec("boneyard-hauler-bed", "derive", "assets/pilots/plaza-props-3d/covered_wagon.e4.glb", "assets/raw/boss-land-yacht-damage.png", variant="north-b"),
    "half-buried-sleeper": spec("boneyard-sleeper", "derive", "assets/raw/boss-land-yacht-damage.png", "assets/raw/plate-e4-bld-set.png"),
    "unmarked-wagon": spec("boneyard-wagon", "reuse", "assets/pilots/plaza-props-3d/covered_wagon.e4.glb", "assets/raw/plate-e4-bld-set.png"),
    "west-way-station": spec("long-road-station", "reuse", "assets/pilots/map-rebuild-spike/landmarks/dust-flats/west-road-wrecker-shed.glb", "assets/pilots/plaza-props-3d/fuel-rack.e4.glb", variant="west"),
    "middle-way-station": spec("long-road-station", "reuse", "assets/pilots/plaza-props-3d/filling-shed.e4.glb", "assets/pilots/plaza-props-3d/fuel-rack.e4.glb", variant="middle"),
    "east-way-station": spec("long-road-station", "reuse", "assets/pilots/map-rebuild-spike/landmarks/dust-flats/north-railhead-storm-tower.glb", "assets/pilots/plaza-props-3d/road-marker.e4.glb", variant="east"),
    "convoy-lead-hauler-start": spec("long-road-hauler", "derive", "assets/pilots/plaza-props-3d/covered_wagon.e4.glb", "assets/raw/plate-e4-enemy-motorgang.png", "assets/raw/boss-land-yacht.png"),
    "east-railhead": spec("long-road-railhead", "reuse", "assets/pilots/map-rebuild-spike/landmarks/dust-flats/dry-wash-recovery-gantry.glb", "assets/pilots/plaza-props-3d/motor-roadway.e4.glb"),
    "start-line-rig": spec("race-gate", "reuse", "assets/pilots/plaza-props-3d/harbor-lantern.e5.glb", "assets/pilots/plaza-props-3d/rope-buoy-rack.e5.glb", variant="start"),
    "finish-line-rig": spec("race-gate", "reuse", "assets/pilots/plaza-props-3d/harbor-lantern.e5.glb", "assets/pilots/plaza-props-3d/rope-buoy-rack.e5.glb", variant="finish"),
    "northwest-buoy-line-anchor": spec("buoy-anchor", "reuse", "assets/pilots/plaza-props-3d/rope-buoy-rack.e5.glb", "assets/raw/prop-buoys.png", variant="northwest"),
    "midcourse-buoy-line-anchor": spec("buoy-anchor", "reuse", "assets/pilots/plaza-props-3d/rope-buoy-rack.e5.glb", "assets/raw/prop-buoys.png", variant="midcourse"),
    "northeast-buoy-line-anchor": spec("buoy-anchor", "reuse", "assets/pilots/plaza-props-3d/rope-buoy-rack.e5.glb", "assets/raw/prop-buoys.png", variant="northeast"),
    "spectator-raft-port": spec("spectator-raft", "reuse", "assets/pilots/plaza-props-3d/covered_wagon.e5.glb", "assets/raw/plate-e5-bld-claimboat.png", variant="port"),
    "spectator-raft-starboard": spec("spectator-raft", "reuse", "assets/pilots/plaza-props-3d/covered_wagon.e5.glb", "assets/raw/plate-e5-bld-claimboat.png", variant="starboard"),
    "judges-tower": spec("judges-tower", "derive", "assets/raw/plate-e5-bld-lighthouse.png", "assets/raw/plate-e5-bld-claimboat.png"),
    "west-ridge-dish-cluster": spec("ridge-dish-cluster", "derive", "assets/raw/kit-era-7.png", "assets/raw/plate-e7-bld-relay-tower.png", variant="west"),
    "east-ridge-dish-cluster": spec("ridge-dish-cluster", "derive", "assets/raw/kit-era-7.png", "assets/raw/plate-e7-bld-relay-tower.png", variant="east"),
    "dead-gap-charting-station": spec("dead-gap-chart-station", "derive", "assets/raw/kit-era-7.png", "assets/raw/plate-e7-bld-playbook-library.png"),
    "valley-cable-drum-yard": spec("signal-cable-yard", "reuse", "assets/pilots/run3d/stockpile.glb", "assets/raw/kit-era-7.png"),
    "drone-recovery-beacon": spec("drone-recovery-beacon", "reuse", "assets/pilots/run3d/sentry-beacon.glb", "assets/raw/kit-era-7.png"),
    "earthrise-listening-array": spec("earthrise-listening-array", "derive", "assets/raw/plate-e8-bld-set.png", "assets/processed/kit-era-8.png"),
    "lava-tube-survey-gantry": spec("lava-tube-survey-gantry", "derive", "assets/raw/plate-e8-bld-set.png", "assets/processed/kit-era-8.png"),
    "regolith-core-yard": spec("regolith-core-yard", "reuse", "assets/pilots/plaza-props-3d/crater-rim-set.e8.glb", "assets/raw/plate-e8-bld-set.png"),
    "west-rim-debris-catcher": spec("rim-debris-catcher", "reuse", "assets/pilots/plaza-props-3d/lander-legs.e8.glb", "assets/raw/plate-e8-bld-set.png", variant="west"),
    "east-rim-debris-catcher": spec("rim-debris-catcher", "reuse", "assets/pilots/plaza-props-3d/lander-legs.e8.glb", "assets/raw/plate-e8-bld-set.png", variant="east"),
    "eclipse-shadow-dial": spec("eclipse-kit", "derive", "assets/raw/plate-e8-bld-set.png", "assets/processed/kit-era-8.png", variant="shadow-dial"),
    "west-rim-solar-witness": spec("eclipse-kit", "derive", "assets/raw/plate-e8-bld-set.png", "assets/processed/kit-era-8.png", variant="west-witness"),
    "east-rim-solar-witness": spec("eclipse-kit", "derive", "assets/raw/plate-e8-bld-set.png", "assets/processed/kit-era-8.png", variant="east-witness"),
    "launch-shadow-gate": spec("eclipse-kit", "derive", "assets/raw/plate-e8-bld-set.png", "assets/pilots/map-rebuild-spike/landmarks/mare-claim/lava-tube-survey-gantry.glb", variant="launch-gate"),
    "mass-driver-eclipse-marker": spec("eclipse-kit", "derive", "assets/raw/plate-e8-bld-set.png", "assets/processed/kit-era-8.png", variant="driver-marker"),
    "south-anchor-gate": spec("storm-anchor-gate", "derive", "assets/pilots/map-rebuild-spike/landmarks/dome-basin/canal-gate-works.glb", "assets/raw/plate-e9-enemy-dust-devil.png", variant="south"),
    "west-wind-anchor": spec("wind-anchor", "reuse", "assets/pilots/map-rebuild-spike/landmarks/dome-basin/dust-devil-warning-mast.glb", "assets/raw/plate-e9-enemy-dust-devil.png", variant="west"),
    "center-wind-anchor": spec("wind-anchor", "derive", "assets/pilots/map-rebuild-spike/landmarks/dome-basin/dust-devil-warning-mast.glb", "assets/raw/plate-e9-enemy-dust-devil.png", variant="center"),
    "east-wind-anchor": spec("wind-anchor", "derive", "assets/pilots/map-rebuild-spike/landmarks/dome-basin/dust-devil-warning-mast.glb", "assets/raw/plate-e9-enemy-dust-devil.png", variant="east"),
    "north-anchor-gate": spec("storm-anchor-gate", "derive", "assets/pilots/map-rebuild-spike/landmarks/dome-basin/canal-gate-works.glb", "assets/raw/plate-e9-enemy-dust-devil.png", variant="north"),
    "archive-entry-gate": spec("archive-entry-gate", "derive", "assets/pilots/map-rebuild-spike/landmarks/ember-shore/center-vein-bridge-school.glb", "assets/raw/plate-e10-worlds.png"),
    "west-stack-ruin": spec("archive-stack-ruin", "derive", "assets/raw/plate-contract-e10-archive-world.png", variant="west"),
    "east-stack-ruin": spec("archive-stack-ruin", "derive", "assets/raw/plate-contract-e10-archive-world.png", variant="east"),
    "warning-shelf-ruin": spec("archive-warning-shelf", "derive", "assets/raw/plate-contract-e10-archive-world.png"),
    "ours-unless-marker": spec("ours-unless-marker", "derive", "assets/raw/plate-e10-worlds.png", "assets/raw/plate-e10-charter-press-hall.png"),
}

ROLE_COLORS = {
    "timber": (0.32, 0.16, 0.055),
    "iron": (0.20, 0.14, 0.085),
    "stone": (0.26, 0.23, 0.18),
    "earth": (0.40, 0.22, 0.075),
    "water": (0.095, 0.070, 0.035),
    "cactus": (0.09, 0.21, 0.07),
    "bone": (0.56, 0.48, 0.33),
    "cloth": (0.32, 0.045, 0.025),
    "brass": (0.42, 0.26, 0.07),
    "soot": (0.075, 0.050, 0.035),
    "parchment": (0.61, 0.46, 0.27),
    "rust": (0.38, 0.10, 0.03),
}
ROLE_INDEX = {role: index for index, role in enumerate(ROLE_COLORS)}

# The accepted E1 pack reads as painted illustration because its material
# separates sun-bleached faces from deep ink pockets.  Keep that value range
# for the two E2 packs instead of the older near-black proxy palette.
E2_ROLE_COLORS = {
    **ROLE_COLORS,
    "timber": (0.42, 0.235, 0.080),
    "iron": (0.235, 0.205, 0.155),
    "stone": (0.355, 0.305, 0.225),
    "earth": (0.50, 0.295, 0.095),
    "water": (0.125, 0.090, 0.048),
    "cloth": (0.42, 0.070, 0.025),
    "brass": (0.60, 0.390, 0.105),
    "parchment": (0.69, 0.535, 0.300),
    "rust": (0.40, 0.120, 0.030),
}

# E3 recipe provenance: Fairground 7b930acc1; Canyon Works 07bcf8834 plus run-4
# timber/iron/stone separation (2026-09-21, regrade_canyon_landmarks.py).
# Blackout uses the later grounded-stone/brass repair, not its original V1 palette.
# Moth's shipped PNG and embedded GLB still match 75beb002c, despite its newer atlas metadata.
E3_ROLE_COLORS = {
    **ROLE_COLORS,
    "timber": (0.36, 0.205, 0.080),
    "iron": (0.155, 0.205, 0.225),
    "stone": (0.260, 0.285, 0.300),
    "earth": (0.37, 0.205, 0.080),
    "water": (0.045, 0.50, 0.46),
    "cactus": (0.070, 0.25, 0.18),
    "bone": (0.69, 0.58, 0.37),
    "cloth": (0.29, 0.050, 0.025),
    "brass": (0.65, 0.405, 0.095),
    "soot": (0.035, 0.050, 0.070),
    "parchment": (0.75, 0.59, 0.32),
    "rust": (0.42, 0.130, 0.040),
}

E3_CANYON_ROLE_COLORS = {
    **ROLE_COLORS,
    "timber": (0.44, 0.285, 0.145),
    "iron": (0.265, 0.300, 0.310),
    "stone": (0.355, 0.365, 0.360),
    "earth": (0.38, 0.220, 0.095),
    "water": (0.045, 0.48, 0.44),
    "cactus": (0.075, 0.25, 0.18),
    "bone": (0.59, 0.49, 0.30),
    "cloth": (0.25, 0.050, 0.025),
    "brass": (0.64, 0.405, 0.095),
    "soot": (0.045, 0.060, 0.075),
    "parchment": (0.69, 0.53, 0.275),
    "rust": (0.43, 0.140, 0.045),
}

E3_ATLAS_RECIPES = {
    "blackout-ridge": {
        "era": 3,
        "plate": ROOT / "assets/raw/plate-e3-bld-pylon-set.png",
        "colors": {**E3_ROLE_COLORS, "stone": (0.115, 0.098, 0.078), "brass": (0.78, 0.500, 0.120)},
    },
    "canyon-works": {
        "era": 3,
        "plate": ROOT / "assets/raw/ter-canyon-atlas.png",
        "colors": E3_CANYON_ROLE_COLORS,
    },
    "fairground": {
        "era": 3,
        "plate": ROOT / "assets/raw/plate-e3-bld-arc-lamp.png",
        "colors": E3_ROLE_COLORS,
    },
    "moth-season": {
        "era": 3,
        "plate": ROOT / "assets/raw/plate-e3-mothswarm.png",
        "colors": E3_ROLE_COLORS,
    },
}

E4_ROLE_COLORS = {
    **ROLE_COLORS,
    "timber": (0.34, 0.20, 0.080), "iron": (0.12, 0.11, 0.090),
    "stone": (0.25, 0.22, 0.17), "earth": (0.43, 0.27, 0.10),
    "water": (0.04, 0.35, 0.32), "cactus": (0.10, 0.24, 0.08),
    "bone": (0.63, 0.52, 0.32), "cloth": (0.35, 0.07, 0.03),
    "brass": (0.60, 0.37, 0.09), "soot": (0.035, 0.025, 0.020),
    "parchment": (0.70, 0.52, 0.28), "rust": (0.39, 0.11, 0.025),
}

E5_ROLE_COLORS = {
    **ROLE_COLORS,
    "timber": (0.20, 0.12, 0.055),
    "iron": (0.11, 0.12, 0.105),
    "stone": (0.16, 0.19, 0.17),
    "earth": (0.20, 0.16, 0.095),
    "water": (0.045, 0.23, 0.24),
    "cactus": (0.08, 0.34, 0.34),
    "bone": (0.63, 0.52, 0.30),
    "cloth": (0.40, 0.095, 0.040),
    "brass": (0.62, 0.40, 0.10),
    "soot": (0.030, 0.038, 0.036),
    "parchment": (0.70, 0.55, 0.30),
    "rust": (0.38, 0.12, 0.035),
}

E7_ROLE_COLORS = {
    **ROLE_COLORS,
    "timber": (0.31, 0.17, 0.065),
    "iron": (0.095, 0.12, 0.105),
    "stone": (0.22, 0.25, 0.20),
    "earth": (0.30, 0.23, 0.105),
    "water": (0.035, 0.46, 0.43),
    "cactus": (0.08, 0.33, 0.30),
    "bone": (0.62, 0.50, 0.27),
    "cloth": (0.24, 0.060, 0.030),
    "brass": (0.67, 0.43, 0.095),
    "soot": (0.025, 0.035, 0.030),
    "parchment": (0.71, 0.53, 0.25),
    "rust": (0.33, 0.085, 0.025),
}

E8_ROLE_COLORS = {
    **ROLE_COLORS,
    "timber": (0.26, 0.19, 0.105),
    "iron": (0.34, 0.37, 0.35),
    "stone": (0.38, 0.37, 0.32),
    "earth": (0.30, 0.28, 0.235),
    "water": (0.035, 0.50, 0.49),
    "cactus": (0.10, 0.35, 0.34),
    "bone": (0.72, 0.66, 0.50),
    "cloth": (0.34, 0.065, 0.030),
    "brass": (0.65, 0.43, 0.105),
    "soot": (0.020, 0.025, 0.024),
    "parchment": (0.68, 0.62, 0.47),
    "rust": (0.31, 0.105, 0.040),
}

E9_ROLE_COLORS = {
    **ROLE_COLORS,
    "timber": (0.30, 0.12, 0.045), "iron": (0.20, 0.17, 0.13),
    "stone": (0.34, 0.20, 0.14), "earth": (0.43, 0.12, 0.035),
    "water": (0.05, 0.42, 0.37), "cactus": (0.14, 0.43, 0.12),
    "bone": (0.67, 0.53, 0.31), "cloth": (0.42, 0.075, 0.025),
    "brass": (0.68, 0.40, 0.08), "soot": (0.035, 0.025, 0.022),
    "parchment": (0.72, 0.50, 0.25), "rust": (0.47, 0.09, 0.025),
}

E10_ROLE_COLORS = {
    **ROLE_COLORS,
    "timber": (0.22, 0.15, 0.070), "iron": (0.075, 0.095, 0.090),
    "stone": (0.18, 0.18, 0.16), "earth": (0.24, 0.17, 0.075),
    "water": (0.04, 0.46, 0.44), "cactus": (0.08, 0.30, 0.28),
    "bone": (0.70, 0.61, 0.40), "cloth": (0.29, 0.055, 0.030),
    "brass": (0.72, 0.48, 0.11), "soot": (0.012, 0.018, 0.018),
    "parchment": (0.76, 0.61, 0.34), "rust": (0.32, 0.09, 0.030),
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_atlas(key, profile, *, output_root=None):
    directory = (LANDMARKS if output_root is None else Path(output_root)) / key
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{key}-landmarks-atlas.png"
    if profile["era"] == 3:
        # Unknown E3 packs must not silently fall through to the darker default palette.
        profile = E3_ATLAS_RECIPES[key]
    kit = claim.image_pixels(ROOT / f"assets/processed/kit-era-{profile['era']}.png")
    plate = claim.image_pixels(profile["plate"])
    axis = np.linspace(0.0, 1.0, ATLAS_SIZE, dtype=np.float32)
    u, v = np.meshgrid(axis, axis)
    kit_sample = claim.tiled_sample(kit, u, v, 3.7, 0.13, 0.47)
    plate_sample = claim.tiled_sample(plate, u, v, 4.3, 0.51, 0.19)
    source = kit_sample * 0.46 + plate_sample * 0.54
    luma = claim.luminance(source)
    low, high = np.percentile(luma, (5.0, 95.0))
    grain = np.clip((luma - low) / max(high - low, 0.001), 0.0, 1.0)
    ink = claim.engraved_ink(plate, u, v, 4.0, 0.29, 0.61)
    atlas = np.zeros((ATLAS_SIZE, ATLAS_SIZE, 3), dtype=np.float32)
    tile = ATLAS_SIZE // TILE_COUNT
    colors = profile["colors"] if profile["era"] == 3 else E2_ROLE_COLORS if profile["era"] == 2 else E4_ROLE_COLORS if profile["era"] == 4 else E5_ROLE_COLORS if profile["era"] == 5 else E7_ROLE_COLORS if profile["era"] == 7 else E8_ROLE_COLORS if profile["era"] == 8 else E9_ROLE_COLORS if profile["era"] == 9 else E10_ROLE_COLORS if profile["era"] == 10 else ROLE_COLORS
    for role, index in ROLE_INDEX.items():
        row, column = divmod(index, TILE_COUNT)
        y0, y1 = row * tile, (row + 1) * tile
        x0, x1 = column * tile, (column + 1) * tile
        value = 0.52 + grain[y0:y1, x0:x1, None] * 0.78
        color = np.asarray(colors[role], dtype=np.float32)
        patch = color[None, None, :] * value
        ink_weight = 0.34 if profile["era"] == 2 else 0.25
        patch *= 1.0 - ink[y0:y1, x0:x1, None] * (ink_weight if role not in {"soot", "iron"} else 0.16)
        hatch = np.clip((np.sin((u[y0:y1, x0:x1] + v[y0:y1, x0:x1] * 0.42) * math.tau * 74.0) - 0.86) / 0.14, 0.0, 1.0)
        scratch = np.clip((np.sin((u[y0:y1, x0:x1] * 0.18 - v[y0:y1, x0:x1]) * math.tau * 113.0 + index * 0.7) - 0.91) / 0.09, 0.0, 1.0)
        patch *= 1.0 - hatch[..., None] * 0.13
        patch *= 1.0 - scratch[..., None] * (0.15 if profile["era"] == 2 else 0.0)
        if profile["era"] == 2 and role in {"timber", "iron", "rust", "soot"}:
            stain = np.clip((np.sin((u[y0:y1, x0:x1] * 0.63 + v[y0:y1, x0:x1]) * math.tau * 17.0 + index) - 0.45) / 0.55, 0.0, 1.0)
            patch *= 1.0 - stain[..., None] * 0.10
        atlas[y0:y1, x0:x1] = patch
    rgba = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    rgba[:, :, :3] = np.clip(atlas, 0.008, 0.82)
    image = bpy.data.images.new(f"{key.title()}LandmarkAtlas", ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image, path


def make_material(key, image):
    material = bpy.data.materials.new(f"{key.title()}LandmarkPackMaterial")
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = 0.92
    shader.inputs["Metallic"].default_value = 0.0
    texture = material.node_tree.nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Linear"
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    return material


def role_object(obj, role):
    obj["landmark_role"] = role
    return obj


def add_box(name, location, dimensions, role="timber", rotation=0.0):
    width, depth, height = dimensions
    x, y, base = location
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, base + height * 0.5), rotation=(0.0, 0.0, rotation))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return role_object(obj, role)


def add_cylinder(name, start, end, radius, role="iron", vertices=8):
    start = mathutils.Vector(start)
    end = mathutils.Vector(end)
    direction = end - start
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=direction.length, location=(start + end) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    return role_object(obj, role)


def add_beam(name, start, end, width=0.18, role="timber"):
    start = mathutils.Vector(start)
    end = mathutils.Vector(end)
    direction = end - start
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(start + end) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = (width, width, direction.length)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return role_object(obj, role)


def add_rock(name, location, scale, role="stone"):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return role_object(obj, role)


def add_torus(name, location, major, minor, role="iron", rotation=(math.pi * 0.5, 0.0, 0.0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=12, minor_segments=4, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    return role_object(obj, role)


def add_dish(name, location, radius, role="water", yaw=0.0):
    """A shallow signal dish facing the gameplay camera axis."""
    bpy.ops.mesh.primitive_cone_add(
        vertices=14, radius1=radius, radius2=radius * 0.24, depth=radius * 0.48,
        location=location, rotation=(math.pi * 0.5, 0.0, yaw),
    )
    dish = bpy.context.object
    dish.name = name
    return role_object(dish, role)


def normalize_object(obj, dimensions=None):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if dimensions:
        obj.dimensions = dimensions
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # All component transforms are applied before this point, so local vertex
    # coordinates are the authoritative export bounds. Blender can retain a
    # stale object bound_box after joining imported GLBs.
    points = [vertex.co.copy() for vertex in obj.data.vertices]
    minimum = mathutils.Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maximum = mathutils.Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    shift = mathutils.Vector((-(minimum.x + maximum.x) * 0.5, -(minimum.y + maximum.y) * 0.5, -minimum.z))
    for vertex in obj.data.vertices:
        vertex.co += shift
    obj.data.update()
    bpy.context.view_layer.update()
    obj.select_set(False)
    return obj


def import_source(path, role, dimensions=None, select=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported = [obj for obj in bpy.data.objects if obj not in before]
    meshes = []
    for obj in imported:
        if obj.type == "MESH" and (select is None or select in obj.name):
            matrix = obj.matrix_world.copy()
            obj.parent = None
            obj.matrix_world = matrix
            meshes.append(obj)
    for obj in imported:
        if obj not in meshes and obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
    if not meshes:
        raise ValueError(f"no source mesh matched {path} {select or ''}")
    if len(meshes) > 1:
        bpy.ops.object.select_all(action="DESELECT")
        for obj in meshes:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.object.join()
        obj = bpy.context.object
    else:
        obj = meshes[0]
    obj.name = f"Source.{Path(path).stem}"
    normalize_object(obj, dimensions)
    return role_object(obj, role)


def place(obj, location, yaw=0.0, scale=1.0):
    obj.location = location
    obj.rotation_euler.z = yaw
    obj.scale = (scale, scale, scale)
    return obj


def map_uv(obj, role):
    while obj.data.uv_layers:
        obj.data.uv_layers.remove(obj.data.uv_layers[0])
    layer = obj.data.uv_layers.new(name="LandmarkAtlasUV")
    index = ROLE_INDEX[role]
    row, column = divmod(index, TILE_COUNT)
    for polygon in obj.data.polygons:
        polygon.material_index = 0
        for loop_index in polygon.loop_indices:
            co = obj.data.vertices[obj.data.loops[loop_index].vertex_index].co
            local_u = (co.x * 0.13 + co.z * 0.07) % 1.0
            local_v = (co.y * 0.13 + co.z * 0.11) % 1.0
            layer.data[loop_index].uv = ((column + 0.08 + local_u * 0.84) / TILE_COUNT, (row + 0.08 + local_v * 0.84) / TILE_COUNT)


def conform_parts_to_terrain(parts, terrain, mount, locked_offset=None):
    """Ground distributed rigid pieces without bending their silhouettes.

    The runtime seam mounts one asset at Terrain.visualY. Map-wide packs still
    need their separate posts, stones, sleepers, and props authored relative
    to that origin; otherwise a flat local Z=0 buries them in sculpted banks.
    """
    mount_x, _offset_y, mount_z = mount["position"]
    yaw = mount["rotation"][1]
    scale = mount["scale"][0]
    cosine, sine = math.cos(yaw), math.sin(yaw)
    origin_height = terrain_height(terrain, mount_x, mount_z)
    for obj in parts:
        bounds = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
        local_x = (min(point.x for point in bounds) + max(point.x for point in bounds)) * 0.5
        local_blender_y = (min(point.y for point in bounds) + max(point.y for point in bounds)) * 0.5
        local_game_z = -local_blender_y
        game_x = mount_x + scale * (cosine * local_x - sine * local_game_z)
        game_z = mount_z + scale * (sine * local_x + cosine * local_game_z)
        obj.location.z += (terrain_height(terrain, game_x, game_z) - origin_height) / scale
    bpy.context.view_layer.update()
    if locked_offset is not None:
        # Body-only replacements cannot move their shipped mount. Keep most
        # pieces terrain-conformed, but lift any newly wider piece that would
        # force a different base-centre compensation.
        locked_minimum = locked_offset / scale
        for obj in parts:
            minimum = min((obj.matrix_world @ mathutils.Vector(corner)).z for corner in obj.bound_box)
            if minimum < locked_minimum:
                obj.location.z += locked_minimum - minimum
        bpy.context.view_layer.update()
    minimum_z = min(
        (obj.matrix_world @ mathutils.Vector(corner)).z
        for obj in parts
        for corner in obj.bound_box
    )
    if locked_offset is not None:
        assert abs(minimum_z * scale - locked_offset) < 2e-6
    # finish_asset base-centres the joined mesh by subtracting this minimum.
    # Carry the same amount into the mount so the world-space grounding remains
    # unchanged and repeated rebuilds stay deterministic.
    return minimum_z * scale


def finish_asset(parts, identifier, material, pack, source_spec):
    meshes = []
    for obj in parts:
        if obj.type != "MESH":
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.convert(target="MESH")
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        map_uv(obj, obj.get("landmark_role", "timber"))
        obj.data.materials.clear()
        obj.data.materials.append(material)
        obj.select_set(False)
        meshes.append(obj)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    asset = bpy.context.object
    asset.name = identifier
    asset.data.name = f"{identifier}.mesh"
    asset.data.materials.clear()
    asset.data.materials.append(material)
    if asset.data.shape_keys:
        asset.shape_key_clear()
        asset.data.update()
        asset.update_tag(refresh={"DATA"})
        bpy.context.view_layer.update()
    # The spring is authored around a fixed water centre and bank datum.
    if identifier != "isolated_spring":
        normalize_object(asset)
    for custom_key in list(asset.keys()):
        del asset[custom_key]
    asset["render_only"] = True
    asset["landmark"] = True
    asset["mount_id"] = identifier
    asset["map_pack"] = pack
    asset["source_tier"] = source_spec["tier"]
    asset["era"] = PACKS[pack]["era"]
    asset["simulation_authority"] = "none; mounted render-only scenery"
    triangles = sum(len(poly.vertices) - 2 for poly in asset.data.polygons)
    if triangles > 3000:
        raise ValueError(f"{identifier} exceeds 3k triangle budget: {triangles}")
    asset.select_set(False)
    return asset


def headframe_parts(variant):
    parts = []
    lean = 0.36 if variant == "ruined" else 0.0
    top = 6.15
    for index, (bx, by, tx, ty) in enumerate(((-1.85, -1.10, -1.05, -0.62), (1.85, -1.10, 1.05, -0.62), (-1.85, 1.10, -1.05, 0.62), (1.85, 1.10, 1.05, 0.62))):
        if variant == "ruined" and index == 3:
            parts.append(add_beam(f"Headframe.BrokenLeg.{index}", (bx, by, 0.0), (tx + 0.42, ty, top * 0.52), 0.27))
        else:
            parts.append(add_beam(f"Headframe.Leg.{index}", (bx, by, 0.0), (tx + lean, ty, top), 0.27))
    for y in (-0.66, 0.66):
        parts.extend([
            add_beam(f"Headframe.Top.{y}", (-1.28 + lean, y, top), (1.28 + lean, y, top), 0.28),
            add_beam(f"Headframe.BraceA.{y}", (-1.65, y, 0.55), (1.02 + lean, y, top - 0.35), 0.15, "timber"),
        ])
        if not (variant == "ruined" and y > 0):
            parts.append(add_beam(f"Headframe.BraceB.{y}", (1.65, y, 0.55), (-1.02 + lean, y, top - 0.35), 0.15, "timber"))
    parts.extend([
        add_beam("Headframe.Ridge", (lean, -0.90, top + 0.65), (lean, 0.90, top + 0.65), 0.21),
        add_torus("Headframe.Wheel", (lean, -0.74, top + 0.04), 0.58, 0.08, "iron"),
        add_cylinder("Headframe.Axle", (lean, -0.84, top + 0.04), (lean, 0.84, top + 0.04), 0.09, "brass", 10),
        add_cylinder("Headframe.Rope", (lean, -0.74, top - 2.9), (lean, -0.74, top - 0.35), 0.034, "parchment", 6),
        add_box("Headframe.Platform", (0, 0, 0.2), (4.4, 2.8, 0.28), "timber"),
        add_box("Headframe.MineMouth", (0, 1.23, 0.35), (2.5, 0.42, 1.25), "soot"),
    ])
    for index, x in enumerate((-1.25, 0.0, 1.25)):
        parts.append(add_rock(f"Headframe.Tailing.{index}", (x, 1.7 + index * 0.12, 0.24), (0.65, 0.48, 0.28 + index * 0.08), "stone"))
    if variant == "seized":
        parts.extend([add_box("Headframe.Patch", (1.25, 0.13, 3.0), (0.8, 0.08, 1.3), "rust", 0.16), add_beam("Headframe.Spear", (-2.0, 0.5, 0), (-2.0, 0.5, 4.4), 0.12, "iron")])
    if variant == "ruined":
        parts.extend([
            add_beam("Headframe.Fallen", (-2.2, 1.0, 0.1), (2.0, 1.25, 0.65), 0.18, "timber"),
            add_box("Headframe.PatchedSign", (-1.25, -1.18, 3.0), (0.85, 0.08, 1.15), "parchment", -0.13),
        ])
    return parts


def boiler_worksite_parts(variant):
    """Articulated E2 worksite derived from the boiler-house shape family."""
    side = -1 if variant == "south" else 1
    parts = [
        add_box("Boiler.Foundation", (0, 0, 0), (7.8, 5.8, 0.22), "soot"),
        add_box("Boiler.Shed", (-0.8, 0, 0.2), (4.8, 4.8, 3.25), "timber", -0.035 * side),
        add_box("Boiler.PatchedRoof", (-0.6, 0, 3.38), (5.7, 5.35, 0.24), "rust", 0.055 * side),
        add_cylinder("Boiler.Drum", (1.0, -1.45, 1.45), (1.0, 1.45, 1.45), 1.05, "iron", 14),
        add_cylinder("Boiler.Stack", (-1.65, 0.55, 0.2), (-1.65, 0.55, 6.0), 0.42, "soot", 12),
        add_cylinder("Boiler.StackCap", (-1.65, 0.55, 5.86), (-1.65, 0.55, 6.18), 0.57, "iron", 12),
        add_torus("Boiler.Gauge", (2.02, -0.62, 2.02), 0.32, 0.055, "brass"),
        add_torus("Boiler.Valve", (2.02, 0.50, 1.65), 0.42, 0.055, "rust"),
        add_cylinder("Boiler.FeedPipe", (1.55, 0.9, 2.05), (3.7, side * 2.7, 1.15), 0.15, "rust", 8),
        add_box("Boiler.ServiceDoor", (-0.9, -2.43, 0.22), (1.2, 0.12, 2.15), "soot", 0.02 * side),
    ]
    for index, x in enumerate((-2.6, -0.9, 0.8)):
        parts.append(add_box(f"Boiler.RepairBatten.{index}", (x, -2.48, 1.0), (0.14, 0.08, 1.7 - index * 0.15), "parchment", (-0.07, 0.04, -0.05)[index]))
    for index, z in enumerate((1.0, 2.15, 3.3, 4.45)):
        parts.append(add_torus(f"Boiler.StackBand.{index}", (-1.65, 0.55, z), 0.43, 0.045, "brass", (0, 0, 0)))
    if variant == "hill":
        parts.extend([
            add_box("Boiler.SootApron", (0.6, -3.1, 0.04), (7.2, 2.2, 0.08), "soot", -0.08),
            add_beam("Boiler.FallenRafter", (-3.6, 2.7, 0.1), (2.9, 2.9, 0.75), 0.16, "timber"),
        ])
    else:
        parts.append(add_box("Boiler.WarningPlate", (1.55, -2.52, 1.55), (1.25, 0.07, 0.72), "brass", 0.04 * side))
    return parts


def approach_worksite_parts(variant):
    side = -1 if variant == "south" else 1
    parts = [
        place(import_source(SOURCE["palisade"], "timber", (5.6, 1.0, 3.7)), (-4.4, 0, 0), side * 0.07),
        place(import_source(SOURCE["coal"], "timber", (3.4, 2.5, 1.5)), (2.6, side * 1.2, 0), -side * 0.12),
        place(import_source(SOURCE["pipe"], "iron", (5.8, 2.0, 1.8)), (4.0, -side * 1.75, 0), side * 0.14),
        add_box("Approach.TarScar", (0.8, -side * 2.6, 0.025), (6.8, 2.2, 0.05), "soot", side * 0.08),
        add_beam("Approach.BrokenGate", (-1.8, 0.8, 0.15), (1.9, 1.2, 0.65), 0.16, "timber"),
    ]
    for index, x in enumerate((-0.8, 0.2, 1.2)):
        parts.append(add_cylinder(f"Approach.Drum.{index}", (x, -side * 1.8, 0), (x, -side * 1.8, 0.9), 0.34, "rust", 10))
    for index in range(5):
        parts.append(add_rock(f"Approach.Rubble.{index}", (-1.8 + index * 0.75, side * (2.2 + 0.25 * (index % 2)), 0.25), (0.45 + 0.08 * (index % 2), 0.35, 0.28), "stone"))
    return parts


def cactus_parts():
    parts = []
    positions = [(-4, -2, 2.8), (-2, 1, 3.8), (0, -1, 2.4), (2, 2, 4.2), (4, -1.5, 3.2), (5, 2.5, 2.2), (-5, 2.3, 2.5), (1, -3, 2.8)]
    for index, (x, y, height) in enumerate(positions):
        parts.append(add_cylinder(f"Cactus.{index}.Trunk", (x, y, 0), (x, y, height), 0.24, "cactus", 7))
        side = -1 if index % 2 else 1
        parts.append(add_cylinder(f"Cactus.{index}.Arm", (x, y, height * 0.48), (x + side * 0.75, y, height * 0.62), 0.18, "cactus", 7))
        parts.append(add_cylinder(f"Cactus.{index}.Tip", (x + side * 0.75, y, height * 0.62), (x + side * 0.75, y, height * 0.82), 0.16, "cactus", 7))
    return parts


def rail_parts(length=18.0, sleepers=12, rise=0.15):
    parts = []
    for x in (-0.55, 0.55):
        parts.append(add_box(f"Rail.{x}", (x, 0, rise), (0.11, length, 0.12), "iron"))
    for index in range(sleepers):
        y = -length * 0.5 + (index + 0.5) * length / sleepers
        parts.append(add_box(f"Sleeper.{index}", (0, y, max(0.0, rise - 0.14)), (1.65, 0.22, 0.14), "timber"))
    return parts


def incline_worksite_parts(variant):
    if variant == "engine-crane":
        return [
            place(import_source(SOURCE["incline_manifold"], "iron", (5.8, 2.7, 4.6)), (0.0, 0.8, 0.0)),
            add_box("InclineCrane.Foundation", (0.0, 0.0, 0.0), (7.0, 4.2, 0.24), "stone"),
            add_beam("InclineCrane.LegWest", (-2.8, -1.2, 0.2), (-1.2, -0.6, 6.5), 0.25, "timber"),
            add_beam("InclineCrane.LegEast", (2.8, -1.2, 0.2), (1.2, -0.6, 6.5), 0.25, "timber"),
            add_beam("InclineCrane.Header", (-1.6, -0.6, 6.5), (1.6, -0.6, 6.5), 0.24, "iron"),
            add_torus("InclineCrane.Sheave", (0.0, -0.72, 5.72), 0.72, 0.09, "brass"),
            add_cylinder("InclineCrane.HoistLine", (0.0, -0.74, 2.2), (0.0, -0.74, 5.25), 0.04, "soot", 6),
        ]
    if variant in {"west-brake", "east-brake"}:
        side = -1.0 if variant == "west-brake" else 1.0
        accent = "water" if side < 0 else "brass"
        parts = [
            place(import_source(SOURCE["incline_winch"], "iron", (4.4, 2.8, 3.0)), (0.0, 0.5, 0.0), side * 0.06),
            add_box("InclineBrake.Foundation", (0.0, 0.0, 0.0), (5.4, 4.0, 0.24), "stone"),
            add_beam("InclineBrake.LegWest", (-1.7, 0.5, 0.2), (-1.1, 0.2, 6.0), 0.22, "timber"),
            add_beam("InclineBrake.LegEast", (1.7, 0.5, 0.2), (1.1, 0.2, 6.0), 0.22, "timber"),
            add_beam("InclineBrake.Header", (-1.45, 0.2, 6.0), (1.45, 0.2, 6.0), 0.22, "iron"),
            add_torus("InclineBrake.Wheel", (side * 0.55, -0.05, 4.9), 0.90, 0.10, accent),
            add_cylinder("InclineBrake.Cable", (side * 0.55, -0.08, 1.2), (side * 0.55, -0.08, 4.15), 0.04, "soot", 6),
            add_box("InclineBrake.Counterweight", (-side * 1.0, -0.12, 3.7), (0.72, 0.72, 1.15), "rust"),
        ]
        if side > 0:
            parts.append(add_beam("InclineBrake.EastFork", (1.05, 0.2, 5.9), (2.05, 0.2, 6.85), 0.16, "brass"))
        return parts
    if variant == "cable-house":
        return [
            place(import_source(SOURCE["incline_winch"], "iron", (4.2, 2.6, 2.9)), (0.0, -0.2, 0.0)),
            place(import_source(SOURCE["coal"], "timber", (2.4, 1.8, 1.4)), (-3.2, 1.2, 0.0), 0.12),
            place(import_source(SOURCE["coal"], "timber", (2.4, 1.8, 1.4)), (3.2, 1.2, 0.0), -0.12),
            add_box("CableHouse.Foundation", (0.0, 0.0, 0.0), (9.0, 5.4, 0.24), "stone"),
            add_box("CableHouse.Shed", (0.0, 1.0, 0.2), (5.4, 3.0, 3.2), "timber"),
            add_box("CableHouse.Roof", (0.0, 1.0, 3.32), (6.1, 3.6, 0.28), "rust", -0.04),
            add_beam("CableHouse.GantryWest", (-2.4, -1.3, 0.2), (-1.4, -1.3, 5.4), 0.22, "timber"),
            add_beam("CableHouse.GantryEast", (2.4, -1.3, 0.2), (1.4, -1.3, 5.4), 0.22, "timber"),
            add_beam("CableHouse.GantryHeader", (-1.7, -1.3, 5.4), (1.7, -1.3, 5.4), 0.22, "iron"),
            add_torus("CableHouse.Sheave", (0.0, -1.42, 4.65), 0.68, 0.09, "brass"),
        ]
    if variant == "ford-pump":
        return [
            place(import_source(SOURCE["incline_pump"], "iron", (6.6, 4.4, 5.5)), (0.0, 0.4, 0.0), -0.04),
            add_box("FordPump.Foundation", (0.0, 0.0, 0.0), (7.5, 5.4, 0.24), "stone"),
            add_cylinder("FordPump.Intake", (-2.6, 0.6, 0.55), (-2.6, -3.4, 0.18), 0.16, "iron", 8),
            add_beam("FordPump.WaterMarkPost", (2.4, -1.85, 0.2), (2.4, -1.85, 3.8), 0.10, "iron"),
            add_box("FordPump.WaterMark", (2.4, -1.85, 3.8), (1.0, 0.12, 1.25), "water", -0.08),
        ]
    raise ValueError(f"unknown Incline worksite variant {variant}")


def boneyard_flivver_parts(variant):
    """Six readable motor hulks; each keeps one different failure silhouette."""
    east = variant.startswith("east")
    suffix = variant[-1]
    lean = (-0.08 if east else 0.07) + ({"a": 0.0, "b": 0.05, "c": -0.04}[suffix])
    parts = [
        add_box(f"{variant}.Chassis", (0.0, 0.0, 0.22), (5.8, 2.8, 0.30), "soot", lean * 0.25),
        add_box(f"{variant}.Hood", (-1.55, 0.0, 0.52), (2.55, 2.42, 0.86), "rust", lean),
        add_box(f"{variant}.Cab", (1.10, 0.0, 0.62), (2.35, 2.22, 1.62), "timber", -lean * 0.6),
        add_box(f"{variant}.Roof", (1.10, 0.0, 2.18), (2.70, 2.55, 0.20), "iron", -lean * 0.4),
        add_box(f"{variant}.Windshield", (0.62, -1.14, 1.33), (1.35, 0.10, 0.68), "water", -lean * 0.6),
        add_cylinder(f"{variant}.Exhaust", (-1.05, 0.72, 1.05), (-1.05, 0.72, 2.82), 0.12, "soot", 8),
        add_torus(f"{variant}.Lamp", (-2.45, -1.25, 1.16), 0.26, 0.06, "brass"),
    ]
    missing = {"west-a": (1.72, 1.40), "west-b": (-1.72, -1.40), "west-c": (1.72, -1.40), "east-a": (-1.72, 1.40), "east-b": (1.72, -1.40), "east-c": (-1.72, -1.40)}[variant]
    for index, (x, y) in enumerate(((-1.72, -1.40), (-1.72, 1.40), (1.72, -1.40), (1.72, 1.40))):
        if (x, y) != missing:
            parts.append(add_torus(f"{variant}.Wheel.{index}", (x, y, 0.72), 0.62, 0.13, "iron"))
    parts.extend([
        add_cylinder(f"{variant}.BareAxle", (missing[0], -1.62, 0.70), (missing[0], 1.62, 0.70), 0.10, "brass", 8),
        add_box(f"{variant}.LoosePanel", ((-0.4 if suffix == "b" else 2.15), 1.55, 0.34), (1.45, 0.14, 0.82), "cloth", lean + 0.18),
    ])
    if suffix == "c":
        parts.extend([
            add_beam(f"{variant}.BentBumper", (-2.85, -1.18, 0.42), (-3.35, 0.95, 0.92), 0.11, "iron"),
            add_rock(f"{variant}.WheelChock", (2.55, 1.45, 0.30), (0.55, 0.42, 0.30), "stone"),
        ])
    return parts


def boneyard_boiler_parts(variant):
    yaw = 0.10 if variant == "west" else -0.08
    side = -1.0 if variant == "west" else 1.0
    return [
        place(import_source(SOURCE["boiler"], "rust", (4.8, 3.35, 3.55)), (0.0, 0.0, 0.18), yaw),
        add_cylinder(f"{variant}.ColdStack", (side * 1.15, 0.55, 2.55), (side * 1.35, 0.55, 5.50), 0.27, "soot", 10),
        add_torus(f"{variant}.Valve", (-side * 1.58, -1.58, 2.30), 0.52, 0.08, "brass"),
        add_cylinder(f"{variant}.CappedPipe", (-side * 1.55, -0.25, 1.05), (-side * 2.75, -0.25, 1.25), 0.17, "iron", 8),
        add_box(f"{variant}.SplitPlate", (side * 1.55, -1.72, 1.22), (1.25, 0.10, 1.05), "soot", -yaw),
        add_rock(f"{variant}.ChockA", (-2.05, 1.40, 0.32), (0.65, 0.48, 0.32), "stone"),
        add_rock(f"{variant}.ChockB", (2.05, -1.25, 0.28), (0.58, 0.44, 0.28), "stone"),
    ]


def boneyard_hauler_bed_parts(variant):
    mirror = -1.0 if variant == "north-a" else 1.0
    parts = [
        add_box(f"{variant}.Deck", (0.0, 0.0, 0.52), (7.2, 3.65, 0.34), "timber", mirror * 0.03),
        add_box(f"{variant}.Headboard", (-3.20, 0.0, 0.72), (0.28, 3.70, 2.25), "rust", mirror * 0.03),
        add_beam(f"{variant}.RailPort", (-2.9, -1.62, 1.75), (2.9, -1.62, 1.42), 0.13, "iron"),
        add_beam(f"{variant}.RailStarboard", (-2.9, 1.62, 1.75), (2.9, 1.62, 1.42), 0.13, "iron"),
        add_cylinder(f"{variant}.SpentTank", (0.65, -0.72, 1.22), (0.65, 0.72, 1.22), 0.58, "rust", 10),
        add_box(f"{variant}.LooseTailgate", (3.30, mirror * 0.55, 0.30), (0.22, 2.35, 1.15), "cloth", mirror * 0.18),
    ]
    for index, (x, y) in enumerate(((-2.25, -1.85), (-2.25, 1.85), (2.25, -1.85))):
        parts.append(add_torus(f"{variant}.Wheel.{index}", (x, y, 0.72), 0.68, 0.14, "soot"))
    parts.append(add_cylinder(f"{variant}.BareRearAxle", (2.25, -2.05, 0.72), (2.25, 2.05, 0.72), 0.11, "brass", 8))
    return parts


def boneyard_sleeper_parts():
    parts = [
        add_box("Sleeper.BurialBed", (0.0, 0.0, 0.04), (8.8, 4.8, 0.58), "earth", 0.08),
        add_box("Sleeper.Cabin", (0.0, 0.0, 0.42), (7.6, 3.55, 2.95), "iron", 0.10),
        add_box("Sleeper.Roof", (0.0, 0.0, 3.18), (8.0, 3.85, 0.24), "rust", 0.10),
        add_box("Sleeper.DarkEnd", (3.72, -0.30, 0.82), (0.18, 2.45, 2.05), "soot", 0.10),
        add_cylinder("Sleeper.ColdFlue", (-2.45, 0.72, 3.24), (-2.45, 0.72, 5.10), 0.20, "soot", 9),
        add_beam("Sleeper.BrokenCoupler", (-4.05, 0.0, 0.92), (-5.20, 0.0, 0.55), 0.16, "brass"),
    ]
    for index, x in enumerate((-2.35, -0.25, 1.85)):
        parts.append(add_box(f"Sleeper.Window.{index}", (x, -1.82, 1.78), (1.20, 0.10, 0.82), "water", 0.10))
    for index, (x, y, size) in enumerate(((-3.7, 2.0, 0.75), (-1.9, -2.0, 0.62), (1.8, 2.1, 0.82), (3.8, -1.8, 0.70))):
        parts.append(add_rock(f"Sleeper.BurialRock.{index}", (x, y, 0.34), (size, size * 0.72, size * 0.46), "earth"))
    return parts


def boneyard_wagon_parts():
    return [
        place(import_source(SOURCE["e4_wagon"], "timber", (6.4, 3.4, 4.15)), (0.0, 0.0, 0.16), -0.05),
        add_box("UnmarkedWagon.CanvasPatch", (0.55, -1.74, 2.95), (1.85, 0.10, 1.20), "cloth", 0.08),
        add_beam("UnmarkedWagon.LooseShaft", (-3.25, 1.35, 0.45), (-5.35, 1.75, 0.22), 0.12, "timber"),
        add_torus("UnmarkedWagon.HungLamp", (-2.20, -1.85, 2.50), 0.28, 0.06, "brass"),
    ]


def long_road_station_parts(variant):
    """Three rest stops with visibly different jobs at the gameplay camera."""
    if variant == "west":
        return [
            place(import_source(SOURCE["e4_wrecker_shed"], "timber", (8.6, 5.0, 5.25)), (0.0, 0.0, 0.12), -0.04),
            add_cylinder("WestStation.FuelDrumA", (-2.55, 2.18, 0.28), (-2.55, 2.18, 1.62), 0.46, "rust", 10),
            add_cylinder("WestStation.FuelDrumB", (-1.35, 2.18, 0.28), (-1.35, 2.18, 1.62), 0.46, "brass", 10),
            add_beam("WestStation.LampMast", (3.70, -2.25, 0.18), (3.70, -2.25, 6.35), 0.16, "iron"),
            add_beam("WestStation.LampArm", (3.70, -2.25, 5.90), (2.55, -2.25, 5.90), 0.14, "brass"),
            add_torus("WestStation.TealLamp", (2.55, -2.34, 5.58), 0.30, 0.07, "water"),
            add_box("WestStation.OilApron", (0.0, 2.70, 0.03), (5.8, 1.2, 0.08), "soot", 0.06),
        ]
    if variant == "middle":
        return [
            place(import_source(SOURCE["e4_filling_shed"], "timber", (7.4, 4.9, 4.6)), (-0.65, 0.0, 0.12), 0.03),
            add_box("MiddleStation.RepairCanopy", (3.15, 0.0, 3.65), (4.7, 4.4, 0.26), "rust", -0.04),
            add_beam("MiddleStation.CanopyPostA", (1.10, -1.82, 0.18), (1.10, -1.82, 3.70), 0.16, "iron"),
            add_beam("MiddleStation.CanopyPostB", (5.20, -1.82, 0.18), (5.20, -1.82, 3.70), 0.16, "iron"),
            add_beam("MiddleStation.RepairCraneMast", (4.75, 1.55, 0.18), (4.75, 1.55, 6.80), 0.20, "iron"),
            add_beam("MiddleStation.RepairCraneArm", (4.75, 1.55, 6.40), (1.65, 1.55, 6.40), 0.18, "parchment"),
            add_torus("MiddleStation.RepairSheave", (4.75, 1.46, 6.02), 0.44, 0.08, "brass"),
            add_cylinder("MiddleStation.HangingHose", (1.65, 1.55, 3.55), (1.65, 1.55, 6.40), 0.07, "soot", 8),
            add_torus("MiddleStation.SpareTyreA", (-3.75, -2.20, 0.80), 0.58, 0.13, "soot"),
            add_torus("MiddleStation.SpareTyreB", (-2.45, -2.20, 0.80), 0.58, 0.13, "soot"),
        ]
    if variant == "east":
        return [
            place(import_source(SOURCE["e4_storm_tower"], "iron", (5.0, 4.2, 9.8)), (-2.05, 0.55, 0.12), -0.03),
            add_box("EastStation.RelayHut", (2.65, 0.45, 0.18), (4.6, 3.8, 3.35), "timber", 0.03),
            add_box("EastStation.RelayRoof", (2.65, 0.45, 3.48), (5.15, 4.25, 0.28), "rust", 0.03),
            add_box("EastStation.TealWindow", (2.65, -1.48, 1.52), (1.65, 0.10, 1.05), "water", 0.03),
            add_beam("EastStation.TollPost", (5.25, -2.35, 0.18), (5.25, -2.35, 4.15), 0.18, "iron"),
            add_beam("EastStation.TollBoom", (5.25, -2.35, 3.62), (-3.50, -2.35, 3.62), 0.17, "parchment"),
            add_torus("EastStation.TollLamp", (5.25, -2.45, 4.50), 0.31, 0.07, "brass"),
            add_box("EastStation.RoadArrow", (0.85, -2.43, 3.58), (1.20, 0.08, 0.72), "cloth", -0.18),
        ]
    raise ValueError(f"unknown Long Road station variant {variant}")


def long_road_hauler_parts():
    """The inherited wagon made playful and unmistakably motor-powered."""
    parts = [
        place(import_source(SOURCE["e4_wagon"], "timber", (7.4, 3.8, 4.55)), (0.15, 0.0, 0.12), 0.0),
        add_box("LeadHauler.EngineHood", (-3.35, 0.0, 0.68), (2.05, 3.15, 1.60), "rust"),
        add_box("LeadHauler.Grille", (-4.40, 0.0, 0.78), (0.18, 2.72, 1.25), "iron"),
        add_beam("LeadHauler.Bumper", (-4.52, -1.72, 0.62), (-4.52, 1.72, 0.62), 0.17, "brass"),
        add_torus("LeadHauler.HeadlampPort", (-4.52, -0.96, 1.48), 0.31, 0.07, "water", (0.0, math.pi * 0.5, 0.0)),
        add_torus("LeadHauler.HeadlampStarboard", (-4.52, 0.96, 1.48), 0.31, 0.07, "water", (0.0, math.pi * 0.5, 0.0)),
        add_cylinder("LeadHauler.Exhaust", (-2.65, 1.30, 1.10), (-2.65, 1.30, 5.65), 0.15, "soot", 9),
        add_torus("LeadHauler.ExhaustCap", (-2.65, 1.30, 5.58), 0.28, 0.06, "brass", (0.0, 0.0, 0.0)),
        add_beam("LeadHauler.RoofRackPort", (-2.0, -1.38, 4.72), (2.55, -1.38, 4.72), 0.10, "iron"),
        add_beam("LeadHauler.RoofRackStarboard", (-2.0, 1.38, 4.72), (2.55, 1.38, 4.72), 0.10, "iron"),
        add_box("LeadHauler.RoofLuggage", (1.45, 0.0, 4.72), (2.15, 2.15, 0.82), "cloth", 0.08),
        add_beam("LeadHauler.ConvoyFlagMast", (2.75, 1.28, 3.90), (2.75, 1.28, 6.45), 0.10, "brass"),
        add_box("LeadHauler.ConvoyFlag", (3.32, 1.28, 5.78), (1.38, 0.08, 0.74), "cloth", -0.10),
    ]
    for index, x in enumerate((-1.75, 0.0, 1.75)):
        parts.append(add_torus(f"LeadHauler.Filament.{index}", (x, -1.98, 3.78), 0.20, 0.05, "water" if index == 1 else "brass"))
    return parts


def long_road_railhead_parts():
    parts = [
        place(import_source(SOURCE["e4_recovery_gantry"], "iron", (8.8, 4.8, 5.8)), (0.0, 0.2, 0.14), 0.0),
        add_beam("EastRailhead.RailPort", (-5.2, -1.12, 0.22), (5.2, -1.12, 0.22), 0.13, "iron"),
        add_beam("EastRailhead.RailStarboard", (-5.2, 1.12, 0.22), (5.2, 1.12, 0.22), 0.13, "iron"),
        add_beam("EastRailhead.FuelCraneMast", (3.55, 2.55, 0.18), (3.55, 2.55, 7.65), 0.22, "iron"),
        add_beam("EastRailhead.FuelCraneArm", (3.55, 2.55, 7.25), (0.35, 2.55, 7.25), 0.19, "parchment"),
        add_torus("EastRailhead.CraneWheel", (3.55, 2.44, 6.82), 0.46, 0.08, "brass"),
        add_cylinder("EastRailhead.DropHose", (0.35, 2.55, 4.25), (0.35, 2.55, 7.25), 0.07, "soot", 8),
        add_beam("EastRailhead.SignalMast", (-3.35, -2.52, 0.18), (-3.35, -2.52, 5.35), 0.16, "iron"),
        add_torus("EastRailhead.TealSignal", (-3.35, -2.52, 4.90), 0.36, 0.08, "water"),
        add_beam("EastRailhead.BufferHeader", (5.15, -1.55, 1.18), (5.15, 1.55, 1.18), 0.24, "rust"),
        add_beam("EastRailhead.BufferBraceA", (4.18, -1.28, 0.18), (5.15, -1.28, 1.18), 0.18, "iron"),
        add_beam("EastRailhead.BufferBraceB", (4.18, 1.28, 0.18), (5.15, 1.28, 1.18), 0.18, "iron"),
        add_beam("EastRailhead.TrackEndCrossA", (5.18, -1.15, 0.55), (5.18, 1.15, 2.30), 0.15, "parchment"),
        add_beam("EastRailhead.TrackEndCrossB", (5.18, 1.15, 0.55), (5.18, -1.15, 2.30), 0.15, "parchment"),
        add_torus("EastRailhead.EndCoupler", (5.32, 0.0, 1.18), 0.34, 0.08, "brass", (0.0, math.pi * 0.5, 0.0)),
    ]
    for index, x in enumerate((-4.7, -2.8, -0.9, 1.0, 2.9, 4.8)):
        parts.append(add_box(f"EastRailhead.Sleeper.{index}", (x, 0.0, 0.10), (0.24, 3.25, 0.20), "timber"))
    return parts


def race_gate_parts(variant):
    accent = "brass" if variant == "finish" else "water"
    parts = [
        add_box(f"{variant}.DeckPort", (-2.35, 0, 0.30), (1.45, 1.65, 0.34), "timber"),
        add_box(f"{variant}.DeckStarboard", (2.35, 0, 0.30), (1.45, 1.65, 0.34), "timber"),
        add_cylinder(f"{variant}.FloatPort", (-3.0, -0.72, 0.30), (-1.7, -0.72, 0.30), 0.42, "iron", 10),
        add_cylinder(f"{variant}.FloatStarboard", (1.7, -0.72, 0.30), (3.0, -0.72, 0.30), 0.42, "iron", 10),
        add_beam(f"{variant}.PostPort", (-2.35, 0, 0.55), (-2.35, 0, 4.35), 0.17, "timber"),
        add_beam(f"{variant}.PostStarboard", (2.35, 0, 0.55), (2.35, 0, 4.35), 0.17, "timber"),
        add_beam(f"{variant}.Header", (-2.55, 0, 4.10), (2.55, 0, 4.10), 0.18, "iron"),
        add_beam(f"{variant}.BraceA", (-2.35, 0, 1.15), (2.00, 0, 3.95), 0.10, "brass"),
        add_beam(f"{variant}.BraceB", (2.35, 0, 1.15), (-2.00, 0, 3.95), 0.10, "brass"),
        place(import_source(SOURCE["e5_lantern"], accent, (1.12, 0.82, 2.65)), (0, 0, 4.0), 0.0),
        place(import_source(SOURCE["e5_buoy_rack"], "timber", (1.45, 0.68, 1.55)), (-2.35, 0.15, 0.60), -0.08),
    ]
    marker_xs = (-1.0, 1.0) if variant == "finish" else (0.0,)
    for index, x in enumerate(marker_xs):
        parts.extend([
            add_box(f"{variant}.Marker.{index}", (x, -0.14, 3.15), (0.76, 0.07, 0.76), accent, 0.15 if index % 2 else -0.15),
            add_torus(f"{variant}.MarkerRing.{index}", (x, -0.20, 3.53), 0.20, 0.035, "parchment"),
        ])
    if variant == "finish":
        parts.append(add_beam("finish.BellStriker", (0, -0.05, 2.85), (0.75, -0.28, 2.42), 0.07, "brass"))
    return parts


def buoy_anchor_parts(variant):
    yaw = {"northwest": -0.12, "midcourse": 0.0, "northeast": 0.12}[variant]
    accent = "brass" if variant == "midcourse" else "water"
    parts = [
        add_cylinder(f"{variant}.BallastFloat", (0, 0, 0), (0, 0, 0.52), 1.10, "iron", 14),
        add_torus(f"{variant}.RopeCollar", (0, 0, 0.50), 0.82, 0.08, "parchment", (0, 0, 0)),
        place(import_source(SOURCE["e5_buoy_rack"], "timber", (1.55, 0.75, 1.70)), (0, 0, 0.52), yaw),
        add_beam(f"{variant}.Mast", (0, 0, 0.55), (0, 0, 3.15), 0.10, "timber"),
        add_cylinder(f"{variant}.Beacon", (0, 0, 3.02), (0, 0, 3.55), 0.18, accent, 10),
        add_torus(f"{variant}.BeaconCage", (0, 0, 3.30), 0.25, 0.045, "brass", (0, 0, 0)),
    ]
    for index, angle in enumerate((0.2, math.pi * 0.5 + 0.2, math.pi + 0.2, math.pi * 1.5 + 0.2)):
        x, y = math.cos(angle) * 1.05, math.sin(angle) * 1.05
        parts.append(add_beam(f"{variant}.Tie.{index}", (0, 0, 1.0), (x, y, 0.35), 0.045, "parchment"))
    return parts


def spectator_raft_parts(variant):
    side = -1 if variant == "port" else 1
    parts = [
        place(import_source(SOURCE["e5_dinghy"], "timber", (4.10, 1.45, 1.45)), (0, -1.12, 0), side * 0.05),
        place(import_source(SOURCE["e5_dinghy"], "timber", (4.10, 1.45, 1.45)), (0, 1.12, 0), -side * 0.05),
        add_box(f"{variant}.Deck", (0, 0, 0.72), (4.75, 3.15, 0.24), "timber"),
        add_box(f"{variant}.Canopy", (0, 0, 3.15), (3.80, 2.55, 0.18), "cloth", side * 0.07),
        add_box(f"{variant}.Patch", (side * 0.72, -0.02, 3.33), (1.15, 1.15, 0.06), "parchment", -side * 0.11),
    ]
    for index, x in enumerate((-1.45, 1.45)):
        for y in (-1.02, 1.02):
            parts.append(add_beam(f"{variant}.CanopyPost.{index}.{y}", (x, y, 0.9), (x + side * 0.12, y, 3.2), 0.07, "timber"))
    for index, x in enumerate((-1.15, 0.0, 1.15)):
        parts.append(add_box(f"{variant}.Bench.{index}", (x, 0, 1.00), (0.30, 2.60, 0.28), "parchment"))
    for index, y in enumerate((-1.50, 1.50)):
        parts.extend([
            add_cylinder(f"{variant}.LanternPost.{index}", (side * 1.95, y, 0.85), (side * 1.95, y, 2.15), 0.055, "iron", 7),
            add_cylinder(f"{variant}.Lantern.{index}", (side * 1.95, y, 2.05), (side * 1.95, y, 2.45), 0.12, "water", 8),
        ])
    return parts


def judges_tower_parts():
    parts = [
        add_cylinder("Judge.FloatPort", (-2.2, -1.45, 0.40), (2.2, -1.45, 0.40), 0.48, "iron", 12),
        add_cylinder("Judge.FloatStarboard", (-2.2, 1.45, 0.40), (2.2, 1.45, 0.40), 0.48, "iron", 12),
        add_box("Judge.LowerDeck", (0, 0, 0.68), (5.25, 3.75, 0.28), "timber"),
        add_box("Judge.UpperDeck", (0, 0, 4.35), (4.20, 3.25, 0.30), "timber"),
        add_box("Judge.Cabin", (0, 0, 4.62), (3.35, 2.60, 2.15), "timber"),
        add_box("Judge.Roof", (0, 0, 6.73), (3.90, 3.05, 0.25), "rust"),
        place(import_source(SOURCE["e5_lantern"], "water", (1.05, 0.78, 2.55)), (0, 0, 6.85), 0.0),
        add_torus("Judge.CourseDial", (0, -1.34, 5.55), 0.54, 0.07, "brass"),
        add_beam("Judge.DialNeedle", (0, -1.42, 5.55), (0.34, -1.45, 5.82), 0.055, "parchment"),
    ]
    for x in (-1.55, 1.55):
        for y in (-1.20, 1.20):
            parts.extend([
                add_beam(f"Judge.Leg.{x}.{y}", (x, y, 0.85), (x * 0.88, y * 0.88, 4.40), 0.16, "timber"),
                add_beam(f"Judge.Brace.{x}.{y}", (x, y, 1.10), (-x * 0.70, y * 0.70, 4.10), 0.09, "brass"),
            ])
    for index, x in enumerate((-1.10, 0.0, 1.10)):
        parts.append(add_box(f"Judge.Window.{index}", (x, -1.32, 5.15), (0.62, 0.08, 0.72), "water"))
    return parts


def ridge_dish_cluster_parts(variant):
    """E7 ridge furniture: readable dishes without duplicating relay-pad towers."""
    side = -1 if variant == "west" else 1
    parts = [
        add_box(f"{variant}.DishRailL", (-2.15, 0.0, 0.0), (0.34, 3.45, 0.18), "timber", side * 0.025),
        add_box(f"{variant}.DishRailR", (2.15, 0.0, 0.0), (0.34, 3.45, 0.18), "timber", -side * 0.025),
        add_box(f"{variant}.DishTieFront", (0.0, -1.38, 0.0), (4.75, 0.30, 0.16), "timber", side * 0.02),
        add_box(f"{variant}.DishTieRear", (0.0, 1.38, 0.0), (4.75, 0.30, 0.16), "timber", -side * 0.025),
    ]
    stations = (
        (-1.75, 0.10, 6.4, 1.22, side * 0.16),
        (1.65, 0.35, 5.2, 1.02, -side * 0.20),
        (0.15, -1.05, 3.8, 0.78, side * 0.30),
    )
    for index, (x, y, height, radius, yaw) in enumerate(stations):
        parts.extend([
            add_cylinder(f"{variant}.DishMast.{index}", (x, y, 0.18), (x, y, height), 0.16, "iron", 8),
            add_torus(f"{variant}.DishRim.{index}", (x, y + 0.14, height), radius * 0.92, 0.07, "brass", (math.pi * 0.5, 0.0, yaw)),
            add_dish(f"{variant}.DishBowl.{index}", (x, y, height), radius, "water", yaw),
            add_cylinder(f"{variant}.DishBackHub.{index}", (x, y - radius * 0.48, height), (x, y + 0.04, height), radius * 0.17, "brass", 10),
            add_beam(f"{variant}.FeedArm.{index}", (x, y + 0.10, height), (x + math.sin(yaw) * radius * 0.22, y + 0.75, height + math.cos(yaw) * radius * 0.22), 0.06, "brass"),
            add_rock(f"{variant}.FeedLamp.{index}", (x + math.sin(yaw) * radius * 0.22, y + 0.78, height + math.cos(yaw) * radius * 0.22), (0.15, 0.12, 0.15), "parchment"),
            add_beam(f"{variant}.DishRearLegL.{index}", (x - 0.64, y - 0.48, 0.18), (x - 0.14, y - 0.18, height * 0.78), 0.105, "iron"),
            add_beam(f"{variant}.DishRearLegR.{index}", (x + 0.64, y - 0.48, 0.18), (x + 0.14, y - 0.18, height * 0.78), 0.105, "iron"),
        ])
        for rib in range(4):
            angle = math.tau * rib / 4.0
            parts.append(add_beam(
                f"{variant}.DishBackRib.{index}.{rib}",
                (x, y - radius * 0.30, height),
                (x + math.cos(angle) * radius * 0.76, y - radius * 0.22, height + math.sin(angle) * radius * 0.76),
                0.055, "brass",
            ))
        for brace_side in (-1, 1):
            parts.append(add_beam(
                f"{variant}.DishBrace.{index}.{brace_side}",
                (x, y, height * 0.68), (x + brace_side * 0.82, y, 0.20), 0.085, "brass",
            ))
    parts.extend([
        add_box(f"{variant}.PunchTapeCabinet", (side * 2.35, 1.15, 0.16), (1.25, 0.82, 1.85), "timber", side * 0.05),
        add_torus(f"{variant}.CableCoil", (-side * 2.25, -1.20, 0.30), 0.62, 0.08, "parchment", (0.0, 0.0, 0.0)),
        add_beam(f"{variant}.StormBrace", (-2.4, -1.25, 0.18), (2.4, -1.25, 1.0), 0.10, "rust"),
    ])
    return parts


def dead_gap_chart_station_parts():
    parts = [
        add_box("ChartStation.FloorA", (-1.55, 0.0, 0.0), (2.65, 3.25, 0.16), "timber", -0.04),
        add_box("ChartStation.FloorB", (1.55, 0.0, 0.0), (2.65, 3.25, 0.16), "timber", 0.05),
        add_box("ChartStation.Console", (0.0, 0.35, 0.16), (4.2, 1.35, 1.62), "timber"),
        add_box("ChartStation.ChartFace", (0.0, 1.05, 1.05), (3.25, 0.09, 1.22), "parchment", -0.025),
        add_cylinder("ChartStation.SignalMast", (0.0, -0.45, 1.75), (0.0, -0.45, 7.0), 0.18, "iron", 8),
        add_torus("ChartStation.SignalArcOuter", (0.0, 0.0, 5.65), 1.38, 0.10, "water"),
        add_torus("ChartStation.SignalArcMiddle", (0.0, 0.02, 5.65), 0.94, 0.075, "brass"),
        add_torus("ChartStation.SignalArcInner", (0.0, 0.04, 5.65), 0.50, 0.06, "parchment"),
        add_beam("ChartStation.SignalNeedle", (0.0, 0.10, 5.65), (0.82, 0.12, 6.33), 0.055, "cloth"),
        add_torus("ChartStation.PunchTapeRollL", (-1.25, 1.10, 1.56), 0.28, 0.055, "brass"),
        add_torus("ChartStation.PunchTapeRollR", (1.25, 1.10, 1.56), 0.28, 0.055, "brass"),
        add_box("ChartStation.TapeRibbon", (0.0, 1.15, 1.42), (2.25, 0.06, 0.18), "parchment", 0.04),
    ]
    for side in (-1, 1):
        parts.extend([
            add_beam(f"ChartStation.MastGuy.{side}", (0.0, -0.45, 4.65), (side * 2.0, -1.30, 0.18), 0.075, "iron"),
            add_cylinder(f"ChartStation.GroundPin.{side}", (side * 2.0, -1.52, 0.18), (side * 2.0, -1.08, 0.18), 0.14, "brass", 8),
        ])
    return parts


def signal_cable_yard_parts():
    parts = [
        place(import_source(SOURCE["stockpile"], "timber", (3.7, 2.5, 1.75)), (1.65, 0.95, 0.0), -0.12),
        add_box("CableYard.SleeperA", (0.0, -1.65, 0.0), (6.5, 0.30, 0.20), "timber", 0.03),
        add_box("CableYard.SleeperB", (0.0, 1.65, 0.0), (6.5, 0.30, 0.20), "timber", -0.04),
    ]
    for index, (x, y, radius) in enumerate(((-2.05, -0.35, 1.12), (0.0, -0.55, 0.92), (2.0, -0.45, 0.76))):
        width = 0.74
        parts.extend([
            add_cylinder(f"CableYard.Drum.{index}", (x - width, y, radius), (x + width, y, radius), radius * 0.72, "parchment", 12),
            add_torus(f"CableYard.FlangeL.{index}", (x - width, y, radius), radius, 0.095, "brass", (0.0, math.pi * 0.5, 0.0)),
            add_torus(f"CableYard.FlangeR.{index}", (x + width, y, radius), radius, 0.095, "brass", (0.0, math.pi * 0.5, 0.0)),
            add_cylinder(f"CableYard.Axle.{index}", (x - width - 0.22, y, radius), (x + width + 0.22, y, radius), 0.10, "iron", 8),
        ])
    parts.extend([
        add_torus("CableYard.LooseCoil", (-2.25, 1.05, 0.20), 0.72, 0.075, "water", (0.0, 0.0, 0.0)),
        add_box("CableYard.TestCabinet", (-1.60, 1.28, 0.18), (1.15, 0.75, 1.72), "timber", 0.05),
        add_torus("CableYard.TestDial", (-1.60, 0.88, 1.20), 0.28, 0.05, "water"),
        add_beam("CableYard.PatchedRail", (-3.10, 1.75, 0.18), (3.10, 1.75, 0.64), 0.11, "rust"),
    ])
    return parts


def drone_recovery_beacon_parts():
    parts = [
        place(import_source(SOURCE["sentry_beacon"], "iron", (2.35, 2.35, 4.65)), (0.0, 0.0, 0.15), 0.0),
        add_torus("DroneBeacon.CrownRing", (0.0, 0.0, 5.25), 1.08, 0.10, "water", (0.0, 0.0, 0.0)),
        add_cylinder("DroneBeacon.CrownLamp", (0.0, 0.0, 4.60), (0.0, 0.0, 5.85), 0.20, "parchment", 10),
    ]
    for index, angle in enumerate((0.0, math.pi * 0.5, math.pi, math.pi * 1.5)):
        inner = (math.cos(angle) * 0.75, math.sin(angle) * 0.75, 0.30)
        outer = (math.cos(angle) * 3.10, math.sin(angle) * 3.10, 0.18)
        pad = (math.cos(angle) * 3.25, math.sin(angle) * 3.25, 0.0)
        parts.extend([
            add_beam(f"DroneBeacon.RecoveryArm.{index}", inner, outer, 0.15, "brass"),
            add_box(f"DroneBeacon.LandingPad.{index}", pad, (1.25, 1.25, 0.16), "timber", angle + math.pi * 0.25),
            add_rock(f"DroneBeacon.GuideLamp.{index}", (outer[0], outer[1], 0.38), (0.18, 0.18, 0.20), "water"),
        ])
    parts.extend([
        add_torus("DroneBeacon.RecoveredRotor", (2.35, -1.70, 0.55), 0.68, 0.07, "rust", (0.0, 0.0, 0.0)),
        add_beam("DroneBeacon.RotorBlade", (1.35, -1.70, 0.55), (3.35, -1.70, 0.55), 0.065, "rust"),
    ])
    return parts


def earthrise_listening_array_parts():
    parts = [
        add_box("EarthriseArray.Pad", (0, 0, 0.04), (8.2, 3.8, 0.24), "soot"),
        add_box("EarthriseArray.BackBus", (0, 1.25, 0.62), (8.0, 0.30, 0.90), "rust"),
    ]
    for index, (x, height, radius, yaw) in enumerate(((-2.8, 4.0, 0.88, -0.18), (-1.4, 5.0, 1.08, -0.09), (0.0, 6.0, 1.30, 0.0), (1.5, 4.8, 1.02, 0.10), (2.9, 3.8, 0.82, 0.20))):
        parts.extend([
            add_cylinder(f"EarthriseArray.Mast.{index}", (x, -0.15, 0.30), (x, -0.15, height), 0.16, "iron", 8),
            add_dish(f"EarthriseArray.Bowl.{index}", (x, -0.05, height), radius, "water", yaw),
            add_torus(f"EarthriseArray.Rim.{index}", (x, 0.08, height), radius * 0.92, 0.06, "brass", (math.pi * 0.5, 0.0, yaw)),
            add_beam(f"EarthriseArray.LegL.{index}", (x - 0.58, -0.72, 0.25), (x - 0.10, -0.18, height * 0.72), 0.10, "iron"),
            add_beam(f"EarthriseArray.LegR.{index}", (x + 0.58, -0.72, 0.25), (x + 0.10, -0.18, height * 0.72), 0.10, "iron"),
        ])
    parts.extend([
        add_box("EarthriseArray.RadioCabinet", (0.0, 1.42, 0.18), (1.45, 0.72, 1.55), "timber"),
        add_torus("EarthriseArray.EarthDial", (0.0, 0.98, 1.18), 0.30, 0.05, "water"),
    ])
    return parts


def lava_tube_survey_gantry_parts():
    parts = [
        add_box("TubeGantry.Footing", (0, 0, 0.06), (6.2, 4.7, 0.26), "soot"),
        add_box("TubeGantry.ServiceDeck", (0, 0, 1.05), (4.7, 3.5, 0.30), "timber"),
        add_torus("TubeGantry.OuterRingFront", (0, -0.45, 4.1), 2.3, 0.18, "brass"),
        add_torus("TubeGantry.OuterRingRear", (0, 0.45, 4.1), 2.3, 0.18, "brass"),
        add_torus("TubeGantry.InnerRing", (0, 0, 4.1), 1.55, 0.10, "water"),
        add_cylinder("TubeGantry.Scanner", (0, -0.85, 3.25), (0, 0.85, 3.25), 0.78, "water", 14),
    ]
    for side in (-1, 1):
        parts.extend([
            add_box(f"TubeGantry.Counterweight.{side}", (side * 2.7, 0, 2.45), (0.70, 2.4, 4.2), "iron", side * 0.03),
            add_beam(f"TubeGantry.TowerOuter.{side}", (side * 3.0, -1.65, 0.30), (side * 2.25, 0, 6.5), 0.28, "iron"),
            add_beam(f"TubeGantry.TowerInner.{side}", (side * 1.65, 1.65, 0.30), (side * 2.25, 0, 6.5), 0.24, "iron"),
            add_cylinder(f"TubeGantry.CrownLamp.{side}", (side * 2.25, 0, 6.35), (side * 2.25, 0, 7.05), 0.15, "water", 8),
        ])
    for ray in range(8):
        angle = math.tau * ray / 8.0
        parts.append(add_beam(
            f"TubeGantry.RingRay.{ray}",
            (math.cos(angle) * 1.62, 0.05, 4.1 + math.sin(angle) * 1.62),
            (math.cos(angle) * 2.20, 0.05, 4.1 + math.sin(angle) * 2.20),
            0.07, "parchment",
        ))
    parts.append(add_beam("TubeGantry.HoistCable", (0, 0, 6.45), (0, 0, 3.75), 0.055, "parchment"))
    return parts


def regolith_core_yard_parts():
    parts = [
        add_box("CoreYard.WorkPad", (0, 0, 0.04), (6.4, 4.6, 0.22), "soot"),
        place(import_source(SOURCE["e8_crater_rim"], "stone", (4.6, 3.9, 1.45)), (-1.25, 0.55, 0.0), 0.16),
        add_box("CoreYard.RackTop", (1.75, 0, 3.0), (2.7, 2.1, 0.22), "iron"),
        add_box("CoreYard.Canopy", (1.75, 0, 3.55), (3.3, 2.7, 0.30), "rust", 0.04),
        add_cylinder("CoreYard.SampleMast", (-0.15, -1.15, 1.60), (-0.15, -1.15, 7.1), 0.16, "iron", 8),
        add_torus("CoreYard.SampleDial", (-0.15, -1.15, 5.45), 0.70, 0.08, "water"),
    ]
    for index, (x, y, height) in enumerate(((0.9, -0.65, 2.35), (1.7, 0, 2.75), (2.45, 0.60, 2.18))):
        parts.append(add_cylinder(f"CoreYard.Core.{index}", (x, y, 0.50), (x, y, height), 0.26, "parchment", 10))
    parts.extend([
        add_cylinder("CoreYard.AssayPan", (-2.45, -0.30, 0.22), (-2.45, -0.30, 0.52), 1.02, "iron", 14),
        add_rock("CoreYard.He3Sample", (-2.45, -0.30, 0.72), (0.48, 0.36, 0.30), "water"),
        add_box("CoreYard.SortingBench", (-1.9, 1.45, 0.74), (2.2, 0.68, 0.42), "rust", 0.08),
    ])
    return parts


def rim_debris_catcher_parts(variant):
    side = -1 if variant == "west" else 1
    parts = [
        add_box(f"{variant}.CatcherFooting", (0, 0, 0.06), (5.1, 4.2, 0.24), "soot"),
        place(import_source(SOURCE["e8_lander_legs"], "iron", (4.1, 3.7, 2.65)), (0, 0, 0), side * 0.06),
        add_torus(f"{variant}.CatcherOuterFront", (0, -0.44, 4.9), 1.82, 0.15, "brass"),
        add_torus(f"{variant}.CatcherOuterRear", (0, 0.44, 4.9), 1.82, 0.15, "brass"),
        add_torus(f"{variant}.CatcherInner", (0, 0, 4.9), 1.04, 0.10, "water"),
        add_cylinder(f"{variant}.ImpactHub", (0, -0.60, 4.9), (0, 0.60, 4.9), 0.38, "water", 12),
    ]
    for ray in range(8):
        angle = math.tau * ray / 8.0
        parts.append(add_beam(
            f"{variant}.NetRay.{ray}",
            (math.cos(angle) * 0.34, -0.05, 4.9 + math.sin(angle) * 0.34),
            (math.cos(angle) * 1.68, -0.05, 4.9 + math.sin(angle) * 1.68),
            0.06, "parchment",
        ))
    for support_side in (-1, 1):
        parts.extend([
            add_beam(f"{variant}.BasketStay.{support_side}", (support_side * 1.65, -1.30, 0.45), (support_side * 1.30, -0.35, 4.40), 0.15, "iron"),
            add_beam(f"{variant}.RearStay.{support_side}", (support_side * 1.40, 1.25, 0.40), (support_side * 1.00, 0.35, 5.65), 0.12, "brass"),
        ])
    parts.append(add_cylinder(f"{variant}.WarningLamp", (side * 2.05, 0, 0.35), (side * 2.05, 0, 2.45), 0.10, "iron", 8))
    return parts


def eclipse_kit_parts(variant):
    if variant == "shadow-dial":
        parts = [
            add_box("EclipseDial.Plinth", (0.0, 0.0, 0.0), (7.4, 7.0, 0.30), "soot"),
            add_cylinder("EclipseDial.Drum", (0.0, 0.0, 0.30), (0.0, 0.0, 1.25), 2.65, "stone", 16),
            add_torus("EclipseDial.OuterRing", (0.0, -0.10, 4.45), 2.20, 0.16, "brass"),
            add_torus("EclipseDial.ShadowRing", (0.0, -0.18, 4.45), 1.30, 0.11, "soot"),
            add_cylinder("EclipseDial.Hub", (0.0, -0.45, 4.45), (0.0, 0.45, 4.45), 0.34, "water", 12),
            add_beam("EclipseDial.Gnomon", (-0.20, -0.24, 1.20), (1.35, -0.24, 6.75), 0.16, "parchment"),
            add_beam("EclipseDial.WestStay", (-2.65, 1.85, 0.30), (-0.55, 0.12, 4.25), 0.18, "iron"),
            add_beam("EclipseDial.EastStay", (2.65, 1.85, 0.30), (0.55, 0.12, 4.25), 0.18, "iron"),
        ]
        for ray in range(8):
            angle = math.tau * ray / 8.0
            parts.append(add_beam(
                f"EclipseDial.Ray.{ray}",
                (math.cos(angle) * 1.42, -0.04, 4.45 + math.sin(angle) * 1.42),
                (math.cos(angle) * 2.02, -0.04, 4.45 + math.sin(angle) * 2.02),
                0.065, "parchment",
            ))
        return parts
    if variant.endswith("witness"):
        side = -1 if variant.startswith("west") else 1
        parts = [
            add_box(f"EclipseWitness.{variant}.Footing", (0.0, 0.0, 0.0), (5.4, 4.4, 0.26), "soot"),
            add_cylinder(f"EclipseWitness.{variant}.Mast", (0.0, 0.0, 0.26), (0.0, 0.0, 6.6), 0.20, "iron", 10),
            add_dish(f"EclipseWitness.{variant}.SunBowl", (0.0, -0.10, 5.25), 1.55, "brass", side * 0.16),
            add_torus(f"EclipseWitness.{variant}.SolarRim", (0.0, -0.46, 5.25), 1.38, 0.11, "water", (math.pi * 0.5, 0.0, side * 0.16)),
            add_torus(f"EclipseWitness.{variant}.BlackCore", (0.0, -0.58, 5.25), 0.52, 0.12, "soot", (math.pi * 0.5, 0.0, side * 0.16)),
            add_beam(f"EclipseWitness.{variant}.Sight", (0.0, 0.0, 5.25), (side * 2.25, 0.0, 7.05), 0.09, "parchment"),
            add_beam(f"EclipseWitness.{variant}.StayA", (-2.10, 1.45, 0.26), (-0.35, 0.12, 4.80), 0.15, "iron"),
            add_beam(f"EclipseWitness.{variant}.StayB", (2.10, 1.45, 0.26), (0.35, 0.12, 4.80), 0.15, "iron"),
        ]
        return parts
    if variant == "launch-gate":
        width, height = 9.0, 7.0
        return [
            add_box("EclipseLaunch.Footing", (0.0, 0.0, 0.0), (10.0, 3.8, 0.28), "soot"),
            add_beam("EclipseLaunch.West", (-width * 0.5, 0.0, 0.28), (-width * 0.5, 0.0, height), 0.28, "iron"),
            add_beam("EclipseLaunch.East", (width * 0.5, 0.0, 0.28), (width * 0.5, 0.0, height), 0.28, "iron"),
            add_beam("EclipseLaunch.Top", (-width * 0.5, 0.0, height), (width * 0.5, 0.0, height), 0.26, "brass"),
            add_beam("EclipseLaunch.BraceL", (-width * 0.5, 0.10, 0.80), (-1.30, 0.10, height), 0.14, "rust"),
            add_beam("EclipseLaunch.BraceR", (width * 0.5, 0.10, 0.80), (1.30, 0.10, height), 0.14, "rust"),
            add_torus("EclipseLaunch.ShadowDisk", (0.0, -0.20, height - 0.82), 0.78, 0.11, "soot"),
            add_beam("EclipseLaunch.Crescent", (-0.62, -0.34, height - 1.28), (0.56, -0.34, height - 0.35), 0.11, "water"),
        ]
    return [
        add_box("EclipseDriver.Footing", (0.0, 0.0, 0.0), (6.6, 3.4, 0.28), "soot"),
        add_cylinder("EclipseDriver.Mast", (0.0, 0.0, 0.28), (0.0, 0.0, 6.8), 0.22, "iron", 10),
        add_torus("EclipseDriver.BlackRing", (0.0, -0.18, 5.35), 0.88, 0.11, "soot"),
        add_beam("EclipseDriver.Crescent", (-0.68, -0.32, 4.70), (0.62, -0.32, 5.98), 0.12, "water"),
        add_beam("EclipseDriver.RailPointer", (-2.75, 0.0, 1.10), (2.75, 0.0, 3.25), 0.16, "brass"),
        add_cylinder("EclipseDriver.DriverHub", (1.85, -0.45, 2.90), (1.85, 0.45, 2.90), 0.36, "parchment", 10),
        add_beam("EclipseDriver.WestStay", (-2.50, 1.20, 0.28), (-0.30, 0.10, 5.0), 0.15, "iron"),
        add_beam("EclipseDriver.EastStay", (2.50, 1.20, 0.28), (0.30, 0.10, 5.0), 0.15, "iron"),
    ]


def storm_anchor_gate_parts(variant):
    north = variant == "north"
    span = 9.8 if north else 8.8
    height = 7.2 if north else 6.2
    parts = [
        add_box(f"{variant}.AnchorGateFoot", (0, 0, 0.04), (span + 1.2, 3.4, 0.24), "soot"),
        place(import_source(SOURCE["e9_canal_gate"], "iron", (span, 3.0, 3.15)), (0, 0, 0.18), 0.0),
    ]
    for side in (-1, 1):
        parts.extend([
            add_beam(f"{variant}.RakedStay.{side}", (side * span * 0.50, 1.45, 0.22), (side * span * 0.38, 0, height), 0.24, "iron"),
            add_cylinder(f"{variant}.WindLamp.{side}", (side * span * 0.38, 0, height - 0.55), (side * span * 0.38, 0, height + 0.30), 0.16, "water", 8),
            add_box(f"{variant}.Deadweight.{side}", (side * span * 0.50, 1.50, 0.22), (1.25, 1.0, 1.0), "stone", side * 0.08),
        ])
    parts.extend([
        add_beam(f"{variant}.StormBar", (-span * 0.38, 0, height), (span * 0.38, 0, height), 0.20, "brass"),
        add_torus(f"{variant}.WindEye", (0, -0.20, height), 0.82 if north else 0.66, 0.10, "rust", (math.pi * 0.5, 0.0, 0.0)),
    ])
    if north:
        parts.extend([
            add_beam("north.CrossBraceL", (-3.2, 0.12, 3.2), (0, 0.12, 6.7), 0.11, "brass"),
            add_beam("north.CrossBraceR", (3.2, 0.12, 3.2), (0, 0.12, 6.7), 0.11, "brass"),
        ])
    return parts


def wind_anchor_parts(variant):
    stage = {"west": 0, "center": 1, "east": 2}[variant]
    height = 5.4 + stage * 0.8
    parts = [
        add_box(f"{variant}.AnchorPad", (0, 0, 0.04), (5.6 + stage * 0.4, 4.6, 0.24), "soot"),
        place(import_source(SOURCE["e9_dust_mast"], "iron", (3.3, 3.0, height)), (0, 0, 0.20), 0.08 * (stage - 1)),
        add_cylinder(f"{variant}.BuriedDrum", (-1.75, 0.75, 0.65), (1.75, 0.75, 0.65), 0.56 + stage * 0.08, "rust", 12),
    ]
    for side in (-1, 1):
        parts.extend([
            add_beam(f"{variant}.Guy.{side}", (0, 0, height * 0.78), (side * (2.5 + stage * 0.2), -1.65, 0.32), 0.065, "parchment"),
            add_box(f"{variant}.GroundAnchor.{side}", (side * (2.5 + stage * 0.2), -1.65, 0.12), (0.85, 0.72, 0.42), "stone", side * 0.12),
        ])
    for index in range(stage + 1):
        radius = 1.15 - index * 0.18
        parts.append(add_torus(
            f"{variant}.WindBrake.{index}",
            (0, -0.15, height * 0.55 + index * 0.72),
            radius,
            0.09,
            "brass" if index % 2 == 0 else "water",
            (math.pi * 0.5, 0.0, 0.0),
        ))
    parts.extend([
        add_beam(f"{variant}.VaneArm", (0, 0, height), (1.8 + stage * 0.3, 0, height + 0.45), 0.09, "brass"),
        add_box(f"{variant}.VaneFlag", (1.9 + stage * 0.3, 0, height + 0.32), (0.95, 0.10, 0.62), "cloth", -0.10 * stage),
    ])
    return parts


def archive_entry_gate_parts():
    parts = [
        add_box("ArchiveEntry.Foot", (0, 0, 0.04), (10.6, 4.8, 0.24), "soot"),
        place(import_source(SOURCE["e10_bridge_school"], "iron", (8.8, 4.0, 6.4)), (0, 0, 0.20), 0.0),
        add_torus("ArchiveEntry.MemoryPortal", (0, -1.95, 6.4), 2.15, 0.18, "brass", (math.pi * 0.5, 0.0, 0.0)),
        add_torus("ArchiveEntry.MemoryLight", (0, -2.05, 6.4), 1.28, 0.10, "water", (math.pi * 0.5, 0.0, 0.0)),
    ]
    for side in (-1, 1):
        parts.extend([
            add_beam(f"ArchiveEntry.RuinStay.{side}", (side * 4.7, 1.8, 0.25), (side * 3.35, 0, 8.0), 0.22, "iron"),
            add_cylinder(f"ArchiveEntry.Light.{side}", (side * 3.35, 0, 7.35), (side * 3.35, 0, 8.25), 0.16, "water", 8),
        ])
    parts.extend([
        add_beam("ArchiveEntry.BrokenLintelL", (-3.35, 0, 8.0), (-0.45, 0, 8.0), 0.18, "brass"),
        add_beam("ArchiveEntry.BrokenLintelR", (0.80, 0, 8.0), (3.35, 0, 8.0), 0.18, "brass"),
    ])
    return parts


def archive_stack_ruin_parts(variant):
    east = variant == "east"
    parts = [
        add_box(f"{variant}.Foundation", (0, 0, 0), (7.4, 5.2, .24), "stone"),
        add_box(f"{variant}.UpperTerrace", (0, .4, .24), (6.4, 3.7, .35), "stone"),
        add_box(f"{variant}.Recess", (0, 1.45, .59), (5.3, .3, 4.6), "soot"),
    ]
    # The plate's books and layered masonry replace the former blank display panel.
    for level in range(3):
        base = .65 + level * 1.45
        parts.append(add_box(f"{variant}.Shelf.{level}", (0, .65, base), (5.2, 1.35, .16), "timber"))
        for book in range(11):
            if (book + level + int(east)) % 7 == 0:
                continue
            x = -2.25 + book * .44
            height = .78 + .10 * ((book + level) % 4)
            role = ("cloth", "timber", "parchment", "rust")[(book + level) % 4]
            parts.append(add_box(f"{variant}.Book.{level}.{book}", (x, .38, base + .16), (.28, .67, height), role, .035 * ((book % 3) - 1)))
            parts.append(add_box(f"{variant}.SpineBand.{level}.{book}", (x, .03, base + .32), (.29, .035, .045), "brass"))
    for side in (-1, 1):
        height = 5.2 if (side == 1) == east else 5.96
        parts.extend([
            add_box(f"{variant}.ColumnBase.{side}", (side * 2.8, .45, .59), (.9, 1.15, .30), "stone"),
            add_cylinder(f"{variant}.Column.{side}", (side * 2.8, .45, .89), (side * 2.8, .45, height - .3), .31, "stone", 8),
            add_box(f"{variant}.Capital.{side}", (side * 2.8, .45, height - .3), (.85, .95, .3), "stone"),
        ])
    for course in range(3):
        parts.append(add_box(f"{variant}.BrokenCornice.{course}", (-.65 + course * .25, 1.15, 5.12 + .2 * course), (4.0 - course * .7, 1.0, .18), "stone"))
    for i in range(6):
        parts.append(add_box(f"{variant}.FallenBlock.{i}", (-2.7 + i * 1.05, -1.75 + .15 * (i % 2), .24), (.65, .65, .24 + .1 * (i % 3)), "stone", .21 * (i - 2)))
    parts.append(add_torus(f"{variant}.MemorySeal", (0, -.16, 4.8), .28, .055, "brass", (math.pi * .5, 0, 0)))
    return parts


def archive_warning_shelf_parts():
    parts = [
        add_box("WarningShelf.Foundation", (0, 0, 0), (8.4, 5.4, .24), "stone"),
        add_box("WarningShelf.Terrace", (0, .35, .24), (7.1, 3.8, .35), "stone"),
        add_box("WarningShelf.Recess", (0, 1.2, .59), (5.6, .25, 5.2), "soot"),
    ]
    for level in range(4):
        parts.append(add_box(f"WarningShelf.EmptyShelf.{level}", (0, .1, .65 + 1.45 * level), (5.6, .65, .14), "timber"))
    for x in (-.95, .95):
        parts.append(add_box(f"WarningShelf.Divider.{x}", (x, .35, .65), (.12, 1.0, 4.5), "timber"))
    for side in (-1, 1):
        for course in range(6):
            parts.append(add_box(f"WarningShelf.Pier.{side}.{course}", (side * 3.05, .55, .59 + course * .9), (.8, 1.5, .85), "stone"))
        parts.append(add_box(f"WarningShelf.Capital.{side}", (side * 3.05, .55, 5.99), (1.1, 1.7, .3), "stone"))
    parts.append(add_box("WarningShelf.BrokenLintel", (-.55, .65, 6.29), (5.7, 1.5, .4), "stone"))
    return parts


def ours_unless_marker_parts():
    parts = [
        add_box("OursUnless.Foot", (0, 0, 0.04), (5.8, 3.8, 0.24), "soot"),
        add_box("OursUnless.Panel", (0, 0, 1.05), (4.8, 0.30, 2.8), "parchment"),
        add_torus("OursUnless.OursRing", (-0.85, -0.22, 2.45), 0.74, 0.10, "brass", (math.pi * 0.5, 0.0, 0.0)),
        add_rock("OursUnless.OursLight", (-0.85, -0.40, 2.45), (0.34, 0.16, 0.34), "water"),
        add_box("OursUnless.UnlessGap", (1.05, -0.22, 2.45), (1.35, 0.12, 1.35), "soot", 0.0),
        add_beam("OursUnless.UnlessSlash", (0.42, -0.42, 1.78), (1.68, -0.42, 3.12), 0.11, "rust"),
        add_cylinder("OursUnless.Crown", (0, 0, 3.85), (0, 0, 5.1), 0.15, "brass", 8),
        add_torus("OursUnless.CrownLight", (0, 0, 5.25), 0.42, 0.07, "water", (math.pi * 0.5, 0.0, 0.0)),
    ]
    return parts


def build_parts(identifier, source_spec):
    kind = source_spec["kind"]
    variant = source_spec.get("variant", "")
    if kind == "headframe":
        return headframe_parts(variant)
    if kind == "house":
        house = import_source(CLAIM_OFFICE, "timber", (7.2, 5.0, 5.1))
        parts = [house]
        if variant == "maintained":
            parts.extend([add_box("House.Repair", (2.2, -2.52, 1.5), (1.6, 0.09, 1.3), "rust", -0.08), add_cylinder("House.Stove", (2.3, 0.5, 4.5), (2.3, 0.5, 6.0), 0.20, "soot", 8)])
        else:
            house.rotation_euler.z = 0.05 if variant in {"abandoned", "south"} else -0.04
            parts.extend([add_beam("House.FallenA", (-3.0, -2.8, 0), (1.8, -3.0, 0.55), 0.16), add_box("House.Board", (-1.6, -2.54, 1.1), (1.4, 0.08, 0.22), "timber", 0.25)])
        return parts
    if kind == "camp":
        return [place(import_source(SOURCE["wagon"], "timber", (5.6, 2.8, 2.8)), (-2.8, 0, 0), -0.18), place(import_source(SOURCE["stockpile"], "timber", (5.2, 3.5, 2.5)), (3.2, 1.0, 0), 0.22)]
    if kind == "stake":
        return [add_beam("Stake.Post", (0, 0, 0), (0, 0, 3.4), 0.18), add_box("Stake.Plaque", (0, -0.03, 2.3), (1.6, 0.12, 0.95), "parchment", -0.06), add_torus("Stake.PanMark", (0, -0.12, 2.55), 0.32, 0.05, "brass", (math.pi * 0.5, 0, 0))]
    if kind == "riparian":
        parts = [place(import_source(SOURCE["sluice"], "timber", (8.5, 3.2, 2.5)), (0, 9.0, 0), -0.04)]
        for index, (x, y) in enumerate(((-5.0, 7.0), (-4.3, 7.3), (4.1, -9.5), (4.8, -9.8))):
            parts.append(add_cylinder(f"Reed.{index}", (x, y, 0), (x, y, 1.4 + index * 0.12), 0.055, "cactus", 6))
        parts.extend([add_rock("Riparian.BankRockA", (-3.8, -9.2, 0.28), (0.7, 0.5, 0.35), "stone"), add_rock("Riparian.BankRockB", (3.8, 8.2, 0.30), (0.75, 0.55, 0.38), "stone")])
        for index, y in enumerate(np.linspace(-5.6, 5.6, 7)):
            parts.append(add_rock(f"Riparian.FordStone.{index}", ((-0.25 if index % 2 else 0.25), y, 0.20), (0.72, 0.88, 0.24), "stone"))
        return parts
    if kind == "ruined-mine":
        ruin = import_source(STAMP_MILL, "timber", (7.5, 5.4, 5.7))
        return [ruin, add_beam("Ruin.FallenA", (-4.2, -2.8, 0), (1.4, -2.5, 0.7), 0.22), add_beam("Ruin.FallenB", (2.7, 2.9, 0), (4.5, -0.8, 1.2), 0.20), add_box("Ruin.Scorch", (-1.5, -2.75, 1.5), (1.9, 0.09, 1.8), "soot", 0.14)]
    if kind == "cactus":
        return cactus_parts()
    if kind == "skeleton":
        parts = [add_cylinder("Skeleton.Spine", (-2.7, 0, 0.45), (2.5, 0, 0.45), 0.13, "bone", 7), add_rock("Skeleton.Skull", (3.0, 0, 0.7), (0.7, 0.48, 0.52), "bone")]
        for index, x in enumerate(np.linspace(-2.0, 1.7, 7)):
            width = 1.25 - abs(x) * 0.16
            parts.extend([add_cylinder(f"Skeleton.RibL.{index}", (x, 0, 0.45), (x, width, 0.16), 0.065, "bone", 6), add_cylinder(f"Skeleton.RibR.{index}", (x, 0, 0.45), (x, -width, 0.16), 0.065, "bone", 6)])
        parts.extend([add_cylinder("Skeleton.HornL", (3.2, 0.25, 0.9), (3.8, 0.9, 1.15), 0.07, "bone", 6), add_cylinder("Skeleton.HornR", (3.2, -0.25, 0.9), (3.8, -0.9, 1.15), 0.07, "bone", 6)])
        return parts
    if kind == "spring":
        # Broken clusters around the authored pool, with open ground between them.
        parts=[]
        # Unequal, overlapping low stones at the bank, with smaller outer debris.
        for index in range(31):
            angle=index*2.399963229728653
            radius=1.38+.15*math.sin(angle*3)+(.26 if index%4==0 else 0)
            x,y=math.cos(angle)*radius,math.sin(angle)*radius
            size=.17+(index%5)*.032
            parts.append(add_rock(f"Spring.Rock.{index}", (x,y,.09+(index%3)*.02),
                (size*1.25,size,.10+(index%4)*.025), "stone"))
        return parts
    if kind == "winch":
        parts = [add_cylinder("Winch.Drum", (-0.9, 0, 1.45), (0.9, 0, 1.45), 0.58, "timber", 12), add_box("Winch.Base", (0, 0, 0), (4.2, 2.4, 0.28), "timber"), add_beam("Winch.SupportL", (-1.4, 0, 0.2), (-1.0, 0, 2.6), 0.22), add_beam("Winch.SupportR", (1.4, 0, 0.2), (1.0, 0, 2.6), 0.22), add_torus("Winch.Wheel", (1.15, -0.02, 1.5), 0.95, 0.10, "iron")]
        parts.append(add_beam("Winch.Crank", (1.15, -0.8, 1.5), (2.0, -1.2 if variant == "south" else -0.4, 1.9), 0.10, "iron"))
        return parts
    if kind == "floodplain":
        parts = [place(import_source(SOURCE["sluice"], "timber", (7.5, 3.0, 2.2)), (-4, 11.0, 0), -0.1), place(import_source(SOURCE["stockpile"], "timber", (5.0, 3.2, 2.2)), (4.2, -11.0, 0), 0.16)]
        for center_x in (-16.0, 16.0):
            for index, y in enumerate(np.linspace(-7.0, 7.0, 7)):
                parts.append(add_rock(f"Floodplain.FordStone.{center_x}.{index}", (center_x + (-0.28 if index % 2 else 0.28), y, 0.20), (0.75, 0.92, 0.25), "stone"))
        return parts
    if kind == "lanterns":
        # Blender Y is -game Z. These are the seven authored Night Shift
        # pre-placed fixtures, so the render body does not invent a second
        # lantern layout for eventual presentation replacement.
        positions = [(fixture["x"], -fixture["z"], 0) for fixture in NIGHT_LANTERN_FIXTURES]
        parts = []
        for index, position in enumerate(positions):
            parts.append(place(import_source(SOURCE["lantern"], "iron", (0.7, 0.7, 3.4)), position, 0.12 * index))
            parts.append(add_box(f"Lantern.Terrace.{index}", (position[0], position[1], 0), (3.4, 2.5, 0.28), "stone", 0.06 * index))
        return parts
    if kind == "lampworks":
        return [place(import_source(SOURCE["boiler"], "iron", (6.2, 5.0, 4.3)), (0, 0, 0), -0.08), place(import_source(SOURCE["stockpile"], "timber", (4.8, 3.2, 2.2)), (5.2, 1.8, 0), 0.18), place(import_source(SOURCE["lantern"], "iron", (0.7, 0.7, 3.5)), (-4, -2, 0)), place(import_source(SOURCE["lantern"], "iron", (0.7, 0.7, 3.5)), (4, -2, 0))]
    if kind == "rock-shoulders":
        parts = []
        for side in (-1, 1):
            for index in range(8):
                x = side * (19 + index * 1.4)
                y = -18 + index * 5.2
                parts.append(add_rock(f"Shoulder.{side}.{index}", (x, y, 1.4 + index % 3 * 0.3), (3.0, 2.2, 2.4 + index % 3 * 0.4), "stone"))
        return parts
    if kind == "ford":
        parts = [import_source(SOURCE["sluice"], "timber", (7.2, 2.8, 2.0))]
        for index, y in enumerate(np.linspace(-5.0, 5.0, 9)):
            parts.append(add_rock(f"Ford.Stone.{index}", ((-0.4 if index % 2 else 0.4), y, 0.18), (0.7, 0.9, 0.22), "stone"))
        return parts
    if kind == "road":
        parts = []
        for index, y in enumerate(np.linspace(-28, 28, 18)):
            parts.append(add_box(f"Road.Sleeper.{index}", (math.sin(index * 0.7) * 0.5, y, 0), (3.2, 0.28, 0.12), "timber", 0.04 * math.sin(index)))
            for side in (-1.15, 1.15):
                parts.append(add_box(f"Road.Rut.{index}.{side}", (side, y, 0.04), (0.16, 3.35, 0.08), "soot"))
        return parts
    if kind == "fortified":
        parts = []
        for index, x in enumerate((-12, -6, 0, 6, 12)):
            parts.append(place(import_source(SOURCE["palisade"], "timber", (5.8, 1.0, 4.2)), (x, 0, 0), 0.04 * (index - 2)))
        parts.extend([add_box("Fort.PlatformL", (-9, 1.2, 2.3), (3.0, 2.8, 0.35), "timber"), add_box("Fort.PlatformR", (9, 1.2, 2.3), (3.0, 2.8, 0.35), "timber")])
        return parts
    if kind == "rocket-cart":
        cabin = import_source(RAILCAR, "iron", (2.9, 2.4, 3.0), source_spec.get("select"))
        parts = [cabin, add_box("RocketCart.Bed", (-2.2, 0, 0), (4.4, 2.5, 0.45), "timber")]
        for x in (-3.1, -1.3, 0.9):
            for y in (-1.15, 1.15):
                parts.append(add_cylinder(f"RocketCart.Wheel.{x}.{y}", (x, y - 0.16, 0.65), (x, y + 0.16, 0.65), 0.48, "iron", 8))
        parts.extend([add_cylinder("RocketCart.Body", (-3.3, 0, 1.4), (-0.1, 0, 2.6), 0.42, "rust", 10), add_cylinder("RocketCart.Nozzle", (-3.7, 0, 1.25), (-3.25, 0, 1.42), 0.56, "soot", 10)])
        return parts
    if kind == "siege":
        return [place(import_source(SOURCE["palisade"], "timber", (5.6, 0.9, 3.8)), (x, 0, 0), 0.05 * index) for index, x in enumerate((-11, -5.5, 0, 5.5, 11))]
    if kind == "banners":
        parts = []
        positions = ((-14, 8.2), (-7, 8.6), (0, -8.2), (7, 8.4), (14, -8.6))
        for index, (x, y) in enumerate(positions):
            parts.append(add_cylinder(f"Banner.Pole.{index}", (x, y, 0), (x, y, 5.0 + index % 2 * 0.8), 0.10, "iron", 7))
            parts.append(add_box(f"Banner.Cloth.{index}", (x + 0.75, y, 3.2), (1.5, 0.06, 1.4), "cloth", -0.08 + index * 0.03))
        return parts
    if kind == "boiler":
        return boiler_worksite_parts(variant)
    if kind == "gallery":
        parts = [
            import_source(SOURCE["sluice"], "timber", (7.2, 2.8, 1.85)),
            add_box("Gallery.BlackMouth", (0, 1.22, 0.2), (5.7, 0.36, 2.7), "soot"),
            add_beam("Gallery.Roof", (-3.2, 0, 3.2), (3.2, 0, 3.2), 0.28),
            add_cylinder("Gallery.PumpDrum", (-1.05, -0.65, 0.85), (1.05, -0.65, 0.85), 0.52, "iron", 12),
            add_torus("Gallery.PumpWheel", (1.15, -0.65, 0.9), 0.72, 0.08, "brass"),
        ]
        for x in (-3.2, 3.2):
            for y in (-1.2, 1.2):
                parts.append(add_beam(f"Gallery.Prop.{x}.{y}", (x, y, 0), (x * 0.92, y, 3.2), 0.24))
        parts.extend([
            add_beam("Gallery.BraceA", (-3.2, -1.2, 0.2), (3.0, -1.2, 2.8), 0.15),
            add_beam("Gallery.BraceB", (3.2, 1.2, 0.2), (-3.0, 1.2, 2.8), 0.15),
            add_beam("Gallery.FallenProp", (-3.8, -2.2, 0.08), (2.9, -2.0, 0.62), 0.17, "timber"),
        ])
        for x in (-0.55, 0.55):
            parts.append(add_box(f"Gallery.TramRail.{x}", (x, -3.2, 0.12), (0.11, 7.2, 0.11), "iron"))
        for index, y in enumerate(np.linspace(-6.4, -0.25, 7)):
            parts.append(add_box(f"Gallery.Sleeper.{index}", (0, float(y), 0.04), (1.7, 0.22, 0.12), "timber", 0.03 * math.sin(index)))
        return parts
    if kind == "rail-kit":
        parts = []
        for run, (x, y, yaw, length) in enumerate(((-0.7, -8.5, -0.12, 13.0), (0.55, 2.5, 0.11, 12.0), (-0.6, 12.0, -0.08, 9.5))):
            cosine, sine = math.cos(yaw), math.sin(yaw)
            for rail in (-0.55, 0.55):
                rx = x + cosine * rail
                ry = y + sine * rail
                parts.append(add_box(f"Switchback.Rail.{run}.{rail}", (rx, ry, 0.15), (0.11, length, 0.12), "iron", yaw))
            for index in range(8):
                offset = -length * 0.5 + (index + 0.5) * length / 8
                sx = x - sine * offset
                sy = y + cosine * offset
                parts.append(add_box(f"Switchback.Sleeper.{run}.{index}", (sx, sy, 0.03), (1.72, 0.23, 0.13), "timber", yaw))
        parts.extend([
            add_box("Switchback.PointA", (0.55, -2.2, 0.16), (0.10, 7.2, 0.10), "iron", 0.16),
            add_box("Switchback.PointB", (-0.5, 8.1, 0.16), (0.10, 6.2, 0.10), "iron", -0.14),
            add_beam("Switchback.BrokenRail", (-1.4, 15.5, 0.12), (1.0, 18.2, 0.55), 0.10, "rust"),
        ])
        for index, y in enumerate((-12.0, -4.0, 5.0, 14.0)):
            parts.append(add_box(f"Switchback.RetainingPost.{index}", (-1.8 + (index % 2) * 3.6, y, 0), (0.28, 0.28, 1.35 + 0.2 * (index % 2)), "timber", 0.05 * (index - 2)))
        return parts
    if kind == "tailings":
        parts = [import_source(SOURCE["stockpile"], "timber", (5.5, 3.8, 2.4))]
        for index in range(14):
            angle = math.tau * index / 14
            parts.append(add_rock(f"Tailings.{index}", (math.cos(angle) * (3.0 + index % 3), math.sin(angle) * 2.7, 0.45), (0.7 + index % 3 * 0.2, 0.6, 0.55 + index % 2 * 0.3), "earth"))
        for index, y in enumerate((-2.4, -0.8, 0.8, 2.4)):
            parts.extend([
                add_beam(f"Tailings.CribL.{index}", (-3.2, y, 0), (-3.0, y, 1.5 + 0.12 * index), 0.16, "timber"),
                add_beam(f"Tailings.CribR.{index}", (3.2, y, 0), (3.0, y, 1.25 + 0.10 * index), 0.16, "timber"),
            ])
        parts.extend([
            add_box("Tailings.BrokenCart", (1.6, -3.6, 0.35), (2.6, 1.5, 0.75), "rust", -0.18),
            add_torus("Tailings.CartWheelL", (0.75, -4.32, 0.45), 0.46, 0.06, "iron"),
            add_torus("Tailings.CartWheelR", (2.45, -4.32, 0.45), 0.46, 0.06, "iron"),
        ])
        return parts
    if kind == "trestle":
        parts = rail_parts(18.0, 18, 4.2)
        for deck_index, y in enumerate(np.linspace(-8.5, 8.5, 10)):
            parts.append(add_box(f"Trestle.DeckBeam.{deck_index}", (0, float(y), 3.92), (3.8, 0.24, 0.26), "timber"))
        for y in (-7.0, -3.5, 0, 3.5, 7.0):
            parts.extend([
                add_beam(f"Trestle.PostL.{y}", (-1.4, y, 0), (-1.4, y, 4.1), 0.25),
                add_beam(f"Trestle.PostR.{y}", (1.4, y, 0), (1.4, y, 4.1), 0.25),
                add_beam(f"Trestle.Cross.{y}", (-1.4, y, 2.1), (1.4, y, 2.1), 0.19),
                add_beam(f"Trestle.XA.{y}", (-1.4, y - 1.35, 0.25), (1.4, y + 1.35, 3.8), 0.14),
                add_beam(f"Trestle.XB.{y}", (1.4, y - 1.35, 0.25), (-1.4, y + 1.35, 3.8), 0.14),
            ])
        parts.extend([
            add_beam("Trestle.BraceA", (-1.4, -7, 0), (1.4, 7, 4.1), 0.16),
            add_beam("Trestle.BraceB", (1.4, -7, 0), (-1.4, 7, 4.1), 0.16),
            add_box("Trestle.RepairPlate", (1.48, 2.0, 1.8), (0.08, 1.2, 1.55), "rust", 0.08),
            add_beam("Trestle.FallenBrace", (-2.2, -8.0, 0.05), (2.5, -4.8, 0.55), 0.16, "timber"),
        ])
        for side in (-1, 1):
            inner_y, outer_y = side * 9.0, side * 15.0
            for x in (-0.55, 0.55):
                parts.append(add_beam(f"Trestle.ApproachRail.{side}.{x}", (x, inner_y, 4.2), (x, outer_y, 0.18), 0.12, "iron"))
            for index in range(7):
                t = index / 6.0
                y = inner_y + (outer_y - inner_y) * t
                height = 4.2 + (0.18 - 4.2) * t
                parts.append(add_box(f"Trestle.ApproachSleeper.{side}.{index}", (0, y, max(0, height - 0.14)), (1.65, 0.22, 0.14), "timber"))
        return parts
    if kind == "approach":
        return approach_worksite_parts(variant)
    if kind == "mine-spur":
        parts = rail_parts(16.0, 10)
        parts.extend([
            place(import_source(SOURCE["coal"], "timber", (3.2, 2.4, 1.4)), (2.8, 3.5, 0), -0.12),
            add_box("MineSpur.OreBin", (-2.7, 3.0, 0.1), (3.1, 2.4, 1.6), "timber", 0.08),
            add_box("MineSpur.Point", (0.65, -3.2, 0.16), (0.10, 7.5, 0.10), "iron", -0.18),
            add_beam("MineSpur.FallenRail", (-1.6, 7.2, 0.08), (2.0, 9.0, 0.45), 0.10, "rust"),
        ])
        for index in range(7):
            parts.append(add_rock(f"MineSpur.Tailings.{index}", (-4.0 + index * 0.72, 5.5 + 0.3 * (index % 2), 0.28), (0.48, 0.40, 0.32), "earth"))
        return parts
    if kind == "incline-worksite":
        return incline_worksite_parts(variant)
    if kind == "boneyard-flivver":
        return boneyard_flivver_parts(variant)
    if kind == "boneyard-boiler":
        return boneyard_boiler_parts(variant)
    if kind == "boneyard-hauler-bed":
        return boneyard_hauler_bed_parts(variant)
    if kind == "boneyard-sleeper":
        return boneyard_sleeper_parts()
    if kind == "boneyard-wagon":
        return boneyard_wagon_parts()
    if kind == "long-road-station":
        return long_road_station_parts(variant)
    if kind == "long-road-hauler":
        return long_road_hauler_parts()
    if kind == "long-road-railhead":
        return long_road_railhead_parts()
    if kind == "race-gate":
        return race_gate_parts(variant)
    if kind == "buoy-anchor":
        return buoy_anchor_parts(variant)
    if kind == "spectator-raft":
        return spectator_raft_parts(variant)
    if kind == "judges-tower":
        return judges_tower_parts()
    if kind == "ridge-dish-cluster":
        return ridge_dish_cluster_parts(variant)
    if kind == "dead-gap-chart-station":
        return dead_gap_chart_station_parts()
    if kind == "signal-cable-yard":
        return signal_cable_yard_parts()
    if kind == "drone-recovery-beacon":
        return drone_recovery_beacon_parts()
    if kind == "earthrise-listening-array":
        return earthrise_listening_array_parts()
    if kind == "lava-tube-survey-gantry":
        return lava_tube_survey_gantry_parts()
    if kind == "regolith-core-yard":
        return regolith_core_yard_parts()
    if kind == "rim-debris-catcher":
        return rim_debris_catcher_parts(variant)
    if kind == "eclipse-kit":
        return eclipse_kit_parts(variant)
    if kind == "storm-anchor-gate":
        return storm_anchor_gate_parts(variant)
    if kind == "wind-anchor":
        return wind_anchor_parts(variant)
    if kind == "archive-entry-gate":
        return archive_entry_gate_parts()
    if kind == "archive-stack-ruin":
        return archive_stack_ruin_parts(variant)
    if kind == "archive-warning-shelf":
        return archive_warning_shelf_parts()
    if kind == "ours-unless-marker":
        return ours_unless_marker_parts()
    raise ValueError(f"unknown landmark kind {kind} for {identifier}")


def glb_bounds(obj):
    bounds = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
    return {
        "min": [round(min(getattr(p, axis) for p in bounds), 4) for axis in ("x", "y", "z")],
        "max": [round(max(getattr(p, axis) for p in bounds), 4) for axis in ("x", "y", "z")],
    }


def export_asset(asset, path):
    bpy.ops.object.select_all(action="DESELECT")
    asset.hide_set(False)
    asset.select_set(True)
    bpy.context.view_layer.objects.active = asset
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False,
        export_materials="EXPORT", export_extras=True,
    )
    asset.select_set(False)


def import_asset(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]
    if len(meshes) != 1:
        raise ValueError(f"expected one landmark mesh in {path}; found {len(meshes)}")
    asset = meshes[0]
    # glTF imports use quaternion mode; all pack mount contracts store yaw.
    asset.rotation_mode = "XYZ"
    return asset


def terrain_height(terrain, x, game_z):
    hit, location, _normal, _face = terrain.ray_cast((x, -game_z, 100.0), (0.0, 0.0, -1.0))
    return float(location.z) if hit else 0.0


def make_verdict_water(key, profile):
    """Runtime-water stand-in for mounted evidence; never saved or exported."""
    if key in {"dry-gulch", "boneyard", "long-road", "relay-valley", "mare-claim", "eclipse", "devils-alley", "archive-world"}:
        return None
    if key == "regatta":
        bpy.ops.mesh.primitive_plane_add(size=128.0, location=(0.0, 0.0, 0.04))
        water = bpy.context.object
        water.name = "regatta.LandmarkVerdictWater"
        material = claim.make_water_material(
            "regatta.LandmarkVerdictWaterMaterial", (0.018, 0.16, 0.18), (0.095, 0.42, 0.44), 0.54
        )
        water.data.materials.append(material)
        return water
    half_width = 7.8 if key == "twin-banks" else 6.25
    half_length = 48.0 if profile["era"] == 2 else 32.0
    segments = 96
    vertices = []
    faces = []
    for index in range(segments + 1):
        x = -half_length + half_length * 2.0 * index / segments
        vertices.extend(((x, -half_width, 0.04), (x, half_width, 0.04)))
    for index in range(segments):
        a = index * 2
        faces.extend(((a, a + 3, a + 2), (a, a + 1, a + 3)))
    mesh = bpy.data.meshes.new(f"{key}.LandmarkVerdictWaterMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    water = bpy.data.objects.new(f"{key}.LandmarkVerdictWater", mesh)
    bpy.context.collection.objects.link(water)
    if profile.get("night"):
        material = claim.make_water_material(f"{key}.LandmarkVerdictWaterMaterial", (0.008, 0.007, 0.005), (0.055, 0.034, 0.016), 0.66)
    else:
        material = claim.make_water_material(f"{key}.LandmarkVerdictWaterMaterial", (0.020, 0.016, 0.010), (0.145, 0.095, 0.040), 0.62)
    shader = material.node_tree.nodes.get("Principled BSDF")
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.0 if key == "incline" else 0.18
    if "Coat Weight" in shader.inputs:
        shader.inputs["Coat Weight"].default_value = 0.0 if key == "incline" else 0.01
    if key == "incline":
        shader.inputs["Roughness"].default_value = 0.96
    mesh.materials.append(material)
    return water


def render_mounted(key, profile, terrain_contract):
    claim.reset_scene()
    terrain = import_asset(OUT / profile["terrain"])
    bpy.ops.import_scene.gltf(filepath=str(OUT / profile["panorama"]))
    make_verdict_water(key, profile)
    if key == "incline":
        e2.add_rails(
            key,
            {"tileParams": {"rails": terrain_contract["maskTruth"]["rails"]}},
            lambda x, game_z: terrain_height(terrain, x, game_z),
            e2.preview_materials(key),
        )
    canonical_mounts = terrain_contract["landmarkMounts"]
    evidence_mounts = canonical_mounts or profile.get("previewMounts", [])
    for mount in evidence_mounts:
        asset = import_asset(OUT / mount["asset"])
        x, offset_y, game_z = mount["position"]
        base_z = 0.06 if key == "regatta" else terrain_height(terrain, x, game_z)
        asset.location = (x, -game_z, base_z + offset_y)
        asset.rotation_euler.z = -mount["rotation"][1]
        asset.scale = mount["scale"]
    camera = claim.add_camera(f"{key}.LandmarkRunCamera", *profile["camera"])
    if key in {"incline", "long-road"}:
        camera.data.clip_end = 520.0 if key == "long-road" else 430.0
    lights = claim.add_lighting(sunset=bool(profile.get("night")))
    if profile.get("night"):
        # Keep the contract nocturnal without hiding the mounted silhouettes.
        # This is verdict-only fill; lights are never exported with the pack.
        fill_data = bpy.data.lights.new("NightVerdictFill", "AREA")
        lights[0].data.energy = 1.25
        fill_data.energy = 4000.0
        fill_data.color = (0.30, 0.40, 0.52)
        fill_data.shape = "DISK"
        fill_data.size = 32.0
        fill = bpy.data.objects.new("NightVerdictFill", fill_data)
        bpy.context.collection.objects.link(fill)
        fill.location = (-18.0, -12.0, 28.0)
        claim.aim_at(fill, (0.0, -5.0, 0.0))
        for index, (x, y) in enumerate((fixture["x"], -fixture["z"]) for fixture in NIGHT_LANTERN_FIXTURES):
            lamp_data = bpy.data.lights.new(f"NightLanternPool.{index}", "POINT")
            lamp_data.energy = 280.0
            lamp_data.color = (1.0, 0.34, 0.08)
            lamp_data.shadow_soft_size = 1.0
            lamp = bpy.data.objects.new(f"NightLanternPool.{index}", lamp_data)
            bpy.context.collection.objects.link(lamp)
            lamp.location = (x, y, 3.2)
        yard_data = bpy.data.lights.new("NightLampworksPool", "POINT")
        yard_data.energy = 520.0
        yard_data.color = (1.0, 0.26, 0.055)
        yard_data.shadow_soft_size = 2.5
        yard = bpy.data.objects.new("NightLampworksPool", yard_data)
        bpy.context.collection.objects.link(yard)
        yard.location = (8.0, -18.0, 5.0)
        bpy.context.scene.view_settings.exposure = 1.34
    else:
        fill_data = bpy.data.lights.new("LandmarkVerdictFill", "AREA")
        fill_data.energy = 2400.0 if key == "regatta" else (4600.0 if key == "long-road" else 4200.0 if key == "boneyard" else 3600.0 if key == "relay-valley" else 2600.0 if key in {"incline", "mare-claim", "eclipse", "devils-alley", "archive-world"} else 520.0)
        fill_data.color = (0.56, 0.70, 0.68) if key == "regatta" else ((0.48, 0.50, 0.46) if key == "eclipse" else (0.40, 0.62, 0.58) if key == "relay-valley" else (0.42, 0.58, 0.56) if key == "incline" else (0.42, 0.54, 0.48) if key == "archive-world" else (0.56, 0.36, 0.22) if key == "devils-alley" else (0.40, 0.55, 0.56) if key == "mare-claim" else (0.48, 0.34, 0.20))
        fill_data.shape = "DISK"
        fill_data.size = 92.0 if key == "long-road" else 52.0 if key == "regatta" else (46.0 if key in {"boneyard", "relay-valley", "mare-claim", "eclipse", "devils-alley", "archive-world"} else 40.0 if key == "incline" else 36.0)
        fill = bpy.data.objects.new("LandmarkVerdictFill", fill_data)
        bpy.context.collection.objects.link(fill)
        fill.location = (0.0, 58.0, 76.0) if key == "long-road" else (10.0, 28.0, 42.0) if key == "relay-valley" else (22.0, 32.0, 44.0) if key == "incline" else (16.0, 42.0, 52.0) if key == "boneyard" else (8.0, 38.0, 38.0) if key in {"mare-claim", "eclipse", "devils-alley", "archive-world"} else (12.0, -18.0, 42.0 if key == "regatta" else 30.0)
        claim.aim_at(fill, (0.0, 0.0, 0.0))
        if key == "long-road":
            world = bpy.context.scene.world.node_tree.nodes.get("Background")
            world.inputs["Color"].default_value = (0.075, 0.040, 0.016, 1.0)
            world.inputs["Strength"].default_value = 1.28
            lights[0].data.energy = 3.7
            lights[0].data.color = (1.0, 0.77, 0.48)
            lights[0].data.angle = math.radians(20.0)
            for index, mount in enumerate(terrain_contract["landmarkMounts"]):
                x, _offset, game_z = mount["position"]
                pool_data = bpy.data.lights.new(f"LongRoadLandmarkPool.{index}", "POINT")
                pool_data.energy = 820.0 if index in {0, 1, 2} else 620.0
                pool_data.color = (0.06, 0.65, 0.60) if index in {1, 4} else (1.0, 0.48, 0.10)
                pool_data.shadow_soft_size = 2.8
                pool = bpy.data.objects.new(f"LongRoadLandmarkPool.{index}", pool_data)
                bpy.context.collection.objects.link(pool)
                pool.location = (x, -game_z, 7.5)
            bpy.context.scene.view_settings.exposure = 1.52
        elif key == "regatta":
            world = bpy.context.scene.world.node_tree.nodes.get("Background")
            world.inputs["Color"].default_value = (0.030, 0.050, 0.052, 1.0)
            world.inputs["Strength"].default_value = 1.15
            lights[0].data.energy = 2.8
            lights[0].data.color = (0.70, 0.82, 0.78)
            bpy.context.scene.view_settings.exposure = 1.25
        elif key == "relay-valley":
            world = bpy.context.scene.world.node_tree.nodes.get("Background")
            world.inputs["Color"].default_value = (0.020, 0.032, 0.030, 1.0)
            world.inputs["Strength"].default_value = 1.20
            lights[0].data.energy = 3.5
            lights[0].data.color = (0.70, 0.78, 0.68)
            face_data = bpy.data.lights.new("RelayValleyFrontRake", "SUN")
            face_data.energy = 2.35
            face_data.color = (0.50, 0.63, 0.60)
            face_data.angle = math.radians(14.0)
            face = bpy.data.objects.new("RelayValleyFrontRake", face_data)
            bpy.context.collection.objects.link(face)
            face.location = (24.0, 42.0, 44.0)
            claim.aim_at(face, (0.0, 0.0, 0.0))
            for index, mount in enumerate(profile.get("previewMounts", [])):
                x, _offset, game_z = mount["position"]
                pool_data = bpy.data.lights.new(f"RelayLandmarkPool.{index}", "POINT")
                pool_data.energy = 1050.0 if index < 3 else 650.0
                pool_data.color = (0.06, 0.72, 0.66) if index != 3 else (1.0, 0.50, 0.10)
                pool_data.shadow_soft_size = 2.2
                pool = bpy.data.objects.new(f"RelayLandmarkPool.{index}", pool_data)
                bpy.context.collection.objects.link(pool)
                pool.location = (x, -game_z, 6.0)
            bpy.context.scene.view_settings.exposure = 1.62
        elif key == "incline":
            world = bpy.context.scene.world.node_tree.nodes.get("Background")
            world.inputs["Color"].default_value = (0.16, 0.09, 0.035, 1.0)
            world.inputs["Strength"].default_value = 1.10
            lights[0].data.energy = 3.0
            lights[0].data.color = (1.0, 0.84, 0.62)
            lights[0].data.angle = math.radians(24.0)
            bpy.context.scene.view_settings.exposure = 1.30
        elif key == "boneyard":
            world = bpy.context.scene.world.node_tree.nodes.get("Background")
            world.inputs["Color"].default_value = (0.085, 0.050, 0.025, 1.0)
            world.inputs["Strength"].default_value = 1.32
            lights[0].data.energy = 3.6
            lights[0].data.color = (1.0, 0.78, 0.50)
            lights[0].data.angle = math.radians(18.0)
            bpy.context.scene.view_settings.exposure = 1.58
        elif key in {"mare-claim", "eclipse"}:
            world = bpy.context.scene.world.node_tree.nodes.get("Background")
            world.inputs["Color"].default_value = (0.018, 0.028, 0.032, 1.0)
            world.inputs["Strength"].default_value = 1.12
            lights[0].data.energy = 3.0
            lights[0].data.color = (0.58, 0.70, 0.68)
            lunar_mounts = profile.get("previewMounts") or terrain_contract["landmarkMounts"]
            for index, mount in enumerate(lunar_mounts):
                x, _offset, game_z = mount["position"]
                pool_data = bpy.data.lights.new(f"MareClaimLandmarkPool.{index}", "POINT")
                pool_data.energy = 980.0 if key == "eclipse" else 700.0
                pool_data.color = (0.92, 0.48, 0.14) if key == "eclipse" and index in {0, 3} else ((0.06, 0.70, 0.68) if index in {0, 2} else (0.92, 0.48, 0.14))
                pool_data.shadow_soft_size = 2.4
                pool = bpy.data.objects.new(f"MareClaimLandmarkPool.{index}", pool_data)
                bpy.context.collection.objects.link(pool)
                pool.location = (x, -game_z, 6.2)
            bpy.context.scene.view_settings.exposure = 1.62 if key == "eclipse" else 1.46
        elif key == "devils-alley":
            world = bpy.context.scene.world.node_tree.nodes.get("Background")
            world.inputs["Color"].default_value = (0.050, 0.015, 0.008, 1.0)
            world.inputs["Strength"].default_value = 1.10
            lights[0].data.energy = 3.4
            lights[0].data.color = (0.76, 0.48, 0.28)
            for index, mount in enumerate(terrain_contract["landmarkMounts"]):
                x, _offset, game_z = mount["position"]
                pool_data = bpy.data.lights.new(f"DevilsAlleyLandmarkPool.{index}", "POINT")
                pool_data.energy = 780.0
                pool_data.color = (0.92, 0.34, 0.08) if index in {0, 4} else (0.08, 0.58, 0.55)
                pool_data.shadow_soft_size = 2.5
                pool = bpy.data.objects.new(f"DevilsAlleyLandmarkPool.{index}", pool_data)
                bpy.context.collection.objects.link(pool)
                pool.location = (x, -game_z, 6.0)
            bpy.context.scene.view_settings.exposure = 1.52
        elif key == "archive-world":
            world = bpy.context.scene.world.node_tree.nodes.get("Background")
            world.inputs["Color"].default_value = (0.010, 0.018, 0.018, 1.0)
            world.inputs["Strength"].default_value = 0.88
            lights[0].data.energy = 2.8
            lights[0].data.color = (0.62, 0.67, 0.58)
            for index, mount in enumerate(terrain_contract["landmarkMounts"]):
                x, _offset, game_z = mount["position"]
                pool_data = bpy.data.lights.new(f"ArchiveWorldLandmarkPool.{index}", "POINT")
                pool_data.energy = 900.0 if index != 4 else 650.0
                pool_data.color = (0.08, 0.68, 0.64) if index in {1, 2} else (0.92, 0.57, 0.16)
                pool_data.shadow_soft_size = 2.6
                pool = bpy.data.objects.new(f"ArchiveWorldLandmarkPool.{index}", pool_data)
                bpy.context.collection.objects.link(pool)
                pool.location = (x, -game_z, 6.2)
            bpy.context.scene.view_settings.exposure = 1.62
    suffix = "mounted" if canonical_mounts else "proposed"
    claim.render(camera, ARTIFACTS / f"{key}-landmarks-{suffix}.png")
    if profile.get("overviewCamera"):
        overview = claim.add_camera(f"{key}.LandmarkOverviewCamera", *profile["overviewCamera"])
        overview.data.clip_end = 650.0 if key == "long-road" else 430.0
        if key == "archive-world":
            bpy.context.scene.view_settings.exposure = 2.12
        claim.render(overview, ARTIFACTS / f"{key}-landmarks-{suffix}-overview.png")
    if key == "long-road":
        for index, mount in enumerate(evidence_mounts, 1):
            x, _offset, game_z = mount["position"]
            stop_camera = claim.add_camera(
                f"long-road.LandmarkRouteCamera.{index}",
                (x - 28.0, -game_z + 52.0, 35.0),
                (x, -game_z, 0.4),
                44.0,
            )
            stop_camera.data.clip_end = 520.0
            claim.render(stop_camera, ARTIFACTS / f"long-road-landmarks-route-{index}.png")
    if key == "boneyard":
        truth = terrain_contract["maskTruth"]
        materials = {
            "pads": claim.make_render_material("BoneyardClearance.BuildPads", (0.06, 0.72, 0.66)),
            "roads": claim.make_render_material("BoneyardClearance.Roads", (0.95, 0.38, 0.06)),
            "harvest": claim.make_render_material("BoneyardClearance.Harvest", (0.32, 0.82, 0.24)),
            "sleeper": claim.make_render_material("BoneyardClearance.Sleeper", (0.88, 0.10, 0.055)),
            "spawns": claim.make_render_material("BoneyardClearance.Spawns", (0.54, 0.32, 0.82)),
            "landmarks": claim.make_render_material("BoneyardClearance.Landmarks", (0.92, 0.86, 0.62)),
        }

        def boneyard_curve(name, points, role, lift=1.0, radius=0.22):
            claim.add_curve(
                name,
                [(x, game_z, terrain_height(terrain, x, game_z) + lift) for x, game_z in points],
                radius,
                materials[role],
            )

        def boneyard_ring(name, x, game_z, radius, role, lift=1.08):
            boneyard_curve(
                name,
                [(x + math.cos(math.tau * step / 24.0) * radius, game_z + math.sin(math.tau * step / 24.0) * radius) for step in range(25)],
                role,
                lift,
                0.18,
            )

        for zone in truth["buildZones"]:
            boneyard_curve(
                f"BoneyardClearance.{zone['id']}",
                [(zone["minX"], zone["minZ"]), (zone["maxX"], zone["minZ"]), (zone["maxX"], zone["maxZ"]), (zone["minX"], zone["maxZ"]), (zone["minX"], zone["minZ"])],
                "pads",
            )
        for index, road in enumerate(truth["roadCorridors"]):
            boneyard_curve(
                f"BoneyardClearance.Road.{index}",
                [(road["start"]["x"], road["start"]["z"]), (road["end"]["x"], road["end"]["z"])],
                "roads", 1.14, 0.28,
            )
        for index, anchor in enumerate(truth["harvestAnchors"]):
            boneyard_ring(f"BoneyardClearance.Harvest.{index}", anchor["x"], anchor["z"], 1.7, "harvest")
        boneyard_ring("BoneyardClearance.Sleeper", truth["sleeper"]["x"], truth["sleeper"]["z"], truth["sleeper"]["radius"], "sleeper", 1.18)
        for index, gate in enumerate(truth["spawnGates"]):
            boneyard_ring(f"BoneyardClearance.Spawn.{index}", gate["x"], gate["z"], 3.5, "spawns", 1.22)

        pack_contract = json.loads((LANDMARKS / key / f"{key}-landmark-pack-contract.json").read_text(encoding="utf-8"))

        def distance_to_segment(x, game_z, start, end):
            vx, vz = end[0] - start[0], end[1] - start[1]
            amount = max(0.0, min(1.0, ((x - start[0]) * vx + (game_z - start[1]) * vz) / (vx * vx + vz * vz)))
            return math.hypot(x - (start[0] + amount * vx), game_z - (start[1] + amount * vz))

        for index, mount in enumerate(evidence_mounts):
            record = pack_contract["assets"][mount["id"]]
            width = record["bounds"]["max"][0] - record["bounds"]["min"][0]
            depth = record["bounds"]["max"][1] - record["bounds"]["min"][1]
            yaw = mount["rotation"][1]
            cosine, sine = abs(math.cos(yaw)), abs(math.sin(yaw))
            scale = mount["scale"][0]
            half_x = (width * cosine + depth * sine) * scale * 0.5
            half_z = (width * sine + depth * cosine) * scale * 0.5
            x, _offset, game_z = mount["position"]
            radius = math.hypot(half_x, half_z)
            assert -64.0 <= x - half_x and x + half_x <= 64.0 and -64.0 <= game_z - half_z and game_z + half_z <= 64.0
            assert all(
                distance_to_segment(x, game_z, (road["start"]["x"], road["start"]["z"]), (road["end"]["x"], road["end"]["z"])) > radius + 2.0
                for road in truth["roadCorridors"]
            )
            assert all(math.hypot(x - gate["x"], game_z - gate["z"]) > radius + 3.5 for gate in truth["spawnGates"])
            boneyard_curve(
                f"BoneyardClearance.Landmark.{index}",
                [(x - half_x, game_z - half_z), (x + half_x, game_z - half_z), (x + half_x, game_z + half_z), (x - half_x, game_z + half_z), (x - half_x, game_z - half_z)],
                "landmarks", 1.28, 0.18,
            )
        clearance = claim.add_camera("boneyard.LandmarkClearanceCamera", (0.0, 0.0, 196.0), (0.0, 0.0, 0.0), 49.0)
        clearance.data.clip_end = 430.0
        claim.render(clearance, ARTIFACTS / "boneyard-landmarks-clearance-overlay.png")
    if key == "long-road":
        truth = terrain_contract["maskTruth"]
        materials = {
            "pads": claim.make_render_material("LongRoadClearance.RestStops", (0.06, 0.72, 0.66)),
            "roads": claim.make_render_material("LongRoadClearance.Roads", (0.95, 0.38, 0.06)),
            "route": claim.make_render_material("LongRoadClearance.ConvoyRoute", (0.96, 0.74, 0.08)),
            "harvest": claim.make_render_material("LongRoadClearance.Harvest", (0.32, 0.82, 0.24)),
            "stake": claim.make_render_material("LongRoadClearance.LossStake", (0.88, 0.10, 0.055)),
            "spawns": claim.make_render_material("LongRoadClearance.Spawns", (0.54, 0.32, 0.82)),
            "landmarks": claim.make_render_material("LongRoadClearance.Landmarks", (1.0, 1.0, 1.0)),
        }

        def long_road_curve(name, points, role, lift=1.0, radius=0.25):
            claim.add_curve(
                name,
                [(x, game_z, terrain_height(terrain, x, game_z) + lift) for x, game_z in points],
                radius,
                materials[role],
            )

        def long_road_ring(name, x, game_z, radius, role, lift=1.08):
            long_road_curve(
                name,
                [(x + math.cos(math.tau * step / 24.0) * radius, game_z + math.sin(math.tau * step / 24.0) * radius) for step in range(25)],
                role,
                lift,
                0.24,
            )

        zones = {zone["id"]: zone for zone in truth["buildZones"]}
        for zone in truth["buildZones"]:
            long_road_curve(
                f"LongRoadClearance.{zone['id']}",
                [(zone["minX"], zone["minZ"]), (zone["maxX"], zone["minZ"]), (zone["maxX"], zone["maxZ"]), (zone["minX"], zone["maxZ"]), (zone["minX"], zone["minZ"])],
                "pads", 1.14, 0.34,
            )
        for index, road in enumerate(truth["roadCorridors"]):
            long_road_curve(
                f"LongRoadClearance.Road.{index}",
                [(road["start"]["x"], road["start"]["z"]), (road["end"]["x"], road["end"]["z"])],
                "roads", 1.18, 0.31,
            )
        long_road_curve(
            "LongRoadClearance.ConvoyRoute",
            [(point["x"], point["z"]) for point in truth["convoyRoute"]],
            "route", 1.32, 0.42,
        )
        for index, anchor in enumerate(truth["harvestAnchors"]):
            long_road_ring(f"LongRoadClearance.Harvest.{index}", anchor["x"], anchor["z"], 1.7, "harvest")
        stake = truth["stakeMarkers"][0]
        long_road_ring("LongRoadClearance.LossStake", stake["x"], stake["z"], 3.0, "stake", 1.22)
        for index, gate in enumerate(truth["spawnGates"]):
            long_road_ring(f"LongRoadClearance.Spawn.{index}", gate["x"], gate["z"], 4.0, "spawns", 1.22)

        pack_contract = json.loads((LANDMARKS / key / f"{key}-landmark-pack-contract.json").read_text(encoding="utf-8"))
        for index, mount in enumerate(evidence_mounts):
            record = pack_contract["assets"][mount["id"]]
            width = record["bounds"]["max"][0] - record["bounds"]["min"][0]
            depth = record["bounds"]["max"][1] - record["bounds"]["min"][1]
            yaw = mount["rotation"][1]
            cosine, sine = abs(math.cos(yaw)), abs(math.sin(yaw))
            scale = mount["scale"][0]
            half_x = (width * cosine + depth * sine) * scale * 0.5
            half_z = (width * sine + depth * cosine) * scale * 0.5
            x, _offset, game_z = mount["position"]
            assert -200.0 <= x - half_x and x + half_x <= 200.0
            assert -48.0 <= game_z - half_z and game_z + half_z <= 48.0
            if mount["id"] in zones:
                zone = zones[mount["id"]]
                assert zone["minX"] <= x - half_x and x + half_x <= zone["maxX"]
                assert zone["minZ"] <= game_z - half_z and game_z + half_z <= zone["maxZ"]
            if mount["id"] in {"convoy-lead-hauler-start", "east-railhead"}:
                assert abs(game_z) <= 0.001
            points = [
                (x - half_x, game_z - half_z), (x + half_x, game_z - half_z),
                (x + half_x, game_z + half_z), (x - half_x, game_z + half_z),
                (x - half_x, game_z - half_z),
            ]
            # Clearance truth must remain visible above the mounted bodies in
            # the orthographic proof. The X/Y footprint is exact; only this
            # evidence-only Z lift clears the tallest 9.8 m station.
            long_road_curve(f"LongRoadClearance.Landmark.{index}", points, "landmarks", 12.0, 0.42)
            long_road_curve(
                f"LongRoadClearance.LandmarkCrossA.{index}",
                [(x - half_x, game_z - half_z), (x + half_x, game_z + half_z)],
                "landmarks", 12.02, 0.30,
            )
            long_road_curve(
                f"LongRoadClearance.LandmarkCrossB.{index}",
                [(x + half_x, game_z - half_z), (x - half_x, game_z + half_z)],
                "landmarks", 12.02, 0.30,
            )
        clearance = claim.add_camera("long-road.LandmarkClearanceCamera", (0.0, 0.0, 460.0), (0.0, 0.0, 0.0), 52.0)
        clearance.data.clip_end = 720.0
        bpy.context.scene.view_settings.exposure = 1.58
        claim.render(clearance, ARTIFACTS / "long-road-landmarks-clearance-map.png")
    if key == "incline":
        truth = terrain_contract["maskTruth"]
        materials = {
            "pads": claim.make_render_material("InclineClearance.BuildPads", (0.95, 0.58, 0.08)),
            "water": claim.make_render_material("InclineClearance.WaterBand", (0.06, 0.72, 0.66)),
            "rails": claim.make_render_material("InclineClearance.Rails", (0.88, 0.10, 0.055)),
            "stakes": claim.make_render_material("InclineClearance.Stakes", (0.95, 0.34, 0.06)),
            "harvest": claim.make_render_material("InclineClearance.Harvest", (0.32, 0.82, 0.24)),
            "landmarks": claim.make_render_material("InclineClearance.Landmarks", (0.92, 0.86, 0.62)),
        }

        def incline_outline(name, bounds, role, lift=0.82):
            x0, x1, z0, z1 = bounds
            points = [(x0, z0), (x1, z0), (x1, z1), (x0, z1), (x0, z0)]
            claim.add_curve(name, [(x, z, terrain_height(terrain, x, z) + lift) for x, z in points], 0.20, materials[role])

        for zone in truth["buildZones"]:
            incline_outline(f"InclineClearance.{zone['id']}", (zone["minX"], zone["maxX"], zone["minZ"], zone["maxZ"]), "pads")
        incline_outline("InclineClearance.WaterBand", (-48.0, 48.0, -6.25, 6.25), "water", 0.96)
        for index, rail in enumerate(truth["rails"]):
            claim.add_curve(
                f"InclineClearance.Rail.{index}",
                [(point["x"], point["z"], terrain_height(terrain, point["x"], point["z"]) + 1.04) for point in rail["points"]],
                0.26,
                materials["rails"],
            )
        for role, points, radius in (
            ("stakes", ((item["x"], item["z"]) for item in truth["stakeMarkers"]), 3.0),
            ("harvest", ((item["x"], item["z"]) for item in truth["harvestAnchors"]), 1.8),
        ):
            for index, (x, game_z) in enumerate(points):
                ring = []
                for step in range(17):
                    angle = math.tau * step / 16.0
                    px, pz = x + math.cos(angle) * radius, game_z + math.sin(angle) * radius
                    ring.append((px, pz, terrain_height(terrain, px, pz) + 1.08))
                claim.add_curve(f"InclineClearance.{role}.{index}", ring, 0.18, materials[role])
        pack_contract = json.loads(
            (LANDMARKS / key / f"{key}-landmark-pack-contract.json").read_text(encoding="utf-8")
        )
        footprint = {
            identifier: (
                record["bounds"]["max"][0] - record["bounds"]["min"][0],
                record["bounds"]["max"][1] - record["bounds"]["min"][1],
            )
            for identifier, record in pack_contract["assets"].items()
        }
        for index, mount in enumerate(evidence_mounts):
            x, _offset, game_z = mount["position"]
            width, depth = footprint[mount["id"]]
            scale = mount["scale"][0]
            yaw = abs(mount["rotation"][1])
            half_w = (width * math.cos(yaw) + depth * math.sin(yaw)) * scale * 0.5
            half_d = (width * math.sin(yaw) + depth * math.cos(yaw)) * scale * 0.5
            incline_outline(f"InclineClearance.Landmark.{index}", (x - half_w, x + half_w, game_z - half_d, game_z + half_d), "landmarks", 1.24)
        clearance = claim.add_camera("incline.LandmarkClearanceCamera", (0.0, 0.0, 112.0), (0.0, 0.0, 0.0), 52.0)
        clearance.data.clip_end = 430.0
        claim.render(clearance, ARTIFACTS / "incline-landmarks-clearance-overlay.png")
    if key == "relay-valley":
        truth = terrain_contract["maskTruth"]
        materials = {
            "pads": claim.make_render_material("RelayClearance.BuildPads", (0.95, 0.58, 0.08)),
            "gap": claim.make_render_material("RelayClearance.DeadGap", (0.88, 0.10, 0.055)),
            "patrol": claim.make_render_material("RelayClearance.PatrolLoop", (0.06, 0.72, 0.66)),
            "landmarks": claim.make_render_material("RelayClearance.Landmarks", (0.92, 0.86, 0.62)),
        }

        def outline(name, bounds, role, lift=0.72):
            x0, x1, z0, z1 = bounds
            points = [(x0, z0), (x1, z0), (x1, z1), (x0, z1), (x0, z0)]
            claim.add_curve(
                name,
                [(x, z, terrain_height(terrain, x, z) + lift) for x, z in points],
                0.22, materials[role],
            )

        for zone in truth["buildZones"]:
            outline(
                f"RelayClearance.{zone['id']}",
                (zone["minX"], zone["maxX"], zone["minZ"], zone["maxZ"]),
                "pads",
            )
        gap = next(zone for zone in truth["fogPockets"] if zone["id"] == "ridge-dead-gap")
        outline("RelayClearance.DeadGap", (gap["minX"], gap["maxX"], gap["minZ"], gap["maxZ"]), "gap", 0.96)
        patrol = truth["lanes"]["patrolRoutes"][0]["points"]
        claim.add_curve(
            "RelayClearance.PatrolLoop",
            [(point["x"], point["z"], terrain_height(terrain, point["x"], point["z"]) + 0.74) for point in patrol],
            0.22, materials["patrol"],
        )
        for index, mount in enumerate(evidence_mounts):
            x, _offset, game_z = mount["position"]
            points = []
            for step in range(17):
                angle = math.tau * step / 16.0
                px, pz = x + math.cos(angle) * 4.7, game_z + math.sin(angle) * 4.7
                points.append((px, pz, terrain_height(terrain, px, pz) + 0.82))
            claim.add_curve(f"RelayClearance.Landmark.{index}", points, 0.18, materials["landmarks"])
        clearance = claim.add_camera("relay-valley.LandmarkClearanceCamera", (0.0, 0.0, 160.0), (0.0, 0.0, 0.0), 48.0)
        clearance.data.clip_end = 430.0
        claim.render(clearance, ARTIFACTS / "relay-valley-landmarks-clearance-overlay.png")
    if key == "eclipse":
        truth = terrain_contract["maskTruth"]
        materials = {
            "pads": claim.make_render_material("EclipseClearance.BuildPads", (0.95, 0.58, 0.08)),
            "shadow": claim.make_render_material("EclipseClearance.Shadow", (0.82, 0.12, 0.08)),
            "rails": claim.make_render_material("EclipseClearance.MassDriver", (0.95, 0.38, 0.06)),
            "harvest": claim.make_render_material("EclipseClearance.Harvest", (0.06, 0.70, 0.64)),
            "patrol": claim.make_render_material("EclipseClearance.Patrol", (0.54, 0.32, 0.82)),
            "landmarks": claim.make_render_material("EclipseClearance.Landmarks", (0.92, 0.86, 0.62)),
        }

        def eclipse_outline(name, bounds, role, lift=0.82):
            x0, x1, z0, z1 = bounds
            points = [(x0, z0), (x1, z0), (x1, z1), (x0, z1), (x0, z0)]
            claim.add_curve(name, [(x, z, terrain_height(terrain, x, z) + lift) for x, z in points], 0.20, materials[role])

        for zone in truth["buildZones"]:
            eclipse_outline(f"EclipseClearance.{zone['id']}", (zone["minX"], zone["maxX"], zone["minZ"], zone["maxZ"]), "pads")
        shadow = truth["eclipseShadowZones"][0]
        eclipse_outline("EclipseClearance.Shadow", (shadow["minX"], shadow["maxX"], shadow["minZ"], shadow["maxZ"]), "shadow", 1.08)
        for index, rail in enumerate(truth["rails"]):
            claim.add_curve(
                f"EclipseClearance.Rail.{index}",
                [(point["x"], point["z"], terrain_height(terrain, point["x"], point["z"]) + 1.18) for point in rail["points"]],
                0.28, materials["rails"],
            )
        for index, anchor in enumerate(truth["harvestAnchors"]):
            points = []
            for step in range(17):
                angle = math.tau * step / 16.0
                px, pz = anchor["x"] + math.cos(angle) * 2.0, anchor["z"] + math.sin(angle) * 2.0
                points.append((px, pz, terrain_height(terrain, px, pz) + 1.22))
            claim.add_curve(f"EclipseClearance.Harvest.{index}", points, 0.16, materials["harvest"])
        patrol = truth["lanes"]["patrolRoutes"][0]["points"]
        claim.add_curve(
            "EclipseClearance.Patrol",
            [(point["x"], point["z"], terrain_height(terrain, point["x"], point["z"]) + 1.20) for point in patrol],
            0.20, materials["patrol"],
        )
        pack_contract = json.loads((LANDMARKS / key / f"{key}-landmark-pack-contract.json").read_text(encoding="utf-8"))
        for index, mount in enumerate(evidence_mounts):
            record = pack_contract["assets"][mount["id"]]
            width = record["bounds"]["max"][0] - record["bounds"]["min"][0]
            depth = record["bounds"]["max"][1] - record["bounds"]["min"][1]
            x, _offset, game_z = mount["position"]
            eclipse_outline(f"EclipseClearance.Landmark.{index}", (x - width * 0.5, x + width * 0.5, game_z - depth * 0.5, game_z + depth * 0.5), "landmarks", 1.32)
        clearance = claim.add_camera("eclipse.LandmarkClearanceCamera", (0.0, 0.0, 160.0), (0.0, 0.0, 0.0), 48.0)
        clearance.data.clip_end = 430.0
        claim.render(clearance, ARTIFACTS / "eclipse-landmarks-clearance-overlay.png")
    if key == "mare-claim":
        truth = terrain_contract["maskTruth"]
        materials = {
            "pads": claim.make_render_material("MareClearance.BuildPads", (0.95, 0.58, 0.08)),
            "tube": claim.make_render_material("MareClearance.Tube", (0.82, 0.12, 0.08)),
            "arc": claim.make_render_material("MareClearance.DebrisArc", (0.95, 0.38, 0.06)),
            "harvest": claim.make_render_material("MareClearance.Harvest", (0.06, 0.70, 0.64)),
            "landmarks": claim.make_render_material("MareClearance.Landmarks", (0.92, 0.86, 0.62)),
        }

        def outline(name, bounds, role, lift=0.72):
            x0, x1, z0, z1 = bounds
            points = [(x0, z0), (x1, z0), (x1, z1), (x0, z1), (x0, z0)]
            claim.add_curve(name, [(x, z, terrain_height(terrain, x, z) + lift) for x, z in points], 0.22, materials[role])

        for zone in truth["buildZones"]:
            outline(f"MareClearance.{zone['id']}", (zone["minX"], zone["maxX"], zone["minZ"], zone["maxZ"]), "pads")
        tube = truth.get("lavaTubeMouth")
        if tube:
            outline(f"MareClearance.{tube['id']}", (tube["minX"], tube["maxX"], tube["minZ"], tube["maxZ"]), "tube", 0.92)
        for arc in truth.get("debrisArcLanes", []):
            claim.add_curve(
                f"MareClearance.{arc['id']}",
                [(point["x"], point["z"], terrain_height(terrain, point["x"], point["z"]) + 0.84) for point in arc["points"]],
                0.22,
                materials["arc"],
            )
        for index, anchor in enumerate(truth.get("harvestAnchors", [])):
            points = []
            for step in range(17):
                angle = math.tau * step / 16.0
                px, pz = anchor["x"] + math.cos(angle) * 2.0, anchor["z"] + math.sin(angle) * 2.0
                points.append((px, pz, terrain_height(terrain, px, pz) + 0.82))
            claim.add_curve(f"MareClearance.Harvest.{index}", points, 0.16, materials["harvest"])
        footprint = {
            "earthrise-listening-array": (8.2, 3.8),
            "lava-tube-survey-gantry": (6.2, 4.7),
            "regolith-core-yard": (6.4, 4.6),
            "west-rim-debris-catcher": (5.1, 4.2),
            "east-rim-debris-catcher": (5.1, 4.2),
        }
        for index, mount in enumerate(evidence_mounts):
            x, _offset, game_z = mount["position"]
            width, depth = footprint[mount["id"]]
            scale = mount["scale"][0]
            outline(
                f"MareClearance.Landmark.{index}",
                (x - width * scale * 0.5, x + width * scale * 0.5, game_z - depth * scale * 0.5, game_z + depth * scale * 0.5),
                "landmarks",
                1.04,
            )
        clearance = claim.add_camera("mare-claim.LandmarkClearanceCamera", (0.0, 0.0, 160.0), (0.0, 0.0, 0.0), 48.0)
        clearance.data.clip_end = 430.0
        claim.render(clearance, ARTIFACTS / "mare-claim-landmarks-clearance-overlay.png")
    if key == "devils-alley":
        truth = terrain_contract["maskTruth"]
        materials = {
            "pads": claim.make_render_material("DevilsClearance.BuildPads", (0.95, 0.58, 0.08)),
            "corridors": claim.make_render_material("DevilsClearance.SweepCorridors", (0.88, 0.10, 0.055)),
            "anchors": claim.make_render_material("DevilsClearance.AnchorSites", (0.06, 0.72, 0.66)),
            "landmarks": claim.make_render_material("DevilsClearance.Landmarks", (0.92, 0.86, 0.62)),
        }

        def outline(name, bounds, role, lift=0.82):
            x0, x1, z0, z1 = bounds
            points = [(x0, z0), (x1, z0), (x1, z1), (x0, z1), (x0, z0)]
            claim.add_curve(name, [(x, z, terrain_height(terrain, x, z) + lift) for x, z in points], 0.22, materials[role])

        for zone in truth["buildZones"]:
            outline(f"DevilsClearance.{zone['id']}", (zone["minX"], zone["maxX"], zone["minZ"], zone["maxZ"]), "pads")
        for zone in truth["dustDevilCorridors"]:
            outline(f"DevilsClearance.{zone['id']}", (zone["minX"], zone["maxX"], zone["minZ"], zone["maxZ"]), "corridors", 1.04)
        for zone in truth["anchorSites"]:
            outline(f"DevilsClearance.Anchor.{zone['id']}", (zone["minX"], zone["maxX"], zone["minZ"], zone["maxZ"]), "anchors", 1.20)
        footprint = {
            "south-anchor-gate": (10.0, 3.4), "west-wind-anchor": (5.6, 4.6),
            "center-wind-anchor": (6.0, 4.6), "east-wind-anchor": (6.4, 4.6),
            "north-anchor-gate": (11.0, 3.4),
        }
        for index, mount in enumerate(evidence_mounts):
            x, _offset, game_z = mount["position"]
            width, depth = footprint[mount["id"]]
            outline(f"DevilsClearance.Landmark.{index}", (x - width * 0.5, x + width * 0.5, game_z - depth * 0.5, game_z + depth * 0.5), "landmarks", 1.30)
        clearance = claim.add_camera("devils-alley.LandmarkClearanceCamera", (0.0, 0.0, 160.0), (0.0, 0.0, 0.0), 48.0)
        clearance.data.clip_end = 440.0
        claim.render(clearance, ARTIFACTS / "devils-alley-landmarks-clearance-overlay.png")
    if key == "archive-world":
        bpy.context.scene.view_settings.exposure = 2.12
        truth = terrain_contract["maskTruth"]
        materials = {
            "pads": claim.make_render_material("ArchiveClearance.BuildPads", (0.95, 0.58, 0.08)),
            "wings": claim.make_render_material("ArchiveClearance.Wings", (0.06, 0.72, 0.66)),
            "empty": claim.make_render_material("ArchiveClearance.EmptyShelf", (0.82, 0.12, 0.08)),
            "lights": claim.make_render_material("ArchiveClearance.LightHolds", (0.92, 0.72, 0.26)),
            "landmarks": claim.make_render_material("ArchiveClearance.Landmarks", (0.92, 0.86, 0.62)),
        }

        def outline(name, bounds, role, lift=0.82):
            x0, x1, z0, z1 = bounds
            points = [(x0, z0), (x1, z0), (x1, z1), (x0, z1), (x0, z0)]
            claim.add_curve(name, [(x, z, terrain_height(terrain, x, z) + lift) for x, z in points], 0.22, materials[role])

        for zone in truth["buildZones"]:
            outline(f"ArchiveClearance.{zone['id']}", (zone["minX"], zone["maxX"], zone["minZ"], zone["maxZ"]), "pads")
        for zone in truth["archiveWingZones"]:
            outline(f"ArchiveClearance.Wing.{zone['id']}", (zone["minX"], zone["maxX"], zone["minZ"], zone["maxZ"]), "wings", 1.04)
        empty = truth["emptyShelfZone"]
        outline("ArchiveClearance.EmptyShelf", (empty["minX"], empty["maxX"], empty["minZ"], empty["maxZ"]), "empty", 1.28)
        for index, site in enumerate(truth["lightHoldSites"]):
            points = []
            for step in range(17):
                angle = math.tau * step / 16.0
                px, pz = site["x"] + math.cos(angle) * site["radius"], site["z"] + math.sin(angle) * site["radius"]
                points.append((px, pz, terrain_height(terrain, px, pz) + 1.24))
            claim.add_curve(f"ArchiveClearance.Light.{index}", points, 0.18, materials["lights"])
        footprint = {
            "archive-entry-gate": (10.6, 4.8), "west-stack-ruin": (7.4, 5.2),
            "east-stack-ruin": (7.4, 5.2), "warning-shelf-ruin": (8.4, 5.4),
            "ours-unless-marker": (5.8, 3.8),
        }
        for index, mount in enumerate(evidence_mounts):
            x, _offset, game_z = mount["position"]
            width, depth = footprint[mount["id"]]
            scale = mount["scale"][0]
            outline(f"ArchiveClearance.Landmark.{index}", (x - width * scale * 0.5, x + width * scale * 0.5, game_z - depth * scale * 0.5, game_z + depth * scale * 0.5), "landmarks", 1.34)
        clearance = claim.add_camera("archive-world.LandmarkClearanceCamera", (0.0, 0.0, 160.0), (0.0, 0.0, 0.0), 48.0)
        clearance.data.clip_end = 440.0
        claim.render(clearance, ARTIFACTS / "archive-world-landmarks-clearance-overlay.png")


def render_lineup(key, profile, asset_records):
    claim.reset_scene()
    ground = claim.make_render_material(f"{key}.LineupGround", (0.17, 0.095, 0.035))
    regatta = key == "regatta"
    boneyard = key == "boneyard"
    long_road = key == "long-road"
    turntable = key in {"regatta", "incline", "boneyard", "long-road", "relay-valley", "mare-claim", "eclipse", "devils-alley", "archive-world"}
    add_box("LineupGround", (0, 0, -0.25), ((34 if long_road else 31 if boneyard else 30 if regatta else 31 if key in {"incline", "mare-claim", "eclipse", "devils-alley", "archive-world"} else 24), 26 if boneyard else 20 if long_road else 18, 0.25), "earth").data.materials.append(ground)
    identifiers = list(asset_records)
    objects = []
    for index, identifier in enumerate(identifiers):
        obj = import_asset(OUT / asset_records[identifier]["asset"])
        maximum = max(float(value) for value in obj.dimensions)
        display_scale = min(1.0, (6.3 if long_road else 5.0) / max(maximum, 0.001))
        columns = 4 if regatta or boneyard else (5 if key in {"incline", "mare-claim", "eclipse", "devils-alley", "archive-world"} else 3)
        column, row = index % columns, index // columns
        obj.scale = (display_scale,) * 3
        spacing = 7.8 if long_road else 6.2 if regatta else (5.2 if key == "incline" else 5.7)
        obj.location = ((column - (columns - 1) * 0.5) * spacing, (row - (1.0 if boneyard else 0.5)) * 6.2, 0.0)
        obj.rotation_euler.z = -0.25 + index * 0.12
        objects.append(obj)
    camera_y = -31.0 if boneyard else -28.0 if regatta else -25.0 if long_road else (-22.0 if key == "incline" else -20.0)
    camera = claim.add_camera(f"{key}.LandmarkPackCamera", (0.0, camera_y, 19.0 if boneyard else 17.0 if regatta else 16.5 if long_road else 14.0), (0.0, 0.0, 2.5 if long_road else 2.3), 41.0 if long_road else 40.0 if boneyard else 38.0)
    lights = claim.add_lighting(sunset=False)
    bpy.context.scene.view_settings.exposure = 1.05 if regatta else (1.0 if key == "incline" else 1.10 if key == "relay-valley" else 1.10 if key == "eclipse" else 1.12 if key == "mare-claim" else 1.18 if key == "devils-alley" else 1.30 if key == "archive-world" else 0.82)
    if key == "relay-valley":
        lights[0].data.energy = 3.0
        for name, location, energy, color in (
            ("RelayLineupFront", (0.0, -14.0, 22.0), 2700.0, (0.50, 0.68, 0.60)),
            ("RelayLineupRear", (0.0, 14.0, 16.0), 1700.0, (0.78, 0.50, 0.24)),
        ):
            data = bpy.data.lights.new(name, "AREA")
            data.energy = energy
            data.color = color
            data.shape = "DISK"
            data.size = 14.0
            lamp = bpy.data.objects.new(name, data)
            bpy.context.collection.objects.link(lamp)
            lamp.location = location
            claim.aim_at(lamp, (0.0, 0.0, 2.7))
    if key in {"mare-claim", "eclipse"}:
        lights[0].data.energy = 2.8
        lights[0].data.color = (0.62, 0.70, 0.68)
    if key == "devils-alley":
        lights[0].data.energy = 3.2
        lights[0].data.color = (0.76, 0.48, 0.26)
    if key == "archive-world":
        lights[0].data.energy = 3.0
        lights[0].data.color = (0.62, 0.68, 0.58)
    if key == "boneyard":
        lights[0].data.energy = 3.1
        lights[0].data.color = (1.0, 0.78, 0.50)
        bpy.context.scene.view_settings.exposure = 1.08
    if key == "long-road":
        lights[0].data.energy = 3.25
        lights[0].data.color = (1.0, 0.77, 0.48)
        bpy.context.scene.view_settings.exposure = 1.12
    claim.render(camera, ARTIFACTS / f"{key}-landmarks-pack.png")
    if turntable:
        original_rotations = [obj.rotation_euler.z for obj in objects]
        for index, angle in enumerate((0.0, math.pi * 0.5, math.pi, math.pi * 1.5), 1):
            for obj, original in zip(objects, original_rotations):
                obj.rotation_euler.z = original + angle
            claim.render(camera, ARTIFACTS / f"{key}-landmarks-angle-{index}.png")


def build_pack(key):
    profile = PACKS[key]
    contract_path = OUT / profile["contract"]
    terrain_contract = json.loads(contract_path.read_text(encoding="utf-8"))
    mount_agnostic = not terrain_contract["landmarkMounts"] and bool(profile.get("bodies"))
    original_mounts = json.loads(json.dumps(terrain_contract["landmarkMounts"]))
    original_mounts_by_id = {mount["id"]: mount for mount in original_mounts}
    owned_mounts = terrain_contract["landmarkMounts"]
    if key == "mare-claim":
        supplemental = json.loads((LANDMARKS / "mare-dome/mare-dome-landmark-pack-contract.json").read_text())["mounts"]
        assert all(mount in owned_mounts for mount in supplemental)
        owned_mounts = [mount for mount in owned_mounts if mount not in supplemental]
    mounts = {mount["id"]: mount for mount in owned_mounts}
    for mount in mounts.values():
        previous_offset = float(mount.pop("terrainConformOffsetY", 0.0))
        mount["position"][1] = round(float(mount["position"][1]) - previous_offset, 6)
    identifiers = profile["bodies"] if mount_agnostic else list(mounts)
    missing_specs = sorted(set(identifiers) - set(SPECS))
    if missing_specs:
        raise ValueError(f"missing landmark source specs for {key}: {missing_specs}")
    claim.reset_scene()
    image, atlas_path = make_atlas(key, profile)
    material = make_material(key, image)
    terrain = import_asset(OUT / profile["terrain"])
    terrain.hide_set(True)
    terrain.hide_render = True
    assets = {}
    for identifier in identifiers:
        source_spec = SPECS[identifier]
        parts = build_parts(identifier, source_spec)
        if source_spec.get("conform"):
            locked_offset = (
                original_mounts_by_id[identifier].get("terrainConformOffsetY")
                if key in {"hill-mine", "trestle"}
                else None
            )
            offset_y = conform_parts_to_terrain(parts, terrain, mounts[identifier], locked_offset)
            mounts[identifier]["position"][1] = round(mounts[identifier]["position"][1] + offset_y, 6)
            mounts[identifier]["terrainConformOffsetY"] = round(offset_y, 6)
        asset = finish_asset(parts, identifier, material, key, source_spec)
        assets[identifier] = asset
    terrain_mesh = terrain.data
    bpy.data.objects.remove(terrain, do_unlink=True)
    if terrain_mesh.users == 0:
        bpy.data.meshes.remove(terrain_mesh)
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    directory = LANDMARKS / key
    blend_path = directory / f"{key}-landmarks.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    records = {}
    for identifier, asset in assets.items():
        glb_path = directory / f"{identifier}.glb"
        export_asset(asset, glb_path)
        triangles = sum(len(poly.vertices) - 2 for poly in asset.data.polygons)
        records[identifier] = {
            "asset": str(glb_path.relative_to(OUT)),
            "sourceTier": SPECS[identifier]["tier"],
            "sources": SPECS[identifier]["sources"],
            "terrainConformed": bool(SPECS[identifier].get("conform")),
            "triangles": triangles,
            "triangleBudget": 3000,
            "bounds": glb_bounds(asset),
            "sha256": sha256(glb_path),
        }
        if identifier == "seven_lantern_terraces":
            records[identifier]["authoredFixturePositions"] = NIGHT_LANTERN_FIXTURES
    for mount in owned_mounts:
        mount["asset"] = records[mount["id"]]["asset"]
    if key in {"hill-mine", "trestle"}:
        # This quality pass is a file replacement only. The registry already
        # mounts these ids in-game, so their transforms remain byte-for-byte
        # identical to the pulled-main contract.
        terrain_contract["landmarkMounts"] = original_mounts
    if not mount_agnostic:
        terrain_contract["landmarkPack"] = {
            "contract": f"landmarks/{key}/{key}-landmark-pack-contract.json",
            "atlas": str(atlas_path.relative_to(OUT)),
            "era": profile["era"],
            "sourceLadder": "reuse > derive > build-new",
            "ownership": "separate mounted render-only GLBs; no simulation authority",
        }
        contract_path.write_text(json.dumps(terrain_contract, indent=2) + "\n", encoding="utf-8")
    # Pin the reviewed main ancestor, not the pack branch's own commit.
    reference_base = subprocess.check_output(
        ["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True
    ).strip()
    pack_contract = {
        "map": key,
        "era": profile["era"],
        "referenceBase": reference_base,
        "sourceLadder": ["reuse", "derive", "build-new"],
        "atlas": {
            "asset": str(atlas_path.relative_to(OUT)), "width": ATLAS_SIZE, "height": ATLAS_SIZE,
            "sharedByEveryAsset": True, "sha256": sha256(atlas_path),
        },
        "blend": {"asset": str(blend_path.relative_to(OUT)), "sha256": sha256(blend_path)},
        "assets": records,
        "mounts": terrain_contract["landmarkMounts"],
        "simulation": "none; terrain, collision, movement, placement, water, spawns, and fog remain unchanged",
    }
    if mount_agnostic:
        pack_contract["mountInterlock"] = "pending-3d-d"
        pack_contract["proposedIds"] = identifiers
    pack_contract_path = directory / f"{key}-landmark-pack-contract.json"
    pack_contract_path.write_text(json.dumps(pack_contract, indent=2) + "\n", encoding="utf-8")
    if mount_agnostic:
        evidence_profile = {
            **profile,
            "previewMounts": [
                {**mount, "asset": records[mount["id"]]["asset"]} for mount in profile["previewMounts"]
            ],
        }
        render_mounted(key, evidence_profile, terrain_contract)
    else:
        render_mounted(key, profile, terrain_contract)
    render_lineup(key, profile, records)
    return pack_contract


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--atlas-only" in args:
        import argparse
        parser = argparse.ArgumentParser(description="Reproduce current E3 atlases without rebuilding geometry or mount tables.")
        parser.add_argument("--atlas-only", choices=sorted(E3_ATLAS_RECIPES), required=True)
        parser.add_argument("--out", type=Path, required=True, help="Separate output root; each pack gets its own subdirectory.")
        options = parser.parse_args(args)
        destination = options.out.resolve()
        if destination == LANDMARKS.resolve() or LANDMARKS.resolve() in destination.parents:
            raise ValueError("Use a separate output root: replacing a shipped atlas also requires re-exporting its GLBs and updating hashes.")
        _, path = make_atlas(options.atlas_only, E3_ATLAS_RECIPES[options.atlas_only], output_root=destination)
        print(json.dumps({"pack": options.atlas_only, "atlas": str(path), "sha256": sha256(path)}, indent=2))
        return
    keys = args or list(PACKS)
    if any(key in E3_ATLAS_RECIPES for key in keys):
        raise ValueError("Use --atlas-only <E3-pack> --out <destination> for current atlas recipes; retain the reviewed .blend geometry and pack-specific repair scripts.")
    if "archive-world" in keys:
        raise ValueError("Use build_archive_landmarks.py --out <destination> for the reviewed Archive geometry, native atlas and planar UVs.")
    if "showroom" in keys:
        raise ValueError("Use build_showroom_landmarks.py --out <destination> for the furnished Showroom geometry, native atlas and walk surfaces.")
    if any(key in {"the-claim", "dry-gulch", "night-shift", "twin-banks", "baron"} for key in keys):
        raise ValueError(
            "This recipe predates the owner's E1 replacement verdict. Author from each body's "
            ".blend, or reproduce the accepted sources with scripts/rebuild-accepted-e1-landmarks.py. "
            "Select only later packs when using this builder."
        )
    ledger_path = LANDMARKS / "landmark-source-ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {
        "law": "reuse > derive > build-new; era-stamped; grit-dressed",
        "packs": {},
    }
    # Other builders also author packs. Refresh the shared ledger from every
    # shipped contract, not just the recipes this builder happens to know.
    for contract_path in sorted(LANDMARKS.glob("*/*-landmark-pack-contract.json")):
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        pack_key = contract["map"]
        ledger["packs"][pack_key] = {
            identifier: {
                "sourceTier": record["sourceTier"],
                "sources": record["sources"],
                "asset": record["asset"],
            }
            for identifier, record in contract["assets"].items()
        }
    results = {key: build_pack(key) for key in keys}
    for key, result in results.items():
        ledger["packs"][key] = {
            identifier: {"sourceTier": record["sourceTier"], "sources": record["sources"], "asset": record["asset"]}
            for identifier, record in result["assets"].items()
        }
    ledger["packs"] = {key: ledger["packs"][key] for key in sorted(ledger["packs"])}
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"packs": list(results), "assets": sum(len(result["assets"]) for result in results.values())}, indent=2))


if __name__ == "__main__":
    main()
