import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { PNG } from 'pngjs';

const dirs = ['down', 'left', 'right', 'up'];
const magenta = [255, 0, 255, 255];
const root = process.argv[2];
const slug = process.argv[3];
const turnaround = process.argv[4];
const descriptor = process.argv[5];
const asymmetry = process.argv[6];
const gait = process.argv[7];
if (!root || !slug || !turnaround || !descriptor || !asymmetry || !gait) {
  throw new Error('usage: node run-bandit.mjs <root> <slug> <turnaround> <descriptor> <asymmetry> <gait>');
}

const cellW = slug === 'bandit-wrecker' ? 425 : 280;
const cellH = slug === 'bandit-wrecker' ? 425 : 340;
const sheetW = cellW * 8;
const sheetH = cellH * 4;
const ffmpeg = fs.existsSync('/tmp/gr-imageio-ffmpeg/ffmpeg') ? '/tmp/gr-imageio-ffmpeg/ffmpeg' : 'ffmpeg';
const evidence = path.join('assets/motion-pilot', root);
const logs = path.join(evidence, 'logs');
const stills = path.join(evidence, 'stills');
const videos = path.join(evidence, 'videos');
const contacts = path.join(evidence, 'contact-sheets');
for (const d of [evidence, logs, stills, videos, contacts]) fs.mkdirSync(d, { recursive: true });

function run(cmd, args, opts = {}) {
  const res = spawnSync(cmd, args, { encoding: 'utf8', ...opts });
  if (res.status !== 0) throw new Error(`${cmd} ${args.join(' ')}\n${res.stderr || res.stdout}`);
  return res.stdout.trim();
}

function runJson(cmd, args, outFile) {
  const txt = run(cmd, ['--json', ...args]);
  fs.writeFileSync(outFile, txt + '\n');
  return JSON.parse(txt);
}

function jobId(data) {
  if (typeof data === 'string') return data;
  if (Array.isArray(data)) return data[0];
  return data.id;
}

async function download(url, file) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`download failed ${res.status}: ${url}`);
  fs.writeFileSync(file, Buffer.from(await res.arrayBuffer()));
}

function directionPrompt(dir) {
  const view = {
    down: 'DOWN/front view, facing the viewer',
    left: 'LEFT profile view, facing screen-left',
    right: 'RIGHT profile view, facing screen-right',
    up: 'UP/back view, facing away from the viewer',
  }[dir];
  return `Frontier Ledger illustrated game sprite reference. Use the exact referenced ${descriptor}. ${asymmetry}. ${view}. Full body mid-stride walk pose, centered single figure, full body visible head to boots, plain flat sand-colored background, fixed ground line, readable silhouette. Keep the same clothing, colors, linework, proportions, and side-specific details as the reference turnaround. No mirroring, no letters, no numbers, no text, no logo, no watermark, no extra characters, no realistic firearms, no gore.`;
}

function videoPrompt(dir) {
  const view = {
    down: 'DOWN/front view; keep front-facing, do not turn',
    left: 'LEFT profile view; keep facing screen-left, do not turn',
    right: 'RIGHT profile view; keep facing screen-right, do not turn',
    up: 'UP/back view; keep back-facing, do not turn',
  }[dir];
  return `Frontier Ledger illustrated game sprite reference. Use the exact referenced ${descriptor}. ${asymmetry}. ${view}. Full body walking steadily in place against a plain flat sand-colored background. ${gait}. Constant centered framing, locked footline and fixed scale, feet on a fixed ground line, no vertical drift, no camera motion, no zoom, no turn, no mirroring, no extra characters, no text or letters, no realistic firearms, no gore. Seamless 4-second loop with one clean readable gait cycle; keep proportions, silhouette, clothing, colors, linework, and pinned side details consistent frame to frame.`;
}

function writePng(file, png) {
  fs.writeFileSync(file, PNG.sync.write(png));
}

function readPng(file) {
  return PNG.sync.read(fs.readFileSync(file));
}

function pixel(img, x, y) {
  const i = (y * img.width + x) * 4;
  return [img.data[i], img.data[i + 1], img.data[i + 2]];
}

function bgMask(img) {
  const corners = [pixel(img, 2, 2), pixel(img, img.width - 3, 2), pixel(img, 2, img.height - 3), pixel(img, img.width - 3, img.height - 3)];
  const bg = corners.reduce((a, p) => [a[0] + p[0], a[1] + p[1], a[2] + p[2]], [0, 0, 0]).map((v) => v / 4);
  const mask = new Uint8Array(img.width * img.height);
  const q = [];
  const isBg = (x, y) => {
    const p = pixel(img, x, y);
    const dr = p[0] - bg[0], dg = p[1] - bg[1], db = p[2] - bg[2];
    const dist = Math.sqrt(dr * dr + dg * dg + db * db);
    const lum = 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2];
    const max = Math.max(...p), min = Math.min(...p);
    const sat = max ? (max - min) / max : 0;
    return dist < 95 || (lum > 118 && sat < 0.34) || (y > img.height * 0.65 && lum > 70 && sat < 0.28);
  };
  const push = (x, y) => {
    if (x < 0 || y < 0 || x >= img.width || y >= img.height) return;
    const i = y * img.width + x;
    if (mask[i] || !isBg(x, y)) return;
    mask[i] = 1;
    q.push([x, y]);
  };
  for (let x = 0; x < img.width; x++) { push(x, 0); push(x, img.height - 1); }
  for (let y = 0; y < img.height; y++) { push(0, y); push(img.width - 1, y); }
  for (let h = 0; h < q.length; h++) {
    const [x, y] = q[h];
    push(x + 1, y); push(x - 1, y); push(x, y + 1); push(x, y - 1);
  }
  return mask;
}

function bbox(img, mask) {
  let x0 = img.width, y0 = img.height, x1 = -1, y1 = -1;
  for (let y = 0; y < img.height; y++) for (let x = 0; x < img.width; x++) {
    if (mask[y * img.width + x]) continue;
    x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y);
  }
  return { x0, y0, x1, y1, w: x1 - x0 + 1, h: y1 - y0 + 1 };
}

function compositeFrame(srcFile, dest, cellX, cellY) {
  const img = readPng(srcFile);
  const mask = bgMask(img);
  const b = bbox(img, mask);
  const maxW = cellW * 0.8;
  const maxH = cellH * (slug === 'bandit-wrecker' ? 0.93 : 0.86);
  const scale = Math.min(maxW / b.w, maxH / b.h);
  const outW = Math.max(1, Math.round(b.w * scale));
  const outH = Math.max(1, Math.round(b.h * scale));
  const tmpRaw = srcFile + '.rgba';
  const tmpPng = srcFile + '.scaled.png';
  const crop = `${b.w}:${b.h}:${b.x0}:${b.y0}`;
  run(ffmpeg, ['-y', '-i', srcFile, '-vf', `crop=${crop},scale=${outW}:${outH}:flags=lanczos`, tmpPng], { stdio: 'pipe' });
  const scaled = readPng(tmpPng);
  fs.rmSync(tmpRaw, { force: true });
  fs.rmSync(tmpPng, { force: true });
  const dx0 = cellX + Math.round((cellW - outW) / 2);
  const dy0 = cellY + cellH - outH - 5;
  for (let y = 0; y < outH; y++) for (let x = 0; x < outW; x++) {
    const si = (y * outW + x) * 4;
    const p = [scaled.data[si], scaled.data[si + 1], scaled.data[si + 2]];
    const max = Math.max(...p), min = Math.min(...p);
    const sat = max ? (max - min) / max : 0;
    const lum = 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2];
    if ((lum > 118 && sat < 0.34) || (p[0] > 225 && p[1] > 205 && p[2] > 160)) continue;
    const di = ((dy0 + y) * dest.width + (dx0 + x)) * 4;
    dest.data[di] = p[0]; dest.data[di + 1] = p[1]; dest.data[di + 2] = p[2]; dest.data[di + 3] = 255;
  }
  return { bbox: b, scale, outW, outH };
}

function makeContact(files, outFile) {
  run(ffmpeg, ['-y', ...files.flatMap((f) => ['-i', f]), '-filter_complex', `hstack=inputs=${files.length}`, outFile], { stdio: 'pipe' });
}

async function main() {
  const statusPre = run('higgsfield', ['account', 'status', '--json']);
  fs.writeFileSync(path.join(logs, 'higgsfield-account-status-before-stills.txt'), statusPre + '\n');
  const stillJobs = [];
  for (const dir of dirs) {
    const createFile = path.join(logs, `${slug}-start-${dir}-take1-create.json`);
    const create = fs.existsSync(createFile)
      ? JSON.parse(fs.readFileSync(createFile, 'utf8'))
      : runJson('higgsfield', ['generate', 'create', 'gpt_image_2', '--prompt', directionPrompt(dir), '--image-references', turnaround, '--quality', 'high', '--resolution', '2k', '--aspect-ratio', '1:1'], createFile);
    stillJobs.push({ dir, id: jobId(create) });
  }
  for (const job of stillJobs) {
    const data = runJson('higgsfield', ['generate', 'wait', job.id, '--quiet', '--timeout', '20m'], path.join(logs, `${slug}-start-${job.dir}-take1-generate.json`));
    const out = path.join(stills, `${slug}-start-${job.dir}-take1.png`);
    await download(data.result_url, out);
    job.output = out;
  }
  fs.writeFileSync(path.join(logs, 'still-jobs.json'), JSON.stringify(stillJobs, null, 2) + '\n');
  fs.writeFileSync(path.join(logs, 'higgsfield-account-status-after-stills.txt'), run('higgsfield', ['account', 'status', '--json']) + '\n');

  const videoJobs = [];
  for (const dir of dirs) {
    for (let take = 1; take <= 3; take++) {
      const createFile = path.join(logs, `${slug}-start-${dir}-video-take${take}-create.json`);
      const create = fs.existsSync(createFile)
        ? JSON.parse(fs.readFileSync(createFile, 'utf8'))
        : runJson('higgsfield', ['generate', 'create', 'seedance_2_0', '--prompt', videoPrompt(dir), '--start-image', path.join(stills, `${slug}-start-${dir}-take1.png`), '--image-references', turnaround, '--duration', '4', '--resolution', '720p', '--aspect-ratio', '1:1', '--mode', 'std', '--generate-audio', 'false'], createFile);
      videoJobs.push({ dir, take, id: jobId(create) });
    }
  }
  fs.writeFileSync(path.join(logs, 'video-jobs-created.json'), JSON.stringify(videoJobs, null, 2) + '\n');
  for (const job of videoJobs) {
    const data = runJson('higgsfield', ['generate', 'wait', job.id, '--quiet', '--timeout', '25m', '--interval', '5s'], path.join(logs, `${slug}-start-${job.dir}-video-take${job.take}-generate.json`));
    const out = path.join(videos, `${slug}-start-${job.dir}-take${job.take}.mp4`);
    await download(data.result_url, out);
    job.output = out;
  }
  fs.writeFileSync(path.join(logs, 'higgsfield-account-status-after-videos.txt'), run('higgsfield', ['account', 'status', '--json']) + '\n');
}

await main();
