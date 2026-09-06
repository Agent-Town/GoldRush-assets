from pathlib import Path
import importlib.util
import json
import subprocess
import sys

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "artifacts/town-e4-pilot"
E3_DIR = OUT / "e3"
E4_DIR = OUT / "e4"
TURNTABLE_DIR = OUT / "turntables"
BLIND_DIR = OUT / "blind-crops"
PROPS = ROOT / "assets/pilots/plaza-props-3d"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


e3_render = load_module("wave8_e3_wide_render", HERE / "render_wave8_e3_wide.py")
town_render = e3_render.town_render
town_render.TURNTABLE_DIR = TURNTABLE_DIR
town = town_render.town

E3_MODELS = e3_render.E3_MODELS
E4_MODELS = {
    "tavern": ROOT / "assets/pilots/tavern-3d/tavern.e4.glb",
    "schoolhouse": ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.e4.glb",
}
E2_MANIFEST = json.loads((PROPS / "era-props.e2.json").read_text())
E3_MANIFEST = json.loads((PROPS / "era-props.e3.json").read_text())


def ensure_directories():
    for directory in (OUT, E3_DIR, E4_DIR, TURNTABLE_DIR, BLIND_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def add_town_context(overrides):
    paths = {**E3_MODELS, **overrides}
    for slot in [*town.SLOTS, town.DYNAMO_SLOT]:
        town.import_model(paths[slot.id], f"RenderBuilding:{slot.id}", slot.position, town.slot_angle(slot))
    prop_paths = {
        "covered_wagon": PROPS / "covered_wagon.e3.glb",
        "water_trough": PROPS / "water_trough.e3.glb",
        "pan_monument": PROPS / "pan_monument.glb",
    }
    for prop in town.PROPS:
        path = prop_paths.get(prop.kind)
        if path:
            town.import_model(path, f"RenderProp:{prop.id}", prop.position, prop.rotation, prop.scale)
    for manifest in (E2_MANIFEST, E3_MANIFEST):
        for descriptor in manifest["props"]:
            position = descriptor["position"]
            town.import_model(
                PROPS / descriptor["glb"], f'RenderEraProp:{descriptor["id"]}',
                town.Point(position["x"], position["z"]), descriptor["rotation"], descriptor["scale"],
            )


def render_town(overrides, path):
    town.reset_scene()
    town.import_model(ROOT / "assets/pilots/town-plate-3d/town-plate.glb", "RenderTownPlate", town.Point(0, 0))
    add_town_context(overrides)
    town.setup_render_scene()
    town.render(path)


def render_target(target):
    ensure_directories()
    if target == "baseline":
        render_town({}, E3_DIR / "town-e3-baseline.png")
    elif target in E4_MODELS:
        render_town({target: E4_MODELS[target]}, E4_DIR / f"{target}.png")
    elif target == "integrated":
        render_town(E4_MODELS, E4_DIR / "town-two-pilot.png")
    else:
        raise ValueError(target)


def save_array(array, output):
    height, width, _ = array.shape
    rgba = np.concatenate((array, np.ones((height, width, 1), dtype=np.float32)), axis=2)
    image = bpy.data.images.new(output.stem, width, height, alpha=True)
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(output)
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)


def crop_pair(base_path, candidate_path, asset_id, order, padding=42):
    base = town_render.image_array(base_path)
    candidate = town_render.image_array(candidate_path)
    base_gray = (base[:, :, 0] * 0.2126 + base[:, :, 1] * 0.7152 + base[:, :, 2] * 0.0722) * 255.0
    candidate_gray = (
        candidate[:, :, 0] * 0.2126 + candidate[:, :, 1] * 0.7152 + candidate[:, :, 2] * 0.0722
    ) * 255.0
    changed = np.abs(candidate_gray - base_gray) > 2.0
    ys, xs = np.where(changed)
    if not len(xs):
        raise RuntimeError(f"No changed pixels for {asset_id}")
    x0, x1 = max(0, int(xs.min()) - padding), min(base.shape[1], int(xs.max()) + 1 + padding)
    y0, y1 = max(0, int(ys.min()) - padding), min(base.shape[0], int(ys.max()) + 1 + padding)
    sources = {"e3": base[y0:y1, x0:x1], "e4": candidate[y0:y1, x0:x1]}
    for label, era in zip(("a", "b"), order):
        save_array(sources[era], BLIND_DIR / f"{asset_id}-{label}.png")
    town_render.combine_ab(
        BLIND_DIR / f"{asset_id}-a.png", BLIND_DIR / f"{asset_id}-b.png",
        BLIND_DIR / f"{asset_id}-pair.png",
    )
    return {
        "crop": {"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0},
        "changedPixelCount": int(changed.sum()),
        "changedRatioInCrop": float(changed[y0:y1, x0:x1].mean()),
    }


def localized_metrics(base_path, candidate_path, padding=64):
    metrics = town_render.comparison_metrics(base_path, candidate_path)
    base = town_render.image_array(base_path)
    candidate = town_render.image_array(candidate_path)
    base_gray = (base[:, :, 0] * 0.2126 + base[:, :, 1] * 0.7152 + base[:, :, 2] * 0.0722) * 255.0
    candidate_gray = (
        candidate[:, :, 0] * 0.2126 + candidate[:, :, 1] * 0.7152 + candidate[:, :, 2] * 0.0722
    ) * 255.0
    changed = np.abs(candidate_gray - base_gray) > 2.0
    ys, xs = np.where(changed)
    if not len(xs):
        raise RuntimeError("No changed target pixels")
    x0, x1 = max(0, int(xs.min()) - padding), min(base.shape[1], int(xs.max()) + 1 + padding)
    y0, y1 = max(0, int(ys.min()) - padding), min(base.shape[0], int(ys.max()) + 1 + padding)
    base_luma = float(base_gray[y0:y1, x0:x1].mean())
    candidate_luma = float(candidate_gray[y0:y1, x0:x1].mean())
    delta = (candidate_luma - base_luma) / max(base_luma, 1e-9) * 100.0
    if abs(delta) > 5.0:
        raise RuntimeError(f"Localized tonal delta {delta:.4f}% exceeds 5%")
    metrics["localizedTonalGate"] = {
        "method": "changed-pixel bounds plus 64px building-and-neighbor context",
        "crop": {"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0},
        "changedPixelCount": int(changed.sum()),
        "avgLuminanceBase": base_luma,
        "avgLuminanceCandidate": candidate_luma,
        "deltaPercent": delta,
        "ceilingPercent": 5.0,
        "passed": True,
    }
    return metrics


def assemble_evidence():
    baseline = E3_DIR / "town-e3-baseline.png"
    metrics = {}
    blind_orders = {"tavern": ("e4", "e3"), "schoolhouse": ("e3", "e4")}
    blind_key = {}
    for asset_id in E4_MODELS:
        candidate = E4_DIR / f"{asset_id}.png"
        town_render.combine_ab(baseline, candidate, OUT / f"{asset_id}-town-verdict-e3-e4-ab.png")
        metrics[asset_id] = localized_metrics(baseline, candidate)
        crop = crop_pair(baseline, candidate, asset_id, blind_orders[asset_id])
        blind_key[asset_id] = {
            "a": blind_orders[asset_id][0], "b": blind_orders[asset_id][1], **crop,
        }

    integrated = E4_DIR / "town-two-pilot.png"
    town_render.combine_ab(baseline, integrated, OUT / "town-two-pilot-verdict-e3-e4-ab.png")
    metrics["integrated"] = town_render.comparison_metrics(baseline, integrated)

    scales = {"tavern": 6.2, "schoolhouse": 7.8}
    for asset_id, scale in scales.items():
        e3_sheet = TURNTABLE_DIR / f"{asset_id}-e3.png"
        e4_sheet = TURNTABLE_DIR / f"{asset_id}-e4.png"
        town_render.render_turntable(E3_MODELS[asset_id], e3_sheet, f"{asset_id}-e3", scale)
        town_render.render_turntable(E4_MODELS[asset_id], e4_sheet, f"{asset_id}-e4", scale)
        town_render.combine_ab(e3_sheet, e4_sheet, OUT / f"{asset_id}-turntable-e3-e4-ab.png")

    (OUT / "comparison-metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (OUT / "blind-key.json").write_text(json.dumps(blind_key, indent=2) + "\n")


def main():
    ensure_directories()
    if "--" in sys.argv:
        render_target(sys.argv[sys.argv.index("--") + 1])
        return
    for target in ("baseline", *E4_MODELS, "integrated"):
        subprocess.run(
            [bpy.app.binary_path, "--background", "--python", str(Path(__file__).resolve()), "--", target],
            check=True, stdout=subprocess.DEVNULL,
        )
    assemble_evidence()


if __name__ == "__main__":
    main()
