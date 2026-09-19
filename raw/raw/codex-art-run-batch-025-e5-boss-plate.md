---
source: codex
project: Gold Rush
date: 2026-07-17
type: reference
---

# Art batch 025 — Dredge-Queen plates

## Result

Native Codex `image_gen` only. No Higgsfield still-image model and no image processing were used.

| Plate | Native job | Size / mode | Exact `#ff00ff` | SHA-256 | Verdict |
|---|---|---|---:|---|---|
| `boss-dredge-queen.png` | `exec-038603ef-912e-45f5-83bb-caacce849a67` | 1672x941 RGB | 0 | `e246745b4a4fb6e7f8262eed3464975574565ee8e0ab2c59d55708774f9b6954` | PASS |
| `boss-dredge-queen-damage.png` | `exec-68d7f3e3-7b66-420c-9a9a-7ee8e8d14f36` | 1672x941 RGB | 0 | `f87c156f51f09460318f5eae324bda4469dfc144335f6992fa322e99e2675933` | PASS |

Native run directory: `019f6bff-9ac0-7572-9cc5-3ea21b52c6be`. Retakes: 0.

## Measured self-QA

- **Component readability — PASS:** downsampled both plates to 240px wide. The claw, near paddlewheel, far paddlewheel, and aft hold remain four separately nameable zones. In the damage plate both wheels remain identifiable while their bent paddles and dropped rims read as broken.
- **Damage continuity — PASS:** same 1672x941 canvas, camera angle, barge proportions, component positions, sea horizon, and storm-front composition. The claw hangs low, the hold is cracked with restrained cargo spill, the unhurt crew rows away in good order, and the flag is lowered.
- **Palette — PASS:** blue-green engraved swells, charcoal wall-clouds, brass/teal machinery, oxblood canvas, and warm lantern points. No photoreal water or dread-black field.
- **Canon — PASS:** no visible text, letters, numbers, watermark, mirrored duplication, firearms, skulls, gore, injuries, flames, or wreck-horror. Both images contain zero exact `#ff00ff` pixels.
- **Boss-band scale — PASS:** the complete barge fills the established railcar/crawler plate band while retaining water margin and an uncropped silhouette.

## Final prompts

Both prompts included this style anchor verbatim:

> E2's verbatim + E5 palette note: sea in layered engraved swells (ink-line crests, never foam spray realism); underwater scenes shift to blue-green parchment with light shafts; brass diving gear + teal instruments; storms are charcoal wall-clouds with warm lantern points, never dread-black.

### Intact plate

Create one full-bleed Frontier Ledger scene of the Dredge-Queen corsair flag-barge riding a storm-front's leading edge. Preserve the established brass frontier-tech identity. Use a slightly elevated near-bow three-quarter view so the amidships salvage claw, both intact port/starboard paddlewheels, and the fat aft loot-hold form four isolated zones readable at 240px. Add oxblood pictogram-only corsair canvas, warm lantern points, teal instruments, and engraved swells. No grid, mirror, text, letters, `#ff00ff`, firearms, skulls, gore, photoreal water, or dread-black field.

### Act-3 plate

Edit only the intact plate's state while preserving its vessel identity, exact angle, framing, scale, hull proportions, component locations, storm, sea, and palette. Break both paddlewheels with bent paddles and dropped rims; hang the claw slack and low; crack open the aft hold with restrained cargo spill; add one small boat carrying unhurt professionals rowing away in good order; lower the flag. The read is defeat with dignity, never wreck-horror. Keep all intact-plate prohibitions.

No extraction, alpha work, runtime integration, source edit, or commit was performed.
