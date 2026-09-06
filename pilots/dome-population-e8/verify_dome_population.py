from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True

import bpy


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RENDERS = HERE / "renders"
BASE_SHA = "a9be388a3fe95a3228c638ed4afaf8a6ec6a7f5a"
SOURCE = ROOT / "assets/raw/plate-e8-bld-set.png"
ASSETS = {
    "orbital-canteen": {"pad": "tavern", "footprint": [5.2, 3.4]},
    "suit-fitter": {"pad": "general_store", "footprint": [4.8, 3.3]},
    "launch-works": {"pad": "orbital-pad-starboard", "footprint": [6.2, 6.2]},
    "he3-assay": {"pad": "assay_office", "footprint": [4.6, 3.4]},
    "mass-driver-dispatch": {"pad": "orbital-pad-port", "footprint": [5.6, 3.8]},
}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


glb = load("e8_population_glb_contract", ROOT / "assets/pilots/dredge-queen-3d/verify_dredge_queen.py")


def reexport(asset_id: str, blend: Path, destination: Path) -> dict:
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    assert [obj.name for obj in meshes] == [asset_id]
    assert not [obj for obj in bpy.data.objects if obj.type == "CAMERA"]
    assert not [obj for obj in bpy.data.objects if obj.type == "LIGHT"]
    assert not list(bpy.data.actions)
    bpy.ops.object.select_all(action="DESELECT")
    meshes[0].select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(
        filepath=str(destination.with_suffix("")),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_materials="EXPORT",
        export_morph=True,
    )
    return glb.contract(destination)


def main() -> None:
    RENDERS.mkdir(parents=True, exist_ok=True)
    evidence = {
        "baseSha": BASE_SHA,
        "sourcePlate": {str(SOURCE.relative_to(ROOT)): hashlib.sha256(SOURCE.read_bytes()).hexdigest()},
        "triangleBudgetPerBuilding": 15_000,
        "atlasLimit": [1024, 1024],
        "assets": {},
    }
    stable_keys = (
        "nodes", "nodeCount", "bindings", "nodeTransforms", "meshes", "meshNames", "primitives",
        "primitiveMaterials", "triangles", "morphTargets", "targetCounts", "materials",
        "materialTextureBindings", "materialContract", "textureSources", "images", "embeddedImages",
        "imageDimensions", "cameras", "lights", "animations", "bounds",
    )
    for asset_id, assignment in ASSETS.items():
        directory = ROOT / f"assets/pilots/{asset_id}-3d"
        production = glb.contract(directory / f"{asset_id}.glb")
        temporary = Path(f"/tmp/{asset_id}-reexport.glb")
        reproduced = reexport(asset_id, directory / f"{asset_id}.blend", temporary)
        footprint = assignment["footprint"]
        size = production["bounds"]["size"]
        # glTF is Y-up: X/Z are the footprint and Blender Z becomes Y.
        footprint_clearance = [round(footprint[0] - size[0], 6), round(footprint[1] - size[2], 6)]
        result = {
            "production": production,
            "reexported": reproduced,
            "byteIdentical": production["sha256"] == reproduced["sha256"],
            "semanticIdentical": {key: production[key] == reproduced[key] for key in stable_keys},
            "assignedPad": assignment["pad"],
            "canonicalFootprint": footprint,
            "footprintClearance": footprint_clearance,
        }
        evidence["assets"][asset_id] = result
        assert production["nodes"] == [asset_id]
        assert production["nodeCount"] == production["meshes"] == production["primitives"] == 1
        assert production["primitiveMaterials"] == [0]
        assert production["triangles"] <= 15_000
        assert production["materials"] == production["images"] == production["embeddedImages"] == 1
        assert production["imageDimensions"] == [[1024, 1024]]
        assert production["materialTextureBindings"] == [{"material": 0, "baseColorTexture": 0, "image": 0}]
        assert production["textureSources"] == [0]
        assert production["materialContract"] == [{
            "metallicFactor": 0,
            "roughnessFactor": 0.8999999761581421,
            "doubleSided": True,
            "hasBaseColorTexture": True,
            "hasEmissiveTexture": False,
            "emissiveFactor": [0.0, 0.0, 0.0],
        }]
        assert production["cameras"] == production["lights"] == production["animations"] == 0
        assert abs(production["bounds"]["min"][1]) < 0.001
        assert abs(production["bounds"]["center"][0]) < 0.001
        assert abs(production["bounds"]["center"][2]) < 0.001
        assert min(footprint_clearance) >= -0.001
        assert result["byteIdentical"] and all(result["semanticIdentical"].values())
        temporary.unlink(missing_ok=True)
    (RENDERS / "dome-population-asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({asset_id: {
        "triangles": item["production"]["triangles"],
        "sha256": item["production"]["sha256"],
        "footprintClearance": item["footprintClearance"],
        "byteIdentical": item["byteIdentical"],
    } for asset_id, item in evidence["assets"].items()}, indent=2))


if __name__ == "__main__":
    main()
