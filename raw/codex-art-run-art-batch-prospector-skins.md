---
source: codex
project: Gold Rush
date: 2026-07-26
type: art-run
---

# art-batch-prospector-skins — THE BOUNTY SKINS

## Result

Native Codex `image_gen` only; no Higgsfield, CLI image model, extraction, alpha processing, runtime integration, or edits to the shipped stock sheets.

Four source-preserving release sheets landed at the required paths:

- `assets/raw/char-prospector-complainant-sheet-hover4-a.png`
- `assets/raw/char-prospector-complainant-sheet-hover4-b.png`
- `assets/raw/char-prospector-gilded-sheet-hover4-a.png`
- `assets/raw/char-prospector-gilded-sheet-hover4-b.png`

Native run directory: `019f9d8e-2f03-73e2-9014-3dcc5a32fdb9`.

| File | Native call | Final size | Exact key | SHA-256 | Verdict |
|---|---|---:|---:|---|---|
| `char-prospector-complainant-sheet-hover4-a.png` | `call_WKDtOn2ihZSx2C3N77aHIRgf` | 1254x1254 RGB | 75.77% | `8160fe2a94882dd90ef8e327e6aa18ea527c9815f1fcf5f72112dff45e553fb8` | PASS |
| `char-prospector-complainant-sheet-hover4-b.png` | `call_PUoMhnR8E4pex9476Cad6fmY` | 1254x1254 RGB | 77.84% | `a9ad8049c47cb2784f67d3e2bc7ca9247ac891bcadf341e95ad188269e9b1637` | PASS after continuity retake |
| `char-prospector-gilded-sheet-hover4-a.png` | `call_FukDc0g82bVnv6Rp7cCsGwkg` | 1254x1254 RGB | 76.40% | `08af6936a427ac001fed61c39919b0a5d34826f7637b535e445b2ed73f1c3f49` | PASS |
| `char-prospector-gilded-sheet-hover4-b.png` | `call_p3fC7JsuogSLmXDyJgtPbOkE` | 1254x1254 RGB | 78.24% | `c0a4a0a375c2377d04c7599efb9cf7f3c2cf8cfa6d2876d6c5a86d1798e7be9f` | PASS |

The shipped `char-prospector-sheet-hover4-{a,b}.png` files were the binding edit targets. `plate-contract-the-claim.png` and `plate-contract-e2-trestle.png` supplied THE VOICE palette and engraving anchors. Native near-magenta fields were normalized to exact `#ff00ff`; no extraction or repainting was performed.

## Measured self-QA

Every sheet preserves the shipped square A/B convention: 4 columns x 4 rows, 16 cells, same 1254x1254 canvas, source order, facing, pose, pan, arms, hover flame, and padding. A retains the stock south/front through northeast half; B retains north/back through southwest. The fractional 313.5 px source division is unchanged.

| Sheet | Visible bbox band | Distinct frames | Exact mirrors | 25% verdict |
|---|---:|---:|---:|---|
| Stock A reference | 179-258w x 212-223h | 16/16 | 0 | PASS |
| Complainant A | 178-257w x 214-225h | 16/16 | 0 | PASS |
| Gilded A | 179-256w x 214-225h | 16/16 | 0 | PASS |
| Stock B reference | 118-240w x 199-218h | 16/16 | 0 | PASS |
| Complainant B | 118-238w x 199-218h | 16/16 | 0 | PASS |
| Gilded B | 118-239w x 199-218h | 16/16 | 0 | PASS |

A 5% near-key probe equals the exact-key count on all four outputs. At 25% size, normalized RMSE separates stock/complainant by 0.070 A and 0.073 B, stock/gilded by 0.050 A and 0.057 B, and complainant/gilded by 0.079 A and 0.079 B.

Full-size and 25% visual inspection found:

- The Complainant's Coat reads as a modest civic reward: broad clerk-teal ribbon, restrained rosette, and compact brown satchel with an abstract embossed seal.
- The Gilded Prospector reads as the top-three prize: selective matte gold-leaf panels, aged dark-brass borders, and a stronger starstone-teal dial, without neon flood or jewel-encrusted excess.
- Both skins remain the same round brass Prospector with miner lamp, articulated arms, pan, and hover base.
- No credible letters, numbers, logos, watermarks, realistic firearms, gore, extra characters, duplicated or mirrored cells, crops, or reordered frames are visible. Tesseract fragments were engraving-hatch false positives; visual inspection found no writing.
- Retakes: 2. An unprimed second-eye pass caught screen-fixed Complainant accessories in the first B take. The accepted B retake moves the satchel to viewer-right in the direct rear view and hides the rear rosette, keeping those pieces on one physical body side. A narrower second retake tried to reverse only the rear ribbon diagonal but produced mixed diagonals across the row, so it was discarded. The accepted ribbon remains a consistent screen-space sash, matching the shipped sheet's screen-space pan convention; this is a documented residual for attended review, not hidden as physical continuity. The same pass noted the stock pan's handedness and purple-edged cyan hover flame; both are binding traits already present in the shipped source sheets and were intentionally preserved rather than changed in this cosmetic-only slice.

Owner lineup: `assets/contact-sheets/char-prospector-three-coat-lineup.png` in stock, complainant, gilded order.

Six-sheet same-machine 25% evidence: `assets/contact-sheets/char-prospector-skins-sheets-25pct.png`, with A on the first row and B on the second.

## Final prompt set

Every native edit included this exact task anchor:

> Gold Rush house sprite: the brass Prospector agent re-dressed, engraved-warm frontier illustration, identical silhouette and grid, #ff00ff flat background, no letters, no gore.

Every call bound the source sheet as the exact edit target and required the exact 4x4 cell structure, character placement, pose, facing, pan, arms, hover flame, scale, padding, complete uncropped figures, and flat `#ff00ff` negative space. Every call prohibited mirrors, reordered/missing/added cells, words, letters, numbers, logos, watermarks, borders, captions, realistic firearms, gore, extra characters, scenery, floors, and cast shadows.

- **Complainant A/B:** re-dress only the stock Prospector with the same broad dark-teal diagonal clerk ribbon, restrained teal rosette where physically visible, and compact brown leather hip satchel with an abstract round embossed seal. Keep the reward modest, charming, and consistent through front, side, and back views. The accepted B correction explicitly binds the satchel and rosette to one physical body side and leaves the stock pan hand unchanged. A later ribbon-only correction was rejected because it mixed diagonal directions across one row.
- **Gilded A/B:** re-dress only the stock Prospector with selective matte gold leaf on broad hull and helmet panels, dark warm engraved seams, subtle age/patina, and a stronger starstone-teal dial. Keep joints, arms, pan, lower ring, vents, and panel borders in aged brass. Prohibit ribbon, satchel, neon cyan flood, jewels, crown, cape, and silhouette protrusions.

No processing, extraction, alpha work, runtime wiring, source code, specs, or existing shipped assets were touched.
