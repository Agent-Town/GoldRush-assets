from __future__ import annotations

from pathlib import Path
import importlib.util
import json
import sys

sys.dont_write_bytecode = True

import bpy


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BLEND = HERE / "salvage-claw-detail-sol.blend"
GLB = HERE / "salvage-claw-detail-sol.glb"
OUT = HERE / "renders"
REEXPORT = Path("/tmp/salvage-claw-detail-sol-reexport.glb")
EXPECTED_NODES = ["winch", "anchor_feet", "crown"]
EXPECTED_MORPHS = {
    "winchMesh": ["Landing_SprungWinch"],
    "anchor_feetMesh": ["Landing_SettledAnchorFeet"],
    "crownMesh": ["Landing_DarkCrown"],
}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


shared = load("salvage_claw_detail_sol_verify_shared", ROOT / "assets/pilots/dredge-queen-3d/verify_dredge_queen.py")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    checked = shared.contract(GLB)
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    mesh_objects = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    source_scene = {
        "meshObjects": [obj.name for obj in mesh_objects],
        "cameras": [obj.name for obj in bpy.data.objects if obj.type == "CAMERA"],
        "lights": [obj.name for obj in bpy.data.objects if obj.type == "LIGHT"],
        "actions": [action.name for action in bpy.data.actions],
    }
    assert sorted(source_scene["meshObjects"]) == sorted(EXPECTED_NODES)
    assert not source_scene["cameras"] and not source_scene["lights"] and not source_scene["actions"]

    bpy.ops.object.select_all(action="DESELECT")
    for obj in mesh_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objects[0]
    bpy.ops.export_scene.gltf(
        filepath=str(REEXPORT.with_suffix("")),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_materials="EXPORT",
        export_morph=True,
    )
    reexported = shared.contract(REEXPORT)
    stable_keys = (
        "nodes", "nodeCount", "bindings", "nodeTransforms", "meshes", "meshNames", "primitives",
        "primitiveMaterials", "triangles", "morphTargets", "targetCounts", "materials",
        "materialTextureBindings", "materialContract", "textureSources", "images", "embeddedImages",
        "imageDimensions", "cameras", "lights", "animations", "bounds",
    )
    evidence = {
        "blender": bpy.app.version_string,
        "sourceScene": source_scene,
        "checked": checked,
        "reexported": reexported,
        "byteIdentical": checked["sha256"] == reexported["sha256"],
        "semanticIdentical": {key: checked[key] == reexported[key] for key in stable_keys},
    }
    (OUT / "salvage-claw-detail-sol-stats.json").write_text(json.dumps(evidence, indent=2) + "\n")

    assert checked["nodes"] == EXPECTED_NODES
    assert checked["nodeCount"] == checked["meshes"] == checked["primitives"] == 3
    assert checked["morphTargets"] == EXPECTED_MORPHS
    assert all(count == 1 for count in checked["targetCounts"].values())
    assert 10_164 < checked["triangles"] <= 45_000
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["primitiveMaterials"] == [0, 0, 0]
    assert checked["imageDimensions"] == [[2048, 2048]]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert abs(checked["bounds"]["size"][0] - 11.4) < 0.001
    assert abs(checked["bounds"]["min"][1]) < 0.001
    assert abs(checked["bounds"]["center"][0]) < 0.001
    assert abs(checked["bounds"]["center"][2]) < 0.001
    assert evidence["byteIdentical"] and all(evidence["semanticIdentical"].values())
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
