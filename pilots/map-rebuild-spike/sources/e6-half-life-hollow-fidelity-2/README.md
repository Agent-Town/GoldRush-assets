# Half-Life Hollow countdown gate — fidelity 2

2026-09-23. Architectural refinement of the existing `south-countdown-gate`, inspired by the existing `assets/raw/plate-contract-e6-half-life-hollow.png` reference. Frozen original source and contract are included. No raster was generated or altered. The original shared 1024px atlas is reused through smaller UV patches.

Run from the game checkout:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/map-rebuild-spike/sources/e6-half-life-hollow-fidelity-2/refine-countdown-gate.py
```

The recipe produces stepped piers, pilasters, paired arch ribs and knees, framed dial housing, concentric bezel, hour marks and caged lanterns. 508→1,956 triangles within the existing 3,000 budget. The exact original float32 source envelope, mount, passage, stations, collision bytes and all sibling bodies are preserved. Source re-export and frozen-input recipe reproduce the GLB byte-for-byte.

Full mechanical-door fidelity remains withheld: the reference's low central door cannot be introduced as a visual obstacle in the existing passable opening. Material distinction, contact, illumination and finer fastenings remain limited; see the game's run-9 review and independent critique.
