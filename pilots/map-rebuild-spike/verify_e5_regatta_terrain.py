"""Strict E5 Regatta terrain, panorama, mask, and evidence verifier."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess

import bpy


ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"
TABLE = ROOT / "assets/contracts/epoch-5-deepwater/mask-tables/e5-regatta.json"
STEM = "regatta-terrain"
KEY = "regatta"
BOARDS = {
    "regatta-mood-ab.png": (1920, 684),
    "regatta-flat-vs-sculpted-ab.png": (1920, 684),
    "regatta-owner-verdict.png": (1920, 504),
    "regatta-panorama-mood-ab.png": (1920, 504),
    "regatta-panorama-distance-gate.png": (1920, 684),
    "regatta-mask-agreement-board.png": (1280, 1260),
}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shared = load_module("e5_regatta_shared_verify", SOURCE / "verify_contract_terrains.py")
builder = load_module("e5_regatta_builder_verify", SOURCE / "build_e5_regatta_terrain.py")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_size(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR"
    return struct.unpack(">II", data[16:24])


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
    bpy.ops.export_scene.gltf(filepath=str(output), export_format="GLB", use_selection=True, export_apply=True, export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT", export_extras=True)
    return meshes[0]


def vertex_height(mesh, x, game_z):
    xi = round((x + builder.WIDTH * 0.5) / (builder.WIDTH / builder.e3.SEGMENTS))
    zi = round((game_z + builder.HEIGHT * 0.5) / (builder.HEIGHT / builder.e3.SEGMENTS))
    return float(mesh.data.vertices[zi * (builder.e3.SEGMENTS + 1) + xi].co.z)


def verify_asset(stem, triangle_count, panorama=False):
    blend = SOURCE / f"{stem}.blend"
    glb = SOURCE / f"{stem}.glb"
    atlas = SOURCE / f"{stem}-atlas.png"
    contract = json.loads((SOURCE / f"{stem}-contract.json").read_text(encoding="utf-8"))
    checked = semantic_contract(glb)
    document, binary = shared.glb_parts(glb)
    texture = shared.embedded_texture(document, binary)
    reexport = Path(f"/tmp/gold-rush-{stem}-reexport.glb")
    mesh = reexport_from_blend(blend, reexport)
    rechecked = semantic_contract(reexport)
    semantic_keys = ("meshes", "primitives", "triangles", "materials", "images", "embeddedImages", "cameras", "lights", "animations", "bounds", "materialContract")
    assert all(checked[field] == rechecked[field] for field in semantic_keys)
    assert glb.read_bytes() == reexport.read_bytes()
    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] == contract["triangles"] == triangle_count
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert texture["width"] == texture["height"] == 2048
    assert texture["sha256"] == sha256(atlas) == contract["files"]["atlas"]["sha256"]
    assert sha256(glb) == contract["files"]["glb"]["sha256"]
    assert sha256(blend) == contract["files"]["blend"]["sha256"]
    if panorama:
        assert triangle_count <= 4_000
        assert contract["lawVersion"] == "PANORAMA LAW v2"
        assert contract["nonInterference"]["waterBuildSpawnMasks"] == "unchanged"
        assert contract["projection"]["groundSkirtRole"].startswith("submerged scenery apron")
        assert contract["projection"]["groundSkirtOuterRadiusMeters"] == 190.0
    else:
        published = json.loads(TABLE.read_text(encoding="utf-8"))
        extras = document["nodes"][0]["extras"]
        assert triangle_count <= 60_000
        assert extras["contract_id"] == extras["tile_id"] == "e5-regatta"
        assert extras["water_surface_owner"] == "runtime; absent from this GLB"
        assert contract["maskTruth"] == published["maskTruth"]
        assert contract["waterSurface"]["includedInTerrainGLB"] is False
        assert contract["landmarkMounts"] == []
        assert max(vertex.co.z for vertex in mesh.data.vertices) <= -0.42
    return checked, mesh


def main():
    terrain, mesh = verify_asset(STEM, 32_768)
    probes = {
        "startBeacon": vertex_height(mesh, -49.0, 0.0),
        "midcourseBeacon": vertex_height(mesh, 0.0, 18.0),
        "fastWaterFloor": vertex_height(mesh, 0.0, 46.0),
        "openWaterFloor": vertex_height(mesh, 0.0, -24.0),
    }
    panorama, _panorama_mesh = verify_asset(f"{KEY}-panorama", 2_704, panorama=True)
    assert probes["startBeacon"] > -2.7
    assert probes["midcourseBeacon"] > -2.7
    assert probes["fastWaterFloor"] < -4.8
    assert -4.2 < probes["openWaterFloor"] < -2.7
    boards = {}
    for name, expected in BOARDS.items():
        path = ARTIFACTS / name
        assert png_size(path) == expected
        boards[name] = {"size": expected, "bytes": path.stat().st_size, "sha256": sha256(path)}
    evidence = {
        "blender": bpy.app.version_string,
        "freshReferenceBaseSha": subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True).strip(),
        "maskTable": str(TABLE.relative_to(ROOT)),
        "terrain": terrain,
        "panorama": panorama,
        "bathymetryProbes": {key: round(value, 4) for key, value in probes.items()},
        "boards": boards,
        "variantReuse": {
            "e5-flotilla": "reuses tileId e5-deepwater-claim; no new sculpt",
            "e5-stillwater": "reuses tileId e5-deepwater-claim; no new sculpt",
        },
    }
    evidence_path = ARTIFACTS / "regatta-asset-contract.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    (ARTIFACTS / "regatta-reexport-evidence.md").write_text(
        "# E5 Regatta re-export evidence\n\n"
        "- Terrain: one bathymetry mesh, one material, one embedded 2048 atlas, 32,768 triangles.\n"
        "- Panorama: separate one-mesh, one-material, one embedded 2048 atlas, 2,704 triangles.\n"
        "- Re-export: byte-identical and semantic-identical for both GLBs.\n"
        "- Water: runtime-owned; no sea surface, fast-water state, or classification is exported.\n"
        "- Masks: exact published Regatta table; five beacons, storm-front zone, runtime deck, and west spawn unchanged.\n"
        "- Reuse: Flotilla and Stillwater keep the existing Deepwater Claim terrain because both contracts reuse that tileId.\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "evidence": str(evidence_path)}, indent=2))


if __name__ == "__main__":
    main()
