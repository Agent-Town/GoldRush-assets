from pathlib import Path
import json
import math

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
GLB = HERE / "dredge-queen.glb"
REFERENCE = ROOT / "assets/raw/boss-dredge-queen.png"
DAMAGE_REFERENCE = ROOT / "assets/raw/boss-dredge-queen-damage.png"
TERRAIN = ROOT / "assets/pilots/map-rebuild-spike/deepwater-claim-terrain.glb"
OUT = HERE / "renders"
RUN_CAMERA_FOV = 48
RUN_CAMERA_OFFSET = Vector((0.0, 57.0, 39.5))
COMPONENTS = {
    "claw": "Damage_SlackClaw",
    "paddle_port": "Damage_BrokenPortPaddle",
    "paddle_starboard": "Damage_BrokenStarboardPaddle",
    "hold": "Damage_CrackedLootHold",
}


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(
    name: str,
    color: tuple[float, float, float, float],
    roughness: float = 0.88,
    metallic: float = 0.0,
    alpha: float = 1.0,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color[:3], alpha)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color[:3], 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Alpha"].default_value = alpha
    if alpha < 1.0:
        mat.surface_render_method = "DITHERED"
    return mat


def add_box(name: str, size: tuple[float, float, float], at: tuple[float, float, float], mat: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=at)
    obj = bpy.context.object
    obj.name = name
    obj.scale = tuple(value * 0.5 for value in size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def import_dredge_queen() -> dict[str, bpy.types.Object]:
    bpy.ops.import_scene.gltf(filepath=str(GLB))
    objects = {obj.name: obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name in COMPONENTS}
    assert set(objects) == set(COMPONENTS), objects.keys()
    return objects


def setup_scene(resolution: tuple[int, int], center: Vector | None = None) -> bpy.types.Object:
    center = center or Vector((0.0, 0.0, 0.0))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    world = bpy.data.worlds.new("Dredge Queen review world")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.018, 0.031, 0.033, 1)
    background.inputs["Strength"].default_value = 0.32
    bpy.ops.object.light_add(type="AREA", location=center + Vector((-8.0, -7.0, 12.0)))
    key = bpy.context.object
    key.data.energy = 2100
    key.data.color = (1.0, 0.62, 0.30)
    key.data.shape = "DISK"
    key.data.size = 7.0
    bpy.ops.object.light_add(type="AREA", location=center + Vector((8.0, 6.0, 8.0)))
    fill = bpy.context.object
    fill.data.energy = 1650
    fill.data.color = (0.12, 0.60, 0.64)
    fill.data.size = 6.0
    bpy.ops.object.light_add(type="AREA", location=center + Vector((0.0, 2.0, 14.0)))
    top = bpy.context.object
    top.data.energy = 1300
    top.data.color = (1.0, 0.82, 0.56)
    top.data.size = 8.0
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
    array = pixels.reshape(height, width, 4)
    bpy.data.images.remove(image)
    return array


def fitted_pixels(path: Path, width: int, height: int) -> np.ndarray:
    source = load_pixels(path)
    source_height, source_width, _ = source.shape
    scale = min(width / source_width, height / source_height)
    resized_width = max(1, int(round(source_width * scale)))
    resized_height = max(1, int(round(source_height * scale)))
    xs = np.linspace(0, source_width - 1, resized_width).astype(np.int32)
    ys = np.linspace(0, source_height - 1, resized_height).astype(np.int32)
    resized = source[ys[:, None], xs[None, :]]
    canvas = np.ones((height, width, 4), dtype=np.float32)
    canvas[:, :, :3] = (0.035, 0.044, 0.041)
    x0 = (width - resized_width) // 2
    y0 = (height - resized_height) // 2
    canvas[y0:y0 + resized_height, x0:x0 + resized_width] = resized
    return canvas


def save_pixels(pixels: np.ndarray, path: Path) -> None:
    height, width, _ = pixels.shape
    image = bpy.data.images.new(path.stem, width, height, alpha=True)
    image.pixels.foreach_set(pixels.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)


def save_grid(paths: list[Path], output: Path, rows: int, columns: int) -> None:
    images = [load_pixels(path) for path in paths]
    lines = [np.concatenate(images[row * columns:(row + 1) * columns], axis=1) for row in range(rows)]
    save_pixels(np.concatenate(lines, axis=0), output)


def save_reference_ab(reference: Path, render_path: Path, output: Path) -> None:
    left = fitted_pixels(reference, 960, 540)
    right = fitted_pixels(render_path, 960, 540)
    divider = np.ones((540, 6, 4), dtype=np.float32)
    divider[:, :, :3] = (0.50, 0.32, 0.11)
    save_pixels(np.concatenate((left, divider, right), axis=1), output)


def damage_metrics(intact_path: Path, damaged_path: Path) -> dict[str, float]:
    intact = load_pixels(intact_path)[:, :, :3]
    damaged = load_pixels(damaged_path)[:, :, :3]
    intact_gray = intact @ np.array((0.2126, 0.7152, 0.0722), dtype=np.float32)
    damaged_gray = damaged @ np.array((0.2126, 0.7152, 0.0722), dtype=np.float32)
    delta = np.abs(damaged_gray - intact_gray) * 255.0

    def edge_energy(gray: np.ndarray) -> float:
        dx = np.abs(np.diff(gray, axis=1)).mean()
        dy = np.abs(np.diff(gray, axis=0)).mean()
        return float((dx + dy) * 255.0)

    return {
        "maeGray8": float(delta.mean()),
        "rmseGray8": float(np.sqrt(np.square(delta).mean())),
        "diffRatio16": float((delta > 16.0).mean()),
        "diffRatio32": float((delta > 32.0).mean()),
        "diffRatio64": float((delta > 64.0).mean()),
        "avgLuminanceIntact8": float(intact_gray.mean() * 255.0),
        "avgLuminanceAct3_8": float(damaged_gray.mean() * 255.0),
        "edgeEnergyIntact": edge_energy(intact_gray),
        "edgeEnergyAct3": edge_energy(damaged_gray),
    }


def set_all_morphs(objects: dict[str, bpy.types.Object], value: float = 0.0) -> None:
    for obj in objects.values():
        if not obj.data.shape_keys:
            continue
        for key in obj.data.shape_keys.key_blocks:
            if key.name != "Basis":
                key.value = value


def render_turntable() -> None:
    reset_scene()
    import_dredge_queen()
    water = material("Turntable deepwater", (0.045, 0.18, 0.19, 1), 0.72)
    add_box("Turntable water", (15, 15, 0.10), (0, 0, -0.08), water)
    camera = setup_scene((640, 640))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 10.0
    target = Vector((0, 0, 2.05))
    views = [
        ("bow-port", Vector((-10.0, -10.0, 7.2))),
        ("bow-starboard", Vector((-10.0, 10.0, 7.2))),
        ("stern-port", Vector((10.0, -10.0, 7.2))),
        ("stern-starboard", Vector((10.0, 10.0, 7.2))),
    ]
    paths: list[Path] = []
    for label, location in views:
        aim(camera, location, target)
        path = OUT / f"turntable-{label}.png"
        render(path)
        paths.append(path)
    save_grid(paths, OUT / "dredge-queen-turntable.png", 2, 2)
    for path in paths:
        path.unlink()


def add_deepwater_context() -> None:
    bpy.ops.import_scene.gltf(filepath=str(TERRAIN))
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and obj.name not in COMPONENTS:
            obj.name = f"Context:{obj.name}"
    water = material("Deepwater surface", (0.025, 0.20, 0.22, 1), 0.62, alpha=0.72)
    add_box("Context:water surface", (128, 128, 0.08), (0, 0, 0.02), water)
    buoy_brass = material("Context buoy brass", (0.32, 0.16, 0.045, 1), 0.82)
    buoy_teal = material("Context buoy teal", (0.02, 0.38, 0.40, 1), 0.68)
    for index, (x, y) in enumerate(((31.0, -14.0), (42.0, -13.0), (44.0, -27.0), (30.0, -28.0))):
        bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=0.34, radius2=0.18, depth=0.74, location=(x, y, 0.36))
        buoy = bpy.context.object
        buoy.name = f"Context buoy {index}"
        buoy.data.materials.append(buoy_brass)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=0.16, location=(x, y, 0.82))
        lamp = bpy.context.object
        lamp.name = f"Context buoy lamp {index}"
        lamp.data.materials.append(buoy_teal)


def render_on_tile() -> None:
    reset_scene()
    objects = import_dredge_queen()
    boss = Vector((36.0, -20.0, 0.0))
    for obj in objects.values():
        obj.location = boss
    add_deepwater_context()
    camera = setup_scene((1280, 800), boss)
    camera.data.type = "PERSP"
    camera.data.angle = math.radians(RUN_CAMERA_FOV)
    target = boss + Vector((0.0, 0.0, 1.75))
    location = target + RUN_CAMERA_OFFSET.normalized() * 17.0
    aim(camera, location, target)
    path = OUT / "dredge-queen-deepwater-run-camera.png"
    render(path)
    save_reference_ab(REFERENCE, path, OUT / "dredge-queen-reference-ab.png")


def render_damage_states() -> None:
    reset_scene()
    objects = import_dredge_queen()
    water = material("Damage review water", (0.04, 0.17, 0.18, 1), 0.74)
    add_box("Damage water", (15, 15, 0.10), (0, 0, -0.08), water)
    camera = setup_scene((640, 520))
    camera.data.type = "PERSP"
    camera.data.angle = math.radians(47)
    views = {
        "claw": (Vector((-1.0, 12.4, 8.4)), Vector((-2.35, 0.0, 2.15))),
        "paddle_port": (Vector((0.0, -12.4, 8.2)), Vector((1.20, -1.25, 1.55))),
        "paddle_starboard": (Vector((0.0, 12.4, 8.2)), Vector((1.20, 1.25, 1.55))),
        "hold": (Vector((10.8, 9.2, 7.8)), Vector((1.55, 0.0, 2.05))),
    }
    paths: list[Path] = []
    for node, morph in COMPONENTS.items():
        set_all_morphs(objects, 0.0)
        objects[node].data.shape_keys.key_blocks[morph].value = 1.0
        location, target = views[node]
        aim(camera, location, target)
        path = OUT / f"damage-{node}.png"
        render(path)
        paths.append(path)
    save_grid(paths, OUT / "dredge-queen-damage-states.png", 2, 2)
    for path in paths:
        path.unlink()

    aim(camera, Vector((10.8, 9.2, 7.8)), Vector((0.7, 0.0, 1.85)))
    set_all_morphs(objects, 0.0)
    intact = OUT / "dredge-queen-act3-camera-intact.png"
    render(intact)
    set_all_morphs(objects, 1.0)
    act3 = OUT / "dredge-queen-act3.png"
    render(act3)
    save_grid([intact, act3], OUT / "dredge-queen-intact-act3.png", 1, 2)
    metrics = damage_metrics(intact, act3)
    metrics["target"] = "same-camera Act 3 keeps the barge identity while the claw hangs low, both paddles drop, the hold opens, cargo spills, and the sail strikes"
    (OUT / "dredge-queen-damage-metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    save_reference_ab(DAMAGE_REFERENCE, act3, OUT / "dredge-queen-act3-reference-ab.png")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    render_turntable()
    render_on_tile()
    render_damage_states()
    print(f"rendered {OUT / 'dredge-queen-turntable.png'}")
    print(f"rendered {OUT / 'dredge-queen-deepwater-run-camera.png'}")
    print(f"rendered {OUT / 'dredge-queen-damage-states.png'}")
    print(f"rendered {OUT / 'dredge-queen-intact-act3.png'}")
    print(f"rendered {OUT / 'dredge-queen-reference-ab.png'}")
    print(f"rendered {OUT / 'dredge-queen-act3-reference-ab.png'}")


if __name__ == "__main__":
    main()
