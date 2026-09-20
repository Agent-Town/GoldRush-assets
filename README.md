# GoldRush-assets — the art store
The four heavy asset directories of `Agent-Town/GoldRush`, split out on 2026-09-06 (owner ruling: "ok, good plan about the shrinking"): `pilots/`, `motion-pilot/`, `raw/`, `processed-full/`. The implementation repo reaches them at `assets/<dir>` through symlinks to one shared checkout, so no code path changes and every worktree shares one copy. Full history of every version stays in `Agent-Town/GoldRush-archive`. Never rewritten, never force-pushed; art batches land here as ordinary commits and the implementation repo's LEDGER cites them.

## Provenance and license

Every family here (terrain and landmark packs, panoramas, motion plates, source plates, full-size processed art) was generated for Gold Rush by its owner through image and 3D generation tools and hand-edited in Blender; the per-asset provenance (source, generation method, transformations, runtime slot) is recorded in the game repository, `Agent-Town/GoldRush`, in `assets/LEDGER.md`. Licensed under the Apache License, Version 2.0, like the code (see LICENSE); attribution to Agent Town is appreciated.
