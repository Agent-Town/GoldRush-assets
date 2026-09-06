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
BASE_SHA = "8d974f11911187136469fbd017c9598e5b2faf28"
MESA_BRANCH_TIP = "60242186e7bd7e72050146d06533d56922e2fc4e"
MESA_GLB_SHA = "067c8c652134258379315a41200caf423ff3e9cb70a1b9d8f2607ee691aafdc3"
OUT = ROOT / "artifacts/town-e6-pilot"
REFS = OUT / "current-references" / f"{BASE_SHA[:12]}-main"
E6 = OUT / "e6"
TURNTABLES = OUT / "turntables"
MESA_TEMP = Path("/tmp/mesa-town-plate-wave11.glb")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


e4 = load_module("wave11_reference_e4", HERE / "render_wave9_e4_wide.py")
e5 = load_module("wave11_reference_e5", HERE / "render_wave10_e5_harbor.py")
town_render = e4.town_render
town = e4.town
town_render.TURNTABLE_DIR = TURNTABLES

E6_MODELS = {
    "atomic_diner": HERE / "tavern.e6.glb",
    "reactor_dome": ROOT / "assets/pilots/reactor-dome-3d/reactor-dome.glb",
    "isotope_kitchen": ROOT / "assets/pilots/isotope-kitchen-3d/isotope-kitchen.glb",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_directories():
    for directory in (OUT, REFS, E6, TURNTABLES):
        directory.mkdir(parents=True, exist_ok=True)


def extract_mesa():
    with MESA_TEMP.open("wb") as handle:
        subprocess.run(
            ["git", "show", "origin/sol/mesa-town-plate:assets/pilots/mesa-town-3d/mesa-town-plate.glb"],
            cwd=ROOT, stdout=handle, check=True,
        )
    if sha256(MESA_TEMP) != MESA_GLB_SHA:
        raise RuntimeError("Evidence-only Mesa GLB does not match the accepted pilot branch")


def annotate(path, label):
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


def render_e1(path):
    town.reset_scene()
    town.import_model(ROOT / "assets/pilots/town-plate-3d/town-plate.glb", "RenderTownPlate", town.Point(0, 0))
    town.add_render_models()
    town.setup_render_scene()
    town.render(path)


def render_e4(path):
    town.reset_scene()
    town.import_model(ROOT / "assets/pilots/town-plate-3d/town-plate.glb", "RenderTownPlate", town.Point(0, 0))
    e4.add_town_context(e4.E4_MODELS)
    town.setup_render_scene()
    camera = bpy.context.scene.camera
    camera.location = (0.0, 24.5, 34.5)
    town.look_at(camera, Vector((0.0, -1.5, 0.45)))
    town.render(path)


def render_e5(path):
    e5.render_town(e5.E5_MODELS, 5, path, overview=True, underwater=True)


def render_e4_wagon(path):
    e4.render_wagon_accretion(path)


def evidence_material(name, color):
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = 0.94
    return material


def add_massing(excluded):
    material = evidence_material("Evidence inherited-site massing", (0.26, 0.19, 0.12, 1.0))
    for slot in [*town.SLOTS, town.DYNAMO_SLOT]:
        if slot.id in excluded:
            continue
        bpy.ops.mesh.primitive_cube_add(
            location=(slot.position.x, slot.position.y, 1.05),
            scale=(slot.width * 0.38, slot.depth * 0.38, 1.05),
            rotation=(0, 0, town.slot_angle(slot)),
        )
        proxy = bpy.context.object
        proxy.name = f"EvidenceMassing:{slot.id}"
        proxy.data.materials.append(material)


def add_pan_survivor():
    town.import_model(
        ROOT / "assets/pilots/plaza-props-3d/pan_monument.glb", "HeritageSurvivor:pan_monument",
        town.Point(0, 0), 0.0, 1.0,
    )


def add_e6_models():
    tavern_slot = next(slot for slot in town.SLOTS if slot.id == "tavern")
    store_slot = next(slot for slot in town.SLOTS if slot.id == "general_store")
    diner = town.import_model(E6_MODELS["atomic_diner"], "E6:AtomicDiner", tavern_slot.position, town.slot_angle(tavern_slot))
    kitchen = town.import_model(
        E6_MODELS["isotope_kitchen"], "E6:IsotopeKitchen", store_slot.position, town.slot_angle(store_slot),
    )
    dome = town.import_model(E6_MODELS["reactor_dome"], "E6:ReactorDome", town.Point(7.0, -16.7), 0.0)
    dome.location.z = 1.18
    return diner, kitchen, dome


def setup_mesa_camera():
    town.setup_render_scene()
    scene = bpy.context.scene
    camera = scene.camera
    camera.location = (0.0, 16.5, 25.5)
    town.look_at(camera, Vector((0.0, -8.5, 0.72)))
    sun = bpy.data.objects.get("EvidenceSun")
    sun.data.energy = 2.05
    fill = bpy.data.objects.get("EvidenceFill")
    fill.data.energy = 960.0


def render_mesa(path, production):
    extract_mesa()
    town.reset_scene()
    town.import_model(MESA_TEMP, "EvidenceExactMesaPlate", town.Point(0, 0))
    add_massing({"tavern", "general_store"} if production else set())
    add_pan_survivor()
    if production:
        add_e6_models()
    setup_mesa_camera()
    town.render(path)


def image_array(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    array = pixels.reshape(height, width, 4)
    bpy.data.images.remove(image)
    return array


def save_array(array, path):
    height, width, _ = array.shape
    image = bpy.data.images.new(path.stem, width, height, alpha=True)
    image.pixels.foreach_set(array.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)


def combine_horizontal(paths, output):
    save_array(np.concatenate([image_array(path) for path in paths], axis=1), output)


def crop_key_features(path, output):
    array = image_array(path)
    height, width, _ = array.shape
    # The gameplay camera puts Diner left-center, Kitchen center-front, and Dome
    # on the lower-right Mesa shelf. Preserve context around all three.
    crop = array[int(height * 0.28):int(height * 0.93), int(width * 0.17):int(width * 0.90)]
    save_array(crop, output)


def assemble():
    reference_paths = [
        REFS / "town-e1-current.png",
        REFS / "town-e4-current.png",
        REFS / "town-e5-current-underwater.png",
    ]
    for path, era in zip(reference_paths, ("E1 CURRENT", "E4 CURRENT MOTOR", "E5 CURRENT SUBMERGED")):
        annotate(path, era)
    annotate(REFS / "e3-e4-current-motor-caravan.png", "E3 / E4 CURRENT WAGON")
    reference_board = REFS / "town-e1-e4-e5-current.png"
    combine_horizontal(reference_paths, reference_board)
    annotate(reference_board, "FRESH CURRENT-FILE REFERENCE | E1 / E4 / E5")

    baseline = E6 / "mesa-massing-baseline.png"
    pilot = E6 / "mesa-three-building-pilot.png"
    town_render.combine_ab(baseline, pilot, OUT / "mesa-e6-pilot-across-plaza-ab.png")
    annotate(OUT / "mesa-e6-pilot-across-plaza-ab.png", "MESA MASSING / E6 PILOT | SAME GAMEPLAY CAMERA")
    crop_key_features(pilot, OUT / "mesa-e6-pilot-key-feature-crop.png")
    annotate(OUT / "mesa-e6-pilot-key-feature-crop.png", "E6 GAMEPLAY-DISTANCE CROP | DINER / KITCHEN / DOME")

    current_tavern = TURNTABLES / "tavern-e1.png"
    diner = TURNTABLES / "atomic-diner-e6.png"
    town_render.render_turntable(
        ROOT / "assets/pilots/tavern-3d/town-v3-tavern.glb", current_tavern, "tavern-e1", 6.5,
    )
    town_render.render_turntable(E6_MODELS["atomic_diner"], diner, "atomic-diner-e6", 7.2)
    town_render.combine_ab(current_tavern, diner, OUT / "atomic-diner-identity-ab.png")
    annotate(OUT / "atomic-diner-identity-ab.png", "TAVERN IDENTITY / E6 ATOMIC DINER")
    town_render.render_turntable(
        E6_MODELS["reactor_dome"], TURNTABLES / "reactor-dome-e6.png", "reactor-dome-e6", 7.8,
    )
    town_render.render_turntable(
        E6_MODELS["isotope_kitchen"], TURNTABLES / "isotope-kitchen-e6.png", "isotope-kitchen-e6", 7.2,
    )
    annotate(TURNTABLES / "atomic-diner-e6.png", "ATOMIC DINER | FOUR ANGLES")
    annotate(TURNTABLES / "reactor-dome-e6.png", "REACTOR DOME | FOUR ANGLES")
    annotate(TURNTABLES / "isotope-kitchen-e6.png", "ISOTOPE KITCHEN | FOUR ANGLES")

    metrics = town_render.comparison_metrics(baseline, pilot)
    report = {
        "baseSha": BASE_SHA,
        "target": (
            "At gameplay distance, E6 must read as a dry atomic Mesa era: the Tavern identity becomes a "
            "chrome/enamel social hub, while the Dome and Kitchen own distinct civic-machine silhouettes."
        ),
        "freshReferenceRule": "all current-era PNGs rerendered from GLBs and manifests on this base; no old PNG input",
        "mesaEvidenceDependency": {
            "branchTip": MESA_BRANCH_TIP,
            "path": "assets/pilots/mesa-town-3d/mesa-town-plate.glb",
            "sha256": MESA_GLB_SHA,
            "usage": "exact site and camera evidence only; no Mesa bytes duplicated in this wave",
        },
        "placements": {
            "atomicDiner": {"identitySlot": "tavern", "position": [-7.1, -7.1], "height": 0.0},
            "isotopeKitchen": {"pilotSlot": "general_store", "position": [0.0, -10.2], "height": 0.0},
            "reactorDome": {"premiumSite": "reactor-dome-candidate", "position": [7.0, -16.7], "height": 1.18},
        },
        "comparisonMetrics": metrics,
        "visualReview": {
            "localFullFrameAndCrop": "required and completed after generation",
            "independentSubagent": "not run: this session explicitly forbids delegation; limitation recorded",
        },
        "renders": [
            str(path.relative_to(ROOT)) for path in [
                reference_board, OUT / "mesa-e6-pilot-across-plaza-ab.png",
                OUT / "mesa-e6-pilot-key-feature-crop.png", OUT / "atomic-diner-identity-ab.png",
                TURNTABLES / "atomic-diner-e6.png", TURNTABLES / "reactor-dome-e6.png",
                TURNTABLES / "isotope-kitchen-e6.png",
            ]
        ],
    }
    (OUT / "visual-evidence-contract.json").write_text(json.dumps(report, indent=2) + "\n")


def render_target(target):
    ensure_directories()
    targets = {
        "e1": lambda: render_e1(REFS / "town-e1-current.png"),
        "e4": lambda: render_e4(REFS / "town-e4-current.png"),
        "e5": lambda: render_e5(REFS / "town-e5-current-underwater.png"),
        "e4wagon": lambda: render_e4_wagon(REFS / "e3-e4-current-motor-caravan.png"),
        "mesa-baseline": lambda: render_mesa(E6 / "mesa-massing-baseline.png", False),
        "mesa-pilot": lambda: render_mesa(E6 / "mesa-three-building-pilot.png", True),
    }
    targets[target]()


def main():
    ensure_directories()
    if "--" in sys.argv:
        render_target(sys.argv[sys.argv.index("--") + 1])
        return
    for target in ("e1", "e4", "e5", "e4wagon", "mesa-baseline", "mesa-pilot"):
        subprocess.run(
            [bpy.app.binary_path, "--background", "--python", str(Path(__file__).resolve()), "--", target],
            check=True,
        )
    assemble()


if __name__ == "__main__":
    main()
