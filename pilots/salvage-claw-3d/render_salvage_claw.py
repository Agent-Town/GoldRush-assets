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
GLB = HERE / "salvage-claw.glb"
REFERENCE = ROOT / "assets/raw/boss-salvage-claw.png"
LANDING_REFERENCE = ROOT / "assets/raw/boss-salvage-claw-damage.png"
TERRAIN = ROOT / "assets/pilots/map-rebuild-spike/mare-claim-terrain.glb"
OUT = HERE / "renders"
COMPONENTS = {
    "winch": "Landing_SprungWinch",
    "anchor_feet": "Landing_SettledAnchorFeet",
    "crown": "Landing_DarkCrown",
}
RUN_CAMERA_OFFSET = Vector((0.0, -18.3, 26.2))


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


shared = load("salvage_claw_shared_render", ROOT / "assets/pilots/dredge-queen-3d/render_dredge_queen.py")


def import_model() -> dict[str, bpy.types.Object]:
    bpy.ops.import_scene.gltf(filepath=str(GLB))
    objects = {obj.name: obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name in COMPONENTS}
    assert set(objects) == set(COMPONENTS), objects.keys()
    return objects


def set_state(objects: dict[str, bpy.types.Object], enabled: set[str]) -> None:
    for name, obj in objects.items():
        if not obj.data.shape_keys:
            continue
        obj.data.shape_keys.key_blocks[COMPONENTS[name]].value = 1.0 if name in enabled else 0.0


def lunar_review_ground() -> None:
    regolith = shared.material("Lunar review regolith", (0.24, 0.235, 0.20, 1), 0.94)
    shared.add_box("Lunar review ground", (16, 16, 0.12), (0, 0, -0.08), regolith)


def configure_camera(resolution: tuple[int, int]) -> bpy.types.Object:
    camera = shared.setup_scene(resolution)
    world = bpy.context.scene.world
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.035, 0.045, 0.043, 1)
    background.inputs["Strength"].default_value = 0.38
    return camera


def stamp(path: Path, title: str, base_sha: str) -> None:
    subprocess.run([
        "magick", str(path), "-gravity", "NorthWest", "-font", "/System/Library/Fonts/SFNS.ttf", "-pointsize", "22",
        "-fill", "#f4dfaa", "-undercolor", "#102126cc",
        "-annotate", "+16+16", f"{title} | BASE {base_sha[:12]}", str(path),
    ], check=True)


def save_grid_image(paths: list[Path], output: Path, rows: int, columns: int) -> None:
    assert len(paths) == rows * columns
    row_paths: list[Path] = []
    for row in range(rows):
        row_path = Path(f"/tmp/{output.stem}-row-{row}.png")
        subprocess.run([
            "magick", *[str(path) for path in paths[row * columns:(row + 1) * columns]], "+append", str(row_path),
        ], check=True)
        row_paths.append(row_path)
    subprocess.run(["magick", *[str(path) for path in row_paths], "-append", str(output)], check=True)
    for row_path in row_paths:
        row_path.unlink(missing_ok=True)


def render_turntable(base_sha: str) -> Path:
    shared.reset_scene()
    import_model()
    lunar_review_ground()
    camera = configure_camera((620, 620))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 14.0
    target = Vector((0, 0, 3.0))
    views = (
        ("front-port", Vector((-10.0, -10.0, 8.3))),
        ("front-starboard", Vector((10.0, -10.0, 8.3))),
        ("rear-port", Vector((-10.0, 10.0, 8.3))),
        ("rear-starboard", Vector((10.0, 10.0, 8.3))),
    )
    paths: list[Path] = []
    for label, location in views:
        shared.aim(camera, location, target)
        path = OUT / f"turntable-{label}.png"
        shared.render(path)
        paths.append(path)
    board = OUT / "salvage-claw-turntable.png"
    save_grid_image(paths, board, 2, 2)
    for path in paths:
        path.unlink()
    stamp(board, "SALVAGE CLAW 4-ANGLE WRAP", base_sha)
    return board


def render_reference_board(base_sha: str) -> Path:
    shared.reset_scene()
    objects = import_model()
    lunar_review_ground()
    camera = configure_camera((960, 540))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 13.8
    shared.aim(camera, Vector((0, -12.0, 6.4)), Vector((0, 0, 3.1)))
    intact = OUT / "model-intact-front.png"
    shared.render(intact)
    set_state(objects, set(COMPONENTS))
    landed = OUT / "model-landed-front.png"
    shared.render(landed)
    intact_ab = OUT / "reference-intact-ab.png"
    landed_ab = OUT / "reference-landed-ab.png"
    shared.save_reference_ab(REFERENCE, intact, intact_ab)
    shared.save_reference_ab(LANDING_REFERENCE, landed, landed_ab)
    board = OUT / "salvage-claw-reference-ab.png"
    save_grid_image([intact_ab, landed_ab], board, 2, 1)
    for path in (intact, landed, intact_ab, landed_ab):
        path.unlink()
    stamp(board, "PLATE / PRODUCTION | DESCENDING THEN LANDED", base_sha)
    return board


def render_state_board(base_sha: str) -> Path:
    paths: list[Path] = []
    for name in ("intact", "winch", "anchor_feet", "crown", "all"):
        shared.reset_scene()
        objects = import_model()
        lunar_review_ground()
        camera = configure_camera((620, 520))
        camera.data.type = "PERSP"
        camera.data.angle = math.radians(48)
        shared.aim(camera, Vector((0, -17.2, 11.8)), Vector((0, 0, 3.8)))
        enabled = set() if name == "intact" else set(COMPONENTS) if name == "all" else {name}
        set_state(objects, enabled)
        path = OUT / f"state-{name}.png"
        shared.render(path)
        stamp(path, name.upper().replace("_", " "), base_sha)
        paths.append(path)
    blank = shared.load_pixels(paths[0])
    blank[:, :, :3] = (0.035, 0.045, 0.043)
    blank_path = OUT / "state-blank.png"
    shared.save_pixels(blank, blank_path)
    board = OUT / "salvage-claw-landing-states.png"
    save_grid_image([*paths, blank_path], board, 2, 3)
    for path in (*paths, blank_path):
        path.unlink()
    stamp(board, "NAMED LANDING MORPHS", base_sha)
    return board


def render_run_camera(base_sha: str) -> Path:
    shared.reset_scene()
    objects = import_model()
    bpy.ops.import_scene.gltf(filepath=str(TERRAIN))
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and obj.name not in COMPONENTS:
            obj.name = f"Context:{obj.name}"
    camera = configure_camera((960, 600))
    camera.data.type = "PERSP"
    camera.data.angle = math.radians(42)
    shared.aim(camera, RUN_CAMERA_OFFSET, Vector((0, 0, 2.7)))
    intact = OUT / "run-camera-intact.png"
    shared.render(intact)
    set_state(objects, set(COMPONENTS))
    landed = OUT / "run-camera-landed.png"
    shared.render(landed)
    board = OUT / "salvage-claw-mare-run-camera.png"
    save_grid_image([intact, landed], board, 1, 2)
    for path in (intact, landed):
        path.unlink()
    stamp(board, "MARE CLAIM RUN CAMERA | DESCENDING / LANDED", base_sha)
    return board


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base_sha = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip()
    boards = [
        render_turntable(base_sha),
        render_reference_board(base_sha),
        render_state_board(base_sha),
        render_run_camera(base_sha),
    ]
    evidence = {
        "baseSha": base_sha,
        "sourcePlates": {
            str(REFERENCE.relative_to(ROOT)): hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
            str(LANDING_REFERENCE.relative_to(ROOT)): hashlib.sha256(LANDING_REFERENCE.read_bytes()).hexdigest(),
        },
        "model": str(GLB.relative_to(ROOT)),
        "terrain": str(TERRAIN.relative_to(ROOT)),
        "camera": {"fovDegrees": 42, "offsetBlenderZUp": list(RUN_CAMERA_OFFSET)},
        "boards": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in boards},
    }
    (OUT / "salvage-claw-reference-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
