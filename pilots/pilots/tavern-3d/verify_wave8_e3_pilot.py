from pathlib import Path
import importlib.util
import json
import sys

import bpy


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "artifacts/town-e3-pilot"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


verify = load_module("wave7_verify", HERE / "verify_wave7_e2_variants.py")


def asset(directory, stem, source, object_name, blend_sha, glb_sha):
    base = ROOT / "assets/pilots" / directory
    return {
        "sourceBlend": base / f"{source}.blend", "sourceGlb": base / f"{source}.glb",
        "variantBlend": base / f"{stem}.e3.blend", "variantGlb": base / f"{stem}.e3.glb",
        "object": object_name, "anchors": ["arc_anchor_1", "arc_anchor_2", "arc_anchor_3"],
        "sourceBlendSha": blend_sha, "sourceGlbSha": glb_sha,
    }


ASSETS = {
    "tavern": asset(
        "tavern-3d", "tavern", "tavern.e2", "TownTavernE3",
        "b6c9c12138f2e7b1c4fb93e0d140fd70449439930b36f56b872d07bed4e7ad3c",
        "e72aa936ee8a5a24aa6a6840d7c43f9eb81c4005702585a93050ac3166af09ad",
    ),
    "schoolhouse": asset(
        "schoolhouse-3d", "schoolhouse", "schoolhouse.e2", "SchoolhouseE3",
        "2c3953fe077a4bef62bdce90a25b14bd7c6fdc51977ed06e0bbfba99c96fa5b6",
        "70391129ce38917012d3a7c3242d4d4420153d828c77a9fcb84b670973f5a6c6",
    ),
    "stamp_mill": asset(
        "stamp-mill-3d", "stamp-mill", "stamp-mill", "StampMillE3",
        "b122221dbeb0697cdb465e6bd20a3c7164b3cad4688b75ae1b06b7dade4c9596",
        "4e2d1acb932a9c41a5d4278de39dcffe00ce30920261c1a2f114a794f343b6aa",
    ),
}

SEMANTIC_KEYS = (
    "meshes", "primitives", "nodes", "anchors", "triangles", "materials", "images",
    "embeddedImages", "imageDimensions", "cameras", "lights", "animations", "bounds",
    "materialContract",
)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    evidence = {"blender": bpy.app.version_string, "variants": {}}
    for asset_id, spec in ASSETS.items():
        assert verify.sha256(spec["sourceBlend"]) == spec["sourceBlendSha"]
        assert verify.sha256(spec["sourceGlb"]) == spec["sourceGlbSha"]
        source = verify.contract(spec["sourceGlb"])
        checked = verify.contract(spec["variantGlb"])
        reexport_path = Path("/tmp") / f"{spec['variantGlb'].stem}-wave8-reexport.glb"
        verify.export_saved_blend(spec, reexport_path)
        reexported = verify.contract(reexport_path)
        material = checked["materialContract"][0]
        item = {
            "sourceIntegrity": {
                "blendSha256": verify.sha256(spec["sourceBlend"]),
                "glbSha256": verify.sha256(spec["sourceGlb"]),
            },
            "source": source, "checked": checked, "reexported": reexported,
            "byteIdentical": checked["sha256"] == reexported["sha256"],
            "semanticIdentical": {key: checked[key] == reexported[key] for key in SEMANTIC_KEYS},
            "sameEnvelopeAsSource": checked["bounds"] == source["bounds"],
        }
        assert checked["meshes"] == checked["primitives"] == 1
        assert [anchor["name"] for anchor in checked["anchors"]] == spec["anchors"]
        assert not [name for name in checked["nodes"] if name.startswith("steam_anchor_")]
        assert checked["triangles"] <= 15_000
        assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
        assert checked["imageDimensions"] == [[1024, 1024]]
        assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
        assert abs(checked["bounds"]["min"][1]) < 0.001
        assert material["metallicFactor"] == 0 and material["roughnessFactor"] >= 0.899
        assert material["hasBaseColorTexture"] and not material["hasEmissiveTexture"]
        assert item["sameEnvelopeAsSource"]
        assert item["byteIdentical"] and all(item["semanticIdentical"].values())
        evidence["variants"][asset_id] = item
    (OUT / "asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
