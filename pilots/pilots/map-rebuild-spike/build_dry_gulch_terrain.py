"""Build the render-only Dry Gulch theme checkpoint.

The mesh follows the existing visual heightfield, wash, and spring descriptors.
Simulation movement and spring placement remain planar and code-owned.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

import bpy
import mathutils
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"

BLEND = OUT / "dry-gulch-terrain.blend"
GLB = OUT / "dry-gulch-terrain.glb"
ATLAS = OUT / "dry-gulch-terrain-atlas.png"
CONTRACT = OUT / "dry-gulch-terrain-contract.json"

claim_spec = importlib.util.spec_from_file_location("claim_terrain_helpers", OUT / "build_the_claim_terrain.py")
claim = importlib.util.module_from_spec(claim_spec)
claim_spec.loader.exec_module(claim)
claim.mathutils = mathutils

HALF = 32.0
SEGMENTS = 128
ATLAS_SIZE = 1254
SOURCE_ATLAS = ROOT / "assets/raw/dry-gulch-terrain-atlas-v2.png"
SPRING_X = -18.0
SPRING_Z = -18.0
SPRING_RADIUS = 1.4


def smoothstep(edge0, edge1, value):
    t = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def gaussian(x, z, cx, cz, sx, sz):
    return np.exp(-(((x - cx) / sx) ** 2 + ((z - cz) / sz) ** 2) * 0.5)


def oval_mask(x, z, cx, cz, rx, rz):
    normalized = ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2
    return 1.0 - smoothstep(0.54, 1.0, normalized)


def wash_mask(x, z, cx, cz, length, width, angle):
    dx = x - cx
    dz = z - cz
    along = dx * math.cos(angle) + dz * math.sin(angle)
    across = -dx * math.sin(angle) + dz * math.cos(angle)
    length_mask = 1.0 - smoothstep(length * 0.42, length * 0.5, np.abs(along))
    warped_across = across + np.sin(along * 0.18) * width * 0.18
    width_mask = 1.0 - smoothstep(width * 0.32, width * 0.5, np.abs(warped_across))
    return np.clip(length_mask * width_mask, 0.0, 1.0)


def terrain_height(x, z):
    """Dry Gulch visual height; accepts scalars or NumPy arrays."""
    x = np.asarray(x, dtype=np.float32)
    z = np.asarray(z, dtype=np.float32)
    ax = np.abs(x)
    az = np.abs(z)

    grain = np.sin(x * 0.17 + z * 0.08) * 0.05 + np.cos(x * 0.08 - z * 0.21) * 0.035
    floor = 0.30 + grain
    rim = smoothstep(19.0, 31.5, np.maximum(ax, az)) * 1.42
    mesas = (
        gaussian(x, z, 22.5, 17.0, 7.5, 6.5) * 1.15
        + gaussian(x, z, 25.0, -8.0, 6.0, 8.5) * 0.82
        + gaussian(x, z, -24.5, 10.0, 6.5, 7.0) * 0.92
        + gaussian(x, z, 7.0, -26.0, 9.0, 5.0) * 0.55
    )
    basin = oval_mask(x, z, SPRING_X, SPRING_Z, 7.5, 7.5 * 0.78) * 0.68
    southwest_wash = wash_mask(x, z, -12.0, -14.0, 38.0, 4.2, -0.55) * 0.20
    east_wash = wash_mask(x, z, 14.0, 10.0, 42.0, 3.6, 0.34) * 0.16
    height = floor + rim + mesas - basin - southwest_wash - east_wash

    perimeter = smoothstep(29.0, 32.0, np.maximum(ax, az))
    height = height * (1.0 - perimeter) + np.minimum(height, 2.55) * perimeter
    height = np.clip(height, -0.58, 2.75)
    dx, dz = x - SPRING_X, z - SPRING_Z
    angle = np.arctan2(dz, dx)
    radius = np.hypot(dx, dz) / (1 + 0.06 * np.sin(angle * 3) + 0.025 * np.sin(angle * 7))
    return height - 0.28 * (1 - smoothstep(0.65, 1.65, radius))


def make_atlas():
    """Use the native-authored ledger albedo; geometry and masks remain code-owned."""
    ATLAS.write_bytes(SOURCE_ATLAS.read_bytes())
    image = bpy.data.images.load(str(ATLAS), check_existing=False)
    assert tuple(image.size) == (ATLAS_SIZE, ATLAS_SIZE)
    image.colorspace_settings.name = "sRGB"
    image.pack()
    return image


def make_terrain(material):
    vertices = []
    uvs = []
    faces = []
    for zi in range(SEGMENTS + 1):
        game_z = -HALF + HALF * 2.0 * zi / SEGMENTS
        for xi in range(SEGMENTS + 1):
            x = -HALF + HALF * 2.0 * xi / SEGMENTS
            vertices.append((x, -game_z, float(terrain_height(x, game_z))))
            uvs.append((xi / SEGMENTS, zi / SEGMENTS))
    row = SEGMENTS + 1
    for zi in range(SEGMENTS):
        for xi in range(SEGMENTS):
            a = zi * row + xi
            b = a + 1
            c = a + row
            d = c + 1
            faces.extend(((a, d, b), (a, c, d)))
    mesh = bpy.data.meshes.new("DryGulchTerrainMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        polygon.use_smooth = True
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = uvs[vertex_index]
    obj = bpy.data.objects.new("DryGulchTerrain", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(material)
    obj["render_only"] = True
    obj["sim_surface"] = "planar"
    obj["height_socket"] = "Terrain.visualY"
    obj["tile_id"] = "e1-dry-gulch"
    obj["water_mask"] = "spring pond circle at (-18,-18), radius 1.4; runtime-owned"
    obj["heightfield"] = "spring basin plus southwest and east descriptor washes"
    return obj


def make_pond(materials):
    water_height = float(terrain_height(SPRING_X, SPRING_Z)) + 0.1875
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=SPRING_RADIUS, depth=0.045, location=(SPRING_X, -SPRING_Z, water_height))
    pond = bpy.context.object
    pond.name = "RenderHelperDryGulchSpring"
    pond.data.materials.append(materials["water"])
    objects = [pond]
    for index in range(14):
        angle = index * 2.399963 + 0.3
        radius = SPRING_RADIUS * (1.08 + (index % 5) * 0.035)
        x = SPRING_X + math.cos(angle) * radius
        z = SPRING_Z + math.sin(angle) * radius
        objects.extend(claim.make_reed_cluster(f"RenderHelperDryGulchSpringReed.{index}", x, z, 0.72 + (index % 4) * 0.08, materials))
    return objects


def make_preview():
    claim.terrain_height = terrain_height
    objects = claim.make_dry_gulch_landmark_preview()
    # Keep the only water source readable from the real run camera. The old
    # desert composition put its headframe directly in front of the spring.
    for obj in objects:
        if obj.name.startswith("RenderHelperMine"):
            obj.location.x += 15.0
            obj.location.y -= 3.0
    spring_materials = {
        "water": claim.make_render_material("DryGulchSpringWater", (0.055, 0.28, 0.20), 0.24, 0.02),
        "reed": claim.make_render_material("DryGulchOasisReed", (0.29, 0.42, 0.09)),
    }
    objects.extend(make_pond(spring_materials))
    return objects


def county_height(x, game_z):
    """Dry Gulch's failed basin continues as dry washes and enclosing mesas."""
    local = float(terrain_height(x, game_z))
    outside = max(0.0, abs(x) - HALF, abs(game_z) - HALF)
    if outside <= 0.0:
        return local
    rolling = math.sin(x * 0.067 + game_z * 0.041) * 0.22 + math.sin(x * 0.139 - game_z * 0.053 + 0.9) * 0.12
    rim = float(smoothstep(48.0, 138.0, max(abs(x), abs(game_z)))) * 5.6
    mesas = (
        float(gaussian(x, game_z, -82.0, 58.0, 23.0, 18.0)) * 3.4
        + float(gaussian(x, game_z, 88.0, 52.0, 24.0, 17.0)) * 3.7
        + float(gaussian(x, game_z, -105.0, -61.0, 28.0, 20.0)) * 4.1
        + float(gaussian(x, game_z, 112.0, -55.0, 29.0, 21.0)) * 4.4
    )
    southwest_wash = float(wash_mask(x, game_z, -42.0, -38.0, 118.0, 8.0, -0.55)) * 0.52
    east_wash = float(wash_mask(x, game_z, 48.0, 30.0, 126.0, 7.0, 0.34)) * 0.46
    target = 0.78 + rolling + rim + mesas - southwest_wash - east_wash
    jitter = math.sin(x * 0.09 + game_z * 0.12) * 8.0 + math.sin(x * 0.19 - game_z * 0.08 + 1.1) * 4.0
    blend = float(smoothstep(5.0, 50.0, outside + jitter))
    return local * (1.0 - blend) + target * blend


def make_dry_county_surround(atlas):
    materials = {
        "cactus": claim.make_render_material("DryCountyCactus", (0.075, 0.22, 0.07)),
        "cactus_light": claim.make_render_material("DryCountyCactusSun", (0.14, 0.32, 0.10)),
        "stone": claim.make_render_material("DryCountyStone", (0.24, 0.21, 0.16)),
        "timber": claim.make_render_material("DryCountyTimber", (0.16, 0.07, 0.025)),
        "wood": claim.make_render_material("DryCountyWood", (0.28, 0.12, 0.038)),
    }
    ground_material = claim.make_claim_county_material(atlas, "RenderHelperDryGulchCountyPaint")
    objects = [claim.make_county_ground("RenderHelperDryGulchCountyGround", county_height, ground_material)]
    cacti = [
        (-43.0, 11.0, 1.28, 1.0, 0.2),
        (-49.0, -14.0, 0.96, -1.0, -0.5),
        (-63.0, 24.0, 1.14, 1.0, 0.8),
        (-78.0, -30.0, 1.36, -1.0, -0.9),
        (44.0, 13.0, 1.18, -1.0, 0.4),
        (56.0, -16.0, 0.92, 1.0, -0.6),
        (71.0, 27.0, 1.32, -1.0, 0.9),
        (87.0, -33.0, 1.08, 1.0, -0.7),
    ]
    for index, (x, game_z, scale, flip, yaw) in enumerate(cacti):
        objects.extend(claim.make_cactus(f"RenderHelperDryCountyCactus.{index}", x, game_z, scale, materials, flip, yaw, height_at=county_height))
    for index, (x, game_z, radius, depth) in enumerate(
        [(-84.0, 58.0, 17.0, 8.6), (91.0, 53.0, 18.0, 9.2), (-111.0, -63.0, 21.0, 10.6), (118.0, -57.0, 22.0, 11.0), (132.0, 78.0, 17.0, 8.0)]
    ):
        objects.extend(claim.add_county_mesa(f"RenderHelperDryCountyMesa.{index}", x, game_z, radius, depth, materials["stone"], 7 + index % 2, height_at=county_height))
    for index, (x, game_z, scale) in enumerate([(-47.0, 28.0, (3.0, 2.0, 1.5)), (51.0, -29.0, (3.5, 2.3, 1.8)), (73.0, 38.0, (2.4, 1.7, 1.3))]):
        objects.append(claim.add_county_rock(f"RenderHelperDryCountyOutcrop.{index}", x, game_z, scale, materials["stone"], index * 0.62, height_at=county_height))

    # A collapsed outer stamp frame makes the horizon another failed working,
    # not a second active Claim headframe.
    x, game_z = 69.0, -38.0
    base = county_height(x, game_z)
    objects.extend(
        [
            claim.add_beam("RenderHelperDryCountyRuin.leg", (x - 1.8, game_z, base), (x - 0.5, game_z, base + 4.3), 0.20, materials["timber"]),
            claim.add_beam("RenderHelperDryCountyRuin.fallenLeg", (x + 2.0, game_z, base + 0.15), (x + 4.8, game_z - 1.2, base + 0.45), 0.22, materials["timber"]),
            claim.add_beam("RenderHelperDryCountyRuin.crossbar", (x - 0.7, game_z, base + 4.2), (x + 1.2, game_z, base + 3.1), 0.18, materials["wood"]),
        ]
    )
    meshes = [obj for obj in objects if obj.type == "MESH"]
    triangles = sum(sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons) for obj in meshes)
    return objects, {
        "exported": False,
        "purpose": "owner exterior verdict only; runtime vista remains code-owned",
        "radiusMeters": claim.COUNTY_RADIUS,
        "objects": len(objects),
        "approxTriangles": triangles,
        "regionalGrammar": ["ochre river county", "faceted desert geology", "cacti only", "hard-used extraction scars"],
        "contractSignature": ["closed failed basin", "two dry washes", "collapsed outer stamp frame", "no exterior water"],
    }


def make_contract(terrain, preview, county_stats):
    coords = np.asarray([vertex.co[:] for vertex in terrain.data.vertices], dtype=np.float32)
    triangles = sum(len(polygon.vertices) - 2 for polygon in terrain.data.polygons)
    return {
        "asset": GLB.name,
        "tileId": "e1-dry-gulch",
        "renderOnly": True,
        "simulation": "planar and unchanged",
        "heightSocket": "Terrain.visualY",
        "boundsMeters": {
            "min": [round(float(value), 4) for value in coords.min(axis=0)],
            "max": [round(float(value), 4) for value in coords.max(axis=0)],
        },
        "meshCount": 1,
        "primitiveCount": 1,
        "materialCount": 1,
        "vertices": len(terrain.data.vertices),
        "triangles": triangles,
        "triangleBudget": 60000,
        "texture": {"count": 1, "width": ATLAS_SIZE, "height": ATLAS_SIZE, "embedded": True},
        "waterTruth": {"kind": "spring_pond", "x": SPRING_X, "z": SPRING_Z, "radius": SPRING_RADIUS},
        "heightfieldTruth": {
            "springBasin": {"x": SPRING_X, "z": SPRING_Z, "radius": 7.5, "depth": 0.68},
            "springBed": {"x": SPRING_X, "z": SPRING_Z, "depth": 0.28, "innerRadius": 0.65, "outerRadius": 1.65, "angularWarp": [0.06, 0.025]},
            "washes": ["southwest-arroyo", "east-mesa-wash"],
        },
        "landmarkMountSpace": claim.landmark_mount_space(),
        "landmarkMounts": [
            claim.landmark_mount("ruined_mining_operation", 2.0, -5.8),
            claim.landmark_mount("abandoned_farmhouse", 10.5, 14.5, -0.12),
            claim.landmark_mount("cactus_thicket", 18.3, 0.0),
            claim.landmark_mount("bison_skeleton", -8.0, 12.5, 0.18),
            {**claim.landmark_mount("isolated_spring", SPRING_X, SPRING_Z), "position": [SPRING_X, 0.28, SPRING_Z]},
        ],
        "panoramaMount": claim.panorama_mount("dry-gulch"),
        "ownerPreview": {
            "exported": False,
            "theme": "failed-desert-basin",
            "landmarks": ["ruined_mining_operation", "abandoned_farmhouse", "cactus_thicket", "bison_skeleton", "isolated_spring"],
            "objects": len(preview),
            "exteriorSurround": county_stats,
        },
        "sourceArt": [str(SOURCE_ATLAS.relative_to(ROOT))] + [
            str(path.relative_to(ROOT))
            for path in (
                claim.BANK_A,
                claim.BANK_B,
                claim.BANK_C,
                claim.KIT_ERA,
                claim.CONTRACT_PLATES["dry-gulch"],
            )
        ],
    }


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    claim.reset_scene()
    atlas = make_atlas()
    material = claim.make_material(atlas)
    material.name = "DryGulchPaintedTerrainMaterial"
    terrain = make_terrain(material)
    preview = make_preview()
    county, county_stats = make_dry_county_surround(atlas)
    backdrop = claim.make_backdrop()
    panorama = claim.link_panorama("dry-gulch")
    for obj in panorama:
        obj.hide_render = True
    camera = claim.add_camera("DryGulchRunCamera", (0.0, -30.3, 26.26), (0.0, -8.65, 0.51), 42.0)
    edge_camera = claim.add_camera("DryGulchEastEdge", (24.0, -30.3, 26.26), (24.0, -8.65, 0.51), 42.0)
    overview = claim.add_camera("DryGulchOverview", (0.0, -38.0, 50.0), (0.0, -1.0, 0.42), 46.0)
    county_camera = claim.add_camera("DryGulchCountyOverview", (0.0, -78.0, 88.0), (0.0, -5.0, 1.1), 52.0)
    low_camera = claim.add_camera("DryGulchLowCamera", (-28.0, 23.0, 11.0), (5.0, -0.4, 0.38), 46.0)
    horizon_camera = claim.add_camera("DryGulchPanoramaHorizon", (0.0, 0.0, 3.8), (-120.0, 0.0, 8.0), 52.0)
    lights = claim.add_lighting(sunset=False)
    terrain.hide_render = False
    for obj in county:
        obj.hide_render = True
    claim.render(camera, ARTIFACTS / "dry-gulch-run-camera.png")
    claim.render(overview, ARTIFACTS / "dry-gulch-layout-overview.png")
    claim.render(edge_camera, ARTIFACTS / "dry-gulch-exterior-before-edge.png")
    terrain.hide_render = True
    for obj in county:
        obj.hide_render = False
    claim.render(edge_camera, ARTIFACTS / "dry-gulch-run-camera-east-edge.png")
    claim.render(county_camera, ARTIFACTS / "dry-gulch-county-overview.png")
    claim.remove_objects(lights)
    sunset_lights = claim.add_lighting(sunset=True)
    claim.render(low_camera, ARTIFACTS / "dry-gulch-low-angle-unique.png")
    claim.render(low_camera, ARTIFACTS / "dry-gulch-panorama-before.png")
    for obj in panorama:
        obj.hide_render = False
    claim.render(low_camera, ARTIFACTS / "dry-gulch-panorama-mounted.png")
    claim.render(horizon_camera, ARTIFACTS / "dry-gulch-panorama-horizon.png")

    claim.remove_objects(sunset_lights + [camera, edge_camera, overview, county_camera, low_camera, horizon_camera, backdrop] + preview + county + panorama)
    terrain.hide_render = False
    bpy.context.scene.world = None
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    contract = make_contract(terrain, preview, county_stats)
    bpy.context.view_layer.objects.active = terrain
    terrain.select_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.export_scene.gltf(
        filepath=str(GLB),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_extras=True,
    )
    contract["files"] = {
        "blend": {"bytes": BLEND.stat().st_size, "sha256": sha256(BLEND)},
        "glb": {"bytes": GLB.stat().st_size, "sha256": sha256(GLB)},
        "atlas": {"bytes": ATLAS.stat().st_size, "sha256": sha256(ATLAS)},
    }
    CONTRACT.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(contract, indent=2))


if __name__ == "__main__":
    main()
