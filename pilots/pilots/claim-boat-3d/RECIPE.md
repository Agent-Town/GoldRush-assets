# Claim Boat — reproducible candidate body

The approved plate is `assets/raw/plate-e5-bld-claimboat.png`. This body reuses the E5 prop geometry/material helpers because the existing E5 hauled dinghy and E9 canal packet represent different vessels. It retains the existing ClaimBoat simulation owner. The old eight-direction sprites remain continuity-blocked.

Native image_gen made the material atlas; its unmodified raw and exact prompt are retained. The builder embeds a 512px copy, projects UVs deterministically and canonicalizes triangulated face/loop order. Smart Project plus uncategorized triangulation previously produced nondeterministic export bytes. The static export sidecar governs saved-source re-export.

Run from repository root with Blender 5.1.2:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-exit-code 1 --python assets/pilots/claim-boat-3d/build_claim_boat.py -- /tmp/claim-boat-regeneration
REEXPORT_OUT_DIR=/tmp/claim-boat-reexport bash scripts/reexport-pilot.sh assets/pilots/claim-boat-3d/claim-boat.blend
node --test scripts/claim-boat-asset.test.mjs scripts/claim-boat-view.test.mjs
```

The contract pins inputs and output and records 196 vertical ray samples over four 1.5m-square rider/pad areas. These sampled clearances are not a continuous collision mesh. The body is waterline-zero, deck +0.8m, one material/mesh, and 21,508 triangles. Full regeneration and saved-source re-export are byte identical in candidate 13; see `artifacts/map-art-repairs-20260908/claim-boat-body-13/checkpoint.json`.

The runtime view follows the existing single boat on Deepwater, Regatta and Stillwater. It does not apply to Flotilla. Hero interpolation and visible weapons use deck height, while simulation positions and shooter origins remain unchanged. This is presentation, not proof of traversable cabin/crane collision, carrying the rider during reanchor, or bank/persistence completion.

Visual acceptance remains open: brass/teal readability, crane silhouette, water contact, camera framing and mobile UI occlusion. See `artifacts/map-art-repairs-20260908/claim-boat-runtime-01/visual-verdict.md`.

Candidate 13 replaces stretched deck artwork and raised seam boxes with individually mapped plank top faces over the existing backing, and crane drums with thin wheels, axles and teal hubs. It retains the original crane direction, deck bounds, pads, atlas and simulation. A port rotation was rejected after phone clipping. See `artifacts/map-art-repairs-20260908/claim-boat-body-13/visual-review.md` for the bounded improvement and remaining gaps.
