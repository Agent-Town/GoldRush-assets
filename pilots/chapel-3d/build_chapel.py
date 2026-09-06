from pathlib import Path
import hashlib
import json
import math

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REFERENCE = ROOT / "assets/processed/bld-chapel.png"
BLEND = OUT / "chapel.blend"
GLB = OUT / "chapel.glb"
ATLAS_SIZE = 1024

REGIONS = {
    "wall": (0.02, 0.02, 0.48, 0.48),
    "roof": (0.52, 0.52, 0.98, 0.98),
    "trim": (0.02, 0.52, 0.23, 0.73),
    "door": (0.52, 0.02, 0.73, 0.48),
    "window": (0.77, 0.02, 0.98, 0.48),
    "deck": (0.27, 0.52, 0.48, 0.73),
    "accent": (0.27, 0.77, 0.48, 0.98),
    "foliage": (0.02, 0.77, 0.23, 0.98),
}


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
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
        "wall": (84, 82, 280, 300), "roof": (106, 16, 350, 232),
        "trim": (38, 75, 312, 308), "door": (70, 58, 220, 250),
        "window": (132, 72, 342, 286), "deck": (28, 30, 254, 164),
        "accent": (104, 18, 258, 178),
        "foliage": (248, 198, 372, 354),
    }
    fallback = {
        "wall": np.array((0.72, 0.59, 0.39)), "roof": np.array((0.42, 0.20, 0.08)),
        "trim": np.array((0.31, 0.19, 0.09)), "door": np.array((0.32, 0.18, 0.08)),
        "window": np.array((0.55, 0.35, 0.10)), "deck": np.array((0.45, 0.28, 0.12)),
        "accent": np.array((0.55, 0.35, 0.10)),
        "foliage": np.array((0.26, 0.30, 0.12)),
    }
    rng = np.random.default_rng(712)
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
            base = np.maximum(base, np.array((0.62, 0.49, 0.31)))
        height, width = y1 - y0, x1 - x0
        noise = rng.normal(0, 0.025, (height, width, 1)).astype(np.float32)
        block = np.ones((height, width, 4), dtype=np.float32)
        block[:, :, :3] = np.clip(base + noise, 0.025, 0.92)
        atlas[y0:y1, x0:x1] = block

        dark = np.clip(base * (0.56 if name == "wall" else 0.36), 0.018, 0.42)
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
            atlas[y0:y1, x0:x1, :3] = np.array((0.22, 0.12, 0.05))
            atlas[y0 + 5:y1 - 5, x0 + 5:x1 - 5, :3] = np.array((0.68, 0.43, 0.12))
            atlas[(y0 + y1) // 2 - 4:(y0 + y1) // 2 + 4, x0:x1, :3] = dark
            atlas[y0:y1, (x0 + x1) // 2 - 4:(x0 + x1) // 2 + 4, :3] = dark
        elif name == "accent":
            atlas[y0:y1, x0:x1, :3] = np.array((0.52, 0.34, 0.11))
            for y in range(y0 + 24, y1, 48):
                atlas[y:y + 3, x0:x1, :3] = np.array((0.27, 0.16, 0.06))
        elif name == "foliage":
            atlas[y0:y1, x0:x1, :3] = np.array((0.25, 0.29, 0.12))
            for y in range(y0 + 18, y1, 38):
                atlas[y:y + 2, x0:x1, :3] = np.array((0.14, 0.18, 0.07))

    image = bpy.data.images.new("ChapelPaintedAtlas", ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(atlas.ravel())
    image.pack()
    return image


def make_material(atlas):
    material = bpy.data.materials.new("ChapelPaintedMaterial")
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


def cone(name, radius1, radius2, depth, location, category, material, vertices=16):
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=location,
    )
    obj = bpy.context.object
    obj.name = name
    return tag(obj, category, material, 0.018)


def prism(name, vertices, faces, category, material, bevel=0.02):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return tag(obj, category, material, bevel)


def lancet(name, width, height, depth, location, category, material, side=False):
    x, y = width / 2, depth / 2
    shoulder = height * 0.22
    outline = [(-x, -height / 2), (x, -height / 2), (x, shoulder), (0, height / 2), (-x, shoulder)]
    vertices = [(px, -y, pz) for px, pz in outline] + [(px, y, pz) for px, pz in outline]
    count = len(outline)
    faces = [tuple(range(count)), tuple(range(count, count * 2))]
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, count + nxt, count + index))
    obj = prism(name, vertices, faces, category, material, 0.016)
    obj.location = location
    if side:
        obj.rotation_euler.z = math.pi / 2
    return obj


def front_gable_roof(name, width, depth, eave_z, ridge_z, category, material):
    x, y = width / 2, depth / 2
    vertices = [
        (-x, -y, eave_z), (x, -y, eave_z), (x, y, eave_z), (-x, y, eave_z),
        (0, -y, ridge_z), (0, y, ridge_z),
    ]
    faces = [(0, 4, 5, 3), (1, 2, 5, 4), (0, 3, 2, 1)]
    return prism(name, vertices, faces, category, material, 0.035)


def gable_panel(name, width, depth, eave_z, ridge_z, y, category, material):
    x, d = width / 2, depth / 2
    vertices = [
        (-x, -d, eave_z), (x, -d, eave_z), (0, -d, ridge_z),
        (-x, d, eave_z), (x, d, eave_z), (0, d, ridge_z),
    ]
    faces = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    panel = prism(name, vertices, faces, category, material, 0.018)
    panel.location.y = y
    return panel


def hip_roof(name, width, depth, eave_z, ridge_z, category, material):
    x, y = width / 2, depth / 2
    vertices = [
        (-x, -y, eave_z), (x, -y, eave_z), (x, y, eave_z), (-x, y, eave_z),
        (0, 0, ridge_z),
    ]
    faces = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (0, 3, 2, 1)]
    return prism(name, vertices, faces, category, material, 0.028)


def build_chapel(material):
    parts = []
    add = parts.append
    add(box("Nave full wrap", (3.00, 2.72, 2.62), (0, 0, 1.31), "wall", material, 0.035))
    add(front_gable_roof("Main shingled gable", 3.52, 3.12, 2.48, 3.80, "roof", material))
    add(gable_panel("Front cream gable", 2.98, 0.06, 2.47, 3.74, -1.36, "wall", material))
    add(gable_panel("Rear cream gable", 2.98, 0.06, 2.47, 3.74, 1.36, "wall", material))
    add(box("Front sill beam", (3.10, 0.16, 0.16), (0, -1.40, 0.38), "trim", material, 0.018))
    for x in (-1.47, 1.47):
        for y in (-1.32, 1.32):
            add(box(f"Corner timber {x} {y}", (0.13, 0.13, 2.36), (x, y, 1.20), "trim", material, 0.014))
    porch_roof = front_gable_roof("Entry porch gable", 2.48, 0.72, 1.88, 2.44, "roof", material)
    porch_roof.location.y = -1.22
    add(porch_roof)
    add(gable_panel("Porch timber gable", 2.18, 0.06, 1.88, 2.38, -1.53, "trim", material))
    add(box("Entry porch deck", (2.28, 0.60, 0.18), (0, -1.28, 0.19), "deck", material, 0.02))
    for x in (-1.03, 1.03):
        add(box(f"Porch post {x}", (0.16, 0.16, 1.48), (x, -1.49, 0.94), "trim", material, 0.018))
        add(box(f"Porch capital {x}", (0.25, 0.23, 0.14), (x, -1.49, 1.68), "trim", material, 0.014))
    add(box("Porch lintel", (2.24, 0.16, 0.18), (0, -1.49, 1.65), "trim", material, 0.018))
    add(lancet("Pointed front door", 0.90, 1.62, 0.10, (0, -1.41, 1.02), "door", material))
    add(lancet("Front gable lancet", 0.52, 0.80, 0.09, (0, -1.41, 2.66), "window", material))
    add(box("Front gable window sill", (0.68, 0.17, 0.10), (0, -1.46, 2.27), "trim", material, 0.012))

    # Three windows on each long wall plus a rear service opening prove the complete wrap.
    for y in (-0.72, 0.05, 0.82):
        for x in (-1.54, 1.54):
            add(lancet(f"Side lancet {x} {y}", 0.42, 0.94, 0.09, (x, y, 1.50), "window", material, side=True))
            add(box(f"Side sill {x} {y}", (0.14, 0.56, 0.09), (x, y, 1.02), "trim", material, 0.012))
    add(lancet("Rear vestry door", 0.72, 1.48, 0.10, (0.66, 1.41, 1.04), "door", material))
    add(lancet("Rear lancet", 0.52, 0.86, 0.09, (-0.60, 1.41, 1.48), "window", material))

    # Bell tower: enclosed base, open belfry, pyramidal roof, bell, and the painted cross.
    add(box("Bell tower base", (1.22, 1.06, 0.72), (0, -0.42, 3.77), "wall", material, 0.025))
    for x in (-0.52, 0.52):
        for y in (-0.82, -0.02):
            add(box(f"Belfry post {x} {y}", (0.15, 0.15, 0.94), (x, y, 4.45), "trim", material, 0.016))
    add(box("Belfry lower beam", (1.30, 1.06, 0.14), (0, -0.42, 4.02), "trim", material, 0.016))
    add(box("Belfry upper beam", (1.30, 1.06, 0.14), (0, -0.42, 4.88), "trim", material, 0.016))
    add(cylinder("Bell yoke", 0.07, 0.78, (0, -0.42, 4.59), "trim", material, vertices=10))
    add(cone("Brass bell", 0.30, 0.18, 0.48, (0, -0.42, 4.40), "accent", material))
    add(cylinder("Bell clapper", 0.07, 0.28, (0, -0.42, 4.12), "accent", material, vertices=10))
    belfry_cap = hip_roof("Belfry shingled cap", 1.48, 1.30, 4.90, 5.57, "roof", material)
    belfry_cap.location.y = -0.42
    add(belfry_cap)
    add(box("Cross upright", (0.12, 0.12, 0.84), (0, -0.42, 5.83), "trim", material, 0.012))
    add(box("Cross beam", (0.48, 0.12, 0.12), (0, -0.42, 5.95), "trim", material, 0.012))

    # Symmetric front/back steps keep the exported base centered without moving the Town slot.
    for y, direction in ((-1.53, -1), (1.53, 1)):
        add(box(f"Outer step {y}", (1.30, 0.12, 0.12), (0, y, 0.06), "deck", material, 0.010))
        add(box(f"Inner step {y}", (1.06, 0.12, 0.12), (0, y - direction * 0.12, 0.12), "deck", material, 0.010))
    for x, y in ((-1.36, -1.30), (1.36, -1.28), (-1.36, 1.30), (1.36, 1.30)):
        add(box(f"Planter {x} {y}", (0.36, 0.34, 0.30), (x, y, 0.25), "wall", material, 0.016))
        add(cone(f"Dusty shrub {x} {y}", 0.28, 0.04, 0.64, (x, y, 0.67), "foliage", material, vertices=8))
    for x in (-1.10, 1.10):
        add(box(f"Porch side rail {x}", (0.11, 0.52, 0.13), (x, -1.27, 0.72), "trim", material, 0.012))
        add(box(f"Porch rail post {x}", (0.13, 0.13, 0.72), (x, -1.48, 0.58), "trim", material, 0.012))
    add(cylinder("Porch lantern left", 0.09, 0.26, (-1.16, -1.51, 1.20), "accent", material, vertices=10))
    add(cylinder("Porch lantern right", 0.09, 0.26, (1.16, -1.51, 1.20), "accent", material, vertices=10))
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


def join_chapel(objects):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    chapel = bpy.context.object
    chapel.name = "ChapelFullWrap"
    chapel.data.name = "ChapelFullWrapMesh"
    chapel.data.uv_layers.active.name = "UVMap"
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    return chapel


def export(chapel):
    bpy.ops.object.select_all(action="DESELECT")
    chapel.select_set(True)
    bpy.context.view_layer.objects.active = chapel
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
    parts = build_chapel(material)
    apply_and_uv(parts)
    chapel = join_chapel(parts)
    export(chapel)
    print(json.dumps({
        "blend": str(BLEND), "glb": str(GLB),
        "sha256": hashlib.sha256(GLB.read_bytes()).hexdigest(),
        "vertices": len(chapel.data.vertices), "polygons": len(chapel.data.polygons),
    }, indent=2))


if __name__ == "__main__":
    main()
