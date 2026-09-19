# E9 Basin Rim population

Five independent production assets built from fresh main base `b9df7e2127dadc1ea74859026459e32a2405af34` and the shipped E9 canal-works plate:

- `water-ledger-office-3d` — canal reeve's public counter, paired water meters, and balance.
- `greenkeeper-3d` — seed vault, irrigation tank, and two rows using exact E1 green `#50674c`.
- `ice-quarry-head-3d` — full gantry, winch house, suspended ice, and quarry signal.
- `weather-warden-spire-3d` — storm lens, field braces, weather globe, and lightning crown.
- `canal-packet-boat-3d` — shallow packet hull, parcels, portholes, awning, and twin paddles.

The Basin Rim plate was not yet on main when this continuous wave began. Evidence mounts the already-pushed plate dependency `sol/basin-rim-e9-plate@440bb19e4058eded9be82b1faf4292e73808cb0a` (GLB SHA-256 `89f23f703d96c5f519c820a7efca16c00ff5cb985923e9113cb1b480de81212e`) without duplicating it into this branch. After the plate merges, the renderer uses its tracked stable path automatically; before then set `BASIN_RIM_PLATE_GLB` to a verified copy.

Every population asset is one grounded/base-centered mesh with one embedded 1024-square non-emissive material, zero cameras/lights/animations, and a saved-BLEND byte-identical re-export. `build-contract.json` records the source and production hashes. `renders/basin-population-five-asset-audit.png` is the four-side wrap gate; `renders/basin-population-ensemble-turntable.png` is the dependency-mounted basin gate.

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/basin-population-e9/build_basin_population.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/basin-population-e9/verify_basin_population.py
BASIN_RIM_PLATE_GLB=/path/to/basin-rim-plate.glb /Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/basin-population-e9/render_basin_population.py
```
