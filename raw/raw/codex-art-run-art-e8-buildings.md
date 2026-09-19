---
source: codex
project: Gold Rush
date: 2026-07-21
type: reference
---

# E8 Orbital Frontier buildings batch 1

## Result

Native Codex `image_gen` only. No Higgsfield still-image model was used. This run produced exactly the six files assigned by `art-e8-buildings`; transforms/terrain, roster art, and town icons were not started.

| File | Native final job | Final size | SHA-256 | Retakes | Verdict |
|---|---|---:|---|---:|---|
| `bld-dome-habitat.png` | `exec-b22eef93-ac87-4025-a108-013160d0b84a` | 1254x1254 RGB | `4f794dec3226b77261f8cc33fcb3ba5bf565fe6247837e5be6956c8af144033f` | 1 framing-only | PASS |
| `bld-airlock-gate.png` | `exec-f3ab5fa6-6417-40e7-b87b-b758d33f67f3` | 1254x1254 RGB | `5b3e61ab3e9e7b021df04afd9f7cd9d224c4b1fc95157b4a716a9c34878a1b56` | 1 framing-only | PASS |
| `bld-launch-pad.png` | `exec-f31d4d07-8ed9-4060-80dd-b7b4711958f6` | 1254x1254 RGB | `5569a0ceac890b98e3c87c50b35e03dbfb109f28fc7da2928f97b476cd550cf3` | 0 | PASS |
| `bld-solar-lens-array.png` | `exec-4da63380-2d99-44b8-a412-8224fce1ce0a` | 1254x1254 RGB | `28f90dd5ddd06498f41472dcbeb71b24097bb2e56f872dabf42d36df9f05bf5c` | 0 | PASS |
| `bld-mass-driver-rail.png` | `exec-f42f9d75-5561-437a-8d38-0cdfaf79c824` | 1254x1254 RGB | `7433b5951f63e97ef5935666cff67aceaac2d7581b1d6cdeb4e2e689f9a10ed7` | 0 | PASS |
| `bld-regolith-works.png` | `exec-56a20b90-90f0-4943-9b5a-cfb00cbecc04` | 1254x1254 RGB | `f0a895d9e5d5680917ba8c9acb458f697f30d9baa7adca31a8b213fddd5578db` | 1 framing-only | PASS |

Native run directory: `019f80f7-b02f-7021-ab82-c6b513974750`.

## Measured self-QA

Visible-height/diagonal-footprint ratios are approximate normalized subject envelopes measured against the 1254px canvas and checked against the shipped E7 `bld-*` 83–93% band. Every final also passed a 128px contact review.

| File | Silhouette reads | Palette in E8 | Height in band | Letters / firearms / gore none | Measured note |
|---|---|---|---|---|---|
| `bld-dome-habitat.png` | Y | Y | Y | Y | ~88%; welcoming glass dome, palisade-derived ribs, sealed entry |
| `bld-airlock-gate.png` | Y | Y | Y | Y | ~84%; double hatch, one pressure wheel, honey-gold porthole |
| `bld-launch-pad.png` | Y | Y | Y | Y | ~89%; stationary civil capsule, broad pad, gantry and umbilicals |
| `bld-solar-lens-array.png` | Y | Y | Y | Y | ~86%; open glass lenses/mirrors feed a power receiver; no barrel or target |
| `bld-mass-driver-rail.png` | Y | Y | Y | Y | ~85% diagonal envelope; exposed twin rails, sleepers, loading deck, blank freight sled; no tube or muzzle |
| `bld-regolith-works.png` | Y | Y | Y | Y | ~90%; sifting drum, twin hoppers, tailings and teal He-3 collection pan |

Full-size and 128px visual review found no visible letters, numbers, logos, watermarks, firearms, gore, or people. OCR returned engraved-texture fragments only, with no credible text. Silver, teal, suit brass, honey-gold glass, warm-grey stippled lunar ground, and parchment negative space dominate; E7 walnut remains only as restrained lineage bracing.

## Final prompts

Every initial prompt and framing correction included this exact anchor:

> Gold Rush house building art: warm engraved-frontier illustration, full-bleed painted structure on transparent-ready plain ground, no letters, no gore.

### Dome Habitat

Create one fresh Dome Habitat building for Epoch 8 Orbital Frontier. The wall is AIR: a welcoming transparent honey-gold glass panel dome over timber-and-suit-brass ribs, descended from the frontier palisade/stockade lineage. Make the ribs visibly echo upright palisade posts without reading as a fort. Warm inhabited interior glow through the glass, small restrained teal agent-glow fittings, silver structural bands, and a compact sealed entry. One complete isolated building in top-down three-quarter oblique game view, centered on plain warm parchment with a small warm-grey stippled regolith footprint and generous vacuum-like negative space; uncropped; readable at 96px; visible structure height 83–93% of the square canvas. No people, secondary building, horizon, signage, writing, letters, numbers, labels, logos, watermark, checkerboard, firearms, barrels, muzzles, cannons, missiles, ammunition, targets, weapons, gore, cold photorealism, black void, or busy scenery.

Framing correction: scale the entire complete structure uniformly up about 6 percent and recenter it so the visible building height lands around 85–88 percent, preserving all design/material/camera details and all feet/ramp with parchment padding.

### Airlock Gate

Create one fresh Airlock Gate building for Epoch 8 Orbital Frontier: the ford of the era, a heavy double-hatch brass airlock portal marking the threshold between vacuum and air. Timber-braced suit-brass frame, two clearly closed nested pressure doors, one small hand pressure-wheel, one honey-gold porthole, silver seals, restrained teal pressure-status glow. It reads immediately as a doorway/gate and civil threshold, never a weapon emplacement. One complete isolated freestanding gate in top-down three-quarter oblique game view on warm parchment and warm-grey stippled regolith; uncropped; readable at 96px; 83–93% visible height. Blank plates only. No people, extra building, signage, writing, letters, numbers, labels, logos, watermark, checkerboard, firearms, barrels, muzzles, cannons, missiles, ammunition, targets, weapon mounts, gore, cold photorealism, black void, or busy scenery.

Framing correction: scale the entire complete gate uniformly up about 8 percent and recenter it so the visible structure height lands around 85–88 percent, preserving all design/material/camera details and all brace feet, threshold, and ramp with parchment padding.

### Launch Pad

Create one fresh civil Launch Pad building for Epoch 8 Orbital Frontier, the town's umbilical: a timber-and-suit-brass launch gantry on a low silver pad platform, with a slender fuel/air service mast, open hold-down arms, hose-like umbilicals, and one small rounded blank cargo-and-people capsule waiting upright. It reads as civilian transport infrastructure, never a missile site. One complete isolated launch structure in top-down three-quarter oblique game view on warm parchment and warm-grey stippled lunar footing; uncropped; readable at 96px; 83–93% visible height. Keep the capsule attached to the broad pad and gantry, not in flight. No flames, launch plume, munitions, weapon framing, signage, writing, letters, numbers, logos, watermark, people, firearms, barrels, muzzles, cannons, missiles, rockets-as-weapons, warheads, ammunition, targets, gore, cold photorealism, black void, horizon, starscape, or busy scenery.

### Solar Lens Array

Create one fresh Solar Lens Array building for Epoch 8 Orbital Frontier, E6 Sunline's big sister: a civil tracking array of three large honey-gold glass focusing lenses and two broad mirror panels on a low articulated suit-brass gimbal frame. It follows the long lunar day and concentrates sunlight into a compact heat/power receiver cell. Make it unmistakably an OPTIC and power instrument, with open circular lens frames, visible glass, wide mirror faces, gear teeth, and restrained teal status glow; no barrel and no target. One complete isolated array in top-down three-quarter oblique game view on warm parchment and warm-grey stippled regolith; uncropped; readable at 96px; 83–93% visible height. No people, buildings, words, writing, letters, numbers, labels, logos, watermark, firearms, gun forms, barrels, muzzles, cannons, missiles, ammunition, sights, crosshairs, targets, beam weapon, projectile beam, gore, cold photorealism, black void, horizon, or busy scenery.

### Mass-driver Rail

Create one fresh Mass-driver Rail building for Epoch 8 Orbital Frontier, E2's rail spur generations later: a long exposed inclined electromagnetic CARGO-launch railway/track on timber-and-steel trestles, visibly continuous twin rails from a broad loading deck at the low end to an open elevated runway end. Many separate brass induction coils sit alongside and beneath the rails, never enclosing them into a tube. One blunt blank rectangular supply canister rides openly on a flat cargo sled halfway up the track, strapped as freight. This THROWS CARGO to orbit and must read as railway infrastructure, not a gun. One complete isolated diagonal rail structure in top-down three-quarter oblique game view on warm parchment and warm-grey stippled regolith; uncropped; both track ends visible; readable at 96px; diagonal silhouette fills 83–93% of the square. No tubular bore, circular muzzle, barrel, recoil carriage, weapon silhouette, people, signage, writing, letters, numbers, labels, logos, watermark, firearms, guns, cannons, missiles, rockets, ammunition, warheads, targets, sights, projectiles, gore, cold photorealism, black void, horizon, or busy scenery.

### Regolith Works

Create one fresh Regolith Works building for Epoch 8 Orbital Frontier, the orbital pan-house: a compact civilian moon-dust sifting and refining works with one large horizontal rotating suit-brass mesh drum, two broad feed hoppers, an open sorting trough, small warm-grey regolith tailing piles, and restrained teal He-3 flecks visibly caught in a shallow collection pan. It reads first as mining/refining machinery descended from gold panning, never as a weapon. One complete isolated works building in top-down three-quarter oblique game view on warm parchment and warm-grey stippled lunar ground; uncropped; readable at 96px; 83–93% visible height. Blank plates and gauges only. No people, creatures, writing, letters, numbers, labels, logos, watermark, firearms, barrels, muzzles, cannons, missiles, ammunition, targets, weapon mounts, gore, cold photorealism, black void, horizon, or busy scenery.

Framing correction: scale the entire complete works uniformly up about 4 percent and recenter it so the visible structure height lands around 85 percent, preserving all design/material/camera details and all hopper rims, feet, tailing pan, lamp, and regolith footprint with parchment padding.

No processing, extraction, alpha work, resizing, runtime wiring, E8 transform edits, terrain, roster art, town portraits, or icons were performed.
