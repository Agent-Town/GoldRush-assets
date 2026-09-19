# Tavern full-wrap repair — Wave 3 gate

Branch: `sol/tavern-full-wrap`

Verdict: **READY-FOR-GATES**

## Asset contract

- Production interface: `assets/pilots/tavern-3d/town-v3-tavern.glb`
- Repaired source: `town-v3-tavern.blend`, rebuilt from the owner-approved `tavern-2-fullwrap.blend`
- 10,988 triangles; one mesh, one primitive, one material, one embedded 1024 x 1024 PNG atlas
- Zero cameras, lights, or animations; metallic `0`, roughness `0.9`, no emissive surface
- Exact mounted bounds preserved: `4.229571w x 3.960802h x 3.349d`; base-centered and grounded at `y=0`
- Final GLB SHA-256: `edec4934d6d956170078b521fe526ccadcde015567094aec59001e2d4b71b90d`
- Recipe re-export is byte-identical to the checked GLB

Machine-readable details are in `renders/wave3-asset-contract.json`.

## Visual evidence

- `renders/wave3-game-ts04-ab.png` — authoritative in-game TS-04 A/B; left is the former dark-plane asset, right is the repair
- `renders/wave3-detail-ab.png` — focused parcel polish A/B; left is the accepted full-wrap asset, right is the consistency repair
- `renders/wave3-angle-polish-ab.png` — all-angle polish A/B; left four views are the accepted full-wrap asset, right four views are final
- `renders/wave3-turntable.png` — front-left, front-right, back-left, and back-right coverage

The actual-game A/B holds the same frontage direction, anchor, and apparent envelope. Objective telemetry localizes the original full-wrap change to the Tavern: `0.515%` of pixels differ by more than 32 grayscale levels, average luminance changes by `+0.015`, and edge energy changes by `+0.853%`. The owner-directed all-angle polish closes the false-front crest's sky-colored rear crescent and attaches the projecting sign to its bracket with two short straps. No other asymmetry was normalized: awnings, windows, steps, and workyard details remain intentionally lived-in. Fresh post-fix visual review returned **SHIP** with no confident blocker.

## Reproduction and gates

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/tavern-3d/build_tavern_repair.py
bash scripts/reexport-pilot.sh assets/pilots/tavern-3d/town-v3-tavern.blend
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/tavern-3d/verify_tavern_repair.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/tavern-3d/render_tavern_repair.py -- /path/to/accepted-pre-polish-town-v3-tavern.glb
```

- Latest observed `main`: `fd38b44f`
- `npm run build`: pass
- Unmodified `e2e/town-tavern-blender.spec.ts`, desktop and mobile: 6/6 pass
- Exact final GLB tested on latest observed main: SHA-256 `edec4934d6d956170078b521fe526ccadcde015567094aec59001e2d4b71b90d`
- Frame-time p95 versus facade: desktop `-2.11%`; mobile `0%`, below the `15%` ceiling
- Tavern prompt, Board interaction, LITE fallback, failed-load fallback, disposal, and exact bounds assertion: pass
- No runtime source, layout coordinate, footprint, or approach-path change
