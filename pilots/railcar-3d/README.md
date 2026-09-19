# Armored Railcar 3D pilot

The [source painting](../../raw/plate-e2-boss-component.png) controls the locomotive silhouette: a long riveted boiler, low armored cabin, three large front axles, two smaller rear axles, a projecting cowcatcher and restrained teal lamps. The [native surface atlas](../../raw/railcar-atlas-fidelity-e2.png) supplies illustrated metal texture; it does not replace that form reference.

The fidelity pass lengthens the chassis while preserving the runtime rail gauge and the round profiles of wheels, gauges and lamps. Narrow cabin windows, underbody reservoirs, cage lanterns and a rear platform restore features that distinguish the painting. The measured dimensions and export budget live in [the asset contract](renders/wave4-asset-contract.json).

The three component meshes retain one damage morph each so the existing encounter can break the wheels, vent the boiler and cave the cabin independently. Hidden breach and steam geometry appears only with damage. No duplicated damaged locomotive or new gameplay state is needed.

## Rebuild and verify

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/railcar-3d/build_railcar.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/railcar-3d/verify_railcar.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/railcar-3d/render_railcar.py
```

The builder checks that elongation preserves round profiles. The verifier checks the component and morph bindings, texture budget, centered base and byte-identical Blender re-export. Neutral renders expose geometry and damage states; the [runtime presentation check](../../../scripts/check-railcar-presentation.mjs) verifies placement, route reversal and component targets in the game.
