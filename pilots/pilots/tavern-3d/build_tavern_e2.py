from pathlib import Path
import hashlib
import json
import math

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parent
SOURCE_BLEND = ROOT / "town-v3-tavern.blend"
SOURCE_GLB = ROOT / "town-v3-tavern.glb"
BLEND = ROOT / "tavern.e2.blend"
GLB = ROOT / "tavern.e2.glb"
SOURCE_BLEND_SHA = "b81ef19a24661c3ea97feb3b7f75caceef5599954d6462b1bbd2ab6085ade2fe"
SOURCE_GLB_SHA = "edec4934d6d956170078b521fe526ccadcde015567094aec59001e2d4b71b90d"

# Existing atlas tiles: dark timber, warm brass, and the restrained agent-teal.
UV_DARK = (0.02, 0.02, 0.23, 0.23)
UV_BRASS = (0.77, 0.27, 0.98, 0.48)
UV_TEAL = (0.52, 0.27, 0.73, 0.48)
UV_WOOD = (0.27, 0.27, 0.48, 0.48)
UV_ROOF = (0.77, 0.77, 0.98, 0.98)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tag(obj: bpy.types.Object, material: bpy.types.Material, uv_bounds, bevel=0.012):
    obj.data.materials.append(material)
    obj["e2_uv_bounds"] = list(uv_bounds)
    if bevel:
        modifier = obj.modifiers.new("Painted edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        modifier.limit_method = "ANGLE"
    return obj


def box(name, size, location, material, uv_bounds, bevel=0.012, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = tuple(value / 2 for value in size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return tag(obj, material, uv_bounds, bevel)


def cylinder(name, radius, depth, location, material, uv_bounds, vertices=10, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    return tag(obj, material, uv_bounds, 0.01)


def add_lamp(parts, x, teal, material):
    glass_uv = UV_TEAL if teal else UV_BRASS
    parts.extend((
        cylinder(f"Lamp hook {x}", 0.025, 0.22, (x, -1.28, 1.77), material, UV_DARK, 8),
        cylinder(f"Lamp cap {x}", 0.095, 0.08, (x, -1.28, 1.64), material, UV_BRASS, 10),
        cylinder(f"Lamp glass {x}", 0.073, 0.22, (x, -1.28, 1.49), material, glass_uv, 10),
        cylinder(f"Lamp base {x}", 0.095, 0.07, (x, -1.28, 1.345), material, UV_BRASS, 10),
    ))


def add_rear_service_lamp(parts, material):
    # The saloon serves the whole parcel, not only the plaza frontage. A third
    # ordinary oil lamp makes the era edit visible at the locked Town camera
    # while remaining attached to the existing rear service wall.
    parts.extend((
        box("Rear lamp wall bracket", (0.07, 0.30, 0.07),
            (-0.62, 1.35, 1.83), material, UV_DARK, 0.008),
        cylinder("Rear lamp hook", 0.025, 0.21, (-0.62, 1.49, 1.72), material, UV_DARK, 8),
        cylinder("Rear lamp cap", 0.095, 0.08, (-0.62, 1.49, 1.59), material, UV_BRASS, 10),
        cylinder("Rear lamp glass", 0.073, 0.22, (-0.62, 1.49, 1.44), material, UV_BRASS, 10),
        cylinder("Rear lamp base", 0.095, 0.07, (-0.62, 1.49, 1.295), material, UV_BRASS, 10),
    ))


def add_e2_parts(material):
    parts = []

    # The E1 awning becomes the full E2 covered porch through an outer roof,
    # valance, and iron corner brackets. It stays inside the E1 envelope.
    parts.extend((
        box("Saloon covered porch roof", (3.90, 0.30, 0.08),
            (0, -1.50, 1.90), material, UV_ROOF, 0.010, rotation=(-0.16, 0, 0)),
        box("Saloon porch valance", (3.90, 0.06, 0.10),
            (0, -1.62, 1.80), material, UV_DARK, 0.008),
        box("Saloon porch bracket left", (0.18, 0.16, 0.42),
            (-1.78, -1.53, 1.67), material, UV_BRASS, 0.010),
        box("Saloon porch bracket right", (0.18, 0.16, 0.42),
            (1.78, -1.53, 1.67), material, UV_BRASS, 0.010),
    ))

    # Required A2 swing doors are half-height and slightly open so their role
    # reads as access hardware rather than decorative door bracing.
    for x, brace_angle in ((-0.285, -0.40), (0.285, 0.40)):
        parts.append(box(f"Saloon swing leaf {x}", (0.52, 0.055, 0.76),
                         (x, -1.465, 0.96), material, UV_WOOD, 0.014,
                         rotation=(0, 0, -0.18 if x < 0 else 0.18)))
        parts.append(box(f"Saloon swing rail {x}", (0.46, 0.035, 0.065),
                         (x, -1.501, 0.96), material, UV_BRASS, 0.006,
                         rotation=(0, brace_angle, 0)))
        parts.append(cylinder(f"Saloon hinge {x}", 0.035, 0.64,
                              (x + (-0.235 if x < 0 else 0.235), -1.49, 0.96),
                              material, UV_DARK, 8))

    # A2 calls for hanging oil lamps, one teal. The teal lamp is agent-tech
    # restraint, not emission; both remain ordinary baked geometry.
    add_lamp(parts, -0.94, False, material)
    add_lamp(parts, 0.94, True, material)
    add_rear_service_lamp(parts, material)

    # The fixed Town camera sees the service side, not the Saloon doors. A
    # kitchen boiler and tall flanged vent make E2 readable across the plaza
    # while remaining below the existing chimney and inside the E1 envelope.
    parts.extend((
        cylinder("Saloon service boiler", 0.29, 1.55, (1.77, 1.325, 1.36),
                 material, UV_DARK, 12),
        cylinder("Saloon boiler band low", 0.325, 0.12, (1.77, 1.325, 0.72),
                 material, UV_BRASS, 12),
        cylinder("Saloon boiler band mid", 0.325, 0.12, (1.77, 1.325, 1.36),
                 material, UV_TEAL, 12),
        cylinder("Saloon boiler band high", 0.325, 0.12, (1.77, 1.325, 2.00),
                 material, UV_BRASS, 12),
        cylinder("Saloon boiler vent", 0.15, 1.45, (1.77, 1.325, 2.82),
                 material, UV_DARK, 12),
        cylinder("Saloon vent lower flange", 0.19, 0.12, (1.77, 1.325, 2.20),
                 material, UV_BRASS, 12),
        cylinder("Saloon vent upper flange", 0.19, 0.12, (1.77, 1.325, 3.30),
                 material, UV_BRASS, 12),
        cylinder("Saloon vent cap", 0.22, 0.14, (1.77, 1.325, 3.62),
                 material, UV_TEAL, 12),
        cylinder("Saloon steam header", 0.09, 1.50, (1.02, 1.325, 2.15),
                 material, UV_BRASS, 10, rotation=(0, math.pi / 2, 0)),
        cylinder("Saloon shutoff wheel", 0.18, 0.06, (1.25, 1.63, 2.15),
                 material, UV_TEAL, 12, rotation=(math.pi / 2, 0, 0)),
    ))
    return parts


def add_steam_anchor(name, location, parent):
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=location)
    anchor = bpy.context.object
    anchor.name = name
    anchor.empty_display_size = 0.12
    anchor.parent = parent
    return anchor


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


def main():
    assert sha256(SOURCE_BLEND) == SOURCE_BLEND_SHA, "E1 Tavern BLEND changed; re-audit the edit base"
    assert sha256(SOURCE_GLB) == SOURCE_GLB_SHA, "E1 Tavern GLB changed; re-audit the edit base"
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE_BLEND))
    tavern = bpy.data.objects["TownTavernFullWrap"]
    source_dimensions = tuple(tavern.dimensions)
    material = tavern.data.materials[0]
    parts = add_e2_parts(material)
    apply_and_uv(parts)

    bpy.ops.object.select_all(action="DESELECT")
    tavern.select_set(True)
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = tavern
    bpy.ops.object.join()
    tavern.name = "TownTavernE2"
    tavern.data.name = "TownTavernE2Mesh"
    tavern.data.uv_layers.active.name = "UVMap"
    for polygon in tavern.data.polygons:
        polygon.material_index = 0
    while len(tavern.data.materials) > 1:
        tavern.data.materials.pop(index=len(tavern.data.materials) - 1)
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    tavern["epoch_variant"] = "E2 Steamworks"
    tavern["identity_edit"] = "covered Saloon porch, swing doors, oil lamps, and service boiler"
    assert all(abs(tavern.dimensions[i] - source_dimensions[i]) < 0.0001 for i in range(3)), (
        source_dimensions, tuple(tavern.dimensions),
        (min(corner[1] for corner in tavern.bound_box), max(corner[1] for corner in tavern.bound_box)),
    )

    anchors = [
        add_steam_anchor("steam_anchor_1", (1.02, 0.71, 3.96), tavern),
        add_steam_anchor("steam_anchor_2", (1.77, 1.325, 3.69), tavern),
    ]

    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.object.select_all(action="DESELECT")
    tavern.select_set(True)
    for anchor in anchors:
        anchor.select_set(True)
    bpy.context.view_layer.objects.active = tavern
    bpy.ops.export_scene.gltf(
        filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False,
        export_materials="EXPORT",
    )
    print(json.dumps({
        "blend": str(BLEND), "glb": str(GLB), "sha256": sha256(GLB),
        "triangles": sum(len(p.vertices) - 2 for p in tavern.data.polygons),
        "dimensions": list(tavern.dimensions), "anchors": [anchor.name for anchor in anchors],
    }, indent=2))


if __name__ == "__main__":
    main()
