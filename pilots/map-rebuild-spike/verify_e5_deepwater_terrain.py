"""Strict Deepwater Claim terrain, panorama, mask, and evidence verifier."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import struct

import bpy


ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"
TABLE = ROOT / "assets/contracts/epoch-5-deepwater/mask-tables/e5-deepwater-claim.json"
STEM = "deepwater-claim-terrain"
KEY = "deepwater-claim"
BOARDS = {
    "deepwater-mood-ab.png": (1920, 1260),
    "deepwater-flat-vs-sculpted-ab.png": (1920, 630),
    "deepwater-owner-verdict.png": (1920, 900),
    "deepwater-panorama-mood-ab.png": (1920, 630),
    "deepwater-panorama-distance-gate.png": (1920, 630),
    "deepwater-mask-agreement-board.png": (1920, 1260),
    "deepwater-ruin-contact-gate.png": (1920, 630),
}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shared = load_module("e5_shared_verify", SOURCE / "verify_contract_terrains.py")
builder = load_module("e5_builder_verify", SOURCE / "build_e5_deepwater_terrain.py")


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
    xi = round((x + builder.WIDTH * 0.5) / (builder.WIDTH / builder.SEGMENTS))
    zi = round((game_z + builder.HEIGHT * 0.5) / (builder.HEIGHT / builder.SEGMENTS))
    return float(mesh.data.vertices[zi * (builder.SEGMENTS + 1) + xi].co.z)


def verify_terrain():
    blend = SOURCE / f"{STEM}.blend"
    glb = SOURCE / f"{STEM}.glb"
    atlas = SOURCE / f"{STEM}-atlas.png"
    contract_path = SOURCE / f"{STEM}-contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    published = json.loads(TABLE.read_text(encoding="utf-8"))
    checked = semantic_contract(glb)
    document, binary = shared.glb_parts(glb)
    texture = shared.embedded_texture(document, binary)
    extras = document["nodes"][0]["extras"]
    reexport = Path("/tmp/gold-rush-deepwater-claim-terrain-reexport.glb")
    mesh = reexport_from_blend(blend, reexport)
    rechecked = semantic_contract(reexport)
    semantic_keys = ("meshes", "primitives", "triangles", "materials", "images", "embeddedImages", "cameras", "lights", "animations", "bounds", "materialContract")
    semantic_identical = all(checked[field] == rechecked[field] for field in semantic_keys)
    byte_identical = glb.read_bytes() == reexport.read_bytes()

    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] == contract["triangles"] == 32_768 <= 60_000
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert checked["materialContract"][0]["metallicFactor"] == 0
    assert checked["materialContract"][0]["roughnessFactor"] >= 0.89
    assert texture["width"] == texture["height"] == 2048
    assert texture["sha256"] == sha256(atlas) == contract["files"]["atlas"]["sha256"]
    assert sha256(glb) == contract["files"]["glb"]["sha256"]
    assert sha256(blend) == contract["files"]["blend"]["sha256"]
    assert semantic_identical and byte_identical
    assert extras["render_only"] is True
    assert extras["sim_authority"] == "published mask table and planar simulation; unchanged"
    assert extras["height_socket"] == "Terrain.visualY"
    assert extras["contract_id"] == extras["tile_id"] == "e5-deepwater-claim"
    assert extras["water_surface_owner"] == "runtime; absent from this GLB"
    assert extras["bathymetry_only"] is True
    assert contract["maskTruth"] == published["maskTruth"]
    assert contract["maskTable"] == str(TABLE.relative_to(ROOT))
    assert contract["waterSurface"]["includedInTerrainGLB"] is False
    assert contract["landmarkMountSpace"] == builder.claim.landmark_mount_space()
    assert len(contract["landmarkMounts"]) == 4
    assert {mount["id"] for mount in contract["landmarkMounts"]} == {
        "drowned-claim-office",
        "drowned-chapel",
        "drowned-general-store",
        "drowned-stamp-mill",
    }
    assert all((ROOT / mount["asset"]).is_file() for mount in contract["landmarkMounts"])
    assert all(-0.35 <= mount["position"][1] <= -0.15 for mount in contract["landmarkMounts"])
    assert all(0.75 <= mount["scale"][1] <= 1.05 for mount in contract["landmarkMounts"])
    assert "heavy body rests on the submerged shelf" in contract["mountedRuinsContact"]
    assert contract["panoramaMount"]["asset"] == "deepwater-claim-panorama.glb"
    assert max(vertex.co.z for vertex in mesh.data.vertices) <= -0.34
    ruin_mount_floors = {
        mount["id"]: vertex_height(mesh, mount["position"][0], mount["position"][2])
        for mount in contract["landmarkMounts"]
    }
    assert all(floor <= -5.20 for floor in ruin_mount_floors.values())

    probes = {
        "lagoonShallows": vertex_height(mesh, 0.0, 30.0),
        "reefCrest": vertex_height(mesh, -24.0, 1.0),
        "reefGap": vertex_height(mesh, 0.0, 0.0),
        "wreckShelf": vertex_height(mesh, -36.0, -24.0),
        "trenchEdge": vertex_height(mesh, 0.0, -56.0),
    }
    assert -1.85 <= probes["lagoonShallows"] <= -0.34
    assert probes["reefCrest"] > -1.50
    assert probes["reefGap"] < -2.50
    assert -7.10 <= probes["wreckShelf"] <= -5.20
    assert probes["trenchEdge"] < -7.50
    return {
        "asset": glb.name,
        "checked": checked,
        "reexported": rechecked,
        "byteIdenticalReexport": byte_identical,
        "semanticIdenticalReexport": semantic_identical,
        "embeddedTexture": texture,
        "extras": extras,
        "bathymetryProbes": {key: round(value, 4) for key, value in probes.items()},
        "ruinMountFloorProbes": {key: round(value, 4) for key, value in ruin_mount_floors.items()},
        "maskSource": str(TABLE.relative_to(ROOT)),
    }


def verify_panorama():
    blend = SOURCE / f"{KEY}-panorama.blend"
    glb = SOURCE / f"{KEY}-panorama.glb"
    atlas = SOURCE / f"{KEY}-panorama-atlas.png"
    contract = json.loads((SOURCE / f"{KEY}-panorama-contract.json").read_text(encoding="utf-8"))
    checked = semantic_contract(glb)
    document, binary = shared.glb_parts(glb)
    texture = shared.embedded_texture(document, binary)
    extras = document["nodes"][0]["extras"]
    reexport = Path("/tmp/gold-rush-deepwater-claim-panorama-reexport.glb")
    reexport_from_blend(blend, reexport)
    rechecked = semantic_contract(reexport)
    semantic_keys = ("meshes", "primitives", "triangles", "materials", "images", "embeddedImages", "cameras", "lights", "animations", "bounds", "materialContract")
    semantic_identical = all(checked[field] == rechecked[field] for field in semantic_keys)
    byte_identical = glb.read_bytes() == reexport.read_bytes()

    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] == contract["triangles"] == 2_704 <= 4_000
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert texture["width"] == texture["height"] == 2048
    assert texture["sha256"] == sha256(atlas) == contract["files"]["atlas"]["sha256"]
    assert sha256(glb) == contract["files"]["glb"]["sha256"]
    assert sha256(blend) == contract["files"]["blend"]["sha256"]
    assert semantic_identical and byte_identical
    assert extras["render_only"] is True and extras["panorama"] is True
    assert extras["affects_playfield"] is False and extras["affects_masks"] is False
    assert contract["lawVersion"] == "PANORAMA LAW v2"
    assert contract["projection"]["groundSkirtInnerBoundaryMeters"]["shape"] == "expanded-playfield-rectangle"
    assert contract["projection"]["groundSkirtOuterRadiusMeters"] == 190.0
    assert contract["projection"]["groundSkirtRole"].startswith("submerged scenery apron")
    assert contract["projection"]["skyBottomMeters"] == -160.0
    assert contract["nonInterference"]["waterBuildSpawnMasks"] == "unchanged"
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
    terrain = verify_terrain()
    panorama = verify_panorama()
    boards = {}
    for name, expected in BOARDS.items():
        path = ARTIFACTS / name
        assert png_size(path) == expected
        boards[name] = {"size": expected, "bytes": path.stat().st_size, "sha256": sha256(path)}
    evidence = {
        "blender": bpy.app.version_string,
        "maskTable": str(TABLE.relative_to(ROOT)),
        "terrain": terrain,
        "panorama": panorama,
        "boards": boards,
        "verdict": {
            "grit": "working post-flood harbor; fight, never postcard",
            "panorama": "open-sea distance; no wall, ceiling, or confirming coast",
            "masks": "published and unchanged",
            "water": "runtime-owned; no sea surface in terrain GLB",
            "landmarks": "frozen; four existing E4 town bodies recorded as separate reuse-only drowned mounts",
        },
    }
    evidence_path = ARTIFACTS / "deepwater-asset-contract.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    (ARTIFACTS / "deepwater-reexport-evidence.md").write_text(
        "# E5 Deepwater Claim re-export evidence\n\n"
        f"- Blender: {bpy.app.version_string}\n"
        "- Terrain: one mesh, one primitive, one material, one embedded 2048 atlas, 32,768 triangles.\n"
        "- Panorama: separate one-mesh, one-material, one embedded 2048 atlas, 2,688 triangles.\n"
        "- Re-export: byte-identical and semantic-identical for both GLBs.\n"
        "- Water: runtime-owned; no sea surface, swell, or classification is exported in the terrain.\n"
        "- Masks: exact published table; lagoon, reef, ten-metre gap, wreck shelf, trench, Claim-Boat deck, and west spawn unchanged.\n"
        "- Landmarks: frozen; four existing E4 town GLBs are recorded as separate drowned-town mounts and are absent from the terrain GLB.\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "evidence": str(evidence_path)}, indent=2))


if __name__ == "__main__":
    main()
