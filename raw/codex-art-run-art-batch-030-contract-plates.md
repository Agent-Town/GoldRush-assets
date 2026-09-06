---
source: codex
project: Gold Rush
date: 2026-07-20
type: reference
---

# Art batch 030 — E8-E9 contract plates

## Result

Native Codex `image_gen` only. No Higgsfield still-image model was used. Eight raw full-bleed contract-board plates landed at the exact requested paths in `assets/raw/`; no extraction, resizing, image processing, runtime integration, or batch 031 work was performed.

Every native generation used `plate-contract-e2-trestle.png` and `plate-contract-e5-regatta.png` as strict style masters, plus the map's run-camera and landmark verdict from `artifacts/map-rebuild-spike/` as composition truth. Far Side and Eclipse used the Mare Claim parent terrain plus their own landmark verdicts.

Native run directory: `019f7da8-9ef8-7b51-bfb2-7908e5d8ad04`.

| Plate | Final native job | Retakes | Size / mode | Mean luminance | Min edge SD | SHA-256 |
|---|---|---:|---|---:|---:|---|
| `plate-contract-e8-mare-claim.png` | `exec-099bc499-b521-4b82-adf4-5e7f495bf8f5` | 1 tonal | 1671x941 RGB | 0.314 | 0.060 | `073db1fa9247a34a96fe305a7f7d3264135a073e0448e1762c2397cbf3388bf4` |
| `plate-contract-e8-far-side.png` | `exec-6ea63828-9189-45cf-9b67-44b0db7e2612` | 0 | 1672x941 RGB | 0.277 | 0.009 | `a1228b8dd22ca7fb4f60a35f7ba585d676b1104fde868be5f99952148d10e37c` |
| `plate-contract-e8-low-orbit.png` | `exec-9d24a865-d7b3-43bc-b9d3-0cfad05c6bbc` | 0 | 1672x941 RGB | 0.283 | 0.095 | `5d9264d7e03f793797b414f12dc146bdea837a08e766a298e53961be9c4b1ffd` |
| `plate-contract-e8-eclipse.png` | `exec-de702880-7811-4caa-81cd-5b10642f4cf7` | 0 | 1671x941 RGB | 0.292 | 0.053 | `aa797389367fd222d84a39e5305a004d2bc7b65d1827a9e21602ba2f9b766fb3` |
| `plate-contract-e9-dome-basin.png` | `exec-7967fe81-12a2-47a7-970e-eb9f8ee8edea` | 0 | 1671x941 RGB | 0.354 | 0.077 | `1e9c06ff14ab8696378d53dfa1679774e1f44852d9f58569a1ae8f5a80e2c05a` |
| `plate-contract-e9-seed-run.png` | `exec-afedf202-ea23-440e-a8f6-3934c011b1ba` | 0 | 1672x941 RGB | 0.329 | 0.066 | `68f713f60ded71b2da0da1025e8f64d22b74d3f31cda60875c6aabfcff104494` |
| `plate-contract-e9-devils-alley.png` | `exec-def9126f-f416-427b-937a-91d502d85a7b` | 1 tonal | 1671x941 RGB | 0.270 | 0.049 | `7650bb0cc28cee37b8e39b41e87946910002aff9322b2f5233c6ad5fadff01f0` |
| `plate-contract-e9-old-canal.png` | `exec-ab788349-2b14-4a39-a4b9-0fc79ef7215a` | 1 tonal | 1672x941 RGB | 0.327 | 0.049 | `f9db475e37b356412613e631423bd00d893cf45dcf59ce271f9111f04ee21af8` |

## Measured and visual QA

- All eight are opaque RGB PNGs with non-uniform content reaching every edge; minimum 16-pixel edge-strip standard deviation spans 0.009-0.095, so no border or inset is present.
- Four plates are 1672x941 at the exact 1.77683 anchor aspect; four are the accepted native one-pixel-tolerance 1671x941 at 1.77577.
- Mean luminance spans 0.270-0.354, inside the six adopted anchor range measured this run at 0.131-0.385.
- Tesseract returned empty output for all eight. Full-resolution and card-scale visual review found no readable text, letters, numbers, captions, signs, logos, coded writing, or watermarks.
- Visual review found no realistic firearms, gore, border treatment, or photorealism.

| Plate | Signature read | Verdict |
|---|---|---|
| E8 Mare Claim | crater-ring basin, central ribbed commons dome, Earthrise dishes, lava-tube gantry, debris catchers and mass-driver line | PASS |
| E8 Far Side | Earthless black sky, lonely crater crossing, half-buried probe cradle, three-suit rack and solitary horizon dish | PASS |
| E8 Low Orbit | free-fall Claw-carcass yard, circular handhold roads, debris catcher and drifting salvage terrain | PASS |
| E8 Eclipse | reused Mare basin under corona and sweeping shadow, central shadow dial, paired solar witnesses, brownout lanterns | PASS |
| E9 Dome Basin | long terraced quarry basin, monumental canal gate wheel, teal water, ice hoist and Ark-yard scaffold | PASS |
| E9 Seed Run | three seed-vault wagons linking progressively green oasis waypoints between the two gates | PASS |
| E9 Devil's Alley | two anchor gates, three escalating wind-brake hoop anchors, three dust columns and airborne comic turret | PASS |
| E9 Old Canal | foreground survey rig, inherited zigzag channel, three mechanical decision frames and north outflow gate | PASS |

## Prompt set

Every generation and tonal retake included this exact sentence:

> Gold Rush engraved contract plate, the adopted board style (E2-E5 batch law): fine sepia-ink etched linework on warm parchment, restrained monochrome-warm palette with subtle golden-light accents, full-bleed 1672x941, no letters, no gore.

Each generation prompt also required the named map's chapter beat, signature terrain, mounted landmarks, edge-to-edge composition, and zero readable text, letters, numbers, signs, captions, logos, coded writing, watermarks, realistic firearms, gore, borders, or photorealism. Mare Claim, Devil's Alley, and Old Canal received one native reference-conditioned tonal edit each after measured luminance exceeded the six-anchor range; those edits preserved composition and landmarks while bringing the final plates into range.

No extraction, resizing, image processing, runtime integration, or batch 031 work was performed.
