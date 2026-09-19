# Production Youngster-M Walk8 Run Note

Date: 2026-07-09
Scope: Youngster-M only. No source wiring, no processed-sprite changes, no mirrors.

## Sources

- Turnaround anchor: `assets/raw/turn-youngster-m.png`
- Identity references: `assets/raw/turn-youngster-m.png`, `assets/raw/codex-youngster-m-e1.png`, `assets/raw/townsfolk-youngster-a.png`
- Pinned asymmetry: Lantern hangs from his LEFT hip; suspenders and vest stay fixed; he is a fully clothed minor in every frame.

## Outputs

- Selected down still: `assets/raw/youngster-m-start-down.png`
- Selected left still: `assets/raw/youngster-m-start-left.png`
- Selected right still: `assets/raw/youngster-m-start-right.png`
- Selected up still: `assets/raw/youngster-m-start-up.png`
- Final raw sheet: `assets/raw/char-youngster-m-sheet-walk8.png`
- Evidence folder: `assets/motion-pilot/production-youngster-m/`
- Final selected sheet copy: `assets/motion-pilot/production-youngster-m/char-youngster-m-sheet-walk8.png`
- Bbox summary: `assets/motion-pilot/production-youngster-m/logs/youngster-m-start-walk8-summary.json`

Final grid: rows down/left/right/up, 8 frames per row, 280x340 cells, 2240x1360 sheet, opaque `#ff00ff`.

## Credit / Generation Log

Balance before stills: 4robinlehmann@gmail.com — ultra plan, 1455.5 credits
Balance after videos: 4robinlehmann@gmail.com — ultra plan, 1211.5 credits

| Asset | Model | Job ID | Credits | Use |
|---|---|---|---:|---|
| down still | GPT Image 2 | `38770d22-a546-43dd-8f05-c2869d207f56` | 7 | selected |
| left still | GPT Image 2 | `4b4304cd-969b-4b8f-929a-6cc79402e2ec` | 7 | selected |
| right still | GPT Image 2 | `b678332e-ca54-4b49-a8a8-7f8be42e4665` | 7 | selected |
| up still | GPT Image 2 | `25fbbefa-175b-40b8-8dde-a1a2d15fa2a9` | 7 | selected |
| down video take 1 | Seedance 2.0 | `497ffb80-f927-44a4-8b8a-1b6470fe13c9` | 18 | rejected, see comparison contact sheet |
| down video take 2 | Seedance 2.0 | `fd203a86-fcb0-44c8-98f6-e21f0e71c443` | 18 | selected |
| down video take 3 | Seedance 2.0 | `1d4a310e-5d5d-4dc9-a312-c10ef13243df` | 18 | rejected, see comparison contact sheet |
| left video take 1 | Seedance 2.0 | `4f040adb-eb9d-4bd5-a897-51b5aee6e6e1` | 18 | rejected, see comparison contact sheet |
| left video take 2 | Seedance 2.0 | `77e43fae-7097-4ab8-bee3-905b0dd01f0b` | 18 | selected |
| left video take 3 | Seedance 2.0 | `f9fef6d5-1eba-426a-8988-39a5a6e14ef5` | 18 | rejected, see comparison contact sheet |
| right video take 1 | Seedance 2.0 | `7537c20d-168e-4102-9c9c-c1bfc8923a56` | 18 | rejected, see comparison contact sheet |
| right video take 2 | Seedance 2.0 | `147a7d34-6740-4613-ad19-d0e784bd5386` | 18 | selected |
| right video take 3 | Seedance 2.0 | `e37b5d9a-68ba-408f-91cd-8e4fa65d6b51` | 18 | rejected, see comparison contact sheet |
| up video take 1 | Seedance 2.0 | `22cbe3f8-a96a-4552-a02b-b4535f3cb5ba` | 18 | rejected, see comparison contact sheet |
| up video take 2 | Seedance 2.0 | `c78cc03c-c607-4d7c-b3c1-5148372d2dc4` | 18 | selected |
| up video take 3 | Seedance 2.0 | `55c9bd1c-3b35-43a4-8248-2eee6c40552c` | 18 | rejected, see comparison contact sheet |

## Extraction

- MP4s decoded with `/tmp/gr-imageio-ffmpeg/ffmpeg`; no repo dependency was added.
- Decoded at `fps=2`, 8 frames per selected direction.
- Final grid order: down, left, right, up; no mirrors and no frame reuse across directions.
- Background is opaque `#ff00ff`; cells are bottom-aligned.

## QA Verdicts

| Direction | Selected | Verdict | Drift |
|---|---:|---|---:|
| down | take2 | Pass criteria: boy identity, fully clothed, lantern left/viewer-right, lively short stride. | 4.5% |
| left | take2 | Pass criteria: true left profile, lantern hidden far-side, fully clothed. | 2% |
| right | take2 | Pass criteria: true right profile, lantern visible near-side, fully clothed. | 2.4% |
| up | take2 | Pass criteria: true back view, suspenders/lantern side hold, fully clothed. | 2.4% |

Runtime integration remains pending; no `src/` files were touched.

## 2026-07-10 Re-extraction Fix

Task 068 re-extracted this sheet from the existing selected videos only; no video was regenerated. The final pass used an isolated `/tmp/gr-rembg-venv` rembg/u2net matte and hard alpha threshold after resize, then composited onto the same opaque `#ff00ff` 8x4 grid.

Fresh owner contact sheet: `contact-sheets/youngster-m-reextract-owner-contact.png`.
Gate numbers: `alphaBad=0`, `nearMagentaInterior=0`, `enclosedTransparentRegions=0`, `enclosedBackgroundBlobs=0`, `cellGeometry=2240x1360`. Detailed row numbers are in `logs/youngster-m-reextract-gates.json`.
