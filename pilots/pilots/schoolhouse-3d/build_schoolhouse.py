from pathlib import Path
import hashlib
import json
import math

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REFERENCE = ROOT / "assets/processed/bld-schoolhouse.png"
BLEND = OUT / "schoolhouse.blend"
GLB = OUT / "schoolhouse.glb"
ATLAS_SIZE = 1024

REGIONS = {
    "wall": (0.02, 0.02, 0.48, 0.48),
    "roof": (0.52, 0.52, 0.98, 0.98),
    "trim": (0.02, 0.52, 0.23, 0.73),
    "door": (0.52, 0.02, 0.73, 0.48),
    "window": (0.77, 0.02, 0.98, 0.48),
    "deck": (0.27, 0.52, 0.48, 0.73),
    "stone": (0.02, 0.77, 0.23, 0.98),
    "accent": (0.27, 0.77, 0.48, 0.98),
}


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0


def source_pixels():
    image = bpy.data.images.load(str(REFERENCE), check_existing=False)
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(image.size[1], image.size[0], 4)
    return pixels


def make_atlas():
    source = source_pixels()
    atlas = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    atlas[:, :, :3] = (0.20, 0.12, 0.06)
    crops = {
        "wall": (142, 86, 318, 278), "roof": (105, 180, 340, 356),
        "trim": (48, 50, 294, 240), "door": (112, 42, 272, 218),
        "window": (95, 72, 306, 270), "deck": (38, 20, 284, 155),
        "stone": (55, 12, 330, 138), "accent": (182, 72, 326, 258),
    }
    fallback = {
        "wall": np.array((0.68, 0.54, 0.34)), "roof": np.array((0.35, 0.20, 0.10)),
        "trim": np.array((0.36, 0.22, 0.10)), "door": np.array((0.31, 0.18, 0.08)),
        "window": np.array((0.17, 0.29, 0.27)), "deck": np.array((0.43, 0.28, 0.13)),
        "stone": np.array((0.43, 0.36, 0.25)), "accent": np.array((0.25, 0.45, 0.42)),
    }
    rng = np.random.default_rng(713)
    for name, region in REGIONS.items():
        u0, v0, u1, v1 = region
        x0, y0 = int(u0 * ATLAS_SIZE), int(v0 * ATLAS_SIZE)
        x1, y1 = int(u1 * ATLAS_SIZE), int(v1 * ATLAS_SIZE)
        sx0, sy0, sx1, sy1 = crops[name]
        crop = source[sy0:sy1, sx0:sx1, :3]
        saturation = crop.max(axis=2) - crop.min(axis=2)
        painted = crop[(saturation > 0.075) & (crop.mean(axis=2) < 0.82)]
        base = np.median(painted, axis=0) if len(painted) else fallback[name]
        base = np.clip(base * 1.35, fallback[name] * 0.78, fallback[name] * 1.32)
        if name == "wall":
            base = np.array((0.66, 0.52, 0.335), dtype=np.float32)
        height, width = y1 - y0, x1 - x0
        noise = rng.normal(0, 0.025, (height, width, 1)).astype(np.float32)
        block = np.ones((height, width, 4), dtype=np.float32)
        block[:, :, :3] = np.clip(base + noise, 0.025, 0.92)
        atlas[y0:y1, x0:x1] = block

        dark = np.clip(base * 0.36, 0.018, 0.42)
        light = np.clip(base * 1.24 + 0.025, 0.04, 0.96)
        if name in ("wall", "trim", "door", "deck"):
            spacing = {"wall": 34, "trim": 46, "door": 58, "deck": 28}[name]
            for x in range(x0 + spacing, x1, spacing):
                atlas[y0:y1, x:x + 3, :3] = dark
                atlas[y0:y1, x + 3:x + 5, :3] = light
            for y in range(y0 + 18, y1, 74):
                atlas[y:y + 2, x0:x1, :3] *= 0.72
        elif name == "roof":
            row = 26
            for y in range(y0 + row, y1, row):
                atlas[y:y + 3, x0:x1, :3] = dark
                offset = 14 if ((y - y0) // row) % 2 else 0
                for x in range(x0 + offset, x1, 34):
                    atlas[max(y - row, y0):y, x:x + 2, :3] = dark
        elif name == "window":
            atlas[y0:y1, x0:x1, :3] = np.array((0.12, 0.16, 0.12))
            atlas[y0 + 5:y1 - 5, x0 + 5:x1 - 5, :3] = np.array((0.78, 0.50, 0.15))
            atlas[(y0 + y1) // 2 - 4:(y0 + y1) // 2 + 4, x0:x1, :3] = dark
            atlas[y0:y1, (x0 + x1) // 2 - 4:(x0 + x1) // 2 + 4, :3] = dark
        elif name == "stone":
            atlas[y0:y1, x0:x1, :3] = np.array((0.20, 0.31, 0.16))
            for y in range(y0 + 30, y1, 30):
                atlas[y:y + 3, x0:x1, :3] = dark
            for row, y in enumerate(range(y0, y1, 30)):
                for x in range(x0 + (18 if row % 2 else 0), x1, 38):
                    atlas[y:min(y + 30, y1), x:x + 3, :3] = dark
        elif name == "accent":
            atlas[y0:y1, x0:x1, :3] = np.array((0.68, 0.42, 0.11))
            for y in range(y0 + 24, y1, 48):
                atlas[y:y + 3, x0:x1, :3] = np.array((0.27, 0.14, 0.05))

    # Match the locked-camera painted Tavern value without changing the palette.
    atlas[:, :, :3] *= 0.78

    image = bpy.data.images.new("SchoolhousePaintedAtlas", ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(atlas.ravel())
    image.pack()
    return image


def make_material(atlas):
    material = bpy.data.materials.new("SchoolhousePaintedMaterial")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = atlas
    texture.projection = "FLAT"
    texture.extension = "REPEAT"
    texture.interpolation = "Linear"
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Roughness"].default_value = 0.9
    shader.inputs["Emission Color"].default_value = (0, 0, 0, 1)
    shader.inputs["Emission Strength"].default_value = 0.0
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def tag(obj, category, material, bevel=0.025):
    obj["atlas_region"] = category
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("Painted edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        modifier.limit_method = "ANGLE"
    return obj


def box(name, size, location, category, material, bevel=0.025):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = tuple(value / 2 for value in size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return tag(obj, category, material, bevel)


def cylinder(name, radius, depth, location, category, material, vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    return tag(obj, category, material, 0.018)


def cone(name, radius1, radius2, depth, location, category, material, vertices=12):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    return tag(obj, category, material, 0.018)


def sphere(name, radius, location, category, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    return tag(obj, category, material, 0.012)


def beam(name, start, end, thickness, category, material):
    midpoint = tuple((a + b) / 2 for a, b in zip(start, end))
    dx, dz = end[0] - start[0], end[2] - start[2]
    obj = box(name, (math.hypot(dx, dz), thickness, thickness), midpoint, category, material, 0.012)
    obj.rotation_euler[1] = -math.atan2(dz, dx)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    return obj


def prism(name, vertices, faces, category, material, bevel=0.02):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return tag(obj, category, material, bevel)


def gable_roof(name, width, depth, eave_z, ridge_z, category, material):
    x, y = width / 2, depth / 2
    vertices = [
        (-x, -y, eave_z), (x, -y, eave_z), (x, y, eave_z), (-x, y, eave_z),
        (-x, 0, ridge_z), (x, 0, ridge_z),
    ]
    faces = [(0, 1, 5, 4), (3, 4, 5, 2), (0, 4, 3), (1, 2, 5), (0, 3, 2, 1)]
    return prism(name, vertices, faces, category, material, 0.035)


def wedge(name, x0, x1, y0, y1, low_z, high_z, thickness, category, material):
    vertices = [
        (x0, y0, low_z), (x1, y0, low_z), (x1, y1, high_z), (x0, y1, high_z),
        (x0, y0, low_z - thickness), (x1, y0, low_z - thickness),
        (x1, y1, high_z - thickness), (x0, y1, high_z - thickness),
    ]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return prism(name, vertices, faces, category, material, 0.018)


def longitudinal_gable_roof(name, width, depth, eave_z, ridge_z, category, material, y=0):
    x, d = width / 2, depth / 2
    vertices = [
        (-x, y - d, eave_z), (x, y - d, eave_z), (x, y + d, eave_z), (-x, y + d, eave_z),
        (0, y - d, ridge_z), (0, y + d, ridge_z),
    ]
    faces = [(0, 4, 5, 3), (1, 2, 5, 4), (0, 1, 4), (3, 5, 2), (0, 3, 2, 1)]
    return prism(name, vertices, faces, category, material, 0.035)


def pyramid_roof(name, width, depth, eave_z, peak_z, category, material):
    x, y = width / 2, depth / 2
    vertices = [(-x, -y, eave_z), (x, -y, eave_z), (x, y, eave_z), (-x, y, eave_z), (0, 0, peak_z)]
    faces = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (0, 3, 2, 1)]
    return prism(name, vertices, faces, category, material, 0.025)


def build_schoolhouse(material):
    parts = []
    add = parts.append
    add(box("One-room full wrap", (3.58, 2.98, 2.38), (0, 0, 1.19), "wall", material, 0.035))
    add(longitudinal_gable_roof("Main shingled gable roof", 4.02, 3.25, 2.34, 3.42, "roof", material))

    add(box("Front porch deck", (2.82, 0.62, 0.20), (0, -1.35, 0.30), "deck", material, 0.02))
    add(longitudinal_gable_roof("Front porch gable", 2.36, 0.80, 2.06, 2.67, "roof", material, y=-1.25))
    for x in (-0.98, 0.98):
        add(box(f"Porch post {x}", (0.16, 0.16, 1.75), (x, -1.59, 1.18), "trim", material, 0.018))
        add(box(f"Porch top rail {x}", (0.12, 0.62, 0.12), (x, -1.31, 0.82), "trim", material, 0.012))
        for y in (-1.08, -1.31, -1.54):
            add(box(f"Porch baluster {x} {y}", (0.08, 0.08, 0.55), (x, y, 0.55), "trim", material, 0.01))
    for x0, x1 in ((-1.34, -1.05), (1.05, 1.34)):
        add(box(f"Front porch rail {x0}", (x1 - x0, 0.10, 0.11), ((x0 + x1) / 2, -1.57, 0.83), "trim", material, 0.01))
        for x in (x0 + 0.07, x1 - 0.07):
            add(box(f"Front porch baluster {x}", (0.07, 0.08, 0.54), (x, -1.57, 0.55), "trim", material, 0.008))
    add(box("Porch lintel", (2.14, 0.14, 0.17), (0, -1.58, 2.02), "trim", material, 0.018))
    add(beam("Left porch gable trim", (-1.10, -1.64, 2.08), (0, -1.64, 2.63), 0.11, "trim", material))
    add(beam("Right porch gable trim", (0, -1.64, 2.63), (1.10, -1.64, 2.08), 0.11, "trim", material))
    add(box("Front door", (0.78, 0.09, 1.62), (0, -1.535, 1.10), "door", material, 0.018))
    for z in (0.65, 1.08, 1.51):
        add(box(f"Door panel rail {z}", (0.58, 0.08, 0.07), (0, -1.59, z), "trim", material, 0.01))
    add(sphere("Door knob", 0.055, (0.24, -1.62, 1.08), "accent", material))
    for x in (-1.23, 1.23):
        add(box(f"Front window {x}", (0.55, 0.09, 0.92), (x, -1.535, 1.35), "window", material, 0.018))
        for z in (0.87, 1.83):
            add(box(f"Front window rail {x} {z}", (0.70, 0.13, 0.10), (x, -1.59, z), "trim", material, 0.012))
        for offset in (-0.32, 0.32):
            add(box(f"Front window stile {x} {offset}", (0.10, 0.13, 1.02), (x + offset, -1.59, 1.35), "trim", material, 0.012))
        add(box(f"Front window vertical mullion {x}", (0.055, 0.14, 0.82), (x, -1.60, 1.35), "trim", material, 0.008))
        add(box(f"Front window horizontal mullion {x}", (0.58, 0.14, 0.055), (x, -1.60, 1.35), "trim", material, 0.008))
    for x in (-0.55, 0.55):
        add(cylinder(f"Porch lamp {x}", 0.09, 0.24, (x, -1.56, 1.55), "accent", material, vertices=10))
        add(cone(f"Porch lamp cap {x}", 0.13, 0.05, 0.12, (x, -1.56, 1.73), "trim", material, vertices=10))

    # Side and back openings make the schoolhouse a complete walk-around volume.
    for y in (-0.52, 0.58):
        for x in (-1.825, 1.825):
            add(box(f"Side window {x} {y}", (0.09, 0.58, 0.90), (x, y, 1.38), "window", material, 0.018))
            for z in (0.91, 1.85):
                add(box(f"Side window rail {x} {y} {z}", (0.13, 0.70, 0.09), (x, y, z), "trim", material, 0.01))
            for offset in (-0.31, 0.31):
                add(box(f"Side window stile {x} {y} {offset}", (0.13, 0.09, 1.00), (x, y + offset, 1.38), "trim", material, 0.01))
            add(box(f"Side window mullion {x} {y}", (0.14, 0.05, 0.82), (x, y, 1.38), "trim", material, 0.008))
    add(box("Back service door", (0.70, 0.09, 1.50), (0.70, 1.535, 1.05), "door", material, 0.018))
    add(box("Back window", (0.66, 0.09, 0.82), (-0.70, 1.535, 1.36), "window", material, 0.018))
    add(box("Back service deck", (2.10, 0.42, 0.15), (0, 1.47, 0.20), "deck", material, 0.015))
    add(box("Side school bench", (0.22, 1.50, 0.18), (1.87, 0.58, 0.30), "deck", material, 0.012))
    for y in (-0.02, 1.18):
        add(box(f"Side bench leg {y}", (0.18, 0.14, 0.34), (1.87, y, 0.17), "trim", material, 0.01))

    for y, direction in ((-1.57, -1), (1.57, 1)):
        add(box(f"Step outer {y}", (2.20, 0.22, 0.14), (0, y, 0.07), "deck", material, 0.012))
        add(box(f"Step inner {y}", (1.90, 0.24, 0.14), (0, y - direction * 0.17, 0.19), "deck", material, 0.012))

    add(box("Bell tower base", (1.12, 1.05, 0.60), (0, 0, 3.34), "wall", material, 0.025))
    for x in (-0.48, 0.48):
        for y in (-0.44, 0.44):
            add(box(f"Bell tower post {x} {y}", (0.12, 0.12, 0.94), (x, y, 4.08), "trim", material, 0.015))
    add(box("Bell tower lower beam", (1.20, 1.12, 0.14), (0, 0, 3.62), "trim", material, 0.015))
    add(box("Bell tower upper beam", (1.20, 1.12, 0.14), (0, 0, 4.52), "trim", material, 0.015))
    add(cone("School bell", 0.34, 0.18, 0.46, (0, 0, 4.04), "accent", material))
    add(sphere("Bell clapper", 0.09, (0, 0, 3.84), "accent", material))
    add(pyramid_roof("Bell tower hipped roof", 1.52, 1.46, 4.58, 5.24, "roof", material))
    add(cylinder("Bell tower finial stem", 0.045, 0.20, (0, 0, 5.32), "accent", material, vertices=10))
    add(sphere("Bell tower finial", 0.13, (0, 0, 5.47), "accent", material))

    for x, y in ((-1.78, -1.28), (1.78, -1.28), (-1.78, 1.28), (1.78, 1.28)):
        add(cylinder(f"Painted barrel {x} {y}", 0.20, 0.44, (x, y, 0.22), "deck", material))
    for x, y in ((-1.48, -1.36), (1.48, 1.36)):
        add(box(f"School supply crate {x} {y}", (0.38, 0.34, 0.34), (x, y, 0.30), "wall", material, 0.018))
    for x, y, height in ((-1.58, -1.35, 0.54), (-1.42, -1.31, 0.66), (-1.50, -1.42, 0.76)):
        add(cone(f"Planter shrub {height}", 0.16, 0.04, height, (x, y, 0.50 + height / 2), "stone", material, vertices=8))
    return parts


def apply_and_uv(objects):
    for obj in objects:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        for modifier in list(obj.modifiers):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.025)
        bpy.ops.object.mode_set(mode="OBJECT")
        uv = obj.data.uv_layers.active.data
        coords = np.array([[loop.uv.x, loop.uv.y] for loop in uv])
        minimum, maximum = coords.min(axis=0), coords.max(axis=0)
        span = np.maximum(maximum - minimum, 1e-6)
        u0, v0, u1, v1 = REGIONS[obj["atlas_region"]]
        for loop, coord in zip(uv, coords):
            normalized = (coord - minimum) / span
            loop.uv = (u0 + normalized[0] * (u1 - u0), v0 + normalized[1] * (v1 - v0))
        obj.select_set(False)


def join_schoolhouse(objects):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    schoolhouse = bpy.context.object
    schoolhouse.name = "SchoolhouseFullWrap"
    schoolhouse.data.name = "SchoolhouseFullWrapMesh"
    schoolhouse.data.uv_layers.active.name = "UVMap"
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    return schoolhouse


def export(schoolhouse):
    bpy.ops.object.select_all(action="DESELECT")
    schoolhouse.select_set(True)
    bpy.context.view_layer.objects.active = schoolhouse
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.export_scene.gltf(
        filepath=str(GLB), export_format="GLB", use_selection=True,
        export_apply=True, export_cameras=False, export_lights=False,
        export_animations=False, export_materials="EXPORT",
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    reset_scene()
    atlas = make_atlas()
    material = make_material(atlas)
    parts = build_schoolhouse(material)
    apply_and_uv(parts)
    schoolhouse = join_schoolhouse(parts)
    export(schoolhouse)
    print(json.dumps({
        "blend": str(BLEND), "glb": str(GLB),
        "sha256": hashlib.sha256(GLB.read_bytes()).hexdigest(),
        "vertices": len(schoolhouse.data.vertices), "polygons": len(schoolhouse.data.polygons),
    }, indent=2))


if __name__ == "__main__":
    main()
