import argparse
import bpy
import math
from mathutils import Matrix, Vector
from pathlib import Path
import sys

ROOT = Path(__file__).parent
PAN_PALETTE_SIZE = 256
PAN_PALETTE_COLUMNS = 4
PAN_PALETTE = (
    (0.18, 0.075, 0.025),  # dark timber
    (0.43, 0.24, 0.11),
    (0.34, 0.19, 0.09),
    (0.11, 0.30, 0.29),    # restrained teal
    (0.62, 0.36, 0.08),    # frontier brass
    (0.86, 0.61, 0.17),    # gold
    (0.31, 0.22, 0.14),    # stone shadow
    (0.55, 0.43, 0.29),    # warm stone
    (0.72, 0.61, 0.43),
    (0.10, 0.075, 0.055),
    (0.48, 0.17, 0.07),
    (0.22, 0.34, 0.16),
    (0.70, 0.48, 0.22),
    (0.37, 0.12, 0.055),
    (0.74, 0.70, 0.58),    # bright nugget
    (0.055, 0.12, 0.12),
)


def cube(name, location, scale, mat, bevel=.035):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new('Painted edge', 'BEVEL')
        mod.width = bevel
        mod.segments = 1
    obj.data.materials.append(mat)
    return obj


def cylinder(name, location, radius, depth, mat, vertices=12, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.context.scene.unit_settings.system = "METRIC"


def wagon():
    reset()
    mat = pan_material("Covered Wagon painted palette")
    parts = [
        pan_cube("timber wagon bed", (0, 0, .50), (.82, .43, .22), mat, 1),
        pan_cube("left bed rail", (0, -.40, .72), (.78, .045, .17), mat, 0, .018),
        pan_cube("right bed rail", (0, .40, .72), (.78, .045, .17), mat, 0, .018),
        pan_cube("front bed board", (-.77, 0, .70), (.055, .36, .16), mat, 2, .018),
        pan_cube("rear bed board", (.77, 0, .70), (.055, .36, .16), mat, 2, .018),
    ]
    for x in (-.58, .58):
        parts.append(pan_cylinder(f"axle {x}", (x, 0, .31), .050, .90, mat, 0, 10, (math.pi / 2, 0, 0)))
        for y in (-.47, .47):
            parts.append(pan_cylinder(f"dark wheel {x} {y}", (x, y, .31), .31, .08, mat, 9, 12, (math.pi / 2, 0, 0)))
            parts.append(pan_cylinder(f"brass hub {x} {y}", (x, y, .31), .115, .09, mat, 4, 10, (math.pi / 2, 0, 0)))

    canvas_profile = [(-.39, .70), (-.39, .97), (-.31, 1.20), (-.16, 1.36), (0, 1.42), (.16, 1.36), (.31, 1.20), (.39, .97), (.39, .70)]

    def arched_slice(name, x0, x1, profile, palette_index):
        vertices = [(x0, y, z) for y, z in profile] + [(x1, y, z) for y, z in profile]
        count = len(profile)
        faces = [tuple(range(count - 1, -1, -1)), tuple(range(count, count * 2))]
        faces.extend((index, index + 1, count + index + 1, count + index) for index in range(count - 1))
        faces.append((count - 1, 0, count, count * 2 - 1))
        return pan_prism(name, vertices, faces, mat, palette_index)

    parts.append(arched_slice("warm canvas cover", -.70, .70, canvas_profile, 8))
    rib_profile = [(y * 1.035, z + .018) for y, z in canvas_profile]
    for x in (-.62, 0, .62):
        parts.append(arched_slice(f"canvas rib {x}", x - .025, x + .025, rib_profile, 13))
    parts.append(pan_cube("driver bench", (-.56, 0, .86), (.18, .34, .055), mat, 12, .018))
    join_and_export_palette("covered_wagon", parts, mat)


def trough():
    reset()
    mat = pan_material("Water Trough painted palette")
    parts = [pan_cube("dark timber base", (0, 0, .14), (.78, .31, .14), mat, 0)]
    parts += [pan_cube(f"plank side {y}", (0, y, .38), (.82, .07, .27), mat, 1) for y in (-.31, .31)]
    parts += [pan_cube(f"plank end {x}", (x, 0, .38), (.07, .25, .27), mat, 2) for x in (-.75, .75)]
    parts += [pan_cube(f"light rim {y}", (0, y, .615), (.76, .035, .035), mat, 12, .012) for y in (-.31, .31)]
    parts += [pan_cube(f"light end rim {x}", (x, 0, .615), (.035, .24, .035), mat, 12, .012) for x in (-.75, .75)]
    parts.append(pan_cube("still teal water", (0, 0, .53), (.68, .22, .018), mat, 3, 0))
    join_and_export_palette("water_trough", parts, mat)


def pan_material(name):
    image = bpy.data.images.new(f"{name}Atlas", PAN_PALETTE_SIZE, PAN_PALETTE_SIZE, alpha=False)
    image.colorspace_settings.name = "sRGB"
    pixels = [0.0] * (PAN_PALETTE_SIZE * PAN_PALETTE_SIZE * 4)
    cell = PAN_PALETTE_SIZE // PAN_PALETTE_COLUMNS
    for y in range(PAN_PALETTE_SIZE):
        for x in range(PAN_PALETTE_SIZE):
            index = min(len(PAN_PALETTE) - 1, (y // cell) * PAN_PALETTE_COLUMNS + x // cell)
            offset = (y * PAN_PALETTE_SIZE + x) * 4
            pixels[offset:offset + 4] = (*PAN_PALETTE[index], 1.0)
    image.pixels.foreach_set(pixels)
    image.update()
    temporary_atlas = ROOT / f".{name.lower().replace(' ', '-')}-atlas.png"
    image.filepath_raw = str(temporary_atlas)
    image.file_format = "PNG"
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.image_settings.color_mode = "RGB"
    image.save()
    image.pack()
    temporary_atlas.unlink(missing_ok=True)

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Closest"
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Roughness"].default_value = 0.9
    mat.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    mat.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return mat


def pan_uv(obj, palette_index):
    uv_layer = obj.data.uv_layers.get("UVMap") or obj.data.uv_layers.new(name="UVMap")
    column = palette_index % PAN_PALETTE_COLUMNS
    row = palette_index // PAN_PALETTE_COLUMNS
    uv = ((column + 0.5) / PAN_PALETTE_COLUMNS, (row + 0.5) / PAN_PALETTE_COLUMNS)
    for loop in uv_layer.data:
        loop.uv = uv


def pan_cube(name, location, scale, mat, palette_index, bevel=.035):
    obj = cube(name, location, scale, mat, bevel)
    obj["palette_index"] = palette_index
    return obj


def pan_cylinder(name, location, radius, depth, mat, palette_index, vertices=12, rotation=(0, 0, 0)):
    obj = cylinder(name, location, radius, depth, mat, vertices, rotation)
    obj["palette_index"] = palette_index
    return obj


def pan_prism(name, vertices, faces, mat, palette_index):
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj["palette_index"] = palette_index
    return obj


def pan_torus(name, location, major_radius, minor_radius, mat, palette_index, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=16,
        minor_segments=6,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    obj["palette_index"] = palette_index
    return obj


def pan_beam_between(name, start, end, radius, mat, palette_index, vertices=10):
    start_v = Vector(start)
    end_v = Vector(end)
    direction = end_v - start_v
    obj = pan_cylinder(name, (start_v + end_v) * 0.5, radius, direction.length, mat, palette_index, vertices)
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return obj


def join_and_export_palette(name, parts, mat):
    converted = []
    for part in parts:
        bpy.ops.object.select_all(action="DESELECT")
        part.select_set(True)
        bpy.context.view_layer.objects.active = part
        bpy.ops.object.convert(target="MESH")
        pan_uv(part, int(part.get("palette_index", 1)))
        converted.append(part)

    bpy.ops.object.select_all(action="DESELECT")
    for part in converted:
        part.select_set(True)
    bpy.context.view_layer.objects.active = converted[0]
    bpy.ops.object.join()
    model = bpy.context.object
    model.name = name
    model.data.name = "Cylinder" if name == "pan_monument" else f"{name}Mesh"
    model.data.materials.clear()
    model.data.materials.append(mat)
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    model["asset_role"] = "town_plaza_prop"
    model["material_contract"] = "one packed palette atlas"
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / f"{name}.blend"))
    bpy.ops.export_scene.gltf(
        filepath=str(ROOT / f"{name}.glb"),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_materials="EXPORT",
    )


def monument():
    reset()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.context.scene.unit_settings.system = "METRIC"
    mat = pan_material("Pan Monument painted palette")
    parts = [
        pan_cylinder("lower dark plinth", (0, 0, .16), .76, .32, mat, 6, 12),
        pan_cylinder("upper warm plinth", (0, 0, .39), .62, .20, mat, 7, 12),
        pan_cylinder("brass collar", (0, 0, .55), .35, .12, mat, 4, 12),
        pan_cylinder("dark stem", (0, 0, 1.02), .16, .88, mat, 6, 10),
        pan_torus("teal civic band", (0, 0, .84), .20, .050, mat, 3),
    ]

    pan_center = Vector((-0.08, 0.0, 1.64))
    rotation = Matrix.Rotation(math.radians(28), 4, "X") @ Matrix.Rotation(math.radians(13), 4, "Z")
    pan_euler = rotation.to_euler()
    normal = rotation @ Vector((0.0, 0.0, 1.0))

    segments = 20
    rings = ((0.0, -.22), (.24, -.16), (.46, -.06), (.60, .025))
    vertices = [tuple(pan_center + rotation @ Vector((0.0, 0.0, rings[0][1])))]
    for radius, height in rings[1:]:
        vertices.extend(
            tuple(pan_center + rotation @ Vector((math.cos(index / segments * math.tau) * radius, math.sin(index / segments * math.tau) * radius, height)))
            for index in range(segments)
        )
    faces = []
    for index in range(segments):
        faces.append((0, 1 + index, 1 + (index + 1) % segments))
    for ring_index in range(1, len(rings) - 1):
        inner_start = 1 + (ring_index - 1) * segments
        outer_start = 1 + ring_index * segments
        for index in range(segments):
            faces.append((
                inner_start + index,
                outer_start + index,
                outer_start + (index + 1) % segments,
                inner_start + (index + 1) % segments,
            ))
    mesh = bpy.data.meshes.new("ConcavePanBasinMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    basin = bpy.data.objects.new("concave gold pan basin", mesh)
    bpy.context.collection.objects.link(basin)
    basin.data.materials.append(mat)
    basin["palette_index"] = 4
    parts.append(basin)
    rim_center = pan_center + normal * .025
    parts.append(pan_torus("tilted brass pan rim", rim_center, .60, .060, mat, 4, pan_euler))

    bpy.ops.mesh.primitive_circle_add(
        vertices=20,
        radius=.30,
        fill_type="TRIFAN",
        location=pan_center + rotation @ Vector((0.0, 0.0, -.205)),
        rotation=pan_euler,
    )
    bottom = bpy.context.object
    bottom.name = "bright gold pan bottom"
    bottom.data.materials.append(mat)
    bottom["palette_index"] = 7
    parts.append(bottom)

    def pan_point(x, y, z=-.13):
        return pan_center + rotation @ Vector((x, y, z))

    for index, (y, half_width) in enumerate(((-.09, .24), (.04, .21))):
        parts.append(pan_beam_between(
            f"pan riffle {index + 1}",
            pan_point(-half_width, y),
            pan_point(half_width, y),
            .019,
            mat,
            6,
            6,
        ))

    handle_direction = rotation @ Vector((1.0, 0.0, 0.0))
    handle_start = pan_center + handle_direction * .54
    handle_end = pan_center + handle_direction * 1.38
    parts.append(pan_beam_between("long visible pan handle", handle_start, handle_end, .080, mat, 0, 10))
    parts.append(pan_cylinder("handle cap", handle_end, .110, .075, mat, 4, 10, handle_direction.to_track_quat("Z", "Y").to_euler()))

    for index, (x, y, size, palette_index) in enumerate(((-.06, .20, .110, 14), (.08, .20, .145, 5), (.23, .14, .105, 14), (.13, .04, .090, 5))):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=size, location=pan_point(x, y, -.115))
        nugget = bpy.context.object
        nugget.name = f"gold nugget {index + 1}"
        nugget.data.materials.append(mat)
        nugget["palette_index"] = palette_index
        parts.append(nugget)

    join_and_export_palette("pan_monument", parts, mat)


BUILDERS = {
    "covered_wagon": wagon,
    "water_trough": trough,
    "pan_monument": monument,
}


def main():
    parser = argparse.ArgumentParser(description="Build one or all Town plaza prop pilots")
    parser.add_argument("target", nargs="?", choices=tuple(BUILDERS), help="omit to rebuild every prop")
    script_args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(script_args)
    if args.target:
        BUILDERS[args.target]()
    else:
        for build in BUILDERS.values():
            build()


if __name__ == "__main__":
    main()
