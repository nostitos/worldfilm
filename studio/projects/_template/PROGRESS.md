# PROGRESS.md — __PROJECT_SLUG__

Resumable state of this film. A fresh session reads this first and continues from the first unfinished stage.
Update it at the end of every stage (what was produced, what the critic said, what is pending). A row is "done"
only when its gate line is green: a SKIP is not a pass (check_gate_report.py). Every delivered variant gets its own
row because it is gated on its own render. Delete rows for deliverables this film does not have.

| stage | status | artifact(s) | notes |
|---|---|---|---|
| 0 intake | todo | BRIEF.md, brand.md, MOTION.md, facts.json | dial = ?  rests: still / drift |
| 1 reference lock | todo | references/*.reference.json, gates/compare-sheet.png, styleframes/ | approved by: |
| 2 direction | todo | DIRECTIONS.md, TREATMENT.md, shotspec.json (validate_spec), gates/static | storyboard critic: |
| 3 world | todo | world.js (anchors(cam), optional side candidates), data/, tools/build.py | precomputed once: |
| 4 camera | todo | film/camera.js (pose graph, optional rest drift, framing targets), shots[].camera | framing targets asserted in the sweep: |
| 5 timing | todo | narration (if any), beat grid (if any) | |
| 6 build | todo | index.html, compositions/<variant>.html, film/main.js (label placement rule), tools/sweep.mjs configured | lint/check:  sweep: N frames, 0 violations |
| 7 draft gates | todo | gates/draft-<master>/ (run_gates via npx hyperframes + check_gate_report, pops, luma, loop seam if configured) | frozen margin: |
| 8 sound | todo | per audio route: audio/cues.json + assets/mix.wav + gates/audible-mix.json, or a supplied track, or none | reviewed by: |
| 9 master · primary | todo | renders/<slug>-<WxH>.mp4, gates/master-<slug>-<WxH>/ | run_gates / pops / luma / audible: |
| 9 master · music-only | todo | renders/<slug>-<WxH>-music-only.mp4 (only when audio.music_only is set) | loudness after --master-stem: |
| 9 master · Docker A/B | todo | renders/picture-a/b.mp4, gates/master/hash-compare.json (when gates.frame_hash_ab) | frames identical: |
| 9 master · <variant id WxH> | todo | renders/<slug>-<id>-<WxH>.mp4, gates/master-<slug>-<id>-<WxH>/ | own render; run_gates / pops / luma: |
| 9 Gauntlet | todo | GAUNTLET.jsonl, gates/critic_rN.md | rounds: |

## Known misses and limits
- (what is red, what nobody has checked by eye or ear, what a later session must not mistake for done)

## Log
- (date) stage N: what happened, what changed, what is next
