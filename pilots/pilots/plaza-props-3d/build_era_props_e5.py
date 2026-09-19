from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent
ATLAS = ROOT / "era-props-e5-atlas.png"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


common = load_module("era_props_e5_common", ROOT / "build_era_props_e2.py")
common.ATLAS = ATLAS
common.PALETTE = (
    (0.035, 0.030, 0.025), (0.075, 0.060, 0.045), (0.15, 0.115, 0.075), (0.28, 0.20, 0.11),
    (0.055, 0.085, 0.080), (0.075, 0.18, 0.18), (0.12, 0.32, 0.32), (0.28, 0.48, 0.45),
    (0.14, 0.09, 0.045), (0.30, 0.19, 0.075), (0.52, 0.36, 0.15), (0.70, 0.54, 0.28),
    (0.055, 0.050, 0.045), (0.20, 0.18, 0.14), (0.44, 0.38, 0.27), (0.68, 0.60, 0.43),
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def beam(name, start, end, radius, material, palette, vertices=6):
    start, end = Vector(start), Vector(end)
    delta = end - start
    obj = common.cylinder(name, radius, delta.length, (start + end) * 0.5, material, palette, vertices)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def material():
    result = common.material_from_atlas()
    result.name = "E5HarborPropsSharedMaterial"
    return result


def finish(name, stem, parts, shared, triangle_limit):
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
    model["epoch_variant"] = "E5 Deepwater Harbor Rebuild"
    model["flood_break"] = "fresh harbor fixture; no E1-E4 geometry imported"
    triangles = sum(len(polygon.vertices) - 2 for polygon in model.data.polygons)
    assert triangles <= triangle_limit, (name, triangles, triangle_limit)
    blend, glb = ROOT / f"{stem}.blend", ROOT / f"{stem}.glb"
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.object.select_all(action="DESELECT")
    model.select_set(True)
    bpy.context.view_layer.objects.active = model
    bpy.ops.export_scene.gltf(
        filepath=str(glb), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT",
    )
    return {
        "id": stem,
        "triangles": triangles,
        "dimensions": list(model.dimensions),
        "sha256": sha256(glb),
        "anchors": [],
    }


def rope_coil(parts, prefix, location, material_, radius=0.22, rotation=(math.pi / 2, 0, 0)):
    parts.extend((
        common.torus(f"{prefix} outer", radius, 0.035, location, material_, 10, rotation=rotation),
        common.torus(f"{prefix} inner", radius * 0.67, 0.030, location, material_, 10, rotation=rotation),
    ))


def lantern(parts, prefix, location, material_, scale=1.0):
    x, y, z = location
    parts.extend((
        common.cylinder(f"{prefix} cap", 0.12 * scale, 0.08 * scale, (x, y, z + 0.16 * scale), material_, 10, 8),
        common.cylinder(f"{prefix} teal glass", 0.085 * scale, 0.25 * scale, (x, y, z), material_, 6, 8),
        common.cylinder(f"{prefix} foot", 0.11 * scale, 0.07 * scale, (x, y, z - 0.16 * scale), material_, 1, 8),
    ))


def build_hauled_dinghy():
    common.reset(); mat = material()
    parts = [
        common.box("Harbor arrival dinghy keel", (1.64, 0.54, 0.12), (0, 0, 0.31), mat, 2),
        common.box("Harbor arrival dinghy port hull", (1.60, 0.12, 0.48), (0, -0.34, 0.52), mat, 3, rotation=(-0.18, 0, 0)),
        common.box("Harbor arrival dinghy starboard hull", (1.60, 0.12, 0.48), (0, 0.34, 0.52), mat, 3, rotation=(0.18, 0, 0)),
        common.box("Harbor arrival dinghy bow", (0.14, 0.74, 0.46), (0.74, 0, 0.53), mat, 1, rotation=(0, 0.16, 0)),
        common.box("Harbor arrival dinghy stern", (0.14, 0.68, 0.42), (-0.74, 0, 0.51), mat, 2),
        common.box("Harbor arrival cradle west", (0.16, 0.92, 0.13), (-0.48, 0, 0.07), mat, 12),
        common.box("Harbor arrival cradle east", (0.16, 0.92, 0.13), (0.48, 0, 0.07), mat, 12),
        common.box("Harbor arrival seabed ballast", (0.48, 0.34, 0.18), (-0.62, 0, 0.09), mat, 12),
        beam("Harbor arrival folded mast", (-0.58, 0.26, 0.75), (0.48, 0.26, 1.28), 0.045, mat, 10, 6),
        common.box("Harbor arrival patched sail", (0.78, 0.05, 0.38), (-0.02, 0.28, 1.01), mat, 14, 0, rotation=(0, -0.12, 0.31)),
        common.box("Harbor arrival sail tar patch", (0.28, 0.055, 0.19), (0.08, 0.30, 1.03), mat, 4, 0, rotation=(0, -0.12, 0.31)),
    ]
    rope_coil(parts, "Harbor arrival waterlogged hawser", (-0.42, -0.39, 0.72), mat, 0.18)
    parts.append(common.cylinder("Harbor arrival teal buoy", 0.10, 0.34, (0.47, -0.39, 0.74), mat, 6, 8))
    return finish("CoveredWagonE5", "covered_wagon.e5", parts, True, 1800)


def build_freshwater_cistern():
    common.reset(); mat = material()
    parts = [
        common.box("Harbor freshwater cistern foot", (1.58, 0.72, 0.12), (0, 0, 0.06), mat, 12),
        common.cylinder("Harbor freshwater cistern", 0.29, 1.34, (0, 0, 0.36), mat, 3, 12, rotation=(0, math.pi / 2, 0)),
        common.cylinder("Harbor freshwater west rope band", 0.31, 0.08, (-0.44, 0, 0.36), mat, 10, 10, rotation=(0, math.pi / 2, 0)),
        common.cylinder("Harbor freshwater east rope band", 0.31, 0.08, (0.44, 0, 0.36), mat, 10, 10, rotation=(0, math.pi / 2, 0)),
        common.box("Harbor freshwater rain lip", (1.48, 0.70, 0.08), (0, 0, 0.61), mat, 14),
        common.cylinder("Harbor freshwater teal tap", 0.055, 0.32, (0.52, -0.31, 0.39), mat, 6, 8, rotation=(math.pi / 2, 0, 0)),
    ]
    return finish("WaterTroughE5", "water_trough.e5", parts, True, 1200)


def build_harbor_lantern():
    common.reset(); mat = material()
    parts = [
        common.cylinder("Harbor lantern stone foot", 0.27, 0.16, (0, 0, 0.08), mat, 13, 10),
        common.cylinder("Harbor lantern tarred post", 0.075, 2.12, (0, 0, 1.12), mat, 1, 8),
        beam("Harbor lantern rope crossarm", (-0.46, 0, 2.02), (0.46, 0, 2.02), 0.045, mat, 10, 6),
    ]
    lantern(parts, "Harbor lantern west", (-0.38, 0, 1.74), mat, 0.90)
    lantern(parts, "Harbor lantern east", (0.38, 0, 1.74), mat, 0.90)
    return finish("HarborLanternE5", "harbor-lantern.e5", parts, True, 1000)


def build_net_frame():
    common.reset(); mat = material()
    parts = [
        common.box("Net frame seabed ballast", (1.62, 0.42, 0.10), (0, 0, 0.05), mat, 12),
        beam("Net frame west leg", (-0.72, 0, 0.08), (-0.52, 0, 2.08), 0.055, mat, 2, 6),
        beam("Net frame east leg", (0.72, 0, 0.08), (0.52, 0, 2.08), 0.055, mat, 2, 6),
        beam("Net frame header", (-0.58, 0, 2.06), (0.58, 0, 2.06), 0.060, mat, 10, 6),
    ]
    for index, z in enumerate((0.44, 0.78, 1.12, 1.46, 1.80), 1):
        parts.append(beam(f"Patched drying net line {index}", (-0.62, 0, z), (0.62, 0, z + 0.18), 0.018, mat, 5, 4))
    for index, x in enumerate((-0.42, 0, 0.42), 1):
        parts.append(common.cylinder(f"Net cork float {index}", 0.07, 0.13, (x, 0, 1.94), mat, 11, 6))
    return finish("NetFrameE5", "net-frame.e5", parts, True, 1000)


def build_tide_board():
    common.reset(); mat = material()
    parts = [
        common.cylinder("Tide board stone foot", 0.30, 0.16, (0, 0, 0.08), mat, 13, 10),
        common.box("Tide board tarred post", (0.14, 0.14, 2.26), (0, 0, 1.20), mat, 1),
        common.box("Tide board pictogram panel", (1.28, 0.10, 0.86), (0.40, 0, 1.72), mat, 3),
        common.torus("Tide board buoy ring", 0.22, 0.045, (0.40, -0.08, 1.90), mat, 6, rotation=(math.pi / 2, 0, 0)),
    ]
    for index, z in enumerate((1.48, 1.65, 1.82), 1):
        parts.append(common.box(f"Tide board water bar {index}", (0.62 - index * 0.08, 0.04, 0.035), (0.40, -0.09, z), mat, 7, 0))
    return finish("TideBoardE5", "tide-board.e5", parts, True, 1000)


def build_rope_buoy_rack():
    common.reset(); mat = material()
    parts = [
        common.box("Rope buoy rack foot", (1.62, 0.72, 0.12), (0, 0, 0.06), mat, 12),
        beam("Rope buoy rack west post", (-0.64, 0, 0.10), (-0.64, 0, 1.62), 0.055, mat, 2, 6),
        beam("Rope buoy rack east post", (0.64, 0, 0.10), (0.64, 0, 1.62), 0.055, mat, 2, 6),
        beam("Rope buoy rack header", (-0.70, 0, 1.58), (0.70, 0, 1.58), 0.060, mat, 10, 6),
    ]
    for index, x in enumerate((-0.32, 0.32), 1):
        rope_coil(parts, f"Rope buoy rack coil {index}", (x, -0.08, 0.82), mat, 0.18)
        parts.append(common.cylinder(f"Rope buoy rack buoy {index}", 0.08, 0.30, (x, 0.10, 1.30), mat, 6 if index == 1 else 11, 8))
    return finish("RopeBuoyRackE5", "rope-buoy-rack.e5", parts, True, 1000)


def main():
    common.write_shared_atlas()
    print(json.dumps([
        build_hauled_dinghy(), build_freshwater_cistern(), build_harbor_lantern(),
        build_net_frame(), build_tide_board(), build_rope_buoy_rack(),
    ], indent=2))


if __name__ == "__main__":
    main()
