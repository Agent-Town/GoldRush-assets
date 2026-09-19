from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import math
import subprocess
import sys

sys.dont_write_bytecode = True

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
GLB = HERE / "land-yacht.glb"
REFERENCE = ROOT / "assets/raw/boss-land-yacht.png"
DAMAGE_REFERENCE = ROOT / "assets/raw/boss-land-yacht-damage.png"
TERRAIN = ROOT / "assets/pilots/map-rebuild-spike/dust-flats-terrain.glb"
OUT = HERE / "renders"
COMPONENTS = {
    "wheels": "Damage_BeachedWheels",
    "crane": "Damage_SlackCrane",
    "wheelhouse": "Damage_CrackedWheelhouse",
}
BASE_SHA = "de21f043a8c3b4c69950afbca0c7a612c6826e88"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


shared = load("land_yacht_shared_renderer", ROOT / "assets/pilots/dredge-queen-3d/render_dredge_queen.py")
shared.GLB = GLB
shared.REFERENCE = REFERENCE
shared.DAMAGE_REFERENCE = DAMAGE_REFERENCE
shared.TERRAIN = TERRAIN
shared.OUT = OUT
shared.COMPONENTS = COMPONENTS


def warm_scene(resolution: tuple[int, int]):
    camera = shared.setup_scene(resolution)
    background = bpy.context.scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.095, 0.045, 0.018, 1)
    background.inputs["Strength"].default_value = 0.42
    lights = [obj for obj in bpy.context.scene.objects if obj.type == "LIGHT"]
    if lights:
        lights[0].data.color = (1.0, 0.55, 0.23)
        lights[0].data.energy = 2350
    return camera


def turntable() -> None:
    shared.reset_scene()
    shared.import_dredge_queen()
    ground = shared.material("Dust review ground", (0.31, 0.12, 0.035, 1), 0.94)
    shared.add_box("Dust review ground", (18, 18, 0.10), (0, 0, -0.08), ground)
    camera = warm_scene((640, 640))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 11.5
    target = Vector((0, 0, 2.60))
    paths = []
    for label, location in (
        ("front-port", Vector((-12, -12, 8.2))), ("front-starboard", Vector((-12, 12, 8.2))),
        ("rear-port", Vector((12, -12, 8.2))), ("rear-starboard", Vector((12, 12, 8.2))),
    ):
        shared.aim(camera, location, target)
        path = OUT / f"turntable-{label}.png"
        shared.render(path)
        paths.append(path)
    shared.save_grid(paths, OUT / "land-yacht-turntable.png", 2, 2)
    for path in paths:
        path.unlink()


def add_dust_flats() -> None:
    bpy.ops.import_scene.gltf(filepath=str(TERRAIN))
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and obj.name not in COMPONENTS:
            obj.name = f"Context:{obj.name}"
    dust = shared.material("Evidence dust", (0.40, 0.19, 0.065, 1), 0.94)
    for index, at in enumerate(((-5.2, -2.2, 0.35), (-4.4, 1.8, 0.30), (4.1, -1.6, 0.28))):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.46 + index * 0.08, location=at)
        bpy.context.object.name = f"Evidence:DustPuff:{index}"
        bpy.context.object.scale = (1.8, 1.0, 0.55)
        bpy.context.object.data.materials.append(dust)


def on_tile() -> None:
    shared.reset_scene()
    shared.import_dredge_queen()
    add_dust_flats()
    camera = warm_scene((1280, 800))
    camera.data.type = "PERSP"
    camera.data.angle = math.radians(42)
    # Exact production run rig mapped from Three.js (x/y-up/z) to Blender
    # (x/y/z-up): Balance.camera.offset plus CameraRig's down-screen target.
    shared.aim(camera, Vector((0.0, 26.2, 18.3)), Vector((0.0, -3.35, 0.45)))
    path = OUT / "land-yacht-dust-flats-run-camera.png"
    shared.render(path)
    shared.save_reference_ab(REFERENCE, path, OUT / "land-yacht-reference-ab.png")


def damage_states() -> None:
    shared.reset_scene()
    objects = shared.import_dredge_queen()
    ground = shared.material("Damage dust", (0.31, 0.12, 0.035, 1), 0.94)
    shared.add_box("Damage dust", (18, 18, 0.10), (0, 0, -0.08), ground)
    camera = warm_scene((640, 520))
    camera.data.type = "PERSP"
    camera.data.angle = math.radians(48)
    views = {
        "wheels": (Vector((7.2, -12.0, 6.8)), Vector((0.0, -0.5, 1.0))),
        "crane": (Vector((-11.8, -9.0, 8.0)), Vector((-2.7, 0.0, 3.0))),
        "wheelhouse": (Vector((10.6, 9.4, 8.2)), Vector((1.3, 0.0, 3.7))),
    }
    paths = []
    for component, morph in COMPONENTS.items():
        shared.set_all_morphs(objects, 0.0)
        objects[component].data.shape_keys.key_blocks[morph].value = 1.0
        location, target = views[component]
        shared.aim(camera, location, target)
        path = OUT / f"damage-{component}.png"
        shared.render(path)
        paths.append(path)
    blank = OUT / "damage-blank.png"
    shared.set_all_morphs(objects, 0.0)
    shared.aim(camera, Vector((-11.8, 9.0, 8.0)), Vector((0, 0, 2.6)))
    shared.render(blank)
    shared.save_grid([*paths, blank], OUT / "land-yacht-damage-states.png", 2, 2)
    for path in [*paths, blank]:
        path.unlink()

    shared.aim(camera, Vector((-11.2, -10.6, 8.6)), Vector((-0.4, 0, 2.4)))
    shared.set_all_morphs(objects, 0.0)
    intact = OUT / "land-yacht-intact.png"
    shared.render(intact)
    shared.set_all_morphs(objects, 1.0)
    wreck = OUT / "land-yacht-wreck.png"
    shared.render(wreck)
    shared.save_grid([intact, wreck], OUT / "land-yacht-intact-wreck.png", 1, 2)
    shared.save_reference_ab(DAMAGE_REFERENCE, wreck, OUT / "land-yacht-damage-reference-ab.png")
    metrics = shared.damage_metrics(intact, wreck)
    metrics["target"] = "beached wheels, slack grab crane, and cracked wheelhouse remain one readable land-yacht wreck"
    (OUT / "land-yacht-damage-metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")


def annotate(path: Path, label: str) -> None:
    temporary = path.with_name(f".{path.name}")
    subprocess.run([
        "magick", str(path), "-font", "/System/Library/Fonts/Helvetica.ttc", "-gravity", "north",
        "-fill", "#f7df9d", "-undercolor", "#17120dcc", "-pointsize", "22",
        "-annotate", "+0+8", f"{label} | base {BASE_SHA}", str(temporary),
    ], check=True)
    temporary.replace(path)


def finish_evidence() -> None:
    labeled = {
        "land-yacht-turntable.png": "LAND-YACHT | FOUR-ANGLE COMPONENT AUDIT",
        "land-yacht-reference-ab.png": "CURRENT INTACT PLATE / PRODUCTION GLB",
        "land-yacht-damage-reference-ab.png": "CURRENT DAMAGE PLATE / FULL WRECK MORPHS",
        "land-yacht-intact-wreck.png": "INTACT / ACT-3 BEACHED WRECK",
        "land-yacht-damage-states.png": "WHEELS / CRANE / WHEELHOUSE DAMAGE ZONES",
        "land-yacht-dust-flats-run-camera.png": "DUST FLATS RUN CAMERA",
    }
    for filename, label in labeled.items():
        annotate(OUT / filename, label)
    sources = [REFERENCE, DAMAGE_REFERENCE, ROOT / "assets/raw/plate-e4-boss-land-yacht.png"]
    contract = {
        "baseSha": BASE_SHA,
        "rule": "fresh direct render from current source plates and production GLB; no prior render is an input",
        "sourceSha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
        "productionGlb": str(GLB.relative_to(ROOT)),
        "runtimeIds": list(COMPONENTS),
        "runCamera": {
            "fovDegrees": 42,
            "offsetThreeJs": [0.0, 26.2, 18.3],
            "lookTargetThreeJs": [0.0, 0.45, -3.35],
        },
        "renders": [str((OUT / filename).relative_to(ROOT)) for filename in labeled],
    }
    (OUT / "land-yacht-reference-contract.json").write_text(json.dumps(contract, indent=2) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    turntable()
    on_tile()
    damage_states()
    finish_evidence()
    print(f"rendered {OUT}")


if __name__ == "__main__":
    main()
