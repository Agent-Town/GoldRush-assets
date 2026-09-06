import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { PNG } from 'pngjs';

const dirs = ['down', 'left', 'right', 'up'];
const root = 'assets/motion-pilot/production-hero-v3';
const cellW = 280;
const cellH = 340;
const magenta = [255, 0, 255, 255];
const ffmpeg = '/tmp/gr-imageio-ffmpeg/ffmpeg';
const bottomMargin = 12;

function readPng(file) {
  return PNG.sync.read(fs.readFileSync(file));
}

function writePng(file, png) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, PNG.sync.write(png));
}

function dist(a, b) {
  const dr = a[0] - b[0];
  const dg = a[1] - b[1];
  const db = a[2] - b[2];
  return Math.sqrt(dr * dr + dg * dg + db * db);
}

function pixelAt(img, x, y) {
  const idx = (y * img.width + x) * 4;
  return [img.data[idx], img.data[idx + 1], img.data[idx + 2]];
}

function backgroundMask(img) {
  const samples = [
    pixelAt(img, 4, 4),
    pixelAt(img, img.width - 5, 4),
    pixelAt(img, 4, img.height - 5),
    pixelAt(img, img.width - 5, img.height - 5),
  ];
  const bg = samples.reduce((acc, p) => [acc[0] + p[0], acc[1] + p[1], acc[2] + p[2]], [0, 0, 0]).map((v) => v / samples.length);
  const mask = new Uint8Array(img.width * img.height);
  const queue = [];
  const push = (x, y) => {
    if (x < 0 || y < 0 || x >= img.width || y >= img.height) return;
    const i = y * img.width + x;
    if (mask[i]) return;
    const p = pixelAt(img, x, y);
    const lum = 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2];
    if (dist(p, bg) > 78 || lum < 116) return;
    mask[i] = 1;
    queue.push([x, y]);
  };
  for (let x = 0; x < img.width; x += 1) {
    push(x, 0);
    push(x, img.height - 1);
  }
  for (let y = 0; y < img.height; y += 1) {
    push(0, y);
    push(img.width - 1, y);
  }
  for (let head = 0; head < queue.length; head += 1) {
    const [x, y] = queue[head];
    push(x + 1, y);
    push(x - 1, y);
    push(x, y + 1);
    push(x, y - 1);
  }
  return mask;
}

function bbox(img, mask) {
  let x0 = img.width;
  let y0 = img.height;
  let x1 = -1;
  let y1 = -1;
  for (let y = 0; y < img.height; y += 1) {
    for (let x = 0; x < img.width; x += 1) {
      if (mask[y * img.width + x]) continue;
      x0 = Math.min(x0, x);
      y0 = Math.min(y0, y);
      x1 = Math.max(x1, x);
      y1 = Math.max(y1, y);
    }
  }
  return { x0, y0, x1, y1, w: x1 - x0 + 1, h: y1 - y0 + 1 };
}

function removeSmallForegroundComponents(img, mask) {
  const visited = new Uint8Array(img.width * img.height);
  const minArea = 700;
  const neighbors = [
    [-1, -1], [0, -1], [1, -1],
    [-1, 0], [1, 0],
    [-1, 1], [0, 1], [1, 1],
  ];
  for (let y = 0; y < img.height; y += 1) {
    for (let x = 0; x < img.width; x += 1) {
      const start = y * img.width + x;
      if (visited[start] || mask[start]) continue;
      const pixels = [start];
      const queue = [start];
      visited[start] = 1;
      for (let head = 0; head < queue.length; head += 1) {
        const i = queue[head];
        const cx = i % img.width;
        const cy = Math.floor(i / img.width);
        for (const [dx, dy] of neighbors) {
          const nx = cx + dx;
          const ny = cy + dy;
          if (nx < 0 || ny < 0 || nx >= img.width || ny >= img.height) continue;
          const ni = ny * img.width + nx;
          if (visited[ni] || mask[ni]) continue;
          visited[ni] = 1;
          queue.push(ni);
          pixels.push(ni);
        }
      }
      if (pixels.length < minArea) {
        for (const i of pixels) mask[i] = 1;
      }
    }
  }
  return mask;
}

function copyPixel(dst, dx, dy, src, sx, sy) {
  const sx0 = Math.max(0, Math.min(src.width - 1, Math.round(sx)));
  const sy0 = Math.max(0, Math.min(src.height - 1, Math.round(sy)));
  const si = (sy0 * src.width + sx0) * 4;
  const di = (dy * dst.width + dx) * 4;
  dst.data[di] = src.data[si];
  dst.data[di + 1] = src.data[si + 1];
  dst.data[di + 2] = src.data[si + 2];
  dst.data[di + 3] = 255;
}

function blankPng(width, height) {
  const out = new PNG({ width, height });
  for (let i = 0; i < out.data.length; i += 4) {
    out.data[i] = magenta[0];
    out.data[i + 1] = magenta[1];
    out.data[i + 2] = magenta[2];
    out.data[i + 3] = magenta[3];
  }
  return out;
}

function makeCell(frame, scale) {
  const out = blankPng(cellW, cellH);
  const scaledW = Math.round(frame.box.w * scale);
  const scaledH = Math.round(frame.box.h * scale);
  const left = Math.round((cellW - scaledW) / 2);
  const top = cellH - scaledH - bottomMargin;
  for (let y = 0; y < scaledH; y += 1) {
    for (let x = 0; x < scaledW; x += 1) {
      const sx = frame.box.x0 + x / scale;
      const sy = frame.box.y0 + y / scale;
      const mi = Math.round(sy) * frame.img.width + Math.round(sx);
      if (frame.mask[mi]) continue;
      copyPixel(out, left + x, top + y, frame.img, sx, sy);
    }
  }
  return out;
}

function blit(dst, src, ox, oy) {
  for (let y = 0; y < src.height; y += 1) {
    for (let x = 0; x < src.width; x += 1) {
      const si = (y * src.width + x) * 4;
      const di = ((oy + y) * dst.width + ox + x) * 4;
      dst.data[di] = src.data[si];
      dst.data[di + 1] = src.data[si + 1];
      dst.data[di + 2] = src.data[si + 2];
      dst.data[di + 3] = src.data[si + 3];
    }
  }
}

function jobUrl(dir) {
  const file = `${root}/logs/hero-${dir}-take1-generate.json`;
  const json = JSON.parse(fs.readFileSync(file, 'utf8'));
  if (!json[0]?.result_url) throw new Error(`No result_url in ${file}`);
  return json[0].result_url;
}

for (const dir of dirs) {
  const video = `${root}/videos/hero-${dir}-take1.mp4`;
  if (!fs.existsSync(video)) {
    const curl = spawnSync('curl', ['-L', '--fail', '--silent', '--show-error', jobUrl(dir), '-o', video], { stdio: 'inherit' });
    if (curl.status !== 0) process.exit(curl.status);
  }
  const rawDir = `${root}/frames/hero-${dir}-take1-raw`;
  fs.rmSync(rawDir, { recursive: true, force: true });
  fs.mkdirSync(rawDir, { recursive: true });
  const log = fs.openSync(`${root}/logs/hero-${dir}-take1-ffmpeg-extract.log`, 'w');
  const ff = spawnSync(ffmpeg, ['-y', '-i', video, '-vf', 'fps=2', '-frames:v', '8', `${rawDir}/frame-%02d.png`], {
    stdio: ['ignore', log, log],
  });
  fs.closeSync(log);
  if (ff.status !== 0) process.exit(ff.status);
}

const frames = [];
for (const dir of dirs) {
  const files = fs.readdirSync(`${root}/frames/hero-${dir}-take1-raw`).filter((f) => f.endsWith('.png')).sort();
  if (files.length !== 8) throw new Error(`${dir} extracted ${files.length} frames`);
  for (const file of files) {
    const img = readPng(`${root}/frames/hero-${dir}-take1-raw/${file}`);
    const mask = removeSmallForegroundComponents(img, backgroundMask(img));
    const box = bbox(img, mask);
    frames.push({ dir, file, img, mask, box });
  }
}

const maxW = Math.max(...frames.map((f) => f.box.w));
const maxH = Math.max(...frames.map((f) => f.box.h));
const scale = Math.min(260 / maxW, 328 / maxH);
const summary = [];
const sheet = blankPng(cellW * 8, cellH * 4);

for (let row = 0; row < dirs.length; row += 1) {
  const dir = dirs[row];
  const dirFrames = frames.filter((f) => f.dir === dir);
  const contact = blankPng(cellW * 8, cellH);
  for (let col = 0; col < dirFrames.length; col += 1) {
    const cell = makeCell(dirFrames[col], scale);
    blit(contact, cell, col * cellW, 0);
    blit(sheet, cell, col * cellW, row * cellH);
  }
  writePng(`${root}/contact-sheets/hero-${dir}-contact.png`, contact);
  summary.push({
    dir,
    scale: Number(scale.toFixed(4)),
    widthMin: Math.min(...dirFrames.map((f) => f.box.w)),
    widthMax: Math.max(...dirFrames.map((f) => f.box.w)),
    heightMin: Math.min(...dirFrames.map((f) => f.box.h)),
    heightMax: Math.max(...dirFrames.map((f) => f.box.h)),
    heightDriftPx: Math.max(...dirFrames.map((f) => f.box.h)) - Math.min(...dirFrames.map((f) => f.box.h)),
    heightDriftPct: Number((((Math.max(...dirFrames.map((f) => f.box.h)) - Math.min(...dirFrames.map((f) => f.box.h))) / Math.max(...dirFrames.map((f) => f.box.h))) * 100).toFixed(1)),
  });
}

writePng('assets/raw/char-hero-sheet-walk8.png', sheet);
writePng(`${root}/char-hero-sheet-walk8.png`, sheet);
fs.writeFileSync(`${root}/logs/hero-walk8-v3-summary.json`, `${JSON.stringify(summary, null, 2)}\n`);
console.log(JSON.stringify(summary, null, 2));
