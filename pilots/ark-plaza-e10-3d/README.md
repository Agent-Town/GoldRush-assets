# E10 Ark Plaza production pilot

Fresh-build capstone site for the Town Sites ladder. The production interface is `ark-plaza-e10.glb`; `ark-plaza-e10.blend` and `build_ark_plaza.py` retain shipped E10 plates from main `d944dc7ebd690141d52f363d38aa6dc1a83f4343`. The town-layout pin is refreshed to the current collision-metadata additions after checking unchanged parsed slots, props and inherited routes.

The plaza is one walkable ship deck: ten subdued lineage inlays and pictogram medallions converge on the separately mounted, unchanged Pan Monument and its recessed running fountain. The north bulkhead/gantry announces the Long Table Hall; the south arch points toward the world-window bridge. Observation pods, hull ribs, service runs, benches, consoles, patched plates, and warm portholes keep the Ark working and inhabited rather than resort-clean.

## Rebuild and verify

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/ark-plaza-e10-3d/build_ark_plaza.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/ark-plaza-e10-3d/verify_ark_plaza.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/ark-plaza-e10-3d/render_current_references.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/ark-plaza-e10-3d/render_ark_plaza.py
```

Final contract: 19,676 / 20,000 triangles; one node/mesh/primitive; one embedded 1024 atlas/material; zero cameras, lights, or animations; byte-identical saved-BLEND re-export; inherited walk-route maximum `0.0419939` across the established `-0.45 / 0 / +0.45m` actor corridor against the `0.05` ceiling. Evidence-only Pan mount, stars, lights, camera, and overlays never enter the GLB.

Factory refresh 2026-09-09: current saved-source re-export is byte identical and the full recipe reproduces geometry, UVs, normals and packed texture. That initial ordering gap is resolved by the canonical source repair below. The 2048 atlas remains above the current finale-family 1024 cap. No source models or runtime changed in that initial pin-only refresh. Evidence and runnable check: `artifacts/map-art-repairs-20260908/ark-factory-01/README.md`.

Canonical source repair: the builder stores existing triangles in stable cyclic/face order, retaining UVs, smoothing and explicit corner normals. Candidate/repeat/full saved-source exports are byte identical at `c4dcc21aa07f714fa3be7828711faf4c52989bcf49e79efba8ab52fa429e1dfc`. Production BLEND/GLB now use that source. Geometry/UVs remain exact and the measured custom-normal encoding change is at most 0.02421 degrees. The 2048 atlas remains unchanged and over cap. See `artifacts/map-art-repairs-20260908/ark-factory-02/checkpoint.json` and `visual-review.md`.

Texture cap repair supersedes the earlier over-cap checkpoint: the original 2048 atlas computation now embeds a 1024 derivative, with unchanged raw art and exact geometry/UV/normal/index buffers. Final source/recipe/re-export SHA is `3751c97243834be03564e8b74749b7af88b4cd1a44f0d6337d3b5929eea50ff6`; its factory exception is removed. See `artifacts/map-art-repairs-20260908/ark-texture-01/checkpoint.json`. Runtime terrain intersection and route coverage remain separate open scene issues.
