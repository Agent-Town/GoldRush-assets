# Town plate pilot

`build_town_plate.py` rebuilds the Wave 2 plate plus its joined parcel decoration, the shared texture, source `.blend`, exported `.glb`, and locked-camera evidence. It reads canonical building positions, footprints, approaches, and shipped-prop clearances from the existing project sources instead of duplicating them by hand. The palette for every barrel, crate, sack, hitching post, rope coil, bucket, unlit lantern, pictogram board, plank, and planter is reserved inside the plate's existing 2048² atlas, so the runtime interface remains one GLB, one mesh, and one material.

Run from the repository root with Blender 5.1:

```bash
/Applications/Blender.app/Contents/MacOS/Blender \
  --background \
  --python assets/pilots/plaza-props-3d/build_plaza_props.py \
  -- pan_monument

/Applications/Blender.app/Contents/MacOS/Blender \
  --background \
  --python assets/pilots/town-plate-3d/build_town_plate.py

bash scripts/reexport-pilot.sh \
  assets/pilots/town-plate-3d/town-plate.blend

bash scripts/reexport-pilot.sh \
  assets/pilots/plaza-props-3d/pan_monument.blend

/Applications/Blender.app/Contents/MacOS/Blender \
  --background \
  --python assets/pilots/town-plate-3d/verify_town_plate.py

python3 assets/pilots/town-plate-3d/verify_road_wear.py
```

The verifier checks both GLBs' budgets and material contracts, ray-casts the saved joined plate mesh at every canonical walk-route, plaza, and building-pad sample, checks the authored decoration-clearance contract, and compares both checked/re-exported pairs byte for byte. Evidence is written under `artifacts/town-plate-3d/`.

The saved Town plate `.blend` and `.glb` contain the plate and joined Wave 2 decoration only. The corrected Pan Monument remains in its existing plaza-prop asset because Town already mounts it independently. Buildings and all other shipped props are imported temporarily for evidence after the plate is saved and exported.

`render_current_references.py` always renders E1, the E4 Motor town, its motor-caravan detail, and the submerged E5 town directly from the current GLBs and manifests. No prior PNG is an input. The F-3DC-04 verifier compares the rebuilt plate with its ratified main base and requires identical route coordinates, mesh payload, triangle count, and flat-walk values while proving that only the embedded atlas changed.
