from __future__ import annotations

from pathlib import Path
import hashlib
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
OUT = ROOT / "artifacts/dome-orbital-era-props"
RENDERS = OUT / "renders"
BASE_SHA = "00200c722be8ec618a156b775f2f35f035bc5158"
PLATE = ROOT / "assets/pilots/dome-commons-3d/dome-commons-plate.glb"
PAN = HERE / "pan_monument.glb"
MANIFEST = json.loads((HERE / "era-props.e8.json").read_text())
PROP_PATHS = {item["glb"]: HERE / item["glb"] for item in MANIFEST["props"]}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


population = load("e8_orbital_props_population", ROOT / "assets/pilots/dome-population-e8/render_dome_population.py")
population.BASE_SHA = BASE_SHA
town = population.town


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_props() -> None:
    for item in MANIFEST["props"]:
        position = item["position"]
        town.import_model(
            PROP_PATHS[item["glb"]], f'E8Prop:{item["id"]}', town.Point(position["x"], position["z"]),
            item["rotation"], item["scale"],
        )


def setup_site(include_props: bool = True) -> None:
    town.reset_scene()
    town.import_model(PLATE, "Production:DomeCommonsPlate", town.Point(0.0, 0.0))
    town.import_model(PAN, "Heritage:PanMonument", town.Point(0.0, 0.0))
    population.add_population()
    if include_props:
        add_props()


def setup_camera(angle: float, top_down: bool = False) -> bpy.types.Object:
    camera = population.setup_lighting(1280, 800)
    if top_down:
        camera.data.type = "ORTHO"
        camera.data.ortho_scale = 45.0
        camera.location = (0.0, 0.0, 50.0)
        town.look_at(camera, Vector((0.0, 0.0, 0.0)))
        return camera
    distance = 46.0
    camera.location = (math.sin(angle) * distance, math.cos(angle) * distance, 34.0)
    town.look_at(camera, Vector((0.0, 0.0, 3.2)))
    camera.data.lens = camera.data.sensor_height / (2.0 * math.tan(math.radians(48.0) * 0.5))
    camera.data.clip_end = 180.0
    population.add_earth(angle)
    return camera


def render_site(path: Path, angle: float = 0.0, include_props: bool = True) -> None:
    setup_site(include_props)
    setup_camera(angle)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def add_clearance_overlay() -> None:
    route_material = town.emission_material("E8 route overlay", (0.08, 0.82, 0.78, 1), 1.8)
    pad_material = town.emission_material("E8 pad overlay", (0.98, 0.72, 0.16, 1), 1.8)
    prop_material = town.emission_material("E8 prop clearance", (0.94, 0.24, 0.12, 1), 1.8)
    town.curve_object("WalkLoop:ring-road", town.RING_ROUTE, route_material, True, 0.10)
    for route_id, points in town.RADIAL_ROUTES.items():
        town.curve_object(f"HeroPath:{route_id}", points, route_material, False, 0.10)

    layout = json.loads((ROOT / "artifacts/dome-commons-e8/dome-commons-layout-contract.json").read_text())
    for pad in [*layout["canonicalSlots"], *layout["orbitalPads"]]:
        x, y = pad["position"]
        width, depth = pad["footprint"]
        if pad.get("shape") == "circle":
            radius = width * 0.5
            points = [town.Point(x + math.sin(index / 32 * math.tau) * radius,
                                 y + math.cos(index / 32 * math.tau) * radius) for index in range(32)]
        else:
            points = [town.Point(x - width / 2, y - depth / 2), town.Point(x + width / 2, y - depth / 2),
                      town.Point(x + width / 2, y + depth / 2), town.Point(x - width / 2, y + depth / 2)]
        town.curve_object(f'Pad:{pad["id"]}', points, pad_material, True, 0.08)

    radii = {
        "journey-flag-line.e8.glb": 2.38,
        "crater-rim-set.e8.glb": 1.35,
        "lander-legs.e8.glb": 1.347077,
    }
    for item in MANIFEST["props"]:
        x, y = item["position"]["x"], item["position"]["z"]
        radius = radii[item["glb"]] * item["scale"]
        points = [town.Point(x + math.sin(index / 32 * math.tau) * radius,
                             y + math.cos(index / 32 * math.tau) * radius) for index in range(32)]
        town.curve_object(f'Clearance:{item["id"]}', points, prop_material, True, 0.11)


def render_clearance(path: Path) -> None:
    setup_site(True)
    setup_camera(0.0, True)
    add_clearance_overlay()
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def audit_floor(size: float = 14.0) -> None:
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0.0, 0.0, -0.01))
    bpy.context.object.name = "EvidenceOnly:AuditFloor"
    bpy.context.object.data.materials.append(population.evidence_material("E8 audit floor", (0.16, 0.14, 0.12, 1.0)))


def render_pack(path: Path) -> None:
    town.reset_scene()
    placements = (
        ("journey-flag-line.e8.glb", town.Point(0.0, 1.25), 0.0),
        ("crater-rim-set.e8.glb", town.Point(-2.4, -1.15), 0.3),
        ("lander-legs.e8.glb", town.Point(2.35, -1.2), -0.3),
    )
    for stem, position, rotation in placements:
        town.import_model(PROP_PATHS[stem], f"Pack:{stem}", position, rotation, 1.25)
    audit_floor()
    camera = population.setup_lighting(1280, 800)
    camera.location = (9.5, -11.5, 8.0)
    town.look_at(camera, Vector((0.0, 0.0, 1.0)))
    camera.data.lens = 52.0
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def annotate(path: Path, label: str, point_size: int = 22) -> None:
    temporary = path.with_name(f".{path.name}")
    subprocess.run([
        "magick", str(path), "-font", "/System/Library/Fonts/Helvetica.ttc", "-gravity", "north",
        "-fill", "#f7df9d", "-undercolor", "#17120dcc", "-pointsize", str(point_size),
        "-annotate", "+0+8", f"{label} | base {BASE_SHA}", str(temporary),
    ], check=True)
    temporary.replace(path)


def assemble() -> None:
    baseline = RENDERS / "dome-e8-before-props.png"
    candidate = RENDERS / "dome-e8-with-orbital-props.png"
    ab = RENDERS / "dome-e8-orbital-props-ab.png"
    subprocess.run(["magick", str(baseline), str(candidate), "+append", str(ab)], check=True)
    annotate(ab, "E8 DOME COMMONS | BEFORE / ORBITAL ACCESSORY PASS")

    angles = [RENDERS / f"dome-e8-props-angle-{index}.png" for index in range(1, 5)]
    subprocess.run(["magick", str(angles[0]), str(angles[1]), "+append", "/tmp/e8-props-top.png"], check=True)
    subprocess.run(["magick", str(angles[2]), str(angles[3]), "+append", "/tmp/e8-props-bottom.png"], check=True)
    turntable = RENDERS / "dome-e8-orbital-props-turntable.png"
    subprocess.run(["magick", "/tmp/e8-props-top.png", "/tmp/e8-props-bottom.png", "-append", str(turntable)], check=True)
    annotate(turntable, "E8 ORBITAL PROPS | FOUR-ANGLE SITE AUDIT", 26)

    clearance = RENDERS / "dome-e8-orbital-props-clearance.png"
    pack = RENDERS / "e8-orbital-props-pack.png"
    annotate(clearance, "E8 CLEARANCE | CYAN PATHS / GOLD PADS / RED PROP ENVELOPES")
    annotate(pack, "E8 ORBITAL PACK | JOURNEY FLAGS / CRATER SURVEY / LANDER LEGS")

    fresh_board = population.render_fresh_references()
    fresh = RENDERS / "fresh-main-reference-and-e8.png"
    subprocess.run(["magick", str(fresh_board), str(baseline), "-gravity", "center", "+append", str(fresh)], check=True)
    annotate(fresh, "FRESH CURRENT-FILE REFERENCES / E8 WORKING BASE", 26)

    tracked = [PLATE, PAN, *population.MODELS.values(), *PROP_PATHS.values(), HERE / "era-props-e8-atlas.png"]
    (OUT / "e8-orbital-props-visual-evidence.json").write_text(json.dumps({
        "baseSha": BASE_SHA,
        "rule": "all boards rendered from current GLBs on the freshly pulled base; no prior PNG is an input",
        "productionAssets": {str(path.relative_to(ROOT)): sha256(path) for path in tracked},
        "evidenceOnly": ["Earth sky cameo", "lights", "cameras", "audit floor", "clearance curves"],
        "renders": [str(path.relative_to(ROOT)) for path in [ab, turntable, clearance, pack, fresh, baseline, candidate, *angles]],
    }, indent=2) + "\n")
    Path("/tmp/e8-props-top.png").unlink(missing_ok=True)
    Path("/tmp/e8-props-bottom.png").unlink(missing_ok=True)


def main() -> None:
    RENDERS.mkdir(parents=True, exist_ok=True)
    targets = {
        "before": lambda: render_site(RENDERS / "dome-e8-before-props.png", include_props=False),
        "after": lambda: render_site(RENDERS / "dome-e8-with-orbital-props.png", include_props=True),
        **{f"angle{index}": (lambda index=index: render_site(
            RENDERS / f"dome-e8-props-angle-{index}.png", (index - 1) * math.pi * 0.5, True,
        )) for index in range(1, 5)},
        "clearance": lambda: render_clearance(RENDERS / "dome-e8-orbital-props-clearance.png"),
        "pack": lambda: render_pack(RENDERS / "e8-orbital-props-pack.png"),
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
