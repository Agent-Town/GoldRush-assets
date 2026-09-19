"""Shared craft kit for the Opus-5 boss-detail duel entries.

This module carries the shipped pilot idiom verbatim where it is legality-relevant
(atlas sampling, one-material setup, region UV remap, join/normalise/export) and adds
the higher-detail construction helpers the 45k-triangle duel ceiling pays for:
lofted hulls, lattice trusses, chain runs, arc sweeps, and radial repeats.

Nothing here writes to a shipped file. Both duel builders import this kit.
"""

from pathlib import Path
import math

import bpy
import numpy as np
from mathutils import Vector


# --------------------------------------------------------------------------------------
# scene + material
# --------------------------------------------------------------------------------------


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.length_unit = "METERS"


def sampled_color(colors: np.ndarray, mask: np.ndarray, fallback: tuple[float, float, float]) -> np.ndarray:
    selected = colors[mask]
    if len(selected) < 32:
        return np.array(fallback, dtype=np.float32)
    return np.clip(np.median(selected, axis=0), 0.01, 0.82)


def resized_nearest(source: np.ndarray, height: int, width: int) -> np.ndarray:
    ys = np.linspace(0, source.shape[0] - 1, height).astype(np.int32)
    xs = np.linspace(0, source.shape[1] - 1, width).astype(np.int32)
    return source[ys[:, None], xs[None, :]]


def plate_colors(path: Path) -> np.ndarray:
    source = bpy.data.images.load(str(path), check_existing=False)
    pixels = np.array(source.pixels[:], dtype=np.float32).reshape(source.size[1], source.size[0], 4)
    return pixels[:, :, :3]


def create_material(name: str, image: bpy.types.Image) -> bpy.types.Material:
    """Exact shipped material contract: metallic 0, roughness 0.9, double-sided, no emission."""
    material = bpy.data.materials.new(name)
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


# --------------------------------------------------------------------------------------
# tagging
# --------------------------------------------------------------------------------------


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


def from_pydata(
    name: str,
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    region: str,
    material: bpy.types.Material,
    bevel: float = 0.0,
    damage_group: str | None = None,
    smooth: bool = False,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return tag(obj, region, material, bevel, damage_group, smooth)


# --------------------------------------------------------------------------------------
# shipped primitives
# --------------------------------------------------------------------------------------


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
        vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=at, rotation=rotation
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
    minor_segments: int = 4,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(
        major_segments=major_segments,
        minor_segments=minor_segments,
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
    subdivisions: int = 2,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=radius, location=at)
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
    depth: float | None = None,
) -> bpy.types.Object:
    a, b = Vector(start), Vector(end)
    direction = b - a
    obj = box(
        name,
        (width, depth if depth is not None else width, direction.length),
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


def quad_panel(
    name: str,
    points: tuple[tuple[float, float, float], ...],
    thickness: float,
    region: str,
    material: bpy.types.Material,
    damage_group: str | None = None,
    axis: int = 1,
) -> bpy.types.Object:
    offset = Vector((0.0, 0.0, 0.0))
    offset[axis] = thickness * 0.5
    front = [Vector(point) - offset for point in points]
    back = [Vector(point) + offset for point in points]
    vertices = [tuple(point) for point in [*front, *back]]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return from_pydata(name, vertices, faces, region, material, 0.004, damage_group)


def triangle_panel(
    name: str,
    points: tuple[tuple[float, float, float], ...],
    thickness: float,
    region: str,
    material: bpy.types.Material,
    damage_group: str | None = None,
    axis: int = 1,
) -> bpy.types.Object:
    offset = Vector((0.0, 0.0, 0.0))
    offset[axis] = thickness * 0.5
    front = [Vector(point) - offset for point in points]
    back = [Vector(point) + offset for point in points]
    vertices = [tuple(point) for point in [*front, *back]]
    faces = [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    return from_pydata(name, vertices, faces, region, material, 0.004, damage_group)


# --------------------------------------------------------------------------------------
# detail-tier construction (what the raised ceiling buys)
# --------------------------------------------------------------------------------------


def loft(
    name: str,
    rings: list[list[tuple[float, float, float]]],
    region: str,
    material: bpy.types.Material,
    cap_start: bool = True,
    cap_end: bool = True,
    damage_group: str | None = None,
    smooth: bool = False,
) -> bpy.types.Object:
    """Skin a stack of equal-length closed rings. The cheapest way to buy real hull form."""
    count = len(rings[0])
    assert all(len(ring) == count for ring in rings), "loft rings must be equal length"
    vertices: list[tuple[float, float, float]] = []
    for ring in rings:
        vertices.extend(tuple(float(value) for value in point) for point in ring)
    faces: list[tuple[int, ...]] = []
    for index in range(len(rings) - 1):
        base = index * count
        nxt = base + count
        for step in range(count):
            following = (step + 1) % count
            faces.append((base + step, base + following, nxt + following, nxt + step))
    if cap_start:
        faces.append(tuple(range(count - 1, -1, -1)))
    if cap_end:
        base = (len(rings) - 1) * count
        faces.append(tuple(range(base, base + count)))
    return from_pydata(name, vertices, faces, region, material, 0.0, damage_group, smooth)


def hull_section(
    half_beam: float, keel: float, deck: float, crown: float = 0.06, tumblehome: float = 0.95
) -> list[tuple[float, float, float]]:
    """One armoured-corsair station: keel, bilge turn, max beam, tumblehome, deck edge, cambered deck."""
    mid = (keel + deck) * 0.5
    starboard = [
        (0.0, 0.0, keel),
        (0.0, half_beam * 0.52, keel + (deck - keel) * 0.06),
        (0.0, half_beam * 0.89, keel + (deck - keel) * 0.30),
        (0.0, half_beam, mid),
        (0.0, half_beam * tumblehome, deck - (deck - keel) * 0.16),
        (0.0, half_beam * (tumblehome - 0.09), deck),
    ]
    port = [(0.0, -point[1], point[2]) for point in reversed(starboard[1:])]
    return [*starboard, (0.0, 0.0, deck + crown), *port]


def hull_loft(
    name: str,
    stations: list[tuple[float, float, float, float]],
    region: str,
    material: bpy.types.Material,
    damage_group: str | None = None,
) -> bpy.types.Object:
    rings = []
    for x, half_beam, keel, deck in stations:
        rings.append([(x, point[1], point[2]) for point in hull_section(half_beam, keel, deck)])
    return loft(name, rings, region, material, damage_group=damage_group)


def truss(
    parts: list[bpy.types.Object],
    prefix: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    spread: float,
    width: float,
    bays: int,
    region: str,
    brace_region: str,
    material: bpy.types.Material,
    damage_group: str | None = None,
    axis: int = 1,
) -> None:
    """Two chords, transverse rungs, and alternating diagonals: a real lattice derrick."""
    a, b = Vector(start), Vector(end)
    offset = Vector((0.0, 0.0, 0.0))
    offset[axis] = spread * 0.5
    for sign in (-1, 1):
        chord_a = a + offset * sign
        chord_b = b + offset * sign
        parts.append(beam(f"{prefix} chord {sign}", tuple(chord_a), tuple(chord_b), width, region, material, damage_group))
    for bay in range(bays + 1):
        t = bay / bays
        point = a.lerp(b, t)
        parts.append(
            beam(
                f"{prefix} rung {bay}",
                tuple(point - offset),
                tuple(point + offset),
                width * 0.62,
                brace_region,
                material,
                damage_group,
            )
        )
    for bay in range(bays):
        low = a.lerp(b, bay / bays)
        high = a.lerp(b, (bay + 1) / bays)
        near, far = (-1, 1) if bay % 2 == 0 else (1, -1)
        parts.append(
            beam(
                f"{prefix} diagonal {bay}",
                tuple(low + offset * near),
                tuple(high + offset * far),
                width * 0.50,
                brace_region,
                material,
                damage_group,
            )
        )


def chain_run(
    parts: list[bpy.types.Object],
    prefix: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    links: int,
    radius: float,
    region: str,
    material: bpy.types.Material,
    damage_group: str | None = None,
) -> None:
    """Alternating perpendicular links. The plate's chains are load-bearing, not painted.

    A link's plane CONTAINS the run direction, so the torus axis must be perpendicular to it.
    Consecutive links alternate between the two perpendiculars, which is what reads as a chain.
    """
    a, b = Vector(start), Vector(end)
    direction = (b - a).normalized()
    seed = Vector((0.0, 0.0, 1.0)) if abs(direction.z) < 0.90 else Vector((1.0, 0.0, 0.0))
    first = direction.cross(seed).normalized()
    second = direction.cross(first).normalized()
    for link in range(links):
        centre = a.lerp(b, (link + 0.5) / links)
        axis = first if link % 2 == 0 else second
        parts.append(
            torus(
                f"{prefix} link {link}",
                radius,
                radius * 0.34,
                tuple(centre),
                region,
                material,
                rotation=tuple(axis.to_track_quat("Z", "Y").to_euler()),
                damage_group=damage_group,
                major_segments=6,
                minor_segments=4,
            )
        )


def swept_tube(
    name: str,
    points: list[tuple[float, float, float]],
    radii: list[float],
    region: str,
    material: bpy.types.Material,
    sides: int = 8,
    damage_group: str | None = None,
    smooth: bool = True,
) -> bpy.types.Object:
    """A tapering tube swept along a curve, parallel-transported so it never twists.

    This is what buys a real curved talon or cable: a beam chain reads as sticks,
    a swept tube reads as a claw, and it costs fewer triangles than beams+knuckles.
    """
    assert len(points) == len(radii) >= 2
    path = [Vector(point) for point in points]
    tangents = []
    for index in range(len(path)):
        if index == 0:
            tangent = path[1] - path[0]
        elif index == len(path) - 1:
            tangent = path[-1] - path[-2]
        else:
            tangent = path[index + 1] - path[index - 1]
        tangents.append(tangent.normalized())
    seed = Vector((0.0, 0.0, 1.0)) if abs(tangents[0].z) < 0.90 else Vector((1.0, 0.0, 0.0))
    right = tangents[0].cross(seed).normalized()
    rings: list[list[tuple[float, float, float]]] = []
    for index, (centre, tangent, radius) in enumerate(zip(path, tangents, radii)):
        if index > 0:
            # parallel transport: re-project the previous frame onto the new normal plane
            right = (right - tangent * right.dot(tangent))
            right = right.normalized() if right.length > 1e-6 else tangent.cross(seed).normalized()
        up = tangent.cross(right).normalized()
        ring = []
        for step in range(sides):
            angle = math.tau * step / sides
            offset = right * (math.cos(angle) * radius) + up * (math.sin(angle) * radius)
            ring.append(tuple(centre + offset))
        rings.append(ring)
    return loft(name, rings, region, material, damage_group=damage_group, smooth=smooth)


def arc_points(
    centre: tuple[float, float, float],
    radius: float,
    start_angle: float,
    end_angle: float,
    steps: int,
    plane: str = "xz",
) -> list[tuple[float, float, float]]:
    points = []
    for step in range(steps + 1):
        angle = start_angle + (end_angle - start_angle) * step / steps
        cos, sin = math.cos(angle) * radius, math.sin(angle) * radius
        if plane == "xz":
            points.append((centre[0] + cos, centre[1], centre[2] + sin))
        elif plane == "xy":
            points.append((centre[0] + cos, centre[1] + sin, centre[2]))
        else:
            points.append((centre[0], centre[1] + cos, centre[2] + sin))
    return points


def polyline(
    parts: list[bpy.types.Object],
    prefix: str,
    points: list[tuple[float, float, float]],
    width: float,
    region: str,
    material: bpy.types.Material,
    damage_group: str | None = None,
) -> None:
    for index, (start, end) in enumerate(zip(points, points[1:])):
        parts.append(beam(f"{prefix} {index}", start, end, width, region, material, damage_group))


def rivet_line(
    parts: list[bpy.types.Object],
    prefix: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    count: int,
    radius: float,
    material: bpy.types.Material,
    region: str = "brass",
    damage_group: str | None = None,
    rotation: tuple[float, float, float] = (math.pi / 2, 0, 0),
) -> None:
    a, b = Vector(start), Vector(end)
    for index in range(count):
        at = a.lerp(b, (index + 0.5) / count)
        parts.append(
            cylinder(
                f"{prefix} rivet {index}",
                radius,
                radius * 1.3,
                tuple(at),
                region,
                material,
                vertices=6,
                rotation=rotation,
                bevel=0,
                damage_group=damage_group,
            )
        )


def lens(
    parts: list[bpy.types.Object],
    name: str,
    radius: float,
    at: tuple[float, float, float],
    material: bpy.types.Material,
    rotation: tuple[float, float, float] = (math.pi / 2, 0, 0),
    damage_group: str | None = None,
    region: str = "teal",
) -> None:
    """A restrained teal eye in a brass bezel. Painted, never emissive."""
    parts.append(
        cylinder(f"{name} lens", radius, radius * 0.42, at, region, material, vertices=10, rotation=rotation, bevel=0, damage_group=damage_group)
    )
    parts.append(
        torus(f"{name} bezel", radius * 1.16, radius * 0.20, at, "brass", material, rotation=rotation, damage_group=damage_group, major_segments=10)
    )


# --------------------------------------------------------------------------------------
# assembly, normalisation, export (shipped contract, unchanged)
# --------------------------------------------------------------------------------------


def prepare_part(obj: bpy.types.Object, regions: dict[str, tuple[float, float, float, float]]) -> None:
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
    u0, v0, u1, v1 = regions[obj["atlas_region"]]
    for loop, coord in zip(uv, coords):
        normalized = (coord - low) / span
        loop.uv = (u0 + normalized[0] * (u1 - u0), v0 + normalized[1] * (v1 - v0))
    obj.select_set(False)


def join_component(
    name: str,
    parts: list[bpy.types.Object],
    material: bpy.types.Material,
    regions: dict[str, tuple[float, float, float, float]],
) -> bpy.types.Object:
    for part in parts:
        prepare_part(part, regions)
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


def triangle_count(objects: tuple[bpy.types.Object, ...]) -> int:
    return sum(sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons) for obj in objects)


def world_bounds(objects: tuple[bpy.types.Object, ...]) -> tuple[Vector, Vector]:
    points = [obj.matrix_world @ vertex.co for obj in objects for vertex in obj.data.vertices]
    return (
        Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points))),
        Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points))),
    )


def normalize_base_center(objects: tuple[bpy.types.Object, ...], axis: int, target: float) -> None:
    """Scale on one axis to the shipped footprint, centre X/Y, sit the base on z=0."""
    minimum, maximum = world_bounds(objects)
    center_x = (minimum.x + maximum.x) * 0.5
    center_y = (minimum.y + maximum.y) * 0.5
    scale = target / ((maximum - minimum)[axis])
    for obj in objects:
        for vertex in obj.data.vertices:
            vertex.co.x = (vertex.co.x - center_x) * scale
            vertex.co.y = (vertex.co.y - center_y) * scale
            vertex.co.z = (vertex.co.z - minimum.z) * scale
        obj.data.update()


def export(objects: tuple[bpy.types.Object, ...], blend: Path, glb: Path) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(
        filepath=str(glb.with_suffix("")),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_materials="EXPORT",
        export_morph=True,
    )
