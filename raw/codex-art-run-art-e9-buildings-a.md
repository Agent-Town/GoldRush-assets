---
source: codex
project: Gold Rush
date: 2026-07-21
type: reference
---

# E9 Red Fields buildings batch 1

## Result

Native Codex `image_gen` only. No Higgsfield still-image model was used. This run produced exactly the five fresh files assigned by `art-e9-buildings-a`; Ark scaffold states, E9 transforms/terrain, roster, town icons, processing, and wiring were not started.

The literal E1 riverbank callback was taken from the existing ledger measurement (mean RGB `79.9,102.6,76.0`) and pinned in prompts as RGB `80,103,76` / `#50674c`.

| File | Native final job | Final size | SHA-256 | Retakes | Verdict |
|---|---|---:|---|---:|---|
| `bld-dome-commons.png` | `exec-0a20b18e-c272-47c0-baf2-0f3886ff344a` | 1254x1254 RGB | `f68a5ae32910210df0fd96e44ce1864e6ca93ce2418b82cb540f5ea4a12c8ad4` | 0 | PASS |
| `bld-canal-works.png` | `exec-077ba876-0e9b-4ffc-9bed-0eb5516887f5` | 1254x1254 RGB | `d9b5fbc7a4365fbd3ddc1cad00663acc28516ef43acb0d6e76cfbbf84773b22f` | 0 | PASS |
| `bld-ice-quarry-rig.png` | `exec-7a85c625-e103-48ad-b480-b61cc272ae07` | 1254x1254 RGB | `8e32e6c6abd3ec8b0e3deae3b4955e06d907f85fee99b34b8d6b568a969c8162` | 0 | PASS |
| `bld-weather-spire.png` | `exec-e2fe00b8-4c64-47ac-987a-3a4738c51884` | 1254x1254 RGB | `a2a9a934d48c4b30f8c5a6ec0599bb2b8285e40c9799b9dd672783ea521d4292` | 2 | PASS |
| `bld-seed-vault.png` | `exec-9c392381-2fb5-4a0a-8a05-e9c33033fedc` | 1254x1254 RGB | `5d170ee2c325a38e6d6c358d09a028db90274de301828d00b9fbf1adc88a40d8` | 1 | PASS |

Native run directory: `019f8135-bfc3-78d3-9106-22bb404d7ddc`.

## Measured self-QA

Visible-height ratios use the largest dark/colored connected structure envelope on the 1254px parchment canvas. Every final passed direct full-size inspection, a five-up 128px gameplay-scale contact review, and OCR with empty output.

| File | Silhouette reads Y/N | Palette in E9 Y/N | Height in band Y/N | Letters / firearms / gore none Y/N | Height read vs E8 band |
|---|---|---|---|---|---|
| `bld-dome-commons.png` | Y | Y | Y | Y | ~85.3%; broad warm-lit communal dome, front threshold and planted base |
| `bld-canal-works.png` | Y | Y | Y | Y | ~84.6%; dry stepped lock chambers and great waiting wheel |
| `bld-ice-quarry-rig.png` | Y | Y | Y | Y | ~89.0%; gantry, hoisted block, quarry cut and downward saw-wheel |
| `bld-weather-spire.png` | Y | Y | Y | Y | ~90.9%; open vane-rings, wind cups, coils and warm/teal crown instrument; no barrel/target |
| `bld-seed-vault.png` | Y | Y | Y | Y | ~84.6%; compact raised berm, warm glass entry, seed racks and exact-green shoots |

Palette review: rust-red engraved earth/timber, parchment, aged brass and honey-warm glass dominate all five. E8 orbital silver does not dominate. Dome and Seed Vault are warm-lit from within. Vegetation uses the E1 callback swatch; teal remains restricted to small agent-tech instruments and cool ice.

Canon review: no people, firearms, weapons, gore, readable writing, logos, or military silhouettes. Weather Spire reads as atmospheric control through open rings, wind cups and condensation coils. Ice Quarry Rig reads as civil cutting/hoisting works. Canal Works is dry infrastructure awaiting water.

## Final prompts

Every initial generation and correction included this exact anchor:

> Gold Rush house building art: warm engraved-frontier illustration, full-bleed painted structure on transparent-ready plain ground, no letters, no gore.

### Dome Commons

Create one fresh Epoch 9 Dome Commons, the tavern lineage's apotheosis and the biggest shared interior yet. A large welcoming communal glass dome, broad and civic rather than fortified, with warm-glowing interior rooms visible through glass panels over a rust-red timber-and-brass frame. Echo the tavern's gathering-house silhouette family through a clear front entrance, porch-like threshold and communal massing, but do not copy it. Show a small literal callback of E1 riverbank green RGB 80,103,76 (`#50674c`) in planted beds visible inside and around the base. One isolated complete building, centered, uncropped, top-down three-quarter oblique gameplay view, plain warm parchment ground, generous negative space, readable at 96px; visible height 83–93% of the square canvas. E9 rust-red engraved earth/frame, aged brass, honey-warm interior glass, restrained agent-teal only on tiny instruments; no dominant orbital silver. Welcoming commons; no people, second building, horizon, fort, bunker, weapon emplacement, firearms, barrels, muzzles, cannons, targets, weapons, writing, logos, watermark, checkerboard, photorealism, or unrelated lush green.

### Canal Works

Create one fresh Epoch 9 Canal Works, THE building of the Red Fields era and the sluice lineage's apotheosis. A compact but monumental civil hydro-engineering structure built ahead of the water: multiple timber-and-brass lock gates, dry stepped canal chambers, handwheels and gear housings, and one great vertical water-wheel unmistakably WAITING DRY for the day it turns. No flowing water; only a very thin damp edge and one thread of literal E1 riverbank green RGB 80,103,76 (`#50674c`) at that edge. Echo the original sluice's open trough, timber braces and wheel family without copying its exact layout. One isolated complete works, centered, uncropped, top-down three-quarter oblique gameplay view on plain warm parchment and rust-red footing, readable at 96px; visible height/diagonal footprint 83–93%. Rust-red timber/earth, aged brass, warm dark dry channels, restrained teal on tiny civil gauges; no dominant orbital silver. Blank faces/plates; no people, active waterfall, broad water flow, weapon form, text, logos, watermark, checkerboard, photorealism, or busy scenery.

### Ice Quarry Rig

Create one fresh Epoch 9 Ice Quarry Rig, the water-miners' civil quarry works that carves subsurface ice into blocks for the canal. A tall brass-and-timber quarry gantry/derrick over a clearly excavated square ice cut, with a chain hoist lifting one translucent cool teal-white rectangular ice block, clean cut ice blocks stacked at the base, a broad mechanical cutting frame with visible toothed saw-wheel oriented downward into the quarry, and warm-grey/rust tailings. It reads as mining and block-cutting infrastructure, never an emplacement. One isolated complete rig, centered, uncropped, top-down three-quarter oblique gameplay view on warm parchment and rust-red footing, readable at 96px; visible height 83–93%. E9 rust timber/earth, brass mechanisms, cool ice, warm-grey/rust tailings and restrained teal instruments; no dominant orbital silver. No people, weapon, turret, gun, barrel, muzzle, cannon, drill-cannon silhouette, target, text, logos, watermark, checkerboard, photorealism, or busy landscape.

### Weather Spire

Create one fresh Epoch 9 Weather Spire, E4/E5 weather-tech's civic endgame: a tall engraved atmospheric-control mast that calls rain and breaks storm fronts. A tapered rust-red timber-and-brass spire on a broad stable civil base, with several open horizontal vane-rings, wind cups, condensation coils spiraling around the mast, rain-catching fins, glass barometer bulbs, and a warm-glowing crown instrument with restrained teal agent-glow. It reads immediately as a weather instrument, not a weapon; no directional firing tube. One isolated complete spire, centered, uncropped, top-down three-quarter oblique gameplay view on warm parchment and rust-red footing, readable at 96px; visible height 83–93%, all feet visible. No people, writing, labels, weapon, barrel, muzzle, bore, cannon, gun, firearm, beam emitter, target, crosshair, logos, watermark, checkerboard, photorealism, or busy landscape.

Targeted corrections: blank every tiny wind-cup disc and gauge face, removing pseudo-writing while preserving the design; then scale the complete corrected spire uniformly down about 6% and recenter to a 90–92% visible-height read with crown and base fully visible.

### Seed Vault

Create one fresh Epoch 9 Seed Vault, the green economy's bank. A low welcoming bermed vault-house: rust-red engraved earth berm wraps a sturdy brass-and-glass entry hall, broad warm-lit glass front, rounded roof planted into the berm, and visible interior seed racks, unlabeled jars, seed trays and new green shoots. The green literally uses E1 riverbank RGB 80,103,76 (`#50674c`) through the glass and in a narrow planted strip at the entry. It reads as a granary/vault and community seed house, not a bunker. One isolated complete building, centered, uncropped, top-down three-quarter oblique gameplay view on plain warm parchment, readable at 96px. E9 rust earth, aged brass, honey-warm glass/interior, exact-green shoots, tiny teal instruments only; no dominant orbital silver. No people, labels, text, fortification, weapon, logos, watermark, checkerboard, photorealism, unrelated lush landscape, or busy scenery.

Targeted correction: compact the width about 12%, raise the arched glass roof and berm about 18%, and extend the entry/stairs slightly downward; recenter to an 84–87% height and at most 92% width while preserving the same welcoming seed-house identity and all blank racks/containers.

No processing, extraction, alpha work, resizing, runtime wiring, E9 transforms/terrain, Ark scaffold states, roster art, town portraits, icons, or later-era work was performed.
