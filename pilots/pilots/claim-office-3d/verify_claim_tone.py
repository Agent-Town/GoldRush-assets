from pathlib import Path
import json
import subprocess


ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "artifacts/town3d-claim-office"
METRICS = ARTIFACTS / "luminance-metrics.json"


def crop_mean(source: Path, crop: dict[str, int]) -> float:
    geometry = f"{crop['width']}x{crop['height']}+{crop['x']}+{crop['y']}"
    result = subprocess.run(
        [
            "magick", str(source), "-precision", "12", "-crop", geometry,
            "+repage", "-colorspace", "Gray", "-format", "%[fx:mean]", "info:",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout)


def main() -> None:
    metrics = json.loads(METRICS.read_text())
    source = ARTIFACTS / metrics["source"]
    office = crop_mean(source, metrics["claimOffice"]["crop"])
    neighbor = crop_mean(source, metrics["paintedNeighbor"]["crop"])
    delta = abs(office - neighbor)
    delta_percent = delta / neighbor * 100

    assert metrics["paintedNeighbor"]["building"] == "Tavern LITE facade"
    assert abs(office - metrics["claimOffice"]["meanLuminance"]) < 0.000001
    assert abs(neighbor - metrics["paintedNeighbor"]["meanLuminance"]) < 0.000001
    assert abs(delta - metrics["absoluteDelta"]) < 0.000001
    assert abs(delta_percent - metrics["deltaPercentOfPaintedNeighbor"]) < 0.001
    assert metrics["passes"] is (delta_percent <= metrics["limitPercent"])
    print(json.dumps({"claimOffice": office, "paintedNeighbor": neighbor, "deltaPercent": delta_percent}, indent=2))


if __name__ == "__main__":
    main()
