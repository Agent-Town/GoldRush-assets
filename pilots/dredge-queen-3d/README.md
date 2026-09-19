# Dredge Queen production model

> **2026-09-17, task `boss-models-batch`:** the shipped body is now Astra's rebuild from `92f6cc115` —
> 33,124 triangles, four component meshes, ONE 2048² atlas, and a **second claw morph `Cycle_OpenGrab`**
> that the 2026-09-12 fidelity bake did not have. That morph is the whole reason for the swap: the runtime
> hunk held back by F-SAR-4(a) drives it, and `DredgeQueenBossSystem.inspectDredgeQueen3d` now refuses a
> claw mesh without it. Measured trade: 44,920 -> 33,124 triangles and a 1024² -> 2048² atlas (over the
> bosses cap, grandfathered with its cause in `scripts/glb-contract-guard.baseline.json`), against
> 1,480,976 -> 1,217,764 optimized bytes. The paragraphs below describe the superseded fidelity bake and
> are kept for history (CLAUDE.md §4.10b); `renders-fidelity-e5/` is that bake's evidence.

The current body is `dredge-queen-detail-opus5.glb`. Its shape authority is the intact and damaged `boss-dredge-queen` plates under `assets/raw/`; the `plate-e5` image remains an alternate reference. The earlier `dredge-queen.glb` and its renders are historical pilot evidence.

The fidelity revision restores the rounded hull, two-level domed wheelhouse, paired covered paddle wheels, vaulted hold and torn cloth silhouette. Damage preserves separate claw, port paddle, starboard paddle and hold targets. The lowered claw splays its tips, wheels lose their stance, hold lids open and the flag folds. It is still more compact and simpler than the illustrated ship.

The [asset contract](renders-fidelity-e5/contract.json) owns current dimensions, counts, bindings, identity transforms and export proof. The builder uses the unchanged shared `detail_opus5_kit` and the native-generated `assets/raw/dredge-queen-atlas-fidelity-e5.png`. No paid generation or external texture request is needed.

Rebuild with Blender `--background --threads 1 --python assets/pilots/dredge-queen-3d/build_dredge_queen_detail_opus5.py`, then run `verify_dredge_queen_fidelity.py` with the same flags. The verifier checks the four original bindings, finite normalized shape keys, one embedded 1024 atlas, the 45,000-triangle ceiling, flag/lid clearance and byte-identical saved-Blend re-export.

The production model is adopted. Raw runtime evidence covers 20 desktop/mobile approach, component-damage, hold and wreck states. Shared hull centering aligns approach and interpolated targets; the hold remains at its declared offset and leaves the wreck at the hull anchor. Cached convex hulls place the health bar above the active shape. Atlas emission and fitted labels are calibrated against the actual camera. 32 unchanged mechanics/story/persistence/census checks pass. A subsequent loader-reset regression in the bounds query was reproduced and fixed by declining bounds before model readiness; both reset cases, nine loader cases and actual interpolated movement pass on that guard. Optimized asset delivery is 1,480,976 bytes and renders all 20 states through the actual loader. Broad regression remains pending.

The [layer contract](../../layer-contracts/dredge-queen.v1.json) records native material provenance and current acceptance limits. Evidence lives under `artifacts/boss-fidelity/e5-dredge-queen/`; neutral renders alone are not runtime acceptance. Mobile evidence uses the existing maximum zoom-out and does not prove arbitrary camera fit or full encounter save-state equivalence.
