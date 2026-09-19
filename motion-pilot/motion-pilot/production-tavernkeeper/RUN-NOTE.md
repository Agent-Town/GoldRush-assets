# Production Tavernkeeper Walk8 Run Note

Date: 2026-07-09
Scope: Tavernkeeper only. No source wiring, no processed-sprite changes, no mirrors.

## Sources

- Turnaround anchor: `assets/raw/turn-tavernkeeper.png`
- Identity references: `assets/raw/turn-tavernkeeper.png`, `assets/raw/townsfolk-tavernkeeper.png`, `assets/processed-full/townsfolk-tavernkeeper.png`
- Pinned asymmetry: Towel and large apron utility pocket are on his LEFT side; front views show them on viewer-right, screen-right profiles show them near/visible, screen-left profiles hide them on the far side.

## Outputs

- Selected down still: `assets/raw/tavernkeeper-start-down.png`
- Selected left still: `assets/raw/tavernkeeper-start-left.png`
- Selected right still: `assets/raw/tavernkeeper-start-right.png`
- Selected up still: `assets/raw/tavernkeeper-start-up.png`
- Final raw sheet: `assets/raw/char-tavernkeeper-sheet-walk8.png`
- Evidence folder: `assets/motion-pilot/production-tavernkeeper/`
- Final selected sheet copy: `assets/motion-pilot/production-tavernkeeper/char-tavernkeeper-sheet-walk8.png`
- Bbox summary: `assets/motion-pilot/production-tavernkeeper/logs/tavernkeeper-start-walk8-summary.json`

Final grid: rows down/left/right/up, 8 frames per row, 280x340 cells, 2240x1360 sheet, opaque `#ff00ff`.

## Credit / Generation Log

Balance before stills: 4robinlehmann@gmail.com — ultra plan, 2187.5 credits
Balance after videos: 4robinlehmann@gmail.com — ultra plan, 1943.5 credits

| Asset | Model | Job ID | Credits | Use |
|---|---|---|---:|---|
| down still | GPT Image 2 | `3b45a57f-75a2-48af-94c4-7787eede062b` | 7 | selected |
| left still | GPT Image 2 | `ade587f6-4019-46c4-aed8-2232ab881ea0` | 7 | selected |
| right still | GPT Image 2 | `1eea3f32-8fe5-4f3f-b901-5e11f036b7fe` | 7 | selected |
| up still | GPT Image 2 | `85196264-5b11-41ee-8dc6-f7a4f14a20ba` | 7 | selected |
| down video take 1 | Seedance 2.0 | `3d7cc954-eabe-4497-af9b-96f99b8a441f` | 18 | rejected, see comparison contact sheet |
| down video take 2 | Seedance 2.0 | `ec9a46e6-857f-4ca2-b289-348762fa3805` | 18 | rejected, see comparison contact sheet |
| down video take 3 | Seedance 2.0 | `01eab2a2-8b25-4d96-ab15-c6371a5600d9` | 18 | selected |
| left video take 1 | Seedance 2.0 | `7318059f-e218-4e95-93fb-d36b8e145554` | 18 | rejected, see comparison contact sheet |
| left video take 2 | Seedance 2.0 | `ec688e5b-b406-4fcb-b610-5d74170d2d5a` | 18 | selected |
| left video take 3 | Seedance 2.0 | `3a2d819a-6632-4717-b2c9-47d48faa3d89` | 18 | rejected, see comparison contact sheet |
| right video take 1 | Seedance 2.0 | `7fe605a8-648c-4728-91c1-13cda512f8ae` | 18 | selected |
| right video take 2 | Seedance 2.0 | `e2f624c3-4d8f-45f6-9367-f48837674358` | 18 | rejected, see comparison contact sheet |
| right video take 3 | Seedance 2.0 | `c8a004a1-6a5c-4392-918a-1ffb8591c776` | 18 | rejected, see comparison contact sheet |
| up video take 1 | Seedance 2.0 | `34bea612-0728-4691-b258-7fe0dc23d2f3` | 18 | rejected, see comparison contact sheet |
| up video take 2 | Seedance 2.0 | `a3685b08-8cd9-4700-ba5a-3fe7fdb24957` | 18 | rejected, see comparison contact sheet |
| up video take 3 | Seedance 2.0 | `7ecadd77-8539-4eba-8a2a-1ffe4ffb4458` | 18 | selected |

## Extraction

- MP4s decoded with `/tmp/gr-imageio-ffmpeg/ffmpeg`; no repo dependency was added.
- Decoded at `fps=2`, 8 frames per selected direction.
- Final grid order: down, left, right, up; no mirrors and no frame reuse across directions.
- Background is opaque `#ff00ff`; cells are bottom-aligned.

## QA Verdicts

| Direction | Selected | Verdict | Drift |
|---|---:|---|---:|
| down | take3 | Pass criteria: tavernkeeper face/body, towel left/viewer-right, grounded heavy front gait. | 5% |
| left | take2 | Pass criteria: true left profile, towel/pocket hidden far-side, no swapped apron detail. | 2.1% |
| right | take1 | Pass criteria: true right profile, left-side towel/pocket visible, no mirrored right-side towel. | 1.7% |
| up | take3 | Pass criteria: true back view, rear apron and towel side hold, no face turn. | 2.4% |

Runtime integration remains pending; no `src/` files were touched.

## 2026-07-10 Re-extraction Fix

Task 068 re-extracted this sheet from the existing selected videos only; no video was regenerated. The final pass used an isolated `/tmp/gr-rembg-venv` rembg/u2net matte and hard alpha threshold after resize, then composited onto the same opaque `#ff00ff` 8x4 grid.

Fresh owner contact sheet: `contact-sheets/tavernkeeper-reextract-owner-contact.png`.
Gate numbers: `alphaBad=0`, `nearMagentaInterior=0`, `enclosedTransparentRegions=0`, `enclosedBackgroundBlobs=0`, `cellGeometry=2240x1360`. Detailed row numbers are in `logs/tavernkeeper-reextract-gates.json`.
