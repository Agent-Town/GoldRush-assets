from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


common = load_module("wave10_e5_common", HERE / "build_wave7b_variants.py")
tavern_e2 = load_module("wave10_e5_tavern_uv", HERE / "build_tavern_e2.py")


STANDARD = common.STANDARD_REGIONS
DYNAMO = common.DYNAMO_REGIONS


def spec(directory, stem, source, object_name, output, blend_sha, glb_sha, uv):
    return {
        "directory": directory,
        "stem": stem,
        "source": source,
        "object": object_name,
        "output": output,
        "blend_sha": blend_sha,
        "glb_sha": glb_sha,
        "uv": uv,
    }


SPECS = {
    "tavern": spec(
        "tavern-3d", "tavern", "town-v3-tavern", "TownTavernFullWrap", "TownTavernE5",
        "b81ef19a24661c3ea97feb3b7f75caceef5599954d6462b1bbd2ab6085ade2fe",
        "edec4934d6d956170078b521fe526ccadcde015567094aec59001e2d4b71b90d",
        {"dark": tavern_e2.UV_DARK, "timber": tavern_e2.UV_WOOD,
         "roof": tavern_e2.UV_ROOF, "rope": tavern_e2.UV_BRASS, "teal": tavern_e2.UV_TEAL},
    ),
    "general_store": spec(
        "general-store-3d", "general-store", "general-store", "GeneralStoreFullWrap", "GeneralStoreE5",
        "7dcd16a3538931e1772278ddbac1f8b26e190b1ddff4e1670b7fb72b0d8fac4e",
        "b5f254861353b3ba7f3cf52d8ab1bffffc176cb2226d5edba50d85639163c154",
        {"dark": STANDARD["window"], "timber": STANDARD["wall"], "roof": STANDARD["roof"],
         "rope": STANDARD["accent"], "teal": STANDARD["stone"]},
    ),
    "claim_office": spec(
        "claim-office-3d", "claim-office", "claim-office", "ClaimOfficeFullWrap", "ClaimOfficeE5",
        "46a2f73fb7a82678292760551e466cedd5ec94639ed0e31cc3cf3a3d5ee8e817",
        "b2a23b06c7cb6822166dceff2a02f410f125fac8fe1909d99ec0c8489f1e104b",
        {"dark": STANDARD["door"], "timber": STANDARD["wall"], "roof": STANDARD["roof"],
         "rope": STANDARD["accent"], "teal": STANDARD["stone"]},
    ),
    "assay_office": spec(
        "assay-office-3d", "assay-office", "assay-office", "AssayOfficeFullWrap", "AssayOfficeE5",
        "07d9b7345b6ae8647a4bf5a615b7f4625578734d6bf250bd3f17e0cdc524c9fa",
        "8005176893d4b2b4c465ec8e75d4a6b53c0ffa19d1212f7c99c6c825033adeb4",
        {"dark": STANDARD["door"], "timber": STANDARD["wall"], "roof": STANDARD["roof"],
         "rope": STANDARD["accent"], "teal": STANDARD["stone"]},
    ),
    "chapel": spec(
        "chapel-3d", "chapel", "chapel", "ChapelFullWrap", "ChapelE5",
        "cf84d4dacce680130577be3d3bcdc3f75c5a4a789541c1de543e7e15e1d6fd59",
        "7422e20113ae7c21b5231a6468ca1a051a1c7bd4c895ed874b775d9372d7b84b",
        {"dark": STANDARD["window"], "timber": STANDARD["wall"], "roof": STANDARD["roof"],
         "rope": STANDARD["accent"], "teal": STANDARD["foliage"]},
    ),
    "schoolhouse": spec(
        "schoolhouse-3d", "schoolhouse", "schoolhouse", "SchoolhouseFullWrap", "SchoolhouseE5",
        "ebe299897e6f59a564889c5d9731e1ff8333584dbe18506786357a24e092ef6f",
        "83290545b29f1ba16a5bc59de239b12c8e6bc594a8382320b3ceb8c3778f03d0",
        {"dark": STANDARD["window"], "timber": STANDARD["wall"], "roof": STANDARD["roof"],
         "rope": STANDARD["accent"], "teal": STANDARD["stone"]},
    ),
    "stamp_mill": spec(
        "stamp-mill-3d", "stamp-mill", "stamp-mill", "StampMillFullWrap", "StampMillE5",
        "b122221dbeb0697cdb465e6bd20a3c7164b3cad4688b75ae1b06b7dade4c9596",
        "4e2d1acb932a9c41a5d4278de39dcffe00ce30920261c1a2f114a794f343b6aa",
        {"dark": STANDARD["window"], "timber": STANDARD["wall"], "roof": STANDARD["roof"],
         "rope": STANDARD["accent"], "teal": STANDARD["stone"]},
    ),
    "dynamo_hall": spec(
        "dynamo-hall-3d", "dynamo-hall", "dynamo-hall", "DynamoHallFullWrap", "DynamoHallE5",
        "7e1c17772d0f7f59b296de26e908dbaaa7eb85139bae677116fff0b6041cc58b",
        "3e8f70f2a4e990ef729ffb4ee80de6ff2d2e4828f86a31d794a821db487fcefb",
        {"dark": DYNAMO["dark"], "timber": DYNAMO["timber"], "roof": DYNAMO["roof"],
         "rope": DYNAMO["copper"], "teal": DYNAMO["teal"]},
    ),
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def beam(name, start, end, radius, material, uv, vertices=6):
    start, end = Vector(start), Vector(end)
    delta = end - start
    obj = common.cylinder(name, radius, delta.length, (start + end) * 0.5, material, uv, vertices)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def lantern(parts, prefix, location, material, uv, teal=True, scale=1.0):
    x, y, z = location
    parts.extend((
        common.cylinder(f"{prefix} hook", 0.025 * scale, 0.22 * scale,
                        (x, y, z + 0.12 * scale), material, uv["dark"], 6),
        common.cylinder(f"{prefix} cap", 0.12 * scale, 0.08 * scale,
                        (x, y, z - 0.01 * scale), material, uv["rope"], 8),
        common.cylinder(f"{prefix} glass", 0.085 * scale, 0.24 * scale,
                        (x, y, z - 0.16 * scale), material, uv["teal" if teal else "rope"], 8),
        common.cylinder(f"{prefix} foot", 0.11 * scale, 0.07 * scale,
                        (x, y, z - 0.32 * scale), material, uv["dark"], 8),
    ))


def tide_board(parts, prefix, location, size, material, uv, face_y):
    x, y, z = location
    parts.append(common.box(prefix, size, location, material, uv["timber"], 0.008))
    sign = 1 if face_y >= 0 else -1
    for index, offset in enumerate((-0.20, 0.0, 0.20), 1):
        parts.append(common.box(
            f"{prefix} tide bar {index}", (size[0] * (0.72 - index * 0.08), 0.025, 0.035),
            (x, y + sign * (size[1] * 0.52), z + offset * size[2]), material, uv["teal"], 0,
        ))


def rope_coil(parts, prefix, location, material, uv, rotation=(math.pi / 2, 0, 0), radius=0.24):
    parts.extend((
        common.torus(f"{prefix} outer", radius, 0.035, location, material, uv["rope"], rotation),
        common.torus(f"{prefix} inner", radius * 0.67, 0.030, location, material, uv["rope"], rotation),
    ))


def grounded_sill(model, asset_id, material, uv):
    corners = [model.matrix_world @ Vector(corner) for corner in model.bound_box]
    x0, x1 = min(corner.x for corner in corners), max(corner.x for corner in corners)
    y0, y1 = min(corner.y for corner in corners), max(corner.y for corner in corners)
    z0 = min(corner.z for corner in corners)
    width = min(0.58, (x1 - x0) * 0.22)
    depth = min(0.42, (y1 - y0) * 0.22)
    height = 0.12
    return [
        common.box(
            f"{asset_id} seabed ballast {side}", (width, depth, height),
            (x, y, z0 + height / 2), material, uv["dark"], 0.004,
        )
        for side, x, y in (
            ("southwest", x0 + width / 2, y0 + depth / 2),
            ("southeast", x1 - width / 2, y0 + depth / 2),
            ("northwest", x0 + width / 2, y1 - depth / 2),
            ("northeast", x1 - width / 2, y1 - depth / 2),
        )
    ]


def harborize_material(model, asset_id):
    source_material = model.data.materials[0]
    material = source_material.copy()
    material.name = f"{asset_id}E5HarborPaintedMaterial"
    texture = next(node for node in material.node_tree.nodes if node.type == "TEX_IMAGE")
    source_image = texture.image
    image = bpy.data.images.new(
        f"{asset_id}E5HarborPaintedAtlas", width=source_image.size[0], height=source_image.size[1], alpha=True,
    )
    image.colorspace_settings.name = "sRGB"
    pixels = np.asarray(source_image.pixels[:], dtype=np.float32).reshape((-1, 4)).copy()
    rgb = pixels[:, :3]
    luminance = rgb @ np.array((0.2126, 0.7152, 0.0722), dtype=np.float32)
    teal_mask = (rgb[:, 1] > rgb[:, 0] * 1.03) & (rgb[:, 2] > rgb[:, 0] * 0.92) & (luminance > 0.06)
    timber = rgb * np.array((0.90, 0.92, 0.84), dtype=np.float32)
    teal = rgb * np.array((0.68, 1.00, 1.05), dtype=np.float32) + np.array(
        (0.0, 0.008, 0.012), dtype=np.float32,
    )
    colored = np.where(teal_mask[:, None], teal, timber)
    pixels[:, :3] = np.clip(colored, 0.008, 0.92)
    image.pixels.foreach_set(pixels.ravel())
    image.update()
    atlas_path = Path("/tmp") / f"{asset_id}-e5-harbor-atlas.png"
    image.filepath_raw = str(atlas_path)
    image.file_format = "PNG"
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.image_settings.color_mode = "RGBA"
    bpy.context.scene.render.image_settings.color_depth = "8"
    image.save()
    harbor_image = bpy.data.images.load(str(atlas_path), check_existing=False)
    harbor_image.name = f"{asset_id}E5HarborPaintedAtlas"
    harbor_image.pack()
    texture.image = harbor_image
    bpy.data.images.remove(image)
    atlas_path.unlink(missing_ok=True)
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Roughness"].default_value = 0.9
    shader.inputs["Emission Color"].default_value = (0, 0, 0, 1)
    shader.inputs["Emission Strength"].default_value = 0.0
    model.data.materials[0] = material
    bpy.data.materials.remove(source_material)
    if source_image.users == 0:
        bpy.data.images.remove(source_image)
    return material


def add_tavern(material, uv):
    parts = [
        beam("Harbor House west gable rope", (-0.94, -1.54, 2.78), (0, -1.54, 3.67), 0.055, material, uv["rope"]),
        beam("Harbor House east gable rope", (0, -1.54, 3.67), (0.94, -1.54, 2.78), 0.055, material, uv["rope"]),
        beam("Harbor House gable sill", (-0.94, -1.54, 2.78), (0.94, -1.54, 2.78), 0.050, material, uv["dark"]),
        beam("Harbor House west rope trim", (-1.88, -1.54, 2.35), (-0.98, -1.54, 2.35), 0.045, material, uv["rope"]),
        beam("Harbor House east rope trim", (0.98, -1.54, 2.35), (1.88, -1.54, 2.35), 0.045, material, uv["rope"]),
    ]
    tide_board(parts, "Harbor House tide chart", (0.98, -1.565, 2.05), (1.02, 0.06, 0.72), material, uv, -1)
    lantern(parts, "Harbor House gable lantern", (0, -1.52, 3.30), material, uv, True, 1.12)
    lantern(parts, "Harbor House west work lantern", (-1.58, -1.55, 2.18), material, uv, False, 0.85)
    rope_coil(parts, "Harbor House rope coil", (-1.78, -1.59, 1.28), material, uv, radius=0.22)
    return parts, "Harbor House lantern gable, rope-trimmed eaves, tide-chart board, work lantern, and rope coil"


def add_general_store(material, uv):
    parts = [
        beam("Bonded Chandlery west loading post", (-1.72, 1.43, 0.22), (-1.72, 1.43, 2.74), 0.075, material, uv["dark"], 8),
        beam("Bonded Chandlery east loading post", (1.72, 1.43, 0.22), (1.72, 1.43, 2.74), 0.075, material, uv["dark"], 8),
        beam("Bonded Chandlery loading beam", (-1.82, 1.43, 2.74), (1.82, 1.43, 2.74), 0.090, material, uv["timber"], 8),
        beam("Bonded Chandlery hoist boom", (0.84, 1.43, 2.74), (1.90, 1.43, 3.54), 0.075, material, uv["timber"], 8),
        beam("Bonded Chandlery hoist drop", (1.84, 1.43, 3.48), (1.84, 1.43, 2.28), 0.032, material, uv["rope"]),
        common.torus("Bonded Chandlery cargo hook", 0.14, 0.035, (1.84, 1.43, 2.16), material, uv["dark"], rotation=(math.pi / 2, 0, 0)),
        common.torus("Bonded Chandlery customs seal", 0.30, 0.045, (0, 1.55, 3.28), material, uv["teal"], rotation=(math.pi / 2, 0, 0)),
        common.cylinder("Bonded Chandlery customs seal hub", 0.09, 0.07, (0, 1.55, 3.28), material, uv["rope"], 8, rotation=(math.pi / 2, 0, 0)),
    ]
    tide_board(parts, "Bonded Chandlery tide board", (-0.86, 1.55, 2.26), (1.12, 0.06, 0.68), material, uv, 1)
    rope_coil(parts, "Bonded Chandlery hawser", (-1.75, 1.55, 1.38), material, uv, radius=0.24)
    return parts, "Bonded Chandlery loading gantry, cargo hoist, customs-seal pictogram, tide board, and working hawser"


def add_claim_office(material, uv):
    parts = [
        beam("Harbor Office signal mast", (1.12, -0.18, 3.24), (1.12, -0.18, 4.86), 0.070, material, uv["dark"], 8),
        beam("Harbor Office signal yard", (0.46, -0.18, 4.46), (1.78, -0.18, 4.46), 0.055, material, uv["rope"], 8),
        common.box("Harbor Office storm signal west", (0.42, 0.06, 0.38), (0.62, -0.18, 4.17), material, uv["teal"], 0.006, rotation=(0, 0, 0.16)),
        common.box("Harbor Office storm signal east", (0.42, 0.06, 0.38), (1.60, -0.18, 4.10), material, uv["roof"], 0.006, rotation=(0, 0, -0.16)),
        beam("Harbor Office tide staff", (-1.68, -1.38, 0.18), (-1.68, -1.38, 2.88), 0.065, material, uv["timber"], 8),
    ]
    for index, z in enumerate((0.72, 1.18, 1.64, 2.10, 2.56), 1):
        parts.append(common.box(f"Harbor Office tide staff mark {index}", (0.40, 0.06, 0.055), (-1.50, -1.40, z), material, uv["teal"], 0))
    tide_board(parts, "Harbor Office registry board", (0, -1.47, 2.65), (1.34, 0.06, 0.72), material, uv, -1)
    lantern(parts, "Harbor Office signal lantern", (1.12, -0.18, 4.78), material, uv, True, 0.82)
    return parts, "Harbor Office storm-signal mast, tide staff, pictogram registry board, and teal signal lantern"


def add_assay_office(material, uv):
    parts = [
        common.box("Salvage Assay sorting canopy", (3.40, 0.62, 0.14), (0, -1.28, 2.58), material, uv["roof"], 0.010),
        beam("Salvage Assay west canopy post", (-1.50, -1.54, 0.20), (-1.50, -1.54, 2.55), 0.065, material, uv["timber"], 8),
        beam("Salvage Assay east canopy post", (1.50, -1.54, 0.20), (1.50, -1.54, 2.55), 0.065, material, uv["timber"], 8),
        beam("Salvage Assay roof hoist mast", (0.92, 0.08, 2.88), (0.92, 0.08, 4.03), 0.075, material, uv["dark"], 8),
        beam("Salvage Assay roof hoist boom", (0.92, 0.08, 3.86), (2.02, 0.08, 3.36), 0.070, material, uv["timber"], 8),
        beam("Salvage Assay roof hoist line", (1.92, 0.08, 3.40), (1.92, 0.08, 2.70), 0.028, material, uv["rope"]),
        common.torus("Salvage Assay hanging sieve", 0.26, 0.045, (1.92, 0.08, 2.58), material, uv["teal"]),
        common.torus("Salvage Assay pearl gauge", 0.31, 0.045, (-0.48, -1.61, 2.18), material, uv["rope"], rotation=(math.pi / 2, 0, 0)),
        common.cylinder("Salvage Assay pearl gauge face", 0.23, 0.06, (-0.48, -1.62, 2.18), material, uv["teal"], 12, rotation=(math.pi / 2, 0, 0)),
    ]
    rope_coil(parts, "Salvage Assay wet line", (1.48, -1.58, 1.32), material, uv, radius=0.22)
    return parts, "Salvage Assay sorting canopy, roof hoist, hanging sieve, pearl gauge, and wet working line"


def add_chapel(material, uv):
    parts = [
        beam("Mariners Chapel west storm stay", (-1.38, 0.64, 3.04), (-0.28, 0.12, 5.56), 0.035, material, uv["rope"]),
        beam("Mariners Chapel east storm stay", (1.38, 0.64, 3.04), (0.28, 0.12, 5.56), 0.035, material, uv["rope"]),
        beam("Mariners Chapel west rope rail", (-1.34, -1.40, 0.68), (-0.48, -1.40, 0.68), 0.045, material, uv["rope"]),
        beam("Mariners Chapel east rope rail", (0.48, -1.40, 0.68), (1.34, -1.40, 0.68), 0.045, material, uv["rope"]),
        common.torus("Mariners Chapel rescue ring", 0.30, 0.055, (0, -1.48, 2.26), material, uv["rope"], rotation=(math.pi / 2, 0, 0)),
        common.box("Mariners Chapel ring cross lash", (0.66, 0.035, 0.055), (0, -1.51, 2.26), material, uv["teal"], 0),
        common.box("Mariners Chapel west roof stay bracket", (0.22, 0.18, 0.14), (-1.38, 0.64, 3.04), material, uv["dark"], 0.006),
        common.box("Mariners Chapel east roof stay bracket", (0.22, 0.18, 0.14), (1.38, 0.64, 3.04), material, uv["dark"], 0.006),
        common.box("Mariners Chapel west tower stay bracket", (0.18, 0.16, 0.18), (-0.28, 0.12, 5.56), material, uv["dark"], 0.006),
        common.box("Mariners Chapel east tower stay bracket", (0.18, 0.16, 0.18), (0.28, 0.12, 5.56), material, uv["dark"], 0.006),
    ]
    lantern(parts, "Mariners Chapel storm lantern", (0, -1.45, 3.03), material, uv, True, 1.0)
    tide_board(parts, "Mariners Chapel tide memorial", (0.94, -1.47, 1.46), (0.72, 0.05, 0.70), material, uv, -1)
    return parts, "Mariners Chapel storm stays, rope rail, rescue-ring pictogram, storm lantern, and tide memorial"


def arc(parts, prefix, center, radius, start, end, material, uv):
    points = []
    for index in range(7):
        angle = start + (end - start) * index / 6
        points.append((center[0] + math.cos(angle) * radius, center[1], center[2] + math.sin(angle) * radius))
    for index, (left, right) in enumerate(zip(points, points[1:]), 1):
        parts.append(beam(f"{prefix} arc {index}", left, right, 0.045, material, uv["rope"], 6))
    return points


def add_schoolhouse(material, uv):
    parts = [
        common.box("Navigation School lookout deck", (2.36, 1.16, 0.13), (-0.18, 0.20, 3.70), material, uv["timber"], 0.010),
    ]
    for x in (-1.08, 0.72):
        parts.extend((
            beam(f"Navigation School rail post {x}", (x, -0.28, 3.72), (x, -0.28, 4.24), 0.045, material, uv["dark"]),
            beam(f"Navigation School rear rail post {x}", (x, 0.68, 3.72), (x, 0.68, 4.24), 0.045, material, uv["dark"]),
        ))
    parts.extend((
        beam("Navigation School front lookout rail", (-1.08, -0.28, 4.19), (0.72, -0.28, 4.19), 0.045, material, uv["rope"]),
        beam("Navigation School rear lookout rail", (-1.08, 0.68, 4.19), (0.72, 0.68, 4.19), 0.045, material, uv["rope"]),
    ))
    center = (-0.20, 0.20, 4.82)
    points = arc(parts, "Navigation School sextant", center, 0.54, math.radians(16), math.radians(164), material, uv)
    parts.extend((
        beam("Navigation School sextant horizon arm", points[0], points[-1], 0.045, material, uv["dark"]),
        beam("Navigation School sextant sight", center, points[2], 0.040, material, uv["teal"]),
        common.cylinder("Navigation School sextant pivot", 0.10, 0.10, center, material, uv["teal"], 8, rotation=(math.pi / 2, 0, 0)),
    ))
    tide_board(parts, "Navigation School chart board", (0, -1.56, 2.56), (1.30, 0.06, 0.76), material, uv, -1)
    lantern(parts, "Navigation School chart lantern", (-1.45, -1.52, 2.55), material, uv, True, 0.82)
    return parts, "Navigation School lookout deck, required sextant finial, chart board, rope rails, and teal chart lantern"


def add_stamp_mill(material, uv):
    parts = [
        beam("Drydock Works west gantry", (-1.70, -0.48, 0.18), (-1.70, -0.48, 3.62), 0.075, material, uv["timber"], 8),
        beam("Drydock Works east gantry", (1.70, -0.48, 0.18), (1.70, -0.48, 3.62), 0.075, material, uv["timber"], 8),
        beam("Drydock Works crossbeam", (-1.84, -0.48, 3.62), (1.84, -0.48, 3.62), 0.090, material, uv["dark"], 8),
        beam("Drydock Works hoist line", (0, -0.48, 3.58), (0, -0.48, 2.36), 0.032, material, uv["rope"]),
        common.torus("Drydock Works hoist hook", 0.16, 0.040, (0, -0.48, 2.22), material, uv["teal"], rotation=(math.pi / 2, 0, 0)),
        beam("Drydock Works hull rib west", (-1.20, -0.70, 0.25), (-0.72, -0.70, 1.86), 0.070, material, uv["rope"], 8),
        beam("Drydock Works hull rib east", (1.20, -0.70, 0.25), (0.72, -0.70, 1.86), 0.070, material, uv["rope"], 8),
        beam("Drydock Works hull keel", (-1.20, -0.70, 0.25), (1.20, -0.70, 0.25), 0.065, material, uv["dark"], 8),
        common.cylinder("Drydock Works capstan", 0.26, 0.68, (2.20, -0.42, 0.58), material, uv["timber"], 10),
        beam("Drydock Works capstan bar", (1.72, -0.42, 0.84), (2.68, -0.42, 0.84), 0.045, material, uv["rope"]),
    ]
    lantern(parts, "Drydock Works gantry lantern", (-1.70, -0.48, 3.48), material, uv, True, 0.78)
    return parts, "Drydock Works timber gantry, drydock hull cradle, hoist, capstan, and teal work lantern"


def add_dynamo_hall(material, uv):
    parts = [
        beam("Harbor Works crane mast", (1.58, -0.18, 0.18), (1.58, -0.18, 3.78), 0.085, material, uv["dark"], 8),
        beam("Harbor Works crane boom", (1.58, -0.18, 3.50), (2.48, -0.18, 2.80), 0.080, material, uv["timber"], 8),
        beam("Harbor Works crane stay", (1.58, -0.18, 3.72), (2.48, -0.18, 2.80), 0.040, material, uv["rope"]),
        beam("Harbor Works crane line", (2.42, -0.18, 2.84), (2.42, -0.18, 1.74), 0.030, material, uv["rope"]),
        common.torus("Harbor Works crane hook", 0.15, 0.040, (2.42, -0.18, 1.62), material, uv["teal"], rotation=(math.pi / 2, 0, 0)),
        common.cylinder("Harbor Works west winch drum", 0.34, 1.10, (-0.72, -1.20, 1.36), material, uv["timber"], 12, rotation=(0, math.pi / 2, 0)),
        common.cylinder("Harbor Works east winch drum", 0.34, 1.10, (0.72, -1.20, 1.36), material, uv["timber"], 12, rotation=(0, math.pi / 2, 0)),
        common.cylinder("Harbor Works west winch band", 0.37, 0.08, (-0.72, -1.20, 1.36), material, uv["rope"], 10, rotation=(0, math.pi / 2, 0)),
        common.cylinder("Harbor Works east winch band", 0.37, 0.08, (0.72, -1.20, 1.36), material, uv["teal"], 10, rotation=(0, math.pi / 2, 0)),
        beam("Harbor Works net frame west", (-2.36, 0.58, 0.18), (-2.36, 0.58, 2.52), 0.060, material, uv["timber"], 8),
        beam("Harbor Works net frame east", (-1.28, 0.58, 0.18), (-1.28, 0.58, 2.52), 0.060, material, uv["timber"], 8),
        beam("Harbor Works net frame header", (-2.36, 0.58, 2.48), (-1.28, 0.58, 2.48), 0.060, material, uv["rope"], 8),
    ]
    for index, z in enumerate((0.68, 1.10, 1.52, 1.94), 1):
        parts.append(beam(f"Harbor Works net line {index}", (-2.32, 0.58, z), (-1.32, 0.58, z + 0.18), 0.018, material, uv["teal"], 4))
    lantern(parts, "Harbor Works crane lantern", (1.58, -0.18, 3.60), material, uv, True, 0.82)
    return parts, "Harbor Works crane, twin rope winches, drying-net frame, cargo hook, and teal crane lantern"


BUILDERS = {
    "tavern": add_tavern,
    "general_store": add_general_store,
    "claim_office": add_claim_office,
    "assay_office": add_assay_office,
    "chapel": add_chapel,
    "schoolhouse": add_schoolhouse,
    "stamp_mill": add_stamp_mill,
    "dynamo_hall": add_dynamo_hall,
}


def build_variant(asset_id, source):
    directory = ROOT / "assets/pilots" / source["directory"]
    source_blend = directory / f'{source["source"]}.blend'
    source_glb = directory / f'{source["source"]}.glb'
    target_blend = directory / f'{source["stem"]}.e5.blend'
    target_glb = directory / f'{source["stem"]}.e5.glb'
    assert sha256(source_blend) == source["blend_sha"], f"{asset_id} E1 BLEND changed"
    assert sha256(source_glb) == source["glb_sha"], f"{asset_id} E1 GLB changed"

    bpy.ops.wm.open_mainfile(filepath=str(source_blend))
    model = bpy.data.objects[source["object"]]
    source_dimensions = tuple(model.dimensions)
    material = harborize_material(model, asset_id)
    parts, identity_edit = BUILDERS[asset_id](material, source["uv"])
    parts.extend(grounded_sill(model, asset_id, material, source["uv"]))
    identity_edit += "; four tarred ballast shoes seat the submerged rebuild directly on the seabed"
    for part in parts:
        part.modifiers.clear()
    common.apply_and_uv(parts)

    bpy.ops.object.select_all(action="DESELECT")
    model.select_set(True)
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = model
    bpy.ops.object.join()
    model.name = source["output"]
    model.data.name = f'{source["output"]}Mesh'
    model.data.uv_layers.active.name = "UVMap"
    for polygon in model.data.polygons:
        polygon.material_index = 0
    while len(model.data.materials) > 1:
        model.data.materials.pop(index=len(model.data.materials) - 1)
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    model["epoch_variant"] = "E5 Deepwater Harbor Rebuild"
    model["identity_edit"] = identity_edit
    model["flood_break"] = "fresh E1 identity shell; no E2-E4 geometry imported"
    assert all(abs(model.dimensions[index] - source_dimensions[index]) < 0.0001 for index in range(3)), (
        asset_id, source_dimensions, tuple(model.dimensions),
    )
    triangles = sum(len(polygon.vertices) - 2 for polygon in model.data.polygons)
    assert triangles <= 15_000, (asset_id, triangles)

    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(target_blend))
    bpy.ops.object.select_all(action="DESELECT")
    model.select_set(True)
    bpy.context.view_layer.objects.active = model
    bpy.ops.export_scene.gltf(
        filepath=str(target_glb), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT",
    )
    return {
        "id": asset_id,
        "blend": str(target_blend.relative_to(ROOT)),
        "glb": str(target_glb.relative_to(ROOT)),
        "sha256": sha256(target_glb),
        "triangles": triangles,
        "dimensions": list(model.dimensions),
        "identityEdit": identity_edit,
    }


def main():
    print(json.dumps([build_variant(asset_id, source) for asset_id, source in SPECS.items()], indent=2))


if __name__ == "__main__":
    main()
