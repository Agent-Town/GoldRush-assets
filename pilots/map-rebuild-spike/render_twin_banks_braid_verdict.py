"""Verdict boards for the Twin Banks true-braid re-cut.

The sculpt builder (`build_twin_banks_braid.py`) proves mask agreement against
its own height FUNCTION. That is the generator, not the delivery. This script
closes the gap the factory keeps re-learning (a run that "passed" while the
shipped bytes said otherwise): it re-opens the EXPORTED GLB and judges the
vertices that actually ship.

It produces the two boards the commission asks for and the builder did not make:

  1. mask-agreement proof -- the mask boundary drawn as an evidence-only ribbon
     draped on the delivered relief, so the bank lip can be SEEN landing on the
     mask line instead of merely reported as a zero;
  2. run-camera A/B -- main's single-channel sculpt and this braid rendered
     through one identical camera, lighting rig and scene, composed side by side.

It also audits the one soft spot in the builder's gate. That gate excludes a
0.45 m transition band around the boundary from its violation count (declared,
and defensible -- a levee lip legitimately straddles the line). Excluded is not
the same as examined, so this reports the worst excursion INSIDE the band too.

Evidence-only, in the craftbook's sense: the ribbon, cameras and lights own
nothing, are never exported, and touch neither the contract nor the mask.

Usage:
  blender -b --factory-startup --python render_twin_banks_braid_verdict.py
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import sys

import bpy
import mathutils
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"

sys.dont_write_bytecode = True

_spec = importlib.util.spec_from_file_location("braid_builder", OUT / "build_twin_banks_braid.py")
braid = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(braid)

claim = braid.claim
BRAID = braid.BRAID
HALF = braid.HALF
WATER_Y = braid.WATER_Y

NEW_GLB = OUT / "twin-banks-terrain.glb"
OLD_GLB = Path("/tmp/twin-banks-main-baseline.glb")  # extracted from git by the caller

# The builder's own run camera, repeated verbatim so the A/B is a true A/B.
RUN_CAMERA = ((0.0, -30.3, 26.26), (0.0, -8.65, 0.51), 42.0)
BAND = 0.45  # the builder's declared transition band, in metres


# --------------------------------------------------------------------------
# THE DELIVERED BYTES
# --------------------------------------------------------------------------

def import_terrain(path: Path):
    """Load a delivered GLB and hand back its single terrain object."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    fresh = [obj for obj in bpy.data.objects if obj not in before]
    meshes = [obj for obj in fresh if obj.type == "MESH"]
    if len(meshes) != 1:
        raise SystemExit(f"{path.name}: expected exactly one mesh, found {len(meshes)}")
    return meshes[0], fresh


def delivered_vertices(obj) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """World-space game coordinates of every delivered vertex: x, z, height."""
    mesh = obj.data
    count = len(mesh.vertices)
    flat = np.empty(count * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", flat)
    local = flat.reshape(count, 3)
    matrix = np.array(obj.matrix_world.to_4x4(), dtype=np.float32)
    world = local @ matrix[:3, :3].T + matrix[:3, 3]
    # The sculpt authors blender_y = -game_z; undo that to judge in game space.
    return world[:, 0], -world[:, 1], world[:, 2]


def audit_delivered(obj) -> dict:
    """Judge the EXPORTED mesh against the mask -- including the excluded band."""
    x, z, y = delivered_vertices(obj)
    fields = BRAID.fields(x, z)
    zone = BRAID.classify(x, z)
    wet_sd = fields["wet"]
    edge = np.abs(wet_sd) < BAND

    wet = ((zone == 1) | (zone == 2)) & ~edge
    bank = (zone == 0) & ~edge

    dry_in_mask = wet & (y > WATER_Y)
    water_outside = bank & (y < WATER_Y)

    # The audit the builder's gate cannot make: how far does the relief stray
    # INSIDE the tolerated band? A levee lip may straddle; a bank may not drown.
    band_wet = ((zone == 1) | (zone == 2)) & edge
    band_bank = (zone == 0) & edge
    worst_band_dry = float((y[band_wet] - WATER_Y).max()) if band_wet.any() else 0.0
    worst_band_wet = float((WATER_Y - y[band_bank]).max()) if band_bank.any() else 0.0

    return {
        "source": "exported GLB vertices (not the generator's height function)",
        "vertices": int(x.size),
        "waterPlaneY": WATER_Y,
        "transitionBandMetres": BAND,
        "outsideBand": {
            "dryGroundInsideMask": int(dry_in_mask.sum()),
            "waterOutsideMask": int(water_outside.sum()),
        },
        "insideBandAudit": {
            "note": "excluded from the pass/fail count by design; reported so the exclusion is auditable",
            "samples": int(edge.sum()),
            "worstDryRiseInsideMaskMetres": round(worst_band_dry, 4),
            "worstBankDropBelowWaterMetres": round(worst_band_wet, 4),
        },
        "zoneHeights": {
            name: {
                "samples": int(sel.sum()),
                "minY": round(float(y[sel].min()), 4),
                "meanY": round(float(y[sel].mean()), 4),
                "maxY": round(float(y[sel].max()), 4),
            }
            for name, sel in (("river", zone == 1), ("ford", zone == 2), ("bank", zone == 0))
            if sel.any()
        },
    }


# --------------------------------------------------------------------------
# THE EVIDENCE RIBBON (owns nothing)
# --------------------------------------------------------------------------

def mask_boundary_points(samples=721) -> np.ndarray:
    """Zero-crossings of the mask's own wet field: where water legally stops."""
    axis = np.linspace(-HALF, HALF, samples, dtype=np.float32)
    grid_x, grid_z = np.meshgrid(axis, axis)
    wet = BRAID.fields(grid_x, grid_z)["wet"]
    inside = wet <= 0.0

    points = []
    # Horizontal neighbours, then vertical: interpolate the exact crossing so the
    # line sits on the mask, not on the sampling grid.
    for a, b, axis_is_x in ((inside[:, :-1], inside[:, 1:], True), (inside[:-1, :], inside[1:, :], False)):
        rows, cols = np.nonzero(a != b)
        if axis_is_x:
            wa, wb = wet[rows, cols], wet[rows, cols + 1]
            t = wa / (wa - wb)
            px = axis[cols] + t * (axis[cols + 1] - axis[cols])
            pz = axis[rows]
        else:
            wa, wb = wet[rows, cols], wet[rows + 1, cols]
            t = wa / (wa - wb)
            px = axis[cols]
            pz = axis[rows] + t * (axis[rows + 1] - axis[rows])
        points.append(np.stack([px, pz], axis=1))
    return np.concatenate(points, axis=0)


def build_mask_ribbon(name: str, colour, size=0.16, lift=0.06):
    """Drape the mask boundary on the relief as emissive dots.

    Draped rather than floated: in the ortho board the XY registration is exact
    either way, but on the run camera a floating line would parallax off the
    ground it is supposed to be proving.
    """
    points = mask_boundary_points()
    height = braid.braid_height(points[:, 0], points[:, 1]) + lift

    half = size * 0.5
    corners = np.array([(-half, -half), (half, -half), (half, half), (-half, half)], dtype=np.float32)
    count = len(points)
    verts = np.empty((count * 4, 3), dtype=np.float32)
    for index, (dx, dz) in enumerate(corners):
        verts[index::4, 0] = points[:, 0] + dx
        verts[index::4, 1] = -(points[:, 1] + dz)  # game z -> blender y
        verts[index::4, 2] = height
    base = np.arange(count) * 4
    faces = np.stack([base, base + 1, base + 2, base + 3], axis=1)

    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(verts.tolist(), [], faces.tolist())
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    material = bpy.data.materials.new(f"{name}Material")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (*colour, 1.0)
    emission.inputs["Strength"].default_value = 6.0
    output = nodes.new("ShaderNodeOutputMaterial")
    material.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    mesh.materials.append(material)
    return obj


# --------------------------------------------------------------------------
# COMPOSITION (no PIL in this interpreter; bpy owns the pixels)
# --------------------------------------------------------------------------

def read_png(path: Path) -> np.ndarray:
    image = bpy.data.images.load(str(path))
    width, height = image.size
    buffer = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(buffer)
    bpy.data.images.remove(image)
    return buffer.reshape(height, width, 4)  # bottom-up, as Blender stores it


def write_png(path: Path, pixels: np.ndarray) -> None:
    height, width = pixels.shape[:2]
    image = bpy.data.images.new(path.stem, width=width, height=height, alpha=True)
    image.pixels.foreach_set(pixels.reshape(-1).astype(np.float32))
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)


def compose_side_by_side(left: Path, right: Path, target: Path, gutter=12) -> None:
    a, b = read_png(left), read_png(right)
    if a.shape != b.shape:
        raise SystemExit(f"A/B frames must match: {a.shape} vs {b.shape}")
    height, width = a.shape[:2]
    canvas = np.zeros((height, width * 2 + gutter, 4), dtype=np.float32)
    canvas[..., 3] = 1.0
    canvas[:, :width] = a
    canvas[:, width + gutter:] = b
    # A warm parchment seam, so the join never reads as part of either frame.
    canvas[:, width:width + gutter, :3] = np.array([0.36, 0.22, 0.09], dtype=np.float32)
    write_png(target, canvas)


# --------------------------------------------------------------------------
# BOARDS
# --------------------------------------------------------------------------

def scene_cameras():
    run = claim.add_camera("BraidVerdictRun", *RUN_CAMERA)
    ortho_data = bpy.data.cameras.new("BraidVerdictOrtho")
    ortho_data.type = "ORTHO"
    ortho_data.ortho_scale = HALF * 2.0
    ortho_data.clip_start = 1.0
    ortho_data.clip_end = 400.0
    ortho = bpy.data.objects.new("BraidVerdictOrtho", ortho_data)
    bpy.context.collection.objects.link(ortho)
    ortho.location = (0.0, 0.0, 120.0)
    ortho.rotation_euler = (0.0, 0.0, 0.0)
    return run, ortho


def render_side(glb: Path, run_target: Path, ortho_target: Path | None = None, ribbon=False) -> dict | None:
    claim.reset_scene()
    terrain, _ = import_terrain(glb)
    claim.make_backdrop()
    claim.add_lighting(sunset=False)
    run, ortho = scene_cameras()

    audit = audit_delivered(terrain) if ribbon else None

    claim.render(run, run_target)
    if ribbon:
        line = build_mask_ribbon("BraidVerdictMaskLine", (0.05, 0.95, 0.85))
        claim.render(run, run_target.with_name(run_target.stem + "-masked.png"))
        if ortho_target:
            scene = bpy.context.scene
            keep = (scene.render.resolution_x, scene.render.resolution_y)
            scene.render.resolution_x = scene.render.resolution_y = 1024
            claim.render(ortho, ortho_target)
            scene.render.resolution_x, scene.render.resolution_y = keep
        claim.remove_objects([line])
    return audit


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    if not OLD_GLB.exists():
        raise SystemExit(f"baseline missing: {OLD_GLB} (extract main's GLB there first)")

    before = ARTIFACTS / "twin-banks-braid-ab-before-main.png"
    after = ARTIFACTS / "twin-banks-braid-ab-after-braid.png"

    render_side(OLD_GLB, before)
    audit = render_side(
        NEW_GLB,
        after,
        ortho_target=ARTIFACTS / "twin-banks-braid-mask-proof-ortho.png",
        ribbon=True,
    )

    compose_side_by_side(before, after, ARTIFACTS / "twin-banks-braid-ab-run-camera.png")

    report = ARTIFACTS / "twin-banks-braid-delivered-audit.json"
    report.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))

    failed = audit["outsideBand"]["dryGroundInsideMask"] or audit["outsideBand"]["waterOutsideMask"]
    if failed:
        raise SystemExit("delivered GLB fights the mask; the sculpt is not shippable")


if __name__ == "__main__":
    main()
