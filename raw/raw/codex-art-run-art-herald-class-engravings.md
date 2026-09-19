---
source: codex
project: Gold Rush
date: 2026-07-30
type: art-run
---

# art-herald-class-engravings — reusable Herald class set

## Result

Native Codex `image_gen` only; no Higgsfield, CLI image model, extraction, resizing, runtime wiring, source code, specs, or existing assets were changed. Exactly eight first-take full-bleed RGB engravings landed at:

- `assets/raw/gazette-class-board.png`
- `assets/raw/gazette-class-trail.png`
- `assets/raw/gazette-class-river.png`
- `assets/raw/gazette-class-science.png`
- `assets/raw/gazette-class-ledger.png`
- `assets/raw/gazette-class-threat.png`
- `assets/raw/gazette-class-growth.png`
- `assets/raw/gazette-class-ceremony.png`

Native run directory: `019fb103-5aac-7b02-83e6-3845851b9213`.

Every prompt included this task anchor verbatim:

> engraved frontier newspaper illustration, warm sepia ink on parchment, fine crosshatching, the Gold Rush plate style — never photoreal, never gory, no letters or numerals in the image.

Common prompt constraints required a full-bleed wide landscape composition with no border, frame, or caption area; one bold focal silhouette readable at 320px wide; parchment cream, warm sepia, walnut, muted ochre, aged brass, and only restrained agent-tech teal; blank paper surfaces or non-alphanumeric pictograms only; and no writing, watermark, logo, realistic firearm, gore, injury, caricature, split panel, collage, or photorealism.

## Measured self-QA

All eight files are opaque 1536x1024 RGB PNGs. The exact 320px-wide contact pass reads, left to right: board, trail, river, science; ledger, threat, growth, ceremony. Each focal subject remains immediate at that size.

Tesseract is over-sensitive to dense engraved hatching and returned scattered line-fragment false positives. Full-resolution visual inspection of every board, page, chart, tag, stamp, flag, facade, and horizon found no credible visible letters or numerals. The intentional marks are blank surfaces or object/terrain pictograms.

| File | Mean luminance | Mean HSL saturation | Edge coverage | SHA-256 | 320px verdict |
|---|---:|---:|---:|---|---|
| `gazette-class-board.png` | 0.411 | 0.515 | 0.403 | `ea582244ff5ea76b1da27cf978ebabfe562c99fb361fe6c9e57c0f71372fc5fd` | PASS — pinned blank claims and terrain pictograms dominate |
| `gazette-class-trail.png` | 0.381 | 0.462 | 0.415 | `3021b50ffe7ddce2c121f7d5aaa0e897c260b37e74150b3e544da5ba923d5edd` | PASS — switchback route and wagon read immediately |
| `gazette-class-river.png` | 0.418 | 0.525 | 0.431 | `9570f3b8754f50da2303a20e681c578838d1cea8d80957062cbdd5940337004b` | PASS — river bend and near-bank sluice stay distinct |
| `gazette-class-science.png` | 0.392 | 0.468 | 0.410 | `21ed58f3c8c25b1f77e88f816c51f94b87cb65831ca94dd397f638a1f83afcc8` | PASS — blank pictogram chart and instruments read as schoolhouse science |
| `gazette-class-ledger.png` | 0.461 | 0.603 | 0.422 | `deea582a7cf2648eaf2ae15152c92958694611e7b4db247018ba637b6fd4e77d` | PASS — blank open ledger, ink pot, and pictogram seal dominate |
| `gazette-class-threat.png` | 0.283 | 0.529 | 0.421 | `368302af547e74d78422b8769f23af005a7763d01ec261b3f192e5fe3a48792c` | PASS — ridge-scale dust cloud reads ominous without violence |
| `gazette-class-growth.png` | 0.493 | 0.500 | 0.429 | `fcda307abb15f3c2235490e64f5bd556aae9afa8a2a48a3e2fdf99f06057ad69` | PASS — raised timber frame, ropes, neighbors, and brass agent read as cooperative construction |
| `gazette-class-ceremony.png` | 0.347 | 0.366 | 0.394 | `95ad125a35bb0b61dc30157ad07d3ac9beb8eff24f1ff58851083c1092935a0b` | PASS — lantern arcs and open plaza gathering read as ceremony |

Across the set:

- Anchor match: PASS — all eight use warm sepia/parchment engraved crosshatching and remain illustrated.
- No letters/numerals: PASS by full-resolution visual review; OCR hits are hatch-line false positives.
- Reads at 320px wide: PASS for all eight in one exact-size contact review.
- Plate palette: PASS — luminance 0.283-0.493 and HSL saturation 0.366-0.603; no saturated modern-color outlier.
- Canon: PASS — no realistic firearms, gore, injury, hostile depiction of a people, or grim violence.
- Retakes: 0.

## Prompt set

1. **Board / claims:** sturdy tavern claim board with pinned blank claim sheets, blank map scraps, crossed cord, wax seals, simple terrain pictograms, lantern, and brass tack cup; no people.
2. **Trail / terrain:** strong S-shaped switchback trail climbing into rugged wooded hills, one small pack wagon, and simple cairns; no people.
3. **River / water:** broad river bend, compact near-bank wooden sluice, gold pan, and pebbled shallows; no people.
4. **Schoolhouse / science:** warm one-room schoolhouse centered on a blank pictogram chart of river, sun, rock layers, and stars, with compass, lens, calipers, specimen jars, and one restrained teal agent-tech indicator; no people.
5. **Ledger / records:** close three-quarter tabletop still life of a blank open ledger, ink pot, quill, brass pan-pictogram seal, wax, and tied claim tokens; no hands or people.
6. **Boss / threat:** ominous distant dust cloud above a dark ridge at dusk, tiny frontier-tech warning beacon, and empty foreground trail; no attacker, weapon, harm, gore, or people.
7. **Town growth:** neighbors cooperatively raising a timber building frame with ropes, braces, and pulley while a friendly round brass agent steadies a beam; safe and celebratory.
8. **Ceremony:** lantern arcs across a frontier plaza at dusk, warm gathering silhouettes, a small brass agent, blank fabric bunting, and a glowing civic ritual atmosphere; no stage text or signage.

## Firewall

Generation and raw save only. The `heraldReader` class-map is a separate small lane slice and remains untouched.
