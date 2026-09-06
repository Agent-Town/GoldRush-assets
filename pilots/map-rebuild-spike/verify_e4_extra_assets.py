"""Strict E4 campaign terrain, Panorama v2, mask, and evidence verifier."""

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
PROFILES = {
    "long-road": {
        "contractId": "e4-long-road",
        "table": ROOT / "assets/contracts/epoch-4-motor/mask-tables/e4-long-road.json",
        "dimensions": (400.0, 96.0),
        "mounts": 5,
        "panoramaTriangles": 2688,
        "panoramaHalfExtents": [200.0, 48.0],
    },
    "gusher-county": {
        "contractId": "e4-gusher-county",
        "table": ROOT / "assets/contracts/epoch-4-motor/mask-tables/e4-gusher-county.json",
        "dimensions": (160.0, 160.0),
        "mounts": 10,
        "panoramaTriangles": 3072,
        "panoramaHalfExtents": [80.0, 80.0],
    },
    "boneyard": {
        "contractId": "e4-boneyard",
        "table": ROOT / "assets/contracts/epoch-4-motor/mask-tables/e4-boneyard.json",
        "dimensions": (128.0, 128.0),
        "mounts": 12,
        "panoramaTriangles": 3072,
        "panoramaHalfExtents": [64.0, 64.0],
    },
}
BOARDS = {
    "e4-extra-mood-ab.png": (1920, 1836),
    "e4-extra-flat-vs-sculpted-ab.png": (1920, 1836),
    "e4-extra-owner-verdict.png": (1920, 1296),
    "e4-extra-panorama-mood-ab.png": (1920, 1296),
    "e4-extra-panorama-distance-gate.png": (1920, 1836),
    "e4-extra-mask-agreement-board.png": (1920, 828),
}
SEGMENTS = 128


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shared = load_module("e4_extra_shared_verify", SOURCE / "verify_contract_terrains.py")


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


def grid_surface_height(mesh, x, game_z, dimensions):
    width, height = dimensions
    columns = SEGMENTS + 1
    step_x, step_z = width / SEGMENTS, height / SEGMENTS
    half_x, half_z = width * 0.5, height * 0.5
    cell_x = min(SEGMENTS - 1, max(0, int((x + half_x) // step_x)))
    cell_z = min(SEGMENTS - 1, max(0, int((game_z + half_z) // step_z)))
    x0, z0 = -half_x + cell_x * step_x, -half_z + cell_z * step_z
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


def build_zone_surface_flatness(mesh, table, dimensions):
    results = []
    for zone in table["maskTruth"]["buildZones"]:
        heights = [
            grid_surface_height(
                mesh,
                zone["minX"] + (zone["maxX"] - zone["minX"]) * xi / 64,
                zone["minZ"] + (zone["maxZ"] - zone["minZ"]) * zi / 32,
                dimensions,
            )
            for xi in range(65)
            for zi in range(33)
        ]
        deviation = max(heights) - min(heights)
        assert deviation <= 0.001
        results.append({
            "id": zone["id"],
            "sampledSurfacePoints": len(heights),
            "maxDeviationMeters": round(deviation, 6),
        })
    return results


def node_extras(document):
    matches = [node["extras"] for node in document.get("nodes", []) if "extras" in node]
    assert len(matches) == 1
    return matches[0]


def verify_asset(key, panorama=False):
    profile = PROFILES[key]
    suffix = "panorama" if panorama else "terrain"
    stem = f"{key}-{suffix}"
    blend = SOURCE / f"{stem}.blend"
    glb = SOURCE / f"{stem}.glb"
    atlas = SOURCE / f"{stem}-atlas.png"
    contract = json.loads((SOURCE / f"{stem}-contract.json").read_text(encoding="utf-8"))
    checked = shared.verify.contract(glb)
    document, binary = shared.glb_parts(glb)
    texture = shared.embedded_texture(document, binary)
    reexport = Path("/tmp") / f"gold-rush-{stem}-reexport.glb"
    mesh = reexport_from_blend(blend, reexport)
    rechecked = shared.verify.contract(reexport)
    semantic = ("meshes", "primitives", "triangles", "materials", "images", "embeddedImages", "cameras", "lights", "animations", "bounds", "materialContract")
    assert all(checked[field] == rechecked[field] for field in semantic)
    assert glb.read_bytes() == reexport.read_bytes()
    assert checked["meshes"] == checked["primitives"] == 1
    expected_triangles = profile["panoramaTriangles"] if panorama else 32768
    assert checked["triangles"] == contract["triangles"] == expected_triangles
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert texture["width"] == texture["height"] == 2048
    assert texture["sha256"] == sha256(atlas) == contract["files"]["atlas"]["sha256"]
    assert sha256(glb) == contract["files"]["glb"]["sha256"]
    assert sha256(blend) == contract["files"]["blend"]["sha256"]
    extras = node_extras(document)
    if panorama:
        assert expected_triangles <= 4000
        assert contract["lawVersion"] == "PANORAMA LAW v2"
        assert contract["projection"]["groundSkirtInnerBoundaryMeters"]["halfExtents"] == profile["panoramaHalfExtents"]
        assert contract["mount"]["asset"] == f"{key}-panorama.glb"
        assert contract["mount"]["renderOnly"] is True
        assert contract["nonInterference"]["waterBuildSpawnMasks"] == "unchanged"
        assert extras["affects_playfield"] is False and extras["affects_masks"] is False
        return checked, None

    table = json.loads(profile["table"].read_text(encoding="utf-8"))
    assert expected_triangles <= 60000
    assert extras["contract_id"] == extras["tile_id"] == profile["contractId"]
    assert extras["sim_authority"] == "published mask table and planar simulation; unchanged"
    assert contract["maskTruth"] == table["maskTruth"]
    assert contract["waterAgreement"] == table["waterAgreement"]
    assert contract["maskTable"] == str(profile["table"].relative_to(ROOT))
    assert contract["heightSocket"] == "Terrain.visualY"
    mounts = contract["landmarkMounts"]
    assert len(mounts) == profile["mounts"]
    assert all(mount["asset"] == "" and set(mount) == {"id", "asset", "position", "rotation", "scale"} for mount in mounts)
    assert json.loads(extras["landmark_mount_ids"]) == [mount["id"] for mount in mounts]
    assert contract["panoramaMount"]["asset"] == f"{key}-panorama.glb"
    assert contract["verdictPreviewOnly"]["excludedFromBlendAndGlb"] is True
    flatness = build_zone_surface_flatness(mesh, table, profile["dimensions"])
    assert [entry["id"] for entry in flatness] == [entry["id"] for entry in contract["buildZoneFlatness"]]
    return checked, flatness


def main():
    evidence = {
        "blender": bpy.app.version_string,
        "freshReferenceBaseSha": subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True).strip(),
        "maps": {},
        "boards": {},
    }
    for key, profile in PROFILES.items():
        terrain, flatness = verify_asset(key)
        panorama, _ = verify_asset(key, panorama=True)
        evidence["maps"][key] = {
            "maskTable": str(profile["table"].relative_to(ROOT)),
            "terrain": terrain,
            "panorama": panorama,
            "independentBuildZoneSurfaceFlatness": flatness,
            "landmarkMountCount": profile["mounts"],
        }
    for name, expected in BOARDS.items():
        path = ARTIFACTS / name
        assert png_size(path) == expected
        evidence["boards"][name] = {"size": expected, "bytes": path.stat().st_size, "sha256": sha256(path)}
    evidence_path = ARTIFACTS / "e4-extra-asset-contract.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    (ARTIFACTS / "e4-extra-reexport-evidence.md").write_text(
        "# E4 extra-map re-export evidence\n\n"
        "- Terrains: Long Road, Gusher County, and Boneyard each use one mesh, one material, one embedded 2048 atlas, and 32,768 triangles.\n"
        "- Panorama v2: three separate one-mesh, one-material, one-atlas rings; Long Road uses 2,688 triangles and the other two use 3,072.\n"
        "- Re-export: byte-identical and semantic-identical for all six GLBs.\n"
        "- Masks: ten build rectangles independently surface-sampled at 2,145 points each with <=0.001 m deviation.\n"
        "- Simulation: movement, collision, placement, spawns, convoy, eruptions, salvage, weather, and combat remain planar/code-owned.\n"
        "- Mounts: 5 + 10 + 12 empty-asset landmark mount records; no landmark bodies are baked into any terrain.\n"
        "- Panorama caveat: the high run camera exposes some county-ground apron; the center-horizon gate reads distance and the evidence does not crop the apron away.\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "evidence": str(evidence_path)}, indent=2))


if __name__ == "__main__":
    main()
