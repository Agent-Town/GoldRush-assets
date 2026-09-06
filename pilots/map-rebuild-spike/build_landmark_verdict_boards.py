"""Assemble owner boards for the seven mounted landmark packs."""

import os
import json
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
INK = (10, 9, 7)
GOLD = (224, 187, 92)

MAPS = [
    ("THE CLAIM", "the-claim", ROOT / "assets/raw/plate-contract-the-claim.png", "owner-run-camera-sculpted.png"),
    ("DRY GULCH", "dry-gulch", ROOT / "assets/raw/plate-contract-dry-gulch.png", "dry-gulch-run-camera.png"),
    ("TWIN BANKS", "twin-banks", ROOT / "assets/raw/plate-contract-twin-banks.png", "twin-banks-run-camera-unique.png"),
    ("NIGHT SHIFT", "night-shift", ROOT / "assets/raw/plate-contract-night-shift.png", "night-shift-run-camera-unique.png"),
    ("BARON", "baron", ROOT / "assets/raw/plate-contract-baron.png", "baron-run-camera-unique.png"),
    ("THE HILL MINE", "hill-mine", ROOT / "assets/raw/plate-contract-hill-mine.png", "hill-mine-run-camera.png"),
    ("THE TRESTLE", "trestle", ROOT / "artifacts/e2-trestle/desktop-chrome-crossing.png", "trestle-run-camera.png"),
]


def font(size):
    for candidate in (Path("/System/Library/Fonts/Supplemental/Arial.ttf"), Path("/System/Library/Fonts/Helvetica.ttc")):
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def fitted(path, size):
    with Image.open(path) as source:
        return ImageOps.fit(source.convert("RGB"), size, method=Image.Resampling.LANCZOS)


def contained(path, size, background=INK):
    with Image.open(path) as source:
        image = source.convert("RGB")
        image.thumbnail(size, resample=Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", size, background)
        canvas.paste(image, ((size[0] - image.width) // 2, (size[1] - image.height) // 2))
        return canvas


def centered(draw, bounds, label, size):
    x0, y0, x1, y1 = bounds
    text_font = font(size)
    box = draw.textbbox((0, 0), label, font=text_font)
    draw.text(((x0 + x1 - box[2] + box[0]) / 2, (y0 + y1 - box[3] + box[1]) / 2 - box[1]), label, font=text_font, fill=GOLD)


def build_verdict_board():
    canvas = Image.new("RGB", (1920, 2884), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 54), "LANDMARK SOURCE LADDER — SEVEN MOUNTED MAP PACKS", 30)
    centered(draw, (0, 48, 1920, 92), "Same-world source | separate grit-dressed bodies | mounted at the real run camera", 17)
    y = 112
    for name, key, source, _before in MAPS:
        labels = (f"{name} — SOURCE", "PACK BODIES", "MOUNTED")
        paths = (source, ARTIFACTS / f"{key}-landmarks-pack.png", ARTIFACTS / f"{key}-landmarks-mounted.png")
        for column, (label, path) in enumerate(zip(labels, paths)):
            x = column * 640
            centered(draw, (x, y, x + 640, y + 36), label, 17)
            canvas.paste(fitted(path, (640, 360)), (x, y + 36))
        y += 396
    canvas.save(ARTIFACTS / "all-landmark-packs-verdict.png", optimize=True)


def build_proxy_ab():
    canvas = Image.new("RGB", (1920, 4144), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 54), "LANDMARK A/B — COMPOSITION PROXIES TO MOUNTED BODIES", 30)
    centered(draw, (0, 48, 1920, 92), "Terrain and simulation are unchanged; only separate render-only landmark bodies are added", 17)
    y = 112
    for name, key, _source, before in MAPS:
        centered(draw, (0, y, 960, y + 36), f"{name} — PROXY COMPOSITION", 18)
        centered(draw, (960, y, 1920, y + 36), f"{name} — MOUNTED PACK", 18)
        canvas.paste(fitted(ARTIFACTS / before, (960, 540)), (0, y + 36))
        canvas.paste(fitted(ARTIFACTS / f"{key}-landmarks-mounted.png", (960, 540)), (960, y + 36))
        y += 576
    canvas.save(ARTIFACTS / "all-landmark-packs-proxy-ab.png", optimize=True)


def build_regatta_turntable():
    canvas = Image.new("RGB", (1920, 1160), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "REGATTA LANDMARK BODIES — FOUR ANGLES", 30)
    centered(draw, (0, 48, 1920, 76), "Full-wrap inspection; all eight bodies share one painted E5 atlas", 17)
    centered(draw, (0, 72, 1920, 100), "FRONT: start | finish | NW anchor | mid anchor    BACK: NE anchor | raft port | raft starboard | judge", 14)
    angle_labels = ("FRONT", "STARBOARD", "REAR", "PORT")
    for index in range(4):
        x, y = (index % 2) * 960, 100 + (index // 2) * 530
        canvas.paste(fitted(ARTIFACTS / f"regatta-landmarks-angle-{index + 1}.png", (960, 530)), (x, y))
        draw.rectangle((x + 12, y + 12, x + 168, y + 46), fill=INK)
        draw.text((x + 24, y + 18), angle_labels[index], font=font(16), fill=GOLD)
    canvas.save(ARTIFACTS / "regatta-landmarks-turntable.png", optimize=True)


def build_regatta_verdict():
    contract = json.loads(
        (ROOT / "assets/pilots/map-rebuild-spike/landmarks/regatta/regatta-landmark-pack-contract.json").read_text(encoding="utf-8")
    )
    base = contract["referenceBase"]
    canvas = Image.new("RGB", (1920, 1008), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "THE REGATTA — LANDMARK BODY VERDICT", 30)
    centered(draw, (0, 48, 1920, 84), f"Fresh reference {base[:12]} | mounts pending 3D-D interlock", 17)
    top = (
        ("E5 SHAPE + PAINT SOURCE", ROOT / "assets/raw/plate-e5-bld-claimboat.png"),
        ("EIGHT PRODUCTION BODIES", ARTIFACTS / "regatta-landmarks-pack.png"),
        ("COMPOSITION PROPOSAL", ARTIFACTS / "regatta-landmarks-proposed-overview.png"),
    )
    for column, (label, path) in enumerate(top):
        x = column * 640
        centered(draw, (x, 84, x + 640, 120), label, 17)
        canvas.paste(fitted(path, (640, 320)), (x, 120))
    centered(draw, (0, 440, 960, 476), "REAL RUN CAMERA — PROPOSED", 18)
    centered(draw, (960, 440, 1920, 476), "FOUR-ANGLE BODY CHECK", 18)
    canvas.paste(fitted(ARTIFACTS / "regatta-landmarks-proposed.png", (960, 532)), (0, 476))
    canvas.paste(fitted(ARTIFACTS / "regatta-landmarks-turntable.png", (960, 532)), (960, 476))
    canvas.save(ARTIFACTS / "regatta-landmarks-verdict.png", optimize=True)


def build_incline_turntable():
    canvas = Image.new("RGB", (1920, 1160), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "THE INCLINE LANDMARK BODIES — FOUR ANGLES", 30)
    centered(draw, (0, 48, 1920, 76), "Full-wrap inspection; five E2 haul-line bodies share one steamworks atlas", 17)
    centered(draw, (0, 72, 1920, 100), "ENGINE CRANE | WEST BRAKE | EAST BRAKE | CABLE HOUSE | FORD PUMP", 14)
    angle_labels = ("FRONT", "STARBOARD", "REAR", "PORT")
    for index in range(4):
        x, y = (index % 2) * 960, 100 + (index // 2) * 530
        canvas.paste(fitted(ARTIFACTS / f"incline-landmarks-angle-{index + 1}.png", (960, 530)), (x, y))
        draw.rectangle((x + 12, y + 12, x + 168, y + 46), fill=INK)
        draw.text((x + 24, y + 18), angle_labels[index], font=font(16), fill=GOLD)
    canvas.save(ARTIFACTS / "incline-landmarks-turntable.png", optimize=True)


def build_incline_verdict():
    contract = json.loads(
        (ROOT / "assets/pilots/map-rebuild-spike/landmarks/incline/incline-landmark-pack-contract.json").read_text(encoding="utf-8")
    )
    base = contract["referenceBase"]
    canvas = Image.new("RGB", (1920, 1008), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "THE INCLINE — LANDMARK BODY VERDICT", 30)
    centered(draw, (0, 48, 1920, 84), f"Fresh reference {base[:12]} | mounts pending 3D-D interlock", 17)
    top = (
        ("E2 PAINT + SHAPE SOURCE", ROOT / "assets/processed/kit-era-2.png"),
        ("FIVE PRODUCTION BODIES", ARTIFACTS / "incline-landmarks-pack.png"),
        ("GOLD PADS | TEAL WATER | RED RAILS | GREEN HARVEST | WHITE BODIES", ARTIFACTS / "incline-landmarks-clearance-overlay.png"),
    )
    for column, (label, path) in enumerate(top):
        x = column * 640
        centered(draw, (x, 84, x + 640, 120), label, 13 if column == 2 else 17)
        canvas.paste(fitted(path, (640, 320)), (x, 120))
    centered(draw, (0, 440, 960, 476), "REAL RUN CAMERA — PROPOSED", 18)
    centered(draw, (960, 440, 1920, 476), "FOUR-ANGLE BODY CHECK", 18)
    canvas.paste(fitted(ARTIFACTS / "incline-landmarks-proposed.png", (960, 532)), (0, 476))
    canvas.paste(fitted(ARTIFACTS / "incline-landmarks-turntable.png", (960, 532)), (960, 476))
    canvas.save(ARTIFACTS / "incline-landmarks-verdict.png", optimize=True)


def build_mare_claim_turntable():
    canvas = Image.new("RGB", (1920, 1160), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "MARE CLAIM LANDMARK BODIES — FOUR ANGLES", 30)
    centered(draw, (0, 48, 1920, 76), "Full-wrap inspection; five E8 bodies share one silver-teal orbital-grit atlas", 17)
    centered(draw, (0, 72, 1920, 100), "EARTHRISE ARRAY | TUBE GANTRY | CORE YARD | WEST CATCHER | EAST CATCHER", 14)
    angle_labels = ("FRONT", "STARBOARD", "REAR", "PORT")
    for index in range(4):
        x, y = (index % 2) * 960, 100 + (index // 2) * 530
        canvas.paste(fitted(ARTIFACTS / f"mare-claim-landmarks-angle-{index + 1}.png", (960, 530)), (x, y))
        draw.rectangle((x + 12, y + 12, x + 168, y + 46), fill=INK)
        draw.text((x + 24, y + 18), angle_labels[index], font=font(16), fill=GOLD)
    canvas.save(ARTIFACTS / "mare-claim-landmarks-turntable.png", optimize=True)


def build_mare_claim_verdict():
    contract = json.loads(
        (ROOT / "assets/pilots/map-rebuild-spike/landmarks/mare-claim/mare-claim-landmark-pack-contract.json").read_text(encoding="utf-8")
    )
    base = contract["referenceBase"]
    canvas = Image.new("RGB", (1920, 1008), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "MARE CLAIM — LANDMARK BODY VERDICT", 30)
    centered(draw, (0, 48, 1920, 84), f"Fresh reference {base[:12]} | mounts pending 3D-D interlock", 17)
    top = (
        ("E8 PAINT + SHAPE SOURCE", ROOT / "assets/raw/plate-e8-bld-set.png"),
        ("FIVE PRODUCTION BODIES", ARTIFACTS / "mare-claim-landmarks-pack.png"),
        ("GOLD PADS | RED TUBE | ORANGE ARC | TEAL HARVEST | WHITE BODIES", ARTIFACTS / "mare-claim-landmarks-clearance-overlay.png"),
    )
    for column, (label, path) in enumerate(top):
        x = column * 640
        centered(draw, (x, 84, x + 640, 120), label, 13 if column == 2 else 17)
        canvas.paste(fitted(path, (640, 320)), (x, 120))
    centered(draw, (0, 440, 960, 476), "REAL RUN CAMERA — PROPOSED", 18)
    centered(draw, (960, 440, 1920, 476), "FOUR-ANGLE BODY CHECK", 18)
    canvas.paste(fitted(ARTIFACTS / "mare-claim-landmarks-proposed.png", (960, 532)), (0, 476))
    canvas.paste(fitted(ARTIFACTS / "mare-claim-landmarks-turntable.png", (960, 532)), (960, 476))
    canvas.save(ARTIFACTS / "mare-claim-landmarks-verdict.png", optimize=True)


def build_variant_turntable(key, title, subtitle, body_label):
    canvas = Image.new("RGB", (1920, 1160), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), f"{title} LANDMARK BODIES — FOUR ANGLES", 30)
    centered(draw, (0, 48, 1920, 76), subtitle, 17)
    centered(draw, (0, 72, 1920, 100), body_label, 14)
    for index, label in enumerate(("FRONT", "STARBOARD", "REAR", "PORT")):
        x, y = (index % 2) * 960, 100 + (index // 2) * 530
        canvas.paste(fitted(ARTIFACTS / f"{key}-landmarks-angle-{index + 1}.png", (960, 530)), (x, y))
        draw.rectangle((x + 12, y + 12, x + 168, y + 46), fill=INK)
        draw.text((x + 24, y + 18), label, font=font(16), fill=GOLD)
    canvas.save(ARTIFACTS / f"{key}-landmarks-turntable.png", optimize=True)


def build_variant_verdict(key, title, source, source_label, clearance_label):
    contract = json.loads((ROOT / f"assets/pilots/map-rebuild-spike/landmarks/{key}/{key}-landmark-pack-contract.json").read_text(encoding="utf-8"))
    canvas = Image.new("RGB", (1920, 1008), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), f"{title} — LANDMARK BODY VERDICT", 30)
    centered(draw, (0, 48, 1920, 84), f"Fresh reference {contract['referenceBase'][:12]} | five canonical reuse-tile mounts", 17)
    top = (
        (source_label, source),
        ("FIVE PRODUCTION BODIES", ARTIFACTS / f"{key}-landmarks-pack.png"),
        (clearance_label, ARTIFACTS / f"{key}-landmarks-clearance-overlay.png"),
    )
    for column, (label, path) in enumerate(top):
        x = column * 640
        centered(draw, (x, 84, x + 640, 120), label, 13 if column == 2 else 17)
        canvas.paste(fitted(path, (640, 320)), (x, 120))
    centered(draw, (0, 440, 960, 476), "EXACT REUSE-TILE RUN CAMERA", 18)
    centered(draw, (960, 440, 1920, 476), "OVERVIEW + FOUR-ANGLE CHECK", 18)
    canvas.paste(fitted(ARTIFACTS / f"{key}-landmarks-mounted.png", (960, 532)), (0, 476))
    canvas.paste(fitted(ARTIFACTS / f"{key}-landmarks-mounted-overview.png", (960, 266)), (960, 476))
    canvas.paste(fitted(ARTIFACTS / f"{key}-landmarks-turntable.png", (960, 266)), (960, 742))
    canvas.save(ARTIFACTS / f"{key}-landmarks-verdict.png", optimize=True)


def build_boneyard_verdict():
    key = "boneyard"
    contract = json.loads((ROOT / f"assets/pilots/map-rebuild-spike/landmarks/{key}/{key}-landmark-pack-contract.json").read_text(encoding="utf-8"))
    canvas = Image.new("RGB", (1920, 1008), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "THE BONEYARD — LANDMARK BODY VERDICT", 30)
    centered(draw, (0, 48, 1920, 84), f"Fresh reference {contract['referenceBase'][:12]} | twelve exact canonical salvage mounts", 17)
    top = (
        ("E4 PAINT + SHAPE SOURCE", ROOT / "assets/raw/plate-e4-bld-set.png"),
        ("TWELVE PRODUCTION BODIES", ARTIFACTS / "boneyard-landmarks-pack.png"),
        ("TEAL PADS | ORANGE ROADS | GREEN SALVAGE | RED SLEEPER | WHITE BODIES", ARTIFACTS / "boneyard-landmarks-clearance-overlay.png"),
    )
    for column, (label, path) in enumerate(top):
        x = column * 640
        centered(draw, (x, 84, x + 640, 120), label, 12 if column == 2 else 17)
        canvas.paste(fitted(path, (640, 320)), (x, 120))
    centered(draw, (0, 440, 960, 476), "EXACT TERRAIN RUN CAMERA — MOUNTED", 18)
    centered(draw, (960, 440, 1920, 476), "OVERVIEW + FOUR-ANGLE CHECK", 18)
    canvas.paste(fitted(ARTIFACTS / "boneyard-landmarks-mounted.png", (960, 532)), (0, 476))
    canvas.paste(fitted(ARTIFACTS / "boneyard-landmarks-mounted-overview.png", (960, 266)), (960, 476))
    canvas.paste(fitted(ARTIFACTS / "boneyard-landmarks-turntable.png", (960, 266)), (960, 742))
    canvas.save(ARTIFACTS / "boneyard-landmarks-verdict.png", optimize=True)


def build_long_road_clearance_board():
    """Pair the full 400 m proof with readable, exact-body AABB crops."""
    source_path = ARTIFACTS / "long-road-landmarks-clearance-map.png"
    canvas = Image.new("RGB", (1280, 720), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1280, 38), "THE LONG ROAD — FULL ROUTE + FIVE EXACT BODY AABBS", 22)
    centered(draw, (0, 34, 1280, 62), "White crossed boxes are the mounted GLB bounds; route truth remains visible underneath", 13)
    with Image.open(source_path) as source_file:
        source = source_file.convert("RGB")
        # The source is deliberately a distant, orthographic 400 m map. Keep it
        # whole above, then enlarge each exact mount without changing the proof.
        canvas.paste(ImageOps.fit(source, (1280, 300), method=Image.Resampling.LANCZOS), (0, 62))
        stops = (
            ("LEAD HAULER", 348, 356),
            ("WEST STOP", 419, 333),
            ("MIDDLE STOP", 640, 379),
            ("EAST STOP", 861, 333),
            ("RAILHEAD", 946, 356),
        )
        panel_width = 256
        for index, (label, center_x, center_y) in enumerate(stops):
            x = index * panel_width
            crop = source.crop((center_x - 78, center_y - 58, center_x + 78, center_y + 58))
            crop = ImageOps.fit(crop, (panel_width, 304), method=Image.Resampling.NEAREST)
            canvas.paste(crop, (x, 402))
            draw.rectangle((x + 1, 402, x + panel_width - 2, 705), outline=(236, 221, 176), width=2)
            centered(draw, (x, 364, x + panel_width, 400), label, 14)
    centered(draw, (0, 704, 1280, 720), "Exact contract mounts | no transform edits | all station bodies remain inside their rest-stop zones", 10)
    canvas.save(ARTIFACTS / "long-road-landmarks-clearance-overlay.png", optimize=True)


def build_long_road_route_tour():
    """Show every body at the locked gameplay angle, not only in overview."""
    canvas = Image.new("RGB", (1920, 1008), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 50), "THE LONG ROAD — FIVE-STOP GAMEPLAY-CAMERA TOUR", 28)
    centered(draw, (0, 46, 1920, 78), "Same 44 degree run camera and relative offset at every canonical mount", 15)
    labels = (
        "WEST WAY STATION",
        "MIDDLE WAY STATION",
        "EAST WAY STATION",
        "CONVOY LEAD HAULER",
        "EAST RAILHEAD",
    )
    panels = (
        (0, 110, 640, 450),
        (640, 110, 640, 450),
        (1280, 110, 640, 450),
        (0, 592, 960, 416),
        (960, 592, 960, 416),
    )
    for index, (label, (x, y, width, height)) in enumerate(zip(labels, panels), 1):
        centered(draw, (x, y - 30, x + width, y), label, 15)
        canvas.paste(fitted(ARTIFACTS / f"long-road-landmarks-route-{index}.png", (width, height)), (x, y))
    canvas.save(ARTIFACTS / "long-road-landmarks-route-tour.png", optimize=True)


def build_long_road_verdict():
    key = "long-road"
    contract = json.loads((ROOT / f"assets/pilots/map-rebuild-spike/landmarks/{key}/{key}-landmark-pack-contract.json").read_text(encoding="utf-8"))
    canvas = Image.new("RGB", (1920, 1008), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "THE LONG ROAD — LANDMARK BODY VERDICT", 30)
    centered(draw, (0, 48, 1920, 84), f"Fresh reference {contract['referenceBase'][:12]} | five exact canonical moving-town mounts", 17)
    top = (
        ("E4 MOTOR PAINT + SHAPE SOURCE", ROOT / "assets/processed/kit-era-4.png"),
        ("FIVE PRODUCTION BODIES", ARTIFACTS / "long-road-landmarks-pack.png"),
        ("TEAL STOPS | ORANGE ROADS | GOLD ROUTE | WHITE CROSSED AABBS", ARTIFACTS / "long-road-landmarks-clearance-overlay.png"),
    )
    for column, (label, path) in enumerate(top):
        x = column * 640
        centered(draw, (x, 84, x + 640, 120), label, 12 if column == 2 else 17)
        canvas.paste(fitted(path, (640, 320)), (x, 120))
    centered(draw, (0, 440, 960, 476), "EXACT TERRAIN RUN CAMERA — MOUNTED", 18)
    centered(draw, (960, 440, 1920, 476), "400 M OVERVIEW + FIVE-STOP RUN-CAMERA TOUR", 18)
    canvas.paste(fitted(ARTIFACTS / "long-road-landmarks-mounted.png", (960, 532)), (0, 476))
    canvas.paste(fitted(ARTIFACTS / "long-road-landmarks-mounted-overview.png", (960, 266)), (960, 476))
    canvas.paste(fitted(ARTIFACTS / "long-road-landmarks-route-tour.png", (960, 266)), (960, 742))
    canvas.save(ARTIFACTS / "long-road-landmarks-verdict.png", optimize=True)


def build_old_canal_turntable():
    canvas = Image.new("RGB", (1920, 1160), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "OLD CANAL LANDMARK BODIES — FOUR ANGLES", 30)
    centered(draw, (0, 48, 1920, 76), "Full-wrap inspection; five E9 wrong-survey bodies share one dry canal-work atlas", 17)
    centered(draw, (0, 72, 1920, 100), "SURVEY RIG | SEGMENT A | SEGMENT B | SEGMENT C | OUTFLOW GATE", 14)
    angle_labels = ("FRONT", "STARBOARD", "REAR", "PORT")
    for index in range(4):
        x, y = (index % 2) * 960, 100 + (index // 2) * 530
        canvas.paste(fitted(ARTIFACTS / f"old-canal-landmarks-angle-{index + 1}.png", (960, 530)), (x, y))
        draw.rectangle((x + 12, y + 12, x + 168, y + 46), fill=INK)
        draw.text((x + 24, y + 18), angle_labels[index], font=font(16), fill=GOLD)
    canvas.save(ARTIFACTS / "old-canal-landmarks-turntable.png", optimize=True)


def build_old_canal_verdict():
    contract = json.loads((ROOT / "assets/pilots/map-rebuild-spike/landmarks/old-canal/old-canal-landmark-pack-contract.json").read_text(encoding="utf-8"))
    canvas = Image.new("RGB", (1920, 1008), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "THE OLD CANAL — LANDMARK BODY VERDICT", 30)
    centered(draw, (0, 48, 1920, 84), f"Fresh reference {contract['referenceBase'][:12]} | five canonical wrong-survey mounts", 17)
    top = (
        ("E9 PAINT + SHAPE SOURCE", ROOT / "assets/raw/plate-e9-bld-canal-works.png"),
        ("FIVE PRODUCTION BODIES", ARTIFACTS / "old-canal-landmarks-pack.png"),
        ("GOLD PADS | RED DECISIONS | TEAL OLD CUT | WHITE BODIES", ARTIFACTS / "old-canal-landmarks-clearance-overlay.png"),
    )
    for column, (label, path) in enumerate(top):
        x = column * 640
        centered(draw, (x, 84, x + 640, 120), label, 14 if column == 2 else 17)
        canvas.paste(fitted(path, (640, 320)), (x, 120))
    centered(draw, (0, 440, 960, 476), "EXACT RUNTIME CAMERA — CENTER DECISION", 18)
    centered(draw, (960, 440, 1920, 476), "WHOLE-CANAL OVERVIEW + FOUR-ANGLE CHECK", 18)
    canvas.paste(fitted(ARTIFACTS / "old-canal-landmarks-mounted.png", (960, 532)), (0, 476))
    canvas.paste(fitted(ARTIFACTS / "old-canal-landmarks-mounted-overview.png", (960, 266)), (960, 476))
    canvas.paste(fitted(ARTIFACTS / "old-canal-landmarks-turntable.png", (960, 266)), (960, 742))
    canvas.save(ARTIFACTS / "old-canal-landmarks-verdict.png", optimize=True)


def build_archive_world_turntable():
    canvas = Image.new("RGB", (1920, 1160), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "ARCHIVE WORLD LANDMARK BODIES — FOUR ANGLES", 30)
    centered(draw, (0, 48, 1920, 76), "Full-wrap inspection; five E10 memory-ruin bodies share one deep-ink archive atlas", 17)
    centered(draw, (0, 72, 1920, 100), "ENTRY GATE | WEST STACK | EAST STACK | WARNING SHELF | OURS-UNLESS", 14)
    angle_labels = ("FRONT", "STARBOARD", "REAR", "PORT")
    for index in range(4):
        x, y = (index % 2) * 960, 100 + (index // 2) * 530
        canvas.paste(fitted(ARTIFACTS / f"archive-world-landmarks-angle-{index + 1}.png", (960, 530)), (x, y))
        draw.rectangle((x + 12, y + 12, x + 168, y + 46), fill=INK)
        draw.text((x + 24, y + 18), angle_labels[index], font=font(16), fill=GOLD)
    canvas.save(ARTIFACTS / "archive-world-landmarks-turntable.png", optimize=True)


def build_archive_world_verdict():
    contract = json.loads((ROOT / "assets/pilots/map-rebuild-spike/landmarks/archive-world/archive-world-landmark-pack-contract.json").read_text(encoding="utf-8"))
    canvas = Image.new("RGB", (1920, 1008), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "ARCHIVE WORLD — LANDMARK BODY VERDICT", 30)
    centered(draw, (0, 48, 1920, 84), f"Fresh reference {contract['referenceBase'][:12]} | five canonical memory-ruin mounts", 17)
    top = (
        ("E10 PAINT + SHAPE SOURCE", ROOT / "assets/raw/plate-e10-worlds.png"),
        ("FIVE PRODUCTION BODIES", ARTIFACTS / "archive-world-landmarks-pack.png"),
        ("GOLD PADS | TEAL WINGS | RED EMPTY SHELF | WHITE BODIES", ARTIFACTS / "archive-world-landmarks-clearance-overlay.png"),
    )
    for column, (label, path) in enumerate(top):
        x = column * 640
        centered(draw, (x, 84, x + 640, 120), label, 14 if column == 2 else 17)
        canvas.paste(fitted(path, (640, 320)), (x, 120))
    centered(draw, (0, 440, 960, 476), "EXACT RUNTIME CAMERA — CENTRAL MEMORY CUT STAYS EMPTY", 18)
    centered(draw, (960, 440, 1920, 476), "WHOLE-ARCHIVE OVERVIEW + FOUR-ANGLE CHECK", 18)
    canvas.paste(fitted(ARTIFACTS / "archive-world-landmarks-mounted.png", (960, 532)), (0, 476))
    canvas.paste(fitted(ARTIFACTS / "archive-world-landmarks-mounted-overview.png", (960, 266)), (960, 476))
    canvas.paste(fitted(ARTIFACTS / "archive-world-landmarks-turntable.png", (960, 266)), (960, 742))
    canvas.save(ARTIFACTS / "archive-world-landmarks-verdict.png", optimize=True)


def build_dome_basin_turntable():
    canvas = Image.new("RGB", (1920, 1160), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "DOME BASIN LANDMARK BODIES — FOUR ANGLES", 30)
    centered(draw, (0, 48, 1920, 76), "Full-wrap inspection; five E9 bodies share one redfields canal-work atlas", 17)
    centered(draw, (0, 72, 1920, 100), "CANAL GATE | ICE HOIST | SEED WEATHER | ARK SCAFFOLD | DUST WARNING", 14)
    angle_labels = ("FRONT", "STARBOARD", "REAR", "PORT")
    for index in range(4):
        x, y = (index % 2) * 960, 100 + (index // 2) * 530
        canvas.paste(fitted(ARTIFACTS / f"dome-basin-landmarks-angle-{index + 1}.png", (960, 530)), (x, y))
        draw.rectangle((x + 12, y + 12, x + 168, y + 46), fill=INK)
        draw.text((x + 24, y + 18), angle_labels[index], font=font(16), fill=GOLD)
    canvas.save(ARTIFACTS / "dome-basin-landmarks-turntable.png", optimize=True)


def build_dome_basin_verdict():
    contract = json.loads(
        (ROOT / "assets/pilots/map-rebuild-spike/landmarks/dome-basin/dome-basin-landmark-pack-contract.json").read_text(encoding="utf-8")
    )
    base = contract["referenceBase"]
    canvas = Image.new("RGB", (1920, 1008), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "DOME BASIN — LANDMARK BODY VERDICT", 30)
    centered(draw, (0, 48, 1920, 84), f"Fresh reference {base[:12]} | mounts pending 3D-D interlock", 17)
    top = (
        ("E9 PAINT + SHAPE SOURCE", ROOT / "assets/raw/plate-e9-bld-canal-works.png"),
        ("FIVE PRODUCTION BODIES", ARTIFACTS / "dome-basin-landmarks-pack.png"),
        ("GOLD PADS | TEAL CANAL | RED ROUTE | GREEN HARVEST | WHITE BODIES", ARTIFACTS / "dome-basin-landmarks-clearance-overlay.png"),
    )
    for column, (label, path) in enumerate(top):
        x = column * 640
        centered(draw, (x, 84, x + 640, 120), label, 13 if column == 2 else 17)
        canvas.paste(fitted(path, (640, 320)), (x, 120))
    centered(draw, (0, 440, 960, 476), "REAL RUN CAMERA — PROPOSED", 18)
    centered(draw, (960, 440, 1920, 476), "FOUR-ANGLE BODY CHECK", 18)
    canvas.paste(fitted(ARTIFACTS / "dome-basin-landmarks-proposed.png", (960, 532)), (0, 476))
    canvas.paste(fitted(ARTIFACTS / "dome-basin-landmarks-turntable.png", (960, 532)), (960, 476))
    canvas.save(ARTIFACTS / "dome-basin-landmarks-verdict.png", optimize=True)


def build_ember_shore_turntable():
    canvas = Image.new("RGB", (1920, 1160), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "EMBER SHORE LANDMARK BODIES — FOUR ANGLES", 30)
    centered(draw, (0, 48, 1920, 76), "Full-wrap inspection; five E10 preserve-shore bodies share one deep-sky atlas", 17)
    centered(draw, (0, 72, 1920, 100), "LAST-WARM VENT | TITAN SHELF | VEIN MARKER | BRIDGE SCHOOL | PRESERVE RACK", 14)
    angle_labels = ("FRONT", "STARBOARD", "REAR", "PORT")
    for index in range(4):
        x, y = (index % 2) * 960, 100 + (index // 2) * 530
        canvas.paste(fitted(ARTIFACTS / f"ember-shore-landmarks-angle-{index + 1}.png", (960, 530)), (x, y))
        draw.rectangle((x + 12, y + 12, x + 168, y + 46), fill=INK)
        draw.text((x + 24, y + 18), angle_labels[index], font=font(16), fill=GOLD)
    canvas.save(ARTIFACTS / "ember-shore-landmarks-turntable.png", optimize=True)


def build_ember_shore_verdict():
    contract = json.loads(
        (ROOT / "assets/pilots/map-rebuild-spike/landmarks/ember-shore/ember-shore-landmark-pack-contract.json").read_text(encoding="utf-8")
    )
    base = contract["referenceBase"]
    canvas = Image.new("RGB", (1920, 1008), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "EMBER SHORE — LANDMARK BODY VERDICT", 30)
    centered(draw, (0, 48, 1920, 84), f"Fresh reference {base[:12]} | mounts pending 3D-D interlock", 17)
    top = (
        ("E10 PAINT + SHAPE SOURCE", ROOT / "assets/raw/plate-e10-worlds.png"),
        ("FIVE PRODUCTION BODIES", ARTIFACTS / "ember-shore-landmarks-pack.png"),
        ("GOLD PADS | RED VEINS | TEAL VENT | WHITE BODIES", ARTIFACTS / "ember-shore-landmarks-clearance-overlay.png"),
    )
    for column, (label, path) in enumerate(top):
        x = column * 640
        centered(draw, (x, 84, x + 640, 120), label, 14 if column == 2 else 17)
        canvas.paste(fitted(path, (640, 320)), (x, 120))
    centered(draw, (0, 440, 960, 476), "REAL RUN CAMERA — PROPOSED", 18)
    centered(draw, (960, 440, 1920, 476), "FOUR-ANGLE BODY CHECK", 18)
    canvas.paste(fitted(ARTIFACTS / "ember-shore-landmarks-proposed.png", (960, 532)), (0, 476))
    canvas.paste(fitted(ARTIFACTS / "ember-shore-landmarks-turntable.png", (960, 532)), (960, 476))
    canvas.save(ARTIFACTS / "ember-shore-landmarks-verdict.png", optimize=True)


def build_mare_claim_turntable():
    canvas = Image.new("RGB", (1920, 1160), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "MARE CLAIM LANDMARK BODIES — FOUR ANGLES", 30)
    centered(draw, (0, 48, 1920, 76), "Full-wrap inspection; five E8 bodies share one lunar brass/teal atlas", 17)
    centered(draw, (0, 72, 1920, 100), "EARTHRISE ARRAY | LAVA TUBE GANTRY | CORE YARD | WEST CATCHER | EAST CATCHER", 14)
    angle_labels = ("FRONT", "STARBOARD", "REAR", "PORT")
    for index in range(4):
        x, y = (index % 2) * 960, 100 + (index // 2) * 530
        canvas.paste(fitted(ARTIFACTS / f"mare-claim-landmarks-angle-{index + 1}.png", (960, 530)), (x, y))
        draw.rectangle((x + 12, y + 12, x + 168, y + 46), fill=INK)
        draw.text((x + 24, y + 18), angle_labels[index], font=font(16), fill=GOLD)
    canvas.save(ARTIFACTS / "mare-claim-landmarks-turntable.png", optimize=True)


def build_mare_claim_verdict():
    contract = json.loads(
        (ROOT / "assets/pilots/map-rebuild-spike/landmarks/mare-claim/mare-claim-landmark-pack-contract.json").read_text(encoding="utf-8")
    )
    base = contract["referenceBase"]
    canvas = Image.new("RGB", (1920, 1008), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "MARE CLAIM — LANDMARK BODY VERDICT", 30)
    centered(draw, (0, 48, 1920, 84), f"Fresh reference {base[:12]} | mounts pending 3D-D interlock", 17)
    top = (
        ("E8 PAINT + SHAPE SOURCE", ROOT / "assets/raw/plate-e8-bld-set.png"),
        ("FIVE PRODUCTION BODIES", ARTIFACTS / "mare-claim-landmarks-pack.png"),
        ("GOLD PADS | RED TUBE | ORANGE ARC | TEAL HARVEST | WHITE BODIES", ARTIFACTS / "mare-claim-landmarks-clearance-overlay.png"),
    )
    for column, (label, path) in enumerate(top):
        x = column * 640
        centered(draw, (x, 84, x + 640, 120), label, 13 if column == 2 else 17)
        canvas.paste(fitted(path, (640, 320)), (x, 120))
    centered(draw, (0, 440, 960, 476), "REAL RUN CAMERA — PROPOSED", 18)
    centered(draw, (960, 440, 1920, 476), "FOUR-ANGLE BODY CHECK", 18)
    canvas.paste(fitted(ARTIFACTS / "mare-claim-landmarks-proposed.png", (960, 532)), (0, 476))
    canvas.paste(fitted(ARTIFACTS / "mare-claim-landmarks-turntable.png", (960, 532)), (960, 476))
    canvas.save(ARTIFACTS / "mare-claim-landmarks-verdict.png", optimize=True)


def build_dust_flats_verdict():
    contract = json.loads(
        (ROOT / "assets/pilots/map-rebuild-spike/landmarks/dust-flats/dust-flats-landmark-pack-contract.json").read_text(encoding="utf-8")
    )
    canvas = Image.new("RGB", (1920, 1008), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "DUST FLATS — LANDMARK BODY VERDICT", 30)
    centered(draw, (0, 48, 1920, 84), f"Fresh reference {contract['referenceBase'][:12]} | mounts pending 3D-D interlock", 17)
    top = (
        ("E4 PAINT + SHAPE SOURCE", ROOT / "assets/raw/plate-e4-bld-set.png"),
        ("FIVE PRODUCTION BODIES", ARTIFACTS / "dust-flats-landmarks-pack.png"),
        ("NINE-CONSTRAINT CLEARANCE PROOF", ARTIFACTS / "dust-flats-landmarks-clearance-board.png"),
    )
    for column, (label, path) in enumerate(top):
        x = column * 640
        centered(draw, (x, 84, x + 640, 120), label, 12 if column == 2 else 17)
        canvas.paste(contained(path, (640, 320)) if column == 2 else fitted(path, (640, 320)), (x, 120))
    centered(draw, (0, 440, 960, 476), "REAL RUN CAMERA — PROPOSED", 18)
    centered(draw, (960, 440, 1920, 476), "FOUR-ANGLE BODY CHECK", 18)
    canvas.paste(fitted(ARTIFACTS / "dust-flats-landmarks-proposed.png", (960, 532)), (0, 476))
    canvas.paste(fitted(ARTIFACTS / "dust-flats-landmarks-turntable.png", (960, 532)), (960, 476))
    canvas.save(ARTIFACTS / "dust-flats-landmarks-verdict.png", optimize=True)


def build_dust_flats_comparison():
    metrics = json.loads((ARTIFACTS / "dust-flats-landmarks/comparison/report/visual-parity-diff.json").read_text(encoding="utf-8"))["results"][0]
    canvas = Image.new("RGB", (1920, 620), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 50), "DUST FLATS — FIXED RUN-CAMERA COMPARISON", 28)
    centered(
        draw, (0, 46, 1920, 82),
        f"Distance {metrics['parityDistance']:.5f} | edge energy {metrics['contentProxies']['edgeEnergyRatio']:.5f}x | luminance delta {metrics['contentProxies']['avgLuminanceDelta']:.5f}",
        15,
    )
    centered(draw, (0, 78, 960, 112), "BARE TERRAIN", 18)
    centered(draw, (960, 78, 1920, 112), "PROPOSED RENDER-ONLY BODIES", 18)
    canvas.paste(fitted(ARTIFACTS / "dust-flats-landmarks-bare-reference.png", (960, 508)), (0, 112))
    canvas.paste(fitted(ARTIFACTS / "dust-flats-landmarks-proposed.png", (960, 508)), (960, 112))
    canvas.save(ARTIFACTS / "dust-flats-landmarks-comparison-labelled.png", optimize=True)


def build_dust_flats_clearance_board():
    report = json.loads((ARTIFACTS / "dust-flats-landmarks/clearance-metrics.json").read_text(encoding="utf-8"))
    overlay_path = ARTIFACTS / "dust-flats-landmarks-clearance-overlay.png"
    canvas = Image.new("RGB", (1920, 1240), INK)
    draw = ImageDraw.Draw(canvas)
    centered(draw, (0, 0, 1920, 52), "DUST FLATS — CONSERVATIVE CLEARANCE PROOF", 28)
    centered(draw, (0, 48, 1920, 84), "Rotated GLB AABBs | preview transforms only | canonical mounts remain with 3D-D", 15)
    canvas.paste(fitted(overlay_path, (1120, 1120)), (0, 100))
    legend = (
        ("FIELDS", (242, 148, 20)), ("ORBIT RESERVE", (230, 26, 12)),
        ("ROAD SHOULDERS", (245, 82, 10)), ("DRY WASH", (13, 181, 168)),
        ("HARVEST", (77, 199, 56)), ("TAR SEAMS", (143, 56, 158)),
        ("LOSS STAKE", (214, 41, 15)), ("INITIAL SPAWN", (235, 26, 66)),
        ("LANDMARK AABBS", (240, 229, 168)),
    )
    for index, (label, color) in enumerate(legend):
        column, row = index % 2, index // 2
        x, y = 1140 + column * 380, 112 + row * 48
        draw.rectangle((x, y + 6, x + 28, y + 28), fill=color)
        draw.text((x + 40, y + 5), label, font=font(14), fill=GOLD)
    centered(draw, (1120, 352, 1920, 388), "FIVE WHITE-FOOTPRINT ZOOMS", 18)
    labels = {
        "north-railhead-storm-tower": "NORTH STORM TOWER",
        "west-road-wrecker-shed": "WEST WRECKER SHED",
        "east-horizon-fuel-reserve": "EAST FUEL RESERVE",
        "south-grade-charting-post": "SOUTH CHARTING POST",
        "dry-wash-recovery-gantry": "WASH RECOVERY GANTRY",
    }
    with Image.open(overlay_path) as source_file:
        source = source_file.convert("RGB")
        for index, (identifier, record) in enumerate(report["landmarks"].items()):
            column, row = index % 2, index // 2
            x, y = 1145 + column * 380, 396 + row * 270
            x0, x1, z0, z1 = record["aabb"]
            center_x, center_z = (x0 + x1) * 0.5, (z0 + z1) * 0.5
            pixel_x = int((center_x + 82.0) / 164.0 * source.width)
            pixel_y = int((82.0 - center_z) / 164.0 * source.height)
            crop = source.crop((pixel_x - 105, pixel_y - 105, pixel_x + 105, pixel_y + 105))
            crop = ImageOps.fit(crop, (220, 220), method=Image.Resampling.LANCZOS)
            canvas.paste(crop, (x, y))
            draw.text((x + 230, y + 50), labels[identifier], font=font(13), fill=GOLD)
            tightest = record["tightest"]
            draw.text((x + 230, y + 82), f"tightest: {tightest['constraint']}", font=font(12), fill=(226, 216, 176))
            draw.text((x + 230, y + 108), f"{tightest['meters']:.3f} m", font=font(17), fill=(242, 232, 190))
    canvas.save(ARTIFACTS / "dust-flats-landmarks-clearance-board.png", optimize=True)


def main():
    if sys.argv[1:] == ["long-road"]:
        build_variant_turntable(
            "long-road", "THE LONG ROAD", "Full-wrap inspection; five E4 moving-town bodies share one motor-warm atlas",
            "WEST FUEL STOP | MIDDLE REPAIR STOP | EAST RELAY STOP | LEAD HAULER | EAST RAILHEAD",
        )
        build_long_road_clearance_board()
        build_long_road_route_tour()
        build_long_road_verdict()
        return
    if sys.argv[1:] == ["boneyard"]:
        build_variant_turntable(
            "boneyard", "THE BONEYARD", "Full-wrap inspection; twelve E4 salvage relics share one dust-warm motor atlas",
            "FLIVVER ROWS | SPENT BOILERS | HAULER BEDS | HALF-BURIED SLEEPER | UNMARKED WAGON",
        )
        build_boneyard_verdict()
        return
    if sys.argv[1:] == ["eclipse"]:
        build_variant_turntable(
            "eclipse", "ECLIPSE", "Full-wrap inspection; five E8 solar-shadow instruments share one lunar brass/teal atlas",
            "SHADOW DIAL | WEST WITNESS | EAST WITNESS | LAUNCH GATE | DRIVER MARKER",
        )
        build_variant_verdict(
            "eclipse", "ECLIPSE", ROOT / "assets/raw/plate-e8-bld-set.png", "E8 PAINT + SHAPE SOURCE",
            "GOLD PADS | RED SHADOW | ORANGE RAIL | TEAL HARVEST | WHITE BODIES",
        )
        return
    if sys.argv[1:] == ["regatta"]:
        build_regatta_turntable()
        build_regatta_verdict()
        return
    if sys.argv[1:] == ["incline"]:
        build_incline_turntable()
        build_incline_verdict()
        return
    if sys.argv[1:] == ["dust-flats"]:
        build_variant_turntable(
            "dust-flats", "DUST FLATS", "Full-wrap inspection; five E4 motor-county bodies share one dust-warm brass/teal atlas",
            "STORM TOWER | WRECKER SHED | FUEL RESERVE | CHARTING POST | RECOVERY GANTRY",
        )
        build_dust_flats_comparison()
        build_dust_flats_clearance_board()
        build_dust_flats_verdict()
        return
    if sys.argv[1:] == ["mare-claim"]:
        build_mare_claim_turntable()
        build_mare_claim_verdict()
        return
    if sys.argv[1:] == ["old-canal"]:
        build_old_canal_turntable()
        build_old_canal_verdict()
        return
    if sys.argv[1:] == ["archive-world"]:
        build_archive_world_turntable()
        build_archive_world_verdict()
        return
    if sys.argv[1:] == ["dome-basin"]:
        build_dome_basin_turntable()
        build_dome_basin_verdict()
        return
    if sys.argv[1:] == ["ember-shore"]:
        build_ember_shore_turntable()
        build_ember_shore_verdict()
        return
    if sys.argv[1:] == ["mare-claim"]:
        build_mare_claim_turntable()
        build_mare_claim_verdict()
        return
    build_verdict_board()
    build_proxy_ab()


if __name__ == "__main__":
    main()
