"""Strict E9 campaign-extra terrain, panorama, mask, and evidence verifier."""

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
MAPS = (
    ("seed-run", "e9-seed-run"),
    ("devils-alley", "e9-devils-alley"),
    ("old-canal", "e9-old-canal"),
)
BOARDS = {
    "e9-extra-mood-ab.png": (1920, 1836),
    "e9-extra-flat-vs-sculpted-ab.png": (1920, 1836),
    "e9-extra-owner-verdict.png": (1920, 1296),
    "e9-extra-panorama-mood-ab.png": (1920, 1296),
    "e9-extra-panorama-distance-gate.png": (1920, 1836),
    "e9-extra-mask-agreement-board.png": (1280, 2376),
}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shared = load_module("e9_extra_shared_verify", SOURCE / "verify_contract_terrains.py")
builder = load_module("e9_extra_builder_verify", SOURCE / "build_e9_extra_terrains.py")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_size(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR"
    return struct.unpack(">II", data[16:24])


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


def grid_surface_height(mesh, x, game_z):
    columns = builder.SEGMENTS + 1
    width = height = 128.0
    step_x = width / builder.SEGMENTS
    step_z = height / builder.SEGMENTS
    cell_x = min(builder.SEGMENTS - 1, max(0, int((x + width * 0.5) // step_x)))
    cell_z = min(builder.SEGMENTS - 1, max(0, int((game_z + height * 0.5) // step_z)))
    x0 = -width * 0.5 + cell_x * step_x
    z0 = -height * 0.5 + cell_z * step_z
    tx = min(1.0, max(0.0, (x - x0) / step_x))
    tz = min(1.0, max(0.0, (game_z - z0) / step_z))
    a = cell_z * columns + cell_x
    h00 = float(mesh.data.vertices[a].co.z)
    h10 = float(mesh.data.vertices[a + 1].co.z)
    h01 = float(mesh.data.vertices[a + columns].co.z)
    h11 = float(mesh.data.vertices[a + columns + 1].co.z)
    if tx >= tz:
        return h00 + tx * (h10 - h00) + tz * (h11 - h10)
    return h00 + tx * (h11 - h01) + tz * (h01 - h00)


def build_zone_surface_flatness(mesh, table):
    results = []
    for zone in table["maskTruth"]["buildZones"]:
        heights = [
            grid_surface_height(
                mesh,
                zone["minX"] + (zone["maxX"] - zone["minX"]) * xi / 64,
                zone["minZ"] + (zone["maxZ"] - zone["minZ"]) * zi / 32,
            )
            for xi in range(65)
            for zi in range(33)
        ]
        deviation = max(heights) - min(heights)
        assert deviation <= 0.001
        results.append({"id": zone["id"], "sampledSurfacePoints": len(heights), "maxDeviationMeters": round(deviation, 6)})
    return results


def verify_asset(stem, expected_triangles, tile_id, panorama=False, table=None):
    blend = SOURCE / f"{stem}.blend"
    glb = SOURCE / f"{stem}.glb"
    atlas = SOURCE / f"{stem}-atlas.png"
    contract_path = SOURCE / f"{stem}-contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    checked = shared.verify.contract(glb)
    document, binary = shared.glb_parts(glb)
    texture = shared.embedded_texture(document, binary)
    reexport = Path("/tmp") / f"gold-rush-{stem}-reexport.glb"
    mesh = reexport_from_blend(blend, reexport)
    rechecked = shared.verify.contract(reexport)
    semantic_keys = ("meshes", "primitives", "triangles", "materials", "images", "embeddedImages", "cameras", "lights", "animations", "bounds", "materialContract")
    assert all(checked[field] == rechecked[field] for field in semantic_keys)
    assert glb.read_bytes() == reexport.read_bytes()
    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] == contract["triangles"] == expected_triangles
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert texture["width"] == texture["height"] == 2048
    assert texture["sha256"] == sha256(atlas) == contract["files"]["atlas"]["sha256"]
    assert sha256(glb) == contract["files"]["glb"]["sha256"]
    assert sha256(blend) == contract["files"]["blend"]["sha256"]
    extras = document["nodes"][0]["extras"]
    assert extras["render_only"] is True
    flatness = None
    if panorama:
        assert expected_triangles <= 4000
        assert contract["lawVersion"] == "PANORAMA LAW v2"
        assert contract["nonInterference"]["waterBuildSpawnMasks"] == "unchanged"
        assert contract["projection"]["groundSkirtInnerBoundaryMeters"]["halfExtents"] == [64.0, 64.0]
        assert extras["affects_playfield"] is False and extras["affects_masks"] is False
    else:
        assert expected_triangles <= 60000 and table is not None
        assert extras["contract_id"] == extras["tile_id"] == tile_id
        assert extras["sim_authority"] == "published mask table and planar simulation; unchanged"
        assert contract["maskTruth"] == table["maskTruth"]
        assert contract["waterAgreement"] == table["waterAgreement"]
        assert contract["maskTable"] == f"assets/contracts/epoch-9-redfields/mask-tables/{tile_id}.json"
        assert contract["heightSocket"] == "Terrain.visualY"
        assert len(contract["landmarkMounts"]) == 5
        assert all(mount["asset"] == "" for mount in contract["landmarkMounts"])
        assert json.loads(extras["landmark_mount_ids"]) == [mount["id"] for mount in contract["landmarkMounts"]]
        assert contract["verdictPreviewOnly"]["excludedFromBlendAndGlb"] is True
        flatness = build_zone_surface_flatness(mesh, table)
        assert [entry["id"] for entry in flatness] == [entry["id"] for entry in contract["buildZoneFlatness"]]
    return checked, flatness


def main():
    evidence = {
        "blender": bpy.app.version_string,
        "freshReferenceBaseSha": subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True).strip(),
        "maps": {},
        "boards": {},
    }
    for key, tile_id in MAPS:
        table_path = ROOT / f"assets/contracts/epoch-9-redfields/mask-tables/{tile_id}.json"
        table = json.loads(table_path.read_text(encoding="utf-8"))
        terrain, flatness = verify_asset(f"{key}-terrain", 32768, tile_id, table=table)
        panorama, _ = verify_asset(f"{key}-panorama", 3072, tile_id, panorama=True)
        evidence["maps"][key] = {
            "maskTable": str(table_path.relative_to(ROOT)),
            "terrain": terrain,
            "panorama": panorama,
            "independentBuildZoneSurfaceFlatness": flatness,
        }
    for name, expected in BOARDS.items():
        path = ARTIFACTS / name
        assert png_size(path) == expected
        evidence["boards"][name] = {"size": expected, "bytes": path.stat().st_size, "sha256": sha256(path)}
    evidence_path = ARTIFACTS / "e9-extra-asset-contract.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    (ARTIFACTS / "e9-extra-reexport-evidence.md").write_text(
        "# E9 campaign-extra re-export evidence\n\n"
        "- Seed Run, Devil's Alley, and Old Canal terrains: one mesh, one material, one embedded 2048 atlas, 32,768 triangles each.\n"
        "- Three panoramas: separate one-mesh, one-material, one embedded 2048 atlas, 3,072 triangles each.\n"
        "- Re-export: byte-identical and semantic-identical for all six GLBs.\n"
        "- Masks: all fifteen build rectangles independently surface-sampled at 2,145 points each with <=0.001 m deviation.\n"
        "- Simulation: movement, collision, placement, spawns, persistence, water, wind, and event mechanics remain planar/code-owned.\n"
        "- Mounts: five empty-asset landmark mount records per terrain; no landmark bodies baked into terrain.\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "evidence": str(evidence_path)}, indent=2))


if __name__ == "__main__":
    main()
