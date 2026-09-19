# Production Bandit-base Walk8 Run Note

Date: 2026-07-10
Scope: Bandit-base only. No source wiring, no processed-sprite changes, no mirrors.

## Sources

- Turnaround anchor: `assets/raw/turn-bandit-base.png`
- Identity references: `assets/raw/turn-bandit-base.png`
- Pinned asymmetry: rope coil and grapple hook hang on his LEFT hip; brass teal charm is on his RIGHT chest strap; no guns or cartridge belts anywhere.

## Outputs

- Selected down still: `assets/motion-pilot/production-bandit-base/stills/bandit-base-start-down-take1.png`
- Selected left still: `assets/motion-pilot/production-bandit-base/stills/bandit-base-start-left-take1.png`
- Selected right still: `assets/motion-pilot/production-bandit-base/stills/bandit-base-start-right-take1.png`
- Selected up still: `assets/motion-pilot/production-bandit-base/stills/bandit-base-start-up-take1.png`
- Final raw sheet: `assets/raw/char-bandit-base-sheet-walk8.png`
- Evidence folder: `assets/motion-pilot/production-bandit-base/`
- Final selected sheet copy: `assets/motion-pilot/production-bandit-base/char-bandit-base-sheet-walk8.png`
- Bbox summary: `assets/motion-pilot/production-bandit-base/logs/bandit-base-walk8-rembg-summary.json`

Final grid: rows down/left/right/up, 8 frames per row, 280x340 cells, 2240x1360 sheet, opaque `#ff00ff`.

## Credit / Generation Log

Balance before first attempted stills: 4robinlehmann@gmail.com - ultra plan, 900 credits.
Balance after final videos: 4robinlehmann@gmail.com - ultra plan, 628 credits.

Note: the first still create pass was superseded by a resume-sync mistake before downloads; four unused GPT Image 2 still jobs were created. Net spend for this character was 272 credits instead of the expected 244.

| Asset | Model | Job ID | Credits | Use |
|---|---|---|---:|---|
| down still | GPT Image 2 | `06268d11-cddc-4912-aa82-3b251674a112` | 7 | selected |
| left still | GPT Image 2 | `e47087aa-679e-42d3-9942-0e669c17b312` | 7 | selected |
| right still | GPT Image 2 | `154fbe27-5462-4527-a260-45bda3102eb1` | 7 | selected |
| up still | GPT Image 2 | `55d6592d-de24-41fa-9773-13eb497c66ea` | 7 | selected |
| down video take 1 | Seedance 2.0 | `238e8a58-7e1e-4772-8be7-e909c065d926` | 18 | selected |
| down video take 2 | Seedance 2.0 | `f6276b62-f4d3-4f55-bf05-b25d1bac4ec8` | 18 | rejected |
| down video take 3 | Seedance 2.0 | `155e01d7-eaea-4a4e-a0fd-ed441a3d8361` | 18 | rejected |
| left video take 1 | Seedance 2.0 | `f64994bb-c770-47e6-93c4-bc13038a2749` | 18 | selected |
| left video take 2 | Seedance 2.0 | `2f1defe5-c448-470e-bc29-2fa9abe2b724` | 18 | rejected |
| left video take 3 | Seedance 2.0 | `6629ab64-bdb8-4d54-9895-d725742df3e4` | 18 | rejected |
| right video take 1 | Seedance 2.0 | `0d1982e1-fc37-4fee-a07a-43fad61f2eff` | 18 | rejected |
| right video take 2 | Seedance 2.0 | `0393d656-2f35-4ee4-8e61-80ca1d8b12c9` | 18 | rejected |
| right video take 3 | Seedance 2.0 | `c545af87-ca80-4d83-97aa-0961cd5ab465` | 18 | selected |
| up video take 1 | Seedance 2.0 | `1cea3e81-5ea6-4755-95ee-629f94aa3002` | 18 | selected |
| up video take 2 | Seedance 2.0 | `529af43d-5e0e-4d01-a67b-f7639ce3a26c` | 18 | rejected |
| up video take 3 | Seedance 2.0 | `f871ceac-5dd5-4121-8027-0b652ea8ec2f` | 18 | rejected |

## QA Verdicts

| Direction | Selected | Verdict | Drift |
|---|---:|---|---:|
| down | take1 | Pass: outlaw rustler identity, rope/grapple on left hip, charm visible, no firearms. | ~2% |
| left | take1 | Pass: true left profile, side gear remains readable, wary grounded gait. | ~2% |
| right | take3 | Pass: true right profile, silhouette coherent, side details do not mirror into firearms. | ~2% |
| up | take1 | Pass: true back view, rope side and chest strap/back strap stay coherent, footline stable. | ~2% |

Runtime integration remains pending; no `src/` files were touched.
