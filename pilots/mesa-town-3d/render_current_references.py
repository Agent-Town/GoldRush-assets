from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys

sys.dont_write_bytecode = True

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
BASE_SHA = "8d974f11911187136469fbd017c9598e5b2faf28"
OUT = ROOT / "artifacts/mesa-town-3d/current-references" / f"{BASE_SHA[:12]}-main"
CURRENT_PLATE = ROOT / "assets/pilots/town-plate-3d/town-plate.glb"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


e4 = load_module("mesa_reference_e4", ROOT / "assets/pilots/tavern-3d/render_wave9_e4_wide.py")
e5 = load_module("mesa_reference_e5", ROOT / "assets/pilots/tavern-3d/render_wave10_e5_harbor.py")
town = e4.town


def render_e1(path: Path) -> None:
    town.reset_scene()
    town.import_model(CURRENT_PLATE, "RenderTownPlate", town.Point(0, 0))
    town.add_render_models()
    town.setup_render_scene()
    town.render(path)


def render_e4(path: Path) -> None:
    town.reset_scene()
    town.import_model(CURRENT_PLATE, "RenderTownPlate", town.Point(0, 0))
    e4.add_town_context(e4.E4_MODELS)
    town.setup_render_scene()
    camera = bpy.context.scene.camera
    camera.location = (0.0, 24.5, 34.5)
    town.look_at(camera, Vector((0.0, -1.5, 0.45)))
    town.render(path)


def render_e5(path: Path) -> None:
    e5.render_town(e5.E5_MODELS, 5, path, overview=True, underwater=True)


def render_e4_wagon(path: Path) -> None:
    e4.render_wagon_accretion(path)


def image_array(path: Path) -> np.ndarray:
    image = bpy.data.images.load(str(path), check_existing=False)
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    array = pixels.reshape(height, width, 4)
    bpy.data.images.remove(image)
    return array


def save_array(array: np.ndarray, path: Path) -> None:
    height, width, _ = array.shape
    image = bpy.data.images.new(path.stem, width, height, alpha=True)
    image.pixels.foreach_set(array.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def annotate(path: Path, label: str) -> None:
    temporary = path.with_name(f".{path.name}")
    subprocess.run(
        [
            "magick", str(path), "-font", "/System/Library/Fonts/Helvetica.ttc",
            "-gravity", "north", "-fill", "#f7df9d",
            "-undercolor", "#17120dcc", "-pointsize", "24", "-annotate", "+0+8",
            f"{label} | base {BASE_SHA}", str(temporary),
        ],
        check=True,
    )
    temporary.replace(path)


def assemble() -> None:
    renders = [
        OUT / "town-e1-current.png",
        OUT / "town-e4-current.png",
        OUT / "town-e5-current-underwater.png",
    ]
    board = OUT / "town-e1-e4-e5-current.png"
    save_array(np.concatenate([image_array(path) for path in renders], axis=1), board)
    annotate(board, "FRESH CURRENT-FILE REFERENCE | E1 / E4 / E5")
    annotate(OUT / "e3-e4-current-motor-caravan.png", "FRESH CURRENT-FILE REFERENCE | E3 / E4 WAGON")

    tracked_paths = [CURRENT_PLATE, *e4.E4_MODELS.values(), *e5.E5_MODELS.values()]
    report = {
        "baseSha": BASE_SHA,
        "rule": "fresh render from current tracked GLBs and manifests; no prior PNG is an input",
        "order": ["E1 current plate", "E4 southern boulevard and motor caravan", "E5 submerged square"],
        "sources": {
            "townPlate": str(CURRENT_PLATE.relative_to(ROOT)),
            "e4Models": {key: str(path.relative_to(ROOT)) for key, path in e4.E4_MODELS.items()},
            "e5Models": {key: str(path.relative_to(ROOT)) for key, path in e5.E5_MODELS.items()},
            "e4Manifest": "assets/pilots/plaza-props-3d/era-props.e4.json",
            "e5Manifest": "assets/pilots/plaza-props-3d/era-props.e5.json",
        },
        "assetSha256": {str(path.relative_to(ROOT)): sha256(path) for path in tracked_paths},
        "renders": [str(path.relative_to(ROOT)) for path in [*renders, OUT / "e3-e4-current-motor-caravan.png", board]],
    }
    (OUT / "reference-contract.json").write_text(json.dumps(report, indent=2) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if "--" in sys.argv:
        target = sys.argv[sys.argv.index("--") + 1]
        if target == "assemble":
            assemble()
            return
        functions = {"e1": render_e1, "e4": render_e4, "e5": render_e5, "e4wagon": render_e4_wagon}
        filenames = {
            "e1": "town-e1-current.png",
            "e4": "town-e4-current.png",
            "e5": "town-e5-current-underwater.png",
            "e4wagon": "e3-e4-current-motor-caravan.png",
        }
        functions[target](OUT / filenames[target])
        return
    for target in ("e1", "e4", "e5", "e4wagon"):
        subprocess.run(
            [bpy.app.binary_path, "--background", "--python", str(Path(__file__).resolve()), "--", target],
            check=True,
        )
    assemble()


if __name__ == "__main__":
    main()
