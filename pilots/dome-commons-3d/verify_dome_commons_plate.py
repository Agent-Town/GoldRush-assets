from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import math
import subprocess
import struct
import sys

sys.dont_write_bytecode = True

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[3]
SOURCE_DIR = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/dome-commons-e8"
BLEND = SOURCE_DIR / "dome-commons-plate.blend"
GLB = SOURCE_DIR / "dome-commons-plate.glb"
TEMP_REEXPORT = Path("/tmp/dome-commons-plate-reexport.glb")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_builder():
    spec = importlib.util.spec_from_file_location("dome_commons_verifier_builder", SOURCE_DIR / "build_dome_commons_plate.py")
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
        "materialContract": [
            {
                "metallicFactor": material.get("pbrMetallicRoughness", {}).get("metallicFactor", 1),
                "roughnessFactor": material.get("pbrMetallicRoughness", {}).get("roughnessFactor", 1),
                "hasBaseColorTexture": "baseColorTexture" in material.get("pbrMetallicRoughness", {}),
                "hasEmissiveTexture": "emissiveTexture" in material,
                "emissiveFactor": material.get("emissiveFactor", [0, 0, 0]),
                "alphaMode": material.get("alphaMode", "OPAQUE"),
                "alphaCutoff": material.get("alphaCutoff", 0.5) if material.get("alphaMode") == "MASK" else None,
                "doubleSided": material.get("doubleSided", False),
            }
            for material in materials
        ],
    }


def three_runtime_material(path: Path) -> dict:
    script = r'''
import fs from "node:fs";
import { GLTFLoader } from "./node_modules/three/examples/jsm/loaders/GLTFLoader.js";
const data = fs.readFileSync(process.argv[1]);
const jsonLength = data.readUInt32LE(12);
const document = JSON.parse(data.subarray(20, 20 + jsonLength).toString());
const material = structuredClone(document.materials[0]);
if (material.pbrMetallicRoughness) delete material.pbrMetallicRoughness.baseColorTexture;
const minimal = {
  asset: { version: "2.0" }, scene: 0, scenes: [{ nodes: [0] }], nodes: [{ mesh: 0 }],
  meshes: [{ primitives: [{ attributes: {}, material: 0 }] }], materials: [material],
};
const gltf = await new Promise((resolve, reject) => new GLTFLoader().parse(JSON.stringify(minimal), "", resolve, reject));
let loadedMaterial;
gltf.scene.traverse((node) => { if (node.isMesh) loadedMaterial = node.material; });
console.log(JSON.stringify({
  transparent: loadedMaterial.transparent,
  depthWrite: loadedMaterial.depthWrite,
  alphaTest: loadedMaterial.alphaTest,
  doubleSided: loadedMaterial.side === 2,
}));
'''
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script, str(path)],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    return json.loads(completed.stdout)


def sample_segment(builder, start, end, spacing: float = 0.10):
    distance = math.hypot(end.x - start.x, end.y - start.y)
    count = max(1, math.ceil(distance / spacing))
    return [
        builder.Point(start.x + (end.x - start.x) * index / count,
                      start.y + (end.y - start.y) * index / count)
        for index in range(count)
    ]


def sample_polyline(builder, points, closed: bool = False, spacing: float = 0.10):
    pairs = list(zip(points, points[1:]))
    if closed:
        pairs.append((points[-1], points[0]))
    samples = []
    for start, end in pairs:
        samples.extend(sample_segment(builder, start, end, spacing))
    samples.append(points[0] if closed else points[-1])
    return samples


def realized_surface(builder) -> dict:
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    plate = bpy.data.objects["DomeCommonsPlate"]
    assert plate.location.length <= 1e-9
    bvh = BVHTree.FromObject(plate, bpy.context.evaluated_depsgraph_get())

    def height(point) -> float:
        # Begin below the air-wall shell so the ground, not the transparent dome,
        # is the sampled gameplay surface.
        hit, _normal, _face, _distance = bvh.ray_cast(
            Vector((point.x, point.y, 0.45)), Vector((0.0, 0.0, -1.0)), 3.0,
        )
        if hit is None:
            raise RuntimeError(f"No Dome Commons floor below {point}")
        return float(hit.z)

    route_reports = {}
    route_heights = []
    for route_id, points, closed in [
        ("ring-road", builder.RING_ROUTE, True),
        *[(route_id, points, False) for route_id, points in builder.CANONICAL_ROUTES.items()],
    ]:
        values = [height(point) for point in sample_polyline(builder, points, closed)]
        route_heights.extend(values)
        route_reports[route_id] = {
            "samples": len(values), "min": min(values), "max": max(values),
            "maxAbs": max(abs(value) for value in values),
        }

    plaza_points = [
        builder.Point(x * 0.2, y * 0.2)
        for x in range(-16, 17)
        for y in range(-16, 17)
        if (x * 0.2) ** 2 + (y * 0.2) ** 2 <= builder.PLAZA_CLEAR_RADIUS**2
    ]
    plaza_values = [height(point) for point in plaza_points]

    pad_reports = {}
    for slot in builder.CANONICAL_SLOTS:
        theta = builder.town.slot_angle(slot)
        values = []
        for local_x in [(-0.5 + index / 10.0) * slot.width for index in range(11)]:
            for local_y in [(-0.5 + index / 8.0) * slot.depth for index in range(9)]:
                point = builder.Point(
                    slot.position.x + math.cos(theta) * local_x + math.sin(theta) * local_y,
                    slot.position.y - math.sin(theta) * local_x + math.cos(theta) * local_y,
                )
                values.append(height(point))
        pad_reports[slot.id] = {
            "samples": len(values), "min": min(values), "max": max(values),
            "maxAbs": max(abs(value) for value in values),
        }

    orbital_reports = {}
    for pad in builder.ORBITAL_PADS:
        values = []
        for ix in range(-8, 9):
            for iy in range(-8, 9):
                local_x = ix / 8.0 * pad.width * 0.5
                local_y = iy / 8.0 * pad.depth * 0.5
                if pad.shape == "circle" and math.hypot(local_x, local_y) > pad.width * 0.5:
                    continue
                values.append(height(builder.Point(pad.position.x + local_x, pad.position.y + local_y)))
        orbital_reports[pad.id] = {
            "samples": len(values), "min": min(values), "max": max(values),
            "maxAbs": max(abs(value) for value in values),
        }

    result = {
        "surface": "saved dome-commons-plate.blend ground ray-cast from inside the air wall",
        "routeSamples": len(route_heights),
        "routeMaxAbs": max(abs(value) for value in route_heights),
        "plazaSamples": len(plaza_values),
        "plazaMaxAbs": max(abs(value) for value in plaza_values),
        "routes": route_reports,
        "canonicalPads": pad_reports,
        "orbitalPads": orbital_reports,
    }
    assert result["routeMaxAbs"] <= builder.PATH_RELIEF_LIMIT
    assert result["plazaMaxAbs"] <= builder.PATH_RELIEF_LIMIT
    assert all(report["maxAbs"] <= builder.PATH_RELIEF_LIMIT for report in pad_reports.values())
    assert all(report["maxAbs"] <= builder.PATH_RELIEF_LIMIT for report in orbital_reports.values())
    return result


def reexport() -> dict:
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    bpy.ops.object.select_all(action="DESELECT")
    plate = bpy.data.objects["DomeCommonsPlate"]
    plate.select_set(True)
    bpy.context.view_layer.objects.active = plate
    bpy.ops.export_scene.gltf(
        filepath=str(TEMP_REEXPORT), export_format="GLB", use_selection=True,
        export_apply=True, export_cameras=False, export_lights=False,
        export_animations=False, export_materials="EXPORT",
    )
    contract = glb_contract(TEMP_REEXPORT)
    TEMP_REEXPORT.unlink(missing_ok=True)
    return contract


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    builder = load_builder()
    checked = glb_contract(GLB)
    realized = realized_surface(builder)
    reexported = reexport()
    runtime_material = three_runtime_material(GLB)
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
        "threeRuntimeMaterial": runtime_material,
        "realizedSurface": realized,
    }
    (ARTIFACTS / "dome-commons-asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")

    assert checked["nodes"] == ["DomeCommonsPlate"]
    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] <= builder.TRIANGLE_BUDGET
    assert checked["materials"] == checked["textures"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["imageDimensions"] == [[builder.ATLAS_SIZE, builder.ATLAS_SIZE]]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    material = checked["materialContract"][0]
    assert material["metallicFactor"] == 0
    assert material["roughnessFactor"] >= 0.89
    assert material["hasBaseColorTexture"]
    assert not material["hasEmissiveTexture"]
    assert material["alphaMode"] == "MASK"
    assert material["alphaCutoff"] == 0.5
    assert material["doubleSided"]
    assert runtime_material == {
        "transparent": False, "depthWrite": True, "alphaTest": 0.5, "doubleSided": True,
    }
    assert evidence["byteIdentical"]
    assert all(evidence["semanticIdentical"].values())
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
