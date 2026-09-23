# Canyon Works — supported dynamo and layered rim

2026-09-23, fidelity run 9 / E3 leg. Inputs frozen from store `d76ee141dcac825aa29cf4e5d4a868fe845fb1c8`; each input contract binds its corresponding Blender file by SHA-256.

`refine-canyon.py` replaces only the primary dynamo mesh inside the preserved landmark scene. The five authored bounds, four sibling meshes, shared atlas, mounts, inspection stations and collision authority stay unchanged. The 2,552-triangle dynamo reuses the tracked Canyon atlas recipe's existing PNG; no atlas pixel is hand-edited. The small teal dial is passive enamel, not an energized grid connection. The model is static scenery, not an animated or state-driven generator.

`dress-canyon-rim.py` preserves the old sky geometry/UVs and every original apron triangle position, including the 97 seam-closing vertices. The apron gains the unchanged terrain atlas and world depth. Fourteen layered buttresses and fourteen irregular talus pieces use the existing native `assets/raw/ter-canyon-atlas.png`, restricted to its rocky quadrant. All new rock vertices lie outside x ±48 / z ±56. Panorama: 3,980 / 4,000 triangles, three materials. Embedded raw texture is resampled to the existing 2048-square panorama contract; the raw source file remains unchanged. No newly generated bitmap or paid art service is used.

Run both recipes with `/Applications/Blender.app/Contents/MacOS/Blender --background --python <recipe>` from the game checkout. Frozen inputs make reruns independent of the delivered output. Saved-source re-export, geometry authority checks and desktop/phone comparisons live in `artifacts/sol/map-art-campaign-2/run-9/e3-canyon-works/` in the game repo. No scripts or sources outside this map are regenerated.
