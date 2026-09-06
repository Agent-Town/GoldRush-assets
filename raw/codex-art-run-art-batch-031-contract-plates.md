---
source: codex
project: Gold Rush
date: 2026-07-20
type: reference
---

# Art batch 031 — E10 contract plates

## Result

Native Codex `image_gen` only. No Higgsfield still-image model was used. Four raw full-bleed contract-board plates landed at the exact requested paths in `assets/raw/`; no extraction, resizing, image processing, runtime integration, or batch 032 work was performed.

Every generation used `plate-contract-e2-trestle.png` and `plate-contract-e5-regatta.png` as strict style masters. Ember Shore and Archive World additionally used their run-camera and mounted-landmark evidence. Last Claim used the Ark plaza, ten-era dressing, and functional-prop renders. River used the adopted Claim plate and mounted Claim render.

Native run directory: `019f7dcc-0eb5-7fa1-bf3b-16083f0ac551`.

| Plate | Native job | Retakes | Size / mode | Mean luminance | Min edge SD | SHA-256 |
|---|---|---:|---|---:|---:|---|
| `plate-contract-e10-ember-shore.png` | `exec-20f02faa-0e85-4cb1-bd00-4110cc1cc1fe` | 0 | 1672x941 RGB | 0.254 | 0.059 | `4fbce36f8e649ac19f2c7316862d586b7f141f5a6cb6b94d96a4a7625650a554` |
| `plate-contract-e10-archive-world.png` | `exec-30473efe-337b-4798-b42c-21dc11c18bb1` | 0 | 1672x941 RGB | 0.171 | 0.039 | `74ecbdf82e92a04402802349d83ba0760c8fd8dcc73258e7fe6876ba1333578a` |
| `plate-contract-e10-last-claim.png` | `exec-3d07c8ee-d745-423a-a47d-967c8c2d73fd` | 0 | 1672x941 RGB | 0.154 | 0.022 | `19216a69e7fb8ebb79b9f5a3e61d14e8fa41798acc4f70dfe4c0706aeeb7c0f2` |
| `plate-contract-e10-river.png` | `exec-8d60ed32-8ac7-463e-8eed-42386778e874` | 0 | 1672x941 RGB | 0.330 | 0.080 | `8e87399729c5aaca4ae52d016d0eb99f5b42c5bc0aed461dc8e6623d48914706` |

## Measured and visual QA

- All four are opaque RGB PNGs with non-uniform content reaching every edge; minimum 16-pixel edge-strip standard deviation spans 0.022-0.080, so no border or inset is present.
- All four are 1672x941 at the exact 1.77683 anchor aspect.
- Mean luminance spans 0.154-0.330, inside the six adopted-anchor range measured this run at 0.131-0.385.
- Tesseract returned empty output for all four. Full-resolution visual review found no readable text, letters, numbers, captions, signs, logos, coded writing, or watermarks.
- Visual review found no realistic firearms, gore, border treatment, or photorealism.

| Plate | Signature read | Verdict |
|---|---|---|
| E10 Ember Shore | exactly three recessed cooling rifts, southern warm-vent altar, ancient cooled titan machine on the far shelf, small preserve hardware | PASS |
| E10 Archive World | paired ruined stack wings, empty central missing-memory cut, three light holds, deep warning shelf | PASS |
| E10 Last Claim | circular Ark deck, ten distinct lineage stations, stern-side Static fade, bow lantern/pan-song/portrait preserves | PASS |
| E10 River | first-claim mountain valley at dawn, broad continuing river, pale center ford, exactly one pan in the foreground shallows | PASS |

## Prompt set

Every generation included this exact sentence:

> Gold Rush engraved contract plate, the adopted board style (E2-E5 batch law): fine sepia-ink etched linework on warm parchment, restrained monochrome-warm palette with subtle golden-light accents, full-bleed 1672x941, no letters, no gore.

- **Ember Shore:** dry black volcanic shore under an old alien sky; exactly three recessed cooling lava-vein rifts; the southern last-warm-vent altar; colossal cooled titan machine on the northern/eastern shelf; small cooling-marker, bridge-school, and preserve-rack hardware; elevated oblique edge-to-edge composition.
- **Archive World:** broad south entry into opposed west/east ruined stack wings; narrow central missing-sentence cut left empty; far warning shelf; three warm light holds re-inking small islands of shelves; collapsed stacks and a conspicuously bare deep shelf; elevated oblique edge-to-edge composition.
- **Last Claim:** circular brass-and-timber Ark deck in space; clear stern-to-bow route; ten distinct unlabeled era lineage stations; bow preserves of one lantern, one pan-song mechanism, and one blank portrait; Static rendered as loss of ink at the stern; whole-deck oblique composition.
- **River:** first frontier river claim at dawn; broad river continuing out both sides; pale center ford; low gravel banks and familiar valley ridges; exactly one old pan in the foreground shallows with restrained gold flecks; no people, enemies, waves, buildings, machinery, tents, stakes, sluices, signs, or extra tools.

Every prompt also forbade visible text, letters, numbers, runes, glyphs, pictograms, symbol-like writing, signage, captions, logos, watermarks, borders, photorealism, realistic firearms, and gore.
