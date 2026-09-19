from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import math
import struct
import sys

sys.dont_write_bytecode = True

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[3]
SOURCE_DIR = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/town-plate-3d"
BLEND = SOURCE_DIR / "town-plate.blend"
GLB = SOURCE_DIR / "town-plate.glb"
CHECKED = ARTIFACTS / "town-plate-reexport-current.glb"
PAN_GLB = ROOT / "assets/pilots/plaza-props-3d/pan_monument.glb"
PAN_CHECKED = ARTIFACTS / "pan-monument-checked.glb"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_glb(path: Path) -> tuple[dict, bytes]:
    data = path.read_bytes()
    magic, version, total = struct.unpack_from("<4sII", data, 0)
    assert magic == b"glTF" and version == 2 and total == len(data)
    cursor = 12
    document = None
    binary = b""
    while cursor < len(data):
        length, kind = struct.unpack_from("<II", data, cursor)
        cursor += 8
        payload = data[cursor:cursor + length]
        cursor += length
        if kind == 0x4E4F534A:
            document = json.loads(payload)
        elif kind == 0x004E4942:
            binary = payload
    assert document is not None
    return document, binary


def embedded_png_dimensions(document: dict, binary: bytes) -> list[list[int]]:
    dimensions = []
    for image in document.get("images", []):
        if image.get("mimeType") != "image/png" or "bufferView" not in image:
            continue
        view = document["bufferViews"][image["bufferView"]]
        start = view.get("byteOffset", 0)
        payload = binary[start:start + view["byteLength"]]
        assert payload[:8] == b"\x89PNG\r\n\x1a\n"
        width, height = struct.unpack(">II", payload[16:24])
        dimensions.append([width, height])
    return dimensions


def glb_contract(path: Path) -> dict:
    document, binary = parse_glb(path)
    accessors = document.get("accessors", [])
    primitives = [primitive for mesh in document.get("meshes", []) for primitive in mesh.get("primitives", [])]
    positions = [accessors[primitive["attributes"]["POSITION"]] for primitive in primitives]
    minimum = [min(accessor["min"][axis] for accessor in positions) for axis in range(3)]
    maximum = [max(accessor["max"][axis] for accessor in positions) for axis in range(3)]
    materials = document.get("materials", [])
    images = document.get("images", [])
    return {
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "meshes": len(document.get("meshes", [])),
        "primitives": len(primitives),
        "triangles": sum(accessors[primitive["indices"]]["count"] // 3 for primitive in primitives),
        "materials": len(materials),
        "textures": len(document.get("textures", [])),
        "images": len(images),
        "embeddedImages": sum("bufferView" in image for image in images),
        "imageMimeTypes": [image.get("mimeType") for image in images],
        "imageDimensions": embedded_png_dimensions(document, binary),
        "cameras": len(document.get("cameras", [])),
        "lights": len(document.get("extensions", {}).get("KHR_lights_punctual", {}).get("lights", [])),
        "animations": len(document.get("animations", [])),
        "bounds": {
            "min": [round(value, 6) for value in minimum],
            "max": [round(value, 6) for value in maximum],
            "size": [round(maximum[axis] - minimum[axis], 6) for axis in range(3)],
            "center": [round((maximum[axis] + minimum[axis]) * 0.5, 6) for axis in range(3)],
        },
        "materialContract": [
            {
                "metallicFactor": material.get("pbrMetallicRoughness", {}).get("metallicFactor", 1),
                "roughnessFactor": material.get("pbrMetallicRoughness", {}).get("roughnessFactor", 1),
                "hasBaseColorTexture": "baseColorTexture" in material.get("pbrMetallicRoughness", {}),
                "hasEmissiveTexture": "emissiveTexture" in material,
                "emissiveFactor": material.get("emissiveFactor", [0, 0, 0]),
            }
            for material in materials
        ],
    }


def load_builder():
    spec = importlib.util.spec_from_file_location("town_plate_builder", SOURCE_DIR / "build_town_plate.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def realized_flat_walk() -> dict:
    builder = load_builder()
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    plate = bpy.data.objects["TownPlate"]
    assert plate.location.length <= 1e-9
    bvh = BVHTree.FromObject(plate, bpy.context.evaluated_depsgraph_get())

    def height(point) -> float:
        hit, _normal, _face, _distance = bvh.ray_cast(Vector((point.x, point.y, 8.0)), Vector((0.0, 0.0, -1.0)), 20.0)
        if hit is None:
            raise RuntimeError(f"No plate below {point}")
        return float(hit.z)

    routes = {}
    all_heights = []
    for route_id, points, closed in [
        ("ring-road", builder.RING_ROUTE, True),
        *[(route_id, points, False) for route_id, points in builder.RADIAL_ROUTES.items()],
    ]:
        values = [height(point) for point in builder.route_sample_points(points, closed)]
        all_heights.extend(values)
        routes[route_id] = {
            "samples": len(values),
            "min": min(values),
            "max": max(values),
            "maxAbs": max(abs(value) for value in values),
        }

    plaza_points = [
        builder.Point(x * 0.2, y * 0.2)
        for x in range(-16, 17)
        for y in range(-16, 17)
        if (x * 0.2) ** 2 + (y * 0.2) ** 2 <= builder.PLAZA_CLEAR_RADIUS**2
    ]
    plaza_values = [height(point) for point in plaza_points]

    pads = {}
    for slot in [*builder.SLOTS, builder.DYNAMO_SLOT]:
        theta = builder.slot_angle(slot)
        values = []
        for local_x in [(-0.5 + index / 8.0) * slot.width for index in range(9)]:
            for local_y in [(-0.5 + index / 6.0) * slot.depth for index in range(7)]:
                point = builder.Point(
                    slot.position.x + math.cos(theta) * local_x + math.sin(theta) * local_y,
                    slot.position.y - math.sin(theta) * local_x + math.cos(theta) * local_y,
                )
                values.append(height(point))
        pads[slot.id] = {
            "samples": len(values),
            "min": min(values),
            "max": max(values),
            "maxAbs": max(abs(value) for value in values),
        }

    result = {
        "surface": "saved town-plate.blend mesh ray-cast",
        "routeSamples": len(all_heights),
        "routeMaxAbs": max(abs(value) for value in all_heights),
        "plazaSamples": len(plaza_values),
        "plazaMaxAbs": max(abs(value) for value in plaza_values),
        "routes": routes,
        "pads": pads,
    }
    assert result["routeMaxAbs"] <= 0.05
    assert result["plazaMaxAbs"] <= 0.05
    assert all(item["maxAbs"] <= 0.05 for item in pads.values())
    return result


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    bpy.ops.object.select_all(action="DESELECT")
    plate = bpy.data.objects["TownPlate"]
    plate.select_set(True)
    bpy.context.view_layer.objects.active = plate
    bpy.ops.export_scene.gltf(
        filepath=str(CHECKED), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT",
    )
    checked = glb_contract(CHECKED)
    reexported = glb_contract(GLB)
    pan_checked = glb_contract(PAN_CHECKED)
    pan_reexported = glb_contract(PAN_GLB)
    realized = realized_flat_walk()
    decoration = json.loads((ARTIFACTS / "decoration-clearance.json").read_text())
    semantic_keys = (
        "meshes", "primitives", "triangles", "materials", "textures", "images", "embeddedImages",
        "imageMimeTypes", "imageDimensions", "cameras", "lights", "animations", "bounds", "materialContract",
    )
    evidence = {
        "blender": bpy.app.version_string,
        "checked": checked,
        "reexported": reexported,
        "byteIdentical": checked["sha256"] == reexported["sha256"],
        "semanticIdentical": {key: checked[key] == reexported[key] for key in semantic_keys},
        "realizedFlatWalk": realized,
        "decorationClearance": decoration,
        "panMonument": {
            "checked": pan_checked,
            "reexported": pan_reexported,
            "byteIdentical": pan_checked["sha256"] == pan_reexported["sha256"],
            "semanticIdentical": {key: pan_checked[key] == pan_reexported[key] for key in semantic_keys},
        },
    }
    (ARTIFACTS / "asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (ARTIFACTS / "flat-walk-realized.json").write_text(json.dumps(realized, indent=2) + "\n")

    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] <= 30_000
    assert checked["materials"] == checked["textures"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["imageMimeTypes"] == ["image/png"]
    assert checked["imageDimensions"] == [[2048, 2048]]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert checked["materialContract"][0]["metallicFactor"] == 0
    assert checked["materialContract"][0]["roughnessFactor"] >= 0.899
    assert checked["materialContract"][0]["hasBaseColorTexture"]
    assert not checked["materialContract"][0]["hasEmissiveTexture"]
    assert evidence["byteIdentical"]
    assert all(evidence["semanticIdentical"].values())
    assert decoration["minimumRouteClearance"] >= 0.20
    assert decoration["minimumPadClearance"] >= 0.12
    assert decoration["minimumExistingPropClearance"] >= 0.12
    assert decoration["minimumPlazaStageClearance"] >= 1.0
    assert decoration["minimumPairClearance"] >= 0.12
    assert pan_checked["meshes"] == pan_checked["primitives"] == 1
    assert pan_checked["triangles"] <= 4_000
    assert pan_checked["materials"] == pan_checked["textures"] == pan_checked["images"] == pan_checked["embeddedImages"] == 1
    assert pan_checked["imageMimeTypes"] == ["image/png"]
    assert pan_checked["imageDimensions"] == [[256, 256]]
    assert pan_checked["cameras"] == pan_checked["lights"] == pan_checked["animations"] == 0
    assert evidence["panMonument"]["byteIdentical"]
    assert all(evidence["panMonument"]["semanticIdentical"].values())
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
