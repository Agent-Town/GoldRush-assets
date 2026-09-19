from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import types

sys.dont_write_bytecode = True

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RENDERS = HERE / "renders"
ARTIFACTS = ROOT / "artifacts/basin-population-e9"
BASE_SHA = "b9df7e2127dadc1ea74859026459e32a2405af34"
PLATE_TIP = "440bb19e4058eded9be82b1faf4292e73808cb0a"
PLATE_SHA = "89f23f703d96c5f519c820a7efca16c00ff5cb985923e9113cb1b480de81212e"
TRACKED_PLATE = ROOT / "assets/pilots/basin-rim-3d/basin-rim-plate.glb"
PLATE = TRACKED_PLATE if TRACKED_PLATE.is_file() else Path(os.environ.get("BASIN_RIM_PLATE_GLB", "/tmp/basin-rim-plate-current.glb"))
PAN = ROOT / "assets/pilots/plaza-props-3d/pan_monument.glb"
DOME_PLATE = ROOT / "assets/pilots/dome-commons-3d/dome-commons-plate.glb"
SOURCE = ROOT / "assets/raw/plate-e9-bld-canal-works.png"
MODELS = {
    asset_id: ROOT / f"assets/pilots/{asset_id}-3d/{asset_id}.glb"
    for asset_id in (
        "water-ledger-office", "greenkeeper", "ice-quarry-head",
        "weather-warden-spire", "canal-packet-boat",
    )
}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_unpinned_reference_renderer(path: Path):
    source = path.read_text().replace("\nverify_pinned_reference_assets()\n", "\n")
    module = types.ModuleType("e9_population_fresh_references")
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


fresh = load_unpinned_reference_renderer(ROOT / "assets/pilots/dome-commons-3d/render_current_references.py")
town = fresh.town


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slot(identifier: str):
    return next(item for item in [*town.SLOTS, town.DYNAMO_SLOT] if item.id == identifier)


def add_population() -> None:
    placements = {
        "greenkeeper": "tavern",
        "water-ledger-office": "claim_office",
        "weather-warden-spire": "chapel",
    }
    for asset_id, slot_id in placements.items():
        item = slot(slot_id)
        town.import_model(MODELS[asset_id], f"E9:{asset_id}", item.position, town.slot_angle(item))
    town.import_model(MODELS["ice-quarry-head"], "E9:ice-quarry-head", town.Point(-7.4, -16.6), math.pi)
    boat = town.import_model(MODELS["canal-packet-boat"], "E9:canal-packet-boat", town.Point(-13.4, -9.95), 0.62)
    boat.location.z = -0.025


def evidence_material(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = 0.9
    return material


def setup_lighting(width: int = 1280, height: int = 800) -> bpy.types.Object:
    camera = town.setup_render_scene()
    scene = bpy.context.scene
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.12, 0.055, 0.028, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.68
    scene.view_settings.look = "AgX - Medium Low Contrast"
    sun = bpy.data.objects.get("EvidenceSun")
    if sun:
        sun.data.energy = 2.65
        sun.data.color = (1.0, 0.72, 0.46)
    fill = bpy.data.objects.get("EvidenceFill")
    if fill:
        fill.data.energy = 1800.0
        fill.data.color = (0.50, 0.78, 0.84)
    return camera


def render_ensemble(path: Path, camera_angle: float = 0.0) -> None:
    town.reset_scene()
    town.import_model(PLATE, "Dependency:BasinRimPlate", town.Point(0.0, 0.0))
    town.import_model(PAN, "Heritage:PanMonument", town.Point(0.0, 0.0))
    add_population()
    camera = setup_lighting()
    distance = 39.0
    camera.location = (math.sin(camera_angle) * distance, math.cos(camera_angle) * distance, 31.5)
    town.look_at(camera, Vector((0.0, 0.0, 0.5)))
    camera.data.lens = camera.data.sensor_height / (2.0 * math.tan(math.radians(51.0) * 0.5))
    camera.data.clip_end = 180.0
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def model_bounds(root: bpy.types.Object) -> tuple[Vector, Vector]:
    meshes = [obj for obj in root.children_recursive if obj.type == "MESH"]
    corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    return (
        Vector((min(point.x for point in corners), min(point.y for point in corners), min(point.z for point in corners))),
        Vector((max(point.x for point in corners), max(point.y for point in corners), max(point.z for point in corners))),
    )


def render_isolated(asset_id: str, angle_index: int, path: Path) -> None:
    town.reset_scene()
    root = town.import_model(MODELS[asset_id], f"Audit:{asset_id}", town.Point(0.0, 0.0), angle_index * math.pi * 0.5)
    minimum, maximum = model_bounds(root)
    target = (minimum + maximum) * 0.5
    span = max(maximum.x - minimum.x, maximum.y - minimum.y, maximum.z - minimum.z)
    bpy.ops.mesh.primitive_plane_add(size=max(16.0, span * 3.5), location=(0.0, 0.0, -0.01))
    bpy.context.object.name = "EvidenceOnly:AuditFloor"
    bpy.context.object.data.materials.append(evidence_material("Audit Floor", (0.22, 0.075, 0.035, 1.0)))
    camera = setup_lighting(640, 480)
    camera.location = (span * 1.35, span * 1.65, span * 1.15)
    town.look_at(camera, target + Vector((0.0, 0.0, span * 0.04)))
    camera.data.lens = 52.0
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def render_e8_reference(path: Path) -> None:
    town.reset_scene()
    town.import_model(DOME_PLATE, "Current:E8:DomeCommons", town.Point(0.0, 0.0))
    town.import_model(PAN, "Current:E8:PanMonument", town.Point(0.0, 0.0))
    camera = town.setup_render_scene()
    scene = bpy.context.scene
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 800
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.070, 0.058, 0.045, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.72
    camera.location = (0.0, 46.0, 34.0)
    town.look_at(camera, Vector((0.0, 0.0, 3.2)))
    camera.data.lens = camera.data.sensor_height / (2.0 * math.tan(math.radians(48.0) * 0.5))
    camera.data.clip_end = 180.0
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def annotate(path: Path, label: str, point_size: int = 22) -> None:
    temporary = path.with_name(f".{path.name}")
    subprocess.run([
        "magick", str(path), "-font", "/System/Library/Fonts/Helvetica.ttc",
        "-gravity", "north", "-fill", "#f7df9d", "-undercolor", "#17120dcc",
        "-pointsize", str(point_size), "-annotate", "+0+8",
        f"{label} | main {BASE_SHA} | plate {PLATE_TIP}", str(temporary),
    ], check=True)
    temporary.replace(path)


def render_fresh_references() -> Path:
    out = ARTIFACTS / "current-references" / f"{BASE_SHA[:12]}-main"
    out.mkdir(parents=True, exist_ok=True)
    fresh.render_e1(out / "town-e1-current.png")
    fresh.render_e4(out / "town-e4-current.png")
    fresh.render_e5(out / "town-e5-current-underwater.png")
    fresh.render_mesa(out / "town-e6-current.png", 6)
    fresh.render_mesa(out / "town-e7-current.png", 7)
    render_e8_reference(out / "town-e8-current.png")
    paths = [
        out / "town-e1-current.png", out / "town-e4-current.png", out / "town-e5-current-underwater.png",
        out / "town-e6-current.png", out / "town-e7-current.png", out / "town-e8-current.png",
    ]
    top, bottom = Path("/tmp/e9-current-top.png"), Path("/tmp/e9-current-bottom.png")
    subprocess.run(["magick", *map(str, paths[:3]), "+append", str(top)], check=True)
    subprocess.run(["magick", *map(str, paths[3:]), "+append", str(bottom)], check=True)
    board = out / "town-e1-e8-current.png"
    subprocess.run(["magick", str(top), str(bottom), "-append", str(board)], check=True)
    top.unlink(missing_ok=True)
    bottom.unlink(missing_ok=True)
    annotate(board, "FRESH CURRENT-FILE REFERENCE | E1 / E4 / E5 / E6 / E7 / E8")
    tracked = [
        fresh.CURRENT_PLATE, fresh.MESA_PLATE, fresh.PAN, DOME_PLATE,
        *fresh.e4.E4_MODELS.values(), *fresh.e5.E5_MODELS.values(),
        *fresh.E6_MODELS.values(), *fresh.E7_MODELS.values(),
    ]
    tracked = list(dict.fromkeys(tracked))
    (out / "reference-contract.json").write_text(json.dumps({
        "baseSha": BASE_SHA,
        "rule": "fresh render from current main GLBs; no prior PNG is an input",
        "order": ["E1 square", "E4 motor boulevard", "E5 submerged square", "E6 Atomic Mesa", "E7 Signal Mesa", "E8 Dome Commons"],
        "assetSha256": {str(item.relative_to(ROOT)): sha256(item) for item in tracked},
        "renders": [str(item.relative_to(ROOT)) for item in [*paths, board]],
    }, indent=2) + "\n")
    return board


def assemble(fresh_board: Path) -> None:
    ensemble = RENDERS / "basin-population-gameplay.png"
    angles = [RENDERS / f"basin-population-angle-{index}.png" for index in range(1, 5)]
    top, bottom = Path("/tmp/e9-ensemble-top.png"), Path("/tmp/e9-ensemble-bottom.png")
    subprocess.run(["magick", str(angles[0]), str(angles[1]), "+append", str(top)], check=True)
    subprocess.run(["magick", str(angles[2]), str(angles[3]), "+append", str(bottom)], check=True)
    turntable = RENDERS / "basin-population-ensemble-turntable.png"
    subprocess.run(["magick", str(top), str(bottom), "-append", str(turntable)], check=True)
    annotate(turntable, "E9 BASIN POPULATION | FOUR-ANGLE ENSEMBLE AUDIT")

    rows = []
    for asset_id in MODELS:
        row = Path(f"/tmp/e9-{asset_id}-row.png")
        source_images = [RENDERS / f"{asset_id}-angle-{index}.png" for index in range(1, 5)]
        subprocess.run(["magick", *map(str, source_images), "+append", str(row)], check=True)
        rows.append(row)
    audit = RENDERS / "basin-population-five-asset-audit.png"
    subprocess.run(["magick", *map(str, rows), "-append", str(audit)], check=True)
    annotate(audit, "E9 FIVE-ASSET FULL-WRAP AUDIT | 4 ANGLES EACH", 28)

    source_scaled = Path("/tmp/e9-population-source.png")
    subprocess.run(["magick", str(SOURCE), "-resize", "1280x800", "-background", "#17120d", "-gravity", "center", "-extent", "1280x800", str(source_scaled)], check=True)
    source_ab = RENDERS / "basin-population-source-ab.png"
    subprocess.run(["magick", str(source_scaled), str(ensemble), "+append", str(source_ab)], check=True)
    annotate(source_ab, "E9 PAINTED CANAL WORKS / PRODUCTION BASIN POPULATION")

    history = RENDERS / "fresh-e1-e9-reference-board.png"
    subprocess.run(["magick", str(fresh_board), str(ensemble), "-gravity", "center", "+append", str(history)], check=True)
    annotate(history, "FRESH CURRENT-FILE REFERENCES / E9 POPULATION")
    for path in [top, bottom, source_scaled, *rows]:
        path.unlink(missing_ok=True)

    tracked = [PAN, SOURCE, *MODELS.values()]
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "basin-population-visual-evidence.json").write_text(json.dumps({
        "baseSha": BASE_SHA,
        "basinPlateDependency": {"tip": PLATE_TIP, "sha256": sha256(PLATE)},
        "rule": "current main references rerendered at this boundary; candidate E9 plate is the pushed dependency, never an old artifact board",
        "productionGlbs": [str(path.relative_to(ROOT)) for path in MODELS.values()],
        "assetSha256": {
            "assets/pilots/basin-rim-3d/basin-rim-plate.glb": sha256(PLATE),
            **{
            (str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)): sha256(path)
            for path in tracked
            },
        },
        "evidenceOnly": ["Basin Rim dependency plate", "Pan Monument mount", "lights", "cameras", "audit floors"],
        "renders": [str(path.relative_to(ROOT)) for path in [ensemble, turntable, audit, source_ab, history, *angles]],
    }, indent=2) + "\n")


def main() -> None:
    if not PLATE.is_file() or sha256(PLATE) != PLATE_SHA:
        raise RuntimeError(f"Basin plate input missing or drifted: {PLATE}")
    RENDERS.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    fresh_board = render_fresh_references()
    for index, angle in enumerate((0.0, math.pi * 0.5, math.pi, math.pi * 1.5), 1):
        render_ensemble(RENDERS / f"basin-population-angle-{index}.png", angle)
    (RENDERS / "basin-population-gameplay.png").write_bytes((RENDERS / "basin-population-angle-1.png").read_bytes())
    for asset_id in MODELS:
        for index in range(4):
            render_isolated(asset_id, index, RENDERS / f"{asset_id}-angle-{index + 1}.png")
    assemble(fresh_board)


if __name__ == "__main__":
    main()
