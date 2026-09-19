from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

import bpy


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "artifacts/ark-era-props-e10"
BASE_SHA = "d7e429d16e24b88e4e65114752b3b12a96280e3b"
ATLAS = HERE / "era-props-e10-atlas.png"
MANIFEST = HERE / "era-props.e10.json"
DECK_RADIUS = 23.0
ASSETS = {
    "bridge-school.e10": "BridgeSchoolE10",
    "charter-press.e10": "CharterPressE10",
    "preserve-rack.e10": "PreserveRackE10",
    "engine-glow-idle.e10": "EngineGlowIdleE10",
    "engine-glow-cruise.e10": "EngineGlowCruiseE10",
    "engine-glow-ward.e10": "EngineGlowWardE10",
}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


glb = load("e10_prop_glb_contract", ROOT / "assets/pilots/dredge-queen-3d/verify_dredge_queen.py")
town = load("e10_prop_town_layout", ROOT / "assets/pilots/town-plate-3d/build_town_plate.py")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def embedded_image_hash(path: Path) -> str:
    document, binary = glb.read_glb(path)
    image = document["images"][0]
    view = document["bufferViews"][image["bufferView"]]
    start = view.get("byteOffset", 0)
    return hashlib.sha256(binary[start:start + view["byteLength"]]).hexdigest()


def reexport(stem: str, destination: Path) -> dict:
    bpy.ops.wm.open_mainfile(filepath=str(HERE / f"{stem}.blend"))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    assert len(meshes) == 1
    assert not [obj for obj in bpy.data.objects if obj.type == "CAMERA"]
    assert not [obj for obj in bpy.data.objects if obj.type == "LIGHT"]
    assert not list(bpy.data.actions)
    bpy.ops.object.select_all(action="DESELECT")
    meshes[0].select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(
        filepath=str(destination.with_suffix("")), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT",
    )
    return glb.contract(destination)


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


def placement_evidence(manifest: dict, contracts: dict) -> dict:
    routes = [[(point.x, point.y) for point in route] for route in town.RADIAL_ROUTES.values()]
    slots = [*town.SLOTS, town.DYNAMO_SLOT]
    evidence = {}
    for placement in manifest["props"]:
        stem = placement["glb"].removesuffix(".glb")
        contract = contracts[stem]
        center = (placement["position"]["x"], placement["position"]["z"])
        scale = placement["scale"]
        radius = max(contract["bounds"]["size"][0], contract["bounds"]["size"][2]) * 0.5 * scale
        route_clearance = min(
            abs(math.hypot(*center) - 6.0),
            *(polyline_distance(center, route) for route in routes),
        ) - radius
        pad_clearance = min(rectangle_clearance(center, radius, slot) for slot in slots)
        plaza_clearance = math.hypot(*center) - radius - 3.1
        deck_margin = DECK_RADIUS - math.hypot(*center) - radius
        item = {
            "footprintRadius": round(radius, 6),
            "routeClearance": round(route_clearance, 6),
            "padClearance": round(pad_clearance, 6),
            "plazaClearance": round(plaza_clearance, 6),
            "deckEdgeMargin": round(deck_margin, 6),
        }
        assert route_clearance >= 1.0
        assert pad_clearance >= 1.0
        assert plaza_clearance >= 1.0
        assert deck_margin >= 1.0
        evidence[placement["id"]] = item
    return evidence


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["epoch"] == 10 and manifest["floodReset"] is True
    assert manifest["atlas"] == ATLAS.name
    assert manifest["progressionVariants"]["engineGlow"] == [
        "engine-glow-idle.e10.glb", "engine-glow-cruise.e10.glb", "engine-glow-ward.e10.glb",
    ]
    assert len(manifest["props"]) == 3
    assert len({item["id"] for item in manifest["props"]}) == len(manifest["props"])
    assert ATLAS.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"

    # The source atlas stays full resolution; verify the factory-sized derivative too.
    recipe = load("e10_prop_atlas_recipe", HERE / "build_era_props_e10.py")
    atlas = next(node.image for node in recipe.material().node_tree.nodes if node.type == "TEX_IMAGE")
    assert list(atlas.size) == [512, 512] and atlas.packed_file
    embedded_atlas_sha256 = hashlib.sha256(atlas.packed_file.data).hexdigest()

    stable_keys = (
        "nodes", "nodeCount", "bindings", "nodeTransforms", "meshes", "meshNames", "primitives",
        "primitiveMaterials", "triangles", "morphTargets", "targetCounts", "materials",
        "materialTextureBindings", "materialContract", "textureSources", "images", "embeddedImages",
        "imageDimensions", "cameras", "lights", "animations", "bounds",
    )
    evidence = {
        "baseSha": BASE_SHA,
        "bundleRequirement": "Bridge School + Charter Press with child lever + Ark persistence rack + idle/cruise/ward engine-glow states",
        "siteReset": "E10 floodReset:true; no Basin Rim accessories survive into the Ark deck",
        "stateBoundary": "engine glow siblings are banked; ordinary era-prop manifest has no engine-state selector",
        "sharedAtlas": {"path": str(ATLAS.relative_to(ROOT)), "sha256": sha256(ATLAS), "size": [1024, 1024],
                        "embeddedSize": [512, 512], "embeddedSha256": embedded_atlas_sha256},
        "assets": {},
    }
    contracts = {}
    for stem, node_name in ASSETS.items():
        path = HERE / f"{stem}.glb"
        checked = glb.contract(path)
        reproduced_path = Path(f"/tmp/{stem}-reexport.glb")
        reproduced = reexport(stem, reproduced_path)
        item = {
            "checked": checked,
            "reexported": reproduced,
            "byteIdentical": checked["sha256"] == reproduced["sha256"],
            "semanticIdentical": {key: checked[key] == reproduced[key] for key in stable_keys},
            "embeddedAtlasSha256": embedded_image_hash(path),
        }
        evidence["assets"][stem] = item
        contracts[stem] = checked
        assert checked["nodes"] == [node_name]
        assert checked["nodeCount"] == checked["meshes"] == checked["primitives"] == 1
        assert checked["primitiveMaterials"] == [0]
        assert checked["triangles"] <= 1_000
        assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
        assert checked["imageDimensions"] == [[512, 512]]
        assert checked["materialTextureBindings"] == [{"material": 0, "baseColorTexture": 0, "image": 0}]
        assert checked["textureSources"] == [0]
        assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
        assert abs(checked["bounds"]["min"][1]) <= 0.001
        assert item["byteIdentical"] and all(item["semanticIdentical"].values())
        reproduced_path.unlink(missing_ok=True)

    embedded_hashes = {item["embeddedAtlasSha256"] for item in evidence["assets"].values()}
    assert embedded_hashes == {evidence["sharedAtlas"]["embeddedSha256"]}
    evidence["placementClearance"] = placement_evidence(manifest, contracts)
    evidence["manifest"] = manifest
    destination = OUT / "e10-ark-props-contract.json"
    destination.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({
        "baseSha": BASE_SHA,
        "assets": {stem: {
            "triangles": item["checked"]["triangles"],
            "sha256": item["checked"]["sha256"],
            "byteIdentical": item["byteIdentical"],
        } for stem, item in evidence["assets"].items()},
        "placementClearance": evidence["placementClearance"],
    }, indent=2))


if __name__ == "__main__":
    main()
