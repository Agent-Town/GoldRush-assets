import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { PNG } from 'pngjs';

const dirs = ['down', 'left', 'right', 'up'];
const cellW = 280;
const cellH = 340;
const magenta = [255, 0, 255, 255];
const ffmpeg = '/tmp/gr-imageio-ffmpeg/ffmpeg';
const bottomMargin = 12;

const characters = {
  tavernkeeper: {
    label: 'Tavernkeeper',
    root: 'assets/motion-pilot/production-tavernkeeper',
    turn: 'assets/raw/turn-tavernkeeper.png',
    rawStillPrefix: 'assets/raw/tavernkeeper-start',
    sheet: 'assets/raw/char-tavernkeeper-sheet-walk8.png',
    refs: ['assets/raw/turn-tavernkeeper.png', 'assets/raw/townsfolk-tavernkeeper.png', 'assets/processed-full/townsfolk-tavernkeeper.png'],
    videoRefs: ['assets/raw/turn-tavernkeeper.png', 'assets/raw/townsfolk-tavernkeeper.png'],
    descriptor: 'the exact referenced tavernkeeper: warm stocky bearded man, broad straw hat, cream rolled-sleeve shirt, rust waistcoat, dark leather tavern apron, friendly rounded face, thick mustache and beard',
    sidePin: 'Towel and large apron utility pocket are on his LEFT side; front views show them on viewer-right, screen-right profiles show them near/visible, screen-left profiles hide them on the far side.',
    gait: 'steady warm tavernkeeper walk with real weight, relaxed arms, no swagger and no combat posture',
    clauses: {
      down: 'DOWN/front view: towel and apron pocket stay on his left side, viewer-right.',
      left: 'LEFT profile facing screen-left: the left-side towel and apron pocket are mostly hidden on the far side; do not move them to the near side.',
      right: 'RIGHT profile facing screen-right: the left-side towel and apron pocket are visible on the near side.',
      up: 'UP/back view walking away: towel drapes from his left shoulder and the back apron tie stays centered.',
    },
    qa: {
      down: 'Pass criteria: tavernkeeper face/body, towel left/viewer-right, grounded heavy front gait.',
      left: 'Pass criteria: true left profile, towel/pocket hidden far-side, no swapped apron detail.',
      right: 'Pass criteria: true right profile, left-side towel/pocket visible, no mirrored right-side towel.',
      up: 'Pass criteria: true back view, rear apron and towel side hold, no face turn.',
    },
  },
  storekeeper: {
    label: 'Storekeeper',
    root: 'assets/motion-pilot/production-storekeeper',
    turn: 'assets/raw/turn-storekeeper.png',
    rawStillPrefix: 'assets/raw/storekeeper-start',
    sheet: 'assets/raw/char-storekeeper-sheet-walk8.png',
    refs: ['assets/raw/turn-storekeeper.png', 'assets/raw/townsfolk-storekeeper.png', 'assets/processed-full/townsfolk-storekeeper.png'],
    videoRefs: ['assets/raw/turn-storekeeper.png', 'assets/raw/townsfolk-storekeeper.png'],
    descriptor: 'the exact referenced storekeeper: tidy middle-aged shopkeeper, round spectacles, small curled mustache, side-parted dark hair, pencil tucked behind his left ear, cream rolled-sleeve shirt, rust-brown vest, brown work apron, notebook slips and small vial in apron pocket',
    sidePin: 'Pencil is tucked behind his LEFT ear; notebook slips and small vial sit in the LEFT apron pocket; screen-right profiles show these details, screen-left profiles hide them far-side.',
    gait: 'careful shopkeeper walk with modest measured steps, neat posture, hands relaxed and never holding a weapon',
    clauses: {
      down: 'DOWN/front view: pencil behind his left ear appears on viewer-right; notebook slips and vial stay in the left apron pocket on viewer-right.',
      left: 'LEFT profile facing screen-left: pencil and pocket tools are far-side/mostly hidden; do not move them to the near side.',
      right: 'RIGHT profile facing screen-right: the pencil and left apron-pocket tools are visible on the near side.',
      up: 'UP/back view walking away: apron straps cross correctly, left-ear pencil may be edge-on or hidden, no front face visible.',
    },
    qa: {
      down: 'Pass criteria: storekeeper glasses/mustache/pencil, left pocket tools viewer-right, centered front gait.',
      left: 'Pass criteria: true left profile, far-side pencil/tools hidden, no side swap.',
      right: 'Pass criteria: true right profile with pencil/pocket tools visible, tidy shopkeeper silhouette.',
      up: 'Pass criteria: true back view, apron straps read, no front-face turn.',
    },
    turnaroundRefs: ['assets/raw/townsfolk-storekeeper.png', 'assets/processed-full/townsfolk-storekeeper.png', 'assets/raw/turn-clerk.png'],
    turnaroundPrompt: 'Frontier Ledger illustrated game character turnaround sheet. Create a five-view A-pose turnaround for the exact referenced storekeeper from the portrait/sprite: tidy middle-aged shopkeeper, round spectacles, small curled mustache, side-parted dark hair, pencil tucked behind his LEFT ear, cream rolled-sleeve shirt, rust-brown vest, brown work apron, notebook slips and small vial in the LEFT apron pocket, sturdy boots. Match the existing Gold Rush turnaround layout template: five full-body figures on one parchment sheet in order left profile, three-quarter front, front A-pose, three-quarter opposite, back. Keep the same person, proportions, clothing, side details, and Frontier Ledger sepia engraved linework across all five views. Plain parchment/sand background, no letters, no numbers, no text, no watermark, no extra characters, no firearms, no gore.',
  },
  elder: {
    label: 'Elder',
    root: 'assets/motion-pilot/production-elder',
    turn: 'assets/raw/turn-elder.png',
    rawStillPrefix: 'assets/raw/elder-start',
    sheet: 'assets/raw/char-elder-sheet-walk8.png',
    refs: ['assets/raw/turn-elder.png', 'assets/raw/townsfolk-elder.png', 'assets/processed-full/townsfolk-elder.png'],
    videoRefs: ['assets/raw/turn-elder.png', 'assets/raw/townsfolk-elder.png'],
    descriptor: 'the exact referenced elder: kind frail older frontier man, white beard, weathered hat, layered coat and fringed striped shawl, small teal pendant centered on his vest, pipe in his right hand',
    sidePin: 'Pipe belongs in his RIGHT hand when visible; teal pendant stays centered on the vest; striped shawl fringe remains over both shoulders.',
    gait: 'aged but readable small-step walk, frail and kind, not slow-motion, stable footline',
    clauses: {
      down: 'DOWN/front view: pipe stays in his right hand on viewer-left when visible; teal pendant remains centered.',
      left: 'LEFT profile facing screen-left: right-hand pipe is visible on the near side; pendant is edge-on; shawl fringe remains visible.',
      right: 'RIGHT profile facing screen-right: right-hand pipe is far-side/mostly hidden; pendant is edge-on; no side swap.',
      up: 'UP/back view walking away: no face visible, shawl back fringe and coat silhouette hold; pipe may be hidden on his right side.',
    },
    qa: {
      down: 'Pass criteria: elderly/frail/kind read, centered pendant, right-hand pipe viewer-left.',
      left: 'Pass criteria: true left profile, small aged steps, pipe visible near-side.',
      right: 'Pass criteria: true right profile, pipe hidden far-side, no pendant drift.',
      up: 'Pass criteria: true back view, shawl back/fringe hold, no face turn.',
    },
  },
  'youngster-m': {
    label: 'Youngster-M',
    root: 'assets/motion-pilot/production-youngster-m',
    turn: 'assets/raw/turn-youngster-m.png',
    rawStillPrefix: 'assets/raw/youngster-m-start',
    sheet: 'assets/raw/char-youngster-m-sheet-walk8.png',
    refs: ['assets/raw/turn-youngster-m.png', 'assets/raw/codex-youngster-m-e1.png', 'assets/raw/townsfolk-youngster-a.png'],
    videoRefs: ['assets/raw/turn-youngster-m.png', 'assets/raw/codex-youngster-m-e1.png'],
    descriptor: 'the exact referenced youngster boy, fully clothed minor, newsboy cap, curly hair, freckles, cream shirt, rust vest, suspenders, belted trousers, rolled cuffs, boots, teal lantern hanging from his left hip',
    sidePin: 'Lantern hangs from his LEFT hip; suspenders and vest stay fixed; he is a fully clothed minor in every frame.',
    gait: 'lively short-stride child walk, playful but modest, fully clothed, no running and no exaggerated posing',
    clauses: {
      down: 'DOWN/front view: lantern stays on his left hip on viewer-right; fully clothed.',
      left: 'LEFT profile facing screen-left: left-hip lantern is far-side/mostly hidden; do not move it to the near side; fully clothed.',
      right: 'RIGHT profile facing screen-right: left-hip lantern is near/visible; fully clothed.',
      up: 'UP/back view walking away: lantern stays on left hip, back suspenders visible, fully clothed, no face turn.',
    },
    qa: {
      down: 'Pass criteria: boy identity, fully clothed, lantern left/viewer-right, lively short stride.',
      left: 'Pass criteria: true left profile, lantern hidden far-side, fully clothed.',
      right: 'Pass criteria: true right profile, lantern visible near-side, fully clothed.',
      up: 'Pass criteria: true back view, suspenders/lantern side hold, fully clothed.',
    },
  },
  'youngster-f': {
    label: 'Youngster-F',
    root: 'assets/motion-pilot/production-youngster-f',
    turn: 'assets/raw/turn-youngster-f.png',
    rawStillPrefix: 'assets/raw/youngster-f-start',
    sheet: 'assets/raw/char-youngster-f-sheet-walk8.png',
    refs: ['assets/raw/turn-youngster-f.png', 'assets/raw/codex-youngster-f-e1.png', 'assets/raw/townsfolk-youngster-b.png'],
    videoRefs: ['assets/raw/turn-youngster-f.png', 'assets/raw/codex-youngster-f-e1.png'],
    descriptor: 'the exact referenced youngster girl, fully clothed minor, broad frontier hat, twin braids, red scarf, tan jacket, denim overalls, sturdy boots, teal lantern hanging from her left hip',
    sidePin: 'Lantern hangs from her LEFT hip; twin braids remain part of the silhouette; she is a fully clothed minor in every frame.',
    gait: 'lively short-stride child walk, bright and modest, fully clothed, no running and no exaggerated posing',
    clauses: {
      down: 'DOWN/front view: lantern stays on her left hip on viewer-right; twin braids visible; fully clothed.',
      left: 'LEFT profile facing screen-left: left-hip lantern is far-side/mostly hidden; do not move it to the near side; braids remain; fully clothed.',
      right: 'RIGHT profile facing screen-right: left-hip lantern is near/visible; braids remain; fully clothed.',
      up: 'UP/back view walking away: lantern stays on left hip, back straps and braids visible, fully clothed, no face turn.',
    },
    qa: {
      down: 'Pass criteria: girl identity, fully clothed, lantern left/viewer-right, lively short stride.',
      left: 'Pass criteria: true left profile, lantern hidden far-side, fully clothed.',
      right: 'Pass criteria: true right profile, lantern visible near-side, fully clothed.',
      up: 'Pass criteria: true back view, straps/braids/lantern side hold, fully clothed.',
    },
  },
};

const args = new Map(process.argv.slice(2).map((arg) => {
  const normalized = arg.replace(/^--/, '');
  const eq = normalized.indexOf('=');
  return eq === -1 ? [normalized, 'true'] : [normalized.slice(0, eq), normalized.slice(eq + 1)];
}));
const phase = args.get('phase') ?? 'all';
const only = args.get('only');
const selectedArg = args.get('selected') ?? '';
const selected = Object.fromEntries(dirs.map((dir) => [dir, 1]));
if (selectedArg) {
  for (const pair of selectedArg.split(',')) {
    const [dir, take] = pair.split('=');
    if (!dirs.includes(dir) || !/^[1-9]\d*$/.test(take)) throw new Error(`Bad selected take: ${pair}`);
    selected[dir] = Number(take);
  }
}

function run(cmd, cmdArgs, options = {}) {
  const result = spawnSync(cmd, cmdArgs, { encoding: 'utf8', ...options });
  if (result.status !== 0) {
    process.stderr.write(result.stdout ?? '');
    process.stderr.write(result.stderr ?? '');
    process.exit(result.status ?? 1);
  }
  return result.stdout;
}

function runMaybe(cmd, cmdArgs, options = {}) {
  return spawnSync(cmd, cmdArgs, { encoding: 'utf8', ...options });
}

function write(file, text) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, text);
}

function copyFile(src, dst) {
  fs.mkdirSync(path.dirname(dst), { recursive: true });
  fs.copyFileSync(src, dst);
}

function readPng(file) {
  return PNG.sync.read(fs.readFileSync(file));
}

function writePng(file, png) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, PNG.sync.write(png));
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

function parseJob(json) {
  return Array.isArray(json) ? json[0] : json;
}

function jobIdFromCreate(json) {
  const job = parseJob(json);
  if (typeof job === 'string') return job;
  return job?.id;
}

function resultUrlFromJob(json) {
  return parseJob(json)?.result_url;
}

function accountCredits() {
  const status = run('higgsfield', ['account', 'status']);
  const match = /([\d.]+)\s+credits/.exec(status);
  if (!match) throw new Error(`Could not parse Higgsfield balance: ${status}`);
  return Number(match[1]);
}

function requireBudget(estimated) {
  const balance = accountCredits();
  if (balance - estimated < 400) {
    throw new Error(`Budget stop: balance ${balance}, estimated spend ${estimated}, would drop below 400`);
  }
  return balance;
}

function createAndWait({ jobType, createArgs, createLog, getLog, outputFile, waitAttempts = 120, waitSeconds = 10 }) {
  let createJson;
  if (fs.existsSync(createLog)) {
    createJson = JSON.parse(fs.readFileSync(createLog, 'utf8'));
  } else {
    const stdout = run('higgsfield', ['generate', 'create', jobType, ...createArgs, '--json']);
    write(createLog, stdout);
    createJson = JSON.parse(stdout);
  }

  const id = jobIdFromCreate(createJson);
  if (!id) throw new Error(`No job id in ${createLog}`);

  let jobJson;
  if (fs.existsSync(getLog)) {
    jobJson = JSON.parse(fs.readFileSync(getLog, 'utf8'));
  } else {
    for (let attempt = 0; attempt < waitAttempts; attempt += 1) {
      const result = runMaybe('higgsfield', ['generate', 'get', id, '--json']);
      if (result.status === 0 && result.stdout.trim()) {
        const parsed = JSON.parse(result.stdout);
        const job = parseJob(parsed);
        if (job.status === 'completed') {
          write(getLog, result.stdout);
          jobJson = parsed;
          break;
        }
        if (job.status === 'failed' || job.status === 'canceled') {
          write(getLog, result.stdout);
          throw new Error(`${id} ended with status ${job.status}`);
        }
      }
      spawnSync('sleep', [String(waitSeconds)]);
    }
  }

  if (!jobJson) throw new Error(`${id} did not complete before timeout`);
  const job = parseJob(jobJson);
  if (job.status !== 'completed') throw new Error(`${id} still ${job.status}`);
  const url = resultUrlFromJob(jobJson);
  if (!url) throw new Error(`No result_url in ${getLog}`);
  if (outputFile && !fs.existsSync(outputFile)) {
    run('curl', ['-L', '--fail', '--silent', '--show-error', url, '-o', outputFile], { stdio: 'inherit' });
  }
  return job;
}

function stillPrompt(character, dir) {
  return [
    'Frontier Ledger illustrated game sprite reference.',
    `Use ${character.descriptor}.`,
    character.sidePin,
    character.clauses[dir],
    `Full body ${dir.toUpperCase()} ${dir === 'down' ? 'front' : dir === 'up' ? 'back' : 'profile'} view, mid-stride walk pose, centered single figure, full body visible head to boots, plain flat sand-colored background, fixed ground line, readable silhouette.`,
    'Keep the same clothing, colors, linework, proportions, and side-specific details as the reference images.',
    'No mirroring, no letters, no numbers, no text, no logo, no watermark, no extra characters, no realistic firearms, no gore.',
  ].join(' ');
}

function videoPrompt(character, dir) {
  return [
    'Frontier Ledger illustrated game sprite reference.',
    `Use ${character.descriptor}.`,
    character.sidePin,
    character.clauses[dir],
    `Full body ${dir.toUpperCase()} ${dir === 'down' ? 'front' : dir === 'up' ? 'back/away' : 'profile'} view, walking steadily in place against a plain flat sand-colored background.`,
    character.gait,
    'Constant centered framing, locked footline and fixed scale, feet on a fixed ground line, no vertical drift, no camera motion, no zoom, no turn, no mirroring, no extra characters, no text or letters, no realistic firearms, no gore.',
    'Seamless 4-second loop with one clean readable gait cycle; keep proportions, silhouette, clothing, colors, linework, and pinned side details consistent frame to frame.',
  ].join(' ');
}

function ensureDirs(character) {
  for (const sub of ['logs', 'stills', 'videos', 'frames', 'contact-sheets']) {
    fs.mkdirSync(`${character.root}/${sub}`, { recursive: true });
  }
}

function generateTurnaround(character) {
  if (!character.turnaroundPrompt || fs.existsSync(character.turn)) return null;
  ensureDirs(character);
  requireBudget(7);
  write(`${character.root}/logs/higgsfield-account-status-before-turnaround.txt`, run('higgsfield', ['account', 'status']));
  const out = `${character.root}/stills/turn-storekeeper-take1.png`;
  const createArgs = [
    '--prompt', character.turnaroundPrompt,
    '--aspect-ratio', '16:9',
    '--resolution', '2k',
    '--quality', 'high',
  ];
  for (const ref of character.turnaroundRefs) createArgs.push('--image', ref);
  const job = createAndWait({
    jobType: 'gpt_image_2',
    createArgs,
    createLog: `${character.root}/logs/turn-storekeeper-take1-create.json`,
    getLog: `${character.root}/logs/turn-storekeeper-take1-generate.json`,
    outputFile: out,
    waitAttempts: 90,
  });
  copyFile(out, character.turn);
  write(`${character.root}/logs/higgsfield-account-status-after-turnaround.txt`, run('higgsfield', ['account', 'status']));
  return job;
}

function generateStills(character) {
  ensureDirs(character);
  requireBudget(28);
  write(`${character.root}/logs/higgsfield-account-status-before-stills.txt`, run('higgsfield', ['account', 'status']));
  const jobs = [];
  for (const dir of dirs) {
    const out = `${character.root}/stills/${path.basename(character.rawStillPrefix)}-${dir}-take1.png`;
    const createArgs = [
      '--prompt', stillPrompt(character, dir),
      '--aspect-ratio', '1:1',
      '--resolution', '2k',
      '--quality', 'high',
    ];
    for (const ref of character.refs) createArgs.push('--image', ref);
    const job = createAndWait({
      jobType: 'gpt_image_2',
      createArgs,
      createLog: `${character.root}/logs/${path.basename(character.rawStillPrefix)}-${dir}-take1-create.json`,
      getLog: `${character.root}/logs/${path.basename(character.rawStillPrefix)}-${dir}-take1-generate.json`,
      outputFile: out,
      waitAttempts: 90,
    });
    copyFile(out, `${character.rawStillPrefix}-${dir}.png`);
    jobs.push({ dir, id: job.id, output: out });
  }
  makeStillContact(character);
  write(`${character.root}/logs/higgsfield-account-status-after-stills.txt`, run('higgsfield', ['account', 'status']));
  write(`${character.root}/logs/still-jobs.json`, `${JSON.stringify(jobs, null, 2)}\n`);
}

function generateVideos(character) {
  ensureDirs(character);
  requireBudget(216);
  write(`${character.root}/logs/higgsfield-account-status-before-videos.txt`, run('higgsfield', ['account', 'status']));
  const created = [];
  const base = path.basename(character.rawStillPrefix);
  for (const dir of dirs) {
    const dirJobs = [];
    for (let take = 1; take <= 3; take += 1) {
      const createArgs = [
        '--prompt', videoPrompt(character, dir),
        '--start-image', `${character.rawStillPrefix}-${dir}.png`,
        '--aspect-ratio', '1:1',
        '--duration', '4',
        '--resolution', '720p',
        '--mode', 'std',
        '--generate-audio', 'false',
      ];
      for (const ref of character.videoRefs) createArgs.push('--image', ref);
      const createLog = `${character.root}/logs/${base}-${dir}-video-take${take}-create.json`;
      let createJson;
      if (fs.existsSync(createLog)) {
        createJson = JSON.parse(fs.readFileSync(createLog, 'utf8'));
      } else {
        const stdout = run('higgsfield', ['generate', 'create', 'seedance_2_0', ...createArgs, '--json']);
        write(createLog, stdout);
        createJson = JSON.parse(stdout);
      }
      const id = jobIdFromCreate(createJson);
      if (!id) throw new Error(`No job id in ${createLog}`);
      created.push({ dir, take, id });
      dirJobs.push({ dir, take, id });
    }
    write(`${character.root}/logs/video-jobs-created.json`, `${JSON.stringify(created, null, 2)}\n`);

    for (const { take, id } of dirJobs) {
      const getLog = `${character.root}/logs/${base}-${dir}-video-take${take}-generate.json`;
      const video = `${character.root}/videos/${base}-${dir}-take${take}.mp4`;
      let jobJson;
      if (fs.existsSync(getLog)) {
        jobJson = JSON.parse(fs.readFileSync(getLog, 'utf8'));
      } else {
        for (let attempt = 0; attempt < 120; attempt += 1) {
          const result = runMaybe('higgsfield', ['generate', 'get', id, '--json']);
          if (result.status === 0 && result.stdout.trim()) {
            const parsed = JSON.parse(result.stdout);
            const job = parseJob(parsed);
            if (job.status === 'completed') {
              write(getLog, result.stdout);
              jobJson = parsed;
              break;
            }
            if (job.status === 'failed' || job.status === 'canceled') {
              write(getLog, result.stdout);
              throw new Error(`${dir} take${take} ${id} ended with status ${job.status}`);
            }
          }
          spawnSync('sleep', ['10']);
        }
      }
      if (!jobJson) throw new Error(`${id} did not complete before timeout`);
      const url = resultUrlFromJob(jobJson);
      if (!url) throw new Error(`No result_url in ${getLog}`);
      if (!fs.existsSync(video)) run('curl', ['-L', '--fail', '--silent', '--show-error', url, '-o', video], { stdio: 'inherit' });
    }
  }
  write(`${character.root}/logs/higgsfield-account-status-after-videos.txt`, run('higgsfield', ['account', 'status']));
  write(`${character.root}/logs/higgsfield-transactions-post-videos.json`, run('higgsfield', ['account', 'transactions', '--size', '100', '--json']));
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
  const bgSum = Math.max(1, bg[0] + bg[1] + bg[2]);
  const bgNorm = bg.map((v) => v / bgSum);
  const mask = new Uint8Array(img.width * img.height);
  const queue = [];
  const isBackground = (p, y) => {
    const lum = 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2];
    const pSum = Math.max(1, p[0] + p[1] + p[2]);
    const pNorm = p.map((v) => v / pSum);
    const chroma = Math.sqrt(
      (pNorm[0] - bgNorm[0]) ** 2 +
      (pNorm[1] - bgNorm[1]) ** 2 +
      (pNorm[2] - bgNorm[2]) ** 2,
    );
    return (dist(p, bg) <= 92 && lum >= 82) || (y > img.height * 0.65 && chroma <= 0.11 && lum >= 42);
  };
  const push = (x, y) => {
    if (x < 0 || y < 0 || x >= img.width || y >= img.height) return;
    const i = y * img.width + x;
    if (mask[i]) return;
    if (!isBackground(pixelAt(img, x, y), y)) return;
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

function removeBackgroundLikeForegroundComponents(img, mask) {
  const visited = new Uint8Array(img.width * img.height);
  const minArea = 620;
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
      let x0 = x;
      let y0 = y;
      let x1 = x;
      let y1 = y;
      let lumTotal = 0;
      let satTotal = 0;
      let dark = 0;
      let rust = 0;
      visited[start] = 1;
      for (let head = 0; head < queue.length; head += 1) {
        const i = queue[head];
        const cx = i % img.width;
        const cy = Math.floor(i / img.width);
        x0 = Math.min(x0, cx);
        y0 = Math.min(y0, cy);
        x1 = Math.max(x1, cx);
        y1 = Math.max(y1, cy);
        const idx = i * 4;
        const r = img.data[idx];
        const g = img.data[idx + 1];
        const b = img.data[idx + 2];
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b;
        lumTotal += lum;
        satTotal += max === 0 ? 0 : (max - min) / max;
        if (lum < 72) dark += 1;
        if (r > g * 1.18 && r > b * 1.5 && r > 70) rust += 1;
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
      const area = pixels.length;
      const avgLum = lumTotal / area;
      const avgSat = satTotal / area;
      const darkRatio = dark / area;
      const rustRatio = rust / area;
      const w = x1 - x0 + 1;
      const h = y1 - y0 + 1;
      const parchmentIsland = avgLum > 108 && avgSat < 0.3 && darkRatio < 0.08 && rustRatio < 0.06;
      const groundShadow = y0 > img.height * 0.63 && w > h * 2.25 && rustRatio < 0.03;
      if (area < minArea || parchmentIsland || groundShadow) {
        for (const i of pixels) mask[i] = 1;
      }
    }
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
  if (x1 < x0 || y1 < y0) return { x0: 0, y0: 0, x1: img.width - 1, y1: img.height - 1, w: img.width, h: img.height };
  return { x0, y0, x1, y1, w: x1 - x0 + 1, h: y1 - y0 + 1 };
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

function fitBlit(dst, src, ox, oy, boxW, boxH) {
  const scale = Math.min(boxW / src.width, boxH / src.height);
  const w = Math.round(src.width * scale);
  const h = Math.round(src.height * scale);
  const left = ox + Math.round((boxW - w) / 2);
  const top = oy + Math.round((boxH - h) / 2);
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      copyPixel(dst, left + x, top + y, src, x / scale, y / scale);
    }
  }
}

function makeStillContact(character) {
  const contact = blankPng(640, 640);
  const files = dirs.map((dir) => `${character.rawStillPrefix}-${dir}.png`);
  for (let i = 0; i < files.length; i += 1) {
    if (!fs.existsSync(files[i])) continue;
    const img = readPng(files[i]);
    fitBlit(contact, img, (i % 2) * 320, Math.floor(i / 2) * 320, 320, 320);
  }
  writePng(`${character.root}/contact-sheets/${path.basename(character.rawStillPrefix)}-stills-contact.png`, contact);
}

function extractVideos(character) {
  const re = new RegExp(`^${path.basename(character.rawStillPrefix)}-(down|left|right|up)-take(\\d+)\\.mp4$`);
  const videos = fs.readdirSync(`${character.root}/videos`).map((file) => re.exec(file)).filter(Boolean);
  for (const match of videos) {
    const [, dir, take] = match;
    const video = `${character.root}/videos/${path.basename(character.rawStillPrefix)}-${dir}-take${take}.mp4`;
    const rawDir = `${character.root}/frames/${path.basename(character.rawStillPrefix)}-${dir}-take${take}-raw`;
    fs.rmSync(rawDir, { recursive: true, force: true });
    fs.mkdirSync(rawDir, { recursive: true });
    const log = fs.openSync(`${character.root}/logs/${path.basename(character.rawStillPrefix)}-${dir}-take${take}-ffmpeg-extract.log`, 'w');
    const ff = spawnSync(ffmpeg, ['-y', '-i', video, '-vf', 'fps=2', '-frames:v', '8', `${rawDir}/frame-%02d.png`], {
      stdio: ['ignore', log, log],
    });
    fs.closeSync(log);
    if (ff.status !== 0) process.exit(ff.status);
  }
}

function loadFrames(character, dir, take) {
  const rawDir = `${character.root}/frames/${path.basename(character.rawStillPrefix)}-${dir}-take${take}-raw`;
  const files = fs.readdirSync(rawDir).filter((f) => f.endsWith('.png')).sort();
  if (files.length !== 8) throw new Error(`${character.label} ${dir} take${take} extracted ${files.length} frames`);
  return files.map((file) => {
    const img = readPng(`${rawDir}/${file}`);
    const mask = removeBackgroundLikeForegroundComponents(img, backgroundMask(img));
    const box = bbox(img, mask);
    return { dir, take, file, img, mask, box };
  });
}

function contactForFrames(frames, outFile, scale = null) {
  const maxW = Math.max(...frames.map((f) => f.box.w));
  const maxH = Math.max(...frames.map((f) => f.box.h));
  const useScale = scale ?? Math.min(260 / maxW, 328 / maxH);
  const contact = blankPng(cellW * 8, cellH);
  for (let i = 0; i < frames.length; i += 1) {
    const cell = makeCell(frames[i], useScale);
    blit(contact, cell, i * cellW, 0);
  }
  writePng(outFile, contact);
  return useScale;
}

function stackContacts(files, outFile) {
  const imgs = files.map(readPng);
  const out = blankPng(cellW * 8, cellH * imgs.length);
  for (let i = 0; i < imgs.length; i += 1) blit(out, imgs[i], 0, i * cellH);
  writePng(outFile, out);
}

function processCharacter(character) {
  ensureDirs(character);
  makeStillContact(character);
  extractVideos(character);
  const allFrames = new Map();
  for (const dir of dirs) {
    const takeContacts = [];
    for (let take = 1; take <= 3; take += 1) {
      const frames = loadFrames(character, dir, take);
      allFrames.set(`${dir}-${take}`, frames);
      const contact = `${character.root}/contact-sheets/${path.basename(character.rawStillPrefix)}-${dir}-take${take}-contact.png`;
      contactForFrames(frames, contact);
      takeContacts.push(contact);
    }
    stackContacts(takeContacts, `${character.root}/contact-sheets/${path.basename(character.rawStillPrefix)}-${dir}-takes123-contact.png`);
  }

  const selectedFrames = [];
  for (const dir of dirs) selectedFrames.push(...allFrames.get(`${dir}-${selected[dir]}`));
  const maxW = Math.max(...selectedFrames.map((f) => f.box.w));
  const maxH = Math.max(...selectedFrames.map((f) => f.box.h));
  const scale = Math.min(260 / maxW, 328 / maxH);
  const sheet = blankPng(cellW * 8, cellH * 4);
  const summary = [];
  for (let row = 0; row < dirs.length; row += 1) {
    const dir = dirs[row];
    const frames = allFrames.get(`${dir}-${selected[dir]}`);
    const contactFile = `${character.root}/contact-sheets/${path.basename(character.rawStillPrefix)}-${dir}-contact.png`;
    contactForFrames(frames, contactFile, scale);
    const contact = readPng(contactFile);
    blit(sheet, contact, 0, row * cellH);
    const heights = frames.map((f) => f.box.h);
    const widths = frames.map((f) => f.box.w);
    const heightMax = Math.max(...heights);
    const heightMin = Math.min(...heights);
    summary.push({
      dir,
      selectedTake: selected[dir],
      scale: Number(scale.toFixed(4)),
      widthMin: Math.min(...widths),
      widthMax: Math.max(...widths),
      heightMin,
      heightMax,
      heightDriftPx: heightMax - heightMin,
      heightDriftPct: Number((((heightMax - heightMin) / heightMax) * 100).toFixed(1)),
      qa: character.qa[dir],
    });
  }
  writePng(character.sheet, sheet);
  writePng(`${character.root}/${path.basename(character.sheet)}`, sheet);
  fs.writeFileSync(`${character.root}/logs/${path.basename(character.rawStillPrefix)}-walk8-summary.json`, `${JSON.stringify(summary, null, 2)}\n`);
  writeRunNote(character, summary);
  console.log(JSON.stringify(summary, null, 2));
}

function readJobId(file) {
  if (!fs.existsSync(file)) return '';
  try {
    return parseJob(JSON.parse(fs.readFileSync(file, 'utf8')))?.id ?? '';
  } catch {
    return '';
  }
}

function balanceText(file) {
  if (!fs.existsSync(file)) return 'unavailable';
  return fs.readFileSync(file, 'utf8').trim();
}

function writeRunNote(character, summary) {
  const base = path.basename(character.rawStillPrefix);
  const lines = [];
  lines.push(`# Production ${character.label} Walk8 Run Note`);
  lines.push('');
  lines.push('Date: 2026-07-09');
  lines.push(`Scope: ${character.label} only. No source wiring, no processed-sprite changes, no mirrors.`);
  lines.push('');
  lines.push('## Sources');
  lines.push('');
  lines.push(`- Turnaround anchor: \`${character.turn}\``);
  lines.push(`- Identity references: ${character.refs.map((ref) => `\`${ref}\``).join(', ')}`);
  lines.push(`- Pinned asymmetry: ${character.sidePin}`);
  lines.push('');
  lines.push('## Outputs');
  lines.push('');
  for (const dir of dirs) lines.push(`- Selected ${dir} still: \`${character.rawStillPrefix}-${dir}.png\``);
  lines.push(`- Final raw sheet: \`${character.sheet}\``);
  lines.push(`- Evidence folder: \`${character.root}/\``);
  lines.push(`- Final selected sheet copy: \`${character.root}/${path.basename(character.sheet)}\``);
  lines.push(`- Bbox summary: \`${character.root}/logs/${base}-walk8-summary.json\``);
  lines.push('');
  lines.push('Final grid: rows down/left/right/up, 8 frames per row, 280x340 cells, 2240x1360 sheet, opaque `#ff00ff`.');
  lines.push('');
  lines.push('## Credit / Generation Log');
  lines.push('');
  lines.push(`Balance before stills: ${balanceText(`${character.root}/logs/higgsfield-account-status-before-stills.txt`)}`);
  lines.push(`Balance after videos: ${balanceText(`${character.root}/logs/higgsfield-account-status-after-videos.txt`)}`);
  lines.push('');
  lines.push('| Asset | Model | Job ID | Credits | Use |');
  lines.push('|---|---|---|---:|---|');
  if (character.turnaroundPrompt) {
    const turnId = readJobId(`${character.root}/logs/turn-storekeeper-take1-generate.json`);
    if (turnId) lines.push(`| turnaround | GPT Image 2 | \`${turnId}\` | 7 | selected |`);
  }
  for (const dir of dirs) {
    const stillId = readJobId(`${character.root}/logs/${base}-${dir}-take1-generate.json`);
    lines.push(`| ${dir} still | GPT Image 2 | \`${stillId}\` | 7 | selected |`);
  }
  for (const dir of dirs) {
    for (let take = 1; take <= 3; take += 1) {
      const id = readJobId(`${character.root}/logs/${base}-${dir}-video-take${take}-generate.json`);
      lines.push(`| ${dir} video take ${take} | Seedance 2.0 | \`${id}\` | 18 | ${selected[dir] === take ? 'selected' : 'rejected, see comparison contact sheet'} |`);
    }
  }
  lines.push('');
  lines.push('## Extraction');
  lines.push('');
  lines.push('- MP4s decoded with `/tmp/gr-imageio-ffmpeg/ffmpeg`; no repo dependency was added.');
  lines.push('- Decoded at `fps=2`, 8 frames per selected direction.');
  lines.push('- Final grid order: down, left, right, up; no mirrors and no frame reuse across directions.');
  lines.push('- Background is opaque `#ff00ff`; cells are bottom-aligned.');
  lines.push('');
  lines.push('## QA Verdicts');
  lines.push('');
  lines.push('| Direction | Selected | Verdict | Drift |');
  lines.push('|---|---:|---|---:|');
  for (const row of summary) {
    lines.push(`| ${row.dir} | take${row.selectedTake} | ${row.qa} | ${row.heightDriftPct}% |`);
  }
  lines.push('');
  lines.push('Runtime integration remains pending; no `src/` files were touched.');
  lines.push('');
  fs.writeFileSync(`${character.root}/RUN-NOTE.md`, `${lines.join('\n')}\n`);
}

function selectedCharacters() {
  if (only) {
    if (!characters[only]) throw new Error(`Unknown --only=${only}`);
    return [[only, characters[only]]];
  }
  return Object.entries(characters);
}

for (const [, character] of selectedCharacters()) {
  if (phase === 'turnaround' || phase === 'all') generateTurnaround(character);
  if (phase === 'stills' || phase === 'all') generateStills(character);
  if (phase === 'videos' || phase === 'all') generateVideos(character);
  if (phase === 'process' || phase === 'all') processCharacter(character);
}
