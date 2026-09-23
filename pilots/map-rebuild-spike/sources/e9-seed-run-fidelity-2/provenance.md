# Seed Run — native surface reuse and mechanical facade

2026-09-24. `native-material-swatches-v2.png` is the exact native-imagegen atlas generated for this E9 leg, copied from `sources/e9-dome-basin-fidelity-2/` (generation/edit prompt and original paths recorded there). No new raster generator or paid API. `sips -z 1024 1024` supplies this map's atlas.

The frozen input blend/contract are Seed Run's own prior pack. `refine-seed-vault.py` projects physical UV proportions, adds a recessed door/reveals, hinges, handwheel, sight windows, foot bearings and threshold inside the exact center vault envelope. Four peer meshes/UVs remain exact; their shared material atlas changes. Run from game root with Blender `--background --python`. New parts share `LandmarkAtlasUV` before joining; source Jacobian proof rejects collapsed mappings. No layout, mounts, collisions, heights, route or station changes.
