# Ark Long Table Hall E10

Fresh interior wave built from `origin/main@101c0d97e9527b26cc5c94fdafab5b4f77aa33c0`. The pushed Ark plaza dependency is `sol/ark-plaza-e10-plate@e8128c260a3ee62ef836ec33e92b1d8459cecce1`; it was not merged into this wave's base and is declared, never copied.

The production GLB is a three-sided, plaza-facing generation-ship mess hall. It carries the long table, ten blank portrait fields with `portrait_anchor_01..10`, the original handled E1 pan in its shrine, the Elder's Tree in its patched tin, ship ribs, portholes, service runs, consoles, hanging lamps, tools, cables, crates, table settings, and visible deck repairs. Portrait likenesses remain runtime/profile-compositor content; the evidence renders use abstract family-group proxies only.

Final contract: 16,308 / 20,000 triangles; one mesh/primitive/material; one embedded 2048 atlas; twelve named anchors; zero lights, cameras, or animations; byte-identical saved-BLEND re-export. Five circulation aisles ray-cast 510 samples with maximum relief `0.0420001` against the `0.05` ceiling.

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/ark-long-table-hall-e10-3d/build_ark_long_table_hall.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/ark-long-table-hall-e10-3d/verify_ark_long_table_hall.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/ark-long-table-hall-e10-3d/render_current_references.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/pilots/ark-long-table-hall-e10-3d/render_ark_long_table_hall.py
```

The neutral visual review first returned REVISE because the pan handle separated visually, the generation proxies repeated, and the room was too pristine. The revised handled silhouette, family groupings, overhead utility feed, tool storage, cable coils, crates, and maintenance dressing received SHIP.
