from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent
ATLAS = ROOT / "era-props-e8-atlas.png"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


common = load_module("era_props_e8_common", ROOT / "build_era_props_e2.py")
common.ATLAS = ATLAS
common.PALETTE = (
    (0.035, 0.038, 0.040), (0.075, 0.080, 0.080), (0.15, 0.155, 0.145), (0.29, 0.29, 0.25),
    (0.055, 0.12, 0.12), (0.075, 0.24, 0.24), (0.13, 0.40, 0.39), (0.38, 0.64, 0.59),
    (0.15, 0.085, 0.035), (0.34, 0.20, 0.075), (0.56, 0.39, 0.14), (0.78, 0.62, 0.29),
    (0.13, 0.11, 0.095), (0.32, 0.29, 0.24), (0.60, 0.57, 0.48), (0.84, 0.82, 0.70),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def material() -> bpy.types.Material:
    result = common.material_from_atlas()
    result.name = "E8OrbitalPropsSharedMaterial"
    return result


def beam(name: str, start, end, radius: float, material_, palette: int, vertices: int = 6):
    start, end = Vector(start), Vector(end)
    delta = end - start
    obj = common.cylinder(name, radius, delta.length, (start + end) * 0.5, material_, palette, vertices)
    for modifier in list(obj.modifiers):
        obj.modifiers.remove(modifier)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def finish(name: str, stem: str, parts: list[bpy.types.Object], triangle_limit: int = 1_000) -> dict:
    common.apply_palette_uv(parts, True)
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
    model["epoch_variant"] = "E8 Orbital Dome Commons"
    model["site_reset"] = "fresh orbital fixture; no E5 harbor geometry imported"
    model["signage"] = "pictogram-only; zero readable letters"
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
        "dimensions": [round(value, 6) for value in model.dimensions],
        "sha256": sha256(glb),
    }


def ico(name: str, location, scale, material_, palette: int):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return common.tag(obj, material_, palette, 0)


def build_crater_rim_set() -> dict:
    common.reset()
    mat = material()
    parts = [
        common.cylinder("Crater glass lens", 0.74, 0.055, (0, 0, 0.0275), mat, 5, 12),
        common.torus("Crater scorched lip", 0.82, 0.055, (0, 0, 0.09), mat, 0, segments=(12, 3)),
    ]
    scales = ((0.25, 0.18, 0.18), (0.29, 0.20, 0.21), (0.21, 0.16, 0.15))
    for index, angle in enumerate((-82, -61, -39, -17, 7, 31, 54, 77), 1):
        radians = math.radians(angle)
        sx, sy, sz = scales[index % len(scales)]
        parts.append(ico(
            f"Crater rim boulder {index}",
            (math.cos(radians) * 1.02, math.sin(radians) * 1.02, sz),
            (sx, sy, sz), mat, 12 + index % 3,
        ))
    for side in (-1, 1):
        x = side * 1.18
        parts.extend((
            common.box(f"Crater survey foot {side}", (0.34, 0.28, 0.09), (x, 0.34, 0.045), mat, 13, 0),
            beam(f"Crater survey stake {side}", (x, 0.34, 0.08), (x, 0.34, 0.92), 0.035, mat, 10, 6),
            common.torus(
                f"Crater survey reflector {side}", 0.11, 0.025, (x, 0.31, 0.77), mat, 7,
                rotation=(math.pi / 2, 0, 0), segments=(8, 3),
            ),
        ))
    return finish("CraterRimSetE8", "crater-rim-set.e8", parts)


def build_lander_legs() -> dict:
    common.reset()
    mat = material()
    parts = [
        common.cylinder("Lander leg crown", 0.34, 0.22, (0, 0, 1.42), mat, 10, 12),
        common.torus("Lander leg teal bearing", 0.30, 0.055, (0, 0, 1.29), mat, 6, segments=(12, 4)),
    ]
    for index, angle in enumerate((90, 210, 330), 1):
        radians = math.radians(angle)
        foot = Vector((math.cos(radians) * 1.18, math.sin(radians) * 1.18, 0.06))
        knee = Vector((math.cos(radians) * 0.64, math.sin(radians) * 0.64, 0.70))
        parts.extend((
            beam(f"Lander leg upper {index}", (0, 0, 1.34), knee, 0.075, mat, 14, 8),
            beam(f"Lander leg lower {index}", knee, foot, 0.085, mat, 3, 8),
            common.box(
                f"Lander regolith shoe {index}", (0.52, 0.40, 0.12), tuple(foot), mat, 13, 0,
                rotation=(0, 0, radians),
            ),
            common.torus(
                f"Lander knee collar {index}", 0.13, 0.035, tuple(knee), mat, 6,
                rotation=(math.pi / 2, 0, radians), segments=(8, 3),
            ),
        ))
    parts.extend((
        beam("Lander service drop", (0.12, 0, 1.35), (0.12, 0, 0.66), 0.035, mat, 9, 6),
        common.cylinder("Lander service cap", 0.075, 0.10, (0.12, 0, 0.62), mat, 7, 8),
    ))
    return finish("LanderLegsE8", "lander-legs.e8", parts)


def flag_icon(parts: list[bpy.types.Object], era: int, x: float, mat) -> None:
    front = -0.046
    z = 1.62
    accent = 11 if era in (1, 4, 6) else 7
    if era == 1:  # pan + handle
        parts.append(common.torus(f"E{era} pan crest", 0.085, 0.018, (x, front, z), mat, accent,
                                  rotation=(math.pi / 2, 0, 0), segments=(8, 4)))
        parts.append(beam(f"E{era} pan handle", (x + 0.06, front, z + 0.05), (x + 0.15, front, z + 0.14), 0.014, mat, accent, 4))
    elif era == 2:  # steam stack
        parts.extend((
            common.box(f"E{era} stack crest", (0.09, 0.025, 0.19), (x, front, z), mat, accent, 0),
            common.box(f"E{era} stack cap", (0.16, 0.028, 0.04), (x, front, z + 0.105), mat, accent, 0),
        ))
    elif era == 3:  # voltage bolt
        for index, (a, b) in enumerate((((x - 0.07, front, z + 0.11), (x + 0.02, front, z + 0.02)),
                                         ((x + 0.02, front, z + 0.02), (x - 0.02, front, z - 0.03)),
                                         ((x - 0.02, front, z - 0.03), (x + 0.08, front, z - 0.13))), 1):
            parts.append(beam(f"E{era} bolt crest {index}", a, b, 0.018, mat, accent, 4))
    elif era == 4:  # wheel
        parts.append(common.torus(f"E{era} wheel crest", 0.105, 0.018, (x, front, z), mat, accent,
                                  rotation=(math.pi / 2, 0, 0), segments=(10, 4)))
        for spoke_index, angle in enumerate((0, math.pi / 2), 1):
            parts.append(beam(f"E{era} wheel spoke {spoke_index}",
                              (x - math.cos(angle) * 0.085, front, z - math.sin(angle) * 0.085),
                              (x + math.cos(angle) * 0.085, front, z + math.sin(angle) * 0.085),
                              0.012, mat, accent, 4))
    elif era == 5:  # tide wave
        points = ((-0.13, 0.03), (-0.065, 0.08), (0, 0.03), (0.065, -0.02), (0.13, 0.03))
        for index, ((ax, az), (bx, bz)) in enumerate(zip(points, points[1:]), 1):
            parts.append(beam(f"E{era} tide crest {index}", (x + ax, front, z + az), (x + bx, front, z + bz), 0.014, mat, accent, 4))
    elif era == 6:  # atom
        for index, rotation in enumerate((-0.65, 0, 0.65), 1):
            icon = common.torus(f"E{era} atom orbit {index}", 0.105, 0.012, (x, front, z), mat, accent,
                                rotation=(math.pi / 2, rotation, 0), segments=(8, 3))
            parts.append(icon)
        parts.append(common.cylinder(f"E{era} atom core", 0.028, 0.035, (x, front, z), mat, 7, 6,
                                     rotation=(math.pi / 2, 0, 0)))
    elif era == 7:  # relay forks
        parts.append(beam(f"E{era} relay mast", (x, front, z - 0.13), (x, front, z + 0.10), 0.014, mat, accent, 4))
        parts.append(beam(f"E{era} relay west", (x, front, z + 0.04), (x - 0.10, front, z + 0.13), 0.014, mat, accent, 4))
        parts.append(beam(f"E{era} relay east", (x, front, z + 0.04), (x + 0.10, front, z + 0.13), 0.014, mat, accent, 4))
    else:  # Earth under glass
        parts.append(common.torus(f"E{era} Earth crest", 0.105, 0.018, (x, front, z), mat, accent,
                                  rotation=(math.pi / 2, 0, 0), segments=(10, 4)))
        parts.append(beam(f"E{era} Earth meridian", (x, front, z - 0.09), (x, front, z + 0.09), 0.011, mat, accent, 4))
        parts.append(beam(f"E{era} Earth equator", (x - 0.09, front, z), (x + 0.09, front, z), 0.011, mat, accent, 4))


def build_journey_flag_line() -> dict:
    common.reset()
    mat = material()
    parts = [
        common.box("Journey flag west foot", (0.40, 0.36, 0.10), (-2.18, 0, 0.05), mat, 13),
        common.box("Journey flag east foot", (0.40, 0.36, 0.10), (2.18, 0, 0.05), mat, 13),
        beam("Journey flag west post", (-2.18, 0, 0.10), (-2.18, 0, 2.32), 0.055, mat, 3, 8),
        beam("Journey flag east post", (2.18, 0, 0.10), (2.18, 0, 2.32), 0.055, mat, 3, 8),
        beam("Journey flag cable", (-2.22, 0, 2.15), (2.22, 0, 2.15), 0.022, mat, 10, 6),
    ]
    flag_palette = (11, 9, 7, 10, 6, 11, 5, 7)
    for era, x in enumerate((-1.75, -1.25, -0.75, -0.25, 0.25, 0.75, 1.25, 1.75), 1):
        parts.extend((
            beam(f"E{era} flag tie", (x, 0, 2.14), (x, 0, 1.91), 0.014, mat, 14, 4),
            common.box(f"E{era} journey crest field", (0.38, 0.045, 0.48), (x, 0, 1.66), mat, flag_palette[era - 1], 0),
        ))
        flag_icon(parts, era, x, mat)
    return finish("JourneyFlagLineE8", "journey-flag-line.e8", parts)


def main() -> None:
    common.write_shared_atlas()
    print(json.dumps([build_crater_rim_set(), build_lander_legs(), build_journey_flag_line()], indent=2))


if __name__ == "__main__":
    main()
