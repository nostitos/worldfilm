# PROGRESS.md — __PROJECT_SLUG__

Resumable state of this film. A fresh session reads this first and continues from the first unchecked stage.
Update it at the end of every stage (the stage name, what was produced, what the critic said, what is pending).
A row is "done" only when its gate line is green: a SKIP is not a pass (check_gate_report.py), and every aspect
variant has its own row because it is gated on its own render.

| stage | status | artifact(s) | notes |
|---|---|---|---|
| 0 intake | todo | BRIEF.md, brand.md, MOTION.md, facts.json | dial = ?  rest drift = ellipse (MOTION.md) |
| 1 reference lock | todo | references/*.reference.json, gates/compare-sheet.png, styleframes/ | approved by: |
| 2 direction | todo | DIRECTIONS.md (3, two killed), TREATMENT.md, shotspec.json (validate_spec), gates/static | storyboard critic: |
| 3 world | todo | world.js (anchors with -right/-right-outer/-left/-left-outer variants), data/, tools/build.py | precomputed once: |
| 4 camera | todo | film/camera.js (pose graph, rest drift, framing targets keyed <= 0.1 s), shots[].camera | dial honoured:  framing targets asserted in the sweep: |
| 5 timing | todo | narration (if any), beat grid, audiomap.json | drop at: |
| 6 build | todo | index.html, compositions/<variant>.html, film/main.js (label placement rule), tools/sweep.mjs configured | lint/check 0/0:  sweep: N frames, 0 violations |
| 7 draft gates | todo | gates/draft-N/ (run_gates via npx hyperframes + check_gate_report, pops, loop_seam, frame_hash) | frozen: x of y samples (2 of margin) |
| 8 sound | todo | audio/cues.json, assets/mix.wav, assets/stems/, assets/music-only.wav (--master-stem), gates/audible-mix.json | listened by: nobody yet |
| 9 master · 16:9 full mix | todo | renders/<slug>-1080p60.mp4, gates/master-<slug>-1080p60 | run_gates / pops / luma / audible: |
| 9 master · 16:9 music-only | todo | renders/<slug>-1080p60-music-only.mp4, gates/master-<slug>-1080p60-music-only | loudness after --master-stem: |
| 9 master · 16:9 Docker A/B | todo | renders/picture-a/b.mp4, gates/master/hash-compare.json | frames identical: |
| 9 master · <variant WxH> | todo | renders/<slug>-<WxH>.mp4, gates/master-<slug>-<WxH> | own render; run_gates / pops / luma: |
| 9 Gauntlet | todo | GAUNTLET.jsonl, gates/critic_rN.md | rounds (budget 10): |

## Known misses and limits
- (what is red, what nobody has checked by eye or ear, what a later session must not mistake for done)

## Log
- (date) stage N: what happened, what changed, what is next

