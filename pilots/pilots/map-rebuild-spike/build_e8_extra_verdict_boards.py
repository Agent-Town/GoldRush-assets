"""Assemble the compact owner gates for the E8 campaign extras."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys

try:
    import PIL  # noqa: F401
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


boards = load_module("e8_extra_board_helpers", OUT / "build_e3_verdict_boards.py")
boards.MAPS = [
    {
        "key": "low-orbit",
        "name": "LOW ORBIT",
        "mood": ROOT / "assets/processed/kit-era-8.png",
        "moodLabel": "FRESH E8 KIT PLATE — APPROVED ORBITAL PALETTE SOURCE",
        "truth": "3 exact scaffold flats | 2 debris fields | 1 handhold spine | west/east spawn | zero-G code-owned",
    },
]


def main():
    base_sha = subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True).strip()
    boards.two_column_board(
        "e8-extra-mood-ab.png",
        "LOW ORBIT MOOD A/B — SALVAGE UNDER PRESSURE, NEVER COLD PHOTOREAL",
        f"Fresh reference base {base_sha[:12]} | silver-teal wreckage, suit brass, honey work light, drawn vacuum",
        [(boards.MAPS[0]["moodLabel"], boards.MAPS[0]["mood"], "SCULPTED WHOLE-YARD COMPOSITION — LOW ORBIT", ARTIFACTS / "low-orbit-composition.png")],
    )
    boards.two_column_board(
        "e8-extra-flat-vs-sculpted-ab.png",
        "E8 CAMPAIGN EXTRAS GEOMETRY A/B — IDENTICAL CAMERA AND MATERIAL",
        "Left is the zero-height render mesh; right is the three-deck scaffold/debris heightfield",
        [("FLAT — LOW ORBIT", ARTIFACTS / "low-orbit-flat-tile-identical-camera.png", "SCULPTED — LOW ORBIT", ARTIFACTS / "low-orbit-sculpted-tile-identical-camera.png")],
    )
    boards.three_column_board(
        "e8-extra-owner-verdict.png",
        "E8 CAMPAIGN EXTRAS OWNER VERDICT — ORBITAL YARD IN THREE READS",
        "Real player camera | whole-tile composition | low vacuum",
        ("run-camera", "overview", "low-sunset"),
        ("RUN", "OVERVIEW", "LOW VACUUM"),
    )
    boards.three_column_board(
        "e8-extra-panorama-mood-ab.png",
        "E8 CAMPAIGN EXTRAS PANORAMA V2 — MOUNTED SEPARATELY",
        "Before/mounted use identical framing; the panorama is one render-only ring",
        ("panorama-before", "panorama-mounted", "panorama-horizon"),
        ("BEFORE", "MOUNTED", "CENTER HORIZON"),
    )
    boards.two_column_board(
        "e8-extra-panorama-distance-gate.png",
        "E8 CAMPAIGN EXTRAS CENTER-HORIZON GATE — DISTANCE, NEVER WALL OR CEILING",
        "Drawn emptiness stays quiet; one soft Earth cameo and asymmetric debris edits read as orbit",
        [("LOW ORBIT — CENTER HORIZON", ARTIFACTS / "low-orbit-panorama-horizon.png", "LOW ORBIT — LOW VACUUM", ARTIFACTS / "low-orbit-low-sunset.png")],
    )
    boards.build_mask_board(
        "e8-extra",
        "E8 CAMPAIGN EXTRAS MASK AGREEMENT — PUBLISHED TABLE IS THE AUTHORITY",
        "Teal = 3 exact scaffold flats | rust = 2 debris fields | gold = handhold spine | zero-G stays code-owned",
    )


if __name__ == "__main__":
    main()
