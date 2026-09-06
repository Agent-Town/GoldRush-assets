from pathlib import Path
import hashlib
import json
import math

import bpy
import bmesh
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

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
    "dark": (0.080, 0.066, 0.052),
    "timber": (0.40, 0.245, 0.130),
    "teal": (0.095, 0.390, 0.375),
    "chrome": (0.73, 0.660, 0.490),
    "roof": (0.45, 0.165, 0.105),
    "cream": (0.74, 0.585, 0.335),
    "amber": (0.82, 0.405, 0.085),
    "glass": (0.065, 0.565, 0.535),
    "coral": (0.63, 0.270, 0.180),
    "shadow_teal": (0.032, 0.155, 0.155),
}

SOURCES = {
    "sunline_mount": ROOT / "assets/pilots/run3d/turret.blend",
    "glow_fence": ROOT / "assets/pilots/run3d/palisade.blend",
    "isotope_institute": ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.e5.blend",
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
    grain = rng.normal(0.0, 0.024, size=(y1 - y0, x1 - x0)).astype(np.float32)
    brush = 0.018 * np.sin(xx * 0.111 + seed) + 0.012 * np.sin(yy * 0.071 + seed * 0.7)
    hatch = np.where(((xx + yy * 2 + seed) % 47) < 2, -0.060, 0.0)
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
        paint_region(pixels, bounds, PALETTE[region], index * 23)
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
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Linear"
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    return material


def atomicize_material(model, name):
    source_material = model.data.materials[0]
    source_texture = next(node for node in source_material.node_tree.nodes if node.type == "TEX_IMAGE")
    source_image = source_texture.image
    width, height = source_image.size
    source = np.asarray(source_image.pixels[:], dtype=np.float32).reshape((height, width, 4)).copy()
    rgb = source[:, :, :3]
    luminance = rgb @ np.asarray((0.2126, 0.7152, 0.0722), dtype=np.float32)
    warm = np.stack((luminance * 1.18 + 0.065, luminance * 1.00 + 0.055,
                     luminance * 0.72 + 0.035), axis=2)
    teal_mask = (rgb[:, :, 1] > rgb[:, :, 0] * 1.05) & (rgb[:, :, 2] > rgb[:, :, 0] * 0.86)
    teal = np.stack((luminance * 0.32, luminance * 0.84 + 0.025, luminance * 0.80 + 0.025), axis=2)
    source[:, :, :3] = np.clip(np.where(teal_mask[:, :, None], teal, warm), 0.012, 0.90)
    for index, region in enumerate(REGIONS, 101):
        paint_region(source, REGIONS[region], PALETTE[region], index)
    image = save_and_pack_image(f"{name}PaintedAtlas", source)
    material = make_material(f"{name}PaintedMaterial", image)
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


def sphere(name, radius, location, material, region, segments=12, rings=6, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, radius=radius, location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
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
    faces = [(0, 1, 5, 4), (4, 5, 2, 3), (0, 4, 3), (1, 2, 5), (0, 3, 2, 1)]
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


def parabolic_dish(name, center, radius, depth, material, region, segments=20, rings=4):
    cx, cy, cz = center
    vertices = [(cx, cy + depth, cz)]
    for ring in range(1, rings + 1):
        fraction = ring / rings
        ring_radius = radius * fraction
        y = cy + depth * (1.0 - fraction * fraction)
        for index in range(segments):
            angle = index * math.tau / segments
            vertices.append((cx + math.cos(angle) * ring_radius, y, cz + math.sin(angle) * ring_radius))
    faces = []
    for index in range(segments):
        faces.append((0, 1 + index, 1 + (index + 1) % segments))
    for ring in range(1, rings):
        inner = 1 + (ring - 1) * segments
        outer = 1 + ring * segments
        for index in range(segments):
            faces.append((inner + index, outer + index, outer + (index + 1) % segments,
                          inner + (index + 1) % segments))
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    tag(obj, material, region, 0)
    solidify = obj.modifiers.new("Painted dish thickness", "SOLIDIFY")
    solidify.thickness = 0.035
    solidify.offset = 0.0
    return obj


def starburst(parts, prefix, center, radius, face_y, material, double_sided=False):
    cx, cy, cz = center
    parts.extend((
        cylinder(f"{prefix} face", radius * 0.77, 0.055, center, material, "teal", 16,
                 rotation=(math.pi / 2, 0, 0)),
        torus(f"{prefix} rim", radius * 0.82, radius * 0.075, center, material, "chrome",
              rotation=(math.pi / 2, 0, 0)),
    ))
    faces = (face_y, -face_y) if double_sided else (face_y,)
    for face_index, direction in enumerate(faces, 1):
        for index in range(8):
            angle = index * math.tau / 8
            inner = (cx + math.cos(angle) * radius * 0.20, cy + direction * 0.085,
                     cz + math.sin(angle) * radius * 0.20)
            outer = (cx + math.cos(angle) * radius * 0.61, cy + direction * 0.085,
                     cz + math.sin(angle) * radius * 0.61)
            parts.append(beam(f"{prefix} ray {face_index}.{index}", inner, outer,
                              radius * 0.035, material, "amber", 6))
            parts.append(cylinder(
                f"{prefix} pip {face_index}.{index}", radius * 0.06, 0.065,
                (outer[0], outer[1] + direction * 0.025, outer[2]), material,
                "glass" if index % 2 == 0 else "amber", 8, rotation=(math.pi / 2, 0, 0),
            ))


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


def join_parts(parts, name, inherited=None):
    bpy.ops.object.select_all(action="DESELECT")
    if inherited is not None:
        inherited.select_set(True)
    for part in parts:
        part.select_set(True)
    active = inherited or parts[0]
    bpy.context.view_layer.objects.active = active
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


def export_model(model, blend_path, glb_path, budget=15_000):
    blend_path.parent.mkdir(parents=True, exist_ok=True)
    minimum_z = min(vertex.co.z for vertex in model.data.vertices)
    if abs(minimum_z) > 1e-7:
        for vertex in model.data.vertices:
            vertex.co.z -= minimum_z
        model.data.update()
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
    assert triangles <= budget, (model.name, triangles, budget)
    assert len(model.data.materials) == 1
    return {
        "blend": str(blend_path.relative_to(ROOT)),
        "glb": str(glb_path.relative_to(ROOT)),
        "sha256": sha256(glb_path),
        "triangles": triangles,
        "dimensions": [round(value, 6) for value in model.dimensions],
    }


def build_appliance_pen():
    reset_scene()
    directory = ROOT / "assets/pilots/appliance-pen-3d"
    material = make_material("AppliancePenPaintedMaterial", make_atlas("AppliancePenPaintedAtlas"))
    parts = [
        box("Appliance Pen grounded pad", (4.50, 3.30, 0.18), (0, 0, 0.09), material, "dark", 0.018),
        box("Appliance Pen enamel floor", (4.34, 3.14, 0.16), (0, 0, 0.24), material, "teal", 0.016),
        box("Appliance Pen wrangler booth", (1.42, 1.06, 1.48), (-1.35, 0.80, 1.02), material, "cream", 0.018),
        barrel_roof("Appliance Pen booth canopy", 1.58, 1.22, 1.74, 0.36, material, "chrome", 10),
        box("Appliance Pen booth window", (0.72, 0.06, 0.52), (-1.35, 0.24, 1.22), material, "glass", 0.006),
        cylinder("Appliance Pen booth dial", 0.22, 0.07, (-1.35, 0.18, 0.62), material, "amber", 12,
                 rotation=(math.pi / 2, 0, 0)),
    ]
    for x in (-2.05, 2.05):
        for y in (-1.42, 1.42):
            parts.extend((
                cylinder(f"Appliance Pen corner post {x}.{y}", 0.10, 1.62, (x, y, 1.02), material, "dark", 8),
                cylinder(f"Appliance Pen corner cap {x}.{y}", 0.15, 0.12, (x, y, 1.86), material, "chrome", 8),
                sphere(f"Appliance Pen corner pip {x}.{y}", 0.09, (x, y, 1.98), material, "glass", 8, 4),
            ))
    for y in (-1.42, 1.42):
        for z in (0.72, 1.32):
            parts.append(beam(f"Appliance Pen long fence {y}.{z}", (-2.05, y, z), (2.05, y, z),
                              0.055, material, "chrome", 6))
        for x in (-1.04, 0.0, 1.04):
            parts.append(cylinder(f"Appliance Pen long pip {y}.{x}", 0.055, 0.07, (x, y, 1.32),
                                  material, "glass", 8, rotation=(math.pi / 2, 0, 0)))
    for x in (-2.05, 2.05):
        for z in (0.72, 1.32):
            parts.append(beam(f"Appliance Pen side fence {x}.{z}", (x, -1.42, z), (x, 1.42, z),
                              0.055, material, "chrome", 6))

    # A cheerful captured-appliance menagerie: one mower grazes, a toaster
    # waits by the booth, and a little vacuum has been parked nose-in.
    parts.extend((
        box("Appliance Pen mower body", (1.05, 0.72, 0.38), (0.78, 0.47, 0.55), material, "coral", 0.05),
        cylinder("Appliance Pen mower west wheel", 0.22, 0.12, (0.35, 0.18, 0.48), material, "dark", 10,
                 rotation=(math.pi / 2, 0, 0)),
        cylinder("Appliance Pen mower east wheel", 0.22, 0.12, (1.21, 0.18, 0.48), material, "dark", 10,
                 rotation=(math.pi / 2, 0, 0)),
        beam("Appliance Pen mower handle left", (0.48, 0.72, 0.72), (0.22, 1.18, 1.34), 0.035,
             material, "chrome", 6),
        beam("Appliance Pen mower handle right", (1.08, 0.72, 0.72), (0.82, 1.18, 1.34), 0.035,
             material, "chrome", 6),
        box("Appliance Pen toaster body", (0.62, 0.42, 0.58), (-0.38, -0.62, 0.62), material, "chrome", 0.08),
        box("Appliance Pen toaster slot", (0.34, 0.12, 0.06), (-0.38, -0.62, 0.93), material, "dark", 0.008),
        sphere("Appliance Pen toaster lamp", 0.07, (-0.38, -0.84, 0.66), material, "amber", 8, 4),
        cylinder("Appliance Pen vacuum drum", 0.34, 0.62, (0.04, 0.75, 0.58), material, "teal", 12),
        beam("Appliance Pen vacuum snout", (0.04, 0.45, 0.47), (-0.38, 0.02, 0.35), 0.075,
             material, "chrome", 8),
        beam("Appliance Pen copper tether", (1.20, 0.74, 0.62), (2.03, 1.36, 0.82), 0.025,
             material, "amber", 6),
    ))
    starburst(parts, "Appliance Pen booth starburst", (-1.35, 0.18, 1.55), 0.31, -1, material)
    apply_and_uv(parts)
    model = join_parts(parts, "AppliancePenE6")
    model["epoch_variant"] = "E6 Atomic Mesa"
    model["identity"] = "Fenced wrangler yard with pacified toaster, mower, vacuum, copper tether, booth, and pictogram-only starburst"
    return export_model(model, directory / "appliance-pen.blend", directory / "appliance-pen.glb")


def add_clock_face(parts, prefix, y, direction, z, material, radius=0.84):
    parts.extend((
        cylinder(f"{prefix} dial", radius, 0.10, (0, y, z), material, "glass", 20,
                 rotation=(math.pi / 2, 0, 0)),
        torus(f"{prefix} rim", radius * 0.92, 0.07, (0, y + direction * 0.02, z), material, "chrome",
              rotation=(math.pi / 2, 0, 0), major_segments=20),
        beam(f"{prefix} long hand", (0, y + direction * 0.09, z), (0.18, y + direction * 0.09, z + 0.48),
             0.035, material, "amber", 6),
        beam(f"{prefix} short hand", (0, y + direction * 0.10, z), (-0.36, y + direction * 0.10, z - 0.10),
             0.045, material, "dark", 6),
        cylinder(f"{prefix} hub", 0.12, 0.14, (0, y + direction * 0.12, z), material, "amber", 10,
                 rotation=(math.pi / 2, 0, 0)),
    ))
    for index in range(12):
        angle = index * math.tau / 12
        parts.append(cylinder(
            f"{prefix} tick {index}", 0.045, 0.12,
            (math.cos(angle) * radius * 0.70, y + direction * 0.12, z + math.sin(angle) * radius * 0.70),
            material, "cream" if index % 3 else "amber", 6, rotation=(math.pi / 2, 0, 0),
        ))


def build_decay_clock():
    reset_scene()
    directory = ROOT / "assets/pilots/decay-clock-3d"
    material = make_material("DecayClockPaintedMaterial", make_atlas("DecayClockPaintedAtlas"))
    parts = [
        box("Decay Clock grounded plinth", (3.32, 2.72, 0.22), (0, 0, 0.11), material, "dark", 0.025),
        box("Decay Clock enamel terrace", (3.12, 2.52, 0.18), (0, 0, 0.31), material, "teal", 0.018),
        box("Decay Clock lower works", (2.42, 2.02, 1.34), (0, 0, 1.02), material, "cream", 0.026),
        box("Decay Clock middle shaft", (1.76, 1.52, 1.62), (0, 0, 2.49), material, "timber", 0.024),
        box("Decay Clock dial house", (2.28, 1.72, 1.98), (0, 0, 4.02), material, "cream", 0.032),
        wedge_roof("Decay Clock copper cap", 2.48, 1.96, 5.00, 5.76, material, "roof"),
        cylinder("Decay Clock finial mast", 0.08, 0.62, (0, 0, 6.02), material, "dark", 8),
        sphere("Decay Clock finial", 0.16, (0, 0, 6.38), material, "amber", 10, 5),
        box("Decay Clock front service door", (0.74, 0.08, 1.02), (0, -1.05, 0.90), material, "dark", 0.012),
        box("Decay Clock rear service grille", (1.20, 0.08, 0.66), (0, 1.05, 1.05), material, "shadow_teal", 0.010),
    ]
    add_clock_face(parts, "Decay Clock public", -0.91, -1, 4.12, material)
    add_clock_face(parts, "Decay Clock rear", 0.91, 1, 4.12, material)
    for side, x, direction in (("west", -1.18, -1), ("east", 1.18, 1)):
        parts.extend((
            cylinder(f"Decay Clock {side} gauge", 0.38, 0.07, (x, 0, 4.12), material, "glass", 16,
                     rotation=(0, math.pi / 2, 0)),
            torus(f"Decay Clock {side} gauge rim", 0.40, 0.045,
                  (x + direction * 0.025, 0, 4.12), material, "chrome",
                  rotation=(0, math.pi / 2, 0), major_segments=16),
            beam(f"Decay Clock {side} gauge hand", (x + direction * 0.08, 0, 4.12),
                 (x + direction * 0.08, 0.16, 4.34), 0.028, material, "amber", 6),
        ))
    for x in (-1.28, 1.28):
        parts.extend((
            cylinder(f"Decay Clock side accumulator {x}", 0.24, 1.36, (x, 0.0, 1.12), material, "teal", 12),
            torus(f"Decay Clock lower accumulator band {x}", 0.25, 0.035, (x, 0, 0.64), material, "chrome"),
            torus(f"Decay Clock upper accumulator band {x}", 0.25, 0.035, (x, 0, 1.60), material, "chrome"),
            beam(f"Decay Clock accumulator pipe {x}", (x, 0, 1.76), (math.copysign(0.72, x), 0, 2.18),
                 0.05, material, "chrome", 8),
        ))
    for z in (2.04, 2.92):
        parts.append(torus(f"Decay Clock shaft belt {z}", 1.00, 0.055, (0, 0, z), material, "chrome",
                           major_segments=16))
    for index, x in enumerate((-0.64, -0.22, 0.22, 0.64), 1):
        parts.append(box(f"Decay Clock timer slit {index}", (0.24, 0.06, 0.58), (x, -0.80, 2.48),
                         material, "glass" if index <= 2 else "shadow_teal", 0.006))
    apply_and_uv(parts)
    model = join_parts(parts, "DecayClockE6")
    model["epoch_variant"] = "E6 Atomic Mesa"
    model["identity"] = "Town half-life clock tower with two readable teal dials, fading timer slits, accumulators, and warm copper cap"
    return export_model(model, directory / "decay-clock.blend", directory / "decay-clock.glb")


def build_catalog_warehouse():
    reset_scene()
    directory = ROOT / "assets/pilots/catalog-warehouse-3d"
    material = make_material("CatalogWarehousePaintedMaterial", make_atlas("CatalogWarehousePaintedAtlas"))
    parts = [
        box("Catalog Warehouse grounded slab", (5.50, 3.72, 0.20), (0, 0, 0.10), material, "dark", 0.020),
        box("Catalog Warehouse enamel sill", (5.34, 3.56, 0.22), (0, 0, 0.30), material, "teal", 0.018),
        box("Catalog Warehouse main shell", (5.12, 3.32, 2.48), (0, 0, 1.58), material, "timber", 0.022),
        barrel_roof("Catalog Warehouse mail-order roof", 5.30, 3.46, 2.86, 0.94, material, "roof", 14),
        box("Catalog Warehouse front loading frame", (3.32, 0.16, 2.08), (0, -1.74, 1.39), material, "chrome", 0.020),
        box("Catalog Warehouse west sliding door", (1.42, 0.08, 1.72), (-0.77, -1.84, 1.28), material, "teal", 0.010),
        box("Catalog Warehouse east sliding door", (1.42, 0.08, 1.72), (0.77, -1.84, 1.28), material, "cream", 0.010),
        beam("Catalog Warehouse door track", (-1.70, -1.81, 2.24), (1.70, -1.81, 2.24), 0.055,
             material, "dark", 8),
        box("Catalog Warehouse west side awning", (0.62, 1.64, 0.12), (-2.48, 0.56, 2.12), material,
            "chrome", 0.014, rotation=(0, math.radians(-8), 0)),
        box("Catalog Warehouse east side awning", (0.62, 1.64, 0.12), (2.48, -0.46, 2.12), material,
            "chrome", 0.014, rotation=(0, math.radians(8), 0)),
        cylinder("Catalog Warehouse rear vent", 0.17, 1.62, (1.70, 1.42, 3.50), material, "dark", 10),
        cylinder("Catalog Warehouse rear vent cap", 0.25, 0.13, (1.70, 1.42, 4.28), material, "amber", 10),
    ]
    starburst(parts, "Catalog Warehouse public seal", (0, -1.72, 3.12), 0.52, -1, material)
    starburst(parts, "Catalog Warehouse rear seal", (0, 1.72, 2.48), 0.42, 1, material)
    parts.extend((
        box("Catalog Warehouse rear service door", (2.62, 0.08, 1.30), (0, 1.72, 1.18),
            material, "shadow_teal", 0.012),
        beam("Catalog Warehouse rear service header", (-1.48, 1.78, 1.92), (1.48, 1.78, 1.92),
             0.055, material, "chrome", 8),
        beam("Catalog Warehouse rear west jamb", (-1.42, 1.78, 0.52), (-1.42, 1.78, 1.92),
             0.045, material, "chrome", 6),
        beam("Catalog Warehouse rear east jamb", (1.42, 1.78, 0.52), (1.42, 1.78, 1.92),
             0.045, material, "chrome", 6),
        beam("Catalog Warehouse rear split", (0, 1.78, 0.52), (0, 1.78, 1.82),
             0.035, material, "teal", 6),
    ))
    for side, x in (("west", -2.58), ("east", 2.58)):
        for index, y in enumerate((-0.86, 0.0, 0.86), 1):
            parts.extend((
                box(f"Catalog Warehouse {side} window {index}", (0.07, 0.46, 0.56), (x, y, 1.62),
                    material, "glass" if index != 2 else "amber", 0.006),
                beam(f"Catalog Warehouse {side} window sill {index}", (x, y - 0.26, 1.32),
                     (x, y + 0.26, 1.32), 0.035, material, "chrome", 6),
            ))
    # Starburst-stamped cargo is readable without letters and turns the depot
    # into enemy-origin lore rather than an anonymous barn.
    crate_positions = [(-1.96, -1.34, 0.64), (1.96, -1.30, 0.58), (-2.02, 1.20, 0.58), (1.92, 1.30, 0.66)]
    for index, (x, y, z) in enumerate(crate_positions, 1):
        parts.extend((
            box(f"Catalog Warehouse crate {index}", (0.70, 0.66, 0.72), (x, y, z), material,
                "cream" if index % 2 else "coral", 0.035),
            cylinder(f"Catalog Warehouse crate pip {index}", 0.11, 0.07,
                     (x, y - math.copysign(0.36, y), z + 0.02), material, "glass", 8,
                     rotation=(math.pi / 2, 0, 0)),
        ))
    for x in (-1.84, 1.84):
        parts.append(beam(f"Catalog Warehouse roof rib {x}", (x, -1.68, 2.86), (x, 1.68, 2.86),
                          0.045, material, "chrome", 6))
    apply_and_uv(parts)
    model = join_parts(parts, "CatalogWarehouseE6")
    model["epoch_variant"] = "E6 Atomic Mesa"
    model["identity"] = "Abandoned mail-order depot with loading track, barrel roof, starburst seals, side awnings, rear vent, and stamped cargo"
    return export_model(model, directory / "catalog-warehouse.blend", directory / "catalog-warehouse.glb")


def open_source(key, object_name=None):
    source = SOURCES[key]
    source_hash = sha256(source)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    candidates = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    if object_name:
        candidates = [obj for obj in candidates if obj.name == object_name]
    assert len(candidates) == 1, (key, [obj.name for obj in candidates])
    model = candidates[0]
    return model, source_hash


def build_sunline_mount():
    model, source_hash = open_source("sunline_mount", "SignalTurret")
    source_dimensions = tuple(model.dimensions)
    material = atomicize_material(model, "SunlineMount")
    # The inherited signal globe is not allowed to survive as the active head:
    # E6 explicitly replaces it with a parabolic mirror. Keep the compact tower
    # and rings, remove only vertices above the upper turntable.
    mesh = model.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.delete(bm, geom=[vertex for vertex in bm.verts if vertex.co.z > 1.22], context="VERTS")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    parts = [
        cylinder("Sunline azimuth collar", 0.32, 0.16, (0, 0, 1.28), material, "chrome", 16),
        parabolic_dish("Sunline parabolic mirror", (0, -0.15, 1.52), 0.42, 0.28,
                       material, "cream", 20, 4),
        torus("Sunline mirror rim", 0.42, 0.035, (0, -0.15, 1.52), material, "teal",
              rotation=(math.pi / 2, 0, 0), major_segments=20),
        beam("Sunline receiver arm", (0, -0.15, 1.52), (0, -0.48, 1.52), 0.035, material, "dark", 6),
        sphere("Sunline receiver", 0.09, (0, -0.51, 1.52), material, "amber", 10, 5),
        beam("Sunline west brace", (-0.34, -0.12, 1.43), (-0.25, 0.02, 1.22), 0.035,
             material, "chrome", 6),
        beam("Sunline east brace", (0.34, -0.12, 1.43), (0.25, 0.02, 1.22), 0.035,
             material, "chrome", 6),
        beam("Sunline zenith needle", (0, -0.15, 1.86), (0, -0.15, 2.015), 0.025,
             material, "dark", 6),
        sphere("Sunline zenith pip", 0.035, (0, -0.15, 2.015), material, "amber", 8, 4),
    ]
    for index in range(8):
        angle = index * math.tau / 8
        parts.append(beam(
            f"Sunline mirror ray {index}", (math.cos(angle) * 0.10, -0.18, 1.52 + math.sin(angle) * 0.10),
            (math.cos(angle) * 0.34, -0.18, 1.52 + math.sin(angle) * 0.34), 0.016,
            material, "amber", 5,
        ))
    for part in parts:
        part.modifiers.clear()
    apply_and_uv(parts)
    model = join_parts(parts, "SunlineMountE6", model)
    model["epoch_variant"] = "E6 Atomic Mesa"
    model["identity_transform"] = "Signal turret retains compact tower silhouette; upper signal is repurposed as a parabolic sunline mirror"
    model["source_blend_sha256"] = source_hash
    # Transform notes require the familiar compact sentry silhouette.
    assert model.dimensions.x <= source_dimensions[0] + 0.001
    assert model.dimensions.y <= source_dimensions[1] + 0.001
    assert model.dimensions.z <= source_dimensions[2] + 0.001
    return export_model(model, ROOT / "assets/pilots/run3d/turret.e6.blend",
                        ROOT / "assets/pilots/run3d/turret.e6.glb")


def build_glow_fence():
    model, source_hash = open_source("glow_fence", "Palisade")
    source_dimensions = tuple(model.dimensions)
    material = atomicize_material(model, "GlowFence")
    parts = []
    for face, x, direction in (("front", 0.175, 1), ("rear", -0.175, -1)):
        for index, y in enumerate((-1.10, -0.55, 0.0, 0.55, 1.10), 1):
            for z in (0.43, 0.72):
                parts.append(cylinder(
                    f"Glow Fence {face} embedded pip {index}.{z}", 0.045, 0.045,
                    (x, y, z), material, "glass" if index % 2 else "amber", 8,
                    rotation=(0, math.pi / 2, 0),
                ))
    for y in (-1.32, 1.32):
        parts.append(cylinder(f"Glow Fence chrome post cap {y}", 0.16, 0.08, (0, y, 0.98),
                              material, "chrome", 8))
    for part in parts:
        part.modifiers.clear()
    apply_and_uv(parts)
    model = join_parts(parts, "GlowFenceE6", model)
    model["epoch_variant"] = "E6 Atomic Mesa"
    model["identity_transform"] = "Original guardrail footprint and timber rhythm persist; measured starstone pips are embedded in both rails"
    model["source_blend_sha256"] = source_hash
    assert model.dimensions.x <= source_dimensions[0] + 0.001
    assert model.dimensions.y <= source_dimensions[1] + 0.001
    assert model.dimensions.z <= source_dimensions[2] + 0.001
    return export_model(model, ROOT / "assets/pilots/run3d/palisade.e6.blend",
                        ROOT / "assets/pilots/run3d/palisade.e6.glb")


def build_isotope_institute():
    model, source_hash = open_source("isotope_institute", "SchoolhouseE5")
    source_dimensions = tuple(model.dimensions)
    material = atomicize_material(model, "IsotopeInstitute")
    parts = [
        cylinder("Isotope Institute tower collar", 0.54, 0.18, (0, -0.58, 5.42), material, "chrome", 16),
        sphere("Isotope Institute observatory dome", 0.52, (0, -0.58, 5.72), material, "teal", 16, 8,
               scale=(1, 1, 0.58)),
        torus("Isotope Institute dome rim", 0.50, 0.05, (0, -0.58, 5.56), material, "chrome",
              major_segments=16),
        beam("Isotope Institute antenna", (0, -0.58, 5.96), (0, -0.58, 6.38), 0.035,
             material, "dark", 6),
        sphere("Isotope Institute antenna pip", 0.08, (0, -0.58, 6.45), material, "amber", 8, 4),
        cylinder("Isotope Institute public dial", 0.38, 0.07, (0, -1.62, 4.56), material, "glass", 16,
                 rotation=(math.pi / 2, 0, 0)),
        torus("Isotope Institute public dial rim", 0.40, 0.045, (0, -1.63, 4.56), material, "chrome",
              rotation=(math.pi / 2, 0, 0), major_segments=16),
        beam("Isotope Institute dial hand", (0, -1.65, 4.56), (0.18, -1.65, 4.78), 0.03,
             material, "amber", 6),
        box("Isotope Institute front chrome belt", (3.52, 0.08, 0.14), (0, -1.64, 2.60), material,
            "chrome", 0.006),
        box("Isotope Institute rear teal belt", (3.52, 0.08, 0.14), (0, 1.64, 2.60), material,
            "teal", 0.006),
        beam("Isotope Institute dial west bracket", (-0.24, -0.92, 4.44),
             (-0.24, -1.58, 4.44), 0.035, material, "chrome", 6),
        beam("Isotope Institute dial east bracket", (0.24, -0.92, 4.68),
             (0.24, -1.58, 4.68), 0.035, material, "chrome", 6),
    ]
    for x in (-1.62, 1.62):
        parts.extend((
            cylinder(f"Isotope Institute side gauge {x}", 0.20, 0.07, (x, -0.66, 2.05), material,
                     "glass", 12, rotation=(0, math.pi / 2, 0)),
            torus(f"Isotope Institute side gauge rim {x}", 0.22, 0.035, (x, -0.66, 2.05), material,
                  "chrome", rotation=(0, math.pi / 2, 0)),
        ))
    for part in parts:
        part.modifiers.clear()
    apply_and_uv(parts)
    model = join_parts(parts, "IsotopeInstituteE6", model)
    model["epoch_variant"] = "E6 Atomic Mesa"
    model["identity_transform"] = "Navigation School lineage persists; sextant-era tower becomes a chrome observatory dome with a public half-life dial"
    model["source_blend_sha256"] = source_hash
    assert model.dimensions.x <= 4.4
    assert model.dimensions.y <= 3.4
    assert model.dimensions.z > source_dimensions[2]
    return export_model(model, ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.e6.blend",
                        ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.e6.glb")


def main():
    result = {
        "appliance_pen": build_appliance_pen(),
        "decay_clock": build_decay_clock(),
        "catalog_warehouse": build_catalog_warehouse(),
        "sunline_mount": build_sunline_mount(),
        "glow_fence": build_glow_fence(),
        "isotope_institute": build_isotope_institute(),
        "sourceBase": "origin/main@1a58335f65645b8491e50763e10a32d12d8696f1",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
