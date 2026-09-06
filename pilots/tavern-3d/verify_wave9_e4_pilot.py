from pathlib import Path
import importlib.util
import json
import sys

import bpy


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "artifacts/town-e4-pilot"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


build = load_module("wave9_e4_build", HERE / "build_wave9_e4_pilot.py")
wave7b = load_module("wave7b_verify", HERE / "verify_wave7b.py")


def asset(asset_id, spec):
    base = ROOT / "assets/pilots" / spec["directory"]
    return {
        "baseBlend": base / f'{spec["source"]}.blend',
        "baseGlb": base / f'{spec["source"]}.glb',
        "variantBlend": base / f'{spec["stem"]}.e4.blend',
        "variantGlb": base / f'{spec["stem"]}.e4.glb',
        "object": spec["output"],
        "anchors": [
            f"exhaust_anchor_{index}"
            for index in range(1, (3 if asset_id == "tavern" else 2) + 1)
        ],
        "budget": 15_000,
        "imageDimensions": [[1024, 1024]],
        "sameEnvelope": True,
        "baseBlendSha": spec["blend_sha"],
        "baseGlbSha": spec["glb_sha"],
    }


ASSETS = {key: asset(key, spec) for key, spec in build.SPECS.items()}


def contract(path):
    verify = wave7b.verify
    report = verify.contract(path)
    document, _ = verify.read_glb(path)
    report["anchors"] = [
        {
            "name": node["name"],
            "translation": [round(value, 6) for value in node.get("translation", [0, 0, 0])],
        }
        for node in document.get("nodes", [])
        if node.get("name", "").startswith("exhaust_anchor_") and "mesh" not in node
    ]
    return report


def export_saved_blend(spec, output):
    bpy.ops.wm.open_mainfile(filepath=str(spec["variantBlend"]))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    anchors = sorted(
        (obj for obj in bpy.data.objects if obj.type == "EMPTY" and obj.name.startswith("exhaust_anchor_")),
        key=lambda obj: obj.name,
    )
    assert len(meshes) == 1 and meshes[0].name == spec["object"]
    assert [anchor.name for anchor in anchors] == spec["anchors"]
    assert not [obj for obj in bpy.data.objects if obj.type in {"CAMERA", "LIGHT"}]
    bpy.ops.object.select_all(action="DESELECT")
    meshes[0].select_set(True)
    for anchor in anchors:
        anchor.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(
        filepath=str(output), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT",
    )


def check_asset(asset_id, spec):
    verify = wave7b.verify
    assert verify.sha256(spec["baseBlend"]) == spec["baseBlendSha"]
    assert verify.sha256(spec["baseGlb"]) == spec["baseGlbSha"]
    base = contract(spec["baseGlb"])
    checked = contract(spec["variantGlb"])
    reexport_path = Path("/tmp") / f"{spec['variantGlb'].stem}-wave9-reexport.glb"
    export_saved_blend(spec, reexport_path)
    reexported = contract(reexport_path)
    material = checked["materialContract"][0]
    item = {
        "baseIntegrity": {
            "blendSha256": verify.sha256(spec["baseBlend"]),
            "glbSha256": verify.sha256(spec["baseGlb"]),
        },
        "base": base,
        "checked": checked,
        "reexported": reexported,
        "byteIdentical": checked["sha256"] == reexported["sha256"],
        "semanticIdentical": {
            key: checked[key] == reexported[key] for key in wave7b.SEMANTIC_KEYS
        },
        "sameEnvelopeAsBase": checked["bounds"] == base["bounds"],
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
    assert item["sameEnvelopeAsBase"]
    assert item["byteIdentical"] and all(item["semanticIdentical"].values())
    return item


def check_tonal_metrics():
    path = OUT / "comparison-metrics.json"
    metrics = json.loads(path.read_text())
    reports = {}
    for asset_id in ASSETS:
        gate = metrics[asset_id]["localizedTonalGate"]
        assert gate["method"] == "changed-pixel bounds plus 64px building-and-neighbor context"
        assert gate["changedPixelCount"] > 0
        assert abs(gate["deltaPercent"]) <= 5.0 and gate["passed"] is True
        reports[asset_id] = gate
    return {"path": str(path.relative_to(ROOT)), "buildings": reports}


def check_blind_pairs():
    path = OUT / "blind-key.json"
    key = json.loads(path.read_text())
    for asset_id in ASSETS:
        assert {key[asset_id]["a"], key[asset_id]["b"]} == {"e3", "e4"}
        assert key[asset_id]["changedPixelCount"] > 0
        assert key[asset_id]["changedRatioInCrop"] > 0.01
        assert (OUT / "blind-crops" / f"{asset_id}-pair.png").is_file()
    return {"path": str(path.relative_to(ROOT)), "buildings": key}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    evidence = {
        "blender": bpy.app.version_string,
        "scope": "two-building verdict pilot; wide family and era-props.e4.json wait for acceptance",
        "buildings": {},
    }
    for asset_id, spec in ASSETS.items():
        checked = check_asset(asset_id, spec)
        nodes = checked["checked"]["nodes"]
        assert not [name for name in nodes if name.startswith("arc_anchor_")]
        assert not [name for name in nodes if name.startswith("steam_anchor_")]
        assert checked["checked"]["triangles"] >= checked["base"]["triangles"]
        evidence["buildings"][asset_id] = checked
    evidence["localizedTonalGate"] = check_tonal_metrics()
    evidence["acrossThePlazaBlindPairs"] = check_blind_pairs()
    (OUT / "asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
