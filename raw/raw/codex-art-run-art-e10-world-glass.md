# Codex art run — E10 Glass Steppe

Date: 2026-07-21  
Task: `art-e10-world-glass`  
Mode: native Codex `image_gen` only; no Higgsfield, processing, extraction, alpha work, resizing, or runtime wiring.

## Target

The Glass Steppe should read as an uninhabited E3-echo world: warm engraved steppe fused into teal crazed glass, with natural jagged lightning scars and one ancient orb-crowned collector monument. Terrain stays top-down and tileable; props stay separated on plain warm ground; the landmark gathers and grounds lightning and has no directional weapon form.

## Outputs

| File | Native final job | Size | SHA-256 | Retakes | Verdict |
|---|---|---:|---|---:|---|
| `ter-glass-steppe-atlas.png` | `exec-bd47c14d-083d-4a62-8c58-71e6a8e09712` | 1254×1254 RGB | `5beb2a40613f698e9c3bf761d071e4ff0d434c6f653207e5a8d616e85bb46aa2` | 1 | PASS |
| `prop-glass-steppe.png` | `exec-9c24e67b-ea85-4c53-81cf-3b95b1d37723` | 1254×1254 RGB | `e0208adebf4987c58481f3db5fd677df7b8dd7a6be79da3c11f421bf4cba446b` | 1 | PASS |
| `landmark-glass-steppe.png` | `exec-8b6cff3d-4654-4d78-9c7d-c085956ce93d` | 1254×1254 RGB | `db5ff55e5e1a93bfb174f7a4b9f88dfa7614b55ad32ad31ffe8e91c2438cd805` | 0 | PASS |

Native run directory: `019f8191-2fac-70b0-b94e-b3d2c41ffa17`.

## Measured self-QA

The atlas is an exact 2×2 with four equal 627×627 cells in the requested order. Pairwise normalized cell RMSE is 0.162–0.219; cell-to-horizontal-mirror RMSE is 0.148–0.188. A targeted edge-continuity edit followed second-opinion review: visual 2×2 repeats show no hard seam bands, and opposing-edge discontinuity measures only 0.93–1.30× each cell's ordinary adjacent-pixel variation. All outputs are opaque sRGB PNGs. OCR-assisted visual review found no credible text. Full-size inspection, exact cell crops, repeat mosaics, and 128px prop/landmark views confirm source-detail and gameplay-scale readability.

| File | Tiles-distinct / props-read / landmark-reads | Palette E3 echo | Scorch-not-pool / landmark-not-weapon | Letters / firearms / gore / people none |
|---|---|---|---|---|
| `ter-glass-steppe-atlas.png` | Y — glass crust, scorch veins, warm hardpan, shard gravel | Y — ochre/sepia/brown + teal glass + deep-ink accents | Y — dark branching fulgurite seams in solid ground; no water body | Y |
| `prop-glass-steppe.png` | Y — tube spires, slabs, shard-pebbles, mound, scorched rock | Y — warm fused sand + restrained teal glass | Y — no collector landmark; rock glow stays inside narrow seams | Y |
| `landmark-glass-steppe.png` | Y — orb crown, open mast, guy wires, ground anchors read at 128px | Y — warm brass/timber + teal glass + deep-ink accents | Y — passive collector; no barrel, muzzle, bore, gun form, projectile, aimed beam, target, or crosshair | Y |

The atlas has no drawn grid, gutter, border, mirror, object, landmark, horizon, water-like pool, or visible repeat seam. The prop sheet is full-bleed painted reference art on plain warm ground, not a keyed grid; its first take's checkerboard backdrop was corrected. The landmark is complete and uncropped, matches the center-region silhouette of `plate-e10-worlds.png`, and gathers natural engraved lightning into its orb and grounding cables.

## Final prompts

### Glass Steppe atlas

> Use case: stylized-concept  
> Asset type: square runtime terrain atlas for a Three.js browser game  
> Primary request: Create a FRESH clean gutterless 2×2 terrain atlas of the Glass Steppe, E3 lightning-fused plains. Use Image 1 ONLY for the glass-steppe CENTER region's teal crazed-glass look. Use Images 2–4 only as quality and atlas-layout precedents.  
> Composition: exact square canvas; strict top-down orthographic ground texture; four equal cells with natural blended transitions at the center boundaries so there is NO visible cross, grid line, gutter, border, frame, or separator. No mirrored cells. Every cell must remain edge-tileable and readable at gameplay zoom.  
> Cell order: TOP LEFT — fulgurite-glass-crust: cooled vitrified plain, crazed/crackle-engraved teal-green glass sheet where sand fused to glass, fine hatch shading, faint restrained teal sheen. TOP RIGHT — lightning-scorch: SOLID glassy ground threaded with narrow dark branching fulgurite strike scars shaped like jagged drawn lightning; restrained teal-white glow ONLY inside the seams. It must unmistakably read as branching scorch veins in solid ground, NEVER an open pool, lake, river, liquid, shoreline, or water body. BOTTOM LEFT — cracked-steppe-earth: dry warm ochre, sepia, and warm-brown hardpan between glass sheets, engraved hatch-stipple, unfused steppe earth. BOTTOM RIGHT — glass-shard-gravel: walkable scattered small glass shards and fused-sand pebbles, warm-cool gravel ground with faint teal glints.  
> Style/medium: Gold Rush house terrain art: warm engraved-frontier illustration, full-bleed edge-tileable ground tiles, no letters, no gore.  
> Palette: E3 Voltage echo — warm ochre/sepia/warm-brown base, teal glass-glow, deep ink-blue accents; never black. Drawn lightning uses jagged engraved strokes, never photoreal glow blooms. This world is NOT deep-ink outer space.  
> Constraints: exactly four distinct top-down terrain cells; no objects, structures, props, landmarks, sky, horizon, perspective, people, creatures, weapons, firearms, blood, gore, text, letters, numbers, logos, watermark.  
> Avoid: visible center cross, ruled quadrants, seams, gutters, frames, repeated or mirrored motifs, neon bloom, photorealism, water-like surfaces, open pools.

### Glass Steppe atlas — edge-tileability correction

> Use case: precise-object-edit  
> Asset type: square runtime terrain atlas correction  
> Primary request: Edit Image 1 to make EACH of its four 627×627 terrain cells independently seamless and edge-tileable in both horizontal and vertical directions. Preserve the exact 1254×1254 canvas, exact 2×2 equal-cell layout, order, top-down orthographic view, material identity, palette, engraved detail, and natural blended internal quadrant transitions.  
> Critical correction: within each quadrant, make the LEFT edge continue naturally into the RIGHT edge and the TOP edge continue naturally into the BOTTOM edge when that single cell is repeated. Remove the dark or tonal border bands and mismatched motifs that create visible horizontal or vertical seams in 2×2 repeats. Opposing edge color, luminance, texture density, crack scale, and local motifs must join naturally. Do not add a frame or blur the whole image.  
> Keep exact cells: TOP LEFT fulgurite glass crust; TOP RIGHT lightning scorch with narrow branching dark fulgurite seams in SOLID ground, never water; BOTTOM LEFT warm cracked steppe hardpan; BOTTOM RIGHT glass-shard gravel.  
> Gold Rush house terrain art: warm engraved-frontier illustration, full-bleed edge-tileable ground tiles, no letters, no gore.  
> Constraints: no visible grid, central cross, gutter, border, frame, mirrored cells, repeated stamp pattern, objects, props, landmarks, sky, horizon, people, creatures, weapons, firearms, blood, gore, text, letters, numbers, logos, watermark, neon bloom, photorealism, pools, lakes, rivers, liquid, or shoreline. Change only what is required for true wrap continuity.

### Glass Steppe prop family — initial generation

> Use case: stylized-concept  
> Asset type: square reference-tier runtime prop family for a Three.js browser game  
> Primary request: Create a FRESH full-bleed painted prop family for the Glass Steppe biome. Use Image 1 ONLY for the CENTER glass-steppe region's teal fused-glass and warm brass/ink visual language. Use Image 2 only as the full-bleed prop-family layout and quality precedent.  
> Scene/backdrop: transparent-ready simple plain warm parchment ground, visually flat and unobtrusive, with generous breathing room separating every prop type. This is NOT a keyed grid and has no cell borders.  
> Required props, all complete and uncropped: a family of standing fulgurite spires — several branching hollow glass-tube columns formed where lightning fused sand, irregular and natural, teal-tinted glass, clearly geological rather than a constructed tower; one cluster of cracked glass slabs/plates lying low on the ground; one distinct scatter cluster of small glass shards and fused-sand pebbles; one distinct fused-sand mound or hummock; one small lightning-scorched rock with narrow branching dark seam scars and restrained teal glow only in the seams.  
> Style/medium: Gold Rush house prop art: warm engraved-frontier illustration, full-bleed painted props on transparent-ready plain ground, no letters, no gore.  
> View/composition: three-quarter oblique game-prop illustration, clean silhouettes, all types readable at 128px, ample separation, no overlap that confuses types.  
> Palette: E3 Voltage echo — warm ochre/sepia/warm-brown fused sand, teal-green glass, deep ink-blue accents, fine ink hatching. Teal light is restrained glass glow, never neon; drawn lightning marks are jagged engraved strokes, never photoreal bloom.  
> Constraints: NO landmark collector spire, NO tall brass-and-timber mast/tower, NO teal-orb crown, NO buildings, NO people, creatures, weapons, firearms, gun forms, blood, gore, text, letters, numbers, logos, watermark. Only uninhabited biome scatter.  
> Avoid: keyed grid, cell borders, labels, sky, horizon, dramatic scene background, neon, photorealism, cropped props, duplicated or mirrored props, weapon-like silhouettes.

### Glass Steppe prop family — background correction

> Use case: precise-object-edit  
> Asset type: square reference-tier runtime prop family  
> Primary request: Edit Image 1 by changing ONLY the backdrop. Replace the entire visible white/gray checkerboard pattern with one continuous, simple, flat, warm parchment ground in ochre-sepia, matching a hand-engraved frontier illustration. The ground must extend full-bleed to all four canvas edges and remain visually quiet and unobtrusive.  
> Preserve exactly: every fulgurite spire, cracked glass slab cluster, shard-and-pebble scatter, fused-sand mound, scorched rock, their positions, sizes, silhouettes, fine engraving, restrained teal glass color, complete uncropped framing, and generous separation.  
> Style anchor: Gold Rush house prop art: warm engraved-frontier illustration, full-bleed painted props on transparent-ready plain ground, no letters, no gore.  
> Constraints: no checkerboard, no grid, no cells, no borders, no labels, no added props, no collector landmark, no people, weapons, firearms, gore, text, logos, watermark. Do not alter or crop any prop.

### Glass Steppe landmark

> Use case: stylized-concept  
> Asset type: square reference-tier full-bleed landmark illustration for a Three.js browser game  
> Primary request: Create a FRESH single illustration of the Glass Steppe's great solitary lightning-COLLECTOR spire. Use Image 1's CENTER region as the design anchor: the tall central weathered brass-and-dark-timber lattice mast crowned by a luminous teal orb/sphere, with guy-wire suspension cables over crazed teal glass plains. Use Image 2 only for the warm parchment-ground rendering and glass material vocabulary.  
> Subject: one monumental, enigmatic ancient relic older than the saga's civilizations — a tall brass-and-dark-timber mast/tower, open lattice construction, multiple non-directional grounding rings and insulators, large round teal orb crown gathering natural lightning, long guy wires anchored around the base. Weathered, passive, unexplained, reverent.  
> Action: several natural lightning branches descend from above into the spherical orb, then dissipate harmlessly through the mast and grounding cables into the crazed fulgurite-glass ground. Lightning is jagged hand-engraved strokes, not a beam and not fired from the monument.  
> Composition: three-quarter oblique landmark view; tower centered and dominant; entire monument, crown, guy wires, anchors, and ground contact fully visible and uncropped; simple warm full-bleed ground; enough breathing room around the silhouette; no keyed background.  
> Style/medium: Gold Rush house landmark art: warm engraved-frontier illustration, full-bleed painted landmark on plain ground, no letters, no gore.  
> Palette: weathered warm brass, dark warm timber, warm ochre/sepia parchment earth, teal-green crazed glass, restrained teal orb glow, deep ink-blue accents. Fine engraved hatching; storybook frontier illustration; never photoreal; never neon bloom.  
> Canon constraints: It must unmistakably read as a PASSIVE lightning collector and ancient monument, NOT a weapon. NO barrel, muzzle, bore, gun form, cannon, projectile, aimed beam, target, crosshair, blade, firearm, or weapon. No people, creatures, buildings, vehicles, blood, gore, text, letters, numbers, logos, watermark.  
> Avoid: telescope silhouette, antenna dish, turret, directional tube, lance, gun barrel, firing pose, science-fiction laser, cropped cables or crown, sky scene dominating the image, black outer-space palette, photoreal glow.

No Sea Moon, Ember World, Ark interior/exterior, roster, town portrait, Pan, icon, code, spec, e2e, processing, extraction, alpha, or runtime integration was started.

READY-FOR-GATES
