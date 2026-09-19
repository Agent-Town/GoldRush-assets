# Hero 3D pilot

The game still uses the sprite heroine in `src/entities/Hero.ts`. This asset is an owner-review pilot and is not imported by the runtime.

The F-ASTRA-2 revision keeps the authored mesh, skin weights and `Hero_Walk_8_Seedance` joint choreography. A baked vertical correction grounds the walk; its duration remains 0.5 seconds. The original eight authored poses are sampled at 128 fps (frames 0–64) so the exported contact correction survives interpolation. All 50 disconnected authored components now have full UV islands, including side, back and cap surfaces. Material regions deliberately repeat across similar parts. The builder also checks that every UV remains inside its assigned material region. No front illustration is projected across the body. The single 1024 × 1024 diffuse atlas uses a conventional Principled base-color input with roughness 0.83, metalness zero and no emission.

RGBA8 texture residency with a full mip chain is approximately **5.33 MiB**, down from **42.67 MiB** for the former 4096 × 2048 atlas (87.5% reduction). This estimate excludes driver overhead and other resources.

## Rebuild

From the repository root, with the existing atlas in place:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --threads 1 assets/pilots/hero-3d/hero-3d.blend --python assets/pilots/hero-3d/build-gameplay-atlas.py
```

The script is idempotent on this blend. It welds only sub-float-precision duplicate vertices (1e-7 units), preserves the walk, regenerates the UV islands and material, saves the editable blend, and exports only `HeroMesh` and `HeroRig`. It refuses a changed component layout or collapsed UV triangle. `uv-audit.json` records every component and the minimum UV triangle area. The sidecar `hero-3d.export.json` also works with `scripts/reexport-pilot.sh` for ordinary owner edits that should preserve their UVs.

## Review the walk

With the normal Vite dev server on port 5301, open:

`http://127.0.0.1:5301/assets/pilots/hero-3d/compare.html`

The page renders the GLB beside an actual `Hero` instance at all eight headings. Its Play button drives both animations. The automated comparison steps the sprite through `Hero.update` and reads `SpriteAnimator` diagnostics; it does not substitute atlas cells, force frame indices, or mirror directions.

```sh
PATH=/opt/homebrew/bin:$PATH node assets/pilots/hero-3d/capture-comparison.mjs
```

This creates `artifacts/sol/open-findings/hero-eight-heading-board.png`, 64 paired poses, the exported GLB audit and sprite/bone evidence. Raw captures stay under `_raw/`. See the task report for measured gates and the final visual judgment. Promotion belongs to the owner.

The diffuse artwork came from native `image_gen`; the original output and provenance live in `artifacts/sol/open-findings/hero-atlas-*`. No paid image service was used. The final texture is a deterministic 1024-square Lanczos resample of that source.

The foot audit evaluates the actual deformed mesh, and `validate-export.mjs` independently checks the exported GLB at 129 phases using Three.js skinning. Its supporting sole stays 2.63–4.66 mm above the reference ground; the loop closes exactly. Both feet alternate through the stride. The older `judgment-*`, `walk-cycle-frame-strip.png` and `hero-turntable.png` files are historical pre-revision references; the linked eight-heading board is current.

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --threads 1 assets/pilots/hero-3d/hero-3d.blend --python assets/pilots/hero-3d/validate-walk.py
PATH=/opt/homebrew/bin:$PATH node assets/pilots/hero-3d/validate-export.mjs
PATH=/opt/homebrew/bin:$PATH npx tsc --project assets/pilots/hero-3d/tsconfig.json
```
