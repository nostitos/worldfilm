# worldfilm tests

Every gate script is exercised on synthetic material whose defects are known, plus one real-footage and one real-film
fixture. Run everything with `bash workflow/tests/run.sh` (19 expectations, about 5 s; `--full` adds the Playwright
blur A/B, about 20 s more); it sources nvm's Node 22 and studio/.venv itself. `doctor.sh` runs the pops, loop, sweep
and gate-report tests as its self-test.


| test | fixture | expected |
|---|---|---|
| `detect_pops.py pop.mp4 --cuts 2.0` | `synth_clips.py`: a square eases across; a hard cut at 2.0 s; a one-frame white flash at frame 45; a one-frame 40 px jump at frame 90 | FAIL with exactly the flash (frame 45, also reported as a flash) and the pop (frame 90); the cut at 2.0 s is detected, not reported as a pop; `--allow 1.5,3.0` turns both into allowed hits and the gate passes |
| `loop_seam.py loop-good.mp4` / `loop-seam.mp4` | a square on a closed circle vs the same circle stopped 4 px short | PASS (seam 0.94 vs inner p95 1.43) / FAIL on position (x1.28) and velocity (x2.63) |
| `frame_hash.py` baseline, copy, eased | `base.mp4` twice (identical) and `eased.mp4` (expo.out -> expo.inOut) | copy: 0/90 differ; eased: 62/90 differ starting at frame 1, listed |
| `blur_ab.py` | `blur-page/index.html` captured with 1 and 4 samples (`capture_subframes.mjs`), hard cut at 0.97 s | gradient energy on moving frames x0.77; no leak across the cut (0.17 / 0.50 levels); the control run without `--cuts` leaks 48.7 levels and FAILs |
| audibility | `synth_sfx.py` sheet with a pop at gain 0.02 and the same pop at 0.9 under a pad | quiet: lift 0.0 dB FAIL; loud: +8.4 dB PASS |
| `beats_drop.py` | a synthesized 120 BPM track whose bass arrives at 12 s | 119.8 BPM, drop 11.98 s; `--start auto --duration 10 --drop-at 0.4` places the window so the drop lands at 4.99 s |
| `sam_separate.py` | `footage/talking-head-3s.mp4` (3 s Mixkit excerpt, see footage/LICENSE.txt), 7 click points | 90 masks, subject 20 % of the frame, clean hair edge; `footage/depth/index.html` composites a graphic between the cutout and the room (`out/depth-still.png`) |
| `measure_reference.py` | the "21,000,000" master | palette #f5f1ea 71 %, accents yellow/cyan/pink-red, line 12 px at 1080p, 1 cut at 64.0 s |
| `compare_frames.mjs` | a frame of the same film vs a reference frame; the blur test square vs the same frame | "close" (palette distance 0.3) / "far" (296) |
| `check_gate_report.py` | `fixtures/gate-report-skip.json` (a real Docker-master report with the contrast gate SKIPped by a path with a space), `fixtures/gate-report-margin.json` (draft20: 7 frozen samples of 9 allowed) | skip: NOT PASSED (contrast SKIPPED; 9/9 samples, no margin); margin: PASSED with `--allow-skip handoff,swatch`, NOT PASSED without it |
| `sweep_lib.mjs` (`sweep_lib_test.mjs`) | synthetic functions: a one-frame mismatch, a counter that steps back (inside and outside a declared swing), an edge that reverses 20 px then jumps 3 px in its hold, overlapping labels, a plate sliding onto its gate, a 3 % ladder under a headline | 14/14: each check reports its defect and stays quiet on clean input |
| `sweep_lib.mjs` on real data (`sweep_blockspace.mjs`) | Block Space's film/camera.js and film/data.js | 1,801 frames, 5 checks, 0 violations (subsidy = BigInt recomputation, readout forward, exact at NOW and the end, end edge settles then holds, ladder gone) |
| `templates/sweep.template.mjs` | the empty template project | exit 2 with "build stages 3-4 first" (a placeholder sweep never passes) |
| `templates/film/place_label.js` (`place_label_test.mjs`) | synthetic projections | 9/9: above when there is room, beside the right post past its outer face, beside the left when the right is the readout's, hold line 0.76 (771 px) and 0.60 portrait (1102 px), collision pushed up, plateBox = placeLabel |
| `synth_sfx.py --master-stem` | the loud test sheet's score stem | lifted to -14 +-1.5 LUFS under -2 dBTP (linear gain; zeros stay zeros) |
| `validate_spec.py` | the template spec, the Block Space spec, and a spec with a path as the gate runner, a one-axis drift and a reversed silence window | valid, valid (warnings for not-yet-built artefacts), INVALID with the three reasons |


`synth_clips.py` writes the synthetic clips into `out/` (ignored by git). `doctor.sh` runs the pops and loop
tests as its self-test.
