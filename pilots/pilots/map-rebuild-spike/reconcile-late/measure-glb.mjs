// Measure a terrain/panorama GLB against its contract, the same way the runtime does.
//
// TWO vertex counts matter, and confusing them produces false findings — this tool
// reported five healthy E1 panoramas as broken before the distinction was found:
//
//   UNIQUE positions — what the contract's `vertices` field means. inspect()
//     (Terrain3dClaimPilot.ts:204) builds a Set of "x,y,z" strings, so a
//     split-vertex export still counts as its welded total and validTerrain PASSES.
//   RAW accessor count — what bakeHeightGrid() uses at line 235:
//     `segments = round(sqrt(position.count)) - 1`. A split export inflates this,
//     the inferred grid comes out the wrong size, two vertices land in one cell and
//     it throws 'invalid terrain grid' — caught, failLoad(), painted fallback, and
//     NO console error.
//
// So a terrain is only safe when its RAW count is also a perfect square matching
// the authored grid. That is the check that was missing.
//
// Usage: node .../measure-glb.mjs <sculpt> [sculpt ...]

import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SPIKE = path.resolve(HERE, '..');

export async function readGlbJson(file) {
  const buffer = await readFile(file);
  if (buffer.readUInt32LE(0) !== 0x46546c67) throw new Error(`${file} is not a GLB`);
  let offset = 12;
  while (offset < buffer.length) {
    const length = buffer.readUInt32LE(offset);
    const type = buffer.readUInt32LE(offset + 4);
    if (type === 0x4e4f534a) return JSON.parse(buffer.toString('utf8', offset + 8, offset + 8 + length));
    offset += 8 + length;
  }
  throw new Error(`${file} has no JSON chunk`);
}

/** Counts as three.js reports them after parsing: per-primitive, summed. */
export function metricsOf(gltf, bin) {
  let vertices = 0;
  let rawVertices = 0;
  let triangles = 0;
  let meshes = 0;
  const unique = new Set();
  const materials = new Set();
  const bounds = { min: [Infinity, Infinity, Infinity], max: [-Infinity, -Infinity, -Infinity] };
  for (const node of gltf.nodes ?? []) if (node.mesh !== undefined) meshes += 1;
  for (const mesh of gltf.meshes ?? []) {
    for (const primitive of mesh.primitives ?? []) {
      const position = gltf.accessors[primitive.attributes.POSITION];
      rawVertices += position.count;
      if (bin) {
        for (const key of positionKeys(gltf, bin, primitive.attributes.POSITION)) unique.add(key);
      }
      triangles += primitive.indices !== undefined
        ? gltf.accessors[primitive.indices].count / 3
        : position.count / 3;
      if (primitive.material !== undefined) materials.add(primitive.material);
      if (position.min && position.max) {
        for (let axis = 0; axis < 3; axis += 1) {
          bounds.min[axis] = Math.min(bounds.min[axis], position.min[axis]);
          bounds.max[axis] = Math.max(bounds.max[axis], position.max[axis]);
        }
      }
    }
  }
  vertices = bin ? unique.size : rawVertices;
  // A baked grid is (n+1)^2. If the RAW count is not that perfect square,
  // bakeHeightGrid infers the wrong resolution and the map falls back to painted.
  const root = Math.sqrt(rawVertices);
  return {
    meshes, vertices, rawVertices, triangles, materials: materials.size, bounds,
    gridSafe: Number.isInteger(root),
  };
}

const COMPONENT = { 5120: Int8Array, 5121: Uint8Array, 5122: Int16Array, 5123: Uint16Array, 5125: Uint32Array, 5126: Float32Array };

function* positionKeys(gltf, bin, accessorIndex) {
  const spec = gltf.accessors[accessorIndex];
  const view = gltf.bufferViews[spec.bufferView];
  const Type = COMPONENT[spec.componentType];
  const start = (view.byteOffset ?? 0) + (spec.byteOffset ?? 0);
  const data = new Type(bin.buffer, bin.byteOffset + start, spec.count * 3);
  for (let i = 0; i < data.length; i += 3) yield `${data[i]},${data[i + 1]},${data[i + 2]}`;
}

export async function readGlbBin(file) {
  const buffer = await readFile(file);
  let offset = 12;
  while (offset < buffer.length) {
    const length = buffer.readUInt32LE(offset);
    const type = buffer.readUInt32LE(offset + 4);
    if (type === 0x004e4942) return buffer.subarray(offset + 8, offset + 8 + length);
    offset += 8 + length;
  }
  return null;
}

/**
 * glTF is Y-up, the contract is authored Z-up (Blender). The runtime compares
 * contract.min[0..2] = x,z,y against three.js bounds x,y,z — i.e. the contract's
 * third component is the HEIGHT. Convert here so the comparison is apples-to-apples.
 */
function contractBoundsAsGltf(contract) {
  if (!contract.boundsMeters) return null;
  const [minX, minZ, minY] = contract.boundsMeters.min;
  const [maxX, maxZ, maxY] = contract.boundsMeters.max;
  return { min: [minX, minY, minZ], max: [maxX, maxY, maxZ] };
}

async function report(sculpt) {
  const rows = [];
  for (const kind of ['terrain', 'panorama']) {
    const glb = path.join(SPIKE, `${sculpt}-${kind}.glb`);
    const contractFile = path.join(SPIKE, `${sculpt}-${kind}-contract.json`);
    let gltf;
    let bin;
    let contract;
    try {
      gltf = await readGlbJson(glb);
      bin = await readGlbBin(glb);
    } catch (error) {
      rows.push({ sculpt, kind, error: String(error.message ?? error) });
      continue;
    }
    try {
      contract = JSON.parse(await readFile(contractFile, 'utf8'));
    } catch {
      contract = null;
    }
    const measured = metricsOf(gltf, bin);
    const expected = contract && {
      meshes: contract.meshCount, triangles: contract.triangles,
      materials: contract.materialCount, vertices: contract.vertices,
      bounds: contractBoundsAsGltf(contract),
    };
    const mismatches = [];
    if (kind === 'terrain' && !measured.gridSafe) {
      mismatches.push(`raw vertex count ${measured.rawVertices} is not a perfect square — bakeHeightGrid would throw 'invalid terrain grid' and the map falls back to painted`);
    }
    if (expected) {
      for (const key of ['meshes', 'triangles', 'materials', 'vertices']) {
        if (expected[key] !== undefined && expected[key] !== measured[key]) {
          mismatches.push(`${key}: contract ${expected[key]} vs glb ${measured[key]}`);
        }
      }
      if (expected.bounds) {
        for (let axis = 0; axis < 3; axis += 1) {
          for (const side of ['min', 'max']) {
            const delta = Math.abs(expected.bounds[side][axis] - measured.bounds[side][axis]);
            if (delta > 0.03) {
              mismatches.push(`bounds.${side}[${'xyz'[axis]}]: contract ${expected.bounds[side][axis]} vs glb ${measured.bounds[side][axis].toFixed(4)} (Δ${delta.toFixed(4)})`);
            }
          }
        }
      }
    }
    rows.push({ sculpt, kind, measured, expected, mismatches, valid: Boolean(contract) && !mismatches.length });
  }
  return rows;
}

export async function measure(sculpts) {
  const all = [];
  for (const sculpt of sculpts) all.push(...await report(sculpt));
  return all;
}

// CLI only — this module is also imported by capture.mjs.
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const all = await measure(process.argv.slice(2));
  for (const row of all) {
    if (row.error) { console.log(`${row.sculpt}-${row.kind}: ${row.error}`); continue; }
    const flag = row.valid ? 'VALID  ' : 'INVALID';
    console.log(`${flag} ${row.sculpt}-${row.kind}: meshes=${row.measured.meshes} tris=${row.measured.triangles} verts=${row.measured.vertices} (raw ${row.measured.rawVertices}) mats=${row.measured.materials}`);
    for (const mismatch of row.mismatches ?? []) console.log(`        ${mismatch}`);
  }
  if (process.env.GR_MEASURE_JSON) console.log(JSON.stringify(all, null, 2));
}
