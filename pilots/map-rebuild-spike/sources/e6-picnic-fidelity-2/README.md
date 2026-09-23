# Picnic — authored props and clean ground pigment

2026-09-23, run 9 E6. The three existing blanket bodies gain folded gingham cloth, open handled cups, rimmed dishes, rounded woven baskets, sandwiches and the central brass atom ornament. The existing shade gains a sagging closed canvas, hems and capped posts, while retaining its authored bench and atom pendant and adding bench feet. The retained pendant is lowered inside the body so it clears the new sagging canvas; the mount and whole-body envelope do not move. No new mount or blocker; the shade was already mounted by run 7.

`landmarks-input.blend` and `landmark-input-contract.json` freeze store `92db3dc4f87789f976b7c310b7adb7372f8c5c30`. The recipe verifies the source blend hash, keeps original object names/matrices, fits each rebuilt mesh to its exact original float32 envelope, retains the staging gate, and exports only the four changed bodies. It records actual two-primitive/two-material counts and leaves all budgets, footprints, mounts and stations unchanged.

From the game worktree root:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/map-rebuild-spike/sources/e6-picnic-fidelity-2/refine-picnic-props.py
```

Optional `-- /absolute/scratch/directory` exports a draft. Source and recipe proof scripts live in game evidence `artifacts/sol/map-art-campaign-2/run-9/` and require explicit PASS markers, because Blender may return zero after a Python exception.

Both new raster sources come solely from the native image tool; see [exact prompts and originals](image-provenance.md). The cloth atlas is retained at generated resolution and resampled to the existing 1024-pixel family cap during Blender export. The unchanged original pack atlas remains used for metal, ceramic and wood. The cleaned ground image removes painted pylon/cross marks from a Picnic-only pigment layer; the shared Glow Mesa terrain GLB, original atlas, geometry, heights and masks remain unchanged. Its runtime URL is inside the deployment mirror's `sources/**.png` include.

The final station/plain evidence, comparisons to run 6, triangle inventory, recipe/source proofs, build/browser/performance receipts and remaining visual limitations live in `run-9/e6-picnic/` in the game repository. No full concept acceptance is implied.
