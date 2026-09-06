from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import hashlib
import json
import sys

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASE_PATH = OUT.parent / "claim-office-3d" / "build_claim_office.py"
SPEC = spec_from_file_location("claim_office_builder", BASE_PATH)
base = module_from_spec(SPEC)
sys.dont_write_bytecode = True
SPEC.loader.exec_module(base)

base.OUT = OUT
base.BLEND = OUT / "assay-office.blend"
base.GLB = OUT / "assay-office.glb"


def image_pixels(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    return np.array(image.pixels[:], dtype=np.float32).reshape(image.size[1], image.size[0], 4)


def source_pixels():
    facade = image_pixels(ROOT / "assets/raw/facade-assay-office.png")[170:1420, 30:995]
    claim = image_pixels(ROOT / "assets/processed/bld-claim-office.png")
    ys = np.linspace(0, facade.shape[0] - 1, 384).astype(int)
    xs = np.linspace(0, facade.shape[1] - 1, 384).astype(int)
    facade = facade[ys[:, None], xs]
    return facade * 0.78 + claim * 0.22


base.source_pixels = source_pixels
build_claim_office = base.build_office


def build_office(material):
    parts = build_claim_office(material)
    for part in list(parts):
        if part.name.startswith("Claim flag") or any(token in part.name for token in ("Step outer 1.49", "Step inner 1.49", "Ledger barrel 1.72", "Claim crate 1.48", "Right service canopy", "Right service platform")):
            parts.remove(part)
            bpy.data.objects.remove(part, do_unlink=True)
    for part in parts:
        part.name = part.name.replace("Claim", "Assay").replace("Office", "Assay Office")
        part.location.x *= 1.04
        part.location.y *= 1.04
        part.scale.x *= 1.04
        part.scale.y *= 1.04
        if any(token in part.name for token in ("cornice", "Porch beam", "Porch foundation")):
            part.scale.x *= 0.96

    add = parts.append
    add(base.box("Assay scales beam", (1.08, 0.11, 0.11), (0, -1.34, 3.48), "accent", material, 0.014))
    add(base.cylinder("Assay scales stem", 0.055, 0.64, (0, -1.34, 3.22), "accent", material, vertices=10))
    add(base.cylinder("Assay scales finial", 0.10, 0.12, (0, -1.34, 3.58), "accent", material, vertices=10))
    for x in (-0.43, 0.43):
        add(base.cylinder(f"Assay scale hanger {x}", 0.022, 0.38, (x, -1.34, 3.27), "trim", material, vertices=8))
        pan = base.cylinder(f"Assay scale pan {x}", 0.22, 0.08, (x, -1.34, 3.07), "accent", material, vertices=12)
        pan.scale.z = 0.38
        add(pan)
    add(base.box("Assay side bench", (0.40, 1.08, 0.72), (2.04, 0.62, 0.50), "deck", material, 0.018))
    add(base.cylinder("Assay side crucible", 0.16, 0.16, (2.04, 0.42, 0.94), "accent", material, vertices=12))
    add(base.cylinder("Assay teal lamp", 0.11, 0.32, (2.04, 0.84, 1.08), "accent", material, vertices=10))
    for x in (-1.20, 1.20):
        add(base.box(f"Assay sample tray {x}", (0.62, 0.28, 0.14), (x, -1.54, 0.76), "stone", material, 0.012))
    add(base.wedge("Assay rear service awning", -1.18, 1.18, 1.18, 1.52, 1.88, 2.10, 0.10, "roof", material))
    add(base.box("Assay rear landing", (2.28, 0.42, 0.16), (0, 1.43, 0.18), "deck", material, 0.015))
    for x in (-1.02, 1.02):
        add(base.box(f"Assay rear brace {x}", (0.12, 0.12, 1.42), (x, 1.38, 0.90), "trim", material, 0.014))
    add(base.box("Assay rear gable band", (2.36, 0.10, 0.16), (0, 1.20, 2.72), "accent", material, 0.014))
    add(base.box("Assay rear pediment inset", (1.64, 0.08, 0.52), (0, -1.03, 3.48), "wall", material, 0.018))
    for x in (-0.46, 0, 0.46):
        medallion = base.cylinder(f"Assay rear sample medallion {x}", 0.11, 0.06, (x, -0.98, 3.48), "accent", material, vertices=12)
        medallion.rotation_euler.x = np.pi / 2
        add(medallion)
    return parts


base.build_office = build_office


def retone_atlas(atlas):
    pixels = np.array(atlas.pixels[:], dtype=np.float32).reshape(base.ATLAS_SIZE, base.ATLAS_SIZE, 4)
    targets = {
        "wall": (0.556, 0.291, 0.096), "roof": (0.120, 0.350, 0.335),
        "trim": (0.454, 0.180, 0.057), "door": (0.365, 0.138, 0.040),
        "window": (0.674, 0.404, 0.115), "deck": (0.530, 0.228, 0.066),
        "stone": (0.533, 0.368, 0.179), "accent": (0.663, 0.410, 0.096),
    }
    for name, target in targets.items():
        u0, v0, u1, v1 = base.REGIONS[name]
        x0, y0, x1, y1 = (int(value * base.ATLAS_SIZE) for value in (u0, v0, u1, v1))
        block = pixels[y0:y1, x0:x1, :3]
        detail = (block.mean(axis=2, keepdims=True) - block.mean()) * 1.8
        pixels[y0:y1, x0:x1, :3] = np.clip(np.array(target) + detail, 0.018, 0.78)
    atlas.pixels.foreach_set(pixels.ravel())
    atlas.pack()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base.reset_scene()
    atlas = base.make_atlas()
    atlas.name = "AssayOfficePaintedAtlas"
    retone_atlas(atlas)
    material = base.make_material(atlas)
    material.name = "AssayOfficePaintedMaterial"
    parts = build_office(material)
    for part in parts:
        bpy.context.view_layer.objects.active = part
        part.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        part.select_set(False)
    base.apply_and_uv(parts)
    office = base.join_office(parts)
    office.name = "AssayOfficeFullWrap"
    office.data.name = "AssayOfficeFullWrapMesh"
    base.export(office)
    print(json.dumps({
        "blend": str(base.BLEND),
        "glb": str(base.GLB),
        "sha256": hashlib.sha256(base.GLB.read_bytes()).hexdigest(),
        "vertices": len(office.data.vertices),
        "polygons": len(office.data.polygons),
    }, indent=2))


if __name__ == "__main__":
    main()
