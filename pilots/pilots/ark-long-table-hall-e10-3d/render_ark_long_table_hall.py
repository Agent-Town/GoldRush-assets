from __future__ import annotations

from pathlib import Path
import json
import math
import subprocess
import sys

sys.dont_write_bytecode = True

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RENDERS = HERE / "renders"
ARTIFACTS = ROOT / "artifacts/ark-long-table-hall-e10"
GLB = HERE / "ark-long-table-hall-e10.glb"
SOURCE_TABLE = ROOT / "assets/raw/plate-e10-long-table.png"
SOURCE_SHRINE = ROOT / "assets/raw/plate-e10-pan-shrine.png"
BASE_SHA = "101c0d97e9527b26cc5c94fdafab5b4f77aa33c0"


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def evidence_material(name: str, color: tuple[float, float, float, float], emission=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = 0.82
    if emission:
        shader.inputs["Emission Color"].default_value = color
        shader.inputs["Emission Strength"].default_value = emission
    return material


def add_portrait_proxies() -> None:
    materials = (
        evidence_material("EvidenceOnly:PortraitInk", (0.09, 0.052, 0.032, 1.0)),
        evidence_material("EvidenceOnly:PortraitRust", (0.42, 0.20, 0.08, 1.0)),
        evidence_material("EvidenceOnly:PortraitTeal", (0.08, 0.27, 0.26, 1.0)),
        evidence_material("EvidenceOnly:PortraitGold", (0.54, 0.34, 0.13, 1.0)),
        evidence_material("EvidenceOnly:PortraitRed", (0.36, 0.10, 0.07, 1.0)),
    )
    family_sizes = (2, 2, 2, 3, 2, 3, 3, 2, 2, 2)
    for index in range(1, 11):
        anchor = bpy.data.objects.get(f"portrait_anchor_{index:02d}")
        if anchor is None:
            continue
        x, y, z = anchor.location
        count = family_sizes[index - 1]
        offsets = (-0.28, 0.28) if count == 2 else (-0.40, 0.0, 0.40)
        for person, offset in enumerate(offsets, 1):
            child = count == 3 and person == 2 and index in (4, 6, 7)
            head_z = z + (0.03 if child else 0.20)
            head_radius = 0.13 if child else (0.16 if count == 3 else 0.18)
            portrait_material = materials[(index + person) % len(materials)]
            bpy.ops.mesh.primitive_uv_sphere_add(
                segments=10, ring_count=5, radius=head_radius,
                location=(x + offset, y - 0.11 - person * 0.002, head_z),
            )
            head = bpy.context.object
            head.name = f"EvidenceOnly:Portrait:{index:02d}:{person}:head"
            head.scale = (0.82, 0.16, 1.0)
            head.data.materials.append(portrait_material)
            bpy.ops.mesh.primitive_uv_sphere_add(
                segments=10, ring_count=5, radius=0.26 if count == 3 else 0.30,
                location=(x + offset, y - 0.10, z - (0.25 if child else 0.28)),
            )
            shoulders = bpy.context.object
            shoulders.name = f"EvidenceOnly:Portrait:{index:02d}:{person}:shoulders"
            shoulders.scale = (1.05, 0.10, 0.52 if child else 0.62)
            shoulders.data.materials.append(portrait_material)


def setup(camera_at: tuple[float, float, float], target: tuple[float, float, float], lens=44.0) -> None:
    reset_scene()
    bpy.ops.import_scene.gltf(filepath=str(GLB), merge_vertices=False)
    add_portrait_proxies()
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    if scene.world is None:
        scene.world = bpy.data.worlds.new("EvidenceOnly:DeepInk")
    scene.world.color = (0.006, 0.009, 0.015)
    scene.view_settings.look = "AgX - Medium Low Contrast"
    scene.view_settings.exposure = 0.35

    bpy.ops.object.camera_add(location=camera_at)
    camera = bpy.context.object
    camera.name = "EvidenceOnly:Camera"
    camera.data.lens = lens
    camera.data.clip_end = 120.0
    look_at(camera, Vector(target))
    scene.camera = camera

    lights = (
        ("EvidenceOnly:WarmTable", (0.0, -3.5, 10.5), (0.0, 0.0, 1.2), 1350.0, 7.0, (1.0, 0.52, 0.24)),
        ("EvidenceOnly:TealFill", (-7.0, -1.0, 6.0), (-2.0, 2.0, 2.0), 900.0, 6.0, (0.18, 0.70, 0.70)),
        ("EvidenceOnly:PortraitWarmth", (0.0, 8.0, 8.4), (0.0, 9.8, 4.2), 1200.0, 7.0, (1.0, 0.62, 0.30)),
        ("EvidenceOnly:Shrine", (-6.0, 1.0, 6.2), (-6.1, 4.6, 1.4), 800.0, 4.0, (1.0, 0.72, 0.35)),
    )
    for name, at, aim, energy, size, color in lights:
        bpy.ops.object.light_add(type="AREA", location=at)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        look_at(light, Vector(aim))


def render(path: Path, camera_at, target, lens=44.0) -> None:
    setup(camera_at, target, lens)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def annotate(path: Path, label: str) -> None:
    temporary = path.with_name(f".{path.name}")
    subprocess.run([
        "magick", str(path), "-font", "/System/Library/Fonts/Helvetica.ttc",
        "-gravity", "north", "-fill", "#f7df9d", "-undercolor", "#10151ddd",
        "-pointsize", "22", "-annotate", "+0+8", f"{label} | base {BASE_SHA}", str(temporary),
    ], check=True)
    temporary.replace(path)


def source_panel(source: Path, output: Path, label: str) -> None:
    subprocess.run([
        "magick", str(source), "-resize", "1280x800", "-background", "#10151d",
        "-gravity", "center", "-extent", "1280x800", str(output),
    ], check=True)
    annotate(output, label)


def assemble() -> None:
    hero = RENDERS / "long-table-hall-hero.png"
    left = RENDERS / "long-table-hall-left.png"
    right = RENDERS / "long-table-hall-right.png"
    portraits = RENDERS / "long-table-hall-portraits.png"
    shrine = RENDERS / "long-table-hall-pan-shrine.png"
    tree = RENDERS / "long-table-hall-elder-tree.png"
    table_source = RENDERS / ".source-table.png"
    shrine_source = RENDERS / ".source-shrine.png"
    source_panel(SOURCE_TABLE, table_source, "SOURCE PLATE | LONG TABLE + TEN-GENERATION WALL")
    source_panel(SOURCE_SHRINE, shrine_source, "SOURCE PLATE | ORIGINAL E1 PAN SHRINE")

    table_ab = RENDERS / "long-table-source-vs-production-ab.png"
    shrine_ab = RENDERS / "pan-shrine-source-vs-production-ab.png"
    audit = RENDERS / "long-table-hall-identity-audit.png"
    subprocess.run(["magick", str(table_source), str(hero), "+append", str(table_ab)], check=True)
    subprocess.run(["magick", str(shrine_source), str(shrine), "+append", str(shrine_ab)], check=True)
    audit_top = RENDERS / ".identity-top.png"
    audit_bottom = RENDERS / ".identity-bottom.png"
    subprocess.run(["magick", str(hero), "-resize", "640x400!", str(portraits),
                    "-resize", "640x400!", "+append", str(audit_top)], check=True)
    subprocess.run(["magick", str(shrine), "-resize", "640x400!", str(tree),
                    "-resize", "640x400!", "+append", str(audit_bottom)], check=True)
    subprocess.run(["magick", str(audit_top), str(audit_bottom), "-append", str(audit)], check=True)
    table_source.unlink(missing_ok=True)
    shrine_source.unlink(missing_ok=True)
    audit_top.unlink(missing_ok=True)
    audit_bottom.unlink(missing_ok=True)

    evidence = {
        "baseSha": BASE_SHA,
        "productionGlb": str(GLB.relative_to(ROOT)),
        "evidenceOnly": ["lights", "cameras", "abstract portrait compositor proxies"],
        "renders": [str(path.relative_to(ROOT)) for path in (
            hero, left, right, portraits, shrine, tree, table_ab, shrine_ab, audit,
        )],
    }
    (ARTIFACTS / "ark-long-table-hall-visual-evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")


def main() -> None:
    RENDERS.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    shots = {
        "hero": ((0.0, -24.0, 9.0), (0.0, 1.0, 2.6), 46.0),
        "left": ((-13.5, -18.0, 7.2), (-1.0, 1.5, 2.6), 48.0),
        "right": ((13.5, -18.0, 7.2), (1.0, 1.5, 2.6), 48.0),
        "portraits": ((-4.8, -5.0, 6.1), (0.0, 9.8, 4.3), 54.0),
        "shrine": ((-3.0, -0.2, 3.4), (-6.15, 4.65, 1.55), 58.0),
        "tree": ((0.5, -5.0, 5.0), (6.05, 4.75, 2.70), 54.0),
    }
    outputs = {
        "hero": RENDERS / "long-table-hall-hero.png",
        "left": RENDERS / "long-table-hall-left.png",
        "right": RENDERS / "long-table-hall-right.png",
        "portraits": RENDERS / "long-table-hall-portraits.png",
        "shrine": RENDERS / "long-table-hall-pan-shrine.png",
        "tree": RENDERS / "long-table-hall-elder-tree.png",
    }
    if "--" in sys.argv:
        target = sys.argv[sys.argv.index("--") + 1]
        if target == "assemble":
            assemble()
            return
        camera, aim, lens = shots[target]
        render(outputs[target], camera, aim, lens)
        annotate(outputs[target], target.upper().replace("_", " "))
        return
    for target in shots:
        subprocess.run([bpy.app.binary_path, "--background", "--python", str(Path(__file__).resolve()),
                        "--", target], check=True)
    subprocess.run([bpy.app.binary_path, "--background", "--python", str(Path(__file__).resolve()),
                    "--", "assemble"], check=True)


if __name__ == "__main__":
    main()
