"""Assemble the compact owner gates for the Archive World."""

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
    if runtime.is_file() and subprocess.run([str(runtime), "-c", "import PIL"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode == 0:
        os.execv(str(runtime), [str(runtime), str(Path(__file__).resolve()), *sys.argv[1:]])
    raise SystemExit("Pillow is required; run with the bundled Codex workspace Python")


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"
spec = importlib.util.spec_from_file_location("archive_board_helpers", OUT / "build_e3_verdict_boards.py")
boards = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boards)
boards.MAPS = [{
    "key": "archive-world",
    "name": "THE ARCHIVE WORLD",
    "mood": ROOT / "assets/processed/kit-era-10.png",
    "moodLabel": "E10 ARK KIT — DEEP-INK MEMORY SOURCE",
    "truth": "4 exact restoration flats | 3 light holds | empty warning shelf | dry and planar",
}]


def mask_board():
    canvas = Image.new("RGB", (1280, 828), boards.INK)
    draw = ImageDraw.Draw(canvas)
    boards.centered(draw, (0, 0, 1280, 54), "ARCHIVE WORLD MASK AGREEMENT — PUBLISHED TABLE IS THE AUTHORITY", 25)
    boards.centered(draw, (0, 48, 1280, 92), "Teal = exact build flats | rust = ours-unless shelf | all progression stays code-owned", 16)
    boards.centered(draw, (0, 96, 1280, 132), boards.MAPS[0]["truth"], 17)
    canvas.paste(boards.fitted(ARTIFACTS / "archive-world-mask-agreement.png", (1280, 696)), (0, 132))
    canvas.save(ARTIFACTS / "e10-archive-mask-agreement-board.png", optimize=True)


def main():
    base_sha = subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True).strip()
    boards.two_column_board(
        "e10-archive-mood-ab.png",
        "E10 ARCHIVE WORLD MOOD A/B — PRESERVATION UNDER PRESSURE",
        f"Fresh reference base {base_sha[:12]} | deep ink, erased paper, scarce memory light; fight, never holiday",
        [("E10 KIT PLATE — ANCESTRY", boards.MAPS[0]["mood"], "ARCHIVE WORLD — WHOLE-YARD SCULPT", ARTIFACTS / "archive-world-composition.png")],
    )
    boards.two_column_board(
        "e10-archive-flat-vs-sculpted-ab.png",
        "E10 ARCHIVE WORLD GEOMETRY A/B — IDENTICAL CAMERA AND MATERIAL",
        "Four mask-exact terraces rise around one missing-sentence cut; the flat plane remains simulation truth",
        [("FLAT RENDER", ARTIFACTS / "archive-world-flat-tile-identical-camera.png", "SCULPTED RENDER", ARTIFACTS / "archive-world-sculpted-tile-identical-camera.png")],
    )
    boards.three_column_board(
        "e10-archive-owner-verdict.png",
        "E10 ARCHIVE WORLD OWNER VERDICT — A LOST LIBRARY, NOT ANOTHER CLAIM",
        "Real player camera | whole-tile composition | low field angle",
        ("run-camera", "overview", "low-sunset"),
        ("RUN", "OVERVIEW", "LOW"),
    )
    boards.three_column_board(
        "e10-archive-panorama-mood-ab.png",
        "E10 ARCHIVE WORLD PANORAMA V2 — MOUNTED SEPARATELY",
        "Before/mounted use identical framing; deep sky quiets toward the zenith",
        ("panorama-before", "panorama-mounted", "panorama-horizon"),
        ("BEFORE", "MOUNTED", "CENTER HORIZON"),
    )
    boards.two_column_board(
        "e10-archive-panorama-distance-gate.png",
        "E10 ARCHIVE WORLD CENTER-HORIZON GATE — DISTANCE, NEVER WALL OR CEILING",
        "Irregular archive silhouettes sink the join; asymmetric memory veils break repetition",
        [("CENTER HORIZON", ARTIFACTS / "archive-world-panorama-horizon.png", "LOW FIELD ANGLE", ARTIFACTS / "archive-world-low-sunset.png")],
    )
    mask_board()


if __name__ == "__main__":
    main()
