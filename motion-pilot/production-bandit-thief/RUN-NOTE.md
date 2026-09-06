# Production Bandit-thief Walk8 Run Note

Date: 2026-07-10
Scope: Bandit-thief only. No source wiring, no processed-sprite changes, no mirrors.

## Sources

- Turnaround anchor: `assets/raw/turn-bandit-thief.png`
- Identity references: `assets/raw/turn-bandit-thief.png`
- Pinned asymmetry: small loot satchel hangs on his LEFT hip; short pry hook and rope loop sit on his RIGHT belt; no guns or cartridge belts anywhere.

## Outputs

- Selected down still: `assets/motion-pilot/production-bandit-thief/stills/bandit-thief-start-down-take1.png`
- Selected left still: `assets/motion-pilot/production-bandit-thief/stills/bandit-thief-start-left-take1.png`
- Selected right still: `assets/motion-pilot/production-bandit-thief/stills/bandit-thief-start-right-take1.png`
- Selected up still: `assets/motion-pilot/production-bandit-thief/stills/bandit-thief-start-up-take1.png`
- Final raw sheet: `assets/raw/char-bandit-thief-sheet-walk8.png`
- Evidence folder: `assets/motion-pilot/production-bandit-thief/`
- Final selected sheet copy: `assets/motion-pilot/production-bandit-thief/char-bandit-thief-sheet-walk8.png`
- Bbox summary: `assets/motion-pilot/production-bandit-thief/logs/bandit-thief-walk8-rembg-summary.json`

Final grid: rows down/left/right/up, 8 frames per row, 280x340 cells, 2240x1360 sheet, opaque `#ff00ff`.

## Credit / Generation Log

Balance before stills: 4robinlehmann@gmail.com - ultra plan, 628 credits.
Balance after videos: 4robinlehmann@gmail.com - ultra plan, 384 credits.

| Asset | Model | Job ID | Credits | Use |
|---|---|---|---:|---|
| down still | GPT Image 2 | `25d14a4e-3f0c-432c-90b8-7e890ee45f64` | 7 | selected |
| left still | GPT Image 2 | `3b17a71c-9856-4384-8c24-93bf738292ea` | 7 | selected |
| right still | GPT Image 2 | `fd37dec9-fe73-4f90-aefa-0a3b28cfc0b2` | 7 | selected |
| up still | GPT Image 2 | `052b7719-a752-458c-bdd4-ee85babc27e5` | 7 | selected |
| down video take 1 | Seedance 2.0 | `3c24d4e1-0f85-432f-8a70-c78ce0ec032e` | 18 | rejected |
| down video take 2 | Seedance 2.0 | `88fe28b8-dc62-4973-98f5-6cce2df5507d` | 18 | selected |
| down video take 3 | Seedance 2.0 | `97684da6-d944-4d4a-b255-33674ce50876` | 18 | rejected |
| left video take 1 | Seedance 2.0 | `eaf7a0aa-210a-46ca-8a64-d161fd0314c2` | 18 | selected |
| left video take 2 | Seedance 2.0 | `05bc51e3-bac6-453b-9b41-66e14d9c39f2` | 18 | rejected |
| left video take 3 | Seedance 2.0 | `c4376da0-46a7-4a40-8962-b69f36c2ad1c` | 18 | rejected |
| right video take 1 | Seedance 2.0 | `22dacdad-25e0-4c59-97e1-7d427b30cde2` | 18 | selected |
| right video take 2 | Seedance 2.0 | `6ffdbff2-2e91-4df8-8330-e9a890e50f7e` | 18 | rejected |
| right video take 3 | Seedance 2.0 | `20b115bf-cc01-4d15-8cf1-73b3901e354d` | 18 | rejected |
| up video take 1 | Seedance 2.0 | `a17d5da3-b471-4f10-8925-4dcc522391ad` | 18 | selected |
| up video take 2 | Seedance 2.0 | `ea52689f-a2d0-4e85-b304-2217f829ffa5` | 18 | rejected |
| up video take 3 | Seedance 2.0 | `08509676-3365-4422-ad18-8d30e007d82b` | 18 | rejected |

## QA Verdicts

| Direction | Selected | Verdict | Drift |
|---|---:|---|---:|
| down | take2 | Pass: lighter thief build, no firearms, front gait is readable and quick. | ~2% |
| left | take1 | Pass: true left profile, satchel visible on pinned side, nimble stride. | ~2% |
| right | take1 | Pass: true right profile, belt tools visible without firearm read, footline stable. | ~2% |
| up | take1 | Pass: true back view, satchel side and back strap hold, no front-face turn. | ~2% |

Runtime integration remains pending; no `src/` files were touched.
