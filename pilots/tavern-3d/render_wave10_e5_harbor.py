from pathlib import Path
import importlib.util
import json
import math
import subprocess
import sys

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "artifacts/town-e5-harbor"
E4_DIR = OUT / "e4"
E5_DIR = OUT / "e5"
TURNTABLE_DIR = OUT / "turntables"
PROPS = ROOT / "assets/pilots/plaza-props-3d"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


previous = load_module("wave10_previous_render", HERE / "render_wave9_e4_wide.py")
town_render = previous.town_render
town = previous.town
town_render.TURNTABLE_DIR = TURNTABLE_DIR

E4_MODELS = previous.E4_MODELS
E5_MODELS = {
    "tavern": ROOT / "assets/pilots/tavern-3d/tavern.e5.glb",
    "general_store": ROOT / "assets/pilots/general-store-3d/general-store.e5.glb",
    "claim_office": ROOT / "assets/pilots/claim-office-3d/claim-office.e5.glb",
    "assay_office": ROOT / "assets/pilots/assay-office-3d/assay-office.e5.glb",
    "chapel": ROOT / "assets/pilots/chapel-3d/chapel.e5.glb",
    "schoolhouse": ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.e5.glb",
    "stamp-mill": ROOT / "assets/pilots/stamp-mill-3d/stamp-mill.e5.glb",
    "dynamo-hall": ROOT / "assets/pilots/dynamo-hall-3d/dynamo-hall.e5.glb",
}
E5_MANIFEST = json.loads((PROPS / "era-props.e5.json").read_text())


def ensure_directories():
    for directory in (OUT, E4_DIR, E5_DIR, TURNTABLE_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def import_manifest(manifest):
    for descriptor in manifest["props"]:
        position = descriptor["position"]
        town.import_model(
            PROPS / descriptor["glb"], f'RenderEraProp:{descriptor["id"]}',
            town.Point(position["x"], position["z"]), descriptor["rotation"], descriptor["scale"],
        )


def add_town_context(paths, era):
    for slot in [*town.SLOTS, town.DYNAMO_SLOT]:
        town.import_model(paths[slot.id], f"RenderBuilding:{slot.id}", slot.position, town.slot_angle(slot))
    prop_paths = {
        "covered_wagon": PROPS / f"covered_wagon.e{era}.glb",
        "water_trough": PROPS / f"water_trough.e{era}.glb",
        "pan_monument": PROPS / "pan_monument.glb",
    }
    for prop in town.PROPS:
        path = prop_paths.get(prop.kind)
        if path:
            town.import_model(path, f"RenderProp:{prop.id}", prop.position, prop.rotation, prop.scale)
    if era == 4:
        for manifest in previous.MANIFESTS:
            import_manifest(manifest)
    else:
        import_manifest(E5_MANIFEST)


def render_town(paths, era, path, overlay=False, overview=False, underwater=False):
    town.reset_scene()
    town.import_model(ROOT / "assets/pilots/town-plate-3d/town-plate.glb", "RenderTownPlate", town.Point(0, 0))
    add_town_context(paths, era)
    town.setup_render_scene()
    if underwater:
        setup_underwater_scene()
    if overview:
        camera = bpy.context.scene.camera
        camera.location = (0.0, 22.5, 32.5)
        town.look_at(camera, Vector((0.0, -1.0, 0.45)))
    if overlay:
        add_clearance_overlay()
    town.render(path)


def setup_underwater_scene():
    scene = bpy.context.scene
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.07, 0.23, 0.24, 1.0)
    background.inputs["Strength"].default_value = 0.95
    sun = bpy.data.objects.get("EvidenceSun")
    sun.data.color = (0.40, 0.78, 0.80)
    sun.data.energy = 2.75
    fill = bpy.data.objects.get("EvidenceFill")
    fill.data.color = (0.28, 0.62, 0.64)
    fill.data.energy = 1680.0
    # Evidence-only water surface: keep it below the complete town plate so it
    # surrounds the drowned settlement without slicing holes through its relief.
    bpy.ops.mesh.primitive_plane_add(size=90.0, location=(0, 0, -1.50))
    seabed = bpy.context.object
    seabed.name = "EvidenceOnlySeabedContinuation"
    material = bpy.data.materials.new("Evidence only submerged silt")
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (0.08, 0.16, 0.14, 1.0)
    shader.inputs["Roughness"].default_value = 0.96
    seabed.data.materials.append(material)


def add_clearance_overlay():
    route_material = town.emission_material("E5 route overlay", (0.08, 0.78, 0.76, 1), 1.8)
    prop_material = town.emission_material("E5 harbor prop clearance", (0.98, 0.52, 0.10, 1), 1.8)
    town.curve_object("WalkLoop:ring-road", town.RING_ROUTE, route_material, True, 0.10)
    for route_id, points in town.RADIAL_ROUTES.items():
        town.curve_object(f"HeroPath:{route_id}", points, route_material, False, 0.10)
    radii = {
        "harbor-lantern.e5.glb": 0.52, "net-frame.e5.glb": 0.88,
        "tide-board.e5.glb": 0.76, "rope-buoy-rack.e5.glb": 0.96,
    }
    for descriptor in E5_MANIFEST["props"]:
        center = descriptor["position"]
        radius = radii[descriptor["glb"]] * descriptor["scale"]
        points = [
            town.Point(
                center["x"] + math.sin(index / 24 * math.tau) * radius,
                center["z"] + math.cos(index / 24 * math.tau) * radius,
            )
            for index in range(24)
        ]
        town.curve_object(f'Clearance:{descriptor["id"]}', points, prop_material, True, 0.115)


def render_target(target):
    ensure_directories()
    if target == "baseline":
        render_town(E4_MODELS, 4, E4_DIR / "town-e4-baseline.png")
    elif target in E5_MODELS:
        render_town({**E4_MODELS, target: E5_MODELS[target]}, 4, E5_DIR / f"{target}.png")
    elif target == "integrated":
        render_town(E5_MODELS, 5, E5_DIR / "town-e5-harbor.png")
    elif target == "underwater":
        render_town(E5_MODELS, 5, E5_DIR / "town-e5-harbor-underwater.png", underwater=True)
    elif target == "clearance":
        render_town(E5_MODELS, 5, OUT / "e5-accessory-clearance-overlay.png", True, underwater=True)
    elif target == "overview":
        render_town(E5_MODELS, 5, OUT / "town-e5-seabed-overview.png", overview=True, underwater=True)
    else:
        raise ValueError(target)


def render_accessory_pack(path):
    town.reset_scene()
    for index, stem in enumerate((
        "harbor-lantern.e5.glb", "net-frame.e5.glb", "tide-board.e5.glb", "rope-buoy-rack.e5.glb",
    )):
        town_render.import_review_model(PROPS / stem, f"Accessory:{stem}", ((index - 1.5) * 2.45, 1.15, 0))
    town_render.import_review_model(PROPS / "covered_wagon.e5.glb", "Fresh:hauled_dinghy", (-3.0, -1.35, 0), 1.35)
    bpy.data.objects["Fresh:hauled_dinghy"].rotation_euler[2] = math.pi + 0.52
    town_render.import_review_model(PROPS / "pan_monument.glb", "Survivor:pan_monument", (0, -1.35, 0), 1.25)
    town_render.import_review_model(PROPS / "water_trough.e5.glb", "Fresh:freshwater_cistern", (3.0, -1.35, 0), 1.35)
    bpy.data.objects["Fresh:freshwater_cistern"].rotation_euler[2] = math.pi
    town_render.setup_review_scene(path, 12.5)


def save_array(array, output):
    height, width, channels = array.shape
    if channels == 3:
        array = np.concatenate((array, np.ones((height, width, 1), dtype=np.float32)), axis=2)
    image = bpy.data.images.new(output.stem, width, height, alpha=True)
    image.pixels.foreach_set(array.ravel())
    image.filepath_raw = str(output)
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)


def combine_contact(paths, output):
    arrays = [town_render.image_array(path) for path in paths]
    rows = [np.concatenate(arrays[index:index + 2], axis=1) for index in range(0, len(arrays), 2)]
    save_array(np.concatenate(rows, axis=0), output)


def assemble_evidence():
    baseline = E4_DIR / "town-e4-baseline.png"
    integrated = E5_DIR / "town-e5-harbor.png"
    metrics = {"integrated": town_render.comparison_metrics(baseline, integrated)}
    blind_key = {"integrated": {"a": "e5", "b": "e4"}}
    for asset_id in E5_MODELS:
        candidate = E5_DIR / f"{asset_id}.png"
        town_render.combine_ab(baseline, candidate, OUT / f"{asset_id}-town-verdict-e4-e5-ab.png")
        metrics[asset_id] = town_render.comparison_metrics(baseline, candidate)
    town_render.combine_ab(baseline, integrated, OUT / "town-wide-verdict-e4-e5-ab.png")
    town_render.combine_ab(integrated, baseline, OUT / "town-ensemble-blind-pair.png")
    scales = {
        "tavern": 6.2, "general_store": 6.6, "claim_office": 6.6, "assay_office": 6.4,
        "chapel": 8.2, "schoolhouse": 7.2, "stamp-mill": 7.0, "dynamo-hall": 7.2,
    }
    e5_sheets = []
    for asset_id, scale in scales.items():
        e4_sheet = TURNTABLE_DIR / f"{asset_id}-e4.png"
        e5_sheet = TURNTABLE_DIR / f"{asset_id}-e5.png"
        town_render.render_turntable(E4_MODELS[asset_id], e4_sheet, f"{asset_id}-e4", scale)
        town_render.render_turntable(E5_MODELS[asset_id], e5_sheet, f"{asset_id}-e5", scale)
        town_render.combine_ab(e4_sheet, e5_sheet, OUT / f"{asset_id}-turntable-e4-e5-ab.png")
        e5_sheets.append(e5_sheet)
    combine_contact(e5_sheets, OUT / "all-buildings-e5-turntable-contact.png")
    render_accessory_pack(OUT / "accessory-pack-and-pan-survivor-e5.png")
    (OUT / "comparison-metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (OUT / "blind-key.json").write_text(json.dumps(blind_key, indent=2) + "\n")


def main():
    ensure_directories()
    if "--" in sys.argv:
        target = sys.argv[sys.argv.index("--") + 1]
        if target == "evidence":
            assemble_evidence()
        else:
            render_target(target)
        return
    for target in ("baseline", *E5_MODELS, "integrated", "underwater", "clearance", "overview"):
        subprocess.run(
            [bpy.app.binary_path, "--background", "--python", str(Path(__file__).resolve()), "--", target],
            check=True, stdout=subprocess.DEVNULL,
        )
    assemble_evidence()


if __name__ == "__main__":
    main()
