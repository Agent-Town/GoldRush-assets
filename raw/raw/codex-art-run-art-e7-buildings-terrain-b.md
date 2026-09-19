---
source: codex
project: Gold Rush
date: 2026-07-21
type: reference
---

# E7 buildings and terrain batch B

## Result

Native Codex `image_gen` only. No Higgsfield still-image model was used. This run produced exactly the six files assigned by `art-e7-buildings-terrain-b`; no processing, wiring, roster, town-icon, or later-era work was started.

| File | Native final job | Final size | SHA-256 | Retakes | Verdict |
|---|---|---:|---|---:|---|
| `prop-dish-clusters.png` | `exec-a936807f-650b-4889-9a67-d97a3e2774aa` | 1254x1254 RGB | `f6bd5cb4536b01e18a0a77f74517b77a3aff59c001772727e134e27cc4f999ff` | 0 | PASS |
| `prop-dead-zone-markers.png` | `exec-c20c8f77-704c-4264-844e-d9390d042f64` | 1254x1254 RGB | `1a533673bb2918ae53651fca396fc5530c912cbc30b5b7407629ff269505c06a` | 0 | PASS |
| `bld-tavern-e7.png` | `exec-795cadf4-b213-4436-a9e0-143fbc88262a` | 1254x1254 RGB | `4d298bd190f2e335c8b9fd28abd45a53577f52c2fa8d31fb7e4714a949e7fd2b` | 0 | PASS |
| `bld-signal-turret-e7.png` | `exec-b30da56f-fd41-4fc1-b6f8-dd52f734c389` | 1254x1254 RGB | `8fffe210b3e79961fcf23e893ba481fda58dd28305dbc0f707560b72e1f6fcfa` | 1 | PASS |
| `bld-schoolhouse-e7.png` | `exec-b0766896-9170-4da2-9032-5578af8bb8be` | 1254x1254 RGB | `151ffc3fbf1561fe53efda6c9047901be843c60a881c43ea065a4a6faea6db36` | 1 | PASS |
| `bld-rail-depot-e7.png` | `exec-3f6ddfbc-b7b4-4719-95b3-427338c0c278` | 1254x1254 RGB | `3c3f691a5e1420afd79a1474727a40b7a4ce38dd2f9acd3dd87794c4b789e226` | 0 | PASS |

Native run directory: `019f80d7-0f17-7080-8033-025be798dc94`.

## Measured self-QA

Source ratios compare the final visible width and height bands with the named edit source. They are approximate normalized-bounds measurements from the full-size source/final pairs; the props have no transform source. All six also passed a 128px contact-sheet read and returned empty OCR output.

| File | Silhouette reads | Palette in E7 | Footprint matches source | Letters / firearms / gore none | Source ratio and measured note |
|---|---|---|---|---|---|
| `prop-dish-clusters.png` | Y | Y | Y (n/a fresh prop) | Y | Three parabolic receivers, honey-gold mesh, walnut posts, teal filaments; broadcast gear only |
| `prop-dead-zone-markers.png` | Y | Y | Y (n/a fresh prop) | Y | Three posts, two cairns, rope/chain boundary; struck-through concentric-arc pictograms only |
| `bld-tavern-e7.png` | Y | Y | Y | Y | `bld-tavern-e6.png`: ~1.00x W / 1.00x H; same two-storey Tavern, porch, annex, stairs, chimney |
| `bld-signal-turret-e7.png` | Y | Y | Y | Y | `bld-signal-turret-e6.png`: ~0.99x W / 0.98x H; same trestle, platform, ladder, mast and circular ring; complete feet with padding |
| `bld-schoolhouse-e7.png` | Y | Y | Y | Y | `bld-schoolhouse-e6.png`: ~1.01x W / 0.99x H; same schoolhouse, porch, roof and tower; aerial held below source finial height |
| `bld-rail-depot-e7.png` | Y | Y | Y | Y | `bld-rail-depot.png`: ~1.04x W / 1.02x H; same depot, canopy, platform, rail stub, clerestory and chimney |

Full-size visual review found no letters, numbers, logos, watermarks, firearms, gore, people, chrome, pastel enamel, or weapon-like Signal rigs. The turret and dishes read as receive/broadcast instruments; signal is shown as concentric arcs, never projectiles. Schoolhouse and depot tape is perforation-holes-only. The finals remain complete, uncropped, and in the shipped E6/E7 square-building band.

## Final prompts

Every initial prompt and both targeted corrections included this exact task anchor:

> Gold Rush house building art: warm engraved-frontier illustration, full-bleed painted structure on transparent-ready plain ground, no letters, no gore.

### Dish clusters

Create a small cluster of three frontier signal dishes and parabolic relay antennas on short walnut posts. The cluster is clearly receiving and broadcasting gear, never weaponry. Use aged brass frames, honey-gold perforated mesh dishes, dark walnut bases, restrained teal agent-glow filaments, and engraved concentric signal arcs around one dish. Antique Frontier Ledger illustration with fine sepia engraved linework, subtle aged-paper texture, warm hand-painted color, top-down three-quarter oblique game view. One compact isolated prop cluster, centered, complete, uncropped, generous padding, readable at 96px, on plain warm parchment ground with no horizon or scenery. E7 Signal Era walnut, aged brass, honey-gold glass and mesh, teal agent-glow; no chrome or pastel enamel. No people, buildings, labels, letters, numbers, logos, watermark, firearms, barrels, muzzles, missiles, ammunition, weapons, projectiles, gore, chrome, pastel enamel, photorealism, black void, or checkerboard.

### Dead-zone markers

Create a compact group of frontier warning markers defining a signal dead-zone: three weathered walnut posts and two low stone cairns joined by slack aged-brass chain or rope. Each post carries a blank metal pictogram plate showing only a simple struck-through concentric-arc no-signal glyph, with no writing. Add faint restrained teal signal glow that visibly stops at the boundary. Antique Frontier Ledger illustration with fine sepia engraved linework, subtle aged-paper texture, warm hand-painted color, top-down three-quarter oblique game view. One compact isolated marker group, centered, complete, uncropped, generous padding, readable at 96px, on plain warm parchment ground with no horizon, landscape, or fog bank. E7 Signal Era walnut, aged brass, honey-gold highlights, restrained teal agent-glow; no chrome or pastel enamel. No people, buildings, readable signs, writing, letters, numbers, logos, watermark, firearms, barrels, muzzles, ammunition, weapons, gore, chrome, pastel enamel, photorealism, black void, or checkerboard.

### Net Café transform

Edit target `bld-tavern-e6.png`; palette reference `bld-exchange.png`. Transform the E6 tavern into the E7 Signal Era Net Café skin. Preserve the exact same two-storey tavern mass, arched front gable, balconies, porch, stairs, side annex, chimney, camera angle, scale, footprint, padding, and overall outer silhouette. Replace chrome and pastel enamel with dark walnut, aged brass, honey-gold window glass, and restrained teal agent-glow. Add small blank terminal boxes inside the existing booth/window bays and one low shallow rooftop relay dish/aerial that stays below the chimney top and reads as signal reception, not a barrel. Keep the familiar tavern/jukebox lineage visible without any text. Antique Frontier Ledger illustration with fine sepia engraved linework, subtle aged-paper texture, warm hand-painted color. Keep the source top-down three-quarter oblique view and gameplay size band; isolated on plain warm parchment ground, complete and uncropped. Change only era materials and small Signal fittings. No people, signage, writing, letters, numbers, logos, watermark, firearms, barrels, muzzles, missiles, weapons, projectiles, gore, chrome, pastel enamel, photorealism, black void, extra buildings, or scenery.

### Beam-relay Turret transform

Edit target `bld-signal-turret-e6.png`; palette reference `bld-relay-tower.png`. Transform the E6 signal turret into the E7 Beam-relay Turret, a pure receiving/broadcast instrument. Preserve the exact four-leg timber trestle, square platform, central mast, ladder, circular ring/dish envelope, camera angle, scale, footprint, padding, and overall outer silhouette. Repaint it in dark walnut, aged brass, honey-gold glass relay cells, and restrained teal agent-glow. Make the top assembly an unmistakable shallow relay dish and concentric-arc emitter inside the same circular envelope, with engraved concentric signal arcs floating around it. It broadcasts and relays; it does not shoot. Antique Frontier Ledger illustration with fine sepia engraved linework, subtle aged-paper texture, warm hand-painted color. Keep the source top-down three-quarter oblique view and gameplay size band; isolated on plain warm parchment ground, complete and uncropped. No people, buildings, writing, letters, numbers, logos, watermark, firearms, gun forms, barrels, muzzles, cannons, scopes, missiles, ammunition, weapons, projectiles, gore, chrome, pastel enamel, photorealism, black void, or scenery.

Targeted correction: keep the E7 Beam-relay Turret design unchanged, but scale the complete structure down uniformly about 7 percent and recenter it vertically so all four timber feet are fully visible with warm parchment padding below them. Restore any clipped foot tips from the E6 source. Keep the top circular relay dish and engraved concentric signal arcs, trestle, relay cells, ladder, platform, orientation, and signal-instrument reading. Framing correction only; no barrel or weapon form.

### Signal Works / Tape-post transform

Edit target `bld-schoolhouse-e6.png`; palette reference `bld-playbook-library.png`. Transform the E6 schoolhouse into the E7 Signal Works / Tape-post skin. Preserve the exact schoolhouse mass, single steep roof, front porch and stairs, small square bell/clock tower envelope, side wall, camera angle, scale, footprint, padding, and overall outer silhouette. Replace chrome and pastel enamel with dark walnut, aged brass, honey-gold windows, and restrained teal agent-glow. Add a small aerial contained within the existing tower height and a few cream punch-tape ribbons feeding through exterior brass reels. Every tape shows round perforation holes only; any cards or plates are completely blank. Antique Frontier Ledger illustration with fine sepia engraved linework, subtle aged-paper texture, warm hand-painted color. Keep the source top-down three-quarter oblique view and gameplay size band; isolated on plain warm parchment ground, complete and uncropped. No people, printed marks, writing, letters, numbers, equations, barcodes, musical notation, labels, logos, watermark, firearms, barrels, muzzles, weapons, projectiles, gore, chrome, pastel enamel, photorealism, black void, extra buildings, or scenery.

Targeted correction: keep the first E7 Signal Works image unchanged except shorten and lower the thin rooftop aerial so no part rises above the E6 source's original gold ball finial height. Retain the dark walnut, aged brass, honey-gold windows, teal agent-glow, punch-tape reels, schoolhouse mass, roof, porch, stairs, footprint, orientation, camera angle, and padding. Punch tape remains holes-only. One targeted change only.

### Relay-depot transform

Edit target `bld-rail-depot.png`; palette reference `bld-exchange.png`. Transform the base rail depot directly into its E7 Signal Era tape-post / relay-depot skin. Preserve the exact long depot mass, gabled roof, platform canopy, front steps, rail stub, roof clerestory, chimney, small roof signal post, camera angle, scale, footprint, padding, and overall outer silhouette. Repaint the building in dark walnut, aged brass, honey-gold window glass, and restrained teal agent-glow. Convert the existing small roof signal post into a compact concentric-arc relay aerial within the same height and width envelope; add subtle brass signal conduits and one blank perforated tape parcel box on the platform. Tape is holes-only with no writing. Antique Frontier Ledger illustration with fine sepia engraved linework, subtle aged-paper texture, warm hand-painted color. Keep the source top-down three-quarter oblique view and gameplay size band; isolated on plain warm parchment ground, complete and uncropped. No people, printed tape, writing, letters, numbers, labels, logos, watermark, firearms, gun forms, barrels, muzzles, missiles, weapons, projectiles, gore, chrome, pastel enamel, photorealism, black void, extra buildings, or landscape.

No processing, extraction, resizing, runtime wiring, roster art, town portraits, icons, or later-era art was performed.
