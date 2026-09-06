"""Build the review boards from the current terrain and panorama renders."""

import os
from pathlib import Path
import subprocess
import sys

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ModuleNotFoundError:
    # The project does not carry a Python dependency environment. Re-exec with
    # an already-installed authoring runtime so the documented plain `python3`
    # command works without installing or billing anything.
    runtimes = (
        Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3",
        Path("/opt/homebrew/anaconda3/bin/python3"),
    )
    for runtime in runtimes:
        if runtime.is_file() and subprocess.run(
            [str(runtime), "-c", "import PIL"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode == 0:
            os.execv(str(runtime), [str(runtime), str(Path(__file__).resolve()), *sys.argv[1:]])
    raise SystemExit("Pillow is required; run with the bundled Codex workspace Python")


ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"
RAW = ROOT / "assets/raw"
INK = (10, 9, 7)
GOLD = (224, 187, 92)

MAPS = [
    ("THE CLAIM", RAW / "plate-contract-the-claim.png", "owner-run-camera-sculpted.png", "the-claim"),
    ("DRY GULCH", RAW / "plate-contract-dry-gulch.png", "dry-gulch-run-camera.png", "dry-gulch"),
    ("TWIN BANKS", RAW / "plate-contract-twin-banks.png", "twin-banks-run-camera-unique.png", "twin-banks"),
    ("NIGHT SHIFT", RAW / "plate-contract-night-shift.png", "night-shift-run-camera-unique.png", "night-shift"),
    ("BARON", RAW / "plate-contract-baron.png", "baron-run-camera-unique.png", "baron"),
]


def font(size):
    candidates = (
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/Helvetica.ttc"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def fitted(path, size):
    with Image.open(path) as source:
        return ImageOps.fit(source.convert("RGB"), size, method=Image.Resampling.LANCZOS)


def boundary_crop(path, size):
    """Magnify the shifted-camera tile/county boundary instead of fitting it."""
    with Image.open(path) as source:
        source = source.convert("RGB")
        width, height = source.size
        crop = source.crop((int(width * 0.25), int(height * 0.10), int(width * 0.82), int(height * 0.90)))
        return ImageOps.fit(crop, size, method=Image.Resampling.LANCZOS)


def centered(draw, bounds, label, text_font):
    x0, y0, x1, y1 = bounds
    box = draw.textbbox((0, 0), label, font=text_font)
    width = box[2] - box[0]
    height = box[3] - box[1]
    draw.text(((x0 + x1 - width) / 2, (y0 + y1 - height) / 2 - box[1]), label, font=text_font, fill=GOLD)


def build_mood_board():
    canvas = Image.new("RGB", (1280, 2092), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1280, 48), "MOOD A/B - FIGHT OR HOLIDAY?", font(30))
    centered(draw, (0, 42, 1280, 92), "Shipped painted contract plate | sculpted terrain at the real gameplay camera", font(17))
    y = 112
    for name, plate, render_name, _key in MAPS:
        centered(draw, (0, y, 640, y + 36), f"PAINTED PLATE - {name}", font(20))
        centered(draw, (640, y, 1280, y + 36), f"SCULPTED RUN CAMERA - {name}", font(20))
        canvas.paste(fitted(plate, (640, 360)), (0, y + 36))
        canvas.paste(fitted(ARTIFACTS / render_name, (640, 360)), (640, y + 36))
        y += 396
    canvas.save(ARTIFACTS / "all-contracts-mood-ab.png", optimize=True)


def build_panorama_board():
    canvas = Image.new("RGB", (1920, 2092), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 48), "PANORAMA MOOD A/B - FIGHT OR HOLIDAY?", font(30))
    centered(draw, (0, 42, 1920, 92), "Painted contract plate | terrain before backplate | mounted engraved panorama", font(17))
    y = 112
    for name, plate, _render_name, key in MAPS:
        centered(draw, (0, y, 640, y + 36), f"PAINTED - {name}", font(18))
        centered(draw, (640, y, 1280, y + 36), "BEFORE BACKPLATE", font(18))
        centered(draw, (1280, y, 1920, y + 36), "MOUNTED PANORAMA", font(18))
        canvas.paste(fitted(plate, (640, 360)), (0, y + 36))
        canvas.paste(fitted(ARTIFACTS / f"{key}-panorama-before.png", (640, 360)), (640, y + 36))
        canvas.paste(fitted(ARTIFACTS / f"{key}-panorama-mounted.png", (640, 360)), (1280, y + 36))
        y += 396
    canvas.save(ARTIFACTS / "all-contracts-panorama-mood-ab.png", optimize=True)


def build_panorama_distance_board():
    # Three 16:9 rows preserve every source pixel vertically. Cropping the
    # horizon captures would hide the exact zenith and terrain-join areas that
    # the Ceiling and Painted Wall gates are meant to expose.
    canvas = Image.new("RGB", (1920, 1792), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 58), "CENTER-HORIZON GATE — DISTANCE, NEVER WALL OR CEILING", font(30))
    for index, (name, _plate, _render_name, key) in enumerate(MAPS):
        x = (index % 2) * 960
        y = 58 + (index // 2) * 578
        centered(draw, (x, y, x + 960, y + 38), name, font(22))
        canvas.paste(fitted(ARTIFACTS / f"{key}-panorama-horizon.png", (960, 540)), (x, y + 38))
    centered(draw, (960, 1214, 1920, 1370), "ACCEPT: DISTANCE", font(32))
    centered(draw, (960, 1360, 1920, 1470), "REJECT: PAINTED WALL", font(24))
    centered(draw, (960, 1460, 1920, 1570), "REJECT: LOW CEILING", font(24))
    centered(draw, (960, 1560, 1920, 1670), "REJECT: REPEATED ECHO", font(24))
    canvas.save(ARTIFACTS / "all-contracts-panorama-distance-gate.png", optimize=True)


def build_claim_exterior_board():
    canvas = Image.new("RGB", (1920, 604), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 960, 64), "BEFORE — FLAT SURROUND", font(28))
    centered(draw, (960, 0, 1920, 64), "AFTER — SCULPTED CLAIM COUNTY", font(28))
    canvas.paste(fitted(ARTIFACTS / "the-claim-exterior-before-low.png", (960, 540)), (0, 64))
    canvas.paste(fitted(ARTIFACTS / "the-claim-panorama-before.png", (960, 540)), (960, 64))
    canvas.save(ARTIFACTS / "the-claim-exterior-ab.png", optimize=True)


def build_exterior_board():
    rows = [
        ("DRY GULCH", "failed basin and dry washes", "dry-gulch"),
        ("TWIN BANKS", "broad floodplain and paired outer works", "twin-banks"),
        ("NIGHT SHIFT", "dark rock corridor and lantern road", "night-shift"),
        ("BARON", "fortified far-bank horizon", "baron"),
    ]
    canvas = Image.new("RGB", (1920, 2472), INK)
    draw = ImageDraw.Draw(canvas)
    for index, (name, signature, key) in enumerate(rows):
        y = index * 618
        draw.text((18, y + 5), f"{name} — {signature}", font=font(24), fill=GOLD)
        centered(draw, (0, y + 34, 960, y + 78), "BEFORE — flat exterior plate", font(15))
        centered(draw, (960, y + 34, 1920, y + 78), "AFTER — authored county continuation", font(15))
        canvas.paste(fitted(ARTIFACTS / f"{key}-exterior-before-edge.png", (960, 540)), (0, y + 78))
        canvas.paste(fitted(ARTIFACTS / f"{key}-run-camera-east-edge.png", (960, 540)), (960, y + 78))
    canvas.save(ARTIFACTS / "all-contracts-exterior-ab.png", optimize=True)


def build_two_by_two(output_name, rows, suffix):
    canvas = Image.new("RGB", (1920, 1080), INK)
    draw = ImageDraw.Draw(canvas)
    for index, (name, key) in enumerate(rows):
        x = (index % 2) * 960
        y = (index // 2) * 540
        draw.text((x + 18, y + 5), f"{name}{suffix}", font=font(25), fill=GOLD)
        source = ARTIFACTS / (f"{key}-low-angle-unique.png" if not suffix else f"{key}-run-camera-east-edge.png")
        image = fitted(source, (960, 504)) if not suffix else boundary_crop(source, (960, 504))
        canvas.paste(image, (x, y + 36))
    canvas.save(ARTIFACTS / output_name, optimize=True)


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    build_mood_board()
    build_panorama_board()
    build_panorama_distance_board()
    build_claim_exterior_board()
    build_exterior_board()
    rows = [("DRY GULCH", "dry-gulch"), ("TWIN BANKS", "twin-banks"), ("NIGHT SHIFT", "night-shift"), ("BARON", "baron")]
    build_two_by_two("all-contracts-exterior-low-verdict.png", rows, "")
    build_two_by_two("all-contracts-exterior-edge-crops.png", rows, " — EDGE CROP")


if __name__ == "__main__":
    main()
