# Codex art run — E10 Sea Moon

Date: 2026-07-21  
Task: `art-e10-world-sea`  
Mode: native Codex `image_gen` only; no Higgsfield, processing, extraction, alpha work, resizing, or runtime wiring.

## Target

The Sea Moon should read as E5 under alien tides: walkable exposed tidal seabed in blue-green parchment and warm sepia, natural marine scatter, and one ancient brass-and-teal dome whose trussed crane hoists a caged bathysphere. The world is uninhabited; the landmark is passive civil tidal/diving infrastructure, never a weapon.

## Outputs

| File | Native final job | Size | SHA-256 | Retakes | Verdict |
|---|---|---:|---|---:|---|
| `ter-sea-moon-atlas.png` | `exec-d28d18f2-2e9d-4226-a123-9c998678209b` | 1254×1254 RGB | `d4e23e63d6999ea0fbdc44efe13389c7836d0a1ae3311dd5d792526583e0c776` | 2 | PASS |
| `prop-sea-moon.png` | `exec-e85ad0e0-5778-4026-88ae-3a09cfd727ea` | 1254×1254 RGB | `902a12a933bca708197af2631b51ee42ecdee2a18cd1e46494863201881eea47` | 0 | PASS |
| `landmark-sea-moon.png` | `exec-cfe74ebf-cf1a-464e-bdd0-5b76bc30b9bc` | 1254×1254 RGB | `8bff408ec54b102aabaf35b04c32859b9196b6e0132d5ca556ec937e06732bd6` | 0 | PASS |

Native run directory: `019f81b2-0d2b-7622-9cce-78f188703aaf`.

## Measured self-QA

The atlas is an exact 2×2 with four equal 627×627 cells in the requested order. Pairwise normalized cell RMSE is 0.141–0.158; cell-to-horizontal-mirror RMSE is 0.123–0.161. Two focused native corrections removed the initial straight center cross and improved independent cell wrapping. Full-size cell crops and 2×2 repeat mosaics show organic internal transitions and no hard repeat-seam bands. All outputs are opaque RGB PNGs. Full-size and 128px inspection plus OCR-assisted review found no credible text.

| File | Tiles-distinct / props-read / landmark-reads | Palette E5 echo | Seabed-not-open-water / landmark-not-weapon | Letters / firearms / gore / people none |
|---|---|---|---|---|
| `ter-sea-moon-atlas.png` | Y — rippled tidal sand, reef crust, flattened kelp, shell gravel | Y — blue-green parchment + ochre/sepia/brown + restrained teal glints | Y — all four are top-down exposed walkable seabed; no horizon, foam, lake, pool, or open ocean | Y |
| `prop-sea-moon.png` | Y — tube spires, reef slabs, shell scatter, kelp clump, encrusted basin | Y — warm parchment/brass with restrained blue-green and teal biolume | Y — natural scatter only; no dome, crane, boat, or built structure | Y |
| `landmark-sea-moon.png` | Y — dome, observation windows, pilings, cables, crane, and caged glass orb read at 128px | Y — weathered brass + teal + blue-green + deep-ink-blue accents + warm lantern | Y — trussed lifting crane visibly suspends a bathysphere; no barrel, muzzle, bore, gun form, projectile, aimed beam, target, or crosshair | Y |

The prop sheet is full-bleed painted reference art on plain warm ground, not a keyed grid. The landmark is complete and uncropped and matches the right-region silhouette and palette of `plate-e10-worlds.png`.

## Final prompts

### Sea Moon atlas — initial generation

> Use case: stylized-concept  
> Asset type: Gold Rush runtime terrain atlas, square 1254×1254 PNG.  
> Primary request: Create a FRESH clean gutterless 2×2 terrain atlas for the Sea Moon, “E5 under alien tides.” Four equal square cells in this exact order: TOP LEFT tidal-flat-sand — wet ridged blue-grey teal-tinged sand flats with fine engraved ripple lines; TOP RIGHT living-reef-crust — solid encrusted coral and shell reef sheet fused to ground, teal-and-brass mineral crust, fine hatch shading, faint teal biolume sheen; BOTTOM LEFT kelp-mat — dark blue-green kelp and weed bed matted flat over seabed with engraved frond hatching; BOTTOM RIGHT shell-gravel-shallows — scattered shells, barnacle bits, pale gravel, faint teal bioluminescent glints in the grain.  
> Reference images: Image 1 is the exact shipped atlas layout and density precedent; Image 2 is the combined E10 worlds look anchor, use ONLY its right-side Sea Moon palette and marine grammar.  
> Composition/framing: exact orthographic top-down ground textures, four equal cells, edge-tileable on every outer and opposing edge, natural transitions at the central boundaries; NO drawn grid, cross, gutters, borders, dividing lines, labels, corner frames, or mirrored/duplicated cells. Fill the entire square.  
> Critical read: EVERY cell is WALKABLE EXPOSED LOW-TIDE TIDAL-SEABED GROUND. No open ocean, no lake, no pool, no water body, no wave surface, no horizon. Surface moisture may appear only as a subtle wet sheen. The reef is a hard solid crust; kelp is flattened into walkable ground.  
> Style/medium: Gold Rush house terrain art: warm engraved-frontier illustration, full-bleed edge-tileable ground tiles, no letters, no gore.  
> Color palette: E5 Deepwater echo — blue-green parchment ground with warm ochre, sepia and brown base showing through; brass-and-teal accents; restrained teal biolume glints; fine ink hatching. Layered engraved ripple/swell line grammar, never photoreal foam. This is world ground, NOT deep-ink space.  
> Constraints: four visually distinct cells readable at gameplay zoom; non-mirrored; no people, creatures, buildings, boats, weapons, firearms, text, numbers, logos, watermark.  
> Avoid: obvious cross seam, open water, waves, surf, foam spray, liquid pools, photorealism, neon glow, symmetry, repeated texture stamps.

### Sea Moon atlas — center-boundary correction

> Edit the just-generated Sea Moon 2×2 terrain atlas only to remove the obvious straight central cross/read-as-grid. Preserve the four exact tile identities, exact order, top-down walkable exposed seabed read, engraved E5 palette, all content, square framing, and fine detail. Blend the vertical and horizontal tile boundaries into irregular organic interlocking transitions so there is no ruler-straight line, gutter, grid, border, or cross, while each quadrant remains distinct and readable. Make opposing edges visually tileable. Do not add water bodies, waves, text, people, creatures, structures, boats, weapons, logos, or watermark. Keep the image otherwise unchanged. Gold Rush house terrain art: warm engraved-frontier illustration, full-bleed edge-tileable ground tiles, no letters, no gore.

### Sea Moon atlas — edge-tileability correction

> Use case: precise-object-edit  
> Asset type: square 1254×1254 runtime terrain atlas correction  
> Primary request: Edit Image 1 to make EACH of its four exact 627×627 terrain cells independently seamless and edge-tileable in both horizontal and vertical directions. Preserve the exact canvas, exact 2×2 equal-cell layout, exact cell order, orthographic walkable exposed-seabed read, four material identities, palette, organic internal quadrant transitions, engraved detail, and all canon constraints.  
> Critical correction: for EACH quadrant independently, make its LEFT edge continue naturally into its RIGHT edge and its TOP edge continue naturally into its BOTTOM edge when that one cell is repeated. Remove tonal border bands and mismatched motifs that cause repeat seams, especially in the reef-crust and shell-gravel cells. Opposing-edge color, luminance, texture density, ripple direction, object scale, and local motifs must join naturally. Do not mirror, clone, stamp, frame, or blur the cells. Preserve the irregular blended central transitions: no ruler-straight cross, grid, gutter, border, or separator.  
> Keep exact cells: TOP LEFT wet ridged tidal-flat sand; TOP RIGHT solid living reef crust; BOTTOM LEFT flattened kelp mat; BOTTOM RIGHT shell/barnacle/pale gravel shallows. Every cell remains WALKABLE EXPOSED LOW-TIDE SEABED, never open water, lake, pool, wave surface, shoreline, or foam.  
> Gold Rush house terrain art: warm engraved-frontier illustration, full-bleed edge-tileable ground tiles, no letters, no gore.  
> Constraints: no objects beyond ground material, structures, props, landmarks, sky, horizon, people, creatures, boats, weapons, firearms, text, letters, numbers, logos, watermark, neon, photorealism. Change only what is required for true wrap continuity.

### Sea Moon prop family

> Use case: stylized-concept  
> Asset type: Gold Rush runtime prop-family reference sheet, square 1254×1254 PNG.  
> Primary request: Create a FRESH full-bleed painted prop family for the uninhabited Sea Moon biome, “E5 under alien tides,” on one uniform plain warm parchment ground. Natural biome scatter only.  
> Reference images: Image 1 is the exact shipped prop-family layout, scale, generous spacing, warm plain-ground, and engraved quality precedent; Image 2 is the combined E10 worlds look anchor, use ONLY its right-side Sea Moon palette and marine shapes.  
> Required distinct prop types with generous breathing room and no overlap: (1) several standing coral and tube-sponge spires — branching teal-tinted marine columns risen from reef, organic and geological; (2) one cluster of cracked reef slabs/plates; (3) one scattered shell, barnacle, and pale gravel grouping; (4) one tall dark blue-green kelp-frond clump; (5) one encrusted boulder forming a shallow dry tide-pool basin, with restrained teal biolume only in its crevices.  
> Composition/framing: full-bleed square sheet; each prop or cluster complete and uncropped, three-quarter top-down game-art view, clearly separated, readable at 128px; plain warm parchment ground fills canvas, not checkerboard, not a keyed grid, no cell lines or labels.  
> Style/medium: Gold Rush house prop art: warm engraved-frontier illustration, full-bleed painted props on transparent-ready plain ground, no letters, no gore.  
> Color palette: E5 Deepwater echo — warm-to-blue-green engraved frontier; warm ochre, sepia, brown, blue-green, weathered brass tones, restrained teal biolume glints. Fine ink hatching and carved storybook contours; never photoreal.  
> Critical constraints: natural marine scatter only. NO great landmark tidal-works, NO dome, NO crane, NO diving bell, NO bathysphere, NO boats, NO buildings, NO built structures. No people, creatures, weapons, firearms, text, letters, numbers, logos, watermark. The only emitted light is restrained teal biolume accent, never neon.  
> Avoid: ocean scene, water surface, aquarium display, keyed grid, checkerboard, inventory UI, labels, excessive glow, mirrored or duplicated props, cropped silhouettes.

### Sea Moon landmark

> Use case: stylized-concept  
> Asset type: Gold Rush runtime authored landmark reference, square 1254×1254 PNG.  
> Primary request: Create a FRESH full-bleed single illustration of the Sea Moon’s one authored landmark: a great solitary weathered brass-and-teal tidal-works, an enigmatic ancient relic half-reclaimed by reef and barnacles. It is a monumental domed observation and diving station with a clearly mechanical crane arm hoisting a caged transparent glass bathysphere / diving-bell orb out over crazed exposed reef-crust seabed. Include guy cables, reef-encrusted pilings, round observation windows, one or two restrained warm lantern points, and the great alien moon low on the horizon.  
> Reference images: Image 1 is the primary design anchor. Match ONLY the dominant far-right Sea Moon domed tidal-works and its crane-hoisted caged orb, blue-green reef world, and giant moon. Image 2 is the shipped single-landmark framing, complete silhouette, engraved density, plain-ground and scale precedent only; do not copy its lightning collector subject.  
> Story read: ancient, passive observation / diving / tidal monument, older than known civilizations, purpose unexplained; weathered and half-reclaimed by living reef. Uninhabited.  
> Composition/framing: three-quarter oblique landmark view on a simple exposed reef-crust ground, square full-bleed illustration, the complete dome, crane, orb, cables and pilings uncropped with comfortable edge padding. Make the crane hook and caged glass diving bell unmistakable. The moon sits behind/above without obscuring the structure.  
> Style/medium: Gold Rush house landmark art: warm engraved-frontier illustration, full-bleed painted landmark on plain ground, no letters, no gore.  
> Color palette: E5 Deepwater echo — blue-green parchment and reef, warm ochre/sepia base, weathered brass diving gear, restrained teal instrument glow, deep-ink-blue accents, warm lantern points. Fine ink hatching, layered engraved swell/ripple grammar, storybook not photoreal; not the Ark’s deep-ink space palette.  
> Absolute canon constraint: this is NOT a weapon. NO barrel, muzzle, bore, gun form, cannon, projectile, aimed beam, target, crosshair, missile, or weapon emplacement. The long arm must visibly be a trussed lifting CRANE with cable, hook, and suspended caged bathysphere/diving bell, never a barrel. No people, creatures, boats, firearms, weapons, text, letters, numbers, logos, watermark.  
> Avoid: lighthouse, gun turret, antenna weapon, telescope cannon, open-ocean scene, horror, neon, photorealism, cropped landmark, keyed grid, checkerboard.

No processing, extraction, alpha work, resizing, runtime wiring, other E10 world art, Ark art, roster art, portraits, Pan art, icons, code, specs, e2e, or prior-era art was touched.

READY-FOR-GATES
