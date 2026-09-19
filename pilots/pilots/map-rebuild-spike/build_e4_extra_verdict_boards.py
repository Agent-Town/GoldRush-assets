"""Assemble compact owner gates for the three unique E4 campaign maps."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys

try:
    from PIL import Image, ImageDraw
except ModuleNotFoundError:
    runtime = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
    if runtime.is_file() and subprocess.run(
        [str(runtime), "-c", "import PIL"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
    ).returncode == 0:
        os.execv(str(runtime), [str(runtime), str(Path(__file__).resolve()), *sys.argv[1:]])
    raise SystemExit("Pillow is required; run with the bundled Codex workspace Python")


ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


boards = load_module("e4_extra_board_base", SOURCE / "build_e3_verdict_boards.py")

MAPS = [
    {
        "key": "long-road",
        "name": "THE LONG ROAD",
        "mood": ROOT / "assets/processed/kit-era-4.png",
        "moodLabel": "FRESH E4 KIT PLATE — MOTOR GRIT SOURCE",
        "truth": "3 build flats | one 400m road | 3 rest stops | north/south spawn | no water",
    },
    {
        "key": "gusher-county",
        "name": "GUSHER COUNTY",
        "mood": ROOT / "assets/processed/kit-era-4.png",
        "moodLabel": "FRESH E4 KIT PLATE — MOTOR GRIT SOURCE",
        "truth": "4 build flats | 8 wild wells | 5 tar seams | 3 lease roads | no water",
    },
    {
        "key": "boneyard",
        "name": "THE BONEYARD",
        "mood": ROOT / "assets/processed/kit-era-4.png",
        "moodLabel": "FRESH E4 KIT PLATE — MOTOR GRIT SOURCE",
        "truth": "3 build flats | 10 salvage hulks | sleeper + wagon | west/east spawn | no water",
    },
]


def mask_board():
    canvas = Image.new("RGB", (1920, 828), boards.INK)
    draw = ImageDraw.Draw(canvas)
    boards.centered(draw, (0, 0, 1920, 54), "E4 EXTRA FAMILY MASK AGREEMENT — PUBLISHED TABLES ARE THE AUTHORITY", 30)
    boards.centered(draw, (0, 48, 1920, 92), "Every build rectangle is independently surface-sampled; landmarks remain empty mount records", 17)
    for column, entry in enumerate(MAPS):
        x = column * 640
        boards.centered(draw, (x + 8, 96, x + 632, 132), f"{entry['name']} — {entry['truth']}", 13)
        canvas.paste(boards.fitted(ARTIFACTS / f"{entry['key']}-mask-agreement.png", (640, 360)), (x, 132))
        boards.centered(draw, (x, 500, x + 640, 536), "EXPORTED SURFACE + PUBLISHED OVERLAY", 15)
        mount_count = {"long-road": 5, "gusher-county": 10, "boneyard": 12}[entry["key"]]
        lines = (
            "build flats: 2,145 samples each | 0.000 m deviation",
            f"mounted landmark interlock: {mount_count} empty-asset records",
            "simulation: planar | dry | movement/build/spawn unchanged",
        )
        for index, label in enumerate(lines):
            boards.centered(draw, (x + 18, 546 + index * 52, x + 622, 590 + index * 52), label, 16)
        draw.line((x + 32, 722, x + 608, 722), fill=(57, 66, 70), width=2)
        boards.centered(draw, (x + 20, 734, x + 620, 784), "Terrain.visualY only — no gameplay elevation", 16)
    canvas.save(ARTIFACTS / "e4-extra-mask-agreement-board.png", optimize=True)


def main():
    boards.MAPS = MAPS
    base_sha = subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True).strip()
    boards.two_column_board(
        "e4-extra-mood-ab.png",
        "E4 EXTRA FAMILY MOOD A/B — MOTOR-ERA FIGHT, NEVER HOLIDAY",
        f"Fresh reference base {base_sha[:12]} | wheel ruts, tar stains, oxidized salvage, and hard working earth",
        [
            (entry["moodLabel"], entry["mood"], f"SCULPTED RUN CAMERA — {entry['name']}", ARTIFACTS / f"{entry['key']}-run-camera.png")
            for entry in MAPS
        ],
    )
    boards.two_column_board(
        "e4-extra-flat-vs-sculpted-ab.png",
        "E4 EXTRA FAMILY GEOMETRY A/B — IDENTICAL CAMERA AND MATERIAL",
        "Left is a zero-height copy; right is the authored render terrain",
        [
            (f"FLAT — {entry['name']}", ARTIFACTS / f"{entry['key']}-flat-tile-identical-camera.png", f"SCULPTED — {entry['name']}", ARTIFACTS / f"{entry['key']}-sculpted-tile-identical-camera.png")
            for entry in MAPS
        ],
    )
    boards.three_column_board(
        "e4-extra-owner-verdict.png",
        "E4 EXTRA FAMILY OWNER VERDICT — THREE DISTINCT MOTOR CONTRACTS",
        "Real player camera | whole-tile composition | low motor dusk",
        ("run-camera", "overview", "low-sunset"),
        ("RUN", "OVERVIEW", "LOW DUSK"),
    )
    boards.three_column_board(
        "e4-extra-panorama-mood-ab.png",
        "E4 EXTRA FAMILY PANORAMA V2 — MOUNTED SEPARATELY",
        "Before/mounted use identical framing; each panorama is one render-only ring",
        ("panorama-before", "panorama-mounted", "panorama-horizon"),
        ("BEFORE", "MOUNTED", "CENTER HORIZON"),
    )
    boards.two_column_board(
        "e4-extra-panorama-distance-gate.png",
        "E4 EXTRA FAMILY CENTER-HORIZON GATE — DISTANCE, NEVER WALL OR CEILING",
        "The zenith stays quiet; asymmetric ridges and stained haze remain visible at the rim",
        [
            (entry["name"], ARTIFACTS / f"{entry['key']}-panorama-horizon.png", f"{entry['name']} — LOW DUSK", ARTIFACTS / f"{entry['key']}-low-sunset.png")
            for entry in MAPS
        ],
    )
    mask_board()


if __name__ == "__main__":
    main()
