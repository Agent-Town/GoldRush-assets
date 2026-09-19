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
OUT = ROOT / "artifacts/dome-orbital-era-props"
BASE_SHA = "00200c722be8ec618a156b775f2f35f035bc5158"
ATLAS = HERE / "era-props-e8-atlas.png"
MANIFEST = HERE / "era-props.e8.json"
LAYOUT = ROOT / "artifacts/dome-commons-e8/dome-commons-layout-contract.json"
ASSETS = {
    "crater-rim-set.e8": "CraterRimSetE8",
    "lander-legs.e8": "LanderLegsE8",
    "journey-flag-line.e8": "JourneyFlagLineE8",
}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


glb = load("e8_prop_glb_contract", ROOT / "assets/pilots/dredge-queen-3d/verify_dredge_queen.py")


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


def segment_distance(point: tuple[float, float], start: tuple[float, float], end: tuple[float, float]) -> float:
    px, pz = point
    ax, az = start
    bx, bz = end
    dx, dz = bx - ax, bz - az
    length_squared = dx * dx + dz * dz
    if length_squared <= 1e-12:
        return math.hypot(px - ax, pz - az)
    t = max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / length_squared))
    return math.hypot(px - (ax + dx * t), pz - (az + dz * t))


def radial_route(destination: tuple[float, float], index: int) -> list[tuple[float, float]]:
    dx, dz = destination
    length = max(1.0, math.hypot(dx, dz))
    bend = (1 if index % 2 == 0 else -1) * 0.34
    control = (dx * 0.5 + (-dz / length) * bend, dz * 0.5 + (dx / length) * bend)
    points = []
    for step in range(7):
        t = step / 6
        points.append((2 * (1 - t) * t * control[0] + t * t * dx,
                       2 * (1 - t) * t * control[1] + t * t * dz))
    return points


def polyline_distance(point: tuple[float, float], points: list[tuple[float, float]]) -> float:
    return min(segment_distance(point, a, b) for a, b in zip(points, points[1:]))


def clearance_evidence(manifest: dict, contracts: dict) -> dict:
    layout = json.loads(LAYOUT.read_text())
    pads = [*layout["canonicalSlots"], *layout["orbitalPads"]]
    destinations = [tuple(slot["approach"]) for slot in layout["canonicalSlots"][:7]] + [(0.0, 14.5)]
    routes = [radial_route(destination, index) for index, destination in enumerate(destinations)]
    evidence = {}
    for placement in manifest["props"]:
        stem = placement["glb"].removesuffix(".glb")
        contract = contracts[stem]
        center = (placement["position"]["x"], placement["position"]["z"])
        scale = placement["scale"]
        footprint_radius = max(contract["bounds"]["size"][0], contract["bounds"]["size"][2]) * 0.5 * scale
        route_distance = min(
            abs(math.hypot(*center) - 6.0),
            *(polyline_distance(center, route) for route in routes),
        ) - footprint_radius
        pad_distance = min(
            math.hypot(center[0] - pad["position"][0], center[1] - pad["position"][1])
            - math.hypot(pad["footprint"][0], pad["footprint"][1]) * 0.5
            - footprint_radius
            for pad in pads
        )
        plaza_distance = math.hypot(*center) - footprint_radius - layout["laws"]["plazaCenterOpen"]
        dome_margin = layout["production"]["dome"]["radius"] - math.hypot(*center) - footprint_radius
        item = {
            "footprintRadius": round(footprint_radius, 6),
            "routeClearance": round(route_distance, 6),
            "padClearance": round(pad_distance, 6),
            "plazaClearance": round(plaza_distance, 6),
            "domeEdgeMargin": round(dome_margin, 6),
        }
        assert route_distance >= 1.0
        assert pad_distance >= 1.0
        assert plaza_distance >= 1.0
        assert dome_margin >= 1.0
        evidence[placement["id"]] = item
    return evidence


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["epoch"] == 8 and manifest["floodReset"] is True
    assert manifest["atlas"] == ATLAS.name
    assert len(manifest["props"]) == 3
    assert {item["glb"] for item in manifest["props"]} == {f"{stem}.glb" for stem in ASSETS}
    assert len({item["id"] for item in manifest["props"]}) == len(manifest["props"])
    assert ATLAS.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"

    # The source atlas stays full resolution; verify the factory-sized derivative too.
    recipe = load("e8_prop_atlas_recipe", HERE / "build_era_props_e8.py")
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
        "bundleRequirement": "crater rim set + lander legs + eight pictogram-only journey crests",
        "siteReset": "E8 floodReset:true; no E5 harbor accessories survive into Dome Commons",
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
        assert checked["materialContract"] == [{
            "metallicFactor": 0,
            "roughnessFactor": 0.8999999761581421,
            "doubleSided": True,
            "hasBaseColorTexture": True,
            "hasEmissiveTexture": False,
            "emissiveFactor": [0.0, 0.0, 0.0],
        }]
        assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
        assert abs(checked["bounds"]["min"][1]) <= 0.001
        assert item["byteIdentical"] and all(item["semanticIdentical"].values())
        reproduced_path.unlink(missing_ok=True)

    embedded_hashes = {item["embeddedAtlasSha256"] for item in evidence["assets"].values()}
    assert embedded_hashes == {evidence["sharedAtlas"]["embeddedSha256"]}
    evidence["placementClearance"] = clearance_evidence(manifest, contracts)
    evidence["manifest"] = manifest
    destination = OUT / "e8-orbital-props-contract.json"
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
