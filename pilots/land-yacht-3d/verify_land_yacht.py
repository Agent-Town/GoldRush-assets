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
BLEND = HERE / "land-yacht.blend"
GLB = HERE / "land-yacht.glb"
OUT = HERE / "renders"
REEXPORT = Path("/tmp/land-yacht-reexport.glb")
REFERENCE = ROOT / "assets/raw/boss-land-yacht.png"
DAMAGE_REFERENCE = ROOT / "assets/raw/boss-land-yacht-damage.png"
SYSTEM = ROOT / "src/systems/LandYachtBossSystem.ts"
EXPECTED_NODES = ["wheels", "crane", "wheelhouse"]
EXPECTED_MORPHS = {
    "wheelsMesh": ["Damage_BeachedWheels"],
    "craneMesh": ["Damage_SlackCrane"],
    "wheelhouseMesh": ["Damage_CrackedWheelhouse"],
}
EXPECTED_BINDINGS = [
    {"node": "wheels", "mesh": "wheelsMesh", "targets": ["Damage_BeachedWheels"], "defaultWeights": [0.0]},
    {"node": "crane", "mesh": "craneMesh", "targets": ["Damage_SlackCrane"], "defaultWeights": [0.0]},
    {"node": "wheelhouse", "mesh": "wheelhouseMesh", "targets": ["Damage_CrackedWheelhouse"], "defaultWeights": [0.0]},
]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


shared = load("land_yacht_shared_verifier", ROOT / "assets/pilots/dredge-queen-3d/verify_dredge_queen.py")


def main() -> None:
    checked = shared.contract(GLB)
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    source_scene = {
        "meshObjects": [obj.name for obj in meshes],
        "cameras": [obj.name for obj in bpy.data.objects if obj.type == "CAMERA"],
        "lights": [obj.name for obj in bpy.data.objects if obj.type == "LIGHT"],
        "actions": [action.name for action in bpy.data.actions],
    }
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(
        filepath=str(REEXPORT.with_suffix("")), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT", export_morph=True,
    )
    exported = shared.contract(REEXPORT)
    stable = (
        "nodes", "nodeCount", "bindings", "nodeTransforms", "meshes", "meshNames", "primitives",
        "primitiveMaterials", "triangles", "morphTargets", "targetCounts", "materials",
        "materialTextureBindings", "materialContract", "textureSources", "images", "embeddedImages",
        "imageDimensions", "cameras", "lights", "animations", "bounds",
    )
    system_text = SYSTEM.read_text()
    evidence = {
        "blender": bpy.app.version_string,
        "baseSha": "d41ab98ce0d7fbc48bb01e8e87c92c61f148de2d",
        "sourcePlates": {
            str(REFERENCE.relative_to(ROOT)): hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
            str(DAMAGE_REFERENCE.relative_to(ROOT)): hashlib.sha256(DAMAGE_REFERENCE.read_bytes()).hexdigest(),
        },
        "runtimeSystem": {"path": str(SYSTEM.relative_to(ROOT)), "sha256": hashlib.sha256(SYSTEM.read_bytes()).hexdigest(),
                          "componentIds": EXPECTED_NODES},
        "damageImplementation": "one morph target on each exact live component mesh",
        "chosenLength": 9.4,
        "sourceScene": source_scene,
        "checked": checked,
        "reexported": exported,
        "byteIdentical": checked["sha256"] == exported["sha256"],
        "semanticIdentical": {key: checked[key] == exported[key] for key in stable},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "land-yacht-asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")

    assert "const COMPONENT_IDS = ['wheels', 'crane', 'wheelhouse'] as const;" in system_text
    assert sorted(source_scene["meshObjects"]) == sorted(EXPECTED_NODES)
    assert not source_scene["cameras"] and not source_scene["lights"] and not source_scene["actions"]
    assert checked["nodes"] == EXPECTED_NODES and checked["nodeCount"] == 3
    assert checked["bindings"] == EXPECTED_BINDINGS
    assert all(transform == {
        "translation": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0, 1.0],
        "scale": [1.0, 1.0, 1.0], "matrix": None,
    } for transform in checked["nodeTransforms"].values())
    assert checked["meshes"] == checked["primitives"] == 3
    assert checked["primitiveMaterials"] == [0, 0, 0]
    assert checked["triangles"] <= 12_000
    assert checked["morphTargets"] == EXPECTED_MORPHS
    assert all(count == 1 for count in checked["targetCounts"].values())
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["materialTextureBindings"] == [{"material": 0, "baseColorTexture": 0, "image": 0}]
    assert checked["textureSources"] == [0] and checked["imageDimensions"] == [[1024, 1024]]
    assert checked["materialContract"] == [{
        "metallicFactor": 0.3499999940395355, "roughnessFactor": 0.6499999761581421, "doubleSided": True,
        "hasBaseColorTexture": True, "hasEmissiveTexture": False, "emissiveFactor": [0.0, 0.0, 0.0],
    }]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert abs(checked["bounds"]["size"][0] - 9.4) < 0.001
    assert abs(checked["bounds"]["min"][1]) < 0.001
    assert abs(checked["bounds"]["center"][0]) < 0.001 and abs(checked["bounds"]["center"][2]) < 0.001
    assert evidence["byteIdentical"] and all(evidence["semanticIdentical"].values())
    REEXPORT.unlink(missing_ok=True)
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
