from pathlib import Path
import hashlib
import json
import math

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REFERENCE = ROOT / "assets/processed/bld-claim-office.png"
BLEND = OUT / "claim-office.blend"
GLB = OUT / "claim-office.glb"
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
        "wall": (102, 54, 294, 224), "roof": (138, 214, 348, 350),
        "trim": (52, 76, 304, 256), "door": (144, 56, 240, 206),
        "window": (74, 72, 310, 224), "deck": (48, 18, 322, 126),
        "stone": (254, 246, 326, 352), "accent": (106, 146, 294, 286),
    }
    fallback = {
        "wall": np.array((0.67, 0.55, 0.34)), "roof": np.array((0.36, 0.17, 0.07)),
        "trim": np.array((0.25, 0.14, 0.07)), "door": np.array((0.30, 0.17, 0.08)),
        "window": np.array((0.20, 0.25, 0.20)), "deck": np.array((0.42, 0.26, 0.12)),
        "stone": np.array((0.44, 0.37, 0.27)), "accent": np.array((0.32, 0.46, 0.42)),
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
        base = np.clip(base * 1.22, fallback[name] * 0.72, fallback[name] * 1.09)
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
            atlas[y0:y1, x0:x1, :3] = np.array((0.05, 0.10, 0.09))
            atlas[y0 + 5:y1 - 5, x0 + 5:x1 - 5, :3] = np.array((0.24, 0.16, 0.07))
            atlas[(y0 + y1) // 2 - 4:(y0 + y1) // 2 + 4, x0:x1, :3] = dark
            atlas[y0:y1, (x0 + x1) // 2 - 4:(x0 + x1) // 2 + 4, :3] = dark
        elif name == "stone":
            for y in range(y0 + 30, y1, 30):
                atlas[y:y + 3, x0:x1, :3] = dark
            for row, y in enumerate(range(y0, y1, 30)):
                for x in range(x0 + (18 if row % 2 else 0), x1, 38):
                    atlas[y:min(y + 30, y1), x:x + 3, :3] = dark
        elif name == "accent":
            atlas[y0:y1, x0:x1, :3] = np.array((0.11, 0.19, 0.18))
            for y in range(y0 + 24, y1, 48):
                atlas[y:y + 3, x0:x1, :3] = np.array((0.05, 0.11, 0.10))

    image = bpy.data.images.new("ClaimOfficePaintedAtlas", ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(atlas.ravel())
    image.pack()
    return image


def make_material(atlas):
    material = bpy.data.materials.new("ClaimOfficePaintedMaterial")
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


def arched_front(material):
    outline = [
        (-2.02, 2.36), (-2.02, 3.18), (-1.20, 3.18), (-1.08, 3.48),
        (-0.78, 3.74), (-0.40, 3.91), (0.0, 3.97), (0.40, 3.91),
        (0.78, 3.74), (1.08, 3.48), (1.20, 3.18), (2.02, 3.18), (2.02, 2.36),
    ]
    front_y, back_y = -1.205, -1.075
    vertices = [(x, front_y, z) for x, z in outline] + [(x, back_y, z) for x, z in outline]
    count = len(outline)
    faces = [tuple(range(count)), tuple(range(count, count * 2))]
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, count + nxt, count + index))
    return prism("Claim Office arched pediment", vertices, faces, "wall", material, 0.025)


def flag(material):
    front_y, back_y = -0.035, 0.035
    outline = [(0, 4.36), (0, 4.82), (-0.92, 4.67), (-0.72, 4.46)]
    vertices = [(x, front_y, z) for x, z in outline] + [(x, back_y, z) for x, z in outline]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return prism("Claim flag", vertices, faces, "accent", material, 0.01)


def build_office(material):
    parts = []
    add = parts.append
    add(box("Office full wrap", (3.94, 2.36, 2.58), (0, 0.05, 1.29), "wall", material, 0.035))
    add(gable_roof("Shingled full roof", 4.18, 2.86, 2.56, 3.48, "roof", material))
    add(arched_front(material))
    add(box("Lower cornice", (4.18, 0.20, 0.18), (0, -1.24, 2.42), "trim", material, 0.025))
    add(box("Upper cornice", (4.20, 0.18, 0.16), (0, -1.24, 3.16), "trim", material, 0.02))
    add(wedge("Deep porch roof", -2.10, 2.10, -1.52, -1.06, 2.08, 2.38, 0.12, "roof", material))
    add(box("Porch deck", (4.18, 0.72, 0.18), (0, -1.18, 0.24), "deck", material, 0.02))
    add(box("Porch foundation", (4.22, 0.66, 0.18), (0, -1.16, 0.09), "trim", material, 0.02))
    for x in (-1.82, -0.72, 0.72, 1.82):
        add(box(f"Porch post {x}", (0.14, 0.14, 1.62), (x, -1.39, 1.18), "trim", material, 0.018))
        add(box(f"Porch capital {x}", (0.24, 0.22, 0.16), (x, -1.39, 1.98), "accent", material, 0.015))
    add(box("Porch beam", (3.88, 0.14, 0.16), (0, -1.39, 1.98), "trim", material, 0.018))
    add(box("Front door", (0.72, 0.10, 1.58), (0, -1.165, 1.07), "door", material, 0.018))
    for x in (-1.12, 1.12):
        add(box(f"Front window {x}", (0.72, 0.09, 0.92), (x, -1.165, 1.34), "window", material, 0.018))
        add(box(f"Front sill {x}", (0.84, 0.16, 0.10), (x, -1.22, 0.86), "trim", material, 0.012))
    for x in (-1.88, 1.88):
        add(box(f"Facade pier {x}", (0.18, 0.16, 2.58), (x, -1.21, 1.36), "trim", material, 0.018))
    # Authored side and back openings make the shell readable from every quadrant.
    for y in (-0.42, 0.58):
        add(box(f"Right wall window {y}", (0.09, 0.64, 0.76), (1.995, y, 1.35), "window", material, 0.018))
        add(box(f"Left wall window {y}", (0.09, 0.64, 0.76), (-1.995, y, 1.35), "window", material, 0.018))
    add(box("Back service door", (0.70, 0.09, 1.46), (0.65, 1.235, 1.00), "door", material, 0.018))
    add(box("Back ledger window", (0.76, 0.09, 0.72), (-0.72, 1.235, 1.34), "window", material, 0.018))
    add(wedge("Right service canopy", 1.92, 2.12, 0.34, 1.45, 1.56, 1.88, 0.10, "roof", material))
    add(box("Right service platform", (0.34, 1.04, 0.16), (1.98, 0.89, 0.18), "deck", material, 0.015))
    for y, direction in ((-1.49, -1), (1.49, 1)):
        add(box(f"Step outer {y}", (1.18, 0.14, 0.12), (0, y, 0.06), "deck", material, 0.012))
        add(box(f"Step inner {y}", (0.94, 0.14, 0.12), (0, y - direction * 0.12, 0.12), "deck", material, 0.012))
    for x, y, radius, height in ((-1.72, -1.23, 0.23, 0.48), (1.72, 1.16, 0.24, 0.50)):
        add(cylinder(f"Ledger barrel {x} {y}", radius, height, (x, y, height / 2), "deck", material))
    for x, y in ((-1.45, -1.24), (1.48, 1.18)):
        add(box(f"Claim crate {x} {y}", (0.40, 0.34, 0.38), (x, y, 0.31), "wall", material, 0.018))
    add(box("Stone chimney", (0.48, 0.50, 1.42), (1.36, 0.48, 3.40), "stone", material, 0.035))
    add(box("Chimney cap", (0.60, 0.62, 0.16), (1.36, 0.48, 4.12), "stone", material, 0.02))
    add(cylinder("Claim flag pole", 0.055, 1.52, (0, 0, 4.16), "trim", material, vertices=10))
    add(cylinder("Claim flag finial", 0.11, 0.16, (0, 0, 4.94), "accent", material, vertices=10))
    add(flag(material))
    add(cylinder("Teal porch lantern", 0.10, 0.28, (-1.72, -1.43, 1.55), "accent", material, vertices=10))
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


def join_office(objects):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    office = bpy.context.object
    office.name = "ClaimOfficeFullWrap"
    office.data.name = "ClaimOfficeFullWrapMesh"
    office.data.uv_layers.active.name = "UVMap"
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    return office


def export(office):
    bpy.ops.object.select_all(action="DESELECT")
    office.select_set(True)
    bpy.context.view_layer.objects.active = office
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
    parts = build_office(material)
    apply_and_uv(parts)
    office = join_office(parts)
    export(office)
    print(json.dumps({
        "blend": str(BLEND), "glb": str(GLB),
        "sha256": hashlib.sha256(GLB.read_bytes()).hexdigest(),
        "vertices": len(office.data.vertices), "polygons": len(office.data.polygons),
    }, indent=2))


if __name__ == "__main__":
    main()
