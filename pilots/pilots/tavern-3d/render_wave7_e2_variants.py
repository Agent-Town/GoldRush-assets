from pathlib import Path
import importlib.util
import json
import math
import sys

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "artifacts/town-e2-variants"
BASE_DIR = OUT / "base"
E2_DIR = OUT / "e2"
TURNTABLE_DIR = OUT / "turntables"
PLATE_BUILD = ROOT / "assets/pilots/town-plate-3d/build_town_plate.py"

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("town_plate_build", PLATE_BUILD)
town = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = town
spec.loader.exec_module(town)


BASE_MODELS = {
    "tavern": ROOT / "assets/pilots/tavern-3d/town-v3-tavern.glb",
    "general_store": ROOT / "assets/pilots/general-store-3d/general-store.glb",
    "claim_office": ROOT / "assets/pilots/claim-office-3d/claim-office.glb",
    "assay_office": ROOT / "assets/pilots/assay-office-3d/assay-office.glb",
    "chapel": ROOT / "assets/pilots/chapel-3d/chapel.glb",
    "schoolhouse": ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.glb",
    "stamp-mill": ROOT / "assets/pilots/stamp-mill-3d/stamp-mill.glb",
    "dynamo-hall": ROOT / "assets/pilots/dynamo-hall-3d/dynamo-hall.glb",
}
E2_MODELS = {
    "tavern": ROOT / "assets/pilots/tavern-3d/tavern.e2.glb",
    "general_store": ROOT / "assets/pilots/general-store-3d/general-store.e2.glb",
    "claim_office": ROOT / "assets/pilots/claim-office-3d/claim-office.e2.glb",
    "assay_office": ROOT / "assets/pilots/assay-office-3d/assay-office.e2.glb",
    "chapel": ROOT / "assets/pilots/chapel-3d/chapel.e2.glb",
    "schoolhouse": ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.e2.glb",
    "stamp-mill": ROOT / "assets/pilots/stamp-mill-3d/stamp-mill.e2.glb",
    "dynamo-hall": ROOT / "assets/pilots/dynamo-hall-3d/dynamo-hall.e2.glb",
}
PROP_DIR = ROOT / "assets/pilots/plaza-props-3d"
MANIFEST = json.loads((PROP_DIR / "era-props.e2.json").read_text())


def add_context_models(overrides, e2_props=False, accessories=False):
    paths = {**BASE_MODELS, **overrides}
    for slot in [*town.SLOTS, town.DYNAMO_SLOT]:
        town.import_model(paths[slot.id], f"RenderBuilding:{slot.id}", slot.position, town.slot_angle(slot))
    prop_paths = {
        "covered_wagon": PROP_DIR / ("covered_wagon.e2.glb" if e2_props else "covered_wagon.glb"),
        "water_trough": PROP_DIR / ("water_trough.e2.glb" if e2_props else "water_trough.glb"),
        "pan_monument": PROP_DIR / "pan_monument.glb",
    }
    for prop in town.PROPS:
        path = prop_paths.get(prop.kind)
        if path:
            town.import_model(path, f"RenderProp:{prop.id}", prop.position, prop.rotation, prop.scale)
    if accessories:
        for descriptor in MANIFEST["props"]:
            position = descriptor["position"]
            town.import_model(
                PROP_DIR / descriptor["glb"], f'RenderEraProp:{descriptor["id"]}',
                town.Point(position["x"], position["z"]), descriptor["rotation"], descriptor["scale"],
            )


def add_clearance_overlay():
    route_material = town.emission_material("Wave7b route overlay", (0.08, 0.78, 0.76, 1), 1.8)
    footprint_material = town.emission_material("Wave7b prop clearance", (0.96, 0.54, 0.10, 1), 1.8)
    town.curve_object("WalkLoop:ring-road", town.RING_ROUTE, route_material, True, 0.10)
    for route_id, points in town.RADIAL_ROUTES.items():
        town.curve_object(f"HeroPath:{route_id}", points, route_material, False, 0.10)
    radii = {
        "coal-bin.e2.glb": 0.65, "pipe-run.e2.glb": 1.05, "gauge-post.e2.glb": 0.42,
        "iron-lamp-post.e2.glb": 0.65, "pressure-manifold.e2.glb": 0.82,
    }
    for descriptor in MANIFEST["props"]:
        center = descriptor["position"]
        radius = radii[descriptor["glb"]] * descriptor["scale"]
        points = [
            town.Point(center["x"] + math.sin(index / 24 * math.tau) * radius,
                       center["z"] + math.cos(index / 24 * math.tau) * radius)
            for index in range(24)
        ]
        town.curve_object(f'Clearance:{descriptor["id"]}', points, footprint_material, True, 0.115)


def render_town(overrides, path, e2_props=False, accessories=False, overlay=False):
    town.reset_scene()
    town.import_model(ROOT / "assets/pilots/town-plate-3d/town-plate.glb", "RenderTownPlate", town.Point(0, 0))
    add_context_models(overrides, e2_props, accessories)
    town.setup_render_scene()
    if overlay:
        add_clearance_overlay()
    town.render(path)


def setup_review_scene(path, ortho_scale=11.0):
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.015))
    ground = bpy.context.object
    ground.data.materials.append(bpy.data.materials.new("Review ground"))
    ground.data.materials[0].diffuse_color = (0.48, 0.35, 0.20, 1)
    bpy.ops.object.light_add(type="AREA", location=(-6, -8, 11))
    bpy.context.object.data.energy = 1250
    bpy.context.object.data.size = 7
    bpy.ops.object.light_add(type="AREA", location=(7, 4, 6))
    bpy.context.object.data.energy = 480
    bpy.context.object.data.size = 5
    bpy.ops.object.camera_add(location=(0, -12, 8.5))
    camera = bpy.context.object
    camera.rotation_euler = (Vector((0, 0, 1.0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho_scale
    bpy.context.scene.camera = camera
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("Review world")
    scene.world.color = (0.16, 0.12, 0.08)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def import_review_model(path, name, position, scale=1.0):
    bpy.ops.import_scene.gltf(filepath=str(path))
    roots = [obj for obj in bpy.context.selected_objects if obj.parent is None]
    for root in roots:
        root.name = name
        root.location = position
        root.scale = (scale, scale, scale)


def render_accessory_pack(path):
    town.reset_scene()
    top = ["coal-bin.e2.glb", "pipe-run.e2.glb", "gauge-post.e2.glb",
           "iron-lamp-post.e2.glb", "pressure-manifold.e2.glb"]
    for index, stem in enumerate(top):
        import_review_model(PROP_DIR / stem, f"Accessory:{stem}", ((index - 2) * 2.0, 1.1, 0))
    import_review_model(PROP_DIR / "covered_wagon.e2.glb", "Variant:covered_wagon", (-1.7, -1.2, 0))
    import_review_model(PROP_DIR / "water_trough.e2.glb", "Variant:water_trough", (1.7, -1.2, 0))
    setup_review_scene(path, 11.2)


def render_prop_variants(path):
    town.reset_scene()
    for x, stem in ((-3.2, "covered_wagon.glb"), (-1.0, "covered_wagon.e2.glb"),
                    (1.4, "water_trough.glb"), (3.5, "water_trough.e2.glb")):
        import_review_model(PROP_DIR / stem, f"PropAB:{stem}", (x, 0, 0), 1.25)
    setup_review_scene(path, 10.0)


def combine_grid(paths, output):
    images = [bpy.data.images.load(str(path), check_existing=False) for path in paths]
    width, height = images[0].size
    arrays = []
    for image in images:
        pixels = np.empty(width * height * 4, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        arrays.append(pixels.reshape(height, width, 4))
    grid = np.concatenate((np.concatenate(arrays[2:], axis=1), np.concatenate(arrays[:2], axis=1)), axis=0)
    contact = bpy.data.images.new(output.stem, width * 2, height * 2, alpha=True)
    contact.pixels.foreach_set(grid.ravel())
    contact.filepath_raw = str(output)
    contact.file_format = "PNG"
    contact.save()
    for image in images:
        bpy.data.images.remove(image)
    bpy.data.images.remove(contact)


def combine_ab(left_path, right_path, output_path):
    images = [bpy.data.images.load(str(path), check_existing=False) for path in (left_path, right_path)]
    width, height = images[0].size
    if tuple(images[1].size) != (width, height):
        raise RuntimeError("A/B render sizes differ")
    arrays = []
    for image in images:
        pixels = np.empty(width * height * 4, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        arrays.append(pixels.reshape(height, width, 4))
    combined = np.concatenate(arrays, axis=1)
    contact = bpy.data.images.new(output_path.stem, width * 2, height, alpha=True)
    contact.pixels.foreach_set(combined.ravel())
    contact.filepath_raw = str(output_path)
    contact.file_format = "PNG"
    contact.save()
    for image in images:
        bpy.data.images.remove(image)
    bpy.data.images.remove(contact)


def render_turntable(asset_path, output_path, prefix, ortho_scale):
    town.reset_scene()
    bpy.ops.import_scene.gltf(filepath=str(asset_path))
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -0.015))
    ground = bpy.context.object
    ground.data.materials.append(bpy.data.materials.new("Review ground"))
    ground.data.materials[0].diffuse_color = (0.48, 0.35, 0.20, 1)
    bpy.ops.object.light_add(type="AREA", location=(-5, -6, 9))
    bpy.context.object.data.energy = 1100
    bpy.context.object.data.shape = "DISK"
    bpy.context.object.data.size = 5
    bpy.ops.object.light_add(type="AREA", location=(6, 4, 5))
    bpy.context.object.data.energy = 500
    bpy.context.object.data.size = 4
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    bpy.context.scene.camera = camera
    bpy.context.scene.render.engine = "BLENDER_EEVEE"
    bpy.context.scene.render.resolution_x = 720
    bpy.context.scene.render.resolution_y = 720
    bpy.context.scene.render.resolution_percentage = 100
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.world = bpy.data.worlds.new("Review world")
    bpy.context.scene.world.color = (0.16, 0.12, 0.08)

    angle_paths = []
    for name, location in {
        "front-left": (-7.2, -8.0, 6.1),
        "front-right": (7.2, -8.0, 6.1),
        "back-left": (-7.2, 8.0, 6.1),
        "back-right": (7.2, 8.0, 6.1),
    }.items():
        camera.location = location
        camera.rotation_euler = (Vector((0, 0, 2.0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.type = "ORTHO"
        camera.data.ortho_scale = ortho_scale
        path = TURNTABLE_DIR / f"{prefix}-{name}.png"
        bpy.context.scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        angle_paths.append(path)
    combine_grid(angle_paths, output_path)
    for path in angle_paths:
        path.unlink()


def image_array(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    array = pixels.reshape(height, width, 4)[:, :, :3]
    bpy.data.images.remove(image)
    return array


def comparison_metrics(base_path, candidate_path):
    base = image_array(base_path)
    candidate = image_array(candidate_path)
    base_gray = (base[:, :, 0] * 0.2126 + base[:, :, 1] * 0.7152 + base[:, :, 2] * 0.0722) * 255.0
    candidate_gray = (candidate[:, :, 0] * 0.2126 + candidate[:, :, 1] * 0.7152 + candidate[:, :, 2] * 0.0722) * 255.0
    difference = np.abs(candidate_gray - base_gray)

    def edge(gray):
        dx = np.zeros_like(gray)
        dy = np.zeros_like(gray)
        dx[:, 1:-1] = (gray[:, 2:] - gray[:, :-2]) * 0.5
        dy[1:-1, :] = (gray[2:, :] - gray[:-2, :]) * 0.5
        return np.sqrt(dx * dx + dy * dy)

    base_edge = edge(base_gray)
    candidate_edge = edge(candidate_gray)
    edge_difference = np.abs(candidate_edge - base_edge)
    edge_ratio = float(candidate_edge.mean() / max(base_edge.mean(), 1e-9))
    diff16 = float((difference > 16).mean())
    diff32 = float((difference > 32).mean())
    edge_diff32 = float((edge_difference > 32).mean())
    # The repo does not carry pixelmatch; diff16 is retained as the explicit
    # threshold mismatch proxy instead of installing a task-only dependency.
    distance = (
        0.35 * diff32
        + 0.25 * diff16
        + 0.25 * edge_diff32
        + 0.15 * min(1.0, abs(math.log2(max(edge_ratio, 1e-9))))
    )
    return {
        "mae": float(difference.mean()),
        "rmse": float(np.sqrt((difference * difference).mean())),
        "diffRatio16": diff16,
        "diffRatio32": diff32,
        "diffRatio64": float((difference > 64).mean()),
        "thresholdMismatchProxy": "diffRatio16 (pixelmatch unavailable; no dependency installed)",
        "edgeEnergyBase": float(base_edge.mean()),
        "edgeEnergyCandidate": float(candidate_edge.mean()),
        "edgeEnergyRatio": edge_ratio,
        "edgeDiffRatio32": edge_diff32,
        "avgLuminanceBase": float(base_gray.mean()),
        "avgLuminanceCandidate": float(candidate_gray.mean()),
        "avgLuminanceDelta": float(candidate_gray.mean() - base_gray.mean()),
        "diagnosticDistance": distance,
    }


def main():
    for directory in (OUT, BASE_DIR, E2_DIR, TURNTABLE_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    base_path = BASE_DIR / "town-all.png"
    render_town({}, base_path)
    for target_id in BASE_MODELS:
        e2_path = E2_DIR / f"{target_id}.png"
        render_town({target_id: E2_MODELS[target_id]}, e2_path)
        combine_ab(base_path, e2_path, OUT / f"{target_id}-town-ab.png")

    all_e2 = E2_DIR / "town-all-wave7b.png"
    render_town(E2_MODELS, all_e2, e2_props=True, accessories=True)
    combine_ab(base_path, all_e2, OUT / "town-all-wave7b-ab.png")
    render_town(E2_MODELS, OUT / "wave7b-clearance-overlay.png", e2_props=True, accessories=True, overlay=True)
    render_accessory_pack(OUT / "accessory-pack-e2.png")
    render_prop_variants(OUT / "prop-variants-e1-e2.png")

    ortho_scales = {
        "tavern": 6.2, "general_store": 6.6, "claim_office": 6.6, "assay_office": 6.4,
        "chapel": 7.2, "schoolhouse": 7.0, "stamp-mill": 7.0, "dynamo-hall": 7.2,
    }
    for target_id, ortho_scale in ortho_scales.items():
        base_sheet = TURNTABLE_DIR / f"{target_id}-e1.png"
        e2_sheet = TURNTABLE_DIR / f"{target_id}-e2.png"
        render_turntable(BASE_MODELS[target_id], base_sheet, f"{target_id}-e1", ortho_scale)
        render_turntable(E2_MODELS[target_id], e2_sheet, f"{target_id}-e2", ortho_scale)
        combine_ab(base_sheet, e2_sheet, OUT / f"{target_id}-turntable-ab.png")

    metrics = {target_id: comparison_metrics(base_path, E2_DIR / f"{target_id}.png") for target_id in BASE_MODELS}
    metrics["integrated"] = comparison_metrics(base_path, all_e2)
    (OUT / "comparison-metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")


if __name__ == "__main__":
    main()
