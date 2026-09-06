"""Build the Archive World's separate Panorama v2 ring."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("archive_panorama_base", OUT / "build_contract_panoramas.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

ROOT = OUT.parents[2]
PROFILE = {
    "contract": "archive-world",
    # The worlds plate supplies a readable engraved horizon; the Ark kit stays
    # the archive's secondary style source rather than becoming a black wall.
    "kit": ROOT / "assets/raw/plate-e10-worlds.png",
    "sourcePlate": ROOT / "assets/processed/kit-era-10.png",
    "epoch": "Epoch 10 Deep Sky archive world",
    "tint": (0.70, 0.47, 0.27),
    "dark": (0.058, 0.030, 0.016),
    "phase": 0.37,
    "strength": 1.02,
    "dust": (0.71, 0.08, 0.16),
    "signature": "broken archive silhouettes beneath deep ink, quiet star stipple, and unequal parchment-gold memory veils",
}

base.PROFILES["archive-world"] = PROFILE
base.LAYERED_PANORAMAS.add("archive-world")
base.FAR_RIDGE_PANORAMAS.add("archive-world")
_playfield_half_extents = base.playfield_half_extents


def playfield_half_extents(key):
    return (64.0, 64.0) if key == "archive-world" else _playfield_half_extents(key)


base.playfield_half_extents = playfield_half_extents
_make_atlas = base.make_atlas


def make_atlas(key, profile):
    image, path = _make_atlas(key, profile)
    pixels = np.asarray(image.pixels[:], dtype=np.float32).reshape(base.ATLAS_SIZE, base.ATLAS_SIZE, 4)
    v = np.linspace(0.0, 1.0, base.ATLAS_SIZE, dtype=np.float32)[:, None]
    u = np.linspace(0.0, 1.0, base.ATLAS_SIZE, endpoint=False, dtype=np.float32)[None, :]
    # Deep ink at the zenith, a restrained parchment-gold horizon, and visible
    # engraved detail only in the distance band: sky, never parchment ceiling.
    horizon = np.asarray((0.20, 0.115, 0.060), dtype=np.float32)
    zenith = np.asarray((0.018, 0.016, 0.022), dtype=np.float32)
    fade = base.smoothstep(0.18, 0.78, v)[..., None]
    sky = horizon[None, None, :] * (1.0 - fade) + zenith[None, None, :] * fade
    luma = pixels[:, :, :3].mean(axis=2, keepdims=True)
    detail_band = base.smoothstep(0.10, 0.17, v) * (1.0 - base.smoothstep(0.43, 0.62, v))
    sky = sky * (0.84 + (luma - luma.mean()) * detail_band[..., None] * 0.52)
    # Four unequal memory veils replace the repeated strip with authored
    # quadrant features and then disappear before the quiet zenith.
    veils = np.zeros((base.ATLAS_SIZE, base.ATLAS_SIZE), dtype=np.float32)
    for center_u, center_v, width_u, width_v in (
        (0.09, 0.31, 0.075, 0.045),
        (0.36, 0.38, 0.115, 0.032),
        (0.64, 0.27, 0.055, 0.066),
        (0.88, 0.42, 0.090, 0.028),
    ):
        du = np.abs(np.mod(u - center_u + 0.5, 1.0) - 0.5)
        broken_center = center_v + np.sin((u - center_u) * np.pi * 12.0) * 0.015
        veils = np.maximum(veils, np.exp(-((du / width_u) ** 4) - (((v - broken_center) / width_v) ** 2)))
    veil_tone = np.asarray((0.34, 0.17, 0.055), dtype=np.float32)
    sky = sky * (1.0 - veils[..., None] * 0.34) + veil_tone[None, None, :] * veils[..., None] * 0.34
    # Sparse engraved stars survive above the veils without filling the vacuum.
    rng = np.random.default_rng(1010)
    stars = (rng.random((base.ATLAS_SIZE, base.ATLAS_SIZE)) > 0.99935) & (v > 0.28)
    star_tone = np.asarray((0.58, 0.39, 0.16), dtype=np.float32)
    sky = np.where(stars[..., None], sky * 0.55 + star_tone[None, None, :] * 0.45, sky)
    sky_mask = base.smoothstep(0.12, 0.22, v)[..., None]
    ground = pixels[:, :, :3] * 0.18 + np.asarray((0.038, 0.025, 0.018), dtype=np.float32)[None, None, :] * 0.82
    pixels[:, :, :3] = np.clip(ground * (1.0 - sky_mask) + sky * sky_mask, 0.006, 0.62)
    image.pixels.foreach_set(pixels.ravel())
    if image.packed_file:
        image.unpack(method="REMOVE")
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image, path


base.make_atlas = make_atlas


if __name__ == "__main__":
    keys = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else ["archive-world"]
    for key in keys:
        if key != "archive-world":
            raise ValueError(f"unsupported E10 archive panorama: {key}")
        base.build(key)
