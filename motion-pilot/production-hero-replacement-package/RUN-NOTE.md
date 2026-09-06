---
source: codex
project: Gold Rush
date: 2026-07-10
type: digest
---

# Hero Replacement Package

Task: `/Users/robin/Claude/Projects/Gold Rush/tasks/running/art--20260710-220139-art-hero-replacement-package.md`

## Scope

- Restored the true v3 hero walk8 raw by moving the mixed/rejected sheet to `assets/raw/char-hero-sheet-walk8-rejected-mixed.png` and copying `assets/motion-pilot/production-hero-v3/char-hero-sheet-walk8.png` back to `assets/raw/char-hero-sheet-walk8.png`.
- Generated female hero drop-in replacements for the other male-hero runtime/key-art files, keeping originals untouched and writing only new `*-f.png` raws.
- Processed runtime replacements through `scripts/extract-alpha.mjs`.
- Kept the flip dark: no `src/` or `assets/layer-contracts/` edits.

## Generator

Generator: Higgsfield GPT Image 2.

Account credits: 115 before this package, 24 after this package. Spend: 91 credits across 13 image jobs. Retakes: 0.

Transient wait errors occurred while polling some jobs (`request failed (no response received)`), but pending-job recovery found the original jobs and avoided duplicate generation spend.

## Outputs

| Original target | New raw | Processing |
|---|---|---|
| `assets/raw/hero-homesteader.png` | `assets/raw/hero-homesteader-f.png` | `extract-alpha` gray key, display 384px plus full copy |
| `assets/raw/char-hero-sheet-front.png` | `assets/raw/char-hero-sheet-front-f.png` | `--key ff00ff --grid 3x2`, 6 cells |
| `assets/raw/char-hero-sheet-back.png` | `assets/raw/char-hero-sheet-back-f.png` | `--key ff00ff --grid 3x2`, 6 cells |
| `assets/raw/char-hero-sheet-side.png` | `assets/raw/char-hero-sheet-side-f.png` | `--key ff00ff --grid 2x2`, 4 cells |
| `assets/raw/char-hero-sheet-side-actions.png` | `assets/raw/char-hero-sheet-side-actions-f.png` | `--key ff00ff --grid 3x2`, 6 cells |
| `assets/raw/char-hero-sheet-rotation.png` | `assets/raw/char-hero-sheet-rotation-f.png` | `--key ff00ff --grid 4x3`, 12 cells |
| `assets/raw/char-hero-sheet-rotation2.png` | `assets/raw/char-hero-sheet-rotation2-f.png` | `--key ff00ff --grid 4x2`, 8 cells |
| `assets/raw/char-hero-sheet-walk4-a.png` | `assets/raw/char-hero-sheet-walk4-a-f.png` | `--key ff00ff --grid 4x4`, 16 cells |
| `assets/raw/char-hero-sheet-walk4-b.png` | `assets/raw/char-hero-sheet-walk4-b-f.png` | `--key ff00ff --grid 4x4`, 16 cells |
| `assets/raw/mkt-hero-16x9.png` | `assets/raw/mkt-hero-16x9-f.png` | raw key art only |
| `assets/raw/mkt-hero-9x16.png` | `assets/raw/mkt-hero-9x16-f.png` | raw key art only |
| `assets/raw/mkt-hero-1x1.png` | `assets/raw/mkt-hero-1x1-f.png` | raw key art only |
| `assets/raw/mkt-og-banner.png` | `assets/raw/mkt-og-banner-f.png` | raw key art only |

Processed count: 75 display PNGs in `assets/processed/`, 75 preserved full-size PNGs in `assets/processed-full/`, and 8 frames JSON manifests in `assets/processed/`.

## Job IDs

| File | Job ID |
|---|---|
| `hero-homesteader-f.png` | `e8ef10d9-c923-47cc-bfeb-de8d202559dd` |
| `char-hero-sheet-front-f.png` | `b63b8c23-640c-4b06-b9f1-c424d8926336` |
| `char-hero-sheet-back-f.png` | `03467652-90bf-400d-8c97-f8c310debb06` |
| `char-hero-sheet-side-f.png` | `4835b34b-4324-4c04-af81-e69de0b9abf7` |
| `char-hero-sheet-side-actions-f.png` | `8f377f25-044c-4c5f-897b-79f2a1be8301` |
| `char-hero-sheet-rotation-f.png` | `a0013119-182f-4924-81cb-eb90cb40f580` |
| `char-hero-sheet-rotation2-f.png` | `ee0e32ff-6bfd-41ab-8e53-4af175702d78` |
| `char-hero-sheet-walk4-a-f.png` | `6b189df2-3741-44c5-827c-b46910c4b6ba` |
| `char-hero-sheet-walk4-b-f.png` | `040a77a3-fbe7-4202-9558-62fbb122f9ae` |
| `mkt-hero-16x9-f.png` | `3ccae82d-871c-4b83-a14e-12172a106f1b` |
| `mkt-hero-9x16-f.png` | `b7418168-8b65-412a-b6ce-2fb7efcca717` |
| `mkt-hero-1x1-f.png` | `f412600d-d57d-4ca0-a3b4-54abbb272305` |
| `mkt-og-banner-f.png` | `32989f49-eaab-4331-9398-8452987dea50` |

Full manifest: `assets/motion-pilot/production-hero-replacement-package/generation-results.json`. Downloaded source files are under `assets/motion-pilot/production-hero-replacement-package/downloads/`.

## Processing Commands

```sh
node scripts/extract-alpha.mjs assets/raw/hero-homesteader-f.png
node scripts/extract-alpha.mjs --key ff00ff --grid 3x2 assets/raw/char-hero-sheet-front-f.png assets/raw/char-hero-sheet-back-f.png assets/raw/char-hero-sheet-side-actions-f.png
node scripts/extract-alpha.mjs --key ff00ff --grid 2x2 assets/raw/char-hero-sheet-side-f.png
node scripts/extract-alpha.mjs --key ff00ff --grid 4x3 assets/raw/char-hero-sheet-rotation-f.png
node scripts/extract-alpha.mjs --key ff00ff --grid 4x2 assets/raw/char-hero-sheet-rotation2-f.png
node scripts/extract-alpha.mjs --key ff00ff --grid 4x4 assets/raw/char-hero-sheet-walk4-a-f.png assets/raw/char-hero-sheet-walk4-b-f.png
```

After extraction, the new display copies were resized to the current display budget: sprite cells 256x256 and `hero-homesteader-f.png` 384x384. Full extraction copies were preserved in `assets/processed-full/` before display resizing.

## QA

- V3 walk8 restore verified by SHA: `assets/raw/char-hero-sheet-walk8.png` matches `assets/motion-pilot/production-hero-v3/char-hero-sheet-walk8.png`.
- Rejected mixed walk8 is preserved as `assets/raw/char-hero-sheet-walk8-rejected-mixed.png`.
- Raw replacement dimensions match target families: 1254x1254 square sheets/cutout, 1700x1700 walk4 sheets, 1672x941 / 941x1672 / 1254x1254 / 1730x909 marketing set.
- Visual contact sheets: `assets/contact-sheets/art-hero-replacement-package-raws.png` and `assets/contact-sheets/art-hero-replacement-package-processed-sample.png`.
- Visual QA pass: young woman hero identity, braid, teal charm, satchel-left/pan-right intent, warm Frontier Ledger palette, no readable text/letters/logos, no firearms, no gore. Marketing replacements preserve the hero plus Prospector companion read.
- Minor caveat: one processed side-walk sample shows a tiny residual brown fleck below the foot area; it is small and non-blocking for a dark flip.

## Flip Plan

After owner pan-side verdict, flip the package in one registry-only commit by editing `assets/layer-contracts/characters.v2.json` and no `src/`: update `char.hero.fallback.file` to `hero-homesteader-f.png`; update `char.hero.rotations.directions.*.frames.files`, `char.hero.walk4.directions.*.frames.files`, `char.hero.orientations.side.frames.files`, `char.hero.orientations.front.frames.grid.file/order`, and `char.hero.orientations.back.frames.grid.file/order` to the matching processed `*-f` frame filenames; then set `char.hero.walk8.enabled=true` only if the owner also approves walk8 activation. Marketing/public swaps should be a separate publication commit or copy-over after owner approval, using `mkt-hero-16x9-f.png`, `mkt-hero-9x16-f.png`, `mkt-hero-1x1-f.png`, and `mkt-og-banner-f.png`.
