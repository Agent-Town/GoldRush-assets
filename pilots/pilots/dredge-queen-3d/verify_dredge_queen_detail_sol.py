from pathlib import Path
import hashlib
import importlib.util
import json
import sys

import bpy


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BLEND = HERE / "dredge-queen-detail-sol.blend"
GLB = HERE / "dredge-queen-detail-sol.glb"
REEXPORT = Path("/tmp/dredge-queen-detail-sol-reexport.glb")
STATS = HERE / "renders/dredge-queen-detail-sol-stats.json"
EXPECTED = {
    "claw": "Damage_SlackClaw",
    "paddle_port": "Damage_BrokenPortPaddle",
    "paddle_starboard": "Damage_BrokenStarboardPaddle",
    "hold": "Damage_CrackedLootHold",
}

spec = importlib.util.spec_from_file_location("dredge_queen_detail_sol_verify_base", HERE / "verify_dredge_queen.py")
base = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = base
spec.loader.exec_module(base)


def main() -> None:
    checked = base.contract(GLB)
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    assert sorted(obj.name for obj in meshes) == sorted(EXPECTED)
    assert not [obj for obj in bpy.data.objects if obj.type in {"CAMERA", "LIGHT"}]
    assert not bpy.data.actions

    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
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
    reexported = base.contract(REEXPORT)
    stable_keys = (
        "nodes", "nodeCount", "bindings", "nodeTransforms", "meshes", "meshNames", "primitives",
        "primitiveMaterials", "triangles", "morphTargets", "targetCounts", "materials",
        "materialTextureBindings", "materialContract", "textureSources", "images", "embeddedImages",
        "imageDimensions", "cameras", "lights", "animations", "bounds",
    )
    evidence = {
        "model": str(GLB.relative_to(ROOT)),
        "blender": bpy.app.version_string,
        "sha256": hashlib.sha256(GLB.read_bytes()).hexdigest(),
        "bytes": GLB.stat().st_size,
        "triangles": checked["triangles"],
        "materials": checked["materials"],
        "drawCallsExpected": checked["primitives"],
        "atlasDimensions": checked["imageDimensions"],
        "bounds": checked["bounds"],
        "nodes": checked["nodes"],
        "bindings": checked["bindings"],
        "byteIdenticalReexport": checked["sha256"] == reexported["sha256"],
        "semanticIdentical": {key: checked[key] == reexported[key] for key in stable_keys},
    }
    STATS.parent.mkdir(exist_ok=True)
    STATS.write_text(json.dumps(evidence, indent=2) + "\n")

    assert set(checked["nodes"]) == set(EXPECTED)
    assert checked["nodeCount"] == checked["meshes"] == checked["primitives"] == 4
    assert 12_000 < checked["triangles"] <= 45_000
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["imageDimensions"] == [[2048, 2048]]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert abs(checked["bounds"]["size"][0] - 8.0) < 0.001
    assert abs(checked["bounds"]["min"][1]) < 0.001
    bindings = {binding["node"]: binding for binding in checked["bindings"]}
    for node, morph in EXPECTED.items():
        assert bindings[node]["targets"] == [morph]
        assert bindings[node]["defaultWeights"] == [0.0]
    assert evidence["byteIdenticalReexport"]
    assert all(evidence["semanticIdentical"].values())
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
