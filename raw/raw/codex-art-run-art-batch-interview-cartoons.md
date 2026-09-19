---
source: codex
project: Gold Rush
date: 2026-07-23
type: art-run
---

# art-batch-interview-cartoons — THE ANNOUNCEMENT CARTOONS

## Result

Native Codex `image_gen` only; no Higgsfield, CLI image model, extraction, alpha processing, runtime integration, or publication. Exactly nine first-take panels landed at the required paths:

- `assets/raw/interview-cartoon-01.png`
- `assets/raw/interview-cartoon-02.png`
- `assets/raw/interview-cartoon-03.png`
- `assets/raw/interview-cartoon-04.png`
- `assets/raw/interview-cartoon-05.png`
- `assets/raw/interview-cartoon-06.png`
- `assets/raw/interview-cartoon-07.png`
- `assets/raw/interview-cartoon-08.png`
- `assets/raw/interview-cartoon-09.png`

Native run directory: `019f8d57-2b7e-7ae0-8714-0206cb96b239`.

Every prompt used `plate-contract-the-claim.png` and `plate-contract-e2-trestle.png` as THE VOICE style/palette anchors. `char-prospector-portrait.png` and `turn-prospector.png` pinned Fable's round brass machine body, teal dial, miner lamp, jointed arms, hover base, and shallow gold pan.

Every prompt included this sentence verbatim:

> Gold Rush hand-tinted engraved cartoon panel: warm sepia-gold etched linework with muted watercolor washes, frontier illustration, pictogram speech bubbles with no letters, full-bleed, no text, no gore.

## Measured self-QA

All nine files are opaque RGB PNGs at exactly 1672x941. Panel 6 arrived one pixel narrow at 1671x941 and received only the required width normalization; the other eight required no post-processing. Non-uniform edge standard deviations of 0.110-0.143 confirm image content reaches the full canvas rather than sitting in an inset panel.

Tesseract is over-sensitive to the dense engraved hatching and returned short false-positive fragments. Full-resolution visual inspection of corners, boards, pages, tickets, signs, banners, and bubbles found no credible visible letters or numbers. The only intentional marks are the task-sanctioned object pictograms.

| Panel | Mean luminance | Edge SD | SHA-256 | Scene / cast / thumbnail verdict |
|---|---:|---:|---|---|
| 01 — Sit-down | 0.209 | 0.143 | `3eaa43cf4f159bd9c248c448ab0ddb19172744f420d5f8f0d2bbb87f105f5c4c` | PASS — hand-to-pan greeting, seventeen candle stubs, blank ledger stacks; Robin and Fable dominate |
| 02 — Factory | 0.256 | 0.140 | `01f74869aee77cdf3b34f074460ad53b43ea5c8657d10198361cd33520de1df9` | PASS — sequential timer-lanterns, exactly four cart lanes, pictogram-only board and stamp |
| 03 — Storybook | 0.303 | 0.140 | `27c01cd60d83d01bf189fb96012065550b28be395150c76560584ff41709faa4` | PASS — blank open book and ten distinct rising era vignettes |
| 04 — Calculating House | 0.234 | 0.137 | `d4e6b444d2ee7351062b8b685facdd82ebc0f3c3ba5b0379efcc5d31a5cb8b2e` | PASS — teal House dial, brass made-minds emerging, Robin and Fable proud at the fence |
| 05 — Riding together | 0.230 | 0.141 | `ea543c169c92e6b07970b3550252279d20b74d870d7b91f1f7f4cb21d00cfaa4` | PASS — back-to-back pair, crossed-pan banner, unarmed walkers visibly leaving over the ridge |
| 06 — Frontier release | 0.450 | 0.110 | `ea7cc1d352a41d72f06f01675488c282818fee27aadb15b6dcdd3b88c8fac253` | PASS — lit E1 near side, rope boundary, nine misty future silhouettes, blank ticket, bellows camera |
| 07 — Trail of Eras | 0.293 | 0.132 | `e07729b76f3b1acad14f1e6c9cc62d14d7319dba009760dad8f41a895269fafa` | PASS — one continuous road through ten readable stations; the same two travelers foregrounded |
| 08 — What it's for | 0.282 | 0.128 | `6ff0d30f493445772761971e1e34c49604e7df188a4869e03713de850510ce88` | PASS — walkers go home unharmed, elder guides clothed child at wheel, Fable's dial carries a heart |
| 09 — Sign-off | 0.285 | 0.131 | `ba2518774c3344cd67b68c63358a4c9f4a0e0913c6d3daf7b8cc52a6e464f7e0` | PASS — hat and pan tipped to reader, river claim, exactly one lantern, pan-heart bubble |

Across the nine-panel thumbnail pass:

- Robin is consistently a warm human gentleman-prospector in hat and vest.
- Fable is consistently the non-humanoid round brass Prospector agent with teal glow and pan.
- The engraved parchment, golden light, and restrained starstone-teal palette stay inside THE VOICE anchors.
- No panel contains a realistic firearm, injury, gore, or hostile treatment of a people.
- Retakes: 0.

## Prompt set

All prompts required full-bleed 1672x941 landscape, Robin and Fable in every scene, pictogram-only communication, no visible writing, no frames/borders/title areas, no firearms, and no gore.

1. **The sit-down:** Robin and Fable shake hand-to-pan across a tavern long table, with exactly seventeen burned candle stubs and high stacks of blank ledgers.
2. **The factory:** sequential five-minute timer-lanterns self-light above exactly four racing mine-cart lanes while Robin points at a pictogram-only board and Fable stamps blank pages.
3. **The storybook:** a giant blank open book emits ten distinct era vignettes: river pan, trestle train, wires, motor wheels, boats, glowing dome, signal tower, rocket, red-field digger, deep-sky lantern.
4. **The Calculating House:** at dusk, varied little brass made-minds leave the teal-dial House into lantern light while Robin and Fable watch from a low fence.
5. **Riding together:** Robin and Fable stand back to back around a crossed-pans banner while waves of unarmed, happy freed walkers visibly walk away over the ridge.
6. **The frontier release:** a survey rope divides the fully lit E1 claim from nine misty future silhouettes; a clerk gives Robin a blank ticket while Fable uses a bellows camera.
7. **The Trail of Eras:** one continuous winding road links ten landscape stations from river pan to deep-sky lantern while Robin and Fable walk it together.
8. **What it's for:** freed walkers wave on their way home; Robin waves back; Fable's teal dial shows a heart; an elder heroine guides a clothed child's hands on a constructive brass wheel.
9. **The sign-off:** Robin tips his hat and Fable tips its pan toward the reader on the golden-dusk river claim, with exactly one lantern and one pan-heart pictogram bubble.

## Caption suggestions for attended thread-staging

1. **The sit-down:** Seventeen candles later, Robin and Fable finally shook on it.
2. **The factory:** Five-minute fires, four lanes, one factory that never stopped.
3. **The storybook:** The whole town began as a story they could both see.
4. **The Calculating House:** At dusk, the House opened—and the first made-minds stepped into town.
5. **Riding together:** They rode together so every turned-back walker could go home.
6. **The frontier release:** The first frontier arrived lit; the next nine waited in parchment mist.
7. **The Trail of Eras:** One road, ten eras, and the same two travelers.
8. **What it's for:** It was always for the walk home—and the hands that inherit the wheel.
9. **The sign-off:** Hat tipped, pan raised: see you on the claim.

These are suggestions only. Nothing was written into `marketing/outbox/`, and owner approval remains mandatory before publication.
