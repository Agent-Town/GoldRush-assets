---
source: codex
project: Gold Rush
date: 2026-09-02
type: art-run
---

# art-batch-announcement-v2 — THREE NEW PANELS

## Result

Native Codex `image_gen` with GPT Image 2 only; no Higgsfield, CLI image model, extraction, source/runtime edits, or publication. Exactly three assigned panels landed at the required paths:

- `assets/raw/interview-cartoon-v2-01-same-door.png`
- `assets/raw/interview-cartoon-v2-05-the-board.png`
- `assets/raw/interview-cartoon-v2-09-the-door.png`

Each panel conditioned on its task-assigned shipped cartoon pair for cast continuity plus the assigned contract plate for THE VOICE. Every prompt included this sentence verbatim:

> Gold Rush hand-tinted engraved cartoon panel: warm sepia-gold etched linework with muted watercolor washes, frontier illustration, pictogram speech bubbles with no letters, full-bleed, no text, no gore.

The Door arrived at 1671×941 from the native generator. It received only the precedent-sanctioned one-pixel right-edge canvas normalization necessary to meet the required 1672×941 opaque RGB delivery; the scene content was otherwise untouched. The other two panels arrived at exact size.

## Measured self-QA

All final files are opaque RGB PNGs at exactly 1672×941. Tesseract returned zero recognized characters for each file. Full-resolution corner, board, bubble, lintel, and thumbnail inspection found no credible letters or numbers: all sanctioned visual information is pictographic.

| Panel | Mean luminance | Top-edge SD | SHA-256 | Scene / cast / thumbnail verdict |
|---|---:|---:|---|---|
| 01 — The Same Door | 0.228117 | 0.042634 | `102b4af97f11d10492b8e3b828480803e32259bc57429a511835952305bf2795` | PASS — one wicket and one shared two-visitor queue; both visitors hold tape reels; Robin and round teal-dial Fable foreground the glass-cased reference reel; visiting gear-head machine is visibly not Fable; no candles. |
| 05 — The Board Today | 0.196486 | 0.039010 | `2df06de6ad0b879d648f8244996be353e930371c7019850986f0f11d6b138df6` | PASS — county board reads at thumbnail; small Baron board has exactly three brass crown seats, one hat-crown seat, and one empty question-mark seat; lantern projector and human→machine→machine→machine tape lineage read clearly; Robin and Fable remain on model. |
| 09 — The Door | 0.264763 | 0.089230 | `4d7f5377b319782994fc676c678ba9bd0a06fcd2e59d655424266d90d3f6ca31` | PASS — two visitors enter side-by-side from behind; rider-machine is plainer gear-head stranger, not Fable; exactly one lit lantern over crossed-pans lintel; no other figures; calm unoccupied lower third retained for external caption overlay. |

Across the three-panel pass, Robin remains a warm human gentleman-prospector and Fable remains the non-humanoid round brass Prospector agent with teal dial and pan. The visiting rider-machine is deliberately gear-headed, plainer, and panless. The palette stays inside the sepia-gold parchment and restrained teal anchors. No realistic firearms, gore, watermarks, logos, or hostile treatment of a people is visible. Retakes: 0.

## Prompt set

1. **The Same Door:** morning assay office with one wicket and one queue shared by a stranger prospector and a panless gear-head visitor machine, both carrying tape reels; Robin and Fable foreground the glass-cased reference tape; pictogram-only standings board and reel-check bubble; no candles.
2. **The Board Today:** grand pictogram county standings; a smaller Baron board with exactly three brass crowns, one hat crown, and one empty question-mark seat; a lantern projector's ride cone; the four-figure human→machine→machine→machine reel lineage; Robin and Fable watching.
3. **The Door:** golden-hour open assay-office door, with a stranger prospector and a panless gear-head visitor machine entering together from behind; one lantern above a crossed-pans lintel; quiet river-and-claim lower third held clear for external copy.

## Caption suggestions for attended thread staging

1. **The Same Door:** One door. One line. Every standing can replay.
2. **The Board Today:** The board changed when the machines studied Robin’s tape.
3. **The Door:** Bring your tape. The door is open.

These are staging suggestions only. Nothing was written into `marketing/outbox/`, and owner approval remains mandatory before publication.
