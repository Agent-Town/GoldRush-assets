from pathlib import Path
import hashlib
import json
import math

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REFERENCE = ROOT / "assets/raw/boss-dredge-queen.png"
DAMAGE_REFERENCE = ROOT / "assets/raw/boss-dredge-queen-damage.png"
BLEND = OUT / "dredge-queen.blend"
GLB = OUT / "dredge-queen.glb"
ATLAS_SIZE = 1024
MODEL_LENGTH = 8.0

REGIONS = {
    "soot": (0.02, 0.02, 0.20, 0.47),
    "iron": (0.23, 0.02, 0.41, 0.47),
    "brass": (0.44, 0.02, 0.61, 0.47),
    "deck": (0.64, 0.02, 0.78, 0.47),
    "teal": (0.81, 0.02, 0.89, 0.47),
    "damage": (0.92, 0.02, 0.98, 0.47),
    "plate": (0.02, 0.52, 0.53, 0.98),
    "sail": (0.56, 0.52, 0.78, 0.98),
    "rope": (0.81, 0.52, 0.89, 0.98),
    "cargo": (0.92, 0.52, 0.98, 0.98),
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


def create_atlas() -> tuple[bpy.types.Image, dict[str, str]]:
    source = bpy.data.images.load(str(REFERENCE), check_existing=False)
    pixels = np.array(source.pixels[:], dtype=np.float32).reshape(source.size[1], source.size[0], 4)
    colors = pixels[:, :, :3]
    luminance = colors.mean(axis=2)
    saturation = colors.max(axis=2) - colors.min(axis=2)
    dark = sampled_color(colors, (luminance > 0.015) & (luminance < 0.14), (0.035, 0.030, 0.022))
    warm = sampled_color(
        colors,
        (colors[:, :, 0] > colors[:, :, 1] * 1.08)
        & (colors[:, :, 1] > colors[:, :, 2] * 1.12)
        & (luminance > 0.12)
        & (luminance < 0.48),
        (0.34, 0.20, 0.07),
    )
    rust = sampled_color(
        colors,
        (colors[:, :, 0] > colors[:, :, 1] * 1.30)
        & (colors[:, :, 1] > colors[:, :, 2] * 1.05)
        & (saturation > 0.09),
        (0.34, 0.075, 0.028),
    )
    teal = sampled_color(
        colors,
        (colors[:, :, 1] > colors[:, :, 0] * 1.18)
        & (colors[:, :, 2] > colors[:, :, 0] * 1.18)
        & (saturation > 0.06),
        (0.025, 0.36, 0.38),
    )
    palette = {
        "soot": np.clip(dark * 0.50, 0.010, 0.060),
        "iron": np.clip(dark * 0.58 + warm * 0.34 + 0.015, 0.035, 0.22),
        "brass": np.clip(warm * 0.88 + 0.025, 0.09, 0.55),
        "deck": np.clip(warm * 0.54 + rust * 0.26 + 0.045, 0.06, 0.36),
        "teal": np.clip(teal * 1.12, 0.02, 0.62),
        "damage": np.clip(rust * 0.72 + np.array((0.16, 0.025, 0.012)), 0.03, 0.48),
        "sail": np.clip(rust * 0.74 + np.array((0.08, 0.012, 0.008)), 0.03, 0.40),
        "rope": np.clip(warm * 0.54 + np.array((0.10, 0.055, 0.012)), 0.05, 0.50),
        "cargo": np.clip(rust * 0.42 + warm * 0.42 + 0.018, 0.05, 0.44),
    }
    atlas = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    atlas[:, :, :3] = palette["soot"]
    rng = np.random.default_rng(517)

    # Carry the approved plate's real engraved line density into the largest tile.
    x0, y0, x1, y1 = region_pixels(REGIONS["plate"])
    crop = colors[
        int(source.size[1] * 0.09):int(source.size[1] * 0.88),
        int(source.size[0] * 0.08):int(source.size[0] * 0.95),
    ]
    painted = resized_nearest(resized_nearest(crop, 300, 420), y1 - y0, x1 - x0)
    ink = 1.0 - np.clip((painted.mean(axis=2) - 0.025) / 0.40, 0.0, 1.0)
    plate_base = palette["iron"] * 0.76 + palette["brass"] * 0.24
    engraved = plate_base[None, None, :] * (1.08 - ink[:, :, None] * 0.55)
    warm_mask = (painted[:, :, 0] > painted[:, :, 2] * 1.28) & (ink > 0.20)
    engraved[warm_mask] = engraved[warm_mask] * 0.75 + palette["brass"] * 0.17
    engraved += rng.normal(0, 0.008, (y1 - y0, x1 - x0, 1))
    atlas[y0:y1, x0:x1, :3] = np.clip(engraved, 0.008, 0.34)

    for name, region in REGIONS.items():
        if name == "plate":
            continue
        x0, y0, x1, y1 = region_pixels(region)
        base = palette[name]
        noise = rng.normal(0, 0.008 if name != "teal" else 0.004, (y1 - y0, x1 - x0, 1))
        block = np.clip(base + noise, 0.008, 0.72)
        atlas[y0:y1, x0:x1, :3] = block
        if name in {"soot", "iron", "brass", "deck", "damage", "sail", "cargo"}:
            height = y1 - y0
            spacing = 17 if name in {"iron", "brass"} else 23
            for offset in range(-height, x1 - x0, spacing):
                for yy in range(y0, y1):
                    xx = x0 + offset + (yy - y0)
                    if x0 <= xx < x1:
                        atlas[yy, xx:min(xx + 2, x1), :3] *= 0.58
        if name in {"iron", "brass", "deck"}:
            for yy in range(y0 + 12, y1, 29):
                for xx in range(x0 + 12, x1, 29):
                    atlas[yy - 2:yy + 3, xx - 2:xx + 3, :3] *= 0.46
        if name == "sail":
            for yy in range(y0 + 18, y1, 26):
                atlas[yy:yy + 2, x0:x1, :3] *= 0.62
        if name == "teal":
            for yy in range(y0 + 7, y1, 15):
                atlas[yy:yy + 2, x0:x1, :3] = np.clip(base * 1.35, 0, 0.78)

    # The source plate is storm-dark. Lift its baked albedo, not the material,
    # so engraved detail survives the high gameplay camera without emission.
    atlas[:, :, :3] = np.clip(atlas[:, :, :3] * 1.34 + 0.012, 0.008, 0.78)

    image = bpy.data.images.new("DredgeQueenPlateAtlas", ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(atlas.ravel())
    image.pack()
    return image, {
        "intact": hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
        "damage": hashlib.sha256(DAMAGE_REFERENCE.read_bytes()).hexdigest(),
    }


def create_material(image: bpy.types.Image) -> bpy.types.Material:
    material = bpy.data.materials.new("DredgeQueenMaterial")
    material.use_nodes = True
    material.use_backface_culling = False
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Linear"
    texture.extension = "REPEAT"
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Roughness"].default_value = 0.9
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
    bevel: float = 0.012,
    damage_group: str | None = None,
    smooth: bool = False,
) -> bpy.types.Object:
    obj["atlas_region"] = region
    obj.data.materials.append(material)
    mark_all(obj, damage_group)
    if bevel > 0:
        modifier = obj.modifiers.new("Worked edge", "BEVEL")
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
    bevel: float = 0.012,
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
    major_segments: int = 12,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(
        major_segments=major_segments,
        minor_segments=4,
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
    scale: tuple[float, float, float] = (1, 1, 1),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=radius, location=at)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
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


def triangle_panel(
    name: str,
    points: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]],
    thickness: float,
    region: str,
    material: bpy.types.Material,
    damage_group: str | None = None,
) -> bpy.types.Object:
    front = [Vector(point) + Vector((0, -thickness * 0.5, 0)) for point in points]
    back = [Vector(point) + Vector((0, thickness * 0.5, 0)) for point in points]
    vertices = [tuple(point) for point in [*front, *back]]
    faces = [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return tag(obj, region, material, 0.004, damage_group)


def quad_panel(
    name: str,
    points: tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ],
    thickness: float,
    region: str,
    material: bpy.types.Material,
    damage_group: str | None = None,
) -> bpy.types.Object:
    front = [Vector(point) + Vector((0, -thickness * 0.5, 0)) for point in points]
    back = [Vector(point) + Vector((0, thickness * 0.5, 0)) for point in points]
    vertices = [tuple(point) for point in [*front, *back]]
    faces = [
        (0, 1, 2, 3),
        (7, 6, 5, 4),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return tag(obj, region, material, 0.004, damage_group)


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
                0.035,
                0.045,
                (x, y, z),
                "brass",
                material,
                vertices=8,
                rotation=(math.pi / 2, 0, 0),
                bevel=0,
                damage_group=group,
            )
        )


def build_claw(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    arm = "DamageClawArm"
    parts.append(box("Armored fore hull", (3.05, 3.70, 0.74), (-2.28, 0, 0.48), "plate", material, 0.10))
    parts.append(box("Reinforced bow wall", (0.58, 3.18, 0.92), (-3.72, 0, 0.64), "iron", material, 0.10))
    parts.append(box("Fore working deck", (2.88, 3.42, 0.18), (-2.30, 0, 0.94), "deck", material, 0.025))
    for side in (-1, 1):
        y = side * 1.76
        parts.append(beam(f"Fore rail {side}", (-3.48, y, 1.16), (-1.02, y, 1.16), 0.075, "brass", material))
        for x in (-3.35, -2.75, -2.15, -1.55, -1.05):
            parts.append(beam(f"Fore post {side} {x}", (x, y, 0.94), (x, y, 1.22), 0.060, "brass", material))
        add_rivets(parts, f"Bow flank {side}", (-3.52, -3.10, -2.68, -2.26, -1.84, -1.42), side * 1.88, 0.58, material)
    parts.append(box("Crane turntable", (0.82, 1.32, 0.30), (-1.36, 0, 1.14), "brass", material, 0.045))
    parts.append(cylinder("Crane pivot drum", 0.42, 1.20, (-1.42, 0, 1.48), "plate", material, vertices=14, rotation=(math.pi / 2, 0, 0), bevel=0))
    for side in (-1, 1):
        y = side * 0.50
        parts.append(beam(f"Crane leg lower {side}", (-1.48, y, 1.42), (-2.88, y, 4.42), 0.17, "iron", material, arm))
        parts.append(beam(f"Crane leg brass edge {side}", (-1.39, y, 1.50), (-2.78, y, 4.48), 0.075, "brass", material, arm))
    for rung, z in enumerate(np.linspace(1.96, 4.14, 7)):
        t = (z - 1.42) / (4.42 - 1.42)
        x = -1.48 + (-2.88 + 1.48) * t
        parts.append(beam(f"Crane cross rung {rung}", (x, -0.53, float(z)), (x, 0.53, float(z)), 0.060, "brass", material, arm))
    parts.append(beam("Crane boom upper", (-2.84, -0.40, 4.45), (-3.58, -0.28, 4.94), 0.16, "iron", material, arm))
    parts.append(beam("Crane boom upper pair", (-2.84, 0.40, 4.45), (-3.58, 0.28, 4.94), 0.16, "iron", material, arm))
    parts.append(cylinder("Crane crown pulley", 0.42, 0.34, (-2.86, 0, 4.53), "brass", material, vertices=14, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=arm))
    parts.append(torus("Crane crown rim", 0.45, 0.055, (-2.86, 0, 4.53), "brass", material, rotation=(math.pi / 2, 0, 0), damage_group=arm))
    parts.append(cylinder("Boom end pulley", 0.34, 0.30, (-3.60, 0, 4.94), "brass", material, vertices=12, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=arm))
    for cable, y in enumerate((-0.17, 0.0, 0.17)):
        parts.append(beam(f"Claw chain upper {cable}", (-3.60, y, 4.86), (-4.24, y, 3.36), 0.055, "rope", material, arm))
    parts.append(cylinder("Claw gearbox", 0.50, 0.82, (-4.25, 0, 3.20), "plate", material, vertices=14, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=arm))
    parts.append(torus("Claw gearbox collar", 0.52, 0.065, (-4.25, 0, 3.20), "brass", material, rotation=(math.pi / 2, 0, 0), damage_group=arm))
    parts.append(ico_sphere("Claw teal sight", 0.22, (-4.25, -0.46, 3.24), "teal", material, arm, scale=(1.0, 0.35, 1.0)))
    for finger, y in enumerate((-0.58, 0.0, 0.58)):
        spread = y * 1.24
        points = [
            (-4.28, y, 3.00),
            (-4.58, y * 1.08, 2.48),
            (-4.76, spread, 1.80),
            (-4.52, spread * 1.08, 1.17),
            (-4.10, spread * 0.86, 0.96),
        ]
        for segment, (start, end) in enumerate(zip(points, points[1:])):
            parts.append(beam(f"Claw finger {finger} {segment}", start, end, 0.19, "brass" if segment in {0, 3} else "iron", material, arm))
    parts.append(beam("Claw lower jaw brace", (-4.49, -0.76, 1.40), (-4.49, 0.76, 1.40), 0.14, "brass", material, arm))
    for shard, at in enumerate(((-4.18, -0.10, 3.0), (-4.12, 0.08, 3.0), (-4.20, 0.0, 2.92))):
        parts.append(box(f"Hidden claw chain scrap {shard}", (0.22, 0.06, 0.05), at, "damage", material, 0.002, damage_group=f"DamageClawShard{shard}"))
    return parts


def build_paddle(material: bpy.types.Material, side: int) -> list[bpy.types.Object]:
    label = "Port" if side < 0 else "Starboard"
    group = f"Damage{label}Paddle"
    center = Vector((1.35, side * 2.48, 1.64))
    parts: list[bpy.types.Object] = []
    parts.append(box(f"{label} wheel sponson", (3.38, 0.36, 0.84), (1.22, side * 2.10, 0.68), "plate", material, 0.055))
    parts.append(box(f"{label} wheel sill", (3.55, 0.44, 0.18), (1.22, side * 2.20, 1.02), "brass", material, 0.025))
    parts.append(torus(f"{label} paddle outer rim", 1.40, 0.105, tuple(center), "iron", material, rotation=(math.pi / 2, 0, 0), damage_group=group, major_segments=16))
    parts.append(torus(f"{label} paddle inner rim", 0.88, 0.070, tuple(center), "brass", material, rotation=(math.pi / 2, 0, 0), damage_group=group, major_segments=16))
    parts.append(cylinder(f"{label} paddle hub", 0.27, 0.52, tuple(center), "brass", material, vertices=14, rotation=(math.pi / 2, 0, 0), bevel=0, damage_group=group))
    for spoke in range(10):
        angle = math.tau * spoke / 10
        reach = 1.28
        dx, dz = math.cos(angle) * reach, math.sin(angle) * reach
        parts.append(beam(f"{label} spoke {spoke}", tuple(center - Vector((dx, 0, dz))), tuple(center + Vector((dx, 0, dz))), 0.065, "brass", material, group))
    for paddle in range(14):
        angle = math.tau * paddle / 14
        x = center.x + math.cos(angle) * 1.46
        z = center.z + math.sin(angle) * 1.46
        parts.append(
            box(
                f"{label} paddle blade {paddle}",
                (0.52, 0.38, 0.18),
                (x, center.y, z),
                "plate",
                material,
                0.008,
                rotation=(0, -angle, 0),
                damage_group=group,
            )
        )
    arch_points = []
    for step in range(7):
        angle = math.radians(18 + step * 24)
        arch_points.append((center.x + math.cos(angle) * 1.64, center.y, center.z + math.sin(angle) * 1.64))
    for step, (start, end) in enumerate(zip(arch_points, arch_points[1:])):
        parts.append(beam(f"{label} wheel armor arch {step}", start, end, 0.14, "plate", material, group if step in {0, 5} else None))
    parts.append(beam(f"{label} forward wheel stay", (-0.32, center.y, 0.88), (-0.12, center.y, 2.34), 0.14, "brass", material))
    parts.append(beam(f"{label} rear wheel stay", (2.92, center.y, 0.88), (2.82, center.y, 2.40), 0.14, "brass", material, group))
    parts.append(cylinder(f"{label} running lantern", 0.14, 0.38, (0.02, side * 2.38, 2.62), "teal", material, vertices=10, bevel=0))
    parts.append(torus(f"{label} lantern cage", 0.16, 0.028, (0.02, side * 2.38, 2.62), "brass", material, rotation=(math.pi / 2, 0, 0)))
    for shard, at in enumerate(((1.35, center.y, 1.52), (1.28, center.y, 1.48), (1.42, center.y, 1.46))):
        parts.append(box(f"Hidden {label} paddle shard {shard}", (0.32, 0.18, 0.10), at, "damage", material, 0.003, damage_group=f"Damage{label}Shard{shard}"))
    return parts


def build_hold(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    parts.append(box("Central armored hull", (4.75, 4.18, 1.02), (1.02, 0, 0.60), "plate", material, 0.10))
    parts.append(box("Aft transom", (0.64, 3.84, 1.22), (3.28, 0, 0.74), "iron", material, 0.09, damage_group="DamageHoldRear"))
    parts.append(box("Main working deck", (4.45, 3.82, 0.20), (0.98, 0, 1.14), "deck", material, 0.025))
    for side in (-1, 1):
        y = side * 1.94
        parts.append(beam(f"Main rail {side}", (-1.05, y, 1.43), (3.14, y, 1.43), 0.075, "brass", material))
        for x in (-0.96, -0.34, 0.30, 0.94, 1.58, 2.22, 2.86):
            parts.append(beam(f"Main rail post {side} {x}", (x, y, 1.14), (x, y, 1.48), 0.060, "brass", material))
        add_rivets(parts, f"Main hull {side}", (-0.92, -0.48, -0.04, 0.40, 0.84, 1.28, 1.72, 2.16, 2.60, 3.04), side * 2.11, 0.70, material)

    # Plate-derived domed corsair wheelhouse.
    parts.append(box("Wheelhouse armored base", (1.86, 2.58, 1.56), (-0.48, 0, 1.98), "iron", material, 0.055))
    parts.append(box("Wheelhouse brass crown", (2.08, 2.78, 0.20), (-0.48, 0, 2.80), "brass", material, 0.025))
    parts.append(ico_sphere("Wheelhouse copper dome", 0.76, (-0.48, 0, 3.12), "plate", material, scale=(1.0, 1.25, 0.55)))
    parts.append(cylinder("Wheelhouse dome cap", 0.17, 0.38, (-0.48, 0, 3.62), "brass", material, vertices=10))
    for side in (-1, 1):
        y = side * 1.31
        parts.append(box(f"Wheelhouse teal windows {side}", (1.22, 0.055, 0.38), (-0.48, y, 2.10), "teal", material, 0.006))
        parts.append(box(f"Wheelhouse window guard upper {side}", (1.36, 0.075, 0.060), (-0.48, y * 1.01, 2.32), "brass", material, 0.004))
        parts.append(box(f"Wheelhouse window guard lower {side}", (1.36, 0.075, 0.060), (-0.48, y * 1.01, 1.88), "brass", material, 0.004))
    parts.append(box("Wheelhouse forward amber pane", (0.055, 1.48, 0.48), (-1.42, 0, 2.10), "cargo", material, 0.008))
    parts.append(cylinder("Wheelhouse smoke stack", 0.18, 0.88, (-0.88, -0.62, 3.28), "soot", material, vertices=12))
    parts.append(torus("Wheelhouse stack crown", 0.22, 0.040, (-0.88, -0.62, 3.74), "brass", material))

    # Fat aft loot hold, clearly separable from the wheelhouse and paddles.
    parts.append(box("Loot hold armored bin", (2.72, 3.30, 1.68), (2.00, 0, 2.05), "iron", material, 0.06, damage_group="DamageHoldRear"))
    parts.append(box("Loot hold port lid", (2.64, 1.62, 0.22), (1.96, -0.82, 2.94), "plate", material, 0.025, rotation=(math.radians(-8), 0, 0), damage_group="DamageHoldPortLid"))
    parts.append(box("Loot hold starboard lid", (2.64, 1.62, 0.22), (1.96, 0.82, 2.94), "plate", material, 0.025, rotation=(math.radians(8), 0, 0), damage_group="DamageHoldStarboardLid"))
    for x in (1.02, 1.52, 2.02, 2.52, 3.00):
        parts.append(beam(f"Hold lid strap {x}", (x, -1.60, 2.97), (x, 1.60, 2.97), 0.070, "brass", material, "DamageHoldPortLid" if x < 2.02 else "DamageHoldStarboardLid"))
    parts.append(torus("Hold rope coil port", 0.38, 0.060, (2.58, -1.68, 2.72), "rope", material, rotation=(math.pi / 2, 0, 0), damage_group="DamageHoldPortLid"))
    parts.append(torus("Hold rope coil starboard", 0.32, 0.055, (1.34, 1.68, 2.70), "rope", material, rotation=(math.pi / 2, 0, 0), damage_group="DamageHoldStarboardLid"))

    # Masts, rigging, and the large oxblood corsair sail own the boss silhouette.
    parts.append(cylinder("Main mast", 0.14, 4.28, (0.52, 0, 3.22), "brass", material, vertices=12))
    parts.append(cone("Main mast finial", 0.20, 0.04, 0.46, (0.52, 0, 5.58), "brass", material, vertices=10))
    parts.append(cylinder("Aft mast", 0.105, 3.34, (3.00, 0, 3.16), "brass", material, vertices=10, damage_group="DamageFlag"))
    parts.append(cone("Aft mast finial", 0.15, 0.03, 0.34, (3.00, 0, 4.98), "brass", material, vertices=10, damage_group="DamageFlag"))
    parts.append(quad_panel("Oxblood main corsair sail", ((0.66, 0.02, 5.34), (3.88, 0.02, 4.98), (3.48, 0.02, 3.16), (0.74, 0.02, 2.78)), 0.065, "sail", material, "DamageFlag"))
    parts.append(triangle_panel("Oxblood aft sail", ((3.08, 0.03, 4.64), (3.92, 0.03, 4.18), (3.12, 0.03, 3.18)), 0.055, "sail", material, "DamageFlag"))
    parts.append(beam("Ghost pickaxe slash one", (1.30, -0.04, 3.70), (2.24, -0.04, 4.38), 0.065, "brass", material, "DamageFlag"))
    parts.append(beam("Ghost pickaxe slash two", (1.34, -0.06, 4.40), (2.24, -0.06, 3.66), 0.065, "brass", material, "DamageFlag"))
    for index, (start, end) in enumerate((
        ((0.52, -0.05, 5.50), (-3.35, -1.88, 1.46)),
        ((0.52, 0.05, 5.50), (3.20, 1.90, 1.48)),
        ((3.00, -0.03, 4.88), (0.56, -1.90, 1.46)),
        ((3.00, 0.03, 4.88), (3.22, 1.88, 1.48)),
    )):
        parts.append(beam(f"Rigging line {index}", start, end, 0.032, "rope", material, "DamageFlag" if index >= 2 else None))

    for index, (x, y) in enumerate(((-0.92, -1.62), (-0.92, 1.62), (0.72, -1.62), (0.72, 1.62), (2.72, -1.62), (2.72, 1.62))):
        parts.append(cylinder(f"Deck teal lantern {index}", 0.10, 0.34, (x, y, 1.82), "teal", material, vertices=10, bevel=0))
        parts.append(torus(f"Deck lantern cage {index}", 0.12, 0.024, (x, y, 1.82), "brass", material, rotation=(math.pi / 2, 0, 0)))
        parts.append(beam(f"Deck lantern post {index}", (x, y, 1.44), (x, y, 1.98), 0.050, "brass", material))

    # Damage-only cargo starts hidden inside the intact hold, then spills in Act 3.
    hidden = ((2.16, 0.0, 1.64), (2.02, 0.12, 1.60), (2.26, -0.10, 1.55), (2.04, -0.08, 1.58))
    for index, at in enumerate(hidden):
        if index % 2:
            parts.append(cylinder(f"Hidden cargo drum {index}", 0.18, 0.34, at, "cargo", material, vertices=10, rotation=(0, math.pi / 2, 0), bevel=0, damage_group=f"DamageCargo{index}"))
        else:
            parts.append(box(f"Hidden cargo crate {index}", (0.34, 0.30, 0.28), at, "cargo", material, 0.008, damage_group=f"DamageCargo{index}"))
    parts.append(box("Hidden hold rupture", (0.66, 0.08, 0.48), (2.82, 0.0, 1.56), "damage", material, 0.004, damage_group="DamageHoldBreach"))
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


def rotate_y(co: Vector, pivot: Vector, angle: float) -> None:
    local = co - pivot
    x = local.x * math.cos(angle) + local.z * math.sin(angle)
    z = -local.x * math.sin(angle) + local.z * math.cos(angle)
    co.x = pivot.x + x
    co.z = pivot.z + z


def add_damage_shapes(
    claw: bpy.types.Object,
    paddle_port: bpy.types.Object,
    paddle_starboard: bpy.types.Object,
    hold: bpy.types.Object,
) -> None:
    claw.shape_key_add(name="Basis")
    slack = claw.shape_key_add(name="Damage_SlackClaw")
    pivot = Vector((-1.40, 0.0, 1.30))
    for index in group_vertex_indices(claw, "DamageClawArm"):
        co = slack.data[index].co
        rotate_y(co, pivot, math.radians(-30))
        co.z -= 0.34
        co.y *= 1.06
    shard_moves = (Vector((-0.36, -0.40, -0.22)), Vector((-0.22, 0.44, -0.35)), Vector((0.10, 0.56, -0.46)))
    for shard, movement in enumerate(shard_moves):
        for index in group_vertex_indices(claw, f"DamageClawShard{shard}"):
            slack.data[index].co += movement

    for paddle, side, label in ((paddle_port, -1, "Port"), (paddle_starboard, 1, "Starboard")):
        paddle.shape_key_add(name="Basis")
        broken = paddle.shape_key_add(name=f"Damage_Broken{label}Paddle")
        center = Vector((1.35, side * 2.48, 1.64))
        for index in group_vertex_indices(paddle, f"Damage{label}Paddle"):
            co = broken.data[index].co
            radial_x = co.x - center.x
            radial_z = co.z - center.z
            upper = max(0.0, radial_z)
            co.y += side * (0.30 + upper * 0.46)
            co.x += radial_z * (0.18 if side > 0 else -0.18)
            co.z -= 0.42 + abs(radial_x) * 0.18
        moves = (
            Vector((-0.56, side * 0.46, -0.18)),
            Vector((0.16, side * 0.62, -0.44)),
            Vector((0.62, side * 0.40, 0.08)),
        )
        for shard, movement in enumerate(moves):
            for index in group_vertex_indices(paddle, f"Damage{label}Shard{shard}"):
                broken.data[index].co += movement

    hold.shape_key_add(name="Basis")
    cracked = hold.shape_key_add(name="Damage_CrackedLootHold")
    for index in group_vertex_indices(hold, "DamageHoldPortLid"):
        co = cracked.data[index].co
        co.y -= 0.58
        co.z += max(0.0, 2.50 - co.z) * 0.15 + 0.28
    for index in group_vertex_indices(hold, "DamageHoldStarboardLid"):
        co = cracked.data[index].co
        co.y += 0.62
        co.z += max(0.0, 2.50 - co.z) * 0.12 - 0.18
        co.x += 0.18
    for index in group_vertex_indices(hold, "DamageHoldRear"):
        co = cracked.data[index].co
        rear = max(0.0, min(1.0, (co.x - 1.55) / 1.80))
        co.x += rear * 0.20
        co.z -= rear * 0.50
        co.y *= 1.0 + rear * 0.08
    for index in group_vertex_indices(hold, "DamageFlag"):
        co = cracked.data[index].co
        mast_x = 0.52 if co.x < 2.60 else 3.00
        co.x = mast_x + (co.x - mast_x) * 0.30
        co.z = 2.42 + (co.z - 2.42) * 0.25
        co.y *= 0.60
    cargo_moves = (
        Vector((1.86, -2.08, -0.94)),
        Vector((1.58, 2.16, -0.86)),
        Vector((2.22, -1.12, -1.02)),
        Vector((2.00, 1.28, -0.92)),
    )
    for cargo, movement in enumerate(cargo_moves):
        for index in group_vertex_indices(hold, f"DamageCargo{cargo}"):
            cracked.data[index].co += movement
    for index in group_vertex_indices(hold, "DamageHoldBreach"):
        cracked.data[index].co += Vector((0.68, 1.68, -0.34))

    for obj in (claw, paddle_port, paddle_starboard, hold):
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
    scale = MODEL_LENGTH / (maximum.x - minimum.x)
    for obj in objects:
        for vertex in obj.data.vertices:
            vertex.co.x = (vertex.co.x - center_x) * scale
            vertex.co.y = (vertex.co.y - center_y) * scale
            vertex.co.z = (vertex.co.z - minimum.z) * scale
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
    atlas, source_hashes = create_atlas()
    material = create_material(atlas)
    claw = join_component("claw", build_claw(material), material)
    paddle_port = join_component("paddle_port", build_paddle(material, -1), material)
    paddle_starboard = join_component("paddle_starboard", build_paddle(material, 1), material)
    hold = join_component("hold", build_hold(material), material)
    objects = (claw, paddle_port, paddle_starboard, hold)
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
    print(json.dumps({
        "blend": str(BLEND),
        "glb": str(GLB),
        "sha256": hashlib.sha256(GLB.read_bytes()).hexdigest(),
        "sourcePlates": {
            str(REFERENCE.relative_to(ROOT)): source_hashes["intact"],
            str(DAMAGE_REFERENCE.relative_to(ROOT)): source_hashes["damage"],
        },
        "objects": [obj.name for obj in objects],
        "damageMorphs": [obj.data.shape_keys.key_blocks[1].name for obj in objects],
        "triangles": triangles,
        "boundsBlender": {
            "min": [round(value, 6) for value in minimum],
            "max": [round(value, 6) for value in maximum],
        },
    }, indent=2))


if __name__ == "__main__":
    main()
