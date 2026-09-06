from pathlib import Path
import hashlib
import json
import math

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REFERENCE = ROOT / "assets/raw/plate-e2-boss-component.png"
BLEND = OUT / "railcar.blend"
GLB = OUT / "railcar.glb"
ATLAS_SIZE = 1024
RAIL_GAUGE = 0.78
MODEL_LENGTH = 2.40

# A compact, plate-derived atlas: the large iron tile retains the source painting,
# while the remaining tiles derive their palette and engraving from the same plate.
REGIONS = {
    "dark": (0.02, 0.02, 0.23, 0.48),
    "brass": (0.27, 0.02, 0.48, 0.48),
    "teal": (0.52, 0.02, 0.73, 0.48),
    "soot": (0.77, 0.02, 0.98, 0.48),
    "iron": (0.02, 0.52, 0.48, 0.98),
    "edge": (0.52, 0.52, 0.73, 0.98),
    "glass": (0.77, 0.52, 0.86, 0.98),
    "damage": (0.89, 0.52, 0.98, 0.98),
}


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.length_unit = "METERS"


def region_pixels(region: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return tuple(int(value * ATLAS_SIZE) for value in region)


def sampled_color(colors: np.ndarray, mask: np.ndarray, fallback: tuple[float, float, float]) -> np.ndarray:
    selected = colors[mask]
    if len(selected) < 32:
        return np.array(fallback, dtype=np.float32)
    return np.clip(np.median(selected, axis=0), 0.02, 0.72)


def resized_nearest(source: np.ndarray, height: int, width: int) -> np.ndarray:
    ys = np.linspace(0, source.shape[0] - 1, height).astype(np.int32)
    xs = np.linspace(0, source.shape[1] - 1, width).astype(np.int32)
    return source[ys[:, None], xs[None, :]]


def create_atlas() -> tuple[bpy.types.Image, str]:
    source = bpy.data.images.load(str(REFERENCE), check_existing=False)
    pixels = np.array(source.pixels[:], dtype=np.float32).reshape(source.size[1], source.size[0], 4)
    colors = pixels[:, :, :3]
    luminance = colors.mean(axis=2)
    saturation = colors.max(axis=2) - colors.min(axis=2)
    sampled_dark = sampled_color(colors, (luminance > 0.025) & (luminance < 0.16), (0.055, 0.045, 0.035))
    sampled_brass = sampled_color(colors, (colors[:, :, 0] > colors[:, :, 1] * 1.08) & (colors[:, :, 1] > colors[:, :, 2] * 1.15) & (luminance > 0.16) & (luminance < 0.60), (0.34, 0.19, 0.065))
    sampled_edge = sampled_color(colors, (luminance > 0.13) & (luminance < 0.38) & (saturation > 0.08), (0.22, 0.13, 0.065))
    # Keep the concept plate's blackened-iron hierarchy. The former direct crop
    # admitted parchment/tan panels and made the boss read as a wooden toy.
    palette = {
        "dark": np.clip(sampled_dark * 0.82, 0.024, 0.13),
        "brass": np.clip(sampled_brass * 0.72 + sampled_dark * 0.16, 0.045, 0.40),
        "teal": np.array((0.025, 0.25, 0.27), dtype=np.float32),
        "soot": np.clip(sampled_dark * 0.42, 0.012, 0.065),
        "edge": np.clip(sampled_edge * 0.46 + sampled_dark * 0.48, 0.035, 0.24),
        "glass": np.array((0.020, 0.31, 0.34), dtype=np.float32),
        "damage": np.array((0.26, 0.042, 0.018), dtype=np.float32),
    }
    image = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    image[:, :, :3] = palette["dark"] * 0.65
    rng = np.random.default_rng(714)

    # Convert a real crop of the owner-approved locomotive into dark engraved
    # iron. The crop contributes its linework, not its parchment background.
    x0, y0, x1, y1 = region_pixels(REGIONS["iron"])
    intact_crop = colors[int(source.size[1] * 0.43):int(source.size[1] * 0.95), int(source.size[0] * 0.08):int(source.size[0] * 0.91)]
    painted = resized_nearest(resized_nearest(intact_crop, 240, 320), y1 - y0, x1 - x0)
    ink = 1.0 - np.clip((painted.mean(axis=2) - 0.06) / 0.52, 0.0, 1.0)
    iron_base = palette["edge"] * 0.62 + palette["dark"] * 0.38
    engraved = iron_base[None, None, :] * (0.96 - ink[:, :, None] * 0.52)
    engraved += rng.normal(0, 0.010, (y1 - y0, x1 - x0, 1))
    # Sparse warm flecks retain the plate's battered, hand-painted finish.
    warm = (painted[:, :, 0] > painted[:, :, 2] * 1.32) & (ink > 0.35)
    engraved[warm] = engraved[warm] * 0.72 + palette["brass"] * 0.20
    image[y0:y1, x0:x1, :3] = np.clip(engraved, 0.012, 0.32)

    for name, region in REGIONS.items():
        if name == "iron":
            continue
        x0, y0, x1, y1 = region_pixels(region)
        base = palette[name]
        noise = rng.normal(0, 0.012 if name != "glass" else 0.006, (y1 - y0, x1 - x0, 1))
        block = np.clip(base + noise, 0.015, 0.76)
        image[y0:y1, x0:x1, :3] = block
        if name in {"dark", "brass", "edge", "soot", "damage"}:
            height = y1 - y0
            for offset in range(-height, x1 - x0, 22):
                for yy in range(y0, y1):
                    xx = x0 + offset + (yy - y0)
                    if x0 <= xx < x1:
                        image[yy, xx:min(xx + 2, x1), :3] *= 0.64
        if name in {"brass", "edge"}:
            for yy in range(y0 + 18, y1, 38):
                for xx in range(x0 + 18, x1, 38):
                    image[yy - 3:yy + 4, xx - 3:xx + 4, :3] *= 0.44
        if name == "glass":
            for yy in range(y0 + 11, y1, 20):
                image[yy:yy + 2, x0:x1, :3] = np.clip(base * 1.38, 0, 0.78)

    atlas = bpy.data.images.new("ArmoredRailcarPlateAtlas", ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    atlas.colorspace_settings.name = "sRGB"
    atlas.pixels.foreach_set(image.ravel())
    atlas.pack()
    return atlas, hashlib.sha256(REFERENCE.read_bytes()).hexdigest()


def create_material(image: bpy.types.Image) -> bpy.types.Material:
    material = bpy.data.materials.new("ArmoredRailcarPlateMaterial")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Linear"
    texture.extension = "REPEAT"
    shader.inputs["Metallic"].default_value = 0.32
    shader.inputs["Roughness"].default_value = 0.66
    shader.inputs["Emission Color"].default_value = (0, 0, 0, 1)
    shader.inputs["Emission Strength"].default_value = 0
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def mark_all(obj: bpy.types.Object, group_name: str | None) -> None:
    if not group_name:
        return
    group = obj.vertex_groups.new(name=group_name)
    group.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")


def tag(obj: bpy.types.Object, region: str, material: bpy.types.Material, bevel: float = 0.008, damage_group: str | None = None, smooth: bool = False) -> bpy.types.Object:
    obj["atlas_region"] = region
    obj.data.materials.append(material)
    mark_all(obj, damage_group)
    if bevel > 0:
        modifier = obj.modifiers.new("Painted iron edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        modifier.limit_method = "ANGLE"
    if smooth:
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    return obj


def box(name: str, size: tuple[float, float, float], at: tuple[float, float, float], region: str, material: bpy.types.Material, bevel: float = 0.008, rotation: tuple[float, float, float] = (0, 0, 0), damage_group: str | None = None) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=at, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = tuple(value * 0.5 for value in size)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return tag(obj, region, material, bevel, damage_group)


def cylinder(name: str, radius: float, depth: float, at: tuple[float, float, float], region: str, material: bpy.types.Material, vertices: int = 12, rotation: tuple[float, float, float] = (0, 0, 0), bevel: float = 0.006, damage_group: str | None = None) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=at, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return tag(obj, region, material, bevel, damage_group, smooth=True)


def cone(name: str, radius1: float, radius2: float, depth: float, at: tuple[float, float, float], region: str, material: bpy.types.Material, vertices: int = 12, rotation: tuple[float, float, float] = (0, 0, 0), damage_group: str | None = None) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=at, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return tag(obj, region, material, 0.006, damage_group, smooth=True)


def torus(name: str, major_radius: float, minor_radius: float, at: tuple[float, float, float], region: str, material: bpy.types.Material, rotation: tuple[float, float, float] = (0, 0, 0), damage_group: str | None = None) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(major_segments=12, minor_segments=4, location=at, major_radius=major_radius, minor_radius=minor_radius, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return tag(obj, region, material, 0, damage_group, smooth=True)


def ico_sphere(name: str, radius: float, at: tuple[float, float, float], region: str, material: bpy.types.Material, damage_group: str) -> bpy.types.Object:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=radius, location=at)
    obj = bpy.context.object
    obj.name = name
    return tag(obj, region, material, 0, damage_group, smooth=True)


def subdivide(obj: bpy.types.Object, cuts: int = 2) -> bpy.types.Object:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.subdivide(number_cuts=cuts)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)
    return obj


def beam(name: str, start: tuple[float, float, float], end: tuple[float, float, float], width: float, region: str, material: bpy.types.Material, damage_group: str | None = None) -> bpy.types.Object:
    a, b = Vector(start), Vector(end)
    direction = b - a
    obj = box(name, (width, width, direction.length), tuple((a + b) * 0.5), region, material, bevel=min(0.006, width * 0.18), damage_group=damage_group)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    obj.select_set(False)
    return obj


def add_rivets(parts: list[bpy.types.Object], prefix: str, xs: tuple[float, ...], y: float, z: float, material: bpy.types.Material, group: str | None = None) -> None:
    side = 1 if y > 0 else -1
    for index, x in enumerate(xs):
        parts.append(cylinder(f"{prefix} rivet {index}", 0.026, 0.035, (x, y, z), "brass", material, vertices=8, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=group))


def build_wheels(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    parts.append(box("Black iron underframe", (2.12, 0.72, 0.20), (0.02, 0, 0.43), "dark", material, 0.016))
    parts.append(box("Left armored sill", (2.02, 0.10, 0.11), (0.02, -0.35, 0.51), "iron", material, 0.007))
    parts.append(box("Right armored sill", (2.02, 0.10, 0.11), (0.02, 0.35, 0.51), "iron", material, 0.007))
    parts.append(box("Front armor block", (0.16, 0.78, 0.24), (-0.87, 0, 0.49), "dark", material, 0.012))
    parts.append(box("Rear armored buffer", (0.14, 0.72, 0.18), (1.08, 0, 0.43), "iron", material, 0.008))
    parts.append(beam("Rear coupling", (1.08, 0, 0.35), (1.24, 0, 0.28), 0.075, "dark", material))

    wheel_xs = (-0.66, -0.20, 0.48, 0.84)
    wheel_radii = (0.245, 0.235, 0.185, 0.175)
    for axle, (x, radius) in enumerate(zip(wheel_xs, wheel_radii)):
        damage = "DamageBent" if axle == 0 else None
        center_z = radius + 0.025
        parts.append(cylinder(f"Axle {axle}", 0.050, 0.82, (x, 0, center_z), "dark", material, vertices=8, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=damage))
        for side in (-1, 1):
            y = side * 0.39
            parts.append(torus(f"Heavy wheel rim {axle} {side}", radius - 0.035, 0.043, (x, y, center_z), "edge", material, rotation=(math.pi / 2, 0, 0), damage_group=damage))
            parts.append(cylinder(f"Armored wheel hub {axle} {side}", 0.070, 0.080, (x, y, center_z), "brass", material, vertices=10, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=damage))
            parts.append(box(f"Suspension armor {axle} {side}", (0.15, 0.075, 0.20), (x, side * 0.39, 0.43), "iron", material, 0.006, damage_group=damage))
            for spoke in range(4):
                angle = math.radians(spoke * 45)
                reach = radius - 0.045
                dx, dz = math.cos(angle) * reach, math.sin(angle) * reach
                parts.append(beam(f"Wheel spoke {axle} {side} {spoke}", (x - dx, y, center_z - dz), (x + dx, y, center_z + dz), 0.026, "edge", material, damage))
    for side in (-1, 1):
        y = side * 0.445
        parts.append(beam(f"Main drive rod {side}", (-0.69, y, 0.22), (0.89, y, 0.27), 0.052, "brass", material, "DamageBent"))
        parts.append(beam(f"Upper suspension rail {side}", (-0.75, y, 0.45), (0.96, y, 0.45), 0.040, "edge", material, "DamageBent"))

    # Deep armored wedge: the reference's most important boss silhouette cue.
    tine_ys = (-0.56, -0.38, -0.19, 0.0, 0.19, 0.38, 0.56)
    for index, y in enumerate(tine_ys):
        parts.append(beam(f"Cowcatcher blade {index}", (-0.83, y * 0.50, 0.54), (-1.38, y, 0.10), 0.058, "edge", material))
    parts.append(beam("Cowcatcher cutting edge", (-1.38, -0.58, 0.10), (-1.38, 0.58, 0.10), 0.070, "dark", material))
    parts.append(beam("Cowcatcher armored brow", (-0.84, -0.34, 0.55), (-0.84, 0.34, 0.55), 0.075, "iron", material))
    parts.append(beam("Cowcatcher left cheek", (-0.84, -0.34, 0.55), (-1.38, -0.58, 0.10), 0.082, "dark", material))
    parts.append(beam("Cowcatcher right cheek", (-0.84, 0.34, 0.55), (-1.38, 0.58, 0.10), 0.082, "dark", material))
    parts.append(beam("Cowcatcher central armored ram", (-0.83, 0, 0.57), (-1.38, 0, 0.12), 0.14, "iron", material))
    parts.append(beam("Cowcatcher left ram brace", (-0.87, -0.29, 0.51), (-1.34, -0.16, 0.15), 0.085, "brass", material))
    parts.append(beam("Cowcatcher right ram brace", (-0.87, 0.29, 0.51), (-1.34, 0.16, 0.15), 0.085, "brass", material))
    parts.append(box("Cowcatcher left armored blade", (0.66, 0.16, 0.16), (-1.11, -0.31, 0.33), "iron", material, 0.008, rotation=(0, math.radians(-39), 0)))
    parts.append(box("Cowcatcher right armored blade", (0.66, 0.16, 0.16), (-1.11, 0.31, 0.33), "iron", material, 0.008, rotation=(0, math.radians(-39), 0)))
    for x, scale in ((-1.20, 0.82), (-1.03, 0.62)):
        parts.append(beam(f"Cowcatcher cross rail {x}", (x, -0.58 * scale, 0.24 + (x + 1.20) * 0.60), (x, 0.58 * scale, 0.24 + (x + 1.20) * 0.60), 0.045, "brass", material))
    add_rivets(parts, "Left frame", (-0.72, -0.42, -0.12, 0.18, 0.48, 0.78), -0.475, 0.51, material)
    add_rivets(parts, "Right frame", (-0.72, -0.42, -0.12, 0.18, 0.48, 0.78), 0.475, 0.51, material)
    return parts


def build_boiler(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    parts.append(cylinder("Blackened riveted boiler", 0.275, 1.48, (-0.06, 0, 0.70), "iron", material, vertices=16, rotation=(0, math.pi / 2, 0), bevel=0))
    parts.append(box("Armored smokebox shroud", (0.17, 0.62, 0.58), (-0.88, 0, 0.70), "dark", material, 0.018))
    parts.append(cylinder("Smokebox face", 0.285, 0.07, (-0.98, 0, 0.70), "soot", material, vertices=16, rotation=(0, math.pi / 2, 0), bevel=0))
    parts.append(torus("Smokebox armored ring", 0.248, 0.032, (-1.02, 0, 0.70), "brass", material, rotation=(0, math.pi / 2, 0)))
    parts.append(cylinder("Prow eye collar", 0.112, 0.032, (-1.028, 0, 0.70), "brass", material, vertices=12, rotation=(0, math.pi / 2, 0), bevel=0))
    parts.append(cylinder("Teal prow eye", 0.070, 0.044, (-1.06, 0, 0.70), "teal", material, vertices=12, rotation=(0, math.pi / 2, 0), bevel=0))
    for index in range(10):
        angle = math.radians(index * 36)
        parts.append(cylinder(f"Smokebox face rivet {index}", 0.021, 0.025, (-1.045, math.cos(angle) * 0.218, 0.70 + math.sin(angle) * 0.218), "brass", material, vertices=8, rotation=(0, math.pi / 2, 0), bevel=0))
    for index, x in enumerate((-0.74, -0.47, -0.18, 0.11, 0.42)):
        parts.append(torus(f"Boiler armor band {index}", 0.277, 0.024, (x, 0, 0.70), "brass", material, rotation=(0, math.pi / 2, 0), damage_group="DamageVent" if index == 4 else None))
    # Tall, flanged stack and squat pressure domes match the concept rather than
    # a friendly toy-locomotive profile.
    parts.append(cylinder("Stack throat", 0.090, 0.20, (-0.62, 0, 1.00), "dark", material, vertices=12))
    parts.append(torus("Stack lower flange", 0.105, 0.022, (-0.62, 0, 1.04), "brass", material))
    parts.append(cone("Stack flare", 0.132, 0.100, 0.12, (-0.62, 0, 1.13), "edge", material, vertices=12))
    parts.append(torus("Stack crown", 0.118, 0.024, (-0.62, 0, 1.195), "brass", material))
    parts.append(cylinder("Steam dome", 0.088, 0.14, (-0.12, 0, 0.99), "brass", material, vertices=12))
    parts.append(cone("Steam dome crown", 0.100, 0.055, 0.07, (-0.12, 0, 1.075), "brass", material, vertices=12))
    parts.append(cylinder("Rear pressure dome", 0.065, 0.12, (0.33, 0, 0.975), "edge", material, vertices=10))
    parts.append(cone("Rear pressure cap", 0.078, 0.042, 0.06, (0.33, 0, 1.055), "brass", material, vertices=10))
    parts.append(box("Boiler armored spine", (1.18, 0.14, 0.07), (-0.06, 0, 0.965), "dark", material, 0.008))
    parts.append(cylinder("Safety valve left", 0.038, 0.14, (0.47, -0.11, 0.97), "brass", material, vertices=8, damage_group="DamageVent"))
    parts.append(cylinder("Safety valve right", 0.038, 0.14, (0.47, 0.11, 0.97), "brass", material, vertices=8, damage_group="DamageVent"))
    parts.append(box("Left rupture hatch", (0.24, 0.045, 0.13), (0.42, -0.25, 0.84), "damage", material, 0.004, damage_group="DamageVent"))
    parts.append(box("Right rupture hatch", (0.24, 0.045, 0.13), (0.42, 0.25, 0.84), "damage", material, 0.004, damage_group="DamageVent"))
    parts.append(box("Hidden left boiler rupture", (0.20, 0.025, 0.10), (0.42, -0.23, 0.84), "soot", material, 0, damage_group="DamageVentHole"))
    parts.append(box("Hidden right boiler rupture", (0.20, 0.025, 0.10), (0.42, 0.23, 0.84), "soot", material, 0, damage_group="DamageVentHole"))
    parts.append(ico_sphere("Hidden steam puff small", 0.065, (0.37, 0, 0.74), "glass", material, "DamageSteamSmall"))
    parts.append(ico_sphere("Hidden steam puff medium", 0.085, (0.29, 0, 0.72), "glass", material, "DamageSteamMedium"))
    parts.append(ico_sphere("Hidden steam puff large", 0.105, (0.21, 0, 0.70), "glass", material, "DamageSteamLarge"))
    for side in (-1, 1):
        y = side * 0.305
        parts.append(box(f"Boiler flank armor {side}", (1.18, 0.055, 0.16), (-0.08, side * 0.28, 0.62), "dark", material, 0.008))
        parts.append(beam(f"Boiler lower pipe {side}", (-0.78, side * 0.32, 0.54), (0.58, side * 0.32, 0.52), 0.042, "brass", material))
        parts.append(beam(f"Boiler upper pipe {side}", (-0.54, side * 0.31, 0.84), (0.54, side * 0.31, 0.81), 0.030, "edge", material))
        for gauge, (x, z, radius) in enumerate(((-0.42, 0.74, 0.065), (-0.16, 0.64, 0.050), (0.14, 0.79, 0.058))):
            parts.append(torus(f"Gauge collar {side} {gauge}", radius, 0.016, (x, side * 0.326, z), "brass", material, rotation=(math.pi / 2, 0, 0)))
            parts.append(cylinder(f"Teal gauge {side} {gauge}", radius * 0.70, 0.020, (x, side * 0.342, z), "teal", material, vertices=10, rotation=(math.pi / 2, 0, 0), bevel=0))
        add_rivets(parts, f"Boiler {side}", (-0.76, -0.59, -0.42, -0.25, -0.08, 0.09, 0.26, 0.43, 0.58), side * 0.325, 0.54, material)
    return parts


def build_cabin(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    parts.append(box("Cab black armored base", (0.68, 0.78, 0.36), (0.88, 0, 0.62), "iron", material, 0.012))
    parts.append(box("Cab far riveted wall", (0.60, 0.06, 0.42), (0.88, -0.37, 0.84), "dark", material, 0.010))
    parts.append(subdivide(box("Cab near caving wall", (0.60, 0.06, 0.42), (0.88, 0.37, 0.84), "dark", material, 0.008, damage_group="DamageCabWall"), 2))
    parts.append(box("Cab front bulkhead", (0.07, 0.70, 0.43), (0.55, 0, 0.84), "iron", material, 0.010))
    parts.append(box("Cab rear bulkhead", (0.08, 0.70, 0.45), (1.20, 0, 0.83), "iron", material, 0.010, damage_group="DamageDent"))
    # Two sloped roof plates create the armored bunker silhouette in the plate.
    parts.append(box("Cab roof left slope", (0.70, 0.48, 0.09), (0.88, -0.205, 1.075), "dark", material, 0.012, rotation=(math.radians(-16), 0, 0), damage_group="DamageCabRoof"))
    parts.append(box("Cab roof right slope", (0.70, 0.48, 0.09), (0.88, 0.205, 1.075), "dark", material, 0.012, rotation=(math.radians(16), 0, 0), damage_group="DamageCabRoof"))
    parts.append(box("Cab roof crown", (0.70, 0.22, 0.070), (0.88, 0, 1.105), "edge", material, 0.008, damage_group="DamageCabRoof"))
    for index, x in enumerate((0.60, 0.79, 0.98, 1.17)):
        parts.append(box(f"Cab roof rib {index}", (0.035, 0.82, 0.028), (x, 0, 1.135), "brass", material, 0.003, damage_group="DamageDent" if index >= 2 else None))
    # Low roof guard echoes the plate without reading as a cargo rack.
    for side in (-1, 1):
        parts.append(beam(f"Roof guard long {side}", (0.62, side * 0.30, 1.175), (1.15, side * 0.30, 1.175), 0.028, "brass", material, "DamageDent" if side > 0 else None))
        for x in (0.63, 1.14):
            parts.append(beam(f"Roof guard post {side} {x}", (x, side * 0.30, 1.13), (x, side * 0.30, 1.175), 0.026, "edge", material, "DamageDent" if side > 0 else None))
    parts.append(beam("Roof guard front", (0.62, -0.30, 1.175), (0.62, 0.30, 1.175), 0.028, "brass", material))
    parts.append(beam("Roof guard rear", (1.15, -0.30, 1.175), (1.15, 0.30, 1.175), 0.028, "brass", material, "DamageDent"))
    parts.append(box("Rear armor plate", (0.10, 0.72, 0.56), (1.23, 0, 0.75), "dark", material, 0.01, damage_group="DamageDent"))
    for side in (-1, 1):
        y = side * 0.392
        damage = "DamageDent" if side > 0 else None
        parts.append(box(f"Cab narrow window {side}", (0.36, 0.025, 0.13), (0.88, y, 0.91), "glass", material, 0.004, damage_group=damage))
        parts.append(box(f"Cab window top guard {side}", (0.45, 0.035, 0.050), (0.88, side * 0.414, 0.995), "brass", material, 0.004, damage_group=damage))
        parts.append(box(f"Cab window lower guard {side}", (0.45, 0.035, 0.050), (0.88, side * 0.414, 0.825), "brass", material, 0.004, damage_group=damage))
        parts.append(box(f"Cab window vertical bar {side}", (0.050, 0.035, 0.20), (0.88, side * 0.418, 0.91), "edge", material, 0.004, damage_group=damage))
        parts.append(box(f"Cab corner brace front {side}", (0.060, 0.045, 0.44), (0.60, side * 0.414, 0.84), "brass", material, 0.004, damage_group=damage))
        parts.append(box(f"Cab corner brace rear {side}", (0.060, 0.045, 0.44), (1.16, side * 0.414, 0.84), "brass", material, 0.004, damage_group=damage))
        # Faceted outer plates turn the cabin from an upright box into an armored bunker.
        parts.append(box(f"Cab forward cheek plate {side}", (0.28, 0.045, 0.24), (0.70, side * 0.404, 0.71), "iron", material, 0.005, rotation=(0, math.radians(-12), 0), damage_group=damage))
        parts.append(box(f"Cab rear cheek plate {side}", (0.28, 0.045, 0.24), (1.06, side * 0.404, 0.71), "iron", material, 0.005, rotation=(0, math.radians(12), 0), damage_group=damage))
        add_rivets(parts, f"Cab {side}", (0.62, 0.75, 0.88, 1.01, 1.14), side * 0.425, 0.62, material, damage)
        # Crack strips live inside the wall in the intact Basis and emerge only in the morph.
        crack_segments = (
            ((0.68, 0.99), (0.87, 0.79)),
            ((0.69, 0.81), (0.90, 1.00)),
            ((0.84, 0.81), (1.02, 0.74)),
        )
        for crack, ((x_start, z_start), (x_end, z_end)) in enumerate(crack_segments):
            parts.append(beam(f"Hidden crack {side} {crack}", (x_start, side * 0.25, z_start), (x_end, side * 0.25, z_end), 0.018, "soot", material, "DamageCracks"))
    parts.append(box("Hidden cabin rupture void", (0.42, 0.025, 0.25), (0.88, 0.18, 0.86), "soot", material, 0, damage_group="DamageCabVoid"))
    parts.append(box("Rear teal firing slit", (0.025, 0.34, 0.12), (1.285, 0, 0.88), "teal", material, 0.004, damage_group="DamageDent"))
    parts.append(beam("Cab rear ladder left", (1.28, -0.31, 0.44), (1.28, -0.31, 0.76), 0.034, "brass", material))
    parts.append(beam("Cab rear ladder right", (1.28, 0.31, 0.44), (1.28, 0.31, 0.76), 0.034, "brass", material))
    for z in (0.50, 0.62, 0.74):
        parts.append(beam(f"Cab ladder rung {z}", (1.28, -0.31, z), (1.28, 0.31, z), 0.03, "brass", material))
    return parts


def prepare_part(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    for modifier in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.025)
    bpy.ops.object.mode_set(mode="OBJECT")
    uv = obj.data.uv_layers.active.data
    coords = np.array([[loop.uv.x, loop.uv.y] for loop in uv], dtype=np.float32)
    low = coords.min(axis=0)
    span = np.maximum(coords.max(axis=0) - low, 1e-6)
    u0, v0, u1, v1 = REGIONS[obj["atlas_region"]]
    for loop, coord in zip(uv, coords):
        normalized = (coord - low) / span
        loop.uv = (u0 + normalized[0] * (u1 - u0), v0 + normalized[1] * (v1 - v0))
    obj.select_set(False)


def join_component(name: str, parts: list[bpy.types.Object], material: bpy.types.Material) -> bpy.types.Object:
    for part in parts:
        prepare_part(part)
    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    component = bpy.context.object
    component.name = name
    component.data.name = f"{name}Mesh"
    component.data.materials.clear()
    component.data.materials.append(material)
    for polygon in component.data.polygons:
        polygon.material_index = 0
    component.data.uv_layers.active.name = "UVMap"
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    component.select_set(False)
    return component


def group_vertex_indices(obj: bpy.types.Object, group_name: str) -> set[int]:
    group = obj.vertex_groups.get(group_name)
    if group is None:
        return set()
    index = group.index
    return {vertex.index for vertex in obj.data.vertices if any(item.group == index for item in vertex.groups)}


def add_damage_shapes(wheels: bpy.types.Object, boiler: bpy.types.Object, cabin: bpy.types.Object) -> None:
    wheels.shape_key_add(name="Basis")
    bent = wheels.shape_key_add(name="Damage_BentWheels")
    marked = group_vertex_indices(wheels, "DamageBent")
    for index in marked:
        co = bent.data[index].co
        side = 1 if co.y >= 0 else -1
        center = Vector((-0.66, side * 0.39, 0.27))
        local = co - center
        angle = math.radians(42 * side)
        new_y = local.y * math.cos(angle) - local.z * math.sin(angle)
        new_z = local.y * math.sin(angle) + local.z * math.cos(angle)
        co.y = center.y + new_y + side * 0.11
        co.x += (co.z - center.z) * 0.16
        derail_lift = max(0.0, min(1.0, (-co.x - 0.12) / 0.62)) * (0.25 if side > 0 else 0.10)
        co.x -= derail_lift * 0.45
        co.z = max(0.0, center.z + new_z + derail_lift)

    boiler.shape_key_add(name="Basis")
    venting = boiler.shape_key_add(name="Damage_VentingBoiler")
    marked = group_vertex_indices(boiler, "DamageVent")
    for index in marked:
        co = venting.data[index].co
        side = 1 if co.y >= 0 else -1
        co.y += side * 0.20
        co.z += 0.18 + max(0.0, co.x - 0.08) * 0.24
        co.x += side * 0.025
    for index in group_vertex_indices(boiler, "DamageVentHole"):
        co = venting.data[index].co
        co.y += (1 if co.y >= 0 else -1) * 0.085
    steam_moves = {
        "DamageSteamSmall": Vector((0.08, 0.43, 0.43)),
        "DamageSteamMedium": Vector((0.12, 0.48, 0.61)),
        "DamageSteamLarge": Vector((0.18, 0.50, 0.80)),
    }
    for group_name, movement in steam_moves.items():
        for index in group_vertex_indices(boiler, group_name):
            venting.data[index].co += movement

    cabin.shape_key_add(name="Basis")
    cracked = cabin.shape_key_add(name="Damage_CrackedCabin")
    cracks = group_vertex_indices(cabin, "DamageCracks")
    dents = group_vertex_indices(cabin, "DamageDent")
    caving_wall = group_vertex_indices(cabin, "DamageCabWall")
    caving_roof = group_vertex_indices(cabin, "DamageCabRoof")
    for index in cracks:
        co = cracked.data[index].co
        co.y += (1 if co.y >= 0 else -1) * 0.18
    for index in dents:
        co = cracked.data[index].co
        co.x -= 0.085 + max(0.0, co.z - 0.82) * 0.10
        co.z -= 0.035 + max(0.0, co.x - 0.60) * 0.13
        if co.y > 0:
            co.y -= 0.065
    for index in caving_wall:
        co = cracked.data[index].co
        u = (co.x - 0.88) / 0.30
        v = (co.z - 0.84) / 0.21
        influence = max(0.0, 1.0 - min(1.0, math.sqrt(u * u + v * v)))
        co.y -= 0.19 * influence
        co.x -= 0.045 * influence
        co.z -= 0.055 * influence
    for index in group_vertex_indices(cabin, "DamageCabVoid"):
        cracked.data[index].co.y += 0.23
    for index in caving_roof:
        co = cracked.data[index].co
        near = max(0.0, min(1.0, (co.y + 0.02) / 0.46))
        rear = max(0.0, min(1.0, (co.x - 0.45) / 0.72))
        collapse = near * (0.45 + rear * 0.55)
        co.y -= 0.08 * collapse
        co.x -= 0.045 * collapse
        co.z -= 0.18 * collapse

    for obj in (wheels, boiler, cabin):
        obj.active_shape_key_index = 0
        for key in obj.data.shape_keys.key_blocks:
            key.value = 0.0


def triangle_count(objects: tuple[bpy.types.Object, ...]) -> int:
    return sum(sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons) for obj in objects)


def world_bounds(objects: tuple[bpy.types.Object, ...]) -> tuple[Vector, Vector]:
    points = [obj.matrix_world @ vertex.co for obj in objects for vertex in obj.data.vertices]
    return Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points))), Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))


def normalize_base_center(objects: tuple[bpy.types.Object, ...]) -> None:
    minimum, maximum = world_bounds(objects)
    center_x = (minimum.x + maximum.x) * 0.5
    center_y = (minimum.y + maximum.y) * 0.5
    scale_x = MODEL_LENGTH / (maximum.x - minimum.x)
    for obj in objects:
        for vertex in obj.data.vertices:
            vertex.co.x = (vertex.co.x - center_x) * scale_x
            vertex.co.y -= center_y
            vertex.co.z -= minimum.z
        obj.data.update()


def export(objects: tuple[bpy.types.Object, ...]) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.export_scene.gltf(
        filepath=str(GLB.with_suffix("")),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_materials="EXPORT",
        export_morph=True,
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    reset_scene()
    atlas, source_sha = create_atlas()
    material = create_material(atlas)
    wheels = join_component("Railcar_Wheels", build_wheels(material), material)
    boiler = join_component("Railcar_Boiler", build_boiler(material), material)
    cabin = join_component("Railcar_Cabin", build_cabin(material), material)
    objects = (wheels, boiler, cabin)
    normalize_base_center(objects)
    add_damage_shapes(*objects)

    minimum, maximum = world_bounds(objects)
    tris = triangle_count(objects)
    assert tris <= 12_000, f"triangle budget exceeded: {tris}"
    assert abs((maximum.x - minimum.x) - MODEL_LENGTH) < 0.01, f"length bounds {minimum.x:.4f}..{maximum.x:.4f}"
    assert abs((maximum.x + minimum.x) * 0.5) < 0.001
    assert abs((maximum.y + minimum.y) * 0.5) < 0.001
    assert abs(minimum.z) < 0.001
    assert len({slot.material.name for obj in objects for slot in obj.material_slots if slot.material}) == 1
    export(objects)
    print(json.dumps({
        "blend": str(BLEND),
        "glb": str(GLB),
        "sha256": hashlib.sha256(GLB.read_bytes()).hexdigest(),
        "sourcePlateSha256": source_sha,
        "objects": [obj.name for obj in objects],
        "damageMorphs": [obj.data.shape_keys.key_blocks[1].name for obj in objects],
        "triangles": tris,
        "boundsBlender": {"min": [round(value, 6) for value in minimum], "max": [round(value, 6) for value in maximum]},
        "lengthGaugeRatio": round((maximum.x - minimum.x) / RAIL_GAUGE, 4),
    }, indent=2))


if __name__ == "__main__":
    main()
