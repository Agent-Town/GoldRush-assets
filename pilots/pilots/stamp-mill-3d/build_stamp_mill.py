from pathlib import Path
import hashlib
import importlib.util
import json

import bpy


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "assets/pilots/schoolhouse-3d/build_schoolhouse.py"
spec = importlib.util.spec_from_file_location("town3d_building", SOURCE)
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)
recipe.REFERENCE = ROOT / "assets/processed/bld-stamp-mill.png"
recipe.BLEND = OUT / "stamp-mill.blend"
recipe.GLB = OUT / "stamp-mill.glb"


def build(material):
    box, cylinder, roof = recipe.box, recipe.cylinder, recipe.longitudinal_gable_roof
    parts = [
        box("Mill full wrap", (5.72, 1.34, 2.44), (0, 0, 1.22), "wall", material, 0.035),
        roof("Mill shingled roof", 6.02, 1.48, 2.40, 3.35, "roof", material),
        box("Front loading deck", (4.30, 0.22, 0.18), (-0.35, -0.70, 0.22), "deck", material, 0.018),
        box("Front door", (0.82, 0.08, 1.62), (-1.65, -0.69, 1.05), "door", material, 0.015),
        box("Back service door", (0.72, 0.08, 1.48), (1.55, 0.69, 1.00), "door", material, 0.015),
        box("Ore hopper", (1.28, 1.16, 0.92), (2.08, -0.12, 2.72), "accent", material, 0.025),
        box("Stamp battery housing", (1.45, 0.14, 1.55), (0.35, -0.72, 1.25), "trim", material, 0.018),
        cylinder("Flywheel", 0.68, 0.12, (1.75, -0.72, 1.12), "accent", material, vertices=20),
        cylinder("Boiler stack", 0.22, 2.25, (-2.15, 0.25, 3.35), "stone", material, vertices=14),
        cylinder("Stack cap", 0.30, 0.16, (-2.15, 0.25, 4.48), "accent", material, vertices=14),
    ]
    parts[-3].rotation_euler[0] = 1.57079632679
    for x in (-0.15, 0.35, 0.85):
        parts.append(box(f"Stamp rod {x}", (0.12, 0.12, 1.48), (x, -0.76, 1.45), "accent", material, 0.01))
    for x in (-2.15, -0.85, 0.45, 1.75):
        parts.append(box(f"Front timber {x}", (0.13, 0.12, 2.28), (x, -0.72, 1.18), "trim", material, 0.012))
        parts.append(box(f"Back timber {x}", (0.13, 0.12, 2.28), (x, 0.72, 1.18), "trim", material, 0.012))
    for x in (-1.05, 0.15, 1.25):
        parts.append(box(f"Side window front {x}", (0.56, 0.07, 0.72), (x, -0.71, 1.45), "window", material, 0.012))
        parts.append(box(f"Side window back {x}", (0.56, 0.07, 0.72), (x, 0.71, 1.45), "window", material, 0.012))
    return parts


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    recipe.reset_scene()
    atlas = recipe.make_atlas()
    pixels = recipe.np.array(atlas.pixels[:], dtype=recipe.np.float32).reshape(atlas.size[1], atlas.size[0], 4)
    pixels[:, :, :3] = recipe.np.clip(pixels[:, :, :3] * 1.5, 0, 1)
    atlas.pixels.foreach_set(pixels.ravel())
    atlas.pack()
    material = recipe.make_material(atlas)
    parts = build(material)
    recipe.apply_and_uv(parts)
    model = recipe.join_schoolhouse(parts)
    model.name = "StampMillFullWrap"
    model.data.name = "StampMillFullWrapMesh"
    recipe.export(model)
    print(json.dumps({"sha256": hashlib.sha256(recipe.GLB.read_bytes()).hexdigest(), "vertices": len(model.data.vertices), "polygons": len(model.data.polygons)}, indent=2))


if __name__ == "__main__":
    main()
