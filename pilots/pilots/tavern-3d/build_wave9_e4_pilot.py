from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


e3 = load_module("wave8_e3_build", HERE / "build_wave8_e3_pilot.py")
common = e3.common


SPECS = {
    "tavern": {
        "directory": "tavern-3d",
        "stem": "tavern",
        "source": "tavern.e3",
        "object": "TownTavernE3",
        "output": "TownTavernE4",
        "blend_sha": "8b40932949f2cac9634ae6d0bf669734aaf72257459edd34e85e81d5d8c98c1c",
        "glb_sha": "1d3d60500c2f5d5915e03b6ed7e645ab57efc1a7de9f8e14229babb3cb7f1202",
        "uv": e3.SPECS["tavern"]["uv"],
    },
    "schoolhouse": {
        "directory": "schoolhouse-3d",
        "stem": "schoolhouse",
        "source": "schoolhouse.e3",
        "object": "SchoolhouseE3",
        "output": "SchoolhouseE4",
        "blend_sha": "838d3146143820e6f1f813f194c27c6cb5886d1616a0dbf69cbeeeacd0a652ac",
        "glb_sha": "8a977ea418b138990e1f7adb6e51eff76f569119b5104c2a20b39073d40bcd10",
        "uv": e3.SPECS["schoolhouse"]["uv"],
    },
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def beam(name, start, end, radius, material, uv_bounds, vertices=8):
    start, end = Vector(start), Vector(end)
    delta = end - start
    obj = common.cylinder(
        name, radius, delta.length, (start + end) * 0.5, material, uv_bounds, vertices,
    )
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def tyre_silhouette(name, radius, location, material, uv_bounds, segments=8):
    # A flat octagon reads as a wheel from both three-quarter sides without spending
    # the triangles that the Tavern's near-full E3 budget cannot afford.
    vertices = [
        (radius * math.cos(index * math.tau / segments), 0, radius * math.sin(index * math.tau / segments))
        for index in range(segments)
    ]
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], [tuple(range(segments))])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    return common.tag(obj, material, uv_bounds, 0)


def add_tavern(material, uv):
    # Six un-bevelled cuboids plus two flat octagonal tyres keep the 14,900-triangle
    # E3 source under its 15k cap while avoiding square-wheel "teeth" from the rear.
    parts = [
        common.box(
            "Motor Inn porte cochere roof",
            (2.80, 0.92, 0.18), (0, 1.20, 2.25), material, uv["dark"], 0,
        ),
        common.box(
            "Motor Inn iron road fascia",
            (2.80, 0.12, 0.28), (0, 1.61, 2.10), material, uv["dark"], 0,
        ),
        common.box(
            "Motor Inn west drive post",
            (0.14, 0.14, 2.00), (-1.25, 1.60, 1.10), material, uv["copper"], 0,
        ),
        common.box(
            "Motor Inn east drive post",
            (0.14, 0.14, 2.00), (1.25, 1.60, 1.10), material, uv["copper"], 0,
        ),
        common.box(
            "Motor Inn parked runabout body",
            (0.96, 0.04, 0.18), (0.20, 1.65, 2.10), material, uv["copper"], 0,
        ),
        common.box(
            "Motor Inn parked runabout cab",
            (0.38, 0.04, 0.16), (0.38, 1.65, 2.27), material, uv["copper"], 0,
        ),
        tyre_silhouette(
            "Motor Inn parked runabout west tyre",
            0.09, (-0.08, 1.67, 1.97), material, uv["dark"],
        ),
        tyre_silhouette(
            "Motor Inn parked runabout east tyre",
            0.09, (0.52, 1.67, 1.97), material, uv["dark"],
        ),
    ]
    anchors = [(0.96, 1.62, 0.66), (1.02, 0.71, 3.96), (1.77, 1.325, 3.69)]
    identity = (
        "Motor Inn porte-cochere, parked brass runabout silhouette, rubber-dark tyres, "
        "iron road fascia, and retained E3 festoon lights"
    )
    return parts, anchors, identity


def add_schoolhouse(material, uv):
    parts = [
        common.box(
            "Polytechnic drafting hall wing",
            (0.28, 1.48, 1.86), (-1.83, 0.55, 1.25), material, uv["warm"], 0.015,
        ),
        common.box(
            "Polytechnic drafting hall roof",
            (0.32, 1.62, 0.16), (-1.80, 0.55, 2.24), material, uv["dark"], 0.012,
        ),
        common.box(
            "Polytechnic wide window recess",
            (0.025, 1.24, 0.68), (-1.95, 0.55, 1.62), material, uv["dark"], 0.003,
        ),
        common.box(
            "Polytechnic wide teal glazing",
            (0.008, 1.12, 0.52), (-1.968, 0.55, 1.62), material, uv["teal"], 0,
        ),
        common.box(
            "Polytechnic wide window left muntin",
            (0.006, 0.045, 0.52), (-1.975, 0.18, 1.62), material, uv["copper"], 0,
        ),
        common.box(
            "Polytechnic wide window right muntin",
            (0.006, 0.045, 0.52), (-1.975, 0.92, 1.62), material, uv["copper"], 0,
        ),
        common.box(
            "Polytechnic wide window transom",
            (0.006, 1.12, 0.045), (-1.975, 0.55, 1.62), material, uv["copper"], 0,
        ),
        common.cylinder(
            "Polytechnic drafting exhaust",
            0.095, 0.82, (-1.78, 1.23, 2.51), material, uv["dark"], 8,
        ),
        common.cylinder(
            "Polytechnic drafting exhaust brass collar",
            0.14, 0.10, (-1.78, 1.23, 2.86), material, uv["copper"], 8,
        ),
        common.cylinder(
            "Polytechnic drafting exhaust rain cap",
            0.18, 0.10, (-1.78, 1.23, 2.95), material, uv["teal"], 8,
        ),
        common.cylinder(
            "Polytechnic wind gauge roof foot",
            0.20, 0.18, (-0.88, 0.52, 3.10), material, uv["copper"], 10,
        ),
        common.cylinder(
            "Polytechnic wind gauge mast",
            0.085, 1.78, (-0.88, 0.52, 3.92), material, uv["dark"], 8,
        ),
        beam(
            "Polytechnic wind gauge crossarm",
            (-1.32, 0.52, 4.73), (-0.44, 0.52, 4.73), 0.05, material, uv["copper"], 8,
        ),
        common.torus(
            "Polytechnic wind gauge bearing",
            0.15, 0.032, (-0.88, 0.52, 4.73), material, uv["teal"],
        ),
        common.cylinder(
            "Polytechnic wind gauge west cup",
            0.10, 0.13, (-1.32, 0.52, 4.73), material, uv["dark"], 8,
            rotation=(math.pi / 2, 0, 0),
        ),
        common.cylinder(
            "Polytechnic wind gauge east cup",
            0.10, 0.13, (-0.44, 0.52, 4.73), material, uv["dark"], 8,
            rotation=(math.pi / 2, 0, 0),
        ),
        beam(
            "Polytechnic wind direction boom",
            (-0.88, 0.05, 4.88), (-0.88, 0.99, 4.88), 0.035, material, uv["copper"], 6,
        ),
        common.box(
            "Polytechnic wind direction tail",
            (0.22, 0.07, 0.20), (-0.88, 0.94, 4.88), material, uv["teal"], 0,
            rotation=(0, math.pi / 4, 0),
        ),
        beam(
            "Polytechnic wind gauge west roof brace",
            (-0.88, 0.52, 3.20), (-1.22, 0.52, 2.88), 0.055, material, uv["copper"], 8,
        ),
        beam(
            "Polytechnic wind gauge east roof brace",
            (-0.88, 0.52, 3.20), (-0.54, 0.52, 2.88), 0.055, material, uv["copper"], 8,
        ),
        common.torus(
            "Polytechnic rubber drafting wheel",
            0.23, 0.04, (-1.94, 0.55, 0.70), material, uv["dark"],
            rotation=(0, math.pi / 2, 0),
        ),
        common.cylinder(
            "Polytechnic brass drafting wheel hub",
            0.085, 0.07, (-1.935, 0.55, 0.70), material, uv["copper"], 10,
            rotation=(0, math.pi / 2, 0),
        ),
        beam(
            "Polytechnic drafting wheel drive",
            (-1.94, 0.55, 0.92), (-1.94, 0.55, 1.28), 0.035, material, uv["copper"], 6,
        ),
    ]
    anchors = [(-1.78, 1.23, 3.04), (1.58, 1.33, 5.30)]
    identity = (
        "Polytechnic drafting-hall wing with across-the-plaza wide glazing, roof wind gauge, "
        "rubber-dark motor trim, brass carryovers, and retained E3 orrery infrastructure"
    )
    return parts, anchors, identity


BUILDERS = {"tavern": add_tavern, "schoolhouse": add_schoolhouse}


def add_anchors(locations, parent):
    anchors = []
    for index, location in enumerate(locations, 1):
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=location)
        anchor = bpy.context.object
        anchor.name = f"exhaust_anchor_{index}"
        anchor.empty_display_size = 0.12
        anchor.parent = parent
        anchors.append(anchor)
    return anchors


def build_variant(key, spec):
    directory = ROOT / "assets/pilots" / spec["directory"]
    source_blend = directory / f'{spec["source"]}.blend'
    source_glb = directory / f'{spec["source"]}.glb'
    target_blend = directory / f'{spec["stem"]}.e4.blend'
    target_glb = directory / f'{spec["stem"]}.e4.glb'
    assert sha256(source_blend) == spec["blend_sha"], f"{key} E3 BLEND changed"
    assert sha256(source_glb) == spec["glb_sha"], f"{key} E3 GLB changed"

    bpy.ops.wm.open_mainfile(filepath=str(source_blend))
    model = bpy.data.objects[spec["object"]]
    source_dimensions = tuple(model.dimensions)
    for obj in list(bpy.data.objects):
        if obj.type == "EMPTY" and (
            obj.name.startswith("arc_anchor_") or obj.name.startswith("steam_anchor_")
        ):
            bpy.data.objects.remove(obj, do_unlink=True)

    material = model.data.materials[0]
    parts, anchor_locations, identity_edit = BUILDERS[key](material, spec["uv"])
    if key == "tavern":
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
    model["epoch_variant"] = "E4 Motor Age"
    model["identity_edit"] = identity_edit
    model["exhaust_style"] = "light dust puff; never black smoke"
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
    assert triangles <= 15_000, (key, triangles)
    return {
        "id": key,
        "blend": str(target_blend.relative_to(ROOT)),
        "glb": str(target_glb.relative_to(ROOT)),
        "sha256": sha256(target_glb),
        "triangles": triangles,
        "dimensions": list(model.dimensions),
        "anchors": [anchor.name for anchor in anchors],
        "identityEdit": identity_edit,
    }


def main():
    print(json.dumps([build_variant(key, spec) for key, spec in SPECS.items()], indent=2))


if __name__ == "__main__":
    main()
