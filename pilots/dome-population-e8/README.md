# E8 Dome Commons population

Five production building GLBs populate the accepted Dome Commons plate without changing the plate, the Pan Monument, or runtime code:

- `orbital-canteen-3d/orbital-canteen.glb` — pressure canteen with a large Earth-window seat and public counter
- `suit-fitter-3d/suit-fitter.glb` — sealed rotunda with two suit pods, helmets, and service hoses
- `launch-works-3d/launch-works.glb` — rocket, launch seal, control cupola, gantry, and umbilical
- `he3-assay-3d/he3-assay.glb` — glass-roofed assay lab, sample tower, vials, and paired He-3 pans
- `mass-driver-dispatch-3d/mass-driver-dispatch.glb` — driver barrel, coil bank, dispatch house, cargo sled, and signal

The shared builder bakes a separate one-material 1024 atlas into each production GLB. All production assets are one mesh/primitive, non-emissive, base-centered, grounded, and contain no cameras, lights, animations, or evidence helpers. Evidence-only Earth, lighting, camera, Pan mount, and audit floor live only in the render script.

## Canonical sites

| Asset | Assigned site | Asset footprint | Site footprint |
| --- | --- | --- | --- |
| orbital canteen | Tavern parcel | 4.90 x 3.2784 | 5.20 x 3.40 |
| suit fitter | General Store parcel | 3.77593 x 3.222 | 4.80 x 3.30 |
| launch works | starboard orbital circle | 5.44 diameter | 6.20 diameter |
| He-3 assay | Assay Office parcel | 4.503 x 3.065 | 4.60 x 3.40 |
| mass-driver dispatch | port orbital rectangle | 5.45 x 3.28 | 5.60 x 3.80 |

## Reproduce and verify

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/dome-population-e8/build_dome_population.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/dome-population-e8/verify_dome_population.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/dome-population-e8/render_dome_population.py
```

The verifier reopens every saved `.blend`, exports it independently, and requires byte-for-byte equality with the checked-in GLB. The renderer produces the locked gameplay ensemble, four ensemble angles, four isolated angles per building, the source A/B, and a fresh E1-E8 reference board labeled with the pulled base SHA.
