"""ARC 3 — the fresh eye: eight maps at ONE identical run camera.

The craftbook's judgement rule is that the run camera is the judge, and that a map
which only reads from a low beauty angle is not done. Per-map builders each pose
their own hero angle, which is exactly how a weak composition survives review. So
this sweep ignores those and puts every map through the SAME camera, lighting rig
and lens — the shipped Twin Banks run camera, on a 64 m tile that every map shares.

Identical framing is the whole point: it makes the maps comparable to each other
rather than each flattered by its own best angle.

Panoramas are mounted, because mood is half the verdict and the panorama laws
(the Painted Wall, the Ceiling, the Echo) can only be judged with the ring up.

Usage:
  blender -b --factory-startup --python render_fresh_eye_sweep.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import bpy
import mathutils
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/opus5-fresh-eye"

sys.dont_write_bytecode = True

claim_spec = importlib.util.spec_from_file_location("sweep_claim_helpers", OUT / "build_the_claim_terrain.py")
claim = importlib.util.module_from_spec(claim_spec)
claim_spec.loader.exec_module(claim)
claim.mathutils = mathutils

# The shipped run camera, held FIXED across every map -- correct on purpose. The
# gameplay camera sits a fixed height above the player, so what the player can
# read does not change when the tile does. This is the readability judge.
RUN_CAMERA = ((0.0, -30.3, 26.26), (0.0, -8.65, 0.51), 42.0)
# The composition judge, and it must SCALE. The first pass of this sweep assumed
# "every tile is 64 m" and framed all eight identically; the tiles are actually
# 64, 96x112 and 128 m across, so the big maps were being judged on their middle
# quarter, and their own edges read as holes punched in the world.
OVERVIEW = ((0.0, -38.0, 50.0), (0.0, -1.0, 0.42), 46.0)
OVERVIEW_REFERENCE_HALF = 32.0
SHOT = (760, 470)

# Eight maps spanning the saga, one per chapter-ish, chosen to cover the range of
# dominant landforms rather than to flatter the sweep.
MAPS = [
    ("the-claim", "E1 — the first claim: the tutorial ground"),
    ("twin-banks", "E1 — the braid (this commission's ARC 1)"),
    ("canyon-works", "E2 — steamworks: the pylon-site standard"),
    ("echo-canyon", "E3 — voltage: the gorge"),
    ("deepwater-claim", "E5 — deepwater"),
    ("glow-mesa", "E6 — atomic: the mesa"),
    ("dome-basin", "E9 — red fields: the persistent tile"),
    ("archive-world", "E10 — deep sky: the archive"),
]


def frame(map_key: str) -> np.ndarray:
    claim.reset_scene()
    terrain = OUT / f"{map_key}-terrain.glb"
    if not terrain.exists():
        raise SystemExit(f"missing terrain: {terrain}")
    bpy.ops.import_scene.gltf(filepath=str(terrain))
    # Measure the TILE here, before the backdrop exists -- the backdrop is a 220 m
    # plane and scanning the scene after it is added measures the studio, not the map.
    tile_meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    tile_points = [o.matrix_world @ mathutils.Vector(c) for o in tile_meshes for c in o.bound_box]
    half = max(max(abs(p[0]) for p in tile_points), max(abs(p[1]) for p in tile_points))

    # Panorama deliberately NOT mounted for the run-camera frame. The shipped
    # builders hide the ring for their run-camera boards and only raise it for a
    # separate distance/mood view -- mounting it here encloses the tile and eats
    # the key light, which reads as "this map is black" when the map is fine.
    claim.make_backdrop()
    claim.add_lighting(sunset=False)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = SHOT
    camera = claim.add_camera(f"FreshEye_{map_key}", *RUN_CAMERA)
    claim.render(camera, ARTIFACTS / f"{map_key}-run-camera.png")

    # Pull the overview back to this tile's actual size.
    scale = half / OVERVIEW_REFERENCE_HALF
    location, target, fov = OVERVIEW
    wide = claim.add_camera(
        f"FreshEyeWide_{map_key}",
        (location[0], location[1] * scale, location[2] * scale),
        (target[0], target[1] * scale, target[2]),
        fov,
    )
    print(f"      tile half-extent {half:.0f} m -> overview x{scale:.2f}")
    path = ARTIFACTS / f"{map_key}-overview.png"
    claim.render(wide, path)

    image = bpy.data.images.load(str(path))
    width, height = image.size
    buffer = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(buffer)
    bpy.data.images.remove(image)
    return buffer.reshape(height, width, 4)


def sheet(frames: list[np.ndarray], names: list[str], target: Path) -> None:
    """Two rows of two, in the order given; filenames carry the labels."""
    width, height = SHOT
    gutter = 10
    columns = 2
    rows = (len(frames) + columns - 1) // columns
    canvas = np.zeros((height * rows + gutter * (rows - 1), width * columns + gutter * (columns - 1), 4), dtype=np.float32)
    canvas[..., :3] = np.array([0.30, 0.18, 0.07], dtype=np.float32)
    canvas[..., 3] = 1.0
    for index, image in enumerate(frames):
        row, column = divmod(index, columns)
        # Blender images are bottom-up, so fill the last row first to read top-down.
        y = (rows - 1 - row) * (height + gutter)
        x = column * (width + gutter)
        canvas[y:y + height, x:x + width] = image
    out = bpy.data.images.new(target.stem, width=canvas.shape[1], height=canvas.shape[0], alpha=True)
    out.pixels.foreach_set(canvas.reshape(-1))
    out.filepath_raw = str(target)
    out.file_format = "PNG"
    out.save()
    bpy.data.images.remove(out)


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    frames = []
    for map_key, chapter in MAPS:
        print(f"  {map_key:<18} {chapter}")
        frames.append(frame(map_key))
    sheet(frames[:4], [m for m, _ in MAPS[:4]], ARTIFACTS / "fresh-eye-sheet-1.png")
    sheet(frames[4:], [m for m, _ in MAPS[4:]], ARTIFACTS / "fresh-eye-sheet-2.png")
    print(f"\nfresh-eye sweep: {len(frames)} maps at one identical run camera")


if __name__ == "__main__":
    main()
