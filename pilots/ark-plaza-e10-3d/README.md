# E10 Ark Plaza production pilot

Fresh-build capstone site for the Town Sites ladder. The production interface is `ark-plaza-e10.glb`; `ark-plaza-e10.blend` and `build_ark_plaza.py` reproduce it deterministically from shipped E10 plates pinned to main `d944dc7ebd690141d52f363d38aa6dc1a83f4343`.

The plaza is one walkable ship deck: ten subdued lineage inlays and pictogram medallions converge on the separately mounted, unchanged Pan Monument and its recessed running fountain. The north bulkhead/gantry announces the Long Table Hall; the south arch points toward the world-window bridge. Observation pods, hull ribs, service runs, benches, consoles, patched plates, and warm portholes keep the Ark working and inhabited rather than resort-clean.

## Rebuild and verify

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/ark-plaza-e10-3d/build_ark_plaza.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/ark-plaza-e10-3d/verify_ark_plaza.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/ark-plaza-e10-3d/render_current_references.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/ark-plaza-e10-3d/render_ark_plaza.py
```

Final contract: 19,676 / 20,000 triangles; one node/mesh/primitive; one embedded 2048 atlas/material; zero cameras, lights, or animations; byte-identical saved-BLEND re-export; inherited walk-route maximum `0.0419939` across the established `-0.45 / 0 / +0.45m` actor corridor against the `0.05` ceiling. Evidence-only Pan mount, stars, lights, camera, and overlays never enter the GLB.
