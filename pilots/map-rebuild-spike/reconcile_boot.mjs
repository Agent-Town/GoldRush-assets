/**
 * THE MAP RECONCILIATION (early half) — boot each map at the REAL gameplay camera.
 *
 * The fresh-eye arc judged sculpts from Blender at a synthetic run camera. That
 * proved composition but not DELIVERY: the player never sees Blender. This driver
 * boots the shipped game on a scratch port and screenshots the living map through
 * the same door the census walks (`?debug&era=N&contract=ID`), so the verdict is
 * held against what actually renders — fog, water, panorama, landmarks, tone map
 * and all.
 *
 * Standalone on purpose (no playwright test runner): one browser, one vite, N maps,
 * sequential, so a single map's failure never costs the sweep.
 *
 * Usage:
 *   node assets/pilots/map-rebuild-spike/reconcile_boot.mjs [--maps a,b,c] [--mobile] [--port 5261]
 */

import { spawn } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const ROOT = path.resolve(import.meta.dirname, '../../..');

/** era + door id, in campaign order. The early half of the reconciliation claim. */
export const EARLY_MAPS = [
  { id: 'the-claim', era: 1 },
  { id: 'e1-dry-gulch', era: 1 },
  { id: 'e1-night-shift', era: 1 },
  { id: 'e1-twin-banks', era: 1 },
  { id: 'e1-baron', era: 1 },
  { id: 'e2-hill-mine', era: 2 },
  { id: 'e2-trestle', era: 2 },
  { id: 'e2-pressure-garden', era: 2 },
  { id: 'e2-incline', era: 2 },
  { id: 'e3-blackout-ridge', era: 3 },
  { id: 'e3-moth-season', era: 3 },
  { id: 'e3-canyon-works', era: 3 },
  { id: 'e3-fairground', era: 3 },
  { id: 'e4-dust-flats', era: 4 },
  { id: 'e4-long-road', era: 4 },
  { id: 'e4-gusher-county', era: 4 },
  { id: 'e4-boneyard', era: 4 },
  { id: 'e5-deepwater-claim', era: 5 },
  { id: 'e5-regatta', era: 5 },
  { id: 'e5-stillwater', era: 5 },
  { id: 'e5-flotilla', era: 5 },
];

const args = process.argv.slice(2);
const flag = (name, fallback) => {
  const index = args.indexOf(`--${name}`);
  return index === -1 ? fallback : args[index + 1];
};
const PORT = Number(flag('port', '5261'));
const OUT_DIR = path.join(ROOT, flag('out', 'artifacts/map-reconcile-early'));
const MOBILE = args.includes('--mobile');
const only = flag('maps', null);
const MAPS = only ? EARLY_MAPS.filter((map) => only.split(',').includes(map.id)) : EARLY_MAPS;

const BASE = `http://127.0.0.1:${PORT}`;

async function startVite() {
  // Direct bin + its own process group: `npx vite` leaves the real vite as a
  // grandchild, so killing npx orphans the server AND holds this process alive on
  // an open pipe. Own group + kill(-pid) ends the whole tree.
  const child = spawn(path.join(ROOT, 'node_modules/.bin/vite'), ['--host', '127.0.0.1', '--port', String(PORT), '--strictPort'], {
    cwd: ROOT,
    stdio: ['ignore', 'pipe', 'pipe'],
    detached: true,
  });
  child.stderr.on('data', (chunk) => process.stderr.write(`[vite] ${chunk}`));
  const deadline = Date.now() + 40_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(BASE, { signal: AbortSignal.timeout(2_000) });
      if (response.ok) return child;
    } catch { /* not up yet */ }
    await new Promise((resolve) => setTimeout(resolve, 400));
  }
  killTree(child);
  throw new Error(`vite did not come up on ${PORT}`);
}

function killTree(child) {
  try { process.kill(-child.pid, 'SIGKILL'); } catch { child.kill('SIGKILL'); }
}

/** Boot one door and hold the frame. Returns the diagnostics row + shot paths. */
async function shoot(context, map, tag) {
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push(message.text()); });
  page.on('pageerror', (error) => pageErrors.push(error.message));
  const row = { id: map.id, era: map.era, tag, boot: 'FAIL: not run', shot: null };
  const started = Date.now();
  try {
    const query = `?debug&era=${map.era}&contract=${map.id}&nowaves&nolevel&nokill&nopause&tier=full&seed=reconcile-${map.id}`;
    await page.goto(`${BASE}/${query}`, { waitUntil: 'commit' });
    await page.waitForFunction(
      () => Boolean(window.__GR_TEST__) && (window.__THREE_GAME_DIAGNOSTICS__?.frame ?? 0) > 10,
      undefined,
      { timeout: 45_000 },
    );
    const dismiss = page.getByTestId('contract-briefing-dismiss');
    if (await dismiss.isVisible().catch(() => false)) await dismiss.click();
    await page.waitForFunction(
      () => document.querySelector('#game-canvas')?.dataset.terrain3dPilotState !== 'loading',
      undefined,
      { timeout: 45_000 },
    );
    // Let the sim settle so water, dust and the panorama haze are at their normal
    // running state rather than their first-frame state.
    await page.waitForTimeout(1_200);
    const active = await page.evaluate(() => window.__GR_TEST__.activeContract().id);
    row.door = active;
    row.doorTruth = active === map.id ? 'PASS' : `FAIL: door opened ${active}`;
    const canvas = page.locator('#game-canvas');
    row.renderSource = await canvas.getAttribute('data-terrain3d-pilot-render-source');
    row.panoramaFraming = await canvas.getAttribute('data-terrain3d-pilot-panorama-framing');
    row.continuation = await canvas.getAttribute('data-terrain3d-pilot-continuation');
    row.diagnostics = await page.evaluate(() => {
      const diagnostics = window.__THREE_GAME_DIAGNOSTICS__ ?? {};
      return { frame: diagnostics.frame ?? null, camera: diagnostics.camera ?? null };
    });
    const shot = path.join(OUT_DIR, `${map.id}-${tag}.png`);
    // Canvas-only: the HUD is another owner's surface and would only mask the map.
    await canvas.screenshot({ path: shot });
    row.shot = path.relative(ROOT, shot);
    row.boot = 'PASS';
  } catch (error) {
    row.boot = `FAIL: ${(error instanceof Error ? error.message : String(error)).split('\n')[0].slice(0, 200)}`;
  } finally {
    row.consoleErrors = consoleErrors.slice(0, 6);
    row.pageErrors = pageErrors.slice(0, 6);
    row.seconds = Number(((Date.now() - started) / 1_000).toFixed(1));
    await page.close();
  }
  return row;
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });
  const vite = await startVite();
  const browser = await chromium.launch({ channel: 'chromium' });
  const rows = [];
  try {
    const desktop = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1 });
    for (const map of MAPS) {
      const row = await shoot(desktop, map, 'desktop');
      rows.push(row);
      console.log(`${row.boot === 'PASS' ? 'ok  ' : 'FAIL'} ${map.id.padEnd(20)} ${row.seconds}s  source=${row.renderSource ?? '-'} door=${row.door ?? '-'} console=${row.consoleErrors.length}`);
    }
    await desktop.close();
    if (MOBILE) {
      const mobile = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true });
      for (const map of MAPS) {
        const row = await shoot(mobile, map, 'mobile');
        rows.push(row);
        console.log(`${row.boot === 'PASS' ? 'ok  ' : 'FAIL'} ${map.id.padEnd(20)} [390px] ${row.seconds}s`);
      }
      await mobile.close();
    }
  } finally {
    await browser.close();
    killTree(vite);
  }
  await writeFile(path.join(OUT_DIR, 'boot-rows.json'), `${JSON.stringify(rows, null, 2)}\n`);
  const failures = rows.filter((row) => row.boot !== 'PASS' || row.doorTruth !== 'PASS' || row.consoleErrors.length || row.pageErrors.length);
  console.log(`\n${rows.length} shots, ${failures.length} with a boot/door/console finding -> ${path.relative(ROOT, OUT_DIR)}/boot-rows.json`);
}

// Entry-guarded: reconcile_boards.mjs imports EARLY_MAPS from here, and an
// unguarded top-level main() made that import boot a whole second sweep.
if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(import.meta.filename)) {
  await main();
  process.exit(0);
}
