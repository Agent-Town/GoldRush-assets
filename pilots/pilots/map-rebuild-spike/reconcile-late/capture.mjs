// THE MAP RECONCILIATION (late half) — run-camera capture harness.
//
// Boots each late-era map in the REAL game at the REAL gameplay camera
// (vite dev server on a scratch port + playwright chromium), samples the tile by
// teleporting the hero, and writes shots + a measured diagnostics record per map.
//
// Deliberately NOT a per-map Blender hero angle: the craftbook's rule is
// "the run camera is the judge" and a builder-posed angle is exactly how a weak
// composition survives review (SOL-3D-D-CRAFTBOOK §2, reviews/opus5-3d-findings.md).
//
// Usage: node assets/pilots/map-rebuild-spike/reconcile-late/capture.mjs [mapId ...]

import { spawn } from 'node:child_process';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { metricsOf, readGlbJson } from './measure-glb.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, '../../../..');
const OUT = path.join(HERE, 'shots');
const PORT = Number(process.env.GR_RECONCILE_PORT ?? 5241);
const BASE = `http://127.0.0.1:${PORT}`;

/** The twenty maps of the late half, in era order, with their sculpt source. */
export const MAPS = [
  { id: 'e6-glow-mesa', era: 6, sculpt: 'glow-mesa' },
  { id: 'e6-showroom', era: 6, sculpt: 'showroom' },
  { id: 'e6-half-life-hollow', era: 6, sculpt: 'half-life-hollow' },
  { id: 'e6-picnic', era: 6, sculpt: 'glow-mesa', alias: 'e6-glow-mesa' },
  { id: 'e7-relay-valley', era: 7, sculpt: 'relay-valley' },
  { id: 'e7-echo-canyon', era: 7, sculpt: 'echo-canyon' },
  { id: 'e7-dead-band', era: 7, sculpt: 'relay-valley', alias: 'e7-relay-valley' },
  { id: 'e7-relay-rush', era: 7, sculpt: 'relay-valley', alias: 'e7-relay-valley' },
  { id: 'e8-mare-claim', era: 8, sculpt: 'mare-claim' },
  { id: 'e8-far-side', era: 8, sculpt: 'mare-claim', alias: 'e8-mare-claim' },
  { id: 'e8-low-orbit', era: 8, sculpt: 'low-orbit' },
  { id: 'e8-eclipse', era: 8, sculpt: 'mare-claim', alias: 'e8-mare-claim' },
  { id: 'e9-dome-basin', era: 9, sculpt: 'dome-basin' },
  { id: 'e9-seed-run', era: 9, sculpt: 'seed-run' },
  { id: 'e9-devils-alley', era: 9, sculpt: 'devils-alley' },
  { id: 'e9-old-canal', era: 9, sculpt: 'old-canal' },
  { id: 'e10-ember-shore', era: 10, sculpt: 'ember-shore' },
  { id: 'e10-archive-world', era: 10, sculpt: 'archive-world' },
  { id: 'e10-last-claim', era: 10, sculpt: null },
  { id: 'e10-river', era: 10, sculpt: null },
];

async function waitForServer(url, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(2_000) });
      if (response.ok) return;
    } catch {
      // server not up yet
    }
    await new Promise((resolve) => setTimeout(resolve, 400));
  }
  throw new Error(`dev server did not answer ${url} within ${timeoutMs}ms`);
}

async function tileBounds(sculpt) {
  if (!sculpt) return null;
  try {
    const text = await readFile(path.join(HERE, '..', `${sculpt}-terrain-contract.json`), 'utf8');
    const contract = JSON.parse(text);
    const { min, max } = contract.boundsMeters ?? {};
    if (min && max) return { minX: min[0], maxX: max[0], minZ: min[1], maxZ: max[1], minY: min[2], maxY: max[2] };
  } catch {
    // fall through to the mesh's own bounds
  }
  // Several contracts (low-orbit, seed-run, devils-alley, old-canal) carry no
  // boundsMeters — the registry supplies them. Measure the GLB instead of
  // silently degrading to a single centre shot.
  try {
    const gltf = await readGlbJson(path.join(HERE, '..', `${sculpt}-terrain.glb`));
    const { bounds } = metricsOf(gltf);
    return {
      minX: bounds.min[0], maxX: bounds.max[0],
      minZ: bounds.min[2], maxZ: bounds.max[2],
      minY: bounds.min[1], maxY: bounds.max[1],
    };
  } catch {
    return null;
  }
}

/** Sample spots across the tile, in the hero's own frame — the player's real read. */
function samples(bounds) {
  if (!bounds) return [{ name: 'center', x: 0, z: 0 }];
  const halfX = Math.min(46, (bounds.maxX - bounds.minX) / 2 - 8);
  const halfZ = Math.min(46, (bounds.maxZ - bounds.minZ) / 2 - 8);
  return [
    { name: 'center', x: 0, z: 0 },
    { name: 'north', x: 0, z: -Math.round(halfZ * 0.72) },
    { name: 'south', x: 0, z: Math.round(halfZ * 0.72) },
    { name: 'west', x: -Math.round(halfX * 0.72), z: 0 },
    { name: 'east', x: Math.round(halfX * 0.72), z: 0 },
  ];
}

async function captureMap(page, map) {
  const errors = { console: [], page: [] };
  page.removeAllListeners('console');
  page.removeAllListeners('pageerror');
  page.on('console', (message) => { if (message.type() === 'error') errors.console.push(message.text()); });
  page.on('pageerror', (error) => errors.page.push(error.message));

  const record = { id: map.id, era: map.era, sculpt: map.sculpt, alias: map.alias ?? null, shots: [], errors };
  const url = `${BASE}/?debug&era=${map.era}&contract=${map.id}`
    + `&nowaves&nolevel&nokill&nopause&tier=full&seed=reconcile-${map.id}`;
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(
    () => Boolean(window.__GR_TEST__) && (window.__THREE_GAME_DIAGNOSTICS__?.frame ?? 0) > 10,
    undefined,
    { timeout: 30_000 },
  );
  const dismiss = page.getByTestId('contract-briefing-dismiss');
  if (await dismiss.isVisible().catch(() => false)) await dismiss.click();
  await page.waitForFunction(
    () => document.querySelector('#game-canvas')?.dataset.terrain3dPilotState !== 'loading',
    undefined,
    { timeout: 30_000 },
  );
  // Landmarks resolve after the terrain mounts; a 'pending' read would mis-report an
  // empty map as a landmark-less one. Soft wait — some maps legitimately mount none.
  await page.waitForFunction(
    () => document.querySelector('#game-canvas')?.dataset.terrain3dPilotLandmarkLoadState !== 'pending',
    undefined,
    { timeout: 15_000 },
  ).catch(() => {});

  record.activeContract = await page.evaluate(() => window.__GR_TEST__.activeContract().id);
  // THE DOOR GUARD. Without it this harness quietly judged twelve maps while the
  // game had opened `the-claim` — the contract door falls back when campaign state
  // in the browser profile says the map is not reachable. Every shot would have
  // been of E1's river tile with the target map's HUD on top. Fail loud.
  if (record.activeContract !== map.id) throw new Error(`door opened ${record.activeContract}, asked for ${map.id}`);
  record.diagnostics = await page.evaluate(() => ({ ...document.querySelector('#game-canvas').dataset }));
  record.bounds = await tileBounds(map.sculpt);

  for (const spot of samples(record.bounds)) {
    await page.evaluate(({ x, z }) => window.__GR_TEST__.teleport(x, z), spot);
    const frame = await page.evaluate(() => window.__THREE_GAME_DIAGNOSTICS__?.frame ?? 0);
    await page.waitForFunction(
      (from) => (window.__THREE_GAME_DIAGNOSTICS__?.frame ?? 0) >= from + 8,
      frame,
      { timeout: 10_000 },
    );
    const file = path.join(OUT, `${map.id}-${spot.name}.png`);
    await page.locator('#game-canvas').screenshot({ path: file });
    record.shots.push({ name: spot.name, x: spot.x, z: spot.z, file: path.relative(REPO, file) });
  }
  return record;
}

async function main() {
  const only = process.argv.slice(2);
  const targets = only.length ? MAPS.filter((map) => only.includes(map.id)) : MAPS;
  if (!targets.length) throw new Error(`no maps matched ${only.join(', ')}`);
  await mkdir(OUT, { recursive: true });

  const server = spawn('npx', ['vite', '--host', '127.0.0.1', '--port', String(PORT), '--strictPort'], {
    cwd: REPO, stdio: ['ignore', 'pipe', 'pipe'],
  });
  server.stdout.on('data', () => {});
  server.stderr.on('data', (chunk) => process.stderr.write(`[vite] ${chunk}`));

  const records = [];
  try {
    await waitForServer(BASE, 60_000);
    const browser = await chromium.launch({ channel: 'chromium' });
    try {
      for (const map of targets) {
        process.stdout.write(`capturing ${map.id} ... `);
        // A FRESH CONTEXT PER MAP. Sharing one profile let campaign progression
        // leak between boots, which is what made the contract door fall back.
        const context = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1 });
        try {
          const record = await captureMap(await context.newPage(), map);
          records.push(record);
          process.stdout.write(`${record.shots.length} shots, source=${record.diagnostics.terrain3dPilotRenderSource}`
            + `, pano=${record.diagnostics.terrain3dPilotPanorama}`
            + `, console=${record.errors.console.length}\n`);
        } catch (error) {
          records.push({ id: map.id, era: map.era, sculpt: map.sculpt, failed: String(error).split('\n')[0] });
          process.stdout.write(`FAILED ${String(error).split('\n')[0]}\n`);
        } finally {
          await context.close();
        }
      }
    } finally {
      await browser.close();
    }
  } finally {
    server.kill('SIGTERM');
  }

  const summary = path.join(HERE, 'capture.json');
  const previous = only.length
    ? await readFile(summary, 'utf8').then((text) => JSON.parse(text).maps ?? []).catch(() => [])
    : [];
  const merged = [...previous.filter((row) => !records.some((record) => record.id === row.id)), ...records]
    .sort((a, b) => MAPS.findIndex((map) => map.id === a.id) - MAPS.findIndex((map) => map.id === b.id));
  await writeFile(summary, `${JSON.stringify({ capturedAt: new Date().toISOString(), maps: merged }, null, 2)}\n`);
  process.stdout.write(`\nwrote ${path.relative(REPO, summary)} (${merged.length} maps)\n`);
}

await main();
