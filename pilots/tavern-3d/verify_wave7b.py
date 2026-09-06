from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

import bpy


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts/town-e2-variants"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


verify = load_module("wave7_verify", Path(__file__).with_name("verify_wave7_e2_variants.py"))
town = load_module("wave7_town", ROOT / "assets/pilots/town-plate-3d/build_town_plate.py")


def building(directory, stem, object_name, anchors, blend_sha, glb_sha):
    base = ROOT / "assets/pilots" / directory
    return {
        "baseBlend": base / f"{stem}.blend", "baseGlb": base / f"{stem}.glb",
        "variantBlend": base / f"{stem}.e2.blend", "variantGlb": base / f"{stem}.e2.glb",
        "object": object_name, "anchors": anchors, "baseBlendSha": blend_sha, "baseGlbSha": glb_sha,
        "budget": 15_000, "imageDimensions": [[1024, 1024]], "sameEnvelope": True,
    }


BUILDINGS = {
    **{key: {**value, "budget": 15_000, "imageDimensions": [[1024, 1024]], "sameEnvelope": True}
       for key, value in verify.ASSETS.items()},
    "general_store": building(
        "general-store-3d", "general-store", "GeneralStoreE2", ["steam_anchor_1", "steam_anchor_2"],
        "7dcd16a3538931e1772278ddbac1f8b26e190b1ddff4e1670b7fb72b0d8fac4e",
        "b5f254861353b3ba7f3cf52d8ab1bffffc176cb2226d5edba50d85639163c154",
    ),
    "schoolhouse": building(
        "schoolhouse-3d", "schoolhouse", "SchoolhouseE2",
        ["steam_anchor_1", "steam_anchor_2", "steam_anchor_3"],
        "ebe299897e6f59a564889c5d9731e1ff8333584dbe18506786357a24e092ef6f",
        "83290545b29f1ba16a5bc59de239b12c8e6bc594a8382320b3ceb8c3778f03d0",
    ),
    "assay_office": building(
        "assay-office-3d", "assay-office", "AssayOfficeE2", ["steam_anchor_1"],
        "07d9b7345b6ae8647a4bf5a615b7f4625578734d6bf250bd3f17e0cdc524c9fa",
        "8005176893d4b2b4c465ec8e75d4a6b53c0ffa19d1212f7c99c6c825033adeb4",
    ),
    "chapel": building(
        "chapel-3d", "chapel", "ChapelE2", ["steam_anchor_1"],
        "cf84d4dacce680130577be3d3bcdc3f75c5a4a789541c1de543e7e15e1d6fd59",
        "7422e20113ae7c21b5231a6468ca1a051a1c7bd4c895ed874b775d9372d7b84b",
    ),
    "stamp_mill": building(
        "stamp-mill-3d", "stamp-mill", "StampMillE2", ["steam_anchor_1", "steam_anchor_2"],
        "b122221dbeb0697cdb465e6bd20a3c7164b3cad4688b75ae1b06b7dade4c9596",
        "4e2d1acb932a9c41a5d4278de39dcffe00ce30920261c1a2f114a794f343b6aa",
    ),
    "dynamo_hall": building(
        "dynamo-hall-3d", "dynamo-hall", "DynamoHallE2", ["steam_anchor_1", "steam_anchor_2"],
        "7e1c17772d0f7f59b296de26e908dbaaa7eb85139bae677116fff0b6041cc58b",
        "3e8f70f2a4e990ef729ffb4ee80de6ff2d2e4828f86a31d794a821db487fcefb",
    ),
}

PROPS_DIR = ROOT / "assets/pilots/plaza-props-3d"
PROP_VARIANTS = {
    "covered_wagon": {
        "baseBlend": PROPS_DIR / "covered_wagon.blend", "baseGlb": PROPS_DIR / "covered_wagon.glb",
        "variantBlend": PROPS_DIR / "covered_wagon.e2.blend", "variantGlb": PROPS_DIR / "covered_wagon.e2.glb",
        "object": "CoveredWagonE2", "anchors": ["steam_anchor_1"], "budget": 1800,
        "imageDimensions": [[256, 256]], "sameEnvelope": True,
        "baseBlendSha": "8255fe293eeb3eec83a07b5fb1f7147ffcacc5f05199855d31a8f03f25dd9820",
        "baseGlbSha": "1d095b29836a96c8a85b0f5741ff60235546dc44c58f23e405f9260875215422",
    },
    "water_trough": {
        "baseBlend": PROPS_DIR / "water_trough.blend", "baseGlb": PROPS_DIR / "water_trough.glb",
        "variantBlend": PROPS_DIR / "water_trough.e2.blend", "variantGlb": PROPS_DIR / "water_trough.e2.glb",
        "object": "WaterTroughE2", "anchors": [], "budget": 1200,
        "imageDimensions": [[256, 256]], "sameEnvelope": True,
        "baseBlendSha": "52714b0c41f381c19cbe2305a13bbf3dbc11a4d50471d3fe992d617e01776fa7",
        "baseGlbSha": "dfc4a1218f0cc522cf281b1984d8380e62b781618c1bf122df40fd9179d9b7f3",
    },
}


def accessory(stem, object_name, anchors):
    return {
        "variantBlend": PROPS_DIR / f"{stem}.blend", "variantGlb": PROPS_DIR / f"{stem}.glb",
        "object": object_name, "anchors": anchors, "budget": 1000,
        "imageDimensions": [[1024, 1024]], "sameEnvelope": False,
    }


ACCESSORIES = {
    "coal_bin": accessory("coal-bin.e2", "CoalBinE2", []),
    "pipe_run": accessory("pipe-run.e2", "PipeRunE2", ["steam_anchor_1"]),
    "gauge_post": accessory("gauge-post.e2", "GaugePostE2", []),
    "iron_lamp_post": accessory("iron-lamp-post.e2", "IronLampPostE2", []),
    "pressure_manifold": accessory("pressure-manifold.e2", "PressureManifoldE2", ["steam_anchor_1"]),
}

SEMANTIC_KEYS = (
    "meshes", "primitives", "nodes", "anchors", "triangles", "materials", "images", "embeddedImages",
    "imageDimensions", "cameras", "lights", "animations", "bounds", "materialContract",
)


def check_asset(asset_id, spec):
    if "baseGlb" in spec:
        assert verify.sha256(spec["baseBlend"]) == spec["baseBlendSha"]
        assert verify.sha256(spec["baseGlb"]) == spec["baseGlbSha"]
        base = verify.contract(spec["baseGlb"])
    else:
        base = None
    checked = verify.contract(spec["variantGlb"])
    reexport_path = Path("/tmp") / f"{spec['variantGlb'].stem}-wave7b-reexport.glb"
    verify.export_saved_blend(spec, reexport_path)
    reexported = verify.contract(reexport_path)
    material = checked["materialContract"][0]
    item = {
        "baseIntegrity": None if base is None else {
            "blendSha256": verify.sha256(spec["baseBlend"]), "glbSha256": verify.sha256(spec["baseGlb"]),
        },
        "base": base, "checked": checked, "reexported": reexported,
        "byteIdentical": checked["sha256"] == reexported["sha256"],
        "semanticIdentical": {key: checked[key] == reexported[key] for key in SEMANTIC_KEYS},
        "sameEnvelopeAsBase": None if base is None else checked["bounds"] == base["bounds"],
    }
    assert checked["meshes"] == checked["primitives"] == 1
    assert [anchor["name"] for anchor in checked["anchors"]] == spec["anchors"]
    assert checked["triangles"] <= spec["budget"]
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["imageDimensions"] == spec["imageDimensions"]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert abs(checked["bounds"]["min"][1]) < 0.001
    assert material["metallicFactor"] == 0 and material["roughnessFactor"] >= 0.899
    assert material["hasBaseColorTexture"] and not material["hasEmissiveTexture"]
    assert item["byteIdentical"] and all(item["semanticIdentical"].values())
    if spec["sameEnvelope"]:
        assert item["sameEnvelopeAsBase"]
    return item


def embedded_image_sha(path):
    document, binary = verify.read_glb(path)
    image = document["images"][0]
    view = document["bufferViews"][image["bufferView"]]
    start = view.get("byteOffset", 0)
    return hashlib.sha256(binary[start:start + view["byteLength"]]).hexdigest()


def check_manifest():
    manifest_path = PROPS_DIR / "era-props.e2.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["epoch"] == 2 and manifest["atlas"] == "era-props-e2-atlas.png"
    expected_glbs = {"coal-bin.e2.glb", "pipe-run.e2.glb", "gauge-post.e2.glb",
                     "iron-lamp-post.e2.glb", "pressure-manifold.e2.glb"}
    radii = {
        "coal-bin.e2.glb": 0.65, "pipe-run.e2.glb": 1.05, "gauge-post.e2.glb": 0.42,
        "iron-lamp-post.e2.glb": 0.65, "pressure-manifold.e2.glb": 0.82,
    }
    props = manifest["props"]
    assert {item["glb"] for item in props} == expected_glbs
    assert len({item["id"] for item in props}) == len(props)
    reports = []
    for item in props:
        assert set(item) == {"id", "glb", "position", "rotation", "scale"}
        assert set(item["position"]) == {"x", "z"}
        assert (PROPS_DIR / item["glb"]).is_file()
        radius = radii[item["glb"]] * item["scale"]
        x, z = item["position"]["x"], item["position"]["z"]
        route = town.route_distance(x, z) - radius
        stage = math.hypot(x, z) - radius - town.PLAZA_CLEAR_RADIUS
        pad = min(town.rectangle_outside_distance(x, z, slot) - radius for slot in [*town.SLOTS, town.DYNAMO_SLOT])
        existing = min(
            math.hypot(x - prop.position.x, z - prop.position.y) - radius - town.prop_radius(prop)
            for prop in town.PROPS
        )
        assert route >= 0.35 and stage >= 0.35 and pad >= 0.25 and existing >= 0.35, item["id"]
        reports.append({"id": item["id"], "routeClearance": round(route, 4),
                        "stageClearance": round(stage, 4), "padClearance": round(pad, 4),
                        "existingPropClearance": round(existing, 4)})
    pairwise = []
    for index, left in enumerate(props):
        for right in props[index + 1:]:
            distance = math.hypot(left["position"]["x"] - right["position"]["x"],
                                  left["position"]["z"] - right["position"]["z"])
            clearance = distance - radii[left["glb"]] * left["scale"] - radii[right["glb"]] * right["scale"]
            assert clearance >= 0.25, (left["id"], right["id"], clearance)
            pairwise.append(clearance)
    return {
        "path": str(manifest_path.relative_to(ROOT)), "count": len(props), "types": sorted(expected_glbs),
        "placements": reports, "minimumPairwiseClearance": round(min(pairwise), 4),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    evidence = {"blender": bpy.app.version_string, "inventoryCount": len(BUILDINGS),
                "buildings": {}, "propVariants": {}, "accessories": {}}
    for asset_id, spec in BUILDINGS.items():
        evidence["buildings"][asset_id] = check_asset(asset_id, spec)
    for asset_id, spec in PROP_VARIANTS.items():
        evidence["propVariants"][asset_id] = check_asset(asset_id, spec)
    for asset_id, spec in ACCESSORIES.items():
        evidence["accessories"][asset_id] = check_asset(asset_id, spec)
    atlas_hashes = {asset_id: embedded_image_sha(spec["variantGlb"]) for asset_id, spec in ACCESSORIES.items()}
    assert len(set(atlas_hashes.values())) == 1
    evidence["sharedAccessoryAtlas"] = {
        "path": str((PROPS_DIR / "era-props-e2-atlas.png").relative_to(ROOT)),
        "sha256": verify.sha256(PROPS_DIR / "era-props-e2-atlas.png"),
        "embeddedSha256": next(iter(atlas_hashes.values())), "allEmbeddedCopiesIdentical": True,
    }
    evidence["manifest"] = check_manifest()
    output = OUT / "wave7b-asset-contract.json"
    output.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
