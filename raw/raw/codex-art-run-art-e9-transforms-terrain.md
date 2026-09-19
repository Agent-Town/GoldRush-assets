# Codex art run — E9 transforms + Red Fields terrain

Date: 2026-07-21  
Task: `art-e9-transforms-terrain`  
Mode: native Codex `image_gen` only; no Higgsfield, extraction, alpha processing, resizing, or runtime wiring.

## Outputs

| File | Intent | SHA-256 |
|---|---|---|
| `bld-tavern-e9.png` | E8 Orbital Canteen edit → Dome Commons Annex | `76f6c34b86b990e3fd5aeec38322dba92c3b40bd38045bc1525a18a57fcecf48` |
| `bld-signal-turret-e9.png` | E8 Lens Turret edit → Storm-lance weather conductor | `84ad4b0b75feeba6be22c2d6c32a6f234e46a6a138686c5ebffb54af3bcaed0a` |
| `bld-schoolhouse-e9.png` | E8 Mission Archive edit → Areology Hall | `673fb84786ea9f826ae41cce6ae4da747b4ae624df109e1a32963ef591fda145` |
| `bld-rail-depot-e9.png` | E8 Comms Mast edit → World-band Tower | `96fe7a85c8c17c3b11700823fe53d321ea1fe06e2bfb3ec9c3843e575bf27255` |
| `ter-redfields-atlas.png` | Fresh exact 2×2 Red Fields terrain atlas | `fe3acfff6c2ee688556e1a46c0a7e79ce518247f1a8788a2e014cd2bd8b3322e` |

All five are 1254×1254 RGB PNGs.

## Measured self-QA

Approximate source ratios compare the normalized visible structure envelopes against the named E8 edit sources. All five passed full-size and five-up 128px direct inspection. OCR was empty on four files; the Storm-lance returned only the non-credible hatch fragment `fe a a en`, with no visible glyphs on inspection.

| File | Silhouette reads / tiles distinct | Palette in E9 | Footprint matches source | Letters / firearms / gore none | Source ratio and measured note |
|---|---|---|---|---|---|
| `bld-tavern-e9.png` | Y | Y | Y | Y | `bld-tavern-e8.png`: ~1.02× W / 1.01× H; same dome, facade, porch, stair and annex envelope; base planters carry muted E1 green |
| `bld-signal-turret-e9.png` | Y | Y | Y | Y | `bld-signal-turret-e8.png`: ~0.90× W / 0.92× H; same four-foot trestle, ladder, platform and mast proportions; ~86% canvas height remains inside the 83–93% band; open coils and vertical lightning rod read as weather control, never a barrel |
| `bld-schoolhouse-e9.png` | Y | Y | Y | Y | `bld-schoolhouse-e8.png`: ~1.02× W / 1.03× H; same porch, roof, tower, tape path and side apparatus envelope; tape holes-only, panels blank |
| `bld-rail-depot-e9.png` | Y | Y | Y | Y | `bld-rail-depot-e8.png`: ~1.00× W / 1.00× H; same depot, platform, rail stubs, cart and mast envelope; facade and canister blank |
| `ter-redfields-atlas.png` | Y | Y | N/A | Y | exact four 627×627 cells; pairwise normalized RMSE 0.113–0.166; cell-vs-horizontal-mirror RMSE 0.094–0.113; no gutter or drawn grid; green was native-edited against an exact `#50674c` reference swatch (closest encoded sampled pixel `#53604a`, RGB distance 7.87) |

The atlas order is top-left dune-rust, top-right regolith-crust, bottom-left canal-wet earth, bottom-right the-green. Shared boundaries use narrow natural texture transitions rather than gutters or divider strokes. The wet cell contains sheen only, no open flow. The green cell retains visible red earth beneath low ground cover.

## Prompts

Every building generation and correction included this sentence verbatim:

> Gold Rush house building art: warm engraved-frontier illustration, full-bleed painted structure on transparent-ready plain ground, no letters, no gore.

Every atlas generation and correction included this sentence verbatim:

> Gold Rush house terrain art: warm engraved-frontier illustration, full-bleed edge-tileable ground tiles, no letters, no gore.

### Dome Commons Annex

Edit `bld-tavern-e8.png`, preserving its exact silhouette, footprint, camera, roofline, dome, facade, porch, stairs, height and padding. Repaint the Orbital Canteen into a warm-lit E9 commons annex using rust-red engraved earth/timber, aged brass, honey-gold glass, warm parchment and only restrained silver lineage bracing. Add a thin base-planter thread of E1 riverbank green `#50674c`. No people, signs, writing, weapons, firearms, logos, watermarks, checkerboard, or gore.

### Storm-lance

Edit `bld-signal-turret-e8.png`, preserving the exact four-foot trestle, platform, ladder, mast, footprint and proportions. Repaint dominant silver into rust-red engraved timber and aged brass. Replace the optic reading with a vertical lightning rod, open condensation coils, vane-rings, glass charge bulbs and a warm/teal charge crown that gathers and grounds storms. It is an atmospheric-control instrument only: no barrel, muzzle, bore, gun, cannon, projectile, aimed beam, target or crosshair. A framing correction scaled the complete structure into the 83–93% building band. Two later enlargement candidates were rejected because they clipped the front foot; the complete first correction is the final.

### Areology Hall

Edit `bld-schoolhouse-e8.png`, preserving its exact schoolhouse silhouette, porch, steps, roof, tower, tape path, side-apparatus envelope and framing. Repaint into rust-red timber/earth, aged brass, honey-lit windows and brass-and-glass survey detail. All charts and panels remain blank; tape is perforation-holes-only. A targeted correction replaced a barrel-like horizontal survey tube with a non-directional rock-sample turntable, mineral samples and upright glass vials.

### World-band Tower

Edit `bld-rail-depot-e8.png`, preserving the exact depot, canopy, platform, steps, rail stubs, clerestory, cart, mast placement and outer envelope. Repaint into rust-red engraved timber, aged brass, honey-gold glass insulators, restrained teal status fittings and restrained silver lineage bracing. Evolve the mast into open concentric receive/broadcast rings. Keep facade plates and canister blank; no weapon forms or writing.

### Red Fields atlas

Create an exact gutterless 2×2 top-down atlas with four equal cells: dune-rust wind-carved crust; dead dry regolith crust with fine hatch stipple; canal-wet dark rust earth with sheen but no open water; and low spreading ground cover over red earth using E1 riverbank green `#50674c`. Keep the four cells distinct, full-bleed and edge-tileable, with no mirrors, labels, objects, grid lines or gutters. One native edit softened the generated cross-boundary into natural transitions; a second native edit used a temporary exact `#50674c` color swatch to correct the living tile away from olive drift.

No other era art or project surface was changed.
