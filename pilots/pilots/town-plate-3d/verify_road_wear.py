from pathlib import Path
import hashlib
import json
import struct
import subprocess


ROOT = Path(__file__).resolve().parents[3]
BASELINE = "dc46019af763ff13d5e9ea8fc99d91cbe689e332"
GLB = "assets/pilots/town-plate-3d/town-plate.glb"
LAYOUT = "artifacts/town-plate-3d/layout-contract.json"
OUT = ROOT / "artifacts/town-plate-3d/road-wear-contract.json"
COMPONENT_BYTES = {5121: 1, 5123: 2, 5125: 4, 5126: 4}
INDEX_FORMAT = {5121: "B", 5123: "H", 5125: "I"}
TYPE_COMPONENTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def git_bytes(path):
    return subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT)


def parse_glb(data):
    magic, version, total = struct.unpack_from("<4sII", data, 0)
    assert magic == b"glTF" and version == 2 and total == len(data)
    document = None
    binary = b""
    cursor = 12
    while cursor < len(data):
        length, kind = struct.unpack_from("<II", data, cursor)
        cursor += 8
        payload = data[cursor:cursor + length]
        cursor += length
        if kind == 0x4E4F534A:
            document = json.loads(payload)
        elif kind == 0x004E4942:
            binary = payload
    return document, binary


def accessor_payload(document, binary, accessor_index):
    accessor = document["accessors"][accessor_index]
    view = document["bufferViews"][accessor["bufferView"]]
    element_size = COMPONENT_BYTES[accessor["componentType"]] * TYPE_COMPONENTS[accessor["type"]]
    stride = view.get("byteStride", element_size)
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    end = start + (accessor["count"] - 1) * stride + element_size
    return binary[start:end]


def topology_payload(document, binary, accessor_index):
    accessor = document["accessors"][accessor_index]
    view = document["bufferViews"][accessor["bufferView"]]
    stride = view.get("byteStride", COMPONENT_BYTES[accessor["componentType"]])
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    values = [
        struct.unpack_from("<" + INDEX_FORMAT[accessor["componentType"]], binary, start + index * stride)[0]
        for index in range(accessor["count"])
    ]
    triangles = sorted(tuple(sorted(values[index:index + 3])) for index in range(0, len(values), 3))
    return b"".join(struct.pack("<III", *triangle) for triangle in triangles)


def summary(data):
    document, binary = parse_glb(data)
    digest = hashlib.sha256()
    triangle_count = 0
    for mesh in document["meshes"]:
        for primitive in mesh["primitives"]:
            for name, accessor_index in sorted(primitive["attributes"].items()):
                digest.update(name.encode() + b"\0" + accessor_payload(document, binary, accessor_index))
            digest.update(topology_payload(document, binary, primitive["indices"]))
            triangle_count += document["accessors"][primitive["indices"]]["count"] // 3
    image = document["images"][0]
    view = document["bufferViews"][image["bufferView"]]
    start = view.get("byteOffset", 0)
    return {
        "glbSha256": hashlib.sha256(data).hexdigest(),
        "geometrySha256": digest.hexdigest(),
        "imageSha256": hashlib.sha256(binary[start:start + view["byteLength"]]).hexdigest(),
        "triangles": triangle_count,
    }


def main():
    baseline = summary(git_bytes(GLB))
    candidate = summary((ROOT / GLB).read_bytes())
    baseline_layout = json.loads(git_bytes(LAYOUT))
    candidate_layout = json.loads((ROOT / LAYOUT).read_text())
    checks = {
        "centerlinesIdentical": baseline_layout["routes"] == candidate_layout["routes"],
        "geometryIdentical": baseline["geometrySha256"] == candidate["geometrySha256"],
        "trianglesIdentical": baseline["triangles"] == candidate["triangles"],
        "flatWalkIdentical": baseline_layout["flatWalk"] == candidate_layout["flatWalk"],
        "textureChanged": baseline["imageSha256"] != candidate["imageSha256"],
    }
    assert all(checks.values()), checks
    report = {
        "baselineRef": BASELINE,
        "scope": "texture-only inherited road wear; E4 boulevard geometry and every canonical centerline preserved",
        "baseline": baseline,
        "candidate": candidate,
        "checks": checks,
        "routeMaxAbs": candidate_layout["flatWalk"]["routeMaxAbs"],
        "plazaMaxAbs": candidate_layout["flatWalk"]["plazaMaxAbs"],
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
