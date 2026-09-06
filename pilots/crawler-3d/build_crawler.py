from pathlib import Path
import hashlib
import json
import math

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REFERENCE = ROOT / "assets/raw/plate-e3-boss-dynamo-crawler.png"
BLEND = OUT / "crawler.blend"
GLB = OUT / "crawler.glb"
ATLAS_SIZE = 1024
MODEL_LENGTH = 3.20

REGIONS = {
    "soot": (0.02, 0.02, 0.23, 0.48),
    "iron": (0.27, 0.02, 0.48, 0.48),
    "brass": (0.52, 0.02, 0.73, 0.48),
    "copper": (0.77, 0.02, 0.98, 0.48),
    "plate": (0.02, 0.52, 0.48, 0.98),
    "teal": (0.52, 0.52, 0.73, 0.98),
    "ceramic": (0.77, 0.52, 0.86, 0.98),
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
    return np.clip(np.median(selected, axis=0), 0.01, 0.82)


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
    dark = sampled_color(colors, (luminance > 0.02) & (luminance < 0.15), (0.045, 0.035, 0.025))
    warm = sampled_color(
        colors,
        (colors[:, :, 0] > colors[:, :, 1] * 1.08)
        & (colors[:, :, 1] > colors[:, :, 2] * 1.15)
        & (luminance > 0.13)
        & (luminance < 0.55),
        (0.31, 0.16, 0.045),
    )
    edge = sampled_color(colors, (luminance > 0.11) & (luminance < 0.34) & (saturation > 0.07), (0.18, 0.10, 0.04))
    palette = {
        "soot": np.clip(dark * 0.40, 0.010, 0.060),
        "iron": np.clip(dark * 0.42 + edge * 0.58 + 0.024, 0.050, 0.26),
        "brass": np.clip(warm * 0.86 + dark * 0.08, 0.080, 0.52),
        "copper": np.array((0.48, 0.15, 0.032), dtype=np.float32),
        "teal": np.array((0.018, 0.39, 0.41), dtype=np.float32),
        "ceramic": np.array((0.55, 0.40, 0.20), dtype=np.float32),
        "damage": np.array((0.48, 0.060, 0.010), dtype=np.float32),
    }
    atlas = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    atlas[:, :, :3] = palette["soot"]
    rng = np.random.default_rng(715)

    # The large plate tile carries actual line density from the approved Crawler
    # painting; the other regions derive its palette and engraved scratch rhythm.
    x0, y0, x1, y1 = region_pixels(REGIONS["plate"])
    crop = colors[int(source.size[1] * 0.20):int(source.size[1] * 0.92), int(source.size[0] * 0.17):int(source.size[0] * 0.78)]
    painted = resized_nearest(resized_nearest(crop, 260, 360), y1 - y0, x1 - x0)
    ink = 1.0 - np.clip((painted.mean(axis=2) - 0.055) / 0.55, 0.0, 1.0)
    plate_base = palette["iron"] * 0.82 + palette["brass"] * 0.18
    engraved = plate_base[None, None, :] * (1.08 - ink[:, :, None] * 0.48)
    warm_mask = (painted[:, :, 0] > painted[:, :, 2] * 1.30) & (ink > 0.26)
    engraved[warm_mask] = engraved[warm_mask] * 0.78 + palette["copper"] * 0.15
    engraved += rng.normal(0, 0.009, (y1 - y0, x1 - x0, 1))
    atlas[y0:y1, x0:x1, :3] = np.clip(engraved, 0.010, 0.31)

    for name, region in REGIONS.items():
        if name == "plate":
            continue
        x0, y0, x1, y1 = region_pixels(region)
        base = palette[name]
        noise = rng.normal(0, 0.010 if name != "teal" else 0.005, (y1 - y0, x1 - x0, 1))
        block = np.clip(base + noise, 0.010, 0.76)
        atlas[y0:y1, x0:x1, :3] = block
        if name in {"soot", "iron", "brass", "copper", "ceramic", "damage"}:
            height = y1 - y0
            for offset in range(-height, x1 - x0, 19):
                for yy in range(y0, y1):
                    xx = x0 + offset + (yy - y0)
                    if x0 <= xx < x1:
                        atlas[yy, xx:min(xx + 2, x1), :3] *= 0.57
        if name in {"brass", "copper", "iron"}:
            for yy in range(y0 + 15, y1, 34):
                for xx in range(x0 + 15, x1, 34):
                    atlas[yy - 3:yy + 4, xx - 3:xx + 4, :3] *= 0.43
        if name == "teal":
            for yy in range(y0 + 8, y1, 18):
                atlas[yy:yy + 2, x0:x1, :3] = np.clip(base * 1.45, 0, 0.80)

    image = bpy.data.images.new("RivalDynamoCrawlerAtlas", ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(atlas.ravel())
    image.pack()
    return image, hashlib.sha256(REFERENCE.read_bytes()).hexdigest()


def create_material(image: bpy.types.Image) -> bpy.types.Material:
    material = bpy.data.materials.new("RivalDynamoCrawlerMaterial")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Linear"
    texture.extension = "REPEAT"
    shader.inputs["Metallic"].default_value = 0.18
    shader.inputs["Roughness"].default_value = 0.82
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


def tag(
    obj: bpy.types.Object,
    region: str,
    material: bpy.types.Material,
    bevel: float = 0.008,
    damage_group: str | None = None,
    smooth: bool = False,
) -> bpy.types.Object:
    obj["atlas_region"] = region
    obj.data.materials.append(material)
    mark_all(obj, damage_group)
    if bevel > 0:
        modifier = obj.modifiers.new("Battered edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        modifier.limit_method = "ANGLE"
    if smooth:
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    return obj


def box(
    name: str,
    size: tuple[float, float, float],
    at: tuple[float, float, float],
    region: str,
    material: bpy.types.Material,
    bevel: float = 0.008,
    rotation: tuple[float, float, float] = (0, 0, 0),
    damage_group: str | None = None,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=at, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = tuple(value * 0.5 for value in size)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return tag(obj, region, material, bevel, damage_group)


def cylinder(
    name: str,
    radius: float,
    depth: float,
    at: tuple[float, float, float],
    region: str,
    material: bpy.types.Material,
    vertices: int = 12,
    rotation: tuple[float, float, float] = (0, 0, 0),
    bevel: float = 0.006,
    damage_group: str | None = None,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=at, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return tag(obj, region, material, bevel, damage_group, smooth=True)


def cone(
    name: str,
    radius1: float,
    radius2: float,
    depth: float,
    at: tuple[float, float, float],
    region: str,
    material: bpy.types.Material,
    vertices: int = 12,
    rotation: tuple[float, float, float] = (0, 0, 0),
    damage_group: str | None = None,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices,
        radius1=radius1,
        radius2=radius2,
        depth=depth,
        location=at,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return tag(obj, region, material, 0.006, damage_group, smooth=True)


def torus(
    name: str,
    major_radius: float,
    minor_radius: float,
    at: tuple[float, float, float],
    region: str,
    material: bpy.types.Material,
    rotation: tuple[float, float, float] = (0, 0, 0),
    damage_group: str | None = None,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(
        major_segments=8,
        minor_segments=3,
        location=at,
        major_radius=major_radius,
        minor_radius=minor_radius,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return tag(obj, region, material, 0, damage_group, smooth=True)


def ico_sphere(
    name: str,
    radius: float,
    at: tuple[float, float, float],
    region: str,
    material: bpy.types.Material,
    damage_group: str | None = None,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=radius, location=at)
    obj = bpy.context.object
    obj.name = name
    return tag(obj, region, material, 0, damage_group, smooth=True)


def beam(
    name: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    width: float,
    region: str,
    material: bpy.types.Material,
    damage_group: str | None = None,
) -> bpy.types.Object:
    a, b = Vector(start), Vector(end)
    direction = b - a
    obj = box(
        name,
        (width, width, direction.length),
        tuple((a + b) * 0.5),
        region,
        material,
        bevel=min(0.006, width * 0.18),
        damage_group=damage_group,
    )
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    obj.select_set(False)
    return obj


def add_rivets(
    parts: list[bpy.types.Object],
    prefix: str,
    xs: tuple[float, ...],
    y: float,
    z: float,
    material: bpy.types.Material,
    group: str | None = None,
) -> None:
    for index, x in enumerate(xs):
        parts.append(
            cylinder(
                f"{prefix} rivet {index}",
                0.025,
                0.035,
                (x, y, z),
                "brass",
                material,
                vertices=8,
                rotation=(math.pi / 2, 0, 0),
                bevel=0,
                damage_group=group,
            )
        )


def build_tracks(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    parts.append(box("Crawler armored underframe", (2.98, 1.02, 0.36), (0.03, 0, 0.49), "soot", material, 0.015))
    parts.append(box("Crawler deck", (2.72, 0.96, 0.22), (0.05, 0, 0.70), "plate", material, 0.012))
    parts.append(box("Forward ram block", (0.34, 1.05, 0.42), (-1.35, 0, 0.50), "iron", material, 0.016))
    parts.append(box("Rear draw block", (0.28, 1.00, 0.34), (1.38, 0, 0.48), "iron", material, 0.012))

    wheel_xs = (-1.12, -0.56, 0.02, 0.60, 1.14)
    wheel_radii = (0.31, 0.34, 0.34, 0.32, 0.27)
    for side in (-1, 1):
        y = side * 0.56
        near_group = "DamageTrackNear" if side > 0 else None
        skirt_group = "DamageTrackSkirt" if side > 0 else None
        # Low, riveted skirts give the boss a continuous armored hull while
        # retaining a strip of wheel rhythm above and below.  They remain part
        # of the track damage morph on the readable side.
        parts.append(
            box(
                f"Track armored skirt {side}",
                (2.48, 0.10, 0.32),
                (0.02, side * 0.625, 0.40),
                "plate",
                material,
                0,
                damage_group=skirt_group,
            )
        )
        for strap, x in enumerate((-0.88, -0.30, 0.28, 0.86)):
            parts.append(
                box(
                    f"Track skirt strap {side} {strap}",
                    (0.065, 0.125, 0.34),
                    (x, side * 0.632, 0.40),
                    "brass",
                    material,
                    0,
                    damage_group=skirt_group,
                )
            )
        parts.append(box(f"Track belt top {side}", (2.58, 0.14, 0.13), (0.02, y, 0.60), "iron", material, 0.004, damage_group=near_group))
        parts.append(box(f"Track belt bottom {side}", (2.60, 0.14, 0.13), (0.00, y, 0.11), "iron", material, 0.004, damage_group=near_group))
        parts.append(box(f"Track belt prow slope {side}", (0.52, 0.14, 0.13), (-1.27, y, 0.35), "iron", material, 0.004, rotation=(0, math.radians(-62), 0), damage_group=near_group))
        parts.append(box(f"Track belt stern slope {side}", (0.43, 0.14, 0.13), (1.29, y, 0.33), "iron", material, 0.004, rotation=(0, math.radians(64), 0), damage_group=near_group))
        for axle, (x, radius) in enumerate(zip(wheel_xs, wheel_radii)):
            group = near_group if side > 0 and axle <= 2 else None
            parts.append(torus(f"Track drive rim {side} {axle}", radius - 0.045, 0.045, (x, y, radius + 0.04), "plate", material, rotation=(math.pi / 2, 0, 0), damage_group=group))
            parts.append(cylinder(f"Track hub {side} {axle}", 0.075, 0.075, (x, y, radius + 0.04), "brass", material, vertices=10, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=group))
            for spoke in range(2):
                angle = math.radians(spoke * 90)
                reach = radius - 0.075
                dx, dz = math.cos(angle) * reach, math.sin(angle) * reach
                parts.append(beam(f"Track spoke {side} {axle} {spoke}", (x - dx, y, radius + 0.04 - dz), (x + dx, y, radius + 0.04 + dz), 0.030, "brass", material, group))
        # Forty tread shoes are enough to read as a continuous belt at the run camera.
        for tread, x in enumerate(np.linspace(-1.20, 1.20, 14)):
            group = near_group if side > 0 and tread < 8 else None
            parts.append(box(f"Top tread shoe {side} {tread}", (0.14, 0.22, 0.055), (float(x), y, 0.69), "plate", material, 0.002, damage_group=group))
            parts.append(box(f"Bottom tread shoe {side} {tread}", (0.14, 0.22, 0.055), (float(x), y, 0.025), "plate", material, 0.002, damage_group=group))
        add_rivets(parts, f"Track frame {side}", (-1.16, -0.86, -0.56, -0.26, 0.04, 0.34, 0.64, 0.94, 1.18), side * 0.625, 0.63, material, near_group)
    for y in (-0.42, 0.0, 0.42):
        parts.append(beam(f"Forward ram tine {y}", (-1.32, y, 0.58), (-1.62, y * 1.30, 0.12), 0.115, "plate", material))
    parts.append(beam("Forward ram cutting bar", (-1.62, -0.64, 0.12), (-1.62, 0.64, 0.12), 0.115, "brass", material))
    # Damage-only torn belt fragments begin hidden inside the near track.
    for index, x in enumerate((-0.58, -0.34, -0.10)):
        parts.append(box(f"Hidden broken tread {index}", (0.17, 0.20, 0.055), (x, 0.40, 0.30), "damage", material, 0.002, damage_group=f"DamageTrackShard{index}"))
    return parts


def build_drain_mast(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    mast_group = "DamageMast"
    parts.append(box("Drain mast armored foot", (0.52, 0.70, 0.54), (-1.02, 0, 0.89), "plate", material, 0.014))
    parts.append(box("Drain mast spine", (0.18, 0.24, 1.48), (-1.02, 0, 1.64), "soot", material, 0.010, damage_group=mast_group))
    parts.append(box("Drain mast left rail", (0.075, 0.10, 1.38), (-1.12, -0.18, 1.66), "brass", material, 0.004, damage_group=mast_group))
    parts.append(box("Drain mast right rail", (0.075, 0.10, 1.38), (-1.12, 0.18, 1.66), "brass", material, 0.004, damage_group=mast_group))
    for rung, z in enumerate(np.linspace(1.05, 2.18, 7)):
        parts.append(beam(f"Mast rung {rung}", (-1.12, -0.20, float(z)), (-1.12, 0.20, float(z)), 0.035, "brass", material, mast_group))
    for index, z in enumerate((1.15, 1.38, 1.61, 1.84, 2.07)):
        parts.append(cylinder(f"Mast ceramic core {index}", 0.070, 0.30, (-1.02, 0, z), "ceramic", material, vertices=10, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=mast_group))
        for y in (-0.12, 0.0, 0.12):
            parts.append(torus(f"Mast insulator disc {index} {y}", 0.080, 0.020, (-1.02, y, z), "ceramic", material, rotation=(math.pi / 2, 0, 0), damage_group=mast_group))
    parts.append(cylinder("Mast crown collar", 0.20, 0.15, (-1.02, 0, 2.30), "brass", material, vertices=12, damage_group=mast_group))
    parts.append(ico_sphere("Mast teal collector", 0.175, (-1.02, 0, 2.44), "teal", material, mast_group))
    parts.append(torus("Mast collector cage", 0.205, 0.030, (-1.02, 0, 2.44), "brass", material, rotation=(math.pi / 2, 0, 0), damage_group=mast_group))
    # The horizontal drain arm makes the mast point toward the nearest pylon.
    parts.append(beam("Drain arm lower", (-0.96, -0.12, 2.05), (-0.18, -0.12, 1.78), 0.055, "brass", material, mast_group))
    parts.append(beam("Drain arm upper", (-0.96, 0.12, 2.05), (-0.18, 0.12, 1.78), 0.055, "brass", material, mast_group))
    parts.append(cylinder("Drain arm glass", 0.075, 0.56, (-0.55, 0, 1.91), "teal", material, vertices=12, rotation=(0, math.radians(70), 0), bevel=0, damage_group=mast_group))
    parts.append(box("Drain arm pivot", (0.28, 0.42, 0.34), (-0.16, 0, 1.77), "plate", material, 0.012, damage_group=mast_group))
    parts.append(beam("Mast front brace", (-1.16, 0, 0.76), (-1.34, 0, 1.56), 0.060, "iron", material, mast_group))
    parts.append(beam("Mast rear brace", (-0.88, 0, 0.76), (-0.72, 0, 1.54), 0.060, "iron", material, mast_group))
    for index, offset in enumerate(((-0.04, -0.02, 0.00), (0.04, 0.02, 0.03), (0.0, 0.0, -0.04))):
        parts.append(box(f"Hidden mast ceramic shard {index}", (0.10, 0.055, 0.035), (-1.02 + offset[0], offset[1], 1.22 + offset[2]), "damage", material, 0.001, damage_group=f"DamageMastShard{index}"))
    parts.append(box("Hidden mast rupture block", (0.24, 0.18, 0.18), (-1.02, 0.0, 0.94), "damage", material, 0.002, damage_group="DamageMastBreach"))
    return parts


def build_capacitor_bank(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    parts.append(cylinder("Armored dynamo core", 0.52, 1.35, (-0.12, 0, 1.19), "plate", material, vertices=16, rotation=(0, math.pi / 2, 0), bevel=0))
    for x in (-0.76, -0.45, -0.14, 0.17, 0.49):
        parts.append(torus(f"Core armor band {x}", 0.52, 0.029, (x, 0, 1.19), "brass", material, rotation=(0, math.pi / 2, 0)))
    for side in (-1, 1):
        y = side * 0.52
        parts.append(cylinder(f"Core teal viewport {side}", 0.175, 0.040, (-0.22, y, 1.20), "teal", material, vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0))
        parts.append(torus(f"Core viewport collar {side}", 0.200, 0.028, (-0.22, y, 1.20), "brass", material, rotation=(math.pi / 2, 0, 0)))
        parts.append(box(f"Core flank plate {side}", (0.98, 0.08, 0.24), (-0.08, side * 0.50, 0.94), "soot", material, 0.008))
    parts.append(box("Capacitor rack bed", (1.46, 0.98, 0.18), (0.74, 0, 0.82), "iron", material, 0.010))
    parts.append(box("Capacitor rear bulkhead", (0.14, 0.86, 0.48), (1.38, 0, 1.05), "plate", material, 0.012, damage_group="DamageCapRear"))
    cap_xs = (0.38, 0.72, 1.06)
    for row, y in enumerate((-0.28, 0.28)):
        for column, x in enumerate(cap_xs):
            group = "DamageCapNear" if y > 0 and column >= 1 else None
            parts.append(cylinder(f"Capacitor jar {row} {column}", 0.135, 0.74, (x, y, 1.24), "copper", material, vertices=12, bevel=0, damage_group=group))
            parts.append(cone(f"Capacitor crown {row} {column}", 0.16, 0.13, 0.09, (x, y, 1.65), "brass", material, vertices=12, damage_group=group))
            parts.append(cylinder(f"Capacitor terminal {row} {column}", 0.045, 0.15, (x, y, 1.79), "ceramic", material, vertices=8, damage_group=group))
            for band, z in enumerate((1.04, 1.28, 1.50)):
                parts.append(torus(f"Capacitor coil {row} {column} {band}", 0.138, 0.021, (x, y, z), "brass", material, damage_group=group))
            parts.append(beam(f"Capacitor feed pipe {row} {column}", (x, y, 0.90), (x - 0.12, y, 0.72), 0.045, "teal", material, group))
    for side in (-1, 1):
        y = side * 0.50
        parts.append(beam(f"Rack upper rail {side}", (0.20, y, 1.63), (1.30, y, 1.63), 0.045, "brass", material, "DamageCapNear" if side > 0 else None))
        parts.append(beam(f"Rack lower rail {side}", (0.18, y, 0.84), (1.34, y, 0.84), 0.052, "plate", material, "DamageCapNear" if side > 0 else None))
        for x in (0.22, 0.70, 1.18):
            parts.append(beam(f"Rack post {side} {x}", (x, y, 0.84), (x, y, 1.63), 0.042, "iron", material, "DamageCapNear" if side > 0 and x > 0.6 else None))
        add_rivets(parts, f"Cap rack {side}", (0.24, 0.48, 0.72, 0.96, 1.20), side * 0.54, 0.84, material, "DamageCapNear" if side > 0 else None)
    parts.append(cylinder("Core exhaust stack", 0.105, 0.56, (-0.48, -0.18, 1.72), "soot", material, vertices=12))
    parts.append(cone("Core exhaust crown", 0.14, 0.10, 0.14, (-0.48, -0.18, 2.06), "brass", material, vertices=12))
    parts.append(cylinder("Core pressure stack", 0.080, 0.40, (-0.18, 0.22, 1.70), "iron", material, vertices=10))
    parts.append(torus("Core pressure cap", 0.095, 0.022, (-0.18, 0.22, 1.91), "brass", material))
    # Damage-only hot fragments start hidden in the near two jars.
    for index, x in enumerate((0.72, 1.06)):
        parts.append(ico_sphere(f"Hidden ruptured core {index}", 0.15, (x, 0.20, 1.22), "damage", material, f"DamageCapRupture{index}"))
        parts.append(beam(f"Hidden arc fork {index}", (x, 0.18, 1.22), (x + 0.05, 0.21, 1.42), 0.038, "teal", material, f"DamageCapArc{index}"))
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


def add_damage_shapes(drain_mast: bpy.types.Object, tracks: bpy.types.Object, capacitor_bank: bpy.types.Object) -> None:
    drain_mast.shape_key_add(name="Basis")
    toppled = drain_mast.shape_key_add(name="Damage_ToppledDrainMast")
    pivot = Vector((-1.02, 0.0, 0.83))
    angle = math.radians(-66)
    for index in group_vertex_indices(drain_mast, "DamageMast"):
        co = toppled.data[index].co
        local = co - pivot
        x = local.x * math.cos(angle) + local.z * math.sin(angle)
        z = -local.x * math.sin(angle) + local.z * math.cos(angle)
        co.x = pivot.x + x
        co.z = pivot.z + z - 0.10
        co.y += max(0.0, local.z) * 0.11
    shard_moves = (
        Vector((-0.34, 0.30, 0.18)),
        Vector((-0.22, -0.34, 0.31)),
        Vector((0.14, 0.39, 0.12)),
    )
    for shard, movement in enumerate(shard_moves):
        for index in group_vertex_indices(drain_mast, f"DamageMastShard{shard}"):
            toppled.data[index].co += movement
    for index in group_vertex_indices(drain_mast, "DamageMastBreach"):
        toppled.data[index].co += Vector((0.0, 0.52, 0.08))

    tracks.shape_key_add(name="Basis")
    shattered = tracks.shape_key_add(name="Damage_ShatteredTracks")
    for index in group_vertex_indices(tracks, "DamageTrackNear"):
        co = shattered.data[index].co
        front = max(0.0, min(1.0, (-co.x + 0.25) / 1.55))
        co.y += 0.20 + front * 0.34
        co.z += math.sin((co.x + 1.5) * 5.5) * 0.12 + front * 0.14
        co.x -= front * 0.18
    for index in group_vertex_indices(tracks, "DamageTrackSkirt"):
        co = shattered.data[index].co
        front = max(0.0, min(1.0, (-co.x + 0.30) / 1.60))
        co.y += 0.58
        co.z -= 0.16 + front * 0.26
        co.x -= front * 0.16
    shard_moves = (
        Vector((-0.48, 0.52, 0.32)),
        Vector((-0.12, 0.62, 0.04)),
        Vector((0.26, 0.48, 0.24)),
    )
    for shard, movement in enumerate(shard_moves):
        for index in group_vertex_indices(tracks, f"DamageTrackShard{shard}"):
            shattered.data[index].co += movement

    capacitor_bank.shape_key_add(name="Basis")
    ruptured = capacitor_bank.shape_key_add(name="Damage_RupturedCapacitorBank")
    for index in group_vertex_indices(capacitor_bank, "DamageCapNear"):
        co = ruptured.data[index].co
        rear = max(0.0, min(1.0, (co.x - 0.35) / 1.05))
        co.y += 0.34 + rear * 0.32
        co.x += rear * 0.18
        co.z -= 0.20 + rear * 0.28
    for index in group_vertex_indices(capacitor_bank, "DamageCapRear"):
        co = ruptured.data[index].co
        co.x += 0.18
        co.z -= max(0.0, co.z - 0.80) * 0.22
    rupture_moves = (Vector((0.0, 0.68, 0.14)), Vector((0.12, 0.76, 0.26)))
    arc_moves = (Vector((-0.07, 0.72, 0.44)), Vector((0.15, 0.82, 0.56)))
    for rupture, movement in enumerate(rupture_moves):
        for index in group_vertex_indices(capacitor_bank, f"DamageCapRupture{rupture}"):
            co = ruptured.data[index].co
            center = Vector(((0.72, 1.06)[rupture], 0.20, 1.22))
            local = co - center
            co.x = center.x + local.x * 1.35
            co.y = center.y + local.y * 1.75
            co.z = center.z + local.z * 0.62
            co += movement
    for arc, movement in enumerate(arc_moves):
        for index in group_vertex_indices(capacitor_bank, f"DamageCapArc{arc}"):
            ruptured.data[index].co += movement

    for obj in (drain_mast, tracks, capacitor_bank):
        obj.active_shape_key_index = 0
        for key in obj.data.shape_keys.key_blocks:
            key.value = 0.0


def triangle_count(objects: tuple[bpy.types.Object, ...]) -> int:
    return sum(sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons) for obj in objects)


def world_bounds(objects: tuple[bpy.types.Object, ...]) -> tuple[Vector, Vector]:
    points = [obj.matrix_world @ vertex.co for obj in objects for vertex in obj.data.vertices]
    return (
        Vector((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points))),
        Vector((max(point.x for point in points), max(point.y for point in points), max(point.z for point in points))),
    )


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
    drain_mast = join_component("drain_mast", build_drain_mast(material), material)
    tracks = join_component("tracks", build_tracks(material), material)
    capacitor_bank = join_component("capacitor_bank", build_capacitor_bank(material), material)
    objects = (drain_mast, tracks, capacitor_bank)
    normalize_base_center(objects)
    add_damage_shapes(*objects)

    minimum, maximum = world_bounds(objects)
    triangles = triangle_count(objects)
    assert triangles <= 12_000, f"triangle budget exceeded: {triangles}"
    assert abs((maximum.x - minimum.x) - MODEL_LENGTH) < 0.01
    assert abs((maximum.x + minimum.x) * 0.5) < 0.001
    assert abs((maximum.y + minimum.y) * 0.5) < 0.001
    assert abs(minimum.z) < 0.001
    assert len({slot.material.name for obj in objects for slot in obj.material_slots if slot.material}) == 1
    export(objects)
    print(
        json.dumps(
            {
                "blend": str(BLEND),
                "glb": str(GLB),
                "sha256": hashlib.sha256(GLB.read_bytes()).hexdigest(),
                "sourcePlate": str(REFERENCE.relative_to(ROOT)),
                "sourcePlateSha256": source_sha,
                "objects": [obj.name for obj in objects],
                "damageMorphs": [obj.data.shape_keys.key_blocks[1].name for obj in objects],
                "triangles": triangles,
                "boundsBlender": {
                    "min": [round(value, 6) for value in minimum],
                    "max": [round(value, 6) for value in maximum],
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
