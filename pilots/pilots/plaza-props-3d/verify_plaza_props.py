from pathlib import Path
import hashlib
import json
import struct
import tempfile

import bpy


ROOT = Path(__file__).resolve().parents[3]
SOURCE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = ROOT / "artifacts/town-model-audit"
EXPECTED = {
    "covered_wagon": [1.78, 1.438, 1.03],
    "water_trough": [1.64, 0.65, 0.76],
    "pan_monument": [2.085583, 1.999664, 1.52],
}


def glb(path):
    data = path.read_bytes()
    magic, version, total = struct.unpack_from("<4sII", data)
    assert magic == b"glTF" and version == 2 and total == len(data)
    json_length, json_kind = struct.unpack_from("<II", data, 12)
    assert json_kind == 0x4E4F534A
    json_end = 20 + json_length
    doc = json.loads(data[20:json_end])
    binary_length, binary_kind = struct.unpack_from("<II", data, json_end)
    assert binary_kind == 0x004E4942
    return data, doc, data[json_end + 8:json_end + 8 + binary_length]


def contract(path):
    data, doc, binary = glb(path)
    meshes = doc.get("meshes", [])
    primitives = [primitive for mesh in meshes for primitive in mesh.get("primitives", [])]
    accessors = doc.get("accessors", [])
    positions = [accessors[primitive["attributes"]["POSITION"]] for primitive in primitives]
    minimum = [min(position["min"][axis] for position in positions) for axis in range(3)]
    maximum = [max(position["max"][axis] for position in positions) for axis in range(3)]
    materials = doc.get("materials", [])
    images = doc.get("images", [])
    image_sizes = []
    for image in images:
        view = doc["bufferViews"][image["bufferView"]]
        start = view.get("byteOffset", 0)
        payload = binary[start:start + view["byteLength"]]
        assert payload[:8] == b"\x89PNG\r\n\x1a\n"
        image_sizes.append(list(struct.unpack(">II", payload[16:24])))
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "meshes": len(meshes),
        "primitives": len(primitives),
        "triangles": sum(accessors[primitive["indices"]]["count"] // 3 for primitive in primitives),
        "materials": len(materials),
        "textures": len(doc.get("textures", [])),
        "images": len(images),
        "embeddedImages": sum("bufferView" in image for image in images),
        "imageSizes": image_sizes,
        "cameras": len(doc.get("cameras", [])),
        "lights": len(doc.get("extensions", {}).get("KHR_lights_punctual", {}).get("lights", [])),
        "animations": len(doc.get("animations", [])),
        "transformedNodes": sum(
            any(transform in node for transform in ("matrix", "translation", "rotation", "scale"))
            for node in doc.get("nodes", [])
        ),
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


def assert_contract(name, checked, blend_meshes, blend_lights, blend_cameras, blend_actions):
    assert checked["meshes"] == checked["primitives"] == blend_meshes == 1
    assert checked["triangles"] <= 4_000
    assert checked["materials"] == checked["textures"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["imageSizes"] == [[256, 256]]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert checked["transformedNodes"] == 0
    assert blend_lights == blend_cameras == blend_actions == 0
    assert len(checked["materialContract"]) == 1
    material = checked["materialContract"][0]
    assert material["metallicFactor"] == 0
    assert abs(material["roughnessFactor"] - 0.9) <= 0.001
    assert material["hasBaseColorTexture"] and not material["hasEmissiveTexture"]
    assert material["emissiveFactor"] == [0, 0, 0]
    assert all(abs(actual - expected) <= 0.002 for actual, expected in zip(checked["bounds"]["size"], EXPECTED[name]))
    assert abs(checked["bounds"]["min"][1]) <= 0.001
    if name != "pan_monument":
        assert abs(checked["bounds"]["center"][0]) <= 0.001
        assert abs(checked["bounds"]["center"][2]) <= 0.001


def main():
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    evidence = {"blender": bpy.app.version_string, "assets": {}}
    for name in EXPECTED:
        checked_path = SOURCE_DIR / f"{name}.glb"
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE_DIR / f"{name}.blend"))
        meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
        blend_lights = sum(obj.type == "LIGHT" for obj in bpy.context.scene.objects)
        blend_cameras = sum(obj.type == "CAMERA" for obj in bpy.context.scene.objects)
        blend_actions = len(bpy.data.actions)
        assert len(meshes) == 1
        bpy.ops.object.select_all(action="DESELECT")
        meshes[0].select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        reexport_path = Path(tempfile.gettempdir()) / f"{name}-town-audit-reexport.glb"
        bpy.ops.export_scene.gltf(
            filepath=str(reexport_path), export_format="GLB", use_selection=True,
            export_apply=True, export_cameras=False, export_lights=False,
            export_animations=False, export_materials="EXPORT",
        )
        checked = contract(checked_path)
        reexported = contract(reexport_path)
        assert_contract(name, checked, len(meshes), blend_lights, blend_cameras, blend_actions)
        semantic_keys = (
            "meshes", "primitives", "triangles", "materials", "textures", "images",
            "embeddedImages", "imageSizes", "cameras", "lights", "animations", "transformedNodes", "bounds",
            "materialContract",
        )
        semantic_identical = all(checked[key] == reexported[key] for key in semantic_keys)
        byte_identical = checked["sha256"] == reexported["sha256"]
        assert semantic_identical and byte_identical
        evidence["assets"][name] = {
            "checked": checked,
            "reexported": reexported,
            "byteIdentical": byte_identical,
            "semanticIdentical": semantic_identical,
        }
    (ARTIFACT_DIR / "plaza-props-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
