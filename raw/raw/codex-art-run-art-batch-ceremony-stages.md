---
source: codex
project: Gold Rush
date: 2026-07-22
type: art-run
---

# art-batch-ceremony-stages — THE TEN STAGES

## Result

Native Codex `image_gen` (`gpt-image-2`) only. No Higgsfield, CLI image model, vector composition, extraction, runtime wiring, or product-code edit was used. Ten full-bleed ceremony backdrops landed at the exact requested paths, `assets/raw/ceremony-stage-t1.png` through `ceremony-stage-t10.png`.

All ten native renders were accepted without a retake. T3, T4, and T10 returned at 1671x941 and received only the established one-pixel width normalization to the required 1672x941; no crop, repaint, compositing, or other image processing was performed.

Native run directory: `019f8849-8510-7ea3-940c-24398d5e4740`.

## Measured QA

The 41 adopted `plate-contract-*.png` anchors span mean luminance 0.104365-0.521297. Every stage is inside that measured band. Minimum edge SD is the lowest grayscale standard deviation across the four 16-pixel edge strips; every value is non-zero, confirming edge-to-edge image content rather than an inset or flat border.

| Stage | Native job | Retakes | Size / mode | Mean luminance | Min edge SD | SHA-256 |
|---|---|---:|---|---:|---:|---|
| T1 | `exec-e9cb129e-7f79-4ab3-99b4-2c2ab1509c7f` | 0 | 1672x941 RGB | 0.242963 | 0.079217 | `81d1ec2b0c3f80ca18abbe027a009d3cf2d9bee02cbc9963f9ab875696bfd498` |
| T2 | `exec-75543e24-13f9-495e-b1de-cde245c8eb83` | 0 | 1672x941 RGB | 0.219695 | 0.047901 | `c5cd54af43cd9a1504ff210e57022fa5f0a1ca1426599639e155cb6b15cde1a7` |
| T3 | `exec-3d864f11-697a-40fe-9625-590b67066705` | 0 | 1672x941 RGB | 0.164611 | 0.032517 | `321cc87bc4456e36af8fa7663d9f41fac4bb21566353cd3e19046910d551f199` |
| T4 | `exec-2b6b18cd-a71e-41f1-b5fb-ba7542ceef69` | 0 | 1672x941 RGB | 0.408113 | 0.061554 | `4a94e6c6db293d60036c08751275dc486443ca91172a2f11eccfcb523fb032f1` |
| T5 | `exec-5e666f7f-79a8-41fb-8a1d-00f57e15e7b9` | 0 | 1672x941 RGB | 0.232597 | 0.023059 | `b85f88643d1935f35c8cacfe0397e438aabf09f84554fb2cd81eead5468daee2` |
| T6 | `exec-7081cb4e-fd60-4cac-bdd0-7aad1b41a89f` | 0 | 1672x941 RGB | 0.225113 | 0.047814 | `2b772d615d4d175112e48b82f2614a1591538343d1254641fca3ae2d0d372d1a` |
| T7 | `exec-8a3fcb35-c74b-4163-8fb0-fc6a20b7b419` | 0 | 1672x941 RGB | 0.280633 | 0.046706 | `792a6b4cf78c3d370a4b049e84f1a63b4f9c8991c6ba77d54302958fc00feccd` |
| T8 | `exec-edb5933f-8779-421f-9ef4-ff28eaabf7ac` | 0 | 1672x941 RGB | 0.263472 | 0.027843 | `6f492b72a4f90f84c7de1f0615948af512f133a8a30e24a6533af5fa5c0a5c09` |
| T9 | `exec-b9b01629-716e-48ac-95ef-5d22417b5fae` | 0 | 1672x941 RGB | 0.332351 | 0.067228 | `912ac013cac505902b32b48c2c7c49b46ceffdba5b6f91d591384616483f5daf` |
| T10 | `exec-9d2757ef-c63f-47d6-9a9d-b3831ca9ce1f` | 0 | 1672x941 RGB | 0.325836 | 0.098097 | `911d59826293d8f580958835a5b634e3427558d8007f717c2101f37fa9e57025` |

- Dimensions and mode: all ten are exactly 1672x941 opaque RGB PNGs.
- No letters: full-resolution visual inspection found no readable text, letters, numbers, signs, labels, logos, watermarks, or writing. Tesseract's high-confidence detections were incoherent hatch fragments only (`SS`, `AS`, `RY`, and similar), never a readable word.
- Palette: all ten use warm parchment, sepia ink, golden light, and restrained starstone teal; measured luminance stays inside the complete adopted plate-anchor band.
- Canon: no realistic firearms, military weapon language, gore, injury, photorealism, or Native American enemies appear.
- Full bleed: all four edges of every stage contain non-uniform image content; there is no inset, decorative border, or title area.

## Independent review

A neutral 2x5 montage review against six adopted contract-plate masters found that all ten scenes remain distinct and readable and that the batch preserves the same parchment, engraving, gold-light, industrial-frontier, and teal-accent family. The reviewer called T3's blank valve collar, T6's bright teal dial/plate area, and T10's blank press bed the strongest local departures; those are the task-mandated runtime interaction surfaces, so they are retained intentionally. T4, T7, T8, and T9 were singled out for especially clear breathing room.

`codex review --uncommitted` found the art assets and ledger consistent. Its only P2 comment concerned pre-existing transient churn in `logs/.goal-tree.html`, outside this task; that file was not touched or repaired here.

## Per-stage scene and hotspot QA

| Stage | Scene depicted before the hand engages | Canon objects present | Reserved UI zone | Verdict |
|---|---|---|---|---|
| T1 | The whole cast waits beneath the raised first stamp while the first train brings the unmarked Gazette press. | raised iron stamp, ore bed, full town, rail spur, locomotive, press | lower-right 28% quiet timber floor | PASS |
| T2 | The communal first crank waits in the dark Dynamo Hall. | dormant flywheel, gathered push line, unlit lamp in the Elder's Tree, dark town | lower-center 30% circular timber floor | PASS |
| T3 | The night refinery waits before the crack-tower valve opens. | twin towers, dry pipework/spigots, crude wagon, crowd, southern flats | central x40-60% / y42-72% blank valve collar | PASS |
| T4 | The sacred overland haul is mustered behind the last dune. | ship on carrier, lead Flivver, full valley convoy, townsfolk, dune; no sea reveal | lower-center 34% open road | PASS |
| T5 | Six hulls hold one line over the submerged reactor in the year's flattest calm. | six hulls, converging ropes, waiting barge, drowned claim strata, deep teal glow | lower-center x40-60% / y60-86% calm water | PASS |
| T6 | The Calculating House listens at dusk before the Prospector's plate is mounted. | House, glowing teal dial, first jack-board light, made minds, Prospector front row | blank patch above door x46-56% / y25-36%; clear center path | PASS |
| T7 | The made crew boards the Starship while the final umbilical remains attached. | starship, gantry, made crew, Prospector and Chalk at porthole, relay valley, river | lower-right x68-92% / y64-90% quiet pad deck | PASS |
| T8 | The unnamed Colony Seed waits in the Claw yard beneath the single red destination. | grounded Seed, inhabited dome cluster, working town, red dot | lower-center 38% blank regolith / naming zone | PASS |
| T9 | The whole aged town lines the open Generation Ark ramp before the seed-tin carry. | Ark, boarding generations, green canals, working machinery, heir fleet, caretaker and stopped watch | central ramp x39-61% / y48-100% | PASS |
| T10 | The blank Charter Press waits at dawn before four hands meet the lever. | canonical vaulted hall, monumental rollers, blank charter bed, teal reservoirs | central foreground x38-62% / y54-100%; empty lever socket | PASS |

## Final prompt set

Every prompt included this exact sentence verbatim:

> Gold Rush engraved ceremony stage in the adopted board voice: fine sepia-ink etched linework on warm parchment, restrained monochrome-warm palette with golden-light and starstone-teal accents, full-bleed, no letters, no gore.

Every prompt requested exactly 1672x941 landscape, full-bleed edge-to-edge art; classified the supplied contract plates as style-only references unless noted; reserved the hotspot listed above; and prohibited the player's hands, UI controls, captions, borders, readable text, letters, numbers, labels, signs, logos, watermarks, runes, writing, realistic firearms, photorealism, and gore.

### T1

Gold Rush engraved ceremony stage in the adopted board voice: fine sepia-ink etched linework on warm parchment, restrained monochrome-warm palette with golden-light and starstone-teal accents, full-bleed, no letters, no gore. The Stamp Mill yard at late golden dusk, the whole recurring cast looking up, first iron stamp raised above the ore bed, first train arriving behind them with an unmarked Gazette printing press; quiet lower-right timber floor for the release hotspot; no painted release handle or falling impact.

### T2

Gold Rush engraved ceremony stage in the adopted board voice: fine sepia-ink etched linework on warm parchment, restrained monochrome-warm palette with golden-light and starstone-teal accents, full-bleed, no letters, no gore. Newly raised Dynamo Hall at blue dusk, monumental flywheel motionless, townsfolk gathered around the capstan stations, first lamp hanging unlit in the Elder's Tree, every window dark; broad lower-center floor kept clear for the communal crank UI.

### T3

Gold Rush engraved ceremony stage in the adopted board voice: fine sepia-ink etched linework on warm parchment, restrained monochrome-warm palette with golden-light and starstone-teal accents, full-bleed, no letters, no gore. Completed refinery built at night with twin crack towers, dry spigots, brass pipes, teal insulators, first crude wagon and gathered town; central dark brass housing carries an empty circular collar for the runtime valve; no flowing liquid.

### T4

Gold Rush engraved ceremony stage in the adopted board voice: fine sepia-ink etched linework on warm parchment, restrained monochrome-warm palette with golden-light and starstone-teal accents, full-bleed, no letters, no gore. One ship lashed to a heavy carrier behind the lead Flivver, every valley vehicle in a long settled convoy, final dune completely hiding the sea; broad foreground road quiet for the drive hotspot; no moving dust or wave reveal.

### T5

Gold Rush engraved ceremony stage in the adopted board voice: fine sepia-ink etched linework on warm parchment, restrained monochrome-warm palette with golden-light and starstone-teal accents, full-bleed, no letters, no gore. Six frontier hulls aligned across perfectly calm inland water at dusk, every rope converging on one submerged raise point, waiting homecoming barge, drowned prior claims suggested beneath clear water, barely visible deep teal reactor glow; quiet lower-center water for the winch pulse UI.

### T6

Gold Rush engraved ceremony stage in the adopted board voice: fine sepia-ink etched linework on warm parchment, restrained monochrome-warm palette with golden-light and starstone-teal accents, full-bleed, no letters, no gore. The newly completed Calculating House at dusk, round teal dial glowing in the Prospector's boot rhythm, unlabeled jack-board's first light, faint listening wires and dishes, a crowd of varied made minds with the round brass Prospector front row; blank patch above the door for the runtime plate and screw.

### T7

Gold Rush engraved ceremony stage in the adopted board voice: fine sepia-ink etched linework on warm parchment, restrained monochrome-warm palette with golden-light and starstone-teal accents, full-bleed, no letters, no gore. First handmade starship upright on a quiet river-valley pad, final umbilical still attached, made crew boarding, Prospector and Chalk together at one porthole, dark relay towers waiting; quiet lower-right pad for the release UI; no plume or countdown.

### T8

Gold Rush engraved ceremony stage in the adopted board voice: fine sepia-ink etched linework on warm parchment, restrained monochrome-warm palette with golden-light and starstone-teal accents, full-bleed, no letters, no gore. Finished unnamed Colony Seed grounded in the lunar yard the Claw became, inhabited dome cluster and working town, one small rust-red destination in deep sky; blank lower-center regolith naming zone; no typed name, ballot, countdown, or burn.

### T9

Gold Rush engraved ceremony stage in the adopted board voice: fine sepia-ink etched linework on warm parchment, restrained monochrome-warm palette with golden-light and starstone-teal accents, full-bleed, no letters, no gore. Generation Ark waiting on the green Red Fields world with broad ramp lowered, every aged generation boarding along both sides, green canals running, Old Digger machinery working, heirs' sail-fleet at the horizon, ancient caretaker waving with stopped watch; central ramp empty for the runtime seed-tin carry.

### T10

Gold Rush engraved ceremony stage in the adopted board voice: fine sepia-ink etched linework on warm parchment, restrained monochrome-warm palette with golden-light and starstone-teal accents, full-bleed, no letters, no gore. Preserve the canonical Charter Press hall and monumental rollers from `plate-e10-charter-press-hall.png`, but remove foreground people and physical lever; blank parchment waits on the press bed under dawn and teal glass; central foreground kept empty for the runtime four hands and lever.

## Reference images

- T1-T7 style masters: `plate-contract-e2-trestle.png`, `plate-contract-e5-regatta.png`, `plate-contract-e7-relay-valley.png`.
- T8-T9 style masters: `plate-contract-e8-mare-claim.png`, `plate-contract-e9-dome-basin.png`, `plate-contract-e10-last-claim.png`.
- T10 scene reference: `plate-e10-charter-press-hall.png`; style masters: `plate-contract-e10-last-claim.png`, `plate-contract-e10-river.png`.
