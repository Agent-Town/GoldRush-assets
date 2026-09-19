from pathlib import Path
import importlib.util
import json
import sys

import bpy


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "artifacts/town-e6-wide"
BASE_SHA = "1a58335f65645b8491e50763e10a32d12d8696f1"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


verify = load_module("wave12_e6_contract_helpers", HERE / "verify_wave7_e2_variants.py")


def asset(directory, stem, obj, footprint, image_size, source=None, exact_source_footprint=False):
    item = {
        "blend": ROOT / directory / f"{stem}.blend",
        "glb": ROOT / directory / f"{stem}.glb",
        "object": obj,
        "budget": 15_000,
        "footprint": footprint,
        "imageSize": image_size,
    }
    if source:
        item["sourceBlend"] = ROOT / source[0]
        item["sourceGlb"] = ROOT / source[1]
        item["sourceBlendSha"] = source[2]
        item["sourceGlbSha"] = source[3]
        item["exactSourceFootprint"] = exact_source_footprint
    return item


ASSETS = {
    "appliance_pen": asset(
        "assets/pilots/appliance-pen-3d", "appliance-pen", "AppliancePenE6", [4.6, 3.4], [1024, 1024],
    ),
    "decay_clock": asset(
        "assets/pilots/decay-clock-3d", "decay-clock", "DecayClockE6", [4.4, 3.2], [1024, 1024],
    ),
    "catalog_warehouse": asset(
        "assets/pilots/catalog-warehouse-3d", "catalog-warehouse", "CatalogWarehouseE6", [5.6, 3.8], [1024, 1024],
    ),
    "sunline_mount": asset(
        "assets/pilots/run3d", "turret.e6", "SunlineMountE6", [1.35, 1.35], [512, 512],
        (
            "assets/pilots/run3d/turret.blend", "assets/pilots/run3d/turret.glb",
            "ef7a77c7c5d991cf0153a9f81a0a4bdae32ee4d5664b1d2c731e0c68c4f040cb",
            "2973dcbf4bf51d4c153398c847e6ed1a3d03d0116e901cd5a04091dd7202aab7",
        ),
        True,
    ),
    "glow_fence": asset(
        "assets/pilots/run3d", "palisade.e6", "GlowFenceE6", [0.46, 3.0], [512, 512],
        (
            "assets/pilots/run3d/palisade.blend", "assets/pilots/run3d/palisade.glb",
            "c55d7520a59286c30a4db3ac39d495d2d6d577c07b61a891e049b4a2e4725941",
            "a9841ee934fcc0035571caa4b73fc9bd9fc4827697ade631b43fe3f9c8928878",
        ),
        True,
    ),
    "isotope_institute": asset(
        "assets/pilots/schoolhouse-3d", "schoolhouse.e6", "IsotopeInstituteE6", [4.4, 3.4], [1024, 1024],
        (
            "assets/pilots/schoolhouse-3d/schoolhouse.e5.blend",
            "assets/pilots/schoolhouse-3d/schoolhouse.e5.glb",
            "6cb1105354fb87625153e7445217892154081adf4a7bf4b27426db9bbf4dcc64",
            "941076bc0b4fdd4a50709785c65de18df2398b0472cc87998ab58d1a20db2c7d",
        ),
        True,
    ),
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
    reexport_path = Path("/tmp") / f"{spec['glb'].stem}-wave12-reexport.glb"
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
        source_contract = verify.contract(spec["sourceGlb"])
        item["sourceIntegrity"] = {
            "blendSha256": verify.sha256(spec["sourceBlend"]),
            "glbSha256": verify.sha256(spec["sourceGlb"]),
            "sourceBounds": source_contract["bounds"],
        }
        assert item["sourceIntegrity"]["blendSha256"] == spec["sourceBlendSha"]
        assert item["sourceIntegrity"]["glbSha256"] == spec["sourceGlbSha"]
        if spec["exactSourceFootprint"]:
            assert checked["bounds"]["size"][0] == source_contract["bounds"]["size"][0]
            assert checked["bounds"]["size"][2] == source_contract["bounds"]["size"][2]
    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["nodes"] == [spec["object"]]
    assert checked["anchors"] == []
    assert checked["triangles"] <= spec["budget"]
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["imageDimensions"] == [spec["imageSize"]]
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
    assert evidence["baseSha"] == BASE_SHA
    assert evidence["dependencies"]["mesa"]["sha256"] == (
        "067c8c652134258379315a41200caf423ff3e9cb70a1b9d8f2607ee691aafdc3"
    )
    assert metrics["diffRatio16"] > 0.05
    assert metrics["edgeEnergyRatio"] > 1.10
    required = [
        OUT / "current-references" / f"{BASE_SHA[:12]}-main" / "town-e1-e4-e5-current.png",
        OUT / "mesa-e6-wide-across-plaza-ab.png",
        OUT / "mesa-e6-wide-key-feature-crop.png",
        *[OUT / "turntables" / f"{name}-e6.png" for name in (
            "appliance-pen", "decay-clock", "catalog-warehouse", "sunline-mount", "glow-fence", "isotope-institute",
        )],
        *[OUT / "identity" / f"{name}-identity-ab.png" for name in (
            "sunline-mount", "glow-fence", "isotope-institute",
        )],
    ]
    assert all(path.is_file() for path in required)
    return {
        "path": str(contract_path.relative_to(ROOT)),
        "baseSha": evidence["baseSha"],
        "diffRatio16": metrics["diffRatio16"],
        "edgeEnergyRatio": metrics["edgeEnergyRatio"],
        "renderCount": len(required),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    evidence = {
        "blender": bpy.app.version_string,
        "scope": "E6 Mesa Town wide building and transform set",
        "laws": {
            "source": "specs/epoch-saga/e6-atomic-bundle.md §A1 and §A2",
            "transforms": "Sunline, Glow Fence, and Isotope Institute preserve their inherited footprints",
            "materials": "one embedded painted atlas per GLB; no emission or helpers",
            "budget": "15,000 triangles per asset",
            "anchors": "none invented; E6 bundle defines no emitter-anchor family",
        },
        "assets": {asset_id: check_asset(asset_id, spec) for asset_id, spec in ASSETS.items()},
        "visualEvidence": check_visual_evidence(),
    }
    (OUT / "asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
