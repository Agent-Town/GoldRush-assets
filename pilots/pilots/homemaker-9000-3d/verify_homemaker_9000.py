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
BLEND = HERE / "homemaker-9000.blend"
GLB = HERE / "homemaker-9000.glb"
OUT = HERE / "renders"
REEXPORT = Path("/tmp/homemaker-9000-reexport.glb")
REFERENCE = ROOT / "assets/raw/plate-e6-boss-homemaker-9000.png"
STORYBOOK = ROOT / "lore/STORYBOOK.md"
EXPECTED_NODES = ["vac", "rack", "core"]
EXPECTED_MORPHS = {
    "vacMesh": ["Damage_DroppedVac"],
    "rackMesh": ["Damage_SpentRack"],
    "coreMesh": ["Damage_ChairPose"],
}
EXPECTED_BINDINGS = [
    {"node": "vac", "mesh": "vacMesh", "targets": ["Damage_DroppedVac"], "defaultWeights": [0.0]},
    {"node": "rack", "mesh": "rackMesh", "targets": ["Damage_SpentRack"], "defaultWeights": [0.0]},
    {"node": "core", "mesh": "coreMesh", "targets": ["Damage_ChairPose"], "defaultWeights": [0.0]},
]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


shared = load("homemaker_shared_verifier", ROOT / "assets/pilots/dredge-queen-3d/verify_dredge_queen.py")


def shape_bounds(obj: bpy.types.Object, key_name: str) -> dict[str, list[float]]:
    key = obj.data.shape_keys.key_blocks[key_name]
    return {
        "min": [round(min(vertex.co[axis] for vertex in key.data), 6) for axis in range(3)],
        "max": [round(max(vertex.co[axis] for vertex in key.data), 6) for axis in range(3)],
    }


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
    final_bounds = {obj.name: shape_bounds(obj, obj.data.shape_keys.key_blocks[1].name) for obj in meshes}
    core = bpy.data.objects["core"]
    chair_group = core.vertex_groups["ChairDebris"]
    chair_vertices = [
        vertex.index for vertex in core.data.vertices
        if any(item.group == chair_group.index for item in vertex.groups)
    ]
    core_keys = core.data.shape_keys.key_blocks
    basis_chair_span = max(core_keys["Basis"].data[index].co.x for index in chair_vertices) - min(core_keys["Basis"].data[index].co.x for index in chair_vertices)
    final_chair_span = max(core_keys["Damage_ChairPose"].data[index].co.x for index in chair_vertices) - min(core_keys["Damage_ChairPose"].data[index].co.x for index in chair_vertices)

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
    story_text = STORYBOOK.read_text()
    metrics = json.loads((OUT / "homemaker-9000-damage-metrics.json").read_text())
    evidence = {
        "blender": bpy.app.version_string,
        "baseSha": "f50cc240618ddc23b88efee1f27d4cf2035a04ab",
        "sourcePlate": {str(REFERENCE.relative_to(ROOT)): hashlib.sha256(REFERENCE.read_bytes()).hexdigest()},
        "storybook": {"path": str(STORYBOOK.relative_to(ROOT)), "sha256": hashlib.sha256(STORYBOOK.read_bytes()).hexdigest()},
        "damageImplementation": "one morph on each exact future component mesh; all three at weight 1 form the Act-3 chair state",
        "finalMorphBounds": final_bounds,
        "chairReveal": {"basisSpanX": round(basis_chair_span, 6), "finalSpanX": round(final_chair_span, 6)},
        "damageMetrics": metrics,
        "sourceScene": source_scene,
        "checked": checked,
        "reexported": exported,
        "byteIdentical": checked["sha256"] == exported["sha256"],
        "semanticIdentical": {key: checked[key] == exported[key] for key in stable},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "homemaker-9000-asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")

    assert "components: VAC / RACK / CORE" in story_text
    assert "Builds ONE CHAIR from debris, carefully. Sits." in story_text
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
        "metallicFactor": 0, "roughnessFactor": 0.8999999761581421, "doubleSided": True,
        "hasBaseColorTexture": True, "hasEmissiveTexture": False, "emissiveFactor": [0.0, 0.0, 0.0],
    }]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert abs(checked["bounds"]["size"][0] - 7.2) < 0.001
    assert abs(checked["bounds"]["min"][1]) < 0.001
    assert abs(checked["bounds"]["center"][0]) < 0.001 and abs(checked["bounds"]["center"][2]) < 0.001
    assert basis_chair_span < 0.05 and final_chair_span > 3.5
    assert all(bounds["min"][2] >= -0.001 for bounds in final_bounds.values())
    assert metrics["diffRatio16"] >= 0.07
    assert evidence["byteIdentical"] and all(evidence["semanticIdentical"].values())
    REEXPORT.unlink(missing_ok=True)
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
