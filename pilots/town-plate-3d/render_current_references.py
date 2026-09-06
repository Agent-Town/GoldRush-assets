from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

sys.dont_write_bytecode = True

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE_SHA = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
REFERENCE_LABEL = os.environ.get("TOWN_REFERENCE_LABEL", "main")
OUT = ROOT / "artifacts/town-plate-3d/current-references" / f"{BASE_SHA[:12]}-{REFERENCE_LABEL}"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


e4 = load_module("current_reference_e4", ROOT / "assets/pilots/tavern-3d/render_wave9_e4_wide.py")
e5 = load_module("current_reference_e5", ROOT / "assets/pilots/tavern-3d/render_wave10_e5_harbor.py")
town = e4.town
PLATE = HERE / "town-plate.glb"


def render_e1(path):
    town.reset_scene()
    town.import_model(PLATE, "RenderTownPlate", town.Point(0, 0))
    town.add_render_models()
    town.setup_render_scene()
    town.render(path)


def render_e4(path):
    town.reset_scene()
    town.import_model(PLATE, "RenderTownPlate", town.Point(0, 0))
    e4.add_town_context(e4.E4_MODELS)
    town.setup_render_scene()
    camera = bpy.context.scene.camera
    camera.location = (0.0, 24.5, 34.5)
    town.look_at(camera, Vector((0.0, -1.5, 0.45)))
    town.render(path)


def render_e5(path):
    e5.render_town(e5.E5_MODELS, 5, path, overview=True, underwater=True)


def render_e4_wagon(path):
    e4.render_wagon_accretion(path)


def image_array(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    array = pixels.reshape(height, width, 4)
    bpy.data.images.remove(image)
    return array


def save_array(array, path):
    height, width, _ = array.shape
    image = bpy.data.images.new(path.stem, width, height, alpha=True)
    image.pixels.foreach_set(array.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assemble():
    renders = [OUT / "town-e4-current.png"]
    if REFERENCE_LABEL == "main":
        renders = [OUT / "town-e1-current.png", *renders, OUT / "town-e5-current-underwater.png"]
        save_array(np.concatenate([image_array(path) for path in renders], axis=1), OUT / "town-e1-e4-e5-current.png")
    comparison_renders = []
    comparison_metrics = None
    if REFERENCE_LABEL != "main":
        baseline = ROOT / "artifacts/town-plate-3d/current-references" / f"{BASE_SHA[:12]}-main" / "town-e4-current.png"
        before = image_array(baseline)
        after = image_array(OUT / "town-e4-current.png")
        pair = OUT / "road-wear-e4-before-after.png"
        focus_pair = OUT / "road-wear-e4-focus-before-after.png"
        save_array(np.concatenate((before, after), axis=1), pair)
        save_array(np.concatenate((before[180:800, 240:1040], after[180:800, 240:1040]), axis=1), focus_pair)
        comparison_renders.extend((pair, focus_pair))
        delta = np.abs(after[:, :, :3] - before[:, :, :3]) * 255.0
        comparison_metrics = {
            "meanAbsRgb8": float(delta.mean()),
            "changedPixelRatio2": float((delta.max(axis=2) > 2.0).mean()),
            "changedPixelRatio8": float((delta.max(axis=2) > 8.0).mean()),
        }
    sources = {
        "townPlate": str(PLATE.relative_to(ROOT)),
        "e4Models": {key: str(path.relative_to(ROOT)) for key, path in e4.E4_MODELS.items()},
        "e5Models": {key: str(path.relative_to(ROOT)) for key, path in e5.E5_MODELS.items()},
        "e4Manifest": "assets/pilots/plaza-props-3d/era-props.e4.json",
        "e5Manifest": "assets/pilots/plaza-props-3d/era-props.e5.json",
    }
    tracked_paths = [PLATE, *e4.E4_MODELS.values(), *e5.E5_MODELS.values()]
    report = {
        "baseSha": BASE_SHA,
        "label": REFERENCE_LABEL,
        "rule": "fresh render from current tracked GLBs and manifests; no prior PNG is an input",
        "order": ["E1 current plate", "E4 Motor town overview", "E5 submerged harbor overview"],
        "sources": sources,
        "assetSha256": {str(path.relative_to(ROOT)): sha256(path) for path in tracked_paths},
        "comparisonMetrics": comparison_metrics,
        "renders": [str(path.relative_to(ROOT)) for path in [
            *renders,
            *([OUT / "e3-e4-current-motor-caravan.png", OUT / "town-e1-e4-e5-current.png"] if REFERENCE_LABEL == "main" else []),
            *comparison_renders,
        ]],
    }
    (OUT / "reference-contract.json").write_text(json.dumps(report, indent=2) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if "--" in sys.argv:
        target = sys.argv[sys.argv.index("--") + 1]
        if target == "assemble":
            assemble()
            return
        {"e1": render_e1, "e4": render_e4, "e5": render_e5, "e4wagon": render_e4_wagon}[target](OUT / {
            "e1": "town-e1-current.png",
            "e4": "town-e4-current.png",
            "e5": "town-e5-current-underwater.png",
            "e4wagon": "e3-e4-current-motor-caravan.png",
        }[target])
        return
    targets = ("e1", "e4", "e5", "e4wagon") if REFERENCE_LABEL == "main" else ("e4",)
    for target in targets:
        subprocess.run(
            [bpy.app.binary_path, "--background", "--python", str(Path(__file__).resolve()), "--", target],
            check=True,
        )
    assemble()


if __name__ == "__main__":
    main()
