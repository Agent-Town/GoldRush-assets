from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


common = load_module("wave7b_build", HERE / "build_wave7b_variants.py")
tavern_e2 = load_module("tavern_e2_build", HERE / "build_tavern_e2.py")


SPECS = {
    "tavern": {
        "directory": "tavern-3d", "stem": "tavern", "source": "tavern.e2",
        "object": "TownTavernE2", "output": "TownTavernE3",
        "blend_sha": "b6c9c12138f2e7b1c4fb93e0d140fd70449439930b36f56b872d07bed4e7ad3c",
        "glb_sha": "e72aa936ee8a5a24aa6a6840d7c43f9eb81c4005702585a93050ac3166af09ad",
        "uv": {
            "dark": tavern_e2.UV_DARK, "copper": tavern_e2.UV_BRASS,
            "teal": tavern_e2.UV_TEAL, "warm": tavern_e2.UV_BRASS,
        },
    },
    "schoolhouse": {
        "directory": "schoolhouse-3d", "stem": "schoolhouse", "source": "schoolhouse.e2",
        "object": "SchoolhouseE2", "output": "SchoolhouseE3",
        "blend_sha": "2c3953fe077a4bef62bdce90a25b14bd7c6fdc51977ed06e0bbfba99c96fa5b6",
        "glb_sha": "70391129ce38917012d3a7c3242d4d4420153d828c77a9fcb84b670973f5a6c6",
        "uv": {
            "dark": common.STANDARD_REGIONS["window"], "copper": common.STANDARD_REGIONS["accent"],
            "teal": common.STANDARD_REGIONS["stone"], "warm": common.STANDARD_REGIONS["deck"],
        },
    },
    "stamp_mill": {
        "directory": "stamp-mill-3d", "stem": "stamp-mill", "source": "stamp-mill",
        "object": "StampMillFullWrap", "output": "StampMillE3",
        "blend_sha": "b122221dbeb0697cdb465e6bd20a3c7164b3cad4688b75ae1b06b7dade4c9596",
        "glb_sha": "4e2d1acb932a9c41a5d4278de39dcffe00ce30920261c1a2f114a794f343b6aa",
        "uv": {
            "dark": common.STANDARD_REGIONS["window"], "copper": common.STANDARD_REGIONS["accent"],
            "teal": common.STANDARD_REGIONS["stone"], "warm": common.STANDARD_REGIONS["wall"],
        },
    },
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sphere(name, radius, location, material, uv_bounds, scale=(1, 1, 1), segments=10, rings=5):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, radius=radius, location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return common.tag(obj, material, uv_bounds, 0)


def beam(name, start, end, radius, material, uv_bounds, vertices=6):
    start, end = Vector(start), Vector(end)
    delta = end - start
    obj = common.cylinder(
        name, radius, delta.length, (start + end) * 0.5, material, uv_bounds, vertices,
    )
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def insulator(parts, prefix, x, y, base, material, uv):
    parts.append(common.cylinder(f"{prefix} iron pin", 0.055, 0.48, (x, y, base + 0.24), material, uv["dark"], 8))
    for index, z in enumerate((base + 0.20, base + 0.32), 1):
        parts.append(common.cylinder(f"{prefix} ceramic skirt {index}", 0.16, 0.075, (x, y, z), material, uv["warm"], 10))
    parts.append(common.cylinder(f"{prefix} copper cap", 0.075, 0.10, (x, y, base + 0.48), material, uv["copper"], 8))


def add_tavern(material, uv):
    parts = []
    supports = [(-1.72, -1.50, 2.48), (1.72, -1.50, 2.48)]
    for index, (x, y, z) in enumerate(supports, 1):
        parts.append(common.box(f"Lounge lamp arm {index}", (0.13, 0.18, 0.72), (x, y, z - 0.34), material, uv["dark"], 0.008))
        insulator(parts, f"Lounge arm {index}", x, y, z - 0.23, material, uv)

    cable = [supports[0], (-0.86, -1.53, 2.27), (0, -1.54, 2.18), (0.86, -1.53, 2.27), supports[1]]
    for index, (start, end) in enumerate(zip(cable, cable[1:]), 1):
        parts.append(beam(f"Lounge festoon wire {index}", start, end, 0.035, material, uv["dark"]))
    for index, point in enumerate(cable[1:-1], 1):
        x, y, z = point
        parts.extend((
            beam(f"Lounge festoon drop {index}", (x, y, z), (x, y, z - 0.16), 0.025, material, uv["copper"]),
            sphere(f"Lounge festoon bulb {index}", 0.105, (x, y, z - 0.24), material, uv["warm"], (0.82, 0.82, 1.12), 8, 4),
        ))

    sign_center = Vector((2.065, 0.48, 2.25))
    parts.append(common.cylinder(
        "Lounge voltage pictogram backplate", 0.27, 0.05, (2.055, 0.48, 2.25),
        material, uv["dark"], 8, rotation=(0, math.pi / 2, 0),
    ))
    parts.append(common.torus(
        "Lounge voltage pictogram ring", 0.31, 0.035, sign_center, material, uv["teal"],
        rotation=(0, math.pi / 2, 0),
    ))
    bolt = [
        sign_center + Vector((0, -0.10, 0.23)),
        sign_center + Vector((0, 0.04, 0.03)),
        sign_center + Vector((0, -0.04, 0.03)),
        sign_center + Vector((0, 0.11, -0.24)),
    ]
    for index, (start, end) in enumerate(zip(bolt, bolt[1:]), 1):
        parts.append(beam(f"Lounge voltage bolt {index}", start, end, 0.035, material, uv["teal"], 8))

    for index, y in enumerate((-0.53, 0.52), 1):
        parts.extend((
            common.box(
                f"Lounge side window frame {index}", (0.035, 0.54, 0.74), (2.055, y, 1.38),
                material, uv["dark"], 0.004,
            ),
            common.box(
                f"Lounge warm side pane {index}", (0.025, 0.42, 0.62), (2.080, y, 1.38),
                material, uv["warm"], 0.004,
            ),
            common.box(
                f"Lounge side window vertical muntin {index}", (0.025, 0.035, 0.58),
                (2.097, y, 1.38), material, uv["dark"], 0,
            ),
            common.box(
                f"Lounge side window horizontal muntin {index}", (0.025, 0.38, 0.035),
                (2.097, y, 1.38), material, uv["dark"], 0,
            ),
        ))
    anchors = [supports[0], supports[1], tuple(sign_center)]
    return parts, anchors, "Electric Lounge festoon, warm panes, and lightning-circle pictogram"


def add_schoolhouse(material, uv):
    parts = []
    dome_center = (-0.95, 0.22, 4.00)
    parts.extend((
        common.box("Academy dome roof saddle", (1.28, 1.02, 0.14), (-0.95, 0.22, 3.51), material, uv["dark"], 0.02),
        common.cylinder("Academy orrery dome drum", 0.54, 0.36, (-0.95, 0.22, 3.77), material, uv["dark"], 14),
        sphere("Academy faceted orrery dome", 0.58, dome_center, material, uv["copper"], (1, 1, 0.58), 14, 6),
        common.torus("Academy dome equator", 0.54, 0.04, (-0.95, 0.22, 3.98), material, uv["teal"]),
        beam("Academy dome west bracket", (-1.59, 0.22, 3.43), (-1.46, 0.22, 3.73), 0.05, material, uv["copper"], 8),
        beam("Academy dome east bracket", (-0.31, 0.22, 3.43), (-0.44, 0.22, 3.73), 0.05, material, uv["copper"], 8),
        common.torus("Academy corona toroid", 0.23, 0.035, (-0.95, 0.22, 4.39), material, uv["teal"]),
        beam("Academy corona spoke west", (-0.95, 0.22, 4.38), (-1.15, 0.22, 4.38), 0.025, material, uv["copper"], 6),
        beam("Academy corona spoke east", (-0.95, 0.22, 4.38), (-0.75, 0.22, 4.38), 0.025, material, uv["copper"], 6),
        beam("Academy corona spoke north", (-0.95, 0.22, 4.38), (-0.95, 0.42, 4.38), 0.025, material, uv["copper"], 6),
        beam("Academy corona spoke south", (-0.95, 0.22, 4.38), (-0.95, 0.02, 4.38), 0.025, material, uv["copper"], 6),
        common.cylinder("Academy lightning rod", 0.045, 1.20, (-0.95, 0.22, 4.88), material, uv["copper"], 8),
        common.cylinder("Academy lightning point", 0.018, 0.28, (-0.95, 0.22, 5.46), material, uv["teal"], 6),
    ))
    insulator(parts, "Academy west", -1.60, -0.42, 3.98, material, uv)
    insulator(parts, "Academy east", -0.30, -0.42, 3.98, material, uv)
    parts.extend((
        beam("Academy roof wire west", (-1.60, -0.42, 4.45), (-1.15, 0.12, 4.39), 0.035, material, uv["dark"]),
        beam("Academy roof wire east", (-0.30, -0.42, 4.45), (-0.75, 0.12, 4.39), 0.035, material, uv["dark"]),
    ))

    orrery_center = (-0.44, -1.60, 2.68)
    parts.extend((
        common.box("Academy upper-window recess", (0.92, 0.04, 0.88), (-0.44, -1.55, 2.68), material, uv["dark"], 0.004),
        common.cylinder(
            "Academy upper-window orrery backplate", 0.31, 0.06, (-0.44, -1.57, 2.68),
            material, uv["dark"], 12, rotation=(math.pi / 2, 0, 0),
        ),
        common.torus("Academy upper-window orrery outer", 0.39, 0.035, orrery_center, material, uv["copper"], rotation=(math.pi / 2, 0, 0)),
        common.torus("Academy upper-window orrery inner", 0.25, 0.03, orrery_center, material, uv["teal"], rotation=(math.pi / 2, 0, 0)),
        sphere("Academy upper-window orrery sun", 0.09, orrery_center, material, uv["warm"], segments=8, rings=4),
        beam("Academy orrery axle", (-0.83, -1.60, 2.68), (-0.05, -1.60, 2.68), 0.025, material, uv["dark"]),
    ))
    anchors = [(-0.95, 0.22, 5.60), (-1.60, -0.42, 4.48), (-0.30, -0.42, 4.48)]
    return parts, anchors, "Academy observatory dome, lightning rod, roof insulators, and upper-window orrery"


def add_stamp_mill(material, uv):
    parts = []
    parts.extend((
        common.cylinder("Mill electric motor housing", 0.40, 1.62, (1.38, -0.34, 2.12), material, uv["copper"], 14, rotation=(0, math.pi / 2, 0)),
        common.cylinder("Mill motor iron end", 0.44, 0.12, (0.62, -0.34, 2.12), material, uv["dark"], 14, rotation=(0, math.pi / 2, 0)),
        common.cylinder("Mill motor teal end", 0.44, 0.12, (2.14, -0.34, 2.12), material, uv["teal"], 14, rotation=(0, math.pi / 2, 0)),
        common.cylinder("Mill motor copper band", 0.43, 0.12, (1.38, -0.34, 2.12), material, uv["dark"], 14, rotation=(0, math.pi / 2, 0)),
        beam("Mill motor conduit riser", (0.65, -0.34, 2.36), (0.65, -0.34, 3.65), 0.075, material, uv["copper"], 8),
        beam("Mill motor conduit roof", (0.65, -0.34, 3.65), (0.12, -0.34, 4.08), 0.075, material, uv["copper"], 8),
    ))
    post_x = (-1.45, 0.0, 1.45)
    for index, x in enumerate(post_x, 1):
        insulator(parts, f"Mill bus post {index}", x, -0.28, 3.76, material, uv)
        parts.extend((
            common.cylinder(
                f"Mill bus post {index} upper pin", 0.065, 0.20, (x, -0.28, 4.30),
                material, uv["dark"], 8,
            ),
            common.cylinder(
                f"Mill bus post {index} upper ceramic", 0.20, 0.085, (x, -0.28, 4.29),
                material, uv["warm"], 10,
            ),
            common.cylinder(
                f"Mill bus post {index} bus cap", 0.09, 0.08, (x, -0.28, 4.39),
                material, uv["copper"], 8,
            ),
        ))
    parts.extend((
        beam("Mill iron roof crossarm", (-1.70, -0.28, 4.20), (1.70, -0.28, 4.20), 0.10, material, uv["dark"], 8),
        beam("Mill copper roof bus", (-1.70, -0.28, 4.39), (1.70, -0.28, 4.39), 0.085, material, uv["copper"], 8),
        beam("Mill bus west roof brace", (-1.78, -0.28, 3.54), (-1.45, -0.28, 4.20), 0.06, material, uv["dark"], 8),
        beam("Mill bus east roof brace", (1.78, -0.28, 3.54), (1.45, -0.28, 4.20), 0.06, material, uv["dark"], 8),
        common.torus(
            "Mill voltage toroid", 0.12, 0.035, (0, -0.28, 4.39), material, uv["teal"],
            rotation=(0, math.pi / 2, 0),
        ),
        common.cylinder(
            "Mill motor winding backplate", 0.34, 0.08, (1.38, -0.69, 2.12), material, uv["dark"], 12,
            rotation=(math.pi / 2, 0, 0),
        ),
        common.torus(
            "Mill motor winding tell", 0.25, 0.025, (1.38, -0.755, 2.12), material, uv["teal"],
            rotation=(math.pi / 2, 0, 0),
        ),
        common.cylinder(
            "Mill motor winding hub", 0.08, 0.10, (1.38, -0.73, 2.12), material, uv["copper"], 10,
            rotation=(math.pi / 2, 0, 0),
        ),
    ))
    anchors = [(x, -0.28, 4.54) for x in post_x]
    return parts, anchors, "electrified motor housing, conduit riser, and three-insulator roof bus"


BUILDERS = {"tavern": add_tavern, "schoolhouse": add_schoolhouse, "stamp_mill": add_stamp_mill}


def add_anchors(locations, parent):
    anchors = []
    for index, location in enumerate(locations, 1):
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=location)
        anchor = bpy.context.object
        anchor.name = f"arc_anchor_{index}"
        anchor.empty_display_size = 0.12
        anchor.parent = parent
        anchors.append(anchor)
    return anchors


def build_variant(key, spec):
    directory = ROOT / "assets/pilots" / spec["directory"]
    source_blend = directory / f'{spec["source"]}.blend'
    source_glb = directory / f'{spec["source"]}.glb'
    target_blend = directory / f'{spec["stem"]}.e3.blend'
    target_glb = directory / f'{spec["stem"]}.e3.glb'
    assert sha256(source_blend) == spec["blend_sha"], f"{key} source BLEND changed"
    assert sha256(source_glb) == spec["glb_sha"], f"{key} source GLB changed"

    bpy.ops.wm.open_mainfile(filepath=str(source_blend))
    model = bpy.data.objects[spec["object"]]
    source_dimensions = tuple(model.dimensions)
    for obj in list(bpy.data.objects):
        if obj.type == "EMPTY" and obj.name.startswith("steam_anchor_"):
            bpy.data.objects.remove(obj, do_unlink=True)
    material = model.data.materials[0]
    parts, anchor_locations, identity_edit = BUILDERS[key](material, spec["uv"])
    for part in parts:
        part.modifiers.clear()
    common.apply_and_uv(parts)

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
    model["epoch_variant"] = "E3 Voltage Age"
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
    print(json.dumps([build_variant(key, spec) for key, spec in SPECS.items()], indent=2))


if __name__ == "__main__":
    main()
