# Codex art run — E10 Ember World

Date: 2026-07-21  
Task: `art-e10-world-ember`  
Mode: native Codex `image_gen` only; no Higgsfield, processing, extraction, alpha work, resizing, or runtime wiring.

## Outputs

| File | Native final job | Size | SHA-256 | Retakes | Verdict |
|---|---|---:|---|---:|---|
| `ter-ember-world-atlas.png` | `exec-90d97ba5-3716-49bd-b8d3-55d0eedb1abd` | 1254×1254 RGB | `abc3c358788339299ad953312f07cb6c5367186770282d1f8d5fc5a392806ce8` | 1 | PASS |
| `prop-ember-world.png` | `exec-b874a6d6-dba0-43e6-9570-5de52f6f181f` | 1254×1254 RGB | `4854aa05147d8f3cb327724e497478f82dafc95a3491a890947ebd54c6beb2f9` | 0 | PASS |

Native run directory: `019f8176-13f7-74e2-8955-8dc6f66b5485`.

## Measured self-QA

The atlas is an exact 2×2 with four equal 627×627 cells in the requested order. Pairwise normalized cell RMSE is 0.110–0.134; cell-to-horizontal-mirror RMSE is 0.084–0.120. One targeted native correction replaced the first take's hard central cross with narrow natural transitions while preserving the four exact cells. Both finals are opaque sRGB PNGs with zero exact `#ff00ff`; OCR output is empty. Full-size inspection confirms the atlas edges are full-bleed and the prop family remains readable at gameplay zoom.

| File | Tiles distinct / props read | Palette E2 echo | Vein not lake / no landmark | Letters / firearms / gore / people none |
|---|---|---|---|---|
| `ter-ember-world-atlas.png` | Y — cooled basalt, active vein, ash drift, ember gravel | Y — ochre, sepia, warm brown, charcoal, restrained ember seams | Y — narrow branching cracks through solid basalt; no open lava body | Y |
| `prop-ember-world.png` | Y — boulders, spires, vent, cinders, slab | Y — warm parchment, ochre-red pumice, sepia/charcoal engraved stone | Y — no titan machine or other landmark; only the vent seams glow | Y |

The atlas has no drawn grid, gutter, border, mirrored cell, label, object, or landmark. The prop sheet is full-bleed painted reference art on plain warm ground, not a keyed grid. Its vent glow is restrained rather than neon; no other prop emits light.

## Final prompts

### Ember World atlas — initial generation

> Use case: stylized-concept  
> Asset type: runtime terrain atlas reference for a Three.js game  
> Primary request: Create a FRESH clean gutterless exact 2×2 top-down terrain atlas for the Ember World, a cooling-volcanic biome. Four equal square cells, in this exact order: TOP LEFT cooled-basalt-crust — dark hardened lava rock, engraved hexagonal and columnar crack patterns, warm brown through charcoal, completely cold with no glow; TOP RIGHT active-lava-vein — dark basalt threaded by narrow branching molten orange-red cracks, warm ember light rising only from seams, unmistakably veins and NOT an open lava pool or lake; BOTTOM LEFT ash-drift — warm-grey volcanic ash field with fine engraved hatch stipple, soft wind drifts and ripples, quiet cold zone; BOTTOM RIGHT ember-gravel — walkable warm ochre-red pumice and cinder gravel, scattered cooled lava pebbles, very faint ember undertone.  
> Style/medium: Gold Rush Frontier Ledger hand-engraved storybook illustration, fine ink hatching and cross-hatch shading, parchment-warm ochres, sepias and warm browns, illustrated and readable, never photorealistic. Match the form and quality of the supplied terrain atlases; use the Ember World region of the supplied E10 worlds plate only as a look anchor.  
> Composition/framing: perfectly top-down orthographic ground textures filling the canvas edge to edge; exact equal quadrants; each cell independently edge-tileable; natural texture transitions meet directly at the central boundaries with NO visible grid, divider, gutter, border, cross, frame, or empty spacing. No mirrored or repeated cells. No landmarks, buildings, machines, props, figures, horizons, labels, icons, or inset panels.  
> Color palette: E2 Steamworks echo — warm ochre, sepia, warm brown, charcoal, warm grey; restrained molten orange-red only in the active-vein seams and a nearly imperceptible undertone in ember gravel. No deep-ink space palette; no neon; no teal required.  
> Gold Rush house terrain art: warm engraved-frontier illustration, full-bleed edge-tileable ground tiles, no letters, no gore.  
> Constraints: exactly four distinct readable ground textures; active lava is narrow branching cracks in solid dark rock, never an open body of lava. No text, letters, numbers, logos, signatures, watermarks, people, creatures, weapons, firearms, gore, body imagery, titan machine, cooled machine landmark, buildings, or scenery.

### Ember World atlas — boundary correction

> Use case: precise-object-edit  
> Asset type: runtime terrain atlas correction  
> Primary request: Edit the supplied Ember World 2×2 terrain atlas. Preserve the exact canvas, exact four equal quadrants, top-down view, all four existing materials and their order unchanged: cooled basalt top-left, active narrow lava veins top-right, ash drift bottom-left, ember gravel bottom-right. Change ONLY the overly hard central horizontal and vertical quadrant boundaries: soften them into narrow natural texture transitions so there is no drawn cross, grid line, gutter, border, gap, or straight divider visible. The atlas must still have four exact equal cells and each cell must remain distinct and independently readable. Do not blur the whole image. Do not let lava enter other cells. Keep active lava as narrow branching cracks in dark basalt, never a pool or lake. Keep the outer edges full bleed.  
> Gold Rush house terrain art: warm engraved-frontier illustration, full-bleed edge-tileable ground tiles, no letters, no gore.  
> Constraints: no new objects, no props, no landmark, no machine, no people, no creatures, no text, letters, numbers, logos, signatures, watermarks, firearms, weapons, gore, body imagery, neon, deep-ink space palette, mirrors, repeated cells, frame, or empty spacing.

### Ember World prop family

> Use case: stylized-concept  
> Asset type: reference-tier runtime biome prop family for a Three.js game  
> Primary request: Create a FRESH cohesive painted prop family for the Ember World cooling-volcanic biome. Show distinct uninhabited natural scatter props: a compact group of cooled basalt boulders; two or three tall obsidian and cooled-lava spires as dark irregular stone columns; one warm-glowing ember vent / small fumarole with restrained orange-red glow visible only in narrow cracked seams and a subtle wisp of heat shimmer; scattered pumice and cinder rocks in warm ochre-red; and one broad cracked cooled-lava slab. All requested prop types must read distinctly at gameplay zoom.  
> Scene/backdrop: full-bleed painted props arranged as one coherent reference-tier family on a simple plain warm parchment ground, with generous breathing room between types, no horizon, no landscape scene, no grid, no keyed background, no checkerboard, no labels, no inset boxes. Complete and uncropped.  
> Style/medium: Gold Rush Frontier Ledger hand-engraved storybook illustration with fine sepia ink hatching, cross-hatch shading, warm hand-painted surfaces, strongly readable silhouettes, never photorealistic. Match the presentation quality of the supplied Gold Rush prop sheets and the warm volcanic visual grammar from the left side of the E10 worlds reference.  
> Composition/framing: top-down three-quarter oblique game-prop view, compact family arrangement filling the square canvas without touching edges; each prop type visually separable; no repeated or mirrored elements.  
> Color palette: E2 Steamworks echo — ochres, sepias, warm browns, charcoal basalt and obsidian, warm-grey ash dust. The ONLY light emission is restrained orange-red ember glow in the vent seams, warm and readable, glow accents not neon. No teal glow, no deep-ink space palette.  
> Gold Rush house prop art: warm engraved-frontier illustration, full-bleed painted props on transparent-ready plain ground, no letters, no gore.  
> Constraints: natural terrain scatter only. Absolutely NO titan machine, cooled titan-machine landmark, machinery, industrial structure, building, ruin, beacon, lamp, person, creature, weapon, firearm, body imagery, molten horror, open lava lake, text, letters, numbers, symbols, logos, signatures, or watermarks. No other light-emitting props.

No other E10 world, cooled-titan-machine landmark, Ark surface, roster, town portrait, pan, icon, code, spec, e2e, processing, extraction, alpha, or runtime integration was started.
