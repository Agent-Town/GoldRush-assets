"""Verify terrain contracts contain resolved mounts for merged landmark packs."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts/map-rebuild-spike"

EXPECTED = {
    "regatta": (
        "start-line-rig",
        "finish-line-rig",
        "northwest-buoy-line-anchor",
        "midcourse-buoy-line-anchor",
        "northeast-buoy-line-anchor",
        "spectator-raft-port",
        "spectator-raft-starboard",
        "judges-tower",
    ),
    "glow-mesa": (
        "mesa-starstone-derrick",
        "six-vein-control-pylon",
        "isotope-cooling-rack",
        "west-herd-glow-gate",
        "east-herd-glow-gate",
    ),
    "relay-valley": (
        "west-ridge-dish-cluster",
        "east-ridge-dish-cluster",
        "dead-gap-charting-station",
        "valley-cable-drum-yard",
        "drone-recovery-beacon",
    ),
    "mare-claim": (
        "earthrise-listening-array",
        "lava-tube-survey-gantry",
        "regolith-core-yard",
        "west-rim-debris-catcher",
        "east-rim-debris-catcher",
    ),
    "dome-basin": (
        "canal-gate-works",
        "ice-quarry-hoist",
        "seed-row-weather-station",
        "ark-yard-scaffold",
        "dust-devil-warning-mast",
    ),
    "ember-shore": (
        "last-warm-vent-altar",
        "cooled-titan-shelf",
        "west-vein-cooling-marker",
        "center-vein-bridge-school",
        "shore-preserve-rack",
    ),
    "pressure-garden": (
        "garden-pressure-manifold",
        "west-terrace-pipe-header",
        "east-terrace-pipe-header",
        "coal-seam-service-winch",
        "water-band-pump-station",
    ),
    "incline": (
        "lower-yard-engine-crane",
        "west-line-brake-tower",
        "east-line-brake-tower",
        "upper-ore-cable-house",
        "ford-service-pump",
    ),
    "blackout-ridge": (
        "off-map-current-receiver",
        "trunk-line-breaker-shelter",
        "breath-bank-service-rack",
        "ridge-switch-house",
        "blackout-watch-lamp",
    ),
    "canyon-works": (
        "sub-hall-dynamo-house",
        "west-switchback-line-house",
        "east-switchback-line-house",
        "dam-crest-gate-house",
        "downriver-tram-lamp",
    ),
    "moth-season": (
        "north-migration-watch-gate",
        "south-quiet-road-gate",
        "west-lamplighter-refuge",
        "east-tithe-bell-house",
        "mothglass-counting-cage",
    ),
    "fairground": (
        "south-midway-admission-arch",
        "west-current-calliope-wagon",
        "east-mothglass-prize-cage",
        "north-crowd-counting-rostrum",
        "fair-bell-battery-kiosk",
    ),
    "dust-flats": (
        "north-railhead-storm-tower",
        "west-road-wrecker-shed",
        "east-horizon-fuel-reserve",
        "south-grade-charting-post",
        "dry-wash-recovery-gantry",
    ),
    "boneyard": (
        "flivver-row-west-a",
        "flivver-row-west-b",
        "flivver-row-west-c",
        "spent-boiler-west",
        "spent-boiler-east",
        "flivver-row-east-a",
        "flivver-row-east-b",
        "flivver-row-east-c",
        "hauler-bed-north-a",
        "hauler-bed-north-b",
        "half-buried-sleeper",
        "unmarked-wagon",
    ),
    "showroom": (
        "showroom-entrance-arch",
        "west-starburst-billboard",
        "east-starburst-billboard",
        "abandoned-catalog-office",
        "catalog-sorting-gantry",
    ),
    "half-life-hollow": (
        "south-countdown-gate",
        "west-hollow-warning-pylon",
        "east-hollow-warning-pylon",
        "expired-appliance-convoy",
        "north-extraction-gantry",
    ),
    "echo-canyon": (
        "south-broadcast-gate",
        "west-echo-array",
        "east-echo-array",
        "mirror-observation-post",
        "north-return-gate",
    ),
    "low-orbit": (
        "west-scaffold-handhold-frame",
        "claw-carcass-rig",
        "east-scaffold-handhold-frame",
        "north-debris-catcher",
        "south-return-beacon",
    ),
    "seed-run": (
        "south-seed-caravan-gate",
        "west-seed-vault",
        "center-seed-vault",
        "east-seed-vault",
        "north-basin-waygate",
    ),
    "devils-alley": (
        "south-anchor-gate",
        "west-wind-anchor",
        "center-wind-anchor",
        "east-wind-anchor",
        "north-anchor-gate",
    ),
    "old-canal": (
        "south-survey-rig",
        "canal-segment-a-marker",
        "canal-segment-b-marker",
        "canal-segment-c-marker",
        "north-outflow-gate",
    ),
    "archive-world": (
        "archive-entry-gate",
        "west-stack-ruin",
        "east-stack-ruin",
        "warning-shelf-ruin",
        "ours-unless-marker",
    ),
}

VARIANT_EXPECTED = {
    "picnic": ("e6-glow-mesa", ("picnic-staging-gate", "west-picnic-blanket", "center-picnic-blanket", "east-picnic-blanket", "mesa-civilian-shade")),
    "dead-band": ("e7-relay-valley", ("dead-band-yard-null-post", "west-old-tool-cache", "east-old-tool-cache", "iron-shadow-warning-frame", "north-silence-gate")),
    "relay-rush": ("e7-relay-valley", ("rush-start-horn", "rush-relay-r1-frame", "rush-relay-r2-frame", "rush-relay-r3-frame", "rush-relay-r4-frame")),
    "far-side": ("e8-mare-claim", ("far-side-landing-frame", "probe-recovery-cradle", "west-comms-shadow-marker", "east-suit-cache-rack", "far-horizon-listening-post")),
    "eclipse": ("e8-mare-claim", ("eclipse-shadow-dial", "west-rim-solar-witness", "east-rim-solar-witness", "launch-shadow-gate", "mass-driver-eclipse-marker")),
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def inside(point: list[float], rect: dict) -> bool:
    x, _y, z = point
    return rect["minX"] <= x <= rect["maxX"] and rect["minZ"] <= z <= rect["maxZ"]


def verify(key: str) -> None:
    terrain = read_json(OUT / f"{key}-terrain-contract.json")
    pack = read_json(OUT / "landmarks" / key / f"{key}-landmark-pack-contract.json")
    mounts = terrain["landmarkMounts"]
    if key == "mare-claim":
        domes = read_json(OUT / "landmarks/mare-dome/mare-dome-landmark-pack-contract.json")["mounts"]
        assert tuple(m["id"] for m in domes) == ("west-air-pad-dome", "central-air-pad-dome", "east-air-pad-dome")
        assert [m["position"] for m in domes] == [[-18, .08, 0], [0, .08, 0], [18, .08, 0]]
        assert all(m["contractIds"] == ["e8-mare-claim", "e8-eclipse"] for m in domes)
        assert all((OUT / m["asset"]).is_file() for m in domes)
        assert mounts[-3:] == domes
        mounts = mounts[:-3]
    expected = EXPECTED[key]
    assert tuple(mount["id"] for mount in mounts) == expected
    assert pack["mounts"] == terrain["landmarkMounts"]
    assert pack["mountInterlock"] == "resolved-3d-d"
    assert "proposedIds" not in pack
    assert terrain["landmarkPack"]["contract"] == f"landmarks/{key}/{key}-landmark-pack-contract.json"
    assert terrain["landmarkMountSpace"]["ownership"].endswith("never baked into terrain")
    assert (ARTIFACTS / f"{key}-mounts-sweep-verdict.png").stat().st_size > 100_000
    assets = pack["assets"]
    for mount in mounts:
        assert mount["asset"] == assets[mount["id"]]["asset"]
        assert (OUT / mount["asset"]).is_file()
        assert set(mount) == {"id", "position", "rotation", "scale", "asset"}
        assert len(mount["position"]) == len(mount["rotation"]) == len(mount["scale"]) == 3
    if key == "glow-mesa":
        blocked = terrain["maskTruth"]["buildZones"] + terrain["maskTruth"]["fixtureZones"]
        assert all(not any(inside(mount["position"], rect) for rect in blocked) for mount in mounts)
    if key == "relay-valley":
        blocked = terrain["maskTruth"]["buildZones"] + terrain["maskTruth"]["fogPockets"]
        assert all(not any(inside(mount["position"], rect) for rect in blocked) for mount in mounts)
    if key == "mare-claim":
        blocked = terrain["maskTruth"]["buildZones"] + [terrain["maskTruth"]["lavaTubeMouth"]]
        assert all(not any(inside(mount["position"], rect) for rect in blocked) for mount in mounts)
    if key == "dome-basin":
        blocked = terrain["maskTruth"]["buildZones"]
        assert all(not any(inside(mount["position"], rect) for rect in blocked) for mount in mounts)
    if key == "pressure-garden":
        blocked = terrain["maskTruth"]["buildZones"]
        assert all(not any(inside(mount["position"], rect) for rect in blocked) for mount in mounts)
    if key == "incline":
        blocked = terrain["maskTruth"]["buildZones"]
        assert all(not any(inside(mount["position"], rect) for rect in blocked) for mount in mounts)
    if key == "showroom":
        blocked = terrain["maskTruth"]["showroomHouses"]
        assert all(not any(inside(mount["position"], rect) for rect in blocked) for mount in mounts)
    if key in {"blackout-ridge", "moth-season", "dust-flats"}:
        blocked = terrain["maskTruth"]["buildZones"]
        assert all(not any(inside(mount["position"], rect) for rect in blocked) for mount in mounts)
    if key == "canyon-works":
        width = terrain["maskTruth"]["dimensions"]["width"] / 2
        blocked = terrain["maskTruth"]["buildZones"] + [{"minX": -width, "maxX": width, **terrain["waterAgreement"]["shallowsEnd"]}]
        assert all(not any(inside(mount["position"], rect) for rect in blocked) for mount in mounts)
    if key == "fairground":
        blocked = terrain["maskTruth"]["buildZones"] + terrain["maskTruth"]["fixtureZones"]
        assert all(not any(inside(mount["position"], rect) for rect in blocked) for mount in mounts)


def verify_variant(key: str) -> None:
    terrain = read_json(OUT / f"{key}-terrain-contract.json")
    tile_id, expected = VARIANT_EXPECTED[key]
    mounts = terrain["landmarkMounts"]
    assert terrain["sculptVerdict"]["verdict"] == "reuse"
    assert terrain["tileId"] == tile_id
    assert terrain["maskTruth"]["tileId"] == tile_id
    assert tuple(mount["id"] for mount in mounts) == expected
    landmark_pack = terrain["landmarkPack"]
    if landmark_pack.get("status") == "pending-3d-c":
        # interlock open: ids published, bodies not yet built
        for mount in mounts:
            assert mount["asset"] == ""
            assert set(mount) == {"id", "position", "rotation", "scale", "asset"}
            assert len(mount["position"]) == len(mount["rotation"]) == len(mount["scale"]) == 3
    else:
        # completed by 3D-C: the pack landed and every mount asset is filled
        assert landmark_pack["contract"] == f"landmarks/{key}/{key}-landmark-pack-contract.json"
        pack = read_json(OUT / "landmarks" / key / f"{key}-landmark-pack-contract.json")
        assert pack["mounts"] == mounts
        assets = pack["assets"]
        for mount in mounts:
            assert mount["asset"] == assets[mount["id"]]["asset"]
            assert (OUT / mount["asset"]).is_file()
            assert set(mount) == {"id", "position", "rotation", "scale", "asset"}
            assert len(mount["position"]) == len(mount["rotation"]) == len(mount["scale"]) == 3
    assert (ARTIFACTS / f"{key}-reuse-verdict.png").stat().st_size > 100_000


def main() -> None:
    for key in EXPECTED:
        verify(key)
    for key in VARIANT_EXPECTED:
        verify_variant(key)
    counts = {key: len(EXPECTED[key]) for key in EXPECTED}
    counts.update({key: len(VARIANT_EXPECTED[key][1]) for key in VARIANT_EXPECTED})
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
