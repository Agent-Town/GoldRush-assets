---
source: codex
project: Gold Rush
date: 2026-07-19
type: reference
---

# E4-E5 contract-board plates

## Result

Native Codex `image_gen` only. No Higgsfield still-image model was used. Every plate was conditioned on three representative images from the six existing contract anchors plus the relevant map render or E5 kit. The outputs remain raw full-bleed art; no extraction, resizing, or processing was performed.

| Plate | Native job | Retakes | Size / mode | Mean luminance | Edge SD | SHA-256 | Verdict |
|---|---|---:|---|---:|---:|---|---|
| `plate-contract-e4-dust-flats.png` | `exec-58360556-aebd-4339-8315-0f68aa7ee520` | 0 | 1672x941 RGB | 0.467 | 0.208 | `40667a6032678719b8b20f11161e592fa39028051d4a85e2c08661093d9aa901` | PASS |
| `plate-contract-e4-long-road.png` | `exec-ff5bcb72-6ea0-4bac-b3b4-b27814b08954` | 0 | 1672x941 RGB | 0.494 | 0.195 | `56e796f2b00fd167b0c29fa95a93565ad5f3b5226ae21a39f3f1ad9656e877ef` | PASS |
| `plate-contract-e4-gusher-county.png` | `exec-957edf74-71ee-4033-a874-9d5cbde007a8` | 0 | 1671x941 RGB | 0.376 | 0.208 | `492e77d50a77fc9e1473c23e2637edbeadb3a10730be62ddea791c92dc474d5e` | PASS |
| `plate-contract-e4-boneyard.png` | `exec-9a9a6ee7-973f-4e53-8c57-a320a9de9cb3` | 0 | 1671x941 RGB | 0.340 | 0.180 | `a2bfe78c57805aec91ff3564bdef1e442e2ac8b6d0ec042cb5baaac662855989` | PASS |
| `plate-contract-e5-deepwater-claim.png` | `exec-7970406f-ae7d-47f8-8492-6d81e0bf246d` | 0 | 1672x941 RGB | 0.309 | 0.226 | `58869a143bf52f13fc022a06248b9808f0adaf956c65394f73d226621ba97d98` | PASS |
| `plate-contract-e5-regatta.png` | `exec-4f45c7b7-0417-4bdc-a266-bb48e52748fc` | 0 | 1672x941 RGB | 0.284 | 0.338 | `82b7ac00f1f98d5f0fbb473df763671c6f2e99f24ed966df035255081c57a9d8` | PASS |
| `plate-contract-e5-stillwater.png` | `exec-5773f5d2-bb97-4837-ae67-df6d71f910d9` | 0 | 1671x941 RGB | 0.389 | 0.163 | `ff612f57b7646c68763ce8d34a3333f053d2f6fb5dc73df132dbcde2fb0188e3` | PASS |
| `plate-contract-e5-flotilla.png` | `exec-7ac189ff-1a2e-4f6e-aac7-c3e2eb78c5c8` | 0 | 1672x941 RGB | 0.357 | 0.255 | `155c6554f6d10ec25bace3de77bd168dd1ae4bfad2ee6783eb64bbc8be96d3be` | PASS |

Native run directory: `019f7aa5-ea60-7a62-9b78-9fef4118ce71`.

## Measured and visual QA

- All eight are opaque RGB PNGs with image content at every edge and no frame. Their combined edge standard deviation spans 0.163-0.338, inside the six-anchor range of 0.151-0.421.
- Aspect ratio spans 1.77577-1.77683:1; five plates exactly match the 1672x941 anchors and three differ by one horizontal pixel from native generation.
- Batch mean luminance spans 0.284-0.494, inside the six-anchor range of 0.078-0.525.
- OCR-assisted review returned only short linework false positives. Card-scale visual review found no readable word, letter, number, caption, sign, logo, or watermark.
- No realistic firearms, gore, border treatment, or dread-black E5 water appears.

| Plate | Signature read |
|---|---|
| E4 Dust Flats | dominant wheel-cut orbit road, central derrick field, sparse storm-watch and service chain |
| E4 Long Road | one dark end-to-end road, tiny moving convoy, widely spaced way-station anchors, no fixed town |
| E4 Gusher County | many wild derricks, staggered non-burning crude geysers, tar channels, comic outhouse spout |
| E4 Boneyard | valley of dead Flivvers and boilers, huge half-buried amber-eyed sleeper, unlabeled medicine wagon |
| E5 Deepwater Claim | pan-bow Claim-Boat, reef gaps, lighthouse, dive bell, one drowned accreted town under green glass |
| E5 Regatta | five-beacon race course, competing boats, storm-front fast line, submerged course relief |
| E5 Stillwater | fog and glass sea, silent sail-trim boat, hand pan, long leviathan shadow following one ripple |
| E5 Flotilla | distinct district hulls in a protective formation around a trailing boat |

## Prompt set

Every prompt included this exact sentence:

> Engraved sepia contract plate in the Gold Rush house style: warm frontier illustration, fine etched linework on parchment, full-bleed, no letters, no gore, no firearms.

Every prompt also required a wide full-bleed landscape composition matching the anchors; zero readable text, letters, numbers, signs, captions, logos, watermarks, borders, realistic firearms, or gore; and the map's signature terrain and landmark read.

### E4 Dust Flats

An immense dry basin whose wheel-cut orbit road dominates a central derrick field, with a sparse storm-watch tower, open A-frame road-wrecker shed, fuel reserve, grade-charting post, and dry-wash recovery gantry.

### E4 Long Road

One dark wheel-cut road receding through a four-hundred-unit corridor, carrying a tiny mobile convoy past widely spaced old way-stations; no fixed settlement.

### E4 Gusher County

A field of wild derricks erupting tall non-burning crude geysers on staggered schedules, surrounded by cap rigs, valve gantries, tar channels, and one comic outhouse spout.

### E4 Boneyard

A dusty valley of dead Flivvers, spent boilers, wheels, and pipework, with one immense half-buried amber-eyed sleeper and one faded unlabeled medicine-show wagon.

### E5 Deepwater Claim

An oblique surface-and-underwater cutaway: the pan-bow Claim-Boat and lighthouse above, reef gaps and a brass dive bell below, with era-stamped wreck objects and exactly one drowned accreted town.

### E5 Regatta

A storm race through five beacon checkpoints above submerged course relief, with the fastest water beside a charcoal wall-cloud and several competing boats holding daring lines.

### E5 Stillwater

The reused Shelf Reefs under pale fog and glass-smooth water: one silent sail-trim boat hand-panning while a long brass leviathan shadow curves toward a single ripple.

### E5 Flotilla

The reused Shelf Reefs crossed by a protective formation of distinct district hulls: kitchen scow, non-gun harpoon raft, still-room barge, supply skiffs, and lighthouse tender shielding a straggler.

No extraction, processing, runtime integration, or batch-029 work was performed.
