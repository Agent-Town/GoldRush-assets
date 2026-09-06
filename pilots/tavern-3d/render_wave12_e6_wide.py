from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys

sys.dont_write_bytecode = True

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE_SHA = "1a58335f65645b8491e50763e10a32d12d8696f1"
MESA_BRANCH_TIP = "60242186e7bd7e72050146d06533d56922e2fc4e"
MESA_GLB_SHA = "067c8c652134258379315a41200caf423ff3e9cb70a1b9d8f2607ee691aafdc3"
PILOT_BRANCH_TIP = "cfdff259c5d3f271f2022b23341d1da4a6f0c4f2"
PILOT_ASSETS = {
    "atomic_diner": ("assets/pilots/tavern-3d/tavern.e6.glb",
                     "68ec4ed82ec24c42386a2abf6ff0fc4738556be4e380a9f06bc7e3de4478fd74"),
    "reactor_dome": ("assets/pilots/reactor-dome-3d/reactor-dome.glb",
                    "64c81b9b6e622890556cb057f3de230ff76f66731d370e08a2f2f19dda61b5ea"),
    "isotope_kitchen": ("assets/pilots/isotope-kitchen-3d/isotope-kitchen.glb",
                       "9664b671eb91bfae861ff70b11014ba2f393c0adb150a0b35a330c38afedf7b6"),
}

OUT = ROOT / "artifacts/town-e6-wide"
REFS = OUT / "current-references" / f"{BASE_SHA[:12]}-main"
E6 = OUT / "e6"
TURNTABLES = OUT / "turntables"
IDENTITY = OUT / "identity"
TEMP = Path("/tmp/gold-rush-wave12-e6")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


e4 = load_module("wave12_reference_e4", HERE / "render_wave9_e4_wide.py")
e5 = load_module("wave12_reference_e5", HERE / "render_wave10_e5_harbor.py")
town_render = e4.town_render
town = e4.town
town_render.TURNTABLE_DIR = TURNTABLES

LOCAL_MODELS = {
    "appliance_pen": ROOT / "assets/pilots/appliance-pen-3d/appliance-pen.glb",
    "decay_clock": ROOT / "assets/pilots/decay-clock-3d/decay-clock.glb",
    "catalog_warehouse": ROOT / "assets/pilots/catalog-warehouse-3d/catalog-warehouse.glb",
    "sunline_mount": ROOT / "assets/pilots/run3d/turret.e6.glb",
    "glow_fence": ROOT / "assets/pilots/run3d/palisade.e6.glb",
    "isotope_institute": ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.e6.glb",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_directories():
    for directory in (OUT, REFS, E6, TURNTABLES, IDENTITY, TEMP):
        directory.mkdir(parents=True, exist_ok=True)


def extract_git_asset(ref, source, target, expected_sha):
    with target.open("wb") as handle:
        subprocess.run(["git", "show", f"{ref}:{source}"], cwd=ROOT, stdout=handle, check=True)
    if sha256(target) != expected_sha:
        raise RuntimeError(f"Evidence dependency mismatch: {ref}:{source}")


def extract_dependencies():
    extract_git_asset(
        "origin/sol/mesa-town-plate", "assets/pilots/mesa-town-3d/mesa-town-plate.glb",
        TEMP / "mesa-town-plate.glb", MESA_GLB_SHA,
    )
    for key, (source, expected) in PILOT_ASSETS.items():
        extract_git_asset("origin/sol/mesa-town-e6-pilot", source, TEMP / f"{key}.glb", expected)


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
    for identifier, position, size in (
        ("reactor", (7.0, -16.7), (2.65, 2.65)),
        ("warehouse", (-7.4, -16.6), (2.45, 1.65)),
    ):
        if identifier in excluded:
            continue
        bpy.ops.mesh.primitive_cube_add(location=(position[0], position[1], 2.20), scale=(size[0], size[1], 1.0))
        bpy.context.object.data.materials.append(material)


def add_pan_survivor():
    town.import_model(
        ROOT / "assets/pilots/plaza-props-3d/pan_monument.glb", "HeritageSurvivor:pan_monument",
        town.Point(0, 0), 0.0, 1.0,
    )


def slot(identifier):
    return next(item for item in [*town.SLOTS, town.DYNAMO_SLOT] if item.id == identifier)


def add_e6_models():
    models = {}
    placements = {
        "atomic_diner": (TEMP / "atomic_diner.glb", "tavern", 0.0),
        "isotope_kitchen": (TEMP / "isotope_kitchen.glb", "general_store", 0.0),
        "isotope_institute": (LOCAL_MODELS["isotope_institute"], "schoolhouse", 0.0),
        "decay_clock": (LOCAL_MODELS["decay_clock"], "claim_office", 0.0),
        "appliance_pen": (LOCAL_MODELS["appliance_pen"], "assay_office", 0.0),
    }
    for key, (path, slot_id, height) in placements.items():
        item = slot(slot_id)
        models[key] = town.import_model(path, f"E6:{key}", item.position, town.slot_angle(item))
        models[key].location.z = height
    models["reactor_dome"] = town.import_model(
        TEMP / "reactor_dome.glb", "E6:reactor_dome", town.Point(7.0, -16.7), 0.0,
    )
    models["reactor_dome"].location.z = 1.18
    models["catalog_warehouse"] = town.import_model(
        LOCAL_MODELS["catalog_warehouse"], "E6:catalog_warehouse", town.Point(-7.4, -16.6), 3.141592653589793,
    )
    models["catalog_warehouse"].location.z = 1.18
    # Compact buildables retain their native footprints and demonstrate the A2
    # transforms at the Mesa perimeter, not on a Town building pad.
    models["sunline_mount"] = town.import_model(
        LOCAL_MODELS["sunline_mount"], "E6:sunline_mount", town.Point(12.0, 7.0), -0.25, 1.20,
    )
    for index, (x, y, rotation) in enumerate(((-12.0, 0.8, 0.0), (12.0, 0.8, 0.0), (0.0, 12.8, 1.57)), 1):
        models[f"glow_fence_{index}"] = town.import_model(
            LOCAL_MODELS["glow_fence"], f"E6:glow_fence_{index}", town.Point(x, y), rotation, 1.0,
        )
    return models


def setup_mesa_camera():
    town.setup_render_scene()
    camera = bpy.context.scene.camera
    camera.location = (0.0, 24.5, 35.0)
    town.look_at(camera, Vector((0.0, -4.0, 0.72)))
    sun = bpy.data.objects.get("EvidenceSun")
    sun.data.energy = 2.05
    fill = bpy.data.objects.get("EvidenceFill")
    fill.data.energy = 960.0


def render_mesa(path, production):
    extract_dependencies()
    town.reset_scene()
    town.import_model(TEMP / "mesa-town-plate.glb", "EvidenceExactMesaPlate", town.Point(0, 0))
    add_pan_survivor()
    if production:
        add_e6_models()
    else:
        add_massing(set())
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
    crop = array[int(height * 0.16):int(height * 0.96), int(width * 0.08):int(width * 0.94)]
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

    baseline = E6 / "mesa-full-massing-baseline.png"
    candidate = E6 / "mesa-complete-e6-set.png"
    town_render.combine_ab(baseline, candidate, OUT / "mesa-e6-wide-across-plaza-ab.png")
    annotate(OUT / "mesa-e6-wide-across-plaza-ab.png", "MESA MASSING / COMPLETE E6 SET | SAME GAMEPLAY CAMERA")
    crop_key_features(candidate, OUT / "mesa-e6-wide-key-feature-crop.png")
    annotate(OUT / "mesa-e6-wide-key-feature-crop.png", "E6 GAMEPLAY-DISTANCE CROP | FULL CIVIC SET")

    turntable_scales = {
        "appliance_pen": 6.2, "decay_clock": 9.2, "catalog_warehouse": 7.4,
        "sunline_mount": 3.2, "glow_fence": 4.4, "isotope_institute": 8.2,
    }
    for key, scale in turntable_scales.items():
        target = TURNTABLES / f"{key.replace('_', '-')}-e6.png"
        town_render.render_turntable(LOCAL_MODELS[key], target, f"{key}-e6", scale)
        annotate(target, f"{key.replace('_', ' ').upper()} | FOUR ANGLES")

    comparisons = {
        "sunline_mount": (ROOT / "assets/pilots/run3d/turret.glb", LOCAL_MODELS["sunline_mount"], 3.2),
        "glow_fence": (ROOT / "assets/pilots/run3d/palisade.glb", LOCAL_MODELS["glow_fence"], 4.4),
        "isotope_institute": (ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.e5.glb",
                              LOCAL_MODELS["isotope_institute"], 8.2),
    }
    for key, (source, target, scale) in comparisons.items():
        before = IDENTITY / f"{key}-before.png"
        after = IDENTITY / f"{key}-e6.png"
        town_render.render_turntable(source, before, f"{key}-before", scale)
        town_render.render_turntable(target, after, f"{key}-e6", scale)
        board = IDENTITY / f"{key.replace('_', '-')}-identity-ab.png"
        town_render.combine_ab(before, after, board)
        annotate(board, f"INHERITED IDENTITY / E6 {key.replace('_', ' ').upper()}")

    metrics = town_render.comparison_metrics(baseline, candidate)
    report = {
        "baseSha": BASE_SHA,
        "target": "Complete E6 Mesa ensemble reads as a warm atomic civic town at gameplay distance while compact transforms retain their inherited silhouettes.",
        "freshReferenceRule": "all current-era PNGs rerendered from tracked files on this base; no old PNG input",
        "dependencies": {
            "mesa": {"branchTip": MESA_BRANCH_TIP, "sha256": MESA_GLB_SHA, "usage": "evidence only"},
            "pilot": {"branchTip": PILOT_BRANCH_TIP, "assets": PILOT_ASSETS, "usage": "evidence only"},
        },
        "placements": {
            "atomicDiner": "tavern slot", "isotopeKitchen": "general_store slot",
            "isotopeInstitute": "schoolhouse slot", "decayClock": "claim_office slot",
            "appliancePen": "assay_office slot", "reactorDome": [7.0, -16.7, 1.18],
            "catalogWarehouse": [-7.4, -16.6, 1.18],
        },
        "comparisonMetrics": metrics,
        "visualReview": {
            "localFullFrameCropAndTurntables": "required before delivery",
            "independentSubagent": "not run: this session explicitly forbids delegation; limitation recorded",
        },
    }
    (OUT / "visual-evidence-contract.json").write_text(json.dumps(report, indent=2) + "\n")


def render_target(target):
    ensure_directories()
    targets = {
        "e1": lambda: render_e1(REFS / "town-e1-current.png"),
        "e4": lambda: render_e4(REFS / "town-e4-current.png"),
        "e5": lambda: render_e5(REFS / "town-e5-current-underwater.png"),
        "e4wagon": lambda: render_e4_wagon(REFS / "e3-e4-current-motor-caravan.png"),
        "mesa-baseline": lambda: render_mesa(E6 / "mesa-full-massing-baseline.png", False),
        "mesa-wide": lambda: render_mesa(E6 / "mesa-complete-e6-set.png", True),
    }
    targets[target]()


def main():
    ensure_directories()
    if "--" in sys.argv:
        render_target(sys.argv[sys.argv.index("--") + 1])
        return
    for target in ("e1", "e4", "e5", "e4wagon", "mesa-baseline", "mesa-wide"):
        subprocess.run(
            [bpy.app.binary_path, "--background", "--python", str(Path(__file__).resolve()), "--", target],
            check=True,
        )
    assemble()


if __name__ == "__main__":
    main()
