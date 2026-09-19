# Production Prospector Hover8 Run Note

Date: 2026-07-09
Scope: Prospector only. No source wiring, no processed-sprite changes.

## Outputs

- Final raw sheet: `assets/raw/char-prospector-sheet-hover8.png`
- Evidence folder: `assets/motion-pilot/production-prospector/`
- Final selected contact sheets:
  - `contact-sheets/prospector-down-contact.png`
  - `contact-sheets/prospector-left-contact.png`
  - `contact-sheets/prospector-right-contact.png`
  - `contact-sheets/prospector-up-contact.png`
- Raw video contact sheets: `contact-sheets/*-raw-contact.png`
- Bbox summary: `logs/prospector-hover8-summary.json`

## Generation Log

All four take-1 videos were already on disk. I generated no retakes and spent no additional credits during extraction/QA.

Post-spend balances below are reconstructed from `higgsfield account transactions` plus current account status; other attended-wave jobs existed around this time, so these are the true account balances after the matched Prospector transactions, not a Prospector-only isolated balance.

| Direction | Take | Job ID | Credits | Post-spend balance | Use |
|---|---:|---|---:|---:|---|
| down | 1 | `475075a8-33d4-4936-95a3-b5d0a2c5c289` | 18 | 591.5 | selected |
| left | 1 | `1307bab0-4d89-436a-8316-e87a3d616a51` | 18 | 573.5 | selected |
| right | 1 | `c0bd0015-b45b-48b2-be16-55df33df9c08` | 18 | 555.5 | selected |
| up | 1 | `d76a4842-0288-441e-b34d-211d96f28be4` | 18 | 537.5 | selected |

Total spend for this task's jobs: 72 credits.

## Extraction

- MP4s decoded with the existing isolated `/tmp/gr-imageio-ffmpeg` binary; no repo dependency was added.
- Decoded at `fps=2`, 8 frames per selected direction.
- Cells are 280x340, horizontally centered, vertical bob preserved from the video, opaque `#ff00ff`.
- Final grid order: down, left, right, up; 8 frames per row; no mirrors.

## QA Verdicts

| Direction | Selected take | Altitude band | Verdict |
|---|---:|---|---|
| down | 1 | 29 raw px / 14.7 sheet px | Pass: clean front/down read, no legs, teal jet flicker, rhythmic bob. |
| left | 1 | 97 raw px / 49.1 sheet px | Pass: explicit left view, readable side hover, band is larger but rhythmic rather than drifting. |
| right | 1 | 43.5 raw px / 21.5 sheet px | Pass: explicit right view, stable side silhouette, jet flicker survives. |
| up | 1 | 67.5 raw px / 36.7 sheet px | Pass: back/up read holds, no turn toward camera, hover cycle stays bounded. |

The sheet is produced for review and downstream processing experiments, not marked integration-ready.
