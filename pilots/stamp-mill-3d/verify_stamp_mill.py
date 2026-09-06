from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "assets/pilots/schoolhouse-3d/verify_schoolhouse.py"
spec = importlib.util.spec_from_file_location("town3d_verify", SOURCE)
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)
verify.SOURCE_DIR = Path(__file__).resolve().parent
verify.ARTIFACT_DIR = ROOT / "artifacts/town3d-stamp-mill"
verify.CHECKED = verify.SOURCE_DIR / "stamp-mill.glb"
verify.REEXPORTED = verify.ARTIFACT_DIR / "stamp-mill-reexport.glb"


def main():
    verify.ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    import bpy
    bpy.ops.wm.open_mainfile(filepath=str(verify.SOURCE_DIR / "stamp-mill.blend"))
    bpy.ops.object.select_all(action="DESELECT")
    model = bpy.data.objects["StampMillFullWrap"]
    model.select_set(True)
    bpy.context.view_layer.objects.active = model
    bpy.ops.export_scene.gltf(filepath=str(verify.REEXPORTED), export_format="GLB", use_selection=True, export_apply=True, export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT")
    checked, reexported = verify.contract(verify.CHECKED), verify.contract(verify.REEXPORTED)
    keys = ("meshes", "primitives", "triangles", "materials", "images", "embeddedImages", "cameras", "lights", "animations", "bounds", "materialContract")
    semantic = all(checked[key] == reexported[key] for key in keys)
    import json
    evidence = {"blender": bpy.app.version_string, "checked": checked, "reexported": reexported, "byteIdentical": checked["sha256"] == reexported["sha256"], "semanticIdentical": semantic}
    (verify.ARTIFACT_DIR / "asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (verify.ARTIFACT_DIR / "reexport-evidence.md").write_text(
        "# Stamp Mill re-export evidence\n\n"
        f"- Blender: {bpy.app.version_string}\n- Checked SHA-256: `{checked['sha256']}` ({checked['bytes']} bytes)\n"
        f"- Re-export SHA-256: `{reexported['sha256']}` ({reexported['bytes']} bytes)\n"
        f"- Byte-identical: **{'yes' if evidence['byteIdentical'] else 'no'}**\n- Parsed contract identical: **{'yes' if semantic else 'no'}**\n"
        f"- Meshes/primitives/tris: {checked['meshes']}/{checked['primitives']}/{checked['triangles']}\n"
        f"- Materials/images: {checked['materials']}/{checked['images']} (embedded: {checked['embeddedImages']})\n"
        f"- Bounds x/y/z: `{checked['bounds']['size']}`; min `{checked['bounds']['min']}`; center `{checked['bounds']['center']}`\n"
        f"- Cameras/lights/animations: {checked['cameras']}/{checked['lights']}/{checked['animations']}\n"
    )
    assert checked["meshes"] == checked["primitives"] == 1 and checked["triangles"] <= 15_000
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["bounds"]["size"][0] <= 6.2 and checked["bounds"]["size"][2] <= 1.65
    assert abs(checked["bounds"]["min"][1]) <= 0.001 and semantic


if __name__ == "__main__":
    main()
