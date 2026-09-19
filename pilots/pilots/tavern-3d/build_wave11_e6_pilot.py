from pathlib import Path
import hashlib
import json
import math

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
SOURCE_TAVERN = HERE / "town-v3-tavern.blend"
SOURCE_TAVERN_GLB = HERE / "town-v3-tavern.glb"
SOURCE_TAVERN_BLEND_SHA = "b81ef19a24661c3ea97feb3b7f75caceef5599954d6462b1bbd2ab6085ade2fe"
SOURCE_TAVERN_GLB_SHA = "edec4934d6d956170078b521fe526ccadcde015567094aec59001e2d4b71b90d"

REGIONS = {
    "dark": (0.02, 0.02, 0.23, 0.23),
    "timber": (0.27, 0.27, 0.48, 0.48),
    "teal": (0.52, 0.27, 0.73, 0.48),
    "chrome": (0.77, 0.27, 0.98, 0.48),
    "roof": (0.77, 0.77, 0.98, 0.98),
    "cream": (0.02, 0.52, 0.23, 0.73),
    "amber": (0.27, 0.52, 0.48, 0.73),
    "glass": (0.52, 0.52, 0.73, 0.73),
    "coral": (0.77, 0.52, 0.98, 0.73),
    "shadow_teal": (0.02, 0.77, 0.23, 0.98),
}

PALETTE = {
    "dark": (0.085, 0.070, 0.055),
    "timber": (0.42, 0.255, 0.135),
    "teal": (0.105, 0.405, 0.390),
    "chrome": (0.72, 0.645, 0.465),
    "roof": (0.48, 0.175, 0.105),
    "cream": (0.72, 0.560, 0.310),
    "amber": (0.82, 0.400, 0.090),
    "glass": (0.075, 0.585, 0.550),
    "coral": (0.61, 0.255, 0.175),
    "shadow_teal": (0.035, 0.165, 0.165),
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.images,
                       bpy.data.cameras, bpy.data.lights):
        for datablock in list(collection):
            collection.remove(datablock)


def paint_region(pixels, bounds, color, seed):
    height, width, _ = pixels.shape
    u0, v0, u1, v1 = bounds
    x0, x1 = int(u0 * width), max(int(u0 * width) + 1, int(u1 * width))
    y0, y1 = int(v0 * height), max(int(v0 * height) + 1, int(v1 * height))
    yy, xx = np.mgrid[y0:y1, x0:x1]
    rng = np.random.default_rng(seed)
    grain = rng.normal(0.0, 0.025, size=(y1 - y0, x1 - x0)).astype(np.float32)
    brush = 0.018 * np.sin(xx * 0.115 + seed) + 0.012 * np.sin(yy * 0.073 + seed * 0.7)
    hatch = np.where(((xx + yy * 2 + seed) % 47) < 2, -0.065, 0.0)
    variation = grain + brush + hatch
    base = np.asarray(color, dtype=np.float32)
    pixels[y0:y1, x0:x1, :3] = np.clip(base[None, None, :] + variation[:, :, None], 0.012, 0.94)
    pixels[y0:y1, x0:x1, 3] = 1.0


def save_and_pack_image(name, pixels):
    height, width, _ = pixels.shape
    image = bpy.data.images.new(name, width=width, height=height, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(pixels.astype(np.float32).ravel())
    image.update()
    temp = Path("/tmp") / f"{name}.png"
    image.filepath_raw = str(temp)
    image.file_format = "PNG"
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.image_settings.color_mode = "RGBA"
    bpy.context.scene.render.image_settings.color_depth = "8"
    image.save()
    packed = bpy.data.images.load(str(temp), check_existing=False)
    packed.name = name
    packed.pack()
    bpy.data.images.remove(image)
    temp.unlink(missing_ok=True)
    return packed


def make_atlas(name):
    pixels = np.zeros((1024, 1024, 4), dtype=np.float32)
    pixels[:, :, :3] = np.asarray((0.16, 0.11, 0.075), dtype=np.float32)
    pixels[:, :, 3] = 1.0
    for index, (region, bounds) in enumerate(REGIONS.items(), 1):
        paint_region(pixels, bounds, PALETTE[region], index * 19)
    return save_and_pack_image(name, pixels)


def make_material(name, image):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    shader = nodes.get("Principled BSDF")
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Roughness"].default_value = 0.92
    shader.inputs["Emission Color"].default_value = (0, 0, 0, 1)
    shader.inputs["Emission Strength"].default_value = 0.0
    for node in list(nodes):
        if node.type == "TEX_IMAGE":
            nodes.remove(node)
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Linear"
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    return material


def atomicize_tavern_material(model):
    source_material = model.data.materials[0]
    source_texture = next(node for node in source_material.node_tree.nodes if node.type == "TEX_IMAGE")
    source_image = source_texture.image
    width, height = source_image.size
    source = np.asarray(source_image.pixels[:], dtype=np.float32).reshape((height, width, 4)).copy()
    rgb = source[:, :, :3]
    luminance = rgb @ np.asarray((0.2126, 0.7152, 0.0722), dtype=np.float32)
    warm = np.stack((luminance * 1.22 + 0.075, luminance * 1.02 + 0.065,
                     luminance * 0.72 + 0.040), axis=2)
    teal_mask = (rgb[:, :, 1] > rgb[:, :, 0] * 1.05) & (rgb[:, :, 2] > rgb[:, :, 0] * 0.88)
    teal = np.stack((luminance * 0.34, luminance * 0.86 + 0.025, luminance * 0.82 + 0.025), axis=2)
    source[:, :, :3] = np.clip(np.where(teal_mask[:, :, None], teal, warm), 0.012, 0.90)
    for index, region in enumerate(("dark", "timber", "teal", "chrome", "roof"), 101):
        paint_region(source, REGIONS[region], PALETTE[region], index)
    image = save_and_pack_image("AtomicDinerPaintedAtlas", source)
    material = make_material("AtomicDinerPaintedMaterial", image)
    model.data.materials[0] = material
    bpy.data.materials.remove(source_material)
    if source_image.users == 0:
        bpy.data.images.remove(source_image)
    return material


def tag(obj, material, region, bevel=0.012):
    obj.data.materials.append(material)
    obj["paint_region"] = region
    if bevel:
        modifier = obj.modifiers.new("Painted edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        modifier.limit_method = "ANGLE"
    return obj


def box(name, size, location, material, region, bevel=0.012, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = tuple(value / 2 for value in size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return tag(obj, material, region, bevel)


def cylinder(name, radius, depth, location, material, region, vertices=12, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    return tag(obj, material, region, 0.006)


def torus(name, major_radius, minor_radius, location, material, region, rotation=(0, 0, 0), major_segments=16):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius, minor_radius=minor_radius, major_segments=major_segments, minor_segments=6,
        location=location, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    return tag(obj, material, region, 0)


def sphere(name, radius, location, material, region, segments=12, rings=6):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, radius=radius, location=location,
    )
    obj = bpy.context.object
    obj.name = name
    return tag(obj, material, region, 0)


def beam(name, start, end, radius, material, region, vertices=6):
    start, end = Vector(start), Vector(end)
    delta = end - start
    obj = cylinder(name, radius, delta.length, (start + end) * 0.5, material, region, vertices)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def wedge_roof(name, width, depth, eave_z, ridge_z, material, region):
    x = width / 2
    y = depth / 2
    vertices = [
        (-x, -y, eave_z), (x, -y, eave_z), (x, y, eave_z), (-x, y, eave_z),
        (-x, 0, ridge_z), (x, 0, ridge_z),
    ]
    faces = [
        (0, 1, 5, 4), (4, 5, 2, 3), (0, 4, 3), (1, 2, 5), (0, 3, 2, 1),
    ]
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return tag(obj, material, region, 0.018)


def barrel_roof(name, width, depth, spring_z, radius, material, region, segments=12):
    vertices = []
    for y in (-depth / 2, depth / 2):
        for index in range(segments + 1):
            angle = math.pi * index / segments
            vertices.append((math.cos(angle) * width / 2, y, spring_z + math.sin(angle) * radius))
    faces = []
    count = segments + 1
    for index in range(segments):
        faces.append((index, index + 1, count + index + 1, count + index))
    faces.extend((tuple(range(count)), tuple(range(count, count * 2))))
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return tag(obj, material, region, 0.014)


def apply_and_uv(parts):
    for obj in parts:
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        for modifier in list(obj.modifiers):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
        bpy.ops.object.mode_set(mode="OBJECT")
        uv = obj.data.uv_layers.active.data
        coords = np.array([[loop.uv.x, loop.uv.y] for loop in uv])
        minimum, maximum = coords.min(axis=0), coords.max(axis=0)
        span = np.maximum(maximum - minimum, 1e-6)
        u0, v0, u1, v1 = REGIONS[obj["paint_region"]]
        for loop, coord in zip(uv, coords):
            normalized = (coord - minimum) / span
            loop.uv = (u0 + normalized[0] * (u1 - u0), v0 + normalized[1] * (v1 - v0))
        obj.select_set(False)


def join_parts(parts, name):
    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    model = bpy.context.object
    model.name = name
    model.data.name = f"{name}Mesh"
    model.data.uv_layers.active.name = "UVMap"
    for polygon in model.data.polygons:
        polygon.material_index = 0
    while len(model.data.materials) > 1:
        model.data.materials.pop(index=len(model.data.materials) - 1)
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    return model


def export_model(model, blend_path, glb_path):
    for obj in list(bpy.data.objects):
        if obj is not model and obj.type in {"CAMERA", "LIGHT"}:
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.object.select_all(action="DESELECT")
    model.select_set(True)
    bpy.context.view_layer.objects.active = model
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT",
    )
    triangles = sum(len(polygon.vertices) - 2 for polygon in model.data.polygons)
    assert triangles <= 15_000, (model.name, triangles)
    assert len(model.data.materials) == 1
    return {
        "blend": str(blend_path.relative_to(ROOT)),
        "glb": str(glb_path.relative_to(ROOT)),
        "sha256": sha256(glb_path),
        "triangles": triangles,
        "dimensions": [round(value, 6) for value in model.dimensions],
    }


def starburst(parts, prefix, center, radius, face_y, material, hub_region="glass", double_sided=False):
    cx, cy, cz = center
    parts.extend((
        cylinder(f"{prefix} face", radius * 0.77, 0.055, center, material, "teal", 16,
                 rotation=(math.pi / 2, 0, 0)),
        torus(f"{prefix} chrome rim", radius * 0.82, radius * 0.075, center, material, "chrome",
              rotation=(math.pi / 2, 0, 0)),
        cylinder(f"{prefix} hub", radius * 0.18, 0.075, (cx, cy + face_y * 0.045, cz), material,
                 hub_region, 12, rotation=(math.pi / 2, 0, 0)),
    ))
    faces = (face_y, -face_y) if double_sided else (face_y,)
    for face_index, direction in enumerate(faces, 1):
        for index in range(8):
            angle = index * math.tau / 8
            inner = (cx + math.cos(angle) * radius * 0.20, cy + direction * 0.085,
                     cz + math.sin(angle) * radius * 0.20)
            outer = (cx + math.cos(angle) * radius * 0.61, cy + direction * 0.085,
                     cz + math.sin(angle) * radius * 0.61)
            parts.append(beam(
                f"{prefix} face {face_index} ray {index + 1}", inner, outer,
                radius * 0.035, material, "amber", 6,
            ))
            parts.append(cylinder(
                f"{prefix} face {face_index} orbit pip {index + 1}", radius * 0.065, 0.065,
                (outer[0], outer[1] + direction * 0.025, outer[2]), material,
                "glass" if index % 2 == 0 else "amber", 8, rotation=(math.pi / 2, 0, 0),
            ))


def build_atomic_diner():
    assert sha256(SOURCE_TAVERN) == SOURCE_TAVERN_BLEND_SHA
    assert sha256(SOURCE_TAVERN_GLB) == SOURCE_TAVERN_GLB_SHA
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE_TAVERN))
    model = bpy.data.objects["TownTavernFullWrap"]
    material = atomicize_tavern_material(model)
    parts = []

    # Chrome/enamel frontage grows from the original covered porch without
    # erasing the Tavern's two-storey false-front silhouette.
    parts.extend((
        cylinder("Atomic Diner rolled chrome canopy", 0.21, 4.04, (0, -1.46, 1.83), material, "chrome", 12,
                 rotation=(0, math.pi / 2, 0)),
        box("Atomic Diner teal canopy belt", (4.08, 0.06, 0.16), (0, -1.66, 1.73), material, "teal", 0.008),
        box("Atomic Diner west enamel corner", (0.24, 0.26, 1.62), (-1.86, -1.51, 1.03), material, "chrome", 0.018),
        box("Atomic Diner east enamel corner", (0.24, 0.26, 1.62), (1.86, -1.51, 1.03), material, "chrome", 0.018),
        box("Atomic Diner balcony teal belt", (4.04, 0.11, 0.14), (0, -1.39, 2.18), material, "teal", 0.008),
        torus("Atomic Diner crest halo", 0.50, 0.055, (0, -1.40, 3.33), material, "chrome",
              rotation=(math.pi / 2, 0, 0)),
        cylinder("Atomic Diner crest atom face", 0.39, 0.055, (0, -1.43, 3.33), material, "teal", 16,
                 rotation=(math.pi / 2, 0, 0)),
        cylinder("Atomic Diner roof vent", 0.13, 1.34, (1.40, 0.60, 3.98), material, "dark", 10),
        cylinder("Atomic Diner roof vent collar", 0.20, 0.12, (1.40, 0.60, 3.38), material, "chrome", 10),
        cylinder("Atomic Diner roof vent cap", 0.22, 0.13, (1.40, 0.60, 4.62), material, "teal", 10),
    ))
    for index, x in enumerate((-1.55, -1.03, -0.51, 0.01, 0.53, 1.05, 1.57), 1):
        parts.append(cylinder(
            f"Atomic Diner frontage glow pip {index}", 0.055, 0.055, (x, -1.67, 1.74), material,
            "glass" if index % 2 else "amber", 8, rotation=(math.pi / 2, 0, 0),
        ))

    # The large hanging pictogram is the gameplay-distance read and remains
    # letter-free under the house law.
    parts.extend((
        beam("Atomic Diner sign mast", (-1.94, -1.50, 1.80), (-1.94, -1.50, 3.23), 0.065,
             material, "dark", 8),
        beam("Atomic Diner sign crane", (-1.94, -1.50, 3.13), (-2.68, -1.50, 3.13), 0.060,
             material, "chrome", 8),
        beam("Atomic Diner sign drop", (-2.55, -1.50, 3.13), (-2.55, -1.50, 2.86), 0.026,
             material, "dark", 6),
    ))
    starburst(parts, "Atomic Diner hanging starburst", (-2.55, -1.56, 2.43), 0.52, -1, material,
              double_sided=True)
    starburst(parts, "Atomic Diner crest starburst", (0, -1.48, 3.33), 0.34, -1, material)

    # Small rear fittings make the rebuild honest from every side.
    parts.extend((
        cylinder("Atomic Diner rear condenser", 0.22, 1.22, (1.72, 1.42, 0.82), material, "teal", 10),
        torus("Atomic Diner rear condenser lower band", 0.235, 0.035, (1.72, 1.42, 0.42), material, "chrome"),
        torus("Atomic Diner rear condenser upper band", 0.235, 0.035, (1.72, 1.42, 1.18), material, "chrome"),
        beam("Atomic Diner rear service pipe", (1.72, 1.42, 1.35), (1.05, 1.42, 1.82), 0.055,
             material, "chrome", 8),
    ))
    # The painted Tavern source already carries the close-up bevel language.
    # Keep the E6 additions crisp so the inherited 10,988-triangle shell and
    # the gameplay-distance silhouette stay inside the 15k family budget.
    for part in parts:
        part.modifiers.clear()
    apply_and_uv(parts)
    bpy.ops.object.select_all(action="DESELECT")
    model.select_set(True)
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = model
    bpy.ops.object.join()
    model.name = "TownTavernE6AtomicDiner"
    model.data.name = "TownTavernE6AtomicDinerMesh"
    for polygon in model.data.polygons:
        polygon.material_index = 0
    while len(model.data.materials) > 1:
        model.data.materials.pop(index=len(model.data.materials) - 1)
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    model["epoch_variant"] = "E6 Atomic Mesa"
    model["identity_transform"] = (
        "Tavern social hub retained as two-storey false-front; chrome rolled diner frontage, "
        "atomic starburst pictograms, teal enamel pips, roof condenser, and all-angle service plant"
    )
    return export_model(model, HERE / "tavern.e6.blend", HERE / "tavern.e6.glb")


def dome_sector(name, theta0, theta1, radius, base_z, height, material, region, rings=7):
    vertices = []
    for ring in range(rings):
        phi = (math.pi / 2) * ring / rings
        radial = radius * math.cos(phi)
        z = base_z + height * math.sin(phi)
        vertices.extend(((math.cos(theta0) * radial, math.sin(theta0) * radial, z),
                         (math.cos(theta1) * radial, math.sin(theta1) * radial, z)))
    top = len(vertices)
    vertices.append((0, 0, base_z + height))
    faces = []
    for ring in range(rings - 1):
        a = ring * 2
        faces.append((a, a + 1, a + 3, a + 2))
    faces.append(((rings - 1) * 2, (rings - 1) * 2 + 1, top))
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return tag(obj, material, region, 0)


def build_reactor_dome():
    reset_scene()
    directory = ROOT / "assets/pilots/reactor-dome-3d"
    directory.mkdir(parents=True, exist_ok=True)
    material = make_material("ReactorDomePaintedMaterial", make_atlas("ReactorDomePaintedAtlas"))
    parts = [
        cylinder("Reactor Dome grounded plinth", 3.0, 0.20, (0, 0, 0.10), material, "dark", 24),
        cylinder("Reactor Dome teal terrace", 2.84, 0.18, (0, 0, 0.27), material, "teal", 24),
        cylinder("Reactor Dome lower pressure drum", 2.38, 1.18, (0, 0, 0.88), material, "cream", 24),
        torus("Reactor Dome lower belt", 2.45, 0.075, (0, 0, 0.38), material, "chrome", major_segments=24),
        torus("Reactor Dome observation sill", 2.46, 0.075, (0, 0, 1.30), material, "chrome", major_segments=24),
        torus("Reactor Dome crown belt", 2.48, 0.075, (0, 0, 1.78), material, "chrome", major_segments=24),
    ]
    for index in range(24):
        theta0 = index * math.tau / 24
        theta1 = (index + 1) * math.tau / 24
        parts.append(dome_sector(
            f"Reactor Dome pressure panel {index + 1}", theta0, theta1, 2.42, 1.77, 1.92,
            material, "teal" if index % 3 == 0 else "cream",
        ))
    for index in range(16):
        theta = index * math.tau / 16
        radius = 2.43
        parts.append(box(
            f"Reactor Dome observation pane {index + 1}", (0.40, 0.07, 0.34),
            (math.cos(theta) * radius, math.sin(theta) * radius, 1.54), material, "glass", 0.006,
            rotation=(0, 0, theta + math.pi / 2),
        ))
    # Twelve load ribs follow the dome profile and make the pressure shell read
    # as a grounded civic machine instead of a toy saucer.
    for rib in range(12):
        theta = rib * math.tau / 12
        previous = None
        for step in range(7):
            phi = (math.pi / 2) * step / 7
            point = (math.cos(theta) * 2.47 * math.cos(phi), math.sin(theta) * 2.47 * math.cos(phi),
                     1.77 + 1.95 * math.sin(phi))
            if previous is not None:
                parts.append(beam(
                    f"Reactor Dome crown rib {rib + 1}.{step}", previous, point, 0.035,
                    material, "chrome", 6,
                ))
            previous = point
    for index in range(8):
        theta = index * math.tau / 8
        x, y = math.cos(theta) * 2.68, math.sin(theta) * 2.68
        parts.extend((
            cylinder(f"Reactor Dome instrument post {index + 1}", 0.095, 0.92, (x, y, 0.71),
                     material, "dark", 8),
            cylinder(f"Reactor Dome instrument collar {index + 1}", 0.14, 0.10, (x, y, 0.96),
                     material, "chrome", 8),
            sphere(f"Reactor Dome instrument globe {index + 1}", 0.15, (x, y, 1.22),
                   material, "glass", 10, 5),
        ))
        inward = (math.cos(theta) * 2.18, math.sin(theta) * 2.18, 0.82)
        parts.append(beam(
            f"Reactor Dome radial service pipe {index + 1}", inward, (x, y, 0.82), 0.055,
            material, "chrome", 8,
        ))
    for index in range(4):
        theta = math.pi / 4 + index * math.pi / 2
        inner = (math.cos(theta) * 2.30, math.sin(theta) * 2.30, 0.92)
        outer = (math.cos(theta) * 2.60, math.sin(theta) * 2.60, 0.92)
        parts.extend((
            beam(f"Reactor Dome pressure port {index + 1}", inner, outer, 0.16,
                 material, "chrome", 10),
            sphere(f"Reactor Dome pressure port glass {index + 1}", 0.17, outer,
                   material, "glass", 10, 5),
        ))
    parts.extend((
        cylinder("Reactor Dome crown collar", 0.48, 0.20, (0, 0, 3.67), material, "chrome", 16),
        cylinder("Reactor Dome teal antenna glass", 0.16, 0.78, (0, 0, 4.10), material, "glass", 10),
        cylinder("Reactor Dome antenna cap", 0.25, 0.12, (0, 0, 4.49), material, "chrome", 12),
        beam("Reactor Dome antenna needle", (0, 0, 4.50), (0, 0, 4.92), 0.035, material, "amber", 6),
        sphere("Reactor Dome antenna finial", 0.075, (0, 0, 4.98), material, "amber", 8, 4),
    ))
    apply_and_uv(parts)
    model = join_parts(parts, "ReactorDomeE6")
    model["epoch_variant"] = "E6 Atomic Mesa"
    model["identity"] = (
        "Riveted civic pressure dome with alternating enamel panels, continuous teal observation ring, "
        "twelve load ribs, radial service plant, and antenna crown; deliberately no visible door"
    )
    return export_model(model, directory / "reactor-dome.blend", directory / "reactor-dome.glb")


def build_isotope_kitchen():
    reset_scene()
    directory = ROOT / "assets/pilots/isotope-kitchen-3d"
    directory.mkdir(parents=True, exist_ok=True)
    material = make_material("IsotopeKitchenPaintedMaterial", make_atlas("IsotopeKitchenPaintedAtlas"))
    parts = [
        box("Isotope Kitchen grounded plinth", (4.75, 3.30, 0.18), (0, 0, 0.09), material, "dark", 0.018),
        box("Isotope Kitchen teal floor belt", (4.62, 3.18, 0.24), (0, 0, 0.28), material, "teal", 0.018),
        box("Isotope Kitchen rear masonry", (4.42, 0.22, 2.38), (0, 1.38, 1.47), material, "timber", 0.016),
        box("Isotope Kitchen west service wall", (0.22, 2.84, 2.30), (-2.10, 0.05, 1.43), material, "cream", 0.016),
        box("Isotope Kitchen east service wall", (0.22, 2.84, 2.30), (2.10, 0.05, 1.43), material, "cream", 0.016),
        box("Isotope Kitchen canopy slab", (4.58, 3.18, 0.18), (0, 0, 2.69), material, "dark", 0.018),
        cylinder("Isotope Kitchen rounded front valance", 0.18, 4.54, (0, -1.46, 2.61), material,
                 "chrome", 12, rotation=(0, math.pi / 2, 0)),
        box("Isotope Kitchen teal valance belt", (4.56, 0.06, 0.16), (0, -1.62, 2.52), material, "teal", 0.006),
        barrel_roof("Isotope Kitchen isotope vault", 2.15, 2.26, 2.72, 0.92, material, "chrome", 14),
        box("Isotope Kitchen west front post", (0.18, 0.18, 2.32), (-2.06, -1.40, 1.42), material, "chrome", 0.012),
        box("Isotope Kitchen east front post", (0.18, 0.18, 2.32), (2.06, -1.40, 1.42), material, "chrome", 0.012),
        box("Isotope Kitchen west display window", (0.08, 1.22, 1.05), (-2.22, -0.54, 1.35), material, "glass", 0.008),
        box("Isotope Kitchen east display window", (0.08, 1.22, 1.05), (2.22, -0.54, 1.35), material, "amber", 0.008),
        box("Isotope Kitchen sample case base", (1.56, 0.44, 0.62), (0.86, -1.33, 0.66), material, "teal", 0.014),
        box("Isotope Kitchen sample case glass", (1.42, 0.40, 0.48), (0.86, -1.34, 1.13), material, "glass", 0.008),
        cylinder("Isotope Kitchen tall stack", 0.14, 2.24, (-1.52, 0.82, 3.43), material, "dark", 10),
        cylinder("Isotope Kitchen stack lower collar", 0.21, 0.12, (-1.52, 0.82, 2.39), material, "chrome", 10),
        cylinder("Isotope Kitchen stack cap", 0.24, 0.13, (-1.52, 0.82, 4.55), material, "teal", 10),
        box("Isotope Kitchen west front counter", (1.52, 0.28, 0.64), (-1.24, -1.43, 0.66),
            material, "teal", 0.014),
        box("Isotope Kitchen east front counter", (1.52, 0.28, 0.64), (1.24, -1.43, 0.66),
            material, "teal", 0.014),
        box("Isotope Kitchen west front glazing", (1.36, 0.06, 0.84), (-1.24, -1.61, 1.39),
            material, "glass", 0.006),
        box("Isotope Kitchen front chrome sill", (4.12, 0.08, 0.12), (0, -1.60, 0.98),
            material, "chrome", 0.006),
    ]
    # The vault is visibly load-bearing from both the public front and service
    # rear. Teal ribs prevent its cream shell from reading as an untextured blob.
    for y, side in ((-1.15, "front"), (1.15, "rear")):
        previous = None
        for step in range(7):
            angle = math.pi * step / 6
            point = (math.cos(angle) * 1.10, y, 2.72 + math.sin(angle) * 0.92)
            if previous is not None:
                parts.append(beam(
                    f"Isotope Kitchen {side} vault rib {step}", previous, point, 0.035,
                    material, "teal", 6,
                ))
            previous = point
    # Frame the large side panes into their walls; the glazing stays proud like
    # the plate, but no longer reads as a floating colored card.
    for side, x, sign in (("west", -2.255, -1), ("east", 2.255, 1)):
        for y in (-1.17, 0.09):
            parts.append(beam(
                f"Isotope Kitchen {side} window jamb {y}", (x, y, 0.80), (x, y, 1.90),
                0.035, material, "chrome", 6,
            ))
        parts.extend((
            beam(f"Isotope Kitchen {side} window sill", (x, -1.17, 0.80), (x, 0.09, 0.80),
                 0.035, material, "chrome", 6),
            beam(f"Isotope Kitchen {side} window head", (x, -1.17, 1.90), (x, 0.09, 1.90),
                 0.035, material, "chrome", 6),
        ))
    # Warm hanging hoods and sample vials make the kitchen's function legible
    # while the teal chemistry keeps the satire playful rather than clinical.
    for index, x in enumerate((-1.10, 0.0, 1.10), 1):
        parts.extend((
            cylinder(f"Isotope Kitchen hood drop {index}", 0.055, 0.58, (x, -0.18, 2.38),
                     material, "dark", 8),
            sphere(f"Isotope Kitchen hood bell {index}", 0.34, (x, -0.18, 2.04), material,
                   "chrome", 12, 6),
            torus(f"Isotope Kitchen hood teal ring {index}", 0.29, 0.035, (x, -0.18, 1.98),
                  material, "teal"),
            cylinder(f"Isotope Kitchen hood lamp {index}", 0.10, 0.19, (x, -0.18, 1.76),
                     material, "amber", 8),
        ))
    for index, x in enumerate((0.36, 0.70, 1.04, 1.38), 1):
        parts.extend((
            cylinder(f"Isotope Kitchen sample vial {index}", 0.075, 0.31, (x, -1.56, 1.31),
                     material, "glass", 8),
            cylinder(f"Isotope Kitchen sample cap {index}", 0.085, 0.07, (x, -1.56, 1.49),
                     material, "chrome", 8),
        ))
    # Two jointed tongs are attached to the rear work wall; their open claw
    # silhouette is readable from both front quarters.
    for side, x in (("west", -1.30), ("east", 1.34)):
        sign = -1 if x < 0 else 1
        parts.extend((
            cylinder(f"Isotope Kitchen {side} tong shoulder", 0.15, 0.12, (x, 1.31, 2.05),
                     material, "chrome", 10, rotation=(math.pi / 2, 0, 0)),
            beam(f"Isotope Kitchen {side} tong upper", (x, 1.23, 2.05),
                 (x - sign * 0.36, 0.74, 1.68), 0.055, material, "dark", 8),
            cylinder(f"Isotope Kitchen {side} tong elbow", 0.12, 0.12,
                     (x - sign * 0.36, 0.74, 1.68), material, "teal", 8,
                     rotation=(math.pi / 2, 0, 0)),
            beam(f"Isotope Kitchen {side} tong forearm", (x - sign * 0.36, 0.74, 1.68),
                 (x - sign * 0.54, 0.28, 1.24), 0.045, material, "chrome", 8),
            beam(f"Isotope Kitchen {side} tong claw one", (x - sign * 0.54, 0.28, 1.24),
                 (x - sign * 0.70, 0.12, 1.08), 0.028, material, "dark", 6),
            beam(f"Isotope Kitchen {side} tong claw two", (x - sign * 0.54, 0.28, 1.24),
                 (x - sign * 0.38, 0.12, 1.08), 0.028, material, "dark", 6),
        ))
    starburst(parts, "Isotope Kitchen vault medallion", (0, -1.16, 3.24), 0.44, -1, material)
    # Side/rear fittings close the all-angle read.
    for index, x in enumerate((-1.25, -0.42, 0.42, 1.25), 1):
        parts.append(box(
            f"Isotope Kitchen rear warm pane {index}", (0.58, 0.06, 0.62), (x, 1.50, 1.36),
            material, "amber" if index % 2 else "glass", 0.006,
        ))
    parts.extend((
        beam("Isotope Kitchen rear window sill", (-1.62, 1.56, 1.02), (1.62, 1.56, 1.02),
             0.035, material, "chrome", 6),
        beam("Isotope Kitchen rear window head", (-1.62, 1.56, 1.70), (1.62, 1.56, 1.70),
             0.035, material, "chrome", 6),
        beam("Isotope Kitchen rear service header", (-1.72, 1.56, 2.18), (1.72, 1.56, 2.18),
             0.055, material, "teal", 8),
        beam("Isotope Kitchen rear west riser", (-1.72, 1.56, 1.02), (-1.72, 1.56, 2.18),
             0.050, material, "dark", 8),
        beam("Isotope Kitchen rear east riser", (1.72, 1.56, 1.02), (1.72, 1.56, 2.18),
             0.050, material, "dark", 8),
    ))
    for index, x in enumerate((-1.62, -0.84, 0.0, 0.84, 1.62), 1):
        parts.append(beam(
            f"Isotope Kitchen rear window mullion {index}", (x, 1.56, 1.02), (x, 1.56, 1.70),
            0.030, material, "chrome", 6,
        ))
    starburst(parts, "Isotope Kitchen rear vault medallion", (0, 1.17, 3.24), 0.44, 1, material)
    apply_and_uv(parts)
    model = join_parts(parts, "IsotopeKitchenE6")
    model["epoch_variant"] = "E6 Atomic Mesa"
    model["identity"] = (
        "Chrome-and-enamel public kitchen with isotope vault, letter-free atom medallion, hanging warm hoods, "
        "teal sample case, paired articulated tongs, and complete side/rear service treatment"
    )
    return export_model(model, directory / "isotope-kitchen.blend", directory / "isotope-kitchen.glb")


def main():
    result = {
        "atomic_diner": build_atomic_diner(),
        "reactor_dome": build_reactor_dome(),
        "isotope_kitchen": build_isotope_kitchen(),
        "sourceBase": "origin/main@8d974f11911187136469fbd017c9598e5b2faf28",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
