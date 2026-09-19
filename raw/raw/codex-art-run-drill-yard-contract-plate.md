---
source: codex
project: Gold Rush
date: 2026-08-01
type: art-run
---

# Drill Yard contract plate

## Result

Native Codex `image_gen` only. Final plate: `plate-contract-e1-drill-yard.png`.

- Native run directory: `019fbc25-bbd6-7461-8a7d-49ef9e4f097c`
- First take: `exec-80c37766-8013-43ba-bf65-4c0ff42f9395`
- Final retake: `exec-7994d411-4231-4516-894d-0a275e5dcece`
- Retakes: 1. The first take was rejected because distant storefront panels and an assay-table paper contained letter-like marks. The retake removed those surfaces while preserving the safe-yard composition.
- Final SHA-256: `6647dda92cb98d15bec88b697c4bfc554a91ff68089e2fb3fff8ceaea335954a`

## Pre-flight

Both candidate files were absent before generation (`ls` exit 1):

```text
ls: assets/raw/plate-contract-drill-yard.png: No such file or directory
ls: assets/raw/plate-contract-e1-drill-yard.png: No such file or directory
```

`assets/contracts/epoch-1-frontier/contracts.json` still contained `"id": "e1-drill-yard"` at line 34.

## Measured self-QA

| Check | Result | Verdict |
|---|---:|---|
| Dimensions | 1672x941 | PASS |
| Mode | sRGB, opaque RGB | PASS |
| Aspect ratio | 1.77683316:1 | PASS |
| Delta from 1.77683:1 | 0.000178% | PASS (<=0.06%) |
| Mean luminance | 0.455 | PASS (inside 0.078-0.525) |
| Exact `#ff00ff` pixels | 0 | PASS |
| OCR | blank | PASS |
| 240px distinct zones | straw-target line; rolling log rigs; bell post; assay tent and top-up lever | PASS (4) |

## Canon QA

- PASS — no firearms or other weapons.
- PASS — targets are unmistakable bundled straw on broad freestanding timber bases and rolling log mechanisms; no people, victims, bodies, or hanging figures.
- PASS — warm illustrated practice-yard framing; no gore, horror, or battle read.
- PASS — no visible letters, numbers, signage, watermarks, logos, signatures, glyphs, or pseudo-writing; visual inspection and blank OCR agree.
- PASS — full-bleed image with no decorative map border, frame, or corner marks.

## Prompt 1 — rejected first take

```text
Use case: stylized-concept
Asset type: Gold Rush contract catalog board-card plate
Primary request: Create one antique engraved illustration teasing THE DRILL YARD, a safe practice ground at the edge of a warm frontier town where nothing is at stake.
Scene/backdrop: An orderly fenced dirt yard in a quiet frontier valley. Show three immediately distinct zones: a neat practice line of unmistakable bundled-straw targets on sturdy freestanding wooden bases; low rolling timber-log dummies built as obvious wooden training apparatus; a drill bell hanging from its own simple post; and a small canvas assay tent with a prominent county top-up lever beside practical brass assay equipment. No people or living figures anywhere.
Subject clarity: This must read as a friendly outdoor gym and training yard, not a battle, execution, punishment, or danger scene. Straw targets must visibly be tied bundles of straw mounted on broad freestanding wooden frames, plainly inanimate practice equipment, never realistic people, bodies, victims, effigies, scarecrows, or hanged figures. Rolling targets must plainly be logs and timber mechanisms.
Style/medium: Antique frontier expedition ledger map ... Style of a Wild-West survey map: fine sepia engraved linework and hatching, subtle aged-paper texture underneath, muted warm colors, illustrated - not photorealistic, not saturated.
Composition/framing: full-bleed 16:9 landscape composition, exact intended canvas 1672×941, slight elevated oblique survey-map viewpoint, scene fills every edge, no inset panel, no decorative map border, no frame, no corner marks. Keep the target line, bell post, and assay tent visually separate and legible at 240px-wide card scale.
Lighting/mood: warm, calm late-afternoon light; welcoming, orderly, safe, low-stakes.
Color palette: muted warm sepia, ochre, dusty terracotta and restrained brass with only subtle desaturated teal accents.
Constraints: opaque sRGB image; illustrated and canon-safe; no humans, no animals, no victims, no combat, no gore, no horror, no firearms, no guns, no bows, no blades, no weapons of any kind; no visible letters, numbers, words, signage, labels, logos, watermarks, signatures, glyphs, border ornaments, or corner decorations; do not use exact #ff00ff.
```

## Prompt 2 — accepted retake

```text
Use case: precise-object-edit
Asset type: Gold Rush contract catalog board-card plate
Primary request: Retake the previously generated Drill Yard plate to eliminate every letter-like, number-like, sign-like, paper-like, logo-like, or watermark-like mark while preserving the successful safe practice-yard composition and engraved style.
Change only these problem areas: remove the distant town storefront façades and replace them with an unobtrusive open valley edge plus a few plain roof-only sheds seen from above, with absolutely no signboards, façade panels, posters, writing, symbols, marks, or pseudo-text. Remove the sheet of paper from the assay table entirely. Ensure every remaining object surface is blank except for natural engraved material hatching.
Preserve: the orderly fenced dirt yard; unmistakable bundled-straw practice targets on broad freestanding wooden bases; rolling timber-log training mechanisms; drill bell on its simple post; canvas assay tent; prominent county top-up lever; brass assay equipment; warm welcoming low-stakes gym mood; no people.
Style/medium: Antique frontier expedition ledger map ... Style of a Wild-West survey map: fine sepia engraved linework and hatching, subtle aged-paper texture underneath, muted warm colors, illustrated - not photorealistic, not saturated.
Composition/framing: preserve the full-bleed 16:9 landscape, intended exact canvas 1672×941, slight elevated oblique survey-map viewpoint, with target line, bell post, and assay tent separate and legible at 240px wide. No inset, decorative map border, frame, corner marks, or blank margins.
Constraints: opaque sRGB; no humans, no animals, no victims, no combat, no gore, no horror, no firearms, no guns, no bows, no blades, no weapons; absolutely no visible letters, numbers, words, signage, labels, logos, watermarks, signatures, glyphs, paper, posters, border ornaments, corner decorations, or pseudo-writing anywhere; do not use exact #ff00ff.
```

No extraction, processing, runtime integration, source edit, e2e edit, ledger edit, or commit was performed.
