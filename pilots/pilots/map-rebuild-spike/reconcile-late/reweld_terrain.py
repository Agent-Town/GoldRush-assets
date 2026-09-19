"""FIX-IN-PLACE for F-MRL-1 — make the sculpt conform to the contract it declares.

Four late-era terrains (glow-mesa, relay-valley, echo-canyon, low-orbit) are
authored with every polygon FLAT-shaded. glTF cannot carry per-face normals on a
shared vertex, so the exporter splits them: 16 641 authored vertices become
40 018 - 87 071 exported ones. The build scripts wrote the AUTHORED count into
the contract and never re-read the GLB, so the mismatch shipped.

At runtime Terrain3dClaimPilot.validTerrain() requires an exact vertex match, and
on a mismatch failLoad() drops the map to the painted tile -- with no console
error. Seven of the twenty late maps are affected.

The fix is the smallest one that makes the asset legal: shade the terrain smooth
(the house norm -- every VALID late-era terrain is 100% smooth-shaded), re-export
with the build scripts' own flags, and refresh only the contract's `files`
checksums, which describe this artifact. Geometry, UVs, bounds, materials, the
atlas, the mask truth and the declared counts are all untouched: the sculpt
conforms to the contract, never the reverse.

Usage:
  blender -b --factory-startup --python reweld_terrain.py -- [--apply] <sculpt> ...

Without --apply it reports what it would do and exports nothing.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import bpy

SPIKE = Path(__file__).resolve().parent.parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def terrain_object() -> bpy.types.Object:
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if len(meshes) != 1:
        raise SystemExit(f"expected exactly one mesh object, found {[o.name for o in meshes]}")
    return meshes[0]


def reweld(sculpt: str, apply: bool) -> dict:
    blend = SPIKE / f"{sculpt}-terrain.blend"
    glb = SPIKE / f"{sculpt}-terrain.glb"
    contract_path = SPIKE / f"{sculpt}-terrain-contract.json"
    atlas = SPIKE / f"{sculpt}-terrain-atlas.png"
    for path in (blend, glb, contract_path):
        if not path.exists():
            return {"sculpt": sculpt, "error": f"missing {path.name}"}

    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    obj = terrain_object()
    mesh = obj.data
    before_flat = sum(1 for polygon in mesh.polygons if not polygon.use_smooth)
    result = {
        "sculpt": sculpt,
        "object": obj.name,
        "authored_vertices": len(mesh.vertices),
        "contract_vertices": contract["vertices"],
        "flat_polygons_before": before_flat,
        "applied": False,
    }
    if before_flat == 0:
        result["note"] = "already smooth-shaded; nothing to do"
        return result
    if len(mesh.vertices) != contract["vertices"]:
        result["error"] = "authored vertex count already disagrees with the contract; not a shading fix"
        return result
    if not apply:
        result["note"] = "dry run"
        return result

    # The ONLY edit: per-polygon shading. No geometry, UV, material or transform change.
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    result["flat_polygons_after"] = sum(1 for polygon in mesh.polygons if not polygon.use_smooth)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    # Flags copied verbatim from the build scripts (build_e6_extra_terrains.py:521)
    # so the re-export differs from the original in shading and nothing else.
    bpy.ops.export_scene.gltf(
        filepath=str(glb), export_format="GLB", use_selection=True, export_apply=True,
        export_cameras=False, export_lights=False, export_animations=False, export_extras=True,
    )

    contract["files"] = {
        "blend": {"bytes": blend.stat().st_size, "sha256": sha256(blend)},
        "glb": {"bytes": glb.stat().st_size, "sha256": sha256(glb)},
        "atlas": {"bytes": atlas.stat().st_size, "sha256": sha256(atlas)},
    }
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    result["applied"] = True
    result["glb_bytes"] = contract["files"]["glb"]["bytes"]
    return result


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    apply = "--apply" in argv
    sculpts = [arg for arg in argv if not arg.startswith("--")]
    report = [reweld(sculpt, apply) for sculpt in sculpts]
    print("REWELD_JSON_BEGIN")
    print(json.dumps(report, indent=2))
    print("REWELD_JSON_END")


if __name__ == "__main__":
    main()
