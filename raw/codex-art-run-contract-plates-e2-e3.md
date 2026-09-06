---
source: codex
project: Gold Rush
date: 2026-07-19
type: reference
---

# E2-E3 contract-board plates

## Result

Native Codex `image_gen` only. No Higgsfield still-image model was used. Every plate was conditioned on three of the six existing contract plates plus its map's run-camera and landmark-verdict render. The six anchors measure 1672x941 (1.77683:1 landscape), so this batch matches their exact card aspect and dimensions.

| Plate | Native job | Retakes | Size / mode | Mean luminance | SHA-256 | Verdict |
|---|---|---:|---|---:|---|---|
| `plate-contract-e2-trestle.png` | `exec-b523245f-ec93-4082-8d4a-4fc3a62b6421` | 0 | 1672x941 RGB | 0.251 | `6cd06ef04d32a5dcb266a425f904ef9cf01c789638b6a1e098b97da1e472a75f` | PASS |
| `plate-contract-e2-pressure-garden.png` | `exec-5cebca02-2630-4d57-8147-e565f18290fe` | 0 | 1672x941 RGB | 0.369 | `733410f5a8855d0dda5de0249d9bf54235873a276ff6eaedf982ad0d03a55257` | PASS |
| `plate-contract-e2-incline.png` | `exec-0db6d3cd-1796-49ca-8dc4-6de71cfe8a2b` | 1 | 1672x941 RGB | 0.403 | `e04f6930691fcf5c1339f39a24325de3c61e6ab691f1db699a775587c3d9afd8` | PASS |
| `plate-contract-e3-blackout-ridge.png` | `exec-efff21fe-48b4-4444-bfcf-67e8fd347e3b` | 0 | 1672x941 RGB | 0.099 | `5d0c0d2e2e4d04dcad2a9a0c4fa4ced78a4e6a6cb5c2c5d7e056cb896f0fddcd` | PASS |
| `plate-contract-e3-moth-season.png` | `exec-02339822-79ff-49f8-a821-228a3cf8c7a5` | 1 | 1672x941 RGB | 0.106 | `7d649da83b06c4f369f568ee799b20e1c61fa10534d74a30fd542b30f8920f9f` | PASS |
| `plate-contract-e3-canyon-works.png` | `exec-e24a86ef-8b60-4210-b0a2-9b838835a60b` | 0 | 1672x941 RGB | 0.191 | `cb1c804eb40555d28961b09e0218168536fa5550405a2e18c1dab5b4f3caba29` | PASS |
| `plate-contract-e3-fairground.png` | `exec-0c2f379d-b66b-4734-aaaa-4e4d55dce07c` | 0 | 1672x941 RGB | 0.227 | `b39eac2d73904b9252787208c7d4c2a8dec0ceec8c9f100e855a9293e21ccd7f` | PASS |

Native run directory: `019f77b7-a2bd-7a02-b3af-7b37af1e4113`.

## Measured and visual QA

- All seven are opaque 1672x941 sRGB PNGs with full-bleed image content at every edge and no frame.
- Aspect ratio is 1.77683:1, exactly matching all six supplied contract-plate anchors.
- Batch mean luminance spans 0.099-0.403, inside the six-anchor range of 0.078-0.525.
- OCR-assisted review produced only short linework false positives; the visual review found no readable word, letter, number, caption, sign, logo, or watermark.
- No realistic firearms, gore, or border treatment appears in any plate.

| Plate | Signature read |
|---|---|
| E2 Trestle | one immense rail trestle across a deep river gorge, ore cart and lantern reflections |
| E2 Pressure Garden | four rising growing terraces, three boiler beds, upper coal rows, migrating vent plumes, distant outhouse |
| E2 Incline | two clearly countable counterweighted platforms at different elevations, four cliff benches, engine and winch houses |
| E3 Blackout Ridge | off-map trunk crossing the ridge toward a hidden glow, exactly two capacitor-bank installations, no local generator |
| E3 Moth Season | dark central road, two flanking yards, brightest sacrificial shed, pale moth migration |
| E3 Canyon Works | lower sub-hall, dam channel, tram, mirrored pylon chains, paired upper galleries |
| E3 Fairground | dominant generating Ferris wheel, dry bowl, open midway, two rival pavilions |

No extraction, processing, or runtime integration was performed.

Independent card-scale review initially requested two targeted edits: separate the Incline's upper and lower platform reads, and clear the Moth Season shed silhouette from the swarm. The revised montage received a final **SHIP** verdict.

## Final prompt set

Every prompt included this exact sentence:

> Engraved sepia contract plate in the Gold Rush house style: warm frontier illustration, fine etched linework on parchment, full-bleed, no letters, no gore, no firearms.

Every prompt also required a 16:9 full-bleed landscape composition matching the anchors; zero text, letters, numbers, symbols, logos, signage, captions, watermarks, borders, realistic firearms, gore, or modern objects; and a palette inside the supplied anchors' parchment, sepia, ochre, rust, ink-blue, and restrained teal/amber range.

### E2 Trestle

One immense timber-and-iron rail trestle spans a deep river gorge, with twin defended approaches, a small ore cart, and warm lantern reflections far below. Emphasize the bridge silhouette and vertical drop.

### E2 Pressure Garden

Four broad geothermal growing terraces rise beyond one river band; three boiler beds occupy the lower terrace, coal rows crown the highest bed, and migrating steam vents visibly exhale. Include one tiny distant outhouse without text.

### E2 Incline

A sheer stepped cliff carries two parallel funicular lines with counterweighted timber platforms at different elevations. Four benches, a lower engine house, an upper winch house, and a narrow water band make the mountain read as a giant balance scale.

### E3 Blackout Ridge

One off-map copper trunk crosses a dark ridge from a distant unseen source glow. Exactly two capacitor-bank installations store amber-teal current on separate shelves; no generator is visible.

### E3 Moth Season

Two dim work yards flank one deliberately dark north-south corridor. A small sacrificial shed is the single brightest lamp and draws a pale illustrated moth migration; darkness reads as the safe road.

### E3 Canyon Works

A deep industrial gorge carries mirrored west/east chains of copper H-frame pylons and glowing spans from a lower Dynamo Sub-Hall, across a dam channel and tram line, to paired upper cliff galleries.

### E3 Fairground

A grand generating Ferris wheel dominates a dry shallow bowl. Two rival pavilions balance west and east across an open south midway with small escorted festival groups; the wheel remains the uncontested landmark and light source.

### Targeted edit: E2 Incline

Edit only the funicular mechanism so two counterweighted platform cars remain clearly countable at card-thumbnail size, one low and one high. Preserve the exact framing, four benches, engine house, winch house, river, palette, lighting, terrain, and all other elements.

### Targeted edit: E3 Moth Season

Edit only the bright decoy area: enlarge the timber shed, give it a crisp pitched roof, visible plank walls and glowing doorway, and pull the nearest moths away from its edges while preserving the dark corridor, flanking yards, migration, palette, and all other elements.
