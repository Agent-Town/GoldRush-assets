"""Gate both Opus-5 duel entries against the duel ceilings and the shipped drop-in contract.

Reuses the shipped GLB parser (`verify_dredge_queen.contract`) read-only, then for each
boss: re-exports from the saved .blend and proves byte-identical + semantically identical
output, and asserts every clause of the runtime's model guard except the one the duel
deliberately raises (the exact-triangle constant, reported explicitly).

Run:
  Blender --background --python assets/pilots/dredge-queen-3d/verify_detail_opus5.py
"""

from pathlib import Path
import hashlib
import importlib.util
import json
import sys

import bpy

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
QUEEN = ROOT / "assets/pilots/dredge-queen-3d"
CLAW = ROOT / "assets/pilots/salvage-claw-3d"

ATLAS_CEILING = 2048
TRIANGLE_CEILING = 45_000

ENTRIES = {
    "dredge-queen": {
        "blend": QUEEN / "dredge-queen-detail-opus5.blend",
        "glb": QUEEN / "dredge-queen-detail-opus5.glb",
        "shipped": QUEEN / "dredge-queen.glb",
        "nodes": ["claw", "paddle_port", "paddle_starboard", "hold"],
        "morphs": {
            "clawMesh": ["Damage_SlackClaw", "Cycle_OpenGrab"],
            "paddle_portMesh": ["Damage_BrokenPortPaddle"],
            "paddle_starboardMesh": ["Damage_BrokenStarboardPaddle"],
            "holdMesh": ["Damage_CrackedLootHold"],
        },
        "footprint": 8.0,
        "runtimeGuard": {
            "file": "src/systems/DredgeQueenBossSystem.ts",
            "line": 18,
            "constant": "DREDGE_QUEEN_3D_TRIANGLES",
            "shipped": 11_832,
        },
        "plates": [ROOT / "assets/raw/boss-dredge-queen.png", ROOT / "assets/raw/boss-dredge-queen-damage.png"],
        "renders": QUEEN / "renders-detail-opus5",
    },
    "salvage-claw": {
        "blend": CLAW / "salvage-claw-detail-opus5.blend",
        "glb": CLAW / "salvage-claw-detail-opus5.glb",
        "shipped": CLAW / "salvage-claw.glb",
        "nodes": ["winch", "anchor_feet", "crown"],
        "morphs": {
            "winchMesh": ["Landing_SprungWinch"],
            "anchor_feetMesh": ["Landing_SettledAnchorFeet"],
            "crownMesh": ["Landing_DarkCrown"],
        },
        "footprint": 11.4,
        "runtimeGuard": {
            "file": "src/systems/SalvageClawBossSystem.ts",
            "line": 16,
            "constant": "MODEL_TRIANGLES",
            "shipped": 10_164,
        },
        "plates": [ROOT / "assets/raw/boss-salvage-claw.png", ROOT / "assets/raw/boss-salvage-claw-damage.png"],
        "renders": CLAW / "renders-detail-opus5",
    },
}

STABLE_KEYS = (
    "nodes", "nodeCount", "bindings", "nodeTransforms", "meshes", "meshNames", "primitives",
    "primitiveMaterials", "triangles", "morphTargets", "targetCounts", "materials",
    "materialTextureBindings", "materialContract", "textureSources", "images", "embeddedImages",
    "imageDimensions", "cameras", "lights", "animations", "bounds",
)

IDENTITY = {"translation": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0, 1.0], "scale": [1.0, 1.0, 1.0], "matrix": None}


def load_shipped_verifier():
    path = QUEEN / "verify_dredge_queen.py"
    spec = importlib.util.spec_from_file_location("detail_opus5_glb_parser", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["detail_opus5_glb_parser"] = module
    spec.loader.exec_module(module)
    return module


parser = load_shipped_verifier()


def reexport(blend: Path, nodes: list[str], destination: Path) -> dict:
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    mesh_objects = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    assert sorted(obj.name for obj in mesh_objects) == sorted(nodes), [obj.name for obj in mesh_objects]
    assert not [obj for obj in bpy.data.objects if obj.type == "CAMERA"]
    assert not [obj for obj in bpy.data.objects if obj.type == "LIGHT"]
    assert not list(bpy.data.actions)
    ordered = sorted(mesh_objects, key=lambda obj: nodes.index(obj.name))
    bpy.ops.object.select_all(action="DESELECT")
    for obj in ordered:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = ordered[0]
    bpy.ops.export_scene.gltf(
        filepath=str(destination.with_suffix("")),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_materials="EXPORT",
        export_morph=True,
    )
    return parser.contract(destination)


def check(name: str, spec: dict) -> dict:
    checked = parser.contract(spec["glb"])
    shipped = parser.contract(spec["shipped"])
    reexported = reexport(spec["blend"], spec["nodes"], Path(f"/tmp/{name}-detail-opus5-reexport.glb"))
    count = len(spec["nodes"])

    # --- duel ceilings -------------------------------------------------------------
    assert checked["triangles"] <= TRIANGLE_CEILING, checked["triangles"]
    assert checked["images"] == checked["embeddedImages"] == 1, checked["images"]
    assert all(max(dim) <= ATLAS_CEILING for dim in checked["imageDimensions"]), checked["imageDimensions"]

    # --- shipped drop-in contract, clause by clause ---------------------------------
    assert checked["nodes"] == spec["nodes"], checked["nodes"]
    assert checked["nodeCount"] == count
    assert checked["meshes"] == checked["primitives"] == count
    assert checked["primitiveMaterials"] == [0] * count
    assert checked["morphTargets"] == spec["morphs"], checked["morphTargets"]
    assert checked["targetCounts"] == {mesh: len(morphs) for mesh, morphs in spec["morphs"].items()}, checked["targetCounts"]
    assert all(binding["defaultWeights"] == [0.0] * len(spec["morphs"][binding["mesh"]]) for binding in checked["bindings"])
    assert all(transform == IDENTITY for transform in checked["nodeTransforms"].values())
    assert checked["materials"] == 1
    assert checked["materialTextureBindings"] == [{"material": 0, "baseColorTexture": 0, "image": 0}]
    assert checked["materialContract"] == shipped["materialContract"], checked["materialContract"]
    assert checked["textureSources"] == [0]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert abs(checked["bounds"]["size"][0] - spec["footprint"]) < 0.01, checked["bounds"]["size"]
    assert abs(checked["bounds"]["min"][1]) < 0.001, checked["bounds"]["min"]
    assert abs(checked["bounds"]["center"][0]) < 0.001
    assert abs(checked["bounds"]["center"][2]) < 0.001

    # --- determinism ----------------------------------------------------------------
    byte_identical = checked["sha256"] == reexported["sha256"]
    semantic = {key: checked[key] == reexported[key] for key in STABLE_KEYS}
    assert all(semantic.values()), [key for key, ok in semantic.items() if not ok]
    assert byte_identical, (checked["sha256"], reexported["sha256"])

    guard = dict(spec["runtimeGuard"])
    guard["required"] = checked["triangles"]
    guard["note"] = (
        f"Runtime requires exactly {checked['triangles']} triangles, the declared nodes and material, "
        f"and these ordered morph targets: {spec['morphs']}."
    )

    boards = sorted(spec["renders"].glob("*.png")) if spec["renders"].exists() else []
    return {
        "blender": bpy.app.version_string,
        "sourcePlates": {
            str(plate.relative_to(ROOT)): hashlib.sha256(plate.read_bytes()).hexdigest()
            for plate in spec["plates"]
        },
        "shipped": {
            "triangles": shipped["triangles"],
            "atlas": shipped["imageDimensions"],
            "bounds": shipped["bounds"],
            "bytes": shipped["bytes"],
        },
        "detail": {
            "triangles": checked["triangles"],
            "atlas": checked["imageDimensions"],
            "bounds": checked["bounds"],
            "bytes": checked["bytes"],
            "sha256": checked["sha256"],
            "materials": checked["materials"],
            "images": checked["images"],
            "primitives": checked["primitives"],
            "nodes": checked["nodes"],
            "morphTargets": checked["morphTargets"],
        },
        "triangleRatio": round(checked["triangles"] / shipped["triangles"], 3),
        "duelCeilings": {"triangles": TRIANGLE_CEILING, "atlas": ATLAS_CEILING, "withinBudget": True},
        "runtimeGuard": guard,
        "byteIdentical": byte_identical,
        "semanticIdentical": semantic,
        "boards": {
            str(board.relative_to(ROOT)): hashlib.sha256(board.read_bytes()).hexdigest()
            for board in boards
        },
        "checked": checked,
        "reexported": reexported,
    }


def main() -> None:
    report = {}
    for name, spec in ENTRIES.items():
        report[name] = check(name, spec)
        destination = spec["glb"].parent / f"{spec['glb'].stem}-asset-contract.json"
        destination.write_text(json.dumps(report[name], indent=2) + "\n")
        print(f"[verify] {name}: PASS")

    summary = {
        name: {
            "triangles": f"{data['shipped']['triangles']} -> {data['detail']['triangles']} ({data['triangleRatio']}x)",
            "atlas": f"{data['shipped']['atlas']} -> {data['detail']['atlas']}",
            "materials": data["detail"]["materials"],
            "byteIdentical": data["byteIdentical"],
            "runtimeConstant": f"{data['runtimeGuard']['constant']} {data['runtimeGuard']['shipped']} -> {data['runtimeGuard']['required']}",
        }
        for name, data in report.items()
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
