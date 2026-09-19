---
source: codex
project: Gold Rush
date: 2026-07-20
type: reference
---

# E7 Signal Era enemy walk8 sheets

## Result

Native Codex `image_gen` only. No Higgsfield still-image model was used. The shipped boss-system row `the_echo` was excluded. The three non-boss still plates already exist in canonical `assets/raw/`, so no duplicate stills were generated.

| File | Native job | Final size | SHA-256 | Retakes | Verdict |
|---|---|---:|---|---:|---|
| `char-e7-rogue_automaton-sheet-walk8.png` | `exec-96b81245-747c-4a50-8509-1a533da6faf5` | 1120x680 RGB | `cfea38b789256a6bd84ceb7234bd4d23b7ed7b094d9a0b6fdb4ca81e3c54ead3` | 0 | PASS |
| `char-e7-data_rustler-sheet-walk8.png` | `exec-486b1f8f-3034-4e5f-9efe-cb276a860483` | 1120x680 RGB | `add82e04a17f946d5a857e8b7e0d49c18dc3de6d55a7a464af4f48c0c7f65bea` | 0 | PASS |
| `char-e7-static_hare-sheet-walk8.png` | `exec-8c5af75d-7412-498f-8ffe-77c61ff3c14b` | 1120x680 RGB | `079de80935cc3d59001c0024cd0de59b8fd23d813b8082b66d5df561b4c42b9c` | 0 | PASS |

Native run directory: `019f7f5b-1b64-7132-96dc-4be4f4d56ee7`.

Native outputs were normalized into the binding 280x340 cell proportion: exactly 4 columns x 2 rows, 1120x680, frames 1-4 top and 5-8 bottom. The adult sheets were centered at their source scale; the hare sheet was uniformly reduced to the row's 0.35x height band. Near-magenta background pixels were normalized to exact `#ff00ff`. No alpha extraction was performed.

## Measured self-QA

The right-facing bandit reference measures 292 px in each of its eight cells. Ratios below use each final sheet's mean non-key visible height divided by 292 px.

| Sheet | Grid / key purity | Frame heights (px) | Mean ratio vs bandit | 25% silhouette | Distinct / not mirrored |
|---|---|---|---:|---|---|
| Rogue Automaton | exact 4x2; 280x340 cells; zero near-magenta non-key pixels | 272, 262, 273, 267, 281, 256, 275, 273 | 0.92x (adult 1.0x band; round/tape silhouette width-limited) | PASS | 8/8 unique hashes; minimum mirrored RMSE 0.286 |
| Data-Rustler | exact 4x2; 280x340 cells; zero near-magenta non-key pixels | 290, 289, 288, 287, 294, 290, 297, 294 | 1.00x | PASS | 8/8 unique hashes; minimum mirrored RMSE 0.259 |
| Static Hare | exact 4x2; 280x340 cells; zero near-magenta non-key pixels | 94, 112, 99, 102, 94, 107, 103, 93 | 0.34x (target 0.35x) | PASS | 8/8 unique hashes; minimum mirrored RMSE 0.110 |

Visual review at full size and 25% found every frame facing right, consistent identities and ground bands, readable silhouettes, and no letters, numbers, watermarks, realistic firearms, gore, duplicate frames, or mirrored frames.

## Final prompts

Every prompt included this exact anchor:

> Gold Rush house sprite: engraved-warm frontier illustration, clean silhouette at gameplay zoom, #ff00ff flat background, no letters, no gore.

All prompts also bound the same sheet contract: exactly 4 columns x 2 rows; eight equal cells matching a 280x340 proportion; frames 1-4 top and 5-8 bottom; a coherent eight-pose cycle; all poses independently redrawn and facing screen-right; uniform `#ff00ff`; no gutters, grid lines, labels, letters, numbers, watermarks, realistic firearms, gore, duplicates, or mirrors. `char-bandit-base-sheet-walk8.png` supplied walk8 convention/cell proportions and `char-hero-sheet-walk4-a.png` supplied clean character-sheet treatment.

### Rogue Automaton

One adult-band Rogue Automaton per cell, matching `plate-e7-enemy-rogue-automaton.png`: compact agent-frame machine, round brass-and-teal torso, jointed limbs, one honey-glass tube, tangled punched-paper tape loops, broken teal pose accents, and restrained gold seams. Eight poses: left contact, left down, left passing, left up, right contact, right down, right passing, right up.

### Data-Rustler

One adult-band Data-Rustler per cell, matching `plate-e7-enemy-data-rustler.png`: frontier company signal thief with wide dark hat, weathered rail coat, crystal-set backpack, copper clips, coiled wire and relay tools only, small teal lamps, restrained old rail-scrip accent, and a consistently readable backpack silhouette. Eight poses: left contact, left down, left passing, left up, right contact, right down, right passing, right up.

### Static Hare

One compact 0.35x-band Static Hare per cell, matching `plate-e7-enemy-static-hare.png`: warm parchment fur, honey-gold harmless static crackle, broken teal signal ripples, and a playful long-ear silhouette. Eight distinct quadruped-bound phases span compression, launch, airborne stretch, landing, recovery, and alternate-foot poses.

No extraction, alpha processing, runtime wiring, boss art, or still-plate duplication was performed.
