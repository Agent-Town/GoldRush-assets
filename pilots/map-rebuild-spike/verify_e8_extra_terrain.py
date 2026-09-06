"""Strict Low Orbit terrain, panorama, mask, and evidence verifier."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import subprocess

import bpy


ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"
TABLE = ROOT / "assets/contracts/epoch-8-orbital/mask-tables/e8-low-orbit.json"
STEM = "low-orbit-terrain"
BOARDS = {
    "e8-extra-mood-ab.png": (1920, 684),
    "e8-extra-flat-vs-sculpted-ab.png": (1920, 684),
    "e8-extra-owner-verdict.png": (1920, 504),
    "e8-extra-panorama-mood-ab.png": (1920, 504),
    "e8-extra-panorama-distance-gate.png": (1920, 684),
    "e8-extra-mask-agreement-board.png": (1280, 1260),
}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shared = load_module("e8_extra_shared_verify", SOURCE / "verify_contract_terrains.py")
builder = load_module("e8_extra_builder_verify", SOURCE / "build_e8_extra_terrains.py")


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
    step_x = builder.WIDTH / builder.SEGMENTS
    step_z = builder.HEIGHT / builder.SEGMENTS
    cell_x = min(builder.SEGMENTS - 1, max(0, int((x + builder.WIDTH * 0.5) // step_x)))
    cell_z = min(builder.SEGMENTS - 1, max(0, int((game_z + builder.HEIGHT * 0.5) // step_z)))
    x0 = -builder.WIDTH * 0.5 + cell_x * step_x
    z0 = -builder.HEIGHT * 0.5 + cell_z * step_z
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
            grid_surface_height(mesh, zone["minX"] + (zone["maxX"] - zone["minX"]) * xi / 64, zone["minZ"] + (zone["maxZ"] - zone["minZ"]) * zi / 32)
            for xi in range(65)
            for zi in range(33)
        ]
        deviation = max(heights) - min(heights)
        assert deviation <= 0.001
        results.append({"id": zone["id"], "sampledSurfacePoints": len(heights), "maxDeviationMeters": round(deviation, 6)})
    return results


def variant_reuse_flatness():
    """Audit authored variant masks against the accepted shared Mare mesh.

    Variant-tagged campaign contracts explicitly receive no new sculpt, but
    their authored build rectangles still need to agree with the shared visual
    surface.  Report that agreement here so a factory-side mask mismatch cannot
    be hidden behind a correct tileId reuse decision.
    """
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE / "mare-claim-terrain.blend"))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    assert len(meshes) == 1
    mesh = meshes[0]
    audit = {}
    for contract_id in ("e8-far-side", "e8-eclipse"):
        table = json.loads((ROOT / f"assets/contracts/epoch-8-orbital/mask-tables/{contract_id}.json").read_text(encoding="utf-8"))
        zones = []
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
            zones.append(
                {
                    "id": zone["id"],
                    "sampledSurfacePoints": len(heights),
                    "minHeightMeters": round(min(heights), 6),
                    "maxHeightMeters": round(max(heights), 6),
                    "maxDeviationMeters": round(deviation, 6),
                    "renderFlat": deviation <= 0.001,
                }
            )
        audit[contract_id] = {
            "tileId": table["maskTruth"]["tileId"],
            "sharedTerrain": "e8-mare-claim",
            "allBuildZonesRenderFlat": all(zone["renderFlat"] for zone in zones),
            "zones": zones,
        }
    return audit


def verify_asset(stem, expected_triangles, panorama=False):
    blend = SOURCE / f"{stem}.blend"
    glb = SOURCE / f"{stem}.glb"
    atlas = SOURCE / f"{stem}-atlas.png"
    contract_path = SOURCE / f"{stem}-contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    checked = semantic_contract(glb)
    document, binary = shared.glb_parts(glb)
    texture = shared.embedded_texture(document, binary)
    reexport = Path("/tmp") / f"gold-rush-{stem}-reexport.glb"
    mesh = reexport_from_blend(blend, reexport)
    rechecked = semantic_contract(reexport)
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
    assert extras["tile_id"] == "e8-low-orbit"
    if panorama:
        assert expected_triangles <= 4000
        assert contract["lawVersion"] == "PANORAMA LAW v2"
        assert contract["nonInterference"]["waterBuildSpawnMasks"] == "unchanged"
        assert contract["projection"]["groundSkirtOuterRadiusMeters"] == 190.0
        assert extras["sim_authority"] == "none; mounted scenery only"
    else:
        published = json.loads(TABLE.read_text(encoding="utf-8"))
        assert expected_triangles <= 60000
        assert extras["contract_id"] == "e8-low-orbit"
        assert extras["sim_authority"] == "published mask table and planar simulation; unchanged"
        assert extras["runtime_zero_g_absent"] is True
        assert extras["load_bearing_sites_flat"] is True
        assert extras["landmarks_frozen"] is False
        assert contract["maskTruth"] == published["maskTruth"]
        assert contract["waterAgreement"] == published["waterAgreement"]
        assert contract["maskTable"] == str(TABLE.relative_to(ROOT))
        assert contract["heightSocket"] == "Terrain.visualY"
        assert len(contract["landmarkMounts"]) == 5
        assert all(mount["asset"] == "" for mount in contract["landmarkMounts"])
        assert json.loads(extras["landmark_mount_ids"]) == [mount["id"] for mount in contract["landmarkMounts"]]
        assert contract["verdictPreviewOnly"]["excludedFromBlendAndGlb"] is True
        assert "assets/pilots/salvage-claw-3d/salvage-claw.glb" in contract["verdictPreviewOnly"]["assets"]
        assert len(contract["runtimeVisualsAbsent"]) == 5
    return checked, mesh, contract


def main():
    table = json.loads(TABLE.read_text(encoding="utf-8"))
    terrain, mesh, terrain_contract = verify_asset(STEM, 32768)
    flatness = build_zone_surface_flatness(mesh, table)
    assert [entry["id"] for entry in flatness] == [entry["id"] for entry in terrain_contract["buildZoneFlatness"]]
    # Confirm the exported mesh actually carries the non-ground composition:
    # three deck levels sit more than five metres above the void web.
    probes = {
        "westDeck": grid_surface_height(mesh, -37.0, 0.0),
        "clawYard": grid_surface_height(mesh, 0.0, 0.0),
        "eastDeck": grid_surface_height(mesh, 37.0, 0.0),
        "northVoid": grid_surface_height(mesh, 0.0, 61.0),
        "southVoid": grid_surface_height(mesh, 0.0, -61.0),
    }
    assert min(probes["westDeck"], probes["clawYard"], probes["eastDeck"]) - max(probes["northVoid"], probes["southVoid"]) > 5.0
    panorama, _panorama_mesh, _panorama_contract = verify_asset("low-orbit-panorama", 2688, panorama=True)
    boards = {}
    for name, expected in BOARDS.items():
        path = ARTIFACTS / name
        assert png_size(path) == expected
        boards[name] = {"size": expected, "bytes": path.stat().st_size, "sha256": sha256(path)}
    far_side = json.loads((ROOT / "assets/contracts/epoch-8-orbital/mask-tables/e8-far-side.json").read_text(encoding="utf-8"))
    eclipse = json.loads((ROOT / "assets/contracts/epoch-8-orbital/mask-tables/e8-eclipse.json").read_text(encoding="utf-8"))
    assert far_side["maskTruth"]["tileId"] == eclipse["maskTruth"]["tileId"] == "e8-mare-claim"
    variant_audit = variant_reuse_flatness()
    assert variant_audit["e8-eclipse"]["allBuildZonesRenderFlat"] is True
    evidence = {
        "blender": bpy.app.version_string,
        "freshReferenceBaseSha": subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True).strip(),
        "maskTable": str(TABLE.relative_to(ROOT)),
        "terrain": terrain,
        "panorama": panorama,
        "independentBuildZoneSurfaceFlatness": flatness,
        "geometryProbes": {key: round(value, 4) for key, value in probes.items()},
        "boards": boards,
        "variantReuse": {
            "decision": {
                "e8-far-side": "reuses tileId e8-mare-claim; no new sculpt",
                "e8-eclipse": "reuses tileId e8-mare-claim; no new sculpt",
            },
            "sharedTerrainBuildZoneAudit": variant_audit,
        },
    }
    evidence_path = ARTIFACTS / "e8-extra-asset-contract.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    (ARTIFACTS / "e8-extra-reexport-evidence.md").write_text(
        "# E8 campaign-extra re-export evidence\n\n"
        "- Low Orbit terrain: one mesh, one material, one embedded 2048 atlas, 32,768 triangles.\n"
        "- Low Orbit panorama: separate one-mesh, one-material, one embedded 2048 atlas, 2,688 triangles.\n"
        "- Re-export: byte-identical and semantic-identical for both GLBs.\n"
        "- Masks: all three scaffold rectangles independently surface-sampled at 2,145 points each with <=0.001 m deviation.\n"
        "- Simulation: zero-G movement, orbital-return projectiles, collision, placement, spawns, debris, and handholds remain planar/code-owned.\n"
        "- Mounts: five empty-asset landmark mount records; no landmark bodies baked into the terrain.\n"
        "- Reuse: Far Side and Eclipse keep the accepted Mare Claim terrain because both published tables reuse tileId e8-mare-claim.\n"
        "- Variant audit: Eclipse's reused build zones remain render-flat. Far Side's two authored rectangles cross Mare Claim's 0 m / 6 m rim transition, so their mask-to-shared-render agreement needs a factory-side contract or placement correction; this wave does not mutate the accepted shared sculpt.\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "evidence": str(evidence_path), "flatness": flatness, "probes": probes}, indent=2))


if __name__ == "__main__":
    main()
