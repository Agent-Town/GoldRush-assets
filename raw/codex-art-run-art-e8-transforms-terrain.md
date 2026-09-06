---
source: codex
project: Gold Rush
date: 2026-07-21
type: reference
---

# E8 transforms and mare terrain batch 2

## Result

Native Codex `image_gen` only. No Higgsfield still-image model was used. This run produced exactly the five files assigned by `art-e8-transforms-terrain`; no processing, wiring, roster, town-icon, or later-era work was started.

| File | Native final job | Final size | SHA-256 | Retakes | Verdict |
|---|---|---:|---|---:|---|
| `bld-tavern-e8.png` | `exec-6e36e81a-96a9-4187-9d0c-d7b4c969bcec` | 1254x1254 RGB | `9d8b02550296df7b4f3c9c194ef2dcb662d8c204adb02c68452d3d6a8de21090` | 0 | PASS |
| `bld-signal-turret-e8.png` | `exec-77776c01-4fa9-445c-a77b-a34a5b838038` | 1254x1254 RGB | `3d5da5d0dc73031855707ef1685fbc0f44ea72d00bb5d6c9595d165cf332087b` | 0 | PASS |
| `bld-schoolhouse-e8.png` | `exec-a3351354-a70b-4939-9014-bd6d7ee7253e` | 1254x1254 RGB | `99989e5471a0fdc6d84db7519c5e56c5fce358c95544a946b7e015eabaa4ba53` | 1 | PASS |
| `bld-rail-depot-e8.png` | `exec-8f04abb0-472b-48de-b0e6-9d56c3b5c7fb` | 1254x1254 RGB | `8a4c93edfafcaaf78831cba94fbafa0c7d14f09e84d7a6f89572cbe18f84ad2d` | 1 | PASS |
| `ter-mare-atlas.png` | `exec-1f433498-c1ac-41a7-8f1e-0a34a8bdb3ee` | 1254x1254 RGB | `91296f0359f46dd25c67418a6898e7bbecf8e95984b28500962e8c2a2af1d371` | 1 | PASS |

Native run directory: `019f8116-7adb-7f33-a71d-532e2c5a9267`.

## Measured self-QA

Source ratios are approximate normalized visible-bound comparisons with the named E7 edit sources. All five passed full-size and 128px direct inspection and returned empty OCR output. The atlas is exactly four 627x627 cells; pairwise normalized RMSE is 0.104-0.116 and each cell-versus-horizontal-mirror RMSE is 0.088-0.119, confirming distinct, non-mirrored cells.

| File | Silhouette reads / tiles distinct | Palette in E8 | Footprint matches source | Letters / firearms / gore none | Source ratio and measured note |
|---|---|---|---|---|---|
| `bld-tavern-e8.png` | Y | Y | Y | Y | `bld-tavern-e7.png`: ~0.98x W / 1.00x H excluding the removed hanging sign; same two-storey footprint, porch, annex, stairs, gable and chimney envelope; small Earth cameo, not horizon |
| `bld-signal-turret-e8.png` | Y | Y | Y | Y | `bld-signal-turret-e7.png`: ~1.02x W / 0.97x H; same four-foot trestle, platform, ladder, mast and circular ring; broad disc lens and mirror petals, no barrel/muzzle/bore |
| `bld-schoolhouse-e8.png` | Y | Y | Y | Y | `bld-schoolhouse-e7.png`: ~0.99x W / 1.02x H; same schoolhouse, porch, roof and tower; archive panel blank except perforation holes; tape holes-only |
| `bld-rail-depot-e8.png` | Y | Y | Y | Y | `bld-rail-depot-e7.png`: ~0.96x W / 0.99x H; same depot, canopy, platform, rail stub, clerestory and chimney; open comms rings; facade plates blank |
| `ter-mare-atlas.png` | Y | Y | Y (n/a fresh atlas) | Y | Exact 2x2 equal cells: fine regolith / boulder field / crater glass / landing scorch; distinct at 128px; boundaries blended with no gutters, grid line, or mirrored tile |

The Canteen deliberately replaces roof material with a same-envelope glass canopy to satisfy “the tavern under glass”; it does not change the gameplay size band. The Lens Turret reads as a solar/optical instrument, never a weapon emplacement. Visual review found no people, logos, watermarks, cold photorealism, or prohibited content.

## Final prompts

Every generation and correction prompt included the required anchor verbatim.

### Orbital Canteen

Edit `bld-tavern-e7.png` into the E8 Orbital Canteen, “the tavern under glass.” Preserve the exact two-storey tavern mass, arched front gable, balconies, porch, stairs, side annex, chimney, camera angle, scale, footprint, padding, and outer height/width envelope. Repaint with silver structural bands, suit-brass fittings, honey-gold glass panels, restrained teal agent-glow, warm-grey stippled regolith footing, and E7 walnut only as restrained lineage bracing. Add a honey-gold transparent dome or canopy without enlarging the silhouette band. Show one small soft blue-green Earth cameo through the glass behind the structure, never a horizon. Keep warm inhabited interior light and remove signage. Gold Rush house building art: warm engraved-frontier illustration, full-bleed painted structure on transparent-ready plain ground, no letters, no gore. Same top-down three-quarter gameplay view, centered, complete, uncropped, generous parchment padding, readable at 96-128px. No people, writing, logos, watermarks, firearms, barrels, muzzles, bores, weapons, ammunition, gore, cold photorealism, black void, checkerboard, large Earth horizon, or dominant walnut.

### Lens Turret

Edit `bld-signal-turret-e7.png` into the E8 Lens Turret, a tracking optical/lens instrument. Preserve the exact four-foot trestle, platform, ladder, mast, circular top ring, camera angle, scale, footprint, padding, and outer envelope. Repaint as silver lattice with suit-brass joints, honey-gold glass, restrained teal status glow, warm-grey stippled regolith footing, and restrained E7 walnut bracing. Replace the relay dish inside the existing ring with a broad honey-gold focusing lens and open mirror petals in a suit-brass gimbal. It focuses light as a scientific solar optic and is not a weapon. Gold Rush house building art: warm engraved-frontier illustration, full-bleed painted structure on transparent-ready plain ground, no letters, no gore. Same three-quarter gameplay view, centered, complete, uncropped, all four feet visible, readable at 96-128px. Absolutely no barrel, muzzle, bore, target-pointing tube, cannon, gun form, firearm silhouette, weapon, projectile, ammunition, missile, letters, numbers, logos, watermark, gore, people, cold photorealism, black void, checkerboard, or dominant walnut.

### Mission Archive

Edit `bld-schoolhouse-e7.png` into the E8 Mission Archive. Preserve the exact schoolhouse mass, porch, steps, roof slopes, tower envelope, camera angle, scale, footprint, padding, and outer silhouette. Repaint with silver panels and bands, honey-gold glass windows, suit-brass fittings, restrained teal archive-system glow, warm-grey stippled regolith footing, and E7 walnut only as restrained lineage bracing. Convert the rooftop punched-tape apparatus into a compact glass-and-brass archive reader; all cards and tape are blank except perforation holes. Gold Rush house building art: warm engraved-frontier illustration, full-bleed painted structure on transparent-ready plain ground, no letters, no gore. Same top-down three-quarter gameplay view, centered, complete, uncropped, readable at 96-128px. No letters, numbers, words, labels, logos, watermarks, firearms, weapons, gore, people, cold photorealism, black void, checkerboard, or dominant walnut.

Targeted correction: change only the teal wall display beside the tape machine into a blank glass archive panel containing only a sparse regular array of circular perforation holes. Remove every line, stroke, trace, pseudo-writing, symbol, glyph, and diagram; preserve everything else exactly. The correction used the same required style anchor.

### Comms Mast

Edit `bld-rail-depot-e7.png` into the E8 Comms Mast. Preserve the exact depot building, canopy, platform, steps, rail stub, clerestory, chimney position, camera angle, scale, footprint, padding, and outer envelope. Repaint the depot and mast with silver structural bands and lattice, suit-brass bracing, honey-gold glass insulators and windows, restrained teal status fittings, warm-grey stippled regolith footing, and E7 walnut only as restrained lineage bracing. Refine the rooftop ring mast into an unmistakable open communications antenna with concentric receive/broadcast rings, never a weapon. Gold Rush house building art: warm engraved-frontier illustration, full-bleed painted structure on transparent-ready plain ground, no letters, no gore. Same top-down three-quarter gameplay view, centered, complete, uncropped, readable at 96-128px. No letters, numbers, labels, logos, watermarks, firearms, barrels, muzzles, bores, weapons, ammunition, missiles, gore, people, cold photorealism, black void, checkerboard, or dominant walnut.

Targeted correction: change only the two small facade plaques above the right windows into completely blank smooth silver plates with four corner rivets. Remove every scratch, line, pseudo-letter, pseudo-number, glyph, or decorative trace; preserve everything else exactly. The correction used the same required style anchor.

### Mare atlas

Create a clean gutterless 2x2 lunar mare terrain atlas with four equal cells in this exact order: top-left regolith-fine, warm-grey stippled fine moon dust; top-right boulder-field, scattered warm-grey basalt boulders on regolith; bottom-left crater-glass, a shallow impact-glass basin with restrained teal-tinted vitreous sheen; bottom-right landing-scorch, a soft scorched regolith apron in darker warm-grey. Each cell is top-down, edge-tileable, full-bleed, distinct, and readable at gameplay zoom. Gold Rush house terrain art: warm engraved-frontier illustration, full-bleed edge-tileable ground tiles, no letters, no gore. Exact square 2x2 atlas, four equal cells, orthographic top-down, no perspective horizon, outer frame, or padding. Use warm-grey stippled lunar regolith over parchment warmth, restrained teal only in impact glass, and subtle suit-brass warmth in engraved highlights; never cold photoreal. No grid lines, gutters, borders, dividers, mirrored cells, repeated motifs, people, structures, flags, vehicles, signs, labels, writing, logos, watermark, checkerboard, horizon, stars, Earth, firearms, weapons, or gore.

Targeted correction: remove only the visible straight center cross while keeping the exact equal cell territories, order, and identities. Blend ground across the center boundaries with narrow natural irregular transitions so no straight line, gutter, divider, border, or cross remains; preserve each cell's dominant interior texture and outer-edge tileability. The correction used the same required terrain style anchor.
