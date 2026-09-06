# Codex Art Run — E4 batch 01 / batch-016

Date: 2026-07-14  
Tool path: Codex native `image_gen` only  
Task: `/Users/robin/Claude/Projects/Gold Rush/tasks/running/art--20260714-120302-art-e4-batch-01.md`

Status: **RAW GENERATED; PENDING-PROCESSING / PENDING-CONSUMPTION.**

Scope was the E4 bundle batching plan's A1 buildings plus A6 terrain/props. The task's “A5 terrain/props” wording was resolved against the bundle: A5 is townsfolk, while batch-016 explicitly names A1 + A6. No processing, layer contracts, source, specs, reviews, e2e, or integration files were touched.

## References and prompt law

- `assets/raw/kit-era-4.png` conditioned every generation.
- `assets/raw/plate-e3-bld-dynamo-hall.png` additionally conditioned the refinery scale band.
- Every prompt included the bundle anchor verbatim:

> dust-warm ochres pushed lighter and hazier; machines are riveted steel with brass carryovers and teal agent-glow instruments; exhaust reads as light dust puffs, never black smoke; speed is drawn with engraved motion lines, never blur.

- Every prompt required Frontier Ledger engraving, no readable text/letters/numbers/logos/watermarks, no realistic firearms or gun-like silhouettes, no gore, no Native American enemy imagery, no black smoke, and +20% haze-overlay legibility.
- Sheet prompts required exact cell order on `#ff00ff`; the atlas required full-bleed 2x2 terrain cells.

## Outputs and native jobs

| File | Grid / format | Native job | Retakes | State |
|---|---|---|---:|---|
| `bld-derrick.png` | 2x1, pump head up/down, `#ff00ff` | `exec-6e04f74f-181c-4d2c-9784-e4cafa27698d` | 0 | PENDING-PROCESSING |
| `bld-refinery.png` | isolated portrait | `exec-73dcf896-3c1f-4472-aebe-bb8e50bfa7b9` | 0 | PENDING-PROCESSING |
| `bld-garage.png` | isolated portrait | `exec-36d5086c-e49a-47c8-a2e2-a8c3e4949a68` | 0 | PENDING-PROCESSING |
| `bld-grader-post.png` | isolated portrait | `exec-6cc4a674-9488-4082-9fab-36f64f219ce7` | 0 | PENDING-PROCESSING |
| `bld-watchtower.png` | 2x1, lamp lit/unlit, `#ff00ff` | `exec-68449c9e-851c-4c74-a14f-5e7684b09d22` | 0 | PENDING-PROCESSING |
| `ter-dustflats-atlas.png` | 2x2 full-bleed | final `exec-f440c881-27d7-43b0-a055-a9a7def32840` | 2 | PENDING-PROCESSING / CONSUMPTION |
| `ter-pipeline-elements.png` | 5x1, `#ff00ff` | `exec-f2e0553b-c5a2-4c58-ae48-2810880e2d30` | 0 | PENDING-PROCESSING |
| `prop-gusher.png` | 3x1, `#ff00ff` | `exec-caca23e8-5ce6-48c7-a505-f61e3983e724` | 0 | PENDING-PROCESSING |
| `prop-tumbleweed.png` | 4x1, `#ff00ff` | `exec-d1a19cf6-49fd-4846-a5cf-7a385d17fcc1` | 0 | PENDING-PROCESSING |

Atlas rejected attempts: first pass `exec-25e6d119-a687-45c1-b271-289d4f475bf5`; retake 1 `exec-90ab55e9-5b5c-4915-8196-0ee0e69b698c`. Both retained only in Codex's generated-image store, not the repo. Retake 2 reduced combined opposite-edge mean deltas to 9.9–11.4 RGB and p95 to 24–29 across the four cells, matching the existing seamless-terrain QA band more closely than retake 1 (means 17.1–18.5).

## Raw preparation

The five sheet backgrounds were normalized from native near-magenta to exact opaque `#ff00ff`; no alpha extraction, cell extraction, resizing, despill, or integration was performed. Final exact-key coverage: derrick 72.56%, watchtower 79.00%, pipeline 85.93%, gusher 72.55%, tumbleweed 80.74%; near-magenta non-exact pixels: 0 for all five.

## QA

| File | Style / content | Grid / key / full-bleed | Letters | Firearms | Gore | Haze | Verdict |
|---|---|---|---|---|---|---|---|
| `bld-derrick.png` | tower silhouette, teal gauge, rope/plank bracing; only pump arc changes | 2x1; exact key | none | none | none | legible | PASS |
| `bld-refinery.png` | twin squat towers, coil, gold-amber fuel and near-black tar spigots, tiny warm flare | portrait; neutral gray | none | none | none | legible | PASS |
| `bld-garage.png` | wide open bay, Flivver on lift, tool wall, teal diagnostic lamp | portrait; neutral gray | none | none | none | legible | PASS |
| `bld-grader-post.png` | drag scraper, survey flags, pictogram route table; infrastructure read | portrait; neutral gray | none | none | none | legible | PASS |
| `bld-watchtower.png` | tallest guyed silhouette, spotting scope, gold lamp state | 2x1; exact key | none | scope only | none | legible | PASS |
| `ter-dustflats-atlas.png` | cracked pan / drift / graded road / oil ground | 2x2 full-bleed; wrap QA 9.9–11.4 mean | none | none | none | legible | PASS |
| `ter-pipeline-elements.png` | straight / elbow / valve / tap / amber-black leak | 5x1; exact key | none | none | none | legible | PASS |
| `prop-gusher.png` | capped / crude arc / crater; crude reads as liquid, not flame | 3x1; exact key | none | none | none | legible | PASS |
| `prop-tumbleweed.png` | four distinct roll phases with engraved motion lines, no blur | 4x1; exact key | none | none | none | legible | PASS |

Burn count: 11 native image calls; 9 accepted final assets; 2 rejected atlas attempts; 2 retakes total, both on the atlas; no rate-limit or auth errors.

