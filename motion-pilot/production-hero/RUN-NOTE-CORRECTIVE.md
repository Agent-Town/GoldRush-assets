# Production Hero Walk8 Corrective Run Note

Date: 2026-07-09
Scope: hero only. No source wiring, no processed-sprite changes.

## Outputs

- Final raw sheet: `assets/raw/char-hero-sheet-walk8.png`
- Evidence folder: `assets/motion-pilot/production-hero/`
- Corrective summary: `logs/hero-walk8-corrective-summary.json`
- Final selected contact sheets:
  - `contact-sheets/hero-down-contact.png`
  - `contact-sheets/hero-left-contact.png`
  - `contact-sheets/hero-right-contact.png`
  - `contact-sheets/hero-up-contact.png`

## Generation Log

The four attended take1 jobs were already created before this task session. Three failed QA and used the one allowed retake. The account had a plan reset/grant between the attended take1 jobs and the retakes, so the balance jumps between those groups.

| Direction | Take | Job ID | Credits | Balance after | Use |
|---|---:|---|---:|---:|---|
| down | 1 | `2006b9d5-c173-4331-9e4d-46e2bb8fe32d` | 18 | 681.5 | selected, QA fail |
| left | 1 | `8b251098-2ae6-4c14-a8d1-6257f862328f` | 18 | 645.5 | selected, QA pass |
| right | 1 | `9a75bcd4-2a06-458b-8dea-63d4b43f903c` | 18 | 627.5 | rejected: asymmetry fail |
| up | 1 | `4a93f647-1e95-4d7e-99f0-d86af9d58af0` | 18 | 609.5 | rejected: side/back, not true up |
| up | 2 | `c3d7a492-6036-432a-93b7-726e410060a0` | 18 | 2752.5 | selected, QA pass |
| down | 2 | `229f8f45-f77b-4f1c-b8c9-02df37729e1f` | 18 | 2734.5 | rejected: beard/masculine, parchment edge |
| right | 2 | `766f20b9-6a6a-4dea-ad84-3539cd2d3bcd` | 18 | 2716.5 | selected, QA fail |

Corrective spend: 126 credits. Ending balance: 2716.5.

## Extraction

- MP4s decoded with `/tmp/gr-imageio-ffmpeg/ffmpeg`; no repo dependency was added.
- Decoded at `fps=2`, 8 frames per selected direction.
- Each raw frame used a 5% trim, connected sand-background key, bottom alignment, and 280x340 canvas.
- Final grid order: down, left, right, up; 8 frames per row; no mirrors.

## QA Verdicts

| Direction | Selected take | Drift | Verdict |
|---|---:|---|---|
| down | corrective take1 | 851-859px, 0.9% | Fail: gait/drift are stable, but identity still reads masculine. Take2 was worse: beard plus parchment edge. |
| left | corrective take1 | 844-860px, 1.9% | Pass: female side read, coherent gait, stable footline. |
| right | corrective take2 | 846-859px, 1.5% | Fail: identity is better than take1, but far-side pan/satchel remains visible, violating the asymmetry rule. |
| up | corrective take2 | 844-856px, 1.4% | Pass: true back view, no face turn, coherent gait. |

The sheet is produced for review and downstream processing experiments, not marked integration-ready.
