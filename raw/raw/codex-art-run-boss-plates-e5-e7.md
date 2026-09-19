---
source: codex
project: Gold Rush
date: 2026-07-15
type: reference
---

# E5-E7 component boss plates

## Result

Native Codex `image_gen` only. No Higgsfield still-image model was used. All three plates use the E2/E3 boss format: one intact presentation above and three separated damage studies below. The canonical era boss plate supplied subject continuity; the matching `kit-era-N.png` supplied palette/material conditioning; `plate-e2-boss-component.png` supplied layout conditioning.

| Plate | Native job | Retakes | Final size / mode | Exact `#ff00ff` | SHA-256 | Verdict |
|---|---|---:|---|---:|---|---|
| `plate-e5-boss-dredge-queen.png` | `exec-ba5131e7-5ac0-4c99-a774-192ef9d0ff94` | 0 | 1672x941 RGB | 0 | `1599b831c65bc74b3e8811ab614a9c5020e210021c246fd8b1ed5f458192ecbb` | PASS |
| `plate-e6-boss-homemaker-9000.png` | `exec-a19ab518-34cc-41b6-a477-71a26b894de5` | 0 | 1672x941 RGB | 0 | `c7e83389a41b04ca742691fa3d1b40b11e46f39d13074f19185f1c3fc4a2b1d1` | PASS |
| `plate-e7-boss-the-echo.png` | `exec-b5987ed2-3aca-43fc-ac8f-624aa0caf2f7` | 1 | 1672x941 RGB | 0 | `3a5205953303656b39b1f44c874f3715fd5a03ea9958a6d46f10127645685542` | PASS |

Native run directory: `019f6592-72ad-7110-9f50-5ed0cebe8cec`. E6 arrived at 1671x941 and was normalized by one horizontal pixel to 1672x941; no compositional edit was made. E7 take 1 preserved the correct material treatment but used an oblique base view, so take 2 replaced it with the required strict lateral elevation.

## Visual and canon QA

| Plate | Intact read | Separated lower states | Era conditioning | Canon check |
|---|---|---|---|---|
| E5 Dredge-Queen | strict port-side barge; claw dominates; twin paddles and open hold remain discrete | buckled claw / shattered paddle assembly / ruptured loot hold | blue-green Deepwater accents, dark iron, brass, teal instruments | no visible text, firearms, gore, people, creatures, or flames |
| E6 Homemaker-9000 | strict side elevation; VAC, RACK, and CORE dominate the domestic automaton silhouette | torn vacuum / sprung toast rack / slumped fading core and chair | chrome and mint enamel, teal starstone, amber Combine glow | warm atomic comedy; no military weapon language, sickness, corrosion, gore, or visible text |
| E7 The Echo | strict lateral defense line with a close teal duplicate and concentric arcs | contour breakup / tube-relay flicker / hatch-step dissolution | walnut, honey-gold tubes, pervasive teal signal glow | material/mask studies for live-layout geometry; no invented fixed anatomy, people, firearms, gore, code glyphs, or visible text |

No processing, modeling, shader implementation, or runtime integration was performed.

## Final prompts

Every prompt included the exact style anchor:

> Antique frontier expedition ledger map … Style of a Wild-West survey map: fine sepia engraved linework and hatching, subtle aged-paper texture underneath, muted warm colors, illustrated — not photorealistic, not saturated.

### E5

Preserve the canonical Dredge-Queen flag-barge design. Upper 60%: one complete strict port-side elevation with the great forward salvage CLAW as first target, twin PADDLEWHEELS, central loot HOLD, wheelhouse, and blank tattered flag. Lower 40%: isolated buckled claw, shattered paddle assembly, and ruptured loot hold. Condition palette/materials on `kit-era-5.png`; condition layout on `plate-e2-boss-component.png`. No text, firearms, gore, people, creatures, fire, or cropped/overlapping studies.

### E6

Preserve the canonical house-sized Homemaker-9000 domestic automaton. Upper 60%: one strict side elevation with forward VAC, roof RACK, and polished circular CORE as separable zones; helper arms and wheeled feet remain secondary. Lower 40%: torn vacuum, sprung toast rack, and slumped fading core resting against a small chair. Condition palette/materials on `kit-era-6.png`; glow decay uses engraved hatch steps, never corrosion or sickness. No text, military weapons, gore, people, creatures, fire, horror, or cropped/overlapping studies.

### E7 final retake

Preserve the canonical Echo as a shimmering mirror-copy material for the player's live base, never a fixed character or robot. Upper 60%: one strict lateral side-elevation defense line—palisade, three frontier-tech rigs, central relay, cables, honey-gold tubes—with a close teal ghost duplicate and concentric signal arcs. Lower 40%: isolated contour-breakup, tube/relay-flicker, and hatch-step-dissolution mask studies applicable to arbitrary live-layout geometry. Condition palette/materials on `kit-era-7.png`; condition layout on `plate-e2-boss-component.png`. No text, code glyphs, people, faces, creatures, firearms, gore, fire, horror, black voids, or cropped/overlapping studies.
