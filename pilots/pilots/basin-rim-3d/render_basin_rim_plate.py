from __future__ import annotations

from pathlib import Path
import importlib.util
import json
import math
import subprocess
import sys

sys.dont_write_bytecode = True

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RENDERS = HERE / "renders"
ARTIFACTS = ROOT / "artifacts/basin-rim-e9"
GLB = HERE / "basin-rim-plate.glb"
PAN = ROOT / "assets/pilots/plaza-props-3d/pan_monument.glb"
SOURCE = ROOT / "assets/raw/kit-era-9.png"
BASE_SHA = "c272d3a8ba9c36ee2550c7bb55c3fb05edab087e"
CURRENT_E8 = ARTIFACTS / "current-references" / f"{BASE_SHA[:12]}-main/town-e8-current.png"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


builder = load("basin_rim_render_builder", HERE / "build_basin_rim_plate.py")
town = builder.town


def material(name: str, color: tuple[float, float, float, float], emission: float) -> bpy.types.Material:
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = 0.78
    shader.inputs["Emission Color"].default_value = color
    shader.inputs["Emission Strength"].default_value = emission
    return result


def pad_outline(pad):
    if pad.shape == "circle":
        return [
            town.Point(
                pad.position.x + math.cos(index / 40.0 * math.tau) * pad.width * 0.5,
                pad.position.y + math.sin(index / 40.0 * math.tau) * pad.width * 0.5,
            )
            for index in range(40)
        ]
    return [
        town.Point(pad.position.x - pad.width * 0.5, pad.position.y - pad.depth * 0.5),
        town.Point(pad.position.x + pad.width * 0.5, pad.position.y - pad.depth * 0.5),
        town.Point(pad.position.x + pad.width * 0.5, pad.position.y + pad.depth * 0.5),
        town.Point(pad.position.x - pad.width * 0.5, pad.position.y + pad.depth * 0.5),
    ]


def add_overlay() -> None:
    route = material("Evidence Routes", (0.04, 0.82, 0.75, 1.0), 2.4)
    pad = material("Evidence Pads", (1.0, 0.66, 0.08, 1.0), 2.2)
    town.curve_object("WalkLoop:ring", town.RING_ROUTE, route, True, 0.085)
    for route_id, points in town.RADIAL_ROUTES.items():
        town.curve_object(f"WalkLoop:{route_id}", points, route, False, 0.085)
    for slot in builder.CANONICAL_SLOTS:
        town.curve_object(f"FlatPad:{slot.id}", town.pad_outline(slot), pad, True, 0.09)
    for basin_pad in builder.BASIN_PADS:
        town.curve_object(f"FlatPad:{basin_pad.id}", pad_outline(basin_pad), pad, True, 0.09)


def setup(camera_angle: float = 0.0, overlay: bool = False) -> None:
    town.reset_scene()
    town.import_model(GLB, "Production:BasinRimPlate", town.Point(0.0, 0.0))
    town.import_model(PAN, "EvidenceOnly:PanMonument", town.Point(0.0, 0.0))
    if overlay:
        add_overlay()
    camera = town.setup_render_scene()
    scene = bpy.context.scene
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 800
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.12, 0.055, 0.028, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.68
    scene.view_settings.look = "AgX - Medium Low Contrast"
    distance = 39.0
    camera.location = (math.sin(camera_angle) * distance, math.cos(camera_angle) * distance, 31.5)
    town.look_at(camera, Vector((0.0, 0.0, -0.05)))
    camera.data.lens = camera.data.sensor_height / (2.0 * math.tan(math.radians(51.0) * 0.5))
    camera.data.clip_end = 180.0
    sun = bpy.data.objects.get("EvidenceSun")
    if sun:
        sun.data.energy = 2.65
        sun.data.color = (1.0, 0.72, 0.46)
    fill = bpy.data.objects.get("EvidenceFill")
    if fill:
        fill.data.energy = 1800.0
        fill.data.color = (0.50, 0.78, 0.84)


def render(path: Path, angle: float = 0.0, overlay: bool = False) -> None:
    setup(angle, overlay)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def annotate(path: Path, label: str) -> None:
    temporary = path.with_name(f".{path.name}")
    subprocess.run([
        "magick", str(path), "-font", "/System/Library/Fonts/Helvetica.ttc", "-gravity", "north",
        "-fill", "#f7df9d", "-undercolor", "#17120dcc", "-pointsize", "22",
        "-annotate", "+0+8", f"{label} | base {BASE_SHA}", str(temporary),
    ], check=True)
    temporary.replace(path)


def assemble() -> None:
    camera = RENDERS / "basin-rim-plate-camera.png"
    overlay = RENDERS / "basin-rim-flat-walk-overlay.png"
    angles = [RENDERS / f"basin-rim-angle-{index}.png" for index in range(1, 5)]
    rows = [Path("/tmp/basin-rim-row-a.png"), Path("/tmp/basin-rim-row-b.png")]
    subprocess.run(["magick", str(angles[0]), str(angles[1]), "+append", str(rows[0])], check=True)
    subprocess.run(["magick", str(angles[2]), str(angles[3]), "+append", str(rows[1])], check=True)
    turntable = RENDERS / "basin-rim-turntable.png"
    subprocess.run(["magick", str(rows[0]), str(rows[1]), "-append", str(turntable)], check=True)
    for row in rows:
        row.unlink(missing_ok=True)
    annotate(turntable, "E9 BASIN RIM | FOUR-ANGLE RELIEF AUDIT")
    annotate(overlay, "FLAT-WALK PROOF | TEAL ROUTES / AMBER PADS")

    previous_ab = RENDERS / "dome-commons-vs-basin-rim-ab.png"
    subprocess.run(["magick", str(CURRENT_E8), str(camera), "+append", str(previous_ab)], check=True)
    annotate(previous_ab, "CURRENT E8 DOME COMMONS / E9 BASIN RIM FRESH SITE")

    resized = Path("/tmp/basin-rim-source.png")
    subprocess.run([
        "magick", str(SOURCE), "-resize", "1280x800", "-background", "#17120d",
        "-gravity", "center", "-extent", "1280x800", str(resized),
    ], check=True)
    source_ab = RENDERS / "basin-rim-source-ab.png"
    subprocess.run(["magick", str(resized), str(camera), "+append", str(source_ab)], check=True)
    resized.unlink(missing_ok=True)
    annotate(source_ab, "E9 PAINTED VOCABULARY / PRODUCTION PLATE")

    evidence = {
        "baseSha": BASE_SHA,
        "productionGlb": str(GLB.relative_to(ROOT)),
        "freshReference": str(CURRENT_E8.relative_to(ROOT)),
        "sourcePlate": str(SOURCE.relative_to(ROOT)),
        "evidenceOnly": ["Pan Monument mount", "lights", "cameras", "route/pad overlays"],
        "renders": [str(path.relative_to(ROOT)) for path in [camera, overlay, turntable, previous_ab, source_ab, *angles]],
    }
    (ARTIFACTS / "basin-rim-visual-evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")


def main() -> None:
    RENDERS.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    targets = {
        "camera": lambda: render(RENDERS / "basin-rim-plate-camera.png"),
        "overlay": lambda: render(RENDERS / "basin-rim-flat-walk-overlay.png", overlay=True),
        "angle1": lambda: render(RENDERS / "basin-rim-angle-1.png", 0.0),
        "angle2": lambda: render(RENDERS / "basin-rim-angle-2.png", math.pi * 0.5),
        "angle3": lambda: render(RENDERS / "basin-rim-angle-3.png", math.pi),
        "angle4": lambda: render(RENDERS / "basin-rim-angle-4.png", math.pi * 1.5),
    }
    if "--" in sys.argv:
        target = sys.argv[sys.argv.index("--") + 1]
        targets[target]()
        return
    for target in targets:
        subprocess.run([bpy.app.binary_path, "--background", "--python", str(Path(__file__).resolve()), "--", target], check=True)
    assemble()


if __name__ == "__main__":
    main()
