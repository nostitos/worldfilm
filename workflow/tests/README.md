# worldfilm tests

Every gate and check is exercised on synthetic material whose defects are known. Each test must report its defect and
stay quiet on clean input. Its fixtures live under `workflow/`; schema checks also use the separately installed shotspec-film base schema.
No example project, film project or downloaded footage is needed, and the suite passes with `examples/` absent. Run it with `bash workflow/tests/run.sh` (22 expectations, about 6 s);
`--full` adds the Playwright blur A/B (about 20 s more). It sources nvm's Node 22 itself and uses
`studio/.venv/bin/python` when present; set `WORLDFILM_PYTHON` to any Python with numpy and jsonschema otherwise.
Generated clips, reports and spec cases go to `out/` (ignored by git); scratch projects are built in fresh
temporary directories whose paths contain spaces.

| test | fixture | expected |
|---|---|---|
| `detect_pops.py pop.mp4 --cuts 2.0` | `synth_clips.py`: a square eases across; a hard cut at 2.0 s; a one-frame white flash at frame 45; a one-frame 40 px jump at frame 90 | FAIL with exactly the flash (frame 45) and the pop (frame 90); the cut at 2.0 s is detected and not reported as a pop |
| `loop_seam.py loop-good.mp4` / `loop-seam.mp4` | a square on a closed circle vs the same circle stopped 4 px short | PASS / FAIL on position and velocity |
| `frame_hash.py` baseline, copy, eased | `base.mp4` twice (identical) and `eased.mp4` (expo.out -> expo.inOut) | copy: no frame differs; eased: the changed frames are listed |
| `check_gate_report.py` | synthetic gate reports in `fixtures/`: `gate-report-skip.json` (summary PASS, contrast SKIPPED, 4 samples of frozen margin), `gate-report-margin.json` (7 frozen samples of 9 allowed in a 27 s window; handoff and swatch SKIP), `gate-report-edge.json` (9 of 9, exactly at the limit), `gate-report-no-window.json` (frozen_time without `analysed_window_s`) | skip: NOT PASSED even with `--allow-skip handoff,swatch`; margin: PASSED with the allowed skips, NOT PASSED without them; edge: NOT PASSED, PASSED with `--frozen-margin-samples 0`; no window: NOT PASSED |
| `sweep_lib.mjs` (`sweep_lib_test.mjs`) | synthetic functions: a one-frame mismatch, a counter that steps back (inside and outside a declared swing), an edge that reverses 20 px then jumps 3 px in its hold, overlapping labels, a plate sliding onto the rectangle it names, an overlay still 3 % visible | 14/14 |
| `sweep_lib.mjs` on a whole world (`sweep_world_test.mjs`) | `fixtures/synthetic_world.mjs`: ten 25 x 25 cm tiles land on a schedule while a corner readout shows "N tiles · A cm²"; a camera pushes in on a unit square and holds; a label sits above the square; two captions; a grid overlay fades out. Seven switchable defects: the count rounds instead of flooring, the area loses its thousands separator, one stale frame steps the count back, the push overshoots, the HUD places the plate by hand onto the square, the overlay fades to 3 %, the captions overlap | 17/17: the clean world passes all six checks; each defect is caught by its check. The readout is recomputed independently every frame (integer frame arithmetic for the count, a BigInt area, hand-written digit grouping), so a wrong value on screen fails even when the readout's own formula agrees with itself: rounding first fails at frame 23, the lost separator at frame 45 (1,250 cm²), the stale frame at frame 91. `--sweep clean` exits 0 through `runSweep`, `--sweep format` exits 1 |
| `templates/sweep.template.mjs` | the template copied into a scratch project with no film yet | exit 2 (a placeholder sweep never passes) |
| `templates/film/place_label.js` (`place_label_test.mjs`) | synthetic projections of a rectangular frame: anchor at the middle of its top edge, the top corners as its sides | 9/9: above when there is room, beside the right side past its outer face, beside the left when the right is the readout's, hold line 0.76 (771 px) and 0.60 portrait (1102 px), collision pushed up, plateBox = placeLabel |
| audibility | `synth_sfx.py` sheet with a pop at gain 0.02 and the same pop at 0.9 under a pad | quiet: FAIL; loud: PASS; the silence window is zeros |
| `synth_sfx.py --master-stem` | the loud test sheet's score stem | lifted to -14 +-1.5 LUFS under -2 dBTP (linear gain; zeros stay zeros) |
| `validate_spec.py` (`validate_spec_test.py`) | in scratch projects under a path with spaces: `templates/shotspec.template.json`; `fixtures/spec-neutral.json` (a two-shot neutral spec that sets every optional worldfilm block: rest-drift boosts, reference, blur, world, footage layer, variants, gates, per-shot dial, dense framing target, world anchors, audio cues, silence, music-only stem); the fixture with its mask dir missing; the fixture with eight defects (a path as the gate runner, a one-axis drift, a boost past the end, a reversed silence window, a duplicate cue event, an anchor naming a missing text, unsorted poses, a hold before the last framing key); the fixture without a camera dial | valid, valid, INVALID (mask dir), INVALID naming all eight, INVALID (dial). Copies of each spec and the validator output are kept in `out/spec-cases/` |

Manual checks outside `run.sh`:

| test | fixture | expected |
|---|---|---|
| `blur_ab.py` (`--full`) | `blur-page/index.html` captured with 1 and 4 samples (`capture_subframes.mjs`), hard cut at 0.97 s | moving frames soften; no leak across the cut; the control run without `--cuts` leaks and FAILs |
| `beats_drop.py` | a synthesized 120 BPM track whose bass arrives at 12 s | about 120 BPM, drop near 12 s |
| `sam_separate.py` | `footage/talking-head-3s.mp4` (3 s stock excerpt, see footage/LICENSE.txt), click points on the subject | per-frame masks and a cutout; `footage/depth/index.html` composites a graphic between the cutout and the room |

`doctor.sh` runs the pops, loop, sweep and gate-report tests as its self-test.
