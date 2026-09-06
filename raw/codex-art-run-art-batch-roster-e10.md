---
source: codex
project: Gold Rush
date: 2026-07-25
type: reference
---

# E10 Deep Sky enemy walk8 sheets

## Result

Native Codex `image_gen` only. No Higgsfield still-image model was used. The shipped `the_quiet` boss-system row was excluded. The canonical `plate-e10-enemy-static-motes.png` already covers Static Motes, so only the missing Unraveled Memory and Static Squall stills were generated.

| File | Native call | Final size | SHA-256 | Retakes | Verdict |
|---|---|---:|---|---:|---|
| `char-e10-static_mote-sheet-walk8.png` | `call_0308dKCzspvrlzsOeJ46Xwgv` | 280x170 RGB | `7a61f33a14ef52cf8448864d892393339ed4147ff7855a077b5d691053467256` | 0 | PASS |
| `char-e10-unraveled_machine-sheet-walk8.png` | `call_DhRHH9qf8DkWwAAGhIqK6ZCx` | 1120x680 RGB | `b52e7d15479dd75681dc66e0dd519cbd6097c0f7a65a8a3278e63a418c2fee0c` | 0 | PASS |
| `char-e10-static_squall-sheet-walk8.png` | `call_w0milU4C8kxMMkWNn0pmUi8u` | 2240x1360 RGB | `1d321a622d11b7f1946f7b5451f00ab5352645ddedbb9d23c8923f1e7b198d30` | 0 | PASS |
| `plate-e10-enemy-unraveled_machine.png` | `call_mIKxKdcy6OezTQRR3Ya2Bshh` | 1672x941 RGB | `522fae04772d5a7485cb2e3c5a46db71179005c761a1d59c59e8ac60670ea72b` | 0 | PASS |
| `plate-e10-enemy-static_squall.png` | `call_lwX92Ycxx8XNTuKcCq0UCnEu` | 1672x941 RGB | `adbf3656267f062ad47b8074526f1e747bea5e8e50b3f978dba719d69b2840d7` | 0 | PASS |

Native run directory: `019f9548-679b-7650-928b-90bf79bf7952`.

Each sheet is exactly 4 columns x 2 rows with the binding 280x340 bandit-cell proportion scaled to its roster band: Static Mote 70x85 cells (0.25x), Unraveled Memory 280x340 cells (1.00x representative source identity), and Static Squall 560x680 cells (2.00x screen-tall weather band). Frames 1-4 are top and 5-8 bottom. Centered bbox raw-sheet normalization corrected native canvas framing, then magenta-like background pixels were set to exact `#ff00ff`. No alpha extraction was performed.

## Measured self-QA

The right-facing bandit reference measures 292 px visible height in each 280x340 cell. Cell-band ratios are binding for later extraction; visible ratios report silhouette geometry honestly. The tiny mote is width-limited inside its 0.25x cells.

| Sheet | Grid / key purity | Frame visible heights (px) | Height ratio vs bandit | 25% silhouette | Distinct / not mirrored |
|---|---|---|---|---|---|
| Static Mote | exact 4x2; 70x85 cells; 77.714% exact key; zero near-magenta non-key pixels | 44, 37, 32, 27, 42, 41, 61, 28 | 0.25x cell band; 0.13x mean visible, width-limited | PASS | 8/8 unique hashes; minimum mirrored RMSE 0.189 |
| Unraveled Memory | exact 4x2; 280x340 cells; 72.897% exact key; zero near-magenta non-key pixels | 292, 291, 292, 291, 292, 291, 292, 292 | 1.00x cell band; 1.00x mean visible | PASS | 8/8 unique hashes; minimum mirrored RMSE 0.214 |
| Static Squall | exact 4x2; 560x680 cells; 73.015% exact key; zero near-magenta non-key pixels | 576, 591, 623, 651, 609, 608, 585, 579 | 2.00x cell band; 2.06x mean visible | PASS | 8/8 unique hashes; minimum mirrored RMSE 0.233 |

Full-size and 25% visual review found every sheet readable, all motion directed right, coherent identities, and no visible letters, numbers, watermarks, realistic firearms, gore, duplicate frames, or mirrored frames. The two stills are full-bleed warm Frontier Ledger scenes with no visually readable text, letters, numbers, watermarks, firearms, gore, horror, or magenta key.

## Final prompts

Every prompt included this exact anchor:

> Gold Rush house sprite: engraved-warm frontier illustration, clean silhouette at gameplay zoom, #ff00ff flat background, no letters, no gore.

All sheet prompts bound exactly eight independently drawn right-facing frames in a regular 4x2 grid, uniform `#ff00ff`, no gutters or labels, no letters/numbers/watermarks, no firearms or gore, and no duplicates or mirrors. `char-bandit-base-sheet-walk8.png` and `char-hero-sheet-walk4-a.png` supplied the sheet convention.

- Static Mote: tiny faceless un-inked parchment wisp with thin inverse-gold rim, sparse deep-ink clue, minute teal re-ink spark, and eight drift/orbit/re-ink phases; conditioned on `plate-e10-enemy-static-motes.png` and `plate-e10-boss-the-quiet.png`.
- Unraveled Memory: remembered E7 brass frontier automaton with its source chase silhouette intact, trailing edges half-un-inked to pale parchment, one amber memory lamp, one teal lens, and eight true walk phases; conditioned on `char-e7-rogue_automaton-sheet-walk8.png` and the Quiet plate.
- Static Squall: non-creature screen-tall torn-paper weather front moving right, sparse deep-ink stipple, partial concentric desaturation rings, and a warm ochre/teal re-ink wake across eight front-edge states; conditioned on the Static Motes and Quiet plates.
- Unraveled Memory plate: one right-facing remembered brass automaton crossing an Ark deck, trailing machine edges fading into warm parchment absence while a blank portrait re-inks behind it.
- Static Squall plate: a tall torn-paper weather front crossing an Ark garden deck, with warm color and engraved detail returning behind it; blank resonator faces only.

No extraction, alpha processing, runtime wiring, boss art, duplicate Static Mote plate, or source/spec changes were performed.
