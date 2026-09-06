# Mesa Town plate pilot

This is the fresh E6-E7 Town site after the Flood Break: a dry glow-mesa landform built from `assets/raw/ter-mesa-seamless.png` and the ratified `e6-atomic-bundle.md`. It does not layer mesa paint over the drowned square. The production interface for the attended factory is:

- `mesa-town-plate.blend`
- `mesa-town-plate.glb`

The GLB is one 17,280-triangle mesh with one non-emissive material and one embedded 2048-square atlas. It contains the mesa cap, irregular cliff, scree apron, dry wash, restrained starstone seams, and no buildings, props, water, people, lights, cameras, or old street hardware.

## Layout law

`src/town/townLayout.ts` remains the coordinate authority. The ring road, radial cast paths, plaza center, seven canonical slots, and Dynamo Hall site all remain at ground zero. The Pan Monument is not duplicated in the plate: it remains the independently mounted heritage asset at the canonical center.

Two upper pads are deliberately marked **candidates** in `artifacts/mesa-town-3d/mesa-town-layout-contract.json`:

- Reactor Dome: circular 6.2-unit pad at `(7.0, -16.7)`, height `1.18`.
- Catalog Warehouse: 5.6 x 3.8 pad at `(-7.4, -16.6)`, height `1.18`.

Their switchback herd ramps stay below a 20% measured grade. They are surfaced for the attended plate verdict before E6 building production; they are not a silent runtime mount decision.

## Evidence

- `renders/mesa-town-current-vs-pilot-ab.png`: current square versus Mesa pilot, identical camera and inherited-building massing.
- `renders/mesa-town-flat-walk-overlay.png`: canonical routes in teal, canonical pads in orange, proposed premium pads in violet, and graded mesa access in green.
- `renders/mesa-town-turntable.png`: four angles showing the rear shelf, irregular cap, cliff face, and scree apron.
- `artifacts/mesa-town-3d/current-references/8d974f119111-main/town-e1-e4-e5-current.png`: fresh E1/E4/E5 reference board rendered from base `8d974f11911187136469fbd017c9598e5b2faf28`; E4 includes the southern boulevard and motor caravan and E5 is the submerged square.
- `artifacts/mesa-town-3d/mesa-town-asset-contract.json`: parsed GLB, realized ray-cast surface, premium-pad, ramp-grade, and byte-identical re-export proof.

The E1 buildings in the Mesa evidence are footprint/scale proxies only. They are never exported and do not imply that the E1 architecture survives the fresh E6 site.

## Rebuild and verify

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/mesa-town-3d/render_current_references.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/mesa-town-3d/build_mesa_town_plate.py
bash scripts/reexport-pilot.sh assets/pilots/mesa-town-3d/mesa-town-plate.blend
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/mesa-town-3d/verify_mesa_town_plate.py
```
