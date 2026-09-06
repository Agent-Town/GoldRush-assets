from pathlib import Path
import importlib.util
import json
import math
import subprocess
import sys

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "artifacts/town-e4-wide"
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


pilot = load_module("wave9_e4_pilot_render", HERE / "render_wave9_e4_pilot.py")
town_render = pilot.town_render
town = pilot.town
town_render.TURNTABLE_DIR = TURNTABLE_DIR
pilot.OUT = OUT
pilot.E3_DIR = E3_DIR
pilot.E4_DIR = E4_DIR
pilot.TURNTABLE_DIR = TURNTABLE_DIR
pilot.BLIND_DIR = BLIND_DIR

E3_MODELS = pilot.E3_MODELS
E4_MODELS = {
    "tavern": ROOT / "assets/pilots/tavern-3d/tavern.e4.glb",
    "general_store": ROOT / "assets/pilots/general-store-3d/general-store.e4.glb",
    "claim_office": ROOT / "assets/pilots/claim-office-3d/claim-office.e4.glb",
    "assay_office": ROOT / "assets/pilots/assay-office-3d/assay-office.e4.glb",
    "chapel": ROOT / "assets/pilots/chapel-3d/chapel.e4.glb",
    "schoolhouse": ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.e4.glb",
    "stamp-mill": ROOT / "assets/pilots/stamp-mill-3d/stamp-mill.e4.glb",
    "dynamo-hall": ROOT / "assets/pilots/dynamo-hall-3d/dynamo-hall.e4.glb",
}
MANIFESTS = [
    json.loads((PROPS / f"era-props.e{epoch}.json").read_text())
    for epoch in (2, 3, 4)
]
pilot.E3_MODELS = E3_MODELS
pilot.E4_MODELS = E4_MODELS


def ensure_directories():
    for directory in (OUT, E3_DIR, E4_DIR, TURNTABLE_DIR, BLIND_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def add_town_context(overrides):
    integrated = len(overrides) == len(E4_MODELS)
    paths = {**E3_MODELS, **overrides}
    for slot in [*town.SLOTS, town.DYNAMO_SLOT]:
        town.import_model(paths[slot.id], f"RenderBuilding:{slot.id}", slot.position, town.slot_angle(slot))
    prop_paths = {
        "covered_wagon": PROPS / f"covered_wagon.e{4 if integrated else 3}.glb",
        "water_trough": PROPS / f"water_trough.e{4 if integrated else 3}.glb",
        "pan_monument": PROPS / "pan_monument.glb",
    }
    for prop in town.PROPS:
        path = prop_paths.get(prop.kind)
        if path:
            town.import_model(path, f"RenderProp:{prop.id}", prop.position, prop.rotation, prop.scale)
    manifests = MANIFESTS if integrated else MANIFESTS[:2]
    for manifest in manifests:
        for descriptor in manifest["props"]:
            position = descriptor["position"]
            town.import_model(
                PROPS / descriptor["glb"], f'RenderEraProp:{descriptor["id"]}',
                town.Point(position["x"], position["z"]), descriptor["rotation"], descriptor["scale"],
            )


pilot.add_town_context = add_town_context


def add_clearance_overlay():
    route_material = town.emission_material("Wave9 route overlay", (0.08, 0.78, 0.76, 1), 1.8)
    retained_material = town.emission_material("Wave9 retained E2 E3 clearance", (0.98, 0.82, 0.20, 1), 1.8)
    e4_material = town.emission_material("Wave9 E4 prop clearance", (0.96, 0.34, 0.10, 1), 1.8)
    town.curve_object("WalkLoop:ring-road", town.RING_ROUTE, route_material, True, 0.10)
    for route_id, points in town.RADIAL_ROUTES.items():
        town.curve_object(f"HeroPath:{route_id}", points, route_material, False, 0.10)
    radii = {
        "coal-bin.e2.glb": 0.65, "pipe-run.e2.glb": 1.05, "gauge-post.e2.glb": 0.42,
        "iron-lamp-post.e2.glb": 0.65, "pressure-manifold.e2.glb": 0.82,
        "wire-run.e3.glb": 1.20, "insulator-post.e3.glb": 0.50, "transformer-shed.e3.glb": 1.0,
        "fuel-rack.e4.glb": 0.90, "road-marker.e4.glb": 1.10, "filling-shed.e4.glb": 1.65,
    }
    for manifest in MANIFESTS:
        material = e4_material if manifest["epoch"] == 4 else retained_material
        for descriptor in manifest["props"]:
            if descriptor["glb"] not in radii:
                continue
            center = descriptor["position"]
            radius = radii[descriptor["glb"]] * descriptor["scale"]
            points = [
                town.Point(
                    center["x"] + math.sin(index / 24 * math.tau) * radius,
                    center["z"] + math.cos(index / 24 * math.tau) * radius,
                )
                for index in range(24)
            ]
            town.curve_object(f'Clearance:{descriptor["id"]}', points, material, True, 0.115)


def render_target(target):
    ensure_directories()
    if target == "baseline":
        pilot.render_town({}, E3_DIR / "town-e3-baseline.png")
    elif target in E4_MODELS:
        pilot.render_town({target: E4_MODELS[target]}, E4_DIR / f"{target}.png")
    elif target in {"integrated", "clearance"}:
        town.reset_scene()
        town.import_model(ROOT / "assets/pilots/town-plate-3d/town-plate.glb", "RenderTownPlate", town.Point(0, 0))
        add_town_context(E4_MODELS)
        town.setup_render_scene()
        if target == "clearance":
            add_clearance_overlay()
        town.render(E4_DIR / "town-e4-wide.png" if target == "integrated" else OUT / "e4-accessory-clearance-overlay.png")
    else:
        raise ValueError(target)


def render_accessory_pack(path):
    town.reset_scene()
    for index, stem in enumerate(("fuel-rack.e4.glb", "road-marker.e4.glb", "filling-shed.e4.glb")):
        town_render.import_review_model(PROPS / stem, f"Accessory:{stem}", ((index - 1) * 2.6, 1.0, 0))
    town_render.import_review_model(PROPS / "covered_wagon.e4.glb", "Variant:covered_wagon", (-1.6, -1.25, 0), 1.25)
    bpy.data.objects["Variant:covered_wagon"].rotation_euler[2] = math.pi + 0.52
    town_render.import_review_model(PROPS / "water_trough.e4.glb", "Variant:water_trough", (1.6, -1.25, 0), 1.25)
    bpy.data.objects["Variant:water_trough"].rotation_euler[2] = math.pi
    town_render.setup_review_scene(path, 9.8)


def render_wagon_accretion(path):
    town.reset_scene()
    for x, era in ((-1.25, 3), (1.25, 4)):
        name = f"WagonRelic:E{era}"
        town_render.import_review_model(PROPS / f"covered_wagon.e{era}.glb", name, (x, 0, 0), 1.35)
        bpy.data.objects[name].rotation_euler[2] = math.pi + 0.52
    town_render.setup_review_scene(path, 5.2)


def assemble_evidence():
    baseline = E3_DIR / "town-e3-baseline.png"
    metrics = {}
    blind_key = {}
    orders = {
        asset_id: (("e3", "e4") if index % 2 else ("e4", "e3"))
        for index, asset_id in enumerate(E4_MODELS)
    }
    for asset_id in E4_MODELS:
        candidate = E4_DIR / f"{asset_id}.png"
        town_render.combine_ab(baseline, candidate, OUT / f"{asset_id}-town-verdict-e3-e4-ab.png")
        if asset_id == "chapel":
            bounds = (720, 0, 1020, 220)
            base = town_render.image_array(baseline)
            changed = town_render.image_array(candidate)
            sources = {"e3": base[bounds[1]:bounds[3], bounds[0]:bounds[2]],
                       "e4": changed[bounds[1]:bounds[3], bounds[0]:bounds[2]]}
            for label, era in zip(("a", "b"), orders[asset_id]):
                pilot.save_array(sources[era], BLIND_DIR / f"{asset_id}-{label}.png")
            town_render.combine_ab(BLIND_DIR / f"{asset_id}-a.png", BLIND_DIR / f"{asset_id}-b.png",
                                   BLIND_DIR / f"{asset_id}-pair.png")
            metrics[asset_id] = town_render.comparison_metrics(baseline, candidate)
            base_gray = (
                sources["e3"][:, :, 0] * 0.2126
                + sources["e3"][:, :, 1] * 0.7152
                + sources["e3"][:, :, 2] * 0.0722
            ) * 255.0
            candidate_gray = (
                sources["e4"][:, :, 0] * 0.2126
                + sources["e4"][:, :, 1] * 0.7152
                + sources["e4"][:, :, 2] * 0.0722
            ) * 255.0
            changed = np.abs(candidate_gray - base_gray) > 2.0
            base_luma = float(base_gray.mean())
            candidate_luma = float(candidate_gray.mean())
            delta = (candidate_luma - base_luma) / max(base_luma, 1e-9) * 100.0
            metrics[asset_id]["localizedTonalGate"] = {
                "method": "cadence-approved quiet fixture; ensemble owns the era read",
                "crop": {"x": bounds[0], "y": bounds[1], "width": bounds[2] - bounds[0], "height": bounds[3] - bounds[1]},
                "changedPixelCount": int(changed.sum()), "avgLuminanceBase": base_luma,
                "avgLuminanceCandidate": candidate_luma,
                "deltaPercent": delta, "ceilingPercent": 5.0, "passed": abs(delta) <= 5.0,
            }
            crop = {"crop": metrics[asset_id]["localizedTonalGate"]["crop"],
                    "changedPixelCount": int(changed.sum()), "changedRatioInCrop": float(changed.mean())}
        else:
            metrics[asset_id] = pilot.localized_metrics(baseline, candidate)
            crop = pilot.crop_pair(baseline, candidate, asset_id, orders[asset_id])
        blind_key[asset_id] = {"a": orders[asset_id][0], "b": orders[asset_id][1], **crop}
    integrated = E4_DIR / "town-e4-wide.png"
    town_render.combine_ab(baseline, integrated, OUT / "town-wide-verdict-e3-e4-ab.png")
    town_render.combine_ab(integrated, baseline, OUT / "town-ensemble-blind-pair.png")
    blind_key["integrated"] = {"a": "e4", "b": "e3"}
    metrics["integrated"] = town_render.comparison_metrics(baseline, integrated)
    scales = {
        "tavern": 6.2, "general_store": 6.6, "claim_office": 6.6, "assay_office": 6.4,
        "chapel": 8.2, "schoolhouse": 7.0, "stamp-mill": 7.0, "dynamo-hall": 7.2,
    }
    for asset_id, scale in scales.items():
        e3_sheet = TURNTABLE_DIR / f"{asset_id}-e3.png"
        e4_sheet = TURNTABLE_DIR / f"{asset_id}-e4.png"
        town_render.render_turntable(E3_MODELS[asset_id], e3_sheet, f"{asset_id}-e3", scale)
        town_render.render_turntable(E4_MODELS[asset_id], e4_sheet, f"{asset_id}-e4", scale)
        town_render.combine_ab(e3_sheet, e4_sheet, OUT / f"{asset_id}-turntable-e3-e4-ab.png")
    render_accessory_pack(OUT / "accessory-pack-e4.png")
    render_wagon_accretion(OUT / "wagon-accretion-e3-e4-ab.png")
    (OUT / "comparison-metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (OUT / "blind-key.json").write_text(json.dumps(blind_key, indent=2) + "\n")


def main():
    ensure_directories()
    if "--" in sys.argv:
        render_target(sys.argv[sys.argv.index("--") + 1])
        return
    for target in ("baseline", *E4_MODELS, "integrated", "clearance"):
        subprocess.run(
            [bpy.app.binary_path, "--background", "--python", str(Path(__file__).resolve()), "--", target],
            check=True, stdout=subprocess.DEVNULL,
        )
    assemble_evidence()


if __name__ == "__main__":
    main()
