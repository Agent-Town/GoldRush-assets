# Production Hero Walk8 Restart v2 Run Note

Date: 2026-07-09
Scope: hero only. No source wiring, no processed-sprite changes, no legacy walk4 inputs.

## Sources

- Female identity references only:
  - `assets/raw/turn-hero-e1-outfit.png`
  - `assets/raw/turn-hero-base.png`
- Contaminated legacy walk4 cells were not used.

## Outputs

- Direction stills:
  - `assets/raw/hero-start-down.png`
  - `assets/raw/hero-start-left.png`
  - `assets/raw/hero-start-right.png`
  - `assets/raw/hero-start-up.png`
- Final raw sheet: `assets/raw/char-hero-sheet-walk8.png`
- Evidence folder: `assets/motion-pilot/production-hero-v2/`
- Final selected contact sheets:
  - `contact-sheets/hero-down-contact.png`
  - `contact-sheets/hero-left-contact.png`
  - `contact-sheets/hero-right-contact.png`
  - `contact-sheets/hero-up-contact.png`
- Bbox summary: `logs/hero-walk8-v2-summary.json`

## Prompt And Purpose

Purpose: rebuild the canonical hero direction stills and walk8 sheet from female turnaround references, then use those stills as video start images.

Stills used gpt-image-2 with both turnaround images as references. The prompt named the hero as a young WOMAN miner, required braid, brimmed hat, tan coat, left-side satchel, brass pan, teal chest lantern, full body, flat sand background, and no text/firearms/gore. Direction prompts added side-specific satchel rules: left profile shows the satchel; right profile hides it.

Videos used Seedance 2.0 with `--start-image assets/raw/hero-start-<dir>.png` and `--image assets/raw/turn-hero-e1-outfit.png`. The prompt kept the female-first wording, locked footline/framing/scale, no turn, no zoom, no text, no firearms, no gore, and one clean 4-second loop.

## Generation Log

Starting account balance before this v2 run: 2696.5 credits. Ending balance: 2596.5 credits. Net spend: 100 credits.

| Asset | Model | Job ID | Credits | Use |
|---|---|---|---:|---|
| down still | gpt-image-2 | `7fcf8fa2-d08b-4af9-b2a5-3cfe86de9fae` | 7 | selected |
| left still | gpt-image-2 | `7cc567ae-6a1b-4245-9026-ddfb6869e0df` | 7 | selected |
| right still | gpt-image-2 | `b08af4c2-0a6c-4b71-bc4d-2f7e5d836f9b` | 7 | selected |
| up still first try | gpt-image-2 | `bf4b4ec7-364d-43ce-9ab1-d3eb1652ae61` | 0 | failed, refunded |
| up still retake | gpt-image-2 | `0cfdc08a-cd45-4f98-816c-47ef567ce68c` | 7 | selected |
| down video | Seedance 2.0 | `2f033aa8-789c-4067-bfd8-abb4e09d50e2` | 18 | selected |
| left video | Seedance 2.0 | `4ae27c2d-6a93-4869-bc15-ab2651d0bd2a` | 18 | selected |
| right video | Seedance 2.0 | `22f03f79-3a84-43b8-addf-61148a486aa8` | 18 | selected |
| up video | Seedance 2.0 | `1fa5ce59-f66e-438c-b83c-daa4111b93f5` | 18 | selected |

## Extraction

- MP4s decoded with `/tmp/gr-imageio-ffmpeg/ffmpeg`; no repo dependency was added.
- Decoded at `fps=2`, 8 frames per selected direction.
- Each frame used connected sand-background keying, tiny disconnected foreground cleanup, one global sheet scale of `0.3801`, bottom alignment, and 280x340 cells.
- Final grid order: down, left, right, up; 8 frames per row; no mirrors.
- Background is opaque `#ff00ff`.

## QA Verdicts

| Direction | Still verdict | Video/sheet verdict | Drift |
|---|---|---|---|
| down | Pass: young woman, braid, left-side satchel, brass pan opposite hand. | Pass: female identity holds across frames, stable front gait. | 4.2% |
| left | Pass: female left profile; satchel visible on her left side. | Pass: side gait coherent; satchel visible; no identity drift. | 1.2% |
| right | Pass: female right profile; satchel hidden/far side; brass pan visible. | Pass: right profile holds; satchel remains hidden enough for the asymmetry rule. | 1.1% |
| up | Pass: true back view, no face turn; satchel on left, pan on right. | Pass: back-view loop holds, no turn toward camera. | 3.6% |

The sheet is ready for supervisor gates/review. Runtime integration remains pending; no `src/` files were touched.
