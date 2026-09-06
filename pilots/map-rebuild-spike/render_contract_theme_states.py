"""Legacy contract-state proxies and reusable landmark helpers.

The final map-rebuild verdict no longer reuses the Claim terrain for Twin
Banks, Night Shift, or Baron. ``build_unique_contract_terrains.py`` imports the
small proxy helpers here, but owns separate terrain meshes and atlases. The CLI
render entrypoints below are retained only as historical comparison evidence.
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path
import sys

import bpy
import mathutils


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"

claim_spec = importlib.util.spec_from_file_location("claim_terrain_helpers", OUT / "build_the_claim_terrain.py")
claim = importlib.util.module_from_spec(claim_spec)
claim_spec.loader.exec_module(claim)
claim.mathutils = mathutils


def make_water_surface(half_width, material):
    vertices = []
    faces = []
    segments = 64
    for index in range(segments + 1):
        x = -claim.CLAIM_HALF + claim.CLAIM_HALF * 2.0 * index / segments
        vertices.extend(((x, half_width, 0.025), (x, -half_width, 0.025)))
    for index in range(segments):
        a = index * 2
        b = a + 2
        c = a + 1
        d = b + 1
        faces.extend(((a, d, b), (a, c, d)))
    mesh = bpy.data.meshes.new("RenderHelperTwinBanksWaterMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    water = bpy.data.objects.new("RenderHelperTwinBanksWater", mesh)
    bpy.context.collection.objects.link(water)
    mesh.materials.append(material)
    return water


def make_ford_stones(center_x, terrain_material):
    objects = []
    for index, game_z in enumerate((-6.4, -4.25, -2.1, 0.0, 2.1, 4.25, 6.4)):
        x = center_x + (-0.28 if index % 2 == 0 else 0.30)
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=9,
            radius=0.55,
            depth=0.08,
            location=(x, -game_z, 0.070),
            rotation=(0.0, 0.0, 0.18 if index % 2 else -0.12),
        )
        stone = bpy.context.object
        stone.name = f"RenderHelperTwinFord.{center_x}.{index}"
        stone.scale = (0.82, 0.56, 1.0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        stone.data.materials.append(terrain_material)
        objects.append(stone)
    return objects


def make_gravel_bar(name, x, game_z, length, width, yaw, material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=36, radius=0.5, depth=0.055, location=(x, -game_z, 0.062), rotation=(0.0, 0.0, -yaw))
    bar = bpy.context.object
    bar.name = name
    bar.scale = (length, width, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bar.data.materials.append(material)
    return bar


def make_stake(name, x, game_z, materials):
    ground = float(claim.terrain_height(x, game_z))
    return [
        claim.add_box_game(f"{name}.post", x, game_z, ground, (0.16, 0.16, 1.85), materials["timber"]),
        claim.add_box_game(f"{name}.board", x, game_z, ground + 1.28, (1.25, 0.14, 0.58), materials["board"]),
    ]


def render_twin_banks():
    terrain = bpy.data.objects.get("TheClaimTerrain")
    if terrain is None:
        raise RuntimeError("Open the Claim terrain .blend before rendering contract states")
    terrain_material = terrain.data.materials[0]
    materials = {
        "water": claim.make_water_material(),
        "gravel": claim.make_render_material("TwinBanksWetGravel", (0.38, 0.39, 0.28)),
        "timber": claim.make_render_material("TwinBanksStakeTimber", (0.18, 0.09, 0.03)),
        "board": claim.make_render_material("TwinBanksStakeBoard", (0.55, 0.32, 0.09)),
        "reed": claim.make_render_material("TwinBanksReeds", (0.25, 0.42, 0.10)),
    }
    objects = [make_water_surface(7.8, materials["water"])]
    objects.extend(make_ford_stones(-16.0, terrain_material))
    objects.extend(make_ford_stones(16.0, terrain_material))
    objects.extend(
        [
            make_gravel_bar("RenderHelperTwinBanksWestBar", -7.5, 0.2, 5.4, 1.35, -0.12, materials["gravel"]),
            make_gravel_bar("RenderHelperTwinBanksEastBar", 7.4, -0.25, 4.8, 1.2, 0.16, materials["gravel"]),
        ]
    )
    objects.extend(make_stake("RenderHelperTwinBanksSouthStake", 0.0, -12.0, materials))
    objects.extend(make_stake("RenderHelperTwinBanksNorthMarker", 0.0, 12.0, materials))

    reed_positions = [
        (-27, -8.4), (-23, 8.2), (-19, -8.1), (-12, 8.4), (-5, -8.3),
        (4, 8.2), (10, -8.25), (19, 8.35), (24, -8.15), (28, 8.25),
    ]
    for index, (x, game_z) in enumerate(reed_positions):
        objects.extend(claim.make_reed_cluster(f"RenderHelperTwinBanksReed.{index}", x, game_z, 1.0, materials))

    backdrop = claim.make_backdrop()
    camera = claim.add_camera("TwinBanksRunCamera", (0.0, -30.3, 26.26), (0.0, -8.65, 0.51), 42.0)
    overview = claim.add_camera("TwinBanksOverview", (0.0, -38.0, 50.0), (0.0, -1.0, 0.42), 46.0)
    lights = claim.add_lighting(sunset=False)
    claim.render(camera, ARTIFACTS / "twin-banks-run-camera-current-topology.png")
    claim.render(overview, ARTIFACTS / "twin-banks-layout-current-topology.png")
    claim.remove_objects(lights + [camera, overview, backdrop] + objects)


def make_emissive_material(name, color, strength):
    material = claim.make_render_material(name, color, 0.42, 0.05)
    shader = material.node_tree.nodes.get("Principled BSDF")
    emission = shader.inputs.get("Emission Color") or shader.inputs.get("Emission")
    if emission:
        emission.default_value = (*color, 1.0)
    emission_strength = shader.inputs.get("Emission Strength")
    if emission_strength:
        emission_strength.default_value = strength
    return material


def make_lantern_post(name, x, game_z, materials):
    ground = float(claim.terrain_height(x, game_z))
    objects = [
        claim.add_box_game(f"{name}.post", x, game_z, ground, (0.16, 0.16, 2.55), materials["iron"], tilt=(0.02, -0.03)),
        claim.add_box_game(f"{name}.arm", x + 0.28, game_z, ground + 2.30, (0.72, 0.12, 0.12), materials["iron"]),
        claim.add_cylinder_between(f"{name}.chain", (x + 0.54, game_z, ground + 2.30), (x + 0.54, game_z, ground + 1.98), 0.035, materials["iron"], vertices=7),
        claim.add_box_game(f"{name}.hood", x + 0.54, game_z, ground + 1.88, (0.52, 0.46, 0.22), materials["brass"]),
    ]
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.26, location=(x + 0.54, -game_z, ground + 1.57))
    lens = bpy.context.object
    lens.name = f"{name}.lens"
    lens.scale.z = 1.18
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    lens.data.materials.append(materials["cold_lens"])
    objects.append(lens)
    return objects, lens


def add_night_lighting():
    world = bpy.data.worlds.new("NightShiftWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.008, 0.016, 0.055, 1.0)
    background.inputs["Strength"].default_value = 0.72

    fill_data = bpy.data.lights.new("NightShiftColdFill", "AREA")
    fill_data.energy = 2100.0
    fill_data.color = (0.18, 0.28, 0.58)
    fill_data.shape = "DISK"
    fill_data.size = 34.0
    fill = bpy.data.objects.new("NightShiftColdFill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = (-8.0, 2.0, 25.0)
    claim.aim_at(fill, (0.0, 0.0, 0.0))
    return [fill]


def render_night_shift():
    terrain = bpy.data.objects.get("TheClaimTerrain")
    if terrain is None:
        raise RuntimeError("Open the Claim terrain .blend before rendering contract states")
    terrain_material = terrain.data.materials[0]
    materials = {
        "iron": claim.make_render_material("NightShiftLanternIron", (0.035, 0.055, 0.075), 0.62, 0.42),
        "brass": claim.make_render_material("NightShiftColdBrass", (0.16, 0.13, 0.07), 0.55, 0.35),
        "cold_lens": make_emissive_material("NightShiftColdLens", (0.025, 0.06, 0.11), 0.12),
        "warm_lens": make_emissive_material("NightShiftWarmLens", (1.0, 0.22, 0.025), 7.0),
    }
    objects = []
    objects.extend(claim.make_claim_landmark_preview())
    objects.append(claim.make_water_surface(claim.make_water_material()))
    objects.extend(claim.make_ford_stones(terrain_material))

    lantern_positions = [(0, 16), (-16, 18), (16, 18), (-22, -12), (22, -12), (-10, -24), (10, -24)]
    central_lens = None
    for index, (x, game_z) in enumerate(lantern_positions):
        lantern, lens = make_lantern_post(f"RenderHelperNightShiftLantern.{index}", x, game_z, materials)
        objects.extend(lantern)
        if index == 0:
            central_lens = lens

    backdrop = claim.make_backdrop()
    camera = claim.add_camera("NightShiftRunCamera", (0.0, -30.3, 26.26), (0.0, -8.65, 0.51), 42.0)
    lights = add_night_lighting()
    claim.render(camera, ARTIFACTS / "night-shift-run-camera-cold.png")

    central_lens.data.materials.clear()
    central_lens.data.materials.append(materials["warm_lens"])
    warm_data = bpy.data.lights.new("NightShiftRelitPool", "POINT")
    warm_data.energy = 1500.0
    warm_data.color = (1.0, 0.28, 0.035)
    warm_data.shadow_soft_size = 4.5
    warm = bpy.data.objects.new("NightShiftRelitPool", warm_data)
    bpy.context.collection.objects.link(warm)
    warm.location = (0.54, -16.0, float(claim.terrain_height(0.0, 16.0)) + 2.0)
    pool_data = bpy.data.lights.new("NightShiftRelitGroundPool", "AREA")
    pool_data.energy = 900.0
    pool_data.color = (1.0, 0.22, 0.025)
    pool_data.shape = "DISK"
    pool_data.size = 8.0
    pool = bpy.data.objects.new("NightShiftRelitGroundPool", pool_data)
    bpy.context.collection.objects.link(pool)
    pool.location = (0.54, -16.0, float(claim.terrain_height(0.0, 16.0)) + 5.0)
    claim.aim_at(pool, (0.54, -16.0, float(claim.terrain_height(0.0, 16.0))))
    claim.render(camera, ARTIFACTS / "night-shift-run-camera-relit.png")
    claim.remove_objects(lights + [warm, pool, camera, backdrop] + objects)


def make_banner(name, x, game_z, materials, yaw=0.0):
    ground = float(claim.terrain_height(x, game_z))
    return [
        claim.add_box_game(f"{name}.base", x, game_z, ground, (0.58, 0.58, 0.34), materials["iron"], yaw=yaw),
        claim.add_box_game(f"{name}.post", x, game_z, ground, (0.18, 0.18, 4.2), materials["dark_timber"], yaw=yaw),
        claim.add_box_game(f"{name}.crossbar", x + 0.7, game_z, ground + 3.68, (1.55, 0.16, 0.16), materials["dark_timber"], yaw=yaw),
        claim.add_box_game(f"{name}.cloth", x + 0.72, game_z, ground + 2.25, (1.45, 0.10, 1.75), materials["oxblood"], yaw=yaw, bevel=0.02),
    ]


def make_enemy_tent(name, x, game_z, scale, materials, yaw=0.0):
    ground = float(claim.terrain_height(x, game_z))
    objects = [
        claim.add_box_game(f"{name}.ground", x, game_z, ground + 0.02, (4.0 * scale, 3.1 * scale, 0.08), materials["dark_timber"], yaw=yaw),
        claim.add_roof_prism(f"{name}.canvas", x, game_z, ground + 0.08, 3.8 * scale, 2.9 * scale, 2.1 * scale, materials["enemy_canvas"], yaw),
    ]
    patch_x, patch_z = claim.local_point(x, game_z, -0.72 * scale, -0.12 * scale, yaw)
    objects.append(claim.add_box_game(f"{name}.patch", patch_x, patch_z, ground + 0.72 * scale, (0.92 * scale, 1.15 * scale, 0.045), materials["iron"], yaw=yaw - 0.07, tilt=(0.0, -0.58), bevel=0.004))
    objects.append(claim.add_beam(f"{name}.leaningPole", (x + 1.65 * scale, game_z + 1.15 * scale, ground), (x + 1.25 * scale, game_z + 0.85 * scale, ground + 2.05 * scale), 0.08 * scale, materials["dark_timber"]))
    return objects


def make_rocket_cart(materials):
    objects = []
    x, game_z = 12.5, -8.5
    ground = float(claim.terrain_height(x, game_z))
    objects.append(claim.add_box_game("RenderHelperBaronRocketCart.body", x, game_z, ground + 0.45, (2.8, 1.6, 0.75), materials["iron"], yaw=-0.12))
    for index, (dx, dz) in enumerate([(-1.0, -0.85), (-1.0, 0.85), (1.0, -0.85), (1.0, 0.85)]):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=12,
            radius=0.48,
            depth=0.18,
            location=(x + dx, -(game_z + dz), ground + 0.48),
            rotation=(math.pi / 2.0, 0.0, 0.0),
        )
        wheel = bpy.context.object
        wheel.name = f"RenderHelperBaronRocketCart.wheel.{index}"
        wheel.data.materials.append(materials["dark_timber"])
        objects.append(wheel)
    for index, offset in enumerate((-0.48, 0.0, 0.48)):
        objects.append(
            claim.add_cylinder_between(
                f"RenderHelperBaronRocketCart.tube.{index}",
                (x - 0.75, game_z + offset, ground + 0.95),
                (x + 0.85, game_z + offset, ground + 2.55),
                0.14,
                materials["iron"],
                vertices=10,
            )
        )
    return objects


def make_siege_line(materials):
    objects = []
    posts = [-17.0, -13.0, -9.0, 9.0, 13.0, 17.0]
    game_z = -7.4
    for index, x in enumerate(posts):
        ground = float(claim.terrain_height(x, game_z))
        objects.append(claim.add_box_game(f"RenderHelperBaronSiegeLine.post.{index}", x, game_z, ground, (0.20, 0.20, 1.55), materials["dark_timber"], tilt=(0.0, 0.05 if index % 2 else -0.05)))
    for index, (start_x, end_x) in enumerate([(-17.0, -13.0), (-13.0, -9.0), (9.0, 13.0), (13.0, 17.0)]):
        objects.append(
            claim.add_beam(
                f"RenderHelperBaronSiegeLine.rail.{index}",
                (start_x, game_z, float(claim.terrain_height(start_x, game_z)) + 0.82),
                (end_x, game_z, float(claim.terrain_height(end_x, game_z)) + 0.76),
                0.15,
                materials["dark_timber"],
            )
        )
    return objects


def render_baron():
    terrain = bpy.data.objects.get("TheClaimTerrain")
    if terrain is None:
        raise RuntimeError("Open the Claim terrain .blend before rendering contract states")
    terrain_material = terrain.data.materials[0]
    materials = {
        "dark_timber": claim.make_render_material("BaronDarkTimber", (0.095, 0.040, 0.022)),
        "oxblood": claim.make_render_material("BaronOxbloodBanner", (0.31, 0.018, 0.020)),
        "enemy_canvas": claim.make_render_material("BaronEnemyCanvas", (0.13, 0.055, 0.035)),
        "iron": claim.make_render_material("BaronRocketIron", (0.11, 0.08, 0.06), 0.58, 0.50),
    }
    objects = []
    objects.extend(claim.make_claim_landmark_preview())
    objects.append(claim.make_water_surface(claim.make_water_material()))
    objects.extend(claim.make_ford_stones(terrain_material))
    objects.extend(make_banner("RenderHelperBaronBanner.center", 0.0, -8.0, materials))
    objects.extend(make_banner("RenderHelperBaronBanner.west", -19.0, -8.5, materials, yaw=0.12))
    objects.extend(make_banner("RenderHelperBaronBanner.east", 20.0, -8.5, materials, yaw=-0.10))
    objects.extend(make_enemy_tent("RenderHelperBaronCamp.west", -9.0, -10.0, 1.0, materials, yaw=0.12))
    objects.extend(make_enemy_tent("RenderHelperBaronCamp.east", 5.5, -11.0, 0.82, materials, yaw=-0.18))
    objects.extend(make_rocket_cart(materials))
    objects.extend(make_siege_line(materials))

    for index, (start_x, start_z, end_x, end_z) in enumerate([(-7.0, -10.0, -4.5, -8.5), (5.0, -11.0, 2.0, -9.0), (17.0, -15.0, 18.5, -12.0)]):
        objects.append(
            claim.add_beam(
                f"RenderHelperBaronWreckage.{index}",
                (start_x, start_z, float(claim.terrain_height(start_x, start_z)) + 0.12),
                (end_x, end_z, float(claim.terrain_height(end_x, end_z)) + 0.12),
                0.16,
                materials["dark_timber"],
            )
        )

    # Eevee's cascaded shadow map produces tile-sized black blocks when these
    # temporary tall banners sit at the far run-camera edge.
    for obj in objects:
        if obj.name.startswith("RenderHelperBaron") and hasattr(obj, "visible_shadow"):
            obj.visible_shadow = False

    backdrop = claim.make_backdrop()
    camera = claim.add_camera("BaronRunCamera", (0.0, -30.3, 26.26), (0.0, -8.65, 0.51), 42.0)
    lights = claim.add_lighting(sunset=False)
    claim.render(camera, ARTIFACTS / "baron-run-camera-siege.png")
    claim.remove_objects(lights + [camera, backdrop] + objects)


def main():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    state = args[0] if args else "twin-banks"
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    if state == "twin-banks":
        render_twin_banks()
    elif state == "night-shift":
        render_night_shift()
    elif state == "baron":
        render_baron()
    else:
        raise ValueError(f"unsupported contract state: {state}")


if __name__ == "__main__":
    main()
