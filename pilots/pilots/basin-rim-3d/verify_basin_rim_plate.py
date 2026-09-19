from __future__ import annotations

from pathlib import Path
import importlib.util
import json
import math
import re
import subprocess
import sys

sys.dont_write_bytecode = True

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/basin-rim-e9"
BLEND = HERE / "basin-rim-plate.blend"
GLB = HERE / "basin-rim-plate.glb"
TEMP = Path("/tmp/basin-rim-plate-reexport.glb")
TEMP_ATLAS = Path("/tmp/basin-rim-plate-atlas-check.png")


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


builder = load("basin_rim_verify_builder", HERE / "build_basin_rim_plate.py")
shared = load(
    "basin_rim_verify_shared",
    ROOT / "assets/pilots/dome-commons-3d/verify_dome_commons_plate.py",
)


def segment(start, end, spacing: float = 0.10):
    count = max(1, math.ceil(math.hypot(end.x - start.x, end.y - start.y) / spacing))
    return [
        builder.Point(
            start.x + (end.x - start.x) * index / count,
            start.y + (end.y - start.y) * index / count,
        )
        for index in range(count)
    ]


def polyline(points, closed: bool = False):
    pairs = list(zip(points, points[1:]))
    if closed:
        pairs.append((points[-1], points[0]))
    return [point for start, end in pairs for point in segment(start, end)] + [points[0] if closed else points[-1]]


def realized_surface() -> dict:
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    plate = bpy.data.objects["BasinRimPlate"]
    assert plate.location.length <= 1e-9
    bvh = BVHTree.FromObject(plate, bpy.context.evaluated_depsgraph_get())

    def height(point) -> float:
        hit, _normal, _face, _distance = bvh.ray_cast(
            Vector((point.x, point.y, 2.5)), Vector((0.0, 0.0, -1.0)), 6.0,
        )
        if hit is None:
            raise RuntimeError(f"No Basin Rim surface below {point}")
        return float(hit.z)

    def report(points) -> dict:
        values = [height(point) for point in points]
        return {
            "samples": len(values), "min": min(values), "max": max(values),
            "maxAbs": max(abs(value) for value in values),
        }

    routes = {"ring-road": report(polyline(builder.RING_ROUTE, True))}
    routes.update({name: report(polyline(points)) for name, points in builder.CANONICAL_ROUTES.items()})
    plaza = report([
        builder.Point(ix * 0.2, iy * 0.2)
        for ix in range(-16, 17) for iy in range(-16, 17)
        if (ix * 0.2) ** 2 + (iy * 0.2) ** 2 <= builder.PLAZA_CLEAR_RADIUS ** 2
    ])

    canonical_pads = {}
    for slot in builder.CANONICAL_SLOTS:
        theta = builder.town.slot_angle(slot)
        points = []
        for ix in range(11):
            for iy in range(9):
                x = (-0.5 + ix / 10.0) * slot.width
                y = (-0.5 + iy / 8.0) * slot.depth
                points.append(builder.Point(
                    slot.position.x + math.cos(theta) * x + math.sin(theta) * y,
                    slot.position.y - math.sin(theta) * x + math.cos(theta) * y,
                ))
        canonical_pads[slot.id] = report(points)

    basin_pads = {}
    for pad in builder.BASIN_PADS:
        points = []
        for ix in range(-8, 9):
            for iy in range(-8, 9):
                x, y = ix / 16.0 * pad.width, iy / 16.0 * pad.depth
                if pad.shape == "circle" and math.hypot(x, y) > pad.width * 0.5:
                    continue
                points.append(builder.Point(pad.position.x + x, pad.position.y + y))
        basin_pads[pad.id] = report(points)

    result = {
        "surface": "saved basin-rim-plate.blend ray-cast",
        "routeMaxAbs": max(item["maxAbs"] for item in routes.values()),
        "plaza": plaza,
        "routes": routes,
        "canonicalPads": canonical_pads,
        "basinPads": basin_pads,
    }
    print(json.dumps(result, indent=2))
    assert result["routeMaxAbs"] <= builder.PATH_RELIEF_LIMIT
    assert plaza["maxAbs"] <= builder.PATH_RELIEF_LIMIT
    assert all(item["maxAbs"] <= builder.PATH_RELIEF_LIMIT for item in canonical_pads.values())
    assert all(item["maxAbs"] <= builder.PATH_RELIEF_LIMIT for item in basin_pads.values())
    return result


def reexport() -> dict:
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    bpy.ops.object.select_all(action="DESELECT")
    plate = bpy.data.objects["BasinRimPlate"]
    plate.select_set(True)
    bpy.context.view_layer.objects.active = plate
    bpy.ops.export_scene.gltf(
        filepath=str(TEMP), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT",
    )
    result = shared.glb_contract(TEMP)
    TEMP.unlink(missing_ok=True)
    return result


def exact_green_pixels() -> int:
    document, binary = shared.parse_glb(GLB)
    image = document["images"][0]
    view = document["bufferViews"][image["bufferView"]]
    start = view.get("byteOffset", 0)
    TEMP_ATLAS.write_bytes(binary[start:start + view["byteLength"]])
    histogram = subprocess.run(
        ["magick", str(TEMP_ATLAS), "-format", "%c", "histogram:info:-"],
        check=True, capture_output=True, text=True,
    ).stdout
    TEMP_ATLAS.unlink(missing_ok=True)
    match = re.search(rf"^\s*(\d+): .*{builder.E1_GREEN_HEX.upper()}\b", histogram, re.MULTILINE | re.IGNORECASE)
    return int(match.group(1)) if match else 0


def main() -> None:
    checked = shared.glb_contract(GLB)
    exported = reexport()
    material = checked["materialContract"][0]
    semantic_keys = (
        "nodes", "meshes", "primitives", "triangles", "materials", "textures", "images",
        "embeddedImages", "imageDimensions", "cameras", "lights", "animations", "bounds", "materialContract",
    )
    evidence = {
        "blender": bpy.app.version_string,
        "baseSha": builder.BASE_SHA,
        "e1GreenHex": builder.E1_GREEN_HEX,
        "checked": checked,
        "reexported": exported,
        "byteIdentical": checked["sha256"] == exported["sha256"],
        "semanticIdentical": {key: checked[key] == exported[key] for key in semantic_keys},
        "threeRuntimeMaterial": shared.three_runtime_material(GLB),
        "exactE1GreenPixels": exact_green_pixels(),
        "realizedSurface": realized_surface(),
    }
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "basin-rim-asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")

    assert checked["nodes"] == ["BasinRimPlate"]
    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] <= builder.TRIANGLE_BUDGET
    assert checked["materials"] == checked["textures"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["imageDimensions"] == [[builder.ATLAS_SIZE, builder.ATLAS_SIZE]]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert material["metallicFactor"] == 0 and material["roughnessFactor"] >= 0.90
    assert material["hasBaseColorTexture"] and not material["hasEmissiveTexture"]
    assert material["alphaMode"] == "OPAQUE" and material["doubleSided"]
    assert evidence["threeRuntimeMaterial"] == {
        "transparent": False, "depthWrite": True, "alphaTest": 0, "doubleSided": True,
    }
    assert evidence["exactE1GreenPixels"] > 0
    assert evidence["byteIdentical"] and all(evidence["semanticIdentical"].values())
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
