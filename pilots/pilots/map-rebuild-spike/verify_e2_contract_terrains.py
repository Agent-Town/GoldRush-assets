"""Verify the complete authored E2 terrain/panorama family and evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct

import bpy


ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"
FACTORY = ROOT / "assets/contracts/epoch-2-steamworks/contracts.json"
MASK_TABLES = ROOT / "assets/contracts/epoch-2-steamworks/mask-tables"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shared = load_module("e2_shared_verify", SOURCE / "verify_contract_terrains.py")
builder = load_module("e2_builder_verify", SOURCE / "build_e2_contract_terrains.py")

MAPS = {
    "hill-mine": {"id": "e2-hill-mine", "stem": "hill-mine-terrain", "mounts": 5},
    "trestle": {"id": "e2-trestle", "stem": "trestle-terrain", "mounts": 6},
    "pressure-garden": {"id": "e2-pressure-garden", "stem": "pressure-garden-terrain", "mounts": 5},
    "incline": {"id": "e2-incline", "stem": "incline-terrain", "mounts": 5},
}
BOARDS = {
    "e2-mood-ab.png": (1920, 2412),
    "e2-flat-vs-sculpted-ab.png": (1920, 2412),
    "e2-owner-verdict.png": (1920, 1692),
    "e2-panorama-mood-ab.png": (1920, 1692),
    "e2-panorama-distance-gate.png": (1920, 2412),
    "e2-mask-agreement-board.png": (1920, 2412),
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_size(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR"
    return struct.unpack(">II", data[16:24])


def factory_contract(contract_id):
    document = json.loads(FACTORY.read_text(encoding="utf-8"))
    matches = [entry for entry in document["contracts"] if entry["id"] == contract_id]
    assert len(matches) == 1
    return matches[0]


def expected_mask(key, factory):
    path = MASK_TABLES / f"e2-{key}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else builder.authored_mask(key, factory)


def semantic_contract(path):
    return shared.verify.contract(path)


def reexport_from_blend(blend, output):
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    assert len(meshes) == 1
    assert not [obj for obj in bpy.data.objects if obj.type == "CAMERA"]
    assert not [obj for obj in bpy.data.objects if obj.type == "LIGHT"]
    bpy.ops.object.select_all(action="DESELECT")
    meshes[0].select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(
        filepath=str(output),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_materials="EXPORT",
        export_extras=True,
    )
    return meshes[0]


def mesh_height(mesh, x, game_z):
    step = 96.0 / builder.SEGMENTS
    xi = round((x + builder.HALF) / step)
    zi = round((game_z + builder.HALF) / step)
    sampled_x = -builder.HALF + xi * step
    sampled_z = -builder.HALF + zi * step
    height = float(mesh.data.vertices[zi * (builder.SEGMENTS + 1) + xi].co.z)
    return sampled_x, sampled_z, height


def geometry_probes(key, mesh, factory):
    height_at = builder.height_function(key, factory)
    if key == "hill-mine":
        points = [(0, 12), (-30, 25), (30, 25), (-30, 42), (30, 42), (0, 20), (0, 0)]
    elif key == "trestle":
        points = [(0, -18), (0, 18), (-24, -20), (24, 20), (0, 0), (30, 0)]
    elif key == "pressure-garden":
        points = [(-12, 12), (0, 12), (12, 12), (-30, 24), (30, 24), (-12, 39), (3, 39), (0, 0)]
    else:
        points = [(-24, -18), (0, 40), (-30, -20), (-30, 26), (-22, 40), (-12, 0), (12, 0)]
    probes = []
    for x, z in points:
        sampled_x, sampled_z, actual = mesh_height(mesh, x, z)
        expected = float(height_at(sampled_x, sampled_z))
        assert abs(actual - expected) < 0.0002
        probes.append({"requested": [x, z], "sampled": [sampled_x, sampled_z], "height": round(actual, 4)})
    return probes


def verify_terrain(key, config):
    stem = config["stem"]
    blend = SOURCE / f"{stem}.blend"
    glb = SOURCE / f"{stem}.glb"
    atlas = SOURCE / f"{stem}-atlas.png"
    contract_path = SOURCE / f"{stem}-contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    factory = factory_contract(config["id"])
    mask_document = expected_mask(key, factory)
    checked = semantic_contract(glb)
    document, binary = shared.glb_parts(glb)
    texture = shared.embedded_texture(document, binary)
    extras = document["nodes"][0]["extras"]

    reexport = Path("/tmp") / f"gold-rush-{stem}-reexport.glb"
    mesh = reexport_from_blend(blend, reexport)
    rechecked = semantic_contract(reexport)
    semantic_keys = (
        "meshes", "primitives", "triangles", "materials", "images", "embeddedImages",
        "cameras", "lights", "animations", "bounds", "materialContract",
    )
    semantic_identical = all(checked[field] == rechecked[field] for field in semantic_keys)
    byte_identical = glb.read_bytes() == reexport.read_bytes()

    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] == contract["triangles"] == 32_768 <= 60_000
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert checked["materialContract"][0]["metallicFactor"] == 0
    assert checked["materialContract"][0]["roughnessFactor"] >= 0.89
    assert checked["materialContract"][0]["hasBaseColorTexture"]
    assert texture["width"] == texture["height"] == 2048
    assert texture["sha256"] == sha256(atlas) == contract["files"]["atlas"]["sha256"]
    assert sha256(glb) == contract["files"]["glb"]["sha256"]
    assert sha256(blend) == contract["files"]["blend"]["sha256"]
    assert semantic_identical and byte_identical
    assert extras["render_only"] is True
    assert extras["sim_authority"] == "factory contract tables and TileHeight; unchanged"
    assert extras["height_socket"] == "Terrain.visualY"
    assert extras["contract_id"] == config["id"] and extras["tile_id"] == config["id"]
    assert contract["maskTruth"] == mask_document["maskTruth"]
    assert contract["renderOnly"] is True
    assert contract["waterAgreement"] == mask_document["waterAgreement"]
    if (MASK_TABLES / f"e2-{key}.json").is_file():
        assert contract["waterVisualRuling"].startswith("render bank seam follows")
    assert len(contract["landmarkMounts"]) == config["mounts"]
    assert len({mount["id"] for mount in contract["landmarkMounts"]}) == config["mounts"]
    assert all(
        all(math.isfinite(value) for field in ("position", "rotation", "scale") for value in mount[field])
        and mount["position"][1] == mount.get("terrainConformOffsetY", 0)
        for mount in contract["landmarkMounts"]
    )
    assert "never baked into terrain" in contract["landmarkMountSpace"]["ownership"]
    assert "assets/processed/kit-era-2.png" in contract["sourceArt"]
    assert not any("tree" in source.lower() for source in contract["regionalFamily"]["shared"])

    panorama_contract = json.loads((SOURCE / f"{key}-panorama-contract.json").read_text(encoding="utf-8"))
    assert contract["panoramaMount"] == panorama_contract["mount"]
    probes = geometry_probes(key, mesh, factory)
    return {
        "asset": glb.name,
        "checked": checked,
        "reexported": rechecked,
        "byteIdenticalReexport": byte_identical,
        "semanticIdenticalReexport": semantic_identical,
        "embeddedTexture": texture,
        "extras": extras,
        "geometryProbes": probes,
        "maskSource": contract["maskTruth"]["source"],
        "landmarkMountIds": [mount["id"] for mount in contract["landmarkMounts"]],
    }


def verify_panorama(key):
    blend = SOURCE / f"{key}-panorama.blend"
    glb = SOURCE / f"{key}-panorama.glb"
    atlas = SOURCE / f"{key}-panorama-atlas.png"
    contract = json.loads((SOURCE / f"{key}-panorama-contract.json").read_text(encoding="utf-8"))
    checked = semantic_contract(glb)
    document, binary = shared.glb_parts(glb)
    texture = shared.embedded_texture(document, binary)
    extras = document["nodes"][0]["extras"]
    reexport = Path("/tmp") / f"gold-rush-{key}-panorama-reexport.glb"
    reexport_from_blend(blend, reexport)
    rechecked = semantic_contract(reexport)
    semantic_keys = (
        "meshes", "primitives", "triangles", "materials", "images", "embeddedImages",
        "cameras", "lights", "animations", "bounds", "materialContract",
    )
    semantic_identical = all(checked[field] == rechecked[field] for field in semantic_keys)
    byte_identical = glb.read_bytes() == reexport.read_bytes()

    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] == contract["triangles"] <= 4_000
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert texture["width"] == texture["height"] == 2048
    assert texture["sha256"] == sha256(atlas) == contract["files"]["atlas"]["sha256"]
    assert sha256(glb) == contract["files"]["glb"]["sha256"]
    assert sha256(blend) == contract["files"]["blend"]["sha256"]
    assert semantic_identical and byte_identical
    assert extras == {
        "render_only": True,
        "panorama": True,
        "affects_playfield": False,
        "affects_masks": False,
        "affects_spawn_edges": False,
        "affects_fog_gating": False,
        "mount_space": "game X/Y/Z at county origin",
        "panorama_law": "v2",
    }
    assert contract["lawVersion"] == "PANORAMA LAW v2"
    assert set(contract["namedCorrections"]) == {"paintedWall", "ceiling", "echo"}
    assert contract["nonInterference"] == {
        "playfieldBounds": "unchanged",
        "spawnEdges": "unchanged",
        "fogGating": "unchanged",
        "waterBuildSpawnMasks": "unchanged",
    }
    return {
        "asset": glb.name,
        "checked": checked,
        "reexported": rechecked,
        "byteIdenticalReexport": byte_identical,
        "semanticIdenticalReexport": semantic_identical,
        "embeddedTexture": texture,
        "extras": extras,
        "mount": contract["mount"],
    }


def main():
    document = json.loads(FACTORY.read_text(encoding="utf-8"))
    authored_ids = {entry["id"] for entry in document["contracts"]}
    availability = {
        "source": str(FACTORY.relative_to(ROOT)),
        "authored": [contract_id for contract_id in ("e2-hill-mine", "e2-trestle", "e2-pressure-garden", "e2-incline") if contract_id in authored_ids],
        "notAuthored": [contract_id for contract_id in ("e2-hill-mine", "e2-trestle", "e2-pressure-garden", "e2-incline") if contract_id not in authored_ids],
        "policy": "no terrain is authored before its factory mask table exists",
    }
    assert availability["authored"] == ["e2-hill-mine", "e2-trestle", "e2-pressure-garden", "e2-incline"]
    assert availability["notAuthored"] == []
    (ARTIFACTS / "e2-mask-availability.json").write_text(json.dumps(availability, indent=2) + "\n", encoding="utf-8")

    terrains = {key: verify_terrain(key, config) for key, config in MAPS.items()}
    panoramas = {key: verify_panorama(key) for key in MAPS}
    assert len({result["checked"]["sha256"] for result in terrains.values()}) == len(terrains)
    assert len({result["checked"]["sha256"] for result in panoramas.values()}) == len(panoramas)

    boards = {}
    for name, expected_size in BOARDS.items():
        path = ARTIFACTS / name
        assert png_size(path) == expected_size
        boards[name] = {"size": expected_size, "bytes": path.stat().st_size, "sha256": sha256(path)}

    evidence = {
        "blender": bpy.app.version_string,
        "availability": availability,
        "terrains": terrains,
        "panoramas": panoramas,
        "boards": boards,
        "verdict": {
            "grit": "fight",
            "panorama": "distance",
            "masks": "factory-authored and unchanged",
            "landmarks": "mounted separately",
        },
    }
    evidence_path = ARTIFACTS / "e2-asset-contract.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    (ARTIFACTS / "e2-reexport-evidence.md").write_text(
        "# E2 terrain and panorama re-export evidence\n\n"
        f"- Blender: {bpy.app.version_string}\n"
        "- Authored terrain pairs: Hill Mine, Trestle, Pressure Garden, and Incline.\n"
        "- Terrain GLBs: one mesh, one primitive, one material, one embedded 2048 atlas, 32,768 triangles each.\n"
        "- Panorama GLBs: one mesh, one primitive, one material, one embedded 2048 atlas, all below 4,000 triangles.\n"
        "- Re-export: byte-identical and semantic-identical for all eight GLBs.\n"
        "- Generic wrapper: `scripts/reexport-pilot.sh` omits `export_extras=True`; use only on copies until the factory aligns it.\n"
        "- Simulation authority: factory masks and TileHeight remain unchanged; visual water ends at the gameplay shallows boundary.\n"
        "- Pressure Garden and Incline: published mask tables copied exactly; no gameplay coordinates inferred or changed.\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "evidence": str(evidence_path), "availability": availability}, indent=2))


if __name__ == "__main__":
    main()
