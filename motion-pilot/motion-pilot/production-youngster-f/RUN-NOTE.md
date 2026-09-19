# Production Youngster-F Walk8 Run Note

Date: 2026-07-09
Scope: Youngster-F only. No source wiring, no processed-sprite changes, no mirrors.

## Sources

- Turnaround anchor: `assets/raw/turn-youngster-f.png`
- Identity references: `assets/raw/turn-youngster-f.png`, `assets/raw/codex-youngster-f-e1.png`, `assets/raw/townsfolk-youngster-b.png`
- Pinned asymmetry: Lantern hangs from her LEFT hip; twin braids remain part of the silhouette; she is a fully clothed minor in every frame.

## Outputs

- Selected down still: `assets/raw/youngster-f-start-down.png`
- Selected left still: `assets/raw/youngster-f-start-left.png`
- Selected right still: `assets/raw/youngster-f-start-right.png`
- Selected up still: `assets/raw/youngster-f-start-up.png`
- Final raw sheet: `assets/raw/char-youngster-f-sheet-walk8.png`
- Evidence folder: `assets/motion-pilot/production-youngster-f/`
- Final selected sheet copy: `assets/motion-pilot/production-youngster-f/char-youngster-f-sheet-walk8.png`
- Bbox summary: `assets/motion-pilot/production-youngster-f/logs/youngster-f-start-walk8-summary.json`

Final grid: rows down/left/right/up, 8 frames per row, 280x340 cells, 2240x1360 sheet, opaque `#ff00ff`.

## Credit / Generation Log

Balance before stills: 4robinlehmann@gmail.com — ultra plan, 1211.5 credits
Balance after videos: 4robinlehmann@gmail.com — ultra plan, 967.5 credits

| Asset | Model | Job ID | Credits | Use |
|---|---|---|---:|---|
| down still | GPT Image 2 | `47c286ca-1e94-4f85-a71e-feed9b518db4` | 7 | selected |
| left still | GPT Image 2 | `da9dc1dd-a799-4654-ac53-69cf087dad20` | 7 | selected |
| right still | GPT Image 2 | `9dda9b42-9eaa-49f0-b213-8e77e0f49a5c` | 7 | selected |
| up still | GPT Image 2 | `60617820-3bd3-4685-815a-65813facbf82` | 7 | selected |
| down video take 1 | Seedance 2.0 | `7f38bc4a-b9a7-445a-82da-1c1543f650a6` | 18 | rejected, see comparison contact sheet |
| down video take 2 | Seedance 2.0 | `027dfe2b-5835-450c-9cac-3c3409a4bc94` | 18 | selected |
| down video take 3 | Seedance 2.0 | `9820ba33-b28d-47fd-9447-8cd2b87ee2d6` | 18 | rejected, see comparison contact sheet |
| left video take 1 | Seedance 2.0 | `659f2213-cab7-4aa4-87fa-1a415d159812` | 18 | rejected, see comparison contact sheet |
| left video take 2 | Seedance 2.0 | `ed98d44b-4cb2-474b-8643-84667505d572` | 18 | selected |
| left video take 3 | Seedance 2.0 | `882933cf-6373-495e-b162-f8528bd85cbf` | 18 | rejected, see comparison contact sheet |
| right video take 1 | Seedance 2.0 | `38ac7943-f9ca-4874-840d-3dd5f03de22d` | 18 | rejected, see comparison contact sheet |
| right video take 2 | Seedance 2.0 | `ebc686b2-4c33-460a-aedf-4da857e7fe8d` | 18 | selected |
| right video take 3 | Seedance 2.0 | `b0760b83-2de5-45aa-93b6-5aa1896a10d9` | 18 | rejected, see comparison contact sheet |
| up video take 1 | Seedance 2.0 | `8ba5c578-a0d7-4e62-a287-80bd07071086` | 18 | rejected, see comparison contact sheet |
| up video take 2 | Seedance 2.0 | `a34f0bb8-c8b2-4581-b06b-311eef369238` | 18 | selected |
| up video take 3 | Seedance 2.0 | `d6d58edd-b551-4254-bd30-1d17ce9e0fe6` | 18 | rejected, see comparison contact sheet |

## Extraction

- MP4s decoded with `/tmp/gr-imageio-ffmpeg/ffmpeg`; no repo dependency was added.
- Decoded at `fps=2`, 8 frames per selected direction.
- Final grid order: down, left, right, up; no mirrors and no frame reuse across directions.
- Background is opaque `#ff00ff`; cells are bottom-aligned.

## QA Verdicts

| Direction | Selected | Verdict | Drift |
|---|---:|---|---:|
| down | take2 | Pass criteria: girl identity, fully clothed, lantern left/viewer-right, lively short stride. | 1.9% |
| left | take2 | Pass criteria: true left profile, lantern hidden far-side, fully clothed. | 2% |
| right | take2 | Pass criteria: true right profile, lantern visible near-side, fully clothed. | 2% |
| up | take2 | Pass criteria: true back view, straps/braids/lantern side hold, fully clothed. | 7.3% |

Runtime integration remains pending; no `src/` files were touched.

## 2026-07-10 Re-extraction Fix

Task 068 re-extracted this sheet from the existing selected videos only; no video was regenerated. The final pass used an isolated `/tmp/gr-rembg-venv` rembg/u2net matte and hard alpha threshold after resize, then composited onto the same opaque `#ff00ff` 8x4 grid.

Fresh owner contact sheet: `contact-sheets/youngster-f-reextract-owner-contact.png`.
Gate numbers: `alphaBad=0`, `nearMagentaInterior=0`, `enclosedTransparentRegions=0`, `enclosedBackgroundBlobs=0`, `cellGeometry=2240x1360`. Detailed row numbers are in `logs/youngster-f-reextract-gates.json`.
