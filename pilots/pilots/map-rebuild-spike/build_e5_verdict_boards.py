"""Assemble the Deepwater Claim owner and contract gates."""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"
INK = (7, 12, 14)
GOLD = (220, 184, 92)
PAINTED = ROOT / "assets/raw/ter-shelf-atlas.png"
TABLE = ROOT / "assets/contracts/epoch-5-deepwater/mask-tables/e5-deepwater-claim.json"


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
    face = font(size)
    box = draw.textbbox((0, 0), label, font=face)
    draw.text(((x0 + x1 - box[2] + box[0]) / 2, (y0 + y1 - box[3] + box[1]) / 2 - box[1]), label, font=face, fill=GOLD)


def two_column(output, title, subtitle, left_label, left, right_label, right, height=630):
    canvas = Image.new("RGB", (1920, height), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), title, 29)
    centered(draw, (0, 46, 1920, 88), subtitle, 17)
    centered(draw, (0, 92, 960, 126), left_label, 18)
    centered(draw, (960, 92, 1920, 126), right_label, 18)
    canvas.paste(fitted(left, (960, height - 126)), (0, 126))
    canvas.paste(fitted(right, (960, height - 126)), (960, 126))
    canvas.save(ARTIFACTS / output, optimize=True)


def owner_board():
    canvas = Image.new("RGB", (1920, 900), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 54), "E5 DEEPWATER CLAIM — OWNER VERDICT", 30)
    centered(draw, (0, 48, 1920, 92), "Real run camera | whole-tile bathymetry | low storm-lull angle", 17)
    for column, (label, suffix) in enumerate((("RUN", "run-camera"), ("OVERVIEW", "overview"), ("LOW WEATHER", "low-sunset"))):
        x = column * 640
        centered(draw, (x, 98, x + 640, 136), label, 18)
        canvas.paste(fitted(ARTIFACTS / f"deepwater-claim-{suffix}.png", (640, 720)), (x, 136))
    canvas.save(ARTIFACTS / "deepwater-owner-verdict.png", optimize=True)


def mask_schematic():
    """Draw the published mask table in the same x/z registration as the overlay."""
    table = json.loads(TABLE.read_text(encoding="utf-8"))["maskTruth"]
    canvas = Image.new("RGBA", (960, 1134), (9, 25, 29, 255))
    draw = ImageDraw.Draw(canvas, "RGBA")
    plot = (70, 146, 890, 966)

    def point(x, z):
        return (
            plot[0] + (x + 64.0) / 128.0 * (plot[2] - plot[0]),
            plot[1] + (64.0 - z) / 128.0 * (plot[3] - plot[1]),
        )

    def rect(zone):
        left, top = point(zone["minX"], zone["maxZ"])
        right, bottom = point(zone["maxX"], zone["minZ"])
        return (left, top, right, bottom)

    draw.rectangle(plot, fill=(22, 67, 74, 255), outline=(147, 205, 199, 255), width=3)
    for metre in range(-64, 65, 16):
        x, _ = point(metre, 0)
        _, y = point(0, metre)
        draw.line((x, plot[1], x, plot[3]), fill=(183, 213, 204, 44), width=1)
        draw.line((plot[0], y, plot[2], y), fill=(183, 213, 204, 44), width=1)
        draw.text((x + 3, plot[3] + 7), str(metre), font=font(13), fill=(184, 202, 197, 255))
        draw.text((plot[0] - 37, y - 7), str(metre), font=font(13), fill=(184, 202, 197, 255))

    palette = {
        "lagoon-shallows": (54, 190, 177, 96),
        "reef-ring": (31, 145, 150, 130),
        "reef-gap": (233, 191, 78, 190),
        "wreck-shelf": (210, 111, 49, 128),
        "trench-edge": (111, 62, 150, 175),
    }
    regions = table["deepwater"]["waterTile"]["regions"]
    for zone in regions:
        if zone["id"] == "open-water":
            continue
        colour = palette[zone["id"]]
        draw.rectangle(rect(zone), fill=colour, outline=colour[:3] + (255,), width=3)
        left, top, right, bottom = rect(zone)
        label = zone["id"].replace("-", " ").upper()
        draw.text((left + 7, top + 6), label, font=font(15), fill=(245, 229, 183, 255))

    build = table["buildZones"][0]
    draw.rectangle(rect(build), fill=(39, 218, 203, 175), outline=(236, 250, 229, 255), width=4)
    left, top, _right, _bottom = rect(build)
    draw.text((left + 7, top - 25), "CLAIM-BOAT BUILD", font=font(14), fill=(236, 250, 229, 255))

    for wreck in table["deepwater"]["wrecks"]:
        x, y = point(wreck["x"], wreck["z"])
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=(240, 139, 61, 255), outline=(255, 232, 189, 255), width=2)
        draw.text((x + 10, y - 8), wreck["id"].split("-")[0].upper(), font=font(13), fill=(255, 232, 189, 255))

    spawn = table["enemyRoster"][0]["spawnGates"][0]
    x, y = point(spawn["x"], spawn["z"])
    draw.polygon(((x - 2, y), (x + 15, y - 10), (x + 15, y + 10)), fill=(195, 121, 232, 255))
    draw.text((x + 21, y - 9), "WEST SPAWN", font=font(14), fill=(228, 196, 246, 255))

    centered(draw, (0, 20, 960, 72), "PUBLISHED E5 MASK TABLE", 28)
    centered(draw, (0, 66, 960, 112), "Exact 128m x/z plan — north is +z", 17)
    draw.text((70, 1007), "TEAL  lagoon / reef / build     GOLD  reef-gap override", font=font(17), fill=(223, 233, 218, 255))
    draw.text((70, 1043), "ORANGE  wreck shelf + anchors     VIOLET  trench + west spawn", font=font(17), fill=(223, 233, 218, 255))
    draw.text((70, 1081), "Water surface and travel classification remain runtime-owned.", font=font(16), fill=(167, 195, 191, 255))
    output = ARTIFACTS / "deepwater-published-mask-plan.png"
    canvas.convert("RGB").save(output, optimize=True)
    return output


def registered_overlay():
    """Put the Blender top view into the same north-up square registration."""
    source_path = ARTIFACTS / "deepwater-claim-mask-agreement.png"
    with Image.open(source_path) as source:
        source = source.convert("RGB")
        # The perspective camera leaves a deliberate guard around the 128 m
        # tile. Crop that guard before matching the exact plan grid.
        side = int(round(min(source.width, source.height) * 0.855))
        left = (source.width - side) // 2
        top = (source.height - side) // 2
        square = source.crop((left, top, left + side, top + side))
        square = ImageOps.flip(square).resize((820, 820), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (960, 1134), (9, 25, 29))
    canvas.paste(square, (70, 146))
    draw = ImageDraw.Draw(canvas, "RGBA")
    plot = (70, 146, 890, 966)
    draw.rectangle(plot, outline=(147, 205, 199, 255), width=3)
    for metre in range(-64, 65, 16):
        x = plot[0] + (metre + 64.0) / 128.0 * (plot[2] - plot[0])
        y = plot[1] + (64.0 - metre) / 128.0 * (plot[3] - plot[1])
        draw.line((x, plot[1], x, plot[3]), fill=(183, 213, 204, 54), width=1)
        draw.line((plot[0], y, plot[2], y), fill=(183, 213, 204, 54), width=1)
        draw.text((x + 3, plot[3] + 7), str(metre), font=font(13), fill=(184, 202, 197, 255))
        draw.text((plot[0] - 37, y - 7), str(metre), font=font(13), fill=(184, 202, 197, 255))
    centered(draw, (0, 20, 960, 72), "MATCHED BLENDER OVERLAY", 28)
    centered(draw, (0, 66, 960, 112), "Same north-up 128m x/z plan and grid", 17)
    draw.text((70, 1007), "Exact published region rectangles and wreck anchors over sculpted bathymetry.", font=font(17), fill=(223, 233, 218, 255))
    draw.text((70, 1043), "Town bodies and work proxies are hidden for this contract gate.", font=font(17), fill=(223, 233, 218, 255))
    draw.text((70, 1081), "No mask, spawn, build, travel, or water authority is exported.", font=font(16), fill=(167, 195, 191, 255))
    output = ARTIFACTS / "deepwater-registered-mask-overlay.png"
    canvas.save(output, optimize=True)
    return output


def main():
    published_mask = mask_schematic()
    matched_overlay = registered_overlay()
    two_column(
        "deepwater-mood-ab.png",
        "E5 MOOD A/B — WORKING HARBOR, NEVER POSTCARD",
        "Shipped shelf paint establishes the new chain; the sculpt must answer FIGHT",
        "SHIPPED SHELF REEF PAINT",
        PAINTED,
        "SCULPTED RUN CAMERA",
        ARTIFACTS / "deepwater-claim-run-camera.png",
        1260,
    )
    two_column(
        "deepwater-flat-vs-sculpted-ab.png",
        "E5 GEOMETRY A/B — IDENTICAL CAMERA AND MATERIAL",
        "A flat seabed cannot carry the depth ladder; the sculpt exposes lagoon, reef gap, shelf, and trench",
        "FLAT SEABED",
        ARTIFACTS / "deepwater-claim-flat-tile-identical-camera.png",
        "SCULPTED BATHYMETRY",
        ARTIFACTS / "deepwater-claim-sculpted-tile-identical-camera.png",
    )
    owner_board()
    two_column(
        "deepwater-ruin-contact-gate.png",
        "E5 DROWNED TOWN — SUBMERGED DOES NOT MEAN AFLOAT",
        "Identical camera: each heavy E4 body rests in a local seabed hollow before the code-owned water is shown",
        "SEABED CONTACT — WATER HIDDEN",
        ARTIFACTS / "deepwater-claim-ruin-seabed-contact.png",
        "FINAL SUBMERGED STATE",
        ARTIFACTS / "deepwater-claim-ruin-submerged.png",
    )
    two_column(
        "deepwater-panorama-mood-ab.png",
        "E5 PANORAMA V2 — OPEN SEA, MOUNTED SEPARATELY",
        "No confirming coast; the runtime sea hides the sunk ring foot",
        "BEFORE",
        ARTIFACTS / "deepwater-claim-panorama-before.png",
        "MOUNTED",
        ARTIFACTS / "deepwater-claim-panorama-mounted.png",
    )
    two_column(
        "deepwater-panorama-distance-gate.png",
        "E5 CENTER-HORIZON GATE — DISTANCE, NEVER WALL OR CEILING",
        "Quiet zenith, tea haze, asymmetric weather cells, and mystery-scale mast suggestions",
        "CENTER HORIZON",
        ARTIFACTS / "deepwater-claim-panorama-horizon.png",
        "LOW WEATHER",
        ARTIFACTS / "deepwater-claim-low-sunset.png",
    )
    two_column(
        "deepwater-mask-agreement-board.png",
        "E5 MASK AGREEMENT — WATER CLASSIFICATION STAYS CODE-OWNED",
        "Teal lagoon/reef/gap/deck | orange wreck shelf + anchors | violet sealed trench + west spawn",
        "PUBLISHED MASK TABLE — 128m PLAN",
        published_mask,
        "MATCHED TOP-DOWN OVERLAY",
        matched_overlay,
        1260,
    )


if __name__ == "__main__":
    main()
