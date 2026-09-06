# Dredge-Queen 3D pilot

This package translates the two owner-ratified E5 plates into the production body for the shipped Dredge-Queen component-boss seam. The intact plate and aligned Act-3 plate are the sole shape and paint authority:

- `assets/raw/boss-dredge-queen.png`
- `assets/raw/boss-dredge-queen-damage.png`

The model keeps the plate's long armored corsair hull, huge forward crane-claw, separately readable port and starboard paddlewheels, fat aft loot hold, oxblood sail with ghosted crossed-pickaxe paint, warm brass, and restrained teal lenses. The single atlas carries real engraved line density and palette sampled from the intact plate; the damage morphs follow the aligned Act-3 plate.

## Production contract

- `dredge-queen.glb`: base-centered, 8.0 units long, 4.983127 wide, and 5.333330 high.
- 11,832 triangles under the 12,000 ceiling.
- One shared non-emissive material with one embedded 1024 x 1024 PNG atlas; metallic `0`, roughness `0.9`.
- Exactly four named component meshes, aligned with the existing runtime component ids:
  - `claw` -> `Damage_SlackClaw`
  - `paddle_port` -> `Damage_BrokenPortPaddle`
  - `paddle_starboard` -> `Damage_BrokenStarboardPaddle`
  - `hold` -> `Damage_CrackedLootHold`
- Exactly one morph target per component with default weight `0`.
- Zero cameras, lights, animations, external textures, or helper meshes in the BLEND and GLB.
- Byte-identical saved-BLEND re-export under Blender 5.1.2.
- No runtime or simulation edits. The factory replaces the existing primitive presentation through the railcar/crawler-style seam.

The morphs are silhouette events rather than color swaps. The claw boom sags and drops its grab; each paddlewheel bends outward, loses its station height, and throws separate broken paddles; the hold lids split, the aft armor collapses, cargo spills, and the corsair sail is struck down. Port and starboard remain independently targetable because they gate Act 2 separately.

## Evidence

- `renders/dredge-queen-deepwater-run-camera.png`: the intact GLB at W5 `(36, -20)` over the shipped Deepwater Claim terrain, using the production 48-degree FOV and `(0, 26.2, 18.3)` camera direction, shortened only for review coverage.
- `renders/dredge-queen-turntable.png`: four intact three-quarter views.
- `renders/dredge-queen-damage-states.png`: claw, port paddle, starboard paddle, and hold failures, each from a component-facing angle.
- `renders/dredge-queen-intact-act3.png`: same camera, light rig, and framing before/after all four damage morphs. The damage state changes 9.44% of pixels above 16/255 while retaining the intact silhouette and nearly identical average luminance.
- `renders/dredge-queen-reference-ab.png`: intact source plate beside the on-tile run-camera render.
- `renders/dredge-queen-act3-reference-ab.png`: aligned Act-3 plate beside all four damage morphs active.
- `renders/dredge-queen-damage-metrics.json`: image-difference, luminance, and edge-energy telemetry for the same-camera comparison.
- `renders/dredge-queen-asset-contract.json`: parsed GLB contract, source hashes, runtime offsets, and byte-identical re-export proof.

The Deepwater terrain, review water plane, buoys, cameras, and lights are evidence-only and are never exported with the boss.

## Rebuild and verify

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/dredge-queen-3d/build_dredge_queen.py
bash scripts/reexport-pilot.sh assets/pilots/dredge-queen-3d/dredge-queen.blend
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/dredge-queen-3d/verify_dredge_queen.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/dredge-queen-3d/render_dredge_queen.py
```
