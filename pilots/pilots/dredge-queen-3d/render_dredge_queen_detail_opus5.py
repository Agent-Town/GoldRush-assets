"""Evidence boards for the Opus-5 Dredge Queen detail entry.

Imports the shipped render module READ-ONLY as a library (no global patching that
could write to shipped paths) and renders into `renders-detail-opus5/`.

Boards: 4-angle turntable (the duel deliverable), plate A/B, damage states, and a
same-camera shipped-vs-detail comparison.
"""

from pathlib import Path
import importlib.util
import json
import hashlib
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
GLB = HERE / "dredge-queen-detail-opus5.glb"
SHIPPED_GLB = HERE / "dredge-queen.glb"
REFERENCE = ROOT / "assets/raw/boss-dredge-queen.png"
DAMAGE_REFERENCE = ROOT / "assets/raw/boss-dredge-queen-damage.png"
OUT = HERE / "renders-detail-opus5"

COMPONENTS = {
    "claw": "Damage_SlackClaw",
    "paddle_port": "Damage_BrokenPortPaddle",
    "paddle_starboard": "Damage_BrokenStarboardPaddle",
    "hold": "Damage_CrackedLootHold",
}


def load_shared():
    path = HERE / "render_dredge_queen.py"
    spec = importlib.util.spec_from_file_location("dq_detail_render_shared", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["dq_detail_render_shared"] = module
    spec.loader.exec_module(module)
    return module


shared = load_shared()


def import_glb(path: Path) -> dict[str, bpy.types.Object]:
    bpy.ops.import_scene.gltf(filepath=str(path))
    return {obj.name: obj for obj in bpy.context.scene.objects if obj.type == "MESH"}


def configure(resolution: tuple[int, int]) -> bpy.types.Object:
    camera = shared.setup_scene(resolution)
    scene = bpy.context.scene
    # Blender 5.1 renamed the EEVEE identifier; fall back if the shipped literal is stale.
    try:
        scene.render.engine = "BLENDER_EEVEE"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    return camera


def review_ground() -> None:
    water = shared.material("Detail review water", (0.031, 0.096, 0.101, 1), 0.62)
    shared.add_box("Detail review water plane", (26, 26, 0.12), (0, 0, -0.07), water)


def set_morphs(objects: dict[str, bpy.types.Object], enabled: set[str]) -> None:
    for name, obj in objects.items():
        if not obj.data.shape_keys:
            continue
        obj.data.shape_keys.key_blocks[COMPONENTS[name]].value = 1.0 if name in enabled else 0.0


TURNTABLE_VIEWS = (
    ("bow-port", Vector((-9.6, -9.6, 7.4))),
    ("bow-starboard", Vector((9.6, -9.6, 7.4))),
    ("stern-port", Vector((-9.6, 9.6, 7.4))),
    ("stern-starboard", Vector((9.6, 9.6, 7.4))),
)


def render_turntable(glb: Path, output: Path, tile: int = 660, ortho: float = 10.4) -> Path:
    shared.reset_scene()
    import_glb(glb)
    review_ground()
    camera = configure((tile, tile))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho
    target = Vector((0, 0, 2.15))
    paths: list[Path] = []
    for label, location in TURNTABLE_VIEWS:
        shared.aim(camera, location, target)
        path = OUT / f"tmp-{output.stem}-{label}.png"
        shared.render(path)
        paths.append(path)
    shared.save_grid(paths, output, 2, 2)
    for path in paths:
        path.unlink(missing_ok=True)
    return output


def render_single(glb: Path, output: Path, morphs: set[str], resolution=(940, 560), ortho: float = 10.2) -> Path:
    shared.reset_scene()
    objects = import_glb(glb)
    review_ground()
    camera = configure(resolution)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho
    shared.aim(camera, Vector((-8.4, -10.6, 5.6)), Vector((0, 0, 2.2)))
    set_morphs(objects, morphs)
    shared.render(output)
    return output


def render_damage_states() -> Path:
    tiles: list[Path] = []
    states = (
        ("intact", set()),
        ("slack-claw", {"claw"}),
        ("broken-port-paddle", {"paddle_port"}),
        ("broken-starboard-paddle", {"paddle_starboard"}),
        ("cracked-loot-hold", {"hold"}),
        ("act3-all", set(COMPONENTS)),
    )
    for label, morphs in states:
        tiles.append(render_single(GLB, OUT / f"tmp-state-{label}.png", morphs, (640, 420)))
    board = OUT / "dredge-queen-detail-opus5-damage-states.png"
    shared.save_grid(tiles, board, 3, 2)
    for tile in tiles:
        tile.unlink(missing_ok=True)
    return board


def render_versus() -> Path:
    """The duel's own question: same camera, shipped body beside the detail body."""
    left = render_single(SHIPPED_GLB, OUT / "tmp-versus-shipped.png", set(), (900, 620))
    right = render_single(GLB, OUT / "tmp-versus-detail.png", set(), (900, 620))
    board = OUT / "dredge-queen-detail-opus5-vs-shipped.png"
    shared.save_grid([left, right], board, 1, 2)
    for tile in (left, right):
        tile.unlink(missing_ok=True)
    return board


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    boards = [
        render_turntable(GLB, OUT / "dredge-queen-detail-opus5-turntable.png"),
        render_damage_states(),
        render_versus(),
    ]

    intact = render_single(GLB, OUT / "tmp-ab-intact.png", set(), (960, 540), 6.9)
    ab = OUT / "dredge-queen-detail-opus5-reference-ab.png"
    shared.save_reference_ab(REFERENCE, intact, ab)
    intact.unlink(missing_ok=True)
    boards.append(ab)

    act3 = render_single(GLB, OUT / "tmp-ab-act3.png", set(COMPONENTS), (960, 540), 6.9)
    ab3 = OUT / "dredge-queen-detail-opus5-act3-reference-ab.png"
    shared.save_reference_ab(DAMAGE_REFERENCE, act3, ab3)
    act3.unlink(missing_ok=True)
    boards.append(ab3)

    print(json.dumps({
        "boards": {
            str(board.relative_to(ROOT)): hashlib.sha256(board.read_bytes()).hexdigest()
            for board in boards
        }
    }, indent=2))


if __name__ == "__main__":
    main()
