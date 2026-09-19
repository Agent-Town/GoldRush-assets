from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

sys.dont_write_bytecode = True

import bpy


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/ark-deck-era-dressing-e10"
BLEND = HERE / "ark-deck-era-dressing-e10.blend"
GLB = HERE / "ark-deck-era-dressing-e10.glb"
ATLAS = HERE / "ark-deck-era-dressing-e10-atlas.png"
TEMP = Path("/tmp/ark-deck-era-dressing-e10-reexport.glb")
STATION_FOOTPRINT_RADIUS = 1.30


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


builder = load("ark_deck_dressing_builder_verify", HERE / "build_ark_deck_era_dressing.py")
glb = load("ark_deck_dressing_glb_verify", ROOT / "assets/pilots/dredge-queen-3d/verify_dredge_queen.py")
town = load("ark_deck_dressing_town_verify", ROOT / "assets/pilots/town-plate-3d/build_town_plate.py")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def embedded_image_hash(path: Path) -> str:
    document, binary = glb.read_glb(path)
    image = document["images"][0]
    view = document["bufferViews"][image["bufferView"]]
    start = view.get("byteOffset", 0)
    return hashlib.sha256(binary[start:start + view["byteLength"]]).hexdigest()


def reexport() -> dict:
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    assert [obj.name for obj in meshes] == ["ArkDeckEraDressingE10"]
    assert not [obj for obj in bpy.data.objects if obj.type in {"CAMERA", "LIGHT"}]
    assert not list(bpy.data.actions)
    bpy.ops.object.select_all(action="DESELECT")
    meshes[0].select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(
        filepath=str(TEMP), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT",
    )
    contract = glb.contract(TEMP)
    TEMP.unlink(missing_ok=True)
    return contract


def point_segment_distance(point, start, end) -> float:
    px, py = point
    ax, ay = start
    bx, by = end
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    t = 0.0 if length_sq <= 1e-12 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    return math.hypot(px - (ax + dx * t), py - (ay + dy * t))


def polyline_distance(point, points) -> float:
    return min(point_segment_distance(point, start, end) for start, end in zip(points, points[1:]))


def rectangle_clearance(center, radius: float, slot) -> float:
    dx = max(0.0, abs(center[0] - slot.position.x) - slot.width * 0.5)
    dy = max(0.0, abs(center[1] - slot.position.y) - slot.depth * 0.5)
    return math.hypot(dx, dy) - radius


def station_clearance() -> dict:
    routes = [[(point.x, point.y) for point in route] for route in town.RADIAL_ROUTES.values()]
    slots = [*town.SLOTS, town.DYNAMO_SLOT]
    report = {}
    for index in range(10):
        angle, radius, _ = builder.station_center(index)
        center = builder.point(angle, radius, 0.0, 0.0, 0.0)[:2]
        canonical_route = min(
            abs(math.hypot(*center) - 6.0),
            *(polyline_distance(center, route) for route in routes),
        ) - STATION_FOOTPRINT_RADIUS
        pad = min(rectangle_clearance(center, STATION_FOOTPRINT_RADIUS, slot) for slot in slots)
        plaza = math.hypot(*center) - STATION_FOOTPRINT_RADIUS - 3.1
        deck_edge = builder.DECK_RADIUS - math.hypot(*center) - STATION_FOOTPRINT_RADIUS
        medallion_angle = math.radians(90.0) - index * math.tau / 10.0
        medallion = (math.cos(medallion_angle) * 17.62, math.sin(medallion_angle) * 17.62)
        medallion_clearance = math.dist(center, medallion) - 0.76 - 0.42
        beacon = (math.cos(medallion_angle) * 20.55, math.sin(medallion_angle) * 20.55)
        beacon_clearance = math.dist(center, beacon) - 0.20 - 0.42
        item = {
            "center": [round(value, 6) for value in center],
            "canonicalRouteClearance": round(canonical_route, 6),
            "buildingPadClearance": round(pad, 6),
            "openPlazaClearance": round(plaza, 6),
            "deckEdgeMargin": round(deck_edge, 6),
            "medallionClearance": round(medallion_clearance, 6),
            "beaconClearance": round(beacon_clearance, 6),
        }
        assert canonical_route >= 1.0
        assert pad >= 1.0
        assert plaza >= 1.0
        assert deck_edge >= 1.0
        assert medallion_clearance >= 0.08
        assert beacon_clearance >= 0.60
        report[f"E{index + 1}"] = item
    # The two cardinal stations were deliberately offset from the airlock axes.
    assert abs(report["E1"]["center"][0]) - 1.23 >= 1.70
    assert abs(report["E6"]["center"][0]) - 1.23 >= 1.70
    return report


def main() -> None:
    checked = glb.contract(GLB)
    reproduced = reexport()
    stable_keys = (
        "nodes", "nodeCount", "bindings", "nodeTransforms", "meshes", "meshNames", "primitives",
        "primitiveMaterials", "triangles", "morphTargets", "targetCounts", "materials",
        "materialTextureBindings", "materialContract", "textureSources", "images", "embeddedImages",
        "imageDimensions", "cameras", "lights", "animations", "bounds",
    )
    evidence = {
        "baseSha": builder.BASE_SHA,
        "checked": checked,
        "reexported": reproduced,
        "byteIdentical": checked["sha256"] == reproduced["sha256"],
        "semanticIdentical": {key: checked[key] == reproduced[key] for key in stable_keys},
        "externalAtlasSha256": sha256(ATLAS),
        "embeddedAtlasSha256": embedded_image_hash(GLB),
        "stationClearance": station_clearance(),
        "ownershipBoundary": "separate origin-aligned mount; accepted Ark plaza GLB unchanged",
    }
    assert checked["nodes"] == ["ArkDeckEraDressingE10"]
    assert checked["nodeCount"] == checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] <= builder.TRIANGLE_BUDGET
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["imageDimensions"] == [[builder.ATLAS_SIZE, builder.ATLAS_SIZE]]
    assert checked["primitiveMaterials"] == [0]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert abs(checked["bounds"]["min"][1]) <= 0.001, checked["bounds"]
    assert evidence["externalAtlasSha256"] == evidence["embeddedAtlasSha256"]
    assert evidence["byteIdentical"] and all(evidence["semanticIdentical"].values())
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "ark-deck-era-dressing-asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({
        "baseSha": builder.BASE_SHA,
        "sha256": checked["sha256"],
        "triangles": checked["triangles"],
        "byteIdentical": evidence["byteIdentical"],
        "stationClearance": evidence["stationClearance"],
    }, indent=2))


if __name__ == "__main__":
    main()
