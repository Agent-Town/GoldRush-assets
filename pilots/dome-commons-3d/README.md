# Dome Commons E8 plate

This package is the fresh orbital town site after the E6-E7 Mesa chain. It follows the E8 bundle's air-is-the-wall vocabulary: a transparent panel dome over brass/silver ribs, a sealed airlock threshold, warm-grey engraved regolith, and pressure posts with restrained teal bands. It is a town plate, not an E8 building pack.

Fresh working references were rendered from current tracked files at `origin/main@2736e176d69226d40603889ee3e1aa07db623784`. The board includes E1, E4, E5, E6, and the complete E7 Signal Mesa; no prior artifact PNG was used as an input.

## Production contract

- `dome-commons-plate.glb`: one base-centered mesh and one primitive, 49.680908 x 49.599998 on the ground plane and 14.0 units overall height.
- 13,108 triangles under the 20,000 plate ceiling.
- One double-sided, non-emissive material with one embedded 2048 x 2048 RGBA PNG atlas; metallic `0`, roughness `0.9`. Macro screen-door pane lines export as glTF `MASK`, retaining depth writes for the solid floor/ribs in Three.js while leaving the pane centers open.
- Zero cameras, lights, animations, external textures, helper meshes, buildings, people, or prior-era hardware.
- Eight inherited canonical ground-zero pads plus two orbital pads remain flat and clear for the E8 building wave.
- All canonical actor routes stay within `0.034387` of flat and the plaza within `0.032214`, under the `0.05` flat-walk ceiling.
- The Pan Monument remains its unchanged, independently mounted heritage GLB. The plate supplies only its first reclaimed-water ring, with the curb crown below the flat-walk ceiling.
- The gardener's first square of green is a flush atlas inlay, never collision geometry.
- Saved-BLEND re-export is byte-identical. GLB SHA-256: `053bf554ed369ef35a532c1b5847d14469d4f661e27867678a3dc56f88fbe081`.

Earth, the Pan Monument, route/pad overlays, lights, and cameras in the renders are evidence-only. The game's sky rig owns the Earth cameo; the factory owns the site mount. Both the production builder and fresh-reference renderer refuse to run if their inputs drift from the pinned reviewed base.

## Evidence

- `renders/signal-mesa-vs-dome-commons-ab.png`: current complete E7 Mesa beside the fresh E8 site.
- `renders/dome-commons-source-ab.png`: the landed E8 painted vocabulary beside the production plate.
- `renders/dome-commons-plate-camera.png`: the plate at the Town review camera with the evidence-only Pan and Earth.
- `renders/dome-commons-turntable.png`: four-angle air-wall, airlock, rim, floor, and wrap audit.
- `renders/dome-commons-flat-walk-overlay.png`: teal actor routes and amber building pads over the realized floor.
- `artifacts/dome-commons-e8/dome-commons-asset-contract.json`: parsed GLB and byte-identical re-export proof.
- `artifacts/dome-commons-e8/dome-commons-layout-contract.json`: sources, canonical pad coordinates, and heritage boundaries.
- `artifacts/dome-commons-e8/current-references/2736e176d692-main/`: fresh per-era reference renders and source hashes.

## Rebuild and verify

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/dome-commons-3d/build_dome_commons_plate.py
bash scripts/reexport-pilot.sh assets/pilots/dome-commons-3d/dome-commons-plate.blend
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/dome-commons-3d/verify_dome_commons_plate.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/dome-commons-3d/render_current_references.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/dome-commons-3d/render_dome_commons_plate.py
```
