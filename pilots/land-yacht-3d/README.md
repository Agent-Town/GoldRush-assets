# Land-Yacht boss model

Production GLB for the live E4 Land-Yacht system, modeled from the current intact and damage plates on base `de21f043a8c3b4c69950afbca0c7a612c6826e88`.

- Exact runtime nodes: `wheels`, `crane`, `wheelhouse`.
- One damage morph per node: `Damage_BeachedWheels`, `Damage_SlackCrane`, `Damage_CrackedWheelhouse`.
- 10,632 triangles, one embedded 1024-square non-emissive atlas, no cameras/lights/animations.
- Base-center origin; 9.4 units long. The wheels mesh contains all six physical wheels because the live system exposes one `wheels` damage ID.

`build_land_yacht.py` reuses the accepted Dredge-Queen procedural primitives and atlas bake, while owning all Land-Yacht geometry and morphs locally. `verify_land_yacht.py` checks the exact component IDs against `LandYachtBossSystem.ts`, GLB topology/material/bounds, and byte-identical saved-BLEND re-export. `render_land_yacht.py` creates current-plate A/Bs, the Dust Flats run-camera view, four-angle audit, per-zone damage board, and Act-3 wreck comparison.

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/land-yacht-3d/build_land_yacht.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/land-yacht-3d/verify_land_yacht.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/land-yacht-3d/render_land_yacht.py
```
