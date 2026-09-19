# Salvage King's Claw production model

The active runtime asset is `salvage-claw-detail-opus5.glb`, built by `build_salvage_claw_detail_opus5.py`. It uses three named components and their original landing morphs; gameplay anchors and encounter transitions are unchanged.

The fidelity pass gives the Claw wider suspended grabbers, exposed paired drums, a rounded lower body, dedicated metal textures, shuttered windows and deployable ladders with open rail exits. Crown width remains 11.4 units; the intact visual envelope is about 14.493 × 14.493 × 12.042 units before runtime scale 0.78. Landed ladders extend beyond that envelope. The additional reach is visual and does not enlarge damage or targeting bounds.

The model has 30,844 triangles and one embedded 1024-square atlas generated with native image_gen. Its source and asset hashes are recorded in `../../layer-contracts/salvage-claw.v1.json`. The shared geometry kit remains a dependency; the Dredge Queen's changing atlas builder does not.

Rebuild with Blender running `build_salvage_claw_detail_opus5.py`. The saved Blend also supports `scripts/reexport-pilot.sh`. Current evidence lives in `artifacts/boss-fidelity/e8-salvage-claw/`; adoption, export/build, unchanged encounter tests and scoped production/lifecycle checks passed. Earlier models and renders remain historical comparison material. Geometry and engraving remain simpler than the concept; no people are baked into the asset.
