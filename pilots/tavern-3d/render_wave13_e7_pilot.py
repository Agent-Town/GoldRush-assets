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
BASE_SHA = "88ea5d9bca59dca64f35766b466cc2755751dcbb"
MESA_BRANCH_TIP = "60242186e7bd7e72050146d06533d56922e2fc4e"
MESA_GLB_SHA = "067c8c652134258379315a41200caf423ff3e9cb70a1b9d8f2607ee691aafdc3"
PILOT_BRANCH_TIP = "cfdff259c5d3f271f2022b23341d1da4a6f0c4f2"
WIDE_BRANCH_TIP = "bcc9764bd320460c6de99e901a4e979694341030"
PILOT_ASSETS = {
    "atomic_diner": ("assets/pilots/tavern-3d/tavern.e6.glb",
                     "68ec4ed82ec24c42386a2abf6ff0fc4738556be4e380a9f06bc7e3de4478fd74"),
    "reactor_dome": ("assets/pilots/reactor-dome-3d/reactor-dome.glb",
                    "64c81b9b6e622890556cb057f3de230ff76f66731d370e08a2f2f19dda61b5ea"),
    "isotope_kitchen": ("assets/pilots/isotope-kitchen-3d/isotope-kitchen.glb",
                       "9664b671eb91bfae861ff70b11014ba2f393c0adb150a0b35a330c38afedf7b6"),
}
WIDE_ASSETS = {
    "appliance_pen": ("assets/pilots/appliance-pen-3d/appliance-pen.glb",
                      "be11b90d1cf912256f840d852abc61bbf3082c072f01cfe3ce432505c2095e3d"),
    "decay_clock": ("assets/pilots/decay-clock-3d/decay-clock.glb",
                    "2b87660a3c7ee81a85c8b49b8697054f00f12cc3ff6046c6bf8be3910063f6ca"),
    "catalog_warehouse": ("assets/pilots/catalog-warehouse-3d/catalog-warehouse.glb",
                          "f72109125d3c036a3ac8a06004fa212f02539c762076dd9959c30cd578fcce24"),
    "sunline_mount": ("assets/pilots/run3d/turret.e6.glb",
                      "44d17919c60e294bbe977736a01ce93bf1a9f72a8ed85ca4b167a305b5cf1bbe"),
    "glow_fence": ("assets/pilots/run3d/palisade.e6.glb",
                   "686e72c52051d6f5b54b0cfec18fcc76502476bb7f0397870255f3e42807451c"),
    "isotope_institute": ("assets/pilots/schoolhouse-3d/schoolhouse.e6.glb",
                          "f3de54fb073729e1b251f0809b9ea65b2f869afd9c731430454636c03351bfb3"),
}

OUT = ROOT / "artifacts/town-e7-pilot"
REFS = OUT / "current-references" / f"{BASE_SHA[:12]}-main"
E6 = OUT / "e6"
E7 = OUT / "e7"
TURNTABLES = OUT / "turntables"
IDENTITY = OUT / "identity"
TEMP = Path("/tmp/gold-rush-wave13-e7")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


e4 = load_module("wave13_reference_e4", HERE / "render_wave9_e4_wide.py")
e5 = load_module("wave13_reference_e5", HERE / "render_wave10_e5_harbor.py")
town_render = e4.town_render
town = e4.town
town_render.TURNTABLE_DIR = TURNTABLES

LOCAL_MODELS = {
    "relay_tower": ROOT / "assets/pilots/relay-tower-3d/relay-tower.glb",
    "exchange": ROOT / "assets/pilots/exchange-3d/exchange.glb",
    "net_cafe": ROOT / "assets/pilots/tavern-3d/tavern.e7.glb",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_directories():
    for directory in (OUT, REFS, E6, E7, TURNTABLES, IDENTITY, TEMP):
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
    for key, (source, expected) in WIDE_ASSETS.items():
        extract_git_asset("origin/sol/mesa-town-e6-wide", source, TEMP / f"{key}.glb", expected)


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
    crop = array[int(height * 0.08):int(height * 0.98), int(width * 0.04):int(width * 0.96)]
    save_array(crop, output)


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


def add_pan_survivor():
    town.import_model(
        ROOT / "assets/pilots/plaza-props-3d/pan_monument.glb", "HeritageSurvivor:pan_monument",
        town.Point(0, 0), 0.0, 1.0,
    )


def slot(identifier):
    return next(item for item in [*town.SLOTS, town.DYNAMO_SLOT] if item.id == identifier)


def add_e6_models(use_net_cafe=False):
    models = {}
    placements = {
        "atomic_diner": (LOCAL_MODELS["net_cafe"] if use_net_cafe else TEMP / "atomic_diner.glb", "tavern"),
        "isotope_kitchen": (TEMP / "isotope_kitchen.glb", "general_store"),
        "isotope_institute": (TEMP / "isotope_institute.glb", "schoolhouse"),
        "decay_clock": (TEMP / "decay_clock.glb", "claim_office"),
        "appliance_pen": (TEMP / "appliance_pen.glb", "assay_office"),
    }
    for key, (path, slot_id) in placements.items():
        item = slot(slot_id)
        models[key] = town.import_model(path, f"Mesa:{key}", item.position, town.slot_angle(item))
    models["reactor_dome"] = town.import_model(
        TEMP / "reactor_dome.glb", "Mesa:reactor_dome", town.Point(7.0, -16.7), 0.0,
    )
    models["reactor_dome"].location.z = 1.18
    models["catalog_warehouse"] = town.import_model(
        TEMP / "catalog_warehouse.glb", "Mesa:catalog_warehouse", town.Point(-7.4, -16.6), math.pi,
    )
    models["catalog_warehouse"].location.z = 1.18
    models["sunline_mount"] = town.import_model(
        TEMP / "sunline_mount.glb", "Mesa:sunline_mount", town.Point(12.0, 7.0), -0.25, 1.20,
    )
    for index, (x, y, rotation) in enumerate(((-12.0, 0.8, 0.0), (12.0, 0.8, 0.0), (0.0, 12.8, 1.57)), 1):
        models[f"glow_fence_{index}"] = town.import_model(
            TEMP / "glow_fence.glb", f"Mesa:glow_fence_{index}", town.Point(x, y), rotation, 1.0,
        )
    return models


def add_e7_pilot():
    models = add_e6_models(use_net_cafe=True)
    models["exchange"] = town.import_model(
        LOCAL_MODELS["exchange"], "Mesa:E7:exchange", town.Point(-7.55, 9.40), 0.06,
    )
    models["relay_tower"] = town.import_model(
        LOCAL_MODELS["relay_tower"], "Mesa:E7:relay_tower", town.Point(7.55, 9.15), -0.08,
    )
    return models


def setup_mesa_camera():
    town.setup_render_scene()
    camera = bpy.context.scene.camera
    camera.location = (0.0, 25.5, 37.0)
    town.look_at(camera, Vector((0.0, -3.2, 1.18)))
    if camera.data.type == "ORTHO":
        camera.data.ortho_scale = max(camera.data.ortho_scale, 41.0)
    sun = bpy.data.objects.get("EvidenceSun")
    if sun:
        sun.data.energy = 2.05
    fill = bpy.data.objects.get("EvidenceFill")
    if fill:
        fill.data.energy = 960.0


def render_mesa(path, e7=False):
    town.reset_scene()
    town.import_model(TEMP / "mesa-town-plate.glb", "EvidenceExactMesaPlate", town.Point(0, 0))
    add_pan_survivor()
    if e7:
        add_e7_pilot()
    else:
        add_e6_models()
    setup_mesa_camera()
    town.render(path)


def render_turntable_smart(asset_path, output_path, prefix, margin=1.35):
    town.reset_scene()
    bpy.ops.import_scene.gltf(filepath=str(asset_path))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    minimum = Vector((min(point.x for point in corners), min(point.y for point in corners),
                      min(point.z for point in corners)))
    maximum = Vector((max(point.x for point in corners), max(point.y for point in corners),
                      max(point.z for point in corners)))
    center = (minimum + maximum) * 0.5
    width = max(maximum.x - minimum.x, maximum.y - minimum.y)
    height = maximum.z - minimum.z
    bpy.ops.mesh.primitive_plane_add(size=max(20, width * 3), location=(center.x, center.y, -0.015))
    ground = bpy.context.object
    ground.data.materials.append(bpy.data.materials.new("Review ground"))
    ground.data.materials[0].diffuse_color = (0.48, 0.35, 0.20, 1)
    bpy.ops.object.light_add(type="AREA", location=(-7, -8, max(10, height + 3)))
    bpy.context.object.data.energy = 1200
    bpy.context.object.data.shape = "DISK"
    bpy.context.object.data.size = 6
    bpy.ops.object.light_add(type="AREA", location=(7, 5, max(7, height * 0.72)))
    bpy.context.object.data.energy = 520
    bpy.context.object.data.size = 5
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    bpy.context.scene.camera = camera
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("Review world")
    scene.world.color = (0.16, 0.12, 0.08)
    radius = max(8.0, width * 1.8)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = max(height, width) * margin
    angle_paths = []
    for name, location in {
        "front-left": (-radius, -radius, center.z + height * 0.60),
        "front-right": (radius, -radius, center.z + height * 0.60),
        "back-left": (-radius, radius, center.z + height * 0.60),
        "back-right": (radius, radius, center.z + height * 0.60),
    }.items():
        camera.location = location
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        path = TURNTABLES / f"{prefix}-{name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        angle_paths.append(path)
    town_render.combine_grid(angle_paths, output_path)
    for path in angle_paths:
        path.unlink()


def render_turntables():
    targets = {
        "relay-tower-e7": (LOCAL_MODELS["relay_tower"], 12.5),
        "exchange-e7": (LOCAL_MODELS["exchange"], 8.5),
        "net-cafe-e7": (LOCAL_MODELS["net_cafe"], 8.5),
    }
    for name, (path, _scale) in targets.items():
        render_turntable_smart(path, TURNTABLES / f"{name}.png", name)
    render_turntable_smart(
        TEMP / "atomic_diner.glb", IDENTITY / "atomic-diner-e6.png", "atomic-diner-e6",
    )
    town_render.combine_ab(
        IDENTITY / "atomic-diner-e6.png", TURNTABLES / "net-cafe-e7.png",
        IDENTITY / "net-cafe-identity-e6-e7-ab.png",
    )


def comparison_metrics(base_path, candidate_path):
    base = image_array(base_path)[:, :, :3]
    candidate = image_array(candidate_path)[:, :, :3]
    base_gray = (base[:, :, 0] * 0.2126 + base[:, :, 1] * 0.7152 + base[:, :, 2] * 0.0722) * 255.0
    candidate_gray = (
        candidate[:, :, 0] * 0.2126 + candidate[:, :, 1] * 0.7152 + candidate[:, :, 2] * 0.0722
    ) * 255.0
    difference = np.abs(candidate_gray - base_gray)

    def edge(gray):
        dx = np.zeros_like(gray)
        dy = np.zeros_like(gray)
        dx[:, 1:-1] = (gray[:, 2:] - gray[:, :-2]) * 0.5
        dy[1:-1, :] = (gray[2:, :] - gray[:-2, :]) * 0.5
        return np.sqrt(dx * dx + dy * dy)

    base_edge = edge(base_gray)
    candidate_edge = edge(candidate_gray)
    return {
        "mae": float(difference.mean()),
        "rmse": float(np.sqrt((difference * difference).mean())),
        "diffRatio16": float((difference > 16).mean()),
        "diffRatio32": float((difference > 32).mean()),
        "diffRatio64": float((difference > 64).mean()),
        "thresholdMismatchProxy": "diffRatio16 (pixelmatch unavailable; no dependency installed)",
        "edgeEnergyBase": float(base_edge.mean()),
        "edgeEnergyCandidate": float(candidate_edge.mean()),
        "edgeEnergyRatio": float(candidate_edge.mean() / max(base_edge.mean(), 1e-9)),
        "edgeDiffRatio32": float((np.abs(candidate_edge - base_edge) > 32).mean()),
        "avgLuminanceBase": float(base_gray.mean()),
        "avgLuminanceCandidate": float(candidate_gray.mean()),
        "avgLuminanceDelta": float(candidate_gray.mean() - base_gray.mean()),
    }


def main():
    ensure_directories()
    extract_dependencies()

    current_e1 = REFS / "town-e1-current.png"
    current_e4 = REFS / "town-e4-current.png"
    current_e5 = REFS / "town-e5-current-underwater.png"
    current_wagon = REFS / "e3-e4-current-motor-caravan.png"
    render_e1(current_e1)
    render_e4(current_e4)
    render_e5(current_e5)
    render_e4_wagon(current_wagon)
    annotate(current_e1, "CURRENT E1 TOWN")
    annotate(current_e4, "CURRENT E4 BOULEVARD + MOTOR TOWN")
    annotate(current_e5, "CURRENT E5 SUBMERGED SQUARE")
    annotate(current_wagon, "CURRENT E3 / E4 MOTOR CARAVAN")
    combine_horizontal((current_e1, current_e4, current_e5), REFS / "town-e1-e4-e5-current.png")

    baseline = E6 / "mesa-complete-e6.png"
    candidate = E7 / "mesa-e7-three-building-pilot.png"
    render_mesa(baseline, e7=False)
    render_mesa(candidate, e7=True)
    annotate(baseline, "COMPLETE E6 MESA")
    annotate(candidate, "E7 SIGNAL PILOT — NET CAFE + EXCHANGE + RELAY")
    town_render.combine_ab(baseline, candidate, OUT / "mesa-e7-pilot-across-plaza-ab.png")
    crop_key_features(candidate, OUT / "mesa-e7-pilot-key-feature-crop.png")
    render_turntables()

    contract = {
        "baseSha": BASE_SHA,
        "target": (
            "E7 must read as a signal era on the same Mesa: new pylon and Exchange carry the ensemble, "
            "while the Atomic Diner visibly accretes into a Net Cafe without losing its identity."
        ),
        "freshReferenceRule": "all current-era PNGs rerendered from tracked files on this base; no old PNG input",
        "dependencies": {
            "mesa": {"branchTip": MESA_BRANCH_TIP, "sha256": MESA_GLB_SHA, "usage": "evidence only"},
            "e6Pilot": {"branchTip": PILOT_BRANCH_TIP, "assets": PILOT_ASSETS, "usage": "evidence and inheritance"},
            "e6Wide": {"branchTip": WIDE_BRANCH_TIP, "assets": WIDE_ASSETS, "usage": "evidence only"},
        },
        "placements": {
            "netCafe": "inherited tavern / Atomic Diner site",
            "exchange": [-7.55, 9.40, 0.06],
            "relayTower": [7.55, 9.15, -0.08],
        },
        "comparisonMetrics": comparison_metrics(baseline, candidate),
        "visualReview": {
            "required": "locked A/B, feature crop, three four-angle turntables, Net Cafe identity A/B",
            "independentSubagent": "not run: this session explicitly forbids delegation; limitation recorded",
        },
    }
    (OUT / "visual-evidence-contract.json").write_text(json.dumps(contract, indent=2) + "\n")


if __name__ == "__main__":
    main()
