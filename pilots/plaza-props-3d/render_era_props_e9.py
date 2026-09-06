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
OUT = ROOT / "artifacts/basin-redfields-era-props"
RENDERS = OUT / "renders"
BASE_SHA = "51319bf7ebceaaad9df4fdc4da0dcf96033b91e1"
PLATE = ROOT / "assets/pilots/basin-rim-3d/basin-rim-plate.glb"
PAN = HERE / "pan_monument.glb"
MANIFEST_PATH = HERE / "era-props.e9.json"
MANIFEST = json.loads(MANIFEST_PATH.read_text())
STATIC_PATHS = {item["glb"]: HERE / item["glb"] for item in MANIFEST["props"]}
ALL_STEMS = (
    "canal-segment-dry.e9", "canal-segment-wet.e9", "canal-segment-flowing.e9",
    "ice-blocks.e9", "survey-cairn.e9",
    "ark-scaffold-stage-1.e9", "ark-scaffold-stage-2.e9", "ark-scaffold-stage-3.e9",
)
ALL_PATHS = {stem: HERE / f"{stem}.glb" for stem in ALL_STEMS}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


population = load("e9_redfields_props_population", ROOT / "assets/pilots/basin-population-e9/render_basin_population.py")
population.BASE_SHA = BASE_SHA
population.fresh.BASE_SHA = BASE_SHA
town = population.town


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_props() -> None:
    for item in MANIFEST["props"]:
        position = item["position"]
        town.import_model(
            STATIC_PATHS[item["glb"]], f'E9Prop:{item["id"]}',
            town.Point(position["x"], position["z"]), item["rotation"], item["scale"],
        )


def setup_site(include_props: bool = True) -> None:
    town.reset_scene()
    town.import_model(PLATE, "Production:BasinRimPlate", town.Point(0.0, 0.0))
    town.import_model(PAN, "Heritage:PanMonument", town.Point(0.0, 0.0))
    population.add_population()
    if include_props:
        add_props()


def setup_camera(angle: float, top_down: bool = False) -> bpy.types.Object:
    camera = population.setup_lighting(1280, 800)
    if top_down:
        camera.data.type = "ORTHO"
        camera.data.ortho_scale = 52.0
        camera.location = (0.0, 0.0, 56.0)
        town.look_at(camera, Vector((0.0, 0.0, 0.0)))
        return camera
    distance = 42.0
    camera.location = (math.sin(angle) * distance, math.cos(angle) * distance, 33.0)
    town.look_at(camera, Vector((0.0, 0.0, 0.6)))
    camera.data.lens = camera.data.sensor_height / (2.0 * math.tan(math.radians(52.0) * 0.5))
    camera.data.clip_end = 180.0
    return camera


def render_site(path: Path, angle: float = 0.0, include_props: bool = True) -> None:
    setup_site(include_props)
    setup_camera(angle)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def add_clearance_overlay() -> None:
    route_material = town.emission_material("E9 route overlay", (0.08, 0.82, 0.78, 1), 1.8)
    pad_material = town.emission_material("E9 pad overlay", (0.98, 0.72, 0.16, 1), 1.8)
    prop_material = town.emission_material("E9 static prop clearance", (0.94, 0.24, 0.12, 1), 1.8)
    town.curve_object("WalkLoop:ring-road", town.RING_ROUTE, route_material, True, 0.10)
    for route_id, points in town.RADIAL_ROUTES.items():
        town.curve_object(f"HeroPath:{route_id}", points, route_material, False, 0.10)

    layout = json.loads((ROOT / "artifacts/basin-rim-e9/basin-rim-layout-contract.json").read_text())
    for pad in [*layout["canonicalSlots"], *layout["basinPads"]]:
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
        "ice-blocks.e9.glb": 1.313,
        "survey-cairn.e9.glb": 0.60,
        "ark-scaffold-stage-1.e9.glb": 1.21,
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


def audit_floor() -> None:
    bpy.ops.mesh.primitive_plane_add(size=24.0, location=(0.0, 0.0, -0.01))
    bpy.context.object.name = "EvidenceOnly:AuditFloor"
    bpy.context.object.data.materials.append(population.evidence_material("E9 audit floor", (0.22, 0.075, 0.035, 1.0)))


def render_pack(path: Path) -> None:
    town.reset_scene()
    placements = (
        ("canal-segment-dry.e9", town.Point(-5.4, 2.8), 0.0, 0.92),
        ("canal-segment-wet.e9", town.Point(0.0, 2.8), 0.0, 0.92),
        ("canal-segment-flowing.e9", town.Point(5.4, 2.8), 0.0, 0.92),
        ("ice-blocks.e9", town.Point(-5.3, -1.5), -0.2, 1.0),
        ("survey-cairn.e9", town.Point(-2.5, -1.5), 0.2, 1.1),
        ("ark-scaffold-stage-1.e9", town.Point(0.0, -1.6), 0.0, 1.0),
        ("ark-scaffold-stage-2.e9", town.Point(3.2, -1.6), 0.0, 1.0),
        ("ark-scaffold-stage-3.e9", town.Point(6.9, -1.6), 0.0, 0.92),
    )
    for stem, position, rotation, scale in placements:
        town.import_model(ALL_PATHS[stem], f"Pack:{stem}", position, rotation, scale)
    audit_floor()
    camera = population.setup_lighting(1440, 900)
    camera.location = (14.5, -18.0, 13.5)
    town.look_at(camera, Vector((0.7, 0.3, 1.1)))
    camera.data.lens = 55.0
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


def render_fresh_references() -> Path:
    out = OUT / "current-references" / f"{BASE_SHA[:12]}-main"
    out.mkdir(parents=True, exist_ok=True)
    fresh = population.fresh
    fresh.render_e1(out / "town-e1-current.png")
    fresh.render_e4(out / "town-e4-current.png")
    fresh.render_e5(out / "town-e5-current-underwater.png")
    fresh.render_mesa(out / "town-e6-current.png", 6)
    fresh.render_mesa(out / "town-e7-current.png", 7)
    population.render_e8_reference(out / "town-e8-current.png")
    sources = [
        out / "town-e1-current.png", out / "town-e4-current.png", out / "town-e5-current-underwater.png",
        out / "town-e6-current.png", out / "town-e7-current.png", out / "town-e8-current.png",
    ]
    row_a, row_b = Path("/tmp/e9-props-reference-a.png"), Path("/tmp/e9-props-reference-b.png")
    subprocess.run(["magick", *map(str, sources[:3]), "+append", str(row_a)], check=True)
    subprocess.run(["magick", *map(str, sources[3:]), "+append", str(row_b)], check=True)
    board = out / "town-e1-e8-current.png"
    subprocess.run(["magick", str(row_a), str(row_b), "-append", str(board)], check=True)
    annotate(board, "FRESH CURRENT-FILE REFERENCE | E1 / E4 / E5 / E6 / E7 / E8", 26)
    row_a.unlink(missing_ok=True)
    row_b.unlink(missing_ok=True)
    (out / "reference-contract.json").write_text(json.dumps({
        "baseSha": BASE_SHA,
        "rule": "fresh render from current main GLBs; no prior PNG is an input",
        "order": ["E1 square", "E4 motor boulevard", "E5 submerged square", "E6 Atomic Mesa", "E7 Signal Mesa", "E8 Dome Commons"],
        "renders": [str(path.relative_to(ROOT)) for path in [*sources, board]],
    }, indent=2) + "\n")
    return board


def assemble() -> None:
    baseline = RENDERS / "basin-e9-before-props.png"
    candidate = RENDERS / "basin-e9-with-redfields-props.png"
    ab = RENDERS / "basin-e9-redfields-props-ab.png"
    subprocess.run(["magick", str(baseline), str(candidate), "+append", str(ab)], check=True)
    annotate(ab, "E9 BASIN RIM | BEFORE / REDFIELDS ACCESSORY PASS")

    angles = [RENDERS / f"basin-e9-props-angle-{index}.png" for index in range(1, 5)]
    top, bottom = Path("/tmp/e9-props-top.png"), Path("/tmp/e9-props-bottom.png")
    subprocess.run(["magick", str(angles[0]), str(angles[1]), "+append", str(top)], check=True)
    subprocess.run(["magick", str(angles[2]), str(angles[3]), "+append", str(bottom)], check=True)
    turntable = RENDERS / "basin-e9-redfields-props-turntable.png"
    subprocess.run(["magick", str(top), str(bottom), "-append", str(turntable)], check=True)
    annotate(turntable, "E9 REDFIELDS PROPS | FOUR-ANGLE SITE AUDIT", 26)

    clearance = RENDERS / "basin-e9-redfields-props-clearance.png"
    pack = RENDERS / "e9-redfields-props-pack.png"
    annotate(clearance, "E9 CLEARANCE | CYAN PATHS / GOLD PADS / RED STATIC ENVELOPES")
    annotate(pack, "E9 REDFIELDS PACK | CANAL STATES / ICE + SURVEY / ARK STAGES")

    fresh_board = render_fresh_references()
    fresh = RENDERS / "fresh-main-reference-and-e9.png"
    subprocess.run(["magick", str(fresh_board), str(baseline), "-gravity", "center", "+append", str(fresh)], check=True)
    annotate(fresh, "FRESH CURRENT-FILE REFERENCES / E9 WORKING BASE", 26)

    tracked = [PLATE, PAN, *population.MODELS.values(), *ALL_PATHS.values(), HERE / "era-props-e9-atlas.png", MANIFEST_PATH]
    (OUT / "e9-redfields-props-visual-evidence.json").write_text(json.dumps({
        "baseSha": BASE_SHA,
        "rule": "all boards rendered from current GLBs on the freshly pulled base; no prior PNG is an input",
        "stateBoundary": "canal dry/wet/flowing and Ark stages 2/3 are banked siblings; only static props and Ark stage 1 mount without progression state",
        "productionAssets": {str(path.relative_to(ROOT)): sha256(path) for path in tracked},
        "evidenceOnly": ["lights", "cameras", "audit floor", "clearance curves", "banked progression sibling pack layout"],
        "renders": [str(path.relative_to(ROOT)) for path in [ab, turntable, clearance, pack, fresh, baseline, candidate, *angles]],
    }, indent=2) + "\n")
    top.unlink(missing_ok=True)
    bottom.unlink(missing_ok=True)


def main() -> None:
    RENDERS.mkdir(parents=True, exist_ok=True)
    targets = {
        "before": lambda: render_site(RENDERS / "basin-e9-before-props.png", include_props=False),
        "after": lambda: render_site(RENDERS / "basin-e9-with-redfields-props.png", include_props=True),
        **{f"angle{index}": (lambda index=index: render_site(
            RENDERS / f"basin-e9-props-angle-{index}.png", (index - 1) * math.pi * 0.5, True,
        )) for index in range(1, 5)},
        "clearance": lambda: render_clearance(RENDERS / "basin-e9-redfields-props-clearance.png"),
        "pack": lambda: render_pack(RENDERS / "e9-redfields-props-pack.png"),
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
