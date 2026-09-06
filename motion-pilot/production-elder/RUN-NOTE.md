# Production Elder Walk8 Run Note

Date: 2026-07-09
Scope: Elder only. No source wiring, no processed-sprite changes, no mirrors.

## Sources

- Turnaround anchor: `assets/raw/turn-elder.png`
- Identity references: `assets/raw/turn-elder.png`, `assets/raw/townsfolk-elder.png`, `assets/processed-full/townsfolk-elder.png`
- Pinned asymmetry: Pipe belongs in his RIGHT hand when visible; teal pendant stays centered on the vest; striped shawl fringe remains over both shoulders.

## Outputs

- Selected down still: `assets/raw/elder-start-down.png`
- Selected left still: `assets/raw/elder-start-left.png`
- Selected right still: `assets/raw/elder-start-right.png`
- Selected up still: `assets/raw/elder-start-up.png`
- Final raw sheet: `assets/raw/char-elder-sheet-walk8.png`
- Evidence folder: `assets/motion-pilot/production-elder/`
- Final selected sheet copy: `assets/motion-pilot/production-elder/char-elder-sheet-walk8.png`
- Bbox summary: `assets/motion-pilot/production-elder/logs/elder-start-walk8-summary.json`

Final grid: rows down/left/right/up, 8 frames per row, 280x340 cells, 2240x1360 sheet, opaque `#ff00ff`.

## Credit / Generation Log

Balance before stills: 4robinlehmann@gmail.com — ultra plan, 1699.5 credits
Balance after videos: 4robinlehmann@gmail.com — ultra plan, 1455.5 credits

| Asset | Model | Job ID | Credits | Use |
|---|---|---|---:|---|
| down still | GPT Image 2 | `1c44d861-49f7-47be-8ff9-7988123bafcf` | 7 | selected |
| left still | GPT Image 2 | `83cf82ce-7760-43bd-b826-ac5f8d4792f5` | 7 | selected |
| right still | GPT Image 2 | `b85fddf6-d3c6-4a7c-b167-6427ce69c845` | 7 | selected |
| up still | GPT Image 2 | `3404b9b4-73cb-4f97-a88d-2f6736ff7203` | 7 | selected |
| down video take 1 | Seedance 2.0 | `d07b6d33-ec0e-4213-a562-ce963057d806` | 18 | rejected, see comparison contact sheet |
| down video take 2 | Seedance 2.0 | `3d22d558-d046-4442-926d-d46bfa6773b7` | 18 | rejected, see comparison contact sheet |
| down video take 3 | Seedance 2.0 | `ba6c55d5-ce61-4a94-8e83-db0f6cca5081` | 18 | selected |
| left video take 1 | Seedance 2.0 | `216eb984-dbf4-4593-83b6-96fb123dd42d` | 18 | rejected, see comparison contact sheet |
| left video take 2 | Seedance 2.0 | `c71a7308-861d-4cb8-8bc5-5baf6e400ee1` | 18 | selected |
| left video take 3 | Seedance 2.0 | `bad7dce2-1ab1-49da-9ab2-f77a95964d9b` | 18 | rejected, see comparison contact sheet |
| right video take 1 | Seedance 2.0 | `aeb1a1f9-5015-4724-8e30-c42647554dc4` | 18 | selected |
| right video take 2 | Seedance 2.0 | `76a91e9f-87f2-40d5-acd4-9e471d322ade` | 18 | rejected, see comparison contact sheet |
| right video take 3 | Seedance 2.0 | `0173c655-f6ee-4c3e-8ab8-f13a51d7be46` | 18 | rejected, see comparison contact sheet |
| up video take 1 | Seedance 2.0 | `83b74d1e-7523-4a08-bc5e-deccce9ffd5e` | 18 | rejected, see comparison contact sheet |
| up video take 2 | Seedance 2.0 | `1811f44d-9a58-4b15-9413-1b6101457d49` | 18 | rejected, see comparison contact sheet |
| up video take 3 | Seedance 2.0 | `1867cb58-ba81-41fa-84f4-ff31d7ed26ed` | 18 | selected |

## Extraction

- MP4s decoded with `/tmp/gr-imageio-ffmpeg/ffmpeg`; no repo dependency was added.
- Decoded at `fps=2`, 8 frames per selected direction.
- Final grid order: down, left, right, up; no mirrors and no frame reuse across directions.
- Background is opaque `#ff00ff`; cells are bottom-aligned.

## QA Verdicts

| Direction | Selected | Verdict | Drift |
|---|---:|---|---:|
| down | take3 | Pass criteria: elderly/frail/kind read, centered pendant, right-hand pipe viewer-left. | 2.2% |
| left | take2 | Pass criteria: true left profile, small aged steps, pipe visible near-side. | 2.5% |
| right | take1 | Pass criteria: true right profile, pipe hidden far-side, no pendant drift. | 2.5% |
| up | take3 | Pass criteria: true back view, shawl back/fringe hold, no face turn. | 3.3% |

Runtime integration remains pending; no `src/` files were touched.

## 2026-07-10 Re-extraction Fix

Task 068 re-extracted this sheet from the existing selected videos only; no video was regenerated. The final pass used an isolated `/tmp/gr-rembg-venv` rembg/u2net matte and hard alpha threshold after resize, then composited onto the same opaque `#ff00ff` 8x4 grid.

Fresh owner contact sheet: `contact-sheets/elder-reextract-owner-contact.png`.
Gate numbers: `alphaBad=0`, `nearMagentaInterior=0`, `enclosedTransparentRegions=0`, `enclosedBackgroundBlobs=0`, `cellGeometry=2240x1360`. Detailed row numbers are in `logs/elder-reextract-gates.json`.
