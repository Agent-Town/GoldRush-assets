# Salvage King's Claw production model

Deterministic plate-built GLB for the E8 descending boss, authored from the art-batch-026 intact and landed plates on base `32715b4d2f54a84bffd8d42925a3c0c0c531cb07`.

- Production nodes: `winch`, `anchor_feet`, `crown`.
- Landing morphs: `Landing_SprungWinch`, `Landing_SettledAnchorFeet`, `Landing_DarkCrown`.
- 10,164 triangles; one embedded 1024-square, non-emissive painted atlas; no cameras, lights, or animations.
- Base-center origin; 11.4 x 11.4 unit footprint and 10.031203 units tall.
- The intact basis is the descending state. Enabling all three morphs creates the landed future-yard state: sprung paired drums, spread/buckled anchor claws, dark shuttered crown, and two lowered rope ladders. The production model contains no people.

Build, evidence, and gate:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/salvage-claw-3d/build_salvage_claw.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/salvage-claw-3d/render_salvage_claw.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/salvage-claw-3d/verify_salvage_claw.py
bash scripts/reexport-pilot.sh assets/pilots/salvage-claw-3d/salvage-claw.blend
```

`renders/salvage-claw-reference-ab.png` compares both current source plates with the matching production states. `renders/salvage-claw-turntable.png` is the all-angle wrap audit. `renders/salvage-claw-landing-states.png` isolates each named morph, and `renders/salvage-claw-mare-run-camera.png` proves the silhouette over the current Mare Claim terrain at the production camera angle. Every board carries the fresh base SHA.
