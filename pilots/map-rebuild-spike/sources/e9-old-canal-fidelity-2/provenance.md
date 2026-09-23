# Old Canal — native surfaces and supported drives

2026-09-24. Native atlas reused byte-for-byte from `sources/e9-dome-basin-fidelity-2/native-material-swatches-v2.png`; generation/edit prompts and original outputs recorded there. `sips -z 1024 1024` supplies the embedded runtime atlas. No paid raster API.

Frozen input blend/contract are Old Canal’s own prior pack. `refine-canal-drives.py` projects physical UVs and joins the authored upper colored wheels to a grounded central drive, bearing housings, return brackets, spokes and stepped lower feet. Existing wheel centers, geometry and all source bounds remain exact. Survey rig/outflow gate mesh and UV geometry remain unchanged; all five GLBs share the new atlas. New parts rename the UV layer to `LandmarkAtlasUV` before joining. Run with Blender from the game root.

Runtime low masonry and paint refinements live in the game’s presentation/render owners. They never change sampled height, masks, route points, canal choices, water/backfill bands, mounts or collision truth.
