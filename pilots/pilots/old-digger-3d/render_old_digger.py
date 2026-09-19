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
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
GLB = HERE / "old-digger.glb"
REFERENCE = ROOT / "assets/raw/boss-old-digger.png"
GENTLE_REFERENCE = ROOT / "assets/raw/boss-old-digger-gentle.png"
TERRAIN = ROOT / "assets/pilots/basin-rim-3d/basin-rim-plate.glb"
OUT = HERE / "renders"
COMPONENTS = {
    "bucket_wheel_port": "Redemption_GentleBuckets",
    "bucket_wheel_starboard": "Redemption_GentleBuckets",
    "gantry": "Redemption_SafeGantry",
    "tape_deck": "Redemption_TealTapeDeck",
}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


shared = load("old_digger_shared_render", ROOT / "assets/pilots/dredge-queen-3d/render_dredge_queen.py")


def import_model() -> dict[str, bpy.types.Object]:
    bpy.ops.import_scene.gltf(filepath=str(GLB))
    objects = {obj.name: obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name in COMPONENTS}
    assert set(objects) == set(COMPONENTS), objects.keys()
    return objects


def set_state(objects: dict[str, bpy.types.Object], enabled: set[str]) -> None:
    for name, obj in objects.items():
        if obj.data.shape_keys:
            obj.data.shape_keys.key_blocks[COMPONENTS[name]].value = 1.0 if name in enabled else 0.0


def setup_scene(resolution: tuple[int, int]) -> bpy.types.Object:
    camera = shared.setup_scene(resolution)
    background = bpy.context.scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.055, 0.022, 0.010, 1)
    background.inputs["Strength"].default_value = 0.34
    return camera


def red_ground() -> None:
    ground = shared.material("Basin review ground", (0.28, 0.075, 0.025, 1), 0.96)
    shared.add_box("Basin review ground", (18, 14, 0.12), (0, 0, -0.08), ground)


def stamp(path: Path, title: str, base_sha: str) -> None:
    subprocess.run([
        "magick", str(path), "-gravity", "NorthWest", "-font", "/System/Library/Fonts/SFNS.ttf", "-pointsize", "22",
        "-fill", "#f4dfaa", "-undercolor", "#28150dcc", "-annotate", "+16+16",
        f"{title} | BASE {base_sha[:12]}", str(path),
    ], check=True)


def save_grid(paths: list[Path], output: Path, rows: int, columns: int) -> None:
    assert len(paths) == rows * columns
    row_paths: list[Path] = []
    for row in range(rows):
        row_path = Path(f"/tmp/{output.stem}-row-{row}.png")
        subprocess.run(["magick", *[str(path) for path in paths[row * columns:(row + 1) * columns]], "+append", str(row_path)], check=True)
        row_paths.append(row_path)
    subprocess.run(["magick", *[str(path) for path in row_paths], "-append", str(output)], check=True)
    for row_path in row_paths:
        row_path.unlink(missing_ok=True)


def render_turntable(base_sha: str) -> Path:
    shared.reset_scene()
    import_model()
    red_ground()
    camera = setup_scene((680, 560))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 14.8
    target = Vector((0, 0, 2.8))
    views = (
        ("front-port", Vector((-13.0, -13.0, 9.0))),
        ("front-starboard", Vector((13.0, -13.0, 9.0))),
        ("rear-port", Vector((-13.0, 13.0, 9.0))),
        ("rear-starboard", Vector((13.0, 13.0, 9.0))),
    )
    paths: list[Path] = []
    for label, location in views:
        shared.aim(camera, location, target)
        path = OUT / f"turntable-{label}.png"
        shared.render(path)
        paths.append(path)
    board = OUT / "old-digger-turntable.png"
    save_grid(paths, board, 2, 2)
    for path in paths:
        path.unlink()
    stamp(board, "OLD DIGGER 4-ANGLE WRAP", base_sha)
    return board


def render_reference_board(base_sha: str) -> Path:
    shared.reset_scene()
    objects = import_model()
    red_ground()
    camera = setup_scene((960, 540))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 14.2
    shared.aim(camera, Vector((0, -15.0, 6.2)), Vector((0, 0, 2.7)))
    working = OUT / "model-working-side.png"
    shared.render(working)
    set_state(objects, set(COMPONENTS))
    gentle = OUT / "model-gentle-side.png"
    shared.render(gentle)
    working_ab = OUT / "reference-working-ab.png"
    gentle_ab = OUT / "reference-gentle-ab.png"
    shared.save_reference_ab(REFERENCE, working, working_ab)
    shared.save_reference_ab(GENTLE_REFERENCE, gentle, gentle_ab)
    board = OUT / "old-digger-reference-ab.png"
    save_grid([working_ab, gentle_ab], board, 2, 1)
    for path in (working, gentle, working_ab, gentle_ab):
        path.unlink()
    stamp(board, "PLATE / PRODUCTION | WORKING THEN GENTLE", base_sha)
    return board


def render_state_board(base_sha: str) -> Path:
    paths: list[Path] = []
    for name in ("working", "bucket_wheels", "gantry", "tape_deck", "all", "blank"):
        if name == "blank":
            subprocess.run(["magick", "-size", "680x520", "xc:#120b08", str(OUT / "state-blank.png")], check=True)
            paths.append(OUT / "state-blank.png")
            continue
        shared.reset_scene()
        objects = import_model()
        red_ground()
        camera = setup_scene((680, 520))
        camera.data.type = "PERSP"
        camera.data.angle = math.radians(47)
        shared.aim(camera, Vector((0, -17.5, 9.2)), Vector((0, 0, 2.6)))
        enabled = set() if name == "working" else set(COMPONENTS) if name == "all" else {name}
        if name == "bucket_wheels":
            enabled = {"bucket_wheel_port", "bucket_wheel_starboard"}
        set_state(objects, enabled)
        path = OUT / f"state-{name}.png"
        shared.render(path)
        stamp(path, name.upper().replace("_", " "), base_sha)
        paths.append(path)
    board = OUT / "old-digger-redemption-states.png"
    save_grid(paths, board, 2, 3)
    for path in paths:
        path.unlink()
    return board


def render_run_camera(base_sha: str) -> Path:
    shared.reset_scene()
    objects = import_model()
    bpy.context.view_layer.update()
    # Runtime can yaw the body; face the tape-deck heart into the exact camera rig.
    for obj in objects.values():
        obj.matrix_world = Matrix.Rotation(math.pi, 4, 'Z') @ obj.matrix_world
    bpy.ops.import_scene.gltf(filepath=str(TERRAIN))
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and obj.name not in COMPONENTS:
            obj.name = f"Context:{obj.name}"
    camera = setup_scene((960, 600))
    bpy.ops.object.light_add(type="AREA", location=(0, 12.0, 10.0))
    front_fill = bpy.context.object
    front_fill.data.energy = 1250
    front_fill.data.color = (1.0, 0.56, 0.24)
    front_fill.data.shape = "DISK"
    front_fill.data.size = 8.0
    camera.data.type = "PERSP"
    camera.data.angle = math.radians(42)
    shared.aim(camera, Vector((0, 26.2, 18.3)), Vector((0, -3.35, 0.45)))
    working = OUT / "run-camera-working.png"
    shared.render(working)
    set_state(objects, set(COMPONENTS))
    gentle = OUT / "run-camera-gentle.png"
    shared.render(gentle)
    board = OUT / "old-digger-basin-run-camera.png"
    save_grid([working, gentle], board, 1, 2)
    for path in (working, gentle):
        path.unlink()
    stamp(board, "BASIN RIM RUN CAMERA | WORKING / GENTLE", base_sha)
    return board


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base_sha = subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True).strip()
    boards = [render_turntable(base_sha), render_reference_board(base_sha), render_state_board(base_sha), render_run_camera(base_sha)]
    evidence = {
        "baseSha": base_sha,
        "sourcePlates": {
            str(REFERENCE.relative_to(ROOT)): hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
            str(GENTLE_REFERENCE.relative_to(ROOT)): hashlib.sha256(GENTLE_REFERENCE.read_bytes()).hexdigest(),
        },
        "model": str(GLB.relative_to(ROOT)),
        "terrain": str(TERRAIN.relative_to(ROOT)),
        "camera": {"fovDegrees": 42, "offsetBlenderZUp": [0.0, 26.2, 18.3], "target": [0.0, -3.35, 0.45], "bossYawDegrees": 180},
        "stateLaw": "working to gentle-redemption; no damage state",
        "boards": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in boards},
    }
    (OUT / "old-digger-reference-contract.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
