"""Verify source-ladder landmark packs and deterministic exports."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile

import bpy


ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
LANDMARKS = SOURCE / "landmarks"
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"
sys.dont_write_bytecode = True


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shared = load_module("landmark_shared_verify", SOURCE / "verify_contract_terrains.py")

LEDGER = json.loads((LANDMARKS / "landmark-source-ledger.json").read_text(encoding="utf-8"))
MAPS = {key: len(assets) for key, assets in LEDGER["packs"].items()}
SCOPED_BOARDS = {
    "long-road": {
        "long-road-landmarks-turntable.png": (1920, 1160),
        "long-road-landmarks-verdict.png": (1920, 1008),
        "long-road-landmarks-pack.png": (1280, 720),
        "long-road-landmarks-mounted.png": (1280, 720),
        "long-road-landmarks-mounted-overview.png": (1280, 720),
        "long-road-landmarks-clearance-map.png": (1280, 720),
        "long-road-landmarks-clearance-overlay.png": (1280, 720),
        "long-road-landmarks-route-1.png": (1280, 720),
        "long-road-landmarks-route-2.png": (1280, 720),
        "long-road-landmarks-route-3.png": (1280, 720),
        "long-road-landmarks-route-4.png": (1280, 720),
        "long-road-landmarks-route-5.png": (1280, 720),
        "long-road-landmarks-route-tour.png": (1920, 1008),
    },
    "boneyard": {
        "boneyard-landmarks-turntable.png": (1920, 1160),
        "boneyard-landmarks-verdict.png": (1920, 1008),
        "boneyard-landmarks-pack.png": (1280, 720),
        "boneyard-landmarks-mounted.png": (1280, 720),
        "boneyard-landmarks-mounted-overview.png": (1280, 720),
        "boneyard-landmarks-clearance-overlay.png": (1280, 720),
    },
    "eclipse": {
        "eclipse-landmarks-turntable.png": (1920, 1160),
        "eclipse-landmarks-verdict.png": (1920, 1008),
        "eclipse-landmarks-pack.png": (1280, 720),
        "eclipse-landmarks-mounted.png": (1280, 720),
        "eclipse-landmarks-mounted-overview.png": (1280, 720),
        "eclipse-landmarks-clearance-overlay.png": (1280, 720),
    },
    "incline": {
        "incline-landmarks-turntable.png": (1920, 1160),
        "incline-landmarks-verdict.png": (1920, 1008),
        "incline-landmarks-pack.png": (1280, 720),
        "incline-landmarks-proposed.png": (1280, 720),
        "incline-landmarks-proposed-overview.png": (1280, 720),
        "incline-landmarks-clearance-overlay.png": (1280, 720),
    },
    "relay-valley": {
        "relay-valley-landmarks-turntable.png": (1920, 1160),
        "relay-valley-landmarks-verdict.png": (1920, 1008),
        "relay-valley-landmarks-pack.png": (1280, 720),
        "relay-valley-landmarks-proposed.png": (1280, 720),
        "relay-valley-landmarks-proposed-overview.png": (1280, 720),
        "relay-valley-landmarks-clearance-overlay.png": (1280, 720),
    },
    "mare-claim": {
        "mare-claim-landmarks-turntable.png": (1920, 1160),
        "mare-claim-landmarks-verdict.png": (1920, 1008),
        "mare-claim-landmarks-pack.png": (1280, 720),
        "mare-claim-landmarks-proposed.png": (1280, 720),
        "mare-claim-landmarks-proposed-overview.png": (1280, 720),
        "mare-claim-landmarks-clearance-overlay.png": (1280, 720),
    },
    "devils-alley": {
        "devils-alley-landmarks-turntable.png": (1920, 1160),
        "devils-alley-landmarks-verdict.png": (1920, 1008),
        "devils-alley-landmarks-pack.png": (1280, 720),
        "devils-alley-landmarks-mounted.png": (1280, 720),
        "devils-alley-landmarks-mounted-overview.png": (1280, 720),
        "devils-alley-landmarks-clearance-overlay.png": (1280, 720),
    },
    "archive-world": {
        "archive-world-landmarks-turntable.png": (1920, 1160),
        "archive-world-landmarks-verdict.png": (1920, 1008),
        "archive-world-landmarks-pack.png": (1280, 720),
        "archive-world-landmarks-mounted.png": (1280, 720),
        "archive-world-landmarks-mounted-overview.png": (1280, 720),
        "archive-world-landmarks-clearance-overlay.png": (1280, 720),
    },
}
BOARDS = {
    "all-landmark-packs-verdict.png": (1920, 2884),
    "all-landmark-packs-proxy-ab.png": (1920, 4144),
}
SEMANTIC_KEYS = (
    "meshes", "primitives", "triangles", "materials", "images", "embeddedImages",
    "cameras", "lights", "animations", "bounds", "materialContract",
)
E1_CONTRACTS = json.loads((ROOT / "assets/contracts/epoch-1-frontier/contracts.json").read_text(encoding="utf-8"))
NIGHT_LANTERN_FIXTURES = next(
    contract["tileParams"]["prePlacedBuildables"]
    for contract in E1_CONTRACTS["contracts"]
    if contract["id"] == "e1-night-shift"
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_size(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR"
    return struct.unpack(">II", data[16:24])


def export_selected(obj, path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False,
        export_materials="EXPORT", export_extras=True,
    )
    obj.select_set(False)


def verify_pack(key, expected_count, output_dir):
    directory = LANDMARKS / key
    contract_path = directory / f"{key}-landmark-pack-contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    terrain_path = SOURCE / contract.get("hostTerrainContract", f"{key}-terrain-contract.json")
    terrain = json.loads(terrain_path.read_text(encoding="utf-8"))
    atlas = SOURCE / contract["atlas"]["asset"]
    blend = SOURCE / contract["blend"]["asset"]
    assets = contract["assets"]

    assert contract["map"] == key and contract["sourceLadder"] == ["reuse", "derive", "build-new"]
    assert len(assets) == expected_count
    assert set(assets) == set(LEDGER["packs"][key])
    for identifier, record in assets.items():
        assert all(record[field] == LEDGER["packs"][key][identifier][field]
                   for field in ("asset", "sourceTier", "sources"))
        assert all((ROOT / source).is_file() for source in record["sources"])
    assert {path.name for path in directory.glob("*.glb")} == {Path(record["asset"]).name for record in assets.values()}
    if contract.get("hostTerrainContract"):
        assert all(mount in terrain["landmarkMounts"] for mount in contract["mounts"])
    else:
        assert contract["mounts"] == terrain["landmarkMounts"]
    local_mounts = contract["mounts"]
    if key == "mare-claim":
        domes = json.loads((LANDMARKS / "mare-dome/mare-dome-landmark-pack-contract.json").read_text())["mounts"]
        assert len(domes) == 3 and local_mounts[-3:] == domes
        local_mounts = local_mounts[:-3]
    if contract.get("mountInterlock") == "pending-3d-d":
        assert contract["mounts"] == terrain["landmarkMounts"] == []
        assert contract["proposedIds"] == list(assets)
        assert "landmarkPack" not in terrain
    elif not contract.get("hostTerrainContract"):
        assert len(local_mounts) == expected_count
        assert terrain["landmarkPack"]["contract"] == str(contract_path.relative_to(SOURCE))
        assert terrain["landmarkPack"]["atlas"] == str(atlas.relative_to(SOURCE))
    assert contract["atlas"]["width"] == contract["atlas"]["height"] <= 2048
    assert contract["atlas"]["sharedByEveryAsset"] is True
    assert sha256(atlas) == contract["atlas"]["sha256"]
    assert sha256(blend) == contract["blend"]["sha256"]
    assets_by_path = {record["asset"]: record for record in assets.values()}
    assert {mount["asset"] for mount in local_mounts} == set(assets_by_path) if local_mounts else True
    for mount in local_mounts:
        conformed = assets_by_path[mount["asset"]]["terrainConformed"]
        assert conformed is ("terrainConformOffsetY" in mount)
        if conformed:
            assert abs(mount["position"][1] - mount["terrainConformOffsetY"]) < 1e-6
    if key == "night-shift":
        assert assets["seven_lantern_terraces"]["authoredFixturePositions"] == NIGHT_LANTERN_FIXTURES

    # Replacement packs retain historical aggregates; each declared body is authoritative.
    per_body = any("blend" in record for record in assets.values())
    assert not per_body or all("blend" in record for record in assets.values())
    if not per_body:
        bpy.ops.wm.open_mainfile(filepath=str(blend))
        meshes = {obj.name: obj for obj in bpy.data.objects if obj.type == "MESH"}
        assert set(meshes) == set(assets)
        assert not [obj for obj in bpy.data.objects if obj.type in {"CAMERA", "LIGHT"}]
        assert len({obj.data.materials[0].name for obj in meshes.values()}) == 1

    records = {}
    for identifier, record in assets.items():
        glb = SOURCE / record["asset"]
        checked = shared.verify.contract(glb)
        document, binary = shared.glb_parts(glb)
        texture = shared.embedded_texture(document, binary)
        extras = document["nodes"][0]["extras"]
        expected_extras = {
            "render_only": True, "landmark": True, "mount_id": identifier,
            "map_pack": key, "era": contract["era"],
        }
        if per_body:
            assert contract.get("provenance", {}).get("metadataExport")
            assert all(extras.get(name) == value for name, value in expected_extras.items())
            body_blend = SOURCE / record["blend"]["asset"]
            assert sha256(body_blend) == record["blend"]["sha256"]
            profile = json.loads(body_blend.with_suffix(".export.json").read_text())
            assert profile["profile"] == "static" and profile["extras"] is True
            assert profile["animations"] is False and profile["applyTransforms"] is True
            assert profile["selection"] == [identifier]
            bpy.ops.wm.open_mainfile(filepath=str(body_blend))
            meshes = {obj.name: obj for obj in bpy.data.objects if obj.type == "MESH"}
            assert set(meshes) == {identifier}
            assert not [obj for obj in bpy.data.objects if obj.type in {"CAMERA", "LIGHT"}]
        else:
            expected_extras.update(source_tier=record["sourceTier"], simulation_authority="none; mounted render-only scenery")
            assert extras == expected_extras
        assert record["sourceTier"] in {"reuse", "derive", "build-new"} and record["sources"]
        assert checked["meshes"] == record.get("gltfMeshCount", 1)
        assert checked["primitives"] == record.get("primitiveCount", 1)
        assert checked["triangles"] == record["triangles"] <= record["triangleBudget"] == 3000
        assert checked["materials"] == record.get("materialCount", 1)
        assert checked["images"] == checked["embeddedImages"] == 1
        assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
        assert checked["materialContract"][0]["metallicFactor"] == 0
        assert checked["materialContract"][0]["roughnessFactor"] >= 0.89
        assert checked["materialContract"][0]["hasBaseColorTexture"]
        assert texture["width"] == texture["height"] == contract["atlas"]["width"] <= 2048
        assert texture["sha256"] == contract["atlas"]["sha256"]
        assert sha256(glb) == record["sha256"]
        # Declared bounds are Blender Z-up; GLB coordinates are Y-up. Do not recenter approved art.
        low, high = record["bounds"]["min"], record["bounds"]["max"]
        expected_bounds = {"min": [low[0], low[2], -high[1]], "max": [high[0], high[2], -low[1]]}
        for bound in ("min", "max"):
            assert all(abs(a - b) < 0.0002 for a, b in zip(checked["bounds"][bound], expected_bounds[bound])), (key, identifier, bound)
        if not per_body and not contract.get("hostTerrainContract"):
            assert abs(checked["bounds"]["min"][1]) < 0.0002
            assert abs(checked["bounds"]["center"][0]) < 0.0002
            assert abs(checked["bounds"]["center"][2]) < 0.0002

        reexport = output_dir / f"{key}-{identifier}-reexport.glb"
        export_selected(meshes[identifier], reexport)
        rechecked = shared.verify.contract(reexport)
        semantic_identical = all(checked[field] == rechecked[field] for field in SEMANTIC_KEYS)
        byte_identical = glb.read_bytes() == reexport.read_bytes()
        assert semantic_identical and byte_identical
        records[identifier] = {
            "sourceTier": record["sourceTier"],
            "triangles": checked["triangles"],
            "sha256": checked["sha256"],
            "byteIdenticalReexport": byte_identical,
            "semanticIdenticalReexport": semantic_identical,
            "declaredBoundsMatch": True,
            "source": record.get("blend", contract["blend"])["asset"],
            "sourceKind": "per-body" if per_body else "aggregate",
        }
    return {"era": contract["era"], "atlasSha256": contract["atlas"]["sha256"], "assets": records}


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packs", nargs="*")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--historical-boards", action="store_true", help="Also check the original review board inventory; not a current art-acceptance gate")
    options = parser.parse_args(args)
    selected = options.packs or list(MAPS)
    assert len(selected) == len(set(selected)), "duplicate landmark packs"
    unknown = sorted(set(selected) - set(MAPS))
    assert not unknown, f"unknown landmark packs: {unknown}"
    assert {path.parent.name for path in LANDMARKS.glob("*/*-landmark-pack-contract.json")} == set(MAPS)
    ledger = LEDGER
    assert ledger["law"] == "reuse > derive > build-new; era-stamped; grit-dressed"
    output_dir = options.output or Path(tempfile.mkdtemp(prefix="gold-rush-landmark-proof-"))
    output_dir.mkdir(parents=True, exist_ok=True)
    assert not any((output_dir / name).exists() for name in ("asset-contract.json", "reexport-evidence.md")), "choose a fresh evidence output"
    with tempfile.TemporaryDirectory(prefix="gold-rush-landmark-exports-") as scratch:
        packs = {key: verify_pack(key, MAPS[key], Path(scratch)) for key in selected}
    tiers = {tier: 0 for tier in ("reuse", "derive", "build-new")}
    for pack in packs.values():
        for asset in pack["assets"].values():
            tiers[asset["sourceTier"]] += 1
    assert sum(tiers.values()) == sum(MAPS[key] for key in selected)
    boards = {}
    if options.historical_boards and not options.packs:
        for name, size in BOARDS.items():
            path = ARTIFACTS / name
            assert path.is_file() and png_size(path) == size and path.stat().st_size > 100_000
            boards[name] = {"size": list(size), "sha256": sha256(path)}
    elif options.historical_boards:
        requested_boards = {name: size for key in selected for name, size in SCOPED_BOARDS.get(key, {}).items()}
        assert requested_boards, "no historical boards declared for selected packs"
        for name, size in requested_boards.items():
            path = ARTIFACTS / name
            assert path.is_file() and png_size(path) == size and path.stat().st_size > 100_000
            boards[name] = {"size": list(size), "sha256": sha256(path)}
    evidence = {
        "law": ledger["law"],
        "packs": packs,
        "totals": {"packs": len(packs), "assets": sum(tiers.values()), "sourceTiers": tiers},
        "boards": boards,
        "simulation": "unchanged; every landmark is a separate render-only GLB mounted by contract",
    }
    output = output_dir / "asset-contract.json"
    output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    report = output_dir / "reexport-evidence.md"
    report.write_text(
        "# Landmark pack re-export evidence\n\n"
        f"- Packs: {len(packs)}\n- Assets: {sum(tiers.values())}\n"
        f"- Source tiers: reuse {tiers['reuse']}, derive {tiers['derive']}, build-new {tiers['build-new']}\n"
        "- Every GLB: declared mesh, primitive and material counts; one embedded pack atlas (<=2048); <=3,000 triangles.\n"
        "- Every source `.blend` re-export: byte-identical and semantic-identical.\n"
        "- Bounds match the declared Blender-to-GLB coordinate conversion; replacement origins are preserved.\n"
        "- Factory proof does not accept concept fidelity, mounted collision or historical screenshots.\n",
        encoding="utf-8",
    )
    print(json.dumps({**evidence["totals"], "evidence": str(output)}, indent=2))


if __name__ == "__main__":
    main()
