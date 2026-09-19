from pathlib import Path
import hashlib
import importlib.util
import json
import math
import subprocess
import sys

import bpy


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE_SHA = "3fe1e493fb11b6685f1ffc76b65dd81ebff8dd6b"
E7_PILOT_REF = "origin/sol/mesa-town-e7-pilot"
E7_PILOT_TIP = "3947af4943f784a1e26d4ed1ae9b8aed47da2293"
E7_PILOT_ASSETS = {
    "net_cafe": (
        "assets/pilots/tavern-3d/tavern.e7.glb",
        "950253635d46da078c84fa02b01ea0381eb2fb7646b63bd75ac0734d87bcf605",
    ),
    "exchange": (
        "assets/pilots/exchange-3d/exchange.glb",
        "122460f1d0a6c37d38f1e2d1a80fb75c2e2a8c61aa9008866d5d5d48e1288161",
    ),
    "relay_tower": (
        "assets/pilots/relay-tower-3d/relay-tower.glb",
        "d048511881038a144d1d1b6dd2cfbd2b8b067c496d3359bd3f8af5185c8b9eea",
    ),
}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


p = load_module("wave14_e7_render_helpers", HERE / "render_wave13_e7_pilot.py")
OUT = ROOT / "artifacts/town-e7-wide"
REFS = OUT / "current-references" / f"{BASE_SHA[:12]}-main"
E6 = OUT / "e6"
E7 = OUT / "e7"
TURNTABLES = OUT / "turntables"
IDENTITY = OUT / "identity"
TEMP = Path("/tmp/gold-rush-wave14-e7-render")

WIDE_MODELS = {
    "playbook_library": ROOT / "assets/pilots/playbook-library-3d/playbook-library.glb",
    "drone_coop": ROOT / "assets/pilots/drone-coop-3d/drone-coop.glb",
    "signal_refinery": ROOT / "assets/pilots/signal-refinery-3d/signal-refinery.glb",
    "beam_relay": ROOT / "assets/pilots/run3d/turret.e7.glb",
    "signal_works": ROOT / "assets/pilots/schoolhouse-3d/schoolhouse.e7.glb",
    "tape_post": ROOT / "assets/pilots/catalog-warehouse-3d/catalog-warehouse.e7.glb",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_directories():
    for directory in (OUT, REFS, E6, E7, TURNTABLES, IDENTITY, TEMP):
        directory.mkdir(parents=True, exist_ok=True)
    p.OUT = OUT
    p.REFS = REFS
    p.E6 = E6
    p.E7 = E7
    p.TURNTABLES = TURNTABLES
    p.IDENTITY = IDENTITY
    p.BASE_SHA = BASE_SHA
    p.town_render.TURNTABLE_DIR = TURNTABLES


def extract_pilot_assets():
    for key, (source, expected) in E7_PILOT_ASSETS.items():
        target = TEMP / f"{key}.glb"
        with target.open("wb") as handle:
            subprocess.run(["git", "show", f"{E7_PILOT_REF}:{source}"], cwd=ROOT,
                           stdout=handle, check=True)
        assert sha256(target) == expected


def add_e7_complete():
    town = p.town
    models = {}
    replacements = {
        "net_cafe": (TEMP / "net_cafe.glb", "tavern"),
        "isotope_kitchen": (p.TEMP / "isotope_kitchen.glb", "general_store"),
        "signal_works": (WIDE_MODELS["signal_works"], "schoolhouse"),
        "decay_clock": (p.TEMP / "decay_clock.glb", "claim_office"),
        "appliance_pen": (p.TEMP / "appliance_pen.glb", "assay_office"),
    }
    for key, (path, slot_id) in replacements.items():
        item = p.slot(slot_id)
        models[key] = town.import_model(path, f"Mesa:E7:{key}", item.position,
                                        town.slot_angle(item))
    models["reactor_dome"] = town.import_model(
        p.TEMP / "reactor_dome.glb", "Mesa:E7:reactor_dome", town.Point(7.0, -16.7), 0.0,
    )
    models["reactor_dome"].location.z = 1.18
    models["tape_post"] = town.import_model(
        WIDE_MODELS["tape_post"], "Mesa:E7:tape_post", town.Point(-7.4, -16.6), math.pi,
    )
    models["tape_post"].location.z = 1.18
    models["beam_relay"] = town.import_model(
        WIDE_MODELS["beam_relay"], "Mesa:E7:beam_relay", town.Point(12.0, 7.0), -0.25, 1.20,
    )
    for index, (x, y, rotation) in enumerate(
        ((-12.0, 0.8, 0.0), (12.0, 0.8, 0.0), (0.0, 12.8, 1.57)), 1,
    ):
        models[f"glow_fence_{index}"] = town.import_model(
            p.TEMP / "glow_fence.glb", f"Mesa:E7:glow_fence_{index}",
            town.Point(x, y), rotation, 1.0,
        )
    # Accepted pilot sites.
    models["exchange"] = town.import_model(
        TEMP / "exchange.glb", "Mesa:E7:exchange", town.Point(-7.55, 9.40), 0.06,
    )
    models["relay_tower"] = town.import_model(
        TEMP / "relay_tower.glb", "Mesa:E7:relay_tower", town.Point(7.55, 9.15), -0.08,
    )
    # Wide-wave sites use open, non-overlapping Mesa parcels and leave the central stage clear.
    models["playbook_library"] = town.import_model(
        WIDE_MODELS["playbook_library"], "Mesa:E7:playbook_library",
        town.Point(-14.2, -6.4), 0.12,
    )
    models["drone_coop"] = town.import_model(
        WIDE_MODELS["drone_coop"], "Mesa:E7:drone_coop", town.Point(14.2, -6.0), -0.10,
    )
    models["signal_refinery"] = town.import_model(
        WIDE_MODELS["signal_refinery"], "Mesa:E7:signal_refinery",
        town.Point(0.0, 16.2), math.pi,
    )
    return models


def setup_camera():
    p.setup_mesa_camera()
    camera = bpy.context.scene.camera
    p.town.look_at(camera, p.Vector((0.0, 0.5, 1.18)))
    camera.data.ortho_scale = max(camera.data.ortho_scale, 52.0)


def render_mesa(path, e7):
    p.town.reset_scene()
    p.town.import_model(p.TEMP / "mesa-town-plate.glb", "EvidenceExactMesaPlate",
                        p.town.Point(0, 0))
    p.add_pan_survivor()
    if e7:
        add_e7_complete()
    else:
        p.add_e6_models()
    setup_camera()
    p.town.render(path)


def render_turntables():
    for name, path in WIDE_MODELS.items():
        p.render_turntable_smart(path, TURNTABLES / f"{name.replace('_', '-')}-e7.png",
                                 f"{name.replace('_', '-')}-e7")
    comparisons = {
        "beam-relay": (p.TEMP / "sunline_mount.glb", WIDE_MODELS["beam_relay"]),
        "signal-works": (p.TEMP / "isotope_institute.glb", WIDE_MODELS["signal_works"]),
        "tape-post": (p.TEMP / "catalog_warehouse.glb", WIDE_MODELS["tape_post"]),
    }
    for name, (source, target) in comparisons.items():
        before = IDENTITY / f"{name}-e6.png"
        after = IDENTITY / f"{name}-e7.png"
        p.render_turntable_smart(source, before, f"{name}-e6")
        p.render_turntable_smart(target, after, f"{name}-e7")
        p.town_render.combine_ab(before, after, IDENTITY / f"{name}-identity-e6-e7-ab.png")


def main():
    ensure_directories()
    p.extract_dependencies()
    extract_pilot_assets()
    expected_refs = [
        REFS / "town-e1-current.png", REFS / "town-e4-current.png",
        REFS / "town-e5-current-underwater.png", REFS / "e3-e4-current-motor-caravan.png",
        REFS / "town-e1-e4-e5-current.png",
    ]
    assert all(path.is_file() for path in expected_refs), "fresh main references must render first"

    baseline = E6 / "mesa-complete-e6.png"
    candidate = E7 / "mesa-complete-e7-signal-town.png"
    render_mesa(baseline, False)
    render_mesa(candidate, True)
    p.annotate(baseline, "COMPLETE E6 ATOMIC MESA")
    p.annotate(candidate, "COMPLETE E7 SIGNAL MESA")
    p.town_render.combine_ab(baseline, candidate, OUT / "mesa-e7-wide-across-plaza-ab.png")
    p.crop_key_features(candidate, OUT / "mesa-e7-wide-key-feature-crop.png")
    render_turntables()

    metrics = p.comparison_metrics(baseline, candidate)
    contract = {
        "baseSha": BASE_SHA,
        "target": (
            "The complete Mesa must announce E7 at gameplay distance through a broadcast skyline, "
            "public program library, drone coop, signal refinery, Exchange, relay tower, and six "
            "named E6 carry/upgrade verdicts."
        ),
        "freshReferenceRule": "current-era boards rerendered after fetch on this exact base; no prior PNG input",
        "dependencies": {
            "mesaAndE6": "origin/sol/mesa-town-plate + origin/sol/mesa-town-e6-pilot/wide",
            "e7Pilot": {"branchTip": E7_PILOT_TIP, "assets": E7_PILOT_ASSETS},
        },
        "placements": {
            "playbookLibrary": [-14.2, -6.4, 0.12],
            "droneCoop": [14.2, -6.0, -0.10],
            "signalRefinery": [0.0, 16.2, math.pi],
            "acceptedPilot": {"exchange": [-7.55, 9.40, 0.06], "relayTower": [7.55, 9.15, -0.08]},
        },
        "comparisonMetrics": metrics,
        "visualReview": {
            "required": "locked complete E6/E7 A/B, feature crop, six four-angle audits, three inheritance A/Bs",
            "independentSubagent": "not run: this session explicitly forbids delegation; limitation recorded",
        },
    }
    (OUT / "visual-evidence-contract.json").write_text(json.dumps(contract, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
