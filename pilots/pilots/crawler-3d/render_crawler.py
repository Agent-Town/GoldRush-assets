from pathlib import Path
import math

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
GLB = HERE / "crawler.glb"
REFERENCE = ROOT / "assets/raw/plate-e3-boss-dynamo-crawler.png"
CANYON_ATLAS = ROOT / "assets/raw/ter-canyon-atlas.png"
HERO_FRAME = ROOT / "assets/processed/char-hero-sheet-attack8-r2c0.png"
OUT = HERE / "renders"
RUN_CAMERA_FOV = 42
RUN_CAMERA_VECTOR = Vector((0.0, 26.2, 18.3))
COMPONENTS = {
    "drain_mast": "Damage_ToppledDrainMast",
    "tracks": "Damage_ShatteredTracks",
    "capacitor_bank": "Damage_RupturedCapacitorBank",
}


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(
    name: str,
    color: tuple[float, float, float, float],
    roughness: float = 0.88,
    metallic: float = 0.0,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return mat


def canyon_material(
    name: str,
    quadrant: str,
    roughness: float = 0.90,
    scale: float = 5.0,
    saturation: float = 1.0,
    value: float = 1.0,
) -> bpy.types.Material:
    source = bpy.data.images.get("CanyonWorksAtlasSource")
    if source is None:
        source = bpy.data.images.load(str(CANYON_ATLAS), check_existing=False)
        source.name = "CanyonWorksAtlasSource"
    pixels = np.empty(source.size[0] * source.size[1] * 4, dtype=np.float32)
    source.pixels.foreach_get(pixels)
    pixels = pixels.reshape(source.size[1], source.size[0], 4)
    half_y, half_x = source.size[1] // 2, source.size[0] // 2
    slices = {
        "river": (slice(half_y, source.size[1]), slice(0, half_x)),
        "slate": (slice(half_y, source.size[1]), slice(half_x, source.size[0])),
        "concrete": (slice(0, half_y), slice(0, half_x)),
        "grass": (slice(0, half_y), slice(half_x, source.size[0])),
    }
    ys, xs = slices[quadrant]
    crop = pixels[ys, xs]
    image = bpy.data.images.new(f"{name}Image", crop.shape[1], crop.shape[0], alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(crop.ravel())
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader = nodes.get("Principled BSDF")
    texture = nodes.new("ShaderNodeTexImage")
    coordinates = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    hue = nodes.new("ShaderNodeHueSaturation")
    texture.image = image
    texture.interpolation = "Linear"
    texture.extension = "REPEAT"
    shader.inputs["Roughness"].default_value = roughness
    mapping.inputs["Scale"].default_value = (scale, scale, scale)
    hue.inputs["Saturation"].default_value = saturation
    hue.inputs["Value"].default_value = value
    links.new(coordinates.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], texture.inputs["Vector"])
    links.new(texture.outputs["Color"], hue.inputs["Color"])
    links.new(hue.outputs["Color"], shader.inputs["Base Color"])
    return mat


def add_hero_sprite(at: tuple[float, float, float], height: float = 1.45, mirror: bool = False) -> bpy.types.Object:
    source = bpy.data.images.load(str(HERO_FRAME), check_existing=False)
    pixels = np.empty(source.size[0] * source.size[1] * 4, dtype=np.float32)
    source.pixels.foreach_get(pixels)
    pixels = pixels.reshape(source.size[1], source.size[0], 4)
    magenta = (pixels[:, :, 0] > 0.75) & (pixels[:, :, 2] > 0.75) & (pixels[:, :, 1] < 0.25)
    pixels[magenta, 3] = 0.0
    keyed = bpy.data.images.new("HeroineScaleSprite", source.size[0], source.size[1], alpha=True)
    keyed.colorspace_settings.name = "sRGB"
    keyed.pixels.foreach_set(pixels.ravel())
    mat = bpy.data.materials.new("Heroine scale sprite material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader = nodes.get("Principled BSDF")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = keyed
    shader.inputs["Roughness"].default_value = 0.9
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "DITHERED"
    elif hasattr(mat, "blend_method"):
        mat.blend_method = "BLEND"
    width = height
    x, y, z = at
    vertices = [
        (x - width * 0.5, y, z),
        (x + width * 0.5, y, z),
        (x + width * 0.5, y, z + height),
        (x - width * 0.5, y, z + height),
    ]
    mesh = bpy.data.meshes.new("HeroineScaleSpriteMesh")
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    uvs = ((1, 0), (0, 0), (0, 1), (1, 1)) if mirror else ((0, 0), (1, 0), (1, 1), (0, 1))
    for loop, uv in zip(uv_layer.data, uvs):
        loop.uv = uv
    obj = bpy.data.objects.new("Heroine scale sprite", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def add_box(
    name: str,
    size: tuple[float, float, float],
    at: tuple[float, float, float],
    mat: bpy.types.Material,
    rotation: tuple[float, float, float] = (0, 0, 0),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=at, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = tuple(value * 0.5 for value in size)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("Rock-cut edge", "BEVEL")
    bevel.width = 0.035
    bevel.segments = 1
    return obj


def add_cylinder(
    name: str,
    radius: float,
    depth: float,
    at: tuple[float, float, float],
    mat: bpy.types.Material,
    vertices: int = 10,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=at)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def add_rock(
    name: str,
    size: tuple[float, float, float],
    at: tuple[float, float, float],
    mat: bpy.types.Material,
    rotation: tuple[float, float, float] = (0, 0, 0),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=at, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = tuple(value * 0.5 for value in size)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.data.materials.append(mat)
    return obj


def add_beam(
    name: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    width: float,
    mat: bpy.types.Material,
) -> bpy.types.Object:
    a, b = Vector(start), Vector(end)
    direction = b - a
    obj = add_box(name, (width, width, direction.length), tuple((a + b) * 0.5), mat)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    return obj


def add_gorge_surface(
    ledge: bpy.types.Material,
    water: bpy.types.Material,
    slate: bpy.types.Material,
) -> bpy.types.Object:
    x_count = 47
    y_count = 67
    x_values = np.linspace(-15.0, 15.0, x_count)
    y_values = np.linspace(-28.0, 10.0, y_count)
    vertices = []
    for y in y_values:
        for x in x_values:
            # The working river bends through a sunken cut instead of reading
            # as a ruler-straight material boundary.
            river_x = 2.25 + math.sin(y * 0.23) * 0.34 + math.sin(y * 0.071) * 0.18
            distance = abs(x - river_x)
            if distance < 1.05:
                z = -0.86 + math.sin(y * 0.75 + x) * 0.025
            elif distance < 2.10:
                bank = (distance - 1.05) / 1.05
                z = -0.86 + bank * 0.87 + math.sin(y * 0.42 + x) * 0.04
            else:
                z = math.sin(x * 0.70 + y * 0.23) * 0.035 + math.sin(y * 0.88) * 0.025
            # Canyon Works is enclosed by a far river wall and a high distant
            # headwall.  Both are continuous terrain, not stage-set backplates.
            far_rim = max(0.0, x - (3.55 + math.sin(y * 0.16) * 0.42))
            west_rim = max(0.0, -x - 5.1)
            headwall = max(0.0, -y - 4.2)
            z += far_rim * 0.78 + west_rim * 0.42 + headwall * 0.16
            vertices.append((float(x), float(y), float(z)))
    faces = []
    material_indices = []
    for row in range(y_count - 1):
        for column in range(x_count - 1):
            a = row * x_count + column
            faces.append((a, a + 1, a + x_count + 1, a + x_count))
            center_x = (x_values[column] + x_values[column + 1]) * 0.5
            center_y = (y_values[row] + y_values[row + 1]) * 0.5
            river_x = 2.25 + math.sin(center_y * 0.23) * 0.34 + math.sin(center_y * 0.071) * 0.18
            distance = abs(center_x - river_x)
            material_indices.append(1 if distance < 1.05 else (2 if distance < 2.10 else 0))
    mesh = bpy.data.meshes.new("CanyonGorgeSurfaceMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Canyon gorge surface", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(ledge)
    obj.data.materials.append(water)
    obj.data.materials.append(slate)
    for polygon, material_index in zip(obj.data.polygons, material_indices):
        polygon.material_index = material_index
    return obj


def import_crawler() -> dict[str, bpy.types.Object]:
    bpy.ops.import_scene.gltf(filepath=str(GLB))
    return {obj.name: obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name in COMPONENTS}


def setup_scene(resolution: tuple[int, int]) -> bpy.types.Object:
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
    scene.world = bpy.data.worlds.new("Ink-blue voltage dusk")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.006, 0.012, 0.022, 1)
    background.inputs["Strength"].default_value = 0.18
    bpy.ops.object.light_add(type="AREA", location=(-4.8, -5.2, 8.4))
    key = bpy.context.object
    key.data.energy = 1420
    key.data.color = (1.0, 0.52, 0.22)
    key.data.shape = "DISK"
    key.data.size = 4.2
    bpy.ops.object.light_add(type="AREA", location=(4.0, 3.8, 5.8))
    fill = bpy.context.object
    fill.data.energy = 940
    fill.data.color = (0.12, 0.72, 0.76)
    fill.data.size = 3.0
    bpy.ops.object.light_add(type="POINT", location=(-0.4, -1.0, 2.6))
    spark = bpy.context.object
    spark.data.energy = 130
    spark.data.color = (0.07, 0.72, 0.76)
    bpy.ops.object.light_add(type="AREA", location=(-1.0, 2.5, 6.5))
    front = bpy.context.object
    front.data.energy = 1650
    front.data.color = (1.0, 0.82, 0.60)
    front.data.size = 4.5
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


def fitted_pixels(path: Path, width: int, height: int) -> np.ndarray:
    source = load_pixels(path)
    source_height, source_width, _ = source.shape
    scale = min(width / source_width, height / source_height)
    resized_width = max(1, int(round(source_width * scale)))
    resized_height = max(1, int(round(source_height * scale)))
    xs = np.linspace(0, source_width - 1, resized_width).astype(np.int32)
    ys = np.linspace(0, source_height - 1, resized_height).astype(np.int32)
    resized = source[ys[:, None], xs[None, :]]
    canvas = np.zeros((height, width, 4), dtype=np.float32)
    canvas[:, :, :3] = (0.045, 0.032, 0.021)
    canvas[:, :, 3] = 1.0
    x0 = (width - resized_width) // 2
    y0 = (height - resized_height) // 2
    canvas[y0:y0 + resized_height, x0:x0 + resized_width] = resized
    return canvas


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


def save_reference_ab(render_path: Path) -> None:
    left = fitted_pixels(REFERENCE, 960, 540)
    right = fitted_pixels(render_path, 960, 540)
    divider = np.ones((540, 6, 4), dtype=np.float32)
    divider[:, :, :3] = (0.56, 0.34, 0.12)
    board = np.concatenate((left, divider, right), axis=1)
    height, width, _ = board.shape
    image = bpy.data.images.new("crawler-reference-ab", width, height, alpha=True)
    image.pixels.foreach_set(board.ravel())
    image.filepath_raw = str(OUT / "crawler-reference-ab.png")
    image.file_format = "PNG"
    image.save()


def add_canyon_context() -> None:
    slate = canyon_material("Engraved canyon slate", "slate", scale=2.5, saturation=0.62, value=0.62)
    ledge = canyon_material("Switchback dust", "grass", scale=3.0, saturation=0.34, value=0.62)
    shadow = material("Gorge shadow", (0.025, 0.032, 0.035, 1))
    water = canyon_material("Working river", "river", 0.62, scale=3.2, saturation=0.70, value=0.68)
    arc = material("Drain arc", (0.02, 0.68, 0.76, 1), roughness=0.24)
    arc_shader = arc.node_tree.nodes.get("Principled BSDF")
    arc_shader.inputs["Emission Color"].default_value = (0.01, 0.72, 0.82, 1)
    arc_shader.inputs["Emission Strength"].default_value = 3.2

    add_gorge_surface(ledge, water, slate)
    rng = np.random.default_rng(315)
    for bank, x in enumerate((0.95, 3.55)):
        for rubble in range(14):
            y = float(rng.uniform(-7.5, 3.0))
            add_rock(
                f"Bank rubble {bank} {rubble}",
                tuple(float(value) for value in rng.uniform((0.18, 0.16, 0.12), (0.70, 0.55, 0.46))),
                (x + float(rng.uniform(-0.28, 0.28)), y, float(rng.uniform(-0.32, 0.10))),
                slate,
                rotation=tuple(float(value) for value in rng.uniform(-0.6, 0.6, 3)),
            )
    for rubble in range(12):
        add_rock(
            f"Switchback rubble {rubble}",
            tuple(float(value) for value in rng.uniform((0.08, 0.08, 0.06), (0.28, 0.24, 0.20))),
            (float(rng.uniform(-5.0, -0.1)), float(rng.uniform(-2.0, 2.4)), float(rng.uniform(0.02, 0.09))),
            slate,
            rotation=tuple(float(value) for value in rng.uniform(-0.6, 0.6, 3)),
        )

    # A broken row of large far-bank outcrops makes the gorge depth survive the
    # production's high camera without becoming a mirrored panorama wall.
    for outcrop, y in enumerate((-6.4, -4.7, -2.9, -1.0, 1.2, 3.1)):
        add_rock(
            f"Far wall outcrop {outcrop}",
            (float(rng.uniform(1.3, 2.1)), float(rng.uniform(1.2, 2.0)), float(rng.uniform(1.5, 2.8))),
            (float(rng.uniform(4.3, 5.1)), y, float(rng.uniform(0.8, 1.5))),
            slate,
            rotation=tuple(float(value) for value in rng.uniform(-0.45, 0.45, 3)),
        )
    for outcrop, y in enumerate((-4.8, -2.6, -0.2, 2.2)):
        add_rock(
            f"West rim outcrop {outcrop}",
            (float(rng.uniform(0.9, 1.35)), float(rng.uniform(0.9, 1.35)), float(rng.uniform(0.8, 1.35))),
            (float(rng.uniform(-5.25, -4.75)), y, float(rng.uniform(0.28, 0.62))),
            slate,
            rotation=tuple(float(value) for value in rng.uniform(-0.42, 0.42, 3)),
        )

    # The shipped heroine combat frame and the drain arc are evidence-only
    # pressure/scale context.  Neither is exported or claims choreography.
    add_hero_sprite((-3.35, 0.34, 0.02), 1.38, mirror=True)
    arc_start = Vector((-2.36, 0.02, 2.44))
    arc_end = Vector((-3.05, 0.30, 1.12))
    points = [arc_start]
    for step in range(1, 7):
        t = step / 7.0
        point = arc_start.lerp(arc_end, t)
        point.x += math.sin(step * 2.7) * 0.08
        point.y += math.sin(step * 4.1) * 0.07
        point.z += math.sin(step * 3.3) * 0.05
        points.append(point)
    points.append(arc_end)
    for segment, (start, end) in enumerate(zip(points, points[1:])):
        add_beam(f"Drain arc segment {segment}", tuple(start), tuple(end), 0.026, arc)
    bpy.ops.object.light_add(type="POINT", location=arc_end)
    impact = bpy.context.object
    impact.name = "Drain arc impact light"
    impact.data.energy = 72
    impact.data.color = (0.02, 0.78, 0.86)


def set_all_morphs(crawler: dict[str, bpy.types.Object], value: float = 0.0) -> None:
    for obj in crawler.values():
        if not obj.data.shape_keys:
            continue
        for key in obj.data.shape_keys.key_blocks:
            if key.name != "Basis":
                key.value = value


def render_turntable() -> None:
    reset_scene()
    import_crawler()
    stone = material("Turntable slate", (0.095, 0.062, 0.035, 1))
    add_box("Turntable ground", (9, 9, 0.10), (0, 0, -0.07), stone)
    camera = setup_scene((620, 620))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 3.75
    target = Vector((0, 0, 1.05))
    views = [
        ("front-left", Vector((-4.0, -4.2, 3.4))),
        ("front-right", Vector((-4.0, 4.2, 3.4))),
        ("rear-left", Vector((4.0, -4.2, 3.4))),
        ("rear-right", Vector((4.0, 4.2, 3.4))),
    ]
    paths: list[Path] = []
    for label, location in views:
        aim(camera, location, target)
        path = OUT / f"turntable-{label}.png"
        render(path)
        paths.append(path)
    save_grid(paths, OUT / "crawler-turntable.png", 2, 2)
    for path in paths:
        path.unlink()


def render_canyon_run_camera() -> None:
    reset_scene()
    crawler = import_crawler()
    for obj in crawler.values():
        obj.location.x = -1.35
    add_canyon_context()
    camera = setup_scene((1280, 800))
    camera.data.type = "PERSP"
    camera.data.angle = math.radians(RUN_CAMERA_FOV)
    target = Vector((-1.35, -0.15, 0.95))
    # Exact production offset direction, shortened only for owner-review coverage.
    location = target + RUN_CAMERA_VECTOR.normalized() * 7.8
    aim(camera, location, target)
    path = OUT / "crawler-canyon-run-camera.png"
    render(path)
    save_reference_ab(path)


def render_damage_states() -> None:
    reset_scene()
    crawler = import_crawler()
    ground = material("Damage review ledge", (0.18, 0.095, 0.040, 1))
    add_box("Damage ground", (8, 8, 0.10), (0, 0, -0.07), ground)
    camera = setup_scene((560, 560))
    camera.data.type = "PERSP"
    camera.data.angle = math.radians(46)
    target = Vector((0, 0, 1.02))
    aim(camera, Vector((-2.25, 5.5, 4.05)), target)
    paths: list[Path] = []
    for node, morph in COMPONENTS.items():
        set_all_morphs(crawler, 0.0)
        crawler[node].data.shape_keys.key_blocks[morph].value = 1.0
        path = OUT / f"damage-{node}.png"
        render(path)
        paths.append(path)
    save_grid(paths, OUT / "crawler-damage-states.png", 1, 3)
    for path in paths:
        path.unlink()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    render_turntable()
    render_canyon_run_camera()
    render_damage_states()
    print(f"rendered {OUT / 'crawler-turntable.png'}")
    print(f"rendered {OUT / 'crawler-canyon-run-camera.png'}")
    print(f"rendered {OUT / 'crawler-damage-states.png'}")
    print(f"rendered {OUT / 'crawler-reference-ab.png'}")


if __name__ == "__main__":
    main()
