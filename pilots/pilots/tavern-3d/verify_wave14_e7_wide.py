from collections import Counter
from pathlib import Path
import importlib.util
import json
import subprocess
import sys

import bpy


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "artifacts/town-e7-wide"
TEMP = Path("/tmp/gold-rush-wave14-e7-verify")
BASE_SHA = "3fe1e493fb11b6685f1ffc76b65dd81ebff8dd6b"
E6_WIDE_REF = "origin/sol/mesa-town-e6-wide"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


verify = load_module("wave14_e7_contract_helpers", HERE / "verify_wave7_e2_variants.py")

ASSETS = {
    "playbook_library": {
        "blend": ROOT / "assets/pilots/playbook-library-3d/playbook-library.blend",
        "glb": ROOT / "assets/pilots/playbook-library-3d/playbook-library.glb",
        "object": "PlaybookLibraryE7", "budget": 15_000, "footprint": [6.2, 5.0],
    },
    "drone_coop": {
        "blend": ROOT / "assets/pilots/drone-coop-3d/drone-coop.blend",
        "glb": ROOT / "assets/pilots/drone-coop-3d/drone-coop.glb",
        "object": "DroneCoopE7", "budget": 15_000, "footprint": [4.5, 4.5],
    },
    "signal_refinery": {
        "blend": ROOT / "assets/pilots/signal-refinery-3d/signal-refinery.blend",
        "glb": ROOT / "assets/pilots/signal-refinery-3d/signal-refinery.glb",
        "object": "SignalRefineryE7", "budget": 15_000, "footprint": [6.2, 5.1],
    },
    "beam_relay": {
        "blend": ROOT / "assets/pilots/run3d/turret.e7.blend",
        "glb": ROOT / "assets/pilots/run3d/turret.e7.glb",
        "object": "BeamRelayTurretE7", "budget": 15_000, "footprint": [1.35, 1.35],
        "source": {
            "blend": "assets/pilots/run3d/turret.e6.blend",
            "blendSha": "2459bdc55bdcf063d3d7282d526374a8f0832341277ce391fe321075928e18c5",
            "glb": "assets/pilots/run3d/turret.e6.glb",
            "glbSha": "44d17919c60e294bbe977736a01ce93bf1a9f72a8ed85ca4b167a305b5cf1bbe",
            "object": "SunlineMountE6",
        },
    },
    "signal_works": {
        "blend": ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.e7.blend",
        "glb": ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.e7.glb",
        "object": "SignalWorksE7", "budget": 15_000, "footprint": [3.96, 3.375],
        "source": {
            "blend": "assets/pilots/schoolhouse-3d/schoolhouse.e6.blend",
            "blendSha": "7be45aeb005544b861297aced589c7be17420ca5096067fb8e3b5aadbbf92825",
            "glb": "assets/pilots/schoolhouse-3d/schoolhouse.e6.glb",
            "glbSha": "f3de54fb073729e1b251f0809b9ea65b2f869afd9c731430454636c03351bfb3",
            "object": "IsotopeInstituteE6",
        },
    },
    "tape_post": {
        "blend": ROOT / "assets/pilots/catalog-warehouse-3d/catalog-warehouse.e7.blend",
        "glb": ROOT / "assets/pilots/catalog-warehouse-3d/catalog-warehouse.e7.glb",
        "object": "TapePostE7", "budget": 15_000, "footprint": [5.58677, 3.7425],
        "source": {
            "blend": "assets/pilots/catalog-warehouse-3d/catalog-warehouse.blend",
            "blendSha": "596b964914b73b8e5c4457b62cd1cff6dba038c52c6c86ef23afe48f5a9e05e2",
            "glb": "assets/pilots/catalog-warehouse-3d/catalog-warehouse.glb",
            "glbSha": "f72109125d3c036a3ac8a06004fa212f02539c762076dd9959c30cd578fcce24",
            "object": "CatalogWarehouseE6",
        },
    },
}

SEMANTIC_KEYS = (
    "meshes", "primitives", "nodes", "anchors", "triangles", "materials", "images",
    "embeddedImages", "imageDimensions", "cameras", "lights", "animations", "bounds",
    "materialContract",
)


def extract_source(asset_id, source):
    TEMP.mkdir(parents=True, exist_ok=True)
    paths = {}
    for kind in ("blend", "glb"):
        target = TEMP / f"{asset_id}-source.{kind}"
        with target.open("wb") as handle:
            subprocess.run(["git", "show", f"{E6_WIDE_REF}:{source[kind]}"],
                           cwd=ROOT, stdout=handle, check=True)
        assert verify.sha256(target) == source[f"{kind}Sha"]
        paths[kind] = target
    return paths


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
        export_cameras=False, export_lights=False, export_animations=False,
        export_materials="EXPORT",
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


def inheritance_check(asset_id, spec):
    source = spec["source"]
    paths = extract_source(asset_id, source)
    source_polygons, source_triangles, source_vertices = mesh_polygon_signatures(
        paths["blend"], source["object"],
    )
    candidate_polygons, candidate_triangles, candidate_vertices = mesh_polygon_signatures(
        spec["blend"], spec["object"],
    )
    missing = source_polygons - candidate_polygons
    source_contract = verify.contract(paths["glb"])
    candidate_contract = verify.contract(spec["glb"])
    source_footprint = [source_contract["bounds"]["size"][0], source_contract["bounds"]["size"][2]]
    candidate_footprint = [candidate_contract["bounds"]["size"][0], candidate_contract["bounds"]["size"][2]]
    result = {
        "sourceBlendSha256": verify.sha256(paths["blend"]),
        "sourceGlbSha256": verify.sha256(paths["glb"]),
        "sourceTriangles": source_triangles,
        "candidateTriangles": candidate_triangles,
        "sourceVertices": source_vertices,
        "candidateVertices": candidate_vertices,
        "sourcePolygonSignatures": sum(source_polygons.values()),
        "missingSourcePolygonSignatures": sum(missing.values()),
        "exactFootprint": {"sourceXZ": source_footprint, "candidateXZ": candidate_footprint},
        "passed": not missing and source_footprint == candidate_footprint,
    }
    assert result["sourceBlendSha256"] == source["blendSha"]
    assert result["sourceGlbSha256"] == source["glbSha"]
    assert result["passed"], result
    return result


def check_asset(asset_id, spec):
    checked = verify.contract(spec["glb"])
    reexport_path = Path("/tmp") / f"{spec['glb'].stem}-wave14-reexport.glb"
    export_saved_blend(spec, reexport_path)
    reexported = verify.contract(reexport_path)
    material = checked["materialContract"][0]
    size = checked["bounds"]["size"]
    item = {
        "checked": checked,
        "reexported": reexported,
        "byteIdentical": checked["sha256"] == reexported["sha256"],
        "semanticIdentical": {key: checked[key] == reexported[key] for key in SEMANTIC_KEYS},
        "footprintGate": {
            "actualXZ": [size[0], size[2]],
            "maximumXZ": spec["footprint"],
            "passed": size[0] <= spec["footprint"][0] + 0.001
            and size[2] <= spec["footprint"][1] + 0.001,
        },
    }
    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["nodes"] == [spec["object"]]
    assert checked["anchors"] == []
    assert checked["triangles"] <= spec["budget"]
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert len(checked["imageDimensions"]) == 1
    assert max(checked["imageDimensions"][0]) <= 1024
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert abs(checked["bounds"]["min"][1]) < 0.001
    assert material["metallicFactor"] == 0 and material["roughnessFactor"] >= 0.899
    assert material["hasBaseColorTexture"] and not material["hasEmissiveTexture"]
    assert item["footprintGate"]["passed"]
    assert item["byteIdentical"] and all(item["semanticIdentical"].values())
    if "source" in spec:
        item["inheritance"] = inheritance_check(asset_id, spec)
    return item


def check_visual_evidence():
    contract_path = OUT / "visual-evidence-contract.json"
    evidence = json.loads(contract_path.read_text())
    metrics = evidence["comparisonMetrics"]
    luminance_percent = metrics["avgLuminanceDelta"] / metrics["avgLuminanceBase"] * 100.0
    assert evidence["baseSha"] == BASE_SHA
    assert metrics["diffRatio16"] > 0.10
    assert metrics["edgeEnergyRatio"] > 1.10
    assert abs(luminance_percent) <= 5.0
    required = [
        OUT / "current-references" / f"{BASE_SHA[:12]}-main" / "town-e1-e4-e5-current.png",
        OUT / "mesa-e7-wide-across-plaza-ab.png",
        OUT / "mesa-e7-wide-key-feature-crop.png",
        *[OUT / "turntables" / f"{name}-e7.png" for name in (
            "playbook-library", "drone-coop", "signal-refinery",
            "beam-relay", "signal-works", "tape-post",
        )],
        *[OUT / "identity" / f"{name}-identity-e6-e7-ab.png" for name in (
            "beam-relay", "signal-works", "tape-post",
        )],
    ]
    assert all(path.is_file() for path in required), [str(path) for path in required if not path.is_file()]
    return {
        "path": str(contract_path.relative_to(ROOT)),
        "baseSha": evidence["baseSha"],
        "diffRatio16": metrics["diffRatio16"],
        "edgeEnergyRatio": metrics["edgeEnergyRatio"],
        "luminanceDeltaPercent": luminance_percent,
        "renderCount": len(required),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    evidence = {
        "blender": bpy.app.version_string,
        "scope": "E7 Signal Mesa wide completion",
        "laws": {
            "source": "specs/epoch-saga/e7-signal-bundle.md section A",
            "accretion": "three E6 transforms retain every source polygon and exact footprint",
            "materials": "one embedded painted atlas per GLB; no emission or helpers",
            "budget": "15,000 triangles per asset",
            "anchors": "none invented; E7 bundle and queue define no emitter-anchor family",
        },
        "assets": {asset_id: check_asset(asset_id, spec) for asset_id, spec in ASSETS.items()},
        "visualEvidence": check_visual_evidence(),
        "cadence": {
            "netCafe": "PERSIST E6 diner and jukebox; UPGRADE to E7 terminal service (pilot)",
            "sunlineMount": "PERSIST complete E6 body; UPGRADE to beam relay",
            "isotopeInstitute": "PERSIST complete E6 body; UPGRADE to Signal Works",
            "catalogWarehouse": "PERSIST complete E6 body; UPGRADE parcel office to Tape Post",
            "reactorDome": "CARRIED UNCHANGED; E7 signal does not plausibly rebuild containment",
            "isotopeKitchen": "CARRIED UNCHANGED; service continues beside the new refinery",
            "decayClock": "CARRIED UNCHANGED; signal does not replace atomic civic timing",
            "appliancePen": "CARRIED UNCHANGED; captured appliances remain useful",
            "glowFence": "CARRIED UNCHANGED; no E7 transform is named",
            "panMonument": "PERSIST unchanged under heritage law",
        },
    }
    output = OUT / "asset-contract.json"
    output.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
