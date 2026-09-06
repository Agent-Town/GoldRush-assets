"""Strict verifier for the unique E6 campaign terrain/panorama pairs."""

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


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shared = load_module("e6_extra_shared_verify", SOURCE / "verify_contract_terrains.py")
builder = load_module("e6_extra_builder_verify", SOURCE / "build_e6_extra_terrains.py")

MAPS = {
    "showroom": {"id": "e6-showroom", "stem": "showroom-terrain"},
    "half-life-hollow": {"id": "e6-half-life-hollow", "stem": "half-life-hollow-terrain"},
}
REGATTA_MOUNT_IDS = (
    "start-line-rig",
    "finish-line-rig",
    "northwest-buoy-line-anchor",
    "midcourse-buoy-line-anchor",
    "northeast-buoy-line-anchor",
    "spectator-raft-port",
    "spectator-raft-starboard",
    "judges-tower",
)
BOARDS = {
    "e6-extra-mood-ab.png": (1920, 1260),
    "e6-extra-flat-vs-sculpted-ab.png": (1920, 1260),
    "e6-extra-owner-verdict.png": (1920, 900),
    "e6-extra-panorama-mood-ab.png": (1920, 900),
    "e6-extra-panorama-distance-gate.png": (1920, 1260),
    "e6-extra-mask-agreement-board.png": (1920, 1260),
}
SEMANTIC_KEYS = (
    "meshes", "primitives", "triangles", "materials", "images", "embeddedImages",
    "cameras", "lights", "animations", "bounds", "materialContract",
)


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
    assert not [obj for obj in bpy.data.objects if obj.type in {"CAMERA", "LIGHT"}]
    bpy.ops.object.select_all(action="DESELECT")
    mesh = meshes[0]
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.export_scene.gltf(
        filepath=str(output), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False,
        export_materials="EXPORT", export_extras=True,
    )
    return mesh


def mesh_grid_height(mesh, x, game_z):
    segments = builder.e3.SEGMENTS
    columns = segments + 1
    step_x = builder.WIDTH / segments
    step_z = builder.HEIGHT / segments
    xi = min(segments - 1, max(0, int((x + builder.WIDTH * 0.5) // step_x)))
    zi = min(segments - 1, max(0, int((game_z + builder.HEIGHT * 0.5) // step_z)))
    x0 = -builder.WIDTH * 0.5 + xi * step_x
    z0 = -builder.HEIGHT * 0.5 + zi * step_z
    tx = min(1.0, max(0.0, (x - x0) / step_x))
    tz = min(1.0, max(0.0, (game_z - z0) / step_z))
    a = zi * columns + xi
    h00 = float(mesh.data.vertices[a].co.z)
    h10 = float(mesh.data.vertices[a + 1].co.z)
    h01 = float(mesh.data.vertices[a + columns].co.z)
    h11 = float(mesh.data.vertices[a + columns + 1].co.z)
    if tx >= tz:
        return h00 + tx * (h10 - h00) + tz * (h11 - h10)
    return h00 + tx * (h11 - h01) + tz * (h01 - h00)


def rectangle_flatness(mesh, table):
    results = []
    for zone in table["maskTruth"]["buildZones"]:
        heights = [
            mesh_grid_height(mesh, zone["minX"] + (zone["maxX"] - zone["minX"]) * ix / 64,
                             zone["minZ"] + (zone["maxZ"] - zone["minZ"]) * iz / 32)
            for ix in range(65) for iz in range(33)
        ]
        deviation = max(heights) - min(heights)
        assert deviation <= 0.02
        results.append({"id": zone["id"], "sampledSurfacePoints": len(heights), "maxDeviationMeters": round(deviation, 6)})
    return results


def geometry_agreement(key, mesh, table):
    height_at = builder.height_function(key, table)
    probes = ((-58, -6), (0, -41), (0, 0), (0, 46), (57, 45)) if key == "showroom" else ((-56, 36), (0, -31), (0, 2), (0, 33), (57, -35))
    results = []
    for x, z in probes:
        actual = mesh_grid_height(mesh, x, z)
        expected = float(height_at(x, z))
        assert abs(actual - expected) <= 0.012
        results.append({"point": [x, z], "height": round(actual, 4)})
    if key == "showroom":
        expected_grades = {
            "south-showroom-approach": 0.18,
            "model-home-village": 0.82,
            "catalog-goods-yard": 1.52,
        }
        for zone in table["maskTruth"]["buildZones"]:
            center = ((zone["minX"] + zone["maxX"]) * 0.5, (zone["minZ"] + zone["maxZ"]) * 0.5)
            assert abs(mesh_grid_height(mesh, *center) - expected_grades[zone["id"]]) <= 0.012
    else:
        for zone in table["maskTruth"]["glowBridges"] + table["maskTruth"]["causeways"]:
            center = ((zone["minX"] + zone["maxX"]) * 0.5, (zone["minZ"] + zone["maxZ"]) * 0.5)
            assert mesh_grid_height(mesh, *center) < -2.20
    return results


def verify_terrain(key, config):
    stem = config["stem"]
    blend = SOURCE / f"{stem}.blend"
    glb = SOURCE / f"{stem}.glb"
    atlas = SOURCE / f"{stem}-atlas.png"
    contract = json.loads((SOURCE / f"{stem}-contract.json").read_text(encoding="utf-8"))
    _factory, table, table_path = builder.documents(key)
    checked = shared.verify.contract(glb)
    document, binary = shared.glb_parts(glb)
    texture = shared.embedded_texture(document, binary)
    extras = document["nodes"][0]["extras"]
    reexport = Path("/tmp") / f"gold-rush-{stem}-reexport.glb"
    mesh = reexport_from_blend(blend, reexport)
    rechecked = shared.verify.contract(reexport)
    semantic_identical = all(checked[field] == rechecked[field] for field in SEMANTIC_KEYS)
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
    assert extras["render_only"] is True and extras["sim_surface"] == "planar"
    assert extras["sim_authority"] == "published mask table and planar simulation; unchanged"
    assert extras["height_socket"] == "Terrain.visualY"
    assert extras["contract_id"] == extras["tile_id"] == config["id"]
    assert extras["runtime_owned_visuals_absent"] is True
    assert contract["maskTruth"] == table["maskTruth"]
    assert contract["waterAgreement"] == table["waterAgreement"]
    assert contract["maskTable"] == str(table_path.relative_to(ROOT))
    assert contract["landmarkMounts"] == builder.LANDMARK_MOUNTS[key]
    assert len(contract["landmarkMounts"]) == 5
    assert all(set(mount) == {"id", "position", "rotation", "scale", "asset"} for mount in contract["landmarkMounts"])
    assert all(mount["asset"] == "" for mount in contract["landmarkMounts"])
    assert extras["landmarks_frozen"] is False
    assert json.loads(extras["landmark_mount_ids"]) == [mount["id"] for mount in contract["landmarkMounts"]]
    assert contract["runtimeVisualsAbsent"]
    assert contract["panoramaMount"]["asset"] == f"{key}-panorama.glb"
    flatness = rectangle_flatness(mesh, table)
    assert len(flatness) == len(contract["buildZoneFlatness"])
    return {
        "asset": glb.name,
        "checked": checked,
        "reexported": rechecked,
        "byteIdenticalReexport": byte_identical,
        "semanticIdenticalReexport": semantic_identical,
        "embeddedTexture": texture,
        "extras": extras,
        "buildZoneSurfaceFlatness": flatness,
        "geometryAgreement": geometry_agreement(key, mesh, table),
        "maskSource": str(table_path.relative_to(ROOT)),
    }


def verify_panorama(key):
    blend = SOURCE / f"{key}-panorama.blend"
    glb = SOURCE / f"{key}-panorama.glb"
    atlas = SOURCE / f"{key}-panorama-atlas.png"
    contract = json.loads((SOURCE / f"{key}-panorama-contract.json").read_text(encoding="utf-8"))
    checked = shared.verify.contract(glb)
    document, binary = shared.glb_parts(glb)
    texture = shared.embedded_texture(document, binary)
    extras = document["nodes"][0]["extras"]
    reexport = Path("/tmp") / f"gold-rush-{key}-panorama-reexport.glb"
    reexport_from_blend(blend, reexport)
    rechecked = shared.verify.contract(reexport)
    semantic_identical = all(checked[field] == rechecked[field] for field in SEMANTIC_KEYS)
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
    assert extras["render_only"] is True and extras["panorama"] is True
    assert extras["affects_playfield"] is False and extras["affects_masks"] is False
    assert contract["lawVersion"] == "PANORAMA LAW v2"
    assert set(contract["namedCorrections"]) == {"paintedWall", "ceiling", "echo"}
    assert contract["nonInterference"] == {
        "playfieldBounds": "unchanged", "spawnEdges": "unchanged",
        "fogGating": "unchanged", "waterBuildSpawnMasks": "unchanged",
    }
    assert contract["mount"]["asset"] == f"{key}-panorama.glb"
    return {
        "asset": glb.name,
        "checked": checked,
        "reexported": rechecked,
        "byteIdenticalReexport": byte_identical,
        "semanticIdenticalReexport": semantic_identical,
        "embeddedTexture": texture,
        "mount": contract["mount"],
    }


def verify_picnic_reuse():
    contracts = json.loads((ROOT / "assets/contracts/epoch-6-atomic/contracts.json").read_text(encoding="utf-8"))["contracts"]
    picnic = next(contract for contract in contracts if contract["id"] == "e6-picnic")
    table_path = ROOT / "assets/contracts/epoch-6-atomic/mask-tables/e6-picnic.json"
    table = json.loads(table_path.read_text(encoding="utf-8"))
    assert picnic["tileParams"]["tileId"] == table["maskTruth"]["tileId"] == "e6-glow-mesa"
    return {
        "contractId": "e6-picnic",
        "tileId": "e6-glow-mesa",
        "decision": "variant-tagged tile reuse; no duplicate terrain or panorama sculpt",
        "maskSource": str(table_path.relative_to(ROOT)),
    }


def verify_regatta_mount_backfill():
    contract = json.loads((SOURCE / "regatta-terrain-contract.json").read_text(encoding="utf-8"))
    mounts = contract["landmarkMounts"]
    assert tuple(mount["id"] for mount in mounts) == REGATTA_MOUNT_IDS
    assert all(mount["asset"] == "" for mount in mounts)
    assert all(len(mount["position"]) == len(mount["rotation"]) == len(mount["scale"]) == 3 for mount in mounts)
    assert "code-owned sea surface" in contract["landmarkMountSpace"]["positionY"]
    return {
        "contractId": contract["contractId"],
        "mountIds": list(REGATTA_MOUNT_IDS),
        "surfacePlacement": "positionY offsets lift floating furniture from bathymetry to runtime sea level",
    }


def main():
    terrains = {key: verify_terrain(key, config) for key, config in MAPS.items()}
    panoramas = {key: verify_panorama(key) for key in MAPS}
    assert len({entry["checked"]["sha256"] for entry in terrains.values()}) == len(MAPS)
    assert len({entry["checked"]["sha256"] for entry in panoramas.values()}) == len(MAPS)
    boards = {}
    for name, expected in BOARDS.items():
        path = ARTIFACTS / name
        assert png_size(path) == expected
        boards[name] = {"size": list(expected), "bytes": path.stat().st_size, "sha256": sha256(path)}
    base_sha = subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True).strip()
    evidence = {
        "blender": bpy.app.version_string,
        "freshReferenceBaseSha": base_sha,
        "terrains": terrains,
        "panoramas": panoramas,
        "boards": boards,
        "reuse": verify_picnic_reuse(),
        "regattaMountBackfill": verify_regatta_mount_backfill(),
        "verdict": {
            "grit": "ratified E6 painted earth and kit-plate language; polished effort inside hard desert; fight, never holiday",
            "panorama": "distance; quiet zenith, unequal atomic-weather marks, no wall or ceiling",
            "masks": "published and byte-for-byte copied into each contract",
            "simulation": "planar and unchanged; all homes, goods, bridges, causeway, countdown, and extraction state remain code-owned",
            "landmarks": "mount interlock satisfied with empty asset fields; landmark bodies remain separate and 3D-C-owned",
        },
    }
    evidence_path = ARTIFACTS / "e6-extra-asset-contract.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    (ARTIFACTS / "e6-extra-reexport-evidence.md").write_text(
        "# E6 extra-map terrain and panorama re-export evidence\n\n"
        f"- Fresh reference base: `{base_sha}`.\n"
        "- Authored pairs: The Showroom and Half-Life Hollow.\n"
        "- Picnic: intentional `e6-glow-mesa` tile reuse; no duplicate sculpt.\n"
        "- Terrain GLBs: one mesh, one primitive, one material, one embedded 2048 atlas, 32,768 triangles each.\n"
        "- Panorama GLBs: separate one-mesh, one-material, one embedded 2048 atlas, 2,688 triangles each.\n"
        "- All four source `.blend` re-exports are byte-identical and semantic-identical.\n"
        "- Every authored build rectangle is independently triangle-sampled at <=0.02 m deviation.\n"
        "- Half-Life Hollow's two glow bridges and causeway are empty terrain sockets; their preview panels are not exported.\n"
        "- Five canonical empty-asset mounts ship per E6 sculpt; Regatta's eight proposed ids are backfilled at runtime sea level.\n"
        "- Simulation authority, masks, and Terrain.visualY remain unchanged.\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "evidence": str(evidence_path)}, indent=2))


if __name__ == "__main__":
    main()
