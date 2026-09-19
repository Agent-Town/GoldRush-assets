# Codex Art Run — E6 enemy roster walk8 sheets

Date: 2026-07-20  
Tasks: `/Users/robin/Claude/Projects/Gold Rush/tasks/running/art--20260720-061416-art-batch-roster-e6.md`; missing-plate recovery `/Users/robin/Claude/Projects/Gold Rush/tasks/running/art--20260720-150356-art-batch-roster-e6.md`
Tool path: Codex native `image_gen` only

## Scope

Generated the three non-boss E6 roster sheets:

- `/Users/robin/Claude/Projects/Gold Rush/assets/raw/char-e6-feral_toaster-sheet-walk8.png`
- `/Users/robin/Claude/Projects/Gold Rush/assets/raw/char-e6-lawn_shepherd-sheet-walk8.png`
- `/Users/robin/Claude/Projects/Gold Rush/assets/raw/char-e6-glowjack-sheet-walk8.png`

The recovery pass found that only Glowjack's still had landed in `HEAD`, so it generated the two missing full-bleed parchment plates:

- `/Users/robin/Claude/Projects/Gold Rush/assets/raw/plate-e6-enemy-feral_toaster.png`
- `/Users/robin/Claude/Projects/Gold Rush/assets/raw/plate-e6-enemy-lawn_shepherd.png`

The existing `plate-e6-enemy-glowjack.png` was reused. `homemaker_9000` was skipped because its boss system is shipped (`src/systems/HomemakerBossSystem.ts`, `reviews/e6-boss-homemaker.md`) and its 3D model is live.

No alpha extraction, cell extraction, processed output, contracts, source, specs, reviews, e2e, or integration changes were made. Native near-magenta backgrounds were normalized to exact opaque `#ff00ff` with the established 12% color-distance replacement; dimensions and silhouettes were not resampled.

## Inputs

- `specs/enemy-rosters-e6-e10.md` §E6
- `assets/raw/char-bandit-base-sheet-walk8.png`
- `assets/raw/char-hero-sheet-walk4-a.png`
- `assets/raw/plate-e6-enemy-feral-toaster.png`
- `assets/raw/plate-e6-enemy-lawn_shepherd.png`
- `assets/raw/plate-e6-enemy-glowjack.png`
- `assets/LEDGER.md` header laws
- `docs/GOLD_RUSH_BRIEF.md` §4 and canon guardrails
- `lore/canon-rules.md`

Bandit metrology: 2240×1360, 8×4 cells = 280×340 px, figure height 292 px in all 32 cells. At the new 489 px cell height that baseline scales to about 420 px.

## Prompt contract

Every native prompt contained this sentence verbatim:

> Gold Rush house sprite: engraved-warm frontier illustration, clean silhouette at gameplay zoom, #ff00ff flat background, no letters, no gore.

Shared prompt laws: wide 28:17 canvas; exactly 4 equal columns × 2 equal rows; 280:340 cell proportions; row-major eight-phase cycle; one complete subject per cell; all frames authored facing screen-right; no duplicated or mirrored frames; uniform opaque `#ff00ff`; no text, letters, numbers, logos, watermarks, firearms, gore, shadows, floor, or grid lines.

Plate prompt laws: 16:9 full-bleed warm parchment; one dominant three-quarter view plus distinct supporting studies; preserve the accepted sheet design; no grids, magenta, text, labels, logos, watermarks, firearms, gore, horror, black smoke, or mirrored studies.

- `feral_toaster`: chrome and enamel-mint toaster, amber heat slots, gold feral rivets, teal dial, spring-coil legs; compress → launch → rise → fall → contact → squash → push → return; knee-high against the Glowjack adult reference.
- `lawn_shepherd`: low chrome-and-mint mower with rear wheel at screen-left, front roller at screen-right, copper shepherd loop, teal dial, amber machinery; wheel/brush/loop motion across eight authored phases.
- `glowjack`: adult lead-lined enamel-mint duster, amber goggles, wrapped face, sample satchel fixed to the far-side hip, copper tongs fixed to the near-side hand; eight alternating side-walk phases.

## Native runs

| Subject | Accepted native source | Calls | Retake note |
|---|---|---:|---|
| Feral Toaster | `/Users/robin/.codex/generated_images/019f7ca8-ad10-7972-a5e9-e68502cca9a3/exec-f8e94871-e18a-44b4-bc52-ff6748c5c7f2.png` | 3 | First pass rejected for near-square canvas; second rejected as oversized; final accepted at knee-high scale. |
| Lawn-Shepherd | `/Users/robin/.codex/generated_images/019f7ca8-ad10-7972-a5e9-e68502cca9a3/exec-87ca49c2-e5e1-4466-8f95-000539b65156.png` | 1 | Accepted first pass. |
| Glowjack | `/Users/robin/.codex/generated_images/019f7ca8-ad10-7972-a5e9-e68502cca9a3/exec-f4f330d5-764a-46a4-ae52-5cce105b3b92.png` | 1 | Accepted first pass. |
| Feral Toaster plate | `/Users/robin/.codex/generated_images/019f7e8d-9bd9-79f2-a0dc-c5813c51aa2a/exec-cc572c4c-70ee-46df-91f4-6250a588e989.png` | 1 | Accepted first pass; sheet design preserved in four distinct studies. |
| Lawn-Shepherd plate | `/Users/robin/.codex/generated_images/019f7e8d-9bd9-79f2-a0dc-c5813c51aa2a/exec-c103b8a8-5f6f-477c-8fa5-c181d61fc78d.png` | 1 | Accepted first pass; sheet design preserved in four distinct studies. |

Total native calls: 7. Accepted finals: 5. Rejected attempts: 2. No paid-credit or Higgsfield path used.

## Measured self-QA

Pixel ratios use the largest connected subject silhouette in each cell against the 292 px bandit height scaled to the output cell height. Hop compression legitimately changes the Toaster's per-frame height; its cycle maximum is the height-band comparison. All three remained readable in a 25% contact-sheet inspection.

| Sheet | Grid regularity | Key purity | Height vs bandit | 25% silhouette | Frames / facing | Verdict |
|---|---|---|---|---|---|---|
| `char-e6-feral_toaster-sheet-walk8.png` | 1609×977; cols 402/403/402/402; rows 489/488; cell aspect 0.823–0.826 vs ref 0.824 | 91.304% exact `#ff00ff`; 0 near-key; 0 alpha | 143–196 px, avg 163.4; cycle max 0.47× vs 0.45× target | PASS — casing, toast, heat slots, and spring gait remain readable | PASS — eight distinct rightward hop phases; no duplicate/mirror pair | PASS |
| `char-e6-lawn_shepherd-sheet-walk8.png` | 1609×978; cols 402/403/402/402; rows 489/489; cell aspect 0.822–0.824 vs ref 0.824 | 74.707% exact `#ff00ff`; 0 near-key; 0 alpha | 255–264 px, avg 259.6; max 0.63× vs 0.65× target | PASS — mower, rear wheel, front roller, loop, and teal dial remain readable | PASS — eight distinct right-facing wheel/brush phases; no duplicate/mirror pair | PASS |
| `char-e6-glowjack-sheet-walk8.png` | 1607×979; cols 402/402/401/402; rows 490/489; cell aspect 0.818–0.822 vs ref 0.824 | 77.911% exact `#ff00ff`; 0 near-key; 0 alpha | 369–384 px, avg 375.6; max 0.91× vs 1.00× target | PASS — hat, goggles, duster, satchel jars, and tongs remain readable | PASS — eight distinct right-facing walk phases; gear stays side-pinned; no duplicate/mirror pair | PASS |

Visual canon check: E6 chrome/pastel, amber Combine machinery, teal dials/samples, and gold feral seams hold; no visible letters, numbers, logos, watermarks, firearms, gore, extra people, or mirrored frames.

## Plate QA

| Plate | Dimensions | Design continuity | Card-scale read | Text/canon scan | SHA-256 | Verdict |
|---|---:|---|---|---|---|---|
| `plate-e6-enemy-feral_toaster.png` | 1672×941 | PASS — chrome/mint casing, toast, amber slots, teal dial, gold rivets, four spring legs | PASS — toaster silhouette and eager hop read at thumbnail | PASS — OCR empty; no visible letters, firearms, gore, horror, or extra subjects | `b087600677956a070f4ded133b884a0fc94e6dfcf25e9144dd6617764f89d7d9` | PASS |
| `plate-e6-enemy-lawn_shepherd.png` | 1672×941 | PASS — rear wheel, front roller/brushes, copper loop, mint/chrome body, amber machinery, teal dial | PASS — mower silhouette and shepherd loop read at thumbnail | PASS — OCR empty; no visible letters, firearms, gore, horror, or extra subjects | `20f6b69eb630c905c49b277db000908e38fc820b4ac2ca0a7b34bdc026d16ef4` | PASS |

READY-FOR-GATES
