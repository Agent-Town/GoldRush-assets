---
source: codex
project: Gold Rush
date: 2026-07-26
type: art-run
---

# art-batch-tailor-extras — THE CLAIM-DAY SET

## Result

Native Codex `image_gen` only; no Higgsfield, CLI image model, fire-side extraction, final alpha asset, runtime integration, or edits to the shipped stock sheets.

Three release raws landed at the required paths:

- `/Users/robin/Claude/Projects/Gold Rush/worktrees/art/assets/raw/char-hero-claimday-sheet-walk4-a.png`
- `/Users/robin/Claude/Projects/Gold Rush/worktrees/art/assets/raw/char-hero-claimday-sheet-walk4-b.png`
- `/Users/robin/Claude/Projects/Gold Rush/worktrees/art/assets/raw/prop-tailor-sign.png`

Native run directory: `/Users/robin/.codex/generated_images/019f9da3-8e84-7f03-80b9-dccc5db2a139`.

| File | Native call | Final size | Exact key | SHA-256 | Verdict |
|---|---|---:|---:|---|---|
| `char-hero-claimday-sheet-walk4-a.png` | `call_D7B5O0fkwwDdX9NwAyfLHUyf` | 1700x1700 RGB | 82.28% | `25426d89b7f4ea63e2c9952ad732df08a2a29f6bb51e0649ac73fddff1e11a4f` | PASS |
| `char-hero-claimday-sheet-walk4-b.png` | `call_DvdvtSkz70YirTQcopIe9NBz` | 1700x1700 RGB | 83.10% | `10d377501db8dd963098caca1227e9059d8d3bcdf4572f7639a965ae3f06fc6f` | PASS |
| `prop-tailor-sign.png` | `call_ruyuBwChFHUpBK2tz6wyqgFk` + `call_jHdWxYUO4C9xdE1jXfUO6jhz` | 1254x1254 RGB | 49.20% | `266379879fccd891e568cb19b71cdb6d096f2c554ed96c27ce0d355eef679719` | PASS |

The shipped canonical `char-hero-sheet-walk4-{a,b}-f.png` files were the binding edit targets. The fresh Complainant's Coat sheets supplied only the reward-set clerk-teal accent and engraved-warm voice. `plate-contract-the-claim.png` supplied the sign's Frontier Ledger voice; `wagon-shop-day.png` supplied only practical hanging scale.

The native heroine edits supplied only their newly generated teal scarf/stitch pixels. The finals are source-dominant composites over the canonical 1700x1700 female A/B sheets: a teal-color mask plus a two-pixel outline allowance transfers the native accessories while every face, hand, hat, braid, coat, limb, boot, pan, satchel body, pose, scale, and original line remains byte-for-byte sourced from the binding stock art. This was the root fix for the first critique's native 1254-to-1700 softness and facial drift. No cell was extracted, reordered, mirrored, or alpha-keyed.

The final sign decomposes the hard small-scale read into two native outputs: a blank source-preserving banner and a large isolated threaded-needle donor. The donor was keyed, scaled, and centered on the blank cloth; a one-pixel alpha contraction removed the first composite's magenta edge. The accepted 128px review sees a sewing needle first.

## Measured self-QA

Both heroine sheets preserve the shipped 4x4 A/B convention exactly: 16 equal 425x425 cells; A rows south/front, southeast, east/right profile, northeast; B rows north/back, northwest, west/left profile, southwest. Every complete figure stays within its source cell.

| Sheet | Visible bbox band | Distinct frames | Exact mirrors | Exact key = 5%-near key | 25% stock-to-skin RMSE |
|---|---:|---:|---:|---:|---:|
| Claim-Day A | 155-217w x 341-367h | 16/16 | 0 | 82.28% = 82.28% | 0.01464 |
| Claim-Day B | 149-217w x 333-367h | 16/16 | 0 | 83.10% = 83.10% | 0.01099 |

The sign's exact non-key envelope is 1254x1180 at +0,+74 because the native raw retains a faint magenta-family falloff at the lower canvas corners; the illustrated banner itself occupies 970x1100 at +142,+74. Its exact-key and 5%-near-key counts both equal 49.20%.

Full-size, 25%, 2x-crop, OCR-assisted, and unprimed second-eye review found:

- The young heroine remains the same person by construction: her stock face, age, broad hat, single braid, tan coat, teal charm, belt, boots, shallow handleless right-hip pan, left-side satchel, gait, facing, and source frame order remain the base pixels.
- The Claim-Day addition is limited to a compact clerk-teal neckerchief and one small teal crossed-thread stitch on the existing satchel flap. Both stay on their physical garments across A/B views and remain readable without changing the silhouette.
- The sign reads immediately as one pointed aged-steel sewing needle with one thinner clerk-teal thread visibly passing through its eye on a warm-cream hung canvas banner. It carries no letters, numbers, logos, extra tools, people, or primary weapon cues.
- No credible text, watermarks, realistic firearms, gore, extra characters, crops, reordered cells, duplicated cells, mirrors, or non-key background contamination are visible. Tesseract returned empty for all three raws.
- Retakes: heroine 0. The sign's three direct pictogram takes failed the 128px read (dagger/cursive, then key/monogram, then hook/bar). Per the changed-premise retry law, the final was decomposed into a native blank banner plus a large native needle/thread donor and passed a fresh 128px critique at 88% confidence. Residual: the long diagonal shaft has a brief weak dagger risk at thumbnail scale, but the visible eye and separate teal thread make the sewing read primary; no firearm form exists.

Owner lineup: `assets/contact-sheets/char-tailor-release-lineup.png` in stock, Complainant's Coat, Gilded, Claim-Day order.

Stock/Claim-Day same-machine evidence: `assets/contact-sheets/char-hero-claimday-sheets-25pct.png`, with A on the first row and B on the second.

Accessory and sign detail evidence: `assets/contact-sheets/char-hero-claimday-detail-crops-2x.png`.

## Final prompt set

Every heroine edit included this exact anchor:

> Gold Rush house hero sprite: the same young heroine re-dressed, engraved-warm frontier illustration, identical silhouette and grid, #ff00ff flat background, no letters, no gore.

Every heroine call bound the canonical female source sheet as the exact edit target; required the exact 1700x1700, 4x4, 425x425-cell A/B direction and walk-phase contract; preserved face, age, hat, braid, tan coat, teal charm, belt, pan-right, satchel-left, boots, body, pose, scale, padding, and complete uncropped figures; and prohibited mirrors, duplicates, reordering, added/missing cells, words, letters, numbers, logos, watermarks, realistic firearms, gore, extra characters, scenery, floors, shadows, sash, rosette, or torso ribbon.

- **Claim-Day A/B:** add only the same compact clerk-teal neckerchief and one tiny teal crossed-thread stitch on the existing left-side satchel flap. Keep the scarf tied close, below the chin, clear of the existing charm, and correctly visible or hidden through all directions.

The sign's direct generation and correction prompts included this exact anchor:

> Gold Rush house prop: a humble tailor's cloth sign, engraved-warm frontier illustration, clear teal needle-and-thread pictogram, #ff00ff flat background, no letters, no gore.

They required one isolated vertical cream-canvas banner, a short walnut dowel, two aged-brass rings, exactly one needle and one looping thread, generous padding, and a flat exact-magenta field. They prohibited text, letters, numbers, logos, watermarks, scissors, mannequins, people, extra tools, weapon cues, scenery, floor, wall, wagon, shadows, duplicates, and cropped hardware.

The successful changed-premise donor prompt required one literal pointed aged-steel domestic sewing needle at large scale, one much thinner clerk-teal thread visibly passing through its modest eye, a broad open loop, exact `#ff00ff`, and the same engraved-warm Frontier Ledger style; it prohibited hooks, keys, bars, fishing tackle, letters, monograms, swords, daggers, weapons, syringes, arrows, logos, scissors, banners, people, and duplicate tools. A separate native edit removed the failed center mark from the source banner and restored seamless blank woven cloth before compositing.

No fire-side extraction, final alpha asset, runtime wiring, source code, specs, or shipped stock assets were touched.
