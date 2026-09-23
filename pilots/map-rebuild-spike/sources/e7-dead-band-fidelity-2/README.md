# Dead Band — layered silent antenna frames

2026-09-23, map-art campaign run 9, E7 leg. This source answers the run-6
clause: “These simple braced frames do not yet equal the plate's layered
antenna architecture.” Reference: `assets/raw/plate-contract-e7-dead-band.png`.

Run `Blender --background --python assets/pilots/map-rebuild-spike/sources/e7-dead-band-fidelity-2/refine-silent-frames.py`
from the game root (the Mac executable is `/Applications/Blender.app/Contents/MacOS/Blender`).
The recipe reads the frozen input blend/contract and rebuilds only
`iron-shadow-warning-frame` and `north-silence-gate` into the existing pack.

Layered lattice pylons, socket feet, riveted collars, an open truss header,
ceramic aerial collars and an empty double bezel reuse the original packed
atlas. No new raster image, generated service, active-signal cue or emissive
material is introduced. Each output retains one mesh/material/primitive.

The exact source bounds, mounts, inspection stations, all three sibling
bodies, atlas pixels and collision data are retained. The north gate's existing
terrain burial remains a mount/terrain limitation; the recipe does not raise
the gate. Full plate layout and terrace composition remain outside this pass.

The canonical output blend is `landmarks/dead-band/dead-band-landmarks.blend`;
GLBs and hashes are in the adjacent landmark pack contract. Re-export and
frozen-recipe reproduction evidence lives in the game repository under
`artifacts/sol/map-art-campaign-2/run-9/e7-dead-band/`.
