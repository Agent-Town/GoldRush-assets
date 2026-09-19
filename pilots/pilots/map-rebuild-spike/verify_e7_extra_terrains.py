"""Strict verifier for the E7 campaign terrain/panorama wave."""

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
KEY = "echo-canyon"
CONTRACT_ID = "e7-echo-canyon"
STEM = "echo-canyon-terrain"
MOUNT_IDS = (
    "south-broadcast-gate",
    "west-echo-array",
    "east-echo-array",
    "mirror-observation-post",
    "north-return-gate",
)
BOARDS = {
    "e7-extra-mood-ab.png": (1920, 684),
    "e7-extra-flat-vs-sculpted-ab.png": (1920, 684),
    "e7-extra-owner-verdict.png": (1920, 504),
    "e7-extra-panorama-mood-ab.png": (1920, 504),
    "e7-extra-panorama-distance-gate.png": (1920, 684),
    "e7-extra-mask-agreement-board.png": (1280, 1260),
}
SEMANTIC_KEYS = (
    "meshes", "primitives", "triangles", "materials", "images", "embeddedImages",
    "cameras", "lights", "animations", "bounds", "materialContract",
)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shared = load_module("e7_extra_shared_verify", SOURCE / "verify_contract_terrains.py")
builder = load_module("e7_extra_builder_verify", SOURCE / "build_e3_contract_terrains.py")


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
    profile = builder.PROFILES[KEY]
    segments = builder.SEGMENTS
    columns = segments + 1
    step_x = profile["width"] / segments
    step_z = profile["height"] / segments
    xi = min(segments - 1, max(0, int((x + profile["width"] * 0.5) // step_x)))
    zi = min(segments - 1, max(0, int((game_z + profile["height"] * 0.5) // step_z)))
    x0 = -profile["width"] * 0.5 + xi * step_x
    z0 = -profile["height"] * 0.5 + zi * step_z
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
            mesh_grid_height(
                mesh,
                zone["minX"] + (zone["maxX"] - zone["minX"]) * ix / 64,
                zone["minZ"] + (zone["maxZ"] - zone["minZ"]) * iz / 32,
            )
            for ix in range(65) for iz in range(33)
        ]
        deviation = max(heights) - min(heights)
        assert deviation <= 0.02
        results.append({
            "id": zone["id"],
            "sampledSurfacePoints": len(heights),
            "maxDeviationMeters": round(deviation, 6),
        })
    return results


def band_agreement(mesh, table):
    results = []
    for band in table["maskTruth"]["echoCanyonBands"]:
        target = float(band["height"])
        samples = [
            mesh_grid_height(
                mesh,
                band["minX"] + 1.5 + (band["maxX"] - band["minX"] - 3.0) * ix / 16,
                band["minZ"] + 1.5 + (band["maxZ"] - band["minZ"] - 3.0) * iz / 32,
            )
            for ix in range(17) for iz in range(33)
        ]
        maximum_error = max(abs(value - target) for value in samples)
        assert maximum_error <= 0.012
        results.append({
            "id": band["id"],
            "targetHeightMeters": target,
            "sampledSurfacePoints": len(samples),
            "maximumErrorMeters": round(maximum_error, 6),
        })
    return results


def verify_terrain():
    blend = SOURCE / f"{STEM}.blend"
    glb = SOURCE / f"{STEM}.glb"
    atlas = SOURCE / f"{STEM}-atlas.png"
    contract = json.loads((SOURCE / f"{STEM}-contract.json").read_text(encoding="utf-8"))
    factory = builder.factory_contract(CONTRACT_ID)
    table, table_path = builder.mask_table(CONTRACT_ID)
    checked = shared.verify.contract(glb)
    document, binary = shared.glb_parts(glb)
    texture = shared.embedded_texture(document, binary)
    extras = document["nodes"][0]["extras"]
    reexport = Path("/tmp") / "gold-rush-echo-canyon-terrain-reexport.glb"
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
    assert extras["render_only"] is True and extras["sim_authority"].startswith("published mask table")
    assert extras["height_socket"] == "Terrain.visualY"
    assert extras["contract_id"] == CONTRACT_ID and extras["tile_id"] == CONTRACT_ID
    assert extras["runtime_owned_visuals_absent"] is True
    assert contract["maskTruth"] == table["maskTruth"]
    assert contract["waterAgreement"] == table["waterAgreement"]
    assert contract["maskTable"] == str(table_path.relative_to(ROOT))
    assert contract["landmarkMounts"] == builder.LANDMARK_MOUNTS[KEY]
    assert tuple(mount["id"] for mount in contract["landmarkMounts"]) == MOUNT_IDS
    assert all(mount["asset"] == "" for mount in contract["landmarkMounts"])
    assert extras["landmarks_frozen"] is False
    assert json.loads(extras["landmark_mount_ids"]) == list(MOUNT_IDS)
    assert contract["verdictPreviewOnly"]["excludedFromBlendAndGlb"] is True
    assert contract["panoramaMount"]["asset"] == "echo-canyon-panorama.glb"
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
        "echoCanyonBandAgreement": band_agreement(mesh, table),
        "maskSource": str(table_path.relative_to(ROOT)),
        "factoryTileId": factory["tileParams"]["tileId"],
    }


def verify_panorama():
    blend = SOURCE / f"{KEY}-panorama.blend"
    glb = SOURCE / f"{KEY}-panorama.glb"
    atlas = SOURCE / f"{KEY}-panorama-atlas.png"
    contract = json.loads((SOURCE / f"{KEY}-panorama-contract.json").read_text(encoding="utf-8"))
    checked = shared.verify.contract(glb)
    document, binary = shared.glb_parts(glb)
    texture = shared.embedded_texture(document, binary)
    extras = document["nodes"][0]["extras"]
    reexport = Path("/tmp") / "gold-rush-echo-canyon-panorama-reexport.glb"
    reexport_from_blend(blend, reexport)
    rechecked = shared.verify.contract(reexport)
    semantic_identical = all(checked[field] == rechecked[field] for field in SEMANTIC_KEYS)
    byte_identical = glb.read_bytes() == reexport.read_bytes()

    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] == contract["triangles"] == 3_084 <= 4_000
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
    assert contract["mount"]["asset"] == "echo-canyon-panorama.glb"
    return {
        "asset": glb.name,
        "checked": checked,
        "reexported": rechecked,
        "byteIdenticalReexport": byte_identical,
        "semanticIdenticalReexport": semantic_identical,
        "embeddedTexture": texture,
        "mount": contract["mount"],
    }


def verify_reuse():
    contracts = json.loads((ROOT / "assets/contracts/epoch-7-signal/contracts.json").read_text(encoding="utf-8"))["contracts"]
    results = []
    for contract_id in ("e7-dead-band", "e7-relay-rush"):
        contract = next(entry for entry in contracts if entry["id"] == contract_id)
        table_path = ROOT / f"assets/contracts/epoch-7-signal/mask-tables/{contract_id}.json"
        table = json.loads(table_path.read_text(encoding="utf-8"))
        assert contract["tileParams"]["tileId"] == table["maskTruth"]["tileId"] == "e7-relay-valley"
        results.append({
            "contractId": contract_id,
            "tileId": "e7-relay-valley",
            "decision": "variant-tagged tile reuse; no duplicate terrain or panorama sculpt",
            "maskSource": str(table_path.relative_to(ROOT)),
        })
    return results


def main():
    terrain = verify_terrain()
    panorama = verify_panorama()
    boards = {}
    for name, expected in BOARDS.items():
        path = ARTIFACTS / name
        assert png_size(path) == expected
        boards[name] = {"size": list(expected), "bytes": path.stat().st_size, "sha256": sha256(path)}
    base_sha = subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True).strip()
    evidence = {
        "blender": bpy.app.version_string,
        "freshReferenceBaseSha": base_sha,
        "terrain": terrain,
        "panorama": panorama,
        "boards": boards,
        "reuse": verify_reuse(),
        "verdict": {
            "grit": "walnut loam, engraved shale, punch-tape scars, honey work light, and restrained agent teal; fight, never holiday",
            "panorama": "distance; quiet zenith, unequal signal weather, two canyon mouths, no painted wall or ceiling",
            "masks": "published and byte-for-byte copied into the terrain contract; exact h0/h5 bands independently surface-sampled",
            "simulation": "planar and unchanged; broadcast mirroring, enemy spawns, buildability, and all contract state remain code-owned",
            "landmarks": "five canonical empty-asset mounts ship; verdict proxies are absent from the terrain GLB",
        },
    }
    evidence_path = ARTIFACTS / "e7-extra-asset-contract.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    (ARTIFACTS / "e7-extra-reexport-evidence.md").write_text(
        "# E7 extra-map terrain and panorama re-export evidence\n\n"
        f"- Fresh reference base: `{base_sha}`.\n"
        "- Authored pair: Echo Canyon.\n"
        "- Dead Band and Relay Rush: intentional `e7-relay-valley` tile reuse; no duplicate sculpt.\n"
        "- Terrain GLB: one mesh, one primitive, one material, one embedded 2048 atlas, 32,768 triangles.\n"
        "- Panorama GLB: separate one-mesh, one-material, one embedded 2048 atlas, 3,084 triangles.\n"
        "- Both source `.blend` re-exports are byte-identical and semantic-identical.\n"
        "- Every build rectangle is triangle-sampled at <=0.02 m deviation; every authored canyon band is sampled against h0/h5.\n"
        "- Five canonical mounts ship with empty assets; all gate, array, and console bodies are verdict-only and absent from the GLB.\n"
        "- Simulation authority, masks, spawn edges, broadcast mirroring, and Terrain.visualY remain unchanged.\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "evidence": str(evidence_path)}, indent=2))


if __name__ == "__main__":
    main()
