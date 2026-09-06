from pathlib import Path
import importlib.util
import json
import sys

import bpy


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "artifacts/town-e6-pilot"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


verify = load_module("wave11_e6_contract_helpers", HERE / "verify_wave7_e2_variants.py")

ASSETS = {
    "atomic_diner": {
        "blend": HERE / "tavern.e6.blend",
        "glb": HERE / "tavern.e6.glb",
        "object": "TownTavernE6AtomicDiner",
        "budget": 15_000,
        "footprint": [5.2, 3.4],
        "sourceBlend": HERE / "town-v3-tavern.blend",
        "sourceGlb": HERE / "town-v3-tavern.glb",
        "sourceBlendSha": "b81ef19a24661c3ea97feb3b7f75caceef5599954d6462b1bbd2ab6085ade2fe",
        "sourceGlbSha": "edec4934d6d956170078b521fe526ccadcde015567094aec59001e2d4b71b90d",
    },
    "reactor_dome": {
        "blend": ROOT / "assets/pilots/reactor-dome-3d/reactor-dome.blend",
        "glb": ROOT / "assets/pilots/reactor-dome-3d/reactor-dome.glb",
        "object": "ReactorDomeE6",
        "budget": 15_000,
        "footprint": [6.2, 6.2],
    },
    "isotope_kitchen": {
        "blend": ROOT / "assets/pilots/isotope-kitchen-3d/isotope-kitchen.blend",
        "glb": ROOT / "assets/pilots/isotope-kitchen-3d/isotope-kitchen.glb",
        "object": "IsotopeKitchenE6",
        "budget": 15_000,
        "footprint": [4.8, 3.3],
    },
}

SEMANTIC_KEYS = (
    "meshes", "primitives", "nodes", "anchors", "triangles", "materials", "images",
    "embeddedImages", "imageDimensions", "cameras", "lights", "animations", "bounds",
    "materialContract",
)


def export_saved_blend(spec, output):
    bpy.ops.wm.open_mainfile(filepath=str(spec["blend"]))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    helpers = [obj for obj in bpy.data.objects if obj.type in {"EMPTY", "CAMERA", "LIGHT"}]
    assert len(meshes) == 1 and meshes[0].name == spec["object"], [obj.name for obj in meshes]
    assert not helpers, [(obj.name, obj.type) for obj in helpers]
    bpy.ops.object.select_all(action="DESELECT")
    meshes[0].select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(
        filepath=str(output), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT",
    )


def check_asset(asset_id, spec):
    checked = verify.contract(spec["glb"])
    reexport_path = Path("/tmp") / f"{spec['glb'].stem}-wave11-reexport.glb"
    export_saved_blend(spec, reexport_path)
    reexported = verify.contract(reexport_path)
    material = checked["materialContract"][0]
    footprint = checked["bounds"]["size"]
    item = {
        "checked": checked,
        "reexported": reexported,
        "byteIdentical": checked["sha256"] == reexported["sha256"],
        "semanticIdentical": {key: checked[key] == reexported[key] for key in SEMANTIC_KEYS},
        "footprintGate": {
            "actualXZ": [footprint[0], footprint[2]],
            "maximumXZ": spec["footprint"],
            "passed": footprint[0] <= spec["footprint"][0] + 0.001 and footprint[2] <= spec["footprint"][1] + 0.001,
        },
    }
    if "sourceBlend" in spec:
        item["sourceIntegrity"] = {
            "blendSha256": verify.sha256(spec["sourceBlend"]),
            "glbSha256": verify.sha256(spec["sourceGlb"]),
        }
        assert item["sourceIntegrity"] == {
            "blendSha256": spec["sourceBlendSha"], "glbSha256": spec["sourceGlbSha"],
        }
    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["nodes"] == [spec["object"]]
    assert checked["anchors"] == []
    assert checked["triangles"] <= spec["budget"]
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["imageDimensions"] == [[1024, 1024]]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert abs(checked["bounds"]["min"][1]) < 0.001
    assert material["metallicFactor"] == 0 and material["roughnessFactor"] >= 0.899
    assert material["hasBaseColorTexture"] and not material["hasEmissiveTexture"]
    assert item["footprintGate"]["passed"]
    assert item["byteIdentical"] and all(item["semanticIdentical"].values())
    return item


def check_visual_evidence():
    contract_path = OUT / "visual-evidence-contract.json"
    evidence = json.loads(contract_path.read_text())
    metrics = evidence["comparisonMetrics"]
    assert evidence["baseSha"] == "8d974f11911187136469fbd017c9598e5b2faf28"
    assert evidence["mesaEvidenceDependency"]["sha256"] == (
        "067c8c652134258379315a41200caf423ff3e9cb70a1b9d8f2607ee691aafdc3"
    )
    assert metrics["diffRatio16"] > 0.02
    assert metrics["edgeEnergyRatio"] > 1.05
    for path in evidence["renders"]:
        assert (ROOT / path).is_file(), path
    return {
        "path": str(contract_path.relative_to(ROOT)),
        "baseSha": evidence["baseSha"],
        "diffRatio16": metrics["diffRatio16"],
        "edgeEnergyRatio": metrics["edgeEnergyRatio"],
        "renderCount": len(evidence["renders"]),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    evidence = {
        "blender": bpy.app.version_string,
        "scope": "E6 Mesa Town three-building verdict pilot",
        "laws": {
            "source": "specs/epoch-saga/e6-atomic-bundle.md",
            "atomicDiner": "Tavern identity edited forward; dry-site E6 rebuild, not E5 accretion",
            "materials": "one baked 1024 atlas per GLB; no emission or helpers",
            "budget": "15,000 triangles per building",
        },
        "assets": {asset_id: check_asset(asset_id, spec) for asset_id, spec in ASSETS.items()},
        "visualEvidence": check_visual_evidence(),
    }
    (OUT / "asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
