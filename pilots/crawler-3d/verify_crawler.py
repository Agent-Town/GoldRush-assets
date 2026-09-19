from pathlib import Path
import hashlib
import json
import math
import struct

import bpy


HERE = Path(__file__).resolve().parent
BLEND = HERE / "crawler.blend"
GLB = HERE / "crawler.glb"
OUT = HERE / "renders"
REEXPORT = Path("/tmp/crawler-reexport.glb")
EXPECTED_NODES = ["drain_mast", "tracks", "capacitor_bank"]
EXPECTED_MORPHS = {
    "drain_mastMesh": ["Damage_ToppledDrainMast"],
    "tracksMesh": ["Damage_ShatteredTracks"],
    "capacitor_bankMesh": ["Damage_RupturedCapacitorBank"],
}
EXPECTED_BINDINGS = [
    {
        "node": "drain_mast",
        "mesh": "drain_mastMesh",
        "targets": ["Damage_ToppledDrainMast"],
        "defaultWeights": [0.0],
    },
    {
        "node": "tracks",
        "mesh": "tracksMesh",
        "targets": ["Damage_ShatteredTracks"],
        "defaultWeights": [0.0],
    },
    {
        "node": "capacitor_bank",
        "mesh": "capacitor_bankMesh",
        "targets": ["Damage_RupturedCapacitorBank"],
        "defaultWeights": [0.0],
    },
]


def read_glb(path: Path) -> tuple[dict, bytes]:
    data = path.read_bytes()
    magic, version, total = struct.unpack_from("<4sII", data)
    assert magic == b"glTF" and version == 2 and total == len(data)
    json_length, json_kind = struct.unpack_from("<II", data, 12)
    assert json_kind == 0x4E4F534A
    document = json.loads(data[20:20 + json_length])
    binary_offset = 20 + json_length
    binary_length, binary_kind = struct.unpack_from("<II", data, binary_offset)
    assert binary_kind == 0x004E4942
    return document, data[binary_offset + 8:binary_offset + 8 + binary_length]


def image_dimensions(document: dict, binary: bytes) -> list[list[int]]:
    dimensions = []
    for image in document.get("images", []):
        view = document["bufferViews"][image["bufferView"]]
        start = view.get("byteOffset", 0)
        payload = binary[start:start + view["byteLength"]]
        assert payload[:8] == b"\x89PNG\r\n\x1a\n"
        dimensions.append(list(struct.unpack(">II", payload[16:24])))
    return dimensions


def contract(path: Path) -> dict:
    document, binary = read_glb(path)
    accessors = document.get("accessors", [])
    meshes = document.get("meshes", [])
    primitives = [(mesh, primitive) for mesh in meshes for primitive in mesh.get("primitives", [])]
    materials = document.get("materials", [])
    textures = document.get("textures", [])
    primitive_materials = [primitive.get("material") for _, primitive in primitives]
    material_texture_bindings = []
    for material_index, material in enumerate(materials):
        texture_index = material.get("pbrMetallicRoughness", {}).get("baseColorTexture", {}).get("index")
        image_index = textures[texture_index].get("source") if isinstance(texture_index, int) and texture_index < len(textures) else None
        material_texture_bindings.append(
            {"material": material_index, "baseColorTexture": texture_index, "image": image_index}
        )
    positions = [accessors[primitive["attributes"]["POSITION"]] for _, primitive in primitives]
    minimum = [min(item["min"][axis] for item in positions) for axis in range(3)]
    maximum = [max(item["max"][axis] for item in positions) for axis in range(3)]
    nodes = document.get("nodes", [])
    node_names = [node.get("name") for node in nodes if "mesh" in node]
    morphs = {mesh.get("name"): mesh.get("extras", {}).get("targetNames", []) for mesh in meshes}
    bindings = []
    transforms = {}
    for node in nodes:
        if "mesh" not in node:
            continue
        mesh = meshes[node["mesh"]]
        targets = mesh.get("extras", {}).get("targetNames", [])
        weights = node.get("weights", mesh.get("weights", [0.0] * len(targets)))
        bindings.append(
            {"node": node.get("name"), "mesh": mesh.get("name"), "targets": targets, "defaultWeights": weights}
        )
        transforms[node.get("name")] = {
            "translation": node.get("translation", [0.0, 0.0, 0.0]),
            "rotation": node.get("rotation", [0.0, 0.0, 0.0, 1.0]),
            "scale": node.get("scale", [1.0, 1.0, 1.0]),
            "matrix": node.get("matrix"),
        }
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
        "nodes": node_names,
        "nodeCount": len(nodes),
        "bindings": bindings,
        "nodeTransforms": transforms,
        "collectorAnchor": next((node.get("extras", {}).get("collectorAnchor") for node in nodes if node.get("name") == "drain_mast"), None),
        "meshes": len(meshes),
        "meshNames": [mesh.get("name") for mesh in meshes],
        "primitives": len(primitives),
        "primitiveMaterials": primitive_materials,
        "triangles": sum(accessors[primitive["indices"]]["count"] // 3 for _, primitive in primitives),
        "morphTargets": morphs,
        "targetCounts": {
            mesh.get("name"): sum(len(primitive.get("targets", [])) for primitive in mesh.get("primitives", []))
            for mesh in meshes
        },
        "materials": len(materials),
        "materialTextureBindings": material_texture_bindings,
        "textureSources": [texture.get("source") for texture in textures],
        "images": len(document.get("images", [])),
        "embeddedImages": sum("bufferView" in image for image in document.get("images", [])),
        "imageDimensions": image_dimensions(document, binary),
        "cameras": len(document.get("cameras", [])),
        "lights": len(document.get("extensions", {}).get("KHR_lights_punctual", {}).get("lights", [])),
        "animations": len(document.get("animations", [])),
        "bounds": {
            "min": [round(value, 6) for value in minimum],
            "max": [round(value, 6) for value in maximum],
            "size": [round(maximum[axis] - minimum[axis], 6) for axis in range(3)],
            "center": [round((maximum[axis] + minimum[axis]) * 0.5, 6) for axis in range(3)],
        },
    }


def main() -> None:
    OUT.mkdir(exist_ok=True)
    checked = contract(GLB)
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    mesh_objects = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    source_scene = {
        "meshObjects": [obj.name for obj in mesh_objects],
        "cameras": [obj.name for obj in bpy.data.objects if obj.type == "CAMERA"],
        "lights": [obj.name for obj in bpy.data.objects if obj.type == "LIGHT"],
        "actions": [action.name for action in bpy.data.actions],
    }
    assert sorted(source_scene["meshObjects"]) == sorted(EXPECTED_NODES)
    assert not source_scene["cameras"]
    assert not source_scene["lights"]
    assert not source_scene["actions"]
    mast = bpy.data.objects["drain_mast"]
    group = mast.vertex_groups["CollectorAnchor"].index
    indices = [v.index for v in mast.data.vertices if any(g.group == group for g in v.groups)]
    assert indices and set(checked["collectorAnchor"]) == {"intact", "damaged"}
    for state, key_name in (("intact", "Basis"), ("damaged", "Damage_ToppledDrainMast")):
        points = mast.data.shape_keys.key_blocks[key_name].data
        center = [sum(points[i].co[axis] for i in indices) / len(indices) for axis in range(3)]
        expected = [center[0], center[2], -center[1]]
        actual = checked["collectorAnchor"][state]
        assert len(actual) == 3 and all(math.isfinite(value) for value in actual)
        assert all(abs(a - b) < 1e-6 for a, b in zip(actual, expected)), (state, actual, expected)
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
        export_extras=True,
    )
    reexported = contract(REEXPORT)
    stable_keys = (
        "nodes",
        "nodeCount",
        "bindings",
        "nodeTransforms",
        "collectorAnchor",
        "meshes",
        "meshNames",
        "primitives",
        "primitiveMaterials",
        "triangles",
        "morphTargets",
        "targetCounts",
        "materials",
        "materialTextureBindings",
        "textureSources",
        "images",
        "embeddedImages",
        "imageDimensions",
        "cameras",
        "lights",
        "animations",
        "bounds",
    )
    evidence = {
        "blender": bpy.app.version_string,
        "sourcePlate": "assets/raw/plate-e3-boss-dynamo-crawler.png",
        "chosenLength": 3.20,
        "damageImplementation": "one morph target on each named component mesh",
        "runCamera": {"fovDegrees": 42, "offset": [0.0, 26.2, 18.3]},
        "sourceScene": source_scene,
        "checked": checked,
        "reexported": reexported,
        "byteIdentical": checked["sha256"] == reexported["sha256"],
        "semanticIdentical": {key: checked[key] == reexported[key] for key in stable_keys},
    }
    (OUT / "crawler-asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")

    assert checked["nodes"] == EXPECTED_NODES
    assert checked["nodeCount"] == 3
    assert checked["bindings"] == EXPECTED_BINDINGS
    assert all(
        transform
        == {
            "translation": [0.0, 0.0, 0.0],
            "rotation": [0.0, 0.0, 0.0, 1.0],
            "scale": [1.0, 1.0, 1.0],
            "matrix": None,
        }
        for transform in checked["nodeTransforms"].values()
    )
    assert checked["meshes"] == checked["primitives"] == 3
    assert checked["primitiveMaterials"] == [0, 0, 0]
    assert checked["triangles"] <= 12_000
    assert checked["morphTargets"] == EXPECTED_MORPHS
    assert all(count == 1 for count in checked["targetCounts"].values())
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["materialTextureBindings"] == [{"material": 0, "baseColorTexture": 0, "image": 0}]
    assert checked["textureSources"] == [0]
    assert checked["imageDimensions"] == [[1024, 1024]]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert abs(checked["bounds"]["size"][0] - 3.20) < 0.001
    # glTF is Y-up: Blender's base Z becomes accessor Y, and centered depth is Z.
    assert abs(checked["bounds"]["min"][1]) < 0.001
    assert abs(checked["bounds"]["center"][0]) < 0.001
    assert abs(checked["bounds"]["center"][2]) < 0.001
    assert evidence["byteIdentical"] and all(evidence["semanticIdentical"].values())
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
