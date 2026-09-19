# Old Digger production model

Deterministic plate-built GLB for the E9 ancient terraformer, authored from the art-batch-026 working and gentle plates on base `32715b4d2f54a84bffd8d42925a3c0c0c531cb07`.

- Production nodes: `bucket_wheel_port`, `bucket_wheel_starboard`, `gantry`, `tape_deck`.
- Redemption morphs: `Redemption_GentleBuckets`, `Redemption_SafeGantry`, `Redemption_TealTapeDeck`.
- 7,192 triangles; one embedded 1024-square, non-emissive painted atlas; no cameras, lights, or animations.
- Base-center origin; 12.4 units long, 3.16317 deep, and 6.603573 tall.
- There is deliberately no damage or kill state. Enabling all three morphs keeps the machine intact while the bucket wheels align for the corrected canal, safe gantry rails and boarding steps deploy, and the amber tape-deck heart changes to teal. The dirty crossed-pickaxes crest remains physically unchanged.
- The production GLB contains no children or other people; the safe rail and steps carry the gentle plate's human-use read without duplicating character assets.

Build, evidence, and gate:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/old-digger-3d/build_old_digger.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/old-digger-3d/render_old_digger.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/old-digger-3d/verify_old_digger.py
bash scripts/reexport-pilot.sh assets/pilots/old-digger-3d/old-digger.blend
```

`renders/old-digger-reference-ab.png` compares both current source plates with the matching production states. `renders/old-digger-turntable.png` is the all-angle wrap audit. `renders/old-digger-redemption-states.png` isolates the three named non-damage morphs, and `renders/old-digger-basin-run-camera.png` shows working/gentle states on the current Basin Rim plate using the production camera rig. Every board carries the fresh base SHA.

Wheel pivots are exported independently from the existing wheel/hub-cap vertex groups. Runtime drives continuous phase: working, pause to read, then slower gentle work. Wheel phase is transient and resets to the authored pose at a new run; the saved machine position and heading remain persistent.

## Superseded 2026-09-17 — the 2026-09-12 fidelity bake

Task `boss-models-batch` (owner: "Lets do them all") replaced the boss-fidelity land's 16,104-triangle,
three-node `bucket_wheels` model with this four-node split-wheel rebuild, because it is the only Old Digger
that carries the contract `OldDiggerBossSystem` needs to turn the wheels (F-SAR-4(b) in
`reviews/sprite-animator-runtime-land.md`). The trade is measured, both ways: 16,104 -> 7,192 triangles and
3,548,152 -> 1,959,340 bytes, against the fidelity pass's extra facade detail. The superseded README text is
kept here rather than deleted (CLAUDE.md §4.10b):

> # Old Digger production model
> 
> The active model is rebuilt by `build_old_digger.py` from the working and gentle Old Digger plates. The fidelity pass gives it open bucket scoops, deeper rims, a taller industrial hall, extended trusses, rounded track ends, a ribbed dome and differentiated lantern towers. A dedicated native atlas separates forged iron, brass and the amber/teal chamber.
> 
> The asset has 16,104 triangles, one embedded 1024-square atlas and three original components: `bucket_wheels`, `gantry`, `tape_deck`. Their original `Redemption_*` morphs preserve the machine intact, change the chamber to teal and deploy access ladders through open gallery exits. No people, cameras, lights, animations or destruction morphs are baked into the GLB. Length stays 12.4 units, with a centered base origin.
> 
> Runtime placement now samples the terrain under cached contact points and fits the visual machine to its footprint. Simulation positions and survey/boarding/damage rules remain planar. Glass emission uses the dedicated atlas middle-row cells, so the entire machine no longer glows or turns teal.
> 
> Rebuild and validate with Blender running `build_old_digger.py` then `verify_old_digger.py`. The latter verifies the saved-Blend re-export and writes `old-digger-asset-contract.json`. The original geometry helpers remain in `build_dredge_queen.py`; its atlas generator is not invoked by this model.
> 
> Current hashes and native provenance are in `assets/layer-contracts/old-digger.v1.json` at the repository root. Evidence is under `artifacts/boss-fidelity/e9-old-digger/`. V6 is adopted; build and re-export pass. Eight unchanged encounter tests, production/reload, optimized contact and lifecycle checks pass; limits are recorded in `reviews/sol-boss-fidelity-e9-old-digger.md` at the repository root. The gentle chamber now uses its normalized separation to stay behind the cage. Historical renders in this directory are earlier evidence, not current acceptance images. The model remains simpler than the reference, particularly in facade detail and human activity.
