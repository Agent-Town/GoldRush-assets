from pathlib import Path
import importlib.util
import json
import math
import shutil
import subprocess
import sys

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "artifacts/town-e3-wide"
E2_DIR = OUT / "e2"
E3_DIR = OUT / "e3"
TURNTABLE_DIR = OUT / "turntables"
BLIND_DIR = OUT / "blind-verdict"
PROPS = ROOT / "assets/pilots/plaza-props-3d"
MANIFEST = json.loads((PROPS / "era-props.e3.json").read_text())
E2_MANIFEST = json.loads((PROPS / "era-props.e2.json").read_text())


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


town_render = load_module("wave7_render", HERE / "render_wave7_e2_variants.py")
town_render.TURNTABLE_DIR = TURNTABLE_DIR
town = town_render.town

E3_MODELS = {
    "tavern": ROOT / "assets/pilots/tavern-3d/tavern.e3.glb",
    "general_store": ROOT / "assets/pilots/general-store-3d/general-store.e3.glb",
    "claim_office": ROOT / "assets/pilots/claim-office-3d/claim-office.e3.glb",
    "assay_office": ROOT / "assets/pilots/assay-office-3d/assay-office.e3.glb",
    "chapel": ROOT / "assets/pilots/chapel-3d/chapel.e3.glb",
    "schoolhouse": ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.e3.glb",
    "stamp-mill": ROOT / "assets/pilots/stamp-mill-3d/stamp-mill.e3.glb",
    "dynamo-hall": ROOT / "assets/pilots/dynamo-hall-3d/dynamo-hall.e3.glb",
}


def ensure_directories():
    for directory in (OUT, E2_DIR, E3_DIR, TURNTABLE_DIR, BLIND_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def add_e3_context():
    for slot in [*town.SLOTS, town.DYNAMO_SLOT]:
        town.import_model(E3_MODELS[slot.id], f"RenderBuilding:{slot.id}", slot.position, town.slot_angle(slot))
    prop_paths = {
        "covered_wagon": PROPS / "covered_wagon.e3.glb",
        "water_trough": PROPS / "water_trough.e3.glb",
        "pan_monument": PROPS / "pan_monument.glb",
    }
    for prop in town.PROPS:
        path = prop_paths.get(prop.kind)
        if path:
            town.import_model(path, f"RenderProp:{prop.id}", prop.position, prop.rotation, prop.scale)
    for manifest in (E2_MANIFEST, MANIFEST):
        for descriptor in manifest["props"]:
            position = descriptor["position"]
            town.import_model(
                PROPS / descriptor["glb"], f'RenderEraProp:{descriptor["id"]}',
                town.Point(position["x"], position["z"]), descriptor["rotation"], descriptor["scale"],
            )


def add_clearance_overlay():
    route_material = town.emission_material("Wave8 route overlay", (0.08, 0.78, 0.76, 1), 1.8)
    retained_material = town.emission_material("Wave8 retained E2 clearance", (0.98, 0.82, 0.20, 1), 1.8)
    footprint_material = town.emission_material("Wave8 E3 prop clearance", (0.96, 0.34, 0.10, 1), 1.8)
    town.curve_object("WalkLoop:ring-road", town.RING_ROUTE, route_material, True, 0.10)
    for route_id, points in town.RADIAL_ROUTES.items():
        town.curve_object(f"HeroPath:{route_id}", points, route_material, False, 0.10)
    radii = {
        "coal-bin.e2.glb": 0.65, "pipe-run.e2.glb": 1.05, "gauge-post.e2.glb": 0.42,
        "iron-lamp-post.e2.glb": 0.65, "pressure-manifold.e2.glb": 0.82,
        "wire-run.e3.glb": 1.20, "insulator-post.e3.glb": 0.50, "transformer-shed.e3.glb": 1.0,
    }
    for manifest, material in ((E2_MANIFEST, retained_material), (MANIFEST, footprint_material)):
        for descriptor in manifest["props"]:
            center = descriptor["position"]
            radius = radii[descriptor["glb"]] * descriptor["scale"]
            points = [
                town.Point(center["x"] + math.sin(index / 24 * math.tau) * radius,
                           center["z"] + math.cos(index / 24 * math.tau) * radius)
                for index in range(24)
            ]
            town.curve_object(f'Clearance:{descriptor["id"]}', points, material, True, 0.115)


def render_e3_town(path, overlay=False):
    town.reset_scene()
    town.import_model(ROOT / "assets/pilots/town-plate-3d/town-plate.glb", "RenderTownPlate", town.Point(0, 0))
    add_e3_context()
    town.setup_render_scene()
    if overlay:
        add_clearance_overlay()
    town.render(path)


def render_target(target):
    ensure_directories()
    if target == "baseline":
        town_render.render_town(
            town_render.E2_MODELS, E2_DIR / "town-e2-wide-baseline.png", e2_props=True, accessories=True,
        )
    elif target in E3_MODELS:
        town_render.render_town(
            {**town_render.E2_MODELS, target: E3_MODELS[target]}, E3_DIR / f"{target}.png",
            e2_props=True, accessories=True,
        )
    elif target == "integrated":
        render_e3_town(E3_DIR / "town-e3-wide.png")
    elif target == "clearance":
        render_e3_town(OUT / "e3-accessory-clearance-overlay.png", overlay=True)
    else:
        raise ValueError(target)


def render_accessory_pack(path):
    town.reset_scene()
    for index, stem in enumerate(("wire-run.e3.glb", "insulator-post.e3.glb", "transformer-shed.e3.glb")):
        town_render.import_review_model(PROPS / stem, f"Accessory:{stem}", ((index - 1) * 2.5, 1.0, 0))
    town_render.import_review_model(PROPS / "covered_wagon.e3.glb", "Variant:covered_wagon", (-1.6, -1.2, 0), 1.25)
    town_render.import_review_model(PROPS / "water_trough.e3.glb", "Variant:water_trough", (1.6, -1.2, 0), 1.25)
    town_render.setup_review_scene(path, 9.5)


def localized_comparison_metrics(base_path, candidate_path, padding=64):
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
        raise RuntimeError(f"No changed target pixels between {base_path} and {candidate_path}")
    x0, x1 = max(0, int(xs.min()) - padding), min(base_gray.shape[1], int(xs.max()) + 1 + padding)
    y0, y1 = max(0, int(ys.min()) - padding), min(base_gray.shape[0], int(ys.max()) + 1 + padding)
    localized_base = float(base_gray[y0:y1, x0:x1].mean())
    localized_candidate = float(candidate_gray[y0:y1, x0:x1].mean())
    delta_percent = (localized_candidate - localized_base) / max(localized_base, 1e-9) * 100.0
    if abs(delta_percent) > 5.0:
        raise RuntimeError(f"Localized tonal delta {delta_percent:.4f}% exceeds 5% for {candidate_path.stem}")
    metrics["localizedTonalGate"] = {
        "method": "changed-pixel bounds plus 64px building-and-neighbor context",
        "crop": {"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0},
        "changedPixelCount": int(changed.sum()),
        "avgLuminanceBase": localized_base,
        "avgLuminanceCandidate": localized_candidate,
        "deltaPercent": delta_percent,
        "ceilingPercent": 5.0,
        "passed": True,
    }
    return metrics


def assemble_evidence():
    baseline = E2_DIR / "town-e2-wide-baseline.png"
    metrics = {}
    blind_key = {}
    blind_orders = {
        "tavern": ("e2", "e3"), "general_store": ("e3", "e2"),
        "claim_office": ("e2", "e3"), "assay_office": ("e3", "e2"),
        "chapel": ("e2", "e3"), "schoolhouse": ("e3", "e2"),
        "stamp-mill": ("e2", "e3"), "dynamo-hall": ("e3", "e2"),
    }
    for asset_id in E3_MODELS:
        candidate = E3_DIR / f"{asset_id}.png"
        town_render.combine_ab(baseline, candidate, OUT / f"{asset_id}-town-verdict-e2-e3-ab.png")
        metrics[asset_id] = localized_comparison_metrics(baseline, candidate)
        sources = {"e2": baseline, "e3": candidate}
        order = blind_orders[asset_id]
        for label, era in zip(("a", "b"), order):
            shutil.copyfile(sources[era], BLIND_DIR / f"{asset_id}-{label}.png")
        town_render.combine_ab(
            BLIND_DIR / f"{asset_id}-a.png", BLIND_DIR / f"{asset_id}-b.png",
            BLIND_DIR / f"{asset_id}-pair.png",
        )
        blind_key[asset_id] = {"a": order[0], "b": order[1]}

    integrated = E3_DIR / "town-e3-wide.png"
    town_render.combine_ab(baseline, integrated, OUT / "town-wide-verdict-e2-e3-ab.png")
    metrics["integrated"] = town_render.comparison_metrics(baseline, integrated)

    scales = {
        "tavern": 6.2, "general_store": 6.6, "claim_office": 6.6, "assay_office": 6.4,
        "chapel": 7.2, "schoolhouse": 7.0, "stamp-mill": 7.0, "dynamo-hall": 7.2,
    }
    for asset_id, scale in scales.items():
        e2_sheet = TURNTABLE_DIR / f"{asset_id}-e2.png"
        e3_sheet = TURNTABLE_DIR / f"{asset_id}-e3.png"
        town_render.render_turntable(town_render.E2_MODELS[asset_id], e2_sheet, f"{asset_id}-e2", scale)
        town_render.render_turntable(E3_MODELS[asset_id], e3_sheet, f"{asset_id}-e3", scale)
        town_render.combine_ab(e2_sheet, e3_sheet, OUT / f"{asset_id}-turntable-e2-e3-ab.png")

    render_accessory_pack(OUT / "accessory-pack-e3.png")
    (OUT / "comparison-metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (OUT / "blind-key.json").write_text(json.dumps(blind_key, indent=2) + "\n")


def main():
    ensure_directories()
    if "--" in sys.argv:
        render_target(sys.argv[sys.argv.index("--") + 1])
        return
    for target in ("baseline", *E3_MODELS, "integrated", "clearance"):
        subprocess.run(
            [bpy.app.binary_path, "--background", "--python", str(Path(__file__).resolve()), "--", target],
            check=True, stdout=subprocess.DEVNULL,
        )
    assemble_evidence()


if __name__ == "__main__":
    main()
