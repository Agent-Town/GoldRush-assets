# Rival Dynamo Crawler 3D pilot

This package translates the shipped E3 boss plate into one production GLB for the Canyon Works component-boss seam. The queue uses `plate-e3-boss-crawler.png` as shorthand; the ledger-backed source present in the repository is `assets/raw/plate-e3-boss-dynamo-crawler.png` (SHA-256 `eb52e2b77695536c2216958daae45028f044c6a80757ff4450424f59a3dae086`). No generated substitute or external 3D service was used.

## Production contract

- `crawler.glb`: base-centered, 3.20 units long, 1.389 wide, and 2.6775 high.
- 11,980 triangles under the 12,000 ceiling.
- One shared material with one embedded 1024 × 1024 PNG atlas baked from the Crawler plate.
- Exactly three identity-transform mesh nodes:
  - `drain_mast` → `Damage_ToppledDrainMast`
  - `tracks` → `Damage_ShatteredTracks`
  - `capacitor_bank` → `Damage_RupturedCapacitorBank`
- Exactly one morph target per component, with default weight `0`.
- Three primitives, all bound to material `0`; zero cameras, lights, animations, or external textures.
- Byte-identical saved-Blend re-export under Blender 5.1.2.
- No runtime or simulation edits. The factory-owned Crawler choreography mounts this asset through the railcar-style presentation seam.

The silhouette keeps the plate's tall insulator-crowned drain mast, riveted cylindrical dynamo, copper capacitor rack, teal current apertures, and heavy forward ram. Continuous tread shoes, drive wheels, and side frames make the lower chassis read as a crawler rather than a railcar. The single atlas preserves the plate's engraved scratches, near-black iron, structural brass, copper coils, tan ceramic, and restrained voltage teal without emission.

The damage morphs are structural rather than cosmetic. The mast rotates down from its armored foot and throws ceramic fragments; the near tread belt kinks away from the drive wheels and sheds shoes; the rear rack collapses, displaces two capacitor jars, and exposes hot rupture cores and arc forks. The factory may add the same per-component damage tint used by the railcar without changing these mesh contracts.

## Evidence

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
