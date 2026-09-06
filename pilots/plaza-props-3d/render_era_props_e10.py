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
OUT = ROOT / "artifacts/ark-era-props-e10"
RENDERS = OUT / "renders"
BASE_SHA = "d7e429d16e24b88e4e65114752b3b12a96280e3b"
PLATE = ROOT / "assets/pilots/ark-plaza-e10-3d/ark-plaza-e10.glb"
PAN = HERE / "pan_monument.glb"
MANIFEST_PATH = HERE / "era-props.e10.json"
MANIFEST = json.loads(MANIFEST_PATH.read_text())
STATIC_PATHS = {item["glb"]: HERE / item["glb"] for item in MANIFEST["props"]}
ALL_STEMS = (
    "bridge-school.e10", "charter-press.e10", "preserve-rack.e10",
    "engine-glow-idle.e10", "engine-glow-cruise.e10", "engine-glow-ward.e10",
)
ALL_PATHS = {stem: HERE / f"{stem}.glb" for stem in ALL_STEMS}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ark = load("e10_ark_props_plaza", ROOT / "assets/pilots/ark-plaza-e10-3d/render_ark_plaza.py")
ark.BASE_SHA = BASE_SHA
town = ark.town
population = load("e10_ark_props_history", ROOT / "assets/pilots/basin-population-e9/render_basin_population.py")
population.BASE_SHA = BASE_SHA
population.fresh.BASE_SHA = BASE_SHA
hall = load("e10_ark_props_hall", ROOT / "assets/pilots/ark-long-table-hall-e10-3d/render_ark_long_table_hall.py")
hall.BASE_SHA = BASE_SHA


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_props() -> None:
    for item in MANIFEST["props"]:
        position = item["position"]
        town.import_model(
            STATIC_PATHS[item["glb"]], f'E10Prop:{item["id"]}',
            town.Point(position["x"], position["z"]), item["rotation"], item["scale"],
        )


def setup_site(angle: float = math.pi, include_props: bool = True, overlay: bool = False) -> None:
    ark.setup(angle, overlay)
    if include_props:
        add_props()


def render_site(path: Path, angle: float = math.pi, include_props: bool = True) -> None:
    setup_site(angle, include_props)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def add_clearance_envelopes() -> None:
    material = ark.material("EvidenceOnly:E10PropEnvelope", (0.94, 0.24, 0.12, 1.0), 2.2)
    radii = {
        "bridge-school.e10.glb": 1.675,
        "charter-press.e10.glb": 1.783,
        "preserve-rack.e10.glb": 1.65,
    }
    for item in MANIFEST["props"]:
        x, y = item["position"]["x"], item["position"]["z"]
        radius = radii[item["glb"]] * item["scale"]
        points = [town.Point(x + math.sin(index / 32 * math.tau) * radius,
                             y + math.cos(index / 32 * math.tau) * radius) for index in range(32)]
        town.curve_object(f'Clearance:{item["id"]}', points, material, True, 0.11)


def render_clearance(path: Path) -> None:
    setup_site(math.pi, True, True)
    add_clearance_envelopes()
    camera = bpy.context.scene.camera
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 52.0
    camera.location = (0.0, 0.0, 55.0)
    town.look_at(camera, Vector((0.0, 0.0, 0.0)))
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def audit_floor() -> None:
    bpy.ops.mesh.primitive_plane_add(size=20.0, location=(0.0, 0.0, -0.01))
    floor = bpy.context.object
    floor.name = "EvidenceOnly:AuditFloor"
    floor.data.materials.append(ark.material("EvidenceOnly:PackFloor", (0.045, 0.055, 0.065, 1.0)))


def render_pack(path: Path) -> None:
    town.reset_scene()
    placements = (
        ("bridge-school.e10", town.Point(-4.4, 1.8), 0.0, 1.0),
        ("charter-press.e10", town.Point(0.0, 1.8), 0.0, 1.0),
        ("preserve-rack.e10", town.Point(4.4, 1.8), 0.0, 1.0),
        ("engine-glow-idle.e10", town.Point(-5.0, -2.0), 0.0, 0.95),
        ("engine-glow-cruise.e10", town.Point(0.0, -2.0), 0.0, 0.95),
        ("engine-glow-ward.e10", town.Point(5.0, -2.0), 0.0, 0.95),
    )
    for stem, position, rotation, scale in placements:
        town.import_model(ALL_PATHS[stem], f"Pack:{stem}", position, rotation, scale)
    audit_floor()
    camera = town.setup_render_scene()
    scene = bpy.context.scene
    scene.render.resolution_x = 1440
    scene.render.resolution_y = 900
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.018, 0.028, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.52
    camera.location = (14.0, -18.5, 12.0)
    town.look_at(camera, Vector((0.0, 0.0, 1.0)))
    camera.data.lens = 55.0
    sun = bpy.data.objects.get("EvidenceSun")
    if sun:
        sun.data.energy = 2.8
        sun.data.color = (1.0, 0.70, 0.38)
    fill = bpy.data.objects.get("EvidenceFill")
    if fill:
        fill.data.energy = 2200.0
        fill.data.color = (0.27, 0.80, 0.82)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def annotate(path: Path, label: str, point_size: int = 22) -> None:
    temporary = path.with_name(f".{path.name}")
    subprocess.run([
        "magick", str(path), "-font", "/System/Library/Fonts/Helvetica.ttc", "-gravity", "north",
        "-fill", "#f7df9d", "-undercolor", "#10151ddd", "-pointsize", str(point_size),
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
    population.render_ensemble(out / "town-e9-current.png", 0.0)
    render_site(out / "town-e10-current.png", math.pi, False)
    hall.render(out / "town-e10-long-table-current.png", (0.0, -24.0, 9.0), (0.0, 1.0, 2.6), 46.0)
    paths = [
        out / "town-e1-current.png", out / "town-e4-current.png", out / "town-e5-current-underwater.png",
        out / "town-e6-current.png", out / "town-e7-current.png", out / "town-e8-current.png",
        out / "town-e9-current.png", out / "town-e10-current.png", out / "town-e10-long-table-current.png",
    ]
    rows = [Path(f"/tmp/e10-props-reference-{index}.png") for index in range(3)]
    for index, row in enumerate(rows):
        subprocess.run(["magick", *map(str, paths[index * 3:(index + 1) * 3]), "+append", str(row)], check=True)
    board = out / "town-e1-e10-current.png"
    subprocess.run(["magick", *map(str, rows), "-append", str(board)], check=True)
    annotate(board, "FRESH CURRENT-FILE REFERENCE | E1 / E4 / E5 / E6 / E7 / E8 / E9 / E10", 26)
    for row in rows:
        row.unlink(missing_ok=True)
    (out / "reference-contract.json").write_text(json.dumps({
        "baseSha": BASE_SHA,
        "rule": "fresh render from current main GLBs; no prior PNG is an input",
        "order": ["E1 square", "E4 motor boulevard", "E5 submerged square", "E6 Atomic Mesa", "E7 Signal Mesa",
                  "E8 Dome Commons", "E9 Basin Rim", "E10 Ark Plaza", "E10 Long Table Hall"],
        "renders": [str(path.relative_to(ROOT)) for path in [*paths, board]],
    }, indent=2) + "\n")
    return board


def assemble() -> None:
    baseline = RENDERS / "ark-e10-before-props.png"
    candidate = RENDERS / "ark-e10-with-functional-props.png"
    ab = RENDERS / "ark-e10-functional-props-ab.png"
    subprocess.run(["magick", str(baseline), str(candidate), "+append", str(ab)], check=True)
    annotate(ab, "E10 ARK PLAZA | BEFORE / FUNCTIONAL ACCESSORY PASS")

    angles = [RENDERS / f"ark-e10-props-angle-{index}.png" for index in range(1, 5)]
    top, bottom = Path("/tmp/e10-props-top.png"), Path("/tmp/e10-props-bottom.png")
    subprocess.run(["magick", str(angles[0]), str(angles[1]), "+append", str(top)], check=True)
    subprocess.run(["magick", str(angles[2]), str(angles[3]), "+append", str(bottom)], check=True)
    turntable = RENDERS / "ark-e10-functional-props-turntable.png"
    subprocess.run(["magick", str(top), str(bottom), "-append", str(turntable)], check=True)
    annotate(turntable, "E10 ARK PROPS | FOUR-ANGLE SITE AUDIT", 26)

    clearance = RENDERS / "ark-e10-functional-props-clearance.png"
    pack = RENDERS / "e10-ark-functional-props-pack.png"
    annotate(clearance, "E10 CLEARANCE | TEAL PATHS / AMBER PADS / RED PROP ENVELOPES")
    annotate(pack, "E10 ARK PACK | BRIDGE SCHOOL / CHARTER PRESS / PRESERVE RACK / ENGINE STATES")

    fresh_board = render_fresh_references()
    fresh = RENDERS / "fresh-main-reference-and-e10.png"
    subprocess.run(["magick", str(fresh_board), str(baseline), "-gravity", "center", "+append", str(fresh)], check=True)
    annotate(fresh, "FRESH CURRENT-FILE REFERENCES / E10 WORKING BASE", 26)

    tracked = [PLATE, PAN, *ALL_PATHS.values(), HERE / "era-props-e10-atlas.png", MANIFEST_PATH]
    (OUT / "e10-ark-props-visual-evidence.json").write_text(json.dumps({
        "baseSha": BASE_SHA,
        "rule": "all boards rendered from current GLBs on the freshly pulled base; no prior PNG is an input",
        "stateBoundary": "engine idle/cruise/ward are banked siblings; ordinary era-prop manifest has no engine-state selector",
        "productionAssets": {str(path.relative_to(ROOT)): sha256(path) for path in tracked},
        "evidenceOnly": ["starfield", "lights", "cameras", "audit floor", "clearance curves", "banked engine-state pack layout"],
        "renders": [str(path.relative_to(ROOT)) for path in [ab, turntable, clearance, pack, fresh, baseline, candidate, *angles]],
    }, indent=2) + "\n")
    top.unlink(missing_ok=True)
    bottom.unlink(missing_ok=True)


def main() -> None:
    RENDERS.mkdir(parents=True, exist_ok=True)
    targets = {
        "before": lambda: render_site(RENDERS / "ark-e10-before-props.png", math.pi, False),
        "after": lambda: render_site(RENDERS / "ark-e10-with-functional-props.png", math.pi, True),
        **{f"angle{index}": (lambda index=index: render_site(
            RENDERS / f"ark-e10-props-angle-{index}.png", math.pi + (index - 1) * math.pi * 0.5, True,
        )) for index in range(1, 5)},
        "clearance": lambda: render_clearance(RENDERS / "ark-e10-functional-props-clearance.png"),
        "pack": lambda: render_pack(RENDERS / "e10-ark-functional-props-pack.png"),
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
