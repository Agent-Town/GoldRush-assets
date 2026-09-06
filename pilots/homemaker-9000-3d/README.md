# Homemaker-9000 production boss model

Deterministic plate-built GLB for the E6 component boss. Production nodes are exactly `vac`, `rack`, and `core`; each owns one damage morph. Enabling all three morphs produces the storybook's Act-3 powered-down chair state.

Build and gate:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/homemaker-9000-3d/build_homemaker_9000.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/homemaker-9000-3d/render_homemaker_9000.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/homemaker-9000-3d/verify_homemaker_9000.py
bash scripts/reexport-pilot.sh assets/pilots/homemaker-9000-3d/homemaker-9000.blend
```

The GLB contains one embedded 1024 atlas/material and no lights, cameras, animations, or evidence context. Render scripts own all review-only lighting, terrain, and camera objects.

The run-camera board renders both intact and all-morph Act-3 states on the current playable Glow Mesa terrain at the canonical Isotope Kitchen stake. Its 42-degree camera uses the production Three.js offset mapped into Blender's Z-up axes; the exact source, terrain, placement, and camera hashes are recorded in `renders/homemaker-9000-reference-contract.json`.
