---
source: codex
project: Gold Rush
date: 2026-07-27
type: art-run
---

# art-batch-prospector-coats-hover8 — THE COATS AT HOVER8

## Result

Native Codex `image_gen` only; no Higgsfield, CLI image model, extraction, alpha processing, runtime integration, or edits to the shipped stock sheet.

Two source-dominant 8x4 release sheets landed at the exact requested paths:

- `/Users/robin/Claude/Projects/Gold Rush/assets/raw/char-prospector-complainant-sheet-hover8.png`
- `/Users/robin/Claude/Projects/Gold Rush/assets/raw/char-prospector-gilded-sheet-hover8.png`

The read-only edit base was `/Users/robin/Claude/Projects/Gold Rush/assets/raw/char-prospector-sheet-hover8.png`; the accepted hover4 A sheets supplied costume language only. Native run directory: `019f9ffb-6d1d-7e70-bf00-0970c09aefec`.

The native edits arrived at 1609x977 in the correct 8x4 composition. They were deterministically resampled to the binding 2240x1360 canvas, near-magenta background pixels were normalized to exact `#ff00ff`, and coat pixels were admitted only inside each authoritative stock frame bbox. The stock lower band from y=220 through y=339 in every 280x340 cell remains source-exact, preserving the hover base and flame cadence. No extraction or repainting was performed.

| File | Native output | Final size / grid | Exact key | 5%-near key | Visible bbox band | Frame QA | SHA-256 |
|---|---|---:|---:|---:|---:|---:|---|
| `char-prospector-complainant-sheet-hover8.png` | `exec-43a7aa5e-9444-4df7-8372-8a1b8bb35b33.png` | 2240x1360 RGB / 8x4 / 280x340 cells | 2,305,303 / 75.6730% | 2,305,303 / 75.6730%; 0 non-exact | 190-256w x 186-220h | 32/32 distinct; 0 exact mirrors; 0 clipped | `02c34a9424502e5d9c807107db2d30beb7d1ff86dd85169db00a44373ca45054` |
| `char-prospector-gilded-sheet-hover8.png` | `exec-76f9d6ca-9475-44fc-8496-c0eb821e1e7f.png` | 2240x1360 RGB / 8x4 / 280x340 cells | 2,315,788 / 76.0172% | 2,315,788 / 76.0172%; 0 non-exact | 190-256w x 186-220h | 32/32 distinct; 0 exact mirrors; 0 clipped | `1ea7c51bbd113197f98c70bfd7556b40d825cf5e6765c2b261205c31b9d51d39` |

## Measured self-QA

The authoritative stock hover8 base is 2240x1360 RGB with an 8x4 grid, 280x340 cells, 32/32 distinct frames, zero exact mirrors, zero clipped frames, and a visible bbox band of 190-256w x 186-220h. Both coat sheets match that bbox band exactly. The source hash remained `7e0c3caca7db3c749444a57e02d5b5c2ec1df772d4149f854760586aa9599927`.

At same-machine 25% size (560x340), normalized whole-sheet RMSE is:

| Pair | Normalized RMSE |
|---|---:|
| stock / complainant | 0.073968 |
| stock / gilded | 0.065739 |
| complainant / gilded | 0.084839 |

Full-size and lineup inspection found:

- The Complainant's Coat reads as a modest civic thank-you: broad clerk-teal screen-space ribbon, restrained teal rosette, and compact stamped brown satchel. The accepted screen-space sash decision is preserved.
- The Gilded Prospector reads as the top-three prize: selective matte gold-leaf hull and helmet panels, aged dark-brass borders, and a stronger starstone-teal dial without neon flood.
- Pose, facing, frame order, pan hand, arm articulation, hover base, flame cadence, padding, and outer silhouette remain bound to the stock hover8 source.
- No credible letters, numbers, logos, watermarks, realistic firearms, gore, extra characters, crops, duplicated cells, mirrored cells, or reordered frames are visible.

Owner evidence: `assets/contact-sheets/char-prospector-three-coat-hover8-lineup.png`, in stock / complainant / gilded order at one native 280x340 hover8 cell per coat.

The four retained hover4 raws remain present and hash-identical:

| Retained file | SHA-256 |
|---|---|
| `char-prospector-complainant-sheet-hover4-a.png` | `8160fe2a94882dd90ef8e327e6aa18ea527c9815f1fcf5f72112dff45e553fb8` |
| `char-prospector-complainant-sheet-hover4-b.png` | `a9ad8049c47cb2784f67d3e2bc7ca9247ac891bcadf341e95ad188269e9b1637` |
| `char-prospector-gilded-sheet-hover4-a.png` | `08af6936a427ac001fed61c39919b0a5d34826f7637b535e445b2ed73f1c3f49` |
| `char-prospector-gilded-sheet-hover4-b.png` | `c0a4a0a375c2377d04c7599efb9cf7f3c2cf8cfa6d2876d6c5a86d1798e7be9f` |

## Final prompt set

Every native edit included this exact task anchor:

> Gold Rush house sprite: the brass Prospector agent re-dressed, engraved-warm frontier illustration, identical silhouette and grid, #ff00ff flat background, no letters, no gore.

Both prompts named Image 1 as the only edit target and authoritative hover8 pose/grid sheet, with Image 2 as costume and colour reference only. Both bound the exact 2240x1360, 8-column x 4-row, 32-cell, 280x340-cell contract; exact coordinates, scale, padding, pose, facing, frame order, pan hand, hover flame, arm articulation, silhouette, and uncropped bounds; and a perfectly flat `#ff00ff` field. Both prohibited mirrors, duplicates, missing/added/reordered/cropped cells, words, letters, numbers, logos, watermarks, borders, captions, realistic firearms, weapons, gore, extra characters, scenery, cast shadows, neon flood, jewels, crowns, capes, and silhouette protrusions.

- **Complainant:** re-dress only the stock Prospector with the accepted broad clerk-teal diagonal ribbon, restrained teal civic rosette where visible, and compact stamped brown leather satchel with an abstract embossed seal. Preserve the accepted screen-space sash convention; do not redesign the coat.
- **Gilded:** re-dress only the stock Prospector with selective matte gold leaf on broad hull and helmet panels, aged dark-brass borders and engraved seams, subtle patina, and a stronger starstone-teal dial. Keep joints, arms, pan, lower ring, vents, and panel borders in aged brass; prohibit ribbon, satchel, neon flood, jewels, crown, and cape.

No processing, extraction, alpha work, runtime wiring, source code, specs, tasks, reviews, STATUS, or existing shipped assets were touched.
