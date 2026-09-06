---
source: codex
project: Gold Rush
date: 2026-08-03
type: art-run
---

# Drill Yard station props

## Result

Native Codex `image_gen` only. The faucet station and straw target were accepted first takes; the bell was replaced after drain QA with two native retakes. No Higgsfield or CLI image model was used.

- Native run directory: `019fc71d-d003-7b53-8fe3-8608c4d62851`
- Reference: `assets/raw/plate-contract-e1-drill-yard.png`
- `prop-drill-faucet-station.png`: `exec-e8df3541-7143-49d2-8c1f-1957e78737df`
- `prop-drill-bell-post.png`: `exec-1b59e5ec-8583-4482-ba70-12715645fda6`
- `prop-straw-man-stand.png`: `exec-fe4f38e4-73d1-464c-9de0-5ea64ab98289`
- Retakes: 2 for the bell; the first retake was discarded because a rope segment still crossed open air below the bell

## Initial measured self-QA

| File | Dimensions / mode | SHA-256 | Mean luminance | Mean HSL saturation | Exact `#ff00ff` | 96px silhouette | Anchor / no-writing review |
|---|---|---|---:|---:|---:|---|---|
| `prop-drill-faucet-station.png` | 1254x1254 RGB | `a1b369afb2fa6fe2877640e9866d599d44c8f85339bcef09ea83966b6d3a531b` | 0.451 | 0.553 | 0 | PASS — table, scale, crank box | PASS |
| `prop-drill-bell-post.png` | 1254x1254 RGB | `9f84a436795b4db30a120d512d318034871fc9f426ab119ab02aaa4163215b54` | 0.551 | 0.553 | 0 | PASS — post, bell, rope | PASS |
| `prop-straw-man-stand.png` | 1254x1254 RGB | `b8e7bd2122beb7b15fd4edc10fdf10a6570615d06900e7638fe7911a0c7dd097` | 0.525 | 0.615 | 0 | PASS — straw bundle, broad braced base | PASS |

Reference plate: mean luminance 0.455; mean HSL saturation 0.507. The three props remain in the warm sepia/umber plate range. OCR returned dense-hatching false positives only; full-size inspection found no visible letters, numerals, pseudo-writing, logos, watermarks, firearms, gore, or people. The straw target matches the shipped cylindrical tied-bundle silhouette and does not read as human anatomy.

## Prompts

### County assay table

```text
Use case: stylized-concept
Asset type: Gold Rush gameplay prop plate
Primary request: Create one isolated county assay table that visually communicates “draw practice gold here” without any writing: a sturdy timber trestle table, a readable aged-brass gold balance scale, a small walnut strongbox with a prominent hand-crank lever, and one closed blank ledger book.
Reference image: use the supplied Drill Yard contract plate only as the style, palette, camera-angle, and object-language reference.
Style/medium: engraved frontier illustration, warm sepia and umber, painted-storybook game prop, the Gold Rush plate style — never photoreal, no letters or numerals.
Composition/framing: single complete prop, centered and uncropped, elevated three-quarter gameplay view, bold clean silhouette readable at 96px, generous padding, square full-bleed warm parchment-and-dirt ground with no frame or border.
Palette/materials: walnut timber, aged brass, cream paper, warm sepia/umber linework, one restrained teal agent-tech accent only.
Constraints: the strongbox lever is unmistakably hand-operated and the scale pans are clearly visible; all pages, covers, plates, and surfaces are completely blank. No people, coins with marks, text, letters, numerals, pseudo-writing, labels, signs, logos, watermark, firearms, weapons, gore, photorealism, magenta, decorative border, or additional scenery.
```

### Drill bell

```text
Use case: stylized-concept
Asset type: Gold Rush gameplay prop plate
Primary request: Create one isolated Drill Yard bell station: a stout upright timber post with a short overhanging timber arm, one large hanging bronze bell, visible clapper, and a simple pull-rope ending in a loop.
Reference image: use the supplied Drill Yard contract plate only as the style, palette, camera-angle, and object-language reference.
Style/medium: engraved frontier illustration, warm sepia and umber, painted-storybook game prop, the Gold Rush plate style — never photoreal, no letters or numerals.
Composition/framing: single complete station, centered and uncropped, elevated three-quarter gameplay view, strong instantly readable bell silhouette at 96px, generous padding, square full-bleed warm parchment-and-dirt ground with no frame or border.
Palette/materials: dark walnut post, aged bronze bell, hemp rope, warm sepia/umber engraved linework, restrained highlights.
Constraints: friendly civil practice bell, not an alarm weapon or gallows; no people, bodies, extra buildings, text, letters, numerals, pseudo-writing, labels, signs, logos, watermark, firearms, weapons, gore, photorealism, magenta, decorative border, or additional scenery.
```

### Straw target

```text
Use case: stylized-concept
Asset type: Gold Rush gameplay prop plate
Primary request: Create one isolated inanimate Drill Yard straw target matching the supplied contract plate: a thick upright cylindrical bundle of cut golden straw bound by three plain ropes, mounted on a broad crossed-timber freestanding base with diagonal braces. It is training equipment, not a person.
Reference image: use the supplied Drill Yard contract plate as the binding silhouette, style, palette, camera-angle, and object-language reference.
Style/medium: engraved frontier illustration, warm sepia and umber, painted-storybook game prop, the Gold Rush plate style — never photoreal, no letters or numerals.
Composition/framing: single complete target and base, centered and uncropped, elevated three-quarter gameplay view, chunky readable silhouette at 96px, generous padding, square full-bleed warm parchment-and-dirt ground with no frame or border.
Palette/materials: golden straw, walnut crossed-timber stand, hemp rope, warm sepia/umber engraved linework.
Constraints: preserve the simple cylindrical bundle and broad braced base; no head, face, limbs, clothes, hat, human anatomy, scarecrow, effigy, victim, hanging imagery, people, text, letters, numerals, pseudo-writing, labels, signs, logos, watermark, firearms, weapons, gore, photorealism, magenta, decorative border, or additional scenery.
```

## Bell retake — 2026-08-04

- Native run directory: `019fc8c5-9ee4-7821-a4c9-0c28dd720562`
- First retake, discarded: `exec-1d4a0396-ecb2-4ee0-ad02-4c8e98337f78`
- Final retake: `exec-3cc34983-2cfe-417a-9d71-15c3cf0d57ca`

### Measured self-QA

| File | Dimensions / mode | SHA-256 | Mean luminance | Mean HSL saturation | Exact `#ff00ff` | 96px silhouette | Anchor / no-writing review |
|---|---|---|---:|---:|---:|---|---|
| `prop-drill-bell-post.png` | 1254x1254 RGB | `56236ca0ee22555857f113388aa82e9387782c6e30062272e19406d245653399` | 0.508 | 0.568 | 0 | PASS — compact two-post yoke and centered bell | PASS |

Reference plate luminance is 0.455 and saturation is 0.507. The retake's luminance is 0.053 above the plate and between the accepted siblings' 0.451 and 0.525; its saturation is between their 0.553 and 0.615. OCR returned no text, and full-size review found no letters, numerals, pseudo-writing, logos, watermarks, firearms, weapons, gore, people, bodies, or magenta.

**Gallows check:** At 96px, a stranger reads a compact freestanding bronze bell centered in a rectangular two-post wooden yoke with two braced feet.

The hemp rope begins, remains, and terminates as a tight coil tied flat around the cleat on the right upright. No rope crosses open air, hangs below the bell, or ends in a free loop. The bell's clapper remains visible and unconnected to the rope.

Side by side with the accepted faucet station and straw target, the retake reads as the same set: matching engraved line weight, warm parchment-and-dirt ground, elevated three-quarter view, generous padding, and sturdy walnut/brass material weight.

### Final prompt

```text
Use case: precise-object-edit
Asset type: Gold Rush gameplay prop plate
Primary request: Edit Image 1 only to remove the exposed horizontal hemp rope segment that currently runs from the bell clapper across open air to the right upright. Keep the visible bronze clapper intact and completely unconnected to any rope. Keep a small, tidy coil of hemp rope tied flat around the wooden cleat on the right upright, but the entire rope must begin, remain, and terminate against that upright: no rope reaches toward the bell, no rope crosses any open gap, no rope hangs below the bell, and no free loop or dangling end exists.
Input images: Image 1 is the edit target. Images 2 and 3 are accepted sibling references for visual weight, ground treatment, padding, and set cohesion.
Preserve exactly: the compact symmetric two-upright yoke, short non-projecting top crossbar, centered aged-bronze bell, visible clapper, dark walnut supports and braced feet, elevated three-quarter view, full-bleed warm parchment-and-dirt ground, engraved frontier finish, palette, lighting, scale, generous padding, and all other composition.
Style/medium: engraved frontier illustration, warm sepia and umber, painted-storybook game prop, the Gold Rush plate style — never photoreal, no letters or numerals.
Hard constraints: no one-sided post, cantilever, projecting beam, scaffold shape, rope in open air, dangling cord, terminal loop, loop-shaped rope, people, bodies, text, letters, numerals, pseudo-writing, labels, signs, logos, watermark, firearms, weapons, gore, hanging imagery, photorealism, magenta, border, or additional scenery.
```

No processing, extraction, resizing, runtime wiring, source edit, spec edit, test edit, or commit was performed.

## KEYED — 2026-08-04

The faucet and straw files were **EDITED** from their accepted images with native Codex `image_gen`. The bell was **REGENERATED** from its accepted image as the binding visual reference after both background-edit attempts enlarged its frame enough to fail the task's unprimed 96px gallows check. Native outputs rendered visually flat magenta but not byte-flat `#ff00ff`, so the raws received the same deterministic near-key normalization used by keyed sprite sheets: `magick <file> -fuzz 25% -fill '#ff00ff' -opaque '#ff00ff' <file>`. No alpha extraction, resizing, processed asset, source edit, test edit, runtime wiring, or commit was performed.

- Native run directory: `019fc8fa-eace-7522-a0dd-94486fbf5554`
- Faucet edit: `exec-6fd91c5c-4ff4-4301-86a2-9304b139e347`
- Straw-target edit: `exec-3a7c94cc-ecbb-48eb-8eb2-555d5ea5480e`
- Bell first keyed edit, discarded for enlarging the subject: `exec-d5c00809-1f78-455a-815b-c7aded488f98`
- Bell second keyed edit, discarded after the unprimed 96px gallows check: `exec-05eadf24-5b0f-4e08-8af7-080f629f9b89`
- Bell fallback regeneration, accepted candidate: `exec-4dbcd439-1745-4c62-acfa-51b0c15b3371`

### Measured keyed self-QA

| File | Dimensions / mode | SHA-256 | Border RGB min | Border RGB max | Border spread | Exact `#ff00ff` | Key coverage |
|---|---|---|---|---|---|---:|---:|
| `prop-drill-faucet-station.png` | 1254x1254 RGB | `a367d192449109bd9d25c148150ada185d4f85c73fdba25bdbee27f85f209740` | `255,0,255` | `255,0,255` | `0,0,0` | 949,360 | 60.3720% |
| `prop-straw-man-stand.png` | 1254x1254 RGB | `3a4f6308e166609d4a63fc62832ffe2c4334a6e3cb50861c1203b8ddabf09639` | `255,0,255` | `255,0,255` | `0,0,0` | 1,222,187 | 77.7218% |
| `prop-drill-bell-post.png` | 1254x1254 RGB | `54ec0bdf27750e475466fb2bd8d917d9df6a168cfab29cf5de88271d01c8725a` | `255,0,255` | `255,0,255` | `0,0,0` | 1,174,778 | 74.7069% |

The outermost row and column on every side were measured separately; every edge has min=max `255,0,255`. Full-size visual inspection found no magenta on any subject. Deliberately keyed enclosed/open pockets are: the gaps beneath and between the faucet table legs and braces, behind and between the scale chains and pans, and around the crank; every triangular and rectangular opening inside the straw stand's base and braces; and the bell yoke's full center opening, the space below the bell, and both brace gaps.

**Subject comparison — faucet:** Side by side at full 1254px size, the sturdy table, balance, crank strongbox, blank ledger, engraved geometry, and warm walnut/brass/teal palette remain the same drawing; only the ground is now keyed.

**Subject comparison — straw target:** Side by side at full 1254px size, the cylindrical three-rope straw bundle, broad crossed base, diagonal braces, engraved geometry, and warm straw/walnut palette remain the same drawing; only the ground is now keyed. It still has no head, face, limbs, clothes, hat, or human anatomy.

**Subject comparison — bell:** The accepted image remained the binding visual reference, but this file used the allowed fallback regeneration after two keyed edits failed the gallows check. The replacement preserves its compact symmetric two-upright construction, short flush crossbar, centered bronze bell and clapper, tight upright-bound rope coil, braced feet, engraved finish, and warm walnut/bronze palette while lowering the frame and making the bell dominate the 96px silhouette.

**Gallows check:** At 96px, a stranger reads a large bronze bell in a low, broad-footed civilian bell cradle. The bell fills the frame, the short top bar terminates at both uprights, the rope is a tight coil against the right post, and there is no projecting beam, long scaffold leg, rope in open air, terminal loop, gallows, noose, or hanging-body read.

**Canon check:** PASS — no people, firearms, weapons, gore, letters, numerals, pseudo-writing, logos, or watermarks. The straw target remains wholly inanimate and non-anatomical.

**Set verdict:** PASS — beside `plate-contract-e1-drill-yard.png`, all three retain one engraved warm sepia/umber set, elevated three-quarter camera, heavy timber construction, restrained brass/teal accents, and bold gameplay-scale silhouettes.

### Exact keyed edit prompt — county assay table

```text
Use case: precise-object-edit
Asset type: Gold Rush in-world gameplay prop chroma-key source
Input images: Image 1 is the edit target; Image 2 is the background-treatment reference only.
Primary request: Edit Image 1 only. Replace only the square full-bleed warm parchment-and-dirt ground with one perfectly flat, uniform solid #ff00ff field, matching Image 2's exact background treatment. Preserve every subject pixel and visual property of Image 1: the complete county assay table, sturdy timber trestle table, readable aged-brass gold balance scale with both pans and chains, small walnut strongbox with prominent hand-crank lever, closed blank ledger book, geometry, proportions, linework, palette, highlights, shading, camera angle, scale, placement, and bold 96px-readable silhouette. Do not redraw, reinterpret, simplify, add, remove, resize, crop, recolor, or move the prop.
Style/medium: engraved frontier illustration, warm sepia and umber, painted-storybook game prop, the Gold Rush plate style — never photoreal, no letters or numerals.
Composition/framing: retain the elevated three-quarter gameplay camera and generous padding on all four sides. The outermost pixel ring must be exactly uniform #ff00ff. Key every true background opening, including open space between and beneath table legs and braces, behind and between the scale chains and pans, and around the crank, while preserving the opaque prop and its internal materials.
Hard constraints: background is exact solid #ff00ff with no texture, shadows, gradients, floor plane, parchment, dirt, scenery, halo, fringe, magenta rim-light, or magenta bounce. No #ff00ff on the subject. No people, coins with marks, text, letters, numerals, pseudo-writing, labels, signs, logos, watermark, firearms, weapons, gore, photorealism, decorative border, or additional scenery. Output square 1254x1254 RGB or RGBA.
```

### Exact keyed edit prompt — straw target

```text
Use case: precise-object-edit
Asset type: Gold Rush in-world gameplay prop chroma-key source
Input images: Image 1 is the edit target; Image 2 is the background-treatment reference only.
Primary request: Edit Image 1 only. Replace only the square full-bleed warm parchment-and-dirt ground with one perfectly flat, uniform solid #ff00ff field, matching Image 2's exact background treatment. Preserve every subject pixel and visual property of Image 1: the complete isolated inanimate Drill Yard straw target, thick upright cylindrical bundle of cut golden straw bound by three plain ropes, broad crossed-timber freestanding base with diagonal braces, geometry, proportions, linework, palette, highlights, shading, camera angle, scale, placement, and bold 96px-readable silhouette. Do not redraw, reinterpret, simplify, add, remove, resize, crop, recolor, or move the prop.
Style/medium: engraved frontier illustration, warm sepia and umber, painted-storybook game prop, the Gold Rush plate style — never photoreal, no letters or numerals.
Composition/framing: retain the elevated three-quarter gameplay camera and generous padding on all four sides. The outermost pixel ring must be exactly uniform #ff00ff. Key every true background opening, including all open triangular and rectangular spaces between the crossed base rails, uprights, and diagonal braces, while preserving the opaque straw, rope, and timber.
Hard constraints: preserve the simple cylindrical bundle and broad braced base; no head, face, limbs, clothes, hat, human anatomy, scarecrow, effigy, victim, or hanging imagery. Background is exact solid #ff00ff with no texture, shadows, gradients, floor plane, parchment, dirt, scenery, halo, fringe, magenta rim-light, or magenta bounce. No #ff00ff on the subject. No people, text, letters, numerals, pseudo-writing, labels, signs, logos, watermark, firearms, weapons, gore, photorealism, decorative border, or additional scenery. Output square 1254x1254 RGB or RGBA.
```

### Exact keyed edit prompts — drill bell

First edit (discarded because it enlarged the accepted subject):

```text
Use case: precise-object-edit
Asset type: Gold Rush in-world gameplay prop chroma-key source
Input images: Image 1 is the edit target; Image 2 is the background-treatment reference only.
Primary request: Edit Image 1 only. Replace only the square full-bleed warm parchment-and-dirt ground with one perfectly flat, uniform solid #ff00ff field, matching Image 2's exact background treatment. Preserve every subject pixel and visual property of Image 1: the compact symmetric two-upright yoke, short non-projecting top crossbar, centered aged-bronze bell, visible clapper, rope coiled tight against the upright, dark walnut supports and braced feet, geometry, proportions, linework, palette, highlights, shading, camera angle, scale, placement, and bold 96px-readable silhouette. Do not redraw, reinterpret, simplify, add, remove, resize, crop, recolor, or move the prop.
Style/medium: engraved frontier illustration, warm sepia and umber, painted-storybook game prop, the Gold Rush plate style — never photoreal, no letters or numerals.
Composition/framing: retain the elevated three-quarter gameplay camera and generous padding on all four sides. The outermost pixel ring must be exactly uniform #ff00ff. Key every true background opening, especially the complete enclosed rectangular opening framed by the two uprights, short crossbar, bell, and feet, plus open spaces between all braces, while preserving the opaque bell, clapper, wood, and tight rope coil.
Hard constraints: no one-sided post, cantilever, projecting beam, scaffold shape, rope in open air, dangling cord, terminal loop, loop-shaped rope, or hanging imagery. Background is exact solid #ff00ff with no texture, shadows, gradients, floor plane, parchment, dirt, scenery, halo, fringe, magenta rim-light, or magenta bounce. No #ff00ff on the subject. No people, bodies, text, letters, numerals, pseudo-writing, labels, signs, logos, watermark, firearms, weapons, gore, photorealism, decorative border, or additional scenery. Output square 1254x1254 RGB or RGBA.
```

Second edit (discarded after the unprimed 96px gallows check):

```text
Use case: precise-object-edit
Asset type: Gold Rush in-world gameplay prop chroma-key source
Input images: Image 1 is the sole edit target.
Primary request: Change only Image 1's background. Replace the full-bleed warm parchment-and-dirt ground with a perfectly flat solid #ff00ff field. Preserve the existing bell station exactly as drawn and at exactly its current size and position: its subject envelope stays approximately x=250..1028 and y=189..1094 on the 1254x1254 canvas, with the same generous top and side padding. Do not enlarge, shrink, shift, redraw, recompose, or restyle any part of it.
Preserve exactly: compact symmetric two-upright yoke, short non-projecting top crossbar, centered aged-bronze bell, visible clapper, rope coiled tight against the right upright, dark walnut supports, both braced feet, every engraved line, geometry, proportion, color, highlight, shadow, elevated three-quarter camera, and bold 96px-readable silhouette.
Style/medium: engraved frontier illustration, warm sepia and umber, painted-storybook game prop, the Gold Rush plate style — never photoreal, no letters or numerals.
Key every true background opening, especially the complete opening framed by the two uprights and crossbar, the open area below the bell, and gaps around both braces. The outermost ring must be flat #ff00ff.
Hard constraints: compact symmetric two-upright yoke, short non-projecting top crossbar, centered aged-bronze bell, visible clapper, rope coiled tight against the upright; no one-sided post, cantilever, projecting beam, scaffold shape, rope in open air, dangling cord, terminal loop, loop-shaped rope, or hanging imagery. No magenta rim light, bounce, fringe, or magenta on the subject. No people, text, letters, numerals, pseudo-writing, labels, signs, logos, watermark, firearms, weapons, gore, photorealism, decorative border, or additional scenery. Output square 1254x1254 RGB or RGBA.
```

### Exact fallback regeneration prompt — drill bell

```text
Use case: stylized-concept
Asset type: Gold Rush in-world gameplay prop chroma-key source
Input images: Image 1 is the binding visual reference for subject identity, engraved finish, palette, elevated three-quarter camera, and safe rope treatment.
Primary request: Regenerate one isolated Drill Yard bell station on a perfectly flat solid #ff00ff field. Preserve the accepted reference's recognizable aged-bronze bell, visible clapper, dark walnut material, braced freestanding construction, engraved detail, warm palette, and tight rope coil fixed to the right upright, but make the overall silhouette unmistakably a compact civilian bell cradle rather than a tall frame: low and squat, the large bell fills most of the opening, very short uprights, broad close-set feet, almost no empty vertical space above or below the bell, and no long scaffold-like legs. Keep generous flat-key padding on all four sides and a bold readable silhouette at 96px.
Style/medium: engraved frontier illustration, warm sepia and umber, painted-storybook game prop, the Gold Rush plate style — never photoreal, no letters or numerals.
Composition/framing: centered and uncropped, elevated three-quarter gameplay view, square 1254x1254 RGB or RGBA. Background and every true opening around the bell, clapper, uprights, feet, and braces must be a single perfectly uniform exact #ff00ff with no texture, shadows, gradients, floor, or scenery. The outermost pixel ring must be exact #ff00ff.
Bell constraints: compact symmetric two-upright yoke, short non-projecting top crossbar, centered aged-bronze bell, visible clapper, rope coiled tight against the upright; no one-sided post, cantilever, projecting beam, scaffold shape, rope in open air, dangling cord, terminal loop, loop-shaped rope, or hanging imagery.
All constraints: no people, text, letters, numerals, pseudo-writing, labels, signs, logos, watermark, firearms, weapons, gore, photorealism, decorative border, or additional scenery. No magenta rim-light, magenta bounce, halo, or #ff00ff on the subject.
```
