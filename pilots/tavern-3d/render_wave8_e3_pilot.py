from pathlib import Path
import importlib.util
import json
import shutil
import subprocess
import sys

import bpy

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "artifacts/town-e3-pilot"
E2_DIR = OUT / "e2"
E3_DIR = OUT / "e3"
TURNTABLE_DIR = OUT / "turntables"
BLIND_DIR = OUT / "blind-verdict"
BLIND_CROP_DIR = OUT / "blind-crops-verdict"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


town_render = load_module("wave7_render", HERE / "render_wave7_e2_variants.py")
town_render.TURNTABLE_DIR = TURNTABLE_DIR

E3_MODELS = {
    "tavern": ROOT / "assets/pilots/tavern-3d/tavern.e3.glb",
    "schoolhouse": ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.e3.glb",
    "stamp-mill": ROOT / "assets/pilots/stamp-mill-3d/stamp-mill.e3.glb",
}


def ensure_directories():
    for directory in (OUT, E2_DIR, E3_DIR, TURNTABLE_DIR, BLIND_DIR, BLIND_CROP_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def render_town_target(target):
    ensure_directories()
    if target == "baseline-full":
        town_render.render_town(
            town_render.E2_MODELS, E2_DIR / "town-e2-baseline.png", e2_props=True, accessories=False,
        )
    elif target in E3_MODELS:
        town_render.render_town(
            {**town_render.E2_MODELS, target: E3_MODELS[target]}, E3_DIR / f"{target}.png",
            e2_props=True, accessories=False,
        )
    elif target == "baseline-buildings":
        town_render.render_town(
            town_render.E2_MODELS, E2_DIR / "town-e2-buildings-only.png", e2_props=True, accessories=False,
        )
    elif target == "integrated":
        town_render.render_town(
            {**town_render.E2_MODELS, **E3_MODELS}, E3_DIR / "town-three-pilot.png",
            e2_props=True, accessories=False,
        )
    else:
        raise ValueError(target)


def assemble_evidence():
    baseline = E2_DIR / "town-e2-baseline.png"
    metrics = {}
    blind_key = {}
    blind_orders = {"tavern": ("e2", "e3"), "schoolhouse": ("e3", "e2"), "stamp-mill": ("e2", "e3")}

    for asset_id in E3_MODELS:
        candidate = E3_DIR / f"{asset_id}.png"
        town_render.combine_ab(baseline, candidate, OUT / f"{asset_id}-town-verdict-e2-e3-ab.png")
        metrics[asset_id] = town_render.comparison_metrics(baseline, candidate)

        sources = {"e2": baseline, "e3": candidate}
        order = blind_orders[asset_id]
        for label, era in zip(("a", "b"), order):
            shutil.copyfile(sources[era], BLIND_DIR / f"{asset_id}-{label}.png")
        blind_key[asset_id] = {"a": order[0], "b": order[1]}

    crop_specs = {
        "tavern": (260, 280, 150, 720),
        "schoolhouse": (280, 300, 410, 830),
        "stamp-mill": (220, 300, 580, 280),
    }
    for asset_id, (height, width, y, x) in crop_specs.items():
        for label in ("a", "b"):
            subprocess.run(
                [
                    "sips", "-c", str(height), str(width),
                    "--cropOffset", str(y), str(x),
                    str(BLIND_DIR / f"{asset_id}-{label}.png"),
                    "--out", str(BLIND_CROP_DIR / f"{asset_id}-{label}.png"),
                ],
                check=True, stdout=subprocess.DEVNULL,
            )
        town_render.combine_ab(
            BLIND_CROP_DIR / f"{asset_id}-a.png",
            BLIND_CROP_DIR / f"{asset_id}-b.png",
            BLIND_CROP_DIR / f"{asset_id}-pair.png",
        )

    integrated_baseline = E2_DIR / "town-e2-buildings-only.png"
    integrated = E3_DIR / "town-three-pilot.png"
    town_render.combine_ab(integrated_baseline, integrated, OUT / "town-three-pilot-verdict-e2-e3-ab.png")
    metrics["integrated"] = town_render.comparison_metrics(integrated_baseline, integrated)

    ortho_scales = {"tavern": 6.2, "schoolhouse": 7.0, "stamp-mill": 7.0}
    for asset_id, ortho_scale in ortho_scales.items():
        e2_sheet = TURNTABLE_DIR / f"{asset_id}-e2.png"
        e3_sheet = TURNTABLE_DIR / f"{asset_id}-e3.png"
        town_render.render_turntable(
            town_render.E2_MODELS[asset_id], e2_sheet, f"{asset_id}-e2", ortho_scale,
        )
        town_render.render_turntable(E3_MODELS[asset_id], e3_sheet, f"{asset_id}-e3", ortho_scale)
        town_render.combine_ab(e2_sheet, e3_sheet, OUT / f"{asset_id}-turntable-final-e2-e3-ab.png")

    (OUT / "comparison-metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (OUT / "blind-key.json").write_text(json.dumps(blind_key, indent=2) + "\n")


def main():
    ensure_directories()
    if "--" in sys.argv:
        render_town_target(sys.argv[sys.argv.index("--") + 1])
        return
    for target in ("baseline-full", *E3_MODELS, "baseline-buildings", "integrated"):
        subprocess.run(
            [bpy.app.binary_path, "--background", "--python", str(Path(__file__).resolve()), "--", target],
            check=True, stdout=subprocess.DEVNULL,
        )
    assemble_evidence()


if __name__ == "__main__":
    main()
