// Mount every late-era terrain through the REAL runtime pilot, bypassing the
// contract door.
//
// Twelve of the twenty maps carry `harvestAnchors: []`, so the door refuses them
// and the game opens The Claim instead (F-MRL-2). That makes the live boot useless
// for proving whether their sculpt now mounts. `installTerrain3dClaimPilot()` can
// be called directly — this is the technique `e2e/terrain3d-registry.spec.ts:95`
// uses — which exercises the same loader, the same validTerrain, and the same
// bakeHeightGrid without needing the map to be claimable.
//
// Usage: node .../pilot-probe.mjs

import { spawn } from 'node:child_process';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { MAPS } from './capture.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, '../../../..');
const PORT = Number(process.env.GR_RECONCILE_PORT ?? 5242);
const BASE = `http://127.0.0.1:${PORT}`;

async function waitForServer(url, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(url, { signal: AbortSignal.timeout(2_000) })).ok) return;
    } catch { /* not up yet */ }
    await new Promise((resolve) => setTimeout(resolve, 400));
  }
  throw new Error(`dev server did not answer ${url}`);
}

async function main() {
  const server = spawn('npx', ['vite', '--host', '127.0.0.1', '--port', String(PORT), '--strictPort'],
    { cwd: REPO, stdio: ['ignore', 'ignore', 'pipe'] });
  server.stderr.on('data', (chunk) => process.stderr.write(`[vite] ${chunk}`));
  const rows = [];
  try {
    await waitForServer(BASE, 60_000);
    const browser = await chromium.launch({ channel: 'chromium' });
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    await page.goto(`${BASE}/?debug&nowaves&nolevel&tier=full`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => Boolean(window.__GR_TEST__), undefined, { timeout: 30_000 });

    for (const map of MAPS) {
      if (!map.sculpt) { rows.push({ id: map.id, skipped: 'no sculpt — painted by design' }); continue; }
      const contract = JSON.parse(await readFile(
        path.join(HERE, '..', `${map.sculpt}-terrain-contract.json`), 'utf8'));
      const dataset = await page.evaluate(async ({ contractId, tileId }) => {
        const THREE = await Function('return import("/@id/three")')();
        const pilot = await Function('return import("/src/world/Terrain3dClaimPilot.ts")')();
        const scene = new THREE.Scene();
        const canvas = document.createElement('canvas');
        const dispose = pilot.installTerrain3dClaimPilot({ scene, canvas, contractId, tileId });
        await new Promise((resolve, reject) => {
          const deadline = performance.now() + 20_000;
          const check = () => {
            if (canvas.dataset.terrain3dPilotState !== 'loading') resolve();
            else if (performance.now() >= deadline) reject(new Error('timeout'));
            else requestAnimationFrame(check);
          };
          check();
        });
        const result = { ...canvas.dataset };
        dispose();
        return result;
      }, { contractId: map.id, tileId: contract.tileId }).catch((error) => ({ error: String(error).split('\n')[0] }));
      rows.push({ id: map.id, sculpt: map.sculpt, ...dataset });
      const ok = dataset.terrain3dPilotState === 'ready' && dataset.terrain3dPilotRenderSource === 'glb';
      process.stdout.write(`${ok ? 'MOUNTS ' : 'FAILS  '} ${map.id.padEnd(20)} `
        + `state=${String(dataset.terrain3dPilotState).padEnd(7)} src=${String(dataset.terrain3dPilotRenderSource).padEnd(7)} `
        + `pano=${String(dataset.terrain3dPilotPanorama ?? '-').padEnd(24)} failure=${dataset.terrain3dPilotFailure ?? '-'}\n`);
    }
    await browser.close();
  } finally {
    server.kill('SIGTERM');
  }
  await writeFile(path.join(HERE, 'pilot-probe.json'),
    `${JSON.stringify({ probedAt: new Date().toISOString(), maps: rows }, null, 2)}\n`);
}

await main();
