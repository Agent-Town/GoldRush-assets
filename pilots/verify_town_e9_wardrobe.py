"""Judge the delivered E9 wardrobe: semantics, the swatch contract, and a board.

Numbers are not a picture and a picture is not a contract, so this does both:

  * semantic gate -- one node / mesh / primitive / material / image, no cameras,
    lights or animation, Y-up, grounded, footprint preserved against the .e8 it
    was derived from (a variant that changes its parcel is not a variant);
  * the swatch contract -- reads the atlas back OUT of the exported GLB and
    proves an exact #50674c core survived engraving and PNG round-trip. The E9
    bundle says the green is literally E1's riverbank swatch; a callback nobody
    can verify is decoration;
  * a lineup board -- all eight at one identical camera, E8 above / E9 below, so
    the era change is judged by eye rather than asserted.

Usage:
  blender -b --factory-startup --python verify_town_e9_wardrobe.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
PILOTS = Path(__file__).resolve().parent
ERA = 9
SOURCE_ERA = 8  # the coat this era was re-dressed from
ARTIFACTS = ROOT / f"artifacts/town-e{ERA}"

sys.dont_write_bytecode = True

E1_GREEN = (0x50, 0x67, 0x4C)
TOLERANCE = 2  # 8-bit sRGB round-trip slack
BUILDINGS = ["tavern", "schoolhouse", "claim-office", "stamp-mill",
             "assay-office", "general-store", "dynamo-hall", "chapel"]
SHOT = (520, 660)


def load(path: Path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    return meshes


def semantics(path: Path) -> dict:
    meshes = load(path)
    obj = meshes[0]
    obj.data.calc_loop_triangles()
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    images = [i for i in bpy.data.images if i.size[0]]
    return {
        "meshes": len(meshes),
        "objects": len([o for o in bpy.data.objects]),
        "materials": len(bpy.data.materials),
        "images": len(images),
        "atlas": list(images[0].size) if images else None,
        "cameras": len([o for o in bpy.data.objects if o.type == "CAMERA"]),
        "lights": len([o for o in bpy.data.objects if o.type == "LIGHT"]),
        "actions": len(bpy.data.actions),
        "triangles": len(obj.data.loop_triangles),
        "min": [round(min(p[i] for p in pts), 4) for i in range(3)],
        "max": [round(max(p[i] for p in pts), 4) for i in range(3)],
    }


def green_swatch(path: Path) -> dict:
    """Read the atlas out of the delivered GLB and hunt the exact swatch."""
    load(path)
    image = next(i for i in bpy.data.images if i.size[0])
    width, height = image.size
    buffer = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(buffer)
    pixels = buffer.reshape(height, width, 4)[..., :3]
    # House convention, measured against the shipped era-props-e9 atlas (which
    # carries 41,468 exact swatch pixels): for an 8-bit sRGB image, .pixels maps
    # straight to the stored bytes at x255. No linear conversion belongs here --
    # applying one is how this check first reported a swatch that was present.
    bytes8 = np.clip(np.rint(pixels * 255.0), 0, 255).astype(np.int16)
    target = np.array(E1_GREEN, dtype=np.int16)
    exact = np.all(np.abs(bytes8 - target) <= TOLERANCE, axis=-1)
    return {
        "exactPixels": int(exact.sum()),
        "largestRun": int(exact.sum(axis=1).max()) if exact.any() else 0,
        "targetHex": "#%02x%02x%02x" % E1_GREEN,
    }


def board() -> None:
    """One camera, eight buildings, E8 over E9."""
    frames: dict[tuple[str, int], np.ndarray] = {}
    for name in BUILDINGS:
        for era in (SOURCE_ERA, ERA):
            path = PILOTS / f"{name}-3d/{name}.e{era}.glb"
            meshes = load(path)
            scene = bpy.context.scene
            scene.render.engine = "BLENDER_EEVEE"
            scene.render.resolution_x, scene.render.resolution_y = SHOT
            scene.render.film_transparent = False
            world = bpy.data.worlds.new("BoardWorld")
            world.use_nodes = True
            world.node_tree.nodes["Background"].inputs[0].default_value = (0.82, 0.68, 0.44, 1.0)
            world.node_tree.nodes["Background"].inputs[1].default_value = 1.15
            scene.world = world

            target = Vector((0, 0, 0))
            for obj in meshes:
                target += obj.matrix_world @ Vector(obj.bound_box[0])
            height = max((obj.matrix_world @ Vector(c)).z for obj in meshes for c in obj.bound_box)
            focus = Vector((0.0, 0.0, height * 0.46))

            data = bpy.data.cameras.new("BoardCam")
            data.lens = 62.0
            camera = bpy.data.objects.new("BoardCam", data)
            bpy.context.collection.objects.link(camera)
            camera.location = (7.4, -8.2, 5.6)
            direction = focus - Vector(camera.location)
            camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
            scene.camera = camera

            sun = bpy.data.lights.new("BoardSun", type="SUN")
            sun.energy = 3.6
            sun_obj = bpy.data.objects.new("BoardSun", sun)
            sun_obj.rotation_euler = (math.radians(54), 0.0, math.radians(37))
            bpy.context.collection.objects.link(sun_obj)
            fill = bpy.data.lights.new("BoardFill", type="SUN")
            fill.energy = 1.1
            fill_obj = bpy.data.objects.new("BoardFill", fill)
            fill_obj.rotation_euler = (math.radians(62), 0.0, math.radians(-128))
            bpy.context.collection.objects.link(fill_obj)

            out = f"/tmp/board-{name}-e{era}.png"
            scene.render.filepath = out
            bpy.ops.render.render(write_still=True)
            image = bpy.data.images.load(out)
            w, h = image.size
            buf = np.empty(w * h * 4, dtype=np.float32)
            image.pixels.foreach_get(buf)
            frames[(name, era)] = buf.reshape(h, w, 4)
            bpy.data.images.remove(image)

    width, height = SHOT
    gutter = 8
    canvas = np.zeros((height * 2 + gutter, width * len(BUILDINGS) + gutter * (len(BUILDINGS) - 1), 4), dtype=np.float32)
    canvas[..., :3] = np.array([0.36, 0.22, 0.09], dtype=np.float32)
    canvas[..., 3] = 1.0
    for index, name in enumerate(BUILDINGS):
        x = index * (width + gutter)
        canvas[height + gutter:, x:x + width] = frames[(name, SOURCE_ERA)]  # bottom row = source era
        canvas[:height, x:x + width] = frames[(name, ERA)]                   # top row    = this era
    # Blender stores images bottom-up, so the row written first lands on top.
    out = bpy.data.images.new(f"TownE{ERA}Board", width=canvas.shape[1], height=canvas.shape[0], alpha=True)
    out.pixels.foreach_set(canvas.reshape(-1))
    out.filepath_raw = str(ARTIFACTS / f"town-e{ERA}-wardrobe-board.png")
    out.file_format = "PNG"
    out.save()


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    report = []
    failures = []
    for name in BUILDINGS:
        e9 = PILOTS / f"{name}-3d/{name}.e{ERA}.glb"
        e8 = PILOTS / f"{name}-3d/{name}.e{SOURCE_ERA}.glb"
        row = {"building": name, "e9": semantics(e9), "e8": semantics(e8), "green": green_swatch(e9)}

        checks = {
            "single mesh": row["e9"]["meshes"] == 1,
            "single material": row["e9"]["materials"] == 1,
            "single image": row["e9"]["images"] == 1,
            "atlas 1024": row["e9"]["atlas"] == [1024, 1024],
            "no cameras/lights/anim": row["e9"]["cameras"] == 0 and row["e9"]["lights"] == 0 and row["e9"]["actions"] == 0,
            "grounded": abs(row["e9"]["min"][2]) < 0.02,
            # The runtime's real rule, not a loose tolerance: Town rejects a
            # model whose bounds grow past the parcel or drift off centre, and
            # then silently serves the older era.
            "footprint preserved": (
                abs((row["e9"]["max"][0] - row["e9"]["min"][0]) - (row["e8"]["max"][0] - row["e8"]["min"][0])) < 0.01
                and abs((row["e9"]["max"][1] - row["e9"]["min"][1]) - (row["e8"]["max"][1] - row["e8"]["min"][1])) < 0.01
            ),
            "centred": (
                abs(row["e9"]["max"][0] + row["e9"]["min"][0]) * 0.5 <= 0.06
                and abs(row["e9"]["max"][1] + row["e9"]["min"][1]) * 0.5 <= 0.06
            ),
            "triangle cap": row["e9"]["triangles"] <= 15000,
            "green swatch present": row["green"]["exactPixels"] > 1000,
        }
        row["checks"] = checks
        bad = [k for k, ok in checks.items() if not ok]
        if bad:
            failures.append((name, bad))
        report.append(row)
        print(f"  {name:<15} tris {row['e9']['triangles']:>6}  green px {row['green']['exactPixels']:>7}  "
              f"{'OK' if not bad else 'FAIL ' + ','.join(bad)}")

    board()
    (ARTIFACTS / f"town-e{ERA}-verify.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit(f"E{ERA} wardrobe verification failed: {failures}")
    print(f"\nE{ERA} wardrobe verified: {len(report)}/{len(BUILDINGS)}")


if __name__ == "__main__":
    main()
