"""Build the Baron's three render-only prop meshes.

One GLB, one material, one 512 atlas. Each named mesh stays below the 3,000
triangle prop ceiling and exports byte-identically from the saved blend.
"""

from pathlib import Path
import hashlib
import importlib.util
import json
import math
import struct
import sys

import bpy
import numpy as np

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BLEND = HERE / "baron-props.blend"
GLB = HERE / "baron-props.glb"
ATLAS = HERE / "baron-props-atlas.png"
CONTRACT = HERE / "baron-props-asset-contract.json"
REEXPORT = Path("/tmp/baron-props-reexport.glb")
ATLAS_SIZE = 512
TRIANGLE_CEILING = 3_000
NODES = ("launcher", "rocket", "powder_keg")


def load_kit():
    path = ROOT / "assets/pilots/dredge-queen-3d/detail_opus5_kit.py"
    spec = importlib.util.spec_from_file_location("baron_props_detail_kit", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["baron_props_detail_kit"] = module
    spec.loader.exec_module(module)
    return module


kit = load_kit()

REGIONS = {
    "timber": (0.02, 0.02, 0.30, 0.98),
    "brass": (0.33, 0.02, 0.56, 0.98),
    "iron": (0.59, 0.02, 0.76, 0.98),
    "teal": (0.79, 0.02, 0.88, 0.98),
    "ember": (0.91, 0.02, 0.98, 0.98),
}


def create_atlas() -> bpy.types.Image:
    palette = {
        "timber": np.array((0.23, 0.095, 0.035), dtype=np.float32),
        "brass": np.array((0.48, 0.27, 0.075), dtype=np.float32),
        "iron": np.array((0.075, 0.067, 0.056), dtype=np.float32),
        "teal": np.array((0.045, 0.39, 0.39), dtype=np.float32),
        "ember": np.array((0.75, 0.19, 0.035), dtype=np.float32),
    }
    atlas = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    atlas[:, :, :3] = palette["iron"]
    rng = np.random.default_rng(1803)
    for name, (u0, v0, u1, v1) in REGIONS.items():
        x0, y0, x1, y1 = (int(value * ATLAS_SIZE) for value in (u0, v0, u1, v1))
        base = palette[name]
        noise = rng.normal(0, 0.008 if name != "teal" else 0.004, (y1 - y0, x1 - x0, 1))
        atlas[y0:y1, x0:x1, :3] = np.clip(base + noise, 0.008, 0.82)
        spacing = 28 if name in {"timber", "brass", "iron"} else 40
        for offset in range(-y1, x1 - x0, spacing):
            for yy in range(y0, y1):
                xx = x0 + offset + (yy - y0)
                if x0 <= xx < x1:
                    atlas[yy, xx:min(xx + 2, x1), :3] *= 0.52
        if name in {"brass", "iron"}:
            for yy in range(y0 + 18, y1, 42):
                for xx in range(x0 + 14, x1, 34):
                    atlas[yy - 2:yy + 3, xx - 2:xx + 3, :3] *= 0.40
        if name == "timber":
            for xx in range(x0 + 20, x1, 38):
                atlas[y0:y1, xx:xx + 2, :3] *= 0.62

    image = bpy.data.images.new("BaronPropsAtlas", ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(atlas.ravel())
    image.filepath_raw = str(ATLAS)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image


def rocket_parts(prefix: str, material: bpy.types.Material, rack: bool = False) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    sides = 12 if rack else 16
    parts.append(kit.cylinder(f"{prefix} powder body", 0.105, 0.70, (0, 0.04, 0), "timber", material, vertices=sides, rotation=(math.pi / 2, 0, 0)))
    parts.append(kit.cone(f"{prefix} engraved nose", 0.105, 0.012, 0.24, (0, -0.43, 0), "brass", material, vertices=sides, rotation=(math.pi / 2, 0, 0)))
    parts.append(kit.cone(f"{prefix} iron nozzle", 0.12, 0.075, 0.18, (0, 0.48, 0), "iron", material, vertices=sides, rotation=(math.pi / 2, 0, 0)))
    for y in (-0.20, 0.24):
        parts.append(kit.torus(f"{prefix} worked band {y}", 0.108, 0.018, (0, y, 0), "brass", material, rotation=(math.pi / 2, 0, 0), major_segments=sides, minor_segments=4))
    parts.append(kit.cylinder(f"{prefix} fuse eye", 0.052, 0.035, (0, 0.575, 0), "teal", material, vertices=10, rotation=(math.pi / 2, 0, 0), bevel=0))
    if not rack:
        for index, angle in enumerate((0, math.tau / 3, math.tau * 2 / 3)):
            x, z = math.cos(angle) * 0.11, math.sin(angle) * 0.11
            parts.append(kit.box(f"{prefix} stabilizer {index}", (0.035, 0.25, 0.17), (x, 0.34, z), "brass", material, bevel=0.004, rotation=(0, angle, 0)))
        parts.append(kit.torus(f"{prefix} assayer seal", 0.050, 0.012, (0, -0.03, 0.102), "iron", material, rotation=(math.pi / 2, 0, 0), major_segments=10, minor_segments=4))
    return parts


def build_launcher(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    for x in (-0.38, 0.38):
        parts.append(kit.box(f"Launcher timber stave {x}", (0.12, 1.18, 0.14), (x, 0.06, -0.09), "timber", material, bevel=0.018))
    for y in (-0.30, 0.32):
        parts.append(kit.box(f"Launcher brass crossband {y}", (0.92, 0.10, 0.17), (0, y, -0.13), "brass", material, bevel=0.014))
    for index, x in enumerate((-0.27, 0, 0.27)):
        rocket = rocket_parts(f"Rack rocket {index}", material, rack=True)
        for part in rocket:
            part.location.x += x
            part.location.z += 0.10
            bpy.context.view_layer.objects.active = part
            part.select_set(True)
            bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
            part.select_set(False)
        parts.extend(rocket)
    for x in (-0.38, 0.38):
        parts.append(kit.torus(f"Launcher shoulder ring {x}", 0.10, 0.025, (x, 0.61, -0.09), "iron", material, rotation=(math.pi / 2, 0, 0), major_segments=10))
    parts.append(kit.box("Launcher timber shoulder stock", (0.46, 0.18, 0.22), (0.60, 0.38, -0.08), "timber", material, bevel=0.025))
    parts.append(kit.box("Launcher timber grip", (0.17, 0.36, 0.20), (0.43, -0.46, -0.08), "timber", material, bevel=0.022, rotation=(0, 0, -0.22)))
    parts.append(kit.box("Launcher brass butt plate", (0.08, 0.22, 0.25), (0.82, 0.38, -0.08), "brass", material, bevel=0.012))
    return parts


def build_powder_keg(material: bpy.types.Material) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = [
        kit.cylinder("Keg stave body", 0.31, 0.68, (0, 0, 0), "timber", material, vertices=16),
        kit.cylinder("Keg top", 0.27, 0.035, (0, 0, 0.355), "timber", material, vertices=16, bevel=0),
        kit.cylinder("Keg bottom", 0.27, 0.035, (0, 0, -0.355), "timber", material, vertices=16, bevel=0),
    ]
    for z in (-0.25, 0.25):
        parts.append(kit.torus(f"Keg iron band {z}", 0.305, 0.032, (0, 0, z), "iron", material, major_segments=16, minor_segments=4))
    for index in range(8):
        angle = math.tau * index / 8
        parts.append(kit.box(f"Keg stave seam {index}", (0.025, 0.045, 0.58), (math.cos(angle) * 0.303, math.sin(angle) * 0.303, 0), "iron", material, bevel=0, rotation=(0, 0, angle)))
    parts.append(kit.cylinder("Keg teal fuse", 0.045, 0.15, (0.12, 0, 0.42), "teal", material, vertices=8, rotation=(0.12, 0, 0), bevel=0))
    parts.append(kit.torus("Keg assayer seal", 0.085, 0.018, (0, -0.302, 0.02), "brass", material, rotation=(math.pi / 2, 0, 0), major_segments=10, minor_segments=4))
    return parts


def glb_contract(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    assert data[:4] == b"glTF"
    offset = 12
    json_chunk = None
    while offset < len(data):
        length, kind = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset:offset + length]
        offset += length
        if kind == 0x4E4F534A:
            json_chunk = json.loads(chunk.rstrip(b" \x00"))
    assert json_chunk is not None
    accessors = json_chunk.get("accessors", [])
    meshes = json_chunk.get("meshes", [])
    triangles = {}
    for mesh in meshes:
        count = sum(accessors[primitive["indices"]]["count"] // 3 for primitive in mesh.get("primitives", []))
        triangles[mesh["name"].removesuffix("Mesh")] = count
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "triangles": triangles,
        "meshCount": len(meshes),
        "materials": len(json_chunk.get("materials", [])),
        "images": len(json_chunk.get("images", [])),
        "cameras": len(json_chunk.get("cameras", [])),
        "animations": len(json_chunk.get("animations", [])),
    }


def bounds(obj: bpy.types.Object) -> dict[str, list[float]]:
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    minimum = [min(point[axis] for point in points) for axis in range(3)]
    maximum = [max(point[axis] for point in points) for axis in range(3)]
    return {
        "min": [round(value, 6) for value in minimum],
        "max": [round(value, 6) for value in maximum],
        "size": [round(high - low, 6) for low, high in zip(minimum, maximum)],
    }


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    kit.reset_scene()
    atlas = create_atlas()
    material = kit.create_material("BaronPropsMaterial", atlas)
    groups = {
        "launcher": build_launcher(material),
        "rocket": rocket_parts("Flight rocket", material),
        "powder_keg": build_powder_keg(material),
    }
    objects = tuple(kit.join_component(name, groups[name], material, REGIONS) for name in NODES)
    per_prop = {obj.name: sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons) for obj in objects}
    per_bounds = {obj.name: bounds(obj) for obj in objects}
    assert all(count <= TRIANGLE_CEILING for count in per_prop.values()), per_prop
    assert len({slot.material.name for obj in objects for slot in obj.material_slots if slot.material}) == 1
    kit.export(objects, BLEND, GLB)

    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    bpy.ops.object.select_all(action="DESELECT")
    reopened = tuple(bpy.data.objects[name] for name in NODES)
    for obj in reopened:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = reopened[0]
    bpy.ops.export_scene.gltf(
        filepath=str(REEXPORT.with_suffix("")),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_materials="EXPORT",
    )

    checked = glb_contract(GLB)
    reexported = glb_contract(REEXPORT)
    assert checked["triangles"] == per_prop
    assert checked["meshCount"] == len(NODES)
    assert checked["materials"] == checked["images"] == 1
    assert checked["cameras"] == checked["animations"] == 0
    assert checked["sha256"] == reexported["sha256"]
    contract = {
        "blender": bpy.app.version_string,
        "asset": "baron-props.glb",
        "atlas": {
            "asset": "baron-props-atlas.png",
            "width": ATLAS_SIZE,
            "height": ATLAS_SIZE,
            "sha256": hashlib.sha256(ATLAS.read_bytes()).hexdigest(),
            "sharedByEveryProp": True,
        },
        "sourceLadder": "derive",
        "sources": [
            "artifacts/baron-presence/desktop-chrome-baron-carried-launcher.png",
            "assets/pilots/map-rebuild-spike/landmarks/baron/rocket_cart.glb",
            "src/entities/Enemy.ts:createClaimJumperAssets.sackGeometry",
        ],
        "props": {
            name: {"triangles": per_prop[name], "triangleBudget": TRIANGLE_CEILING, "bounds": per_bounds[name]}
            for name in NODES
        },
        "checked": checked,
        "byteIdenticalReexport": True,
        "reexportSha256": reexported["sha256"],
        "simulation": "none; visual mounts and pooled presentation only",
    }
    CONTRACT.write_text(json.dumps(contract, indent=2) + "\n")
    print(json.dumps(contract, indent=2))


if __name__ == "__main__":
    main()
