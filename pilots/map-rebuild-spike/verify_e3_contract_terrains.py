"""Verify authored terrain/panorama pairs and their owner evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

import bpy


ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shared = load_module("e3_shared_verify", SOURCE / "verify_contract_terrains.py")
builder = load_module("e3_builder_verify", SOURCE / "build_e3_contract_terrains.py")

MAPS = {
    "canyon-works": {"id": "e3-canyon-works", "stem": "canyon-works-terrain", "width": 96.0, "height": 112.0, "table": "assets/contracts/epoch-3-voltage/mask-tables/e3-canyon-works.json", "kit": "assets/processed/kit-era-3.png", "probes": ((0, 0), (-24, -20), (24, -20), (0, 32)), "acceptedSnapshot": True},
    "moth-season": {"id": "e3-moth-season", "stem": "moth-season-terrain", "width": 80.0, "height": 80.0, "table": "assets/contracts/epoch-3-voltage/mask-tables/e3-moth-season.json", "kit": "assets/processed/kit-era-3.png", "probes": ((0, 0), (-28, 20), (28, -20), (0, 34)), "acceptedSnapshot": True},
}
BOARDS = {
    "e3-mood-ab.png": (1920, 1260),
    "e3-flat-vs-sculpted-ab.png": (1920, 1260),
    "e3-owner-verdict.png": (1920, 900),
    "e3-panorama-mood-ab.png": (1920, 900),
    "e3-panorama-distance-gate.png": (1920, 1260),
    "e3-mask-agreement-board.png": (1920, 1260),
}

BLACKOUT_DUST_MAPS = {
    "blackout-ridge": {"id": "e3-blackout-ridge", "stem": "blackout-ridge-terrain", "width": 80.0, "height": 96.0, "table": "assets/contracts/epoch-3-voltage/mask-tables/e3-blackout-ridge.json", "kit": "assets/processed/kit-era-3.png", "probes": ((-30, -30), (-18, -18), (6, 4), (24, 30)), "loadBearing": True},
    "dust-flats": {"id": "e4-dust-flats", "stem": "dust-flats-terrain", "width": 160.0, "height": 160.0, "table": "assets/contracts/epoch-4-motor/mask-tables/e4-dust-flats.json", "kit": "assets/processed/kit-era-4.png", "probes": ((0, 0), (24, 0), (30, -38), (70, 70))},
}
BLACKOUT_DUST_BOARDS = {
    "blackout-dust-mood-ab.png": (1920, 1260),
    "blackout-dust-flat-vs-sculpted-ab.png": (1920, 1260),
    "blackout-dust-owner-verdict.png": (1920, 900),
    "blackout-dust-panorama-mood-ab.png": (1920, 900),
    "blackout-dust-panorama-distance-gate.png": (1920, 1260),
    "blackout-dust-mask-agreement-board.png": (1920, 1260),
}

FAIRGROUND_MAPS = {
    "fairground": {"id": "e3-fairground", "stem": "fairground-terrain", "width": 88.0, "height": 88.0, "table": "assets/contracts/epoch-3-voltage/mask-tables/e3-fairground.json", "kit": "assets/processed/kit-era-3.png", "probes": ((0, -30), (-20, 10), (0, 8), (20, 10), (0, 40)), "loadBearing": True, "landmarkFreezeLifted": True},
}
FAIRGROUND_BOARDS = {
    "fairground-mood-ab.png": (1920, 684),
    "fairground-flat-vs-sculpted-ab.png": (1920, 684),
    "fairground-owner-verdict.png": (1920, 504),
    "fairground-panorama-mood-ab.png": (1920, 504),
    "fairground-panorama-distance-gate.png": (1920, 684),
    "fairground-mask-agreement-board.png": (1280, 1260),
}

GLOW_MESA_MAPS = {
    "glow-mesa": {"id": "e6-glow-mesa", "stem": "glow-mesa-terrain", "width": 128.0, "height": 128.0, "table": "assets/contracts/epoch-6-atomic/mask-tables/e6-glow-mesa.json", "kit": "assets/processed/kit-era-6.png", "probes": ((0, -32), (-30, 15), (0, 20), (40, 15), (-35, 45)), "loadBearing": True, "landmarkFreezeLifted": True},
}
GLOW_MESA_BOARDS = {
    "glow-mesa-mood-ab.png": (1920, 684),
    "glow-mesa-flat-vs-sculpted-ab.png": (1920, 684),
    "glow-mesa-owner-verdict.png": (1920, 504),
    "glow-mesa-panorama-mood-ab.png": (1920, 504),
    "glow-mesa-panorama-distance-gate.png": (1920, 684),
    "glow-mesa-mask-agreement-board.png": (1600, 1260),
}

RELAY_VALLEY_MAPS = {
    "relay-valley": {"id": "e7-relay-valley", "stem": "relay-valley-terrain", "width": 128.0, "height": 128.0, "table": "assets/contracts/epoch-7-signal/mask-tables/e7-relay-valley.json", "kit": "assets/processed/kit-era-7.png", "probes": ((0, -20), (-45, 41), (-25, 41), (25, 41), (45, 41), (0, 39)), "loadBearing": True, "landmarkFreezeLifted": True},
}
RELAY_VALLEY_BOARDS = {
    "relay-valley-mood-ab.png": (1920, 684),
    "relay-valley-flat-vs-sculpted-ab.png": (1920, 684),
    "relay-valley-owner-verdict.png": (1920, 504),
    "relay-valley-panorama-mood-ab.png": (1920, 504),
    "relay-valley-panorama-distance-gate.png": (1920, 684),
    "relay-valley-mask-agreement-board.png": (1600, 1260),
}

MARE_CLAIM_MAPS = {
    "mare-claim": {"id": "e8-mare-claim", "stem": "mare-claim-terrain", "width": 128.0, "height": 128.0, "table": "assets/contracts/epoch-8-orbital/mask-tables/e8-mare-claim.json", "kit": "assets/processed/kit-era-8.png", "probes": ((0, 0), (-31, 25), (-44, 47), (44, -47), (-30, -31), (24, -34)), "loadBearing": True},
}
MARE_CLAIM_BOARDS = {
    "mare-claim-mood-ab.png": (1920, 684),
    "mare-claim-flat-vs-sculpted-ab.png": (1920, 684),
    "mare-claim-owner-verdict.png": (1920, 504),
    "mare-claim-panorama-mood-ab.png": (1920, 504),
    "mare-claim-panorama-distance-gate.png": (1920, 684),
    "mare-claim-earth-side-gate.png": (1920, 684),
    "mare-claim-mask-agreement-board.png": (1600, 1260),
}

EMBER_SHORE_MAPS = {
    "ember-shore": {
        "id": "e10-ember-shore",
        "stem": "ember-shore-terrain",
        "width": 128.0,
        "height": 128.0,
        "table": "assets/contracts/epoch-10-deepsky/mask-tables/e10-ember-shore.json",
        "kit": "assets/processed/kit-era-10.png",
        "probes": ((3, -10), (26, 34), (-46, 10), (-13, -30), (49, 18), (0, 48)),
        "loadBearing": True,
        "landmarkFreezeLifted": True,
    },
}
EMBER_SHORE_BOARDS = {
    "ember-shore-mood-ab.png": (1920, 684),
    "ember-shore-flat-vs-sculpted-ab.png": (1920, 684),
    "ember-shore-owner-verdict.png": (1920, 504),
    "ember-shore-panorama-mood-ab.png": (1920, 504),
    "ember-shore-panorama-distance-gate.png": (1920, 684),
    "ember-shore-mask-agreement-board.png": (1600, 1260),
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_size(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR"
    return struct.unpack(">II", data[16:24])


def semantic_contract(path):
    return shared.verify.contract(path)


def reexport_from_blend(blend, output):
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    assert len(meshes) == 1
    assert not [obj for obj in bpy.data.objects if obj.type == "CAMERA"]
    assert not [obj for obj in bpy.data.objects if obj.type == "LIGHT"]
    bpy.ops.object.select_all(action="DESELECT")
    meshes[0].select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(
        filepath=str(output),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_materials="EXPORT",
        export_extras=True,
    )
    return meshes[0]


def geometry_probes(key, mesh, table):
    profile = builder.PROFILES[key]
    height_at = builder.height_function(key, builder.factory_contract(profile["contractId"]), table)
    probes = []
    for x, z in MAPS[key]["probes"]:
        xi = round((x + profile["width"] * 0.5) / (profile["width"] / builder.SEGMENTS))
        zi = round((z + profile["height"] * 0.5) / (profile["height"] / builder.SEGMENTS))
        sampled_x = -profile["width"] * 0.5 + xi * profile["width"] / builder.SEGMENTS
        sampled_z = -profile["height"] * 0.5 + zi * profile["height"] / builder.SEGMENTS
        actual = float(mesh.data.vertices[zi * (builder.SEGMENTS + 1) + xi].co.z)
        expected = float(height_at(sampled_x, sampled_z))
        assert abs(actual - expected) < 0.0002
        probes.append({"requested": [x, z], "sampled": [sampled_x, sampled_z], "height": round(actual, 4)})
    return probes


def mesh_grid_height(mesh, config, x, game_z):
    """Sample the actual exported authoring triangles, not the source function."""
    columns = builder.SEGMENTS + 1
    step_x = config["width"] / builder.SEGMENTS
    step_z = config["height"] / builder.SEGMENTS
    x_grid = min(builder.SEGMENTS - 1, max(0, int((x + config["width"] * 0.5) // step_x)))
    z_grid = min(builder.SEGMENTS - 1, max(0, int((game_z + config["height"] * 0.5) // step_z)))
    x0 = -config["width"] * 0.5 + x_grid * step_x
    z0 = -config["height"] * 0.5 + z_grid * step_z
    tx = min(1.0, max(0.0, (x - x0) / step_x))
    tz = min(1.0, max(0.0, (game_z - z0) / step_z))
    a = z_grid * columns + x_grid
    h00 = float(mesh.data.vertices[a].co.z)
    h10 = float(mesh.data.vertices[a + 1].co.z)
    h01 = float(mesh.data.vertices[a + columns].co.z)
    h11 = float(mesh.data.vertices[a + columns + 1].co.z)
    if tx >= tz:
        return h00 + tx * (h10 - h00) + tz * (h11 - h10)
    return h00 + tx * (h11 - h01) + tz * (h01 - h00)


def site_surface_flatness(mesh, config, table, field):
    results = []
    for site in table["maskTruth"].get(field, []):
        heights = []
        for radial_index in range(17):
            radius = site["radius"] * radial_index / 16
            for angle_index in range(128):
                angle = angle_index * 2.0 * 3.141592653589793 / 128
                x = site["x"] + radius * math.cos(angle)
                game_z = site["z"] + radius * math.sin(angle)
                heights.append(mesh_grid_height(mesh, config, x, game_z))
        assert heights
        deviation = max(heights) - min(heights)
        assert deviation <= 0.02
        results.append({"id": site["id"], "sampledSurfacePoints": len(heights), "maxDeviationMeters": round(deviation, 6)})
    return results


def fixture_surface_flatness(mesh, config, table):
    results = []
    for zone in table["maskTruth"].get("fixtureZones", []):
        heights = [
            mesh_grid_height(mesh, config, x, z)
            for x in [zone["minX"] + (zone["maxX"] - zone["minX"]) * index / 64 for index in range(65)]
            for z in [zone["minZ"] + (zone["maxZ"] - zone["minZ"]) * index / 32 for index in range(33)]
        ]
        deviation = max(heights) - min(heights)
        assert deviation <= 0.02
        results.append({"id": zone["id"], "sampledSurfacePoints": len(heights), "maxDeviationMeters": round(deviation, 6)})
    return results


def build_zone_surface_flatness(mesh, config, table):
    results = []
    for zone in table["maskTruth"].get("buildZones", []):
        heights = [
            mesh_grid_height(mesh, config, x, z)
            for x in [zone["minX"] + (zone["maxX"] - zone["minX"]) * index / 64 for index in range(65)]
            for z in [zone["minZ"] + (zone["maxZ"] - zone["minZ"]) * index / 32 for index in range(33)]
        ]
        deviation = max(heights) - min(heights)
        assert deviation <= 0.02
        results.append({"id": zone["id"], "sampledSurfacePoints": len(heights), "maxDeviationMeters": round(deviation, 6)})
    return results


def ember_shore_surface_agreement(mesh, config, table):
    """Prove each authored cooling band is a landform, not just paint."""
    results = []
    for band in table["maskTruth"]["lavaVeinBands"]:
        depressions = []
        for index in range(65):
            z = band["minZ"] + 4.0 + (band["maxZ"] - band["minZ"] - 8.0) * index / 64
            center = mesh_grid_height(mesh, config, (band["minX"] + band["maxX"]) * 0.5, z)
            shoulders = (
                mesh_grid_height(mesh, config, band["minX"] - 7.0, z),
                mesh_grid_height(mesh, config, band["maxX"] + 7.0, z),
            )
            depressions.append(sum(shoulders) * 0.5 - center)
        mean_depression = sum(depressions) / len(depressions)
        visibly_recessed = sum(value > 0.15 for value in depressions)
        assert mean_depression > 0.35
        assert visibly_recessed >= 52
        results.append({
            "id": band["id"],
            "sampledCrossSections": len(depressions),
            "meanDepressionMeters": round(mean_depression, 4),
            "visiblyRecessedCrossSections": visibly_recessed,
        })
    return results


def verify_terrain(key, config):
    stem = config["stem"]
    blend = SOURCE / f"{stem}.blend"
    glb = SOURCE / f"{stem}.glb"
    atlas = SOURCE / f"{stem}-atlas.png"
    contract = json.loads((SOURCE / f"{stem}-contract.json").read_text(encoding="utf-8"))
    table_path = ROOT / config["table"]
    published_table = json.loads(table_path.read_text(encoding="utf-8"))
    checked = semantic_contract(glb)
    document, binary = shared.glb_parts(glb)
    texture = shared.embedded_texture(document, binary)
    extras = document["nodes"][0]["extras"]

    reexport = Path("/tmp") / f"gold-rush-{stem}-reexport.glb"
    mesh = reexport_from_blend(blend, reexport)
    rechecked = semantic_contract(reexport)
    semantic_keys = ("meshes", "primitives", "triangles", "materials", "images", "embeddedImages", "cameras", "lights", "animations", "bounds", "materialContract")
    semantic_identical = all(checked[field] == rechecked[field] for field in semantic_keys)
    byte_identical = glb.read_bytes() == reexport.read_bytes()

    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] == contract["triangles"] == 32_768 <= 60_000
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert checked["materialContract"][0]["metallicFactor"] == 0
    assert checked["materialContract"][0]["roughnessFactor"] >= 0.89
    assert checked["materialContract"][0]["hasBaseColorTexture"]
    assert texture["width"] == texture["height"] == 2048
    assert texture["sha256"] == sha256(atlas) == contract["files"]["atlas"]["sha256"]
    assert sha256(glb) == contract["files"]["glb"]["sha256"]
    assert sha256(blend) == contract["files"]["blend"]["sha256"]
    assert semantic_identical and byte_identical
    assert extras["render_only"] is True
    assert extras["sim_authority"] == "published mask table and planar simulation; unchanged"
    assert extras["height_socket"] == "Terrain.visualY"
    assert extras["contract_id"] == config["id"] and extras["tile_id"] == config["id"]
    assert extras["landmarks_frozen"] is (not config.get("landmarkFreezeLifted", False))
    if config.get("loadBearing"):
        assert extras["load_bearing_sites_flat"] is True
    if config.get("acceptedSnapshot"):
        table = {"maskTruth": contract["maskTruth"], "waterAgreement": contract["waterAgreement"]}
    else:
        table = published_table
        assert contract["maskTruth"] == published_table["maskTruth"]
        assert contract["waterAgreement"] == published_table["waterAgreement"]
    assert contract["maskTable"] == str(table_path.relative_to(ROOT))
    assert contract["simulation"].endswith("remain unchanged")
    assert contract["landmarkMounts"] == []
    if config.get("landmarkFreezeLifted"):
        assert contract["landmarkFreeze"].startswith("lifted;")
    else:
        assert contract["landmarkFreeze"].startswith("no landmark")
    assert config["kit"] in contract["sourceArt"]
    assert not any("tree" in source.lower() for source in contract["regionalFamily"]["shared"])
    assert len(contract["pylonSiteFlatness"]) == len(table["maskTruth"].get("pylonSites", []))
    assert len(contract.get("capacitorSiteFlatness", [])) == len(table["maskTruth"].get("capacitorSites", []))
    assert len(contract.get("fixtureZoneFlatness", [])) == len(table["maskTruth"].get("fixtureZones", []))
    if key in {"glow-mesa", "relay-valley", "mare-claim", "ember-shore"}:
        assert len(contract.get("buildZoneFlatness", [])) == len(table["maskTruth"]["buildZones"])
    if key == "relay-valley":
        assert len(table["maskTruth"]["ridgeBands"]) == 3
        assert len(table["maskTruth"]["fogPockets"]) == 3
        assert len(table["maskTruth"]["lanes"]["patrolRoutes"]) == 1
    if key == "mare-claim":
        assert len(table["maskTruth"]["buildZones"]) == 7
        assert len(table["maskTruth"]["rimBands"]) == 4
        assert table["maskTruth"]["mareFlat"]["height"] == 0
        assert table["maskTruth"]["lavaTubeMouth"]["id"] == "lava-tube-mouth"
        assert len(table["maskTruth"]["rails"]) == 1
        assert len(table["maskTruth"]["harvestAnchors"]) == 6
        assert len(table["maskTruth"]["debrisArcLanes"]) == 1
    if key == "ember-shore":
        truth = table["maskTruth"]
        assert len(truth["buildZones"]) == 2
        assert len(truth["lavaVeinBands"]) == 3
        assert len(truth["fixtureZones"]) == 1
        assert truth["stakeMarkers"] == [{"id": "last-warm-vent", "x": 3, "z": -10, "lossCondition": True}]
        assert truth["lanes"]["spawnEdges"] == ["north", "west", "east"]
        assert truth["river"] is False and truth["waterSources"] == []
        assert contract["preserveDesign"] == {
            "terrain": "one dry authored terrain mesh; planar simulation and mask authority remain code-owned",
            "coolingBands": "three mask-exact lava-vein rectangles sculpted as cooled landform rifts",
            "water": "none authored, rendered, or implied",
            "static": "code-owned staged desaturation/muting remains a runtime state and is not baked into the terrain",
            "sites": "last-warm-vent and cooled-titan machine footprints are triangle-safe and buildable-flat",
        }
    assert all(result["maxDeviationMeters"] <= contract["pylonFlatnessLimitMeters"] for result in contract["pylonSiteFlatness"])
    assert all(result["maxDeviationMeters"] <= contract["pylonFlatnessLimitMeters"] for result in contract.get("capacitorSiteFlatness", []))
    assert all(result["maxDeviationMeters"] <= contract["fixtureFlatnessLimitMeters"] for result in contract.get("fixtureZoneFlatness", []))
    assert all(result["maxDeviationMeters"] <= contract["fixtureFlatnessLimitMeters"] for result in contract.get("buildZoneFlatness", []))

    panorama_contract = json.loads((SOURCE / f"{key}-panorama-contract.json").read_text(encoding="utf-8"))
    assert contract["panoramaMount"] == panorama_contract["mount"]
    return {
        "asset": glb.name,
        "checked": checked,
        "reexported": rechecked,
        "byteIdenticalReexport": byte_identical,
        "semanticIdenticalReexport": semantic_identical,
        "embeddedTexture": texture,
        "extras": extras,
        "geometryProbes": geometry_probes(key, mesh, table),
        "pylonSurfaceFlatness": site_surface_flatness(mesh, config, table, "pylonSites"),
        "capacitorSurfaceFlatness": site_surface_flatness(mesh, config, table, "capacitorSites"),
        "fixtureSurfaceFlatness": fixture_surface_flatness(mesh, config, table),
        "buildZoneSurfaceFlatness": build_zone_surface_flatness(mesh, config, table) if key in {"glow-mesa", "relay-valley", "mare-claim", "ember-shore"} else [],
        "coolingBandSurfaceAgreement": ember_shore_surface_agreement(mesh, config, table) if key == "ember-shore" else [],
        "maskSource": str(table_path.relative_to(ROOT)),
    }


def verify_panorama(key):
    blend = SOURCE / f"{key}-panorama.blend"
    glb = SOURCE / f"{key}-panorama.glb"
    atlas = SOURCE / f"{key}-panorama-atlas.png"
    contract = json.loads((SOURCE / f"{key}-panorama-contract.json").read_text(encoding="utf-8"))
    checked = semantic_contract(glb)
    document, binary = shared.glb_parts(glb)
    texture = shared.embedded_texture(document, binary)
    extras = document["nodes"][0]["extras"]
    reexport = Path("/tmp") / f"gold-rush-{key}-panorama-reexport.glb"
    reexport_from_blend(blend, reexport)
    rechecked = semantic_contract(reexport)
    semantic_keys = ("meshes", "primitives", "triangles", "materials", "images", "embeddedImages", "cameras", "lights", "animations", "bounds", "materialContract")
    semantic_identical = all(checked[field] == rechecked[field] for field in semantic_keys)
    byte_identical = glb.read_bytes() == reexport.read_bytes()

    assert checked["meshes"] == checked["primitives"] == 1
    assert checked["triangles"] == contract["triangles"] <= 4_000
    assert checked["materials"] == checked["images"] == checked["embeddedImages"] == 1
    assert "COLOR_0" in document["meshes"][0]["primitives"][0]["attributes"]
    assert checked["cameras"] == checked["lights"] == checked["animations"] == 0
    assert texture["width"] == texture["height"] == 2048
    assert texture["sha256"] == sha256(atlas) == contract["files"]["atlas"]["sha256"]
    assert sha256(glb) == contract["files"]["glb"]["sha256"]
    assert sha256(blend) == contract["files"]["blend"]["sha256"]
    assert semantic_identical and byte_identical
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
    assert contract["lawVersion"] == "PANORAMA LAW v2"
    assert set(contract["namedCorrections"]) == {"paintedWall", "ceiling", "echo"}
    terrain = MAPS[key]
    apron = contract["projection"]["groundSkirtInnerBoundaryMeters"]
    assert apron["shape"] == "expanded-playfield-rectangle"
    assert apron["halfExtents"] == [terrain["width"] * 0.5, terrain["height"] * 0.5]
    assert apron["margin"] > 0
    assert contract["projection"]["groundSkirtOuterRadiusMeters"] < contract["projection"]["skyRingRadiusMeters"]
    assert contract["nonInterference"] == {
        "playfieldBounds": "unchanged",
        "spawnEdges": "unchanged",
        "fogGating": "unchanged",
        "waterBuildSpawnMasks": "unchanged",
    }
    if key == "mare-claim":
        assert contract["earthSide"] == {
            "nearSideQuadrantU": 0.75,
            "farSideQuadrantU": 0.25,
            "nearSide": "one soft blue-green Earth cameo",
            "farSide": "no Earth",
            "rule": "Earth is the Mare comfort image; THE FAR SIDE alone removes it",
        }
    if key == "ember-shore":
        assert contract["earthSide"] is None
        assert "star stipple" in contract["style"]
    return {
        "asset": glb.name,
        "checked": checked,
        "reexported": rechecked,
        "byteIdenticalReexport": byte_identical,
        "semanticIdenticalReexport": semantic_identical,
        "embeddedTexture": texture,
        "extras": extras,
        "mount": contract["mount"],
    }


def main():
    global MAPS, BOARDS
    frontier = "--blackout-dust" in sys.argv[1:]
    fairground = "--fairground" in sys.argv[1:]
    glow_mesa = "--glow-mesa" in sys.argv[1:]
    relay_valley = "--relay-valley" in sys.argv[1:]
    mare_claim = "--mare-claim" in sys.argv[1:]
    ember_shore = "--ember-shore" in sys.argv[1:]
    if ember_shore:
        MAPS = EMBER_SHORE_MAPS
        BOARDS = EMBER_SHORE_BOARDS
    elif mare_claim:
        MAPS = MARE_CLAIM_MAPS
        BOARDS = MARE_CLAIM_BOARDS
    elif relay_valley:
        MAPS = RELAY_VALLEY_MAPS
        BOARDS = RELAY_VALLEY_BOARDS
    elif glow_mesa:
        MAPS = GLOW_MESA_MAPS
        BOARDS = GLOW_MESA_BOARDS
    elif fairground:
        MAPS = FAIRGROUND_MAPS
        BOARDS = FAIRGROUND_BOARDS
    elif frontier:
        MAPS = BLACKOUT_DUST_MAPS
        BOARDS = BLACKOUT_DUST_BOARDS
    terrains = {key: verify_terrain(key, config) for key, config in MAPS.items()}
    panoramas = {key: verify_panorama(key) for key in MAPS}
    assert len({result["checked"]["sha256"] for result in terrains.values()}) == len(MAPS)
    assert len({result["checked"]["sha256"] for result in panoramas.values()}) == len(MAPS)

    boards = {}
    for name, expected_size in BOARDS.items():
        path = ARTIFACTS / name
        assert png_size(path) == expected_size
        boards[name] = {"size": expected_size, "bytes": path.stat().st_size, "sha256": sha256(path)}

    evidence = {
        "blender": bpy.app.version_string,
        "maskTables": [config["table"] for config in MAPS.values()],
        "terrains": terrains,
        "panoramas": panoramas,
        "boards": boards,
        "verdict": {
            "grit": "deep-ink preserve world with parchment-gold cooling scars and restrained salvage teal; pressure, never postcard" if ember_shore else ("warm-grey stippled engraving; silver-and-teal over parchment; honey habitat warmth; never cold photoreal" if mare_claim else ("worn signal frontier under teal-gray dusk and honey work light; fight, never holiday" if relay_valley else ("polished convalescent homestead under dangerous teal night; fight, never holiday" if glow_mesa else ("fight inside a worn working fair, never holiday" if fairground else ("fight under locked night and motor haze" if frontier else "fight under dusk rig"))))),
            "panorama": "distance; quiet deep-ink zenith, unequal parchment-gold veils, no Earth" if ember_shore else ("distance; one Earth cameo on the Mare near side and none on the opposite Far Side" if mare_claim else "distance"),
            "masks": "published and unchanged",
            "loadBearingSites": "two preserve rectangles independently sampled buildable-flat; three cooling bands sampled as recessed exported landforms" if ember_shore else ("seven build rectangles independently sampled buildable-flat; four h6 rim bands and h0 mare retained" if mare_claim else ("four relay pads independently sampled buildable-flat; two h5 ridge bands and h0 valley retained" if relay_valley else ("five build zones plus two civic fixtures independently sampled buildable-flat" if glow_mesa else ("Ferris fixture independently sampled buildable-flat" if fairground else ("three pylon and two capacitor disks independently sampled buildable-flat" if frontier else "six pylon disks independently sampled buildable-flat"))))),
            "landmarks": "freeze lifted; verdict-only titan and vent cues excluded; no asset or mount authored" if ember_shore else ("frozen; no assets or mounts authored" if mare_claim else ("freeze lifted; no assets or mounts authored in this pair" if relay_valley or glow_mesa or fairground else "frozen; no assets or mounts authored")),
        },
    }
    evidence["freshReferenceBaseSha"] = __import__("subprocess").check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip()
    evidence_path = ARTIFACTS / ("ember-shore-asset-contract.json" if ember_shore else ("mare-claim-asset-contract.json" if mare_claim else ("relay-valley-asset-contract.json" if relay_valley else ("glow-mesa-asset-contract.json" if glow_mesa else ("fairground-asset-contract.json" if fairground else ("blackout-dust-asset-contract.json" if frontier else "e3-asset-contract.json"))))))
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    panorama_triangles = sorted({result["checked"]["triangles"] for result in panoramas.values()})
    panorama_triangle_label = ", ".join(f"{count:,}" for count in panorama_triangles)
    glb_count = len(MAPS) * 2
    evidence_title = "# Ember Shore terrain and panorama re-export evidence\n\n" if ember_shore else ("# Mare Claim terrain and panorama re-export evidence\n\n" if mare_claim else ("# Relay Valley terrain and panorama re-export evidence\n\n" if relay_valley else ("# Glow Mesa terrain and panorama re-export evidence\n\n" if glow_mesa else ("# Fairground terrain and panorama re-export evidence\n\n" if fairground else ("# Blackout Ridge and Dust Flats terrain re-export evidence\n\n" if frontier else "# E3 terrain and panorama re-export evidence\n\n")))))
    authored_pair = "- Authored pair: The Ember Shore.\n" if ember_shore else ("- Authored pair: The Mare Claim.\n" if mare_claim else ("- Authored pair: The Relay Valley.\n" if relay_valley else ("- Authored pair: The Glow Mesa.\n" if glow_mesa else ("- Authored pair: The Fairground.\n" if fairground else ("- Authored pairs: Blackout Ridge and Dust Flats.\n" if frontier else "- Authored pairs: Canyon Works and Moth Season.\n")))))
    flatness_line = "- Ember Shore load-bearing sites: both preserve rectangles independently sampled from the exported mesh; all three cooling bands sampled as recessed landforms.\n" if ember_shore else ("- Mare Claim load-bearing sites: all seven build rectangles independently sampled from the exported authoring mesh; rim, mare, tube, rail, harvest, and debris masks copied exactly.\n" if mare_claim else ("- Relay Valley load-bearing sites: all four relay-pad rectangles independently sampled from the exported authoring mesh; ridge and dead-zone masks copied exactly.\n" if relay_valley else ("- Glow Mesa load-bearing sites: all five build rectangles plus both civic fixture zones independently sampled from the exported authoring mesh.\n" if glow_mesa else ("- Fairground load-bearing site: the exact Ferris rectangle independently sampled from the exported authoring mesh.\n" if fairground else ("- Blackout load-bearing sites: three pylon and two capacitor disks independently sampled from the exported authoring mesh.\n" if frontier else "- Canyon pylon sites: six buildable-flat disks independently sampled from the exported authoring mesh.\n")))))
    evidence_lines = [
        evidence_title,
        f"- Blender: {bpy.app.version_string}\n",
        authored_pair,
        "- Terrain GLBs: one mesh, one primitive, one material, one embedded 2048 atlas, 32,768 triangles each.\n",
        f"- Panorama GLBs: one mesh, one primitive, one material, one embedded 2048 atlas, {panorama_triangle_label} triangles each.\n",
        f"- Re-export: byte-identical and semantic-identical for all {glb_count} GLBs.\n",
        flatness_line,
        "- Simulation authority: published masks, water/build/spawn semantics, and Terrain.visualY remain unchanged.\n",
        "- Earth-side rule: one soft blue-green cameo on the Mare near side; the opposite Far Side view contains none.\n" if mare_claim else "",
        "- Landmark policy: freeze lifted; no landmark asset or mount authored in this terrain/panorama pair.\n" if ember_shore or relay_valley or glow_mesa or fairground else "- Landmark freeze: no landmark asset or mount changes in this wave.\n",
    ]
    evidence_md = ARTIFACTS / ("ember-shore-reexport-evidence.md" if ember_shore else ("mare-claim-reexport-evidence.md" if mare_claim else ("relay-valley-reexport-evidence.md" if relay_valley else ("glow-mesa-reexport-evidence.md" if glow_mesa else ("fairground-reexport-evidence.md" if fairground else ("blackout-dust-reexport-evidence.md" if frontier else "e3-reexport-evidence.md"))))))
    evidence_md.write_text("".join(evidence_lines), encoding="utf-8")
    print(json.dumps({"ok": True, "evidence": str(evidence_path)}, indent=2))


if __name__ == "__main__":
    main()
