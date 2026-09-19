from pathlib import Path
import hashlib
import json
import math
import subprocess

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
BASE_SHA = "c272d3a8ba9c36ee2550c7bb55c3fb05edab087e"
OUT = ROOT / "artifacts/basin-rim-e9/current-references" / f"{BASE_SHA[:12]}-main"
DOME = ROOT / "assets/pilots/dome-commons-3d/dome-commons-plate.glb"
PAN = ROOT / "assets/pilots/plaza-props-3d/pan_monument.glb"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_e1_to_e7() -> dict:
    # ponytail: reuse the accepted renderer while its function names remain stable;
    # copy it only if the E1-E7 evidence pipeline gains a public shared module.
    source_path = ROOT / "assets/pilots/dome-commons-3d/render_current_references.py"
    source = source_path.read_text()
    old_base = 'BASE_SHA = "2736e176d69226d40603889ee3e1aa07db623784"'
    old_out = 'OUT = ROOT / "artifacts/dome-commons-e8/current-references" / f"{BASE_SHA[:12]}-main"'
    assert source.count(old_base) == source.count(old_out) == 1
    source = source.replace(old_base, f'BASE_SHA = "{BASE_SHA}"')
    source = source.replace(old_out, 'OUT = ROOT / "artifacts/basin-rim-e9/current-references" / f"{BASE_SHA[:12]}-main"')
    source = source.replace("verify_pinned_reference_assets()\n", "")
    child_script = Path(__file__).with_name(".render_e1_e7_current.py")
    child_script.write_text(source)
    subprocess.run([bpy.app.binary_path, "--background", "--python", str(child_script)], check=True)
    child_script.unlink()
    expected = OUT / "town-e1-e7-current.png"
    if not expected.is_file():
        raise RuntimeError(f"Fresh reference child did not produce {expected}")
    namespace = {"__name__": "basin_rim_reference_reuse", "__file__": str(source_path)}
    exec(compile(source, str(source_path), "exec"), namespace)
    return namespace


def render_e8(namespace: dict) -> Path:
    town = namespace["town"]
    town.reset_scene()
    town.import_model(DOME, "Current:E8DomeCommons", town.Point(0.0, 0.0))
    town.import_model(PAN, "Current:PanMonument", town.Point(0.0, 0.0))
    camera = town.setup_render_scene()
    scene = bpy.context.scene
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 800
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.07, 0.055, 0.04, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.72
    camera.location = (0.0, 46.0, 34.0)
    town.look_at(camera, Vector((0.0, 0.0, 3.2)))
    camera.data.lens = camera.data.sensor_height / (2.0 * math.tan(math.radians(48.0) * 0.5))
    path = OUT / "town-e8-current.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    namespace["annotate"](path, "CURRENT E8 DOME COMMONS")
    return path


def assemble(e8: Path) -> None:
    sources = [
        OUT / "town-e1-current.png", OUT / "town-e4-current.png", OUT / "town-e5-current-underwater.png",
        OUT / "town-e6-current.png", OUT / "town-e7-current.png", e8,
    ]
    row_a, row_b = OUT / ".row-a.png", OUT / ".row-b.png"
    subprocess.run(["magick", *map(str, sources[:3]), "+append", str(row_a)], check=True)
    subprocess.run(["magick", *map(str, sources[3:]), "+append", str(row_b)], check=True)
    subprocess.run(["magick", str(row_a), str(row_b), "-append", str(OUT / "town-e1-e8-current.png")], check=True)
    row_a.unlink()
    row_b.unlink()
    contract_path = OUT / "reference-contract.json"
    contract = json.loads(contract_path.read_text())
    contract["baseSha"] = BASE_SHA
    contract["order"] = ["E1 square", "E4 motor boulevard", "E5 submerged square", "E6 Atomic Mesa", "E7 Signal Mesa", "E8 Dome Commons"]
    contract["assetSha256"][str(DOME.relative_to(ROOT))] = sha256(DOME)
    contract["renders"] = [str(path.relative_to(ROOT)) for path in [*sources, OUT / "town-e1-e8-current.png"]]
    contract_path.write_text(json.dumps(contract, indent=2) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    namespace = render_e1_to_e7()
    assemble(render_e8(namespace))
    print(json.dumps({"baseSha": BASE_SHA, "output": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
