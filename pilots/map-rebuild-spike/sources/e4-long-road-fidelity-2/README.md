# Long Road — open service stop and articulated convoy landmark

Run 9, 2026-09-23. Frozen source is from store b1e2c12a979e6b598860bfb5273142ed7b05d2f3. The recipe rebuilds only west-way-station and convoy-lead-hauler-start; all other bodies, atlas pixels, mounts, collision footprints and inspection stations remain exact.

Run from the game checkout:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/map-rebuild-spike/sources/e4-long-road-fidelity-2/refine-roadside-service.py
```

The original image atlas is reused, sampled from quiet parts of each material swatch. No new raster or paid generation. A timber trestle and hooped water tank replace the closed stop shed, beside an open teal service canopy. The static convoy landmark gains spoked wheels, exposed axles, open freight boards, an articulated boiler and feed pipes. The shared Motor vehicle is outside this source and remains unchanged.

The recipe fits the final source mesh to the original exact float32 envelope, retaining object transforms. It updates only model digests, triangle counts and explicit fidelity provenance in the pack contract. The inherited source ledger schema and historical lineage remain unchanged. Source and recipe re-export proof are in the game repository's run-9/e4-long-road evidence.
