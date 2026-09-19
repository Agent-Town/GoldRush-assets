# Homemaker-9000 production boss model

The E6 plate defines the rounded pressure body, apron, recessed amber eye and curved household tools. The model keeps exactly three component meshes (`vac`, `rack`, `core`) and one damage morph on each. All three morphs form the storybook's powered-down chair; the runtime preserves that chair after completion.

The deterministic builder uses the native silver atlas at `assets/raw/homemaker-atlas-fidelity-e6.png`, packed into one embedded 1024-square map. The export has 11,960 triangles under the 12,000 ceiling, one painted material, and no cameras, lights or animations. Rebuild with Blender's background mode and `build_homemaker_9000.py`. The existing verifier checks component bindings, budget and byte-identical saved-Blend re-export; the adoption wrapper records its output with the corresponding V12 neutral damage metric.

Fresh arrivals use the clear flat ground at (8, 4). Existing saved coordinates remain valid. Render interpolation, offset-corrected component centering and terrain support points keep the assembly together; model hulls place its shared health bar above the current damage shape.

[Layer contract](../../layer-contracts/homemaker.v1.json) records native provenance and exact hashes. [Evidence and limits](../../../artifacts/boss-fidelity/e6-homemaker/candidate-state.md) includes matched neutral, runtime and full-bundle views. Earlier renders at the Isotope Kitchen stake are historical. Remaining differences include rough surface response and simplified tools/eye depth; old saved placement can retain its pylon overlap. Main adoption build, export, focused desktop/mobile encounter and runtime checks passed. Broad regression remains pending.
