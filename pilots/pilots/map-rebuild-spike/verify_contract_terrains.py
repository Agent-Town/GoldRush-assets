"""Verify all five unique contract terrain pilots and owner evidence."""

from pathlib import Path
import hashlib
import importlib.util
import json
import math
import struct
import subprocess
import sys
import zlib

import bpy


ROOT = Path(__file__).resolve().parents[3]
SOURCE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = ROOT / "artifacts/map-rebuild-spike"
VERIFY_SOURCE = ROOT / "assets/pilots/schoolhouse-3d/verify_schoolhouse.py"

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("terrain_glb_verify", VERIFY_SOURCE)
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)

ASSETS = [
    ("claim", "the-claim-terrain", "frontier-river-claim", {
        "water_mask": "z=-5..5; shallows to +/-6.25",
        "ford_mask": "x=-3..3 inside water band",
    }),
    ("dryGulch", "dry-gulch-terrain", "e1-dry-gulch", {
        "water_mask": "spring pond circle at (-18,-18), radius 1.4; runtime-owned",
        "heightfield": "spring basin plus southwest and east descriptor washes",
    }),
    ("twinBanks", "twin-banks-terrain", "e1-twin-banks", {
        "contract_id": "e1-twin-banks",
        "water_mask": "z=-7.8..7.8 visual river; runtime water remains descriptor-owned",
        "ford_mask": "two fords centered x=-16 and x=16, each halfWidth=3",
        "regional_family": "Epoch 1 frontier river county",
        "identity_rule": "unique mesh, atlas, macro silhouette, and landmark composition",
    }),
    ("nightShift", "night-shift-terrain", "frontier-river-claim", {
        "contract_id": "e1-night-shift",
        "water_mask": "z=-5..5; shallows to +/-6.25",
        "ford_mask": "x=-3..3 inside water band",
        "regional_family": "Epoch 1 frontier river county",
        "identity_rule": "unique mesh, atlas, macro silhouette, and landmark composition",
    }),
    ("baron", "baron-terrain", "frontier-river-claim", {
        "contract_id": "e1-baron",
        "water_mask": "z=-5..5; shallows to +/-6.25",
        "ford_mask": "x=-3..3 inside water band",
        "regional_family": "Epoch 1 frontier river county",
        "identity_rule": "unique mesh, atlas, macro silhouette, and landmark composition",
    }),
]

PANORAMAS = {
    "claim": "the-claim",
    "dryGulch": "dry-gulch",
    "twinBanks": "twin-banks",
    "nightShift": "night-shift",
    "baron": "baron",
}

EVIDENCE_RENDERS = {
    "all-contracts-mood-ab.png": (
        "baca111367eb164149607b7738b3cee3d38363f9273cd4a9bf20512af97638d4",
        (1280, 2092),
        {
            "assets/raw/plate-contract-the-claim.png": "30f8785f4b7d6fbe383847099d7ec2bc73a3263f1ade662fbba352bf6e00d8fa",
            "artifacts/map-rebuild-spike/owner-run-camera-sculpted.png": "bd2bc951b0b254cdd7577131ff63b22f6bde67979b750bc2c446f6f72a1d3d26",
            "assets/raw/plate-contract-dry-gulch.png": "56c86dbe87afde3c5be42626843dc036aac4a827b82f68a59a235c2d35ad0f57",
            "artifacts/map-rebuild-spike/dry-gulch-run-camera.png": "627a3ab7f50d746c51d512331c1497e5ea0e46a290b1dc56d122dea3aa857c15",
            "assets/raw/plate-contract-twin-banks.png": "6dc2a97319eed5f3c17622b7c77be8b032522ad3dc620d11c666ae9d3895c73f",
            "artifacts/map-rebuild-spike/twin-banks-run-camera-unique.png": "1ca26d9a6ab6e88a60b7dfce5819e249314a985903a3c2f2658291782f9dec91",
            "assets/raw/plate-contract-night-shift.png": "d1ff71857376e4d9337e1e1d69a23b63aa6968cdbcf9f2b72524e21a688b1ade",
            "artifacts/map-rebuild-spike/night-shift-run-camera-unique.png": "7f076b87d4fd1bf71622e3a2dd753311eed6fb6cd1bbfa172733e8fef1889176",
            "assets/raw/plate-contract-baron.png": "287a20e3df6d98f22b5e55340f1fd5b928cbcd3b13d77d6a5bfcccb98bcc1059",
            "artifacts/map-rebuild-spike/baron-run-camera-unique.png": "055703273fceeb9fc8169e033fdaf5d03c48e908869cdff96d50dc6c05f64c43",
        },
    ),
    "all-contracts-building-grit-ab.png": (
        "5c8dc109834f3c1fd7b56606da6c0d1faf4e2528a6336c3d5cc0604690618975",
        (1552, 1945),
        {},
    ),
    "the-claim-exterior-ab.png": (
        "2053765f157d85d857988d290aeaf8ea9717365ddf89c2a2e258f3e11176bdea",
        (1920, 604),
        {
            "artifacts/map-rebuild-spike/the-claim-exterior-before-low.png": "337e06cca6b5e015e2ed57c02dd82e1d8401ef96c1af77a9dc725183356ce4dd",
            "artifacts/map-rebuild-spike/the-claim-panorama-before.png": "2f1c0cadbc540d2a9019de88142861519215687cdd2b334834fc5f9c0cfce0f8",
        },
    ),
    "all-contracts-exterior-ab.png": (
        "9bb6da238dd228c6c8aa1d9d91144a276e36fa4461cca940780723c6e7058c1f",
        (1920, 2472),
        {
            "artifacts/map-rebuild-spike/dry-gulch-exterior-before-edge.png": "b9524cfee3661c491b77baccbe9af07f474456e90f70ac78ee6c29d1b33ffba2",
            "artifacts/map-rebuild-spike/dry-gulch-run-camera-east-edge.png": "cf908aaab51dc31ab7b32c5eeb01b6c45f0fac55f9088d1fcb51d87edcdb3938",
            "artifacts/map-rebuild-spike/twin-banks-exterior-before-edge.png": "4af832dd592bbd4ff410bd589d2c8ee1b54426bc758ad53e96c7ac2b68b8501b",
            "artifacts/map-rebuild-spike/twin-banks-run-camera-east-edge.png": "c7c344ae9b8c374ecdc31483e33df6953de4d14cc97b23df12fd4d9b2eac6d98",
            "artifacts/map-rebuild-spike/night-shift-exterior-before-edge.png": "c2af561bc9fcbbd1ef77fb38a94bb330e60ee1e0caa451326f824bb792ef1095",
            "artifacts/map-rebuild-spike/night-shift-run-camera-east-edge.png": "f5dd7ae95544a294bd5628dc26e169f40b7b1df59d199b9e9e5a7c25fb8711c7",
            "artifacts/map-rebuild-spike/baron-exterior-before-edge.png": "0f0b6006cd7785297cdd7e03a8d043946de282905062bccc4ad66dc03d99fdc5",
            "artifacts/map-rebuild-spike/baron-run-camera-east-edge.png": "d96d3ea3d766571824ddfa53caee42e4087647203f45df8b2b69cfc70cf02feb",
        },
    ),
    "all-contracts-exterior-low-verdict.png": (
        "2d311db747a47bd44b5cbeebaee04ca3f1bebbafe5062eb03bbe40747aeab1ff",
        (1920, 1080),
        {
            "artifacts/map-rebuild-spike/dry-gulch-low-angle-unique.png": "9ecac3f4d6b025df4b3416a1011b996c2fb260d487847aeda9961a8fb6a0bd0a",
            "artifacts/map-rebuild-spike/twin-banks-low-angle-unique.png": "f1eb17695cb4b4e661f9b9011276afffb3592f94fdcbfd64c8f5175b1e39bd7c",
            "artifacts/map-rebuild-spike/night-shift-low-angle-unique.png": "df7ced59dd767be562064c564d7e51cd343625804c81221ddc613961237982de",
            "artifacts/map-rebuild-spike/baron-low-angle-unique.png": "10bb499324450d9cc7f33754af155b0d3a721a61b7b453a45a3132ed45931ad2",
        },
    ),
    "all-contracts-exterior-edge-crops.png": (
        "c1ef653126cb368c19fc51b1167a702e72c334b56643ab646f5b11257236dc38",
        (1920, 1080),
        {
            "artifacts/map-rebuild-spike/dry-gulch-run-camera-east-edge.png": "cf908aaab51dc31ab7b32c5eeb01b6c45f0fac55f9088d1fcb51d87edcdb3938",
            "artifacts/map-rebuild-spike/twin-banks-run-camera-east-edge.png": "c7c344ae9b8c374ecdc31483e33df6953de4d14cc97b23df12fd4d9b2eac6d98",
            "artifacts/map-rebuild-spike/night-shift-run-camera-east-edge.png": "f5dd7ae95544a294bd5628dc26e169f40b7b1df59d199b9e9e5a7c25fb8711c7",
            "artifacts/map-rebuild-spike/baron-run-camera-east-edge.png": "d96d3ea3d766571824ddfa53caee42e4087647203f45df8b2b69cfc70cf02feb",
        },
    ),
    "all-contracts-panorama-mood-ab.png": (
        "e4c09f477c76b3abfbeb7f74c7a5a221a51083181952daa23fe0046a4d347966",
        (1920, 2092),
        {
            "assets/raw/plate-contract-the-claim.png": "30f8785f4b7d6fbe383847099d7ec2bc73a3263f1ade662fbba352bf6e00d8fa",
            "artifacts/map-rebuild-spike/the-claim-panorama-before.png": "2f1c0cadbc540d2a9019de88142861519215687cdd2b334834fc5f9c0cfce0f8",
            "artifacts/map-rebuild-spike/the-claim-panorama-mounted.png": "e46631bee3cfbbe4d7ac5c7392123386e8fed036d58261da4e94bada3f644cf4",
            "assets/raw/plate-contract-dry-gulch.png": "56c86dbe87afde3c5be42626843dc036aac4a827b82f68a59a235c2d35ad0f57",
            "artifacts/map-rebuild-spike/dry-gulch-panorama-before.png": "9ecac3f4d6b025df4b3416a1011b996c2fb260d487847aeda9961a8fb6a0bd0a",
            "artifacts/map-rebuild-spike/dry-gulch-panorama-mounted.png": "f8872abe56616daff1db4eb289647718d069d724dabbf6a9376fbeb60e6698c4",
            "assets/raw/plate-contract-twin-banks.png": "6dc2a97319eed5f3c17622b7c77be8b032522ad3dc620d11c666ae9d3895c73f",
            "artifacts/map-rebuild-spike/twin-banks-panorama-before.png": "f1eb17695cb4b4e661f9b9011276afffb3592f94fdcbfd64c8f5175b1e39bd7c",
            "artifacts/map-rebuild-spike/twin-banks-panorama-mounted.png": "a72940a0857888c07b22f29eeb1f1433283b98f4a941b17f5340a6243bbd76dd",
            "assets/raw/plate-contract-night-shift.png": "d1ff71857376e4d9337e1e1d69a23b63aa6968cdbcf9f2b72524e21a688b1ade",
            "artifacts/map-rebuild-spike/night-shift-panorama-before.png": "df7ced59dd767be562064c564d7e51cd343625804c81221ddc613961237982de",
            "artifacts/map-rebuild-spike/night-shift-panorama-mounted.png": "3e428a90df61c11bc43465b6b86ae97fc68fdd1afa604c35a38185d7b2b65c58",
            "assets/raw/plate-contract-baron.png": "287a20e3df6d98f22b5e55340f1fd5b928cbcd3b13d77d6a5bfcccb98bcc1059",
            "artifacts/map-rebuild-spike/baron-panorama-before.png": "10bb499324450d9cc7f33754af155b0d3a721a61b7b453a45a3132ed45931ad2",
            "artifacts/map-rebuild-spike/baron-panorama-mounted.png": "73e57026c5016e5398b74e767adf5ef0ea29682058cbdc450324a95770ee22e0",
        },
    ),
    "all-contracts-panorama-distance-gate.png": (
        "63820a384100b78edb88c7dcb88b3c7bd222ea93fc99bed904e714fe041893fc",
        (1920, 1792),
        {
            "artifacts/map-rebuild-spike/the-claim-panorama-horizon.png": "eb3921a5654b80df39309efd8dcdf4a5eada1ffbeba21003328c78d4fd373523",
            "artifacts/map-rebuild-spike/dry-gulch-panorama-horizon.png": "3192a6172c94ec3cc2953eea3a1e7668645a8aeff5ce5acbaee111dcdd94f452",
            "artifacts/map-rebuild-spike/twin-banks-panorama-horizon.png": "2dd6c6eaa0920ff1d5d9810e95b214d0868b818ff2adf7ae6f815a84d6d56b92",
            "artifacts/map-rebuild-spike/night-shift-panorama-horizon.png": "e02267deac9caa90097257f0abc14c81f3909b361cc34da2e3e982bf5d20af0b",
            "artifacts/map-rebuild-spike/baron-panorama-horizon.png": "2d50092e8034b03878c64b5b5fdaa245e2b0c1df8d5e51caef7faf810cc71314",
        },
    ),
}


def glb_parts(path):
    data = path.read_bytes()
    magic, version, total = struct.unpack_from("<4sII", data)
    assert magic == b"glTF" and version == 2 and total == len(data)
    json_length = struct.unpack_from("<I", data, 12)[0]
    json_kind = struct.unpack_from("<I", data, 16)[0]
    assert json_kind == 0x4E4F534A
    document = json.loads(data[20 : 20 + json_length])
    bin_offset = 20 + json_length
    bin_length, bin_kind = struct.unpack_from("<II", data, bin_offset)
    assert bin_kind == 0x004E4942
    binary = data[bin_offset + 8 : bin_offset + 8 + bin_length]
    assert len(binary) == bin_length
    return document, binary


def png_pixels(data):
    """Return metadata-independent scanline bytes for an 8-bit PNG."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR"
    width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(">IIBBBBB", data[16:29])
    assert bit_depth in {8, 16} and compression == 0 and filtering == 0 and interlace == 0
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[color_type]
    bytes_per_pixel = channels * (bit_depth // 8)
    compressed = []
    offset = 8
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        if kind == b"IDAT":
            compressed.append(data[offset + 8 : offset + 8 + length])
        offset += length + 12
    encoded = zlib.decompress(b"".join(compressed))
    row_bytes = width * bytes_per_pixel
    assert len(encoded) == height * (row_bytes + 1)
    decoded = bytearray()
    previous = bytearray(row_bytes)

    def paeth(left, above, upper_left):
        estimate = left + above - upper_left
        distances = (abs(estimate - left), abs(estimate - above), abs(estimate - upper_left))
        return (left, above, upper_left)[distances.index(min(distances))]

    for row_index in range(height):
        start = row_index * (row_bytes + 1)
        filter_kind = encoded[start]
        source = encoded[start + 1 : start + 1 + row_bytes]
        row = bytearray(row_bytes)
        for index, value in enumerate(source):
            left = row[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            above = previous[index]
            upper_left = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            predictor = {
                0: 0,
                1: left,
                2: above,
                3: (left + above) // 2,
                4: paeth(left, above, upper_left),
            }[filter_kind]
            row[index] = (value + predictor) & 0xFF
        decoded.extend(row)
        previous = row
    return width, height, bit_depth, color_type, bytes(decoded)


def png_contract(path, expected_sha=None, expected_size=None):
    assert path.is_file()
    data = path.read_bytes()
    width, height, bit_depth, color_type, pixels = png_pixels(data)
    pixel_digest = hashlib.sha256(struct.pack(">IIBB", width, height, bit_depth, color_type) + pixels).hexdigest()
    container_digest = hashlib.sha256(data).hexdigest()
    assert len(data) > 10_000
    if expected_sha:
        assert pixel_digest == expected_sha
    if expected_size:
        assert (width, height) == expected_size
    return {
        "bytes": len(data),
        "pixelSha256": pixel_digest,
        "containerSha256": container_digest,
        "width": width,
        "height": height,
    }


def embedded_texture(document, binary):
    assert len(document.get("images", [])) == 1
    image = document["images"][0]
    assert image.get("mimeType") == "image/png" and "bufferView" in image
    view = document["bufferViews"][image["bufferView"]]
    start = view.get("byteOffset", 0)
    payload = binary[start : start + view["byteLength"]]
    digest = hashlib.sha256(payload).hexdigest()
    assert payload[:8] == b"\x89PNG\r\n\x1a\n" and payload[12:16] == b"IHDR"
    width, height = struct.unpack(">II", payload[16:24])
    return {"bytes": len(payload), "sha256": digest, "width": width, "height": height}


def png_evidence(name, expected_sha, expected_size, inputs):
    path = ARTIFACT_DIR / name
    evidence = png_contract(path, expected_sha, expected_size)
    evidence["inputs"] = {
        input_name: png_contract(ROOT / input_name, input_sha)
        for input_name, input_sha in inputs.items()
    }
    return evidence


def mesh_geometry_probes(key, mesh):
    heights = {
        (round(float(vertex.co.x), 3), round(float(-vertex.co.y), 3)): float(vertex.co.z)
        for vertex in mesh.data.vertices
    }

    def height(x, game_z):
        return heights[(x, game_z)]

    if key == "claim":
        centerline = [height(x, 0.0) for x in (-24.0, -16.0, -8.0, 0.0, 8.0, 16.0, 24.0)]
        ford_lift = height(0.0, 0.0) - (height(-4.0, 0.0) + height(4.0, 0.0)) / 2.0
        bank_rise = height(0.0, 6.5) - height(0.0, 5.0)
        assert max(centerline) < 0.0 and ford_lift > 0.35 and bank_rise > 0.45
        return {"riverCenterlineMax": max(centerline), "fordLift": ford_lift, "northBankRise": bank_rise}

    if key == "dryGulch":
        basin_center = height(-18.0, -18.0)
        basin_ring = [height(-10.5, -18.0), height(-25.5, -18.0), height(-18.0, -10.5), height(-18.0, -25.5)]
        basin_relief = sum(basin_ring) / len(basin_ring) - basin_center
        southwest_wash = (height(-3.5, -15.5) + height(-6.5, -20.5)) / 2.0 - height(-5.0, -18.0)
        east_wash = (height(13.0, 13.0) + height(15.0, 7.0)) / 2.0 - height(14.0, 10.0)
        assert basin_relief > 0.5 and southwest_wash > 0.15 and east_wash > 0.1
        return {"springBasinRelief": basin_relief, "southwestWashDepth": southwest_wash, "eastWashDepth": east_wash}

    if key == "twinBanks":
        west_ford_lift = height(-16.0, 0.0) - (height(-20.0, 0.0) + height(-12.0, 0.0)) / 2.0
        east_ford_lift = height(16.0, 0.0) - (height(12.0, 0.0) + height(20.0, 0.0)) / 2.0
        wide_bank_rise = min(height(0.0, -8.5), height(0.0, 8.5)) - height(0.0, 7.5)
        bank_asymmetry = max(
            abs(height(-24.0, 18.0) - height(-24.0, -18.0)),
            abs(height(20.0, 18.0) - height(20.0, -18.0)),
        )
        assert west_ford_lift > 0.12 and east_ford_lift > 0.12
        assert wide_bank_rise > 0.45 and bank_asymmetry > 0.18
        return {
            "westFordLift": west_ford_lift,
            "eastFordLift": east_ford_lift,
            "wideBankRise": wide_bank_rise,
            "opposedBankAsymmetry": bank_asymmetry,
        }

    ford_lift = height(0.0, 0.0) - (height(-4.0, 0.0) + height(4.0, 0.0)) / 2.0
    if key == "nightShift":
        left_shoulder = height(-28.0, 12.0) - height(0.0, 12.0)
        right_shoulder = height(28.0, -12.0) - height(0.0, -12.0)
        lantern_corridor = height(0.0, 16.0) - height(10.0, 16.0)
        assert ford_lift > 0.25 and left_shoulder > 0.75 and right_shoulder > 0.75
        assert abs(lantern_corridor) > 0.04
        return {
            "fordLift": ford_lift,
            "leftRockShoulder": left_shoulder,
            "rightRockShoulder": right_shoulder,
            "lanternTerraceDelta": lantern_corridor,
        }

    far_bank_rise = height(0.0, -20.0) - height(0.0, 20.0)
    trench_depth = (height(0.0, -8.0) + height(0.0, -11.0)) / 2.0 - height(0.0, -9.5)
    bastion_relief = height(-23.0, -12.5) - height(0.0, 12.5)
    assert ford_lift > 0.25 and far_bank_rise > 0.70
    assert trench_depth > 0.08 and bastion_relief > 0.75
    return {
        "fordLift": ford_lift,
        "farBankRise": far_bank_rise,
        "siegeTrenchDepth": trench_depth,
        "westBastionRelief": bastion_relief,
    }


def verify_asset(key, stem, tile_id, expected_extras):
    blend = SOURCE_DIR / f"{stem}.blend"
    glb = SOURCE_DIR / f"{stem}.glb"
    contract_path = SOURCE_DIR / f"{stem}-contract.json"
    checked = verify.contract(glb)
    document, binary = glb_parts(glb)
    extras = document["nodes"][0].get("extras", {})
    contract = json.loads(contract_path.read_text())

    bpy.ops.wm.open_mainfile(filepath=str(blend))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    cameras = [obj for obj in bpy.data.objects if obj.type == "CAMERA"]
    lights = [obj for obj in bpy.data.objects if obj.type == "LIGHT"]
    bpy.ops.object.select_all(action="DESELECT")
    for mesh in meshes:
        mesh.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    reexport_path = Path("/tmp") / f"gold-rush-{stem}-reexport.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(reexport_path),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_materials="EXPORT",
    )
    reexported = verify.contract(reexport_path)
    _, reexported_binary = glb_parts(reexport_path)
    checked_binary_sha = hashlib.sha256(binary).hexdigest()
    reexported_binary_sha = hashlib.sha256(reexported_binary).hexdigest()
    texture = embedded_texture(document, binary)
    geometry_probes = mesh_geometry_probes(key, meshes[0])
    vertex_payload = b"".join(struct.pack("<3f", *vertex.co[:]) for vertex in meshes[0].data.vertices)
    geometry_sha = hashlib.sha256(vertex_payload).hexdigest()
    semantic_keys = (
        "meshes", "primitives", "triangles", "materials", "images", "embeddedImages",
        "cameras", "lights", "animations", "bounds", "materialContract",
    )
    semantic_identical = all(checked[name] == reexported[name] for name in semantic_keys)

    assert len(meshes) == 1 and not cameras and not lights
    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] <= 60_000
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert checked["materialContract"][0]["metallicFactor"] == 0
    assert checked["materialContract"][0]["roughnessFactor"] >= 0.89
    assert checked["materialContract"][0]["hasBaseColorTexture"]
    assert checked_binary_sha == reexported_binary_sha
    assert extras.get("render_only") is True and extras.get("sim_surface") == "planar"
    assert extras.get("height_socket") == "Terrain.visualY" and extras.get("tile_id") == tile_id
    assert all(extras.get(name) == value for name, value in expected_extras.items())
    assert contract["triangles"] == checked["triangles"]
    assert contract["files"]["blend"]["sha256"] == hashlib.sha256(blend.read_bytes()).hexdigest()
    assert contract["files"]["glb"]["sha256"] == checked["sha256"]
    assert contract["texture"] == {"count": 1, "width": 2048, "height": 2048, "embedded": True}
    assert texture["width"] == texture["height"] == 2048
    assert texture["sha256"] == contract["files"]["atlas"]["sha256"]
    assert semantic_identical
    mount_space = contract["landmarkMountSpace"]
    mounts = contract["landmarkMounts"]
    assert mount_space["coordinates"] == "game X/Y/Z"
    assert mount_space["positionY"] == "local offset added to Terrain.visualY at the mount X/Z"
    assert mount_space["ownership"] == "landmark assets mount at runtime and are never baked into terrain"
    assert len(mounts) == 5 and len({mount["id"] for mount in mounts}) == 5
    for mount in mounts:
        assert mount["id"] and isinstance(mount["id"], str)
        for field in ("position", "rotation", "scale"):
            values = mount[field]
            assert len(values) == 3 and all(math.isfinite(value) for value in values)
        assert mount["position"][1] == 0.0
        assert all(value > 0.0 for value in mount["scale"])
    assert any("plate-contract-" in source for source in contract["sourceArt"])
    exterior = contract["ownerPreview"]["exteriorSurround"]
    exterior_grammar = " ".join(exterior["regionalGrammar"]).lower()
    exterior_signature = exterior.get("claimSignature", exterior.get("contractSignature", []))
    assert exterior["exported"] is False
    assert exterior["radiusMeters"] == 160
    assert "cacti" in exterior_grammar and "tree" not in exterior_grammar
    assert len(exterior_signature) >= 3
    panorama_stem = PANORAMAS[key]
    panorama_mount = contract["panoramaMount"]
    panorama_contract = json.loads((SOURCE_DIR / f"{panorama_stem}-panorama-contract.json").read_text())
    assert panorama_mount == panorama_contract["mount"]
    assert panorama_mount["asset"] == f"{panorama_stem}-panorama.glb"
    assert panorama_mount["position"] == panorama_mount["rotation"] == [0.0, 0.0, 0.0]
    assert panorama_mount["scale"] == [1.0, 1.0, 1.0]
    assert panorama_mount["renderOnly"] is True
    assert "separate mounted scenery" in panorama_mount["ownership"]
    if key == "claim":
        assert contract["waterTruth"]["river"] == {"minZ": -5.0, "maxZ": 5.0}
        assert contract["waterTruth"]["shallowsWidth"] == 1.25
        assert contract["waterTruth"]["ford"] == {"minX": -3.0, "maxX": 3.0}
    elif key == "dryGulch":
        assert contract["waterTruth"] == {
            "kind": "spring_pond", "x": -18.0, "z": -18.0, "radius": 1.4,
        }
        assert contract["heightfieldTruth"]["springBasin"] == {
            "x": -18.0, "z": -18.0, "radius": 7.5, "depth": 0.68,
        }
        assert contract["heightfieldTruth"]["washes"] == [
            "southwest-arroyo", "east-mesa-wash",
        ]
    elif key == "twinBanks":
        assert contract["contractId"] == "e1-twin-banks"
        assert contract["waterTruth"] == {
            "kind": "braided_visual_river",
            "visualHalfWidth": 7.8,
            "fords": [{"x": -16.0, "halfWidth": 3.0}, {"x": 16.0, "halfWidth": 3.0}],
            "gravelBars": [{"x": -7.5, "z": 0.2}, {"x": 7.4, "z": -0.25}],
        }
    else:
        assert contract["contractId"] == extras["contract_id"]
        assert contract["waterTruth"] == {
            "river": {"minZ": -5.0, "maxZ": 5.0},
            "shallowsWidth": 1.25,
            "ford": {"minX": -3.0, "maxX": 3.0},
        }
    if key in {"twinBanks", "nightShift", "baron"}:
        assert contract["regionalFamily"]["epoch"] == "Epoch 1 frontier river county"
        assert set(contract["regionalFamily"]["unique"]) == {
            "terrain mesh", "atlas treatment", "macro silhouette", "spatial rhythm", "landmark composition",
        }
        assert contract["ownerPreview"]["exported"] is False
        assert len(contract["ownerPreview"]["landmarks"]) == 5

    return {
        "key": key,
        "tileId": tile_id,
        "blendObjects": [obj.name for obj in meshes],
        "blendCameras": len(cameras),
        "blendLights": len(lights),
        "checked": checked,
        "reexported": reexported,
        "semanticReexportIdentical": semantic_identical,
        "binaryPayloadReexportIdentical": checked_binary_sha == reexported_binary_sha,
        "binaryPayloadSha256": checked_binary_sha,
        "embeddedTexture": texture,
        "geometrySha256": geometry_sha,
        "geometryProbes": geometry_probes,
        "customSafetyExtras": extras,
    }


def verify_panorama(key, stem):
    blend = SOURCE_DIR / f"{stem}-panorama.blend"
    glb = SOURCE_DIR / f"{stem}-panorama.glb"
    atlas = SOURCE_DIR / f"{stem}-panorama-atlas.png"
    contract = json.loads((SOURCE_DIR / f"{stem}-panorama-contract.json").read_text())
    checked = verify.contract(glb)
    document, binary = glb_parts(glb)
    extras = document["nodes"][0].get("extras", {})
    texture = embedded_texture(document, binary)

    bpy.ops.wm.open_mainfile(filepath=str(blend))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    cameras = [obj for obj in bpy.data.objects if obj.type == "CAMERA"]
    lights = [obj for obj in bpy.data.objects if obj.type == "LIGHT"]
    assert len(meshes) == 1 and not cameras and not lights
    mesh_vertices = meshes[0].data.vertices
    sky_vertex_count = 5 * (192 + 1)
    ridge_row_width = 192 + 1
    ridge_foot = mesh_vertices[sky_vertex_count : sky_vertex_count + ridge_row_width]
    ridge_crest = mesh_vertices[sky_vertex_count + ridge_row_width : sky_vertex_count + ridge_row_width * 2]

    def radius_range(vertices):
        radii = [math.hypot(float(vertex.co.x), float(vertex.co.y)) for vertex in vertices]
        return [min(radii), max(radii)]

    actual_foot_range = radius_range(ridge_foot)
    actual_crest_range = radius_range(ridge_crest)
    bpy.ops.object.select_all(action="DESELECT")
    meshes[0].select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    reexport_path = Path("/tmp") / f"gold-rush-{stem}-panorama-reexport.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(reexport_path),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_materials="EXPORT",
        export_extras=True,
    )
    reexported = verify.contract(reexport_path)
    _, reexported_binary = glb_parts(reexport_path)
    semantic_keys = (
        "meshes", "primitives", "triangles", "materials", "images", "embeddedImages",
        "cameras", "lights", "animations", "bounds", "materialContract",
    )
    semantic_identical = all(checked[name] == reexported[name] for name in semantic_keys)
    binary_identical = hashlib.sha256(binary).hexdigest() == hashlib.sha256(reexported_binary).hexdigest()

    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] == contract["triangles"] == 1_920 <= 4_000
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert texture["width"] == texture["height"] == 2048
    assert texture["sha256"] == contract["files"]["atlas"]["sha256"] == hashlib.sha256(atlas.read_bytes()).hexdigest()
    assert checked["sha256"] == contract["files"]["glb"]["sha256"]
    assert hashlib.sha256(blend.read_bytes()).hexdigest() == contract["files"]["blend"]["sha256"]
    assert semantic_identical and binary_identical
    assert extras == {
        "render_only": True,
        "panorama": True,
        "affects_playfield": False,
        "affects_masks": False,
        "affects_spawn_edges": False,
        "affects_fog_gating": False,
        "mount_space": "game X/Y/Z at county origin",
        "panorama_law": "v2",
    }
    assert contract["renderOnly"] is True
    assert contract["triangleBudget"] == 4_000
    assert contract["lawVersion"] == "PANORAMA LAW v2"
    assert contract["exposure"]["mode"] == "bakedIntoAtlas"
    assert 0 < contract["exposure"]["linearMultiplier"] <= 1
    assert set(contract["namedCorrections"]) == {"paintedWall", "ceiling", "echo"}
    assert contract["projection"]["ridgeOccluderRadiusMeters"] < contract["projection"]["skyRingRadiusMeters"]
    declared_foot_range = contract["projection"]["ridgeFootRadiusRangeMeters"]
    declared_crest_range = contract["projection"]["ridgeOccluderRadiusRangeMeters"]
    assert all(abs(actual - declared) < 0.001 for actual, declared in zip(actual_foot_range, declared_foot_range))
    assert all(abs(actual - declared) < 0.001 for actual, declared in zip(actual_crest_range, declared_crest_range))
    assert contract["projection"]["skyBottomMeters"] < 0 < contract["projection"]["skyTopMeters"]
    assert contract["nonInterference"] == {
        "playfieldBounds": "unchanged",
        "spawnEdges": "unchanged",
        "fogGating": "unchanged",
        "waterBuildSpawnMasks": "unchanged",
    }
    return {
        "key": key,
        "asset": glb.name,
        "checked": checked,
        "reexported": reexported,
        "semanticReexportIdentical": semantic_identical,
        "binaryPayloadReexportIdentical": binary_identical,
        "embeddedTexture": texture,
        "customSafetyExtras": extras,
        "projectionRadiusRanges": {
            "ridgeFootMeters": actual_foot_range,
            "ridgeOccluderMeters": actual_crest_range,
        },
        "mount": contract["mount"],
    }


def main():
    assets = {key: verify_asset(key, stem, tile_id, extras) for key, stem, tile_id, extras in ASSETS}
    panoramas = {key: verify_panorama(key, stem) for key, stem in PANORAMAS.items()}
    geometry_hashes = [asset["geometrySha256"] for asset in assets.values()]
    glb_hashes = [asset["checked"]["sha256"] for asset in assets.values()]
    texture_hashes = [asset["embeddedTexture"]["sha256"] for asset in assets.values()]
    panorama_glb_hashes = [asset["checked"]["sha256"] for asset in panoramas.values()]
    panorama_texture_hashes = [asset["embeddedTexture"]["sha256"] for asset in panoramas.values()]
    assert len(set(geometry_hashes)) == len(ASSETS), "every contract must own a distinct terrain mesh"
    assert len(set(glb_hashes)) == len(ASSETS), "every contract must own a distinct GLB"
    assert len(set(texture_hashes)) == len(ASSETS), "every contract must own a distinct terrain atlas"
    assert len(set(panorama_glb_hashes)) == len(PANORAMAS), "every contract must own a distinct panorama GLB"
    assert len(set(panorama_texture_hashes)) == len(PANORAMAS), "every contract must own a distinct panorama atlas"
    evidence = {
        "blender": bpy.app.version_string,
        "assets": assets,
        "panoramas": panoramas,
        "identityChecks": {
            "uniqueGeometryHashes": len(set(geometry_hashes)),
            "uniqueGlbHashes": len(set(glb_hashes)),
            "uniqueAtlasHashes": len(set(texture_hashes)),
            "uniquePanoramaGlbHashes": len(set(panorama_glb_hashes)),
            "uniquePanoramaAtlasHashes": len(set(panorama_texture_hashes)),
        },
        "ownerEvidence": {
            name: png_evidence(name, expected_sha, expected_size, inputs)
            for name, (expected_sha, expected_size, inputs) in EVIDENCE_RENDERS.items()
        },
    }
    merge_base = subprocess.run(
        ["git", "merge-base", "HEAD", "main"], cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.strip()
    changed_src_paths = subprocess.run(
        ["git", "diff", "--name-only", merge_base, "--", "src"], cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    untracked_src_paths = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", "src"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    src_paths = sorted(set(changed_src_paths + untracked_src_paths))
    evidence["srcEdits"] = bool(src_paths)
    evidence["srcPaths"] = src_paths
    assert not src_paths
    (ARTIFACT_DIR / "verification.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
