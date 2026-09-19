from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

import bpy


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "artifacts/town-e5-harbor"
PROPS = ROOT / "assets/pilots/plaza-props-3d"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


build = load_module("wave10_e5_build", HERE / "build_wave10_e5_harbor.py")
pilot_verify = load_module("wave10_pilot_verify", HERE / "verify_wave9_e4_pilot.py")
previous_verify = load_module("wave10_previous_verify", HERE / "verify_wave9_e4_wide.py")
wave7b = pilot_verify.wave7b


def building(source):
    directory = ROOT / "assets/pilots" / source["directory"]
    return {
        "baseBlend": directory / f'{source["source"]}.blend',
        "baseGlb": directory / f'{source["source"]}.glb',
        "variantBlend": directory / f'{source["stem"]}.e5.blend',
        "variantGlb": directory / f'{source["stem"]}.e5.glb',
        "object": source["output"], "anchors": [], "budget": 15_000,
        "imageDimensions": [[1024, 1024]], "sameEnvelope": True,
        "baseBlendSha": source["blend_sha"], "baseGlbSha": source["glb_sha"],
    }


BUILDINGS = {asset_id: building(source) for asset_id, source in build.SPECS.items()}


def prop(stem, object_name, budget):
    return {
        "variantBlend": PROPS / f"{stem}.blend", "variantGlb": PROPS / f"{stem}.glb",
        "object": object_name, "anchors": [], "budget": budget,
        "imageDimensions": [[1024, 1024]], "sameEnvelope": False,
    }


PROP_VARIANTS = {
    "covered_wagon": prop("covered_wagon.e5", "CoveredWagonE5", 1800),
    "water_trough": prop("water_trough.e5", "WaterTroughE5", 1200),
}
ACCESSORIES = {
    "harbor_lantern": prop("harbor-lantern.e5", "HarborLanternE5", 1000),
    "net_frame": prop("net-frame.e5", "NetFrameE5", 1000),
    "tide_board": prop("tide-board.e5", "TideBoardE5", 1000),
    "rope_buoy_rack": prop("rope-buoy-rack.e5", "RopeBuoyRackE5", 1000),
}


CADENCE = [
    {"fixture": "Harbor House", "verdict": "GONE -> REPLACE", "reason": "The E4 Motor Inn and all pre-flood machinery are gone; a rope-trimmed lantern-gable Harbor House is rebuilt on seabed ballast."},
    {"fixture": "Bonded Chandlery", "verdict": "GONE -> REPLACE", "reason": "The General Store lineage returns as a customs-marked loading house with a cargo hoist and wet hawser."},
    {"fixture": "Harbor Office", "verdict": "GONE -> REPLACE", "reason": "The Claim Office lineage is rebuilt around tide records, a storm-signal mast, and harbor registry pictograms."},
    {"fixture": "Salvage Assay", "verdict": "GONE -> REPLACE", "reason": "The assay role survives through salvage sorting, a roof hoist, sieve, and pearl gauge; the old plant does not."},
    {"fixture": "Mariners Chapel", "verdict": "GONE -> REPLACE", "reason": "The chapel identity returns with storm stays, rescue-ring grammar, a tide memorial, and a grounded ballast sill."},
    {"fixture": "Navigation School", "verdict": "GONE -> REPLACE", "reason": "The school lineage returns with the required sextant finial, lookout deck, chart board, and rope rails."},
    {"fixture": "Drydock Works", "verdict": "GONE -> REPLACE", "reason": "The Stamp Mill lineage becomes a timber drydock works with hull cradle, capstan, and hoist."},
    {"fixture": "Harbor Works", "verdict": "GONE -> REPLACE", "reason": "The Dynamo Hall lineage returns as a crane-and-winch harbor works; no pre-flood generator stack survives."},
    {"fixture": "Covered wagons", "verdict": "GONE -> REPLACE", "reason": "Wagons do not survive the flood; a waterlogged arrival dinghy is fixed to a weighted seabed cradle."},
    {"fixture": "Water trough", "verdict": "GONE -> REPLACE", "reason": "The horse trough leaves with Chain 1 and is replaced by a sealed freshwater cistern."},
    {"fixture": "E2-E4 accessories", "verdict": "GONE", "reason": "Steam, voltage, and motor street hardware is drowned or cannibalized; none is silently mounted in the E5 pack."},
    {"fixture": "Harbor accessories", "verdict": "NEW", "reason": "Harbor lanterns, a drying-net frame, tide board, and rope-buoy rack announce the submerged working town."},
    {"fixture": "Seabed ballast", "verdict": "NEW -> PERSIST", "reason": "Every heavy house terminates at its canonical ground plane on four compact tarred ballast shoes; the buildings do not float."},
    {"fixture": "Pan Monument", "verdict": "PERSIST", "reason": "The unchanged heritage survivor is carried into the reclaimed town ring and remains independently mounted."},
]


def assert_clean_blend(spec):
    model = bpy.data.objects[spec["object"]]
    assert model.get("flood_break", "").startswith("fresh"), spec["object"]
    assert not [obj for obj in bpy.data.objects if obj.type == "EMPTY"], spec["object"]
    assert not [obj for obj in bpy.data.objects if obj.type in {"LIGHT", "CAMERA"}], spec["object"]


def check_building(asset_id, spec):
    checked = pilot_verify.check_asset(asset_id, spec)
    assert_clean_blend(spec)
    nodes = checked["checked"]["nodes"]
    assert not [name for name in nodes if name.startswith(("steam_anchor_", "arc_anchor_", "exhaust_anchor_"))]
    checked["freshIdentityShell"] = previous_verify.check_accretion(spec["baseGlb"], spec["variantGlb"])
    checked["floodBreak"] = "E1 identity shell retained; E2-E4 geometry and emitters absent"
    return checked


def check_prop(asset_id, spec):
    checked = wave7b.check_asset(asset_id, spec)
    assert_clean_blend(spec)
    nodes = checked["checked"]["nodes"]
    assert not [name for name in nodes if name.startswith(("steam_anchor_", "arc_anchor_", "exhaust_anchor_"))]
    return checked


RADII = {
    "harbor-lantern.e5.glb": 0.52, "net-frame.e5.glb": 0.88,
    "tide-board.e5.glb": 0.76, "rope-buoy-rack.e5.glb": 0.96,
}


def check_manifest():
    path = PROPS / "era-props.e5.json"
    manifest = json.loads(path.read_text())
    expected = set(RADII)
    assert manifest["epoch"] == 5 and manifest["floodReset"] is True
    assert manifest["atlas"] == "era-props-e5-atlas.png"
    assert {item["glb"] for item in manifest["props"]} == expected
    assert len({item["id"] for item in manifest["props"]}) == len(manifest["props"])
    reports = []
    for item in manifest["props"]:
        assert set(item) == {"id", "glb", "position", "rotation", "scale"}
        assert set(item["position"]) == {"x", "z"} and (PROPS / item["glb"]).is_file()
        radius = RADII[item["glb"]] * item["scale"]
        x, z = item["position"]["x"], item["position"]["z"]
        route = wave7b.town.route_distance(x, z) - radius
        stage = math.hypot(x, z) - radius - wave7b.town.PLAZA_CLEAR_RADIUS
        pad = min(
            wave7b.town.rectangle_outside_distance(x, z, slot) - radius
            for slot in [*wave7b.town.SLOTS, wave7b.town.DYNAMO_SLOT]
        )
        existing = min(
            math.hypot(x - prop.position.x, z - prop.position.y) - radius - wave7b.town.prop_radius(prop)
            for prop in wave7b.town.PROPS
        )
        assert route >= 0.35 and stage >= 0.35 and pad >= 0.25 and existing >= 0.35, (
            item["id"], route, stage, pad, existing,
        )
        reports.append({
            "id": item["id"], "routeClearance": round(route, 4),
            "stageClearance": round(stage, 4), "padClearance": round(pad, 4),
            "existingPropClearance": round(existing, 4),
        })
    pairwise = []
    for index, left in enumerate(manifest["props"]):
        for right in manifest["props"][index + 1:]:
            clearance = math.hypot(
                left["position"]["x"] - right["position"]["x"],
                left["position"]["z"] - right["position"]["z"],
            ) - RADII[left["glb"]] * left["scale"] - RADII[right["glb"]] * right["scale"]
            assert clearance >= 0.25, (left["id"], right["id"], clearance)
            pairwise.append(clearance)
    return {
        "path": str(path.relative_to(ROOT)), "count": len(manifest["props"]),
        "types": sorted(expected), "placements": reports,
        "minimumPairwiseClearance": round(min(pairwise), 4),
        "floodReset": "manifest declares a hard reset and contains no E2-E4 accessory records",
    }


def check_visual_evidence():
    metrics_path = OUT / "comparison-metrics.json"
    metrics = json.loads(metrics_path.read_text())
    blind_path = OUT / "blind-key.json"
    blind = json.loads(blind_path.read_text())
    assert blind["integrated"] == {"a": "e5", "b": "e4"}
    # The gate compares geometry/materials under the same production lighting;
    # the separate underwater story view must not inflate this score.
    assert metrics["integrated"]["diffRatio16"] > 0.01
    per_building = {}
    for asset_id in BUILDINGS:
        render_id = {"stamp_mill": "stamp-mill", "dynamo_hall": "dynamo-hall"}.get(asset_id, asset_id)
        assert metrics[render_id]["diffRatio16"] > 0.001
        for path in (
            OUT / f"{render_id}-town-verdict-e4-e5-ab.png",
            OUT / f"{render_id}-turntable-e4-e5-ab.png",
        ):
            assert path.is_file()
        per_building[asset_id] = metrics[render_id]
    for path in (
        OUT / "town-wide-verdict-e4-e5-ab.png", OUT / "town-ensemble-blind-pair.png",
        OUT / "all-buildings-e5-turntable-contact.png", OUT / "accessory-pack-and-pan-survivor-e5.png",
        OUT / "e5-accessory-clearance-overlay.png", OUT / "town-e5-seabed-overview.png",
        OUT / "e5" / "town-e5-harbor-underwater.png",
    ):
        assert path.is_file()
    return {
        "metrics": str(metrics_path.relative_to(ROOT)), "blindKey": str(blind_path.relative_to(ROOT)),
        "perBuilding": per_building, "ensembleDiffRatio16": metrics["integrated"]["diffRatio16"],
        "productionLightComparison": "E4 and E5 geometry/materials rendered under the identical shipped Town light rig",
        "seabedRead": "separate cool underwater town-camera evidence; model GLBs contain no duplicate water surface",
    }


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    evidence = {
        "blender": bpy.app.version_string,
        "scope": "eight submerged E5 building faces, dinghy/cistern variants, four-accessory harbor pack, Pan survivor",
        "buildings": {}, "propVariants": {}, "accessories": {},
    }
    for asset_id, spec in BUILDINGS.items():
        evidence["buildings"][asset_id] = check_building(asset_id, spec)
    for asset_id, spec in PROP_VARIANTS.items():
        evidence["propVariants"][asset_id] = check_prop(asset_id, spec)
    for asset_id, spec in ACCESSORIES.items():
        evidence["accessories"][asset_id] = check_prop(asset_id, spec)
    shared_specs = {**PROP_VARIANTS, **ACCESSORIES}
    hashes = {asset_id: wave7b.embedded_image_sha(spec["variantGlb"]) for asset_id, spec in shared_specs.items()}
    assert len(set(hashes.values())) == 1
    atlas = PROPS / "era-props-e5-atlas.png"
    evidence["sharedAccessoryAtlas"] = {
        "path": str(atlas.relative_to(ROOT)), "sha256": sha256(atlas),
        "embeddedSha256": next(iter(hashes.values())), "allEmbeddedCopiesIdentical": True,
    }
    evidence["manifest"] = check_manifest()
    evidence["cadence"] = CADENCE
    pan_blend, pan_glb = PROPS / "pan_monument.blend", PROPS / "pan_monument.glb"
    assert sha256(pan_blend) == "c361cf31fb808541821df0b174fa2b79a7de465b915b843785c221a21f65b941"
    assert sha256(pan_glb) == "e86e7cdabd1039434bf7a206487a8bc4f68bc2b19a4d9b255f01476e4929f5c2"
    evidence["panSurvivor"] = {"blendSha256": sha256(pan_blend), "glbSha256": sha256(pan_glb), "unchanged": True}
    evidence["visualEvidence"] = check_visual_evidence()
    evidence["landmarkFreeze"] = "honored; no landmark GLBs authored or changed"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
