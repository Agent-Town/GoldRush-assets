# Codex Art Run — E5 batch 01 / batch-019 first plates

Date: 2026-07-16  
Tool path: Codex native `image_gen` only  
Task: `/Users/robin/Claude/Projects/Gold Rush/tasks/running/art--20260716-093533-art-e5-batch-01.md`

Status: **RAW GENERATED; PENDING-PROCESSING / PENDING-CONSUMPTION.**

Scope was the E5 bundle's A1 buildings/vessels plus A5 Shelf Reefs terrain/props. No extraction, processed output, layer contracts, source, specs, reviews, e2e, or integration files were touched.

## References and prompt law

- `assets/raw/kit-era-5.png` conditioned every generation for palette, materials, engraving, and mood only.
- The final Claim-Boat B retakes also used `veh-claimboat-sheet-a.png` as the identity reference.
- Every prompt included the E5 anchor verbatim:

> sea in layered engraved swells (ink-line crests, never foam spray realism); underwater scenes shift to blue-green parchment with light shafts; brass diving gear + teal instruments; storms are charcoal wall-clouds with warm lantern points, never dread-black.

- Every prompt required Frontier Ledger engraving, warm readability, no readable text/letters/numbers/logos/watermarks, no people, no realistic firearms or gun-like silhouettes, no gore, and no black smoke.
- Keyed sheets required exact cell order on `#ff00ff`; isolated building portraits used neutral parchment-gray; the atlas required a full-bleed 2x2 terrain-only grid.

## Final prompt set and native jobs

| File | Final prompt contract | Native job | Retakes | State |
|---|---|---|---:|---|
| `veh-claimboat-sheet-a.png` | 4x4; rows S/SE/E/NE; columns calm/light/medium/broad wake; broad-beamed working barge, aft wheelhouse, amidships crane, pan-dredge bow, teal lights, empty deck | `exec-d49c9e6e-660e-4133-aa35-50def3e885aa` | 0 | PENDING-PROCESSING |
| `veh-claimboat-sheet-b.png` | 4x4; rows N/NW/W/SW with bow explicitly up/upper-left/left/lower-left; same physical boat and crane side as A; columns calm/light/medium/broad wake | final `exec-882721c9-fc96-4769-b4de-005513e40a8c` | 2 | PENDING-PROCESSING |
| `bld-lighthouse.png` | 2x1 lit/unlit; stone base, brass lamp house, teal-and-gold Fresnel; no engine-drawn beam baked in | `exec-0e9c50fd-97d0-4439-acc5-46872569aeaf` | 0 | PENDING-PROCESSING |
| `bld-drydock.png` | isolated empty timber cradle, winch house, capstan, rope blocks, teal diagnostic instrument | `exec-b0af8496-1037-4d25-be68-bc8bd32f53ad` | 0 | PENDING-PROCESSING |
| `bld-divebell.png` | 2x1 surfaced/submerging; same hoist, brass bell, air-pump cart; minimal contained water cue in lowered state | `exec-ec678257-5fe8-4baf-b4e6-d790e1f483f8` | 0 | PENDING-PROCESSING |
| `bld-cannery.png` | isolated timber harbor annex, kettle line, fish-pictogram label table, exactly one roof gull | `exec-9e3c0713-8489-4b79-82d3-fb9bab711e8e` | 0 | PENDING-PROCESSING |
| `bld-net-frames.png` | isolated horizontal run of three timber A-frames, rope nets, cork floats, brass weights, teal marker lamp | `exec-0e51a87f-9939-4e2e-ae98-9dad78aef5d1` | 0 | PENDING-PROCESSING |
| `ter-shelf-atlas.png` | full-bleed 2x2; reef shallows / sandbar / kelp bed / deck planking; terrain only, wrap-aware edges | `exec-fcda3d39-b254-4813-9b48-55fb95a80a0b` | 0 | PENDING-PROCESSING / CONSUMPTION |
| `prop-wrecks.png` | 6x1; E1 supply barge / E2 locomotive / E3 pylon barge / E4 six-wheel land-yacht sister / smooth glowing mystery hull / shared debris field | `exec-c65c1a6f-15ae-4704-b3b3-cd58fc9a4aec` | 0 | PENDING-PROCESSING |
| `prop-buoys.png` | 2x1 lit/unlit; same timber-and-brass channel buoy, blank diamond pictogram | `exec-79e21b93-bc40-40e0-80b3-4421de0517f7` | 0 | PENDING-PROCESSING |

Rejected Claim-Boat B attempts: initial `exec-5f974d57-5868-4d15-ac86-4ea6fcee619e` redesigned the hull; retake 1 `exec-85775fbd-6692-48f9-a9e8-dfc995dd4dc8` restored identity but duplicated sheet A's headings. Both remain only in Codex's generated-image store. Retake 2 is the final B sheet and visibly supplies the four opposite headings.

## Raw preparation and metrology

The six keyed files were normalized from native near-magenta to exact opaque `#ff00ff` using a 10% color-distance replacement. No alpha extraction, cell extraction, resizing, despill, or integration was performed.

| Sheet | Dimensions | Exact-key coverage | Near-magenta non-exact | Alpha pixels |
|---|---:|---:|---:|---:|
| `veh-claimboat-sheet-a.png` | 1254x1254 | 63.64% | 0 | 0 |
| `veh-claimboat-sheet-b.png` | 1254x1254 | 65.34% | 0 | 0 |
| `bld-lighthouse.png` | 1672x941 | 71.39% | 0 | 0 |
| `bld-divebell.png` | 1672x941 | 61.64% | 0 | 0 |
| `prop-wrecks.png` | 2172x724 | 67.35% | 0 | 0 |
| `prop-buoys.png` | 1672x941 | 76.92% | 0 | 0 |

Claim-Boat nominal cell size is 313.5px square. The conservative deck composite zone is local cell bounds **x=126..188, y=126..188** (63x63px) in all 32 cells; rotate the mounted building with the hull heading. This deliberately preserves a small universal safe box rather than claiming the full visible deck. Hull/wake trimmed content ranges: sheet A 183–313px wide × 146–311px high; sheet B 124–314px wide × 215–313px high. Some broad-wake strokes reach cell edges; the hulls do not visibly cross cells.

Atlas opposite-edge absolute RGB deltas by cell (mean / p95): reef `10.5 / 28`; sandbar `11.7 / 30`; kelp `16.8 / 49`; deck `9.0 / 25`. Reef, sandbar, and deck match the established raw-generation seam band. Kelp is the noisier cell and requires repeated-tile seam QA before consumption.

## QA

| File | Contract read | Grid / key / full-bleed | Letters | Firearms | Gore | Verdict |
|---|---|---|---|---|---|---|
| `veh-claimboat-sheet-a/b.png` | 8 real headings; wake rises left-to-right; deck stays empty; final B still drifts in wheelhouse/end treatment and apparent crane side vs A | two 4x4 exact-key sheets; no deterministic mirrors | none | none | none | PASS FOR RAW; CONTINUITY + FRINGE GATE BELOW |
| `bld-lighthouse.png` | tallest era silhouette; stable 2-state structure; warm lens on vs dark lens off | 2x1 exact key; trimmed heights 869/873px | none | none | none | PASS |
| `bld-drydock.png` | empty cradle + winch house immediately read as repair/refit | isolated portrait | none | none | none | PASS |
| `bld-divebell.png` | brass bell, hoist, pump cart; surfaced vs visibly lowered | 2x1 exact key | none | none | none | PASS; footprint intentionally grows with water cutaway |
| `bld-cannery.png` | kettle line, fish pictograms, exactly one gull | isolated portrait | none | none | none | PASS |
| `bld-net-frames.png` | three net frames read as harbor work and fence-adjacent slow field | isolated portrait | none | none | none | PASS |
| `ter-shelf-atlas.png` | reef / sandbar / kelp / deck distinct in exact order | 2x2 full-bleed | none | none | none | PASS FOR RAW; KELP SEAM-QA REQUIRED |
| `prop-wrecks.png` | exactly five prior/future-era wrecks plus one debris field; E2 locomotive and smooth mystery hull are unmistakable | 6x1 exact key | none | none | none | PASS FOR RAW; EXTRACTION CAVEAT |
| `prop-buoys.png` | stable buoy silhouette; warm lamp lit vs dark | 2x1 exact key | none | none | none | PASS |

Independent visual critique correctly caught the duplicated headings in the first B retake; the final B retake fixes the headings. A fresh critique of that final candidate still found cross-sheet identity/side drift at high confidence. Both allowed retakes are exhausted, so the pair is raw-complete but must not be wired as one rotating runtime hull until fire-side continuity review accepts or repairs it. (The critique's apparent NW “canvas clipping” came from a temporary review crop ending exactly at the row boundary, not the full raw sheet.) Remaining actionable risks are preserved rather than hidden:

1. Claim-Boat A/B wheelhouse/end treatment and apparent crane side are not fully continuous. Fire-side consumption must resolve that identity gate; do not hide it with mirroring.
2. Claim-Boat wake wisps use pale pink/white antialiased strokes adjacent to the key. Fire-side extraction must inspect fringes at 2x and may need targeted despill/soft-matte treatment.
3. The wreck strip is compositionally readable, but several wreck/debris extrema approach equal-cell boundaries. Treat the manifest's “each 1–2 cells” wording literally: fire-side processing must establish per-wreck crop bounds instead of blindly slicing six equal cells.
4. The atlas is intentionally engraved and high-frequency; repeated-tile gameplay-scale QA must verify kelp seam visibility and scan noise before consumption.

Burn count: 12 native image calls; 10 accepted final assets; 2 rejected Claim-Boat B attempts; 2 retakes total; no auth, quota, or rate-limit errors.
