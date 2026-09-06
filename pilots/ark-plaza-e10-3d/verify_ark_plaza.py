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
HERE = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/ark-plaza-e10"
BLEND = HERE / "ark-plaza-e10.blend"
GLB = HERE / "ark-plaza-e10.glb"
TEMP_REEXPORT = Path("/tmp/ark-plaza-e10-reexport.glb")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_builder():
    spec = importlib.util.spec_from_file_location("ark_plaza_verifier_builder", HERE / "build_ark_plaza.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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
        dimensions.append(list(struct.unpack(">II", payload[16:24])))
    return dimensions


def glb_contract(path: Path) -> dict:
    document, binary = parse_glb(path)
    accessors = document.get("accessors", [])
    primitives = [primitive for mesh in document.get("meshes", []) for primitive in mesh.get("primitives", [])]
    positions = [accessors[primitive["attributes"]["POSITION"]] for primitive in primitives]
    minimum = [min(accessor["min"][axis] for accessor in positions) for axis in range(3)]
    maximum = [max(accessor["max"][axis] for accessor in positions) for axis in range(3)]
    materials = document.get("materials", [])
    return {
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "nodes": [node.get("name") for node in document.get("nodes", [])],
        "meshes": len(document.get("meshes", [])),
        "primitives": len(primitives),
        "triangles": sum(accessors[primitive["indices"]]["count"] // 3 for primitive in primitives),
        "materials": len(materials),
        "textures": len(document.get("textures", [])),
        "images": len(document.get("images", [])),
        "embeddedImages": sum("bufferView" in image for image in document.get("images", [])),
        "imageDimensions": embedded_png_dimensions(document, binary),
        "cameras": len(document.get("cameras", [])),
        "lights": len(document.get("extensions", {}).get("KHR_lights_punctual", {}).get("lights", [])),
        "animations": len(document.get("animations", [])),
        "bounds": {
            "min": [round(value, 6) for value in minimum],
            "max": [round(value, 6) for value in maximum],
            "size": [round(maximum[index] - minimum[index], 6) for index in range(3)],
            "center": [round((maximum[index] + minimum[index]) * 0.5, 6) for index in range(3)],
        },
        "materialContract": [{
            "metallicFactor": material.get("pbrMetallicRoughness", {}).get("metallicFactor", 1),
            "roughnessFactor": material.get("pbrMetallicRoughness", {}).get("roughnessFactor", 1),
            "hasBaseColorTexture": "baseColorTexture" in material.get("pbrMetallicRoughness", {}),
            "alphaMode": material.get("alphaMode", "OPAQUE"),
            "doubleSided": material.get("doubleSided", False),
        } for material in materials],
    }


def sample_segment(start, end, spacing: float = 0.10, corridor_offsets=(-0.45, 0.0, 0.45)):
    distance = math.hypot(end.x - start.x, end.y - start.y)
    count = max(1, math.ceil(distance / spacing))
    dx = end.x - start.x
    dy = end.y - start.y
    normal_x = -dy / max(distance, 1e-9)
    normal_y = dx / max(distance, 1e-9)
    return [
        (
            start.x + dx * index / count + normal_x * offset,
            start.y + dy * index / count + normal_y * offset,
        )
        for index in range(count + 1)
        for offset in corridor_offsets
    ]


def realized_walk_surface(builder) -> dict:
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    plate = bpy.data.objects["ArkPlazaE10"]
    assert plate.location.length <= 1e-9
    bvh = BVHTree.FromObject(plate, bpy.context.evaluated_depsgraph_get())

    def height(x: float, y: float) -> float:
        hit, _normal, _face, _distance = bvh.ray_cast(Vector((x, y, 0.12)), Vector((0.0, 0.0, -1.0)), 2.0)
        if hit is None:
            raise RuntimeError(f"No Ark deck beneath {(x, y)}")
        return float(hit.z)

    route_reports = {}
    route_values = []
    route_groups = [("ring-road", builder.town.RING_ROUTE, True)] + [
        (identifier, points, False) for identifier, points in builder.town.RADIAL_ROUTES.items()
    ]
    for identifier, points, closed in route_groups:
        pairs = list(zip(points, points[1:]))
        if closed:
            pairs.append((points[-1], points[0]))
        samples = [sample for start, end in pairs for sample in sample_segment(start, end)]
        # The unchanged Pan Monument occupies the innermost 0.9 radius on every
        # era site; it is a mount footprint, not actor floor.
        values = [height(x, y) for x, y in samples if math.hypot(x, y) >= 0.92]
        route_values.extend(values)
        route_reports[identifier] = {
            "samples": len(values), "minimum": min(values), "maximum": max(values),
            "maxAbs": max(abs(value) for value in values),
        }
    return {
        "surface": "saved ark-plaza-e10.blend ray-cast across the inherited +/-0.45m actor corridor outside the Pan Monument footprint",
        "panMonumentExclusionRadius": 0.92,
        "actorCorridorOffsets": [-0.45, 0.0, 0.45],
        "routeSamples": len(route_values),
        "routeMaxAbs": max(abs(value) for value in route_values),
        "routes": route_reports,
    }


def reexport() -> dict:
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    bpy.ops.object.select_all(action="DESELECT")
    plate = bpy.data.objects["ArkPlazaE10"]
    plate.select_set(True)
    bpy.context.view_layer.objects.active = plate
    bpy.ops.export_scene.gltf(
        filepath=str(TEMP_REEXPORT), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT",
    )
    contract = glb_contract(TEMP_REEXPORT)
    TEMP_REEXPORT.unlink(missing_ok=True)
    return contract


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    builder = load_builder()
    checked = glb_contract(GLB)
    reexported = reexport()
    realized = realized_walk_surface(builder)
    semantic_keys = (
        "nodes", "meshes", "primitives", "triangles", "materials", "textures", "images",
        "embeddedImages", "imageDimensions", "cameras", "lights", "animations", "bounds", "materialContract",
    )
    evidence = {
        "blender": bpy.app.version_string,
        "baseSha": builder.BASE_SHA,
        "checked": checked,
        "reexported": reexported,
        "byteIdentical": checked["sha256"] == reexported["sha256"],
        "semanticIdentical": {key: checked[key] == reexported[key] for key in semantic_keys},
        "realizedWalkSurface": realized,
    }
    (ARTIFACTS / "ark-plaza-asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")

    assert checked["nodes"] == ["ArkPlazaE10"]
    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] <= builder.TRIANGLE_BUDGET
    assert checked["materials"] == checked["textures"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["imageDimensions"] == [[builder.ATLAS_SIZE, builder.ATLAS_SIZE]]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert checked["materialContract"][0]["hasBaseColorTexture"]
    assert realized["routeMaxAbs"] <= builder.WALK_RELIEF_LIMIT
    assert evidence["byteIdentical"]
    assert all(evidence["semanticIdentical"].values())
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
