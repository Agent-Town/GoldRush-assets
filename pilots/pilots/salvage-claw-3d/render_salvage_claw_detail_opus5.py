"""Evidence boards for the Opus-5 Salvage King's Claw detail entry.

Imports the shipped Dredge Queen render module READ-ONLY as the shared rig and
renders into `renders-detail-opus5/`. Lunar review ground, E8 cold world.
"""

from pathlib import Path
import importlib.util
import hashlib
import json
import sys

import bpy
from mathutils import Vector

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
GLB = HERE / "salvage-claw-detail-opus5.glb"
SHIPPED_GLB = HERE / "salvage-claw.glb"
REFERENCE = ROOT / "assets/raw/boss-salvage-claw.png"
LANDING_REFERENCE = ROOT / "assets/raw/boss-salvage-claw-damage.png"
OUT = HERE / "renders-detail-opus5"

COMPONENTS = {
    "winch": "Landing_SprungWinch",
    "anchor_feet": "Landing_SettledAnchorFeet",
    "crown": "Landing_DarkCrown",
}


def load_shared():
    path = ROOT / "assets/pilots/dredge-queen-3d/render_dredge_queen.py"
    spec = importlib.util.spec_from_file_location("sc_detail_render_shared", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["sc_detail_render_shared"] = module
    spec.loader.exec_module(module)
    return module


shared = load_shared()


def import_glb(path: Path) -> dict[str, bpy.types.Object]:
    bpy.ops.import_scene.gltf(filepath=str(path))
    return {obj.name: obj for obj in bpy.context.scene.objects if obj.type == "MESH"}


def configure(resolution: tuple[int, int]) -> bpy.types.Object:
    camera = shared.setup_scene(resolution)
    world = bpy.context.scene.world
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.035, 0.045, 0.043, 1)
    background.inputs["Strength"].default_value = 0.38
    return camera


def lunar_ground() -> None:
    regolith = shared.material("Lunar review regolith", (0.24, 0.235, 0.20, 1), 0.94)
    shared.add_box("Lunar review ground", (30, 30, 0.12), (0, 0, -0.08), regolith)


def set_morphs(objects: dict[str, bpy.types.Object], enabled: set[str]) -> None:
    for name, obj in objects.items():
        if not obj.data.shape_keys:
            continue
        obj.data.shape_keys.key_blocks[COMPONENTS[name]].value = 1.0 if name in enabled else 0.0


VIEWS = (
    ("front-port", Vector((-11.5, -11.5, 9.4))),
    ("front-starboard", Vector((11.5, -11.5, 9.4))),
    ("rear-port", Vector((-11.5, 11.5, 9.4))),
    ("rear-starboard", Vector((11.5, 11.5, 9.4))),
)


def render_turntable(glb: Path, output: Path, tile: int = 660, ortho: float = 14.6) -> Path:
    shared.reset_scene()
    import_glb(glb)
    lunar_ground()
    camera = configure((tile, tile))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho
    target = Vector((0, 0, 4.4))
    paths: list[Path] = []
    for label, location in VIEWS:
        shared.aim(camera, location, target)
        path = OUT / f"tmp-{output.stem}-{label}.png"
        shared.render(path)
        paths.append(path)
    shared.save_grid(paths, output, 2, 2)
    for path in paths:
        path.unlink(missing_ok=True)
    return output


def render_single(glb: Path, output: Path, morphs: set[str], resolution=(940, 560), ortho: float = 13.8) -> Path:
    shared.reset_scene()
    objects = import_glb(glb)
    lunar_ground()
    camera = configure(resolution)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho
    shared.aim(camera, Vector((0, -13.0, 6.6)), Vector((0, 0, 4.6)))
    set_morphs(objects, morphs)
    shared.render(output)
    return output


def render_landing_states() -> Path:
    tiles = []
    states = (
        ("descending", set()),
        ("sprung-winch", {"winch"}),
        ("settled-feet", {"anchor_feet"}),
        ("dark-crown", {"crown"}),
        ("landed-all", set(COMPONENTS)),
        ("landed-all-repeat", set(COMPONENTS)),
    )
    for label, morphs in states:
        tiles.append(render_single(GLB, OUT / f"tmp-state-{label}.png", morphs, (640, 430), 14.4))
    board = OUT / "salvage-claw-detail-opus5-landing-states.png"
    shared.save_grid(tiles, board, 3, 2)
    for tile in tiles:
        tile.unlink(missing_ok=True)
    return board


def render_versus() -> Path:
    left = render_single(SHIPPED_GLB, OUT / "tmp-versus-shipped.png", set(), (900, 620), 14.2)
    right = render_single(GLB, OUT / "tmp-versus-detail.png", set(), (900, 620), 14.2)
    board = OUT / "salvage-claw-detail-opus5-vs-shipped.png"
    shared.save_grid([left, right], board, 1, 2)
    for tile in (left, right):
        tile.unlink(missing_ok=True)
    return board


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    boards = [
        render_turntable(GLB, OUT / "salvage-claw-detail-opus5-turntable.png"),
        render_landing_states(),
        render_versus(),
    ]

    intact = render_single(GLB, OUT / "tmp-ab-intact.png", set(), (960, 540), 11.2)
    ab = OUT / "salvage-claw-detail-opus5-reference-ab.png"
    shared.save_reference_ab(REFERENCE, intact, ab)
    intact.unlink(missing_ok=True)
    boards.append(ab)

    landed = render_single(GLB, OUT / "tmp-ab-landed.png", set(COMPONENTS), (960, 540), 11.2)
    ab2 = OUT / "salvage-claw-detail-opus5-landed-reference-ab.png"
    shared.save_reference_ab(LANDING_REFERENCE, landed, ab2)
    landed.unlink(missing_ok=True)
    boards.append(ab2)

    print(json.dumps({
        "boards": {
            str(board.relative_to(ROOT)): hashlib.sha256(board.read_bytes()).hexdigest()
            for board in boards
        }
    }, indent=2))


if __name__ == "__main__":
    main()
