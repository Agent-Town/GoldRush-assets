"""Verify source-ladder landmark packs and deterministic exports."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys

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

MAPS = {
    "the-claim": 5,
    "dry-gulch": 5,
    "twin-banks": 5,
    "night-shift": 5,
    "baron": 5,
    "hill-mine": 5,
    "trestle": 6,
    "incline": 5,
    "boneyard": 12,
    "long-road": 5,
    "regatta": 8,
    "relay-valley": 5,
    "mare-claim": 5,
    "eclipse": 5,
    "devils-alley": 5,
    "archive-world": 5,
}
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


def verify_pack(key, expected_count):
    directory = LANDMARKS / key
    contract_path = directory / f"{key}-landmark-pack-contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    terrain_path = SOURCE / f"{key}-terrain-contract.json"
    terrain = json.loads(terrain_path.read_text(encoding="utf-8"))
    atlas = SOURCE / contract["atlas"]["asset"]
    blend = SOURCE / contract["blend"]["asset"]
    assets = contract["assets"]
    mount_agnostic = contract.get("mountInterlock") == "pending-3d-d"

    assert contract["map"] == key and contract["sourceLadder"] == ["reuse", "derive", "build-new"]
    assert len(assets) == expected_count
    assert contract["mounts"] == terrain["landmarkMounts"]
    if mount_agnostic:
        assert contract["mounts"] == terrain["landmarkMounts"] == []
        assert contract["proposedIds"] == list(assets)
        assert "landmarkPack" not in terrain
    else:
        assert len(contract["mounts"]) == expected_count
        assert terrain["landmarkPack"]["contract"] == str(contract_path.relative_to(SOURCE))
        assert terrain["landmarkPack"]["atlas"] == str(atlas.relative_to(SOURCE))
    assert contract["atlas"]["width"] == contract["atlas"]["height"] <= 2048
    assert contract["atlas"]["sharedByEveryAsset"] is True
    assert sha256(atlas) == contract["atlas"]["sha256"]
    assert sha256(blend) == contract["blend"]["sha256"]
    assert all(mount["asset"] == assets[mount["id"]]["asset"] for mount in contract["mounts"])
    for mount in contract["mounts"]:
        conformed = assets[mount["id"]]["terrainConformed"]
        assert conformed is ("terrainConformOffsetY" in mount)
        if conformed:
            assert abs(mount["position"][1] - mount["terrainConformOffsetY"]) < 1e-6
    if key == "night-shift":
        assert assets["seven_lantern_terraces"]["authoredFixturePositions"] == NIGHT_LANTERN_FIXTURES

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
            "render_only": True,
            "landmark": True,
            "mount_id": identifier,
            "map_pack": key,
            "source_tier": record["sourceTier"],
            "era": contract["era"],
            "simulation_authority": "none; mounted render-only scenery",
        }
        assert extras == expected_extras
        assert record["sourceTier"] in {"reuse", "derive", "build-new"} and record["sources"]
        assert checked["meshes"] == checked["primitives"] == 1
        assert checked["triangles"] == record["triangles"] <= record["triangleBudget"] == 3000
        assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
        assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
        assert checked["materialContract"][0]["metallicFactor"] == 0
        assert checked["materialContract"][0]["roughnessFactor"] >= 0.89
        assert checked["materialContract"][0]["hasBaseColorTexture"]
        assert texture["width"] == texture["height"] == contract["atlas"]["width"] <= 2048
        assert texture["sha256"] == contract["atlas"]["sha256"]
        assert sha256(glb) == record["sha256"]
        assert abs(checked["bounds"]["min"][1]) < 0.0002
        assert abs(checked["bounds"]["center"][0]) < 0.0002
        assert abs(checked["bounds"]["center"][2]) < 0.0002

        reexport = Path("/tmp") / f"gold-rush-{key}-{identifier}-reexport.glb"
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
            "baseCentered": True,
        }
    return {"era": contract["era"], "atlasSha256": contract["atlas"]["sha256"], "assets": records}


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    selected = args or list(MAPS)
    unknown = sorted(set(selected) - set(MAPS))
    assert not unknown, f"unknown landmark packs: {unknown}"
    packs = {key: verify_pack(key, MAPS[key]) for key in selected}
    ledger = json.loads((LANDMARKS / "landmark-source-ledger.json").read_text(encoding="utf-8"))
    assert ledger["law"] == "reuse > derive > build-new; era-stamped; grit-dressed"
    assert set(selected).issubset(set(ledger["packs"]))
    tiers = {tier: 0 for tier in ("reuse", "derive", "build-new")}
    for pack in packs.values():
        for asset in pack["assets"].values():
            tiers[asset["sourceTier"]] += 1
    assert sum(tiers.values()) == sum(MAPS[key] for key in selected)
    boards = {}
    if not args:
        for name, size in BOARDS.items():
            path = ARTIFACTS / name
            assert path.is_file() and png_size(path) == size and path.stat().st_size > 100_000
            boards[name] = {"size": list(size), "sha256": sha256(path)}
    elif len(selected) == 1:
        for name, size in SCOPED_BOARDS.get(selected[0], {}).items():
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
    output_dir = ARTIFACTS / (f"{selected[0]}-landmarks" if len(selected) == 1 else "landmark-bar-unification") if args else ARTIFACTS
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "asset-contract.json" if args else output_dir / "landmark-pack-asset-contract.json"
    output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    report = output_dir / "reexport-evidence.md" if args else output_dir / "landmark-reexport-evidence.md"
    report.write_text(
        "# Landmark pack re-export evidence\n\n"
        f"- Packs: {len(packs)}\n- Assets: {sum(tiers.values())}\n"
        f"- Source tiers: reuse {tiers['reuse']}, derive {tiers['derive']}, build-new {tiers['build-new']}\n"
        "- Every GLB: one mesh, primitive, material, embedded pack atlas (<=2048); <=3,000 triangles.\n"
        "- Every source `.blend` re-export: byte-identical and semantic-identical.\n"
        "- Every body: base-centered, separately mounted, render-only, no simulation authority.\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence["totals"], indent=2))


if __name__ == "__main__":
    main()
