/**
 * THE MAP RECONCILIATION (early half) — verdict boards.
 *
 * Two shapes, both side-by-side at one height so the eye compares rather than
 * remembers:
 *   --plate   engraved PLATE (the promised look) | the living map at the run camera
 *   --ab      before | after, same door, same camera (the fix-in-place proof)
 *
 * Filenames carry the labels (the fresh-eye sheet convention) — no font baked in,
 * so a board never lies about which side is which.
 *
 * Usage:
 *   node reconcile_boards.mjs --plate            # every map with a shot on disk
 *   node reconcile_boards.mjs --plate the-claim,e1-baron
 *   node reconcile_boards.mjs --ab e2-trestle --before <path> --after <path>
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';
import { PNG } from 'pngjs';
import { EARLY_MAPS } from './reconcile_boot.mjs';

const ROOT = path.resolve(import.meta.dirname, '../../..');
const SHOTS = path.join(ROOT, 'artifacts/map-reconcile-early');
const BOARDS = path.join(SHOTS, 'boards');
const PANEL_HEIGHT = 620;
const GUTTER = 12;
const CANVAS_RGB = [0.30 * 255, 0.18 * 255, 0.07 * 255];

/** door id -> plate stem. The plates predate the door prefixes for E1/E2 signatures. */
const PLATE = {
  'the-claim': 'the-claim',
  'e1-dry-gulch': 'dry-gulch',
  'e1-night-shift': 'night-shift',
  'e1-twin-banks': 'twin-banks',
  'e1-baron': 'baron',
  'e2-hill-mine': 'hill-mine',
};

export function plateFor(id) {
  const stem = PLATE[id] ?? id;
  return path.join(ROOT, `assets/raw/plate-contract-${stem}.png`);
}

function load(file) {
  return PNG.sync.read(readFileSync(file));
}

/** Box-filter downscale to a target height; keeps the engraving legible. */
function scaleToHeight(png, height) {
  const width = Math.max(1, Math.round((png.width / png.height) * height));
  const out = new PNG({ width, height });
  const xRatio = png.width / width;
  const yRatio = png.height / height;
  for (let y = 0; y < height; y += 1) {
    const y0 = Math.floor(y * yRatio);
    const y1 = Math.max(y0 + 1, Math.floor((y + 1) * yRatio));
    for (let x = 0; x < width; x += 1) {
      const x0 = Math.floor(x * xRatio);
      const x1 = Math.max(x0 + 1, Math.floor((x + 1) * xRatio));
      let r = 0, g = 0, b = 0, count = 0;
      for (let sy = y0; sy < y1 && sy < png.height; sy += 1) {
        for (let sx = x0; sx < x1 && sx < png.width; sx += 1) {
          const offset = (sy * png.width + sx) * 4;
          r += png.data[offset]; g += png.data[offset + 1]; b += png.data[offset + 2];
          count += 1;
        }
      }
      const offset = (y * width + x) * 4;
      out.data[offset] = Math.round(r / count);
      out.data[offset + 1] = Math.round(g / count);
      out.data[offset + 2] = Math.round(b / count);
      out.data[offset + 3] = 255;
    }
  }
  return out;
}

function board(panels, target) {
  const scaled = panels.map((panel) => scaleToHeight(panel, PANEL_HEIGHT));
  const width = scaled.reduce((sum, panel) => sum + panel.width, 0) + GUTTER * (scaled.length - 1);
  const out = new PNG({ width, height: PANEL_HEIGHT });
  for (let i = 0; i < out.data.length; i += 4) {
    out.data[i] = CANVAS_RGB[0]; out.data[i + 1] = CANVAS_RGB[1]; out.data[i + 2] = CANVAS_RGB[2]; out.data[i + 3] = 255;
  }
  let x = 0;
  for (const panel of scaled) {
    PNG.bitblt(panel, out, 0, 0, panel.width, panel.height, x, 0);
    x += panel.width + GUTTER;
  }
  mkdirSync(path.dirname(target), { recursive: true });
  writeFileSync(target, PNG.sync.write(out));
  return { target: path.relative(ROOT, target), width, height: PANEL_HEIGHT };
}

const args = process.argv.slice(2);
const flag = (name) => {
  const index = args.indexOf(`--${name}`);
  return index === -1 ? null : args[index + 1];
};

if (args.includes('--plate')) {
  const only = args[args.indexOf('--plate') + 1];
  const ids = only && !only.startsWith('--') ? only.split(',') : EARLY_MAPS.map((map) => map.id);
  for (const id of ids) {
    const live = path.join(SHOTS, `${id}-desktop.png`);
    const plate = plateFor(id);
    if (!existsSync(live)) { console.log(`skip ${id}: no live shot`); continue; }
    if (!existsSync(plate)) { console.log(`skip ${id}: no plate`); continue; }
    const result = board([load(plate), load(live)], path.join(BOARDS, `${id}-PLATE-vs-LIVE.png`));
    console.log(`${id.padEnd(20)} ${result.width}x${result.height}  ${result.target}`);
  }
}

if (args.includes('--ab')) {
  const id = args[args.indexOf('--ab') + 1];
  const before = flag('before') ?? path.join(SHOTS, `before/${id}-desktop.png`);
  const after = flag('after') ?? path.join(SHOTS, `${id}-desktop.png`);
  const panels = [load(before), load(after)];
  if (args.includes('--with-plate')) panels.unshift(load(plateFor(id)));
  const name = args.includes('--with-plate') ? `${id}-PLATE-vs-BEFORE-vs-AFTER.png` : `${id}-BEFORE-vs-AFTER.png`;
  const result = board(panels, path.join(BOARDS, name));
  console.log(`${id.padEnd(20)} ${result.width}x${result.height}  ${result.target}`);
}
