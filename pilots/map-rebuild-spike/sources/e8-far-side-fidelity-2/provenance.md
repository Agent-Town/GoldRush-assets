# Far Side pressure-vessel source and native surface atlas

Authored 2026-09-24 for run 9 E8. Input Blender/contract files are frozen copies of store `892b7f6f993cfb79dcee9c96d82c32efe32ea20f`. `refine-pressure-vessel.py` rebuilds only `far-side-landing-frame`, inside its exact original envelope, and replaces the shared atlas for the five Far Side bodies. Peer geometry/UVs, gameplay contracts, transforms and inspection stations stay exact.

Run from the game root:

```sh
sips -z 1024 1024 assets/pilots/map-rebuild-spike/sources/e8-far-side-fidelity-2/native-metal-swatches.png --out assets/pilots/map-rebuild-spike/landmarks/far-side/far-side-landmarks-atlas.png
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python assets/pilots/map-rebuild-spike/sources/e8-far-side-fidelity-2/refine-pressure-vessel.py
```

The raster was generated with the native `image_gen` tool. No external paid image service. Original output: `01a0cf50-7215-7be0-bb5a-25fcc4a64636/exec-a9ad1e10-2f6f-4b77-a0d8-bffc8571640d.png`; retained losslessly as `native-metal-swatches.png` (1254 square). The only processing is a 1024-square sips resize; the runtime atlas is packed in every GLB and the saved Blend. No new standalone image URL is referenced by code.

Prompt: Create a square 1024x1024 game texture atlas, opaque, exactly 4 columns by 4 rows of equal 256x256 squares. All sixteen tiles are seamless flat material swatches viewed dead straight on with even diffuse illumination, edge to edge, no gaps, no borders, NO OBJECTS, NO SYMBOLS, NO WORDS. Frontier Ledger style: intricate hand engraved stipple and fine etched metal hatching, tactile quiet aged brass and iron, illustrated not photorealistic, restrained micro detail, low contrast, no large stains, no directional lighting. Tile layout top to bottom: row1 all four tiles very dark charcoal soot with subtle grain. Row2: muted aged honey brass; charcoal black gunmetal; warm silver-grey brushed metal; dark muted oxide red metal. Row3: subdued oxidized teal enamel; darker blue-grey teal enamel; warm pale cream ceramic; muted rusty brown steel. Row4: dark umber painted metal; mid-tone warm grey iron; grey-brown pitted stone; light warm grey hammered metal. Keep every swatch uniform and seamless: no rivets, no seams, no pictured buildings, no gradients. Fine etched texture only. This atlas will cover an illustrated lunar brass pressure vessel. Must have precise equal 4x4 layout with flat unframed boundaries.

The initial pale shell and visually detached mast were rejected by independent critique. Final geometry uses physically proportioned panel UVs, brass skin with dark seam collars, a projecting pressure spindle, and a visible mast knee. Full plate-scale mechanism and contact remain reviewable limitations, not claimed complete.
