---
source: codex
project: Gold Rush
date: 2026-07-29
type: art-run
---

# art-gazette-first-issue — Greenhorn's Gazette issue-one engravings

## Result

Native Codex `image_gen` only; no Higgsfield, CLI image model, extraction, alpha processing, or runtime wiring. Seven full-bleed RGB PNGs landed at the exact requested paths:

- `assets/raw/gazette-panel-claim-goal.png`
- `assets/raw/gazette-panel-seams-gold.png`
- `assets/raw/gazette-panel-the-works.png`
- `assets/raw/gazette-panel-the-arms.png`
- `assets/raw/gazette-panel-freeing-fevered.png`
- `assets/raw/gazette-panel-town-serves.png`
- `assets/raw/gazette-masthead.png`

Native run directory: `019fab51-58ec-7ff2-97f5-a33f192c7ca3`.

Every generation and correction prompt included this sentence verbatim:

> engraved frontier newspaper illustration, warm sepia ink on parchment, fine crosshatching, the Gold Rush plate style — never photoreal, never gory, no letters or numerals in the image.

## Measured self-QA

The six tutorial panels are exactly 1672×941 RGB PNGs. The masthead is a deliberately shallow 1983×793 RGB strip. `#ff00ff` count is 0 in every file. Tesseract returned empty output for all seven; full-resolution visual review also found no credible letters, numerals, logos, captions, or watermarks.

All files were actually resized to 480px wide and viewed. Claim ring/countdown pips, seam/sluice, palisade/turret/beacon, Prospector pulse arm, recovering neighbor/helping hand, four town services, and crossed pan/pickaxe remain distinct at that size.

Palette measurement uses mean normalized `R-B` warmth. The repository's complete `plate-contract-*.png` set spans 0.049–0.353; all seven finals sit inside that plate range, retain `R>G>B`, and contain zero magenta-key pixels.

| File | Size | `R-B` | SHA-256 | Anchor | No letters / numerals | 480px read | Plate palette |
|---|---:|---:|---|---|---|---|---|
| `gazette-panel-claim-goal.png` | 1672×941 | 0.276 | `279767f530001168a8345d0a566a5095b432eb727537d15917f5421c164dc9e9` | PASS — sepia parchment + fine hatch | PASS — OCR empty + visual | PASS — ring, pips, incoming wave | PASS |
| `gazette-panel-seams-gold.png` | 1672×941 | 0.243 | `08390b6afa26f1cf7cc428bafb4b01bfbdcd707bac0ceee6a8fdd4f07ead24f1` | PASS — sepia parchment + fine hatch | PASS — OCR empty + visual | PASS — seam and sluice | PASS |
| `gazette-panel-the-works.png` | 1672×941 | 0.234 | `59551f23d2a5c9db6d6cf9194e28ac1fff485afa8760d23e920323ec54b2f034` | PASS — sepia parchment + fine hatch | PASS — OCR empty + visual | PASS — all three works | PASS |
| `gazette-panel-the-arms.png` | 1672×941 | 0.304 | `4b0bc1a3276e1a41d68cef81842cabc0d51b01fe74c29df71792097ac49c8c78` | PASS — sepia parchment + fine hatch | PASS — blank dial, clean targets, OCR empty | PASS — open-ring volley | PASS |
| `gazette-panel-freeing-fevered.png` | 1672×941 | 0.314 | `2755f444ae46d28a8dee66e1067e1878f3b3ed05d49605a76c02533e2b399c1a` | PASS — sepia parchment + fine hatch | PASS — OCR empty + visual | PASS — gold light leaves eyes, hand offered | PASS |
| `gazette-panel-town-serves.png` | 1672×941 | 0.320 | `85bedbea1132f03f56f5091c523fe2555a3c65bee97c6f0c047101fa5bae1ab5` | PASS — sepia parchment + fine hatch | PASS — blank board, pictogram-only chart, OCR empty | PASS — four services separate | PASS |
| `gazette-masthead.png` | 1983×793 | 0.333 | `d3ca6dbb0e4d3545de7345bda0985dee0a5708645c08dee7d9db1a4f3b98621d` | PASS — sepia parchment + fine hatch | PASS — OCR empty + visual | PASS — pan, pickaxe, river bend | PASS |

Canon review: no realistic firearms, gun barrels, muzzles, bullets, injury, blood, gore, or villain treatment of fevered neighbors. The Prospector's arm is an open-ring teal pulse emitter; the Works turret is an open lens; the Fevered subject is visibly being welcomed back.

`gazette-panel-the-arms.png` required two focused native corrections. The first candidate added faux dial/target glyphs and was rejected. Correction one cleaned the targets but left two dial-like glyphs. The changed-premise final replaced the entire dial interior with blank teal engraved glass and a brass hub. No failed take was landed.

## Prompt set

All first-pass prompts also required edge-to-edge 16:9 landscape art, no frame/border/title area, large silhouettes readable at 480px, warm parchment/sepia/brown with muted ochre-gold and restrained friendly-tech teal, no magenta, and no writing, logos, watermarks, firearms, gore, or photorealism.

1. **Claim and goal** — a dusk river claim inside a holding circular palisade, distant incoming trouble, and one blank pennant carrying only shrinking lantern-pip circles as the wave countdown.
2. **Seams give gold** — a bright glittering rock seam beside a timber sluice straddling running water, both equally legible.
3. **The Works** — one trail bend guarded by exactly three friendly works: low palisade, compact open-lens turret with no barrel, and tall beacon casting concentric watch rings.
4. **The Arms** — the round brass Prospector with teal dial, miner lamp, hover base, and jointed arm firing three expanding rings from a broad open-ring emitter with no tube, muzzle, grip, trigger, stock, ammunition, or gun silhouette.
5. **Freeing the Fevered** — an ordinary frontier neighbor softening mid-charge as harmless gold light leaves their eyes and an unarmed helping hand reaches toward them; victim recovering, never villain.
6. **The Town serves** — one welcoming plaza holding a blank tavern board, schoolhouse line-and-circle chart, tailor's wagon, and complaints desk with bell and unmarked bounty pouch.
7. **Masthead** — a shallow pan and frontier pickaxe crossed over a river bend, with reeds and two claim stakes; wide, simple, text-free, and designed for a shallow horizontal crop.

The two Arms correction prompts changed only the forbidden glyphs. Both repeated the required style anchor verbatim; the final correction required uninterrupted teal crosshatched glass with one central brass hub and no needle, ticks, pale marks, glyphs, letters, or numerals.

## Firewall

Generation and save only. No extraction, processed assets, source code, registry, Gazette JSON, UI, e2e, spec, or runtime wiring was touched. GG-03 owns the swap.
