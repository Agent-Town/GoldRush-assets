"""Measure the GPU cost profile of the duel entries against their shipped models.

Pure-stdlib GLB analysis — no Blender, no engine, no DOM shim. Reports the numbers a
renderer actually pays: draw calls, triangles, index/attribute bytes, morph-target
storage (which three.js uploads as a float texture, so it is the real risk of a
higher-poly model with a morph on every mesh), and base-colour texture VRAM including
the mip chain.

Run:  python3 assets/pilots/dredge-queen-3d/measure_detail_opus5_cost.py
"""

from pathlib import Path
import json
import struct

ROOT = Path(__file__).resolve().parents[3]

COMPONENT_BYTES = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
TYPE_COUNTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}

PAIRS = {
    "dredge-queen": (
        ROOT / "assets/pilots/dredge-queen-3d/dredge-queen.glb",
        ROOT / "assets/pilots/dredge-queen-3d/dredge-queen-detail-opus5.glb",
    ),
    "salvage-claw": (
        ROOT / "assets/pilots/salvage-claw-3d/salvage-claw.glb",
        ROOT / "assets/pilots/salvage-claw-3d/salvage-claw-detail-opus5.glb",
    ),
}


def read_glb(path: Path) -> tuple[dict, bytes]:
    data = path.read_bytes()
    magic, version, total = struct.unpack_from("<4sII", data)
    assert magic == b"glTF" and version == 2 and total == len(data)
    json_length, json_kind = struct.unpack_from("<II", data, 12)
    assert json_kind == 0x4E4F534A
    document = json.loads(data[20:20 + json_length])
    binary_offset = 20 + json_length
    binary_length, binary_kind = struct.unpack_from("<II", data, binary_offset)
    assert binary_kind == 0x004E4942
    return document, data[binary_offset + 8:binary_offset + 8 + binary_length]


def accessor_bytes(accessor: dict) -> int:
    return accessor["count"] * TYPE_COUNTS[accessor["type"]] * COMPONENT_BYTES[accessor["componentType"]]


def image_dimensions(document: dict, binary: bytes) -> list[tuple[int, int]]:
    dimensions = []
    for image in document.get("images", []):
        view = document["bufferViews"][image["bufferView"]]
        start = view.get("byteOffset", 0)
        payload = binary[start:start + view["byteLength"]]
        assert payload[:8] == b"\x89PNG\r\n\x1a\n"
        dimensions.append(struct.unpack(">II", payload[16:24]))
    return dimensions


def texture_vram(dimensions: list[tuple[int, int]]) -> int:
    """RGBA8 upload plus a full mip chain (the 4/3 series), which is what the GPU holds."""
    total = 0
    for width, height in dimensions:
        base = width * height * 4
        total += int(base * 4 / 3)
    return total


def profile(path: Path) -> dict:
    document, binary = read_glb(path)
    accessors = document["accessors"]
    triangles = 0
    index_bytes = 0
    attribute_bytes = 0
    morph_bytes = 0
    morph_targets = 0
    draw_calls = 0
    vertices = 0
    for mesh in document.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            draw_calls += 1
            triangles += accessors[primitive["indices"]]["count"] // 3
            index_bytes += accessor_bytes(accessors[primitive["indices"]])
            for accessor_index in primitive["attributes"].values():
                attribute_bytes += accessor_bytes(accessors[accessor_index])
            vertices += accessors[primitive["attributes"]["POSITION"]]["count"]
            for target in primitive.get("targets", []):
                morph_targets += 1
                for accessor_index in target.values():
                    morph_bytes += accessor_bytes(accessors[accessor_index])
    dimensions = image_dimensions(document, binary)
    geometry_bytes = index_bytes + attribute_bytes + morph_bytes
    return {
        "file": str(path.relative_to(ROOT)),
        "fileBytes": path.stat().st_size,
        "drawCalls": draw_calls,
        "materials": len(document.get("materials", [])),
        "triangles": triangles,
        "vertices": vertices,
        "indexBytes": index_bytes,
        "attributeBytes": attribute_bytes,
        "morphTargets": morph_targets,
        "morphBytes": morph_bytes,
        "geometryBytes": geometry_bytes,
        "atlas": [list(dim) for dim in dimensions],
        "textureVramBytes": texture_vram(dimensions),
        "totalVramBytes": geometry_bytes + texture_vram(dimensions),
    }


def megabytes(value: int) -> float:
    return round(value / (1024 * 1024), 3)


def main() -> None:
    report = {}
    for name, (shipped_path, detail_path) in PAIRS.items():
        shipped = profile(shipped_path)
        detail = profile(detail_path)
        report[name] = {
            "shipped": shipped,
            "detail": detail,
            "delta": {
                "drawCalls": f"{shipped['drawCalls']} -> {detail['drawCalls']} (unchanged)"
                if shipped["drawCalls"] == detail["drawCalls"]
                else f"{shipped['drawCalls']} -> {detail['drawCalls']}",
                "materials": f"{shipped['materials']} -> {detail['materials']}",
                "triangles": f"{shipped['triangles']} -> {detail['triangles']} ({round(detail['triangles'] / shipped['triangles'], 2)}x)",
                "geometryMB": f"{megabytes(shipped['geometryBytes'])} -> {megabytes(detail['geometryBytes'])}",
                "morphMB": f"{megabytes(shipped['morphBytes'])} -> {megabytes(detail['morphBytes'])}",
                "textureVramMB": f"{megabytes(shipped['textureVramBytes'])} -> {megabytes(detail['textureVramBytes'])}",
                "totalVramMB": f"{megabytes(shipped['totalVramBytes'])} -> {megabytes(detail['totalVramBytes'])}",
                "totalVramDeltaMB": megabytes(detail["totalVramBytes"] - shipped["totalVramBytes"]),
            },
        }
    destination = ROOT / "assets/pilots/dredge-queen-3d/detail-opus5-cost-profile.json"
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({name: data["delta"] for name, data in report.items()}, indent=2))
    print(f"\nwrote {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
