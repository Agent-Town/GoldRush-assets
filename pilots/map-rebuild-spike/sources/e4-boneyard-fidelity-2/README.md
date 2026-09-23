# Boneyard — buried pressure engine and two distinct salvage silhouettes

Run 9, 2026-09-23. Frozen input comes from store 8ef0a035c47622425dada043aca1145e88aaca80. Run from the game checkout:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/map-rebuild-spike/sources/e4-boneyard-fidelity-2/refine-buried-wrecks.py
```

The sleeper receives a riveted iron/oxidized shell, inset end door, dull rods, pressure pipes and collapsed cab. A continuous irregular soil deposit covers more of the lower machinery without moving the mount or terrain. West-b becomes an exposed small pressure engine; east-b a toppled reserve on a salvage chassis. Machinery samples quieter regions of the original atlas. The deposit uses a matte, non-emissive material with the existing Motor earth pigment (#9f8564), avoiding an enlarged atlas patch on the soil. No new raster is generated.

Each body retains the exact original source bounds/object transform. Sleeper 2926/3000 triangles; west-b 1370/3000; east-b 1250/3000. The other nine source bodies and GLBs remain exact. All mounts, collision footprints, terrain heights/masks, roads, station declarations and gameplay are unchanged. The game renderer separately reduces the ground's original oversized print with its existing Boneyard-only pigment blend.

Each revised GLB has two mesh primitives and two materials, declared in its pack record: original-atlas machinery and matte earth. This adds one visible draw per revised body; entry and sleeper-station performance evidence is retained with the game review. The runtime explicitly records the earth material as zero emission.
