from pathlib import Path
import hashlib
import json
import struct

import bpy


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BLEND = HERE / "dredge-queen.blend"
GLB = HERE / "dredge-queen.glb"
OUT = HERE / "renders"
REEXPORT = Path("/tmp/dredge-queen-reexport.glb")
REFERENCE = ROOT / "assets/raw/boss-dredge-queen.png"
DAMAGE_REFERENCE = ROOT / "assets/raw/boss-dredge-queen-damage.png"
EXPECTED_NODES = ["claw", "paddle_port", "paddle_starboard", "hold"]
EXPECTED_MORPHS = {
    "clawMesh": ["Damage_SlackClaw"],
    "paddle_portMesh": ["Damage_BrokenPortPaddle"],
    "paddle_starboardMesh": ["Damage_BrokenStarboardPaddle"],
    "holdMesh": ["Damage_CrackedLootHold"],
}
EXPECTED_BINDINGS = [
    {"node": "claw", "mesh": "clawMesh", "targets": ["Damage_SlackClaw"], "defaultWeights": [0.0]},
    {"node": "paddle_port", "mesh": "paddle_portMesh", "targets": ["Damage_BrokenPortPaddle"], "defaultWeights": [0.0]},
    {"node": "paddle_starboard", "mesh": "paddle_starboardMesh", "targets": ["Damage_BrokenStarboardPaddle"], "defaultWeights": [0.0]},
    {"node": "hold", "mesh": "holdMesh", "targets": ["Damage_CrackedLootHold"], "defaultWeights": [0.0]},
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
    material_contract = []
    for material_index, material in enumerate(materials):
        pbr = material.get("pbrMetallicRoughness", {})
        texture_index = pbr.get("baseColorTexture", {}).get("index")
        image_index = textures[texture_index].get("source") if isinstance(texture_index, int) and texture_index < len(textures) else None
        material_texture_bindings.append({"material": material_index, "baseColorTexture": texture_index, "image": image_index})
        material_contract.append({
            "metallicFactor": pbr.get("metallicFactor", 1.0),
            "roughnessFactor": pbr.get("roughnessFactor", 1.0),
            "doubleSided": material.get("doubleSided", False),
            "hasBaseColorTexture": isinstance(texture_index, int),
            "hasEmissiveTexture": "emissiveTexture" in material,
            "emissiveFactor": material.get("emissiveFactor", [0.0, 0.0, 0.0]),
        })
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
        bindings.append({"node": node.get("name"), "mesh": mesh.get("name"), "targets": targets, "defaultWeights": weights})
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
        "materialContract": material_contract,
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
    reexported = contract(REEXPORT)
    stable_keys = (
        "nodes", "nodeCount", "bindings", "nodeTransforms", "meshes", "meshNames", "primitives",
        "primitiveMaterials", "triangles", "morphTargets", "targetCounts", "materials",
        "materialTextureBindings", "materialContract", "textureSources", "images", "embeddedImages",
        "imageDimensions", "cameras", "lights", "animations", "bounds",
    )
    evidence = {
        "blender": bpy.app.version_string,
        "sourcePlates": {
            str(REFERENCE.relative_to(ROOT)): hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
            str(DAMAGE_REFERENCE.relative_to(ROOT)): hashlib.sha256(DAMAGE_REFERENCE.read_bytes()).hexdigest(),
        },
        "chosenLength": 8.0,
        "runtimeComponentOffsets": {
            "claw": [-3.2, 0.0],
            "paddle_port": [-0.3, -2.4],
            "paddle_starboard": [-0.3, 2.4],
            "hold": [1.8, 0.0],
        },
        "damageImplementation": "one morph target on each of four named component meshes",
        "onTileEvidence": {
            "terrain": "assets/pilots/map-rebuild-spike/deepwater-claim-terrain.glb",
            "w5Anchor": [36.0, -20.0],
            "fovDegrees": 48,
            "productionOffsetDirection": [0.0, 26.2, 18.3],
        },
        "sourceScene": source_scene,
        "checked": checked,
        "reexported": reexported,
        "byteIdentical": checked["sha256"] == reexported["sha256"],
        "semanticIdentical": {key: checked[key] == reexported[key] for key in stable_keys},
    }
    (OUT / "dredge-queen-asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")

    assert checked["nodes"] == EXPECTED_NODES
    assert checked["nodeCount"] == 4
    assert checked["bindings"] == EXPECTED_BINDINGS
    assert all(
        transform == {
            "translation": [0.0, 0.0, 0.0],
            "rotation": [0.0, 0.0, 0.0, 1.0],
            "scale": [1.0, 1.0, 1.0],
            "matrix": None,
        }
        for transform in checked["nodeTransforms"].values()
    )
    assert checked["meshes"] == checked["primitives"] == 4
    assert checked["primitiveMaterials"] == [0, 0, 0, 0]
    assert checked["triangles"] <= 12_000
    assert checked["morphTargets"] == EXPECTED_MORPHS
    assert all(count == 1 for count in checked["targetCounts"].values())
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["materialTextureBindings"] == [{"material": 0, "baseColorTexture": 0, "image": 0}]
    assert checked["textureSources"] == [0]
    assert checked["imageDimensions"] == [[1024, 1024]]
    assert checked["materialContract"] == [{
        "metallicFactor": 0,
        "roughnessFactor": 0.8999999761581421,
        "doubleSided": True,
        "hasBaseColorTexture": True,
        "hasEmissiveTexture": False,
        "emissiveFactor": [0.0, 0.0, 0.0],
    }]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert abs(checked["bounds"]["size"][0] - 8.0) < 0.001
    # glTF is Y-up: Blender's base Z becomes accessor Y, centered depth becomes Z.
    assert abs(checked["bounds"]["min"][1]) < 0.001
    assert abs(checked["bounds"]["center"][0]) < 0.001
    assert abs(checked["bounds"]["center"][2]) < 0.001
    assert evidence["byteIdentical"] and all(evidence["semanticIdentical"].values())
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
