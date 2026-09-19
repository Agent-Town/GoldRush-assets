from pathlib import Path
import hashlib, json, struct
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent / "dynamo-hall.glb"
BLEND = Path(__file__).resolve().parent / "dynamo-hall.blend"
ARTIFACTS = ROOT / "artifacts/town3d-dynamo-hall"
REEXPORT = ARTIFACTS / "dynamo-hall-reexport.glb"

def inspect(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    triangles = 0
    for obj in meshes:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh(); mesh.calc_loop_triangles(); triangles += len(mesh.loop_triangles); evaluated.to_mesh_clear()
    corners = [obj.matrix_world @ Vector(v) for obj in meshes for v in obj.bound_box]
    minimum = [min(v[i] for v in corners) for i in range(3)]; maximum = [max(v[i] for v in corners) for i in range(3)]
    materials = {m.name for o in meshes for m in o.data.materials if m}
    images = [i for i in bpy.data.images if i.source != "VIEWER"]
    with path.open("rb") as handle:
        handle.read(12); length, _ = struct.unpack("<II", handle.read(8)); document = json.loads(handle.read(length))
    material_contract = [{
        "metallic": entry.get("pbrMetallicRoughness", {}).get("metallicFactor", 1),
        "roughness": round(entry.get("pbrMetallicRoughness", {}).get("roughnessFactor", 1), 3),
        "emissiveTexture": "emissiveTexture" in entry,
    } for entry in document.get("materials", [])]
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size,
        "meshes": len(meshes), "primitives": sum(len(o.data.materials) for o in meshes), "triangles": triangles,
        "materials": len(materials), "images": len(images),
        "cameras": len([o for o in bpy.context.scene.objects if o.type == "CAMERA"]),
        "lights": len([o for o in bpy.context.scene.objects if o.type == "LIGHT"]),
        "animations": len(bpy.data.actions),
        "bounds": {"min": [round(v,3) for v in minimum], "max": [round(v,3) for v in maximum], "size": [round(maximum[i]-minimum[i],3) for i in range(3)]},
        "material": material_contract,
    }

def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    checked = inspect(SOURCE)
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    bpy.ops.object.select_all(action="DESELECT")
    for mesh in (obj for obj in bpy.data.objects if obj.type == "MESH"):
        mesh.select_set(True)
    bpy.context.view_layer.objects.active = next(obj for obj in bpy.data.objects if obj.type == "MESH")
    bpy.ops.export_scene.gltf(filepath=str(REEXPORT), export_format="GLB", use_selection=True, export_apply=True, export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT")
    reexported = inspect(REEXPORT)
    keys = ("meshes","primitives","triangles","materials","images","cameras","lights","animations","bounds")
    evidence = {"blender": bpy.app.version_string, "checked": checked, "reexported": reexported, "byteIdentical": checked["sha256"] == reexported["sha256"], "semanticIdentical": {k: checked[k] == reexported[k] for k in keys}}
    (ARTIFACTS / "asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (ARTIFACTS / "reexport-evidence.md").write_text(f"# Dynamo Hall re-export evidence\n\n- Blender: {bpy.app.version_string}\n- Checked SHA-256: `{checked['sha256']}` ({checked['bytes']} bytes)\n- Re-export SHA-256: `{reexported['sha256']}` ({reexported['bytes']} bytes)\n- Byte-identical: **{'yes' if evidence['byteIdentical'] else 'no'}**\n- Parsed contract identical: **{'yes' if all(evidence['semanticIdentical'].values()) else 'no'}**\n- Meshes/primitives/tris: {checked['meshes']}/{checked['primitives']}/{checked['triangles']}\n- Materials/images: {checked['materials']}/{checked['images']}\n- Bounds x/y/z: `{checked['bounds']['size']}`; min `{checked['bounds']['min']}`\n- Cameras/lights/animations: {checked['cameras']}/{checked['lights']}/{checked['animations']}\n")
    assert checked["meshes"] == checked["primitives"] == checked["materials"] == checked["images"] == 1
    assert checked["triangles"] <= 15000 and checked["bounds"]["size"][0] <= 5.5 and checked["bounds"]["size"][1] <= 3.5
    assert abs(checked["bounds"]["min"][2]) <= .001 and checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert checked["material"] == [{"metallic": 0, "roughness": .9, "emissiveTexture": False}]
    assert all(evidence["semanticIdentical"].values())
    print(json.dumps(evidence, indent=2))

if __name__ == "__main__": main()
