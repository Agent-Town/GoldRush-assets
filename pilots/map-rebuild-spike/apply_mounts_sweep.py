"""Backfill canonical terrain mount records for merged landmark packs."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"

MOUNT_SPACE = {
    "coordinates": "game X/Y/Z",
    "positionY": "local offset added to Terrain.visualY at the mount X/Z",
    "rotation": "XYZ Euler radians",
    "scale": "XYZ multiplier",
    "ownership": "landmark assets mount at runtime and are never baked into terrain",
}

CANONICAL = {
    "regatta": None,
    "glow-mesa": [
        ("mesa-starstone-derrick", -56.0, 0.0, 50.0, 0.08, 1.0),
        ("six-vein-control-pylon", 0.0, 0.0, -7.0, 0.0, 1.0),
        ("isotope-cooling-rack", 28.0, 0.0, -59.0, -0.16, 1.0),
        ("west-herd-glow-gate", -56.0, 0.0, 16.0, 0.34, 1.0),
        ("east-herd-glow-gate", 56.0, 0.0, 16.0, -0.32, 1.0),
    ],
    "relay-valley": [
        ("west-ridge-dish-cluster", -56.0, 0.0, 30.0, 0.16, 1.0),
        ("east-ridge-dish-cluster", 56.0, 0.0, 30.0, -0.14, 1.0),
        ("dead-gap-charting-station", 0.0, 0.0, 18.0, 0.0, 1.08),
        ("valley-cable-drum-yard", -44.0, 0.0, -26.0, 0.22, 1.0),
        ("drone-recovery-beacon", 44.0, 0.0, -26.0, -0.20, 1.08),
    ],
    "mare-claim": [
        ("earthrise-listening-array", 0.0, 0.0, 56.0, 0.0, 1.0),
        ("lava-tube-survey-gantry", -42.0, 0.0, 28.0, 0.18, 1.0),
        ("regolith-core-yard", 22.0, 0.0, 18.0, -0.12, 1.0),
        ("west-rim-debris-catcher", -56.0, 0.0, 20.0, 0.16, 1.0),
        ("east-rim-debris-catcher", 56.0, 0.0, 20.0, -0.16, 1.0),
    ],
    "dome-basin": [
        ("canal-gate-works", -18.0, 0.0, 20.0, 0.24, 1.0),
        ("ice-quarry-hoist", -56.0, 0.0, 48.0, -0.12, 1.0),
        ("seed-row-weather-station", 50.0, 0.0, -25.0, -0.18, 1.0),
        ("ark-yard-scaffold", -56.0, 0.0, -44.0, 0.10, 1.0),
        ("dust-devil-warning-mast", 52.0, 0.0, 2.0, -0.10, 1.0),
    ],
    "ember-shore": [
        ("last-warm-vent-altar", 3.0, 0.0, -10.0, 0.0, 1.28),
        ("cooled-titan-shelf", 26.0, 0.0, 34.0, -0.18, 1.16),
        ("west-vein-cooling-marker", -36.0, 0.0, 18.0, 0.10, 1.18),
        ("center-vein-bridge-school", -12.0, 0.0, 24.0, -0.12, 1.18),
        ("shore-preserve-rack", 48.0, 0.0, -28.0, -0.18, 1.20),
    ],
    "pressure-garden": [
        ("garden-pressure-manifold", 0.0, 0.0, 4.0, 0.0, 1.0),
        ("west-terrace-pipe-header", -50.0, 0.0, 24.0, 0.18, 1.0),
        ("east-terrace-pipe-header", 50.0, 0.0, 24.0, -0.18, 1.0),
        ("coal-seam-service-winch", -42.0, 0.0, 40.0, 0.12, 1.0),
        ("water-band-pump-station", 42.0, 0.0, -6.0, -0.12, 1.0),
    ],
    "incline": [
        ("lower-yard-engine-crane", 2.0, 0.0, 21.8, 0.14, 1.05),
        ("west-line-brake-tower", -34.0, 0.0, 36.5, 0.18, 1.0),
        ("east-line-brake-tower", 34.0, 0.0, 35.0, -0.16, 1.0),
        ("upper-ore-cable-house", 22.0, 0.0, 29.0, -0.10, 1.0),
        ("ford-service-pump", 25.0, 0.0, 21.5, -0.12, 0.78),
    ],
    "blackout-ridge": [
        ("off-map-current-receiver", -36.0, 0.0, -44.0, 0.16, 1.0),
        ("trunk-line-breaker-shelter", -36.0, 0.0, -18.0, 0.22, 1.0),
        ("breath-bank-service-rack", 32.0, 0.0, 4.0, -0.16, 1.0),
        ("ridge-switch-house", 36.0, 0.0, 28.0, -0.18, 1.0),
        ("blackout-watch-lamp", 0.0, 0.0, 44.0, 3.1416, 1.0),
    ],
    "canyon-works": [
        ("sub-hall-dynamo-house", 0.0, 0.0, -54.0, 0.0, 1.0),
        ("west-switchback-line-house", -38.0, 0.0, -18.0, 0.18, 1.0),
        ("east-switchback-line-house", 38.0, 0.0, -18.0, -0.18, 1.0),
        ("dam-crest-gate-house", 0.0, 0.0, 8.0, 0.0, 1.0),
        ("downriver-tram-lamp", 44.0, 0.0, 42.0, -0.24, 1.0),
    ],
    "moth-season": [
        ("north-migration-watch-gate", 0.0, 0.0, 42.0, 3.1416, 1.0),
        ("south-quiet-road-gate", 0.0, 0.0, -42.0, 0.0, 1.0),
        ("west-lamplighter-refuge", -38.0, 0.0, 0.0, 0.18, 1.0),
        ("east-tithe-bell-house", 38.0, 0.0, 0.0, -0.18, 1.0),
        ("mothglass-counting-cage", 0.0, 0.0, 36.0, 3.1416, 1.0),
    ],
    "fairground": [
        ("south-midway-admission-arch", 0.0, 0.0, -42.0, 0.0, 1.0),
        ("west-current-calliope-wagon", -42.0, 0.0, 10.0, 0.16, 1.0),
        ("east-mothglass-prize-cage", 42.0, 0.0, 10.0, -0.16, 1.0),
        ("north-crowd-counting-rostrum", 0.0, 0.0, 34.0, 3.1416, 1.0),
        ("fair-bell-battery-kiosk", 8.0, 0.0, 34.0, -0.10, 1.0),
    ],
    "dust-flats": [
        ("north-railhead-storm-tower", 0.0, 0.0, 74.0, 3.1416, 1.0),
        ("west-road-wrecker-shed", -74.0, 0.0, 0.0, 0.22, 1.0),
        ("east-horizon-fuel-reserve", 74.0, 0.0, 0.0, -0.22, 1.0),
        ("south-grade-charting-post", 0.0, 0.0, -74.0, 0.0, 1.0),
        ("dry-wash-recovery-gantry", 24.0, 0.0, -54.0, -0.18, 1.0),
    ],
    "boneyard": None,
    "showroom": None,
    "half-life-hollow": None,
    "echo-canyon": None,
    "low-orbit": None,
    "seed-run": None,
    "devils-alley": None,
    "old-canal": None,
    "archive-world": None,
}

OUTSTANDING = (
    "blackout-ridge",
    "canyon-works",
    "moth-season",
    "fairground",
    "dust-flats",
    "boneyard",
)

FINAL_VARIANTS = {
    "picnic": {
        "base": "glow-mesa",
        "mask": "assets/contracts/epoch-6-atomic/mask-tables/e6-picnic.json",
        "reason": "maskTruth.tileId is e6-glow-mesa; duplicate terrain would violate the campaign reuse law",
        "mounts": [
            ("picnic-staging-gate", 0.0, 0.0, -54.0, 0.0, 1.0),
            ("west-picnic-blanket", -16.0, 0.0, 18.0, 0.08, 1.0),
            ("center-picnic-blanket", 0.0, 0.0, 26.0, 0.0, 1.0),
            ("east-picnic-blanket", 16.0, 0.0, 18.0, -0.08, 1.0),
            ("mesa-civilian-shade", 0.0, 0.0, 40.0, 3.1416, 1.0),
        ],
    },
    "dead-band": {
        "base": "relay-valley",
        "mask": "assets/contracts/epoch-7-signal/mask-tables/e7-dead-band.json",
        "reason": "maskTruth.tileId is e7-relay-valley; the dead-band is a signal-state variant on the accepted ridgeline tile",
        "mounts": [
            ("dead-band-yard-null-post", 0.0, 0.0, -40.0, 0.0, 1.0),
            ("west-old-tool-cache", -42.0, 0.0, 38.0, 0.16, 1.0),
            ("east-old-tool-cache", 42.0, 0.0, 38.0, -0.16, 1.0),
            ("iron-shadow-warning-frame", 0.0, 0.0, 6.0, 0.0, 1.0),
            ("north-silence-gate", 0.0, 0.0, 54.0, 3.1416, 1.0),
        ],
    },
    "relay-rush": {
        "base": "relay-valley",
        "mask": "assets/contracts/epoch-7-signal/mask-tables/e7-relay-rush.json",
        "reason": "maskTruth.tileId is e7-relay-valley; rush timing rides the existing relay placement puzzle",
        "mounts": [
            ("rush-start-horn", 0.0, 0.0, -50.0, 0.0, 1.0),
            ("rush-relay-r1-frame", -45.0, 0.0, 41.0, 0.10, 1.0),
            ("rush-relay-r2-frame", -25.0, 0.0, 41.0, 0.04, 1.0),
            ("rush-relay-r3-frame", 25.0, 0.0, 41.0, -0.04, 1.0),
            ("rush-relay-r4-frame", 45.0, 0.0, 41.0, -0.10, 1.0),
        ],
    },
    "far-side": {
        "base": "mare-claim",
        "mask": "assets/contracts/epoch-8-orbital/mask-tables/e8-far-side.json",
        "reason": "maskTruth.tileId is e8-mare-claim; the far-side contract changes atmosphere/comms state, not terrain ownership",
        "mounts": [
            ("far-side-landing-frame", 0.0, 0.0, -40.0, 0.0, 1.0),
            ("probe-recovery-cradle", 0.0, 0.0, 45.0, 3.1416, 1.0),
            ("west-comms-shadow-marker", -42.0, 0.0, 24.0, 0.18, 1.0),
            ("east-suit-cache-rack", 42.0, 0.0, -24.0, -0.18, 1.0),
            ("far-horizon-listening-post", 0.0, 0.0, 56.0, 3.1416, 1.0),
        ],
    },
    "eclipse": {
        "base": "mare-claim",
        "mask": "assets/contracts/epoch-8-orbital/mask-tables/e8-eclipse.json",
        "reason": "maskTruth.tileId is e8-mare-claim; eclipse timing rides the accepted rim-ring claim",
        "mounts": [
            ("eclipse-shadow-dial", 0.0, 0.0, 0.0, 0.0, 1.0),
            ("west-rim-solar-witness", -44.0, 0.0, 47.0, 0.12, 1.0),
            ("east-rim-solar-witness", 44.0, 0.0, 47.0, -0.12, 1.0),
            ("launch-shadow-gate", -30.0, 0.0, -31.0, 0.18, 1.0),
            ("mass-driver-eclipse-marker", 34.0, 0.0, -34.0, -0.10, 1.0),
        ],
    },
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def pack_path(key: str) -> Path:
    return OUT / "landmarks" / key / f"{key}-landmark-pack-contract.json"


def terrain_path(key: str) -> Path:
    return OUT / f"{key}-terrain-contract.json"


def mount(identifier: str, x: float, y: float, z: float, yaw: float, scale: float, asset: str) -> dict:
    return {
        "id": identifier,
        "position": [float(x), float(y), float(z)],
        "rotation": [0.0, float(yaw), 0.0],
        "scale": [float(scale), float(scale), float(scale)],
        "asset": asset,
    }


def canonical_mounts(key: str, terrain: dict, pack: dict) -> list[dict]:
    assets = {identifier: record["asset"] for identifier, record in pack["assets"].items()}
    if CANONICAL[key] is None:
        mounts = pack.get("mounts") or terrain["landmarkMounts"]
        if not mounts:
            raise ValueError(f"{key} has no existing mount positions to backfill")
        return [{**entry, "asset": assets[entry["id"]]} for entry in mounts]
    return [mount(identifier, x, y, z, yaw, scale, assets[identifier]) for identifier, x, y, z, yaw, scale in CANONICAL[key]]


def update_contracts(key: str) -> list[dict]:
    terrain_file = terrain_path(key)
    pack_file = pack_path(key)
    terrain = read_json(terrain_file)
    pack = read_json(pack_file)
    mounts = canonical_mounts(key, terrain, pack)
    terrain["landmarkMounts"] = mounts
    terrain["landmarkMountSpace"] = terrain.get("landmarkMountSpace") or MOUNT_SPACE
    terrain["landmarkPack"] = {
        "contract": f"landmarks/{key}/{key}-landmark-pack-contract.json",
        "atlas": pack["atlas"]["asset"],
        "era": pack["era"],
        "sourceLadder": "reuse > derive > build-new",
        "ownership": "separate mounted render-only GLBs; no simulation authority",
    }
    if "landmarkFreeze" in terrain:
        terrain["landmarkFreeze"] = "lifted; canonical mounted landmark pack records backfilled by the mounts sweep"
    pack["mounts"] = mounts
    pack["mountInterlock"] = "resolved-3d-d"
    pack.pop("proposedIds", None)
    write_json(terrain_file, terrain)
    write_json(pack_file, pack)
    return mounts


def update_variant_contract(key: str) -> list[dict]:
    variant = FINAL_VARIANTS[key]
    base_key = variant["base"]
    base = read_json(terrain_path(base_key))
    mask_table = read_json(ROOT / variant["mask"])
    mounts = [mount(identifier, x, y, z, yaw, scale, "") for identifier, x, y, z, yaw, scale in variant["mounts"]]
    contract = {
        "contractId": f"{key}-reuse-verdict",
        "tileId": mask_table["maskTruth"]["tileId"],
        "renderOnly": True,
        "sculptVerdict": {
            "verdict": "reuse",
            "baseTile": base_key,
            "baseTerrainContract": f"{base_key}-terrain-contract.json",
            "reason": variant["reason"],
            "terrainGlb": base["asset"],
            "panoramaGlb": base["panoramaMount"]["asset"],
            "duplicateSculpt": "forbidden; gameplay contract rides the existing tileId",
        },
        "maskTable": variant["mask"],
        "maskTruth": mask_table["maskTruth"],
        "landmarkMountSpace": MOUNT_SPACE,
        "landmarkMounts": mounts,
        "landmarkPack": {
            "status": "pending-3d-c",
            "ownership": "ALPHA builds separate mounted render-only GLBs from these ids; no simulation authority",
        },
        "simulation": "reuse verdict only; terrain, collision, movement, placement, water, spawns, fog, and variant mechanics remain unchanged",
    }
    write_json(terrain_path(key), contract)
    return mounts


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def trim_dark_border(image: Image.Image) -> Image.Image:
    image = image.convert("RGB")
    mask = Image.new("L", image.size, 0)
    pixels = image.load()
    mask_pixels = mask.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b = pixels[x, y]
            if max(r, g, b) > 14:
                mask_pixels[x, y] = 255
    box = mask.getbbox()
    if not box:
        return image
    left, top, right, bottom = box
    margin = 12
    return image.crop((max(0, left - margin), max(0, top - margin), min(image.width, right + margin), min(image.height, bottom + margin)))


def fit(image: Image.Image, box: tuple[int, int], lift: bool = False) -> Image.Image:
    image = image.convert("RGB")
    image = trim_dark_border(image)
    if lift:
        image = ImageEnhance.Brightness(image).enhance(1.22)
        image = ImageEnhance.Contrast(image).enhance(1.08)
    image.thumbnail(box, Image.Resampling.LANCZOS)
    frame = Image.new("RGB", box, (24, 20, 16))
    frame.paste(image, ((box[0] - image.width) // 2, (box[1] - image.height) // 2))
    return frame


def build_board(key: str, mounts: list[dict]) -> None:
    title = key.replace("-", " ").title()
    board = Image.new("RGB", (1800, 1180), (30, 25, 19))
    draw = ImageDraw.Draw(board)
    draw.text((44, 34), f"{title} Mounts Sweep", font=font(44), fill=(236, 220, 174))
    draw.text((46, 88), "canonical terrain contract mounts + published pack bodies; render-only, planar sim unchanged", font=font(24), fill=(205, 190, 154))
    images = [
        next(path for path in (ARTIFACTS / f"{key}-landmarks-proposed.png", ARTIFACTS / f"{key}-landmarks-mounted.png") if path.exists()),
        next(path for path in (ARTIFACTS / f"{key}-landmarks-proposed-overview.png", ARTIFACTS / f"{key}-landmarks-mounted-overview.png") if path.exists()),
        ARTIFACTS / f"{key}-landmarks-pack.png",
    ]
    labels = ("run-camera ensemble", "map placement overview", "pack body lineup")
    for index, (path, label) in enumerate(zip(images, labels)):
        x = 44 + index * 586
        y = 150
        if path.exists():
            board.paste(fit(Image.open(path), (540, 430), lift=index < 2), (x, y))
        draw.rectangle((x, y, x + 540, y + 430), outline=(108, 91, 62), width=3)
        draw.text((x, y + 446), label, font=font(22), fill=(224, 210, 171))
    y = 670
    draw.text((44, y), "Mount records", font=font(30), fill=(236, 220, 174))
    y += 48
    for entry in mounts:
        x_pos, y_pos, z_pos = entry["position"]
        yaw = entry["rotation"][1]
        scale = entry["scale"][0]
        line = f"{entry['id']}: pos=({x_pos:.1f},{y_pos:.1f},{z_pos:.1f}) yaw={yaw:.2f} scale={scale:.2f} asset={entry['asset']}"
        draw.text((60, y), line, font=font(22), fill=(213, 204, 180))
        y += 36
    if key == "relay-valley" and (ARTIFACTS / "relay-valley-landmarks-clearance-overlay.png").exists():
        overlay = fit(Image.open(ARTIFACTS / "relay-valley-landmarks-clearance-overlay.png"), (420, 300), lift=True)
        board.paste(overlay, (1328, 815))
        draw.rectangle((1328, 815, 1748, 1115), outline=(108, 91, 62), width=3)
        draw.text((1328, 1126), "clearance overlay", font=font(20), fill=(224, 210, 171))
    board.save(ARTIFACTS / f"{key}-mounts-sweep-verdict.png")


def build_reuse_board(key: str, mounts: list[dict]) -> None:
    variant = FINAL_VARIANTS[key]
    base_key = variant["base"]
    title = key.replace("-", " ").title()
    board = Image.new("RGB", (1800, 1180), (30, 25, 19))
    draw = ImageDraw.Draw(board)
    draw.text((44, 34), f"{title} Sculpt Verdict: REUSE {base_key.replace('-', ' ').title()}", font=font(40), fill=(236, 220, 174))
    draw.text((46, 88), variant["reason"], font=font(22), fill=(205, 190, 154))
    images = [
        ARTIFACTS / f"{base_key}-run-camera.png",
        ARTIFACTS / f"{base_key}-overview.png",
        ARTIFACTS / f"{base_key}-mounts-sweep-verdict.png",
    ]
    labels = ("base run-camera tile", "base overview tile", "base mounted pack evidence")
    if key == "far-side" and (ARTIFACTS / "mare-claim-panorama-far-side.png").exists():
        images[2] = ARTIFACTS / "mare-claim-panorama-far-side.png"
        labels = ("base run-camera tile", "base overview tile", "far-side panorama evidence")
    for index, (path, label) in enumerate(zip(images, labels)):
        x = 44 + index * 586
        y = 150
        if path.exists():
            board.paste(fit(Image.open(path), (540, 430), lift=index < 2), (x, y))
        draw.rectangle((x, y, x + 540, y + 430), outline=(108, 91, 62), width=3)
        draw.text((x, y + 446), label, font=font(22), fill=(224, 210, 171))
    y = 670
    draw.text((44, y), "Variant mount records for ALPHA", font=font(30), fill=(236, 220, 174))
    y += 48
    for entry in mounts:
        x_pos, y_pos, z_pos = entry["position"]
        yaw = entry["rotation"][1]
        line = f"{entry['id']}: pos=({x_pos:.1f},{y_pos:.1f},{z_pos:.1f}) yaw={yaw:.2f} scale={entry['scale'][0]:.2f} asset=<pending>"
        draw.text((60, y), line, font=font(22), fill=(213, 204, 180))
        y += 36
    board.save(ARTIFACTS / f"{key}-reuse-verdict.png")


def main() -> None:
    for key in OUTSTANDING:
        mounts = update_contracts(key)
        build_board(key, mounts)


if __name__ == "__main__":
    main()
