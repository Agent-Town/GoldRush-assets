# Production Baron Walk8 Run Note

Date: 2026-07-09
Scope: Baron only. No source wiring, no processed-sprite changes, no mirrors.

## Sources

- Identity anchors: `assets/raw/kit-the-baron.png` and `assets/raw/turn-baron-coat.png`
- Direction start cells: `assets/processed-full/char-baron-sheet-walk4-a-r*c0.png`
- Existing take-1 videos: `assets/motion-pilot/production-baron/videos/baron-{down,left,right,up}-take1.mp4`

Pinned asymmetry: the ace card belongs on the LEFT side of the Baron's hatband. It is visible in front/left views and hidden or edge-on in right/back views.

The `char-baron-sheet-walk4-a-r2c0.png` right start cell contained the rejected near-side visible ace. Right retakes therefore used `references/baron-right-turnaround-start.png` plus explicit hidden-card prompt language.

## Outputs

- Final raw sheet: `assets/raw/char-baron-sheet-walk8.png`
- Evidence folder: `assets/motion-pilot/production-baron/`
- Final selected sheet copy: `assets/motion-pilot/production-baron/char-baron-sheet-walk8.png`
- Bbox summary: `logs/baron-walk8-summary.json`

Final grid: rows down/left/right/up, 8 frames per row, 425x425 cells, 3400x1700 sheet, opaque `#ff00ff`.

## Generation Log

Take-1 videos were already on disk. This task generated the required two additional takes per direction.

Observed account balance before retakes: 2338.5 credits. Ending balance after retakes: 2194.5 credits. Net new spend: 144 credits. The eight latest Seedance transactions at `2026-07-09T16:16:49Z` through `2026-07-09T16:18:22Z` in `logs/higgsfield-transactions-post.json` are the retake spends.

| Direction | Take | Job ID | Credits | Use |
|---|---:|---|---:|---|
| down | 1 | `4a1dd118-e5ea-41b5-883c-f7a1fc5cf180` | 18 | selected |
| down | 2 | `70913571-b0ae-4fc0-8621-897dcf6831e7` | 18 | rejected - no better than take1, retained larger parchment field |
| down | 3 | `9730cd51-3aee-4c05-b856-62cf31486365` | 18 | rejected - no better than take1, retained larger parchment field |
| left | 1 | `1bc964ec-b2db-4bfd-b6dd-ace7379a3b4d` | 18 | selected |
| left | 2 | `f50c0e5a-ed6a-4997-86d5-12b3f3755290` | 18 | rejected - heavier parchment field |
| left | 3 | `466b1fc4-d51c-4d69-b78d-81b714e802c1` | 18 | rejected - heavier parchment field |
| right | 1 | `0cf51c6a-4364-4454-a3aa-1e35b703fb4e` | 18 | rejected - owner-caught near-side visible ace |
| right | 2 | `50633e02-76dc-4136-a93e-b5252e6e385b` | 18 | selected |
| right | 3 | `bdb3f081-1969-417f-a863-98693f81c4d8` | 18 | rejected - still showed a light near-side card |
| up | 1 | `f476f611-57a5-4bdf-8373-5967d54c5313` | 18 | selected |
| up | 2 | `6474ef48-2808-4c75-9009-cd0e4d088857` | 18 | rejected - no improvement over take1 |
| up | 3 | `71cac1c8-a754-4241-81fa-b2de00819a8d` | 18 | rejected - no improvement over take1 |

## Extraction

- MP4s decoded with `/tmp/gr-imageio-ffmpeg/ffmpeg`; no repo dependency was added.
- Decoded at `fps=2`, 8 frames per selected direction.
- Final grid order: down, left, right, up; no mirrors and no frame reuse across directions.
- Baron band matched the existing walk4 scale: 425x425 cells instead of the hero/jumper 280x340 cells.
- Background is opaque `#ff00ff`; file check found `alphaBad=0`.
- One global selected-sheet scale: `0.4941`.
- Down take1 and right take2 used the scoped silhouette mask because their source videos carried parchment backing; left/up used the normal sand-key extractor.

## QA Verdicts

| Direction | Selected | Verdict | Drift |
|---|---|---|---:|
| down | take1 | Pass: true front walk, Baron identity and scale hold, ace visible on left hatband side. | 1.3% |
| left | take1 | Pass: true left-facing gait, ace visible, coat/mustache identity stable. | 1.8% |
| right | take2 | Pass: true right-facing gait, no near-side visible ace, best corrected right take. | 1.5% |
| up | take1 | Pass: true back/away gait, card hidden/edge-on, footline stable. | 1.0% |

Runtime integration remains pending; no `src/` files were touched.

## 2026-07-10 Re-extraction Fix

Task 068 re-extracted this sheet from the existing selected videos only; no video was regenerated. The final pass used an isolated `/tmp/gr-rembg-venv` rembg/u2net matte and hard alpha threshold after resize, then composited onto the same opaque `#ff00ff` 8x4 Baron band.

Fresh owner contact sheet: `contact-sheets/baron-reextract-owner-contact.png`.
Gate numbers: `alphaBad=0`, `nearMagentaInterior=0`, `enclosedTransparentRegions=0`, `enclosedBackgroundBlobs=0`, `cellGeometry=3400x1700`. Detailed row numbers are in `logs/baron-reextract-gates.json`.
