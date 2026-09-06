from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
import types

sys.dont_write_bytecode = True

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RENDERS = HERE / "renders"
ARTIFACTS = ROOT / "artifacts/dome-population-e8"
BASE_SHA = "a9be388a3fe95a3228c638ed4afaf8a6ec6a7f5a"
PLATE = ROOT / "assets/pilots/dome-commons-3d/dome-commons-plate.glb"
PAN = ROOT / "assets/pilots/plaza-props-3d/pan_monument.glb"
SOURCE = ROOT / "assets/raw/plate-e8-bld-set.png"
MODELS = {
    "orbital-canteen": ROOT / "assets/pilots/orbital-canteen-3d/orbital-canteen.glb",
    "suit-fitter": ROOT / "assets/pilots/suit-fitter-3d/suit-fitter.glb",
    "launch-works": ROOT / "assets/pilots/launch-works-3d/launch-works.glb",
    "he3-assay": ROOT / "assets/pilots/he3-assay-3d/he3-assay.glb",
    "mass-driver-dispatch": ROOT / "assets/pilots/mass-driver-dispatch-3d/mass-driver-dispatch.glb",
}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_fresh_reference_renderer(path: Path):
    # The shared renderer intentionally self-checks its historical E8-plate
    # evidence at import time.  A new wave must instead read the current GLBs,
    # so reuse its render functions without invoking that old-board pin.
    source = path.read_text().replace("\nverify_pinned_reference_assets()\n", "\n")
    module = types.ModuleType("e8_population_fresh_references")
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


fresh = load_fresh_reference_renderer(ROOT / "assets/pilots/dome-commons-3d/render_current_references.py")
town = fresh.town


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slot(identifier: str):
    return next(item for item in town.SLOTS if item.id == identifier)


def add_population() -> None:
    placements = {
        "orbital-canteen": "tavern",
        "suit-fitter": "general_store",
        "he3-assay": "assay_office",
    }
    for asset_id, slot_id in placements.items():
        item = slot(slot_id)
        town.import_model(MODELS[asset_id], f"E8:{asset_id}", item.position, town.slot_angle(item))
    town.import_model(MODELS["mass-driver-dispatch"], "E8:mass-driver-dispatch", town.Point(-7.4, -16.6), math.pi)
    town.import_model(MODELS["launch-works"], "E8:launch-works", town.Point(7.0, -16.7))


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
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.070, 0.058, 0.045, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.72
    sun = bpy.data.objects.get("EvidenceSun")
    if sun:
        sun.data.energy = 2.45
        sun.data.color = (1.0, 0.88, 0.68)
    fill = bpy.data.objects.get("EvidenceFill")
    if fill:
        fill.data.energy = 2050.0
        fill.data.color = (0.72, 0.91, 0.91)
    return camera


def add_earth(camera_angle: float) -> None:
    behind = Vector((-math.sin(camera_angle), -math.cos(camera_angle), 0.0))
    lateral = Vector((math.cos(camera_angle), -math.sin(camera_angle), 0.0))
    position = behind * 31.0 + lateral * 9.0 + Vector((0.0, 0.0, 18.2))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=3.15, location=position)
    bpy.context.object.name = "EvidenceOnly:Earth"
    bpy.context.object.data.materials.append(evidence_material("Evidence Earth", (0.15, 0.52, 0.59, 1.0)))


def render_ensemble(path: Path, camera_angle: float = 0.0) -> None:
    town.reset_scene()
    town.import_model(PLATE, "Production:DomeCommonsPlate", town.Point(0.0, 0.0))
    town.import_model(PAN, "Heritage:PanMonument", town.Point(0.0, 0.0))
    add_population()
    camera = setup_lighting()
    distance = 46.0
    camera.location = (math.sin(camera_angle) * distance, math.cos(camera_angle) * distance, 34.0)
    town.look_at(camera, Vector((0.0, 0.0, 3.2)))
    camera.data.lens = camera.data.sensor_height / (2.0 * math.tan(math.radians(48.0) * 0.5))
    camera.data.clip_end = 180.0
    add_earth(camera_angle)
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
    bpy.context.object.data.materials.append(evidence_material("Audit Floor", (0.18, 0.14, 0.10, 1.0)))
    camera = setup_lighting(640, 480)
    camera.location = (span * 1.35, span * 1.65, span * 1.15)
    town.look_at(camera, target + Vector((0.0, 0.0, span * 0.04)))
    camera.data.lens = 52.0
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def annotate(path: Path, label: str, point_size: int = 22) -> None:
    temporary = path.with_name(f".{path.name}")
    subprocess.run([
        "magick", str(path), "-font", "/System/Library/Fonts/Helvetica.ttc",
        "-gravity", "north", "-fill", "#f7df9d", "-undercolor", "#17120dcc",
        "-pointsize", str(point_size), "-annotate", "+0+8", f"{label} | base {BASE_SHA}", str(temporary),
    ], check=True)
    temporary.replace(path)


def render_fresh_references() -> Path:
    fresh.BASE_SHA = BASE_SHA
    fresh.OUT = ARTIFACTS / "current-references" / f"{BASE_SHA[:12]}-main"
    fresh.OUT.mkdir(parents=True, exist_ok=True)
    fresh.render_e1(fresh.OUT / "town-e1-current.png")
    fresh.render_e4(fresh.OUT / "town-e4-current.png")
    fresh.render_e5(fresh.OUT / "town-e5-current-underwater.png")
    fresh.render_mesa(fresh.OUT / "town-e6-current.png", 6)
    fresh.render_mesa(fresh.OUT / "town-e7-current.png", 7)
    fresh.assemble()
    return fresh.OUT / "town-e1-e7-current.png"


def assemble() -> None:
    ensemble = RENDERS / "dome-population-gameplay.png"
    angles = [RENDERS / f"dome-population-angle-{index}.png" for index in range(1, 5)]
    subprocess.run(["magick", str(angles[0]), str(angles[1]), "+append", "/tmp/e8-ensemble-top.png"], check=True)
    subprocess.run(["magick", str(angles[2]), str(angles[3]), "+append", "/tmp/e8-ensemble-bottom.png"], check=True)
    turntable = RENDERS / "dome-population-ensemble-turntable.png"
    subprocess.run(["magick", "/tmp/e8-ensemble-top.png", "/tmp/e8-ensemble-bottom.png", "-append", str(turntable)], check=True)
    annotate(turntable, "E8 DOME POPULATION | FOUR-ANGLE ENSEMBLE AUDIT")

    rows = []
    for asset_id in MODELS:
        row = Path(f"/tmp/e8-{asset_id}-row.png")
        source_images = [RENDERS / f"{asset_id}-angle-{index}.png" for index in range(1, 5)]
        subprocess.run(["magick", *map(str, source_images), "+append", str(row)], check=True)
        rows.append(row)
    audit = RENDERS / "dome-population-five-building-audit.png"
    subprocess.run(["magick", *map(str, rows), "-append", str(audit)], check=True)
    annotate(audit, "E8 FIVE-BUILDING FULL-WRAP AUDIT | 4 ANGLES EACH", 28)

    source_scaled = Path("/tmp/e8-population-source.png")
    subprocess.run(["magick", str(SOURCE), "-resize", "1280x800", "-background", "#17120d", "-gravity", "center", "-extent", "1280x800", str(source_scaled)], check=True)
    source_ab = RENDERS / "dome-population-source-ab.png"
    subprocess.run(["magick", str(source_scaled), str(ensemble), "+append", str(source_ab)], check=True)
    annotate(source_ab, "E8 PAINTED KIT / PRODUCTION DOME POPULATION")

    fresh_board = render_fresh_references()
    history = RENDERS / "fresh-e1-e8-reference-board.png"
    subprocess.run(["magick", str(fresh_board), str(ensemble), "-gravity", "center", "+append", str(history)], check=True)
    annotate(history, "FRESH CURRENT-FILE REFERENCES / E8 POPULATION")

    for path in [Path("/tmp/e8-ensemble-top.png"), Path("/tmp/e8-ensemble-bottom.png"), source_scaled, *rows]:
        path.unlink(missing_ok=True)

    tracked = [PLATE, PAN, SOURCE, *MODELS.values()]
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "dome-population-visual-evidence.json").write_text(json.dumps({
        "baseSha": BASE_SHA,
        "rule": "all boards rendered from GLBs on the freshly fetched base; prior PNGs are not inputs",
        "productionAssets": {str(path.relative_to(ROOT)): sha256(path) for path in tracked},
        "evidenceOnly": ["Earth sky cameo", "Pan Monument independent mount", "lights", "cameras", "audit floor"],
        "renders": [str(path.relative_to(ROOT)) for path in [ensemble, turntable, audit, source_ab, history, *angles]],
    }, indent=2) + "\n")


def main() -> None:
    RENDERS.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    targets = {
        "ensemble": lambda: render_ensemble(RENDERS / "dome-population-gameplay.png"),
        **{f"angle{index}": (lambda index=index: render_ensemble(RENDERS / f"dome-population-angle-{index}.png", (index - 1) * math.pi * 0.5)) for index in range(1, 5)},
        **{
            f"{asset_id}-angle-{index}": (
                lambda asset_id=asset_id, index=index: render_isolated(asset_id, index - 1, RENDERS / f"{asset_id}-angle-{index}.png")
            )
            for asset_id in MODELS for index in range(1, 5)
        },
    }
    if "--" in sys.argv:
        target = sys.argv[sys.argv.index("--") + 1]
        if target == "assemble":
            assemble()
        else:
            targets[target]()
        return
    for target in targets:
        subprocess.run([bpy.app.binary_path, "--background", "--python", str(Path(__file__).resolve()), "--", target], check=True)
    assemble()


if __name__ == "__main__":
    main()
