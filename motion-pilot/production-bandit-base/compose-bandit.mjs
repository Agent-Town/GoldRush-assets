import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { PNG } from 'pngjs';

const dirs = ['down', 'left', 'right', 'up'];
const root = process.argv[2];
const slug = process.argv[3];
const selectedArg = process.argv[4] || 'down=1,left=1,right=1,up=1';
if (!root || !slug) throw new Error('usage: node compose-bandit.mjs <root> <slug> down=1,left=2,right=3,up=1');

const selected = Object.fromEntries(selectedArg.split(',').map((pair) => {
  const [dir, take] = pair.split('=');
  if (!dirs.includes(dir)) throw new Error(`bad dir ${dir}`);
  return [dir, Number(take)];
}));
const cellW = slug === 'bandit-wrecker' ? 425 : 280;
const cellH = slug === 'bandit-wrecker' ? 425 : 340;
const ffmpeg = fs.existsSync('/tmp/gr-imageio-ffmpeg/ffmpeg') ? '/tmp/gr-imageio-ffmpeg/ffmpeg' : 'ffmpeg';
const evidence = path.join('assets/motion-pilot', root);
const framesDir = path.join(evidence, 'frames');
const contacts = path.join(evidence, 'contact-sheets');
const logs = path.join(evidence, 'logs');
fs.mkdirSync(framesDir, { recursive: true });
fs.mkdirSync(contacts, { recursive: true });
fs.mkdirSync(logs, { recursive: true });

function run(cmd, args) {
  const res = spawnSync(cmd, args, { encoding: 'utf8' });
  if (res.status !== 0) throw new Error(`${cmd} ${args.join(' ')}\n${res.stderr || res.stdout}`);
  return res.stdout.trim();
}
function readPng(file) { return PNG.sync.read(fs.readFileSync(file)); }
function writePng(file, png) { fs.writeFileSync(file, PNG.sync.write(png)); }
function pix(img, x, y) {
  const i = (y * img.width + x) * 4;
  return [img.data[i], img.data[i + 1], img.data[i + 2]];
}
function maskFor(img) {
  const corners = [pix(img, 2, 2), pix(img, img.width - 3, 2), pix(img, 2, img.height - 3), pix(img, img.width - 3, img.height - 3)];
  const bg = corners.reduce((a, p) => [a[0] + p[0], a[1] + p[1], a[2] + p[2]], [0, 0, 0]).map((v) => v / 4);
  const mask = new Uint8Array(img.width * img.height);
  const q = [];
  const isBg = (x, y) => {
    const p = pix(img, x, y);
    const d = Math.hypot(p[0] - bg[0], p[1] - bg[1], p[2] - bg[2]);
    const max = Math.max(...p), min = Math.min(...p);
    const sat = max ? (max - min) / max : 0;
    const lum = 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2];
    return d < 95 || (lum > 120 && sat < 0.36) || (y > img.height * 0.68 && lum > 64 && sat < 0.3);
  };
  const push = (x, y) => {
    if (x < 0 || y < 0 || x >= img.width || y >= img.height) return;
    const i = y * img.width + x;
    if (mask[i] || !isBg(x, y)) return;
    mask[i] = 1; q.push([x, y]);
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

function extract(video, pattern) {
  fs.rmSync(path.dirname(pattern), { recursive: true, force: true });
  fs.mkdirSync(path.dirname(pattern), { recursive: true });
  run(ffmpeg, ['-y', '-i', video, '-vf', 'fps=2,scale=720:720', '-frames:v', '8', pattern]);
}

function paste(srcFile, sheet, col, row) {
  const img = readPng(srcFile);
  const mask = maskFor(img);
  const b = bbox(img, mask);
  const scale = Math.min((cellW * 0.8) / b.w, (cellH * (slug === 'bandit-wrecker' ? 0.92 : 0.86)) / b.h);
  const sw = Math.max(1, Math.round(b.w * scale));
  const sh = Math.max(1, Math.round(b.h * scale));
  const tmp = `${srcFile}.scaled.png`;
  run(ffmpeg, ['-y', '-i', srcFile, '-vf', `crop=${b.w}:${b.h}:${b.x0}:${b.y0},scale=${sw}:${sh}:flags=lanczos`, tmp]);
  const scaled = readPng(tmp);
  fs.rmSync(tmp, { force: true });
  const dx0 = col * cellW + Math.round((cellW - sw) / 2);
  const dy0 = row * cellH + cellH - sh - 5;
  for (let y = 0; y < sh; y++) for (let x = 0; x < sw; x++) {
    const si = (y * sw + x) * 4;
    const p = [scaled.data[si], scaled.data[si + 1], scaled.data[si + 2]];
    const max = Math.max(...p), min = Math.min(...p);
    const sat = max ? (max - min) / max : 0;
    const lum = 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2];
    if ((lum > 122 && sat < 0.35) || (p[0] > 225 && p[1] > 205 && p[2] > 160)) continue;
    const di = ((dy0 + y) * sheet.width + (dx0 + x)) * 4;
    sheet.data[di] = p[0]; sheet.data[di + 1] = p[1]; sheet.data[di + 2] = p[2]; sheet.data[di + 3] = 255;
  }
  return { h: b.h, scale, outH: sh };
}

function contact(files, out) {
  run(ffmpeg, ['-y', ...files.flatMap((f) => ['-i', f]), '-filter_complex', `hstack=inputs=${files.length}`, out]);
}

const sheet = new PNG({ width: cellW * 8, height: cellH * 4 });
for (let i = 0; i < sheet.data.length; i += 4) {
  sheet.data[i] = 255; sheet.data[i + 1] = 0; sheet.data[i + 2] = 255; sheet.data[i + 3] = 255;
}
const metrics = {};
for (const [row, dir] of dirs.entries()) {
  const take = selected[dir] || 1;
  const video = path.join(evidence, 'videos', `${slug}-start-${dir}-take${take}.mp4`);
  const dirFrames = path.join(framesDir, `${dir}-take${take}`);
  extract(video, path.join(dirFrames, 'frame-%02d.png'));
  const files = Array.from({ length: 8 }, (_, i) => path.join(dirFrames, `frame-${String(i + 1).padStart(2, '0')}.png`));
  contact(files, path.join(contacts, `${slug}-start-${dir}-take${take}-contact.png`));
  metrics[dir] = [];
  for (const [col, file] of files.entries()) metrics[dir].push(paste(file, sheet, col, row));
}
const out = path.join(evidence, `char-${slug.replace('bandit-', 'bandit-')}-sheet-walk8.png`);
writePng(out, sheet);
fs.copyFileSync(out, path.join('assets/raw', `char-${slug}-sheet-walk8.png`));
fs.writeFileSync(path.join(logs, `${slug}-walk8-summary.json`), JSON.stringify({ selected, cellW, cellH, sheet: { width: sheet.width, height: sheet.height }, metrics }, null, 2) + '\n');
