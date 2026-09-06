from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent
ATLAS = ROOT / "era-props-e3-atlas.png"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


common = load_module("era_props_e2_build", ROOT / "build_era_props_e2.py")
common.ATLAS = ATLAS

SOURCE_HASHES = {
    "covered_wagon.e2": {
        "blend": "178a59a70e47d6349c34f6aeb19d5c300914b0af1d52bd54231086e9e9b9a089",
        "glb": "f212d6a2f655ac23a22efe1eca0f48608e58d9a08d63e5a485348431525d7417",
    },
    "water_trough.e2": {
        "blend": "05f53cd0db08110e98f0e9f93af418a2b8345cc049bda9072580680bb0dc8a0c",
        "glb": "65622eea7d9967fe3b53cbbddeecc2a0f8ab779803f5ef86010a790bc1f79f17",
    },
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def beam(name, start, end, radius, material, palette_index, vertices=6):
    start, end = Vector(start), Vector(end)
    delta = end - start
    obj = common.cylinder(name, radius, delta.length, (start + end) * 0.5, material, palette_index, vertices)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def insulator(parts, prefix, x, y, base, material, vertices=8):
    parts.append(common.cylinder(f"{prefix} iron pin", 0.045, 0.38, (x, y, base + 0.19), material, 4, vertices))
    for index, z in enumerate((base + 0.16, base + 0.27), 1):
        parts.append(common.cylinder(f"{prefix} ceramic skirt {index}", 0.13, 0.065, (x, y, z), material, 15, vertices + 2))
    parts.append(common.cylinder(f"{prefix} copper cap", 0.065, 0.08, (x, y, base + 0.38), material, 6, vertices))


def wagon_filament_festoon(material):
    points = [(-0.60, 1.30), (-0.30, 1.25), (0, 1.23), (0.30, 1.25), (0.60, 1.30)]
    drops = [(-0.45, 1.275), (0, 1.23), (0.45, 1.275)]
    wire_vertices, wire_faces = [], []
    for side in (-1, 1):
        for start, end in zip(points, points[1:]):
            offset = len(wire_vertices)
            wire_vertices.extend((
                (start[0], side * 0.335, start[1] - 0.014), (end[0], side * 0.335, end[1] - 0.014),
                (end[0], side * 0.335, end[1] + 0.014), (start[0], side * 0.335, start[1] + 0.014),
            ))
            wire_faces.append((offset, offset + 1, offset + 2, offset + 3))
    wire_mesh = bpy.data.meshes.new("Wagon filament wire mesh")
    wire_mesh.from_pydata(wire_vertices, [], wire_faces)
    wire = bpy.data.objects.new("Wagon copper filament wire", wire_mesh)
    bpy.context.collection.objects.link(wire)
    common.tag(wire, material, 6, 0)

    hardware_vertices, hardware_faces = [], []
    for side in (-1, 1):
        for x, z in drops:
            offset = len(hardware_vertices)
            hardware_vertices.extend((
                (x - 0.012, side * 0.342, z - 0.010), (x + 0.012, side * 0.342, z - 0.010),
                (x + 0.012, side * 0.342, z - 0.068), (x - 0.012, side * 0.342, z - 0.068),
            ))
            hardware_faces.append((offset, offset + 1, offset + 2, offset + 3))
        for x, z in (points[0], points[2], points[-1]):
            offset = len(hardware_vertices)
            hardware_vertices.extend((
                (x - 0.030, side * 0.340, z - 0.040), (x + 0.030, side * 0.340, z - 0.040),
                (x + 0.030, side * 0.340, z + 0.040), (x - 0.030, side * 0.340, z + 0.040),
            ))
            hardware_faces.append((offset, offset + 1, offset + 2, offset + 3))
    hardware_mesh = bpy.data.meshes.new("Wagon filament hardware mesh")
    hardware_mesh.from_pydata(hardware_vertices, [], hardware_faces)
    hardware = bpy.data.objects.new("Wagon filament hangers and rib clamps", hardware_mesh)
    bpy.context.collection.objects.link(hardware)
    common.tag(hardware, material, 6, 0)

    bulb_vertices, bulb_faces = [], []
    for side in (-1, 1):
        for x, z in drops:
            offset = len(bulb_vertices)
            center_y, center_z = side * 0.355, z - 0.112
            bulb_vertices.extend((
                (x, center_y, center_z + 0.050), (x, center_y, center_z - 0.050),
                (x - 0.045, center_y, center_z), (x, center_y + side * 0.040, center_z),
                (x + 0.045, center_y, center_z), (x, center_y - side * 0.040, center_z),
            ))
            ring = (2, 3, 4, 5)
            for index, vertex in enumerate(ring):
                following = ring[(index + 1) % len(ring)]
                bulb_faces.extend(((offset, offset + vertex, offset + following),
                                   (offset + 1, offset + following, offset + vertex)))
    bulb_mesh = bpy.data.meshes.new("Wagon filament bulbs mesh")
    bulb_mesh.from_pydata(bulb_vertices, [], bulb_faces)
    mesh = bmesh.new()
    mesh.from_mesh(bulb_mesh)
    bmesh.ops.recalc_face_normals(mesh, faces=mesh.faces)
    mesh.to_mesh(bulb_mesh)
    mesh.free()
    bulbs = bpy.data.objects.new("Wagon warm filament dots", bulb_mesh)
    bpy.context.collection.objects.link(bulbs)
    common.tag(bulbs, material, 5, 0)
    return wire, hardware, bulbs


def source_variant(stem, object_name):
    blend, glb = ROOT / f"{stem}.blend", ROOT / f"{stem}.glb"
    assert sha256(blend) == SOURCE_HASHES[stem]["blend"]
    assert sha256(glb) == SOURCE_HASHES[stem]["glb"]
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    for obj in list(bpy.data.objects):
        if obj.type == "EMPTY" and obj.name.startswith("steam_anchor_"):
            bpy.data.objects.remove(obj, do_unlink=True)
    model = bpy.data.objects[object_name]
    model["preserve_uv"] = True
    return model, model.data.materials[0], tuple(model.dimensions)


def add_arc_anchors(locations, parent):
    anchors = []
    for index, location in enumerate(locations, 1):
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=location)
        anchor = bpy.context.object
        anchor.name = f"arc_anchor_{index}"
        anchor.empty_display_size = 0.08
        anchor.parent = parent
        anchors.append(anchor)
    return anchors


def finish(name, stem, parts, material, anchors=(), shared=True, triangle_limit=1000,
           expected_dimensions=None):
    common.apply_palette_uv(parts, shared)
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
    anchors = add_arc_anchors(anchors, model)
    triangles = sum(len(polygon.vertices) - 2 for polygon in model.data.polygons)
    assert triangles <= triangle_limit, (name, triangles, triangle_limit)
    blend, glb = ROOT / f"{stem}.blend", ROOT / f"{stem}.glb"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.object.select_all(action="DESELECT")
    model.select_set(True)
    for anchor in anchors:
        anchor.select_set(True)
    bpy.context.view_layer.objects.active = model
    bpy.ops.export_scene.gltf(
        filepath=str(glb), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT",
    )
    return {"id": stem, "triangles": triangles, "sha256": sha256(glb),
            "anchors": [anchor.name for anchor in anchors], "dimensions": list(model.dimensions)}


def finish_variant(name, stem, parts, material, anchors, dimensions, triangle_limit):
    parts[0]["epoch_variant"] = "E3 Voltage Age"
    for part in parts[1:]:
        part.modifiers.clear()
    model_info = finish(
        name, stem, parts, material, anchors=anchors, shared=False, triangle_limit=triangle_limit,
        expected_dimensions=dimensions,
    )
    return model_info


def build_wagon():
    model, material, dimensions = source_variant("covered_wagon.e2", "CoveredWagonE2")
    parts = [model]
    insulator(parts, "Wagon roof terminal", 0, 0.34, 0.91, material, 4)
    parts.append(beam("Wagon copper roof line", (-0.34, 0.34, 1.29), (0.34, 0.34, 1.29), 0.035, material, 6, 4))
    parts.extend(wagon_filament_festoon(material))
    return finish_variant(
        "CoveredWagonE3", "covered_wagon.e3", parts, material,
        [(0, 0.34, 1.35)], dimensions, 1800,
    )


def build_trough():
    model, material, dimensions = source_variant("water_trough.e2", "WaterTroughE2")
    parts = [model,
        common.cylinder("Trough electric pump", 0.16, 0.42, (0.48, 0.20, 0.36), material, 6, 10, rotation=(0, math.pi / 2, 0)),
        common.torus("Trough pump status ring", 0.12, 0.025, (0.48, -0.02, 0.36), material, 9, rotation=(math.pi / 2, 0, 0)),
        beam("Trough insulated feed", (-0.50, 0.24, 0.57), (0.48, 0.20, 0.54), 0.035, material, 6),
    ]
    for index, x in enumerate((-0.50, 0.02), 1):
        insulator(parts, f"Trough feed terminal {index}", x, 0.24, 0.18, material)
    return finish_variant(
        "WaterTroughE3", "water_trough.e3", parts, material,
        [(-0.50, 0.24, 0.62), (0.02, 0.24, 0.62)], dimensions, 1200,
    )


def accessory_material():
    material = common.material_from_atlas()
    material.name = "E3EraPropsSharedMaterial"
    return material


def finish_accessory(name, stem, parts, material, anchors):
    for part in parts:
        part.modifiers.clear()
    return finish(name, stem, parts, material, anchors=anchors)


def build_wire_run():
    common.reset(); material = accessory_material(); parts = []
    for index, x in enumerate((-0.90, 0.90), 1):
        parts.extend((
            common.box(f"Wire span foot {index}", (0.34, 0.42, 0.12), (x, 0, 0.06), material, 13),
            common.box(f"Wire span timber post {index}", (0.11, 0.11, 1.45), (x, 0, 0.78), material, 2),
            common.box(f"Wire span crossarm {index}", (0.56, 0.10, 0.10), (x, 0, 1.42), material, 4),
        ))
        insulator(parts, f"Wire span terminal {index}", x, 0, 1.28, material)
    cable = [(-0.90, 0, 1.66), (-0.45, 0, 1.56), (0, 0, 1.52), (0.45, 0, 1.56), (0.90, 0, 1.66)]
    for index, (start, end) in enumerate(zip(cable, cable[1:]), 1):
        parts.append(beam(f"Copper catenary {index}", start, end, 0.035, material, 6))
    return finish_accessory(
        "WireRunE3", "wire-run.e3", parts, material,
        [(-0.90, 0, 1.72), (0.90, 0, 1.72)],
    )


def build_insulator_post():
    common.reset(); material = accessory_material()
    parts = [
        common.cylinder("Insulator post footing", 0.30, 0.16, (0, 0, 0.08), material, 13, 12),
        common.cylinder("Insulator post iron shaft", 0.08, 1.42, (0, 0, 0.79), material, 4, 10),
        common.box("Insulator post crossarm", (0.78, 0.10, 0.10), (0, 0, 1.42), material, 4),
    ]
    for index, x in enumerate((-0.28, 0.28), 1):
        insulator(parts, f"Insulator post terminal {index}", x, 0, 1.34, material)
    parts.append(beam("Insulator post copper jumper", (-0.28, 0, 1.72), (0.28, 0, 1.72), 0.035, material, 6))
    return finish_accessory(
        "InsulatorPostE3", "insulator-post.e3", parts, material,
        [(-0.28, 0, 1.78), (0.28, 0, 1.78)],
    )


def build_transformer_shed():
    common.reset(); material = accessory_material()
    parts = [
        common.box("Transformer shed stone foot", (1.42, 1.02, 0.16), (0, 0, 0.08), material, 13),
        common.box("Transformer shed timber shell", (1.28, 0.92, 1.20), (0, 0, 0.70), material, 2),
        common.box("Transformer shed iron roof", (1.52, 1.12, 0.16), (0, 0, 1.36), material, 4, rotation=(0, 0.10, 0)),
        common.box("Transformer shed dark door", (0.42, 0.06, 0.72), (0, -0.49, 0.54), material, 12),
        common.torus("Transformer public coil", 0.25, 0.045, (0, -0.54, 0.92), material, 9, rotation=(math.pi / 2, 0, 0)),
        common.cylinder("Transformer coil hub", 0.08, 0.08, (0, -0.56, 0.92), material, 6, 8, rotation=(math.pi / 2, 0, 0)),
        common.box("Transformer roof crossarm", (1.12, 0.10, 0.10), (0, 0, 1.52), material, 4),
    ]
    for index, x in enumerate((-0.38, 0, 0.38), 1):
        insulator(parts, f"Transformer roof terminal {index}", x, 0, 1.44, material)
    parts.append(beam("Transformer copper roof bus", (-0.38, 0, 1.82), (0.38, 0, 1.82), 0.04, material, 6))
    return finish_accessory(
        "TransformerShedE3", "transformer-shed.e3", parts, material,
        [(-0.38, 0, 1.88), (0, 0, 1.88), (0.38, 0, 1.88)],
    )


def main():
    common.write_shared_atlas()
    results = [build_wagon(), build_trough(), build_wire_run(), build_insulator_post(), build_transformer_shed()]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
