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
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
# Reference evidence is intentionally pinned to the reviewed, fully merged Mesa
# base. Deriving this from HEAD would silently relabel the board after the E8
# wave is committed, even though its source files have not changed.
BASE_SHA = "2736e176d69226d40603889ee3e1aa07db623784"
OUT = ROOT / "artifacts/dome-commons-e8/current-references" / f"{BASE_SHA[:12]}-main"
PINNED_REFERENCE_CONTRACT = OUT / "reference-contract.json"
CURRENT_PLATE = ROOT / "assets/pilots/town-plate-3d/town-plate.glb"
MESA_PLATE = ROOT / "assets/pilots/mesa-town-3d/mesa-town-plate.glb"
PAN = ROOT / "assets/pilots/plaza-props-3d/pan_monument.glb"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_pinned_reference_assets() -> None:
    if not PINNED_REFERENCE_CONTRACT.is_file():
        raise RuntimeError(f"Missing pinned reference manifest: {PINNED_REFERENCE_CONTRACT}")
    contract = json.loads(PINNED_REFERENCE_CONTRACT.read_text())
    if contract.get("baseSha") != BASE_SHA:
        raise RuntimeError(f"Reference manifest is not pinned to reviewed base {BASE_SHA}")
    mismatches = [
        f"{relative}: expected {expected}, got {sha256(ROOT / relative)}"
        for relative, expected in contract.get("assetSha256", {}).items()
        if not (ROOT / relative).is_file() or sha256(ROOT / relative) != expected
    ]
    if mismatches:
        raise RuntimeError("Reference inputs drifted; establish a new reviewed base:\n" + "\n".join(mismatches))


verify_pinned_reference_assets()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


e4 = load_module("dome_reference_e4", ROOT / "assets/pilots/tavern-3d/render_wave9_e4_wide.py")
e5 = load_module("dome_reference_e5", ROOT / "assets/pilots/tavern-3d/render_wave10_e5_harbor.py")
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
    town.import_model(PAN, "HeritageSurvivor:pan_monument", town.Point(0.0, 0.0))


def add_e6() -> None:
    placements = {
        "atomic_diner": "tavern",
        "isotope_kitchen": "general_store",
        "isotope_institute": "schoolhouse",
        "decay_clock": "claim_office",
        "appliance_pen": "assay_office",
    }
    for key, slot_id in placements.items():
        item = slot(slot_id)
        town.import_model(E6_MODELS[key], f"Current:E6:{key}", item.position, town.slot_angle(item))
    dome = town.import_model(E6_MODELS["reactor_dome"], "Current:E6:reactor_dome", town.Point(7.0, -16.7))
    dome.location.z = 1.18
    warehouse = town.import_model(
        E6_MODELS["catalog_warehouse"], "Current:E6:catalog_warehouse", town.Point(-7.4, -16.6), math.pi,
    )
    warehouse.location.z = 1.18
    town.import_model(E6_MODELS["sunline_mount"], "Current:E6:sunline_mount", town.Point(12.0, 7.0), -0.25, 1.20)
    for index, (x, y, rotation) in enumerate(((-12.0, 0.8, 0.0), (12.0, 0.8, 0.0), (0.0, 12.8, 1.57)), 1):
        town.import_model(E6_MODELS["glow_fence"], f"Current:E6:glow_fence_{index}", town.Point(x, y), rotation)


def add_e7() -> None:
    placements = {
        "net_cafe": "tavern",
        "isotope_kitchen": "general_store",
        "signal_works": "schoolhouse",
        "decay_clock": "claim_office",
        "appliance_pen": "assay_office",
    }
    paths = {**E6_MODELS, **E7_MODELS}
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


def setup_mesa_camera() -> None:
    town.setup_render_scene()
    camera = bpy.context.scene.camera
    camera.location = (0.0, 25.5, 37.0)
    town.look_at(camera, Vector((0.0, 0.5, 1.18)))
    if camera.data.type == "ORTHO":
        camera.data.ortho_scale = max(camera.data.ortho_scale, 52.0)


def render_e1(path: Path) -> None:
    town.reset_scene()
    town.import_model(CURRENT_PLATE, "Current:E1:plate", town.Point(0, 0))
    town.add_render_models()
    town.setup_render_scene()
    town.render(path)


def render_e4(path: Path) -> None:
    town.reset_scene()
    town.import_model(CURRENT_PLATE, "Current:E4:plate", town.Point(0, 0))
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
    town.import_model(MESA_PLATE, f"Current:E{era}:mesa", town.Point(0, 0))
    add_pan()
    (add_e6 if era == 6 else add_e7)()
    setup_mesa_camera()
    town.render(path)


def image_array(path: Path) -> np.ndarray:
    image = bpy.data.images.load(str(path), check_existing=False)
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    array = pixels.reshape(height, width, 4)
    bpy.data.images.remove(image)
    return array


def save_array(array: np.ndarray, path: Path) -> None:
    height, width, _ = array.shape
    image = bpy.data.images.new(path.stem, width, height, alpha=True)
    image.pixels.foreach_set(array.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)


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
    paths = {
        "e1": OUT / "town-e1-current.png",
        "e4": OUT / "town-e4-current.png",
        "e5": OUT / "town-e5-current-underwater.png",
        "e6": OUT / "town-e6-current.png",
        "e7": OUT / "town-e7-current.png",
    }
    arrays = {key: image_array(path) for key, path in paths.items()}
    blank = np.ones_like(arrays["e1"])
    blank[:, :, :3] = np.array([0.095, 0.075, 0.055], dtype=np.float32)
    top = np.concatenate([arrays["e1"], arrays["e4"], arrays["e5"]], axis=1)
    bottom = np.concatenate([arrays["e6"], arrays["e7"], blank], axis=1)
    board = OUT / "town-e1-e7-current.png"
    # Blender stores pixel rows bottom-up, so the intended visual top row is
    # written second in the array.
    save_array(np.concatenate([bottom, top], axis=0), board)
    annotate(board, "FRESH CURRENT-FILE REFERENCE | E1 / E4 / E5 / E6 / E7")

    tracked = [CURRENT_PLATE, MESA_PLATE, PAN, *e4.E4_MODELS.values(), *e5.E5_MODELS.values(), *E6_MODELS.values(), *E7_MODELS.values()]
    tracked = list(dict.fromkeys(tracked))
    contract = {
        "baseSha": BASE_SHA,
        "rule": "fresh render from current tracked GLBs; no prior PNG is an input",
        "order": ["E1 square", "E4 motor boulevard", "E5 submerged square", "E6 Atomic Mesa", "E7 Signal Mesa"],
        "assetSha256": {str(path.relative_to(ROOT)): sha256(path) for path in tracked},
        "renders": [str(path.relative_to(ROOT)) for path in [*paths.values(), board]],
    }
    (OUT / "reference-contract.json").write_text(json.dumps(contract, indent=2) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    targets = {
        "e1": (render_e1, OUT / "town-e1-current.png"),
        "e4": (render_e4, OUT / "town-e4-current.png"),
        "e5": (render_e5, OUT / "town-e5-current-underwater.png"),
        "e6": (lambda path: render_mesa(path, 6), OUT / "town-e6-current.png"),
        "e7": (lambda path: render_mesa(path, 7), OUT / "town-e7-current.png"),
    }
    if "--" in sys.argv:
        target = sys.argv[sys.argv.index("--") + 1]
        if target == "assemble":
            assemble()
        else:
            function, path = targets[target]
            function(path)
        return
    for target in targets:
        subprocess.run([bpy.app.binary_path, "--background", "--python", str(Path(__file__).resolve()), "--", target], check=True)
    assemble()


if __name__ == "__main__":
    main()
