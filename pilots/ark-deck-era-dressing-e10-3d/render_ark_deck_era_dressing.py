from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import math
import subprocess
import sys

sys.dont_write_bytecode = True

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "artifacts/ark-deck-era-dressing-e10"
RENDERS = OUT / "renders"
BASE_SHA = "d46554ffde058afca2eb7966e48ac5629300ff98"
DRESSING = HERE / "ark-deck-era-dressing-e10.glb"
PLATE = ROOT / "assets/pilots/ark-plaza-e10-3d/ark-plaza-e10.glb"
PAN = ROOT / "assets/pilots/plaza-props-3d/pan_monument.glb"

STATION_LABELS = (
    "E1 | SLUICE CRADLE + BUCKET",
    "E2 | COLD BOILER + GEAR",
    "E3 | INSULATOR FORK + WIRE",
    "E4 | TIRES + FUEL + ROAD MARKER",
    "E5 | TIDE BOARD + ROPE COIL",
    "E6 | FRIENDLY APPLIANCE PEN",
    "E7 | RELAY MAST + TAPE REELS",
    "E8 | HELMET + SURVEY DISH",
    "E9 | CANAL GATE + LIVING GREEN",
    "E10 | TEN-ERA RIBBON + CHARTER",
)


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


builder = load("ark_deck_dressing_builder_render", HERE / "build_ark_deck_era_dressing.py")
ark = load("ark_deck_dressing_plaza_render", ROOT / "assets/pilots/ark-plaza-e10-3d/render_ark_plaza.py")
ark.BASE_SHA = BASE_SHA
town = ark.town
dome_population = load("ark_deck_dressing_e8_render", ROOT / "assets/pilots/dome-population-e8/render_dome_population.py")
dome_population.BASE_SHA = BASE_SHA
basin_population = load("ark_deck_dressing_e9_render", ROOT / "assets/pilots/basin-population-e9/render_basin_population.py")
basin_population.BASE_SHA = BASE_SHA
basin_population.fresh.BASE_SHA = BASE_SHA
hall = load("ark_deck_dressing_hall_render", ROOT / "assets/pilots/ark-long-table-hall-e10-3d/render_ark_long_table_hall.py")
hall.BASE_SHA = BASE_SHA


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_dressing() -> None:
    town.import_model(DRESSING, "Production:ArkDeckEraDressingE10", town.Point(0.0, 0.0))


def setup_site(angle: float = math.pi, include_dressing: bool = True, overlay: bool = False) -> None:
    ark.setup(angle, overlay)
    if include_dressing:
        add_dressing()


def render_site(path: Path, angle: float = math.pi, include_dressing: bool = True) -> None:
    setup_site(angle, include_dressing)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def annotate(path: Path, label: str, point_size: int = 22) -> None:
    temporary = path.with_name(f".{path.name}")
    subprocess.run([
        "magick", str(path), "-font", "/System/Library/Fonts/Helvetica.ttc", "-gravity", "north",
        "-fill", "#f7df9d", "-undercolor", "#10151ddd", "-pointsize", str(point_size),
        "-annotate", "+0+8", f"{label} | base {BASE_SHA}", str(temporary),
    ], check=True)
    temporary.replace(path)


def add_clearance_envelopes() -> None:
    material = ark.material("EvidenceOnly:MemoryStationEnvelope", (0.94, 0.24, 0.12, 1.0), 2.2)
    for index in range(10):
        angle, radius, _ = builder.station_center(index)
        center = builder.point(angle, radius, 0.0, 0.0, 0.0)
        points = [
            town.Point(
                center[0] + math.sin(step / 32.0 * math.tau) * 1.30,
                center[1] + math.cos(step / 32.0 * math.tau) * 1.30,
            )
            for step in range(32)
        ]
        town.curve_object(f"EvidenceOnly:StationEnvelope:E{index + 1}", points, material, True, 0.10)


def render_clearance(path: Path) -> None:
    setup_site(math.pi, True, True)
    add_clearance_envelopes()
    camera = bpy.context.scene.camera
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 52.0
    camera.location = (0.0, 0.0, 55.0)
    town.look_at(camera, Vector((0.0, 0.0, 0.0)))
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def render_station(index: int, path: Path) -> None:
    angle, radius, _ = builder.station_center(index)
    setup_site(angle + math.pi, True)
    scene = bpy.context.scene
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    camera = scene.camera
    camera.location = (
        math.cos(angle) * 14.2,
        math.sin(angle) * 14.2,
        3.8,
    )
    center = builder.point(angle, radius, 0.0, 0.0, 0.78)
    town.look_at(camera, Vector(center))
    camera.data.lens = 60.0
    camera.data.clip_end = 120.0
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    annotate(path, STATION_LABELS[index], 14)


def render_fresh_references() -> Path:
    out = OUT / "current-references" / f"{BASE_SHA[:12]}-main"
    out.mkdir(parents=True, exist_ok=True)
    fresh = basin_population.fresh
    fresh.render_e1(out / "town-e1-current.png")
    fresh.render_e4(out / "town-e4-current.png")
    fresh.render_e5(out / "town-e5-current-underwater.png")
    fresh.render_mesa(out / "town-e6-current.png", 6)
    fresh.render_mesa(out / "town-e7-current.png", 7)
    dome_population.render_ensemble(out / "town-e8-current.png", 0.0)
    basin_population.render_ensemble(out / "town-e9-current.png", 0.0)
    render_site(out / "town-e10-current.png", math.pi, False)
    hall.render(out / "town-e10-long-table-current.png", (0.0, -24.0, 9.0), (0.0, 1.0, 2.6), 46.0)
    paths = [
        out / "town-e1-current.png", out / "town-e4-current.png", out / "town-e5-current-underwater.png",
        out / "town-e6-current.png", out / "town-e7-current.png", out / "town-e8-current.png",
        out / "town-e9-current.png", out / "town-e10-current.png", out / "town-e10-long-table-current.png",
    ]
    rows = [Path(f"/tmp/ark-deck-dressing-reference-{index}.png") for index in range(3)]
    for index, row in enumerate(rows):
        subprocess.run(["magick", *map(str, paths[index * 3:(index + 1) * 3]), "+append", str(row)], check=True)
    board = out / "town-e1-e10-current.png"
    subprocess.run(["magick", *map(str, rows), "-append", str(board)], check=True)
    annotate(board, "FRESH CURRENT-FILE REFERENCE | E1 / E4 / E5 / E6 / E7 / E8 / E9 / E10", 26)
    for row in rows:
        row.unlink(missing_ok=True)
    tracked = [
        fresh.CURRENT_PLATE, fresh.MESA_PLATE, PAN,
        *fresh.e4.E4_MODELS.values(), *fresh.e5.E5_MODELS.values(),
        *fresh.E6_MODELS.values(), *fresh.E7_MODELS.values(),
        dome_population.PLATE, *dome_population.MODELS.values(),
        basin_population.PLATE, *basin_population.MODELS.values(),
        PLATE, hall.GLB,
    ]
    tracked = list(dict.fromkeys(tracked))
    (out / "reference-contract.json").write_text(json.dumps({
        "baseSha": BASE_SHA,
        "rule": "fresh render from current main GLBs; no prior evidence PNG is an input",
        "order": ["E1 square", "E4 motor boulevard", "E5 submerged square", "E6 Atomic Mesa",
                  "E7 Signal Mesa", "E8 Dome population", "E9 Basin population",
                  "E10 Ark Plaza", "E10 Long Table Hall"],
        "assetSha256": {str(path.relative_to(ROOT)): sha256(path) for path in tracked},
        "renders": [str(path.relative_to(ROOT)) for path in [*paths, board]],
    }, indent=2) + "\n")
    return board


def assemble() -> None:
    baseline = RENDERS / "ark-deck-before-dressing.png"
    candidate = RENDERS / "ark-deck-with-era-dressing.png"
    ab = RENDERS / "ark-deck-era-dressing-ab.png"
    subprocess.run(["magick", str(baseline), str(candidate), "+append", str(ab)], check=True)
    annotate(ab, "ARK DECK | ACCEPTED PLATE / TEN MEMORY STATIONS")

    angles = [RENDERS / f"ark-deck-dressing-angle-{index}.png" for index in range(1, 5)]
    top, bottom = Path("/tmp/ark-deck-dressing-top.png"), Path("/tmp/ark-deck-dressing-bottom.png")
    subprocess.run(["magick", str(angles[0]), str(angles[1]), "+append", str(top)], check=True)
    subprocess.run(["magick", str(angles[2]), str(angles[3]), "+append", str(bottom)], check=True)
    turntable = RENDERS / "ark-deck-era-dressing-turntable.png"
    subprocess.run(["magick", str(top), str(bottom), "-append", str(turntable)], check=True)
    annotate(turntable, "ARK DECK MEMORY STATIONS | FOUR-ANGLE SITE AUDIT", 22)

    station_shots = [RENDERS / f"ark-deck-station-e{era}.png" for era in range(1, 11)]
    station_rows = [Path("/tmp/ark-deck-stations-a.png"), Path("/tmp/ark-deck-stations-b.png")]
    subprocess.run(["magick", *map(str, station_shots[:5]), "+append", str(station_rows[0])], check=True)
    subprocess.run(["magick", *map(str, station_shots[5:]), "+append", str(station_rows[1])], check=True)
    stations = RENDERS / "ark-deck-ten-era-stations.png"
    subprocess.run(["magick", *map(str, station_rows), "-append", str(stations)], check=True)

    clearance = RENDERS / "ark-deck-era-dressing-clearance.png"
    annotate(clearance, "CLEARANCE | TEAL ROUTES / AMBER PADS / RED STATION ENVELOPES", 19)

    fresh_board = render_fresh_references()
    fresh = RENDERS / "fresh-main-reference-and-ark-dressing.png"
    subprocess.run(["magick", str(fresh_board), str(candidate), "-gravity", "center", "+append", str(fresh)], check=True)
    annotate(fresh, "FRESH CURRENT-FILE REFERENCES / ARK DRESSING CANDIDATE", 26)

    tracked = [DRESSING, HERE / "ark-deck-era-dressing-e10-atlas.png", PLATE, PAN, *builder.ERA_SOURCES]
    (OUT / "ark-deck-era-dressing-visual-evidence.json").write_text(json.dumps({
        "baseSha": BASE_SHA,
        "rule": "all boards rendered from current GLBs on the freshly pulled base; no prior PNG is an input",
        "ownershipBoundary": "separate origin-aligned GLB; accepted Ark plaza and Long Table Hall remain untouched",
        "productionAssets": {str(path.relative_to(ROOT)): sha256(path) for path in tracked},
        "evidenceOnly": ["starfield", "lights", "cameras", "route/pad overlay", "red station clearance curves"],
        "renders": [str(path.relative_to(ROOT)) for path in [
            ab, turntable, stations, clearance, fresh, baseline, candidate, *angles, *station_shots,
        ]],
    }, indent=2) + "\n")
    for path in [top, bottom, *station_rows]:
        path.unlink(missing_ok=True)


def main() -> None:
    RENDERS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    targets = {
        "before": lambda: render_site(RENDERS / "ark-deck-before-dressing.png", math.pi, False),
        "after": lambda: render_site(RENDERS / "ark-deck-with-era-dressing.png", math.pi, True),
        **{f"angle{index}": (lambda index=index: render_site(
            RENDERS / f"ark-deck-dressing-angle-{index}.png", math.pi + (index - 1) * math.pi * 0.5, True,
        )) for index in range(1, 5)},
        "clearance": lambda: render_clearance(RENDERS / "ark-deck-era-dressing-clearance.png"),
        **{f"station{index + 1}": (lambda index=index: render_station(
            index, RENDERS / f"ark-deck-station-e{index + 1}.png",
        )) for index in range(10)},
    }
    if "--" in sys.argv:
        target = sys.argv[sys.argv.index("--") + 1]
        if target == "assemble":
            assemble()
        else:
            targets[target]()
        return
    for target in targets:
        subprocess.run([bpy.app.binary_path, "--background", "--python", str(Path(__file__).resolve()), "--", target], check=True)
    assemble()


if __name__ == "__main__":
    main()
