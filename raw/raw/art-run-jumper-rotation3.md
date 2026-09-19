---
source: codex
project: Gold Rush
date: 2026-08-23
type: digest
---

# Claim-jumper rotation3 — lawful-size retake stopped at QA

Tool: native Codex `image_gen` only. No Higgsfield, extraction, compositing, resizing, frames JSON, contract, or runtime work.

Outcome: **FAILED AFTER THE INITIAL TAKE + 2 ALLOWED RETAKES; NO SHEET HANDED FORWARD.** `assets/raw/char-jumper-sheet-rotation3.png` was deliberately not created because no take met the ruled ≥460px-per-cell source-height law, exact-key purity law, and cell-boundary containment law together.

Native retained outputs: `/Users/robin/.codex/generated_images/01a02f20-30ac-7233-b151-6a4130db7294/`.

References inspected and supplied to generation:

- identity portrait: `assets/raw/enemy-claim-jumper.png`
- ACTIVE identity/palette/silhouette: `assets/raw/char-jumper-sheet-walk8.png`
- accepted batch-005R3 composition/order: `assets/raw/char-jumper-sheet-rotation.png`

Prompt contract: exact 4x3 layout and accepted 12-cell order; same dusty hat, face bandana, rust-red poncho-cone, brown trousers/boots and empty gloved hands; antique frontier-ledger engraving; no mirrors, weapons, text, logos, gore, shadows, floor, or extra figures; exact opaque `#ff00ff`; every figure ≥460px tall and contained within its raw cell.

## Takes

1. `exec-8e8ed371-3039-4e8e-b591-cbdd657dd90c.png` — rejected. The tool ignored the requested 1536px square and returned 1254x1254 (313x418 grid cells), making the ≥460px law impossible. Figure heights were 291–363px; projected contract-frame coverage was 56.8–70.9%.
2. `exec-3932e887-722e-44f9-84b5-b5f5f34493df.png` — rejected. The portrait source size landed correctly at 1024x1536 (256x512 cells), but figures measured 333–459px and seven cells touched at least one boundary.
3. `exec-9d6251d6-39b4-46b9-9ad7-ea2cc17de70e.png` — rejected final retake. The 1024x1536 source size held, but figures measured 354–460px; only 2 of 12 reached 460px, 10 of 12 touched a cell boundary, and the background remained generated near-magenta rather than exact-key pure. Row-1 diagonal poses also read too frontally to certify the accepted direction map.

## Final-take measured QA

Method: split the 1024x1536 PNG into exact 256x512 cells. Treat the magenta key family as `R>=200, B>=200, G<=80, |R-B|<=80`; the figure bbox is the remaining-pixel extent inside each cell. A boundary verdict is failed when the bbox reaches any cell edge. At extractor scale ≤1, projected 512px output height equals the raw bbox height.

| Cell | Required pose | Figure bbox | Raw cell % | Projected 512 % | Registration | ≥460px |
|---|---|---:|---:|---:|---|---|
| r0c0 | toward viewer, left foot | 220x444px | 86.7% | 86.7% | touches bottom | fail |
| r0c1 | toward viewer, right foot | 212x446px | 87.1% | 87.1% | touches bottom | fail |
| r0c2 | south-east, left foot | 206x446px | 87.1% | 87.1% | touches bottom | fail |
| r0c3 | south-east, right foot | 215x445px | 86.9% | 86.9% | touches bottom | fail |
| r1c0 | side screen-right, left foot | 205x460px | 89.8% | 89.8% | touches top | pass height / fail registration |
| r1c1 | side screen-right, right foot | 199x460px | 89.8% | 89.8% | touches top | pass height / fail registration |
| r1c2 | side screen-left, left foot | 222x457px | 89.3% | 89.3% | touches top | fail |
| r1c3 | side screen-left, right foot | 224x458px | 89.5% | 89.5% | touches top | fail |
| r2c0 | north-east away, left foot | 201x430px | 84.0% | 84.0% | clear | fail height |
| r2c1 | north-east away, right foot | 208x430px | 84.0% | 84.0% | clear | fail height |
| r2c2 | straight away, left foot | 240x431px | 84.2% | 84.2% | touches right | fail |
| r2c3 | crouch idle toward viewer | 225x354px | 69.1% | 69.1% | touches left | fail |

Final min/max: **354 / 460px**. Height law: **2/12 pass**. Fully passing height + registration: **0/12**.

Key purity: 1 exact `#ff00ff` pixel; **1,022,058 near-magenta non-exact pixels**; required near-magenta non-exact count is zero, so key purity fails. The PNG is opaque.

Identity QA: silhouette and palette remain recognizably the same ACTIVE walk8 jumper — dusty hat, masked face, rust poncho-cone, brown workwear, empty gloved hands. Canon passes: no firearm, text, logo, gore, or extra character. Grid QA fails for the boundary contacts listed above. The source remains only in native generation retention and must not be extracted or wired.

