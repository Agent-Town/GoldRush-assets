# Motion Pilot — Sprite Walk Cycles From Seedance Video

Date: 2026-07-09  
Scope: evidence only. No integration, no source edits, no sheet replacement.

## Run Summary

Three first takes were generated with Higgsfield `seedance_2_0`, 4s, 720p, 1:1, no audio. No retries were used.

| Clip | Job ID | Credits | Video | Contact sheet | Verdict |
|---|---:|---:|---|---|---|
| Hero side-walk | `aaf21593-3210-4f35-91d2-3ccd8e4de128` | 18 | `videos/hero-side-take1.mp4` | `contact-sheets/hero-side-contact.png` | pipeline-worthy |
| Hero down-walk | `6cddf580-ced2-48cb-90fe-ecb8b5af1764` | 18 | `videos/hero-down-take1.mp4` | `contact-sheets/hero-down-contact.png` | pipeline-worthy |
| Baron side-walk | `de6082c4-7ca5-4964-85e7-eed6cb9c03c5` | 18 | `videos/baron-side-take1.mp4` | `contact-sheets/baron-side-contact.png` | pipeline-worthy |

Credit spend: 54 total. Account balance went from 875 to 821 after this run.

## References

- `references/hero-side-start.png` from `assets/processed-full/char-hero-sheet-walk4-a-r2c0.png` plus `assets/raw/hero-homesteader.png`.
- `references/hero-down-start.png` from `assets/processed-full/char-hero-sheet-walk4-a-r0c0.png` plus `assets/raw/hero-homesteader.png`.
- `references/baron-side-start.png` from `assets/processed-full/char-baron-sheet-walk4-a-r2c0.png` plus `assets/raw/kit-the-baron.png`.

## Extraction

- Raw MP4s decoded to 8 frames each at `fps=2`; raw frames are 960x960.
- Final strips use 5% trim, bottom alignment, and a 280x340 frame canvas.
- BBox metrics are in `logs/*-bbox-metrics.txt`.
- Local note: Homebrew `ffmpeg`/`ffprobe` were present but broken on a missing `libx265.215.dylib`. Extraction used an isolated `/tmp` `imageio-ffmpeg` binary instead; no repo dependency was added.

## Assessment

### Hero Side-Walk

Silhouette consistency: strong. Hat, coat, pan, teal lantern, and satchel survive across all 8 frames.  
Style match: close to the in-game sprite, with slightly smoother video linework and a larger/cleaner figure than the current sheet cells.  
Background separability: good. Sand background is flat enough for alpha-keying, with minor video compression and edge softness.  
Limb coherence: good. The cycle reads as a real side gait, not just pose jitter.  
Drift: trimmed height stays 494-504px; width changes are gait-driven.

Verdict: pipeline-worthy.

### Hero Down-Walk

Silhouette consistency: good. Identity and front-view outfit details hold, including the teal lantern.  
Style match: close enough for a first-pass walk8 source. The front pose reads a little heavier and cleaner than the current gameplay sheet.  
Background separability: good. Same flat sand field; keying should be practical after crop/scale cleanup.  
Limb coherence: good but subtler than side-view; the model keeps the torso stable and moves mostly legs/arms.  
Drift: trimmed height grows 499-559px, so the next prompt should add "locked footline and fixed scale" if this becomes production.

Verdict: pipeline-worthy.

### Baron Side-Walk

Silhouette consistency: strong. Coat mass, top hat, mustache, and side profile stay recognizable.  
Style match: good against `kit-the-baron` and the current Baron walk4 sheet, with slightly more polished shading.  
Background separability: good. Flat enough to key, though the dark coat edge will need careful feathering.  
Limb coherence: good. The coat hides some leg motion, but the walk reads clearly and loops naturally.  
Drift: trimmed height stays 606-620px; width variation is mostly gait/coat swing.

Verdict: pipeline-worthy.

## Pipeline Call

Seedance can help. The useful path is video-first for temporal consistency, then frame extraction/crop/key into walk8 sheets. It should not replace the normal extraction/contract QA: production prompts still need locked footline/scale, and every accepted clip needs manual contact-sheet review before SpriteAnimator work.
