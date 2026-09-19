# E9 Basin Rim plate

Fresh E9 town ground built from base `c272d3a8ba9c36ee2550c7bb55c3fb05edab087e`.

- `basin-rim-plate.blend` and `basin-rim-plate.glb` are the production asset.
- `build_basin_rim_plate.py` deterministically rebuilds both files from pinned current-base inputs.
- `verify_basin_rim_plate.py` checks the GLB contract, Three.js material behavior, actual saved-mesh path/pad heights, and byte-identical re-export.
- `render_current_references.py` rebuilds the E1-E8 working board from current GLBs; old artifact boards are never inputs.
- `render_basin_rim_plate.py` creates the source A/B, prior-site A/B, flat-walk overlay, and four-angle audit.

The GLB is one 12,656-triangle mesh with one embedded 2048-square non-emissive atlas and no camera, light, or animation. All inherited town coordinates remain canonical. The Ice Quarry and Ark yard are new flat site candidates recorded in the layout contract; runtime mounts remain factory-owned. The separately mounted Pan Monument is evidence-only in renders and is not duplicated into the plate.

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/basin-rim-3d/build_basin_rim_plate.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/basin-rim-3d/verify_basin_rim_plate.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/basin-rim-3d/render_basin_rim_plate.py
```
