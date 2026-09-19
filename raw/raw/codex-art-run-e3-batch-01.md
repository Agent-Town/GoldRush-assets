# Codex Art Run — E3 batch 01 / batch-013

Date: 2026-07-15  
Tool path: Codex native `image_gen` only  
Task: `/Users/robin/Claude/Projects/Gold Rush/tasks/running/art--20260715-005028-art-e3-batch-01.md`

Status: **RAW GENERATED; PENDING-PROCESSING / PENDING-CONSUMPTION.**

Scope was the E3 bundle batching plan's A1 buildings plus A5 Canyon Works terrain/props. No extraction, processed outputs, layer contracts, source, specs, reviews, e2e, or integration files were touched.

## References and prompt law

- `assets/raw/kit-era-3.png` conditioned every generation.
- `assets/raw/bld-stamp-mill.png` additionally conditioned Dynamo Hall's scale band.
- Every prompt included the bundle's required Frontier Ledger anchor verbatim:

> Frontier Ledger style: hand-engraved storybook illustration, fine ink hatching and cross-hatch shading, parchment-warm palette of ochres, sepias and warm browns with restrained teal agent-tech glow accents; illustrated and warmly readable, never photorealistic, never gory, no text or letters or watermarks anywhere in the image.

- Every prompt included the E3 palette note verbatim:

> nights are deep ink-blue parchment, never black; lit areas are pools of warm lamp-gold; teal agent-glow reads brighter after dark. Arc effects are drawn lightning — jagged engraved strokes, never photoreal glow blooms.

- All prompts prohibited readable text/letters/numbers/logos/watermarks, people, realistic firearms or gun-like silhouettes, and gore.
- Sheet prompts fixed exact cell order on `#ff00ff`; the atlas required a full-bleed 2x2 terrain-only grid.

## Outputs and native jobs

| File | Grid / format | Native job | Retakes | State |
|---|---|---|---:|---|
| `bld-dynamo-hall.png` | isolated portrait; Stamp Mill scale reference | `exec-70a11bfc-bf79-41ef-a083-11772af674a0` | 0 | PENDING-PROCESSING |
| `bld-pylon.png` | 2x1, powered/unpowered, `#ff00ff` | `exec-9a37d053-0027-4abb-a62b-34aff7654505` | 0 | PENDING-PROCESSING |
| `bld-arc-lamp.png` | 2x1, lit/unlit, `#ff00ff` | `exec-76385ce3-5512-4598-816c-7f74189f9b22` | 0 | PENDING-PROCESSING |
| `bld-tram-station.png` | isolated portrait | `exec-9ae36dbe-8f47-44d4-b865-75c9cf7ce6a9` | 0 | PENDING-PROCESSING |
| `bld-exchange-annex.png` | isolated portrait; six outgoing wires | `exec-c1befb1b-eafe-444e-9571-5f6637224ea6` | 0 | PENDING-PROCESSING |
| `ter-canyon-atlas.png` | 2x2 full-bleed | selected retake 1 `exec-ca8b205e-271e-4d5d-beec-40a240ddd7e7` | 2 | PENDING-PROCESSING / CONSUMPTION; seam caveat below |
| `ter-wire-elements.png` | 8x1, `#ff00ff` | `exec-a2eea510-ef65-4566-9d6a-5fa1515d8af5` | 0 | PENDING-PROCESSING |
| `prop-damsite.png` | 2x1, closed/open, `#ff00ff` | `exec-dc487b50-7310-4499-8016-5793ce20fa66` | 0 | PENDING-PROCESSING |

Atlas rejected attempts: initial `exec-14b95743-36d5-4c0a-91b2-a44af3bb52c5` introduced lamps/fixtures into pure terrain; retake 2 `exec-e0c79385-c086-437a-afdd-9bb0cf8eb559` was visually uniform but measured worse at opposite-edge wrap. Both remain only in Codex's generated-image store. The selected retake 1 is terrain-only and the best measured candidate.

## Raw preparation and metrology

The four sheet backgrounds were normalized from native near-magenta to exact opaque `#ff00ff`; no alpha extraction, cell extraction, resizing, despill, or integration was performed.

| Sheet | Dimensions | Exact-key coverage | Near-magenta non-exact | Alpha pixels | Cell content bounds |
|---|---:|---:|---:|---:|---|
| `bld-pylon.png` | 1672x941 | 77.22% | 0 | 0 | 571x766, 571x767 |
| `bld-arc-lamp.png` | 1672x941 | 89.93% | 0 | 0 | 188x892, 188x892 |
| `ter-wire-elements.png` | 2172x724 | 83.23% | 0 | 0 | 226x242, 239x236, 272x251, 271x347, 272x358, 271x366, 272x375, 260x374 |
| `prop-damsite.png` | 1672x941 | 52.97% | 0 | 0 | 793x611, 793x649 |

Selected atlas opposite-edge absolute RGB deltas by cell (mean / p95): r0c0 18.9 / 54; r0c1 15.5 / 42; r1c0 14.7 / 40; r1c1 19.4 / 53. These exceed batch-016's established generation band. Fire-side processing must seam-check at repeated-tile scale before consumption; do not mark the atlas integrated on raw-generation evidence alone.

## QA

| File | Style / content | Grid / key / full-bleed | Letters | Firearms | Gore | Verdict |
|---|---|---|---|---|---|---|
| `bld-dynamo-hall.png` | paired equal flywheels, bus-bars, first pylon, switchboards, teal/gold status lamps | isolated portrait | none | none | none | PASS |
| `bld-pylon.png` | far-zoom H-frame; powered lamp left, dark lamp right | 2x1; exact key; state heights differ 1px | none | none | none | PASS |
| `bld-arc-lamp.png` | twin carbon rods; clear warm-gold glass, not teal | 2x1; exact key; equal 892px heights | none | none | none | PASS |
| `bld-tram-station.png` | compact shed, trolley hook, adult-band bench, pictogram-only folded board | isolated portrait | none | none | none | PASS |
| `bld-exchange-annex.png` | visible patch-board; exactly six gable wires, three left + three right | isolated portrait | none | none | none | PASS |
| `ter-canyon-atlas.png` | stone / slate / formed footing / tuft-rock; terrain-only | 2x2 full-bleed; wrap caveat above | none | none | none | PASS FOR RAW; SEAM-QA REQUIRED BEFORE CONSUMPTION |
| `ter-wire-elements.png` | short/medium/long spans, insulator, cut wire, rail, lit/dark tram in exact order | 8x1; exact key | none | none | none | PASS |
| `prop-damsite.png` | same dam face; closed gates left, visibly open spillway right | 2x1; exact key | none | none | none | PASS |

Burn count: 10 native image calls; 8 accepted final assets; 2 rejected atlas attempts; 2 retakes total, both on the atlas; no rate-limit, auth, or quota errors.
