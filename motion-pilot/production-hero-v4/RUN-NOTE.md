# Production Hero v4 Belt-Pan Attempt

Date: 2026-07-11
Scope: hero v4 belt-pan restart attempt plus owner-verdict investigation for tavernkeeper/youngster side rows. This is evidence-only and **not READY-FOR-GATES**.

## Sources

- Native image reference inputs: `assets/raw/turn-hero-e1-outfit.png`, `assets/raw/turn-hero-base.png`
- Native image output copied to: `assets/motion-pilot/production-hero-v4/hero-v4-native-four-view-reference.png`
- Cropped start stills: `stills/hero-start-{down,left,right,up}.png`

## Belt-Pan Ruling

Owner verdict 2026-07-11: "one side pan... can be at the belt, not in the hand".

Prompt clause used for every Seedance v4 video:

> THE BELT-PAN CLAUSE: the brass pan HANGS AT HER RIGHT BELT/HIP in every frame; BOTH HANDS FREE; the pan is never held in either hand.

## Generation Log

Starting balance before this task: 2024 credits. Ending balance after the attempted retakes: 1880.75 credits.

| Asset | Model | Job ID | Params | Use |
|---|---|---|---|---|
| hero v4 four-view still sheet | native image_gen | local file under `$CODEX_HOME/generated_images/019f4df9-1a3a-71e0-a218-1a267b8afcfe/` | n/a | source still sheet accepted as reference only |
| down video take 1 | Seedance 2.0 | `2859dbe9-2013-434f-9199-8042fb3c1e03` | 1:1, 4s, 720p, no audio | rejected: background/key crumbs |
| left video take 1 | Seedance 2.0 | `29121f4e-1e6e-4a9e-90f9-73d1c5fe9cd0` | 1:1, 4s, 720p, no audio | rejected: not gate-ready; background/key crumbs |
| right video take 1 | Seedance 2.0 | `d11b160d-40a7-4f44-8dfb-d4150e3cb267` | 1:1, 4s, 720p, no audio | rejected: background/key crumbs |
| up video take 1 | Seedance 2.0 | `bfca6c6b-f1c9-47e8-9dab-32b5a1335d35` | 1:1, 4s, 720p, no audio | rejected: turned/front-facing instead of back view |

## QA Verdict

Not ready. `char-hero-sheet-walk8.png` was composed inside this evidence folder for inspection only, then the active raw `assets/raw/char-hero-sheet-walk8.png` was restored from `production-hero-v3`.

| Direction | Facing | Belt-pan | Footline/key | Verdict |
|---|---|---|---|---|
| down | front | belt/right-side intent mostly visible | visible parchment edge/key crumbs | reject |
| left | side | belt-pan partly obscured by satchel/profile | visible parchment edge/key crumbs | reject |
| right | side | belt-pan visible at hip | visible parchment edge/key crumbs | reject |
| up | failed; front-facing | not a back-view validation | large parchment field retained | reject |

## Owner-Verdict Findings

- Tavernkeeper: existing selected `right` evidence still shows the same left-profile/nose-screen-right side as the `left` row; no non-mirrored opposite-side source was found in the existing selected takes.
- Youngster-M: all existing selected/alternate `left` takes show the visible lantern side and nose-screen-right profile. Retakes 4-6 used the turnaround crop but inherited that same side; they do not satisfy the no-mirror/opposite-side requirement.
- Because the task says "no mirrors", deterministic horizontal flipping was not used as a final fix.

## Required Next Attempt

Generate fresh native start stills for the missing opposite-side profiles first, then run Seedance from those starts with the correct 1:1/4s/no-audio params. For hero v4, run best-of-3 from the native belt-pan starts and reject any up/back take that turns front-facing.
