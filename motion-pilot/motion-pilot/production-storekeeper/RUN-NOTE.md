# Production Storekeeper Walk8 Run Note

Date: 2026-07-09
Scope: Storekeeper only. No source wiring, no processed-sprite changes, no mirrors.

## Sources

- Turnaround anchor: `assets/raw/turn-storekeeper.png`
- Identity references: `assets/raw/turn-storekeeper.png`, `assets/raw/townsfolk-storekeeper.png`, `assets/processed-full/townsfolk-storekeeper.png`
- Pinned asymmetry: Pencil is tucked behind his LEFT ear; notebook slips and small vial sit in the LEFT apron pocket; screen-right profiles show these details, screen-left profiles hide them far-side.

## Outputs

- Selected down still: `assets/raw/storekeeper-start-down.png`
- Selected left still: `assets/raw/storekeeper-start-left.png`
- Selected right still: `assets/raw/storekeeper-start-right.png`
- Selected up still: `assets/raw/storekeeper-start-up.png`
- Final raw sheet: `assets/raw/char-storekeeper-sheet-walk8.png`
- Evidence folder: `assets/motion-pilot/production-storekeeper/`
- Final selected sheet copy: `assets/motion-pilot/production-storekeeper/char-storekeeper-sheet-walk8.png`
- Bbox summary: `assets/motion-pilot/production-storekeeper/logs/storekeeper-start-walk8-summary.json`

Final grid: rows down/left/right/up, 8 frames per row, 280x340 cells, 2240x1360 sheet, opaque `#ff00ff`.

## Credit / Generation Log

Balance before stills: 4robinlehmann@gmail.com — ultra plan, 1943.5 credits
Balance after videos: 4robinlehmann@gmail.com — ultra plan, 1699.5 credits

| Asset | Model | Job ID | Credits | Use |
|---|---|---|---:|---|
| turnaround | GPT Image 2 | `b4426a8a-2b6e-410d-b5ea-5a91eaff56a6` | 7 | selected |
| down still | GPT Image 2 | `38fff783-54b2-4070-9c71-d5867f3a1677` | 7 | selected |
| left still | GPT Image 2 | `9ecfadab-45a2-439d-8106-f10ad3984296` | 7 | selected |
| right still | GPT Image 2 | `182e859f-9f86-4253-880b-a15df8b55f8a` | 7 | selected |
| up still | GPT Image 2 | `875e616f-b01b-4c64-82ea-233e152c0437` | 7 | selected |
| down video take 1 | Seedance 2.0 | `9926ca32-74ff-46c6-9c4f-e55545dd79c2` | 18 | rejected, see comparison contact sheet |
| down video take 2 | Seedance 2.0 | `abd2c462-5603-42fb-99f6-a8c984688228` | 18 | rejected, see comparison contact sheet |
| down video take 3 | Seedance 2.0 | `12a5f1ab-804b-47f5-bc25-1c80e7438403` | 18 | selected |
| left video take 1 | Seedance 2.0 | `a25605a5-68b8-43f4-903b-8213973a0ad9` | 18 | rejected, see comparison contact sheet |
| left video take 2 | Seedance 2.0 | `55e8ba1d-34d7-487d-b4fd-714bfe3706d8` | 18 | selected |
| left video take 3 | Seedance 2.0 | `3866918c-b07d-4b72-bd4d-309f162d57b0` | 18 | rejected, see comparison contact sheet |
| right video take 1 | Seedance 2.0 | `6e98439d-3767-4f24-9fd7-d740c93b2194` | 18 | rejected, see comparison contact sheet |
| right video take 2 | Seedance 2.0 | `a5056970-5daa-4ee6-8720-d4929c886177` | 18 | selected |
| right video take 3 | Seedance 2.0 | `c1755a5c-c833-41fb-bcf4-ede92beb1121` | 18 | rejected, see comparison contact sheet |
| up video take 1 | Seedance 2.0 | `e1943910-8d19-48ee-85fd-97d0f54480fe` | 18 | rejected, see comparison contact sheet |
| up video take 2 | Seedance 2.0 | `eef6ebfe-fd93-4f6d-bd17-42238598f734` | 18 | rejected, see comparison contact sheet |
| up video take 3 | Seedance 2.0 | `a87b1cac-37d0-4069-9a4c-ed7e56fff536` | 18 | selected |

## Extraction

- MP4s decoded with `/tmp/gr-imageio-ffmpeg/ffmpeg`; no repo dependency was added.
- Decoded at `fps=2`, 8 frames per selected direction.
- Final grid order: down, left, right, up; no mirrors and no frame reuse across directions.
- Background is opaque `#ff00ff`; cells are bottom-aligned.

## QA Verdicts

| Direction | Selected | Verdict | Drift |
|---|---:|---|---:|
| down | take3 | Pass criteria: storekeeper glasses/mustache/pencil, left pocket tools viewer-right, centered front gait. | 0.6% |
| left | take2 | Pass criteria: true left profile, far-side pencil/tools hidden, no side swap. | 1.7% |
| right | take2 | Pass criteria: true right profile with pencil/pocket tools visible, tidy shopkeeper silhouette. | 1.6% |
| up | take3 | Pass criteria: true back view, apron straps read, no front-face turn. | 1% |

Runtime integration remains pending; no `src/` files were touched.

## 2026-07-10 Re-extraction Fix

Task 068 re-extracted this sheet from the existing selected videos only; no video was regenerated. The final pass used an isolated `/tmp/gr-rembg-venv` rembg/u2net matte and hard alpha threshold after resize, then composited onto the same opaque `#ff00ff` 8x4 grid.

Fresh owner contact sheet: `contact-sheets/storekeeper-reextract-owner-contact.png`.
Gate numbers: `alphaBad=0`, `nearMagentaInterior=0`, `enclosedTransparentRegions=0`, `enclosedBackgroundBlobs=0`, `cellGeometry=2240x1360`. Detailed row numbers are in `logs/storekeeper-reextract-gates.json`.
