"""Assemble compact owner gates for authored terrain pairs."""

import json
import os
from pathlib import Path
import subprocess
import sys

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ModuleNotFoundError:
    runtime = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
    if runtime.is_file() and subprocess.run(
        [str(runtime), "-c", "import PIL"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
    ).returncode == 0:
        os.execv(str(runtime), [str(runtime), str(Path(__file__).resolve()), *sys.argv[1:]])
    raise SystemExit("Pillow is required; run with the bundled Codex workspace Python")


ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"
INK = (7, 8, 11)
GOLD = (224, 187, 92)

MAPS = [
    {
        "key": "canyon-works",
        "name": "CANYON WORKS",
        "mood": ROOT / "artifacts/canyon-works/desktop-chrome-dusk-lit-chain.png",
        "moodLabel": "SHIPPED CANYON WORKS — PALETTE/MOOD REFERENCE",
        "truth": "5 build zones | 6 flat pylon sites | deep z=-5..5 | banks beyond |z|=6.25",
    },
    {
        "key": "moth-season",
        "name": "MOTH SEASON",
        "mood": ROOT / "artifacts/e3-moth-season/desktop-chrome-decoy-tithe.png",
        "moodLabel": "SHIPPED MOTH SEASON — PALETTE/MOOD REFERENCE",
        "truth": "3 build zones | no river | north/south lanes | night locked",
    },
]

BLACKOUT_DUST_MAPS = [
    {
        "key": "blackout-ridge",
        "name": "BLACKOUT RIDGE",
        "mood": ROOT / "artifacts/blackout-ridge/desktop-chrome-stored-breath-cut-10s.png",
        "moodLabel": "SHIPPED BLACKOUT RIDGE — PALETTE/MOOD REFERENCE",
        "truth": "3 build zones | 3 pylon + 2 capacitor flats | no river | night locked",
    },
    {
        "key": "dust-flats",
        "name": "DUST FLATS",
        "mood": ROOT / "artifacts/e4-dust-flats/desktop-chrome-storm-graded-road.png",
        "moodLabel": "SHIPPED DUST FLATS — PALETTE/MOOD REFERENCE",
        "truth": "4 build zones | orbit r=24 | 4 roads | 4 tar seams | dry wash | no river",
    },
]

FAIRGROUND_MAPS = [
    {
        "key": "fairground",
        "name": "THE FAIRGROUND",
        "mood": ROOT / "assets/processed/kit-era-3.png",
        "moodLabel": "SHIPPED E3 KIT PLATE — PALETTE/MOOD SOURCE",
        "truth": "3 build zones | exact wheel fixture | west/east/north spawn edges | no water",
    },
]

GLOW_MESA_MAPS = [
    {
        "key": "glow-mesa",
        "name": "THE GLOW MESA",
        "mood": ROOT / "assets/processed/kit-era-6.png",
        "moodLabel": "FRESH E6 KIT PLATE — PALETTE/MOOD SOURCE",
        "truth": "5 flat build zones | 2 fixtures | 2 decay fields | 3 herd paths | 6 veins | no water",
    },
]

RELAY_VALLEY_MAPS = [
    {
        "key": "relay-valley",
        "name": "THE RELAY VALLEY",
        "mood": ROOT / "assets/processed/kit-era-7.png",
        "moodLabel": "FRESH E7 KIT PLATE — PALETTE/MOOD SOURCE",
        "truth": "4 flat relay pads | 2 h5 ridges | 3 dead zones | 1 patrol loop | no water",
    },
]

E7_EXTRA_MAPS = [
    {
        "key": "echo-canyon",
        "name": "ECHO CANYON",
        "mood": ROOT / "assets/processed/kit-era-7.png",
        "moodLabel": "FRESH E7 KIT PLATE — PALETTE/MOOD SOURCE",
        "truth": "3 flat build zones | 2 exact h5 shelves | h0 floor | north/south lanes | mirror field code-owned",
    },
]

MARE_CLAIM_MAPS = [
    {
        "key": "mare-claim",
        "name": "THE MARE CLAIM",
        "mood": ROOT / "assets/processed/kit-era-8.png",
        "moodLabel": "FRESH E8 KIT PLATE — APPROVED PALETTE SOURCE",
        "truth": "7 flat build zones | 4 h6 rim bands | h0 mare | lava tube | 6 harvest anchors | no water",
    },
]

EMBER_SHORE_MAPS = [
    {
        "key": "ember-shore",
        "name": "THE EMBER SHORE",
        "mood": ROOT / "assets/raw/plate-e10-worlds.png",
        "moodLabel": "FRESH E10 FIRST-WORLD PLATE — EMBER PALETTE SOURCE",
        "truth": "2 flat preserve sites | 3 cooling bands | 3 spawn edges | 1 loss vent | no water",
    },
]

REGATTA_MAPS = [
    {
        "key": "regatta",
        "name": "THE REGATTA",
        "mood": ROOT / "assets/raw/ter-shelf-atlas.png",
        "moodLabel": "SHIPPED E5 SHELF PAINT — PALETTE/MOOD SOURCE",
        "truth": "1 runtime boat deck | 5 beacon centers | 1 fast-water zone | west spawn | water code-owned",
    },
]


def font(size):
    for candidate in (Path("/System/Library/Fonts/Supplemental/Arial.ttf"), Path("/System/Library/Fonts/Helvetica.ttc")):
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def fitted(path, size):
    with Image.open(path) as source:
        if path.name == "plate-e10-worlds.png":
            source = source.crop((0, 0, source.width // 3, source.height))
        return ImageOps.fit(source.convert("RGB"), size, method=Image.Resampling.LANCZOS)


def centered(draw, bounds, label, size):
    x0, y0, x1, y1 = bounds
    face = font(size)
    box = draw.textbbox((0, 0), label, font=face)
    draw.text(((x0 + x1 - box[2] + box[0]) / 2, (y0 + y1 - box[3] + box[1]) / 2 - box[1]), label, font=face, fill=GOLD)


def two_column_board(output, title, subtitle, rows):
    canvas = Image.new("RGB", (1920, 108 + 576 * len(rows)), INK)
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
    canvas = Image.new("RGB", (1920, 108 + 396 * len(MAPS)), INK)
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


def build_mask_board(prefix, title, subtitle):
    if prefix == "ember-shore":
        width = 1600
        canvas = Image.new("RGB", (width, 1260), INK)
        draw = ImageDraw.Draw(canvas)
        centered(draw, (0, 0, width, 54), title, 30)
        centered(draw, (0, 48, width, 92), subtitle, 17)
        entry = MAPS[0]
        centered(draw, (24, 104, 1040, 144), f"{entry['name']} — {entry['truth']}", 17)
        canvas.paste(fitted(ARTIFACTS / "ember-shore-mask-agreement.png", (960, 1080)), (40, 144))

        panel_x = 1050
        draw.rounded_rectangle((panel_x, 144, 1560, 1224), radius=14, fill=(14, 17, 21), outline=(57, 66, 70), width=2)
        draw.text((panel_x + 28, 174), "PUBLISHED MASK KEY", font=font(23), fill=GOLD)
        truth = json.loads((ROOT / "assets/contracts/epoch-10-deepsky/mask-tables/e10-ember-shore.json").read_text())["maskTruth"]
        map_left, map_top, map_size = panel_x + 28, 220, 454
        draw.rectangle((map_left, map_top, map_left + map_size, map_top + map_size), fill=(22, 24, 25), outline=(102, 105, 98), width=2)
        for grid in (-32, 0, 32):
            gx = map_left + int((grid + 64) / 128 * map_size)
            gy = map_top + int((64 - grid) / 128 * map_size)
            draw.line((gx, map_top, gx, map_top + map_size), fill=(40, 43, 43), width=1)
            draw.line((map_left, gy, map_left + map_size, gy), fill=(40, 43, 43), width=1)

        def px(x):
            return map_left + int((x + 64) / 128 * map_size)

        def py(z):
            return map_top + int((64 - z) / 128 * map_size)

        def zone_rect(zone):
            return (px(zone["minX"]), py(zone["maxZ"]), px(zone["maxX"]), py(zone["minZ"]))

        for index, band in enumerate(truth["lavaVeinBands"], 1):
            bounds = zone_rect(band)
            draw.rectangle(bounds, fill=(75, 24, 16), outline=(235, 92, 38), width=3)
            draw.text((bounds[0] + 3, bounds[1] + 2), f"L{index}", font=font(12), fill=(255, 155, 80))
        for index, zone in enumerate(truth["buildZones"], 1):
            bounds = zone_rect(zone)
            draw.rectangle(bounds, outline=(35, 220, 210), width=3)
            draw.text((bounds[0] + 3, bounds[1] + 2), f"B{index}", font=font(12), fill=(98, 255, 246))
        fixture = truth["fixtureZones"][0]
        fixture_bounds = zone_rect(fixture)
        draw.rectangle(fixture_bounds, outline=(224, 187, 92), width=2)
        stake = truth["stakeMarkers"][0]
        sx, sy = px(stake["x"]), py(stake["z"])
        draw.ellipse((sx - 7, sy - 7, sx + 7, sy + 7), outline=(255, 196, 71), width=3)
        draw.text((sx + 8, sy - 10), "V", font=font(13), fill=(255, 218, 110))
        edge_specs = {"north": ((-64, 60), (64, 60)), "west": ((-60, -64), (-60, 64)), "east": ((60, -64), (60, 64))}
        for edge in truth["lanes"]["spawnEdges"]:
            start, end = edge_specs[edge]
            draw.line((px(start[0]), py(start[1]), px(end[0]), py(end[1])), fill=(130, 110, 238), width=4)

        rows = (
            ((35, 220, 210), "B  2 FLAT PRESERVE SITES"),
            ((235, 92, 38), "L  3 COOLING BANDS"),
            ((224, 187, 92), "F  1 VENT FIXTURE"),
            ((255, 196, 71), "V  LOSS-CONDITION VENT"),
            ((130, 110, 238), "S  N/W/E SPAWN EDGES"),
        )
        y = 702
        for color, label in rows:
            draw.rounded_rectangle((panel_x + 28, y, panel_x + 52, y + 24), radius=4, fill=color)
            draw.text((panel_x + 64, y - 1), label, font=font(16), fill=(226, 223, 205))
            y += 42
        draw.line((panel_x + 28, 930, 1532, 930), fill=(57, 66, 70), width=2)
        draw.text((panel_x + 28, 954), "EXPORTED SURFACE", font=font(19), fill=GOLD)
        draw.text((panel_x + 28, 990), "B1-B2: <= 0.02 m deviation", font=font(16), fill=(226, 223, 205))
        draw.text((panel_x + 28, 1026), "three bands read as recessed cooling rifts", font=font(14), fill=(226, 223, 205))
        draw.text((panel_x + 28, 1072), "SIMULATION", font=font(19), fill=GOLD)
        draw.text((panel_x + 28, 1108), "planar | dry | no mounts | no baked Static", font=font(15), fill=(226, 223, 205))
        draw.text((panel_x + 28, 1144), "all coordinates copied from the table", font=font(14), fill=(150, 160, 160))
        canvas.save(ARTIFACTS / "ember-shore-mask-agreement-board.png", optimize=True)
        return

    if prefix == "glow-mesa":
        width = 1600
        canvas = Image.new("RGB", (width, 1260), INK)
        draw = ImageDraw.Draw(canvas)
        centered(draw, (0, 0, width, 54), title, 30)
        centered(draw, (0, 48, width, 92), subtitle, 17)
        entry = MAPS[0]
        centered(draw, (24, 104, 1040, 144), f"{entry['name']} — {entry['truth']}", 17)
        canvas.paste(fitted(ARTIFACTS / f"{entry['key']}-mask-agreement.png", (960, 1080)), (40, 144))

        panel_x = 1050
        draw.rounded_rectangle((panel_x, 144, 1560, 1224), radius=14, fill=(14, 17, 21), outline=(57, 66, 70), width=2)
        draw.text((panel_x + 28, 174), "PUBLISHED MASK KEY", font=font(23), fill=GOLD)
        truth = json.loads((ROOT / "assets/contracts/epoch-6-atomic/mask-tables/e6-glow-mesa.json").read_text())["maskTruth"]
        map_left, map_top, map_size = panel_x + 28, 220, 454
        draw.rectangle((map_left, map_top, map_left + map_size, map_top + map_size), fill=(22, 24, 25), outline=(102, 105, 98), width=2)
        for grid in (-32, 0, 32):
            gx = map_left + int((grid + 64) / 128 * map_size)
            gy = map_top + int((64 - grid) / 128 * map_size)
            draw.line((gx, map_top, gx, map_top + map_size), fill=(40, 43, 43), width=1)
            draw.line((map_left, gy, map_left + map_size, gy), fill=(40, 43, 43), width=1)

        def px(x):
            return map_left + int((x + 64) / 128 * map_size)

        def py(z):
            return map_top + int((64 - z) / 128 * map_size)

        def zone_rect(zone):
            return (px(zone["minX"]), py(zone["maxZ"]), px(zone["maxX"]), py(zone["minZ"]))

        fixture_index = {zone["id"]: index for index, zone in enumerate(truth["fixtureZones"], 1)}
        for index, zone in enumerate(truth["buildZones"], 1):
            draw.rectangle(zone_rect(zone), outline=(35, 220, 210), width=3)
            bounds = zone_rect(zone)
            if zone["id"] not in fixture_index:
                label_x = bounds[2] - 30 if zone["id"] == "warehouse-approach" else bounds[0] + 4
                draw.text((label_x, bounds[1] + 2), f"B{index}", font=font(14), fill=(98, 255, 246))
        for index, zone in enumerate(truth["fixtureZones"], 1):
            bounds = zone_rect(zone)
            inset = (bounds[0] + 5, bounds[1] + 5, bounds[2] - 5, bounds[3] - 5)
            draw.rectangle(inset, outline=(220, 156, 49), width=4)
            build_index = next(i for i, build in enumerate(truth["buildZones"], 1) if build["id"] == zone["id"])
            draw.text((bounds[0] + 7, bounds[1] + 7), f"B{build_index}/F{index}", font=font(12), fill=(255, 194, 82))
        for index, zone in enumerate(truth["decayFields"], 1):
            bounds = zone_rect(zone)
            draw.rectangle(bounds, outline=(190, 77, 42), width=4)
            hatch_height = bounds[3] - bounds[1]
            for offset in range(bounds[0] - hatch_height, bounds[2], 12):
                start_x = max(bounds[0], offset)
                end_x = min(bounds[2], offset + hatch_height)
                if end_x > start_x:
                    start_y = bounds[3] - (start_x - offset)
                    end_y = bounds[3] - (end_x - offset)
                    draw.line((start_x, start_y, end_x, end_y), fill=(120, 52, 34), width=1)
            draw.text((bounds[0] + 4, bounds[1] + 2), f"D{index}", font=font(14), fill=(255, 130, 84))
        for index, zone in enumerate(truth["herdPaths"], 1):
            bounds = zone_rect(zone)
            draw.rectangle(bounds, outline=(45, 120, 110), width=3)
            draw.text((bounds[0] + 4, bounds[3] - 18), f"H{index}", font=font(14), fill=(95, 190, 176))
        for index, anchor in enumerate(truth["harvestAnchors"], 1):
            ax, ay = px(anchor["x"]), py(anchor["z"])
            draw.ellipse((ax - 6, ay - 6, ax + 6, ay + 6), outline=(225, 190, 70), width=3)
            draw.text((ax + 7, ay - 8), f"A{index}", font=font(11), fill=(241, 210, 91))

        rows = (
            ((35, 220, 210), "B  5 BUILD"),
            ((208, 145, 53), "F  2 FIXTURE"),
            ((178, 76, 42), "D  2 DECAY"),
            ((37, 92, 88), "H  3 HERD"),
            ((214, 182, 70), "A  6 VEINS"),
        )
        y = 702
        for color, label in rows:
            draw.rounded_rectangle((panel_x + 28, y, panel_x + 52, y + 24), radius=4, fill=color)
            draw.text((panel_x + 64, y - 1), label, font=font(16), fill=(226, 223, 205))
            y += 42
        draw.line((panel_x + 28, 928, 1532, 928), fill=(57, 66, 70), width=2)
        draw.text((panel_x + 28, 950), "EXPORTED SURFACE", font=font(19), fill=GOLD)
        draw.text((panel_x + 28, 986), "B1-B5 + F1-F2: 0.00 m deviation", font=font(16), fill=(226, 223, 205))
        draw.text((panel_x + 28, 1024), "h1 south base / h5 mesa + warehouse", font=font(16), fill=(226, 223, 205))
        draw.text((panel_x + 28, 1052), "B4/F1 + B5/F2 overlap exactly by table", font=font(14), fill=(170, 178, 170))
        draw.text((panel_x + 28, 1076), "SIMULATION", font=font(19), fill=GOLD)
        draw.text((panel_x + 28, 1112), "planar | no water | no mounts", font=font(16), fill=(226, 223, 205))
        draw.text((panel_x + 28, 1146), "all coordinates copied from the table", font=font(15), fill=(150, 160, 160))
        canvas.save(ARTIFACTS / f"{prefix}-mask-agreement-board.png", optimize=True)
        return

    if prefix == "relay-valley":
        width = 1600
        canvas = Image.new("RGB", (width, 1260), INK)
        draw = ImageDraw.Draw(canvas)
        centered(draw, (0, 0, width, 54), title, 30)
        centered(draw, (0, 48, width, 92), subtitle, 17)
        entry = MAPS[0]
        centered(draw, (24, 104, 1040, 144), f"{entry['name']} — {entry['truth']}", 17)
        canvas.paste(fitted(ARTIFACTS / f"{entry['key']}-mask-agreement.png", (960, 1080)), (40, 144))

        panel_x = 1050
        draw.rounded_rectangle((panel_x, 144, 1560, 1224), radius=14, fill=(14, 17, 21), outline=(57, 66, 70), width=2)
        draw.text((panel_x + 28, 174), "PUBLISHED MASK KEY", font=font(23), fill=GOLD)
        truth = json.loads((ROOT / "assets/contracts/epoch-7-signal/mask-tables/e7-relay-valley.json").read_text())["maskTruth"]
        map_left, map_top, map_size = panel_x + 28, 220, 454
        draw.rectangle((map_left, map_top, map_left + map_size, map_top + map_size), fill=(22, 24, 25), outline=(102, 105, 98), width=2)
        for grid in (-32, 0, 32):
            gx = map_left + int((grid + 64) / 128 * map_size)
            gy = map_top + int((64 - grid) / 128 * map_size)
            draw.line((gx, map_top, gx, map_top + map_size), fill=(40, 43, 43), width=1)
            draw.line((map_left, gy, map_left + map_size, gy), fill=(40, 43, 43), width=1)

        def px(x):
            return map_left + int((x + 64) / 128 * map_size)

        def py(z):
            return map_top + int((64 - z) / 128 * map_size)

        def zone_rect(zone):
            return (px(zone["minX"]), py(zone["maxZ"]), px(zone["maxX"]), py(zone["minZ"]))

        ridge_colors = ((78, 90, 84), (78, 90, 84), (61, 51, 39))
        for index, (zone, color) in enumerate(zip(truth["ridgeBands"], ridge_colors), 1):
            bounds = zone_rect(zone)
            draw.rectangle(bounds, outline=color, width=4)
            label = "V" if zone["id"] == "valley-floor-h0" else f"R{index}"
            draw.text((bounds[0] + 4, bounds[1] + 2), label, font=font(14), fill=(186, 194, 181))
        for index, zone in enumerate(truth["fogPockets"], 1):
            bounds = zone_rect(zone)
            draw.rectangle(bounds, outline=(190, 77, 42), width=4)
            hatch_height = bounds[3] - bounds[1]
            for offset in range(bounds[0] - hatch_height, bounds[2], 12):
                start_x = max(bounds[0], offset)
                end_x = min(bounds[2], offset + hatch_height)
                if end_x > start_x:
                    start_y = bounds[3] - (start_x - offset)
                    end_y = bounds[3] - (end_x - offset)
                    draw.line((start_x, start_y, end_x, end_y), fill=(115, 54, 42), width=1)
            draw.text((bounds[0] + 4, bounds[1] + 2), f"F{index}", font=font(14), fill=(255, 130, 84))
        for index, zone in enumerate(truth["buildZones"], 1):
            bounds = zone_rect(zone)
            draw.rectangle(bounds, outline=(35, 220, 210), width=4)
            draw.text((bounds[0] + 4, bounds[1] + 2), f"B{index}", font=font(14), fill=(98, 255, 246))
        route = truth["lanes"]["patrolRoutes"][0]
        route_points = [(px(point["x"]), py(point["z"])) for point in route["points"]]
        draw.line(route_points, fill=(224, 187, 92), width=4, joint="curve")
        draw.text((px(-22), py(-18)), "P1", font=font(14), fill=(244, 205, 105))

        rows = (
            ((35, 220, 210), "B  4 RELAY PADS"),
            ((78, 90, 84), "R  2 H5 RIDGES"),
            ((190, 77, 42), "F  3 DEAD ZONES"),
            ((224, 187, 92), "P  1 PATROL LOOP"),
        )
        y = 702
        for color, label in rows:
            draw.rounded_rectangle((panel_x + 28, y, panel_x + 52, y + 24), radius=4, fill=color)
            draw.text((panel_x + 64, y - 1), label, font=font(16), fill=(226, 223, 205))
            y += 42
        draw.line((panel_x + 28, 900, 1532, 900), fill=(57, 66, 70), width=2)
        draw.text((panel_x + 28, 924), "EXPORTED SURFACE", font=font(19), fill=GOLD)
        draw.text((panel_x + 28, 960), "B1-B4: 0.00 m deviation", font=font(16), fill=(226, 223, 205))
        draw.text((panel_x + 28, 996), "west/east ridges h5 | valley floor h0", font=font(15), fill=(226, 223, 205))
        draw.text((panel_x + 28, 1034), "LOS pairs B1-B2 / B3-B4; gap unbridged", font=font(14), fill=(170, 178, 170))
        draw.text((panel_x + 28, 1076), "SIMULATION", font=font(19), fill=GOLD)
        draw.text((panel_x + 28, 1112), "planar | no water | no mounts", font=font(16), fill=(226, 223, 205))
        draw.text((panel_x + 28, 1146), "all coordinates copied from the table", font=font(15), fill=(150, 160, 160))
        canvas.save(ARTIFACTS / f"{prefix}-mask-agreement-board.png", optimize=True)
        return

    if prefix == "mare-claim":
        width = 1600
        canvas = Image.new("RGB", (width, 1260), INK)
        draw = ImageDraw.Draw(canvas)
        centered(draw, (0, 0, width, 54), title, 30)
        centered(draw, (0, 48, width, 92), subtitle, 17)
        entry = MAPS[0]
        centered(draw, (24, 104, 1040, 144), f"{entry['name']} — {entry['truth']}", 17)
        canvas.paste(fitted(ARTIFACTS / f"{entry['key']}-mask-agreement.png", (960, 1080)), (40, 144))

        panel_x = 1050
        draw.rounded_rectangle((panel_x, 144, 1560, 1224), radius=14, fill=(14, 17, 21), outline=(57, 66, 70), width=2)
        draw.text((panel_x + 28, 174), "PUBLISHED MASK KEY", font=font(23), fill=GOLD)
        truth = json.loads((ROOT / "assets/contracts/epoch-8-orbital/mask-tables/e8-mare-claim.json").read_text())["maskTruth"]
        map_left, map_top, map_size = panel_x + 28, 220, 454
        draw.rectangle((map_left, map_top, map_left + map_size, map_top + map_size), fill=(22, 24, 25), outline=(102, 105, 98), width=2)
        for grid in (-32, 0, 32):
            gx = map_left + int((grid + 64) / 128 * map_size)
            gy = map_top + int((64 - grid) / 128 * map_size)
            draw.line((gx, map_top, gx, map_top + map_size), fill=(40, 43, 43), width=1)
            draw.line((map_left, gy, map_left + map_size, gy), fill=(40, 43, 43), width=1)

        def px(x):
            return map_left + int((x + 64) / 128 * map_size)

        def py(z):
            return map_top + int((64 - z) / 128 * map_size)

        def zone_rect(zone):
            return (px(zone["minX"]), py(zone["maxZ"]), px(zone["maxX"]), py(zone["minZ"]))

        mare = truth["mareFlat"]
        draw.rectangle(zone_rect(mare), outline=(118, 120, 112), width=2)
        draw.text((zone_rect(mare)[0] + 5, zone_rect(mare)[1] + 3), "M0", font=font(13), fill=(190, 190, 177))
        for index, band in enumerate(truth["rimBands"], 1):
            bounds = zone_rect(band)
            draw.rectangle(bounds, outline=(107, 112, 106), width=4)
            rim_labels = (
                (px(-10), py(54) + 4),
                (px(-10), py(-42) + 4),
                (px(-54) + 4, py(8)),
                (px(42) + 4, py(8)),
            )
            draw.text(rim_labels[index - 1], f"R{index}", font=font(12), fill=(210, 210, 196))
        for index, zone in enumerate(truth["buildZones"], 1):
            bounds = zone_rect(zone)
            draw.rectangle(bounds, outline=(35, 220, 210), width=3)
            draw.text((bounds[0] + 3, bounds[1] + 2), f"B{index}", font=font(12), fill=(98, 255, 246))
        mouth = truth["lavaTubeMouth"]
        mouth_bounds = zone_rect(mouth)
        draw.rectangle(mouth_bounds, outline=(190, 77, 42), width=4)
        draw.text((mouth_bounds[0] + 4, mouth_bounds[1] + 2), "T1", font=font(13), fill=(255, 130, 84))
        for rail_index, rail in enumerate(truth["rails"], 1):
            rail_points = [(px(point["x"]), py(point["z"])) for point in rail["points"]]
            draw.line(rail_points, fill=(224, 187, 92), width=4, joint="curve")
            draw.text((px(42), rail_points[0][1] + 5), f"Q{rail_index}", font=font(12), fill=(244, 205, 105))
        for index, anchor in enumerate(truth["harvestAnchors"], 1):
            ax, ay = px(anchor["x"]), py(anchor["z"])
            draw.ellipse((ax - 5, ay - 5, ax + 5, ay + 5), outline=(88, 174, 168), width=3)
            draw.text((ax + 6, ay - 8), f"H{index}", font=font(10), fill=(110, 220, 212))
        lane = truth["debrisArcLanes"][0]
        debris_points = [(px(point["x"]), py(point["z"])) for point in lane["points"]]
        draw.line(debris_points, fill=(190, 77, 42), width=3, joint="curve")
        draw.text((px(-3), py(50) - 15), "D1", font=font(12), fill=(255, 130, 84))

        rows = (
            ((35, 220, 210), "B  7 FLAT BUILD"),
            ((107, 112, 106), "R  4 H6 RIM"),
            ((190, 190, 177), "M  H0 MARE"),
            ((190, 77, 42), "T  1 LAVA TUBE"),
            ((164, 66, 36), "D  1 DEBRIS ARC"),
            ((88, 174, 168), "H  6 HARVEST"),
            ((224, 187, 92), "Q  1 MASS DRIVER"),
        )
        y = 702
        for color, label in rows:
            draw.rounded_rectangle((panel_x + 28, y, panel_x + 52, y + 24), radius=4, fill=color)
            draw.text((panel_x + 64, y - 1), label, font=font(16), fill=(226, 223, 205))
            y += 34
        draw.line((panel_x + 28, 946, 1532, 946), fill=(57, 66, 70), width=2)
        draw.text((panel_x + 28, 966), "EXPORTED SURFACE", font=font(19), fill=GOLD)
        draw.text((panel_x + 28, 1002), "B1-B7: <= 0.02 m deviation", font=font(16), fill=(226, 223, 205))
        draw.text((panel_x + 28, 1038), "rim h6 | mare h0 | named tube recess", font=font(15), fill=(226, 223, 205))
        draw.text((panel_x + 28, 1080), "SIMULATION", font=font(19), fill=GOLD)
        draw.text((panel_x + 28, 1116), "planar | no water | landmark freeze", font=font(16), fill=(226, 223, 205))
        draw.text((panel_x + 28, 1150), "gravity and air rules remain code-owned", font=font(14), fill=(150, 160, 160))
        canvas.save(ARTIFACTS / f"{prefix}-mask-agreement-board.png", optimize=True)
        return

    width = 1280 if len(MAPS) == 1 else 1920
    canvas = Image.new("RGB", (width, 1260), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, width, 54), title, 30)
    centered(draw, (0, 48, width, 92), subtitle, 17)
    for column, entry in enumerate(MAPS):
        x = 160 if len(MAPS) == 1 else column * 960
        centered(draw, (x, 104, x + 960, 144), f"{entry['name']} — {entry['truth']}", 17)
        canvas.paste(fitted(ARTIFACTS / f"{entry['key']}-mask-agreement.png", (960, 1080)), (x, 144))
    canvas.save(ARTIFACTS / f"{prefix}-mask-agreement-board.png", optimize=True)


def main():
    global MAPS
    frontier = "--blackout-dust" in sys.argv[1:]
    fairground = "--fairground" in sys.argv[1:]
    glow_mesa = "--glow-mesa" in sys.argv[1:]
    relay_valley = "--relay-valley" in sys.argv[1:]
    e7_extra = "--e7-extra" in sys.argv[1:]
    mare_claim = "--mare-claim" in sys.argv[1:]
    ember_shore = "--ember-shore" in sys.argv[1:]
    regatta = "--regatta" in sys.argv[1:]
    if regatta:
        MAPS = REGATTA_MAPS
    elif ember_shore:
        MAPS = EMBER_SHORE_MAPS
    elif mare_claim:
        MAPS = MARE_CLAIM_MAPS
    elif e7_extra:
        MAPS = E7_EXTRA_MAPS
    elif relay_valley:
        MAPS = RELAY_VALLEY_MAPS
    elif glow_mesa:
        MAPS = GLOW_MESA_MAPS
    elif fairground:
        MAPS = FAIRGROUND_MAPS
    elif frontier:
        MAPS = BLACKOUT_DUST_MAPS
    prefix = "regatta" if regatta else ("e7-extra" if e7_extra else ("ember-shore" if ember_shore else ("mare-claim" if mare_claim else ("relay-valley" if relay_valley else ("glow-mesa" if glow_mesa else ("fairground" if fairground else ("blackout-dust" if frontier else "e3")))))))
    family = "THE REGATTA" if regatta else ("E7 EXTRA MAPS" if e7_extra else ("THE EMBER SHORE" if ember_shore else ("THE MARE CLAIM" if mare_claim else ("THE RELAY VALLEY" if relay_valley else ("THE GLOW MESA" if glow_mesa else ("THE FAIRGROUND" if fairground else ("BLACKOUT + DUST" if frontier else "E3")))))))
    base_sha = subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True).strip()
    if regatta:
        mood_title = "REGATTA MOOD A/B — WORKING RACE SEA, NEVER POSTCARD"
        mood_subtitle = f"Fresh reference base {base_sha[:12]} | blue-green shelf paint, charcoal storm scar, brass course work"
        owner_title = f"{family} OWNER VERDICT — RACE COURSE IN THREE READS"
        mask_subtitle = "Teal = runtime boat deck | violet = fast-water zone | orange = five beacons | water stays code-owned"
    elif e7_extra:
        mood_title = "E7 EXTRA MOOD A/B — SIGNAL CANYON, NEVER HOLIDAY"
        mood_subtitle = f"Fresh reference base {base_sha[:12]} | walnut, honey glass, and agent teal over opposed shale walls"
        owner_title = f"{family} OWNER VERDICT — BROADCAST CANYON IN THREE READS"
        mask_subtitle = "Teal = 3 flat build zones | ink = exact h0/h5 bands | rust = map-wide mirror field; simulation stays planar"
    elif ember_shore:
        mood_title = "EMBER SHORE MOOD A/B — PRESERVE UNDER PRESSURE, NEVER POSTCARD"
        mood_subtitle = f"Fresh reference base {base_sha[:12]} | deep ink, parchment-gold ember, restrained salvage teal"
        owner_title = f"{family} OWNER VERDICT — PRESERVE WORLD IN THREE READS"
        mask_subtitle = "B/L/F/V/S labels make every preserve site, cooling band, vent, and spawn edge countable"
    elif mare_claim:
        mood_title = "MARE CLAIM MOOD A/B — WARM GREY ENGRAVING, NEVER COLD PHOTOREAL"
        mood_subtitle = f"Fresh reference base {base_sha[:12]} | silver-and-teal over parchment; honey habitat light is the warm accent"
        owner_title = f"{family} OWNER VERDICT — CRATER CLAIM IN THREE READS"
        mask_subtitle = "B/R/M/T/H/Q/D labels make every build, rim, mare, tube, harvest, rail, and debris coordinate countable"
    elif relay_valley:
        mood_title = "RELAY VALLEY MOOD A/B — SIGNAL FRONTIER, NEVER HOLIDAY"
        mood_subtitle = f"Fresh reference base {base_sha[:12]} | walnut, honey glass, and agent teal must still answer fight"
        owner_title = f"{family} OWNER VERDICT — RIDGE CHAIN IN THREE READS"
        mask_subtitle = "B/R/F/P labels make every relay pad, ridge, dead zone, and patrol coordinate independently countable"
    elif glow_mesa:
        mood_title = "GLOW MESA MOOD A/B — POLISHED HOMESTEAD, DANGEROUS NIGHT"
        mood_subtitle = f"Fresh reference base {base_sha[:12]} | chrome-pastel warmth must still answer fight"
        owner_title = f"{family} OWNER VERDICT — TRUE MESA IN THREE READS"
        mask_subtitle = "B/F/D/H/A labels make every build, fixture, decay, herd, and vein coordinate independently countable"
    elif fairground:
        mood_title = "THE FAIRGROUND MOOD A/B — WORKING FAIR, NEVER HOLIDAY"
        mood_subtitle = "Left establishes the shipped E3 palette source; right must read as brutal, inhabited terrain"
        owner_title = f"{family} OWNER VERDICT — WORKING FAIR IN THREE READS"
        mask_subtitle = "Teal = build zones | rust = gate | gold = exact Ferris fixture | all masks stay planar"
    elif frontier:
        mood_title = "BLACKOUT + DUST MOOD A/B — FIGHT ACROSS NIGHT AND MOTOR HAZE"
        mood_subtitle = "Left establishes shipped same-map palette and hardship; right must add readable terrain"
        owner_title = f"{family} OWNER VERDICT — TWO DISTINCT CONTRACTS"
        mask_subtitle = "Teal = build zones | rust = pylon/orbit/road truth | gold = capacitor/tar sites | masks stay planar"
    else:
        mood_title = "E3 MOOD A/B — NIGHT GRIT MUST STILL READ FIGHT"
        mood_subtitle = "Left establishes shipped same-map palette and hardship; right must add readable terrain"
        owner_title = f"{family} OWNER VERDICT — TWO DISTINCT CONTRACTS"
        mask_subtitle = "Teal = build zones | rust = pylon disks | Canyon rim disks at z=8 overlap shallows by published-table design"
    two_column_board(
        f"{prefix}-mood-ab.png",
        mood_title,
        mood_subtitle,
        [(entry["moodLabel"], entry["mood"], f"SCULPTED RUN CAMERA — {entry['name']}", ARTIFACTS / f"{entry['key']}-run-camera.png") for entry in MAPS],
    )
    two_column_board(
        f"{prefix}-flat-vs-sculpted-ab.png",
        "REGATTA GEOMETRY A/B — WATER HIDDEN" if regatta else f"{family} GEOMETRY A/B — IDENTICAL CAMERA AND MATERIAL",
        "Flat seabed left; authored bathymetry right; code-owned water hidden for both" if regatta else "Left is a zero-height copy; right is the authored render terrain",
        [(f"FLAT — {entry['name']}", ARTIFACTS / f"{entry['key']}-flat-tile-identical-camera.png", f"SCULPTED — {entry['name']}", ARTIFACTS / f"{entry['key']}-sculpted-tile-identical-camera.png") for entry in MAPS],
    )
    three_column_board(
        f"{prefix}-owner-verdict.png",
        owner_title,
        "Real player camera | whole-tile course | low storm-lull angle" if regatta else ("Real player camera | whole-tile composition | low first-world night" if ember_shore else ("Real player camera | whole-tile composition | low vacuum" if mare_claim else "Real player camera | whole-tile composition | low dusk")),
        ("run-camera", "overview", "low-sunset"),
        ("RUN", "OVERVIEW", "LOW STORM") if regatta else (("RUN", "OVERVIEW", "LOW FIRST-WORLD NIGHT") if ember_shore else (("RUN", "OVERVIEW", "LOW VACUUM") if mare_claim else ("RUN", "OVERVIEW", "LOW DUSK"))),
    )
    three_column_board(
        f"{prefix}-panorama-mood-ab.png",
        f"{family} PANORAMA V2 — MOUNTED SEPARATELY",
        "Before/mounted use identical framing; each panorama is one render-only ring",
        ("panorama-before", "panorama-mounted", "panorama-horizon"),
        ("BEFORE", "MOUNTED", "CENTER HORIZON"),
    )
    two_column_board(
        f"{prefix}-panorama-distance-gate.png",
        f"{family} CENTER-HORIZON GATE — DISTANCE, NEVER WALL OR CEILING",
        "Open water stays runtime-owned; tea haze, unequal weather banks, and mast cues read as distance" if regatta else ("Deep-ink star stipple quiets at the zenith; unequal gold veils and low shelves read as distance" if ember_shore else ("The zenith stays quiet; independent lunar ridges read as distance without atmosphere" if mare_claim else "The zenith stays quiet while asymmetric ridge and haze remain visible at the rim")),
        [(entry["name"], ARTIFACTS / f"{entry['key']}-panorama-horizon.png", f"{entry['name']} — {'LOW FIRST-WORLD NIGHT' if ember_shore else ('LOW VACUUM' if mare_claim else 'LOW DUSK')}", ARTIFACTS / f"{entry['key']}-low-sunset.png") for entry in MAPS],
    )
    build_mask_board(
        prefix,
        f"{family} MASK AGREEMENT — PUBLISHED TABLES ARE THE AUTHORITY",
        mask_subtitle,
    )
    if mare_claim:
        two_column_board(
            "mare-claim-earth-side-gate.png",
            "EARTH IS COMFORT, NOT WALLPAPER",
            "The Mare keeps one soft blue-green cameo; the opposite Far Side view contains no Earth",
            [("EARTH-FACING NEAR SIDE", ARTIFACTS / "mare-claim-panorama-horizon.png", "OPPOSITE FAR SIDE", ARTIFACTS / "mare-claim-panorama-far-side.png")],
        )


if __name__ == "__main__":
    main()
