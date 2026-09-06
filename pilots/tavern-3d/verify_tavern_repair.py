from pathlib import Path
import hashlib
import json
import struct

import bpy


ROOT = Path(__file__).resolve().parent
BLEND = ROOT / "town-v3-tavern.blend"
GLB = ROOT / "town-v3-tavern.glb"
OUT = ROOT / "renders"
REEXPORT = Path("/tmp/town-v3-tavern-wave3-reexport.glb")
EXPECTED_SIZE = (4.229571, 3.960802, 3.349)


def read_glb(path: Path) -> tuple[dict, bytes]:
    data = path.read_bytes()
    magic, version, total = struct.unpack_from("<4sII", data)
    assert magic == b"glTF" and version == 2 and total == len(data)
    json_length, json_kind = struct.unpack_from("<II", data, 12)
    assert json_kind == 0x4E4F534A
    doc = json.loads(data[20:20 + json_length])
    binary_offset = 20 + json_length
    binary_length, binary_kind = struct.unpack_from("<II", data, binary_offset)
    assert binary_kind == 0x004E4942
    return doc, data[binary_offset + 8:binary_offset + 8 + binary_length]


def contract(path: Path) -> dict:
    doc, binary = read_glb(path)
    primitives = [primitive for mesh in doc.get("meshes", []) for primitive in mesh.get("primitives", [])]
    accessors = doc.get("accessors", [])
    positions = [accessors[primitive["attributes"]["POSITION"]] for primitive in primitives]
    minimum = [min(item["min"][axis] for item in positions) for axis in range(3)]
    maximum = [max(item["max"][axis] for item in positions) for axis in range(3)]
    materials = doc.get("materials", [])
    dimensions = []
    for image in doc.get("images", []):
        view = doc["bufferViews"][image["bufferView"]]
        start = view.get("byteOffset", 0)
        payload = binary[start:start + view["byteLength"]]
        dimensions.append(list(struct.unpack(">II", payload[16:24])))
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
        "meshes": len(doc.get("meshes", [])),
        "primitives": len(primitives),
        "triangles": sum(accessors[primitive["indices"]]["count"] // 3 for primitive in primitives),
        "materials": len(materials),
        "images": len(doc.get("images", [])),
        "embeddedImages": sum("bufferView" in image for image in doc.get("images", [])),
        "imageDimensions": dimensions,
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


def main() -> None:
    OUT.mkdir(exist_ok=True)
    checked = contract(GLB)
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    tavern = bpy.data.objects["TownTavernFullWrap"]
    bpy.ops.object.select_all(action="DESELECT")
    tavern.select_set(True)
    bpy.context.view_layer.objects.active = tavern
    bpy.ops.export_scene.gltf(
        filepath=str(REEXPORT), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT",
    )
    reexported = contract(REEXPORT)
    keys = ("meshes", "primitives", "triangles", "materials", "images", "embeddedImages", "imageDimensions", "cameras", "lights", "animations", "bounds", "materialContract")
    evidence = {
        "blender": bpy.app.version_string,
        "repairSource": "tavern-2-fullwrap.blend",
        "baseline": {"commit": "1281a8f1661b500ef4df79dc6201437b53bbee76", "sha256": "75b8e5fe7d520adc1266698ab873abf2ba21a81890871815d237a30472f304bd"},
        "checked": checked,
        "reexported": reexported,
        "byteIdentical": checked["sha256"] == reexported["sha256"],
        "semanticIdentical": {key: checked[key] == reexported[key] for key in keys},
    }
    (OUT / "wave3-asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")

    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] <= 15_000
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["imageDimensions"] == [[1024, 1024]]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert all(abs(checked["bounds"]["size"][axis] - EXPECTED_SIZE[axis]) < 0.002 for axis in range(3))
    assert abs(checked["bounds"]["min"][1]) < 0.001
    assert abs(checked["bounds"]["center"][0]) < 0.001 and abs(checked["bounds"]["center"][2]) < 0.001
    material = checked["materialContract"][0]
    assert material["metallicFactor"] == 0 and material["roughnessFactor"] >= 0.899
    assert material["hasBaseColorTexture"] and not material["hasEmissiveTexture"]
    assert evidence["byteIdentical"] and all(evidence["semanticIdentical"].values())
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
