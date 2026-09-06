from __future__ import annotations

from pathlib import Path
import importlib.util
import json
import math
import random
import subprocess
import sys

sys.dont_write_bytecode = True

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RENDERS = HERE / "renders"
ARTIFACTS = ROOT / "artifacts/ark-plaza-e10"
GLB = HERE / "ark-plaza-e10.glb"
PAN = ROOT / "assets/pilots/plaza-props-3d/pan_monument.glb"
SOURCE_ARK = ROOT / "assets/raw/kit-the-ark.png"
SOURCE_INTERIOR = ROOT / "assets/raw/kit-era-10.png"
BASE_SHA = "d944dc7ebd690141d52f363d38aa6dc1a83f4343"
CURRENT_E8 = ARTIFACTS / "current-references" / f"{BASE_SHA[:12]}-main/town-e8-current.png"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


builder = load_module("ark_plaza_render_builder", HERE / "build_ark_plaza.py")
town = builder.town


def material(name: str, color: tuple[float, float, float, float], emission: float = 0.0):
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = 0.82
    if emission:
        shader.inputs["Emission Color"].default_value = color
        shader.inputs["Emission Strength"].default_value = emission
    return result


def add_pan() -> None:
    town.import_model(PAN, "EvidenceOnly:HeritagePanMonument", town.Point(0.0, 0.0))


def add_starfield() -> None:
    star = material("EvidenceOnly:StarGold", (0.96, 0.70, 0.28, 1.0), 3.5)
    random.seed(10)
    for index in range(150):
        radius = random.uniform(25.5, 50.0)
        angle = random.uniform(0.0, math.tau)
        size = random.choice((0.022, 0.028, 0.038, 0.055))
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=1, radius=size,
            location=(math.cos(angle) * radius, math.sin(angle) * radius, -0.78),
        )
        point = bpy.context.object
        point.name = f"EvidenceOnly:Star:{index:03d}"
        point.data.materials.append(star)


def add_overlay() -> None:
    route = material("EvidenceOnly:WalkRoute", (0.04, 0.76, 0.72, 1.0), 2.7)
    pad = material("EvidenceOnly:FlatPad", (0.98, 0.57, 0.13, 1.0), 2.2)
    town.curve_object("WalkLoop:ring", town.RING_ROUTE, route, True, 0.08)
    for route_id, points in town.RADIAL_ROUTES.items():
        town.curve_object(f"WalkRoute:{route_id}", points, route, False, 0.08)
    for slot in [*town.SLOTS, town.DYNAMO_SLOT]:
        town.curve_object(f"CanonicalPad:{slot.id}", town.pad_outline(slot), pad, True, 0.09)


def setup(camera_angle: float, overlay: bool = False) -> None:
    town.reset_scene()
    town.import_model(GLB, "Production:ArkPlazaE10", town.Point(0.0, 0.0))
    add_pan()
    add_starfield()
    if overlay:
        add_overlay()
    camera = town.setup_render_scene()
    scene = bpy.context.scene
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 800
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.018, 0.028, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.42
    scene.view_settings.look = "AgX - Medium Low Contrast"
    scene.view_settings.exposure = 0.65
    distance = 39.0
    camera.location = (math.sin(camera_angle) * distance, math.cos(camera_angle) * distance, 32.0)
    town.look_at(camera, Vector((0.0, 0.0, 1.2)))
    camera.data.lens = camera.data.sensor_height / (2.0 * math.tan(math.radians(50.0) * 0.5))
    camera.data.clip_end = 180.0
    sun = bpy.data.objects.get("EvidenceSun")
    if sun:
        sun.data.energy = 2.65
        sun.data.color = (1.0, 0.70, 0.38)
    fill = bpy.data.objects.get("EvidenceFill")
    if fill:
        fill.data.energy = 2260.0
        fill.data.color = (0.27, 0.80, 0.82)
    bpy.ops.object.light_add(type="AREA", location=(-14.0, -8.0, 14.0))
    ship_light = bpy.context.object
    ship_light.name = "EvidenceOnly:ShipLight"
    ship_light.data.energy = 900.0
    ship_light.data.shape = "DISK"
    ship_light.data.size = 8.0
    ship_light.data.color = (0.22, 0.92, 0.87)
    town.look_at(ship_light, Vector((0.0, 0.0, 0.0)))
    bpy.ops.object.light_add(type="AREA", location=(0.0, 14.0, 13.0))
    hall_light = bpy.context.object
    hall_light.name = "EvidenceOnly:LongTableWarmth"
    hall_light.data.energy = 1650.0
    hall_light.data.shape = "RECTANGLE"
    hall_light.data.size = 9.0
    hall_light.data.color = (1.0, 0.57, 0.25)
    town.look_at(hall_light, Vector((0.0, 19.0, 3.0)))


def render(path: Path, camera_angle: float = 0.0, overlay: bool = False) -> None:
    setup(camera_angle, overlay)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def annotate(path: Path, label: str) -> None:
    temporary = path.with_name(f".{path.name}")
    subprocess.run([
        "magick", str(path), "-font", "/System/Library/Fonts/Helvetica.ttc",
        "-gravity", "north", "-fill", "#f7df9d", "-undercolor", "#10151ddd",
        "-pointsize", "22", "-annotate", "+0+8", f"{label} | base {BASE_SHA}", str(temporary),
    ], check=True)
    temporary.replace(path)


def source_panel(source: Path, output: Path) -> None:
    subprocess.run([
        "magick", str(source), "-resize", "1280x800", "-background", "#10151d",
        "-gravity", "center", "-extent", "1280x800", str(output),
    ], check=True)


def assemble() -> None:
    camera = RENDERS / "ark-plaza-gameplay.png"
    overlay = RENDERS / "ark-plaza-flat-walk-overlay.png"
    angles = [RENDERS / f"ark-plaza-angle-{index}.png" for index in range(1, 5)]
    row_a = Path("/tmp/ark-plaza-row-a.png")
    row_b = Path("/tmp/ark-plaza-row-b.png")
    subprocess.run(["magick", str(angles[0]), str(angles[1]), "+append", str(row_a)], check=True)
    subprocess.run(["magick", str(angles[2]), str(angles[3]), "+append", str(row_b)], check=True)
    turntable = RENDERS / "ark-plaza-four-angle-audit.png"
    subprocess.run(["magick", str(row_a), str(row_b), "-append", str(turntable)], check=True)
    row_a.unlink(missing_ok=True)
    row_b.unlink(missing_ok=True)
    annotate(turntable, "ARK PLAZA | FOUR-ANGLE HULL / PORTAL AUDIT")
    annotate(overlay, "FLAT-WALK PROOF | TEAL ROUTES / AMBER CANONICAL PADS")

    source_ark = Path("/tmp/ark-source-panel.png")
    source_panel(SOURCE_ARK, source_ark)
    source_ab = RENDERS / "ark-source-vs-plaza-ab.png"
    subprocess.run(["magick", str(source_ark), str(camera), "+append", str(source_ab)], check=True)
    source_ark.unlink(missing_ok=True)
    annotate(source_ab, "SHIPPED ARK VOCABULARY / PRODUCTION WALKABLE PLAZA")

    source_interior = Path("/tmp/ark-interior-panel.png")
    source_panel(SOURCE_INTERIOR, source_interior)
    interior_ab = RENDERS / "ark-interior-vs-plaza-ab.png"
    subprocess.run(["magick", str(source_interior), str(camera), "+append", str(interior_ab)], check=True)
    source_interior.unlink(missing_ok=True)
    annotate(interior_ab, "TEN ERA DECK GRAMMARS / PLAZA CONVERGENCE")

    site_ab = RENDERS / "dome-commons-vs-ark-plaza-ab.png"
    subprocess.run(["magick", str(CURRENT_E8), str(camera), "+append", str(site_ab)], check=True)
    annotate(site_ab, "CURRENT MAIN E8 SITE / E10 ARK PLAZA")

    evidence = {
        "baseSha": BASE_SHA,
        "target": "working Ark plaza; ten era decks converge on the unchanged Pan Monument in its final ship-light fountain",
        "productionGlb": str(GLB.relative_to(ROOT)),
        "freshReference": str(CURRENT_E8.relative_to(ROOT)),
        "evidenceOnly": ["Pan Monument mount", "deep-ink starfield", "lights", "cameras", "route/pad overlay"],
        "renders": [str(path.relative_to(ROOT)) for path in [camera, overlay, turntable, source_ab, interior_ab, site_ab, *angles]],
    }
    (ARTIFACTS / "ark-plaza-visual-evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")


def main() -> None:
    RENDERS.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    targets = {
        "camera": lambda: render(RENDERS / "ark-plaza-gameplay.png", math.pi),
        "overlay": lambda: render(RENDERS / "ark-plaza-flat-walk-overlay.png", math.pi, True),
        "angle1": lambda: render(RENDERS / "ark-plaza-angle-1.png", math.pi),
        "angle2": lambda: render(RENDERS / "ark-plaza-angle-2.png", math.pi * 1.5),
        "angle3": lambda: render(RENDERS / "ark-plaza-angle-3.png", 0.0),
        "angle4": lambda: render(RENDERS / "ark-plaza-angle-4.png", math.pi * 0.5),
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
