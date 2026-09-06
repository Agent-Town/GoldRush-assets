from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parent
ATLAS = ROOT / "era-props-e9-atlas.png"
SIZE = 1024
COLUMNS = 4
E1_GREEN = (0x50 / 255.0, 0x67 / 255.0, 0x4C / 255.0)
PALETTE = (
    (0.13, 0.035, 0.018), (0.25, 0.065, 0.025), (0.43, 0.12, 0.045), (0.60, 0.24, 0.08),
    (0.13, 0.065, 0.035), (0.10, 0.20, 0.19), (0.08, 0.34, 0.35), (0.30, 0.63, 0.62),
    (0.07, 0.065, 0.058), (0.20, 0.16, 0.11), (0.50, 0.35, 0.14), (0.72, 0.60, 0.35),
    (0.30, 0.13, 0.065), (0.38, 0.24, 0.13), (0.68, 0.78, 0.76), E1_GREEN,
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


common = load_module("era_props_e9_common", ROOT / "build_era_props_e2.py")
common.ATLAS = ATLAS
common.PALETTE = PALETTE


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_shared_atlas() -> None:
    """Paint one atlas for the pack and preserve the E1 green as literal PNG pixels."""
    common.reset()
    pixels = np.ones((SIZE, SIZE, 4), dtype=np.float32)
    cell = SIZE // COLUMNS
    rng = np.random.default_rng(909)
    for index, color in enumerate(PALETTE):
        column, row = index % COLUMNS, index // COLUMNS
        x0, y0 = column * cell, row * cell
        block = np.array(color, dtype=np.float32) + rng.normal(0, 0.009, (cell, cell, 1))
        pixels[y0:y0 + cell, x0:x0 + cell, :3] = np.clip(block, 0.015, 0.90)
        for x in range(x0 + 27, x0 + cell, 43):
            pixels[y0:y0 + cell, x:x + 2, :3] *= 0.74
        for y in range(y0 + 33, y0 + cell, 71):
            pixels[y:y + 2, x0:x0 + cell, :3] *= 0.82
    # The callback is a swatch contract. Keep a large interior core exactly
    # #50674c after all engraving/noise so export verification can prove it.
    green_x0, green_y0 = 3 * cell, 3 * cell
    pixels[green_y0 + 32:green_y0 + cell - 32, green_x0 + 32:green_x0 + cell - 32, :3] = E1_GREEN
    image = bpy.data.images.new("E9RedfieldsPropsSharedAtlas", SIZE, SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(pixels.ravel())
    image.filepath_raw = str(ATLAS)
    image.file_format = "PNG"
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.image_settings.color_mode = "RGBA"
    bpy.context.scene.render.image_settings.color_depth = "8"
    image.save()


def material() -> bpy.types.Material:
    result = common.material_from_atlas()
    result.name = "E9RedfieldsPropsSharedMaterial"
    return result


def beam(name: str, start, end, radius: float, mat, palette: int, vertices: int = 6):
    start, end = Vector(start), Vector(end)
    delta = end - start
    obj = common.cylinder(name, radius, delta.length, (start + end) * 0.5, mat, palette, vertices)
    for modifier in list(obj.modifiers):
        obj.modifiers.remove(modifier)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def stone(name: str, location, scale, mat, palette: int):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return common.tag(obj, mat, palette, 0)


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
    model["epoch_variant"] = "E9 Red Fields"
    model["site_reset"] = "fresh Basin Rim fixture; no E8 dome geometry imported"
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


def build_canal(state: str, palette: int, accent: int) -> dict:
    common.reset()
    mat = material()
    parts = [
        common.box(f"{state} canal bed", (4.80, 1.46, 0.024), (0, 0, 0.012), mat, palette, 0),
        common.box(f"{state} canal north bank paint", (4.80, 0.12, 0.012), (0, 0.67, 0.030), mat, 12, 0),
        common.box(f"{state} canal south bank paint", (4.80, 0.12, 0.012), (0, -0.67, 0.030), mat, 12, 0),
    ]
    if state == "dry":
        for index, x in enumerate((-1.55, -0.72, 0.18, 1.10, 1.82), 1):
            parts.append(common.box(
                f"Dry canal crack {index}", (0.52, 0.045, 0.010), (x, (-1) ** index * 0.18, 0.031),
                mat, 8, 0, rotation=(0, 0, (-1) ** index * 0.48),
            ))
    elif state == "wet":
        for index, x in enumerate((-1.55, -0.62, 0.40, 1.42), 1):
            parts.append(common.box(
                f"Wet canal seep {index}", (0.72, 0.54, 0.010), (x, (-1) ** index * 0.11, 0.031),
                mat, accent, 0, rotation=(0, 0, (-1) ** index * 0.08),
            ))
    else:
        parts.append(common.box("Flowing canal water", (4.64, 0.92, 0.012), (0, 0, 0.031), mat, accent, 0))
        for index, x in enumerate((-1.65, -0.82, 0.02, 0.86, 1.68), 1):
            parts.append(common.box(
                f"Flow ripple {index}", (0.34, 0.035, 0.008), (x, (-1) ** index * 0.20, 0.042),
                mat, 7, 0, rotation=(0, 0, (-1) ** index * 0.32),
            ))
        # The final reach carries the literal E1 riverbank green callback.
        parts.extend((
            common.box("Flowing canal green north seam", (4.80, 0.10, 0.010), (0, 0.53, 0.041), mat, 15, 0),
            common.box("Flowing canal green south seam", (4.80, 0.10, 0.010), (0, -0.53, 0.041), mat, 15, 0),
        ))
    return finish(f"CanalSegment{state.title()}E9", f"canal-segment-{state}.e9", parts)


def build_ice_blocks() -> dict:
    common.reset()
    mat = material()
    parts: list[bpy.types.Object] = [
        common.box("Ice drag mat", (2.50, 1.65, 0.08), (0, 0, 0.04), mat, 9, 0),
    ]
    blocks = (
        (-0.72, -0.24, 0.46, (0.76, 0.62, 0.86), -0.08),
        (0.05, -0.30, 0.39, (0.68, 0.58, 0.72), 0.12),
        (0.72, -0.18, 0.44, (0.72, 0.64, 0.82), -0.16),
        (-0.35, 0.34, 0.92, (0.70, 0.56, 0.72), 0.18),
        (0.38, 0.31, 0.87, (0.66, 0.54, 0.66), -0.10),
    )
    for index, (x, y, z, size, rotation) in enumerate(blocks, 1):
        parts.append(common.box(f"Cut ice block {index}", size, (x, y, z), mat, 14, 0.025, rotation=(0, 0, rotation)))
        parts.append(common.box(
            f"Cut ice teal seam {index}", (size[0] * 0.74, size[1] + 0.016, 0.035),
            (x, y, z + size[2] * 0.18), mat, 7, 0, rotation=(0, 0, rotation),
        ))
    parts.extend((
        common.torus("Ice block drag rope", 0.36, 0.035, (0.93, 0.50, 0.13), mat, 10, segments=(12, 4)),
        beam("Ice block drag hook", (1.12, 0.46, 0.11), (1.36, 0.60, 0.11), 0.035, mat, 10, 6),
    ))
    return finish("IceBlocksE9", "ice-blocks.e9", parts)


def build_survey_cairn() -> dict:
    common.reset()
    mat = material()
    parts: list[bpy.types.Object] = []
    stones = (
        (-0.22, -0.08, 0.18, (0.38, 0.31, 0.18), 2),
        (0.20, -0.04, 0.17, (0.34, 0.30, 0.17), 1),
        (-0.02, 0.18, 0.20, (0.40, 0.28, 0.20), 3),
        (0.02, 0.00, 0.43, (0.30, 0.25, 0.18), 12),
        (-0.05, 0.02, 0.64, (0.24, 0.21, 0.15), 3),
    )
    for index, (x, y, z, scale, palette) in enumerate(stones, 1):
        parts.append(stone(f"Survey cairn stone {index}", (x, y, z), scale, mat, palette))
    parts.extend((
        beam("Survey cairn pole", (0.42, 0.18, 0.08), (0.42, 0.18, 1.72), 0.035, mat, 10, 6),
        common.torus("Survey water target", 0.16, 0.028, (0.42, 0.15, 1.45), mat, 7,
                     rotation=(math.pi / 2, 0, 0), segments=(10, 4)),
        beam("Survey target cross west-east", (0.28, 0.145, 1.45), (0.56, 0.145, 1.45), 0.016, mat, 7, 4),
        beam("Survey target cross low-high", (0.42, 0.145, 1.31), (0.42, 0.145, 1.59), 0.016, mat, 7, 4),
        common.box("Survey green claim tile", (0.30, 0.24, 0.035), (-0.44, -0.22, 0.035), mat, 15, 0),
    ))
    return finish("SurveyCairnE9", "survey-cairn.e9", parts)


def scaffold_frame(parts: list[bpy.types.Object], mat, height: float, half_x: float, half_y: float, tier: int) -> None:
    for index, (x, y) in enumerate(((-half_x, -half_y), (half_x, -half_y), (half_x, half_y), (-half_x, half_y)), 1):
        parts.extend((
            common.box(f"Stage {tier} foot {index}", (0.34, 0.34, 0.10), (x, y, 0.05), mat, 8, 0),
            beam(f"Stage {tier} upright {index}", (x, y, 0.10), (x, y, height), 0.055, mat, 13, 6),
        ))
    corners = ((-half_x, -half_y), (half_x, -half_y), (half_x, half_y), (-half_x, half_y))
    for index, ((ax, ay), (bx, by)) in enumerate(zip(corners, corners[1:] + corners[:1]), 1):
        parts.append(beam(f"Stage {tier} crown beam {index}", (ax, ay, height), (bx, by, height), 0.060, mat, 10, 6))


def build_scaffold(stage: int) -> dict:
    common.reset()
    mat = material()
    half_x = 0.86 + stage * 0.18
    half_y = 0.66 + stage * 0.10
    height = 0.78 + stage * 0.68
    parts: list[bpy.types.Object] = [
        common.box(f"Ark stage {stage} keel bed", (half_x * 2.15, 0.28, 0.18), (0, 0, 0.09), mat, 8, 0),
        common.box(f"Ark stage {stage} build sled west", (0.24, half_y * 2.2, 0.14), (-half_x, 0, 0.07), mat, 9, 0),
        common.box(f"Ark stage {stage} build sled east", (0.24, half_y * 2.2, 0.14), (half_x, 0, 0.07), mat, 9, 0),
    ]
    scaffold_frame(parts, mat, height, half_x, half_y, stage)
    for side in (-1, 1):
        parts.extend((
            beam(f"Stage {stage} side rib {side} A", (side * half_x, -half_y, 0.16), (side * half_x, half_y, height), 0.035, mat, 11, 6),
            beam(f"Stage {stage} side rib {side} B", (side * half_x, half_y, 0.16), (side * half_x, -half_y, height), 0.035, mat, 11, 6),
        ))
    # Each later sibling is a genuine visible build state, never a texture-only swap.
    if stage >= 2:
        for index, x in enumerate((-0.62, 0, 0.62), 1):
            parts.append(beam(
                f"Stage {stage} hull rib {index}", (x, -half_y * 0.78, 0.20),
                (x, half_y * 0.78, height * 0.86), 0.065, mat, 13, 8,
            ))
        parts.extend((
            common.box(f"Stage {stage} teal blueprint table", (0.82, 0.48, 0.08), (0, -half_y - 0.22, 0.74), mat, 6, 0),
            beam(f"Stage {stage} blueprint west leg", (-0.33, -half_y - 0.22, 0.10), (-0.33, -half_y - 0.22, 0.70), 0.035, mat, 10),
            beam(f"Stage {stage} blueprint east leg", (0.33, -half_y - 0.22, 0.10), (0.33, -half_y - 0.22, 0.70), 0.035, mat, 10),
        ))
    if stage >= 3:
        mast = height + 1.20
        parts.extend((
            beam("Stage 3 Ark prow mast", (0, 0, height), (0, 0, mast), 0.08, mat, 10, 8),
            common.torus("Stage 3 Ark water crest", 0.22, 0.035, (0, -0.05, mast - 0.20), mat, 7,
                         rotation=(math.pi / 2, 0, 0), segments=(12, 4)),
            beam("Stage 3 Ark gangway", (-half_x - 0.66, -half_y, 0.18), (-half_x, -half_y, height * 0.54), 0.07, mat, 13, 8),
            common.box("Stage 3 patched hull sheet", (half_x * 1.22, 0.06, height * 0.52),
                       (0, half_y - 0.03, height * 0.52), mat, 3, 0),
        ))
    return finish(f"ArkScaffoldStage{stage}E9", f"ark-scaffold-stage-{stage}.e9", parts)


def main() -> None:
    write_shared_atlas()
    results = [
        build_canal("dry", 4, 5),
        build_canal("wet", 5, 6),
        build_canal("flowing", 6, 6),
        build_ice_blocks(),
        build_survey_cairn(),
        *(build_scaffold(stage) for stage in (1, 2, 3)),
    ]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
