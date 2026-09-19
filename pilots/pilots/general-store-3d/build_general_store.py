from pathlib import Path
import hashlib
import json
import math

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REFERENCE = ROOT / "assets/processed/bld-general-store.png"
BLEND = OUT / "general-store.blend"
GLB = OUT / "general-store.glb"
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
        "wall": (208, 92, 350, 282), "roof": (145, 226, 333, 360),
        "trim": (52, 106, 302, 246), "door": (116, 62, 260, 228),
        "window": (105, 102, 250, 245), "deck": (43, 18, 292, 151),
        "stone": (248, 267, 314, 360), "accent": (207, 78, 350, 248),
    }
    fallback = {
        "wall": np.array((0.68, 0.43, 0.19)), "roof": np.array((0.38, 0.18, 0.08)),
        "trim": np.array((0.29, 0.18, 0.09)), "door": np.array((0.34, 0.20, 0.09)),
        "window": np.array((0.19, 0.27, 0.25)), "deck": np.array((0.46, 0.29, 0.13)),
        "stone": np.array((0.46, 0.38, 0.26)), "accent": np.array((0.30, 0.48, 0.44)),
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
            atlas[y0:y1, x0:x1, :3] = np.array((0.10, 0.20, 0.19))
            atlas[y0 + 5:y1 - 5, x0 + 5:x1 - 5, :3] = np.array((0.53, 0.35, 0.14))
            atlas[(y0 + y1) // 2 - 4:(y0 + y1) // 2 + 4, x0:x1, :3] = dark
            atlas[y0:y1, (x0 + x1) // 2 - 4:(x0 + x1) // 2 + 4, :3] = dark
        elif name == "stone":
            for y in range(y0 + 30, y1, 30):
                atlas[y:y + 3, x0:x1, :3] = dark
            for row, y in enumerate(range(y0, y1, 30)):
                for x in range(x0 + (18 if row % 2 else 0), x1, 38):
                    atlas[y:min(y + 30, y1), x:x + 3, :3] = dark
        elif name == "accent":
            atlas[y0:y1, x0:x1, :3] = np.array((0.24, 0.43, 0.40))
            for y in range(y0 + 24, y1, 48):
                atlas[y:y + 3, x0:x1, :3] = np.array((0.12, 0.25, 0.24))

    image = bpy.data.images.new("GeneralStorePaintedAtlas", ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(atlas.ravel())
    image.pack()
    return image


def make_material(atlas):
    material = bpy.data.materials.new("GeneralStorePaintedMaterial")
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


def false_front(material):
    outline = [
        (-2.06, 2.52), (-2.06, 3.48), (-1.52, 3.48), (-1.28, 3.76),
        (-0.78, 3.94), (0.0, 4.01), (0.78, 3.94), (1.28, 3.76),
        (1.52, 3.48), (2.06, 3.48), (2.06, 2.52),
    ]
    front_y, back_y = -1.385, -1.255
    vertices = [(x, front_y, z) for x, z in outline] + [(x, back_y, z) for x, z in outline]
    count = len(outline)
    faces = [tuple(range(count)), tuple(range(count, count * 2))]
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, count + nxt, count + index))
    return prism("Store false-front pediment", vertices, faces, "wall", material, 0.025)


def build_store(material):
    parts = []
    add = parts.append
    add(box("Ground floor full wrap", (4.10, 2.72, 2.34), (0, 0.10, 1.17), "wall", material, 0.035))
    add(box("Upper floor full wrap", (3.88, 2.46, 1.02), (0, 0.02, 2.77), "wall", material, 0.03))
    add(gable_roof("Main gabled roof", 4.44, 2.98, 3.20, 4.13, "roof", material))
    add(false_front(material))
    add(box("Front cornice", (4.30, 0.22, 0.18), (0, -1.47, 2.55), "trim", material, 0.025))
    add(box("Upper cornice", (4.32, 0.20, 0.17), (0, -1.47, 3.42), "trim", material, 0.025))
    add(wedge("Deep porch roof", -2.30, 2.30, -1.63, -1.13, 2.05, 2.40, 0.12, "roof", material))
    add(box("Porch deck", (4.58, 0.78, 0.16), (0, -1.23, 0.24), "deck", material, 0.02))
    add(box("Porch foundation", (4.68, 0.70, 0.22), (0, -1.22, 0.11), "trim", material, 0.02))
    for x in (-2.08, -0.72, 0.72, 2.08):
        add(box(f"Porch post {x}", (0.13, 0.13, 1.72), (x, -1.48, 1.22), "trim", material, 0.018))
        add(box(f"Porch capital {x}", (0.22, 0.20, 0.14), (x, -1.48, 2.08), "trim", material, 0.015))
    add(box("Porch beam", (4.40, 0.14, 0.16), (0, -1.48, 2.02), "trim", material, 0.018))
    add(box("Front door", (0.72, 0.10, 1.54), (0, -1.315, 1.08), "door", material, 0.018))
    for x in (-1.22, 1.22):
        add(box(f"Front lower window {x}", (0.72, 0.09, 0.86), (x, -1.315, 1.35), "window", material, 0.018))
        add(box(f"Front upper window {x}", (0.62, 0.08, 0.64), (x, -1.315, 2.91), "window", material, 0.018))
        add(box(f"Front window sill {x}", (0.84, 0.15, 0.10), (x, -1.37, 0.89), "trim", material, 0.012))
    # Side and back openings prove the wrap from every camera quadrant.
    for y in (-0.45, 0.72):
        add(box(f"Right wall window {y}", (0.09, 0.68, 0.78), (2.075, y, 1.34), "window", material, 0.018))
        add(box(f"Left wall window {y}", (0.09, 0.68, 0.78), (-2.075, y, 1.34), "window", material, 0.018))
    add(box("Back service door", (0.72, 0.09, 1.46), (0.72, 1.465, 1.02), "door", material, 0.018))
    add(box("Back window", (0.78, 0.09, 0.72), (-0.78, 1.465, 1.36), "window", material, 0.018))
    add(wedge("Right service awning", 2.05, 2.36, 0.26, 1.52, 1.45, 1.82, 0.10, "roof", material))
    add(box("Right service platform", (0.42, 1.18, 0.16), (2.15, 0.88, 0.20), "deck", material, 0.015))
    # Centered front/back steps preserve a base-center bounding box without layout drift.
    for y, direction in ((-1.55, -1), (1.55, 1)):
        add(box(f"Step outer {y}", (1.18, 0.16, 0.12), (0, y, 0.06), "deck", material, 0.012))
        add(box(f"Step inner {y}", (0.94, 0.16, 0.12), (0, y - direction * 0.13, 0.12), "deck", material, 0.012))
    for x, y, radius, height in ((-1.72, -1.38, 0.25, 0.52), (1.73, -1.36, 0.22, 0.46), (1.92, 1.13, 0.26, 0.56), (-1.76, 1.18, 0.22, 0.48)):
        add(cylinder(f"Painted barrel {x} {y}", radius, height, (x, y, height / 2), "deck", material))
    for x, y in ((-1.52, -1.34), (1.48, -1.38), (1.72, 1.28), (-1.55, 1.30)):
        add(box(f"Service crate {x} {y}", (0.40, 0.34, 0.38), (x, y, 0.35), "wall", material, 0.018))
    add(box("Stone chimney", (0.46, 0.48, 1.44), (1.43, 0.62, 3.63), "stone", material, 0.035))
    add(box("Chimney cap", (0.58, 0.60, 0.16), (1.43, 0.62, 4.36), "stone", material, 0.02))
    add(cylinder("Teal porch lantern", 0.10, 0.28, (-1.86, -1.51, 1.57), "accent", material, vertices=10))
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


def join_store(objects):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    store = bpy.context.object
    store.name = "GeneralStoreFullWrap"
    store.data.name = "GeneralStoreFullWrapMesh"
    store.data.uv_layers.active.name = "UVMap"
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    return store


def export(store):
    bpy.ops.object.select_all(action="DESELECT")
    store.select_set(True)
    bpy.context.view_layer.objects.active = store
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
    parts = build_store(material)
    apply_and_uv(parts)
    store = join_store(parts)
    export(store)
    print(json.dumps({
        "blend": str(BLEND), "glb": str(GLB),
        "sha256": hashlib.sha256(GLB.read_bytes()).hexdigest(),
        "vertices": len(store.data.vertices), "polygons": len(store.data.polygons),
    }, indent=2))


if __name__ == "__main__":
    main()
