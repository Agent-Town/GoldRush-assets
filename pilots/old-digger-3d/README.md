# Old Digger production model

Deterministic plate-built GLB for the E9 ancient terraformer, authored from the art-batch-026 working and gentle plates on base `32715b4d2f54a84bffd8d42925a3c0c0c531cb07`.

- Production nodes: `bucket_wheels`, `gantry`, `tape_deck`.
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
