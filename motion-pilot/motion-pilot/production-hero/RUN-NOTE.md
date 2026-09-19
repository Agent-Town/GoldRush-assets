# Production Hero Walk8 Run Note

Date: 2026-07-09
Scope: hero only. No source wiring, no processed-sprite changes.

## Outputs

- Final raw sheet: `assets/raw/char-hero-sheet-walk8.png`
- Evidence folder: `assets/motion-pilot/production-hero/`
- Final selected contact sheets:
  - `contact-sheets/hero-down-contact.png`
  - `contact-sheets/hero-left-contact.png`
  - `contact-sheets/hero-right-contact.png`
  - `contact-sheets/hero-up-contact.png`
- Rejected/alternate contact sheets: `contact-sheets/*-take1-contact.png`, `contact-sheets/*-take2-contact.png`
- Bbox summary: `logs/hero-walk8-summary.json`

## Generation Log

Observed starting balance before this run: 753.5 credits. Each Seedance 2.0 job cost 18 credits. The account changed plan and received a subscription reset/grant during the run, so the balances below are generation-local, excluding concurrent/external account events.

| Direction | Take | Job ID | Credits | Generation-local balance | Use |
|---|---:|---|---:|---:|---|
| down | 1 | `404a9bf6-a4a2-4e82-849c-0ac22cdc4d59` | 18 | 735.5 | selected |
| left | 1 | `5fdd093d-4dc6-4d14-89a3-6e6e681021f2` | 18 | 717.5 | selected |
| right | 1 | `1b7df91a-dee4-44f1-9029-febccfca7bee` | 18 | 699.5 | selected |
| up | 1 | `a56879c6-f2c8-4732-a69b-e8a0b7a59866` | 18 | 681.5 | rejected: turned/front-facing |
| down | 2 | `2274870c-d9b5-474b-9a67-8b8198f1f953` | 18 | 663.5 | rejected: parchment background, still masculine |
| right | 2 | `90b490d3-5b4f-47e5-a917-47c880a39e1a` | 18 | 645.5 | rejected: parchment background, still masculine |
| up | 2 | `7910a7a8-fd6b-426b-85a1-c45277a2fb11` | 18 | 627.5 | selected with caveat |

Total spend for this task's jobs: 126 credits.

## Extraction

- MP4s decoded with `imageio-ffmpeg` installed to `/tmp/gr-imageio-ffmpeg`; no repo dependency was added.
- Decoded at `fps=2`, 8 frames per selected direction.
- Cells are 280x340, bottom-aligned, opaque `#ff00ff`.
- Final grid order: down, left, right, up; 8 frames per row; no mirrors.

## QA Verdicts

| Direction | Selected take | Drift | Verdict |
|---|---:|---|---|
| down | 1 | 657-674px, 2.6% | Fail: gait and drift are usable, but the face reads too masculine. Take 2 did not fix identity and broke background keying. |
| left | 1 | 806-821px, 1.9% | Pass: best identity/readability of the set, stable footline, coherent side gait. |
| right | 1 | 735-750px, 2.0% | Fail: gait and drift are usable, but the face reads too masculine. Take 2 did not fix identity and broke background keying. |
| up | 2 | 811-830px, 2.3% | Fail: retake stopped the front-facing turn, but it reads as side/back rather than a true up/back view. |

The sheet is produced for review and downstream processing experiments, not marked integration-ready.

## 2026-07-10 Re-extraction Fix

Task 068 re-extracted this sheet from the existing selected videos only; no video was regenerated. The final pass used an isolated `/tmp/gr-rembg-venv` rembg/u2net matte and hard alpha threshold after resize, then composited onto the same opaque `#ff00ff` 8x4 grid.

Fresh owner contact sheet: `contact-sheets/hero-reextract-owner-contact.png`.
Gate numbers: `alphaBad=0`, `nearMagentaInterior=0`, `enclosedTransparentRegions=0`, `enclosedBackgroundBlobs=0`, `cellGeometry=2240x1360`. Detailed row numbers are in `logs/hero-reextract-gates.json`.
