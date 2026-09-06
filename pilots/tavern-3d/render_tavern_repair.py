from pathlib import Path
import importlib.util
import math
import sys

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
CANDIDATE = HERE / "town-v3-tavern.glb"
PLATE_BUILD = ROOT / "assets/pilots/town-plate-3d/build_town_plate.py"

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("town_plate_build", PLATE_BUILD)
town = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = town
spec.loader.exec_module(town)


def add_context_models(tavern_path: Path) -> None:
    paths = {
        "tavern": tavern_path,
        "general_store": ROOT / "assets/pilots/general-store-3d/general-store.glb",
        "claim_office": ROOT / "assets/pilots/claim-office-3d/claim-office.glb",
        "assay_office": ROOT / "assets/pilots/assay-office-3d/assay-office.glb",
        "chapel": ROOT / "assets/pilots/chapel-3d/chapel.glb",
        "schoolhouse": ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.glb",
        "stamp-mill": ROOT / "assets/pilots/stamp-mill-3d/stamp-mill.glb",
        "dynamo-hall": ROOT / "assets/pilots/dynamo-hall-3d/dynamo-hall.glb",
    }
    for slot in [*town.SLOTS, town.DYNAMO_SLOT]:
        town.import_model(paths[slot.id], f"RenderBuilding:{slot.id}", slot.position, town.slot_angle(slot))
    prop_paths = {
        "covered_wagon": ROOT / "assets/pilots/plaza-props-3d/covered_wagon.glb",
        "water_trough": ROOT / "assets/pilots/plaza-props-3d/water_trough.glb",
        "pan_monument": ROOT / "assets/pilots/plaza-props-3d/pan_monument.glb",
    }
    for prop in town.PROPS:
        path = prop_paths.get(prop.kind)
        if path:
            town.import_model(path, f"RenderProp:{prop.id}", prop.position, prop.rotation, prop.scale)


def render_town_detail(tavern_path: Path, detail_path: Path) -> None:
    town.reset_scene()
    town.import_model(ROOT / "assets/pilots/town-plate-3d/town-plate.glb", "RenderTownPlate", town.Point(0, 0))
    add_context_models(tavern_path)
    camera = town.setup_render_scene()
    town.render_focus(camera, Vector((-8.4, -5.5, 1.0)), 9.2, detail_path, (980, 720))


def combine_grid(paths: list[Path], output: Path) -> None:
    images = [bpy.data.images.load(str(path), check_existing=False) for path in paths]
    width, height = images[0].size
    arrays = []
    for image in images:
        pixels = np.empty(width * height * 4, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        arrays.append(pixels.reshape(height, width, 4))
    grid = np.concatenate((np.concatenate(arrays[2:], axis=1), np.concatenate(arrays[:2], axis=1)), axis=0)
    contact = bpy.data.images.new("TavernWave3Turntable", width * 2, height * 2, alpha=True)
    contact.pixels.foreach_set(grid.ravel())
    contact.filepath_raw = str(output)
    contact.file_format = "PNG"
    contact.save()


def render_turntable(asset_path: Path, output_path: Path, prefix: str) -> None:
    if asset_path.suffix != ".glb":
        raise ValueError(f"turntable evidence requires a production GLB: {asset_path}")
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
        camera.data.ortho_scale = 6.2
        path = OUT / f"{prefix}-{name}.png"
        bpy.context.scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        angle_paths.append(path)
    combine_grid(angle_paths, output_path)
    for path in angle_paths:
        path.unlink()


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    accepted = Path(args[0]) if args else Path("/tmp/town-v3-tavern-wave3-accepted.glb")
    if not accepted.exists():
        raise FileNotFoundError(f"accepted pre-polish GLB missing: {accepted}")
    OUT.mkdir(exist_ok=True)
    current_detail = OUT / "wave3-current-detail-ts04.png"
    repaired_detail = OUT / "wave3-repaired-detail-ts04.png"
    render_town_detail(accepted, current_detail)
    render_town_detail(CANDIDATE, repaired_detail)
    town.combine_ab(current_detail, repaired_detail, OUT / "wave3-detail-ab.png")
    current_detail.unlink()
    repaired_detail.unlink()
    baseline_turntable = OUT / "wave3-before-polish-turntable.png"
    current_turntable = OUT / "wave3-turntable.png"
    render_turntable(accepted, baseline_turntable, "wave3-before-polish")
    render_turntable(CANDIDATE, current_turntable, "wave3-after-polish")
    town.combine_ab(baseline_turntable, current_turntable, OUT / "wave3-angle-polish-ab.png")
    baseline_turntable.unlink()


if __name__ == "__main__":
    main()
