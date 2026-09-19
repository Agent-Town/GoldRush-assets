from pathlib import Path
import hashlib
import json
import struct

import bpy


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts/town-e2-variants"
ASSETS = {
    "tavern": {
        "baseBlend": ROOT / "assets/pilots/tavern-3d/town-v3-tavern.blend",
        "baseGlb": ROOT / "assets/pilots/tavern-3d/town-v3-tavern.glb",
        "variantBlend": ROOT / "assets/pilots/tavern-3d/tavern.e2.blend",
        "variantGlb": ROOT / "assets/pilots/tavern-3d/tavern.e2.glb",
        "object": "TownTavernE2",
        "anchors": ["steam_anchor_1", "steam_anchor_2"],
        "baseBlendSha": "b81ef19a24661c3ea97feb3b7f75caceef5599954d6462b1bbd2ab6085ade2fe",
        "baseGlbSha": "edec4934d6d956170078b521fe526ccadcde015567094aec59001e2d4b71b90d",
    },
    "claim_office": {
        "baseBlend": ROOT / "assets/pilots/claim-office-3d/claim-office.blend",
        "baseGlb": ROOT / "assets/pilots/claim-office-3d/claim-office.glb",
        "variantBlend": ROOT / "assets/pilots/claim-office-3d/claim-office.e2.blend",
        "variantGlb": ROOT / "assets/pilots/claim-office-3d/claim-office.e2.glb",
        "object": "ClaimOfficeE2",
        "anchors": ["steam_anchor_1", "steam_anchor_2"],
        "baseBlendSha": "46a2f73fb7a82678292760551e466cedd5ec94639ed0e31cc3cf3a3d5ee8e817",
        "baseGlbSha": "b2a23b06c7cb6822166dceff2a02f410f125fac8fe1909d99ec0c8489f1e104b",
    },
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_glb(path):
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


def contract(path):
    doc, binary = read_glb(path)
    primitives = [primitive for mesh in doc.get("meshes", []) for primitive in mesh.get("primitives", [])]
    accessors = doc.get("accessors", [])
    positions = [accessors[primitive["attributes"]["POSITION"]] for primitive in primitives]
    minimum = [min(item["min"][axis] for item in positions) for axis in range(3)]
    maximum = [max(item["max"][axis] for item in positions) for axis in range(3)]
    materials = doc.get("materials", [])
    anchors = [
        {
            "name": node["name"],
            "translation": [round(value, 6) for value in node.get("translation", [0, 0, 0])],
        }
        for node in doc.get("nodes", [])
        if node.get("name", "").startswith(("steam_anchor_", "arc_anchor_")) and "mesh" not in node
    ]
    dimensions = []
    for image in doc.get("images", []):
        view = doc["bufferViews"][image["bufferView"]]
        start = view.get("byteOffset", 0)
        payload = binary[start:start + view["byteLength"]]
        dimensions.append(list(struct.unpack(">II", payload[16:24])))
    return {
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "meshes": len(doc.get("meshes", [])),
        "primitives": len(primitives),
        "nodes": [node.get("name", "") for node in doc.get("nodes", [])],
        "anchors": anchors,
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


def export_saved_blend(spec, output):
    bpy.ops.wm.open_mainfile(filepath=str(spec["variantBlend"]))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    anchors = sorted(
        (obj for obj in bpy.data.objects
         if obj.type == "EMPTY" and obj.name.startswith(("steam_anchor_", "arc_anchor_"))),
        key=lambda obj: obj.name,
    )
    assert len(meshes) == 1 and meshes[0].name == spec["object"]
    assert [anchor.name for anchor in anchors] == spec["anchors"]
    assert not [obj for obj in bpy.data.objects if obj.type in {"CAMERA", "LIGHT"}]
    bpy.ops.object.select_all(action="DESELECT")
    meshes[0].select_set(True)
    for anchor in anchors:
        anchor.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(
        filepath=str(output), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False,
        export_materials="EXPORT",
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    evidence = {"blender": bpy.app.version_string, "variants": {}}
    for asset_id, spec in ASSETS.items():
        assert sha256(spec["baseBlend"]) == spec["baseBlendSha"]
        assert sha256(spec["baseGlb"]) == spec["baseGlbSha"]
        base = contract(spec["baseGlb"])
        checked = contract(spec["variantGlb"])
        reexport_path = Path("/tmp") / f"{spec['variantGlb'].stem}-wave7-reexport.glb"
        export_saved_blend(spec, reexport_path)
        reexported = contract(reexport_path)
        keys = (
            "meshes", "primitives", "nodes", "anchors", "triangles", "materials", "images",
            "embeddedImages", "imageDimensions", "cameras", "lights", "animations",
            "bounds", "materialContract",
        )
        item = {
            "baseIntegrity": {
                "blendSha256": sha256(spec["baseBlend"]),
                "glbSha256": sha256(spec["baseGlb"]),
            },
            "base": base,
            "checked": checked,
            "reexported": reexported,
            "byteIdentical": checked["sha256"] == reexported["sha256"],
            "semanticIdentical": {key: checked[key] == reexported[key] for key in keys},
            "sameEnvelopeAsBase": checked["bounds"] == base["bounds"],
        }
        material = checked["materialContract"][0]
        assert checked["meshes"] == checked["primitives"] == 1
        assert [anchor["name"] for anchor in checked["anchors"]] == spec["anchors"]
        assert checked["triangles"] <= 15_000
        assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
        assert checked["imageDimensions"] == [[1024, 1024]]
        assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
        assert abs(checked["bounds"]["min"][1]) < 0.001
        assert material["metallicFactor"] == 0 and material["roughnessFactor"] >= 0.899
        assert material["hasBaseColorTexture"] and not material["hasEmissiveTexture"]
        assert item["sameEnvelopeAsBase"]
        assert item["byteIdentical"] and all(item["semanticIdentical"].values())
        evidence["variants"][asset_id] = item
    (OUT / "asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
