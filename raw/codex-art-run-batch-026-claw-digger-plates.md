# Art batch 026 — Claw and Old Digger boss plates

- Date: 2026-07-17
- Generator: native Codex `image_gen` only
- Processing: none
- Retakes: 0
- Output contract: four full-bleed raw PNG references; no source or integration changes

## Outputs

- `/Users/robin/Claude/Projects/Gold Rush/assets/raw/boss-salvage-claw.png`
- `/Users/robin/Claude/Projects/Gold Rush/assets/raw/boss-salvage-claw-damage.png`
- `/Users/robin/Claude/Projects/Gold Rush/assets/raw/boss-old-digger.png`
- `/Users/robin/Claude/Projects/Gold Rush/assets/raw/boss-old-digger-gentle.png`

All four outputs are 1672x941 RGB PNGs.

## Required era anchors

E8, copied verbatim into both Claw prompts:

> silver-and-teal over parchment; the lunar surface is warm grey stippled engraving, never cold photoreal; Earth above is a soft blue-green cameo; suit brass + glass domes; vacuum silence drawn as extra negative space (and heard — the audio system's showcase era: muffled interiors, silent exteriors, heartbeat-and-radio).

E9, copied verbatim into both Old Digger prompts:

> rust-red engraved dunes over parchment; the green that spreads is E1's exact riverbank green (sample it — literally the same swatch: the point IS the callback); domes warm-lit from within; dust devils are drawn columns of hatch-spirals.

## Final prompt set

1. **Claw intact:** Frontier Ledger full-bleed wide three-quarter scene of the Salvage King's Claw descending over a lunar claim, with the crown above, winch drums mid-frame, taut cables, lowering anchor-feet, corsair salvage rigging, pictogram-only claim plates, cold silver-teal machinery, warm honey habitat lights, and crown/winch/feet silhouette readability. No grids, mirrors, text, letters, numbers, firearms, gore, horror, labels, borders, or photorealism. E8 anchor included verbatim.
2. **Claw defeated:** Matched edit of the intact plate preserving machine identity, camera, scale, and framing; landed buckled feet, dark crown, sprung winches, one clean conspicuous empty bolt socket, orderly crew descent on rope ladders with warm lanterns, and a future-yard rather than wreck-horror reading. No flames, bodies, text, firearms, gore, grids, labels, or redesign. E8 anchor included verbatim.
3. **Old Digger working:** Frontier Ledger full-bleed wide three-quarter side elevation of the ancient terraformer in the red basin at dusk, with great bucket-wheels, gantry spine, firefly maintenance drones, a precisely wrong canal, century dust, a ghosted crossed-pickaxes pictogram, and a warm tape-deck heart behind the preserved seal; craftsmanship rather than menace. No grids, mirrors, text, letters, numbers, firearms, gore, horror, labels, borders, or damage. E9 anchor included verbatim.
4. **Old Digger gentle:** Matched edit preserving machine, camera, framing, crest, and wear; a corrected canal with water following, safe fully clothed children waving behind the gantry rail, preserved unreplaced old crest, teal tape-deck heart, and an intact warm redemption state. No damage, wreckage, replacement mark, text, firearms, gore, danger, grids, labels, or redesign. E9 anchor included verbatim.

## Self-QA

- **Measured thumbnail readability — PASS.** Temporary 240px-wide inspection showed the Claw's crown, paired winch drums, and anchor-feet as separate nameable zones in both states. The Old Digger's two great wheel assemblies, long gantry spine, and central tape-deck housing remain readable in both states.
- **Palette purity — PASS.** E8 holds warm-grey parchment regolith, silver/teal machinery, soft blue-green Earth cameo, brass detail, and honey habitat/crew warmth. E9 holds rust-red engraved dunes, parchment sky, restrained riverbank green/water, warm domes, hatch-spiral devils, and teal only at the reprogrammed heart.
- **No text/letters — PASS.** Full-resolution and 240px visual inspection found pictograms only: no visible text, letters, numbers, logos, or watermarks. No firearms, gore, grids, mirrors, or horror treatment.
- **Matched framing — PASS.** Both pairs retain the same 1672x941 composition, camera intent, machine scale, and major silhouette placement. Diagnostic pair RMSE was 0.175 for Claw and 0.081 for Old Digger; these values locate intentional state changes and are not acceptance scores.
- **Warmth law — PASS.** Claw defeat reads as dignified surrender and future civic salvage yard: dark crown, settled feet, orderly ladder descent, warm lanterns. Old Digger redemption reads intact and useful: children wave safely, the crest remains honest, water follows the corrected channel, and the heart turns teal.
- **State-specific details — PASS.** The Claw base reads descending; its defeat plate has buckled landed feet, sprung winches, dark crown, and one clean empty bolt socket. The Old Digger base reads as precise obsolete labor; its gentle plate is not damaged and preserves the same body while correcting the canal.

## Native jobs

- Claw intact: `exec-aba40aa4-43ee-4c78-b0aa-f25b9c91f32a`
- Claw defeated: `exec-f4cc64fb-9a75-4794-b575-2523c726d59f`
- Old Digger working: `exec-bec61376-1c1f-4ca0-9024-25b99b98b152`
- Old Digger gentle: `exec-afb9560f-10dc-4a6a-807d-1018e1f1fe5a`
