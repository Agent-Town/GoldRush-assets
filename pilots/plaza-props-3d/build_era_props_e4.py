from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

import bpy


ROOT = Path(__file__).resolve().parent
ATLAS = ROOT / "era-props-e4-atlas.png"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


e3 = load_module("era_props_e3_build", ROOT / "build_era_props_e3.py")
common = e3.common
common.ATLAS = ATLAS
town = load_module("town_plate_e4_road", ROOT.parent / "town-plate-3d" / "build_town_plate.py")

SOURCE_HASHES = {
    "covered_wagon.e3": {
        "blend": "767e45ec4acefdd069003e64114ddb0633774780d3843fd394b677567d2b1419",
        "glb": "e7e7b0cd6d851e273adec71625edaf1b47629b663274596562389f8b81f9570e",
    },
    "water_trough.e3": {
        "blend": "076bb171f70d2cd158055d421ef1d76d67204c3adc541cbef8064a202c8f1b85",
        "glb": "866920e7f82b15891a93ff585a1f9a70b72e121eaa10ca16f688ed30006126e5",
    },
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_variant(stem, object_name):
    blend, glb = ROOT / f"{stem}.blend", ROOT / f"{stem}.glb"
    assert sha256(blend) == SOURCE_HASHES[stem]["blend"]
    assert sha256(glb) == SOURCE_HASHES[stem]["glb"]
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    for obj in list(bpy.data.objects):
        if obj.type == "EMPTY" and obj.name.startswith(("steam_anchor_", "arc_anchor_")):
            bpy.data.objects.remove(obj, do_unlink=True)
    model = bpy.data.objects[object_name]
    model["preserve_uv"] = True
    return model, model.data.materials[0], tuple(model.dimensions)


def add_exhaust_anchors(locations, parent):
    anchors = []
    for index, location in enumerate(locations, 1):
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=location)
        anchor = bpy.context.object
        anchor.name = f"exhaust_anchor_{index}"
        anchor.empty_display_size = 0.08
        anchor.parent = parent
        anchors.append(anchor)
    return anchors


e3.add_arc_anchors = add_exhaust_anchors


def soot_relic(model, predicate):
    uv_layer = model.data.uv_layers.active
    soot_uv = ((9 % common.COLUMNS + 0.5) / common.COLUMNS,
               (9 // common.COLUMNS + 0.5) / common.COLUMNS)
    for polygon in model.data.polygons:
        points = [model.data.vertices[index].co for index in polygon.vertices]
        minimum = tuple(min(point[axis] for point in points) for axis in range(3))
        maximum = tuple(max(point[axis] for point in points) for axis in range(3))
        if predicate(minimum, maximum):
            for loop_index in polygon.loop_indices:
                uv_layer.data[loop_index].uv = soot_uv


def relic_slash(name, center, angle, material):
    x, y, z = center
    along = (math.cos(angle) * 0.21, math.sin(angle) * 0.21)
    across = (-math.sin(angle) * 0.035, math.cos(angle) * 0.035)
    vertices = [
        (x - along[0] - across[0], y, z - along[1] - across[1]),
        (x + along[0] - across[0], y, z + along[1] - across[1]),
        (x + along[0] + across[0], y, z + along[1] + across[1]),
        (x - along[0] + across[0], y, z - along[1] + across[1]),
    ]
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return common.tag(obj, material, 9, 0)


def finish(name, stem, parts, material, anchors, shared, triangle_limit, dimensions=None):
    parts[0]["epoch_variant"] = "E4 Motor Age"
    parts[0]["exhaust_style"] = "light dust puff; never black smoke"
    for part in parts[1:]:
        part.modifiers.clear()
    return e3.finish(
        name, stem, parts, material, anchors=anchors, shared=shared,
        triangle_limit=triangle_limit, expected_dimensions=dimensions,
    )


def build_wagon():
    model, material, dimensions = source_variant("covered_wagon.e3", "CoveredWagonE3")
    soot_relic(
        model,
        lambda low, high: (
            low[2] > 0.88 and low[1] > 0.18 and low[0] > -0.16 and high[0] < 0.16
        ) or (
            low[2] > 1.23 and low[1] > 0.25 and low[0] > -0.36 and high[0] < 0.36
        ),
    )
    bpy.ops.mesh.primitive_plane_add(
        size=1, location=(0.43, -0.405, 1.15), rotation=(math.pi / 2, 0, 0),
    )
    cab_window = bpy.context.object
    cab_window.name = "Motor caravan teal cab window"
    cab_window.scale = (0.22, 0.18, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    common.tag(cab_window, material, 10, 0)
    bpy.ops.mesh.primitive_plane_add(
        size=1, location=(0.84, -0.411, 0.83), rotation=(math.pi / 2, 0, 0),
    )
    headlamp = bpy.context.object
    headlamp.name = "Motor caravan amber headlamp"
    headlamp.scale = (0.10, 0.10, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    common.tag(headlamp, material, 15, 0)
    parts = [
        model,
        common.cylinder(
            "Motor caravan wedge engine bonnet", 0.17, 0.50, (0.72, -0.23, 0.80),
            material, 6, 3, rotation=(math.pi / 2, 0, 0),
        ),
        common.cylinder(
            "Motor caravan light-dust exhaust", 0.04, 0.58, (0.72, -0.41, 1.14),
            material, 12, 3,
        ),
        cab_window,
        headlamp,
    ]
    return finish(
        "CoveredWagonE4", "covered_wagon.e4", parts, material,
        [(0.72, -0.41, 1.438)], False, 1800, dimensions,
    )


def build_trough():
    model, material, dimensions = source_variant("water_trough.e3", "WaterTroughE3")
    soot_relic(
        model,
        lambda low, high: (
            low[0] > 0.25 and high[0] < 0.71 and low[1] > -0.06 and high[1] < 0.37
            and low[2] > 0.20 and high[2] < 0.53
        ),
    )
    parts = [
        model,
        common.cylinder(
            "Capped relic electric-pump outlet", 0.18, 0.08, (0.70, 0.20, 0.36),
            material, 12, 8, rotation=(0, math.pi / 2, 0),
        ),
        common.box(
            "Boarded trough pump relic slash A", (0.42, 0.05, 0.016), (0.48, 0.16, 0.642),
            material, 9, 0, rotation=(0, 0, 0.58),
        ),
        common.box(
            "Boarded trough pump relic slash B", (0.42, 0.05, 0.016), (0.48, 0.16, 0.642),
            material, 9, 0, rotation=(0, 0, -0.58),
        ),
    ]
    return finish(
        "WaterTroughE4", "water_trough.e4", parts, material,
        [], False, 1200, dimensions,
    )


def accessory_material():
    material = common.material_from_atlas()
    material.name = "E4EraPropsSharedMaterial"
    return material


def build_fuel_rack():
    common.reset(); material = accessory_material()
    parts = [
        common.box("Fuel rack stone foot", (1.52, 0.82, 0.14), (0, 0, 0.07), material, 13),
        common.box("Fuel rack back", (1.42, 0.10, 1.10), (0, 0.32, 0.62), material, 2),
        common.box("Fuel rack west brace", (0.10, 0.70, 1.10), (-0.66, 0, 0.62), material, 4),
        common.box("Fuel rack east brace", (0.10, 0.70, 1.10), (0.66, 0, 0.62), material, 4),
    ]
    for index, x in enumerate((-0.43, 0, 0.43), 1):
        parts.extend((
            common.cylinder(f"Fuel rack drum {index}", 0.20, 0.78, (x, 0, 0.51), material, 7, 10),
            common.cylinder(f"Fuel rack rubber band low {index}", 0.215, 0.06, (x, 0, 0.30), material, 12, 10),
            common.cylinder(f"Fuel rack rubber band high {index}", 0.215, 0.06, (x, 0, 0.72), material, 12, 10),
        ))
    parts.append(common.cylinder("Fuel rack vent cap", 0.09, 0.22, (0, 0.32, 1.22), material, 6, 8))
    return finish("FuelRackE4", "fuel-rack.e4", parts, material, [(0, 0.32, 1.36)], True, 1000)


def build_road_marker():
    common.reset(); material = accessory_material()
    parts = [
        common.cylinder("Road marker footing", 0.34, 0.18, (0, 0, 0.09), material, 13, 12),
        common.box("Road marker brass post", (0.14, 0.14, 2.58), (0, 0, 1.38), material, 6),
        common.box("Road marker upper amber arrow", (1.48, 0.12, 0.38), (0.38, 0, 2.24), material, 7),
        common.box("Road marker lower brass arrow", (1.24, 0.12, 0.34), (-0.30, 0, 1.70), material, 15),
        common.torus("Road marker rubber wheel", 0.30, 0.05, (0, -0.10, 1.02), material, 12, rotation=(math.pi / 2, 0, 0)),
        common.cylinder("Road marker wheel hub", 0.10, 0.10, (0, -0.12, 1.02), material, 6, 8, rotation=(math.pi / 2, 0, 0)),
        common.cylinder("Road marker dust beacon", 0.09, 0.34, (0, 0, 2.82), material, 7, 8),
    ]
    return finish("RoadMarkerE4", "road-marker.e4", parts, material, [(0, 0, 3.03)], True, 1000)


def build_filling_shed():
    common.reset(); material = accessory_material()
    parts = [
        common.box("Filling shed stone foot", (2.42, 1.52, 0.14), (0, 0, 0.07), material, 13),
        common.box("Filling shed rear wall", (2.28, 0.12, 1.52), (0, 0.58, 0.84), material, 2),
        common.box("Filling shed amber canopy", (2.68, 1.82, 0.18), (0, 0, 1.68), material, 7),
        common.box("Filling shed west brass post", (0.13, 0.13, 1.56), (-1.06, -0.68, 0.84), material, 6),
        common.box("Filling shed east brass post", (0.13, 0.13, 1.56), (1.06, -0.68, 0.84), material, 6),
        common.cylinder("Filling shed fuel tank", 0.32, 1.64, (0, 0.40, 0.86), material, 7, 12, rotation=(0, math.pi / 2, 0)),
        common.box("Filling shed west pump", (0.40, 0.36, 1.00), (-0.64, -0.50, 0.57), material, 15),
        common.box("Filling shed east pump", (0.40, 0.36, 1.00), (0.64, -0.50, 0.57), material, 15),
        common.box("Filling shed west road-sign mast", (0.12, 0.12, 1.14), (-0.72, 0.18, 2.24), material, 6),
        common.box("Filling shed east road-sign mast", (0.12, 0.12, 1.14), (0.72, 0.18, 2.24), material, 6),
        common.box("Filling shed amber road board", (2.12, 0.12, 0.46), (0, 0.16, 2.62), material, 7),
        common.torus("Filling shed road-wheel pictogram", 0.26, 0.05, (0, 0.08, 2.62), material, 9, rotation=(math.pi / 2, 0, 0)),
        common.cylinder("Filling shed road-wheel hub", 0.09, 0.10, (0, 0.06, 2.62), material, 6, 8, rotation=(math.pi / 2, 0, 0)),
        common.torus("Filling shed road crest", 0.26, 0.05, (0, -0.86, 1.34), material, 12, rotation=(math.pi / 2, 0, 0)),
        common.box("Filling shed road crest tether", (0.08, 0.08, 0.26), (0, -0.86, 1.58), material, 6, 0),
        common.cylinder("Filling shed exhaust", 0.08, 0.72, (0.92, 0.50, 1.78), material, 4, 8),
        common.cylinder("Filling shed dust cap", 0.12, 0.09, (0.92, 0.50, 2.16), material, 14, 8),
    ]
    return finish(
        "FillingShedE4", "filling-shed.e4", parts, material,
        [(0.92, 0.50, 2.26), (-0.64, -0.50, 1.12), (0.64, -0.50, 1.12)], True, 1000,
    )


def road_segment(name, start, end, width, height, material, palette_index):
    dx, dy = end.x - start.x, end.y - start.y
    length = math.hypot(dx, dy)
    nx, ny = -dy / length * width * 0.5, dx / length * width * 0.5
    points = (
        (start.x + nx, start.y + ny), (end.x + nx, end.y + ny),
        (end.x - nx, end.y - ny), (start.x - nx, start.y - ny),
    )
    vertices = [(x, y, town.terrain_height(x, y) + height) for x, y in points]
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return common.tag(obj, material, palette_index, 0)


def build_motor_roadway():
    common.reset(); material = accessory_material()
    parts = []
    for route_id, points in town.RADIAL_ROUTES.items():
        if route_id != "gate":
            continue
        for index, (start, end) in enumerate(zip(points, points[1:])):
            start_radius = math.hypot(start.x, start.y)
            end_radius = math.hypot(end.x, end.y)
            if end_radius <= 7.00:
                continue
            if start_radius < 7.00:
                low, high = 0.0, 1.0
                for _ in range(24):
                    amount = (low + high) * 0.5
                    candidate = town.Point(
                        start.x + (end.x - start.x) * amount,
                        start.y + (end.y - start.y) * amount,
                    )
                    if math.hypot(candidate.x, candidate.y) < 7.00:
                        low = amount
                    else:
                        high = amount
                start = town.Point(
                    start.x + (end.x - start.x) * high,
                    start.y + (end.y - start.y) * high,
                )
            dx, dy = end.x - start.x, end.y - start.y
            length = math.hypot(dx, dy)
            lane_nx, lane_ny = -dy / length * 1.20, dx / length * 1.20
            rut_nx, rut_ny = -dy / length * 0.23, dx / length * 0.23
            for lane, lane_sign in (("west", -1), ("east", 1)):
                lane_start = town.Point(start.x + lane_nx * lane_sign, start.y + lane_ny * lane_sign)
                lane_end = town.Point(end.x + lane_nx * lane_sign, end.y + lane_ny * lane_sign)
                parts.append(road_segment(
                    f"Motor road {route_id} {lane} lane {index}",
                    lane_start, lane_end, 0.86, 0.018, material, 14,
                ))
                for rut, rut_sign in (("left", -1), ("right", 1)):
                    parts.append(road_segment(
                        f"Motor road {route_id} {lane} {rut} wheel rut {index}",
                        town.Point(lane_start.x + rut_nx * rut_sign, lane_start.y + rut_ny * rut_sign),
                        town.Point(lane_end.x + rut_nx * rut_sign, lane_end.y + rut_ny * rut_sign),
                        0.055, 0.020, material, 13,
                    ))
    return finish("MotorRoadwayE4", "motor-roadway.e4", parts, material, [], True, 1000)


def main():
    common.write_shared_atlas()
    print(json.dumps([
        build_wagon(), build_trough(), build_fuel_rack(), build_road_marker(), build_filling_shed(),
        build_motor_roadway(),
    ], indent=2))


if __name__ == "__main__":
    main()
