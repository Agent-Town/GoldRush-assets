# Codex Art Run — E4 batch 02 / batch-017 enemies + Land-Yacht

Date: 2026-07-14  
Tool path: Codex native `image_gen` only  
Task: `/Users/robin/Claude/Projects/Gold Rush/tasks/running/art--20260714-182854-art-e4-batch-02.md`

Status: **RAW GENERATED; PENDING-PROCESSING / PENDING-CONSUMPTION.**

Scope was the E4 bundle's A4 enemies and boss pair (the task's “A3 enemy sheets” wording predates the current bundle headings). No alpha extraction, cell extraction, processed output, layer contracts, source, specs, reviews, e2e, or integration files were touched.

## References and prompt law

- `assets/raw/kit-era-4.png` conditioned every new enemy generation.
- `assets/raw/char-railtough-sheet-walk4-a.png` anchored the existing Gold Rush sheet camera and figure band for the Pipeline Rustler.
- `assets/raw/plate-e2-boss-component.png` anchored the boss-component presentation.
- The already accepted native `assets/raw/plate-e4-boss-land-yacht.png` supplied the canonical Land-Yacht identity and was reused as `boss-land-yacht.png` after two allowed new intact attempts failed the six-wheel count.
- Every prompt included the bundle anchor verbatim:

> dust-warm ochres pushed lighter and hazier; machines are riveted steel with brass carryovers and teal agent-glow instruments; exhaust reads as light dust puffs, never black smoke; speed is drawn with engraved motion lines, never blur.

- Every prompt required Frontier Ledger engraving; no readable text/letters/numbers/logos/watermarks; no firearms or gun-like poses; no gore; no Native American enemy imagery; no black smoke; and +20% haze-overlay legibility.
- Sheet prompts required separately authored directions with no mirrors and exact opaque `#ff00ff` backgrounds.

## Final prompt set

1. **Motorgang A/B:** one consistent rust-orange-scarf rider and pipe-frame motorbike as one unit, grapple-chain for crate theft, 4x4 split rows `a=s,se,e,ne`, `b=n,nw,w,sw`, columns wheel roll `0/45/90/135°`, light tire dust only.
2. **Tar Sprite:** one cute-menacing knee-high amber-black tar cartoon with a tiny pilot-light hat and short sticky trail, 4x4 rows `s/e/n/w`, columns squash/rise/bulge/settle; never slime horror.
3. **Pipeline Rustler A/B:** one siphon-crew figure with pump backpack pinned anatomical-left and hose coil anatomical-right, A `4x4` rows `s,se,e,ne`, B `4x5` rows `n,nw,w,sw` plus a fifth siphoning-action row facing `s/e/n/w`; no nozzle-as-gun pose.
4. **Land-Yacht:** reuse the accepted six-wheel E4 identity for the intact plate; edit a matching damaged plate with clearly buckled wheel armor, torn hull plates, cracked teal wheelhouse glazing, and a bent/slack crane while retaining the same framing and target zones.

## Outputs and native jobs

| File | Grid / format | Native job or source | Retakes | State |
|---|---|---|---:|---|
| `enm-motorgang-sheet-a.png` | 4x4; rows s,se,e,ne; roll 0/45/90/135 | `exec-b8cbba6f-dc35-4fc4-8d1d-8eebede74df4` | 0 | PENDING-PROCESSING |
| `enm-motorgang-sheet-b.png` | 4x4; rows n,nw,w,sw; roll 0/45/90/135 | `exec-6d3e5b15-055c-4b6d-a14f-f00db6c5a729` | 0 | PENDING-PROCESSING |
| `enm-tarsprite-sheet.png` | 4x4; rows s,e,n,w; four bubble phases | `exec-95039144-c743-4e44-a350-83f9c036bf85` | 0 | PENDING-PROCESSING |
| `enm-pipeline-rustler-sheet-a.png` | 4x4; rows s,se,e,ne; walk4 | `exec-2eab56ae-b6b8-48ff-bd78-5b0738f0062e` | 0 | PENDING-PROCESSING |
| `enm-pipeline-rustler-sheet-b.png` | 4x5; rows n,nw,w,sw + siphon s/e/n/w | `exec-b9f44c5d-0077-4194-9653-f8d131fe3946` | 0 | PENDING-PROCESSING |
| `boss-land-yacht.png` | 1672x941 RGB full-bleed intact/component plate | reused native run-021 source `ig_067da5e3d3ed9937016a4f5bbef7dc8191a5845a2c1db5111b` | 2 rejected new intact attempts | PENDING-CONSUMPTION |
| `boss-land-yacht-damage.png` | 1672x941 RGB full-bleed damaged/component plate | final `exec-ce25d7be-e80d-4ca4-be34-383681ac3658` | 1 | PENDING-CONSUMPTION |

Rejected intact attempts: `exec-9d631a56-60dd-4248-a9e0-9eddb289a625`, `exec-44b9a2bd-a5e3-438d-8998-85c4936164f1`, and `exec-9bef536b-4bfb-4d6f-8920-5a15ee6c4f70` (initial + two retakes; each reduced the required wheel count). Rejected first damage attempt: `exec-616928f1-4989-45f4-84f2-ab88c0eb7945` (damage too subtle and crane pivot shifted).

Burn count: 10 native calls; 6 accepted new finals plus 1 reused accepted native plate; 4 rejected attempts; no rate-limit or auth errors.

## Raw preparation

The five sheet backgrounds were normalized from native near-magenta to exact opaque `#ff00ff`; no alpha extraction, cell extraction, scaling, despill, or integration was performed. `boss-land-yacht-damage.png` was resampled from 1667x943 to the required 1672x941 RGB plate size without compositional editing.

## Measured QA

| File | Size / grid | Exact key / near-key | Non-key row heights px | Content / canon | Verdict |
|---|---|---:|---|---|---|
| `enm-motorgang-sheet-a.png` | 1254x1254, 4x4 | 67.31% / 0 | 252/241/217/220 | rust-orange scarf, grapple-chain, bike+rider unit; no letters/firearms/gore/black smoke; no mirror processing | PASS |
| `enm-motorgang-sheet-b.png` | 1254x1254, 4x4 | 67.72% / 0 | 248/238/217/289 | same identity/materials; rear and opposite directions authored; no letters/firearms/gore/black smoke | PASS |
| `enm-tarsprite-sheet.png` | 1254x1254, 4x4 | 72.55% / 0 | 250/229/297/229 | pilot-light hat, four bubble phases, cute-menacing not gross; no letters/firearms/gore | PASS |
| `enm-pipeline-rustler-sheet-a.png` | 1254x1254, 4x4 | 75.53% / 0 | 273/268/262/270 | pump/hose silhouette and teal gauge readable; no letters/firearms/gore; no mirror processing | PASS |
| `enm-pipeline-rustler-sheet-b.png` | 1024x1536, 4x5 | 70.19% / 0 | 277/276/307/307/290 | fifth row has four clear downward siphoning poses; head/feet/gear contained; no letters/firearms/gore | PASS |
| `boss-land-yacht.png` | 1672x941 full-bleed | n/a | n/a | accepted E4 identity; two wheel zones, crane, wheelhouse, light pale exhaust; no letters/firearms/gore/black smoke | PASS WITH REUSE |
| `boss-land-yacht-damage.png` | 1672x941 full-bleed | n/a | n/a | matching frame/identity; torn hull, buckled wheels, cracked wheelhouse, bent/slack crane; no letters/firearms/gore/black smoke | PASS |

Independent visual critique caught and caused the damage retake. Remaining raw-reference caveats for fire-side processing: the dense Motorgang/Rustler engraving needs gameplay-zoom validation after extraction; the Rustler's side-pinned gauge/hose routing changes apparent screen side with viewpoint and must not be mirrored during extraction; the accepted boss plate uses perspective/overlap rather than six equally exposed wheel faces, while its three-wheel component inset preserves the modeling contract. These are recorded, not silently promoted to integration-ready.

No processing or integration was performed.
