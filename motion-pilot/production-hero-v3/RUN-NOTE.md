# Production Hero Walk8 Restart v3 Run Note

Date: 2026-07-09
Scope: hero only. No source wiring, no processed-sprite changes, no legacy walk4 inputs.

## Sources

- Female identity references only:
  - `assets/raw/turn-hero-e1-outfit.png`
  - `assets/raw/turn-hero-base.png`
- Contaminated legacy walk4 cells were not used.

## Derived Asymmetry Pin

PAN HAND = RIGHT.

Satchel = left hip with right-shoulder strap. The v3 prompts pinned every direction to this: front shows pan in her right hand; left profile hides the far-side pan; right profile shows the near-side right-hand pan; back keeps pan at right hip and satchel at left hip.

## Outputs

- Selected direction stills:
  - `assets/raw/hero-start-down.png` from `stills/hero-start-down-take1.png`
  - `assets/raw/hero-start-left.png` from `stills/hero-start-left-take1.png`
  - `assets/raw/hero-start-right.png` from `stills/hero-start-right-take2.png`
  - `assets/raw/hero-start-up.png` from `stills/hero-start-up-take1.png`
- Final raw sheet: `assets/raw/char-hero-sheet-walk8.png`
- Evidence folder: `assets/motion-pilot/production-hero-v3/`
- Final selected contact sheets:
  - `contact-sheets/hero-down-contact.png`
  - `contact-sheets/hero-left-contact.png`
  - `contact-sheets/hero-right-contact.png`
  - `contact-sheets/hero-up-contact.png`
- Bbox summary: `logs/hero-walk8-v3-summary.json`

## Generation Log

Starting account balance before this v3 run: 2452.5 credits. Ending balance: 2338.5 credits. Net spend: 114 credits.

| Asset | Model | Job ID | Credits | Use |
|---|---|---|---:|---|
| down still | GPT Image 2 | `bf769b80-7e77-49be-b4df-b49990d2a81f` | 7 | selected |
| left still | GPT Image 2 | `2c916932-1f36-47a8-81cd-f2aea0a06946` | 7 | selected |
| right still take 1 | GPT Image 2 | `872358bf-f9cd-45a1-9c01-176591d74a8f` | 7 | rejected: near-side satchel competed with pan |
| right still take 2 | GPT Image 2 | `1c13453f-8c94-404f-ab3d-897feaa0d3d0` | 7 | selected |
| up still take 1 | GPT Image 2 | `c986be5f-03fb-440a-87ee-5cf277feac04` | 7 | selected; recovered from job list after empty wait output |
| up still take 2 | GPT Image 2 | `9114470c-d55a-4044-858d-50fa5f66e394` | 7 | rejected: extra baggage |
| down video | Seedance 2.0 | `06dc8de9-389b-4d13-92dd-786ba1febab7` | 18 | selected |
| left video | Seedance 2.0 | `9a2b5bb9-d6b1-41d5-a49c-c7c30960c82e` | 18 | selected; recovered from job list after empty wait output |
| right video | Seedance 2.0 | `879a65b0-6f5a-4db7-845b-ca70bbc6475e` | 18 | selected; recovered from job list after empty wait output |
| up video | Seedance 2.0 | `8d0ce43c-8c93-4fcd-bfec-5cc3e7c862ce` | 18 | selected |

## Extraction

- MP4s decoded with `/tmp/gr-imageio-ffmpeg/ffmpeg`; no repo dependency was added.
- Decoded at `fps=2`, 8 frames per selected direction.
- Each frame used the v2 connected-background keying and bottom alignment path.
- One global sheet scale: `0.3985`.
- Cell size: 280x340.
- Final grid order: down, left, right, up; 8 frames per row; no mirrors.
- Background is opaque `#ff00ff`.

## QA Verdicts

| Direction | Still verdict | Video/sheet verdict | Drift |
|---|---|---|---|
| down | Pass: young woman; satchel left/viewer-right; pan in right hand/viewer-left. | Pass: female identity holds; pan remains right-hand/viewer-left across all frames. | 0.7% |
| left | Pass: female left profile; satchel visible on near/left side; pan hidden on far/right side. | Pass: pan does not appear in near hand; satchel remains visible; no identity drift. | 1.3% |
| right | Pass on take 2: female right profile; pan is the only near-side carried object; satchel hidden. | Pass: pan remains visible in near/right hand across frames; no near-side satchel. | 0.7% |
| up | Pass on take 1: true back view; satchel left; pan right. | Pass: back-view loop holds; pan stays right, satchel stays left; no turn toward camera. | 4.4% |

The sheet is ready for supervisor gates/review. Runtime integration remains pending; no `src/` files were touched.
