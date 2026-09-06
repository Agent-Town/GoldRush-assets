---
source: codex
project: Gold Rush
date: 2026-07-20
type: reference
---

# E6 buildings and terrain batch B

## Result

Native Codex `image_gen` only. No Higgsfield still-image model was used. This run produced exactly the five files assigned by `art-e6-buildings-terrain-b`; batch 3 was not started. `prop-crates.png` is a fresh generation. The four `bld-*-e6.png` files are image edits of their named base sheets.

| File | Native job | Final size | SHA-256 | Retakes | Verdict |
|---|---|---:|---|---:|---|
| `prop-crates.png` | `exec-d04ebe30-c8a1-414a-b427-cfba620088eb` | 1254x1254 RGB | `8f15a96dc39d285b8137fc6acd21ac05e58a65825cf69846db25779f9ed490fe` | 1 | PASS |
| `bld-tavern-e6.png` | `exec-3e0107d1-0d3f-4ec4-8059-4f9d025753e4` | 1254x1254 RGB | `774509e4a68d8f3fc58fd3c272a98b46f031ef3edf3f38f0911e897a574881fe` | 0 | PASS |
| `bld-signal-turret-e6.png` | `exec-63fc4570-801c-4ea5-bc44-497108df9697` | 1254x1254 RGB | `e18e0b6dd3d31a80ac30e3b45e360e2f5d9c9d1fe0f0d2a3f9e908b7798eafa3` | 0 | PASS |
| `bld-palisade-e6.png` | `exec-adae7058-7082-4755-bd57-3c7aa43067bc` | 1254x1254 RGB | `5ac767e783f53879cd7d5e5ca1145a1d1a74f1fd78e741371cf38f953399b54e` | 0 | PASS |
| `bld-schoolhouse-e6.png` | `exec-b62e855c-4adc-4f1f-a2a1-1e0682fe095c` | 1254x1254 RGB | `d2b0275e810296e9d15ea23040f0822711df05f24b794a8b56fae47199632709` | 0 | PASS |

The first crate take (`exec-5f9d64c3-d011-4629-a80e-c80b0e419108`) was rejected because it baked a checkerboard into an RGB background. The retake uses a plain warm ground. No other file needed a retake.

Native run directory: `019f800c-bf75-70a1-80fc-18e5e62e8aa6`.

## Measured self-QA

Bounds were measured from Canny edge extents. Ratios compare normalized painted width and height against each transform's base sheet; `prop-crates.png` is fresh and has no base transform.

| File | Silhouette reads | Palette in era | Footprint matches base | Letters / firearms / gore none | Normalized bounds |
|---|---|---|---|---|---|
| `prop-crates.png` | Y | Y | Y (fresh; no base) | Y | 95% W × 85% H |
| `bld-tavern-e6.png` | Y | Y | Y | Y | 1.02× W × 1.02× H vs `bld-tavern.png` |
| `bld-signal-turret-e6.png` | Y | Y | Y | Y | 1.00× W × 1.00× H vs `bld-signal-turret.png` |
| `bld-palisade-e6.png` | Y | Y | Y | Y | 1.00× W × 1.00× H vs `bld-palisade.png` |
| `bld-schoolhouse-e6.png` | Y | Y | Y | Y | 1.01× W × 1.01× H vs `bld-schoolhouse.png` |

All five silhouettes remain readable in a 128px contact pass. The Tavern retains its roof, chimney, hanging-sign, balcony, stair, and side-wing envelope; the Sunline Mount retains the four-foot trestle, deck, ladder, mast height, and outer ring; the Glow Fence retains two posts, three rails, and the original openings; the Institute retains the schoolhouse roof, porch, tower peak, stairs, and side-prop envelope. The crates read as civilian provisions and hand tools, not munitions.

All five use chrome, pastel cream/mint enamel, warm timber/parchment, and starstone teal. Visual review found no letters, numbers, logos, watermarks, firearms, gore, sickness, or corrosion. OCR was empty on four files; the schoolhouse returned only nonsensical engraved-texture fragments, with no visible text on full-size review.

Normalized 1254px side-by-side telemetry gave edge-energy ratios of 1.14 Tavern, 1.00 Sunline Mount, 0.72 Glow Fence, and 1.01 Institute. The Glow Fence reduction is the intended smoother enamel face replacing timber grain; its measured outer bounds remain 1.00x the base. First-principles target: retain each inherited outer envelope and gameplay-scale identity while making the E6 material transformation obvious. Verdict: all four E6 edits are less wrong than their bases against that target; ACCEPT.

## Final prompts

Every prompt included this exact task anchor:

> Gold Rush house building art: warm engraved-frontier illustration, full-bleed painted structure on transparent-ready plain ground, no letters, no gore.

### Combine supply crates

Fresh square generation of a compact stack of intact and opened civilian frontier supply crates. Open crates contain harmless wrapped provisions, hand tools, and sealed soft-teal starstone canisters, never ammunition. Timber crates use rounded chrome bands, pastel cream/mint enamel corners, restrained teal pips, and simple atomic-starburst pictograms. Top-down three-quarter game view on one plain warm opaque ground, centered, complete, uncropped, and readable at 96px. No checkerboard, scenery, text, letters, numbers, labels, barcodes, logos, watermark, people, creatures, weapons, firearms, bullets, shells, explosives, gore, sickness, corrosion, black voids, or photorealism.

### Atomic Diner edit

Image 1 (`bld-tavern.png`) was the only edit target; `plate-e6-bld-atomic-diner.png` and batch-A `bld-isotope-kitchen.png` were material references. Repaint only the Tavern's surface skin into an Atomic Diner while preserving the exact two-story silhouette, rooflines, chimney, arched facade, hanging-sign shape, balcony, stairs, rails, side wings, doors, windows, footprint, height, scale, viewpoint, framing, and outer edges. Fit one rounded chrome counter band to the existing lower facade, pastel cream/mint enamel within existing wall faces, soft teal pips along existing rails, and restrained jukebox-like window glow. Keep inherited timber visible. Do not add a car, umbrella, patio, detached props, annex, dome, tower, roof, or platform. Blank/pictogram-only sign; no text, letters, numbers, logos, watermark, people, creatures, firearms, weapons, gore, sickness, corrosion, black voids, or photorealism.

### Sunline Mount edit

Image 1 (`bld-signal-turret.png`) was the only edit target; batch-A `bld-decay-clock.png` and `bld-reactor-dome.png` were material references. Repaint only the skin and mechanism inside the existing top ring. Preserve the exact timber trestle, four splayed feet, cross-bracing, ladder, square deck, guard posts, mast height, circular outer ring, footprint, height, scale, viewpoint, framing, and outer edges. Within the unchanged ring envelope, reinterpret the cyan lantern as a shallow polished parabolic sun mirror with teal focus cell; use fitted chrome, pastel cream/mint enamel, starstone teal, and restrained brass. It reads as a solar mirror/signal instrument, never a weapon. No added platform, dish outside the ring, barrel, muzzle, projectile, detached prop, text, letters, numbers, logos, watermark, people, creatures, firearms, weapons, gore, sickness, corrosion, black voids, or photorealism.

### Glow Fence edit

Image 1 (`bld-palisade.png`) was the only edit target; batch-A `bld-appliance-pen.png` was the material reference. Repaint only the existing two-post/three-rail segment. Preserve both tall end posts, all three horizontal rails, rope-wrap locations, openings, footprint, height, scale, viewpoint, framing, and every outer edge. Apply mint/cream pastel enamel faces and narrow chrome edge bands to the existing rails while retaining warm timber grain; turn rope wraps into fitted chrome/brass collars of the same thickness; embed soft teal pips flush within existing forms. No extra posts, rails, wires, gate, ground scene, detached props, text, letters, numbers, logos, watermark, people, creatures, firearms, weapons, gore, sickness, corrosion, black voids, or photorealism.

### Isotope Institute edit

Image 1 (`bld-schoolhouse.png`) was the only edit target; batch-A `bld-decay-clock.png` and `bld-isotope-kitchen.png` were material references. Repaint only the material skin and the detail inside the existing bell-tower volume. Preserve the exact one-story schoolhouse silhouette, gabled roof, porch, stairs, doors, windows, bench/barrels/crates envelope, square bell tower, tower roof peak, footprint, height, scale, viewpoint, framing, and every outer edge. Use pastel cream/mint enamel inset wall panels, narrow chrome roof/porch bands, and starstone-teal accents. Inside the existing open tower only, reinterpret the bell as a compact unlabeled teal isotope dial under a shallow chrome dome without exceeding the original tower silhouette. No annex, observatory, dome above the roof, larger tower, external pipes, detached machinery, text, letters, numbers, equations, logos, watermark, people, creatures, firearms, weapons, gore, sickness, corrosion, black voids, or photorealism.

No extraction, alpha processing, resizing, runtime wiring, townsfolk, icons, or batch-3 work was performed.
