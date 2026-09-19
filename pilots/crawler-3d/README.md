# Rival Dynamo Crawler 3D pilot

This package translates the shipped E3 boss plate into one GLB for the Canyon Works component boss. The shape reference is `assets/raw/plate-e3-boss-dynamo-crawler.png`; the fidelity pass uses a native-generated material atlas at `assets/raw/crawler-atlas-fidelity-e3.png`. Geometry is authored locally in Blender. Source hashes and measured export properties live in [the asset contract](renders/crawler-asset-contract.json); generation provenance lives in [the layer contract](../../layer-contracts/crawler.v1.json).

## Production contract

- `crawler.glb` is base-centered and normalized to 3.20 units long, under the 12,000-triangle ceiling.
- One shared material with one embedded 1024 × 1024 PNG atlas.
- Exactly three identity-transform mesh nodes:
  - `drain_mast` → `Damage_ToppledDrainMast`
  - `tracks` → `Damage_ShatteredTracks`
  - `capacitor_bank` → `Damage_RupturedCapacitorBank`
- Exactly one morph target per component, with default weight `0`.
- Three primitives, all bound to material `0`; zero cameras, lights, animations, or external textures.
- Byte-identical saved-Blend re-export under Blender 5.1.2.
- The `drain_mast` node carries `collectorAnchor.intact` and `.damaged` vectors in authored asset-root Y-up coordinates. Raw mesh transforms are identity, but production quantization can rebase mesh-local coordinates. Consumers transform loaded geometry into asset-root space before caching support or silhouette points, and apply the model's world transform to these anchors. The beam then follows the actual collector through its morph without moving combat targets.

The silhouette keeps the plate's segmented electrical mast, cylindrical dynamo, wound copper capacitor rack, teal apertures and forward ram. Exposed drive wheels retain the plate's wheel rhythm inside gameplay-required continuous treads. Unequal exhaust stacks, curved capacitor conduits, lower chambers and framed windows supply the most recognizable mechanical details. The atlas separates soot, iron, brass, copper, armor plate, teal glass, ceramic and damage oxide. Runtime lighting must preserve those differences.

The mast rotates down from its armored foot and throws ceramic fragments; the near tread belt kinks away from the drive wheels and sheds shoes; the rear rack collapses, displaces two capacitor jars, and exposes rupture cores and arc forks. The visible geometry and beam attachment may change; gameplay component positions, health, damage resolution and encounter state remain authoritative.

## Evidence

The fidelity pass's matched original/candidate evidence, runtime captures and validation receipts are under `artifacts/boss-fidelity/e3-crawler/`. Focused runtime verification passes; the full regression has explicit exceptions recorded in `reviews/sol-boss-fidelity-e3-crawler.md`. The older renders below document the pilot and must not be treated as screenshots of the current game.

- `renders/crawler-canyon-run-camera.png`: production 42° FOV and current `(0, 26.2, 18.3)` offset direction, shortened only for review coverage. The shipped heroine combat frame establishes scale and the render-only drain arc adds static pressure; the continuous gorge surface uses the shipped `ter-canyon-atlas.png`. Nothing in the context is exported or claims runtime choreography.
- `renders/crawler-turntable.png`: four intact three-quarter views.
- `renders/crawler-damage-states.png`: mast, tracks, and capacitor-bank failures from left to right.
- `renders/crawler-reference-ab.png`: the shipped painted plate beside the run-camera candidate.
- `renders/crawler-asset-contract.json`: parsed GLB contract and byte-re-export proof.

## Rebuild and verify

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/crawler-3d/build_crawler.py
bash scripts/reexport-pilot.sh assets/pilots/crawler-3d/crawler.blend
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/crawler-3d/verify_crawler.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/crawler-3d/render_crawler.py
```
