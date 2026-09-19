from pathlib import Path
from collections import Counter
import importlib.util
import json
import math
import struct
import sys

import bpy


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "artifacts/town-e4-wide"
PROPS = ROOT / "assets/pilots/plaza-props-3d"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


build = load_module("wave9_e4_wide_build", HERE / "build_wave9_e4_wide.py")
pilot_verify = load_module("wave9_e4_pilot_verify", HERE / "verify_wave9_e4_pilot.py")
wave7b = pilot_verify.wave7b

ANCHOR_COUNTS = {
    "tavern": 3, "general_store": 2, "claim_office": 2, "assay_office": 2,
    "chapel": 0, "schoolhouse": 2, "stamp_mill": 2, "dynamo_hall": 3,
}


def building(asset_id, spec):
    base = ROOT / "assets/pilots" / spec["directory"]
    return {
        "baseBlend": base / f'{spec["source"]}.blend',
        "baseGlb": base / f'{spec["source"]}.glb',
        "variantBlend": base / f'{spec["stem"]}.e4.blend',
        "variantGlb": base / f'{spec["stem"]}.e4.glb',
        "object": spec["output"],
        "anchors": [f"exhaust_anchor_{index}" for index in range(1, ANCHOR_COUNTS[asset_id] + 1)],
        "budget": 15_000, "imageDimensions": [[1024, 1024]], "sameEnvelope": True,
        "baseBlendSha": spec["blend_sha"], "baseGlbSha": spec["glb_sha"],
    }


BUILDINGS = {
    **{key: building(key, spec) for key, spec in build.pilot.SPECS.items()},
    **{key: building(key, spec) for key, spec in build.SPECS.items()},
}


def prop_variant(stem, source, object_name, budget, blend_sha, glb_sha, anchors):
    return {
        "baseBlend": PROPS / f"{source}.blend", "baseGlb": PROPS / f"{source}.glb",
        "variantBlend": PROPS / f"{stem}.blend", "variantGlb": PROPS / f"{stem}.glb",
        "object": object_name, "anchors": anchors, "budget": budget,
        "imageDimensions": [[256, 256]], "sameEnvelope": True,
        "baseBlendSha": blend_sha, "baseGlbSha": glb_sha,
    }


PROP_VARIANTS = {
    "covered_wagon": prop_variant(
        "covered_wagon.e4", "covered_wagon.e3", "CoveredWagonE4", 1800,
        "767e45ec4acefdd069003e64114ddb0633774780d3843fd394b677567d2b1419",
        "e7e7b0cd6d851e273adec71625edaf1b47629b663274596562389f8b81f9570e",
        ["exhaust_anchor_1"],
    ),
    "water_trough": prop_variant(
        "water_trough.e4", "water_trough.e3", "WaterTroughE4", 1200,
        "076bb171f70d2cd158055d421ef1d76d67204c3adc541cbef8064a202c8f1b85",
        "866920e7f82b15891a93ff585a1f9a70b72e121eaa10ca16f688ed30006126e5",
        [],
    ),
}


def accessory(stem, object_name, anchors):
    return {
        "variantBlend": PROPS / f"{stem}.blend", "variantGlb": PROPS / f"{stem}.glb",
        "object": object_name, "anchors": anchors, "budget": 1000,
        "imageDimensions": [[1024, 1024]], "sameEnvelope": False,
    }


ACCESSORIES = {
    "fuel_rack": accessory("fuel-rack.e4", "FuelRackE4", ["exhaust_anchor_1"]),
    "road_marker": accessory("road-marker.e4", "RoadMarkerE4", ["exhaust_anchor_1"]),
    "filling_shed": accessory(
        "filling-shed.e4", "FillingShedE4",
        ["exhaust_anchor_1", "exhaust_anchor_2", "exhaust_anchor_3"],
    ),
    "motor_roadway": accessory("motor-roadway.e4", "MotorRoadwayE4", []),
}


CADENCE = [
    {"fixture": "Motor Inn", "cadence": "upgraded", "accretion": "PERSIST E3 festoon; RELIC older steam fittings; REPLACE arc anchors with exhaust anchors", "justification": "Motor travel directly creates the drive-through inn."},
    {"fixture": "Polytechnic", "cadence": "upgraded", "accretion": "PERSIST E3 orrery/grid hardware; RELIC older steam fittings; REPLACE arc anchors with exhaust anchors", "justification": "Vehicle engineering plausibly grows its drafting wing and wind gauge."},
    {"fixture": "General Store", "cadence": "upgraded", "accretion": "PERSIST shop shell and electric loading service; RELIC steam fittings; REPLACE arc anchors with exhaust anchors", "justification": "A frontier store becomes the public motor-supply and service point."},
    {"fixture": "Claim Office", "cadence": "upgraded", "accretion": "PERSIST civic shell and grid feed; RELIC steam fittings; REPLACE arc anchors with exhaust anchors", "justification": "Motor roads create permits, route boards, and vehicle registration."},
    {"fixture": "Assay Office", "cadence": "upgraded", "accretion": "PERSIST electrical laboratory gear; RELIC steam apparatus; REPLACE arc anchors with exhaust anchors", "justification": "Fuel quality and oil samples give the assay lab a direct Motor-era job."},
    {"fixture": "Chapel", "cadence": "upgraded", "accretion": "PERSIST chapel, cross, and prior wiring; RELIC cold steam hardware; REPLACE active arc seam with no E4 emitter", "justification": "Motors barely touch worship: one parking rail and an old oil stain, with no active exhaust fixture."},
    {"fixture": "Stamp Mill", "cadence": "upgraded", "accretion": "PERSIST electric drive; RELIC steam-era plant; REPLACE arc anchors with exhaust anchors", "justification": "Industrial motors directly alter the mill's drive and service yard."},
    {"fixture": "Dynamo Hall", "cadence": "upgraded", "accretion": "PERSIST the E3 grid crown; RELIC steam header; REPLACE arc anchors with exhaust anchors", "justification": "The grid now supplies motors and gains a public Motor Works function."},
    {"fixture": "Covered wagon", "cadence": "upgraded", "accretion": "PERSIST wagon shell; RELIC E2 fittings and E3 voltage terminal; REPLACE arc anchor with exhaust anchor", "justification": "A wedge bonnet, cab window, headlamp, and light-dust exhaust turn the wagon into a playful compact motor caravan."},
    {"fixture": "Water trough", "cadence": "relic'd", "accretion": "PERSIST trough shell; RELIC capped E2/E3 feed and pump; REPLACE active arc seam with no E4 emitter", "justification": "Horse infrastructure fades instead of becoming a motor appliance."},
    {"fixture": "Street lamps", "cadence": "carried-unchanged", "accretion": "PERSIST E3-era street lighting; no E4 replacement", "justification": "Motors do not relight a street."},
    {"fixture": "Town roads", "cadence": "upgraded", "accretion": "PERSIST canonical flat walk geometry; NEW E4 split compacted gate lanes", "justification": "Motors pave paired entrance lanes around the inherited horse-trough relic while the plaza stays open."},
    {"fixture": "E3 grid accessories", "cadence": "carried-unchanged", "accretion": "PERSIST wire runs, insulator posts, and transformer shed; arc effects stay cold in E4", "justification": "The electrical grid still serves the town even when its era effect is dormant."},
    {"fixture": "E2 steam accessories", "cadence": "relic'd", "accretion": "RELIC coal bin, pipe run, gauge post, and manifold; steam effects stay cold", "justification": "Motor infrastructure supersedes their public-era role without erasing the town's history."},
    {"fixture": "Hitching posts", "cadence": "relic'd", "accretion": "RELIC posts remain in place", "justification": "The posts outlive the horse traffic they served."},
    {"fixture": "Fences, well, notice board, and planters", "cadence": "carried-unchanged", "accretion": "PERSIST unchanged", "justification": "Motor technology has no believable reason to rebuild ordinary civic furniture."},
    {"fixture": "Fuel racks, road markers, and filling shed", "cadence": "upgraded", "accretion": "NEW E4 infrastructure", "justification": "Fuel and marked motor routes are the accessory pack's ensemble-level Motor announcement."},
    {"fixture": "Pan Monument", "cadence": "carried-unchanged", "accretion": "PERSIST by Heritage Law", "justification": "The Town changes around its permanent through-line."},
]


COMPONENTS = {
    5121: ("B", 1), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4),
}
COMPONENT_COUNTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def read_accessor(document, binary, accessor_index):
    accessor = document["accessors"][accessor_index]
    view = document["bufferViews"][accessor["bufferView"]]
    component_format, component_size = COMPONENTS[accessor["componentType"]]
    component_count = COMPONENT_COUNTS[accessor["type"]]
    packed_size = component_size * component_count
    stride = view.get("byteStride", packed_size)
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    row_format = "<" + component_format * component_count
    return [
        struct.unpack_from(row_format, binary, offset + index * stride)
        for index in range(accessor["count"])
    ]


def triangle_signatures(path):
    document, binary = wave7b.verify.read_glb(path)
    signatures = Counter()
    for mesh in document["meshes"]:
        for primitive in mesh["primitives"]:
            positions = read_accessor(document, binary, primitive["attributes"]["POSITION"])
            indices = read_accessor(document, binary, primitive["indices"])
            flat_indices = [row[0] for row in indices]
            for start in range(0, len(flat_indices), 3):
                triangle = tuple(sorted(
                    tuple(round(value, 5) for value in positions[index])
                    for index in flat_indices[start:start + 3]
                ))
                signatures[triangle] += 1
    return signatures


def check_accretion(base_path, variant_path):
    inherited = triangle_signatures(base_path)
    descendant = triangle_signatures(variant_path)
    missing = inherited - descendant
    assert not missing, f"Accretion Law failure: {len(missing)} inherited triangles missing from {variant_path.name}"
    return {
        "source": str(base_path.relative_to(ROOT)),
        "inheritedTriangleSignatures": sum(inherited.values()),
        "descendantTriangleSignatures": sum(descendant.values()),
        "missingInheritedTriangleSignatures": 0,
        "passed": True,
    }


def check_accessory(asset_id, spec):
    checked = pilot_verify.contract(spec["variantGlb"])
    output = Path("/tmp") / f"{spec['variantGlb'].stem}-wave9-wide-reexport.glb"
    pilot_verify.export_saved_blend(spec, output)
    reexported = pilot_verify.contract(output)
    material = checked["materialContract"][0]
    assert checked["meshes"] == checked["primitives"] == 1
    assert [anchor["name"] for anchor in checked["anchors"]] == spec["anchors"]
    assert checked["triangles"] <= spec["budget"]
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["imageDimensions"] == spec["imageDimensions"]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    if asset_id != "motor_roadway":
        assert abs(checked["bounds"]["min"][1]) < 0.001
    assert material["metallicFactor"] == 0 and material["roughnessFactor"] >= 0.899
    assert material["hasBaseColorTexture"] and not material["hasEmissiveTexture"]
    assert checked["sha256"] == reexported["sha256"]
    assert all(checked[key] == reexported[key] for key in wave7b.SEMANTIC_KEYS)
    return {"checked": checked, "reexported": reexported, "byteIdentical": True}


RADII = {
    "coal-bin.e2.glb": 0.65, "pipe-run.e2.glb": 1.05, "gauge-post.e2.glb": 0.42,
    "iron-lamp-post.e2.glb": 0.65, "pressure-manifold.e2.glb": 0.82,
    "wire-run.e3.glb": 1.20, "insulator-post.e3.glb": 0.50, "transformer-shed.e3.glb": 1.0,
    "fuel-rack.e4.glb": 0.90, "road-marker.e4.glb": 1.10, "filling-shed.e4.glb": 1.65,
}


def check_manifest():
    path = PROPS / "era-props.e4.json"
    manifest = json.loads(path.read_text())
    assert manifest["epoch"] == 4 and manifest["atlas"] == "era-props-e4-atlas.png"
    expected = {"fuel-rack.e4.glb", "road-marker.e4.glb", "filling-shed.e4.glb", "motor-roadway.e4.glb"}
    assert {item["glb"] for item in manifest["props"]} == expected
    assert len({item["id"] for item in manifest["props"]}) == len(manifest["props"])
    retained = [
        item
        for epoch in (2, 3)
        for item in json.loads((PROPS / f"era-props.e{epoch}.json").read_text())["props"]
    ]
    reports = []
    for item in manifest["props"]:
        assert set(item) == {"id", "glb", "position", "rotation", "scale"}
        assert set(item["position"]) == {"x", "z"} and (PROPS / item["glb"]).is_file()
        if item["glb"] == "motor-roadway.e4.glb":
            assert item["position"] == {"x": 0, "z": 0} and item["rotation"] == 0 and item["scale"] == 1
            document, binary = wave7b.verify.read_glb(PROPS / item["glb"])
            positions = [
                position
                for mesh in document["meshes"]
                for primitive in mesh["primitives"]
                for position in read_accessor(document, binary, primitive["attributes"]["POSITION"])
            ]
            heights = [position[1] for position in positions]
            radii = [math.hypot(position[0], position[2]) for position in positions]
            plate_clearances = [
                position[1] - wave7b.town.terrain_height(position[0], -position[2])
                for position in positions
            ]
            route_separations = [
                wave7b.town.route_distance(position[0], -position[2])
                for position in positions
            ]
            assert min(plate_clearances) >= 0.017 and max(plate_clearances) <= 0.021
            assert min(route_separations) >= 0.35
            assert min(radii) >= wave7b.town.PLAZA_CLEAR_RADIUS
            reports.append({
                "id": item["id"], "terrainConformingSurface": True,
                "minimumStageRadius": round(min(radii), 4),
                "minimumRouteSeparation": round(min(route_separations), 4),
                "minimumPlateClearance": round(min(plate_clearances), 4),
                "maximumPlateClearance": round(max(plate_clearances), 4),
                "minimumSurfaceHeight": round(min(heights), 4),
                "maximumSurfaceHeight": round(max(heights), 4),
            })
            continue
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
        retained_clearance = min(
            math.hypot(x - other["position"]["x"], z - other["position"]["z"])
            - radius - RADII[other["glb"]] * other["scale"]
            for other in retained
        )
        assert route >= 0.35 and stage >= 0.35 and pad >= 0.25 and existing >= 0.35, (item["id"], route, stage, pad, existing)
        assert retained_clearance >= 0.25, (item["id"], retained_clearance)
        reports.append({
            "id": item["id"], "routeClearance": round(route, 4),
            "stageClearance": round(stage, 4), "padClearance": round(pad, 4),
            "existingPropClearance": round(existing, 4),
            "retainedE2E3AccessoryClearance": round(retained_clearance, 4),
        })
    pairwise = []
    physical = [item for item in manifest["props"] if item["glb"] != "motor-roadway.e4.glb"]
    for index, left in enumerate(physical):
        for right in physical[index + 1:]:
            clearance = math.hypot(
                left["position"]["x"] - right["position"]["x"],
                left["position"]["z"] - right["position"]["z"],
            ) - RADII[left["glb"]] * left["scale"] - RADII[right["glb"]] * right["scale"]
            assert clearance >= 0.25, (left["id"], right["id"], clearance)
            pairwise.append(clearance)
    return {
        "path": str(path.relative_to(ROOT)), "count": len(manifest["props"]),
        "types": sorted(expected), "retainedAccessoryCount": len(retained), "placements": reports,
        "minimumPairwiseClearance": round(min(pairwise), 4),
    }


def check_visual_evidence():
    metrics_path = OUT / "comparison-metrics.json"
    metrics = json.loads(metrics_path.read_text())
    blind_path = OUT / "blind-key.json"
    blind = json.loads(blind_path.read_text())
    tonal = {}
    for asset_id in BUILDINGS:
        metric_id = {"stamp_mill": "stamp-mill", "dynamo_hall": "dynamo-hall"}.get(asset_id, asset_id)
        gate = metrics[metric_id]["localizedTonalGate"]
        assert abs(gate["deltaPercent"]) <= 5.0 and gate["passed"] is True
        assert {blind[metric_id]["a"], blind[metric_id]["b"]} == {"e3", "e4"}
        if asset_id == "chapel":
            assert gate["method"].startswith("cadence-approved quiet fixture")
        else:
            assert gate["changedPixelCount"] > 0 and blind[metric_id]["changedPixelCount"] > 0
            assert blind[metric_id]["changedRatioInCrop"] > 0.01
        tonal[asset_id] = gate
    assert blind["integrated"] == {"a": "e4", "b": "e3"}
    assert metrics["integrated"]["diffRatio16"] > 0.01
    return {
        "metrics": str(metrics_path.relative_to(ROOT)), "blindKey": str(blind_path.relative_to(ROOT)),
        "localizedTonalGate": tonal,
        "ensembleMotorRead": {
            "blindPair": str((OUT / "town-ensemble-blind-pair.png").relative_to(ROOT)),
            "changedPixelRatio16": metrics["integrated"]["diffRatio16"],
            "passed": True,
        },
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    evidence = {
        "blender": bpy.app.version_string,
        "scope": "complete eight-building E4 family, wagon, trough, and ratifiable accessory pack",
        "buildings": {}, "propVariants": {}, "accessories": {},
    }
    for asset_id, spec in BUILDINGS.items():
        checked = pilot_verify.check_asset(asset_id, spec)
        nodes = checked["checked"]["nodes"]
        assert not [name for name in nodes if name.startswith(("arc_anchor_", "steam_anchor_"))]
        checked["inheritance"] = check_accretion(spec["baseGlb"], spec["variantGlb"])
        evidence["buildings"][asset_id] = checked
    for asset_id, spec in PROP_VARIANTS.items():
        checked = pilot_verify.check_asset(asset_id, spec)
        nodes = checked["checked"]["nodes"]
        assert not [name for name in nodes if name.startswith(("arc_anchor_", "steam_anchor_"))]
        checked["inheritance"] = check_accretion(spec["baseGlb"], spec["variantGlb"])
        evidence["propVariants"][asset_id] = checked
    for asset_id, spec in ACCESSORIES.items():
        evidence["accessories"][asset_id] = check_accessory(asset_id, spec)
    hashes = {
        asset_id: wave7b.embedded_image_sha(spec["variantGlb"])
        for asset_id, spec in ACCESSORIES.items()
    }
    assert len(set(hashes.values())) == 1
    evidence["sharedAccessoryAtlas"] = {
        "path": str((PROPS / "era-props-e4-atlas.png").relative_to(ROOT)),
        "sha256": wave7b.verify.sha256(PROPS / "era-props-e4-atlas.png"),
        "embeddedSha256": next(iter(hashes.values())), "allEmbeddedCopiesIdentical": True,
    }
    evidence["manifest"] = check_manifest()
    assert all(row["cadence"] in {"upgraded", "carried-unchanged", "relic'd"} for row in CADENCE)
    evidence["cadence"] = CADENCE
    evidence["visualEvidence"] = check_visual_evidence()
    (OUT / "asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
