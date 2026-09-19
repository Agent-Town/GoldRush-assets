---
source: codex
project: Gold Rush
date: 2026-07-20
type: reference
---

# E9 Red Fields enemy walk8 sheets

## Result

Native Codex `image_gen` only. No Higgsfield still-image model was used. The shipped `old_digger` boss-system row was excluded. Existing `plate-e9-enemy-dust-devil.png` and `plate-e9-enemy-claim-crow.png` cover the Dust Devil and Claim-Jump Prospect Drone, so only the missing Faithful Terraformer still was generated.

| File | Native job | Final size | SHA-256 | Retakes | Verdict |
|---|---|---:|---|---:|---|
| `char-e9-dust_devil-sheet-walk8.png` | `exec-79060774-63fd-446b-b68f-3fa3cdd27ca8` | 1792x1088 RGB | `6b6a5fd39c0046b6f8d84cfde3e593cad262a54324270d253ccf8b2e7aeae793` | 0 | PASS |
| `char-e9-feral_terraformer-sheet-walk8.png` | `exec-3389e9c3-5942-4dec-94c0-5562d0fea744` | 2016x1224 RGB | `c6fc51009ef9d49121c75da62d24bc9bfb7a7528646b4e0a910e28ea6e151402` | 1 | PASS |
| `char-e9-claim_jump_prospect_drone-sheet-walk8.png` | `exec-ac95b3d7-559f-4204-ac63-9521d20bc22b` | 504x306 RGB | `f7ef0ffe6f215c277ae59d10bfc3368308a57e2218be5f33a96b295f68d33c03` | 0 | PASS |
| `plate-e9-enemy-feral_terraformer.png` | `exec-a21e7e40-0e1d-4bc4-ae52-7e3e69224f44` | 1672x941 RGB | `767ec3d06a81e69d1163642661b979aadf22828b69405c437ff29610ff792ef4` | 0 | PASS |

Native run directory: `019f7fda-94ec-72d1-bb0e-81bb301e967b`.

Each sheet is exactly 4 columns x 2 rows with the binding 280x340 bandit-cell proportion scaled by its roster height band: Dust Devil 448x544 cells (1.60x), Terraformer 504x612 (1.80x), and Prospect Drone 126x153 (0.45x). Frames 1-4 are top and 5-8 bottom. Near-magenta pixels were normalized to exact `#ff00ff`; no alpha extraction was performed. The Terraformer used one targeted retake because the first take was too low and wide; the accepted take raises the survey gantry for a stronger gameplay silhouette.

## Measured self-QA

The right-facing bandit reference measures 292 px visible height in each 280x340 cell. The exact cell-band ratio is binding for extraction; visible ratios also report silhouette geometry honestly. Wide machines and spread wings are width-limited inside their cells.

| Sheet | Grid / key purity | Frame visible heights (px) | Height ratio vs bandit | 25% silhouette | Distinct / not mirrored |
|---|---|---|---|---|---|
| Dust Devil | exact 4x2; 448x544 cells; zero near-magenta non-key pixels | 430, 425, 423, 424, 402, 407, 408, 405 | 1.60x cell band; 1.42x mean visible | PASS | 8/8 unique hashes; minimum mirrored RMSE 0.198 |
| Faithful Terraformer | exact 4x2; 504x612 cells; zero near-magenta non-key pixels | 390, 389, 388, 387, 387, 385, 387, 388 | 1.80x cell band; 1.33x mean visible, width-limited | PASS | 8/8 unique hashes; minimum mirrored RMSE 0.286 |
| Claim-Jump Prospect Drone | exact 4x2; 126x153 cells; zero near-magenta non-key pixels | 108, 91, 98, 83, 102, 83, 98, 96 | 0.45x cell band; 0.33x mean visible, wing-width-limited | PASS | 8/8 unique hashes; minimum mirrored RMSE 0.220 |

Visual review at full size and 25% found every frame facing right, coherent identities, distinct motion phases, blank claim tags, readable silhouettes, and no visible letters, numbers, watermarks, realistic firearms, gore, duplicate frames, or mirrored frames. The Terraformer still is full-bleed, warm, mechanical rather than creature-like, and carries no text or gold seams.

## Final prompts

Every prompt included this exact anchor:

> Gold Rush house sprite: engraved-warm frontier illustration, clean silhouette at gameplay zoom, #ff00ff flat background, no letters, no gore.

All sheet prompts bound exactly eight independently drawn right-facing frames in a regular 4x2 grid, uniform `#ff00ff`, no gutters or labels, no letters/numbers/watermarks, no firearms or gore, and no duplicates or mirrors. `char-bandit-base-sheet-walk8.png`, `char-hero-sheet-walk4-a.png`, and the E7 walk8 output supplied the sheet convention.

- Dust Devil: faceless rust-red hatch spiral with parchment gaps and intact loose props, animated by lean, compression, foot contact, and prop orbit.
- Faithful Terraformer: old Combine canal craft with cutting chassis, rugged wheels, raised survey gantry, amber work lamp, and restrained teal correction state. The accepted retake requested a narrower side elevation and higher gantry.
- Claim-Jump Prospect Drone: small brass/regolith crow-like survey drone with one teal sensor and blank folding claim tag, animated by wing stroke, body bob, claw motion, and tag flutter.
- Terraformer plate: one house-sized old canal-correction craft in a dead red basin, full-bleed Frontier Ledger illustration with domes and canals behind it.

No extraction, alpha processing, runtime wiring, boss art, or duplicate still generation was performed.
