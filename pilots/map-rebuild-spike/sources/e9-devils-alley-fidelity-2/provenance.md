# Devil’s Alley — native surfaces and wind-anchor fittings

2026-09-24. `native-material-swatches-v2.png` is the exact native-imagegen atlas generated for this E9 leg, copied from `sources/e9-dome-basin-fidelity-2/` (generation/edit prompts and original paths recorded there). No new raster generator or paid API. `sips -z 1024 1024` supplies this map’s atlas.

The frozen input blend/contract are Devil’s Alley’s own prior pack. `refine-wind-anchors.py` projects physical UV proportions and adds attached gauges, anchor bolts, spindle collars and drive bands inside all three exact source envelopes. Two gate peer meshes/UVs remain exact; their shared atlas changes. Run from game root with Blender `--background --python`. New parts share `LandmarkAtlasUV` before joining; Jacobian evidence reports zero collapsed area. No safety ring, layout, mount, collision, terrain, route or station changes.
