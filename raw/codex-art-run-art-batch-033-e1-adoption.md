---
source: codex
project: Gold Rush
date: 2026-07-20
type: art-run
---

# art-batch-033 — E1 contract-plate adoption

## Result

Native Codex `image_gen` only; no Higgsfield or CLI image model. Each redraw used its original E1 plate as the subject/composition reference and `plate-contract-e2-trestle.png` plus `plate-contract-e5-regatta.png` as the adopted style masters. All six were accepted on the first native render. Dry Gulch and Hill Mine returned at 1671x941 and received only the task-required one-pixel width normalization to 1672x941.

Every prompt included this sentence verbatim:

> Gold Rush engraved contract plate, the adopted board style (E2-E5 batch law): fine sepia-ink etched linework on warm parchment, restrained monochrome-warm palette with subtle golden-light accents, full-bleed 1672x941, no letters, no gore.

Native run directory: `019f7d73-8d2e-7a03-92ef-1b27dcf30e1b`.

| Plate | Native job | Size | Mean luminance | Edge SD | SHA-256 | Subject/signature kept | Verdict |
|---|---|---:|---:|---:|---|---|---|
| The Claim | `exec-aceeffb5-5a4b-4411-8182-36ca9fc4d90b` | 1672x941 | 0.280 | 0.057 | `2ba047a4f5bc62451ea04e94d54046a913702aed593535103df40365658b1aff` | river bend, brass pan, teal-tied fresh stake, sluice timber, first camp | PASS |
| Dry Gulch | `exec-6cde54ca-1f6f-4f60-a505-b35e9da3c585` | 1672x941 | 0.385 | 0.117 | `b2ee4b5c703d71d950f2d8a9759eeb5ad2f2b63b208188460a2841461831912b` | branching dry washes converge on exactly one green spring | PASS |
| Night Shift | `exec-aa2b1f53-f086-47ca-bb02-5170ca9de7e5` | 1672x941 | 0.131 | 0.099 | `7eafb6e7fc0601724c9a47ec30d42e84d143718e5751483e4793cd1afe881c8b` | one warm lantern, receding cold lantern chain, pan and sluice | PASS |
| Twin Banks | `exec-6a50ac92-7dd7-45be-84d3-360768fb1d48` | 1672x941 | 0.325 | 0.102 | `d3a60e5e584494002cc121d73253b91d3805a3a63490434dfadd0b58a95c61b8` | braided river, paired fords, gravel bars, reeds, two buildable banks | PASS |
| Claim-Jumper Baron | `exec-e3724f74-6eb6-4d5d-9c2b-0cf52e0ecc32` | 1672x941 | 0.207 | 0.080 | `1d1796bd6ea547070b4b1b7ee9737040c7d50458f06c649657a53660329f9ecd` | crossed-pickaxes banner, north fort skyline, low sparks, off-screen coat-shadow | PASS |
| Hill Mine | `exec-d7164f17-c109-4eec-a45d-25b132322487` | 1672x941 | 0.278 | 0.094 | `732ba7177004d37be04e422661704cf78e9c79859bc0d93585ac69e83dfc2ce1` | terraced works, rail switchbacks, ore carts, headframe, steam wisps | PASS |

## Self-QA

- Dimensions: all six are exactly 1672x941; alpha is uniformly 255 (opaque).
- Full-bleed: image content reaches every edge; no frame, inset, or title area.
- Palette: all six use the adopted masters' warm parchment, sepia ink, restrained teal, oxblood where canonical, and small golden-light accents. Scene luminance varies with the subject's daylight/night contract.
- Subject: every original signature listed above remains readable at card scale.
- Text/canon: visual inspection and blank OCR output found no readable letters, numbers, captions, signs, logos, or watermarks; no realistic firearms or gore.
- Retakes: 0.

## Prompt set

All prompts classified Image 1 as the subject/composition reference and Images 2-3 as style-only masters, required edge-to-edge 16:9 art with no inset/border/title area, and repeated the exact style anchor above.

### The Claim

Repaint the same welcoming first claim: river bend sweeping from the distant valley, brass pan at the waterline, teal-tied fresh stake, waiting sluice timber, and humble camp. Do not add industry, crowds, weapons, signage, frames, or decorative borders.

### Dry Gulch

Repaint the vast dry mesa basin from a high overlook. Branching pale washes must converge on exactly one small green spring near the lower center. Do not introduce a river, settlement, people, animals, machines, borders, or multiple ponds.

### Night Shift

Repaint the rocky night work road with exactly one near lantern emitting warm light and a countable chain of cold unlit lanterns receding into darkness. Keep the foreground pan and modest sluice; add no people, creatures, buildings, fires, borders, or extra lit lanterns.

### Twin Banks

Repaint the braided river with two distinct shallow fords, gravel bars, reeds, and balanced buildable banks carrying claim stakes and timber preparations. Add no finished town, bridge, boats, people, borders, or extra waterways.

### Claim-Jumper Baron

Repaint the north fort-and-camp skyline from the ridge with the torn crossed-pickaxes banner, low horizon sparks, and enormous coat-shadow. Never show the Baron or any person; add no battle, weapons, gore, borders, or readable signage.

### Hill Mine

Repaint the terraced frontier steamworks with the climbing switchback railway dominant, ore carts at distinct elevations, high-bench headframe, timber trestles, pipes, compact works, and restrained steam wisps. Add no people, borders, signage, explosions, flames, weapons, or modern/futuristic machinery.

## Drain note

Retire the E1-specific art-registry framing (insets/keys) so all 41 cards render through the one default path.
