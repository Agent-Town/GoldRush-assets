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
BASE_SHA = "d944dc7ebd690141d52f363d38aa6dc1a83f4343"
OUT = ROOT / "artifacts/ark-plaza-e10/current-references" / f"{BASE_SHA[:12]}-main"
CURRENT_PLATE = ROOT / "assets/pilots/town-plate-3d/town-plate.glb"
MESA_PLATE = ROOT / "assets/pilots/mesa-town-3d/mesa-town-plate.glb"
DOME_PLATE = ROOT / "assets/pilots/dome-commons-3d/dome-commons-plate.glb"
PAN = ROOT / "assets/pilots/plaza-props-3d/pan_monument.glb"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


e4 = load_module("ark_reference_e4", ROOT / "assets/pilots/tavern-3d/render_wave9_e4_wide.py")
e5 = load_module("ark_reference_e5", ROOT / "assets/pilots/tavern-3d/render_wave10_e5_harbor.py")
town = e4.town

E6_MODELS = {
    "atomic_diner": ROOT / "assets/pilots/tavern-3d/tavern.e6.glb",
    "reactor_dome": ROOT / "assets/pilots/reactor-dome-3d/reactor-dome.glb",
    "isotope_kitchen": ROOT / "assets/pilots/isotope-kitchen-3d/isotope-kitchen.glb",
    "appliance_pen": ROOT / "assets/pilots/appliance-pen-3d/appliance-pen.glb",
    "decay_clock": ROOT / "assets/pilots/decay-clock-3d/decay-clock.glb",
    "catalog_warehouse": ROOT / "assets/pilots/catalog-warehouse-3d/catalog-warehouse.glb",
    "sunline_mount": ROOT / "assets/pilots/run3d/turret.e6.glb",
    "glow_fence": ROOT / "assets/pilots/run3d/palisade.e6.glb",
    "isotope_institute": ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.e6.glb",
}

E7_MODELS = {
    "net_cafe": ROOT / "assets/pilots/tavern-3d/tavern.e7.glb",
    "exchange": ROOT / "assets/pilots/exchange-3d/exchange.glb",
    "relay_tower": ROOT / "assets/pilots/relay-tower-3d/relay-tower.glb",
    "playbook_library": ROOT / "assets/pilots/playbook-library-3d/playbook-library.glb",
    "drone_coop": ROOT / "assets/pilots/drone-coop-3d/drone-coop.glb",
    "signal_refinery": ROOT / "assets/pilots/signal-refinery-3d/signal-refinery.glb",
    "beam_relay": ROOT / "assets/pilots/run3d/turret.e7.glb",
    "signal_works": ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.e7.glb",
    "tape_post": ROOT / "assets/pilots/catalog-warehouse-3d/catalog-warehouse.e7.glb",
}


def slot(identifier: str):
    return next(item for item in [*town.SLOTS, town.DYNAMO_SLOT] if item.id == identifier)


def add_pan() -> None:
    town.import_model(PAN, "Heritage:PanMonument", town.Point(0.0, 0.0))


def add_e6() -> None:
    placements = {
        "atomic_diner": "tavern", "isotope_kitchen": "general_store",
        "isotope_institute": "schoolhouse", "decay_clock": "claim_office", "appliance_pen": "assay_office",
    }
    for key, slot_id in placements.items():
        item = slot(slot_id)
        town.import_model(E6_MODELS[key], f"Current:E6:{key}", item.position, town.slot_angle(item))
    dome = town.import_model(E6_MODELS["reactor_dome"], "Current:E6:reactor_dome", town.Point(7.0, -16.7))
    dome.location.z = 1.18
    warehouse = town.import_model(E6_MODELS["catalog_warehouse"], "Current:E6:catalog_warehouse", town.Point(-7.4, -16.6), math.pi)
    warehouse.location.z = 1.18
    town.import_model(E6_MODELS["sunline_mount"], "Current:E6:sunline_mount", town.Point(12.0, 7.0), -0.25, 1.20)
    for index, (x, y, rotation) in enumerate(((-12.0, 0.8, 0.0), (12.0, 0.8, 0.0), (0.0, 12.8, 1.57)), 1):
        town.import_model(E6_MODELS["glow_fence"], f"Current:E6:glow_fence_{index}", town.Point(x, y), rotation)


def add_e7() -> None:
    paths = {**E6_MODELS, **E7_MODELS}
    placements = {
        "net_cafe": "tavern", "isotope_kitchen": "general_store", "signal_works": "schoolhouse",
        "decay_clock": "claim_office", "appliance_pen": "assay_office",
    }
    for key, slot_id in placements.items():
        item = slot(slot_id)
        town.import_model(paths[key], f"Current:E7:{key}", item.position, town.slot_angle(item))
    dome = town.import_model(E6_MODELS["reactor_dome"], "Current:E7:reactor_dome", town.Point(7.0, -16.7))
    dome.location.z = 1.18
    tape = town.import_model(E7_MODELS["tape_post"], "Current:E7:tape_post", town.Point(-7.4, -16.6), math.pi)
    tape.location.z = 1.18
    town.import_model(E7_MODELS["beam_relay"], "Current:E7:beam_relay", town.Point(12.0, 7.0), -0.25, 1.20)
    for index, (x, y, rotation) in enumerate(((-12.0, 0.8, 0.0), (12.0, 0.8, 0.0), (0.0, 12.8, 1.57)), 1):
        town.import_model(E6_MODELS["glow_fence"], f"Current:E7:glow_fence_{index}", town.Point(x, y), rotation)
    town.import_model(E7_MODELS["exchange"], "Current:E7:exchange", town.Point(-7.55, 9.40), 0.06)
    town.import_model(E7_MODELS["relay_tower"], "Current:E7:relay_tower", town.Point(7.55, 9.15), -0.08)
    town.import_model(E7_MODELS["playbook_library"], "Current:E7:playbook_library", town.Point(-14.2, -6.4), 0.12)
    town.import_model(E7_MODELS["drone_coop"], "Current:E7:drone_coop", town.Point(14.2, -6.0), -0.10)
    town.import_model(E7_MODELS["signal_refinery"], "Current:E7:signal_refinery", town.Point(0.0, 16.2), math.pi)


def setup_camera(target_z: float = 1.18) -> None:
    town.setup_render_scene()
    camera = bpy.context.scene.camera
    camera.location = (0.0, 25.5, 37.0)
    town.look_at(camera, Vector((0.0, 0.5, target_z)))
    if camera.data.type == "ORTHO":
        camera.data.ortho_scale = max(camera.data.ortho_scale, 52.0)


def render_e1(path: Path) -> None:
    town.reset_scene()
    town.import_model(CURRENT_PLATE, "Current:E1:plate", town.Point(0.0, 0.0))
    town.add_render_models()
    town.setup_render_scene()
    town.render(path)


def render_e4(path: Path) -> None:
    town.reset_scene()
    town.import_model(CURRENT_PLATE, "Current:E4:plate", town.Point(0.0, 0.0))
    e4.add_town_context(e4.E4_MODELS)
    town.setup_render_scene()
    camera = bpy.context.scene.camera
    camera.location = (0.0, 24.5, 34.5)
    town.look_at(camera, Vector((0.0, -1.5, 0.45)))
    town.render(path)


def render_e5(path: Path) -> None:
    e5.render_town(e5.E5_MODELS, 5, path, overview=True, underwater=True)


def render_mesa(path: Path, era: int) -> None:
    town.reset_scene()
    town.import_model(MESA_PLATE, f"Current:E{era}:mesa", town.Point(0.0, 0.0))
    add_pan()
    (add_e6 if era == 6 else add_e7)()
    setup_camera()
    town.render(path)


def render_e8(path: Path) -> None:
    town.reset_scene()
    town.import_model(DOME_PLATE, "Current:E8:dome-commons", town.Point(0.0, 0.0))
    add_pan()
    setup_camera(2.0)
    scene = bpy.context.scene
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.07, 0.06, 0.045, 1.0)
    town.render(path)


def annotate(path: Path, label: str) -> None:
    temporary = path.with_name(f".{path.name}")
    subprocess.run([
        "magick", str(path), "-font", "/System/Library/Fonts/Helvetica.ttc", "-gravity", "north",
        "-fill", "#f7df9d", "-undercolor", "#17120dcc", "-pointsize", "22",
        "-annotate", "+0+8", f"{label} | base {BASE_SHA}", str(temporary),
    ], check=True)
    temporary.replace(path)


def assemble() -> None:
    paths = [OUT / f"town-e{era}-current.png" for era in (1, 4, 5, 6, 7, 8)]
    top = OUT / ".top.png"
    bottom = OUT / ".bottom.png"
    board = OUT / "town-e1-e8-current.png"
    subprocess.run(["magick", *map(str, paths[:3]), "+append", str(top)], check=True)
    subprocess.run(["magick", *map(str, paths[3:]), "+append", str(bottom)], check=True)
    subprocess.run(["magick", str(top), str(bottom), "-append", str(board)], check=True)
    top.unlink(missing_ok=True)
    bottom.unlink(missing_ok=True)
    annotate(board, "FRESH CURRENT-FILE REFERENCES | E1 / E4 / E5 / E6 / E7 / E8")
    tracked = [
        CURRENT_PLATE, MESA_PLATE, DOME_PLATE, PAN, *e4.E4_MODELS.values(), *e5.E5_MODELS.values(),
        *E6_MODELS.values(), *E7_MODELS.values(),
    ]
    tracked = list(dict.fromkeys(tracked))
    contract = {
        "baseSha": BASE_SHA,
        "rule": "fresh render from current tracked GLBs; no previous evidence PNG is an input",
        "order": ["E1 square", "E4 motor boulevard", "E5 submerged square", "E6 Atomic Mesa", "E7 Signal Mesa", "E8 Dome Commons"],
        "assetSha256": {str(path.relative_to(ROOT)): sha256(path) for path in tracked},
        "renders": [str(path.relative_to(ROOT)) for path in [*paths, board]],
    }
    (OUT / "reference-contract.json").write_text(json.dumps(contract, indent=2) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    targets = {
        "e1": (render_e1, OUT / "town-e1-current.png"),
        "e4": (render_e4, OUT / "town-e4-current.png"),
        "e5": (render_e5, OUT / "town-e5-current.png"),
        "e6": (lambda path: render_mesa(path, 6), OUT / "town-e6-current.png"),
        "e7": (lambda path: render_mesa(path, 7), OUT / "town-e7-current.png"),
        "e8": (render_e8, OUT / "town-e8-current.png"),
    }
    if "--" in sys.argv:
        target = sys.argv[sys.argv.index("--") + 1]
        if target == "assemble":
            assemble()
        else:
            function, output = targets[target]
            function(output)
        return
    for target in targets:
        subprocess.run([bpy.app.binary_path, "--background", "--python", str(Path(__file__).resolve()), "--", target], check=True)
    assemble()


if __name__ == "__main__":
    main()
