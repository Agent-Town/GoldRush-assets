---
source: codex
project: Gold Rush
date: 2026-07-20
type: reference
---

# E8 Orbital enemy walk8 sheets and still plates

## Result

Native Codex `image_gen` only. No Higgsfield still-image model was used. The shipped `salvage_kings_claw` boss-system row was excluded. No individual E8 enemy plates existed, so one still was generated for each non-boss row.

| File | Native job | Final size | SHA-256 | Retakes | Verdict |
|---|---|---:|---|---:|---|
| `char-e8-scrap_corsair-sheet-walk8.png` | `exec-e8e1fe92-cd6b-4eda-8ab2-e8ea91386d48` | 1120x680 RGB | `e94c0c791a9774370c3e388c87c9bf70c73bac0e04dba6923143f10e35ae4ea0` | 1 | PASS |
| `char-e8-debris_rain-sheet-walk8.png` | `exec-e4e18ff4-e967-4685-94fb-497e57b12434` | 1120x680 RGB | `f3298194688a7e7a3ee472cb62227882068c4acde652bf87d552be02003e1799` | 0 | PASS |
| `char-e8-sun_glare_shambler-sheet-walk8.png` | `exec-0dc6d38f-78b0-4057-b129-3af9ac13e13e` | 1120x680 RGB | `c706c5b0ff629a8054ca95d94d14c45926c71e3f993a45ccf218121407d0d981` | 0 | PASS |
| `plate-e8-enemy-scrap_corsair.png` | `exec-d6f8c8be-1749-4cbd-9844-8efc261447d6` | 1672x941 RGB | `e1db7db93a6ca819da3a0e443c4ac82fe44960dce0dde0fbd877343ee2a52aad` | 0 | PASS |
| `plate-e8-enemy-debris_rain.png` | `exec-12e02233-1407-4345-b866-b2c4fa0e7721` | 1672x941 RGB | `ba3e6892e691048662cc8dd7b521b58d965b8a36dd199a881c6fe9d6a12879a3` | 0 | PASS |
| `plate-e8-enemy-sun_glare_shambler.png` | `exec-b63ba7a6-d68e-460d-abd7-99f845a4b30b` | 1672x941 RGB | `0294f5b074244e31786cce62b25a202f467b09385015e040ba772a8cd18ffd7d` | 0 | PASS |

Native run directory: `019f7faf-c938-7491-9677-decf2c262ee1`.

The sheets were normalized into the established 280x340 cell proportion: exactly 4 columns x 2 rows, 1120x680, frames 1-4 top and 5-8 bottom. The accepted Corsair retake was cell-normalized uniformly to its binding 1.1x height band; all sheets had near-magenta background pixels normalized to exact `#ff00ff`. No alpha extraction or runtime wiring was performed.

## Measured self-QA

The right-facing bandit reference measures 292 px in each of its eight reference cells. Ratios below use each final frame's non-key visible height divided by 292 px.

| Sheet | Grid / key purity | Frame heights (px) | Ratio vs bandit | 25% silhouette | Distinct / not mirrored |
|---|---|---|---|---|---|
| Scrap Corsair | exact 4x2; 280x340 cells; 458,663 exact key pixels; zero near-magenta non-key pixels; zero edge-touch pixels | 320, 320, 320, 320, 320, 320, 320, 320 | 1.10x in every frame | PASS | 8/8 unique hashes; minimum mirrored RMSE 0.316 |
| Debris Rain | exact 4x2; 280x340 cells; 692,869 exact key pixels; zero near-magenta non-key pixels; zero edge-touch pixels | 146, 184, 178, 171, 108, 141, 159, 107 | 0.37-0.63x staged cluster band, inside the specified 0.25-0.75x piece range | PASS | 8/8 unique hashes; minimum mirrored RMSE 0.173 |
| Sun-Glare Shambler | exact 4x2; 280x340 cells; 582,081 exact key pixels; zero near-magenta non-key pixels; zero edge-touch pixels | 231, 230, 230, 229, 230, 231, 229, 231 | 0.78-0.79x (target 0.8x) | PASS | 8/8 unique hashes; minimum mirrored RMSE 0.234 |

Visual review at full size and 25% found all silhouettes readable, all motion directed screen-right, and no visible letters, numbers, watermarks, realistic firearms, gore, duplicate frames, or mirrored frames. The three stills preserve the collective E8 roster identities and read cleanly at plate scale with no visible text or violence.

The first Corsair source (`exec-37279d20-3f98-446e-abc4-9fe8409bdd27`) was rejected because it measured about 0.95x and one gaff crossed a cell boundary. The accepted retake removed all edge contact; deterministic per-cell scaling then brought the intact poses to the binding 1.10x band without alpha extraction.

## Final prompts

Every generation and retake prompt included this exact anchor:

> Gold Rush house sprite: engraved-warm frontier illustration, clean silhouette at gameplay zoom, #ff00ff flat background, no letters, no gore.

All sheet prompts also bound the same contract: exactly 4 columns x 2 rows; eight equal cells matching a 280x340 proportion; frames 1-4 top and 5-8 bottom; all poses independently drawn and directed screen-right; uniform `#ff00ff`; no gutters, grid lines, labels, letters, numbers, watermarks, realistic firearms, gore, duplicates, mirrors, cast shadows, or cell overlap. `char-bandit-base-sheet-walk8.png` supplied the walk8 convention and proportions, `char-hero-sheet-walk4-a.png` supplied clean sheet treatment, and `plate-e8-enemies-roster.png` supplied binding identity and palette.

### Scrap Corsair sheet

One 1.1x-adult-band Scrap Corsair per cell: sealed silver-and-teal vacuum suit, compact suit pack, warm brass joints, magnet gaff, blank pictogram tag, and no gold seams. Eight ordered footfall poses preserve equipment placement. The retake prompt changed only scale, side padding, compact gaff angle, and cell containment.

### Debris Rain sheet

One compact cluster per cell using the same short canister, bent panel, compact truss, and rounded casing. Eight rightward phases cover compact entry, unfolding tumble, forward stretch, low approach, impact compression, bounce, dispersal, and salvage settle. Pieces stay in the 0.25-0.75x band with warm-grey, silver/brass, and soft-teal arc grammar; no creature, person, explosion, fire, or weapon.

### Sun-Glare Shambler sheet

One 0.8x-band squat old lunar rover per cell: warm-grey stippled shell, sturdy jointed legs, one amber eye, over-bright sunward panel, soft teal shade state, battered silver, restrained brass, and no gold seams. Eight ordered leg phases keep the machine gentle and weather-driven.

### Individual still plates

Each still prompt used the same exact style anchor, then explicitly applied the house style to a full-bleed 16:9 lunar scene rather than a keyed sheet. The Corsair descends on a salvage line toward recoverable wreckage; Debris Rain follows clear teal arcs and settles as safe salvage; the Shambler moves from glare toward a teal-toned habitat shade pool with a second rover safely powered down. All still prompts prohibited text, letters, numbers, logos, watermarks, firearms, combat, gore, and UI labels.

No extraction, alpha processing, runtime wiring, boss art, source code, specs, reviews, or e2e files were changed.
