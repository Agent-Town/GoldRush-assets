"""Build the Baron's three render-only prop meshes.

One GLB, one material, one 512 colour atlas with surface and emission maps. Each named mesh stays below the 3,000
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
ATLAS_SOURCE = ROOT / "assets/raw/baron-props-atlas-fidelity-e1.png"
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
    "timber": (0.022, 0.022, 0.250, 0.978),
    "brass": (0.279, 0.022, 0.499, 0.978),
    "iron": (0.526, 0.022, 0.723, 0.978),
    "teal": (0.751, 0.022, 0.858, 0.978),
    "ember": (0.885, 0.022, 0.980, 0.978),
}


def create_atlas() -> bpy.types.Image:
    image = bpy.data.images.load(str(ATLAS_SOURCE), check_existing=False)
    image.name = "BaronPropsAtlas"
    image.colorspace_settings.name = "sRGB"
    image.scale(ATLAS_SIZE, ATLAS_SIZE)
    image.filepath_raw = str(ATLAS)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image


def create_material(atlas: bpy.types.Image) -> bpy.types.Material:
    material = kit.create_material("BaronPropsMaterial", atlas)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    # Data maps follow the same padded UV bands as the native colour artwork.
    surface = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    surface[:, :, 1:3] = (0.8, 0)
    emission = np.zeros_like(surface)
    emission[:, :, 3] = 1
    colours = np.array(atlas.pixels[:], dtype=np.float32).reshape(surface.shape)
    # A small illustrated fill keeps props legible beside the unlit body sprite in shadow.
    emission[:, :, :3] = colours[:, :, :3] * 0.12
    properties = {"timber": (0.78, 0), "brass": (0.42, 0.65), "iron": (0.70, 0.45), "teal": (0.3, 0), "ember": (0.7, 0)}
    for name, (u0, v0, u1, v1) in REGIONS.items():
        x0, y0 = (max(0, math.floor(value * ATLAS_SIZE) - 4) for value in (u0, v0))
        x1, y1 = (min(ATLAS_SIZE, math.ceil(value * ATLAS_SIZE) + 4) for value in (u1, v1))
        surface[y0:y1, x0:x1, 1:3] = properties[name]
        if name in {"teal", "ember"}:
            xs = np.clip(np.arange(x0, x1), math.ceil(u0 * ATLAS_SIZE), math.floor(u1 * ATLAS_SIZE) - 1)
            ys = np.clip(np.arange(y0, y1), math.ceil(v0 * ATLAS_SIZE), math.floor(v1 * ATLAS_SIZE) - 1)
            emission[y0:y1, x0:x1, :3] = colours[ys[:, None], xs[None, :], :3]
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        assert np.allclose(surface[cy, cx, 1:3], properties[name])
        fill = 1 if name in {"teal", "ember"} else 0.12
        assert np.allclose(emission[cy, cx, :3], colours[cy, cx, :3] * fill)
        # Cover both bilinear neighbours at every UV corner, including exclusive upper edges.
        for u in (u0, u1):
            for v in (v0, v1):
                x, y = math.floor(u * ATLAS_SIZE - 0.5), math.floor(v * ATLAS_SIZE - 0.5)
                assert np.allclose(surface[y:y + 2, x:x + 2, 1:3], properties[name])
    for name, pixels, colour_space in (("surface", surface, "Non-Color"), ("emission", emission, "sRGB")):
        image = bpy.data.images.new(f"BaronProps-{name}", ATLAS_SIZE, ATLAS_SIZE, alpha=True)
        image.colorspace_settings.name = colour_space
        image.pixels.foreach_set(pixels.ravel())
        image.filepath_raw = str(HERE / f"baron-props-{name}.png")
        image.file_format = "PNG"
        image.save()
        image.pack()
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = image
        if name == "surface":
            channels = nodes.new("ShaderNodeSeparateColor")
            links.new(texture.outputs["Color"], channels.inputs["Color"])
            links.new(channels.outputs["Green"], shader.inputs["Roughness"])
            links.new(channels.outputs["Blue"], shader.inputs["Metallic"])
        else:
            links.new(texture.outputs["Color"], shader.inputs["Emission Color"])
            shader.inputs["Emission Strength"].default_value = 1
    return material


def rocket_parts(prefix: str, material: bpy.types.Material, rack: bool = False) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    sides = 12 if rack else 16
    parts.append(kit.cylinder(f"{prefix} powder body", 0.105, 0.70, (0, 0.04, 0), "timber", material, vertices=sides, rotation=(math.pi / 2, 0, 0)))
    parts.append(kit.cone(f"{prefix} engraved nose", 0.105, 0.012, 0.24, (0, -0.43, 0), "brass", material, vertices=sides, rotation=(math.pi / 2, 0, 0)))
    parts.append(kit.cone(f"{prefix} iron nozzle", 0.12, 0.075, 0.18, (0, 0.48, 0), "iron", material, vertices=sides, rotation=(math.pi / 2, 0, 0)))
    for y in (-0.20, 0.24):
        region = "teal" if rack and y < 0 else "brass"
        parts.append(kit.torus(f"{prefix} worked band {y}", 0.108, 0.018, (0, y, 0), region, material, rotation=(math.pi / 2, 0, 0), major_segments=sides, minor_segments=4))
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
    bpy.context.preferences.filepaths.save_version = 0
    atlas = create_atlas()
    material = create_material(atlas)
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
    assert checked["materials"] == 1 and checked["images"] == 3
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
            str(ATLAS_SOURCE.relative_to(ROOT)),
            "artifacts/baron-presence/desktop-chrome-baron-carried-launcher.png",
            "assets/pilots/map-rebuild-spike/landmarks/baron/rocket_cart.glb",
            "src/entities/Enemy.ts:createClaimJumperAssets.sackGeometry",
        ],
        "surfaceMaps": [
            {"asset": path.name, "role": role, "colorSpace": colour_space,
             "width": ATLAS_SIZE, "height": ATLAS_SIZE,
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path, role, colour_space in (
                (ATLAS, "base color from native generated artwork", "sRGB"),
                (HERE / "baron-props-surface.png", "G roughness, B metalness; deterministic UV-region data", "linear"),
                (HERE / "baron-props-emission.png", "teal/ember emission plus 12% illustrated shadow fill; derived from base color", "sRGB"),
            )
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
