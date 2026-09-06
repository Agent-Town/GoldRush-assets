---
source: codex
project: Gold Rush
date: 2026-07-20
type: reference
---

# Art batch 029 — E6-E7 contract plates

## Result

Native Codex `image_gen` only. No Higgsfield still-image model was used. Eight raw full-bleed contract-board plates landed at the exact requested paths in `assets/raw/`; no extraction, resizing, processing, or runtime integration was performed.

Every native prompt used `plate-contract-e2-trestle.png` and `plate-contract-e5-regatta.png` as strict style masters, plus the map's run-camera and landmark render from `artifacts/map-rebuild-spike/` as composition truth. Reuse contracts used their parent terrain's run-camera and their own mounted-landmark overview.

Native run directory: `019f7d87-fc49-7082-8c72-1b0e98bd899c`.

| Plate | Native job | Retakes | Size / mode | Mean luminance | Min edge SD | SHA-256 |
|---|---|---:|---|---:|---:|---|
| `plate-contract-e6-glow-mesa.png` | `exec-6a66bb83-76ee-45dd-91a0-62894f9cda7a` | 0 | 1672x941 RGB | 0.268 | 0.046 | `99e2cfe272ae8fb587e9d48851fce5dcb736ec2c20f9d8bb15f4e2f1fea4d4a7` |
| `plate-contract-e6-showroom.png` | `exec-df37796c-bc7f-47f6-90fb-4927e060643a` | 0 | 1672x941 RGB | 0.217 | 0.048 | `205f9ebfdf5dc8f73a1365b71ddb151de9dfa696140de60efccd19b7b1a03041` |
| `plate-contract-e6-half-life-hollow.png` | `exec-3341e77e-c594-4f11-98c1-92a8094ca0b8` | 0 | 1672x941 RGB | 0.229 | 0.046 | `1c0d079c1ac0601e2ce1d36d3a36ccd983d52e17868d9db1d12c8ba0696a97d4` |
| `plate-contract-e6-picnic.png` | `exec-1b406e20-f5a5-4238-bb9b-ef0aee6464c2` | 0 | 1672x941 RGB | 0.293 | 0.070 | `851fe1caafb175e5574273889c669403b04db703e93150195b2c86da588a1e88` |
| `plate-contract-e7-relay-valley.png` | `exec-ba5f1d5a-e643-4d7d-b30d-c13c947afb88` | 0 | 1671x941 RGB | 0.305 | 0.045 | `9be43ad06aa95b2606a80a3b87c50fa90b8b7daf6394f86d6dc635f4fadb7a4f` |
| `plate-contract-e7-echo-canyon.png` | `exec-d5b5d6fc-f996-4536-9a17-944f3a1cb5bc` | 0 | 1672x941 RGB | 0.239 | 0.069 | `18e90b8e7e4badf5fa3c4daf5376bee7ed959ac8465fefcd85adafdd733cdd8f` |
| `plate-contract-e7-dead-band.png` | `exec-565114ee-4803-4e8c-813e-f84d3266362c` | 0 | 1672x941 RGB | 0.268 | 0.061 | `61bde1957bb4f56a910811b59e802acfb56f210988d0239dffaaf88cc66885a3` |
| `plate-contract-e7-relay-rush.png` | `exec-77f053b8-ff3c-4664-ab92-23f928d3a99f` | 0 | 1672x941 RGB | 0.354 | 0.068 | `9be44915e63187eee17a4fc9f7c0a680af7db83660d8b291739b7b4cb9d018c1` |

## Measured and visual QA

- All eight are opaque RGB PNGs with non-uniform image content on every 16-pixel edge strip; minimum edge standard deviation is 0.045, so no border or inset is present.
- Seven plates are 1672x941 at the exact 1.77683 anchor aspect. Relay Valley is the native one-pixel-tolerance output at 1671x941, 1.77577, matching the accepted E4-E5 plate range.
- Mean luminance spans 0.217-0.354, inside the six adopted E1 anchor range of 0.123-0.364.
- Tesseract returned empty output for all eight. Full-resolution and card-scale visual review found no readable text, letters, numbers, captions, signs, logos, coded writing, or watermarks.
- Visual review found no realistic firearms, gore, border treatment, or photorealism. Picnic's defenders use clearly fantastical brass-and-teal frontier-tech emitters.

| Plate | Signature read | Verdict |
|---|---|---|
| E6 Glow Mesa | broad scarp, two gated entries, open six-vein center, upper worksite, doorless dome and Calculating House | PASS |
| E6 Showroom | five separate furnished model homes, paired starbursts, entrance arch, catalog office and sorting gantry | PASS |
| E6 Half-Life Hollow | deep central hollow, expiring teal bridges, south clock gate, paired dial pylons, north extraction gantry | PASS |
| E6 Picnic | reused mesa scarp, three communal blankets, shade, sandwiches, atomic centerpiece and distant appliance line | PASS |
| E7 Relay Valley | four-tower ridgeline chain, unbroken LOS beam, fog-cut valley, drones and peripheral dish clusters | PASS |
| E7 Echo Canyon | two raised shelf walls, phased arrays, central observation post, clean south ring and warped north return | PASS |
| E7 Dead Band | empty relay sockets, old-tool caches, crossed iron frames, cable-yard null post and silent north gate | PASS |
| E7 Relay Rush | three-bell start, four ridge relay stops, teal lamp dots and advancing un-inked interference front | PASS |

## Prompt set

Every prompt included this exact sentence:

> Gold Rush engraved contract plate, the adopted board style (E2-E5 batch law): fine sepia-ink etched linework on warm parchment, restrained monochrome-warm palette with subtle golden-light accents, full-bleed 1672x941, no letters, no gore.

Every prompt also required an edge-to-edge landscape composition matching the two style masters; the map render's signature terrain and landmarks; and zero readable text, letters, numbers, signs, captions, logos, coded writing, watermarks, realistic firearms, gore, borders, or photorealism.

### E6 Glow Mesa

A broad atomic mesa scarp with two gated herd paths, six subtle teal mineral veins across an open center, upper warehouse and starstone derrick, peripheral service equipment, and the Calculating House beside a doorless reactor dome.

### E6 Showroom

Five pristine furnished but empty model homes with sleeping appliances, framed by a pictogram-only entrance arch, paired atomic starbursts, abandoned catalog office, and sorting gantry; one kitchen begins the waking cascade.

### E6 Half-Life Hollow

A long sunken valley with narrow side shelves, expiring glow bridges, a center dial causeway, zig-zag extraction route, south countdown gate, paired warning pylons, cold appliance convoy, and north extraction gantry.

### E6 Picnic

Three varied picnic blankets, hampers, plates, flasks, sandwiches, an atomic centerpiece, fully clothed townsfolk, and a civilian shade on the reused Glow Mesa meadow, with whimsical appliances approaching beyond the lunch circle.

### E7 Relay Valley

Four relay sites across split high shelves with a clean LOS beam, parchment-tinted dead-zone fog below, patrol drones, peripheral dish clusters, charting station, cable-drum yard, and recovery beacon.

### E7 Echo Canyon

A long canyon between raised shelves: a clean south broadcast ring crosses paired phased arrays and a two-faced observation post before returning as a warped doubled ring through the north gate.

### E7 Dead Band

Relay Valley with all signal systems absent: empty ridge sockets, a cold null post, caches of old hand tools, crossed iron warning frames, a silence gate, no drones or relay beams, and a genuinely empty far end.

### E7 Relay Rush

A three-bell start horn and four unlabeled relay stops form a timed ridge course while pale un-inked parchment advances from the far edge, desaturating and muting the landscape it crosses.

No extraction, resizing, image processing, runtime integration, or batch 030 work was performed.
