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
ATLAS = ROOT / "era-props-e10-atlas.png"
SIZE = 1024
COLUMNS = 4
PALETTE = (
    (0.025, 0.030, 0.040), (0.055, 0.075, 0.085), (0.075, 0.16, 0.17), (0.09, 0.30, 0.31),
    (0.11, 0.50, 0.50), (0.31, 0.68, 0.64), (0.14, 0.095, 0.055), (0.31, 0.18, 0.08),
    (0.54, 0.34, 0.12), (0.78, 0.58, 0.25), (0.16, 0.15, 0.14), (0.34, 0.34, 0.31),
    (0.62, 0.61, 0.54), (0.79, 0.77, 0.66), (0.31, 0.40, 0.29), (0.50, 0.70, 0.48),
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


common = load_module("era_props_e10_common", ROOT / "build_era_props_e2.py")
common.ATLAS = ATLAS
common.PALETTE = PALETTE


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_shared_atlas() -> None:
    common.reset()
    pixels = np.ones((SIZE, SIZE, 4), dtype=np.float32)
    cell = SIZE // COLUMNS
    rng = np.random.default_rng(1010)
    for index, color in enumerate(PALETTE):
        column, row = index % COLUMNS, index // COLUMNS
        x0, y0 = column * cell, row * cell
        block = np.array(color, dtype=np.float32) + rng.normal(0, 0.008, (cell, cell, 1))
        pixels[y0:y0 + cell, x0:x0 + cell, :3] = np.clip(block, 0.012, 0.90)
        for x in range(x0 + 19, x0 + cell, 37):
            pixels[y0:y0 + cell, x:x + 2, :3] *= 0.76
        for y in range(y0 + 29, y0 + cell, 61):
            pixels[y:y + 2, x0:x0 + cell, :3] *= 0.82
    image = bpy.data.images.new("E10ArkPropsSharedAtlas", SIZE, SIZE, alpha=True)
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
    result.name = "E10ArkPropsSharedMaterial"
    return result


def beam(name: str, start, end, radius: float, mat, palette: int, vertices: int = 6):
    start, end = Vector(start), Vector(end)
    delta = end - start
    obj = common.cylinder(name, radius, delta.length, (start + end) * 0.5, mat, palette, vertices)
    for modifier in list(obj.modifiers):
        obj.modifiers.remove(modifier)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def sphere(name: str, location, scale, mat, palette: int):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return common.tag(obj, mat, palette, 0)


def finish(name: str, stem: str, parts: list[bpy.types.Object], triangle_limit: int = 1_000) -> dict:
    # These fixtures earn their silhouette from round reels/globes, not a bevel
    # multiplier on every hidden cabinet edge. Keep topology for visible forms.
    for part in parts:
        for modifier in list(part.modifiers):
            part.modifiers.remove(modifier)
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
    model["epoch_variant"] = "E10 Deep Sky Ark"
    model["site_reset"] = "fresh Ark deck fixture; no Basin Rim geometry imported"
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
        "id": stem, "triangles": triangles,
        "dimensions": [round(value, 6) for value in model.dimensions], "sha256": sha256(glb),
    }


def build_bridge_school() -> dict:
    common.reset()
    mat = material()
    parts: list[bpy.types.Object] = [
        common.box("Bridge school deck mat", (3.35, 2.25, 0.08), (0, 0, 0.04), mat, 6, 0),
        common.box("Bridge school console body", (3.10, 0.70, 0.92), (0, 0.42, 0.54), mat, 1, 0.035),
        common.box("Bridge school world window", (2.58, 0.08, 0.52), (0, 0.04, 0.72), mat, 3, 0.02),
        common.box("Bridge school console crown", (3.30, 0.82, 0.13), (0, 0.42, 1.08), mat, 8, 0.025),
    ]
    for index, x in enumerate((-1.05, 0.0, 1.05), 1):
        parts.extend((
            common.cylinder(f"Bridge school student stool {index}", 0.24, 0.38, (x, -0.68, 0.19), mat, 7, 10),
            common.cylinder(f"Bridge school stool cushion {index}", 0.30, 0.10, (x, -0.68, 0.42), mat, 9, 10),
            common.torus(f"Bridge school lesson dial {index}", 0.17, 0.03, (x, 0.00, 0.74), mat, 5,
                         rotation=(math.pi / 2, 0, 0), segments=(8, 3)),
        ))
    parts.extend((
        sphere("Bridge school charter globe", (0, 0.48, 1.66), (0.43, 0.43, 0.43), mat, 4),
        common.torus("Bridge school globe orbit north", 0.56, 0.025, (0, 0.48, 1.66), mat, 9,
                     rotation=(0.0, 0.45, 0.0), segments=(12, 3)),
        common.torus("Bridge school globe orbit east", 0.56, 0.025, (0, 0.48, 1.66), mat, 5,
                     rotation=(math.pi / 2, 0.0, 0.0), segments=(12, 3)),
        beam("Bridge school globe stand", (0, 0.48, 1.04), (0, 0.48, 1.30), 0.055, mat, 8, 8),
        common.box("Bridge school child lever", (0.12, 0.12, 0.72), (1.42, -0.02, 0.47), mat, 9, 0.015,
                   rotation=(0, 0.0, -0.28)),
        common.cylinder("Bridge school lever grip", 0.10, 0.22, (1.51, -0.02, 0.82), mat, 5, 8,
                        rotation=(0, math.pi / 2, 0)),
    ))
    return finish("BridgeSchoolE10", "bridge-school.e10", parts)


def build_charter_press() -> dict:
    common.reset()
    mat = material()
    parts: list[bpy.types.Object] = [
        common.box("Charter press deck plate", (3.25, 1.90, 0.10), (0, 0, 0.05), mat, 1, 0),
        common.box("Charter press lower cabinet", (2.70, 1.34, 0.82), (0, 0.15, 0.51), mat, 10, 0.04),
        common.box("Charter press platen", (1.72, 1.12, 0.18), (0, -0.12, 1.04), mat, 12, 0.025),
        common.box("Charter press crown", (3.05, 0.44, 0.24), (0, 0.48, 2.43), mat, 8, 0.04),
    ]
    for side in (-1, 1):
        x = side * 1.22
        parts.extend((
            beam(f"Charter press arch post {side}", (x, 0.44, 0.88), (x, 0.44, 2.40), 0.085, mat, 8, 8),
            common.torus(f"Charter press tape reel {side}", 0.42, 0.065, (x, 0.20, 1.92), mat, 9,
                         rotation=(math.pi / 2, 0, 0), segments=(14, 5)),
            common.cylinder(f"Charter press tape reel hub {side}", 0.13, 0.10, (x, 0.17, 1.92), mat, 4, 10,
                            rotation=(math.pi / 2, 0, 0)),
        ))
    parts.extend((
        beam("Charter press tape span", (-0.80, 0.17, 1.92), (0.80, 0.17, 1.92), 0.025, mat, 5, 5),
        common.box("Charter press paper charter", (1.50, 0.78, 0.035), (0, -0.30, 1.15), mat, 13, 0),
        common.box("Charter press child lever", (0.13, 0.13, 1.22), (1.54, -0.42, 0.78), mat, 9, 0.015,
                   rotation=(0, 0, -0.40)),
        common.cylinder("Charter press child lever grip", 0.12, 0.28, (1.72, -0.42, 1.29), mat, 5, 8,
                        rotation=(0, math.pi / 2, 0)),
        common.torus("Charter press preserve seal", 0.27, 0.045, (0, -0.69, 0.56), mat, 4,
                     rotation=(math.pi / 2, 0, 0), segments=(12, 4)),
        beam("Charter press seal pan handle", (0.18, -0.70, 0.40), (0.43, -0.70, 0.18), 0.025, mat, 9, 5),
    ))
    return finish("CharterPressE10", "charter-press.e10", parts)


def build_preserve_rack() -> dict:
    common.reset()
    mat = material()
    parts: list[bpy.types.Object] = [
        common.box("Preserve rack foot", (3.30, 1.45, 0.10), (0, 0, 0.05), mat, 1, 0),
        common.box("Preserve rack back", (3.10, 0.16, 2.18), (0, 0.57, 1.15), mat, 10, 0.035),
    ]
    for x in (-1.42, 1.42):
        parts.append(beam(f"Preserve rack rib {x}", (x, -0.52, 0.08), (x, 0.57, 2.36), 0.065, mat, 8, 8))
    for tier, z in enumerate((0.58, 1.23, 1.88), 1):
        parts.extend((
            common.box(f"Preserve rack shelf {tier}", (2.90, 1.14, 0.10), (0, 0.04, z), mat, 7, 0.02),
            common.torus(f"Preserve rack blank trophy cradle {tier}", 0.24, 0.045, (-0.78 + tier * 0.38, -0.39, z + 0.25), mat,
                         9 if tier != 2 else 5, rotation=(math.pi / 2, 0, 0), segments=(10, 4)),
        ))
    parts.extend((
        common.box("Preserve rack E1 green tray", (1.38, 0.62, 0.20), (-0.62, -0.20, 0.20), mat, 14, 0.025),
        sphere("Preserve rack green sprout west", (-0.88, -0.20, 0.45), (0.12, 0.12, 0.22), mat, 15),
        sphere("Preserve rack green sprout east", (-0.37, -0.20, 0.43), (0.14, 0.14, 0.19), mat, 15),
        common.box("Preserve rack patched crate", (0.78, 0.66, 0.58), (0.93, -0.16, 0.34), mat, 6, 0.035),
        beam("Preserve rack crate patch", (0.63, -0.51, 0.18), (1.20, -0.51, 0.51), 0.035, mat, 8, 5),
    ))
    return finish("PreserveRackE10", "preserve-rack.e10", parts)


def build_engine_glow(state: str, core_palette: int, cage: bool) -> dict:
    common.reset()
    mat = material()
    parts: list[bpy.types.Object] = [
        common.box(f"Engine {state} hull plate", (4.20, 1.30, 0.18), (0, 0.38, 0.09), mat, 1, 0),
        common.box(f"Engine {state} service spine", (3.70, 0.32, 1.16), (0, 0.58, 0.72), mat, 10, 0.035),
    ]
    for index, x in enumerate((-1.28, 0.0, 1.28), 1):
        length = {"idle": 0.42, "cruise": 0.72, "ward": 0.58}[state]
        parts.extend((
            common.cylinder(f"Engine {state} nozzle {index}", 0.38, 0.58, (x, 0.05, 0.70), mat, 8, 12,
                            rotation=(math.pi / 2, 0, 0)),
            common.torus(f"Engine {state} glow ring {index}", 0.39, 0.055, (x, -0.25, 0.70), mat, core_palette,
                         rotation=(math.pi / 2, 0, 0), segments=(12, 4)),
            common.cylinder(f"Engine {state} glow core {index}", 0.25, length, (x, -0.30 - length * 0.5, 0.70),
                            mat, core_palette, 12, rotation=(math.pi / 2, 0, 0)),
        ))
        if state != "idle":
            parts.extend((
                common.box(f"Engine {state} fin west {index}", (0.08, 0.64, 0.54), (x - 0.40, -0.10, 0.70), mat, 8, 0.01),
                common.box(f"Engine {state} fin east {index}", (0.08, 0.64, 0.54), (x + 0.40, -0.10, 0.70), mat, 8, 0.01),
            ))
    if cage:
        parts.extend((
            beam("Engine ward cage west", (-1.90, -0.62, 0.18), (-1.90, -0.62, 1.42), 0.045, mat, 9, 6),
            beam("Engine ward cage east", (1.90, -0.62, 0.18), (1.90, -0.62, 1.42), 0.045, mat, 9, 6),
            beam("Engine ward cage crown", (-1.90, -0.62, 1.42), (1.90, -0.62, 1.42), 0.045, mat, 9, 6),
        ))
    return finish(f"EngineGlow{state.title()}E10", f"engine-glow-{state}.e10", parts)


def main() -> None:
    write_shared_atlas()
    print(json.dumps([
        build_bridge_school(), build_charter_press(), build_preserve_rack(),
        build_engine_glow("idle", 3, False),
        build_engine_glow("cruise", 5, False),
        build_engine_glow("ward", 9, True),
    ], indent=2))


if __name__ == "__main__":
    main()
