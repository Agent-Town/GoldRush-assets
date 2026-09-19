from pathlib import Path
import hashlib
import json
import math

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parent
ATLAS = ROOT / "era-props-e2-atlas.png"
SIZE = 1024
COLUMNS = 4
PALETTE = (
    (0.08, 0.055, 0.035), (0.18, 0.10, 0.045), (0.34, 0.19, 0.075), (0.55, 0.34, 0.12),
    (0.11, 0.12, 0.105), (0.23, 0.23, 0.18), (0.46, 0.29, 0.10), (0.65, 0.43, 0.16),
    (0.055, 0.19, 0.19), (0.08, 0.35, 0.34), (0.24, 0.43, 0.40), (0.55, 0.56, 0.43),
    (0.045, 0.04, 0.035), (0.16, 0.13, 0.09), (0.47, 0.38, 0.25), (0.72, 0.60, 0.38),
)
BASE_HASHES = {
    "covered_wagon": {
        "blend": "8255fe293eeb3eec83a07b5fb1f7147ffcacc5f05199855d31a8f03f25dd9820",
        "glb": "1d095b29836a96c8a85b0f5741ff60235546dc44c58f23e405f9260875215422",
    },
    "water_trough": {
        "blend": "52714b0c41f381c19cbe2305a13bbf3dbc11a4d50471d3fe992d617e01776fa7",
        "glb": "dfc4a1218f0cc522cf281b1984d8380e62b781618c1bf122df40fd9179d9b7f3",
    },
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.preferences.filepaths.save_version = 0


def write_shared_atlas():
    reset()
    pixels = np.ones((SIZE, SIZE, 4), dtype=np.float32)
    cell = SIZE // COLUMNS
    rng = np.random.default_rng(714)
    for index, color in enumerate(PALETTE):
        column, row = index % COLUMNS, index // COLUMNS
        x0, y0 = column * cell, row * cell
        block = np.array(color, dtype=np.float32) + rng.normal(0, 0.010, (cell, cell, 1))
        pixels[y0:y0 + cell, x0:x0 + cell, :3] = np.clip(block, 0.015, 0.90)
        for x in range(x0 + 24, x0 + cell, 41):
            pixels[y0:y0 + cell, x:x + 2, :3] *= 0.72
        for y in range(y0 + 31, y0 + cell, 67):
            pixels[y:y + 2, x0:x0 + cell, :3] *= 0.80
    image = bpy.data.images.new("E2EraPropsSharedAtlas", SIZE, SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(pixels.ravel())
    image.filepath_raw = str(ATLAS)
    image.file_format = "PNG"
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.image_settings.color_mode = "RGBA"
    image.save()


def material_from_atlas():
    image = bpy.data.images.load(str(ATLAS), check_existing=False)
    image.colorspace_settings.name = "sRGB"
    # Keep the authored master; tiny props embed the factory 512px tier.
    image.scale(512, 512)
    image.pack()
    material = bpy.data.materials.new("E2EraPropsSharedMaterial")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
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


def tag(obj, material, palette_index, bevel=0.008):
    obj.data.materials.append(material)
    obj["palette_index"] = palette_index
    if bevel:
        modifier = obj.modifiers.new("Painted edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        modifier.limit_method = "ANGLE"
    return obj


def box(name, size, location, material, palette_index, bevel=0.008, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = tuple(value / 2 for value in size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return tag(obj, material, palette_index, bevel)


def cylinder(name, radius, depth, location, material, palette_index, vertices=12, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    return tag(obj, material, palette_index, 0.006)


def torus(name, major_radius, minor_radius, location, material, palette_index, rotation=(0, 0, 0), segments=(12, 4)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius, minor_radius=minor_radius,
        major_segments=segments[0], minor_segments=segments[1], location=location, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    return tag(obj, material, palette_index, 0)


def coal_lump(name, location, scale, material):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return tag(obj, material, 12, 0)


def apply_palette_uv(parts, shared):
    for obj in parts:
        if obj.get("preserve_uv"):
            continue
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        for modifier in list(obj.modifiers):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        uv_layer = obj.data.uv_layers.get("UVMap") or obj.data.uv_layers.new(name="UVMap")
        if shared:
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
            bpy.ops.object.mode_set(mode="OBJECT")
            uv_layer = obj.data.uv_layers.active
            coords = np.array([[loop.uv.x, loop.uv.y] for loop in uv_layer.data])
            minimum, maximum = coords.min(axis=0), coords.max(axis=0)
            span = np.maximum(maximum - minimum, 1e-6)
            index = int(obj["palette_index"])
            column, row = index % COLUMNS, index // COLUMNS
            margin = 0.025
            for loop, coord in zip(uv_layer.data, coords):
                normalized = (coord - minimum) / span
                loop.uv = ((column + margin + normalized[0] * (1 - margin * 2)) / COLUMNS,
                           (row + margin + normalized[1] * (1 - margin * 2)) / COLUMNS)
        else:
            index = int(obj["palette_index"])
            column, row = index % COLUMNS, index // COLUMNS
            uv = ((column + 0.5) / COLUMNS, (row + 0.5) / COLUMNS)
            for loop in uv_layer.data:
                loop.uv = uv
        obj.select_set(False)


def add_anchors(locations, parent):
    anchors = []
    for index, location in enumerate(locations, 1):
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=location)
        anchor = bpy.context.object
        anchor.name = f"steam_anchor_{index}"
        anchor.empty_display_size = 0.08
        anchor.parent = parent
        anchors.append(anchor)
    return anchors


def finish(name, parts, material, anchors=(), shared=True, triangle_limit=1000, expected_dimensions=None):
    apply_palette_uv(parts, shared)
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
    if expected_dimensions:
        assert all(abs(model.dimensions[index] - expected_dimensions[index]) < 0.0001 for index in range(3)), (
            name, expected_dimensions, tuple(model.dimensions),
        )
    steam_anchors = add_anchors(anchors, model)
    triangles = sum(len(polygon.vertices) - 2 for polygon in model.data.polygons)
    assert triangles <= triangle_limit, (name, triangles, triangle_limit)
    stem = {
        "CoveredWagonE2": "covered_wagon.e2", "WaterTroughE2": "water_trough.e2",
        "CoalBinE2": "coal-bin.e2", "PipeRunE2": "pipe-run.e2", "GaugePostE2": "gauge-post.e2",
        "IronLampPostE2": "iron-lamp-post.e2", "PressureManifoldE2": "pressure-manifold.e2",
    }[name]
    blend, glb = ROOT / f"{stem}.blend", ROOT / f"{stem}.glb"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.object.select_all(action="DESELECT")
    model.select_set(True)
    for anchor in steam_anchors:
        anchor.select_set(True)
    bpy.context.view_layer.objects.active = model
    bpy.ops.export_scene.gltf(
        filepath=str(glb), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT",
    )
    return {"id": stem, "triangles": triangles, "sha256": sha256(glb),
            "anchors": [anchor.name for anchor in steam_anchors], "dimensions": list(model.dimensions)}


def variant_material(name):
    blend, glb = ROOT / f"{name}.blend", ROOT / f"{name}.glb"
    assert sha256(blend) == BASE_HASHES[name]["blend"]
    assert sha256(glb) == BASE_HASHES[name]["glb"]
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    model = bpy.data.objects[name]
    model["preserve_uv"] = True
    return model, model.data.materials[0], tuple(model.dimensions)


def build_wagon():
    model, material, dimensions = variant_material("covered_wagon")
    parts = [model]
    for x in (-0.32, 0.32):
        for y in (-0.455, 0.455):
            parts.append(box(f"Wagon iron strap {x} {y}", (0.065, 0.035, 0.43), (x, y, 0.78), material, 9, 0.005))
    parts.extend((
        cylinder("Wagon pony tank", 0.11, 0.62, (0.58, 0.34, 0.78), material, 9, 10),
        cylinder("Wagon tank brass band", 0.13, 0.08, (0.58, 0.34, 0.68), material, 4, 10),
        cylinder("Wagon tank teal band", 0.13, 0.08, (0.58, 0.34, 0.92), material, 3, 10),
        cylinder("Wagon short vent", 0.055, 0.36, (0.58, 0.34, 1.20), material, 9, 10),
        cylinder("Wagon vent cap", 0.085, 0.08, (0.58, 0.34, 1.36), material, 4, 10),
        cylinder("Wagon brass feed", 0.045, 0.48, (0.34, 0.34, 1.02), material, 4, 8,
                 rotation=(0, math.pi / 2, 0)),
    ))
    return finish("CoveredWagonE2", parts, material, anchors=[(0.58, 0.34, 1.42)], shared=False,
                  triangle_limit=1800, expected_dimensions=dimensions)


def build_trough():
    model, material, dimensions = variant_material("water_trough")
    parts = [model,
        cylinder("Trough pipe riser", 0.045, 0.42, (0.66, 0.27, 0.42), material, 4, 8),
        cylinder("Trough feed pipe", 0.045, 0.68, (0.32, 0.27, 0.57), material, 4, 8,
                 rotation=(0, math.pi / 2, 0)),
        torus("Trough feed valve", 0.10, 0.025, (0.56, 0.33, 0.48), material, 3,
              rotation=(math.pi / 2, 0, 0)),
    ]
    return finish("WaterTroughE2", parts, material, shared=False, triangle_limit=1200,
                  expected_dimensions=dimensions)


def build_coal_bin():
    reset(); material = material_from_atlas()
    parts = [
        box("Coal bin floor", (1.12, 0.72, 0.10), (0, 0, 0.05), material, 1),
        box("Coal bin back", (1.12, 0.10, 0.62), (0, 0.31, 0.36), material, 2),
        box("Coal bin side left", (0.10, 0.62, 0.62), (-0.51, 0, 0.36), material, 2),
        box("Coal bin side right", (0.10, 0.62, 0.62), (0.51, 0, 0.36), material, 2),
        box("Coal bin front lip", (1.12, 0.10, 0.30), (0, -0.31, 0.20), material, 1),
    ]
    for index, (x, y, z, scale) in enumerate((
        (-0.34, -0.08, 0.24, (0.18, 0.14, 0.13)), (0.0, -0.10, 0.25, (0.20, 0.15, 0.14)),
        (0.34, -0.05, 0.23, (0.17, 0.13, 0.12)), (-0.22, 0.12, 0.35, (0.19, 0.14, 0.14)),
        (0.18, 0.13, 0.36, (0.20, 0.15, 0.15)), (0.0, 0.02, 0.46, (0.18, 0.14, 0.13)),
    )):
        parts.append(coal_lump(f"Coal lump {index}", (x, y, z), scale, material))
    return finish("CoalBinE2", parts, material)


def build_pipe_run():
    reset(); material = material_from_atlas()
    parts = [
        box("Pipe foot left", (0.32, 0.36, 0.12), (-0.82, 0, 0.06), material, 13),
        box("Pipe foot right", (0.32, 0.36, 0.12), (0.82, 0, 0.06), material, 13),
        cylinder("Ring-road pipe", 0.105, 1.92, (0, 0, 0.46), material, 4, 12,
                 rotation=(0, math.pi / 2, 0)),
    ]
    for x in (-0.86, 0.86):
        parts.extend((
            cylinder(f"Pipe riser {x}", 0.105, 0.72, (x, 0, 0.64), material, 4, 12),
            cylinder(f"Pipe flange low {x}", 0.15, 0.09, (x, 0, 0.24), material, 6, 12),
            cylinder(f"Pipe flange high {x}", 0.15, 0.09, (x, 0, 0.96), material, 9, 12),
        ))
    return finish("PipeRunE2", parts, material, anchors=[(0.86, 0, 1.03)])


def build_gauge_post():
    reset(); material = material_from_atlas()
    parts = [
        cylinder("Gauge post footing", 0.28, 0.16, (0, 0, 0.08), material, 13, 12),
        cylinder("Gauge post", 0.08, 1.42, (0, 0, 0.79), material, 4, 10),
        torus("Gauge post rim", 0.29, 0.055, (0, -0.03, 1.47), material, 7,
              rotation=(math.pi / 2, 0, 0), segments=(16, 5)),
        cylinder("Gauge post face", 0.23, 0.08, (0, -0.04, 1.47), material, 15, 16,
                 rotation=(math.pi / 2, 0, 0)),
        box("Gauge post needle", (0.035, 0.025, 0.18), (0.04, -0.10, 1.51), material, 9, 0.003,
            rotation=(0, 0.48, 0)),
        cylinder("Gauge post side pipe", 0.045, 0.48, (0.23, 0, 0.52), material, 6, 8),
    ]
    return finish("GaugePostE2", parts, material)


def build_iron_lamp():
    reset(); material = material_from_atlas()
    parts = [
        cylinder("Iron lamp footing", 0.27, 0.16, (0, 0, 0.08), material, 13, 12),
        cylinder("Iron lamp post", 0.075, 2.08, (0, 0, 1.08), material, 4, 10),
        box("Iron lamp crossbar", (1.05, 0.09, 0.09), (0, 0, 1.94), material, 6),
    ]
    for x in (-0.42, 0.42):
        parts.extend((
            box(f"Lamp bracket {x}", (0.07, 0.07, 0.30), (x, 0, 1.78), material, 4),
            box(f"Lamp glass {x}", (0.24, 0.20, 0.34), (x, 0, 1.59), material, 9),
            cylinder(f"Lamp cap {x}", 0.17, 0.10, (x, 0, 1.80), material, 6, 8),
            cylinder(f"Lamp base {x}", 0.14, 0.09, (x, 0, 1.39), material, 4, 8),
        ))
    return finish("IronLampPostE2", parts, material)


def build_manifold():
    reset(); material = material_from_atlas()
    parts = [
        box("Manifold foot left", (0.28, 0.42, 0.12), (-0.62, 0, 0.06), material, 13),
        box("Manifold foot right", (0.28, 0.42, 0.12), (0.62, 0, 0.06), material, 13),
        cylinder("Pressure manifold header", 0.13, 1.52, (0, 0, 0.52), material, 4, 12,
                 rotation=(0, math.pi / 2, 0)),
    ]
    for index, x in enumerate((-0.48, 0, 0.48)):
        parts.extend((
            cylinder(f"Manifold valve riser {index}", 0.055, 0.50, (x, 0, 0.78), material, 6, 8),
            torus(f"Manifold valve wheel {index}", 0.15, 0.035, (x, -0.04, 0.91), material,
                  9 if index == 1 else 7, rotation=(math.pi / 2, 0, 0)),
        ))
    parts.extend((
        cylinder("Manifold relief vent", 0.07, 0.62, (0, 0, 1.12), material, 4, 10),
        cylinder("Manifold relief cap", 0.12, 0.10, (0, 0, 1.43), material, 9, 10),
    ))
    return finish("PressureManifoldE2", parts, material, anchors=[(0, 0, 1.50)])


def main():
    write_shared_atlas()
    results = [build_wagon(), build_trough(), build_coal_bin(), build_pipe_run(), build_gauge_post(),
               build_iron_lamp(), build_manifold()]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
