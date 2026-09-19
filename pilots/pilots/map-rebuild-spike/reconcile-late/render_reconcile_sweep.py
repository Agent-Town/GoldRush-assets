"""THE MAP RECONCILIATION (late half) — every late sculpt at ONE identical camera.

Twelve of the twenty late maps cannot be opened in the game at all (their contracts
carry `harvestAnchors: []`, so the contract door substitutes The Claim). They can
still be judged against their plates, and this is how: the fresh-eye arc's fixed
run camera, rendered headless from the shipped GLB.

Three views per map, because the plate promises three different things:

  run-camera  the readability judge. Fixed pose across every map on purpose --
              the gameplay camera sits a fixed height above the player, so a map
              that only reads from its own hero angle is not done.
  overview    the composition judge, SCALED to the tile's measured extent. This
              is the view that answers the plate, which is an elevated whole-map
              illustration.
  panorama    the mood/era judge, ring mounted. The panorama laws (Painted Wall,
              Ceiling, Echo) cannot be judged with the ring down.

The run-camera and overview frames deliberately leave the ring DOWN: mounting it
encloses the tile and eats the key light, which reads as "this map is black" when
the map is fine (the fresh-eye arc's own corrected false finding).

Usage:
  blender -b --factory-startup --python render_reconcile_sweep.py -- <sculpt> [sculpt ...]
  blender -b --factory-startup --python render_reconcile_sweep.py -- --suffix before <sculpt>
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import bpy
import mathutils

SPIKE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "renders"

sys.dont_write_bytecode = True

claim_spec = importlib.util.spec_from_file_location("reconcile_claim_helpers", SPIKE / "build_the_claim_terrain.py")
claim = importlib.util.module_from_spec(claim_spec)
claim_spec.loader.exec_module(claim)
claim.mathutils = mathutils

# The shipped run camera, held FIXED across every map (reviews/opus5-3d-findings.md).
RUN_CAMERA = ((0.0, -30.3, 26.26), (0.0, -8.65, 0.51), 42.0)
OVERVIEW = ((0.0, -38.0, 50.0), (0.0, -1.0, 0.42), 46.0)
OVERVIEW_REFERENCE_HALF = 32.0
# Far enough back to see the ring behind the tile, which is where the seams live.
PANORAMA_VIEW = ((0.0, -78.0, 30.0), (0.0, 0.0, 6.0), 52.0)
SHOT = (960, 600)


def tile_extent() -> tuple[float, float]:
    """Half-extent in XY, and the tile's lowest point — both measured, not assumed."""
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    points = [o.matrix_world @ mathutils.Vector(corner) for o in meshes for corner in o.bound_box]
    half = max(max(abs(p[0]) for p in points), max(abs(p[1]) for p in points))
    return half, min(p[2] for p in points)


def sink_backdrop(backdrop, floor: float) -> float:
    """
    The shared studio backdrop is a plane at z = -0.68. Seven of the thirteen late
    tiles dip BELOW that -- half-life-hollow to -2.41 m, low-orbit to -5.87 -- so the
    backdrop occludes the pit and the render shows a clean-edged HOLE where the map
    is perfectly continuous. A boundary-edge count over every late terrain returns
    zero interior holes (height-stats.mjs), so the hole is the studio's, not the map's.

    This is the same false finding the fresh-eye arc recorded against dome-basin
    (min -2.00 m) and then had to correct. Sink the plane under the lowest point.
    """
    drop = min(-0.68, floor - 0.4)
    backdrop.location.z = drop - (-0.68)
    return drop


def mount_panorama(sculpt: str) -> bool:
    """Mount the ring exactly as the runtime does, from the terrain contract."""
    panorama = SPIKE / f"{sculpt}-panorama.glb"
    contract_path = SPIKE / f"{sculpt}-terrain-contract.json"
    if not panorama.exists() or not contract_path.exists():
        return False
    mount = json.loads(contract_path.read_text(encoding="utf-8")).get("panoramaMount")
    if not mount:
        return False
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(panorama))
    for obj in set(bpy.data.objects) - before:
        if obj.parent:
            continue
        obj.location = mount["position"]
        obj.rotation_euler = mount["rotation"]
        obj.scale = mount["scale"]
    return True


def render_map(sculpt: str, suffix: str) -> dict:
    terrain = SPIKE / f"{sculpt}-terrain.glb"
    if not terrain.exists():
        return {"sculpt": sculpt, "error": f"missing {terrain.name}"}
    tag = f"-{suffix}" if suffix else ""

    claim.reset_scene()
    bpy.ops.import_scene.gltf(filepath=str(terrain))
    # Measure the TILE before the backdrop exists: the backdrop is a 220 m plane,
    # and scanning after it lands measures the studio, not the map.
    half, floor = tile_extent()
    backdrop_z = sink_backdrop(claim.make_backdrop(), floor)
    claim.add_lighting(sunset=False)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = SHOT

    claim.render(claim.add_camera(f"Run_{sculpt}", *RUN_CAMERA), OUT / f"{sculpt}-run-camera{tag}.png")

    scale = half / OVERVIEW_REFERENCE_HALF
    location, target, fov = OVERVIEW
    wide = claim.add_camera(
        f"Wide_{sculpt}",
        (location[0], location[1] * scale, location[2] * scale),
        (target[0], target[1] * scale, target[2]),
        fov,
    )
    claim.render(wide, OUT / f"{sculpt}-overview{tag}.png")

    mounted = mount_panorama(sculpt)
    if mounted:
        location, target, fov = PANORAMA_VIEW
        ring = claim.add_camera(
            f"Ring_{sculpt}",
            (location[0], location[1] * scale, location[2] * scale),
            (target[0], target[1] * scale, target[2]),
            fov,
        )
        claim.render(ring, OUT / f"{sculpt}-panorama{tag}.png")
    return {
        "sculpt": sculpt, "half_extent_m": round(half, 2), "tile_floor_m": round(floor, 3),
        "backdrop_z": round(backdrop_z, 3), "overview_scale": round(scale, 3), "panorama": mounted,
    }


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    suffix = ""
    if "--suffix" in argv:
        index = argv.index("--suffix")
        suffix = argv[index + 1]
        argv = argv[:index] + argv[index + 2:]
    OUT.mkdir(parents=True, exist_ok=True)
    report = []
    for sculpt in argv:
        print(f"  rendering {sculpt}")
        report.append(render_map(sculpt, suffix))
    print("SWEEP_JSON_BEGIN")
    print(json.dumps(report, indent=2))
    print("SWEEP_JSON_END")


if __name__ == "__main__":
    main()
