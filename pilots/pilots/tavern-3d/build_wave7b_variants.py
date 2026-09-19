from pathlib import Path
import hashlib
import json
import math

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[3]

STANDARD_REGIONS = {
    "wall": (0.02, 0.02, 0.48, 0.48),
    "roof": (0.52, 0.52, 0.98, 0.98),
    "trim": (0.02, 0.52, 0.23, 0.73),
    "door": (0.52, 0.02, 0.73, 0.48),
    "window": (0.77, 0.02, 0.98, 0.48),
    "deck": (0.27, 0.52, 0.48, 0.73),
    "stone": (0.02, 0.77, 0.23, 0.98),
    "accent": (0.27, 0.77, 0.48, 0.98),
    "foliage": (0.02, 0.77, 0.23, 0.98),
}
DYNAMO_REGIONS = {
    "brick": (0.02, 0.02, 0.48, 0.48),
    "roof": (0.52, 0.52, 0.98, 0.98),
    "timber": (0.02, 0.52, 0.23, 0.73),
    "window": (0.52, 0.02, 0.73, 0.48),
    "copper": (0.77, 0.02, 0.98, 0.48),
    "stone": (0.27, 0.52, 0.48, 0.73),
    "teal": (0.02, 0.77, 0.23, 0.98),
    "dark": (0.27, 0.77, 0.48, 0.98),
}

SPECS = {
    "general_store": {
        "directory": "general-store-3d", "stem": "general-store", "object": "GeneralStoreFullWrap",
        "output": "GeneralStoreE2", "blend_sha": "7dcd16a3538931e1772278ddbac1f8b26e190b1ddff4e1670b7fb72b0d8fac4e",
        "glb_sha": "b5f254861353b3ba7f3cf52d8ab1bffffc176cb2226d5edba50d85639163c154",
        "uv": {"iron": STANDARD_REGIONS["window"], "brass": STANDARD_REGIONS["deck"],
               "teal": STANDARD_REGIONS["accent"], "face": STANDARD_REGIONS["stone"]},
    },
    "schoolhouse": {
        "directory": "schoolhouse-3d", "stem": "schoolhouse", "object": "SchoolhouseFullWrap",
        "output": "SchoolhouseE2", "blend_sha": "ebe299897e6f59a564889c5d9731e1ff8333584dbe18506786357a24e092ef6f",
        "glb_sha": "83290545b29f1ba16a5bc59de239b12c8e6bc594a8382320b3ceb8c3778f03d0",
        "uv": {"iron": STANDARD_REGIONS["window"], "brass": STANDARD_REGIONS["accent"],
               "teal": STANDARD_REGIONS["stone"], "face": STANDARD_REGIONS["wall"]},
    },
    "assay_office": {
        "directory": "assay-office-3d", "stem": "assay-office", "object": "AssayOfficeFullWrap",
        "output": "AssayOfficeE2", "blend_sha": "07d9b7345b6ae8647a4bf5a615b7f4625578734d6bf250bd3f17e0cdc524c9fa",
        "glb_sha": "8005176893d4b2b4c465ec8e75d4a6b53c0ffa19d1212f7c99c6c825033adeb4",
        "uv": {"iron": STANDARD_REGIONS["door"], "brass": STANDARD_REGIONS["accent"],
               "teal": STANDARD_REGIONS["roof"], "face": STANDARD_REGIONS["stone"]},
    },
    "chapel": {
        "directory": "chapel-3d", "stem": "chapel", "object": "ChapelFullWrap",
        "output": "ChapelE2", "blend_sha": "cf84d4dacce680130577be3d3bcdc3f75c5a4a789541c1de543e7e15e1d6fd59",
        "glb_sha": "7422e20113ae7c21b5231a6468ca1a051a1c7bd4c895ed874b775d9372d7b84b",
        "uv": {"iron": STANDARD_REGIONS["window"], "brass": STANDARD_REGIONS["accent"],
               "teal": STANDARD_REGIONS["foliage"], "face": STANDARD_REGIONS["wall"]},
    },
    "stamp_mill": {
        "directory": "stamp-mill-3d", "stem": "stamp-mill", "object": "StampMillFullWrap",
        "output": "StampMillE2", "blend_sha": "b122221dbeb0697cdb465e6bd20a3c7164b3cad4688b75ae1b06b7dade4c9596",
        "glb_sha": "4e2d1acb932a9c41a5d4278de39dcffe00ce30920261c1a2f114a794f343b6aa",
        "uv": {"iron": STANDARD_REGIONS["window"], "brass": STANDARD_REGIONS["accent"],
               "teal": STANDARD_REGIONS["stone"], "face": STANDARD_REGIONS["wall"]},
    },
    "dynamo_hall": {
        "directory": "dynamo-hall-3d", "stem": "dynamo-hall", "object": "DynamoHallFullWrap",
        "output": "DynamoHallE2", "blend_sha": "7e1c17772d0f7f59b296de26e908dbaaa7eb85139bae677116fff0b6041cc58b",
        "glb_sha": "3e8f70f2a4e990ef729ffb4ee80de6ff2d2e4828f86a31d794a821db487fcefb",
        "uv": {"iron": DYNAMO_REGIONS["dark"], "brass": DYNAMO_REGIONS["copper"],
               "teal": DYNAMO_REGIONS["teal"], "face": DYNAMO_REGIONS["stone"]},
    },
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tag(obj, material, uv_bounds, bevel=0.01):
    obj.data.materials.append(material)
    obj["e2_uv_bounds"] = list(uv_bounds)
    if bevel:
        modifier = obj.modifiers.new("Painted edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        modifier.limit_method = "ANGLE"
    return obj


def box(name, size, location, material, uv_bounds, bevel=0.01, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = tuple(value / 2 for value in size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return tag(obj, material, uv_bounds, bevel)


def cylinder(name, radius, depth, location, material, uv_bounds, vertices=12, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    return tag(obj, material, uv_bounds, 0.008)


def torus(name, major_radius, minor_radius, location, material, uv_bounds, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius, minor_radius=minor_radius, major_segments=16, minor_segments=6,
        location=location, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    return tag(obj, material, uv_bounds, 0)


def tank(parts, prefix, x, y, base, top, material, uv):
    center = (base + top) * 0.5
    parts.extend((
        cylinder(f"{prefix} pressure tank", 0.29, top - base, (x, y, center), material, uv["iron"], 12),
        cylinder(f"{prefix} lower band", 0.325, 0.11, (x, y, base + 0.18), material, uv["brass"], 12),
        cylinder(f"{prefix} center band", 0.325, 0.11, (x, y, center), material, uv["teal"], 12),
        cylinder(f"{prefix} upper band", 0.325, 0.11, (x, y, top - 0.18), material, uv["brass"], 12),
    ))


def stack(parts, prefix, x, y, base, top, material, uv, radius=0.15):
    parts.extend((
        cylinder(f"{prefix} stack", radius, top - base, (x, y, (base + top) * 0.5), material, uv["iron"], 12),
        cylinder(f"{prefix} lower flange", radius + 0.055, 0.11, (x, y, base + 0.12), material, uv["brass"], 12),
        cylinder(f"{prefix} upper flange", radius + 0.055, 0.11, (x, y, top - 0.22), material, uv["brass"], 12),
        cylinder(f"{prefix} cap", radius + 0.085, 0.14, (x, y, top - 0.07), material, uv["teal"], 12),
    ))


def gauge(parts, prefix, x, y, z, material, uv, face_positive_y=True, radius=0.27):
    sign = 1 if face_positive_y else -1
    parts.extend((
        cylinder(f"{prefix} gauge rim", radius, 0.09, (x, y, z), material, uv["brass"], 16,
                 rotation=(math.pi / 2, 0, 0)),
        cylinder(f"{prefix} gauge face", radius * 0.76, 0.10, (x, y + sign * 0.035, z), material,
                 uv["face"], 16, rotation=(math.pi / 2, 0, 0)),
        box(f"{prefix} gauge needle", (0.035, 0.025, radius * 0.66),
            (x + radius * 0.10, y + sign * 0.09, z + radius * 0.08), material, uv["teal"], 0.003,
            rotation=(0, 0.52, 0)),
    ))


def add_general_store(material, uv):
    parts = []
    tank(parts, "Store loading", 1.95, 1.28, 0.42, 2.06, material, uv)
    stack(parts, "Store loading", 1.95, 1.28, 2.02, 4.26, material, uv, 0.16)
    parts.extend((
        cylinder("Store overhead steam header", 0.075, 1.55, (1.18, 1.28, 2.18), material, uv["brass"], 10,
                 rotation=(0, math.pi / 2, 0)),
        torus("Store loading shutoff", 0.18, 0.035, (1.35, 1.54, 2.18), material, uv["teal"],
              rotation=(math.pi / 2, 0, 0)),
    ))
    gauge(parts, "Store loading", 0.42, 1.46, 2.20, material, uv)
    return parts, [(1.43, 0.62, 4.44), (1.95, 1.28, 4.31)], "loading boiler, overhead header, dial, relief stack"


def add_schoolhouse(material, uv):
    parts = []
    tank(parts, "School lesson", 1.58, 1.33, 0.38, 1.98, material, uv)
    stack(parts, "School lesson", 1.58, 1.33, 1.94, 5.22, material, uv, 0.14)
    gauge(parts, "School lesson", 0.30, 1.54, 2.08, material, uv, radius=0.31)
    parts.append(
        cylinder("School whistle feed header", 0.075, 0.70, (1.25, 1.33, 3.57), material,
                 uv["iron"], 10, rotation=(0, math.pi / 2, 0))
    )
    for x, height in ((1.18, 4.68), (0.92, 4.38)):
        parts.extend((
            cylinder(f"School steam whistle {x}", 0.07, height - 3.54, (x, 1.33, (height + 3.54) * 0.5),
                     material, uv["brass"], 10),
            cylinder(f"School whistle cap {x}", 0.11, 0.10, (x, 1.33, height - 0.05), material, uv["teal"], 10),
        ))
    return parts, [(1.58, 1.33, 5.30), (1.18, 1.33, 4.72), (0.92, 1.33, 4.42)], "lesson boiler, public dial, paired steam whistles"


def add_assay_office(material, uv):
    parts = []
    tank(parts, "Assay retort", 1.84, 1.28, 0.38, 1.92, material, uv)
    stack(parts, "Assay retort", 1.84, 1.28, 1.88, 4.05, material, uv, 0.145)
    gauge(parts, "Assay retort", 0.25, 1.50, 2.35, material, uv, radius=0.29)
    for z in (1.05, 1.38, 1.71, 2.04):
        parts.append(cylinder(f"Assay condenser coil {z}", 0.055, 1.25, (0.72, 1.54, z), material,
                              uv["brass"], 10, rotation=(0, math.pi / 2, 0)))
    parts.extend((
        cylinder("Assay condenser left riser", 0.065, 1.18, (0.10, 1.54, 1.55), material, uv["iron"], 10),
        cylinder("Assay condenser right riser", 0.065, 1.18, (1.34, 1.54, 1.55), material, uv["iron"], 10),
    ))
    return parts, [(1.84, 1.28, 4.12)], "retort boiler, condenser rack, pressure dial, relief stack"


def add_chapel(material, uv):
    parts = []
    tank(parts, "Chapel heating", 1.36, 1.25, 0.34, 1.82, material, uv)
    stack(parts, "Chapel heating", 1.36, 1.25, 1.78, 5.34, material, uv, 0.13)
    gauge(parts, "Chapel heating", 0.25, 1.44, 2.10, material, uv, radius=0.25)
    for x in (-0.88, -0.44, 0.0, 0.44, 0.88):
        parts.append(cylinder(f"Chapel radiator riser {x}", 0.045, 0.82, (x, 1.50, 1.15), material,
                              uv["brass"], 8))
    parts.append(cylinder("Chapel radiator header", 0.055, 1.90, (0, 1.50, 1.58), material, uv["iron"], 10,
                          rotation=(0, math.pi / 2, 0)))
    return parts, [(1.36, 1.25, 5.42)], "meeting-house heating tank, radiator bank, tall copper flue"


def add_stamp_mill(material, uv):
    parts = []
    parts.extend((
        cylinder("Mill horizontal receiver", 0.28, 1.34, (1.96, -0.48, 1.72), material, uv["iron"], 14,
                 rotation=(0, math.pi / 2, 0)),
        cylinder("Mill receiver band left", 0.32, 0.11, (1.48, -0.48, 1.72), material, uv["brass"], 14,
                 rotation=(0, math.pi / 2, 0)),
        cylinder("Mill receiver band right", 0.32, 0.11, (2.44, -0.48, 1.72), material, uv["teal"], 14,
                 rotation=(0, math.pi / 2, 0)),
        cylinder("Mill piston feed", 0.075, 1.55, (0.82, -0.54, 2.18), material, uv["brass"], 10,
                 rotation=(0, math.pi / 2, 0)),
    ))
    for index, x in enumerate((-1.04, 1.04), 1):
        parts.extend((
            cylinder(f"Mill roof gantry riser {index}", 0.13, 1.22, (x, -0.28, 3.52), material,
                     uv["iron"], 12),
            cylinder(f"Mill roof gantry foot {index}", 0.20, 0.12, (x, -0.28, 2.98), material,
                     uv["brass"], 12),
        ))
    parts.extend((
        cylinder("Mill roof pressure header", 0.15, 2.34, (0, -0.28, 4.11), material,
                 uv["teal"], 12, rotation=(0, math.pi / 2, 0)),
        cylinder("Mill roof header brass cap", 0.20, 0.13, (-1.13, -0.28, 4.11), material,
                 uv["brass"], 12, rotation=(0, math.pi / 2, 0)),
        cylinder("Mill roof header teal cap", 0.20, 0.13, (1.13, -0.28, 4.11), material,
                 uv["teal"], 12, rotation=(0, math.pi / 2, 0)),
        cylinder("Mill roof header shutoff stem", 0.055, 0.26, (0, -0.28, 4.28), material,
                 uv["brass"], 10),
        torus("Mill roof header shutoff", 0.23, 0.05, (0, -0.28, 4.28), material, uv["teal"]),
    ))
    stack(parts, "Mill receiver", 2.56, 0.42, 2.10, 4.34, material, uv, 0.14)
    gauge(parts, "Mill receiver", 0.15, -0.69, 2.62, material, uv, face_positive_y=False, radius=0.28)
    return parts, [(-2.15, 0.25, 4.56), (2.56, 0.42, 4.42)], (
        "horizontal pressure receiver, piston feed, supported roof header gantry, second relief stack"
    )


def add_dynamo_hall(material, uv):
    parts = []
    tank(parts, "Dynamo accumulator", 2.31, 1.22, 0.34, 1.92, material, uv)
    stack(parts, "Dynamo exhaust east", 2.31, 1.22, 1.88, 4.03, material, uv, 0.14)
    stack(parts, "Dynamo exhaust west", 1.72, 1.22, 2.28, 3.78, material, uv, 0.12)
    gauge(parts, "Dynamo load", 0.42, 1.49, 2.12, material, uv, radius=0.32)
    parts.extend((
        cylinder("Dynamo copper bus header", 0.075, 1.55, (1.15, 1.28, 2.36), material, uv["brass"], 10,
                 rotation=(0, math.pi / 2, 0)),
        torus("Dynamo main shutoff", 0.19, 0.04, (1.34, 1.55, 2.36), material, uv["teal"],
              rotation=(math.pi / 2, 0, 0)),
    ))
    return parts, [(2.31, 1.22, 4.10), (1.72, 1.22, 3.85)], "side accumulator, twin exhausts, load dial, bus header"


BUILDERS = {
    "general_store": add_general_store,
    "schoolhouse": add_schoolhouse,
    "assay_office": add_assay_office,
    "chapel": add_chapel,
    "stamp_mill": add_stamp_mill,
    "dynamo_hall": add_dynamo_hall,
}


def apply_and_uv(parts):
    for obj in parts:
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
        u0, v0, u1, v1 = obj["e2_uv_bounds"]
        for loop, coord in zip(uv, coords):
            normalized = (coord - minimum) / span
            loop.uv = (u0 + normalized[0] * (u1 - u0), v0 + normalized[1] * (v1 - v0))
        obj.select_set(False)


def add_anchors(locations, parent):
    anchors = []
    for index, location in enumerate(locations, 1):
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=location)
        anchor = bpy.context.object
        anchor.name = f"steam_anchor_{index}"
        anchor.empty_display_size = 0.12
        anchor.parent = parent
        anchors.append(anchor)
    return anchors


def build_variant(key, spec):
    directory = ROOT / "assets/pilots" / spec["directory"]
    source_blend = directory / f'{spec["stem"]}.blend'
    source_glb = directory / f'{spec["stem"]}.glb'
    target_blend = directory / f'{spec["stem"]}.e2.blend'
    target_glb = directory / f'{spec["stem"]}.e2.glb'
    assert sha256(source_blend) == spec["blend_sha"], f"{key} E1 BLEND changed"
    assert sha256(source_glb) == spec["glb_sha"], f"{key} E1 GLB changed"

    bpy.ops.wm.open_mainfile(filepath=str(source_blend))
    model = bpy.data.objects[spec["object"]]
    source_dimensions = tuple(model.dimensions)
    material = model.data.materials[0]
    parts, anchor_locations, identity_edit = BUILDERS[key](material, spec["uv"])
    apply_and_uv(parts)

    bpy.ops.object.select_all(action="DESELECT")
    model.select_set(True)
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = model
    bpy.ops.object.join()
    model.name = spec["output"]
    model.data.name = f'{spec["output"]}Mesh'
    model.data.uv_layers.active.name = "UVMap"
    for polygon in model.data.polygons:
        polygon.material_index = 0
    while len(model.data.materials) > 1:
        model.data.materials.pop(index=len(model.data.materials) - 1)
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    model["epoch_variant"] = "E2 Steamworks"
    model["identity_edit"] = identity_edit
    assert all(abs(model.dimensions[index] - source_dimensions[index]) < 0.0001 for index in range(3)), (
        key, source_dimensions, tuple(model.dimensions),
    )

    anchors = add_anchors(anchor_locations, model)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(target_blend))
    bpy.ops.object.select_all(action="DESELECT")
    model.select_set(True)
    for anchor in anchors:
        anchor.select_set(True)
    bpy.context.view_layer.objects.active = model
    bpy.ops.export_scene.gltf(
        filepath=str(target_glb), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT",
    )
    triangles = sum(len(polygon.vertices) - 2 for polygon in model.data.polygons)
    assert triangles <= 15_000
    return {
        "id": key, "blend": str(target_blend.relative_to(ROOT)), "glb": str(target_glb.relative_to(ROOT)),
        "sha256": sha256(target_glb), "triangles": triangles, "dimensions": list(model.dimensions),
        "anchors": [anchor.name for anchor in anchors], "identityEdit": identity_edit,
    }


def main():
    results = [build_variant(key, spec) for key, spec in SPECS.items()]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
