// Relief statistics per terrain, so "this map reads as flat" is a measurement
// rather than an impression — and so an apparent HOLE can be told apart from a
// pit that simply drops below the studio backdrop plane.
//
// The fresh-eye arc recorded a rectangular hole in dome-basin's mesh that turned
// out to be a flat floor. A boundary-edge count settles that question outright:
// a real hole has interior boundary edges, a flat floor has none.
//
// Usage: node height-stats.mjs <sculpt> [sculpt ...]

import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readGlbJson } from './measure-glb.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SPIKE = path.resolve(HERE, '..');

const COMPONENT = { 5120: Int8Array, 5121: Uint8Array, 5122: Int16Array, 5123: Uint16Array, 5125: Uint32Array, 5126: Float32Array };
const COUNT = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16 };

async function binChunk(file) {
  const buffer = await readFile(file);
  let offset = 12;
  while (offset < buffer.length) {
    const length = buffer.readUInt32LE(offset);
    const type = buffer.readUInt32LE(offset + 4);
    if (type === 0x004e4942) return buffer.subarray(offset + 8, offset + 8 + length);
    offset += 8 + length;
  }
  throw new Error('no BIN chunk');
}

function accessor(gltf, bin, index) {
  const spec = gltf.accessors[index];
  const view = gltf.bufferViews[spec.bufferView];
  const Type = COMPONENT[spec.componentType];
  const stride = COUNT[spec.type];
  const start = (view.byteOffset ?? 0) + (spec.byteOffset ?? 0);
  return new Type(bin.buffer, bin.byteOffset + start, spec.count * stride);
}

function stats(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
  const deviation = Math.sqrt(values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / values.length);
  const quantile = (q) => sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * q))];
  return {
    min: sorted[0], max: sorted[sorted.length - 1], mean, deviation,
    p05: quantile(0.05), p50: quantile(0.5), p95: quantile(0.95),
  };
}

/** An interior boundary edge = an edge used by exactly one triangle. That is a hole. */
function boundaryEdges(indices) {
  const counts = new Map();
  const bump = (a, b) => {
    const key = a < b ? `${a}_${b}` : `${b}_${a}`;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  };
  for (let i = 0; i < indices.length; i += 3) {
    bump(indices[i], indices[i + 1]);
    bump(indices[i + 1], indices[i + 2]);
    bump(indices[i + 2], indices[i]);
  }
  let boundary = 0;
  for (const count of counts.values()) if (count === 1) boundary += 1;
  return boundary;
}

async function report(sculpt) {
  const file = path.join(SPIKE, `${sculpt}-terrain.glb`);
  const gltf = await readGlbJson(file);
  const bin = await binChunk(file);
  const primitive = gltf.meshes[0].primitives[0];
  const positions = accessor(gltf, bin, primitive.attributes.POSITION);
  const indices = accessor(gltf, bin, primitive.indices);
  // glTF is Y-up: component 1 is height.
  const heights = [];
  for (let i = 1; i < positions.length; i += 3) heights.push(positions[i]);
  const boundary = boundaryEdges(indices);
  // The perimeter of a 128x128 quad grid is 4 * 128 = 512 boundary edges. Anything
  // beyond that is an interior hole.
  const segments = Math.round(Math.sqrt(heights.length)) - 1;
  const perimeter = segments * 4;
  const height = stats(heights);
  // How much of the tile is within 25 cm of its own median — the "reads as a slab" number.
  const flat = heights.filter((value) => Math.abs(value - height.p50) < 0.25).length / heights.length;
  return {
    sculpt,
    vertices: heights.length,
    relief_m: +(height.max - height.min).toFixed(3),
    min_m: +height.min.toFixed(3),
    max_m: +height.max.toFixed(3),
    p05_m: +height.p05.toFixed(3),
    p50_m: +height.p50.toFixed(3),
    p95_m: +height.p95.toFixed(3),
    stdev_m: +height.deviation.toFixed(3),
    flat_fraction: +flat.toFixed(3),
    boundary_edges: boundary,
    expected_perimeter: perimeter,
    interior_holes: boundary > perimeter,
  };
}

const rows = [];
for (const sculpt of process.argv.slice(2)) {
  try {
    rows.push(await report(sculpt));
  } catch (error) {
    rows.push({ sculpt, error: String(error.message ?? error) });
  }
}
const header = ['sculpt', 'relief', 'min', 'max', 'p05', 'p50', 'p95', 'stdev', 'flat%', 'holes'];
console.log(header.map((h, i) => (i ? h.padStart(8) : h.padEnd(18))).join(' '));
for (const row of rows) {
  if (row.error) { console.log(`${row.sculpt.padEnd(18)} ${row.error}`); continue; }
  console.log([
    row.sculpt.padEnd(18),
    String(row.relief_m).padStart(8), String(row.min_m).padStart(8), String(row.max_m).padStart(8),
    String(row.p05_m).padStart(8), String(row.p50_m).padStart(8), String(row.p95_m).padStart(8),
    String(row.stdev_m).padStart(8), String((row.flat_fraction * 100).toFixed(1)).padStart(8),
    String(row.interior_holes ? `YES(${row.boundary_edges}/${row.expected_perimeter})` : 'no').padStart(8),
  ].join(' '));
}
if (process.env.GR_STATS_JSON) console.log(JSON.stringify(rows, null, 2));
