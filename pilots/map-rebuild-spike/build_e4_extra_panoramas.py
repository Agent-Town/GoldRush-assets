"""Build Panorama v2 rings for the three unique E4 campaign maps."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


OUT = Path(__file__).resolve().parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_module("e4_extra_panorama_base", OUT / "build_contract_panoramas.py")

PROFILES = {
    "long-road": {
        "contract": "long-road",
        "kit": base.ROOT / "assets/processed/kit-era-4.png",
        "sourcePlate": base.ROOT / "assets/raw/kit-era-4.png",
        "epoch": "Epoch 4 motor frontier",
        "tint": (0.76, 0.61, 0.42),
        "dark": (0.090, 0.058, 0.030),
        "phase": 0.14,
        "strength": 0.78,
        "dust": (0.68, 0.18, 0.27),
        "signature": "an immense graded road vanishing between unequal storm banks, three way-station notches, and one hard railhead cut",
    },
    "gusher-county": {
        "contract": "gusher-county",
        "kit": base.ROOT / "assets/processed/kit-era-4.png",
        "sourcePlate": base.ROOT / "assets/raw/plate-e4-bld-set.png",
        "epoch": "Epoch 4 motor frontier",
        "tint": (0.70, 0.54, 0.34),
        "dark": (0.072, 0.047, 0.026),
        "phase": 0.48,
        "strength": 0.76,
        "dust": (0.76, 0.16, 0.22),
        "signature": "a tar-dark working county ringed by broken lease shoulders, distant derrick needles, and one low blowout haze",
    },
    "boneyard": {
        "contract": "boneyard",
        "kit": base.ROOT / "assets/processed/kit-era-4.png",
        "sourcePlate": base.ROOT / "assets/raw/plate-e4-boss-land-yacht.png",
        "epoch": "Epoch 4 motor frontier",
        "tint": (0.64, 0.54, 0.43),
        "dark": (0.060, 0.046, 0.034),
        "phase": 0.83,
        "strength": 0.74,
        "dust": (0.62, 0.14, 0.20),
        "signature": "a quiet rust valley beneath mismatched scrap ridges, one half-buried silhouette, and a dust-muted outer plain",
    },
}


def main():
    base.PROFILES.update(PROFILES)
    base.LAYERED_PANORAMAS.update(PROFILES)
    base.FAR_RIDGE_PANORAMAS.update({"gusher-county", "boneyard"})
    original_extents = base.playfield_half_extents

    def campaign_extents(key):
        return {
            "long-road": (200.0, 48.0),
            "gusher-county": (80.0, 80.0),
            "boneyard": (64.0, 64.0),
        }.get(key, original_extents(key))

    base.playfield_half_extents = campaign_extents
    original_atlas = base.make_atlas

    def campaign_atlas(key, profile):
        image, path = original_atlas(key, profile)
        # ``original_atlas`` returns an already packed image.  Unpack before
        # applying the terrain-derived ground band so the second ``pack``
        # refreshes the GLB payload from the final on-disk PNG instead of
        # retaining the pre-band packed bytes.
        if image.packed_file:
            image.unpack(method="REMOVE")
        pixels = np.empty(len(image.pixels), dtype=np.float32)
        image.pixels.foreach_get(pixels)
        rgba = pixels.reshape((base.ATLAS_SIZE, base.ATLAS_SIZE, 4))
        terrain_atlas = OUT / f"{key}-terrain-atlas.png"
        source = base.claim.image_pixels(terrain_atlas if terrain_atlas.is_file() else profile["kit"])
        axis = np.linspace(0.0, 1.0, base.ATLAS_SIZE, dtype=np.float32)
        u, v = np.meshgrid(axis, axis)
        ground = base.claim.tiled_sample(source, u, v, 2.2 if terrain_atlas.is_file() else 7.4, 0.19, 0.57)
        if terrain_atlas.is_file():
            ground = np.clip(ground * np.asarray((0.82, 0.78, 0.70), dtype=np.float32), 0.006, 0.58)
        else:
            ground = np.clip(ground * np.asarray((0.34, 0.24, 0.15), dtype=np.float32), 0.006, 0.36)
        band_rows = int(base.ATLAS_SIZE * 0.17)
        # Panorama skirt UVs occupy v=0..0.16.  Blend terrain paint strongly
        # at v=0 and fade it inside the skirt/ridge UV range; carrying the
        # terrain sample above v=0.17 produces vertical smears in visible sky.
        # Writing this at the
        # opposite atlas edge creates a literal terrain-coloured ceiling.
        strength = np.linspace(1.0, 0.0, band_rows, dtype=np.float32)[:, None, None] ** 1.6
        rgba[:band_rows, :, :3] = rgba[:band_rows, :, :3] * (1.0 - strength) + ground[:band_rows, :, :] * strength
        image.pixels.foreach_set(rgba.ravel())
        image.save()
        image.pack()
        return image, path

    base.make_atlas = campaign_atlas
    requested = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else list(PROFILES)
    default_radii = (base.RADIUS, base.RIDGE_FOOT_RADIUS, base.RIDGE_CREST_RADIUS, base.FAR_RIDGE_FOOT_RADIUS, base.FAR_RIDGE_CREST_RADIUS)
    default_sky_top = base.SKY_TOP
    for key in requested:
        if key not in PROFILES:
            raise ValueError(f"unsupported E4 campaign panorama: {key}")
        if key == "long-road":
            base.RADIUS, base.RIDGE_FOOT_RADIUS, base.RIDGE_CREST_RADIUS = 260.0, 220.0, 238.0
            base.FAR_RIDGE_FOOT_RADIUS, base.FAR_RIDGE_CREST_RADIUS = 245.0, 252.0
            # The 400 m playfield needs a wider ring than the county tiles.
            # Raise that cylinder proportionally so the low verdict camera
            # cannot see over its open top as a false brown zenith ceiling.
            base.SKY_TOP = 245.0
        else:
            base.RADIUS, base.RIDGE_FOOT_RADIUS, base.RIDGE_CREST_RADIUS, base.FAR_RIDGE_FOOT_RADIUS, base.FAR_RIDGE_CREST_RADIUS = default_radii
            base.SKY_TOP = default_sky_top
        base.build(key)


if __name__ == "__main__":
    main()
