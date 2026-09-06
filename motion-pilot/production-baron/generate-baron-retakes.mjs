import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { PNG } from 'pngjs';

const root = 'assets/motion-pilot/production-baron';
const dirs = ['down', 'left', 'right', 'up'];
const takes = [2, 3];

const prompts = {
  down: 'Frontier Ledger illustrated game sprite reference. Use the exact referenced Baron: an enormous warm stage-outlaw boss, oxblood greatcoat, brass buttons, gold waistcoat, tall black hat, curled waxed mustache, broad heavy build, warm never grim. The playing card is tucked into the LEFT side of his hatband; in this DOWN/front view the card stays on his left hatband side and never swaps sides. Full body DOWN/front view, walking steadily in place against a plain flat sand-colored background. Constant centered framing, locked footline and fixed scale, feet on a fixed ground line, no vertical drift, no camera motion, no zoom, no turn, no extra characters, no text or letters, no realistic firearms, no gore. Seamless 4-second loop with one clean readable gait cycle; keep proportions, silhouette, clothing, colors, linework, coat mass, mustache, and hat-card side consistent frame to frame.',
  left: 'Frontier Ledger illustrated game sprite reference. Use the exact referenced Baron: an enormous warm stage-outlaw boss, oxblood greatcoat, brass buttons, gold waistcoat, tall black hat, curled waxed mustache, broad heavy build, warm never grim. The playing card is tucked into the LEFT side of his hatband; in this LEFT profile view the card is visible on the left side of the hatband and never swaps to the other side. Full body LEFT profile view, facing screen-left, walking steadily in place against a plain flat sand-colored background. Constant centered framing, locked footline and fixed scale, feet on a fixed ground line, no vertical drift, no camera motion, no zoom, no turn, no extra characters, no text or letters, no realistic firearms, no gore. Seamless 4-second loop with one clean readable gait cycle; keep proportions, silhouette, clothing, colors, linework, coat mass, mustache, and hat-card side consistent frame to frame.',
  right: 'Frontier Ledger illustrated game sprite reference. Use the exact referenced Baron: an enormous warm stage-outlaw boss, oxblood greatcoat, brass buttons, gold waistcoat, tall black hat, curled waxed mustache, broad heavy build, warm never grim. The playing card is tucked in the LEFT side of his hatband, so in this RIGHT profile view the card faces away from the camera and is NOT visible. Do not show a playing card, paper, badge, letter, or white rectangle on the near side of the hat. Full body RIGHT profile view, facing screen-right, walking steadily in place against a plain flat sand-colored background. Constant centered framing, locked footline and fixed scale, feet on a fixed ground line, no vertical drift, no camera motion, no zoom, no turn, no extra characters, no text or letters, no realistic firearms, no gore. Seamless 4-second loop with one clean readable gait cycle; keep proportions, silhouette, clothing, colors, linework, coat mass, mustache, and hidden hat-card side consistent frame to frame.',
  up: 'Frontier Ledger illustrated game sprite reference. Use the exact referenced Baron: an enormous warm stage-outlaw boss, oxblood greatcoat, brass buttons, gold waistcoat, tall black hat, curled waxed mustache, broad heavy build, warm never grim. The playing card is tucked into the LEFT side of his hatband; in this UP/back view it is hidden or edge-on and must not swap to the other side. Full body UP/back view, walking steadily away from camera against a plain flat sand-colored background. True back view, no face visible and no turn toward camera. Constant centered framing, locked footline and fixed scale, feet on a fixed ground line, no vertical drift, no camera motion, no zoom, no turn, no extra characters, no text or letters, no realistic firearms, no gore. Seamless 4-second loop with one clean readable gait cycle; keep proportions, silhouette, clothing, colors, linework, coat mass, mustache, and hat-card side consistent frame to frame.',
};

const startImages = {
  down: 'assets/processed-full/char-baron-sheet-walk4-a-r0c0.png',
  left: 'assets/processed-full/char-baron-sheet-walk4-a-r1c0.png',
  right: `${root}/references/baron-right-turnaround-start.png`,
  up: 'assets/processed-full/char-baron-sheet-walk4-a-r3c0.png',
};

function run(cmd, args, options = {}) {
  const result = spawnSync(cmd, args, { encoding: 'utf8', ...options });
  if (result.status !== 0) {
    process.stderr.write(result.stdout ?? '');
    process.stderr.write(result.stderr ?? '');
    process.exit(result.status ?? 1);
  }
  return result.stdout;
}

function runMaybe(cmd, args, options = {}) {
  return spawnSync(cmd, args, { encoding: 'utf8', ...options });
}

function write(file, text) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, text);
}

function makeRightStartCrop() {
  const outFile = startImages.right;
  if (fs.existsSync(outFile)) return;
  const src = PNG.sync.read(fs.readFileSync('assets/raw/turn-baron-coat.png'));
  const crop = { x: 0, y: 70, w: 360, h: 780 };
  const out = new PNG({ width: crop.w, height: crop.h });
  for (let y = 0; y < crop.h; y += 1) {
    for (let x = 0; x < crop.w; x += 1) {
      const sx = Math.min(src.width - 1, crop.x + x);
      const sy = Math.min(src.height - 1, crop.y + y);
      const si = (sy * src.width + sx) * 4;
      const di = (y * crop.w + x) * 4;
      out.data[di] = src.data[si];
      out.data[di + 1] = src.data[si + 1];
      out.data[di + 2] = src.data[si + 2];
      out.data[di + 3] = 255;
    }
  }
  fs.mkdirSync(path.dirname(outFile), { recursive: true });
  fs.writeFileSync(outFile, PNG.sync.write(out));
}

makeRightStartCrop();
fs.mkdirSync(`${root}/logs`, { recursive: true });
fs.mkdirSync(`${root}/videos`, { recursive: true });

write(`${root}/logs/higgsfield-account-status-pre.txt`, run('higgsfield', ['account', 'status']));

const created = [];
for (const dir of dirs) {
  for (const take of takes) {
    const logFile = `${root}/logs/baron-${dir}-take${take}-create.json`;
    let job;
    if (fs.existsSync(logFile)) {
      job = JSON.parse(fs.readFileSync(logFile, 'utf8'));
    } else {
      const stdout = run('higgsfield', [
        'generate',
        'create',
        'seedance_2_0',
        '--prompt',
        prompts[dir],
        '--start-image',
        startImages[dir],
        '--image',
        'assets/raw/kit-the-baron.png',
        '--image',
        'assets/raw/turn-baron-coat.png',
        '--aspect-ratio',
        '1:1',
        '--duration',
        '4',
        '--resolution',
        '720p',
        '--mode',
        'std',
        '--generate-audio',
        'false',
        '--json',
      ]);
      write(logFile, stdout);
      job = JSON.parse(stdout);
    }
    const id = Array.isArray(job) ? job[0] : job.id;
    created.push({ dir, take, id });
  }
}

write(`${root}/logs/baron-retake-jobs.json`, `${JSON.stringify(created, null, 2)}\n`);

for (const { dir, take, id } of created) {
  const waitFile = `${root}/logs/baron-${dir}-take${take}-generate.json`;
  const video = `${root}/videos/baron-${dir}-take${take}.mp4`;
  let job;
  if (fs.existsSync(waitFile)) {
    job = JSON.parse(fs.readFileSync(waitFile, 'utf8'));
  } else {
    for (let attempt = 0; attempt < 90; attempt += 1) {
      const result = runMaybe('higgsfield', ['generate', 'get', id, '--json']);
      if (result.status === 0) {
        job = JSON.parse(result.stdout);
        const status = Array.isArray(job) ? job[0]?.status : job.status;
        if (status === 'completed') {
          write(waitFile, result.stdout);
          break;
        }
        if (status === 'failed' || status === 'canceled') {
          write(waitFile, result.stdout);
          throw new Error(`${dir} take${take} ${id} ended with status ${status}`);
        }
      }
      spawnSync('sleep', ['10']);
    }
    if (!job) throw new Error(`${dir} take${take} ${id} did not return a job status`);
  }
  const result = Array.isArray(job) ? job[0] : job;
  if (result.status !== 'completed') throw new Error(`${dir} take${take} ${id} still ${result.status}`);
  if (!result.result_url) throw new Error(`No result_url for ${dir} take${take}`);
  if (!fs.existsSync(video)) {
    run('curl', ['-L', '--fail', '--silent', '--show-error', result.result_url, '-o', video], { stdio: 'inherit' });
  }
}

write(`${root}/logs/higgsfield-account-status-post.txt`, run('higgsfield', ['account', 'status']));
write(`${root}/logs/higgsfield-transactions-post.json`, run('higgsfield', ['account', 'transactions', '--size', '100', '--json']));

console.log(JSON.stringify(created, null, 2));
