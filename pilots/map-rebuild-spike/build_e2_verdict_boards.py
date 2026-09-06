"""Assemble owner boards for the complete authored E2 terrain family."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"
INK = (10, 9, 7)
GOLD = (224, 187, 92)

MAPS = [
    {
        "key": "hill-mine",
        "name": "THE HILL MINE",
        "mood": ROOT / "assets/raw/plate-contract-hill-mine.png",
        "moodLabel": "SHIPPED PAINTED HILL MINE PLATE",
        "truth": "5 build terraces | 3 rail routes | deep z=-5..5 | ford x=-4..4",
    },
    {
        "key": "trestle",
        "name": "THE TRESTLE",
        "mood": ROOT / "artifacts/e2-trestle/desktop-chrome-crossing.png",
        "moodLabel": "SHIPPED FLAT TRESTLE RUNTIME",
        "truth": "2 approach zones | north-south rail | deep z=-5..5 | ford x=-3..3",
    },
    {
        "key": "pressure-garden",
        "name": "THE PRESSURE GARDEN",
        "mood": ROOT / "artifacts/e2-pressure-garden/desktop-chrome-boilers-hot.png",
        "moodLabel": "SHIPPED FLAT PRESSURE GARDEN RUNTIME",
        "truth": "4 terraces | 3 boiler stakes | 3 coal seams | broad ford x=-6..6",
    },
    {
        "key": "incline",
        "name": "THE INCLINE",
        "mood": ARTIFACTS / "incline-shipped-flat-runtime.png",
        "moodLabel": "SHIPPED FLAT INCLINE RUNTIME",
        "truth": "4 yards/benches | 2 funicular rails | 2 fords x=-12,+12",
    },
]


def font(size):
    for candidate in (Path("/System/Library/Fonts/Supplemental/Arial.ttf"), Path("/System/Library/Fonts/Helvetica.ttc")):
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def fitted(path, size):
    with Image.open(path) as source:
        return ImageOps.fit(source.convert("RGB"), size, method=Image.Resampling.LANCZOS)


def centered(draw, bounds, label, size):
    x0, y0, x1, y1 = bounds
    text_font = font(size)
    box = draw.textbbox((0, 0), label, font=text_font)
    draw.text(((x0 + x1 - box[2] + box[0]) / 2, (y0 + y1 - box[3] + box[1]) / 2 - box[1]), label, font=text_font, fill=GOLD)


def two_column_board(output, title, subtitle, rows):
    canvas = Image.new("RGB", (1920, 108 + len(rows) * 576), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 54), title, 30)
    centered(draw, (0, 48, 1920, 92), subtitle, 17)
    y = 104
    for left_label, left_path, right_label, right_path in rows:
        centered(draw, (0, y, 960, y + 36), left_label, 19)
        centered(draw, (960, y, 1920, y + 36), right_label, 19)
        canvas.paste(fitted(left_path, (960, 540)), (0, y + 36))
        canvas.paste(fitted(right_path, (960, 540)), (960, y + 36))
        y += 576
    canvas.save(ARTIFACTS / output, optimize=True)


def three_column_board(output, title, subtitle, suffixes, labels):
    canvas = Image.new("RGB", (1920, 108 + len(MAPS) * 396), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 54), title, 30)
    centered(draw, (0, 48, 1920, 92), subtitle, 17)
    y = 104
    for entry in MAPS:
        for column, (suffix, label) in enumerate(zip(suffixes, labels)):
            x = column * 640
            centered(draw, (x, y, x + 640, y + 36), f"{entry['name']} — {label}", 17)
            canvas.paste(fitted(ARTIFACTS / f"{entry['key']}-{suffix}.png", (640, 360)), (x, y + 36))
        y += 396
    canvas.save(ARTIFACTS / output, optimize=True)


def build_mask_board():
    canvas = Image.new("RGB", (1920, 108 + len(MAPS) * 576), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 54), "E2 MASK AGREEMENT — FACTORY TABLES ARE THE AUTHORITY", 30)
    centered(draw, (0, 48, 1920, 92), "Teal = build zones | rust block = stake | rails and bank seam remain authored", 17)
    y = 104
    for entry in MAPS:
        centered(draw, (0, y, 1920, y + 36), f"{entry['name']} — {entry['truth']}", 19)
        canvas.paste(fitted(ARTIFACTS / f"{entry['key']}-mask-agreement.png", (1920, 540)), (0, y + 36))
        y += 576
    canvas.save(ARTIFACTS / "e2-mask-agreement-board.png", optimize=True)


def main():
    two_column_board(
        "e2-mood-ab.png",
        "E2 MOOD A/B — FIGHT, NEVER HOLIDAY",
        "Same-map source where it exists; Trestle honestly uses its shipped runtime because no dedicated plate exists",
        [
            (entry["moodLabel"], entry["mood"], f"SCULPTED RUN CAMERA — {entry['name']}", ARTIFACTS / f"{entry['key']}-run-camera.png")
            for entry in MAPS
        ],
    )
    two_column_board(
        "e2-flat-vs-sculpted-ab.png",
        "E2 GEOMETRY A/B — IDENTICAL CAMERA AND MATERIAL",
        "Left is a zero-height copy; right is the authored render terrain",
        [
            (f"FLAT — {entry['name']}", ARTIFACTS / f"{entry['key']}-flat-tile-identical-camera.png", f"SCULPTED — {entry['name']}", ARTIFACTS / f"{entry['key']}-sculpted-tile-identical-camera.png")
            for entry in MAPS
        ],
    )
    three_column_board(
        "e2-owner-verdict.png",
        "E2 OWNER VERDICT — FOUR DISTINCT STEAMWORKS MAPS",
        "Real player camera | whole-tile composition | low sunset",
        ("run-camera", "overview", "low-sunset"),
        ("RUN", "OVERVIEW", "LOW SUNSET"),
    )
    three_column_board(
        "e2-panorama-mood-ab.png",
        "E2 PANORAMA V2 — MOUNTED SEPARATELY",
        "Before/mounted use identical terrain framing; every panorama is one render-only ring",
        ("panorama-before", "panorama-mounted", "panorama-horizon"),
        ("BEFORE", "MOUNTED", "CENTER HORIZON"),
    )
    two_column_board(
        "e2-panorama-distance-gate.png",
        "E2 CENTER-HORIZON GATE — DISTANCE, NEVER WALL OR CEILING",
        "Full 16:9 frames preserve the zenith and the terrain-to-haze join",
        [(entry["name"], ARTIFACTS / f"{entry['key']}-panorama-horizon.png", f"{entry['name']} — LOW SUNSET", ARTIFACTS / f"{entry['key']}-low-sunset.png") for entry in MAPS],
    )
    build_mask_board()


if __name__ == "__main__":
    main()
