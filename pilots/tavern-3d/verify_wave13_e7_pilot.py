from collections import Counter
from pathlib import Path
import importlib.util
import json
import subprocess
import sys

import bpy


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "artifacts/town-e7-pilot"
TEMP = Path("/tmp/gold-rush-wave13-e7")
BASE_SHA = "88ea5d9bca59dca64f35766b466cc2755751dcbb"
SOURCE_E6_BLEND_SHA = "e329a411267c43e78a2d068c4ad6341ad1d9d8825e427977877124a04d8eea17"
SOURCE_E6_GLB_SHA = "68ec4ed82ec24c42386a2abf6ff0fc4738556be4e380a9f06bc7e3de4478fd74"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


verify = load_module("wave13_e7_contract_helpers", HERE / "verify_wave7_e2_variants.py")


ASSETS = {
    "relay_tower": {
        "blend": ROOT / "assets/pilots/relay-tower-3d/relay-tower.blend",
        "glb": ROOT / "assets/pilots/relay-tower-3d/relay-tower.glb",
        "object": "RelayTowerE7", "budget": 15_000, "footprint": [7.5, 5.0],
    },
    "exchange": {
        "blend": ROOT / "assets/pilots/exchange-3d/exchange.blend",
        "glb": ROOT / "assets/pilots/exchange-3d/exchange.glb",
        "object": "ExchangeE7", "budget": 15_000, "footprint": [6.1, 5.2],
    },
    "net_cafe": {
        "blend": ROOT / "assets/pilots/tavern-3d/tavern.e7.blend",
        "glb": ROOT / "assets/pilots/tavern-3d/tavern.e7.glb",
        "object": "TownTavernE7NetCafe", "budget": 15_000,
        "footprint": [5.130185, 3.3925], "exactSourceFootprint": True,
    },
}

SEMANTIC_KEYS = (
    "meshes", "primitives", "nodes", "anchors", "triangles", "materials", "images",
    "embeddedImages", "imageDimensions", "cameras", "lights", "animations", "bounds",
    "materialContract",
)


def extract(ref, source, target, expected):
    TEMP.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as handle:
        subprocess.run(["git", "show", f"{ref}:{source}"], cwd=ROOT, stdout=handle, check=True)
    assert verify.sha256(target) == expected
    return target


def source_paths():
    local_blend = ROOT / "assets/pilots/tavern-3d/tavern.e6.blend"
    local_glb = ROOT / "assets/pilots/tavern-3d/tavern.e6.glb"
    blend = local_blend if local_blend.is_file() and verify.sha256(local_blend) == SOURCE_E6_BLEND_SHA else extract(
        "origin/sol/mesa-town-e6-pilot", "assets/pilots/tavern-3d/tavern.e6.blend",
        TEMP / "verify-tavern.e6.blend", SOURCE_E6_BLEND_SHA,
    )
    glb = local_glb if local_glb.is_file() and verify.sha256(local_glb) == SOURCE_E6_GLB_SHA else extract(
        "origin/sol/mesa-town-e6-pilot", "assets/pilots/tavern-3d/tavern.e6.glb",
        TEMP / "verify-tavern.e6.glb", SOURCE_E6_GLB_SHA,
    )
    return blend, glb


def export_saved_blend(spec, output):
    bpy.ops.wm.open_mainfile(filepath=str(spec["blend"]))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    helpers = [obj for obj in bpy.data.objects if obj.type in {"EMPTY", "CAMERA", "LIGHT"}]
    assert len(meshes) == 1 and meshes[0].name == spec["object"], [obj.name for obj in meshes]
    assert not helpers, [(obj.name, obj.type) for obj in helpers]
    bpy.ops.object.select_all(action="DESELECT")
    meshes[0].select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(
        filepath=str(output), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT",
    )


def mesh_polygon_signatures(blend, object_name):
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    model = bpy.data.objects[object_name]
    coordinates = [tuple(round(value, 6) for value in vertex.co) for vertex in model.data.vertices]
    polygons = Counter(
        tuple(sorted(coordinates[index] for index in polygon.vertices))
        for polygon in model.data.polygons
    )
    triangles = sum(len(polygon.vertices) - 2 for polygon in model.data.polygons)
    return polygons, triangles, len(model.data.vertices)


def inheritance_check(spec):
    source_blend, source_glb = source_paths()
    source_polygons, source_triangles, source_vertices = mesh_polygon_signatures(
        source_blend, "TownTavernE6AtomicDiner",
    )
    candidate_polygons, candidate_triangles, candidate_vertices = mesh_polygon_signatures(
        spec["blend"], spec["object"],
    )
    missing = source_polygons - candidate_polygons
    source_contract = verify.contract(source_glb)
    candidate_contract = verify.contract(spec["glb"])
    result = {
        "sourceBlendSha256": verify.sha256(source_blend),
        "sourceGlbSha256": verify.sha256(source_glb),
        "sourceTriangles": source_triangles,
        "candidateTriangles": candidate_triangles,
        "sourceVertices": source_vertices,
        "candidateVertices": candidate_vertices,
        "sourcePolygonSignatures": sum(source_polygons.values()),
        "missingSourcePolygonSignatures": sum(missing.values()),
        "exactFootprint": {
            "sourceXZ": [source_contract["bounds"]["size"][0], source_contract["bounds"]["size"][2]],
            "candidateXZ": [candidate_contract["bounds"]["size"][0], candidate_contract["bounds"]["size"][2]],
        },
        "passed": not missing,
    }
    assert result["sourceBlendSha256"] == SOURCE_E6_BLEND_SHA
    assert result["sourceGlbSha256"] == SOURCE_E6_GLB_SHA
    assert not missing
    assert result["exactFootprint"]["sourceXZ"] == result["exactFootprint"]["candidateXZ"]
    return result


def check_asset(asset_id, spec):
    checked = verify.contract(spec["glb"])
    reexport_path = Path("/tmp") / f"{spec['glb'].stem}-wave13-reexport.glb"
    export_saved_blend(spec, reexport_path)
    reexported = verify.contract(reexport_path)
    material = checked["materialContract"][0]
    footprint = checked["bounds"]["size"]
    item = {
        "checked": checked,
        "reexported": reexported,
        "byteIdentical": checked["sha256"] == reexported["sha256"],
        "semanticIdentical": {key: checked[key] == reexported[key] for key in SEMANTIC_KEYS},
        "footprintGate": {
            "actualXZ": [footprint[0], footprint[2]],
            "maximumXZ": spec["footprint"],
            "passed": footprint[0] <= spec["footprint"][0] + 0.001
            and footprint[2] <= spec["footprint"][1] + 0.001,
        },
    }
    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["nodes"] == [spec["object"]]
    assert checked["anchors"] == []
    assert checked["triangles"] <= spec["budget"]
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["imageDimensions"] == [[1024, 1024]]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert abs(checked["bounds"]["min"][1]) < 0.001
    assert material["metallicFactor"] == 0 and material["roughnessFactor"] >= 0.899
    assert material["hasBaseColorTexture"] and not material["hasEmissiveTexture"]
    assert item["footprintGate"]["passed"]
    assert item["byteIdentical"] and all(item["semanticIdentical"].values())
    if asset_id == "net_cafe":
        item["inheritance"] = inheritance_check(spec)
    return item


def check_visual_evidence():
    contract_path = OUT / "visual-evidence-contract.json"
    evidence = json.loads(contract_path.read_text())
    metrics = evidence["comparisonMetrics"]
    assert evidence["baseSha"] == BASE_SHA
    assert evidence["dependencies"]["mesa"]["sha256"] == (
        "067c8c652134258379315a41200caf423ff3e9cb70a1b9d8f2607ee691aafdc3"
    )
    assert metrics["diffRatio16"] > 0.05
    assert metrics["edgeEnergyRatio"] > 1.10
    assert abs(metrics["avgLuminanceDelta"] / metrics["avgLuminanceBase"] * 100.0) <= 5.0
    required = [
        OUT / "current-references" / f"{BASE_SHA[:12]}-main" / "town-e1-e4-e5-current.png",
        OUT / "mesa-e7-pilot-across-plaza-ab.png",
        OUT / "mesa-e7-pilot-key-feature-crop.png",
        *[OUT / "turntables" / f"{name}.png" for name in (
            "relay-tower-e7", "exchange-e7", "net-cafe-e7",
        )],
        OUT / "identity" / "net-cafe-identity-e6-e7-ab.png",
    ]
    assert all(path.is_file() for path in required)
    return {
        "path": str(contract_path.relative_to(ROOT)),
        "baseSha": evidence["baseSha"],
        "diffRatio16": metrics["diffRatio16"],
        "edgeEnergyRatio": metrics["edgeEnergyRatio"],
        "luminanceDeltaPercent": metrics["avgLuminanceDelta"] / metrics["avgLuminanceBase"] * 100.0,
        "renderCount": len(required),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    evidence = {
        "blender": bpy.app.version_string,
        "scope": "E7 Signal Mesa three-asset verdict pilot",
        "laws": {
            "source": "specs/epoch-saga/e7-signal-bundle.md §A",
            "accretion": "Net Cafe retains the complete E6 Atomic Diner mesh and exact footprint",
            "materials": "one embedded painted atlas per GLB; no emission or helpers",
            "budget": "15,000 triangles per asset",
            "anchors": "none invented; E7 bundle and queue define no emitter-anchor family",
        },
        "assets": {asset_id: check_asset(asset_id, spec) for asset_id, spec in ASSETS.items()},
        "visualEvidence": check_visual_evidence(),
    }
    (OUT / "asset-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
