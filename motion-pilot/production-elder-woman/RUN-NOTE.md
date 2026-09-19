# Production Elder (woman) Walk8 Run Note

Date: 2026-09-07
Scope: Elder (woman) only. No source wiring, no processed-sprite changes, no mirrors.

## Sources

- Turnaround anchor: `assets/raw/turn-elder-woman.png`
- Identity references: `assets/raw/turn-elder-woman.png`, `assets/raw/tf-elder-woman-e1.png`, `assets/processed/townsfolk-elder.png`
- Pinned asymmetry: She is a WOMAN in every frame: no beard, no moustache, no hat, no pipe. The white chalk stub belongs in her RIGHT hand when visible; the coiled silver braid stays pinned low at the BACK of her head; the knitted shawl covers BOTH shoulders and never becomes a one-sided fringed blanket.

## Outputs

- Selected down still: `assets/raw/elder-woman-start-down.png`
- Selected left still: `assets/raw/elder-woman-start-left.png`
- Selected right still: `assets/raw/elder-woman-start-right.png`
- Selected up still: `assets/raw/elder-woman-start-up.png`
- Final raw sheet: `assets/raw/char-elder-woman-sheet-walk8.png`
- Evidence folder: `assets/motion-pilot/production-elder-woman/`
- Final selected sheet copy: `assets/motion-pilot/production-elder-woman/char-elder-woman-sheet-walk8.png`
- Bbox summary: `assets/motion-pilot/production-elder-woman/logs/elder-woman-start-walk8-summary.json`

Final grid: rows down/left/right/up, 8 frames per row, 280x340 cells, 2240x1360 sheet, opaque `#ff00ff`.

## Credit / Generation Log

Balance before turnaround: 4robinlehmann@gmail.com — ultra plan, 3176.49 credits
Balance after turnaround: 4robinlehmann@gmail.com — ultra plan, 3169.99 credits
Balance before stills: 4robinlehmann@gmail.com — ultra plan, 3156.99 credits
Balance after stills: 4robinlehmann@gmail.com — ultra plan, 3137.49 credits
Balance before videos: 4robinlehmann@gmail.com — ultra plan, 3137.49 credits
Balance after videos: 4robinlehmann@gmail.com — ultra plan, 2921.49 credits

| Asset | Model | Job ID | Credits | Use |
|---|---|---|---:|---|
| turnaround | GPT Image 2 | `60c5a1a1-2c98-4d56-8c14-4f382a3b15a3` | 6.5 | selected |
| down still | GPT Image 2 | `58584ded-62ea-444f-bf65-473f7d5925d8` | 6.5 | selected |
| left still | GPT Image 2 | `25e0144c-3e1b-4ca7-ba1d-b2826ef76dbf` | 6.5 | selected |
| right still | GPT Image 2 | `167a0be8-d919-41e5-9939-edae7035e243` | 6.5 | selected |
| up still | GPT Image 2 | `2155a941-ca8d-45bd-9a97-3a4c37b26ec3` | 6.5 | selected |
| down video take 1 | Seedance 2.0 | `6c415367-79e7-4c09-ac66-c1f55720b6e0` | 18 | rejected, see comparison contact sheet |
| down video take 2 | Seedance 2.0 | `a1465bd3-1181-4502-994a-f7524a5a7167` | 18 | rejected, see comparison contact sheet |
| down video take 3 | Seedance 2.0 | `cdc3131c-e465-4a8b-8025-80802abf252b` | 18 | selected |
| left video take 1 | Seedance 2.0 | `270ac05c-44ef-4f76-a4b7-d7f745905cbb` | 18 | selected |
| left video take 2 | Seedance 2.0 | `a51b13f7-9bfa-4872-8b9c-08c51a29d1ca` | 18 | rejected, see comparison contact sheet |
| left video take 3 | Seedance 2.0 | `70cbac66-a3c2-4796-93cb-8d924b349758` | 18 | rejected, see comparison contact sheet |
| right video take 1 | Seedance 2.0 | `d350571f-a0b8-4816-ae97-bb9a7e30026a` | 18 | selected |
| right video take 2 | Seedance 2.0 | `a0f685f5-85f9-4ca3-a4f1-c92a673ebdd5` | 18 | rejected, see comparison contact sheet |
| right video take 3 | Seedance 2.0 | `386dbd75-c1e9-40a3-81ec-33345a294067` | 18 | rejected, see comparison contact sheet |
| up video take 1 | Seedance 2.0 | `feb80458-9ccd-4f40-9e43-7498c7a78950` | 18 | rejected, see comparison contact sheet |
| up video take 2 | Seedance 2.0 | `ea9cdee3-4e56-46c5-8cad-996258803541` | 18 | rejected, see comparison contact sheet |
| up video take 3 | Seedance 2.0 | `d05d1f83-ce01-46aa-9c2f-bf7afbf5acad` | 18 | selected |

## Extraction

- MP4s decoded with `/opt/homebrew/bin/ffmpeg`; no repo dependency was added.
- Decoded at `fps=2`, 8 frames per selected direction.
- Final grid order: down, left, right, up; no mirrors and no frame reuse across directions.
- Background is opaque `#ff00ff`; cells are bottom-aligned.

## QA Verdicts

| Direction | Selected | Verdict | Drift |
|---|---:|---|---:|
| down | take3 | Pass criteria: elderly woman reads frail and kind, clean-shaven face, silver hair back, knitted shawl on both shoulders, right-hand chalk viewer-left, no hat or pipe. | 3.5% |
| left | take1 | Pass criteria: true left profile, small aged steps, coiled braid at the nape, chalk far-side, one woman across all eight frames. | 1.5% |
| right | take1 | Pass criteria: true right profile, near-side chalk visible, coiled braid at the nape, no drift to a man. | 2.2% |
| up | take3 | Pass criteria: true back view, braid and shawl back hold, skirt hem swings, no face turn, no hat. | 5.3% |

The selection reasons per take, the eyes-on notes and the per-cell height table are appended to this file by hand after the contact sheets are read (task elder-walk8-regeneration, item 2).


---

## Selection, by eye (appended by hand after the final `--phase=process` run)

Every take was read at full width on its own contact sheet and against its two siblings on
`contact-sheets/elder-woman-start-<dir>-takes123-contact.png`, after the keying was fixed (see
"Keying" below). Nothing was selected on the drift number alone.

| Dir | Selected | Why this take | Why not the others |
|---|---|---|---|
| down | take 3 | Faces crisp in all eight frames, chalk up in her RIGHT hand on viewer-left, shawl symmetric over both shoulders, boots visible and alternating, least ground-shadow residue. Also the tightest of the three (879-911, drift 3.5%). | take 1 breathes: the figure changes scale across the row (881-936, drift 5.9%). take 2 is very close on the eye but carries visibly more ground-shadow smudge beside the boots in most frames, and measures slightly wider (887-922, 3.8%). |
| left | take 1 | The largest, clearest gait cycle of the three, chalk carried up at chest height so it matches the down and right rows, hem and boots read every frame. Lowest drift on the sheet (839-852, 1.5%). | take 2 barely lifts her feet after frame 3 - the near foot stays planted and the walk stops reading. take 3 walks well but drops the chalk arm low, so the prop disappears against the skirt. |
| right | take 1 | True right profile, biggest readable stride, and the chalk sits on the NEAR side exactly as the direction clause asks - the pinned asymmetry is legible here and nowhere else. | take 2 has a smaller stride and the same silhouette otherwise. take 3 is the reject: the figure runs off the bottom of the frame in frames 2, 5 and 8, leaving a pale wedge where the boot should be. Its 2.0% drift is the best of the three and was NOT followed, because the number is measuring a cropped figure. |
| up | take 3 | Much the steadiest back view (822-868, drift 5.3% against 9.6% and 8.6%), coiled bun and shawl triangle hold, hem swings, boots visible. | take 1 and take 2 both breathe by 75-84 px within the row, which is what a size-pop looks like once the row is scaled into 340 px cells. |

No direction needed the honesty guard's re-take: all four read as the same woman across their eight
frames, with the braid, the knitted shawl, the high collar and the chalk continuous. No mirrors and
no frame reuse - rows 1 and 2 are separate generations with different drape, stride phase and arm
carriage, and the shipped `char-elder-sheet-walk8` man is not the source of a single pixel.

## Keying (why this run's mask differs from the shipped script's)

The shipped colour heuristics were tuned on the 2026-07 cast and fail on this palette twice, both
measured rather than guessed, both fixed in the copy at `produce-elder-woman.mjs` with the numbers
in the code:

1. **Her skirt is the parchment's hue.** The shipped ground clause (`y > 0.65H && chroma <= 0.11 &&
   lum >= 42`) has no bound on distance from the paper, so the border flood walked up through the
   hem and ate the bottom half of every skirt and both boots. Measured on
   `frames/elder-woman-start-down-take1-raw/frame-01.png`: the pure hatched ground reads distance
   p50 13 / p90 24 / p99 61 from the sampled background, the skirt p50 166 / p90 212. Bounding the
   clause at 110 keys the shadow and cannot reach the art. Height drift fell from 28.9-31.9% to
   1.5-9.8% on that change alone.
2. **Her silver hair is the colour of the paper.** Through the hair and temple of
   `elder-woman-start-left-take1-raw/frame-01.png` the pixels read distance 6-72 at luminance
   118-198 - inside the first clause - so the flood speckled every head out through the gaps
   between hair strands. No threshold can separate them; at distance 6 the hair IS the parchment.
   The 2026-07-10 answer to this class was a learned rembg/u2net matte, and no ONNX runtime is
   installed here, so this run uses geometry: background RECONSTRUCTION (erode the background by 6,
   reflood from the border, dilate back and intersect with the original mask), bounded to the band
   above the same 0.65 line. Reconstruction restores the outer contour exactly, so unlike a
   morphological close - which needed r=12 to heal the head and left a parchment skirt around the
   silhouette - it cannot thicken the figure. It is bounded to the upper band because below it the
   drawn ground shadow is the same kind of narrow-necked pocket, and reconstructing there welded
   the shadow onto the boots.

## Sheet and extraction

- Raw sheet `assets/raw/char-elder-woman-sheet-walk8.png`, 2240x1360, 2,067,189 B; 8 cols x 4 rows
  of 280x340, bottom margin 12, background exactly `#ff00ff` and fully opaque (0 non-opaque px,
  73.8% of the sheet exactly `#ff00ff`).
- Extracted with `node scripts/extract-alpha.mjs --key ff00ff --grid 8x4` from a staging copy at
  `artifacts/elder-walk8-regeneration/char-elder-sheet-walk8.png`, so the outputs carry the shipped
  stem the consumers bind to (`assets/processed/char-elder-sheet-walk8-r{0..3}c{0..7}.png` +
  `char-elder-sheet-walk8.frames.json`) while the man's raw `assets/raw/char-elder-sheet-walk8.png`
  is left exactly as it landed on 2026-07-09. Extractor line: keyed 73.8%, spill-cleared 167 px,
  despilled 0 px, bled 2,248,845 px, 32/32 cells @512 px.

### Figure heights per cell (`bbox[3] - bbox[1] + 1`, from the emitted frames.json)

| Row | Dir | c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 | min-max |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| r0 | down | 318 | 316 | 321 | 318 | 324 | 323 | 328 | 325 | 316-328 |
| r1 | left | 302 | 306 | 304 | 302 | 305 | 307 | 302 | 302 | 302-307 |
| r2 | right | 305 | 311 | 306 | 311 | 308 | 306 | 311 | 308 | 305-311 |
| r3 | up | 313 | 308 | 306 | 304 | 301 | 300 | 298 | 296 | 296-313 |

Overall 296-328. Five cells fall outside the contract's 298-321: r0c4 324, r0c5 323, r0c6 328,
r0c7 325, r3c7 296. The largest excursion is 7 px on a ~310 px figure (2.3%), inside the master's
10 px re-take threshold, so no direction was re-taken. NOTE on the band's units: 298-321 is the
shipped sheet measured as `bbox[3] - bbox[1]`, without the +1; in that same convention this sheet
reads 295-327 and the shipped man reads 298-321, while their true pixel heights are 296-328 and
299-322. The comparison above is stated in true pixel heights for both.
