from pathlib import Path
import hashlib
import json
import math

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parent
SOURCE_BLEND = ROOT / "claim-office.blend"
SOURCE_GLB = ROOT / "claim-office.glb"
BLEND = ROOT / "claim-office.e2.blend"
GLB = ROOT / "claim-office.e2.glb"
SOURCE_BLEND_SHA = "46a2f73fb7a82678292760551e466cedd5ec94639ed0e31cc3cf3a3d5ee8e817"
SOURCE_GLB_SHA = "b2a23b06c7cb6822166dceff2a02f410f125fac8fe1909d99ec0c8489f1e104b"

# Reuse the accepted atlas vocabulary. Deck is the warm ochre/brass family;
# roof is soot-dark iron; accent is the restrained E2 teal.
UV_BRASS = (0.29, 0.55, 0.46, 0.70)
UV_IRON = (0.79, 0.04, 0.96, 0.46)
UV_TEAL = (0.30, 0.80, 0.45, 0.95)
UV_STONE = (0.05, 0.80, 0.20, 0.95)


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


def cylinder(name, radius, depth, location, material, uv_bounds, vertices=12, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    return tag(obj, material, uv_bounds, 0.01)


def add_gauge(parts, x, material):
    # Cylinders face the plaza along -Y. The dial stays non-emissive.
    rotation = (math.pi / 2, 0, 0)
    parts.extend((
        cylinder(f"Civic gauge rim {x}", 0.17, 0.065, (x, -1.49, 2.72),
                 material, UV_BRASS, 16, rotation),
        cylinder(f"Civic gauge face {x}", 0.125, 0.065, (x, -1.515, 2.72),
                 material, UV_STONE, 16, rotation),
        box(f"Civic gauge needle {x}", (0.025, 0.018, 0.105),
            (x + 0.022, -1.545, 2.745), material, UV_TEAL, 0.004,
            rotation=(0, 0.45, 0)),
        cylinder(f"Civic gauge stem {x}", 0.035, 0.28, (x, -1.46, 2.48),
                 material, UV_BRASS, 8),
    ))


def add_e2_parts(material):
    parts = []

    # Town Hall-bound civic growth: a paired public pressure readout sits on
    # the existing Claim Office frontage, without changing its flag or shell.
    add_gauge(parts, -0.64, material)
    add_gauge(parts, 0.64, material)

    # The steam service line follows the clear rear service corner—not either
    # side window—and terminates visibly at the existing chimney and a low
    # flange. The shutoff wheel shares the riser's axis.
    parts.extend((
        cylinder("Civic steam riser", 0.055, 1.80, (2.075, 1.12, 1.45),
                 material, UV_IRON, 10),
        cylinder("Civic steam upper run", 0.055, 0.64, (2.075, 0.80, 2.35),
                 material, UV_BRASS, 10, rotation=(math.pi / 2, 0, 0)),
        cylinder("Civic steam chimney feed", 0.055, 0.48, (1.835, 0.48, 2.35),
                 material, UV_BRASS, 10, rotation=(0, math.pi / 2, 0)),
        cylinder("Civic shutoff wheel", 0.13, 0.05, (2.105, 1.12, 1.72),
                 material, UV_TEAL, 12, rotation=(0, math.pi / 2, 0)),
        cylinder("Civic riser low flange", 0.07, 0.08, (2.075, 1.12, 0.55),
                 material, UV_BRASS, 10),
        cylinder("Civic riser upper junction", 0.07, 0.12, (2.075, 1.12, 2.35),
                 material, UV_BRASS, 10, rotation=(math.pi / 2, 0, 0)),
        cylinder("Civic chimney junction", 0.085, 0.12, (2.075, 0.48, 2.35),
                 material, UV_BRASS, 10, rotation=(0, math.pi / 2, 0)),
    ))

    # Riveted-looking caps advance the porch craft without replacing its wood.
    for x in (-1.82, -0.72, 0.72, 1.82):
        parts.append(box(f"Iron porch cap {x}", (0.20, 0.19, 0.10),
                         (x, -1.39, 1.90), material, UV_IRON, 0.01))

    # The fixed Town camera sees the rear service corner. A civic boiler and
    # tall relief stack give the new age a readable silhouette while the flag,
    # roofline, frontage, and footprint remain the Claim Office's own.
    parts.extend((
        cylinder("Civic service boiler", 0.30, 1.55, (1.76, 1.18, 1.36),
                 material, UV_IRON, 12),
        cylinder("Civic boiler band low", 0.34, 0.12, (1.76, 1.18, 0.72),
                 material, UV_BRASS, 12),
        cylinder("Civic boiler band mid", 0.34, 0.12, (1.76, 1.18, 1.36),
                 material, UV_TEAL, 12),
        cylinder("Civic boiler band high", 0.34, 0.12, (1.76, 1.18, 2.00),
                 material, UV_BRASS, 12),
        cylinder("Civic relief stack", 0.17, 2.20, (1.76, 1.18, 3.30),
                 material, UV_IRON, 12),
        cylinder("Civic relief lower flange", 0.22, 0.14, (1.76, 1.18, 2.28),
                 material, UV_BRASS, 12),
        cylinder("Civic relief roof collar", 0.27, 0.14, (1.76, 1.18, 2.72),
                 material, UV_BRASS, 12),
        cylinder("Civic relief upper flange", 0.22, 0.14, (1.76, 1.18, 4.12),
                 material, UV_BRASS, 12),
        cylinder("Civic relief cap", 0.26, 0.16, (1.76, 1.18, 4.45),
                 material, UV_TEAL, 12),
        cylinder("Civic boiler feed", 0.10, 0.70, (1.76, 0.83, 2.25),
                 material, UV_BRASS, 10, rotation=(math.pi / 2, 0, 0)),
    ))

    # One large rear pressure dial remains legible from the gameplay camera;
    # the paired smaller facade dials keep the public-facing Town Hall lineage.
    parts.extend((
        cylinder("Civic rear gauge rim", 0.31, 0.09, (0.25, 1.285, 2.22),
                 material, UV_BRASS, 16, rotation=(math.pi / 2, 0, 0)),
        cylinder("Civic rear gauge face", 0.235, 0.10, (0.25, 1.315, 2.22),
                 material, UV_STONE, 16, rotation=(math.pi / 2, 0, 0)),
        box("Civic rear gauge needle", (0.035, 0.02, 0.19),
            (0.29, 1.37, 2.26), material, UV_TEAL, 0.004, rotation=(0, 0.55, 0)),
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
    assert sha256(SOURCE_BLEND) == SOURCE_BLEND_SHA, "E1 Claim Office BLEND changed; re-audit the edit base"
    assert sha256(SOURCE_GLB) == SOURCE_GLB_SHA, "E1 Claim Office GLB changed; re-audit the edit base"
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE_BLEND))
    office = bpy.data.objects["ClaimOfficeFullWrap"]
    source_dimensions = tuple(office.dimensions)
    material = office.data.materials[0]
    parts = add_e2_parts(material)
    apply_and_uv(parts)

    bpy.ops.object.select_all(action="DESELECT")
    office.select_set(True)
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = office
    bpy.ops.object.join()
    office.name = "ClaimOfficeE2"
    office.data.name = "ClaimOfficeE2Mesh"
    office.data.uv_layers.active.name = "UVMap"
    for polygon in office.data.polygons:
        polygon.material_index = 0
    while len(office.data.materials) > 1:
        office.data.materials.pop(index=len(office.data.materials) - 1)
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    office["epoch_variant"] = "E2 Steamworks"
    office["identity_edit"] = "civic gauges, rear service boiler, relief stack, iron porch caps"
    assert all(abs(office.dimensions[i] - source_dimensions[i]) < 0.0001 for i in range(3))

    anchors = [
        add_steam_anchor("steam_anchor_1", (1.36, 0.48, 4.20), office),
        add_steam_anchor("steam_anchor_2", (1.76, 1.18, 4.53), office),
    ]

    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.object.select_all(action="DESELECT")
    office.select_set(True)
    for anchor in anchors:
        anchor.select_set(True)
    bpy.context.view_layer.objects.active = office
    bpy.ops.export_scene.gltf(
        filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False,
        export_materials="EXPORT",
    )
    print(json.dumps({
        "blend": str(BLEND), "glb": str(GLB), "sha256": sha256(GLB),
        "triangles": sum(len(p.vertices) - 2 for p in office.data.polygons),
        "dimensions": list(office.dimensions), "anchors": [anchor.name for anchor in anchors],
    }, indent=2))


if __name__ == "__main__":
    main()
