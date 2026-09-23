# Incline cable house — fidelity source

2026-09-23, render-only model refinement. Reuses the existing 1024-square atlas; no generated bitmap and no image service.

Frozen input files are exact copies of the delivered aggregate Blender source and landmark pack contract before run 9. `refine-cable-house.py` checks their SHA binding before editing. Run it through Blender from the game checkout; it writes only this pack's aggregate source, cable-house GLB and derived contract counts/hashes.

The recipe removes whole original components: the duplicated winch buried inside the house (788 triangles), old roof (12), and old straight returns (40). It replaces them with a clear 8-spoke wheel/hub/bearings, direct cable returns, wound drum, boarded deck/fascia, shallow timber roof, facade trim and exhaust neck. Net body 2028 -> 2136 triangles, budget 3000. The four sibling source bodies and GLB bytes, all atlas pixels, body bounds, mounts, footprints and inspection stations stay unchanged. 576 retained wheel UV loops are moved into the material's active atlas layer.

The exhaust neck follows the existing cable-house steam source at world offset (-0.6,-1.4), inverse-transformed through the unchanged -0.1 yaw. Renderer-only radius/growth become 1.45/1.4; emitter position, timing, lifespan, rise and gameplay remain unchanged. Saved-source re-export verification lives in the run-9 game evidence.
