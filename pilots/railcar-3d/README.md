# Armored Railcar 3D pilot

Wave 4 replaces the flat component plate with one production-ready boss locomotive GLB. The source painting remains the style bible: `assets/raw/plate-e2-boss-component.png` supplies the atlas linework and palette, low siege-engine massing, blackened riveted iron, warm brass, restrained teal portholes, heavy running gear, and armored cow-catcher silhouette.

## Production contract

- `railcar.glb`: base-centered, 2.40 units long, 1.202 high, and 1.248279 wide at the cow-catcher.
- Runtime rail gauge: 0.78 units; chosen length is 3.0769 gauge widths. Runtime sleeper spacing is 0.90 units.
- 10,948 triangles under the 12,000 ceiling.
- One shared material with one embedded 1024 x 1024 PNG.
- Exactly three mesh nodes: `Railcar_Wheels`, `Railcar_Boiler`, and `Railcar_Cabin`.
- Exactly one damage morph on each node: `Damage_BentWheels`, `Damage_VentingBoiler`, and `Damage_CrackedCabin`.
- Zero cameras, lights, or animations in the `.blend` and GLB.
- No runtime source changes; the factory owns the existing presentation seam.

The intact state deliberately avoids a friendly toy-train read: the boiler owns most of the length, the cabin is a low faceted armor bunker, the leading drive wheels are larger than the rear pair, the roof guard hugs the platework, and two broad prow blades reinforce a central ram. Near-black iron carries the mass while brass edges and small teal apertures preserve form separation at the production high three-quarter camera.

The morph choice keeps the interface to three separable component meshes while avoiding hidden duplicate damage meshes. The boiler morph opens its vent hatches, lifts the relief valves, splits the rear band, and reveals a short plate-styled vent plume. The cabin morph caves its subdivided near armor wall, exposes a dark rupture and branching fractures, and collapses the near roof edge. The wheel morph kinks the lead axle, suspension, and drive rod.

## Rebuild and verify

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/railcar-3d/build_railcar.py
bash scripts/reexport-pilot.sh assets/pilots/railcar-3d/railcar.blend
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/railcar-3d/verify_railcar.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/railcar-3d/render_railcar.py
```

The verifier writes `renders/wave4-asset-contract.json` and proves a byte-identical Blender re-export. The render script produces:

- `railcar-turntable.png`: front-left, front-right, rear-left, rear-right.
- `railcar-on-rail-run-camera.png`: 42-degree production FOV and production camera pitch, with the model raised to the 0.125-unit rail-head top.
- `railcar-damage-states.png`: bent wheels, venting boiler, cracked cabin from left to right.
