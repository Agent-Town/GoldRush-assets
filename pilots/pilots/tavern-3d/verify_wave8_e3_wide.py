from pathlib import Path
import importlib.util
import json
import math
import sys

import bpy


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "artifacts/town-e3-wide"
PROPS = ROOT / "assets/pilots/plaza-props-3d"
E2_MANIFEST = json.loads((PROPS / "era-props.e2.json").read_text())


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


wide = load_module("wave8_wide_build", HERE / "build_wave8_e3_wide.py")
pilot = wide.pilot
wave7b = load_module("wave7b_verify", HERE / "verify_wave7b.py")


def building(spec):
    base = ROOT / "assets/pilots" / spec["directory"]
    return {
        "baseBlend": base / f'{spec["source"]}.blend',
        "baseGlb": base / f'{spec["source"]}.glb',
        "variantBlend": base / f'{spec["stem"]}.e3.blend',
        "variantGlb": base / f'{spec["stem"]}.e3.glb',
        "object": spec["output"], "anchors": ["arc_anchor_1", "arc_anchor_2", "arc_anchor_3"],
        "budget": 15_000, "imageDimensions": [[1024, 1024]], "sameEnvelope": True,
        "baseBlendSha": spec["blend_sha"], "baseGlbSha": spec["glb_sha"],
    }


BUILDINGS = {
    **{key: building(spec) for key, spec in wide.SPECS.items()},
    "schoolhouse": building(pilot.SPECS["schoolhouse"]),
    "stamp_mill": building(pilot.SPECS["stamp_mill"]),
}


def prop_variant(stem, source, object_name, anchors, budget, blend_sha, glb_sha):
    return {
        "baseBlend": PROPS / f"{source}.blend", "baseGlb": PROPS / f"{source}.glb",
        "variantBlend": PROPS / f"{stem}.blend", "variantGlb": PROPS / f"{stem}.glb",
        "object": object_name, "anchors": anchors, "budget": budget,
        "imageDimensions": [[256, 256]], "sameEnvelope": True,
        "baseBlendSha": blend_sha, "baseGlbSha": glb_sha,
    }


PROP_VARIANTS = {
    "covered_wagon": prop_variant(
        "covered_wagon.e3", "covered_wagon.e2", "CoveredWagonE3",
        ["arc_anchor_1"], 1800,
        "178a59a70e47d6349c34f6aeb19d5c300914b0af1d52bd54231086e9e9b9a089",
        "f212d6a2f655ac23a22efe1eca0f48608e58d9a08d63e5a485348431525d7417",
    ),
    "water_trough": prop_variant(
        "water_trough.e3", "water_trough.e2", "WaterTroughE3",
        ["arc_anchor_1", "arc_anchor_2"], 1200,
        "05f53cd0db08110e98f0e9f93af418a2b8345cc049bda9072580680bb0dc8a0c",
        "65622eea7d9967fe3b53cbbddeecc2a0f8ab779803f5ef86010a790bc1f79f17",
    ),
}


def accessory(stem, object_name, anchors):
    return {
        "variantBlend": PROPS / f"{stem}.blend", "variantGlb": PROPS / f"{stem}.glb",
        "object": object_name, "anchors": anchors, "budget": 1000,
        "imageDimensions": [[1024, 1024]], "sameEnvelope": False,
    }


ACCESSORIES = {
    "wire_run": accessory("wire-run.e3", "WireRunE3", ["arc_anchor_1", "arc_anchor_2"]),
    "insulator_post": accessory("insulator-post.e3", "InsulatorPostE3", ["arc_anchor_1", "arc_anchor_2"]),
    "transformer_shed": accessory(
        "transformer-shed.e3", "TransformerShedE3",
        ["arc_anchor_1", "arc_anchor_2", "arc_anchor_3"],
    ),
}


def check_manifest():
    manifest_path = PROPS / "era-props.e3.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["epoch"] == 3 and manifest["atlas"] == "era-props-e3-atlas.png"
    expected = {"wire-run.e3.glb", "insulator-post.e3.glb", "transformer-shed.e3.glb"}
    radii = {"wire-run.e3.glb": 1.20, "insulator-post.e3.glb": 0.50, "transformer-shed.e3.glb": 1.0}
    retained_radii = {
        "coal-bin.e2.glb": 0.65, "pipe-run.e2.glb": 1.05, "gauge-post.e2.glb": 0.42,
        "iron-lamp-post.e2.glb": 0.65, "pressure-manifold.e2.glb": 0.82,
    }
    retained = E2_MANIFEST["props"]
    props = manifest["props"]
    assert {item["glb"] for item in props} == expected
    assert len({item["id"] for item in props}) == len(props)
    reports = []
    for item in props:
        assert set(item) == {"id", "glb", "position", "rotation", "scale"}
        assert set(item["position"]) == {"x", "z"}
        assert (PROPS / item["glb"]).is_file()
        radius = radii[item["glb"]] * item["scale"]
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
        retained_clearance = min(
            math.hypot(x - other["position"]["x"], z - other["position"]["z"])
            - radius - retained_radii[other["glb"]] * other["scale"]
            for other in retained
        )
        assert route >= 0.35 and stage >= 0.35 and pad >= 0.25 and existing >= 0.35, item["id"]
        assert retained_clearance >= 0.25, (item["id"], retained_clearance)
        reports.append({
            "id": item["id"], "routeClearance": round(route, 4),
            "stageClearance": round(stage, 4), "padClearance": round(pad, 4),
            "existingPropClearance": round(existing, 4),
            "retainedE2AccessoryClearance": round(retained_clearance, 4),
        })
    pairwise = []
    for index, left in enumerate(props):
        for right in props[index + 1:]:
            distance = math.hypot(
                left["position"]["x"] - right["position"]["x"],
                left["position"]["z"] - right["position"]["z"],
            )
            clearance = distance - radii[left["glb"]] * left["scale"] - radii[right["glb"]] * right["scale"]
            assert clearance >= 0.25, (left["id"], right["id"], clearance)
            pairwise.append(clearance)
    return {
        "path": str(manifest_path.relative_to(ROOT)), "count": len(props),
        "types": sorted(expected), "retainedE2Count": len(retained), "placements": reports,
        "minimumPairwiseClearance": round(min(pairwise), 4),
    }


def check_tonal_metrics():
    metrics_path = OUT / "comparison-metrics.json"
    metrics = json.loads(metrics_path.read_text())
    reports = {}
    for asset_id in BUILDINGS:
        metric_id = {"stamp_mill": "stamp-mill", "dynamo_hall": "dynamo-hall"}.get(asset_id, asset_id)
        gate = metrics[metric_id]["localizedTonalGate"]
        assert gate["method"] == "changed-pixel bounds plus 64px building-and-neighbor context"
        assert gate["changedPixelCount"] > 0 and abs(gate["deltaPercent"]) <= 5.0 and gate["passed"] is True
        reports[asset_id] = gate
    return {"path": str(metrics_path.relative_to(ROOT)), "buildings": reports}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    evidence = {"blender": bpy.app.version_string, "productionBuildingCount": len(BUILDINGS),
                "buildings": {}, "propVariants": {}, "accessories": {}}
    for asset_id, spec in BUILDINGS.items():
        evidence["buildings"][asset_id] = wave7b.check_asset(asset_id, spec)
    for asset_id, spec in PROP_VARIANTS.items():
        evidence["propVariants"][asset_id] = wave7b.check_asset(asset_id, spec)
    for asset_id, spec in ACCESSORIES.items():
        evidence["accessories"][asset_id] = wave7b.check_asset(asset_id, spec)
    atlas_hashes = {
        asset_id: wave7b.embedded_image_sha(spec["variantGlb"])
        for asset_id, spec in ACCESSORIES.items()
    }
    assert len(set(atlas_hashes.values())) == 1
    evidence["sharedAccessoryAtlas"] = {
        "path": str((PROPS / "era-props-e3-atlas.png").relative_to(ROOT)),
        "sha256": wave7b.verify.sha256(PROPS / "era-props-e3-atlas.png"),
        "embeddedSha256": next(iter(atlas_hashes.values())),
        "allEmbeddedCopiesIdentical": True,
    }
    evidence["manifest"] = check_manifest()
    evidence["localizedTonalGate"] = check_tonal_metrics()
    (OUT / "asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
