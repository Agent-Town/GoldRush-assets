# Flotilla hull source contract

These three bodies represent the existing kitchen, turret and still-room hull owners from the approved Flotilla plate. Background boats in the illustration are not extra gameplay hulls. The central deck stays clear for player-built equipment.

Geometry uses the established E5 Blender helpers. Timber/canvas and burnished metal share one embedded 512px atlas, but use two materials so metal remains legible. Each single Blender/glTF mesh therefore becomes two runtime mesh primitives (six for the full formation). The native canvas derivative has its own raw master and layer provenance; the original Claim Boat atlas is unchanged. Model membership, source hashes and measured dimensions belong in `flotilla-contract.json`.

Blender +Y points toward the bow (game -Z). Waterline is zero and deck height is 0.8 meters. Every vertex must fit the authored radius-five disc. The builder checks 25 central pad rays. Runtime deck outlines are convex and clockwise in game X/Z; the view projects only loaded surviving decks and follows the shared hull owner without changing simulation state.

Build from the repository root with Blender 5.1.2:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/flotilla-3d/build_flotilla.py
```

For saved-scene edits, use the existing `scripts/reexport-pilot.sh` with the neighboring static profile. Full recipe and saved-scene exports must reproduce the installed GLB bytes in a scratch output before provenance is accepted. Generated UVs are rounded to six decimals before fixed triangulation/canonical face ordering; this removes measured one-ULP differences without hiding geometry differences.

Current visual and runtime acceptance evidence lives under `artifacts/map-art-repairs-20260908/flotilla-body-*` and `flotilla-view-01`. Collision/contact and complete map acceptance remain separate open gates. No animation, damage or hull-movement authority lives in these meshes.
