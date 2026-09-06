from pathlib import Path
import hashlib
import json
import math
import subprocess

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
TEMP = Path("/tmp/gold-rush-wave13-e7")
SOURCE_DINER_BLEND_SHA = "e329a411267c43e78a2d068c4ad6341ad1d9d8825e427977877124a04d8eea17"
SOURCE_DINER_GLB_SHA = "68ec4ed82ec24c42386a2abf6ff0fc4738556be4e380a9f06bc7e3de4478fd74"
REFERENCE_SHAS = {
    "relay": (ROOT / "assets/raw/plate-e7-bld-relay-tower.png",
              "a64730578de5a8e84101812034ff6c999574860db3a6df6f337af92a86c2f965"),
    "exchange": (ROOT / "assets/raw/plate-e7-bld-the-exchange.png",
                 "767839164d47d3f9255bfe8b628bc2d6f79b23aa0278949a2489b5015aad661a"),
}

REGIONS = {
    "shadow": (0.02, 0.02, 0.23, 0.23),
    "walnut": (0.27, 0.02, 0.48, 0.23),
    "brass": (0.52, 0.02, 0.73, 0.23),
    "teal": (0.77, 0.02, 0.98, 0.23),
    "dark": (0.02, 0.27, 0.23, 0.48),
    "cream": (0.27, 0.27, 0.48, 0.48),
    "honey": (0.52, 0.27, 0.73, 0.48),
    "glass": (0.77, 0.27, 0.98, 0.48),
    "tape": (0.02, 0.52, 0.48, 0.73),
    "roof": (0.52, 0.52, 0.73, 0.73),
    "mint": (0.77, 0.52, 0.98, 0.73),
    "warm": (0.02, 0.77, 0.48, 0.98),
    "signal": (0.52, 0.77, 0.98, 0.98),
    # Exact region coordinates of the inherited E6 Atomic Diner atlas. E7
    # additions use these aliases when they join that source material.
    "e6_dark": (0.02, 0.02, 0.23, 0.23),
    "e6_teal": (0.52, 0.27, 0.73, 0.48),
    "e6_chrome": (0.77, 0.27, 0.98, 0.48),
    "e6_cream": (0.02, 0.52, 0.23, 0.73),
    "e6_amber": (0.27, 0.52, 0.48, 0.73),
    "e6_glass": (0.52, 0.52, 0.73, 0.73),
}

PALETTE = {
    "shadow": (0.055, 0.043, 0.035),
    "walnut": (0.285, 0.145, 0.075),
    "brass": (0.58, 0.365, 0.135),
    "teal": (0.055, 0.335, 0.325),
    "dark": (0.095, 0.075, 0.052),
    "cream": (0.68, 0.515, 0.285),
    "honey": (0.86, 0.485, 0.105),
    "glass": (0.075, 0.545, 0.520),
    "tape": (0.61, 0.485, 0.285),
    "roof": (0.225, 0.135, 0.080),
    "mint": (0.19, 0.475, 0.405),
    "warm": (0.54, 0.285, 0.105),
    "signal": (0.075, 0.610, 0.580),
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_references():
    for label, (path, expected) in REFERENCE_SHAS.items():
        assert sha256(path) == expected, (label, path)


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
    grain = rng.normal(0.0, 0.023, size=(y1 - y0, x1 - x0)).astype(np.float32)
    brush = 0.017 * np.sin(xx * 0.103 + seed) + 0.011 * np.sin(yy * 0.071 + seed * 0.4)
    engraved = np.where(((xx * 2 + yy + seed) % 53) < 2, -0.055, 0.0)
    base = np.asarray(color, dtype=np.float32)
    pixels[y0:y1, x0:x1, :3] = np.clip(
        base[None, None, :] + (grain + brush + engraved)[:, :, None], 0.012, 0.94,
    )
    pixels[y0:y1, x0:x1, 3] = 1.0


def make_atlas(name, seed_offset):
    pixels = np.zeros((1024, 1024, 4), dtype=np.float32)
    pixels[:, :, :3] = np.asarray((0.12, 0.078, 0.048), dtype=np.float32)
    pixels[:, :, 3] = 1.0
    for index, (region, bounds) in enumerate(REGIONS.items(), 1):
        if region.startswith("e6_"):
            continue
        paint_region(pixels, bounds, PALETTE[region], seed_offset + index * 23)
    image = bpy.data.images.new(name, width=1024, height=1024, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(pixels.ravel())
    image.update()
    TEMP.mkdir(parents=True, exist_ok=True)
    temporary = TEMP / f"{name}.png"
    image.filepath_raw = str(temporary)
    image.file_format = "PNG"
    image.save()
    packed = bpy.data.images.load(str(temporary), check_existing=False)
    packed.name = name
    packed.pack()
    bpy.data.images.remove(image)
    temporary.unlink(missing_ok=True)
    return packed


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


def cylinder(name, radius, depth, location, material, region, vertices=10, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    return tag(obj, material, region, 0.006)


def sphere(name, radius, location, material, region, segments=10, rings=5):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, radius=radius, location=location,
    )
    obj = bpy.context.object
    obj.name = name
    return tag(obj, material, region, 0)


def torus(name, major_radius, minor_radius, location, material, region,
          rotation=(0, 0, 0), major_segments=14, minor_segments=5):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius, minor_radius=minor_radius, major_segments=major_segments,
        minor_segments=minor_segments, location=location, rotation=rotation,
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


def barrel_roof(name, width, depth, spring_z, radius, material, region, segments=12):
    vertices = []
    for y in (-depth / 2, depth / 2):
        for index in range(segments + 1):
            angle = math.pi * index / segments
            vertices.append((math.cos(angle) * width / 2, y, spring_z + math.sin(angle) * radius))
    count = segments + 1
    faces = []
    for index in range(segments):
        faces.append((index, index + 1, count + index + 1, count + index))
    faces.extend((tuple(reversed(range(count))), tuple(range(count, count * 2))))
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return tag(obj, material, region, 0.016)


def parabolic_dish(name, center, radius, depth, material, region, rings=4, segments=18):
    cx, cy, cz = center
    vertices = [(cx, cy + depth, cz)]
    for ring in range(1, rings + 1):
        fraction = ring / rings
        radial = radius * fraction
        y = cy + depth * (1.0 - fraction * fraction)
        for segment in range(segments):
            angle = math.tau * segment / segments
            vertices.append((cx + math.cos(angle) * radial, y, cz + math.sin(angle) * radial))
    faces = []
    for segment in range(segments):
        faces.append((0, 1 + segment, 1 + (segment + 1) % segments))
    for ring in range(1, rings):
        first = 1 + (ring - 1) * segments
        second = 1 + ring * segments
        for segment in range(segments):
            next_segment = (segment + 1) % segments
            faces.append((first + segment, second + segment,
                          second + next_segment, first + next_segment))
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return tag(obj, material, region, 0)


def signal_arcs(parts, prefix, center, radii, material, region="signal", segments=8):
    cx, cy, cz = center
    for arc_index, radius in enumerate(radii, 1):
        previous = None
        for step in range(segments + 1):
            angle = math.radians(25 + 130 * step / segments)
            point = (cx + math.cos(angle) * radius, cy, cz + math.sin(angle) * radius)
            if previous is not None:
                parts.append(beam(
                    f"{prefix} arc {arc_index}.{step}", previous, point,
                    0.026, material, region, 5,
                ))
            previous = point


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
    blend_path.parent.mkdir(parents=True, exist_ok=True)
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
        export_cameras=False, export_lights=False, export_animations=False,
        export_materials="EXPORT",
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


def build_relay_tower():
    reset_scene()
    directory = ROOT / "assets/pilots/relay-tower-3d"
    material = make_material("RelayTowerE7PaintedMaterial", make_atlas("RelayTowerE7PaintedAtlas", 700))
    parts = [
        cylinder("Relay Tower grounded mesa foot", 2.42, 0.22, (0, 0, 0.11), material, "shadow", 20),
        box("Relay Tower civic base", (4.42, 4.02, 1.72), (0, 0, 1.00), material, "walnut", 0.028),
        barrel_roof("Relay Tower radio hall roof", 4.50, 4.10, 1.74, 0.72, material, "roof", 14),
        box("Relay Tower front portico", (3.68, 0.42, 0.72), (0, -2.02, 0.66), material, "brass", 0.020),
        box("Relay Tower front teal sill", (3.86, 0.10, 0.16), (0, -2.25, 1.06), material, "teal", 0.008),
        box("Relay Tower rear service frame", (3.40, 0.12, 1.05), (0, 2.08, 1.18), material, "dark", 0.010),
        box("Relay Tower roof tower bed", (2.52, 2.30, 0.22), (0, 0, 2.48), material, "brass", 0.014),
    ]
    for index, x in enumerate((-1.45, -0.72, 0.0, 0.72, 1.45), 1):
        parts.extend((
            box(f"Relay Tower front tube window {index}", (0.48, 0.08, 0.72),
                (x, -2.23, 1.39), material, "honey" if index % 2 else "glass", 0.006),
            beam(f"Relay Tower front mullion {index}", (x - 0.29, -2.27, 1.02),
                 (x - 0.29, -2.27, 1.78), 0.028, material, "brass", 6),
        ))
    for side, x in (("port", -2.23), ("starboard", 2.23)):
        for index, y in enumerate((-1.15, 0.0, 1.15), 1):
            parts.append(box(
                f"Relay Tower {side} signal pane {index}", (0.08, 0.64, 0.62),
                (x, y, 1.30), material, "glass" if index != 2 else "honey", 0.006,
            ))

    # Four tapered lattice legs and crossed braces are the gameplay-distance pylon read.
    lower = [(-0.94, -0.84, 2.56), (0.94, -0.84, 2.56),
             (-0.94, 0.84, 2.56), (0.94, 0.84, 2.56)]
    upper = [(-0.53, -0.47, 6.18), (0.53, -0.47, 6.18),
             (-0.53, 0.47, 6.18), (0.53, 0.47, 6.18)]
    for index, (start, end) in enumerate(zip(lower, upper), 1):
        parts.append(beam(f"Relay Tower lattice leg {index}", start, end, 0.085, material, "dark", 8))
    for level in range(5):
        z0 = 2.72 + level * 0.68
        z1 = z0 + 0.68
        fraction0 = (z0 - 2.56) / (6.18 - 2.56)
        fraction1 = (z1 - 2.56) / (6.18 - 2.56)
        half_x0, half_y0 = 0.94 - 0.41 * fraction0, 0.84 - 0.37 * fraction0
        half_x1, half_y1 = 0.94 - 0.41 * fraction1, 0.84 - 0.37 * fraction1
        for face_index, (a, b, c, d) in enumerate((
            ((-half_x0, -half_y0, z0), (half_x0, -half_y0, z0),
             (-half_x1, -half_y1, z1), (half_x1, -half_y1, z1)),
            ((-half_x0, half_y0, z0), (half_x0, half_y0, z0),
             (-half_x1, half_y1, z1), (half_x1, half_y1, z1)),
            ((-half_x0, -half_y0, z0), (-half_x0, half_y0, z0),
             (-half_x1, -half_y1, z1), (-half_x1, half_y1, z1)),
            ((half_x0, -half_y0, z0), (half_x0, half_y0, z0),
             (half_x1, -half_y1, z1), (half_x1, half_y1, z1)),
        ), 1):
            parts.extend((
                beam(f"Relay Tower brace {level + 1}.{face_index}a", a, d, 0.035,
                     material, "brass", 6),
                beam(f"Relay Tower brace {level + 1}.{face_index}b", b, c, 0.035,
                     material, "brass", 6),
            ))
    parts.extend((
        box("Relay Tower search platform", (1.78, 1.62, 0.18), (0, 0, 6.28), material, "brass", 0.012),
        beam("Relay Tower dish pedestal", (0, 0, 6.34), (0, 0, 6.92), 0.14, material, "dark", 10),
        parabolic_dish("Relay Tower great search dish", (0, -0.18, 7.63), 1.38, 0.38,
                       material, "brass", 5, 20),
        torus("Relay Tower dish rim", 1.33, 0.045, (0, -0.20, 7.63), material,
              "teal", rotation=(math.pi / 2, 0, 0), major_segments=20, minor_segments=5),
        sphere("Relay Tower dish teal focus", 0.14, (0, -0.78, 7.63), material, "glass", 10, 5),
        beam("Relay Tower dish focus arm west", (-0.78, -0.18, 7.28), (0, -0.78, 7.63),
             0.035, material, "dark", 6),
        beam("Relay Tower dish focus arm east", (0.78, -0.18, 7.28), (0, -0.78, 7.63),
             0.035, material, "dark", 6),
        beam("Relay Tower dish focus arm crown", (0, -0.18, 8.34), (0, -0.78, 7.63),
             0.035, material, "dark", 6),
    ))
    for index in range(8):
        angle = index * math.tau / 8
        parts.append(beam(
            f"Relay Tower dish engraved rib {index + 1}", (0, -0.225, 7.63),
            (math.cos(angle) * 1.24, -0.225, 7.63 + math.sin(angle) * 1.24),
            0.024, material, "dark", 5,
        ))
    signal_arcs(parts, "Relay Tower broadcast", (0, -0.86, 7.55), (1.65, 2.03, 2.42), material)

    # Two linked/searching cells carry the plate's side silhouette and visible load paths.
    for side, x in (("port", -3.12), ("starboard", 3.12)):
        sign = -1 if x < 0 else 1
        parts.extend((
            cylinder(f"Relay Tower {side} cell", 0.54, 1.26, (x, 0, 3.28), material,
                     "glass", 14),
            cylinder(f"Relay Tower {side} cell crown", 0.61, 0.16, (x, 0, 3.92), material,
                     "brass", 14),
            cylinder(f"Relay Tower {side} cell foot", 0.61, 0.16, (x, 0, 2.64), material,
                     "dark", 14),
            beam(f"Relay Tower {side} cell truss upper", (sign * 0.74, 0, 4.45),
                 (x, 0, 3.88), 0.065, material, "brass", 8),
            beam(f"Relay Tower {side} cell truss lower", (sign * 0.90, 0, 3.02),
                 (x, 0, 2.70), 0.065, material, "dark", 8),
            beam(f"Relay Tower {side} signal pipe", (sign * 1.02, -0.22, 3.32),
                 (x - sign * 0.54, -0.22, 3.32), 0.075, material, "teal", 8),
            sphere(f"Relay Tower {side} cell finial", 0.11, (x, 0, 4.15), material,
                   "signal", 8, 4),
        ))
    # Rear service face is a working cable wall, not an unfinished dark plane.
    for index, x in enumerate((-1.26, -0.42, 0.42, 1.26), 1):
        parts.extend((
            box(f"Relay Tower rear cable hatch {index}", (0.62, 0.08, 0.68),
                (x, 2.34, 1.18), material, "walnut", 0.008),
            cylinder(f"Relay Tower rear cable dial {index}", 0.12, 0.08,
                     (x, 2.41, 1.35), material, "glass" if index % 2 else "honey", 10,
                     rotation=(math.pi / 2, 0, 0)),
            beam(f"Relay Tower rear cable drop {index}", (x, 2.42, 1.05),
                 (x + (0.18 if index % 2 else -0.18), 2.42, 0.72),
                 0.025, material, "brass", 5),
        ))
    apply_and_uv(parts)
    model = join_parts(parts, "RelayTowerE7")
    model["epoch_variant"] = "E7 Signal Mesa"
    model["identity"] = (
        "Grounded walnut radio hall with tapered lattice pylon, true concave search dish, "
        "two linked signal cells, honey tube windows, and concentric engraved broadcast arcs"
    )
    model["reference_sha256"] = REFERENCE_SHAS["relay"][1]
    return export_model(model, directory / "relay-tower.blend", directory / "relay-tower.glb")


def add_reel(parts, prefix, center, radius, material, region="tape"):
    x, y, z = center
    parts.extend((
        cylinder(f"{prefix} reel", radius, 0.15, center, material, region, 14,
                 rotation=(math.pi / 2, 0, 0)),
        cylinder(f"{prefix} hub", radius * 0.25, 0.19, (x, y - 0.02, z), material,
                 "teal", 10, rotation=(math.pi / 2, 0, 0)),
    ))
    for index in range(6):
        angle = index * math.tau / 6
        parts.append(cylinder(
            f"{prefix} punch {index + 1}", radius * 0.065, 0.20,
            (x + math.cos(angle) * radius * 0.56, y - 0.035,
             z + math.sin(angle) * radius * 0.56), material, "shadow", 6,
            rotation=(math.pi / 2, 0, 0),
        ))


def build_exchange():
    reset_scene()
    directory = ROOT / "assets/pilots/exchange-3d"
    material = make_material("ExchangeE7PaintedMaterial", make_atlas("ExchangeE7PaintedAtlas", 1700))
    parts = [
        box("Exchange grounded plinth", (5.72, 4.46, 0.20), (0, 0, 0.10), material, "shadow", 0.024),
        box("Exchange walnut switchboard hall", (5.42, 4.10, 2.58), (0, 0.08, 1.48), material, "walnut", 0.028),
        barrel_roof("Exchange signal hall roof", 5.54, 4.20, 2.78, 1.08, material, "roof", 16),
        box("Exchange public counter wing", (5.64, 0.92, 1.30), (0, -2.00, 0.82), material, "cream", 0.025),
        box("Exchange teal counter belt", (5.68, 0.12, 0.22), (0, -2.51, 1.18), material, "teal", 0.008),
        box("Exchange rear cable gallery", (4.42, 0.28, 1.34), (0, 2.16, 1.52), material, "dark", 0.018),
        box("Exchange roof service spine", (3.70, 1.22, 0.26), (0.28, 0.28, 3.66), material, "brass", 0.016),
    ]
    # Plaza-facing switchboard: large, readable, and pictogram-only.
    for index, x in enumerate((-2.06, -1.38, -0.69, 0.0, 0.69, 1.38, 2.06), 1):
        parts.extend((
            box(f"Exchange switchboard bay {index}", (0.54, 0.12, 0.62),
                (x, -2.49, 1.53), material, "dark", 0.008),
            cylinder(f"Exchange switchboard dial {index}", 0.13, 0.08,
                     (x, -2.58, 1.65), material, "glass" if index % 2 else "honey", 10,
                     rotation=(math.pi / 2, 0, 0)),
            cylinder(f"Exchange switchboard jack left {index}", 0.045, 0.08,
                     (x - 0.12, -2.58, 1.38), material, "teal", 6,
                     rotation=(math.pi / 2, 0, 0)),
            cylinder(f"Exchange switchboard jack right {index}", 0.045, 0.08,
                     (x + 0.12, -2.58, 1.38), material, "honey", 6,
                     rotation=(math.pi / 2, 0, 0)),
        ))
    # Retained social annex: booths and an unmistakable jukebox remain at the public edge.
    for side, x in (("west", -2.12), ("east", 2.12)):
        parts.extend((
            box(f"Exchange {side} curved booth", (0.82, 0.62, 0.72),
                (x, -1.84, 0.66), material, "mint", 0.10),
            cylinder(f"Exchange {side} booth table", 0.26, 0.10,
                     (x, -2.18, 1.08), material, "brass", 12),
        ))
    parts.extend((
        box("Exchange retained jukebox body", (0.68, 0.36, 1.16), (-1.62, -2.33, 0.78),
            material, "walnut", 0.10),
        cylinder("Exchange retained jukebox arch", 0.33, 0.38, (-1.62, -2.32, 1.34),
                 material, "honey", 12, rotation=(math.pi / 2, 0, 0)),
        box("Exchange retained jukebox teal window", (0.38, 0.08, 0.44),
            (-1.62, -2.55, 0.94), material, "glass", 0.012),
    ))

    # Vacuum-tube skyline and looped punch tape are the blind-test signature.
    for index, x in enumerate((-2.05, -1.36, -0.68, 0.0, 0.68, 1.36, 2.05), 1):
        parts.extend((
            cylinder(f"Exchange roof tube socket {index}", 0.16, 0.14,
                     (x, -0.18, 3.82), material, "brass", 10),
            cylinder(f"Exchange roof honey tube {index}", 0.105, 0.66,
                     (x, -0.18, 4.20 + (0.10 if index % 2 else 0.0)), material,
                     "honey" if index % 2 else "glass", 10),
            sphere(f"Exchange roof tube cap {index}", 0.11,
                   (x, -0.18, 4.53 + (0.10 if index % 2 else 0.0)), material,
                   "brass", 8, 4),
        ))
    add_reel(parts, "Exchange west roof", (-1.62, -0.02, 4.82), 0.46, material)
    add_reel(parts, "Exchange center roof", (0.18, -0.02, 4.92), 0.52, material)
    add_reel(parts, "Exchange east roof", (1.82, -0.02, 4.80), 0.42, material)
    # Two visible tape loops, drawn as supported segmented ribbons.
    for loop_index, (x0, x1, crown) in enumerate(((-1.62, 0.18, 5.66), (0.18, 1.82, 5.48)), 1):
        previous = (x0, -0.11, 4.90)
        for step in range(1, 9):
            fraction = step / 8
            point = (x0 + (x1 - x0) * fraction, -0.11,
                     4.90 + math.sin(math.pi * fraction) * (crown - 4.90))
            parts.append(beam(
                f"Exchange tape loop {loop_index}.{step}", previous, point,
                0.055, material, "tape", 5,
            ))
            previous = point
    # Dome + signal crown tie the annex to the E7 plate without resort-scale polish.
    parts.extend((
        cylinder("Exchange roof dome drum", 0.68, 0.24, (-1.78, 0.92, 3.88),
                 material, "brass", 16),
        sphere("Exchange roof teal dome", 0.62, (-1.78, 0.92, 4.33),
               material, "glass", 16, 8),
        cylinder("Exchange signal mast", 0.075, 1.34, (2.26, 0.86, 4.42),
                 material, "dark", 8),
        sphere("Exchange signal mast finial", 0.12, (2.26, 0.86, 5.12),
               material, "signal", 8, 4),
    ))
    signal_arcs(parts, "Exchange roof signal", (2.26, 0.78, 4.68), (0.42, 0.72, 1.02), material, segments=6)
    # Complete side and rear service faces.
    for side, x in (("west", -2.76), ("east", 2.76)):
        for index, y in enumerate((-1.12, 0.08, 1.28), 1):
            parts.append(box(
                f"Exchange {side} tube window {index}", (0.08, 0.62, 0.72),
                (x, y, 1.58), material, "glass" if index == 2 else "honey", 0.006,
            ))
    for index, x in enumerate((-1.74, -0.58, 0.58, 1.74), 1):
        parts.extend((
            box(f"Exchange rear service door {index}", (0.82, 0.08, 0.94),
                (x, 2.34, 1.20), material, "dark", 0.010),
            cylinder(f"Exchange rear cable spool {index}", 0.20, 0.10,
                     (x, 2.41, 1.64), material, "tape", 10,
                     rotation=(math.pi / 2, 0, 0)),
            cylinder(f"Exchange rear live jack {index}", 0.075, 0.09,
                     (x, 2.44, 1.16), material, "glass" if index % 2 else "honey", 8,
                     rotation=(math.pi / 2, 0, 0)),
        ))
    apply_and_uv(parts)
    model = join_parts(parts, "ExchangeE7")
    model["epoch_variant"] = "E7 Signal Mesa"
    model["identity"] = (
        "Walnut switchboard hall grown beside a retained social counter and jukebox, with seven "
        "public jack bays, honey vacuum tubes, three punch-tape reels, dome, and complete cable gallery"
    )
    model["reference_sha256"] = REFERENCE_SHAS["exchange"][1]
    return export_model(model, directory / "exchange.blend", directory / "exchange.glb")


def extract_source(path, ref, source, expected):
    if path.exists() and sha256(path) == expected:
        return path
    TEMP.mkdir(parents=True, exist_ok=True)
    target = TEMP / path.name
    with target.open("wb") as handle:
        subprocess.run(["git", "show", f"{ref}:{source}"], cwd=ROOT, stdout=handle, check=True)
    assert sha256(target) == expected
    return target


def build_net_cafe():
    source_blend = extract_source(
        ROOT / "assets/pilots/tavern-3d/tavern.e6.blend",
        "origin/sol/mesa-town-e6-pilot",
        "assets/pilots/tavern-3d/tavern.e6.blend",
        SOURCE_DINER_BLEND_SHA,
    )
    source_glb = extract_source(
        ROOT / "assets/pilots/tavern-3d/tavern.e6.glb",
        "origin/sol/mesa-town-e6-pilot",
        "assets/pilots/tavern-3d/tavern.e6.glb",
        SOURCE_DINER_GLB_SHA,
    )
    assert sha256(source_glb) == SOURCE_DINER_GLB_SHA
    bpy.ops.wm.open_mainfile(filepath=str(source_blend))
    model = bpy.data.objects["TownTavernE6AtomicDiner"]
    material = model.data.materials[0]
    parts = []
    # Three exterior booth terminals make the A2 requirement visible without deleting the diner.
    for index, x in enumerate((-0.92, 0.0, 0.92), 1):
        parts.extend((
            box(f"Net Cafe booth terminal body {index}", (0.56, 0.14, 0.54),
                (x, -1.61, 1.22), material, "e6_dark", 0.012),
            box(f"Net Cafe booth terminal screen {index}", (0.38, 0.06, 0.26),
                (x, -1.65, 1.31), material, "e6_glass", 0.006),
            beam(f"Net Cafe booth terminal aerial {index}", (x, -1.64, 1.50),
                 (x + 0.10, -1.64, 1.78), 0.022, material, "e6_chrome", 5),
            sphere(f"Net Cafe booth terminal dot {index}", 0.045,
                   (x + 0.10, -1.64, 1.80), material, "e6_amber", 8, 4),
        ))
    # The jukebox remains in the inherited 13,904-triangle diner shell; new tape readers flank it.
    for side, x in (("west", -1.46), ("east", 1.46)):
        parts.extend((
            cylinder(f"Net Cafe {side} tape reel", 0.22, 0.08,
                     (x, -1.64, 2.13), material, "e6_cream", 12,
                     rotation=(math.pi / 2, 0, 0)),
            cylinder(f"Net Cafe {side} tape hub", 0.07, 0.10,
                     (x, -1.64, 2.13), material, "e6_teal", 8,
                     rotation=(math.pi / 2, 0, 0)),
            beam(f"Net Cafe {side} tape drop", (x, -1.64, 1.95),
                 (x + (0.18 if x < 0 else -0.18), -1.64, 1.58),
                 0.030, material, "e6_cream", 5),
        ))
    # Silhouette-level signal crown: compact, footprint-safe, and visibly attached to the diner roof.
    parts.extend((
        cylinder("Net Cafe roof signal foot", 0.22, 0.16, (0.86, 0.34, 4.58),
                 material, "e6_chrome", 10),
        beam("Net Cafe roof signal mast", (0.86, 0.34, 4.62), (0.86, 0.34, 6.16),
             0.065, material, "e6_dark", 7),
        parabolic_dish("Net Cafe roof relay dish", (0.86, 0.18, 6.34), 0.66, 0.20,
                       material, "e6_chrome", 3, 12),
        sphere("Net Cafe roof relay focus", 0.090, (0.86, -0.13, 6.34),
               material, "e6_glass", 8, 4),
        beam("Net Cafe roof focus arm west", (0.48, 0.18, 6.04),
             (0.86, -0.13, 6.34), 0.024, material, "e6_dark", 5),
        beam("Net Cafe roof focus arm east", (1.24, 0.18, 6.04),
             (0.86, -0.13, 6.34), 0.024, material, "e6_dark", 5),
    ))
    signal_arcs(parts, "Net Cafe roof broadcast", (0.86, -0.16, 6.24),
                (0.88, 1.18), material, "e6_teal", segments=5)
    for part in parts:
        part.modifiers.clear()
    apply_and_uv(parts)
    bpy.ops.object.select_all(action="DESELECT")
    model.select_set(True)
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = model
    bpy.ops.object.join()
    model.name = "TownTavernE7NetCafe"
    model.data.name = "TownTavernE7NetCafeMesh"
    for polygon in model.data.polygons:
        polygon.material_index = 0
    while len(model.data.materials) > 1:
        model.data.materials.pop(index=len(model.data.materials) - 1)
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    model["epoch_variant"] = "E7 Signal Mesa"
    model["identity_transform"] = (
        "Atomic Diner retained in full, including its jukebox; public booth terminals, tape readers, "
        "and a footprint-safe roof relay dish grow the social hub into the Net Cafe"
    )
    model["source_e6_blend_sha256"] = SOURCE_DINER_BLEND_SHA
    model["source_e6_glb_sha256"] = SOURCE_DINER_GLB_SHA
    return export_model(model, HERE / "tavern.e7.blend", HERE / "tavern.e7.glb")


def main():
    assert_references()
    result = {
        "relay_tower": build_relay_tower(),
        "exchange": build_exchange(),
        "net_cafe": build_net_cafe(),
        "sourceBase": "origin/main@88ea5d9bca59dca64f35766b466cc2755751dcbb",
        "sourceE6Pilot": "origin/sol/mesa-town-e6-pilot@cfdff259c5d3f271f2022b23341d1da4a6f0c4f2",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
