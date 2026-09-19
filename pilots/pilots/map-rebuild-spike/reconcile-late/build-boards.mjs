// Verdict boards: the promised plate beside the delivered sculpt, one sheet per era.
//
// Each row is one map: PLATE (what was promised) | OVERVIEW (composition, scaled
// to the tile) | RUN CAMERA (what the player can actually read). Same three views
// for every map so the set is comparable rather than each map flattered by its own
// best angle.
//
// Usage: node build-boards.mjs <sheet-name> <mapId:sculpt> [mapId:sculpt ...]

import { mkdir, access } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, '../../../..');
const RENDERS = path.join(HERE, 'renders');
const SHOTS = path.join(HERE, 'shots');
const PLATES = path.join(REPO, 'assets/raw');
const OUT = path.join(HERE, 'boards');

const CELL = { width: 620, height: 388 };
const LABEL = 26;
const GUTTER = 6;
const BACKDROP = { r: 26, g: 20, b: 14 };

async function exists(file) {
  return access(file).then(() => true).catch(() => false);
}

function labelSvg(text, width, tint = '#e8d5b0') {
  const safe = text.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  return Buffer.from(
    `<svg width="${width}" height="${LABEL}"><rect width="${width}" height="${LABEL}" fill="#1a1409"/>`
    + `<text x="8" y="18" font-family="DejaVu Sans,Helvetica,Arial" font-size="14" fill="${tint}">${safe}</text></svg>`,
  );
}

async function cell(file, caption, tint) {
  const width = CELL.width;
  const height = CELL.height + LABEL;
  const canvas = sharp({ create: { width, height, channels: 3, background: BACKDROP } });
  const layers = [{ input: labelSvg(caption, width, tint), top: 0, left: 0 }];
  if (file && await exists(file)) {
    const image = await sharp(file).flatten({ background: BACKDROP })
      .resize(CELL.width, CELL.height, { fit: 'contain', background: BACKDROP }).toBuffer();
    layers.push({ input: image, top: LABEL, left: 0 });
  } else {
    layers.push({ input: labelSvg('— not available —', width, '#8a7a5c'), top: LABEL + CELL.height / 2, left: 0 });
  }
  return canvas.composite(layers).png().toBuffer();
}

async function row(map) {
  const plate = path.join(PLATES, `plate-contract-${map.id}.png`);
  const overview = map.sculpt ? path.join(RENDERS, `${map.sculpt}-overview.png`) : null;
  const run = map.sculpt ? path.join(RENDERS, `${map.sculpt}-run-camera.png`) : null;
  const live = path.join(SHOTS, `${map.id}-center.png`);
  const third = await exists(live) ? live : run;
  const thirdCaption = await exists(live)
    ? `LIVE run camera — ${map.id} (in-game)`
    : `run camera — ${map.sculpt ?? 'no sculpt'} (headless; door refuses this map)`;
  const cells = await Promise.all([
    cell(plate, `PLATE (promised) — ${map.id}`, '#f0c987'),
    cell(overview, `overview — ${map.sculpt ?? 'no sculpt'}${map.alias ? ` (alias of ${map.alias})` : ''}`, '#c9d5a8'),
    cell(third, thirdCaption, '#a8c9d5'),
  ]);
  const width = CELL.width * 3 + GUTTER * 2;
  const height = CELL.height + LABEL;
  return sharp({ create: { width, height, channels: 3, background: BACKDROP } })
    .composite(cells.map((input, index) => ({ input, top: 0, left: index * (CELL.width + GUTTER) })))
    .png().toBuffer();
}

async function main() {
  const [name, ...specs] = process.argv.slice(2);
  if (!name || !specs.length) throw new Error('usage: build-boards.mjs <sheet> <mapId:sculpt[:alias]> ...');
  await mkdir(OUT, { recursive: true });
  const maps = specs.map((spec) => {
    const [id, sculpt, alias] = spec.split(':');
    return { id, sculpt: sculpt || null, alias: alias || null };
  });
  const rows = [];
  for (const map of maps) rows.push(await row(map));
  const rowWidth = CELL.width * 3 + GUTTER * 2;
  const rowHeight = CELL.height + LABEL;
  const file = path.join(OUT, `${name}.png`);
  await sharp({
    create: {
      width: rowWidth,
      height: rowHeight * rows.length + GUTTER * (rows.length - 1),
      channels: 3,
      background: BACKDROP,
    },
  })
    .composite(rows.map((input, index) => ({ input, top: index * (rowHeight + GUTTER), left: 0 })))
    .png()
    .toFile(file);
  process.stdout.write(`${path.relative(REPO, file)} — ${rows.length} maps\n`);
}

await main();
