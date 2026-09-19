// THE ELDER WALKS AS THE WOMAN SHE IS — production script for `char-elder-woman-sheet-walk8`.
//
// This is a COPY of the shipped `assets/motion-pilot/production-town-cast/produce-town-cast.mjs`
// (task elder-walk8-regeneration, 2026-09-07; owner ruling A8, verbatim: "F-AGE1: has to be adapted
// to be woman"). The shipped script and the shipped `production-elder/` evidence are never edited:
// the bearded man's run stays exactly as it landed on 2026-07-09, and git keeps him.
//
// WHAT DIFFERS FROM THE SHIPPED SCRIPT, and why each difference exists:
//  1. `characters` holds one entry, `elderWoman`, rewritten from the batch-3 plates
//     (`assets/raw/tf-elder-woman-e1.png`, `assets/processed/townsfolk-elder.png`). The shipped
//     `elder` entry at :64 references `assets/processed-full/townsfolk-elder.png`, which the a8
//     batch did NOT replace and which is STILL the bearded man — passing it would put the beard
//     back into every frame. It is deliberately absent from `refs` here.
//  2. ffmpeg: the shipped hard-coded `/tmp/gr-imageio-ffmpeg/ffmpeg` does not exist on this Mac.
//     Resolved from $GR_FFMPEG, else the homebrew binary. No repo dependency is added either way.
//  3. Every media reference is UPLOADED first (`higgsfield upload create --json`) and passed to
//     `--image` / `--start-image` as an upload id; ids are cached in `logs/uploads.json` so a
//     resumed run re-uses them and never pays to upload twice.
//  4. Creates are BARE and are never retried; the waiting is a separate, free `generate wait
//     <id> --timeout 10m` (plus the shipped poll loop). This started as `create --wait
//     --wait-timeout 10m` with one retry, and the first still MEASURED why that is wrong: the
//     CLI returned `request failed (no response received)` twice, ~90 s apart, while the account
//     showed two 6.5-credit spends and `generate list` showed two real jobs. What a transient
//     create loses is the RESPONSE, not the job — so a retried create double-spends, and the
//     right recovery is `generate list` + adopt, which is what this run did.
//  5. `runRetryOnce` therefore survives only on FREE calls (uploads, waits), never on a create.
//  6. The video stage stops if the balance is under 1,000 credits (this task's floor), on top of
//     the shipped 400-credit `requireBudget` rule.
//  7. Credits are MEASURED: `higgsfield account transactions` is captured after every paid stage
//     and the RUN-NOTE reports the account-status delta, not the 2026-07 nominal price.
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { PNG } from 'pngjs';

const dirs = ['down', 'left', 'right', 'up'];
const cellW = 280;
const cellH = 340;
const magenta = [255, 0, 255, 255];
const ffmpeg = process.env.GR_FFMPEG ?? '/opt/homebrew/bin/ffmpeg';
const bottomMargin = 12;
const RUN_DATE = '2026-09-07';
const VIDEO_BALANCE_FLOOR = 1000;

const characters = {
  elderWoman: {
    label: 'Elder (woman)',
    root: 'assets/motion-pilot/production-elder-woman',
    turn: 'assets/raw/turn-elder-woman.png',
    rawStillPrefix: 'assets/raw/elder-woman-start',
    sheet: 'assets/raw/char-elder-woman-sheet-walk8.png',
    refs: ['assets/raw/turn-elder-woman.png', 'assets/raw/tf-elder-woman-e1.png', 'assets/processed/townsfolk-elder.png'],
    videoRefs: ['assets/raw/turn-elder-woman.png', 'assets/raw/tf-elder-woman-e1.png'],
    descriptor: 'the exact referenced elder WOMAN from the plates: a kind, frail old frontier schoolmistress-scientist, clean-shaven female face lined with deep laugh-lines, silver-grey hair drawn back off her forehead into a coiled braid pinned low at the nape, a heavy knitted dark-brown cabled shawl worn over BOTH shoulders and closed at the front, a plain warm-brown high-collared buttoned dress with a small ruffled collar, a long skirt over sturdy boots, and a short white chalk stub held in her RIGHT hand',
    sidePin: 'She is a WOMAN in every frame: no beard, no moustache, no hat, no pipe. The white chalk stub belongs in her RIGHT hand when visible; the coiled silver braid stays pinned low at the BACK of her head; the knitted shawl covers BOTH shoulders and never becomes a one-sided fringed blanket.',
    gait: 'aged but readable small-step walk, frail and kind, not slow-motion, stable footline, long skirt swinging with the step',
    clauses: {
      down: 'DOWN/front view: her right hand with the white chalk stub reads on viewer-LEFT; the knitted shawl closes symmetrically over both shoulders; the coiled braid is behind her head and barely visible; clean-shaven female face, no hat.',
      left: 'LEFT profile facing screen-left: her right arm and the chalk stub are on the FAR side and mostly hidden behind her body; the coiled braid at the nape reads clearly against the shawl collar; do not move the chalk to the near side, and do not add a hat or a beard.',
      right: 'RIGHT profile facing screen-right: her right arm and the white chalk stub are on the NEAR side and clearly visible; the coiled braid at the nape reads against the shawl collar; no side swap, no hat, no beard.',
      up: 'UP/back view walking away: no face visible; the coiled silver braid pinned low at the back of her head and the knitted shawl across her back hold the silhouette; the long skirt hem swings with the step; the chalk may be hidden at her right side.',
    },
    qa: {
      down: 'Pass criteria: elderly woman reads frail and kind, clean-shaven face, silver hair back, knitted shawl on both shoulders, right-hand chalk viewer-left, no hat or pipe.',
      left: 'Pass criteria: true left profile, small aged steps, coiled braid at the nape, chalk far-side, one woman across all eight frames.',
      right: 'Pass criteria: true right profile, near-side chalk visible, coiled braid at the nape, no drift to a man.',
      up: 'Pass criteria: true back view, braid and shawl back hold, skirt hem swings, no face turn, no hat.',
    },
    turnaroundRefs: ['assets/raw/tf-elder-woman-e1.png', 'assets/processed/townsfolk-elder.png', 'assets/raw/turn-elder.png'],
    turnaroundPrompt: 'Frontier Ledger illustrated game character turnaround sheet. Create a five-view A-pose turnaround for the exact referenced ELDER WOMAN from the portrait plates: a kind frail old frontier schoolmistress, clean-shaven female face with deep laugh-lines, silver-grey hair drawn back into a coiled braid pinned low at the nape, a heavy knitted dark-brown cabled shawl over BOTH shoulders closed at the front, a plain warm-brown high-collared buttoned dress with a small ruffled collar, a long skirt, sturdy boots, and a short white chalk stub in her RIGHT hand. Match the layout template of the third reference image ONLY - five full-body figures on one parchment sheet in order left profile, three-quarter front, front A-pose, three-quarter opposite, back - but the PERSON is the woman of the first two references. She has no beard, no moustache, no hat, no pipe, no pendant and no fringed striped blanket; do not copy the man of the layout reference. Keep the same person, proportions, clothing, side details, and Frontier Ledger sepia engraved linework across all five views. Plain parchment/sand background, no letters, no numbers, no text, no watermark, no extra characters, no firearms, no gore.',
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

/**
 * One retry on a TRANSIENT Higgsfield failure. The era-aging batches logged 16 of these
 * (`request failed (no response received)`, LEDGER row 75): the request never reached a
 * generation, so it costs nothing and returns no job. Anything else is a real failure and
 * still exits, exactly as the shipped `run` does.
 */
function runRetryOnce(cmd, cmdArgs, options = {}) {
  const first = spawnSync(cmd, cmdArgs, { encoding: 'utf8', ...options });
  if (first.status === 0) return first.stdout;
  const text = `${first.stdout ?? ''}${first.stderr ?? ''}`;
  const transient = /no response received|request failed|timeout|EOF|connection reset/i.test(text);
  if (!transient) {
    process.stderr.write(first.stdout ?? '');
    process.stderr.write(first.stderr ?? '');
    process.exit(first.status ?? 1);
  }
  process.stderr.write(`TRANSIENT, retrying once: ${text.trim().slice(0, 300)}\n`);
  spawnSync('sleep', ['15']);
  const second = spawnSync(cmd, cmdArgs, { encoding: 'utf8', ...options });
  if (second.status !== 0) {
    process.stderr.write(second.stdout ?? '');
    process.stderr.write(second.stderr ?? '');
    process.exit(second.status ?? 1);
  }
  return second.stdout;
}

/**
 * Media references must reach `generate create` as UPLOAD IDS. Each local file is uploaded
 * exactly once per run root; the id is cached in `logs/uploads.json` so a resumed phase never
 * re-uploads and never pays twice.
 */
const uploadCache = new Map();
let uploadCacheFile = null;

function loadUploadCache(root) {
  uploadCacheFile = `${root}/logs/uploads.json`;
  if (!fs.existsSync(uploadCacheFile)) return;
  for (const [file, id] of Object.entries(JSON.parse(fs.readFileSync(uploadCacheFile, 'utf8')))) {
    uploadCache.set(file, id);
  }
}

function uploadId(file) {
  if (uploadCache.has(file)) return uploadCache.get(file);
  if (!fs.existsSync(file)) throw new Error(`Upload source missing: ${file}`);
  const stdout = runRetryOnce('higgsfield', ['upload', 'create', file, '--json']);
  const parsed = JSON.parse(stdout);
  const id = parseJob(parsed)?.id ?? parsed?.id ?? (typeof parsed === 'string' ? parsed : null);
  if (!id) throw new Error(`No upload id for ${file}: ${stdout}`);
  uploadCache.set(file, id);
  if (uploadCacheFile) write(uploadCacheFile, `${JSON.stringify(Object.fromEntries(uploadCache), null, 2)}\n`);
  console.log(`upload ${file} -> ${id}`);
  return id;
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

function requireBudget(estimated, hardFloor = 0) {
  const balance = accountCredits();
  if (hardFloor && balance < hardFloor) {
    throw new Error(`Budget stop: balance ${balance} is below this task's ${hardFloor}-credit floor; STOP and report`);
  }
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
    // NEVER auto-retry a create. MEASURED 2026-09-07, this run: `generate create --wait
    // --wait-timeout 10m` returned `request failed (no response received)` after ~90 s on the
    // down still, the retry returned the same, and the account showed TWO 6.5-credit spends at
    // 07:21:32 and 07:22:54 with two real jobs behind them (58584ded… completed, e173f49c…
    // in_progress). The lost thing is the RESPONSE, not the job: a create that "fails" has
    // usually already charged, so retrying it double-spends. Create bare and cheap, then wait
    // in a separate, FREE call that may be retried as often as it likes.
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
    // Free and therefore freely retried: `generate wait` blocks server-side, `generate get`
    // polls. Both may fail transiently without costing anything.
    runMaybe('higgsfield', ['generate', 'wait', id, '--timeout', '10m', '--quiet', '--json']);
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

const turnaroundBase = (character) => `turn-${path.basename(character.turn, '.png').replace(/^turn-/, '')}-take1`;

function generateTurnaround(character) {
  if (!character.turnaroundPrompt || fs.existsSync(character.turn)) return null;
  ensureDirs(character);
  loadUploadCache(character.root);
  requireBudget(7);
  write(`${character.root}/logs/higgsfield-account-status-before-turnaround.txt`, run('higgsfield', ['account', 'status']));
  const base = turnaroundBase(character);
  const out = `${character.root}/stills/${base}.png`;
  const createArgs = [
    '--prompt', character.turnaroundPrompt,
    '--aspect-ratio', '16:9',
    '--resolution', '2k',
    '--quality', 'high',
  ];
  for (const ref of character.turnaroundRefs) createArgs.push('--image', uploadId(ref));
  const job = createAndWait({
    jobType: 'gpt_image_2',
    createArgs,
    createLog: `${character.root}/logs/${base}-create.json`,
    getLog: `${character.root}/logs/${base}-generate.json`,
    outputFile: out,
    waitAttempts: 90,
  });
  copyFile(out, character.turn);
  write(`${character.root}/logs/higgsfield-account-status-after-turnaround.txt`, run('higgsfield', ['account', 'status']));
  write(`${character.root}/logs/higgsfield-transactions-post-turnaround.json`, run('higgsfield', ['account', 'transactions', '--size', '20', '--json']));
  return job;
}

function generateStills(character) {
  ensureDirs(character);
  loadUploadCache(character.root);
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
    for (const ref of character.refs) createArgs.push('--image', uploadId(ref));
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
  write(`${character.root}/logs/higgsfield-transactions-post-stills.json`, run('higgsfield', ['account', 'transactions', '--size', '20', '--json']));
  write(`${character.root}/logs/still-jobs.json`, `${JSON.stringify(jobs, null, 2)}\n`);
}

function generateVideos(character) {
  ensureDirs(character);
  loadUploadCache(character.root);
  // This task's own floor (master elder-walk8-regeneration): STOP before the videos under 1,000.
  requireBudget(216, VIDEO_BALANCE_FLOOR);
  write(`${character.root}/logs/higgsfield-account-status-before-videos.txt`, run('higgsfield', ['account', 'status']));
  const created = [];
  const base = path.basename(character.rawStillPrefix);
  for (const dir of dirs) {
    const dirJobs = [];
    for (let take = 1; take <= 3; take += 1) {
      const createArgs = [
        '--prompt', videoPrompt(character, dir),
        '--start-image', uploadId(`${character.rawStillPrefix}-${dir}.png`),
        '--aspect-ratio', '1:1',
        '--duration', '4',
        '--resolution', '720p',
        '--mode', 'std',
        '--generate-audio', 'false',
      ];
      for (const ref of character.videoRefs) createArgs.push('--image', uploadId(ref));
      const createLog = `${character.root}/logs/${base}-${dir}-video-take${take}-create.json`;
      let createJson;
      if (fs.existsSync(createLog)) {
        createJson = JSON.parse(fs.readFileSync(createLog, 'utf8'));
      } else {
        // Bare create, never retried — see the note in createAndWait: a lost response still charges.
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
        runMaybe('higgsfield', ['generate', 'wait', id, '--timeout', '10m', '--quiet', '--json']);
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
    // THE GROUND CLAUSE NEEDS A DISTANCE BOUND FOR THIS PALETTE (measured 2026-09-07, this run).
    // The shipped script's second clause is `y > 0.65H && chroma <= 0.11 && lum >= 42` with NO
    // bound on how FAR the pixel is from the parchment. It exists to swallow the hatched ground
    // shadow, which is chromatically the same warm sepia as the paper. The Elder-woman art is that
    // same warm sepia end to end — her skirt is the parchment's hue, only darker — so on the first
    // pass the border flood walked up through the hem and ate the bottom half of every skirt and
    // both boots (see contact-sheets/*-takes123-contact.png in the first process run, kept).
    // MEASURED on frames/elder-woman-start-down-take1-raw/frame-01.png, 960x960: over the pure
    // hatched ground band (rows 850-934, cols 150-329, n=15,300) the Euclidean RGB distance to the
    // sampled background is p50 13, p90 24, p99 61; over the skirt (rows 700-799, cols 420-559,
    // n=14,000) it is p50 166, p90 212, p99 251. A bound of 110 sits far above the ground's p99 and
    // far below the skirt's p50, so it keys the shadow and cannot reach the art.
    const groundShadowLike = dist(p, bg) <= 110 && chroma <= 0.11 && lum >= 42;
    return (dist(p, bg) <= 92 && lum >= 82) || (y > img.height * 0.65 && groundShadowLike);
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
  return reconstructUpperBackground(img, mask, 6);
}

/** Chamfer distance from every pixel to the nearest pixel of `mask` equal to `value`. */
function distanceField(width, height, mask, value) {
  const d = new Float64Array(width * height).fill(1e9);
  for (let i = 0; i < width * height; i += 1) if (mask[i] === value) d[i] = 0;
  const relax = (i, j, cost) => { if (d[j] + cost < d[i]) d[i] = d[j] + cost; };
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = y * width + x;
      if (x > 0) relax(i, i - 1, 1);
      if (y > 0) relax(i, i - width, 1);
      if (x > 0 && y > 0) relax(i, i - width - 1, Math.SQRT2);
      if (x < width - 1 && y > 0) relax(i, i - width + 1, Math.SQRT2);
    }
  }
  for (let y = height - 1; y >= 0; y -= 1) {
    for (let x = width - 1; x >= 0; x -= 1) {
      const i = y * width + x;
      if (x < width - 1) relax(i, i + 1, 1);
      if (y < height - 1) relax(i, i + width, 1);
      if (x < width - 1 && y < height - 1) relax(i, i + width + 1, Math.SQRT2);
      if (x > 0 && y < height - 1) relax(i, i + width - 1, Math.SQRT2);
    }
  }
  return d;
}

/**
 * HER HAIR IS THE COLOUR OF THE PAPER (measured 2026-09-07, this run). On
 * `frames/elder-woman-start-left-take1-raw/frame-01.png` the pixels through her silver hair and
 * temple read Euclidean distance 6-72 from the sampled background at luminance 118-198 — inside
 * `dist <= 92 && lum >= 82` — so the border flood walked in through the gaps between hair strands
 * and speckled the whole head out. NO colour threshold can separate them: at dist 6 the hair IS
 * the parchment's colour. The shipped 2026-07 run met this same class on the bearded cast and
 * answered it on 2026-07-10 with a learned rembg/u2net matte (see
 * `assets/motion-pilot/production-elder/RUN-NOTE.md` "Re-extraction Fix"); no ONNX runtime is
 * installed on this machine, so this run answers it with geometry instead.
 *
 * BACKGROUND RECONSTRUCTION, not a morphological close. Keep only the background reachable from
 * the image border through a channel WIDER than 2r, then restore that region's boundary exactly:
 *   1. erode the background by r  -> the hair-strand gaps break
 *   2. flood from the border over what survives -> the true outside
 *   3. dilate the outside back by r and intersect with the ORIGINAL mask
 * Step 3 is the whole point. A plain close at the radius that heals the head (r=12, measured)
 * thickens the figure and leaves a parchment skirt around the silhouette — visible around the
 * chalk hand and the shawl's front edge in the probe. Reconstruction cannot: every pixel it keeps
 * as background was background before, so the outer contour is bit-identical and only pockets
 * reached through a narrow neck are handed back to the art.
 *
 * BOUNDED TO THE UPPER BAND, at the same 0.65 line the ground clause already uses. Below it the
 * model paints a hatched ground shadow whose pale gaps are exactly this kind of narrow-necked
 * pocket, and reconstruction there re-solidified the shadow into a blob attached to the boots
 * (measured: it survived `removeBackgroundLikeForegroundComponents`, because once joined to the
 * figure it is no longer a wide flat component of its own, and it inflated the up row's height
 * drift). The head is never in that band; the ground always is.
 *
 * r=6 chosen by eye over 6 / 10 / 14 on four frames, one per direction: 6 already closes every
 * hair gap, and larger radii only recover more of the same pixels.
 */
function reconstructUpperBackground(img, mask, r) {
  const { width, height } = img;
  const limit = Math.floor(height * 0.65);
  const toFigure = distanceField(width, height, mask, 0);
  const eroded = new Uint8Array(width * height);
  for (let i = 0; i < width * height; i += 1) eroded[i] = mask[i] && toFigure[i] > r ? 1 : 0;

  const outside = new Uint8Array(width * height);
  const queue = [];
  const push = (x, y) => {
    if (x < 0 || y < 0 || x >= width || y >= height) return;
    const i = y * width + x;
    if (outside[i] || !eroded[i]) return;
    outside[i] = 1;
    queue.push([x, y]);
  };
  for (let x = 0; x < width; x += 1) { push(x, 0); push(x, height - 1); }
  for (let y = 0; y < height; y += 1) { push(0, y); push(width - 1, y); }
  for (let head = 0; head < queue.length; head += 1) {
    const [x, y] = queue[head];
    push(x + 1, y); push(x - 1, y); push(x, y + 1); push(x, y - 1);
  }

  const toOutside = distanceField(width, height, outside, 1);
  for (let y = 0; y < limit; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = y * width + x;
      if (mask[i] && toOutside[i] > r) mask[i] = 0;
    }
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
  lines.push(`Date: ${RUN_DATE}`);
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
  for (const [label, file] of [
    ['before turnaround', 'higgsfield-account-status-before-turnaround.txt'],
    ['after turnaround', 'higgsfield-account-status-after-turnaround.txt'],
    ['before stills', 'higgsfield-account-status-before-stills.txt'],
    ['after stills', 'higgsfield-account-status-after-stills.txt'],
    ['before videos', 'higgsfield-account-status-before-videos.txt'],
    ['after videos', 'higgsfield-account-status-after-videos.txt'],
  ]) {
    lines.push(`Balance ${label}: ${balanceText(`${character.root}/logs/${file}`)}`);
  }
  lines.push('');
  lines.push('| Asset | Model | Job ID | Credits | Use |');
  lines.push('|---|---|---|---:|---|');
  if (character.turnaroundPrompt) {
    const tBase = turnaroundBase(character);
    const turnId = readJobId(`${character.root}/logs/${tBase}-generate.json`)
      || readJobId(`${character.root}/logs/${tBase}-create.json`);
    if (turnId) lines.push(`| turnaround | GPT Image 2 | \`${turnId}\` | 6.5 | selected |`);
  }
  for (const dir of dirs) {
    const stillId = readJobId(`${character.root}/logs/${base}-${dir}-take1-generate.json`)
      || readJobId(`${character.root}/logs/${base}-${dir}-take1-create.json`);
    lines.push(`| ${dir} still | GPT Image 2 | \`${stillId}\` | 6.5 | selected |`);
  }
  for (const dir of dirs) {
    for (let take = 1; take <= 3; take += 1) {
      const id = readJobId(`${character.root}/logs/${base}-${dir}-video-take${take}-generate.json`)
        || readJobId(`${character.root}/logs/${base}-${dir}-video-take${take}-create.json`);
      lines.push(`| ${dir} video take ${take} | Seedance 2.0 | \`${id}\` | 18 | ${selected[dir] === take ? 'selected' : 'rejected, see comparison contact sheet'} |`);
    }
  }
  lines.push('');
  lines.push('## Extraction');
  lines.push('');
  lines.push(`- MP4s decoded with \`${ffmpeg}\`; no repo dependency was added.`);
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
  lines.push('The selection reasons per take, the eyes-on notes and the per-cell height table are appended to this file by hand after the contact sheets are read (task elder-walk8-regeneration, item 2).');
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
