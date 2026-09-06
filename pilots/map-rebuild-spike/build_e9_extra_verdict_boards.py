"""Assemble the compact owner gates for the E9 campaign extras."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys

try:
    from PIL import Image, ImageDraw  # noqa: F401
except ModuleNotFoundError:
    runtime = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
    if runtime.is_file() and subprocess.run(
        [str(runtime), "-c", "import PIL"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0:
        os.execv(str(runtime), [str(runtime), str(Path(__file__).resolve()), *sys.argv[1:]])
    raise SystemExit("Pillow is required; run with the bundled Codex workspace Python")


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


boards = load_module("e9_extra_board_helpers", OUT / "build_e3_verdict_boards.py")
boards.MAPS = [
    {
        "key": "seed-run",
        "name": "SEED RUN",
        "mood": ROOT / "assets/processed/kit-era-9.png",
        "moodLabel": "E9 KIT PLATE — REDFIELDS PALETTE SOURCE",
        "truth": "5 exact flats | 3 green waypoints | rising caravan road | dry and planar",
    },
    {
        "key": "devils-alley",
        "name": "DEVIL'S ALLEY",
        "mood": ROOT / "assets/raw/plate-e9-enemy-dust-devil.png",
        "moodLabel": "DUST-DEVIL PLATE — WIND-CORRIDOR SOURCE",
        "truth": "5 exact flats | 3 wind corridors | 3 anchor sites | dry and planar",
    },
    {
        "key": "old-canal",
        "name": "OLD CANAL",
        "mood": ROOT / "assets/raw/plate-e9-bld-canal-works.png",
        "moodLabel": "CANAL-WORKS PLATE — WRONG-SURVEY SOURCE",
        "truth": "5 exact flats | crooked inherited canal | water/persistence code-owned",
    },
]


def build_mask_board():
    width, row_height = 1280, 756
    canvas = Image.new("RGB", (width, 108 + row_height * len(boards.MAPS)), boards.INK)
    draw = ImageDraw.Draw(canvas)
    boards.centered(draw, (0, 0, width, 54), "E9 CAMPAIGN EXTRAS MASK AGREEMENT — PUBLISHED TABLES ARE THE AUTHORITY", 26)
    boards.centered(draw, (0, 48, width, 92), "Teal = exact build flats | rust/gold = authored route or hazard truth | simulation stays planar", 16)
    y = 104
    for entry in boards.MAPS:
        boards.centered(draw, (0, y, width, y + 36), f"{entry['name']} — {entry['truth']}", 17)
        canvas.paste(boards.fitted(ARTIFACTS / f"{entry['key']}-mask-agreement.png", (1280, 720)), (0, y + 36))
        y += row_height
    canvas.save(ARTIFACTS / "e9-extra-mask-agreement-board.png", optimize=True)


def main():
    base_sha = subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True).strip()
    boards.two_column_board(
        "e9-extra-mood-ab.png",
        "E9 EXTRA MAPS MOOD A/B — THE REDFIELDS FIGHT BACK",
        f"Fresh reference base {base_sha[:12]} | rust-red engraving, black working cuts, scarce warm signals",
        [(entry["moodLabel"], entry["mood"], f"SCULPTED WHOLE-YARD — {entry['name']}", ARTIFACTS / f"{entry['key']}-composition.png") for entry in boards.MAPS],
    )
    boards.two_column_board(
        "e9-extra-flat-vs-sculpted-ab.png",
        "E9 EXTRA MAPS GEOMETRY A/B — IDENTICAL CAMERA AND MATERIAL",
        "Each right-hand tile is a distinct landform; exact authored flats remain unchanged",
        [(f"FLAT — {entry['name']}", ARTIFACTS / f"{entry['key']}-flat-tile-identical-camera.png", f"SCULPTED — {entry['name']}", ARTIFACTS / f"{entry['key']}-sculpted-tile-identical-camera.png") for entry in boards.MAPS],
    )
    boards.three_column_board(
        "e9-extra-owner-verdict.png",
        "E9 EXTRA MAPS OWNER VERDICT — THREE REDFIELDS, THREE DIFFERENT PRESSURES",
        "Real player camera | whole-tile composition | low field angle",
        ("run-camera", "overview", "low-sunset"),
        ("RUN", "OVERVIEW", "LOW"),
    )
    boards.three_column_board(
        "e9-extra-panorama-mood-ab.png",
        "E9 EXTRA MAPS PANORAMA V2 — MOUNTED SEPARATELY",
        "Before/mounted use identical framing; every panorama is one render-only ring",
        ("panorama-before", "panorama-mounted", "panorama-horizon"),
        ("BEFORE", "MOUNTED", "CENTER HORIZON"),
    )
    boards.two_column_board(
        "e9-extra-panorama-distance-gate.png",
        "E9 EXTRA MAPS CENTER-HORIZON GATE — DISTANCE, NEVER WALL OR CEILING",
        "Asymmetric red shelves sink the join; engraved haze quiets toward the zenith",
        [(f"{entry['name']} — CENTER HORIZON", ARTIFACTS / f"{entry['key']}-panorama-horizon.png", f"{entry['name']} — LOW", ARTIFACTS / f"{entry['key']}-low-sunset.png") for entry in boards.MAPS],
    )
    build_mask_board()


if __name__ == "__main__":
    main()
