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
ARTIFACTS = ROOT / "artifacts/ark-long-table-hall-e10"
BLEND = HERE / "ark-long-table-hall-e10.blend"
GLB = HERE / "ark-long-table-hall-e10.glb"
TEMP = Path("/tmp/ark-long-table-hall-e10-reexport.glb")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_builder():
    spec = importlib.util.spec_from_file_location("ark_long_table_hall_verifier_builder",
                                                  HERE / "build_ark_long_table_hall.py")
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
    position_accessors = [accessors[primitive["attributes"]["POSITION"]] for primitive in primitives]
    minimum = [min(accessor["min"][axis] for accessor in position_accessors) for axis in range(3)]
    maximum = [max(accessor["max"][axis] for accessor in position_accessors) for axis in range(3)]
    nodes = [node.get("name", "") for node in document.get("nodes", [])]
    return {
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "nodes": nodes,
        "anchors": sorted(name for name in nodes if name.startswith("portrait_anchor_")
                          or name in ("pan_shrine_anchor", "elder_tree_anchor")),
        "meshes": len(document.get("meshes", [])),
        "primitives": len(primitives),
        "triangles": sum(accessors[primitive["indices"]]["count"] // 3 for primitive in primitives),
        "materials": len(document.get("materials", [])),
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
            "size": [round(maximum[i] - minimum[i], 6) for i in range(3)],
        },
    }


def sample_line(start: tuple[float, float], end: tuple[float, float], spacing=0.10):
    distance = math.hypot(end[0] - start[0], end[1] - start[1])
    count = max(1, math.ceil(distance / spacing))
    return [(start[0] + (end[0] - start[0]) * index / count,
             start[1] + (end[1] - start[1]) * index / count) for index in range(count + 1)]


def circulation_surface() -> dict:
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    hall = bpy.data.objects["ArkLongTableHallE10"]
    assert hall.location.length <= 1e-9
    bvh = BVHTree.FromObject(hall, bpy.context.evaluated_depsgraph_get())

    def height(x: float, y: float) -> float:
        hit, _normal, _face, _distance = bvh.ray_cast(Vector((x, y, 0.12)), Vector((0.0, 0.0, -1.0)), 1.0)
        if hit is None:
            raise RuntimeError(f"No hall deck beneath {(x, y)}")
        return float(hit.z)

    routes = {
        "south-entry": ((0.0, -10.2), (0.0, -7.7)),
        "port-circulation": ((-4.0, -8.0), (-4.0, 8.0)),
        "starboard-circulation": ((4.0, -8.0), (4.0, 8.0)),
        "forward-cross-aisle": ((-4.0, 8.0), (4.0, 8.0)),
        "aft-cross-aisle": ((-4.0, -8.0), (4.0, -8.0)),
    }
    reports = {}
    all_values = []
    for identifier, (start, end) in routes.items():
        values = [height(x, y) for x, y in sample_line(start, end)]
        reports[identifier] = {"samples": len(values), "minimum": min(values),
                               "maximum": max(values), "maxAbs": max(abs(value) for value in values)}
        all_values.extend(values)
    return {
        "surface": "saved BLEND ray-cast on the five production circulation aisles around the fixed table/shrine/tree",
        "samples": len(all_values),
        "maxAbs": max(abs(value) for value in all_values),
        "limit": 0.05,
        "routes": reports,
    }


def reexport() -> dict:
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    bpy.ops.object.select_all(action="SELECT")
    bpy.context.view_layer.objects.active = bpy.data.objects["ArkLongTableHallE10"]
    bpy.ops.export_scene.gltf(
        filepath=str(TEMP), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False,
        export_materials="EXPORT",
    )
    contract = glb_contract(TEMP)
    TEMP.unlink(missing_ok=True)
    return contract


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    builder = load_builder()
    checked = glb_contract(GLB)
    reexported = reexport()
    circulation = circulation_surface()
    semantic_keys = (
        "nodes", "anchors", "meshes", "primitives", "triangles", "materials", "textures",
        "images", "embeddedImages", "imageDimensions", "cameras", "lights", "animations", "bounds",
    )
    evidence = {
        "blender": bpy.app.version_string,
        "baseSha": builder.BASE_SHA,
        "checked": checked,
        "reexported": reexported,
        "byteIdentical": checked["sha256"] == reexported["sha256"],
        "semanticIdentical": {key: checked[key] == reexported[key] for key in semantic_keys},
        "circulationSurface": circulation,
    }
    (ARTIFACTS / "ark-long-table-hall-asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")

    expected_anchors = sorted([*[f"portrait_anchor_{index:02d}" for index in range(1, 11)],
                               "pan_shrine_anchor", "elder_tree_anchor"])
    assert checked["anchors"] == expected_anchors
    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] <= builder.TRIANGLE_BUDGET
    assert checked["materials"] == checked["textures"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["imageDimensions"] == [[builder.ATLAS_SIZE, builder.ATLAS_SIZE]]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert circulation["maxAbs"] <= circulation["limit"]
    assert evidence["byteIdentical"]
    assert all(evidence["semanticIdentical"].values())
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
