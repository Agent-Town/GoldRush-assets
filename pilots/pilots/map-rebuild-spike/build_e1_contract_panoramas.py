"""Build the five Epoch 1 render-only panorama rings — THE PINNED E1 GENERATION.

Panoramas are mounted scenery, never terrain. They carry no gameplay bounds,
water, spawn, fog, or placement authority.

WHY THIS FILE EXISTS (beauty shift night-shift round 2, 2026-08-03).
`build_contract_panoramas.py` began life as this file: "Build separate render-only
panorama rings for the five Epoch 1 maps." The five shipped E1 panoramas were built
from it at 9e0dcf98 (2026-07-14, "art: correct E1 panorama projection"). It was then
generalised in place into the all-epoch generator (+1107/-27 lines across the E2..E10
map families), and six of its thirteen functions were rewritten -- make_atlas 140 ->
415 lines, make_ring 64 -> 439, plus ridge_height, distant_ridge_height, make_material
and contract_for. Several of those edits retuned code the E1 keys flow through: the
haze mix 0.52 -> 0.78, the near band base paper*0.43+dark*0.27 -> paper*0.51+dark*0.22,
the near erosion clip(0.96+d*0.14, 0.91, 1.03) -> clip(0.91+d*0.72, 0.78, 1.07), a new
terrain-atlas seam-continuity block, and new sky/ridge ring geometry. E1 was never
re-run, and nothing guarded it. So from 2026-07-14 onwards `build_contract_panoramas.py
-- night-shift` regenerated a NEWER GENERATION of art, not the shipped art -- the defect
that blocked U4 in round 1 (reviews/beauty-night-shift.md F-2).

The pipeline itself was never broken: it is deterministic. This file, run on today's
`build_the_claim_terrain.py` helper and today's source plates, reproduces all five
shipped E1 panorama atlases AND all five shipped GLBs BYTE FOR BYTE (10/10 sha256,
measured 2026-08-03, Blender 5.1.2). Only the .blend differs, by the length of the
absolute path Blender stores inside it -- which is why the generated contract's
files.blend.{bytes,sha256} move and nothing else does.

THE LAW: the five E1 panoramas are rebuilt with THIS script and no other.
`build_contract_panoramas.py` still carries the E1 profiles because `map_index =
list(PROFILES).index(key)` places every later map's cloud edits off that ordering --
removing them would silently repaint E2..E10 -- but its main() now refuses the E1 keys
and points here. Guard: `verify_e1_panoramas.py` rebuilds into a scratch directory and
asserts the ten shipped sha256s, so the next generalisation cannot drift E1 in silence.
"""


from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
KIT = ROOT / "assets/processed/kit-era-1.png"
ATLAS_SIZE = 2048
RADIUS = 190.0
RIDGE_FOOT_RADIUS = 161.5
RIDGE_CREST_RADIUS = 174.0
SEGMENTS = 192
ROWS = 5
SKY_BOTTOM = -10.0
SKY_TOP = 130.0
RIDGE_TOP_BASE = 5.0
RIDGE_TOP_SCALE = 55.0
QUADRANT_PHASE_OFFSETS = (0.00, 0.37, 0.81, 1.29)
QUADRANT_VERTICAL_OFFSETS = (-0.025, 0.035, -0.045, 0.015)

claim_spec = importlib.util.spec_from_file_location("panorama_claim_helpers", OUT / "build_the_claim_terrain.py")
claim = importlib.util.module_from_spec(claim_spec)
claim_spec.loader.exec_module(claim)

PROFILES = {
    "the-claim": {
        "contract": "claim",
        "tint": (0.86, 0.70, 0.49),
        "dark": (0.19, 0.085, 0.028),
        "phase": 0.03,
        "strength": 0.48,
        "dust": (0.90, 0.17, 0.34),
        "signature": "open wind-scoured valley holding against a bruised outer rim",
    },
    "dry-gulch": {
        "contract": "dry-gulch",
        "tint": (1.00, 0.66, 0.31),
        "dark": (0.22, 0.075, 0.022),
        "phase": 0.29,
        "strength": 0.54,
        "dust": (0.57, 0.15, 0.08),
        "signature": "bleached enclosed basin beneath stepped dry mesas",
    },
    "twin-banks": {
        "contract": "twin-banks",
        "tint": (0.66, 0.66, 0.54),
        "dark": (0.16, 0.075, 0.035),
        "phase": 0.51,
        "strength": 0.47,
        "dust": (0.16, 0.22, 0.16),
        "signature": "low opposed shelves opening around a broad river county",
    },
    "night-shift": {
        "contract": "night-shift",
        "tint": (0.28, 0.38, 0.70),
        "dark": (0.025, 0.040, 0.075),
        "phase": 0.73,
        "strength": 0.42,
        "dust": (0.70, 0.13, 0.12),
        "signature": "cold enclosing rock corridor with one stubborn warm horizon break",
    },
    "baron": {
        "contract": "baron",
        "tint": (0.78, 0.42, 0.25),
        "dark": (0.16, 0.035, 0.025),
        "phase": 0.91,
        "strength": 0.50,
        "dust": (0.88, 0.16, 0.32),
        "signature": "occupied wind-cut ridge rhythm against a darker fevered rim",
    },
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def smoothstep(edge0, edge1, value):
    value = np.asarray(value, dtype=np.float32)
    t = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def mirrored_coordinates(values, size, repeats, phase):
    wrapped = np.mod(values * repeats + phase, 2.0)
    mirrored = np.where(wrapped <= 1.0, wrapped, 2.0 - wrapped)
    return mirrored * (size - 1)


def bilinear_sample(source, x, y):
    x0 = np.floor(x).astype(np.int32)
    x1 = np.minimum(x0 + 1, source.shape[1] - 1)
    y0 = np.floor(y).astype(np.int32)
    y1 = np.minimum(y0 + 1, source.shape[0] - 1)
    wx = (x - x0)[None, :, None]
    wy = (y - y0)[..., None]
    top = source[y0, x0[None, :]] * (1.0 - wx) + source[y0, x1[None, :]] * wx
    bottom = source[y1, x0[None, :]] * (1.0 - wx) + source[y1, x1[None, :]] * wx
    return top * (1.0 - wy) + bottom * wy


def circular_bump(u, center, width):
    distance = np.abs(np.mod(u - center + 0.5, 1.0) - 0.5)
    return np.exp(-((distance / width) ** 2))


def ridge_height(key, u):
    angle = u * math.tau
    jagged = np.sin(angle * 13.0 + 0.6) * 0.018 + np.sin(angle * 17.0 - 0.4) * 0.010
    if key == "the-claim":
        return 0.17 + np.sin(angle * 2.0 + 0.2) * 0.030 + np.sin(angle * 5.0) * 0.016 + np.sin(angle * 9.0 + 0.4) * 0.008 + jagged
    if key == "dry-gulch":
        mesas = np.abs(np.sin(angle * 2.0 - 0.8)) ** 5
        return 0.18 + mesas * 0.070 + np.sin(angle * 6.0) * 0.012 + np.sin(angle * 11.0 + 0.3) * 0.006 + jagged
    if key == "twin-banks":
        opening = circular_bump(u, 0.25, 0.11)
        return 0.14 + (1.0 - np.abs(np.sin(angle))) * 0.055 + np.sin(angle * 5.0 + 0.2) * 0.012 + jagged - opening * 0.180
    if key == "night-shift":
        shoulders = np.maximum(np.exp(-((u - 0.18) / 0.10) ** 2), np.exp(-((u - 0.78) / 0.11) ** 2))
        opening = circular_bump(u, 0.25, 0.085)
        return 0.18 + shoulders * 0.080 + np.sin(angle * 5.0) * 0.014 + np.sin(angle * 9.0) * 0.006 + jagged - opening * 0.290
    occupied = np.maximum(np.sin(angle * 6.0 + 0.4), 0.0) ** 3
    return 0.17 + occupied * 0.060 + np.sin(angle * 2.0) * 0.018 + np.sin(angle * 9.0 + 0.7) * 0.008 + jagged


def distant_ridge_height(key, u):
    """A lower, broader silhouette that never echoes the nearer mesh ridge."""
    angle = u * math.tau
    if key == "the-claim":
        return 0.105 + circular_bump(u, 0.34, 0.055) * 0.060 + circular_bump(u, 0.17, 0.11) * 0.025 + np.sin(angle * 3.0 + 0.7) * 0.008
    if key == "dry-gulch":
        return 0.115 + circular_bump(u, 0.43, 0.038) * 0.085 + circular_bump(u, 0.56, 0.082) * 0.035 + np.sin(angle * 7.0) * 0.006
    if key == "twin-banks":
        return 0.085 + circular_bump(u, 0.15, 0.075) * 0.052 + circular_bump(u, 0.37, 0.11) * 0.035 + np.sin(angle * 4.0 - 0.5) * 0.006
    if key == "night-shift":
        return 0.120 + circular_bump(u, 0.16, 0.062) * 0.080 + circular_bump(u, 0.38, 0.045) * 0.038 + np.sin(angle * 5.0 + 0.8) * 0.006
    return 0.105 + circular_bump(u, 0.94, 0.047) * 0.075 + circular_bump(u, 0.075, 0.085) * 0.032 + np.sin(angle * 5.0 - 0.3) * 0.007


def make_atlas(key, profile):
    # Blender image pixels are bottom-up. Work top-down so the selected strip
    # is the kit plate's actual engraved clouds and distant ridge, then flip
    # back before packing the texture. Crop out the town tower and right-edge
    # tree silhouettes; the panorama may contain no desert trees.
    source = np.flipud(claim.image_pixels(KIT))
    y0, y1 = int(source.shape[0] * 0.015), int(source.shape[0] * 0.145)
    x0, x1 = int(source.shape[1] * 0.36), int(source.shape[1] * 0.74)
    source = source[y0:y1, x0:x1, :]
    u = np.linspace(0.0, 1.0, ATLAS_SIZE, endpoint=False, dtype=np.float32)
    v = np.linspace(0.0, 1.0, ATLAS_SIZE, dtype=np.float32)
    uu, vv = np.meshgrid(u, v)

    # Sample four shifted areas of the shipped kit plate. The result is only a
    # source for paper colour and engraved ink; enlarging its painted cloud
    # masses directly was the v1 "Ceiling" failure.
    plate_sample = np.zeros((ATLAS_SIZE, ATLAS_SIZE, 3), dtype=np.float32)
    weight_total = np.zeros((ATLAS_SIZE, ATLAS_SIZE, 1), dtype=np.float32)
    for quadrant, (phase_offset, vertical_offset) in enumerate(zip(QUADRANT_PHASE_OFFSETS, QUADRANT_VERTICAL_OFFSETS)):
        center = 0.125 + quadrant * 0.25
        distance = np.abs(np.mod(u - center + 0.5, 1.0) - 0.5)
        weight = np.exp(-((distance / 0.19) ** 4)).astype(np.float32)
        x = mirrored_coordinates(u, source.shape[1], 2.0, profile["phase"] + phase_offset)
        warped_v = np.clip(vv + vertical_offset * smoothstep(0.14, 0.78, vv), 0.0, 1.0)
        y = warped_v * (source.shape[0] - 1)
        plate_sample += bilinear_sample(source, x, y) * weight[None, :, None]
        weight_total += weight[None, :, None]
    plate_sample /= weight_total

    tint = np.asarray(profile["tint"], dtype=np.float32)
    plate_luma = claim.luminance(plate_sample)
    surround = (
        np.roll(plate_luma, 3, axis=0)
        + np.roll(plate_luma, -3, axis=0)
        + np.roll(plate_luma, 3, axis=1)
        + np.roll(plate_luma, -3, axis=1)
    ) * 0.25
    plate_ink = np.clip((surround - plate_luma) * 8.0, 0.0, 1.0)
    # Long horizontal averaging removes the tree-like vertical combing that a
    # literal crop introduced while preserving the plate's eroded ink values.
    horizontal_ink = sum(np.roll(plate_ink, shift, axis=1) for shift in (-42, -28, -14, 0, 14, 28, 42)) / 7.0

    # PANORAMA LAW v2 / Ceiling: preserve dense engraving at the horizon but
    # quiet it continuously into near-plain parchment at the top of the ring.
    source_paper = np.mean(source[: max(1, source.shape[0] // 3)], axis=(0, 1))
    paper_value = float(claim.luminance(source_paper[None, None, :])[0, 0])
    # Keep the shipped plate's parchment value without multiplying its warm
    # chroma twice. The previous orange-on-orange treatment romanticised the
    # county into a holiday sunset instead of a hard, dusty working frontier.
    paper = paper_value * (0.56 + tint * 0.44)
    zenith = np.clip(paper * 1.08, 0.0, 0.92)
    lower_sky = np.clip(paper * 0.78, 0.0, 0.92)
    atlas = zenith[None, None, :] * (1.0 - vv[..., None]) + lower_sky[None, None, :] * vv[..., None]
    horizon_density = smoothstep(0.50, 0.83, vv)
    atlas *= 1.0 - horizontal_ink[..., None] * (0.075 * horizon_density[..., None])

    # PANORAMA LAW v2 / Echo: one deliberately different, horizontally quiet
    # cloud edit per quadrant. These use ink extracted from the shipped plate,
    # while their positions and silhouettes are map-specific edit decisions.
    map_index = list(PROFILES).index(key)
    cloud_heights = (0.47, 0.62, 0.53, 0.68)
    cloud_widths = (0.105, 0.135, 0.090, 0.120)
    cloud_mask = np.zeros((ATLAS_SIZE, ATLAS_SIZE), dtype=np.float32)
    for quadrant in range(4):
        center_u = (0.105 + quadrant * 0.25 + ((map_index * 2 + quadrant) % 5 - 2) * 0.009) % 1.0
        center_v = cloud_heights[(quadrant + map_index) % 4] + (map_index - 2) * 0.008
        width_u = cloud_widths[(quadrant * 3 + map_index) % 4]
        width_v = 0.032 + ((quadrant + map_index) % 3) * 0.009
        du = np.abs(np.mod(uu - center_u + 0.5, 1.0) - 0.5)
        primary = np.exp(-((du / width_u) ** 4) - (((vv - center_v) / width_v) ** 2))
        shoulder_u = (center_u + width_u * (0.28 if quadrant % 2 else -0.32)) % 1.0
        shoulder_du = np.abs(np.mod(uu - shoulder_u + 0.5, 1.0) - 0.5)
        shoulder = np.exp(-((shoulder_du / (width_u * 0.56)) ** 4) - (((vv - center_v + width_v * 0.42) / (width_v * 0.72)) ** 2))
        cloud_mask = np.maximum(cloud_mask, np.maximum(primary * 0.82, shoulder * 0.58))
    cloud_density = cloud_mask * smoothstep(0.29, 0.50, vv) * (1.0 - smoothstep(0.73, 0.84, vv))
    cloud_engraving = cloud_density * (0.24 + horizontal_ink * 0.76)
    atlas *= 1.0 - cloud_engraving[..., None] * 0.080

    # One low, asymmetric wind-scoured dust feature per contract hardens the
    # frontier mood without adding a ceiling or a repeated 360-degree strip.
    dust_center, dust_width, dust_strength = profile["dust"]
    dust_distance = np.abs(np.mod(uu - dust_center + 0.5, 1.0) - 0.5)
    dust_centerline = 0.69 + np.sin(uu * math.tau + profile["phase"] * math.tau) * 0.038
    dust_plume = np.exp(-((dust_distance / dust_width) ** 4) - (((vv - dust_centerline) / 0.055) ** 2))
    dust_plume *= 0.45 + horizontal_ink * 0.55
    dust_tone = np.clip(np.asarray(profile["dark"], dtype=np.float32) * 0.48 + paper * 0.38, 0.0, 0.92)
    atlas = atlas * (1.0 - dust_plume[..., None] * dust_strength) + dust_tone[None, None, :] * dust_plume[..., None] * dust_strength

    ridge = distant_ridge_height(key, uu)
    ridge_boundary = 1.0 - ridge
    ridge_mask = smoothstep(ridge_boundary - 0.010, ridge_boundary + 0.014, vv)
    dark = np.asarray(profile["dark"], dtype=np.float32)
    ridge_base = dark * 0.54 + paper * 0.24
    # PANORAMA LAW v2 / Painted Wall: the physical foreground ridge hides the
    # sky-ring foot; this light dust band makes the remaining join atmospheric.
    above_ridge = ridge_boundary - vv
    haze = np.exp(-(((above_ridge - 0.045) / 0.055) ** 2)) * (1.0 - ridge_mask)
    haze_tone = np.clip(paper * 0.88 + tint * 0.07, 0.0, 0.92)
    broad_plate = sum(np.roll(plate_luma, shift, axis=1) for shift in (-64, -32, 0, 32, 64)) / 5.0
    ridge_variation = np.clip(0.96 + (broad_plate - np.mean(broad_plate)) * 0.22, 0.88, 1.04)
    ridge_depth = smoothstep(ridge_boundary - 0.004, ridge_boundary + 0.10, vv)
    ridge_base_weight = 0.18 + ridge_depth * 0.64
    ridge_tone = haze_tone[None, None, :] * (1.0 - ridge_base_weight[..., None]) + ridge_base[None, None, :] * ridge_base_weight[..., None]
    ridge_color = ridge_tone * ridge_variation[..., None]
    atlas = atlas * (1.0 - haze[..., None] * 0.52) + haze_tone[None, None, :] * haze[..., None] * 0.52
    atlas = atlas * (1.0 - ridge_mask[..., None]) + ridge_color * ridge_mask[..., None]

    # Reserve the atlas foot for the nearer occluding ridge. A dusty, eroded
    # midtone keeps this belt from becoming the matte black wall that a second
    # copy of the far-ridge ink produced in the first v2 build.
    near_band = smoothstep(0.83, 0.89, vv)
    near_depth = smoothstep(0.84, 1.0, vv)
    near_base = paper * 0.43 + dark * 0.27
    near_color = haze_tone[None, None, :] * (1.0 - near_depth[..., None]) + near_base[None, None, :] * near_depth[..., None]
    near_erosion = np.clip(0.96 + (broad_plate - np.mean(broad_plate)) * 0.14, 0.91, 1.03)
    near_color *= near_erosion[..., None]
    atlas = atlas * (1.0 - near_band[..., None]) + near_color * near_band[..., None]

    if key == "night-shift":
        warm_break = np.exp(-((uu - 0.58) / 0.055) ** 2) * smoothstep(0.64, 0.84, vv) * (1.0 - ridge_mask)
        atlas = atlas * (1.0 - warm_break[..., None] * 0.34) + np.array((0.65, 0.20, 0.055))[None, None, :] * warm_break[..., None] * 0.34

    # Bake the map-specific panorama exposure into the pixels. Blender's glTF
    # exporter converts this material to KHR_materials_unlit, which deliberately
    # has no Background Strength socket; keeping the multiplier here makes the
    # authored value survive in the mounted GLB instead of only in .blend renders.
    atlas = np.flipud(np.clip(atlas * profile["strength"], 0.006, 0.92))
    rgba = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    rgba[:, :, :3] = atlas
    path = OUT / f"{key}-panorama-atlas.png"
    image = bpy.data.images.new(f"{key.title().replace('-', '')}PanoramaAtlas", ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "sRGB"
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image, path


def make_material(key, atlas, profile):
    material = bpy.data.materials.new(f"{key.title().replace('-', '')}PanoramaMaterial")
    material.use_nodes = True
    material.use_backface_culling = False
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBackground")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = atlas
    texture.extension = "REPEAT"
    texture.interpolation = "Linear"
    shader.inputs["Strength"].default_value = 1.0
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Color"])
    material.node_tree.links.new(shader.outputs["Background"], output.inputs["Surface"])
    return material


def make_ring(key, material):
    vertices = []
    uvs = []
    faces = []
    for row in range(ROWS):
        v = row / (ROWS - 1)
        height = SKY_BOTTOM + v * (SKY_TOP - SKY_BOTTOM)
        radius = RADIUS + math.sin(v * math.pi) * 3.0
        for index in range(SEGMENTS + 1):
            u = index / SEGMENTS
            angle = u * math.tau
            vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, height))
            uvs.append((u, v))
    width = SEGMENTS + 1
    for row in range(ROWS - 1):
        for index in range(SEGMENTS):
            a = row * width + index
            b = a + 1
            c = (row + 1) * width + index + 1
            d = c - 1
            faces.extend([(a, c, b), (a, d, c)])

    # A closer irregular ridge belt occludes the sunk sky ring. It remains in
    # this one panorama mesh/material and carries no terrain or sim authority.
    ridge_start = len(vertices)
    for row in range(2):
        for index in range(SEGMENTS + 1):
            u = index / SEGMENTS
            angle = u * math.tau
            fraction = float(ridge_height(key, np.asarray(u, dtype=np.float32)))
            height = SKY_BOTTOM if row == 0 else RIDGE_TOP_BASE + fraction * RIDGE_TOP_SCALE
            radius = (RIDGE_FOOT_RADIUS if row == 0 else RIDGE_CREST_RADIUS) + math.sin(angle * 3.0 + 0.4) * 1.7
            vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, height))
            # The mesh silhouette owns the ridge shape; a constant texture band
            # avoids re-projecting the far ridge profile onto this nearer one.
            uvs.append((u, 0.0 if row == 0 else 0.12))
    for index in range(SEGMENTS):
        a = ridge_start + index
        b = a + 1
        d = ridge_start + width + index
        c = d + 1
        faces.extend([(a, c, b), (a, d, c)])
    mesh = bpy.data.meshes.new(f"{key.title().replace('-', '')}PanoramaMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="PanoramaUV")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            uv_layer.data[loop_index].uv = uvs[mesh.loops[loop_index].vertex_index]
    obj = bpy.data.objects.new(f"{key.title().replace('-', '')}Panorama", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(material)
    obj["render_only"] = True
    obj["panorama"] = True
    obj["affects_playfield"] = False
    obj["affects_masks"] = False
    obj["affects_spawn_edges"] = False
    obj["affects_fog_gating"] = False
    obj["mount_space"] = "game X/Y/Z at county origin"
    obj["panorama_law"] = "v2"
    obj.visible_shadow = False
    return obj


def contract_for(key, profile, obj, blend, glb, atlas_path):
    triangles = sum(len(poly.vertices) - 2 for poly in obj.data.polygons)
    return {
        "asset": glb.name,
        "map": key,
        "renderOnly": True,
        "style": "engraved Epoch 1 kit-plate horizon; warm valley against a darker fevered rim",
        "signature": profile["signature"],
        "exposure": {
            "mode": "bakedIntoAtlas",
            "linearMultiplier": profile["strength"],
        },
        "lawVersion": "PANORAMA LAW v2",
        "namedCorrections": {
            "paintedWall": "sunk sky ring behind an irregular closer ridge belt with a dusty haze transition",
            "ceiling": "engraving density grades from dense horizon to near-plain parchment zenith",
            "echo": "asymmetric cloud and dust edits plus independent near/far ridge profiles break mirrored repetition",
        },
        "projection": {
            "skyRingRadiusMeters": RADIUS,
            "ridgeFootRadiusMeters": RIDGE_FOOT_RADIUS,
            "ridgeOccluderRadiusMeters": RIDGE_CREST_RADIUS,
            "ridgeFootRadiusRangeMeters": [RIDGE_FOOT_RADIUS - 1.7, RIDGE_FOOT_RADIUS + 1.7],
            "ridgeOccluderRadiusRangeMeters": [RIDGE_CREST_RADIUS - 1.7, RIDGE_CREST_RADIUS + 1.7],
            "skyBottomMeters": SKY_BOTTOM,
            "skyTopMeters": SKY_TOP,
            "ridgeTopFormulaMeters": f"{RIDGE_TOP_BASE} + silhouetteFraction * {RIDGE_TOP_SCALE}",
        },
        "mount": claim.panorama_mount(key),
        "nonInterference": {
            "playfieldBounds": "unchanged",
            "spawnEdges": "unchanged",
            "fogGating": "unchanged",
            "waterBuildSpawnMasks": "unchanged",
        },
        "meshCount": 1,
        "primitiveCount": 1,
        "materialCount": 1,
        "vertices": len(obj.data.vertices),
        "triangles": triangles,
        "triangleBudget": 4000,
        "texture": {"count": 1, "width": ATLAS_SIZE, "height": ATLAS_SIZE, "embedded": True},
        "sourceArt": [str(KIT.relative_to(ROOT)), str(claim.CONTRACT_PLATES[profile["contract"]].relative_to(ROOT))],
        "files": {
            "blend": {"bytes": blend.stat().st_size, "sha256": sha256(blend)},
            "glb": {"bytes": glb.stat().st_size, "sha256": sha256(glb)},
            "atlas": {"bytes": atlas_path.stat().st_size, "sha256": sha256(atlas_path)},
        },
    }


def build(key):
    profile = PROFILES[key]
    claim.reset_scene()
    atlas, atlas_path = make_atlas(key, profile)
    material = make_material(key, atlas, profile)
    ring = make_ring(key, material)
    blend = OUT / f"{key}-panorama.blend"
    glb = OUT / f"{key}-panorama.glb"
    contract_path = OUT / f"{key}-panorama-contract.json"
    bpy.ops.object.select_all(action="DESELECT")
    ring.select_set(True)
    bpy.context.view_layer.objects.active = ring
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(
        filepath=str(glb),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_extras=True,
    )
    contract = contract_for(key, profile, ring, blend, glb, atlas_path)
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(contract, indent=2))


def main():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    keys = args or list(PROFILES)
    for key in keys:
        if key not in PROFILES:
            raise ValueError(f"unsupported panorama profile: {key}")
        build(key)


if __name__ == "__main__":
    main()
