"""Why does this terrain export split its vertices?

The contract records the AUTHORED vertex count (what the mesh has in Blender);
the GLB carries the EXPORTED count. Nobody compared them, so four late-era
terrains ship a split-vertex GLB that the runtime's validTerrain() rejects — and
the map silently falls back to the painted tile.

This reports, per .blend: the mesh's own counts, its shading state, sharp edges,
custom split normals, seams, and modifiers — i.e. every reason glTF would split.

Usage:
  blender -b --factory-startup --python inspect_terrain_blend.py -- <sculpt> [sculpt ...]
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

import bpy

SPIKE = Path(__file__).resolve().parent.parent


def inspect(sculpt: str) -> dict:
    blend = SPIKE / f"{sculpt}-terrain.blend"
    if not blend.exists():
        return {"sculpt": sculpt, "error": f"missing {blend.name}"}
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    rows = []
    for obj in meshes:
        mesh = obj.data
        flat = sum(1 for polygon in mesh.polygons if not polygon.use_smooth)
        sharp = sum(1 for edge in mesh.edges if edge.use_edge_sharp)
        seams = sum(1 for edge in mesh.edges if edge.use_seam)
        rows.append({
            "object": obj.name,
            "vertices": len(mesh.vertices),
            "polygons": len(mesh.polygons),
            "loops": len(mesh.loops),
            "flat_polygons": flat,
            "smooth_polygons": len(mesh.polygons) - flat,
            "sharp_edges": sharp,
            "uv_seams": seams,
            "has_custom_split_normals": bool(mesh.has_custom_normals),
            "uv_layers": [layer.name for layer in mesh.uv_layers],
            "modifiers": [(m.name, m.type) for m in obj.modifiers],
            "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        })
    return {"sculpt": sculpt, "objects": rows}


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    report = [inspect(sculpt) for sculpt in argv]
    print("INSPECT_JSON_BEGIN")
    print(json.dumps(report, indent=2))
    print("INSPECT_JSON_END")


if __name__ == "__main__":
    main()
