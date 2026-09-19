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
HERE = Path(__file__).resolve().parent
GLB = HERE / "homemaker-9000.glb"
REFERENCE = ROOT / "assets/raw/plate-e6-boss-homemaker-9000.png"
TERRAIN = ROOT / "assets/pilots/map-rebuild-spike/glow-mesa-terrain.glb"
DOME = ROOT / "assets/pilots/dome-commons-3d/dome-commons-plate.glb"
PAN = ROOT / "assets/pilots/plaza-props-3d/pan_monument.glb"
OUT = HERE / "renders"
TOWN_REFS = OUT / "current-town"
BASE_SHA = "f50cc240618ddc23b88efee1f27d4cf2035a04ab"
BOSS_SITE = Vector((0.0, 32.0, 1.0))
RUN_CAMERA_OFFSET = Vector((0.0, -18.3, 26.2))
RUN_LOOK_OFFSET = Vector((0.0, 3.35, 0.45))
COMPONENTS = {
    "vac": "Damage_DroppedVac",
    "rack": "Damage_SpentRack",
    "core": "Damage_ChairPose",
}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


shared = load("homemaker_shared_renderer", ROOT / "assets/pilots/dredge-queen-3d/render_dredge_queen.py")
shared.GLB = GLB
shared.REFERENCE = REFERENCE
shared.DAMAGE_REFERENCE = REFERENCE
shared.TERRAIN = TERRAIN
shared.OUT = OUT
shared.COMPONENTS = COMPONENTS


def atomic_scene(resolution: tuple[int, int]):
    camera = shared.setup_scene(resolution)
    background = bpy.context.scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.10, 0.055, 0.020, 1)
    background.inputs["Strength"].default_value = 0.48
    lights = [obj for obj in bpy.context.scene.objects if obj.type == "LIGHT"]
    if lights:
        lights[0].data.color = (1.0, 0.68, 0.30)
        lights[0].data.energy = 2500
        if len(lights) > 1:
            lights[1].data.color = (0.10, 0.72, 0.70)
            lights[1].data.energy = 1900
    return camera


def turntable() -> None:
    shared.reset_scene()
    shared.import_dredge_queen()
    ground = shared.material("Atomic review ground", (0.28, 0.13, 0.045, 1), 0.94)
    shared.add_box("Atomic review ground", (18, 18, 0.10), (0, 0, -0.08), ground)
    camera = atomic_scene((640, 640))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 10.5
    target = Vector((0, 0, 2.75))
    paths = []
    for label, location in (
        ("front-left", Vector((-10, -11, 7.6))), ("front-right", Vector((10, -11, 7.6))),
        ("rear-left", Vector((-10, 11, 7.6))), ("rear-right", Vector((10, 11, 7.6))),
    ):
        shared.aim(camera, location, target)
        path = OUT / f"turntable-{label}.png"
        shared.render(path)
        paths.append(path)
    shared.save_grid(paths, OUT / "homemaker-9000-turntable.png", 2, 2)
    for path in paths:
        path.unlink()


def add_mesa() -> None:
    bpy.ops.import_scene.gltf(filepath=str(TERRAIN))
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and obj.name not in COMPONENTS:
            obj.name = f"Context:{obj.name}"


def on_tile() -> None:
    shared.reset_scene()
    objects = shared.import_dredge_queen()
    for obj in objects.values():
        obj.location += BOSS_SITE
    add_mesa()
    camera = atomic_scene((1280, 800))
    for light in (obj for obj in bpy.context.scene.objects if obj.type == "LIGHT"):
        light.location += BOSS_SITE
    camera.data.type = "PERSP"
    camera.data.angle = math.radians(42)
    shared.aim(camera, BOSS_SITE + RUN_CAMERA_OFFSET, BOSS_SITE + RUN_LOOK_OFFSET)
    intact = OUT / "homemaker-9000-glow-mesa-run-camera-intact.png"
    final = OUT / "homemaker-9000-glow-mesa-run-camera-final-chair.png"
    shared.render(intact)
    shared.set_all_morphs(objects, 1.0)
    shared.render(final)
    shared.save_grid([intact, final], OUT / "homemaker-9000-glow-mesa-run-camera.png", 1, 2)
    shared.save_reference_ab(REFERENCE, intact, OUT / "homemaker-9000-reference-ab.png")


def damage_states() -> None:
    shared.reset_scene()
    objects = shared.import_dredge_queen()
    ground = shared.material("Damage mesa", (0.28, 0.13, 0.045, 1), 0.94)
    shared.add_box("Damage mesa", (18, 18, 0.10), (0, 0, -0.08), ground)
    camera = atomic_scene((640, 540))
    camera.data.type = "PERSP"
    camera.data.angle = math.radians(46)
    views = {
        "vac": (Vector((-10.8, -11.2, 7.4)), Vector((-1.4, -0.3, 2.6))),
        "rack": (Vector((8.8, -11.4, 9.0)), Vector((0.0, 0.0, 4.3))),
        "core": (Vector((9.8, -12.4, 7.2)), Vector((0.0, 0.1, 2.4))),
    }
    paths = []
    for component, morph in COMPONENTS.items():
        shared.set_all_morphs(objects, 0.0)
        objects[component].data.shape_keys.key_blocks[morph].value = 1.0
        location, target = views[component]
        shared.aim(camera, location, target)
        path = OUT / f"damage-{component}.png"
        shared.render(path)
        paths.append(path)
    shared.set_all_morphs(objects, 1.0)
    shared.aim(camera, Vector((-9.8, -12.4, 7.2)), Vector((0.0, 0.1, 2.15)))
    final_panel = OUT / "damage-final-chair.png"
    shared.render(final_panel)
    shared.save_grid([*paths, final_panel], OUT / "homemaker-9000-damage-states.png", 2, 2)
    for path in [*paths, final_panel]:
        path.unlink()

    shared.set_all_morphs(objects, 0.0)
    shared.aim(camera, Vector((-10.8, -12.8, 7.8)), Vector((0.0, 0.0, 2.65)))
    intact = OUT / "homemaker-9000-intact.png"
    shared.render(intact)
    shared.set_all_morphs(objects, 1.0)
    chair = OUT / "homemaker-9000-chair.png"
    shared.render(chair)
    shared.save_grid([intact, chair], OUT / "homemaker-9000-intact-chair.png", 1, 2)
    metrics = shared.damage_metrics(intact, chair)
    metrics["target"] = "VAC dropped, RACK spent, CORE seated in its self-built debris chair; one warm powered-down machine"
    (OUT / "homemaker-9000-damage-metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")


def annotate(path: Path, label: str) -> None:
    temporary = path.with_name(f".{path.name}")
    subprocess.run([
        "magick", str(path), "-font", "/System/Library/Fonts/Helvetica.ttc", "-gravity", "north",
        "-fill", "#f7df9d", "-undercolor", "#17120dcc", "-pointsize", "22",
        "-annotate", "+0+8", f"{label} | base {BASE_SHA}", str(temporary),
    ], check=True)
    temporary.replace(path)


def image_array(path: Path) -> np.ndarray:
    image = bpy.data.images.load(str(path), check_existing=False)
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    bpy.data.images.remove(image)
    return pixels.reshape(height, width, 4)


def save_array(array: np.ndarray, path: Path) -> None:
    height, width, _ = array.shape
    image = bpy.data.images.new(path.stem, width, height, alpha=True)
    image.pixels.foreach_set(array.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)


def current_town_references() -> None:
    # Render directly from the current GLBs. The older E8 evidence module is
    # intentionally hash-pinned to its historical base and must never be used as
    # current guidance after the road-wear replacement changed the E1 plate.
    e4 = load("homemaker_reference_e4", ROOT / "assets/pilots/tavern-3d/render_wave9_e4_wide.py")
    e5 = load("homemaker_reference_e5", ROOT / "assets/pilots/tavern-3d/render_wave10_e5_harbor.py")
    town = e4.town
    current_plate = ROOT / "assets/pilots/town-plate-3d/town-plate.glb"
    mesa_plate = ROOT / "assets/pilots/mesa-town-3d/mesa-town-plate.glb"
    e6_models = {
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
    e7_models = {
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

    def add_mesa_population(era: int) -> None:
        paths = {**e6_models, **e7_models}
        placements = {
            "atomic_diner" if era == 6 else "net_cafe": "tavern",
            "isotope_kitchen": "general_store",
            "isotope_institute" if era == 6 else "signal_works": "schoolhouse",
            "decay_clock": "claim_office",
            "appliance_pen": "assay_office",
        }
        for key, slot_id in placements.items():
            item = slot(slot_id)
            town.import_model(paths[key], f"Current:E{era}:{key}", item.position, town.slot_angle(item))
        dome = town.import_model(e6_models["reactor_dome"], f"Current:E{era}:reactor_dome", town.Point(7.0, -16.7))
        dome.location.z = 1.18
        north_key = "catalog_warehouse" if era == 6 else "tape_post"
        north = town.import_model(paths[north_key], f"Current:E{era}:{north_key}", town.Point(-7.4, -16.6), math.pi)
        north.location.z = 1.18
        town.import_model(e6_models["sunline_mount"] if era == 6 else e7_models["beam_relay"],
                          f"Current:E{era}:compact", town.Point(12.0, 7.0), -0.25, 1.20)
        for index, (x, y, rotation) in enumerate(((-12.0, 0.8, 0.0), (12.0, 0.8, 0.0), (0.0, 12.8, 1.57)), 1):
            town.import_model(e6_models["glow_fence"], f"Current:E{era}:glow_fence_{index}", town.Point(x, y), rotation)
        if era == 7:
            for key, point, rotation in (
                ("exchange", (-7.55, 9.40), 0.06), ("relay_tower", (7.55, 9.15), -0.08),
                ("playbook_library", (-14.2, -6.4), 0.12), ("drone_coop", (14.2, -6.0), -0.10),
                ("signal_refinery", (0.0, 16.2), math.pi),
            ):
                town.import_model(e7_models[key], f"Current:E7:{key}", town.Point(*point), rotation)

    def setup_mesa_camera() -> None:
        town.setup_render_scene()
        camera = bpy.context.scene.camera
        camera.location = (0.0, 25.5, 37.0)
        town.look_at(camera, Vector((0.0, 0.5, 1.18)))
        if camera.data.type == "ORTHO":
            camera.data.ortho_scale = max(camera.data.ortho_scale, 52.0)

    def render_mesa(path: Path, era: int) -> None:
        town.reset_scene()
        town.import_model(mesa_plate, f"Current:E{era}:mesa", town.Point(0, 0))
        add_pan()
        add_mesa_population(era)
        setup_mesa_camera()
        town.render(path)

    TOWN_REFS.mkdir(parents=True, exist_ok=True)
    paths = {
        "e1": TOWN_REFS / "town-e1-current.png",
        "e4": TOWN_REFS / "town-e4-current.png",
        "e5": TOWN_REFS / "town-e5-current-underwater.png",
        "e6": TOWN_REFS / "town-e6-current.png",
        "e7": TOWN_REFS / "town-e7-current.png",
        "e8": TOWN_REFS / "town-e8-current-empty-dome.png",
    }
    town.reset_scene()
    town.import_model(current_plate, "Current:E1:plate", town.Point(0, 0))
    town.add_render_models()
    town.setup_render_scene()
    town.render(paths["e1"])
    town.reset_scene()
    town.import_model(current_plate, "Current:E4:plate", town.Point(0, 0))
    e4.add_town_context(e4.E4_MODELS)
    town.setup_render_scene()
    camera = bpy.context.scene.camera
    camera.location = (0.0, 24.5, 34.5)
    town.look_at(camera, Vector((0.0, -1.5, 0.45)))
    town.render(paths["e4"])
    e5.render_town(e5.E5_MODELS, 5, paths["e5"], overview=True, underwater=True)
    render_mesa(paths["e6"], 6)
    render_mesa(paths["e7"], 7)

    town.reset_scene()
    town.import_model(DOME, "Current:E8:dome", town.Point(0, 0))
    town.import_model(PAN, "Current:E8:pan", town.Point(0, 0))
    town.setup_render_scene()
    camera = bpy.context.scene.camera
    camera.location = (0.0, 25.5, 37.0)
    town.look_at(camera, Vector((0.0, 0.5, 1.0)))
    if camera.data.type == "ORTHO":
        camera.data.ortho_scale = max(camera.data.ortho_scale, 52.0)
    town.render(paths["e8"])

    arrays = {key: image_array(path) for key, path in paths.items()}
    top = np.concatenate([arrays["e1"], arrays["e4"], arrays["e5"]], axis=1)
    bottom = np.concatenate([arrays["e6"], arrays["e7"], arrays["e8"]], axis=1)
    board = TOWN_REFS / "town-e1-e8-current.png"
    save_array(np.concatenate([bottom, top], axis=0), board)
    annotate(board, "FRESH CURRENT-FILE REFERENCE | E1 / E4 / E5 / E6 / E7 / E8")

    tracked = [
        current_plate, mesa_plate, DOME, PAN,
        *e4.E4_MODELS.values(), *e5.E5_MODELS.values(), *e6_models.values(), *e7_models.values(),
    ]
    tracked = list(dict.fromkeys(tracked))
    contract = {
        "baseSha": BASE_SHA,
        "rule": "fresh render from current tracked GLBs; no prior PNG is an input",
        "order": ["E1 square", "E4 motor boulevard", "E5 submerged square", "E6 Atomic Mesa", "E7 Signal Mesa", "E8 empty Dome Commons"],
        "assetSha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in tracked},
        "renders": [str(path.relative_to(ROOT)) for path in [*paths.values(), board]],
    }
    (TOWN_REFS / "reference-contract.json").write_text(json.dumps(contract, indent=2) + "\n")


def finish_evidence() -> None:
    labeled = {
        "homemaker-9000-turntable.png": "HOMEMAKER-9000 | FOUR-ANGLE COMPONENT AUDIT",
        "homemaker-9000-reference-ab.png": "CURRENT BOSS PLATE / PRODUCTION GLB",
        "homemaker-9000-intact-chair.png": "ACT 1 HELP / ACT 3 DONE",
        "homemaker-9000-damage-states.png": "VAC / RACK / CORE / FINAL CHAIR",
        "homemaker-9000-glow-mesa-run-camera.png": "GLOW MESA PRODUCTION CAMERA | INTACT / ACT 3 CHAIR",
    }
    for filename, label in labeled.items():
        annotate(OUT / filename, label)
    contract = {
        "baseSha": BASE_SHA,
        "rule": "fresh direct render from current plate and production GLB; no prior render is an input",
        "sourceSha256": {str(REFERENCE.relative_to(ROOT)): hashlib.sha256(REFERENCE.read_bytes()).hexdigest()},
        "terrainSha256": {str(TERRAIN.relative_to(ROOT)): hashlib.sha256(TERRAIN.read_bytes()).hexdigest()},
        "productionGlb": str(GLB.relative_to(ROOT)),
        "runtimeIds": list(COMPONENTS),
        "bossSiteThreeJs": [BOSS_SITE.x, BOSS_SITE.z, -BOSS_SITE.y],
        "runCamera": {
            "fovDegrees": 42,
            "offsetThreeJs": [0.0, 26.2, 18.3],
            "offsetBlenderZUp": [round(value, 2) for value in RUN_CAMERA_OFFSET],
            "lookOffsetThreeJs": [0.0, 0.45, -3.35],
            "lookOffsetBlenderZUp": [round(value, 2) for value in RUN_LOOK_OFFSET],
        },
        "runCameraStateRenders": [
            str((OUT / "homemaker-9000-glow-mesa-run-camera-intact.png").relative_to(ROOT)),
            str((OUT / "homemaker-9000-glow-mesa-run-camera-final-chair.png").relative_to(ROOT)),
        ],
        "renders": [str((OUT / filename).relative_to(ROOT)) for filename in labeled],
    }
    (OUT / "homemaker-9000-reference-contract.json").write_text(json.dumps(contract, indent=2) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    turntable()
    on_tile()
    damage_states()
    current_town_references()
    finish_evidence()
    print(f"rendered {OUT}")


if __name__ == "__main__":
    main()
