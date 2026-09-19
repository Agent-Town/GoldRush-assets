from pathlib import Path
from math import cos, pi, sin

import bpy


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "tavern-2-fullwrap.blend"
BLEND = ROOT / "town-v3-tavern.blend"
GLB = ROOT / "town-v3-tavern.glb"
TARGET_DIMENSIONS = (4.2295708656, 3.3489999771, 3.9608023167)


def add_consistency_repairs(tavern: bpy.types.Object) -> None:
    source_dimensions = tuple(tavern.dimensions)
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []

    # Close the false-front crest with a thin annular backing directly behind
    # its trim. The existing tan center remains untouched; the band only fills
    # the sky-colored crescent visible from rear three-quarter views.
    center_x = 0.006
    spring_z = 2.880
    segments = 12
    count = segments + 1
    for y in (-1.339, -1.323):
        vertices.extend(
            (center_x + 0.810 * cos(pi * step / segments), y, spring_z + 0.790 * sin(pi * step / segments))
            for step in range(count)
        )
        vertices.extend(
            (center_x + 0.665 * cos(pi * step / segments), y, spring_z + 0.675 * sin(pi * step / segments))
            for step in range(count)
        )
    outer_front = 0
    inner_front = count
    outer_back = count * 2
    inner_back = count * 3
    for index in range(segments):
        next_index = index + 1
        faces.extend(
            (
                (outer_front + index, outer_front + next_index, inner_front + next_index, inner_front + index),
                (outer_back + index, inner_back + index, inner_back + next_index, outer_back + next_index),
                (outer_front + index, outer_back + index, outer_back + next_index, outer_front + next_index),
                (inner_front + index, inner_front + next_index, inner_back + next_index, inner_back + index),
            )
        )
    faces.extend(
        (
            (outer_front, inner_front, inner_back, outer_back),
            (outer_front + segments, outer_back + segments, inner_back + segments, inner_front + segments),
        )
    )
    arch_vertex_count = len(vertices)

    # Two compact straps make the projecting sign visibly load-bearing.
    def add_box(center: tuple[float, float, float], size: tuple[float, float, float]) -> None:
        base = len(vertices)
        cx, cy, cz = center
        sx, sy, sz = (value / 2 for value in size)
        vertices.extend(
            (cx + x * sx, cy + y * sy, cz + z * sz)
            for x, y, z in (
                (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
            )
        )
        faces.extend(
            tuple(base + index for index in face)
            for face in (
                (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
            )
        )

    add_box((-2.390, -1.3766, 2.080), (0.040, 0.060, 0.180))
    add_box((-2.215, -1.3766, 2.080), (0.040, 0.060, 0.180))

    mesh = bpy.data.meshes.new("TavernConsistencyRepairs")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            if vertex_index < arch_vertex_count:
                x, _, z = vertices[vertex_index]
                uv_layer.data[loop_index].uv = (
                    0.03 + 0.19 * (x - (center_x - 0.810)) / 1.620,
                    0.03 + 0.19 * (z - spring_z) / 0.790,
                )
            else:
                uv_layer.data[loop_index].uv = (0.12, 0.12)

    repair = bpy.data.objects.new("TavernConsistencyRepairs", mesh)
    bpy.context.collection.objects.link(repair)
    repair.data.materials.append(tavern.data.materials[0])
    bpy.ops.object.select_all(action="DESELECT")
    tavern.select_set(True)
    repair.select_set(True)
    bpy.context.view_layer.objects.active = tavern
    bpy.ops.object.join()
    for polygon in tavern.data.polygons:
        polygon.material_index = 0
    while len(tavern.data.materials) > 1:
        tavern.data.materials.pop(index=len(tavern.data.materials) - 1)

    assert len(tavern.data.materials) == 1
    assert tuple(tavern.dimensions) == source_dimensions


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    tavern = bpy.data.objects["Tavern_2_FullWrap_Painted"]
    add_consistency_repairs(tavern)
    for axis, target in enumerate(TARGET_DIMENSIONS):
        tavern.scale[axis] *= target / tavern.dimensions[axis]
    bpy.context.view_layer.objects.active = tavern
    tavern.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    tavern.name = "TownTavernFullWrap"
    tavern["repair_source"] = SOURCE.name
    tavern["repair_contract"] = "production bounds preserved; full wrap, backed crest, attached hanging sign"
    assert all(abs(tavern.dimensions[index] - target) < 0.0001 for index, target in enumerate(TARGET_DIMENSIONS))

    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.export_scene.gltf(
        filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT",
    )


if __name__ == "__main__":
    main()
