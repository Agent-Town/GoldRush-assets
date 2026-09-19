# Pose-library credit corrective — `art-pose-library-01` (2026-07-11)

Written s1367 (2026-08-02) · finding **F-1367-1** · precedent: `production-hero/RUN-NOTE-CORRECTIVE.md`

## Why this file is here, and not next to the note it corrects

The note it corrects — `assets/motion-pilot/pose-library/hero/RUN-NOTE.md` — lives in
`worktrees/art/`, which is a **plain directory, not a git worktree** (F-1331-4). It is tracked on
main **nowhere**. Its only durable copy is the salvage branch `save/art-staging-20260801`
(commit `781079ed`, s1350's RECIPE slice). A corrective written beside it would inherit exactly
the same mortality. **This file is on main so the next reader finds it.**

## The claim being corrected

`pose-library/hero/RUN-NOTE.md:49`:

> Hero used 36 Seedance 2.0 generations at 18 credits each: 648 credits total. Balance moved from
> 1709.99 to 1061.99. A complete Prospector character requires 24 further videos (432 credits),
> which would leave 629.99, below the task's 800-credit floor. **Generation therefore stopped
> before any Prospector still or video was started.**

and its machine twin, `pose-library/hero/logs/hero-credit-log.json`:

```json
"stopFloor": 800,
"stoppedBeforeNextCharacter": true
```

**The bolded sentence and the `stoppedBeforeNextCharacter` field are false.** Everything else in
both documents is exact.

## What actually happened, from the run's own logs

All times UTC. The machine is Bangkok (UTC+07), so file mtimes read +7.

| UTC | Event | Evidence |
|---|---|---|
| 12:56 | hero **and prospector** four-view stills | both dirs, mtime 19:56 +07 |
| 12:58 | hero **and prospector** native stills | prospector has **8** |
| 12:59:32 – 13:14:43 | hero Seedance ×36 | 36 create ids, 36 results, all `completed` |
| 13:21 | hero sheets composed | `char-hero-sheet-*.png` |
| **13:22:04 – 13:22:30** | **prospector Seedance submitted** | **18 distinct create ids; 6 polled results, all `status: completed`, all `job_type: seedance_2_0`** |
| 13:39 | RUN-NOTE.md + hero-credit-log.json **written** | mtime 20:39 +07 |

The credit log's own `transactionWindowUtc.last` is `2026-07-11T13:14:43.990607Z`. The earliest
Prospector job's `created_at` is `2026-07-11T13:22:04.854083Z` — **7 min 21 s after the accounting
window closed, and 16 minutes before the note asserting none of it happened was written.**

`pose-library/prospector/` holds **39 files**: 24 logs + 8 stills + 5 `.mp4` + 2 four-view `.png`.

## The instrument was right; the sentence beside it was not

The credit log is **internally correct**. Its window matches the hero set *to the second*
(hero's last result: `13:14:43.947579Z`). It measured hero exactly and it never looked at anything
else. The defect is that a correctly-scoped **measurement** carried an out-of-scope **conclusion**
in the same file, and the prose then inherited the numbers' authority for a claim the numbers
never covered.

## Unrecorded spend — a range, deliberately not a number

| | jobs | × 18 | balance after 1061.99 | vs the 800 floor |
|---|---:|---:|---:|---|
| **Confirmed** (polled, `status: completed`) | 6 | **108** | 953.99 | above |
| **Submitted** (distinct job ids returned) | 18 | **324** | **737.99** | **62.01 BELOW** |

Twelve submissions have a job id but no polled result on disk. Whether the service charged for
them cannot be determined from this repo. **If it did, the run breached the very floor it says it
stopped to protect.**

No document on disk settles it, and the run notes say why themselves: `production-hero/RUN-NOTE.md:20`
records a "plan reset/grant during the run", and `production-prospector/RUN-NOTE.md:22` warns its
balances are "not a Prospector-only isolated balance". Their balances are `.5`-fractioned against
this run's `.99` — a different account state. **Chaining them would be arithmetic, not evidence.**

The decisive source is a `higgsfield account transactions` query for `2026-07-11T13:22Z`. That is an
external paid service, so it is an owner/attended call (CLAUDE.md §7), not a fire's.

## This was a second, separate Prospector spend

An earlier task already generated Prospector video: `production-prospector/RUN-NOTE.md` (2026-07-09,
4 jobs, 72 credits, producing `assets/raw/char-prospector-sheet-hover8.png`). Its four job ids —
`475075a8…`, `1307bab0…`, `c0bd0015…`, `d76a4842…` — have **zero overlap** with the 18 here, as do
hero's 36. Three genuinely distinct submission sets.

## What is NOT owed

- **No salvage.** `prospector/contact-sheets/` and `prospector/frames/` are **empty**: the run was
  cut off before extraction, so no best-of-three table and **no curated layer exists here** (unlike
  hero, whose 12 picks s1366 salvaged). The 2 prospector four-view composites were already salvaged
  in `ca534290`, and all 24 prospector logs in `781079ed`. **The evidence for this corrective has
  been safe in git since s1350 — it was stored, never read.**
- **No deletion.** RETENTION LAW. The 5 `.mp4` and 8 stills stay where they are; they are part of
  the 527.89 MB awaiting the owner's F-1331-4 ruling.
- **No re-run.** The submission pattern (idle ×4 directions ×3 takes = 12; work down/left ×3 = 6;
  work right/up never submitted) is a run **cut off mid-sequence**, not one that never began.

## Bearing on F-1331-4

s1366 asked this question in its §G and handed it forward unresolved. The answer: the directory
represents **at least 108 and at most 324 credits of spend that no ledger records**, on top of the
648 that one does. It does not change the byte count, and it does not change the recommendation —
but the owner ruling on that directory should know the run's own accounting understates it.
