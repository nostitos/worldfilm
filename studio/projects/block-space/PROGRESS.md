# PROGRESS.md — block-space

Resumable state. A fresh session reads this first and continues from the first unchecked stage.

| stage | status | artifact(s) | notes |
|---|---|---|---|
| 0 intake | done | BRIEF.md, brand.md, MOTION.md, facts.json | dial = 4 |
| 1 reference lock | done | references/*.reference.json, gates/compare-sheet.png, styleframes/ | approved by: builder (user delegated the prototype) |
| 2 direction | done | DIRECTIONS.md (A, B killed), TREATMENT.md, shotspec.json, gates/static | static gates PASS |
| 3 world | done | world.js, data/periods.csv (integer satoshi), tools/build.py | 3,438 slabs instanced once; the road ends at NOW; the schedule beyond halving 6 is one ladder |
| 4 camera | done | film/camera.js (pose graph, projector), shots[].camera | dial 4; the end stretch is solved from an edge-position curve, keyed every 0.1 s; rest drift is elliptical since 2026-10-09 (after the shipped 16:9 masters) |
| 5 timing | done | 120 BPM grid in shotspec.json; no voice | silence 25.0-27.0; payoff 27.0 |
| 6 build | done | index.html, compositions/vertical.html, film/, world.js, tools/sweep.mjs | lint 0/0, check 0/0 |
| 7 draft gates | done | gates/draft19 (run_gates PASS 8/0, pops WARN 2 single frames, luma 52, audible 15/15, hashes) | 19 drafts; sweep 0 violations over 1,801 frames |
| 8 sound | done | audio/cues.json, assets/mix.wav, assets/stems/, assets/music-only.wav, gates/audible-mix.json, gates/music-only-master.json | listened by: nobody yet (measurement only) |
| 9 master · 16:9 full mix | done, one gate red | renders/block-space-1080p60.mp4 = picture-blur (4-sample 180° shutter, host Playwright capture) + mix; gates/master-block-space-1080p60 | run_gates 7 PASS / 1 FAIL / 2 SKIP: frozen_time 1.11 s/30 s (limit 1.0; hold 0.2 s); loudness -14.0 LUFS, TP -2.5; contrast PASS; pops 0 (1 shimmer frame 10.12 s); luma 52.3; audible 15/15, silence clean |
| 9 master · 16:9 music-only | done, one gate red | renders/block-space-1080p60-music-only.mp4 = picture-blur + assets/music-only.wav; gates/master-block-space-1080p60-music-only | same picture (frozen_time 1.11 FAIL); loudness -14.3 LUFS, TP -2.0 after --master-stem (the raw stem read -16.3: renders/abandoned/...-stemgain.mp4) |
| 9 master · 16:9 Docker (sharp) | done | renders/block-space-1080p60-docker.mp4 = picture-a + mix; picture-a/picture-b frame-identical (gates/master/hash-compare.json 0/1800); gates/master-block-space-1080p60-docker | run_gates 8 PASS / 0 FAIL / 2 SKIP (frozen_time 1.00 s/30 s, at the limit); pops 0 (2 shimmer); luma 52.2; audible 15/15 |
| 9 master · 9:16 | done | renders/block-space-1080x1920.mp4 = picture-vertical (Docker, 3rd render) + mix; gates/master-block-space-1080x1920 | run_gates 8 PASS / 0 FAIL / 2 SKIP (frozen_time 0.11); pops 0 (1 shimmer 10.17 s); luma 51.3. First render: 2 pops (portal ground bar left the frame in one frame); second: 1 pop (label raced the gate); third: portalFade 14 + label hold at 60 % |
| 9 Gauntlet | done | GAUNTLET.jsonl (11 rows), gates/critic_r1..r10.md | SHIP at round 10 on draft19; row 11 = master gates as measured, no further critic round |

## The shipped 16:9 masters predate the elliptical-drift change
film/camera.js was changed on 2026-10-09 (rest drift on an ellipse, height in quadrature with the lateral sway) after
the 16:9 masters above were rendered. The shipped 16:9 masters therefore fail frozen_time at 1.11 s/30 s (limit 1.0)
on the blur master (1.00 on the Docker master): the micro-drift's turning points read as frozen at the NOW stop and
19.3 s. A local draft with the change (gates/draft20: run_gates PASS 8/0, frozen 0.78 s/30 s) and the 9:16 master
(0.11) show the fix. The work was stopped there on purpose: Block Space is the test case for the workflow, and the
round-10 SHIP already proved every stage. `bash build.sh` regenerates the 16:9 masters with the fix (Docker A/B,
framemd5 compare, blur master, gates), about 25 minutes on this Mac; a verification critic round would then be round 12.

## Known misses and limits
- listened by: nobody. Every audio claim is a measurement (prove_audible, loudness, silence windows).
- The blur master is a host Playwright capture (chrome-headless-shell, SwiftShader) of the same page the Docker
  renders used, not a Docker-pinned render; the installed HyperFrames CLI (0.8.143) exposes no motion-blur option.
- frozen_time quantises at one 10 fps sample = 0.11 s/30 s; the design sits at the bar in its quiet end stretch
  (fast flight over sub-pixel hairlines at 21.2 s, the settle at 23.0-23.3 s, the silence drift at 25.1 and 26.7 s).
- Critic round 10's cosmetic note (readout plate near the horizon, 22.3-23.0 s) is unchanged.

## Log
- 2026-10-09 stages 0-8 built; rounds 1-4 fixed structure (halving visible, a true NOW stop, the street ends, one orange, luma floor, label sizes)
- 2026-10-09 rounds 5-8 fixed framing and placement (end composition solved from a target curve, portals, ladder, label flip rules, shimmer traced to aliasing and fixed in the picture, not the shutter)
- 2026-10-09 round 9 found rounded subsidies (float 50/2^era) where Bitcoin truncates integer satoshi: fixed at the source, asserted per frame against BigInt
- 2026-10-09 round 10: SHIP. Remaining notes: year model (now asserted in the sweep), two single shimmer frames, readout plate near the horizon 22.3-23.0
- 2026-10-09 stage 9: Docker masters A/B (identical), blur master, vertical cut, gates on the delivered files -> gates/master-*
- 2026-10-09 stage 9 close-out: vertical re-rendered twice for its own pops gate (portal dissolve, label hold); music-only re-muxed from assets/music-only.wav (--master-stem); elliptical drift committed to film/camera.js but the 16:9 masters were NOT re-rendered (brief changed: the workflow is the deliverable); abandoned partial renders in renders/abandoned/

