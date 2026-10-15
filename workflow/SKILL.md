---
name: worldfilm
description: Build code-rendered films from a deterministic world, a camera pose graph and a shared event clock. Adds measured reference matching, optional footage separation, sound audibility checks, subframe capture and frame-level validation to shotspec-film. Use for simulations, spatial explainers, data visualizations and footage with graphics in depth.
---

# worldfilm

Build a reusable production method for the current brief. The subject, visual language, movement, duration, aspect
ratios and soundtrack belong to the project. Never inherit those choices from a worked film or a test fixture.

Use HyperFrames as the renderer. shotspec-film supplies the base Shot Spec, `run_gates.py` and review procedures;
this skill supplies the world, camera and verification tools. The current brief governs creative choices.

## Start

From the repository root:

```bash
source studio/env.sh
bash workflow/scripts/doctor.sh
bash workflow/tests/run.sh
bash studio/new-project.sh my-film
```

In an existing project, read its `PROGRESS.md` and continue from the first unfinished stage. The starter in
`studio/projects/_template` and the equivalent files in `workflow/templates` are the reusable baseline.
Required tests use synthetic fixtures; optional examples and their assets are never required to use this skill.

Dependencies: Node 22+, Python and `studio/requirements.txt`, ffmpeg, HyperFrames, Playwright and Chromium.
shotspec-film is found through `SHOTSPEC_HOME`, `studio/kits/shotspec-film` or an installed skill. SAM footage
separation additionally needs `studio/requirements-sam.txt`; Docker is needed for the reproducibility check.
The root README documents installation. Read third-party licence notices before redistributing bundled components.

## Production invariants

- Build stateful simulations once using seeded randomness and precomputed arrays or geometry. Each frame is a
  function of time; seeking frames in a different order must not change the output. No wall clock or unseeded RNG.
- Use one clock for the picture, camera, labels, audio events and checks.
- Preserve each source's units, precision and rounding policy. Check displayed data with an independent
  computation when applicable: integers for discrete counts, decimal arithmetic for exact decimals, and stated
  tolerances for measurements. A fact file copied from the same erroneous formula is not independent proof.
- Project labels from named subject attachment points. Use the same placement function for drawing and collision
  assertions so the checks measure the actual layout.
- Run gates against each delivered aspect and audio mix. A skipped check is unverified until explicitly explained
  and accepted. Keep the frozen-time sampling margin chosen for this project.
- Update `PROGRESS.md` after each stage. Record waivers, missing observations and the exact files reviewed in
  `GAUNTLET.jsonl`. Measurement does not establish that a person watched or listened.

## Stages

### 0. Intake
Fill `BRIEF.md`, `brand.md`, `MOTION.md` and `facts.json`. Establish the subject, audience, delivery format, palette,
typography, safe areas, motion personality, camera dial, audio approach and review budget. Choose limits against
references and intended viewing conditions. A locked shot, intentional darkness, silence or a static reading hold
can be valid when the brief calls for it; record how they will be evaluated.

### 1. Reference lock
Measure each supplied reference with `measure_reference.py`: palette, accent shares, line weight, texture,
luminance, motion shape and cut rhythm. Render styleframes using the real drawing code; compare them with
`compare_frames.mjs`. Record the measures in `project.reference` and obtain approval or document existing delegated
authority before building motion. Reference pixels are study material unless separately licensed for use.

### 2. Direction
Write directions and select one, recording why the alternatives were rejected. Compile `shotspec.json` from
`tools/build.py` where shared data drives the facts, text, timing and browser constants. Validate with
`validate_spec.py`, run static gates, and review rendered storyboard stills. Plan numeric checks before motion
work so source mistakes are caught early.

### 3. World
`world.js` exposes a world factory such as `createWorld(canvas, {width, height, ...options})`, with `render(cam)`,
`anchors(cam)` and cleanup. The composition exposes a pure `render(t)` or equivalent seek contract. Store
project-specific input paths in `project.world.data_files`.

Return only the attachment points the subject needs, with projection, visibility and distance information.
Above, right and left candidates are available to the label helper; different subject geometry can provide
different points. Keep per-aspect changes in `project.variants[].world_options` and verify that they do not
unintentionally alter another aspect.

For real footage, use `sam_separate.py` to produce masks, preview and alpha cutout. Declare the footage layer and
its depth order. Background and subject frames must follow the same time.

### 4. Camera
Set the project dial once; record any motivated per-shot override. Dials describe camera energy: 1 Locked,
2 Anchored, 3 Motivated, 4 Flowing, 5 Perpetual. They do not choose the film's subject or force decorative motion.

Key `shots[].camera.poses` as `{t, pos, look, fov}`. For positive distance or zoom channels, log-space keys make
relative changes perceptually consistent; interpolate smooth moves with a monotone spline. Handle signed
coordinates and intentional cuts explicitly. Record settle times and velocity peaks for reading and sound cues.

For moving rests at dials 3–5, prefer elliptical drift: `dz = L * sin(omega*t)`,
`dy = V * cos(omega*t)`. Choose amplitudes and rate in the world's scale; the two quadrature components avoid a
single-axis sway stopping at both turning points. Extra drift and boosts must preserve the intended framing.
Locked shots remain locked.

When a shot has a screen-space framing target, solve the camera from that target, key densely enough for the
required accuracy (0.1 s is a starting interval), and assert the projected quantity in the sweep. Check visibility,
direction of the settle and hold tolerance in the relevant shot window. Do not guess poses and judge only stills.

### 5. Timing
Record voiceover first when used, then retime the picture to its real duration. Use `beatgrid_fit.py` for
phase-accurate music timing and `beats_drop.py` to analyse an existing track. A synthesized score can follow the
project's event grid. Music, tempo, drops and silence windows are creative choices. If a silence window exists,
keep the same boundaries in the spec and cue sheet and test the delivered file.

### 6. Build
Use one paused GSAP timeline registered as `window.__timelines.main`, a clock method rather than an accessor,
and deterministic time-based drawing. Expose `window.__worldfilm.seek(t)` for frame capture. A spatial world can
be one composition; use shot sub-compositions where appropriate. Serve variant assets relative to the project
root. Run HyperFrames lint and check.

Use `film/place_label.js` where its placement model fits. Try the point above the subject, then suitable right or
left attachment points, while avoiding the readout, safe-area boundaries and caption region. Configure the hold
line and collision behavior for the design. A label must not obscure its subject or collide with another required
label while visible; assert those relationships using the drawing function's geometry.

Configure `tools/sweep.mjs` from `templates/sweep.template.mjs`: independent data and formatted-readout checks,
project-required monotonicity, framing targets, subject-label clearance and visibility windows. Omit inapplicable
checks deliberately. A required check left TODO cannot pass. Evaluate each delivered layout in its own dimensions.

### 7. Draft gates
Render a draft without blur. Run the configured sweep and the base gate runner:

```bash
python3 "$SHOTSPEC_HOME/scripts/run_gates.py" --spec shotspec.json --video renders/draft.mp4 --composition-dir . --out gates/draft --hyperframes-cmd "npx hyperframes"
python3 "$WORLDFILM_HOME/scripts/check_gate_report.py" gates/draft/gate-report.json
```

Use `npx hyperframes` for the gate runner: an executable path containing spaces can be split incorrectly.
Read SKIP results; allow a skip only with a written reason. Choose required gates and any exceptions in the
project, and pass the allowed list explicitly to `check_gate_report.py`.

The frozen-time runner samples at 10 fps: one sample is `0.1 * 30 / analysed_window_s` seconds per 30 seconds.
Keep two samples of margin unless the project explicitly chooses a different policy. The check measures image
change, so empty or low-detail motion can resemble a hold. Review such cases against the intended movement.

Run `detect_pops.py`, `luma_floor.py` with the project's approved floor, and `loop_seam.py` only for loops.
Store `frame_hash.py` baselines for regression and reproducibility checks. Fix or explicitly accept failures before
review; never inherit a pass from another aspect or audio export.

### 8. Sound
For synthesized sound, generate `audio/cues.json` from events and velocity peaks. Use `synth_sfx.py` to create the
mix and stems; align transient peaks to visual events when appropriate. Use `prove_audible.py` on the delivered
mix, with project-required in-band lift and timing. Its defaults are +4 dB and +125/−45 ms; choose stricter or
different targets only for a stated production need.

Stems carry the mix's gain. Any single-stem export goes through `synth_sfx.py --master-stem` before muxing.
Verify chosen loudness, peak ceiling and any declared silence windows. Request the required human listening
pass and record who listened; a metric is not a listening verdict.

### 9. Master and review
For deterministic output, render twice with `hyperframes render --docker` and compare decoded frames with
`frame_hash.py`. If blur is requested, use engine blur when available; otherwise use `capture_subframes.mjs`
with the spec's samples and shutter angle. Pass hard-cut times so samples never cross them. State the renderer
and environment used for each output; local capture and a Docker render are distinct reproducibility claims.

Render and gate each aspect and mix separately. Export the requested masters, subtitles and poster. Use fresh
critics to examine structure, framing, data, timing and sound together; fix concrete findings within the budget
chosen at intake. A ten-round ceiling can limit open-ended work, but no round number predicts a category of
failure or establishes quality. Stop when the agreed criteria are met or the user ends refinement.
A post-review picture change requires a verification review or a clearly documented gap.

## Tools

| tool | purpose |
|---|---|
| `measure_reference.py`, `compare_frames.mjs` | Reference measurements and styleframe comparison |
| `capture_subframes.mjs` | Seekable stills and shutter capture with cut exclusion |
| `detect_pops.py`, `luma_floor.py`, `loop_seam.py` | Pop/flash, luminance and loop checks |
| `frame_hash.py` | Decoded-frame hashes and optional PSNR tolerance |
| `check_gate_report.py` | Explain skipped/failed gates and sampling margin |
| `sweep_lib.mjs`, `templates/sweep.template.mjs` | Project-specific assertions on every relevant frame |
| `templates/film/place_label.js` | Shared drawing and checking placement function |
| `synth_sfx.py`, `prove_audible.py`, `beats_drop.py` | Synthesized sound, audibility and track analysis |
| `sam_separate.py` | Optional subject masks and alpha footage |
| `validate_spec.py`, `doctor.sh` | Schema validation and environment readiness |
| `templates/build.sh` | The configured build, sound, render and gate sequence |
