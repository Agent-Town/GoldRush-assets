from pathlib import Path
import math

import bpy
import numpy as np
from mathutils import Vector


HERE = Path(__file__).resolve().parent
GLB = HERE / "railcar.glb"
OUT = HERE / "renders"
RAIL_GAUGE = 0.78
TIE_SPACING = 0.90
RUN_CAMERA_FOV = 42
RUN_CAMERA_VECTOR = Vector((-1.35, 21.65, 25.75))  # Production sightline plus maximum gameplay look-ahead.
RAIL_HEAD_TOP = 0.125
RAIL_CENTER_Z = 0.08


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name: str, color: tuple[float, float, float, float], roughness: float = 0.85, metallic: float = 0.0) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return mat


def add_box(name: str, size: tuple[float, float, float], at: tuple[float, float, float], mat: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=at)
    obj = bpy.context.object
    obj.name = name
    obj.scale = tuple(value * 0.5 for value in size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def import_railcar(on_rails: bool = False) -> dict[str, bpy.types.Object]:
    bpy.ops.import_scene.gltf(filepath=str(GLB))
    railcar = {obj.name: obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.startswith("Railcar_")}
    if on_rails:
        for obj in railcar.values():
            obj.location.z += RAIL_HEAD_TOP
    return railcar


def add_rail_context() -> None:
    ground_mat = material("Hill Mine painted earth", (0.42, 0.285, 0.145, 1))
    rail_mat = material("Rail iron", (0.055, 0.048, 0.038, 1), 0.58, 0.35)
    tie_mat = material("Sleepers", (0.20, 0.105, 0.042, 1), 0.92)
    add_box("Review ground", (20, 20, 0.08), (0, 0, -0.08), ground_mat)
    for side in (-1, 1):
        add_box(f"Rail {side}", (10, 0.08, 0.09), (0, side * RAIL_GAUGE * 0.5, RAIL_CENTER_Z), rail_mat)
    for index, x in enumerate(np.arange(-4.5, 4.51, TIE_SPACING)):
        add_box(f"Sleeper {index}", (0.22, 1.32, 0.07), (float(x), 0, 0.025), tie_mat)


def setup_scene(resolution: tuple[int, int]) -> bpy.types.Object:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.color_depth = "8"
    scene.world = bpy.data.worlds.new("Warm frontier sky")
    scene.world.color = (0.055, 0.042, 0.028)
    bpy.ops.object.light_add(type="AREA", location=(-3.4, -4.0, 7.0))
    key = bpy.context.object
    key.data.energy = 720
    key.data.shape = "DISK"
    key.data.size = 4.0
    bpy.ops.object.light_add(type="AREA", location=(4.0, 3.0, 4.8))
    fill = bpy.context.object
    fill.data.energy = 330
    fill.data.size = 3.5
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.data.lens = 50
    camera.data.sensor_fit = "VERTICAL"
    scene.camera = camera
    return camera


def aim(camera: bpy.types.Object, location: Vector, target: Vector) -> None:
    camera.location = location
    camera.rotation_euler = (target - location).to_track_quat("-Z", "Y").to_euler()


def render(path: Path) -> None:
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def load_pixels(path: Path) -> np.ndarray:
    image = bpy.data.images.load(str(path), check_existing=False)
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    return pixels.reshape(height, width, 4)


def save_grid(paths: list[Path], output: Path, rows: int, columns: int) -> None:
    images = [load_pixels(path) for path in paths]
    lines = [np.concatenate(images[row * columns:(row + 1) * columns], axis=1) for row in range(rows)]
    grid = np.concatenate(lines, axis=0)
    height, width, _ = grid.shape
    contact = bpy.data.images.new(output.stem, width, height, alpha=True)
    contact.pixels.foreach_set(grid.ravel())
    contact.filepath_raw = str(output)
    contact.file_format = "PNG"
    contact.save()


def render_turntable() -> None:
    reset_scene()
    import_railcar()
    ground = material("Turntable ground", (0.30, 0.20, 0.11, 1))
    add_box("Turntable ground", (8, 8, 0.08), (0, 0, -0.06), ground)
    camera = setup_scene((650, 650))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 3.25
    target = Vector((0, 0, 0.72))
    locations = [
        ("front-left", Vector((-3.2, -3.3, 2.45))),
        ("front-right", Vector((-3.2, 3.3, 2.45))),
        ("rear-left", Vector((3.2, -3.3, 2.45))),
        ("rear-right", Vector((3.2, 3.3, 2.45))),
    ]
    paths = []
    for label, location in locations:
        aim(camera, location, target)
        path = OUT / f"turntable-{label}.png"
        render(path)
        paths.append(path)
    save_grid(paths, OUT / "railcar-turntable.png", 2, 2)
    for path in paths:
        path.unlink()


def render_on_rail() -> None:
    reset_scene()
    import_railcar(on_rails=True)
    add_rail_context()
    camera = setup_scene((1280, 800))
    camera.data.type = "PERSP"
    camera.data.angle = math.radians(RUN_CAMERA_FOV)
    target = Vector((0, 0, 0.68))
    # Exact production sightline, shortened only to give the review render useful pixel coverage.
    location = target + RUN_CAMERA_VECTOR.normalized() * 7.8
    aim(camera, location, target)
    render(OUT / "railcar-on-rail-run-camera.png")


def render_damage_states() -> None:
    reset_scene()
    railcar = import_railcar(on_rails=True)
    add_rail_context()
    camera = setup_scene((540, 540))
    camera.data.type = "PERSP"
    camera.data.angle = math.radians(46)
    target = Vector((0, 0, 0.70))
    aim(camera, Vector((-1.25, 4.1, 3.1)), target)
    states = [
        ("bent-wheels", "Railcar_Wheels", "Damage_BentWheels"),
        ("venting-boiler", "Railcar_Boiler", "Damage_VentingBoiler"),
        ("cracked-cabin", "Railcar_Cabin", "Damage_CrackedCabin"),
    ]
    paths = []
    for label, object_name, key_name in states:
        for obj in railcar.values():
            if obj.data.shape_keys:
                for key in obj.data.shape_keys.key_blocks:
                    if key.name != "Basis":
                        key.value = 0.0
        railcar[object_name].data.shape_keys.key_blocks[key_name].value = 1.0
        path = OUT / f"damage-{label}.png"
        render(path)
        paths.append(path)
    save_grid(paths, OUT / "railcar-damage-states.png", 1, 3)
    for path in paths:
        path.unlink()


def main() -> None:
    OUT.mkdir(exist_ok=True)
    render_turntable()
    render_on_rail()
    render_damage_states()
    print(f"rendered {OUT / 'railcar-turntable.png'}")
    print(f"rendered {OUT / 'railcar-on-rail-run-camera.png'}")
    print(f"rendered {OUT / 'railcar-damage-states.png'}")


if __name__ == "__main__":
    main()
