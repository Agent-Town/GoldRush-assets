# Low Orbit — recovery housing, joined structure and metal surfaces

Run 9 E8, 2026-09-24. Frozen source/contract from store `70b78b433ff926b3552fc3d201970d101edf4906` (the Low Orbit bytes were unchanged by that Far Side commit).

`refine-salvage-rig.py` replaces only the claw carcass visual, inside its exact previous envelope, with an annular recovery housing, bolted rim, four pressure-tower piers, articulated jaws, hydraulics and a braced hoist. The full body retains its exact extrema. The chamfered deck retains its height and eight-sided shape; its visual plan area is 1.535% smaller after fitting the new jaws inside the original full-body envelope. Collision geometry is unchanged. Four peer meshes, their UVs and transforms remain exact; they share the new atlas. Mounts, collision, stations and gameplay geometry do not change.

The atlas reuses the native `image_gen` output from `../e8-far-side-fidelity-2/provenance.md`, which records the complete generation prompt. The native output is copied here unchanged so this map's recipe has local durable raster input. Runtime texture is a 1024-square sips resize, packed in the GLBs and Blend. No new runtime standalone image URL, and no paid third-party image service.

```sh
sips -z 1024 1024 assets/pilots/map-rebuild-spike/sources/e8-low-orbit-fidelity-2/native-metal-swatches.png --out assets/pilots/map-rebuild-spike/landmarks/low-orbit/low-orbit-landmarks-atlas.png
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python assets/pilots/map-rebuild-spike/sources/e8-low-orbit-fidelity-2/refine-salvage-rig.py
```

Ordinary entry and declared-station evidence remain separate. A clean station does not cure HUD/entry composition. Full suspended field scale and floating debris are contract/layout-owned and are not expanded here.
