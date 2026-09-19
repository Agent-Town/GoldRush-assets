---
source: codex
project: Gold Rush
date: 2026-07-20
type: reference
---

# E7 buildings and terrain batch A

## Result

Native Codex `image_gen` only. No Higgsfield still-image model was used. This run produced exactly the seven files assigned by `art-e7-buildings-terrain-a`; batch 2, roster art, and town icons were not started.

| File | Native job | Final size | SHA-256 | Retakes | Verdict |
|---|---|---:|---|---:|---|
| `bld-relay-tower.png` | `exec-de08d7c8-7d79-46c7-ab26-d99ab658b342` | 1254x1254 RGB | `9688b05e28e17cfdb35c5a1c80588adf765e53256e005918d2410f3804658fc4` | 0 | PASS |
| `bld-exchange.png` | `exec-72b995be-e64f-47fe-9b22-6542cf8a4322` | 1254x1254 RGB | `137bdc29f51f1d9944c0a33a4e3dceeadd6aaa0ed0a59dd7df83d14d39efdf1d` | 0 | PASS |
| `bld-playbook-library.png` | `exec-71c456cf-f8e9-4345-ad78-5804ba2cc863` | 1254x1254 RGB | `d635b8db9a19444b549f489f36e200af436226bf3b4516290566ad947f24c223` | 0 | PASS |
| `bld-drone-coop.png` | `exec-1c3a6264-dd5e-4c64-a659-61f8f4e29ae3` | 1254x1254 RGB | `c2295ea0cb535bca678f9d888b1d64063a09f0d776b2d7536a0fbf796a720e15` | 0 | PASS |
| `bld-signal-refinery.png` | `exec-0de2aad3-062b-4897-8dd4-9a4958feda13` | 1254x1254 RGB | `f151ba3a426a81df096c40c28f430b32032fec71642886795af042380124e309` | 0 | PASS |
| `ter-relay-valley-atlas.png` | `exec-16708966-b9df-4ed9-8810-f6876fa92846` | 1254x1254 RGB | `05187fa2056c45ca73e30d9b5fbd5485759fdd91439df81b962274f15970a087` | 0 | PASS |
| `prop-punch-tape-ribbons.png` | `exec-bc0d851c-be0f-4869-aa29-644626a9647f` | 1254x1254 RGB | `e96ea3c09490c20dc493c642ac5c32bf4f0615720b5dca2b8306cc6608d525d5` | 0 | PASS |

Native run directory: `019f8046-ba3a-7cf2-9775-2a47aa39df2f`.

## Measured self-QA

Visible-height ratios are the painted building bounds divided by canvas height, measured on the final files. The shipped E6 square-building references span roughly 72–91%; the E7 set remains in that gameplay band, with the Library's small roof finial reaching 93%.

| File | Silhouette reads | Palette in E7 | Height in band | Letters / firearms / gore none | Measured note |
|---|---|---|---|---|---|
| `bld-relay-tower.png` | Y | Y | Y | Y | 90%; dish, lattice, twin cells, console hut |
| `bld-exchange.png` | Y | Y | Y | Y | 83%; arched switchboard-hall mass |
| `bld-playbook-library.png` | Y | Y | Y | Y | 93%; peaked archive hall, blank cards, perforated tape |
| `bld-drone-coop.png` | Y | Y | Y | Y | 89%; four roosting helper-drone silhouettes |
| `bld-signal-refinery.png` | Y | Y | Y | Y | 91%; receiver → tube bank → teal accumulator |
| `ter-relay-valley-atlas.png` | Y | Y | Y (n/a atlas) | Y | exact 2x2; shale / loam / meadow / cable trench |
| `prop-punch-tape-ribbons.png` | Y | Y | Y (n/a prop) | Y | two reels, loose loops, coil; holes only |

All seven remain readable in a 128px contact pass. Full-size visual review found no letters, numbers, logos, watermarks, firearms, gore, people, or weapon-like signal rigs. OCR returned only nonsensical engraved-texture fragments, with no credible text visible. The palette stays in walnut, aged brass, honey-gold glass, cream tape, and teal agent-glow; no E6 chrome or pastel-enamel language is present.

## Final prompts

Every prompt included this exact task anchor:

> Gold Rush house building art: warm engraved-frontier illustration, full-bleed painted structure on transparent-ready plain ground, no letters, no gore.

### Relay Tower

A single Relay Tower building, the Signal Era pylon: tall brass-and-dark-walnut lattice mast with one unmistakable shallow relay dish, exactly two large glass relay cells visibly linked and searching, and a compact walnut console hut at the base. Antique Frontier Ledger illustration with fine sepia engraved linework and warm hand-painted color. One complete isolated structure in top-down three-quarter oblique game view, centered on plain warm parchment ground, no scenery or horizon, generous padding, uncropped, readable at 96px, and in the shipped square building-sheet band. Honey-gold vacuum-tube warmth with clear teal intelligence glow at the base and cells. Engraved concentric signal arcs around the dish read as signal/line-of-sight, never projectiles. References: `plate-e7-bld-relay-tower.png`, `bld-reactor-dome.png`, `kit-era-7.png`. No people, secondary tower, letters, numbers, labels, logos, watermark, firearms, barrels, muzzles, missiles, weapons, gore, chrome, pastel enamel, photorealism, black void, or busy landscape.

### The Exchange

A new distinct switchboard hall building descended from a frontier tavern annex: broad walnut hall with a strong arched roof silhouette, exterior switchboard bay, plug cords, looping perforated punch tape, teal sockets, and honey-gold glass vacuum tubes. Antique Frontier Ledger illustration with fine sepia engraved linework and warm hand-painted color. One complete isolated building in top-down three-quarter oblique game view, centered on plain warm parchment ground, no interior cutaway, street, or town, uncropped, readable at 96px, and in the shipped square building-sheet band. It reads first as a switchboard hall and remains distinct from a tavern. References: `plate-e7-bld-the-exchange.png`, `bld-isotope-kitchen.png`, `kit-era-7.png`. No people, drones, letters, numbers, printed tape, labels, logos, watermark, signage, firearms, weapons, gore, chrome, pastel enamel, photorealism, black void, or complex landscape.

### Playbook Library

A Playbook Library building: schoolhouse-lineage timber civic hall transformed into a compact card-catalog of punch tapes, with a recognizable peaked roof and small archive tower, exterior walnut catalog drawers, blank cards, perforated tape reels, honey-gold reading lamps, and teal helper-filing glow. Antique Frontier Ledger illustration with fine sepia engraved linework and warm hand-painted color. One complete isolated exterior building in top-down three-quarter oblique game view, centered on plain warm parchment ground, no interior cutaway or scenery, uncropped, readable at 96px, and in the shipped square building-sheet band. Every card is blank; every tape encodes only as round perforation holes; no glyph-like marks. References: `plate-e7-bld-playbook-library.png`, `bld-catalog-warehouse.png`, `kit-era-7.png`. No people, robots, writing, letters, numbers, equations, labels, logos, watermark, printed tape, firearms, weapons, gore, chrome, pastel enamel, photorealism, black void, or busy landscape.

### Drone Coop

An unmistakable frontier dovecote for small hover drones: compact walnut-and-brass towered coop with repeated open roost niches, three or four simple round hover-drone silhouettes visibly resting in niches, teal agent-glow under each drone, and warm honey-gold interior light. Antique Frontier Ledger illustration with fine sepia engraved linework and warm hand-painted color. One complete isolated building in top-down three-quarter oblique game view, centered on plain warm parchment ground, no yard scene, uncropped, readable at 96px, and in the shipped square building-sheet band. It reads first as a coop/dovecote, not a fortress; the drones are harmless compact helpers, not aircraft or weapons. References: `kit-era-7.png`, `bld-appliance-pen.png`. No people, birds, letters, numbers, labels, logos, watermark, firearms, guns, missiles, propellers, fighter aircraft, gore, chrome, pastel enamel, photorealism, black void, or busy landscape.

### Signal Refinery

A Signal Refinery building that visibly reads the spectrum and condenses it into usable SIGNAL: compact walnut industrial house with one broad receiving loop, a bank of honey-gold glass tuning tubes, engraved concentric signal arcs feeding through brass filters into a bright teal storage cell. Antique Frontier Ledger illustration with fine sepia engraved linework and warm hand-painted color. One complete isolated building in top-down three-quarter oblique game view, centered on plain warm parchment ground, no landscape or workers, uncropped, readable at 96px, and in the shipped square building-sheet band. The input-to-output path is clear; the refinery is a signal instrument, never a turret or weapon. References: `kit-era-7.png`, `bld-machine-shop.png`. No smokestacks, chemical tanks, letters, numbers, gauges with numerals, labels, logos, watermark, firearms, barrels, muzzles, weapons, gore, oil-refinery imagery, chrome, pastel enamel, photorealism, black void, or busy landscape.

### Relay Valley atlas

Exactly four equal edge-to-edge top-down terrain cells matching the shipped atlas layout: top-left weathered dark ridge shale with engraved fractures; top-right warm muted valley loam with fine dry grit; bottom-left dusty antenna meadow with sparse flattened straw and tiny restrained teal signal flecks; bottom-right an orderly cable-trench material with walnut sleepers, dark soil, brass cable edges, and thin teal conduit glow. Antique Frontier Ledger terrain illustration, engraved sepia linework, subtle aged-paper texture, muted warm colors. Exact clean 2x2 grid with no gutters, borders, labels, icons, focal objects, horizon, buildings, props, or perspective; consistent orthographic scale and upper-left lighting. References: `ter-glowmesa-atlas.png`, `kit-era-7.png`. No letters, numbers, logos, watermark, people, creatures, buildings, towers, firearms, gore, lush grass, bright chrome, pastel enamel, photorealism, or black void.

### Punch-tape ribbons

A compact arrangement of punch-tape ribbon props: two brass-and-walnut reels, several graceful looping cream-paper ribbons, and one neat loose coil. The tape carries only regular round perforation holes, with honey-gold paper light and restrained teal edge glow. Antique Frontier Ledger illustration with fine sepia engraved linework and warm hand-painted color. Isolated prop group in top-down three-quarter oblique game view on plain warm parchment ground, centered, complete, uncropped, readable at 96px, and square. References: `plate-e7-bld-playbook-library.png`, `plate-e7-bld-the-exchange.png`, `kit-era-7.png`. No printed marks, people, robots, buildings, scenery, letters, numbers, glyphs, barcodes, musical notation, labels, logos, watermark, firearms, weapons, gore, chrome, pastel enamel, photorealism, black void, or checkerboard.

No processing, extraction, resizing, runtime wiring, transforms, roster art, town portraits, icons, batch-2 props, or batch-2 buildings were performed.
