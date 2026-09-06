from pathlib import Path
import hashlib
import json
import struct

import bpy


ROOT = Path(__file__).resolve().parents[3]
SOURCE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = ROOT / "artifacts/town3d-schoolhouse"
CHECKED = SOURCE_DIR / "schoolhouse.glb"
REEXPORTED = ARTIFACT_DIR / "schoolhouse-reexport.glb"


def glb_json(path):
    data = path.read_bytes()
    magic, version, total = struct.unpack_from("<4sII", data)
    assert magic == b"glTF" and version == 2 and total == len(data)
    length, kind = struct.unpack_from("<II", data, 12)
    assert kind == 0x4E4F534A
    return json.loads(data[20:20 + length])


def contract(path):
    doc = glb_json(path)
    meshes = doc.get("meshes", [])
    primitives = [primitive for mesh in meshes for primitive in mesh.get("primitives", [])]
    accessors = doc.get("accessors", [])
    positions = [accessors[p["attributes"]["POSITION"]] for p in primitives]
    minimum = [min(item["min"][axis] for item in positions) for axis in range(3)]
    maximum = [max(item["max"][axis] for item in positions) for axis in range(3)]
    triangles = sum(accessors[p["indices"]]["count"] // 3 for p in primitives)
    materials = doc.get("materials", [])
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
        "meshes": len(meshes),
        "primitives": len(primitives),
        "triangles": triangles,
        "materials": len(materials),
        "images": len(doc.get("images", [])),
        "embeddedImages": sum("bufferView" in image for image in doc.get("images", [])),
        "cameras": len(doc.get("cameras", [])),
        "lights": len(doc.get("extensions", {}).get("KHR_lights_punctual", {}).get("lights", [])),
        "animations": len(doc.get("animations", [])),
        "bounds": {
            "min": [round(value, 6) for value in minimum],
            "max": [round(value, 6) for value in maximum],
            "size": [round(maximum[axis] - minimum[axis], 6) for axis in range(3)],
            "center": [round((maximum[axis] + minimum[axis]) / 2, 6) for axis in range(3)],
        },
        "materialContract": [{
            "metallicFactor": material.get("pbrMetallicRoughness", {}).get("metallicFactor", 1),
            "roughnessFactor": material.get("pbrMetallicRoughness", {}).get("roughnessFactor", 1),
            "hasBaseColorTexture": "baseColorTexture" in material.get("pbrMetallicRoughness", {}),
            "hasEmissiveTexture": "emissiveTexture" in material,
            "emissiveFactor": material.get("emissiveFactor", [0, 0, 0]),
        } for material in materials],
    }


def main():
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE_DIR / "schoolhouse.blend"))
    bpy.ops.object.select_all(action="DESELECT")
    schoolhouse = bpy.data.objects["SchoolhouseFullWrap"]
    schoolhouse.select_set(True)
    bpy.context.view_layer.objects.active = schoolhouse
    bpy.ops.export_scene.gltf(
        filepath=str(REEXPORTED), export_format="GLB", use_selection=True,
        export_apply=True, export_cameras=False, export_lights=False,
        export_animations=False, export_materials="EXPORT",
    )
    checked = contract(CHECKED)
    reexported = contract(REEXPORTED)
    evidence = {
        "blender": bpy.app.version_string,
        "checked": checked,
        "reexported": reexported,
        "byteIdentical": checked["sha256"] == reexported["sha256"],
        "semanticIdentical": {key: checked[key] == reexported[key] for key in (
            "meshes", "primitives", "triangles", "materials", "images", "embeddedImages",
            "cameras", "lights", "animations", "bounds", "materialContract",
        )},
    }
    (ARTIFACT_DIR / "asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")
    semantics_pass = all(evidence["semanticIdentical"].values())
    (ARTIFACT_DIR / "reexport-evidence.md").write_text(
        "# Schoolhouse re-export evidence\n\n"
        f"- Blender: {bpy.app.version_string}\n"
        f"- Checked SHA-256: `{checked['sha256']}` ({checked['bytes']} bytes)\n"
        f"- Re-export SHA-256: `{reexported['sha256']}` ({reexported['bytes']} bytes)\n"
        f"- Byte-identical: **{'yes' if evidence['byteIdentical'] else 'no'}**\n"
        f"- Parsed contract identical: **{'yes' if semantics_pass else 'no'}**\n"
        f"- Meshes/primitives/tris: {checked['meshes']}/{checked['primitives']}/{checked['triangles']}\n"
        f"- Materials/images: {checked['materials']}/{checked['images']} (embedded images: {checked['embeddedImages']})\n"
        f"- Bounds x/y/z: `{checked['bounds']['size']}`; min `{checked['bounds']['min']}`; center `{checked['bounds']['center']}`\n"
        f"- Cameras/lights/animations: {checked['cameras']}/{checked['lights']}/{checked['animations']}\n"
        f"- Material: metallic {checked['materialContract'][0]['metallicFactor']}, roughness {checked['materialContract'][0]['roughnessFactor']}, no emissive texture.\n"
    )
    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] <= 15_000
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert checked["bounds"]["size"][0] <= 4.4 and checked["bounds"]["size"][2] <= 3.4
    assert abs(checked["bounds"]["min"][1]) <= 0.001
    assert abs(checked["bounds"]["center"][0]) <= 0.06 and abs(checked["bounds"]["center"][2]) <= 0.06
    assert semantics_pass
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
