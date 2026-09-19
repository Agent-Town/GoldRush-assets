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
ARTIFACTS = ROOT / "artifacts/dome-commons-e8"
GLB = HERE / "dome-commons-plate.glb"
PAN = ROOT / "assets/pilots/plaza-props-3d/pan_monument.glb"
SOURCE_PLATE = ROOT / "assets/raw/plate-e8-bld-set.png"
BASE_SHA = "2736e176d69226d40603889ee3e1aa07db623784"
CURRENT_E7 = ROOT / "artifacts/dome-commons-e8/current-references" / f"{BASE_SHA[:12]}-main/town-e7-current.png"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


builder = load_module("dome_render_builder", HERE / "build_dome_commons_plate.py")
town = builder.town


def material(name: str, color: tuple[float, float, float, float], roughness: float = 0.82,
             emission: float = 0.0) -> bpy.types.Material:
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = 0.0
    if emission:
        shader.inputs["Emission Color"].default_value = color
        shader.inputs["Emission Strength"].default_value = emission
    return result


def add_earth_cameo(camera_angle: float) -> None:
    # Evidence-only sky rig. The production GLB owns the air wall and floor;
    # the game's sky system owns Earth.
    behind = Vector((-math.sin(camera_angle), -math.cos(camera_angle), 0.0))
    lateral = Vector((math.cos(camera_angle), -math.sin(camera_angle), 0.0))
    position = behind * 31.0 + lateral * 9.0 + Vector((0.0, 0.0, 18.2))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=3.15, location=position)
    earth = bpy.context.object
    earth.name = "EvidenceOnly:EarthCameo"
    earth.data.materials.append(material("Evidence Earth", (0.15, 0.52, 0.59, 1.0), 0.96))


def add_pan() -> None:
    town.import_model(PAN, "Heritage:PanMonument", town.Point(0.0, 0.0))


def add_pad_overlay() -> None:
    route = material("Evidence Walk Route", (0.04, 0.74, 0.71, 1.0), 0.78, 2.2)
    pad = material("Evidence Flat Pad", (0.95, 0.69, 0.18, 1.0), 0.78, 1.8)
    town.curve_object("WalkLoop:ring", town.RING_ROUTE, route, True, 0.085)
    for route_id, points in town.RADIAL_ROUTES.items():
        town.curve_object(f"WalkLoop:{route_id}", points, route, False, 0.085)
    for slot in builder.CANONICAL_SLOTS:
        town.curve_object(f"FlatPad:{slot.id}", town.pad_outline(slot), pad, True, 0.09)
    for orbital in builder.ORBITAL_PADS:
        if orbital.shape == "circle":
            points = [
                town.Point(orbital.position.x + math.cos(index / 32.0 * math.tau) * orbital.width * 0.5,
                           orbital.position.y + math.sin(index / 32.0 * math.tau) * orbital.width * 0.5)
                for index in range(32)
            ]
        else:
            points = [
                town.Point(orbital.position.x - orbital.width * 0.5, orbital.position.y - orbital.depth * 0.5),
                town.Point(orbital.position.x + orbital.width * 0.5, orbital.position.y - orbital.depth * 0.5),
                town.Point(orbital.position.x + orbital.width * 0.5, orbital.position.y + orbital.depth * 0.5),
                town.Point(orbital.position.x - orbital.width * 0.5, orbital.position.y + orbital.depth * 0.5),
            ]
        town.curve_object(f"FlatPad:{orbital.id}", points, pad, True, 0.09)


def setup_scene(camera_angle: float = 0.0, overlay: bool = False) -> None:
    town.reset_scene()
    town.import_model(GLB, "Production:DomeCommonsPlate", town.Point(0.0, 0.0))
    add_pan()
    if overlay:
        add_pad_overlay()
    camera = town.setup_render_scene()
    scene = bpy.context.scene
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 800
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.070, 0.058, 0.045, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.72
    scene.view_settings.look = "AgX - Medium Low Contrast"
    distance = 46.0
    camera.location = (math.sin(camera_angle) * distance, math.cos(camera_angle) * distance, 34.0)
    town.look_at(camera, Vector((0.0, 0.0, 3.2)))
    camera.data.lens = camera.data.sensor_height / (2.0 * math.tan(math.radians(48.0) * 0.5))
    camera.data.clip_end = 180.0
    sun = bpy.data.objects.get("EvidenceSun")
    if sun:
        sun.data.energy = 2.45
        sun.data.color = (1.0, 0.88, 0.68)
    fill = bpy.data.objects.get("EvidenceFill")
    if fill:
        fill.data.energy = 2050.0
        fill.data.color = (0.72, 0.91, 0.91)
    add_earth_cameo(camera_angle)


def render(path: Path, camera_angle: float = 0.0, overlay: bool = False) -> None:
    setup_scene(camera_angle, overlay)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def annotate(path: Path, label: str) -> None:
    temporary = path.with_name(f".{path.name}")
    subprocess.run(
        [
            "magick", str(path), "-font", "/System/Library/Fonts/Helvetica.ttc",
            "-gravity", "north", "-fill", "#f7df9d", "-undercolor", "#17120dcc",
            "-pointsize", "22", "-annotate", "+0+8", f"{label} | base {BASE_SHA}", str(temporary),
        ],
        check=True,
    )
    temporary.replace(path)


def assemble() -> None:
    camera = RENDERS / "dome-commons-plate-camera.png"
    overlay = RENDERS / "dome-commons-flat-walk-overlay.png"
    angles = [RENDERS / f"dome-commons-angle-{index}.png" for index in range(1, 5)]
    turntable = RENDERS / "dome-commons-turntable.png"
    first_row = Path("/tmp/dome-commons-turntable-row-1.png")
    second_row = Path("/tmp/dome-commons-turntable-row-2.png")
    subprocess.run(["magick", str(angles[0]), str(angles[1]), "+append", str(first_row)], check=True)
    subprocess.run(["magick", str(angles[2]), str(angles[3]), "+append", str(second_row)], check=True)
    subprocess.run(["magick", str(first_row), str(second_row), "-append", str(turntable)], check=True)
    first_row.unlink(missing_ok=True)
    second_row.unlink(missing_ok=True)
    annotate(turntable, "DOME COMMONS | FOUR-ANGLE AIR-WALL AUDIT")

    baseline = ARTIFACTS / "current-references" / f"{BASE_SHA[:12]}-main/town-e7-current.png"
    ab = RENDERS / "signal-mesa-vs-dome-commons-ab.png"
    subprocess.run(["magick", str(baseline), str(camera), "+append", str(ab)], check=True)
    annotate(ab, "CURRENT E7 SIGNAL MESA / E8 DOME COMMONS SITE")

    source_resized = Path("/tmp/dome-commons-source-1280x800.png")
    subprocess.run([
        "magick", str(SOURCE_PLATE), "-resize", "1280x800", "-background", "#17120d",
        "-gravity", "center", "-extent", "1280x800", str(source_resized),
    ], check=True)
    source_ab = RENDERS / "dome-commons-source-ab.png"
    subprocess.run(["magick", str(source_resized), str(camera), "+append", str(source_ab)], check=True)
    source_resized.unlink(missing_ok=True)
    annotate(source_ab, "E8 PAINTED VOCABULARY / PRODUCTION PLATE")
    annotate(overlay, "FLAT-WALK PROOF | TEAL ROUTES / AMBER PADS")

    evidence = {
        "baseSha": BASE_SHA,
        "productionGlb": str(GLB.relative_to(ROOT)),
        "freshReference": str(CURRENT_E7.relative_to(ROOT)),
        "evidenceOnly": ["Earth cameo", "Pan Monument mount", "lights", "cameras", "route/pad overlays"],
        "renders": [str(path.relative_to(ROOT)) for path in [camera, overlay, turntable, ab, source_ab, *angles]],
    }
    (ARTIFACTS / "dome-commons-visual-evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")


def main() -> None:
    RENDERS.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    targets = {
        "camera": lambda: render(RENDERS / "dome-commons-plate-camera.png", 0.0),
        "overlay": lambda: render(RENDERS / "dome-commons-flat-walk-overlay.png", 0.0, True),
        "angle1": lambda: render(RENDERS / "dome-commons-angle-1.png", 0.0),
        "angle2": lambda: render(RENDERS / "dome-commons-angle-2.png", math.pi * 0.5),
        "angle3": lambda: render(RENDERS / "dome-commons-angle-3.png", math.pi),
        "angle4": lambda: render(RENDERS / "dome-commons-angle-4.png", math.pi * 1.5),
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
