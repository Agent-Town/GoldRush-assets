---
source: codex
project: Gold Rush
date: 2026-07-20
type: reference
---

# E6 buildings and terrain batch A

## Result

Native Codex `image_gen` only. No Higgsfield still-image model was used. This run produced exactly the seven files assigned by `art-e6-buildings-terrain-a`; batch 2 was not started.

| File | Native job | Final size | SHA-256 | Retakes | Verdict |
|---|---|---:|---|---:|---|
| `bld-reactor-dome.png` | `exec-541f661e-fbd1-426a-8f57-b4d330dd514e` | 1672x941 RGB | `fc5191539377ab224a4913cfb161c07b76b986996ab008b143282847eb94437b` | 0 | PASS |
| `bld-isotope-kitchen.png` | `exec-f1aa42f1-0ce2-409e-ae22-cdb7785dd195` | 1254x1254 RGB | `156fb47b8cbc608df7b9c47cc49eb563ece5911c0f71501751485fa88d49c89d` | 0 | PASS |
| `bld-appliance-pen.png` | `exec-df114df6-4b39-4c93-b7c6-967ee3844e74` | 1254x1254 RGB | `099d7ad867317995d02d67e886fee2dc8998527814547c00e0a04108bf34f964` | 0 | PASS |
| `bld-decay-clock.png` | `exec-de99e225-0377-4ee3-bf9d-dbb8d2974cf3` | 1254x1254 RGB | `c0526f11f5e434353d32ebe1e0f1d8dc8eaf358db164db0fedd54aa1712dda99` | 0 | PASS |
| `bld-catalog-warehouse.png` | `exec-6218c01b-0fb9-498f-9b0e-20d1af121e25` | 1254x1254 RGB | `8c9c91eee2b132610f9b9f8ad33cee2e1469c101592dd34bef4e8ce843f9adc2` | 0 | PASS |
| `ter-glowmesa-atlas.png` | `exec-2ffc08e9-67f8-4ac9-a513-a6a3d53fb1e3` | 1254x1254 RGB | `aa96c122968dec3fe40515f46fc09febc34795c2fc1c8455da2d1534d7377ea5` | 0 | PASS |
| `prop-decay-puddles.png` | `exec-caaa088c-f639-48b3-87ed-0adc708f7bb3` | 1671x941 RGB | `83edea57a8e2e4fe884a83bf85dbc53c20e717dace6757a40c120830195aea07` | 0 | PASS |

The native Reactor source was cropped vertically and normalized to the shipped 1672x941 two-cell band without changing composition. The native puddle source supplied the strong state; that cell was copied twice and reduced with deterministic saturation/value modulation so all three states have pixel-identical geometry and differ only in glow intensity.

Native run directory: `019f7d5d-ec93-7480-8e46-ae49579cc8fd`.

## Measured self-QA

Height ratio is the painted subject's visible vertical bound divided by canvas height, measured on the final files. The accepted shipped building references span both square portraits and wide state sheets.

| File | Gameplay-zoom read | Palette / state law | No letters or numbers | Visible height ratio |
|---|---|---|---|---:|
| `bld-reactor-dome.png` | twin doorless domes read at 128px | teal observation ring; humming → dormant; same silhouette | PASS | 55% per wide state cell |
| `bld-isotope-kitchen.png` | lab-diner, hood arms, sample case | chrome counter band; mint/cream enamel; teal samples | PASS | 86% |
| `bld-appliance-pen.png` | enclosed corral and mower read | chrome rails; pastel posts; starstone pips | PASS | 72% |
| `bld-decay-clock.png` | clock tower and large dial read | teal dial; chrome/enamel civic utility | PASS | 91% |
| `bld-catalog-warehouse.png` | loading canopy, depot, crates read | pastel crates; restrained amber; pictograms only | PASS | 80% |
| `ter-glowmesa-atlas.png` | four materials remain distinct at 128px | caprock / scree / enamel road / teal vein-rock | PASS | n/a, exact 2x2 atlas |
| `prop-decay-puddles.png` | three glow stages remain distinct at 128px | identical silhouette; strong → medium → dim teal | PASS | 70% per cell |

OCR produced no credible text on any file; the Reactor's engraved mechanical marks produced only nonsensical false positives. Visual review found no letters, numbers, watermarks, firearms, gore, sickness, or corrosion.

## Final prompts

Every prompt included this exact task anchor:

> Gold Rush house building art: warm engraved-frontier illustration, full-bleed painted structure on transparent-ready plain ground, no letters, no gore.

### Reactor Dome

Two equal side-by-side cells showing the exact same raised Deep Reactor building silhouette: left humming, right dormant. A rivet-seamed low hemispherical dome with a continuous teal observation ring and absolutely no visible door. Humming has soft teal starstone light and restrained amber instrument pips; dormant has identical geometry, camera, scale, and placement with glow faded through engraved hatch-steps, never corrosion or sickness. Square two-cell source sheet, top-down three-quarter oblique game view, complete and uncropped, readable at 96px. References: `plate-e6-bld-reactor-dome.png`, `bld-rail-depot.png`, `bld-machine-shop.png`, `kit-era-6.png`. No people, creatures, writing, watermark, firearms, sickness, corrosion, black voids, or photorealism.

### Isotope Kitchen

One gleaming lab-diner hybrid building: rounded chrome counter band, pastel enamel walls, lead-glass extraction hoods, articulated tong arms, and a diner pie case repurposed for softly glowing mineral samples. The humorous domestic-laboratory function reads without signage. Square runtime portrait, top-down three-quarter oblique game view, complete and uncropped, readable at 96px. References: `plate-e6-bld-isotope-kitchen.png`, `plate-e6-bld-atomic-diner.png`, `bld-rail-depot.png`, `bld-machine-shop.png`, `kit-era-6.png`. No people, creatures, writing, watermark, firearms, gore, sickness, corrosion, black voids, or photorealism.

### Appliance Pen

A cheerful atomic-era wrangler corral: sturdy low fenced yard with rounded chrome rails, pastel enamel posts, and embedded starstone-teal pips. Inside are a few pacified domestic Combine appliances, dominated by one tethered mower grazing dry frontier grass. Read first as a corral, not a house or junkyard. Square runtime portrait, top-down three-quarter oblique game view, complete and uncropped, readable at 96px. References: `plate-e6-bld-atomic-diner.png`, `kit-era-6.png`, `bld-palisade.png`, `bld-stockpile-yard.png`, `bld-rail-depot.png`. No people, creature anatomy, writing, watermark, firearms, gore, sickness, corrosion, scrap heap, black voids, or photorealism.

### Decay Clock

A compact frontier town half-life clock tower: one tall teal circular dial with simple unlabeled tick marks and one bold hand, chrome-and-pastel-enamel housing, weathered timber/brass lower utility room, and softly glowing starstone regulators. Read unmistakably as a clock tower without numerals or writing. Square runtime portrait, top-down three-quarter oblique game view, complete and uncropped, readable at 96px. References: `plate-e6-bld-atomic-diner.png`, `kit-era-6.png`, `bld-sentry-beacon.png`, `bld-signal-turret.png`, `bld-rail-depot.png`. No people, creatures, equations, writing, watermark, firearms, gore, sickness, corrosion, black voids, or photorealism.

### Catalog Warehouse

The Combine's abandoned mail-order depot: broad frontier warehouse with high loading canopy, sealed rolling doors, exterior parcel chutes, and orderly stacks of pastel-enamel shipping crates. Crates carry only simple atomic starburst pictograms. Recently deserted, orderly, faintly amber-lit, never ruined. Square runtime portrait, top-down three-quarter oblique game view, complete and uncropped, readable at 96px. References: `plate-e6-bld-atomic-diner.png`, `kit-era-6.png`, `bld-rail-depot.png`, `bld-stockpile-yard.png`, `bld-machine-shop.png`. No people, creatures, writing, barcodes, watermark, firearms, gore, sickness, corrosion, black voids, or photorealism.

### Glow Mesa atlas

A clean 2x2 terrain atlas with exactly four equal edge-to-edge cells: top-left warm ochre mesa caprock with engraved fractures; top-right loose dusty scree; bottom-left worn pastel-mint and cream enamel road with thin chrome/brass seams; bottom-right warm dark starstone vein-rock with restrained teal flecks. Identical scale and top-down orthographic lighting, no gutters or focal objects. References: `ter-canyon-atlas.png`, `ter-dustflats-atlas.png`, `kit-era-6.png`. No writing, icons, watermark, people, creatures, buildings, firearms, gore, sickness, corrosion, black voids, photorealism, or nighttime scene.

### Decay puddles

Exactly three equal side-by-side cells showing the same irregular shallow decay puddle silhouette and identical camera/scale: strong soft teal glow, medium fading teal glow, nearly-safe dim residual teal flecks. Decay appears only as glow fading through engraved hatch-steps, never corrosion, poison, slime, illness, or gore. Wide horizontal sheet, complete top-down puddle centered in each cell, no gutters or labels, readable at gameplay zoom. References: `kit-era-6.png`, `ter-dustflats-atlas.png`, `plate-e6-boss-homemaker-9000.png`. No writing, watermark, people, creatures, buildings, firearms, gore, sickness, corrosion, black voids, or photorealism.

No processing, extraction, runtime wiring, transforms, town portraits, icons, crates, or batch-2 assets were performed.
