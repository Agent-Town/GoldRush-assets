# Land Yacht boss model

This GLB translates the E4 intact/damage plates into a wheeled ship with a raised hull/deck, armored wheel faces, framed wheelhouse and suspended open crane grab. Its three original component/damage bindings remain. The six physical wheels belong to the one gameplay wheels component; broken assemblies remain attached through salvage.

The fidelity pass has 9,613 triangles, one embedded 1024-square atlas and one material. Geometry comes from the local Blender builder using the existing Dredge Queen kit. The native-generated atlas source is `assets/raw/land-yacht-atlas-fidelity-e4.png`; provenance and hashes are registered in [the layer contract](../../layer-contracts/land-yacht.v1.json). Export facts are in [the asset contract](renders/land-yacht-asset-contract.json).

The production source rebuild matches the inspected candidate bytes, saved-Blend re-export passes, and TypeScript passes. Focused desktop/mobile mechanics, lifecycle and fresh-page resume checks pass, along with the final production build and optimized-asset captures. Broad regression is pending. Current evidence and limitations are under `artifacts/boss-fidelity/e4-landyacht/`; the older render boards in this package predate the fidelity pass and are historical.

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/land-yacht-3d/build_land_yacht.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/land-yacht-3d/verify_land_yacht.py
```
