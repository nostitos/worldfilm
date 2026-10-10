---
name: worldfilm
description: World-first, critic-gated pipeline for code-rendered films on top of shotspec-film: simulate a world once (three.js / canvas / DOM / SAM-separated footage), film it with a camera that has a branded energy dial and log-space pose graphs, match the look against measured references, synthesize the sound from the picture's event table and prove every cue audible, master with sub-frame motion blur, and gate the render for pops, loop seams and frame-hash regressions before fresh critics judge it. Requires shotspec-film (HyperFrames renderer, Shot Spec, run_gates.py, Gauntlet). Use when a film is a place to fly through rather than a stack of layers: data cities, simulations, machines, 3D explainers, real footage with graphics in depth.
---

# worldfilm

One film = one world + one camera + one clock. The world is simulated once at load and rendered from a pure
`render(t)`; the camera is a pose graph with a dial set at intake; labels are projected from world anchors; sound is
synthesized from the same event table the picture uses; the master is captured with a real shutter. Everything else
(Shot Spec, facts honesty, measured gates, fresh critics, HyperFrames lint/check/render) is shotspec-film and is not
repeated here: read `shotspec-film/SKILL.md` first, then this file. The spec is `shotspec.json` validated by
`schema/worldfilm.schema.json`, which extends the Shot Spec (old specs validate unchanged).

## Start here
The skill directory (this file's folder; `~/.codex/skills/worldfilm` is a symlink to `workflow/`) sits beside
`studio/`: `source studio/env.sh` (Node 22 via nvm, `studio/.venv`, kit paths), `bash workflow/scripts/doctor.sh`
(READY or the list of what is missing; it also fails a build.sh that passes a path to run_gates), `bash
workflow/tests/run.sh` (every check against its known defect; `--full` adds the Playwright blur A/B), `bash
studio/new-project.sh <slug>` (the template project: BRIEF, brand, MOTION, PROGRESS, shotspec, facts, `build.sh`,
`tools/build.py`, `tools/sweep.mjs`, `tools/srt.py`, `audio/make_cues.py`). In an existing project read
`PROGRESS.md` first and continue from the first unchecked stage; the worked example is
`studio/projects/block-space` (every file named below exists there, with its gate reports and ten critic rounds).

## Dependencies
shotspec-film (the Shot Spec, `run_gates.py`, the static gates and the critic Gauntlet; found through `SHOTSPEC_HOME`,
`studio/kits/shotspec-film` or the installed skill) · the HyperFrames CLI (renderer, `lint`, `check`, `render --docker`)
· three.js · Playwright with Chromium (stills and the shutter capture) · ffmpeg 8 · Python 3.13 with numpy, scipy,
librosa, soundfile, jsonschema (`studio/requirements.txt`) and, for footage, torch, torchvision, transformers and
opencv for SAM 2.1 (`studio/requirements-sam.txt`) · Docker for pixel-stable masters · the `claude` or `codex` CLI for
fresh critics. Code adapted from other projects is listed with its licence in `THIRD_PARTY_NOTICES.md`.

## Non-negotiables (added to shotspec-film's six)
7. The world is built once. `render(t)` moves the camera and the labels; no simulation step runs per frame; no
   `Date`, timers, or unseeded randomness (`project.world.seed`).
8. The camera dial is set once at intake (`project.camera.dial`, 1-5) and governs the camera only; elements keep
   moving at every setting. Height and look-ahead are keyed in log space; poses are interpolated with a monotone
   cubic unless a pose names an ease; consecutive shots share their boundary pose (momentum is handed on). Every
   rest drifts on an ellipse (stage 4): no frame where the camera's velocity is zero.
9. Look is matched to numbers: `measure_reference.py` on every reference, `compare_frames.mjs` on the styleframes,
   and `project.reference.approved` set by a human before stage 3. Reference pixels are never copied.
10. Every sound cue is locked to an event in `events(t)` or a camera velocity peak, and proven audible in the
    delivered file (`prove_audible.py`, +4 dB in its band over the bed, peak not late).
11. Drafts and the Gauntlet render without blur; the master gets the shutter (`project.blur`). The shutter never
    crosses a cut.
12. Three gates run on every render after run_gates: `detect_pops.py` (one-frame pops and flashes), `loop_seam.py`
    (loops only), `frame_hash.py` (baseline on the first clean draft; a kit or tooling change must leave frames
    identical, or the differing frames are listed and explained in the ledger).
13. `PROGRESS.md` is updated at the end of every stage so a fresh session resumes from the first unchecked stage.
14. A skipped gate is not a passed gate. Every run_gates report is read by `check_gate_report.py` (SKIP fails unless
    allowed with a reason in the ledger; frozen_time keeps two samples of margin); run_gates is called with
    `--hyperframes-cmd "npx hyperframes"`, never a path.
15. Every aspect variant is its own film at the gates: its own composition, render, pops / luma / run_gates reports
    and PROGRESS.md row. Nothing is inherited from the 16:9 pass.

## Stages
### 0. Intake
`BRIEF.md`, `brand.md` (colour tokens, type with minimum cap heights, materials, OKLCH interpolation rule),
`MOTION.md` (personality archetype, base duration and eases, the dial with its grammar, the rest-drift numbers,
framing targets, the label placement rule and hold line, the variants, safe areas, transition rules, sound locks),
`facts.json`. Templates: `templates/` (`studio/new-project.sh <slug>` copies them with `build.sh`, `tools/`,
`audio/make_cues.py` and `tools/sweep.mjs` skeletons). One round of questions at most; if the user is away, decide,
write the assumption into PROGRESS.md and keep going.

### 1. Reference lock
`measure_reference.py <video|still|folder> --out references/<name>.reference.json` for each reference (palette,
accents by hue family, line weight at 1080p, grain, luminance, motion-shape series, cut rhythm). Render two or three
styleframes with the real drawing code (the world at its first, middle and last pose), then
`compare_frames.mjs --pairs "styleframes/a.png=ref.mp4@12.5;..." --out gates/compare-sheet.png`. Fill
`project.reference` from the measures; get approval (or record the delegation) before any motion is built. A
styleframe whose luma mean is under 35 is a black tunnel on a phone: fix the light, not the brief.

### 2. Direction
`DIRECTIONS.md`: three written looks, one styleframe each, two killed with the reason. Story-grammar format
chosen (chronology, mission, comparison, reveal). `TREATMENT.md` (three structures, benchmark,
beat sheet, cue map, sound table, subtitle design). Compile `shotspec.json` (`tools/build.py`: one source for data,
facts, spec and browser constants; nothing reaches the screen that did not pass through it), `validate_spec.py
shotspec.json` (schema plus the cross-checks: anchors, poses, framing-target keys, drift boosts, silence windows,
the gate runner command), then `run_gates.py --spec shotspec.json --static` and the storyboard critic on rendered
stills (`capture_subframes.mjs --dir . --stills t1,t2,... --out stills/sheet.png`).

### 3. World
`world.js` exports `createWorld(canvas, {width, height, ...options})` -> `{ render(cam), anchors(cam), dispose }`.
All stateful behaviour (layouts, agents, physics, paths) is simulated at load into typed arrays or instanced
geometry; data worlds read the CSV named in `project.world.data_files` (every value on screen traces to
`facts_file`). Requirements:
- Money is integers. Compute every displayed number in the unit the source uses (satoshi, cents, blocks: integer
  arithmetic, `5e9 >> era`, not `50 / 2**era` rounded), format the integer, and have `tools/sweep.mjs` recompute it
  INDEPENDENTLY (BigInt, a different formula) every frame against what the readout shows. The facts gate cannot see
  a rounding that facts.json shares with the picture; eight critic rounds did not see it either, the ninth did.
- `anchors(cam)` projects named world points to screen with visibility and distance, and for every anchor `<a>`
  that names an object with posts (a gate, a frame, a door) also returns `<a>-right`, `<a>-right-outer`, `<a>-left`,
  `<a>-left-outer` (the post tops and their outer faces): the label placement rule in stage 6 needs them.
- Labels are DOM elements (HyperFrames check can measure their contrast; canvas text is invisible to it).
- `options` are per-composition switches a variant turns on (`project.variants[].world_options`, e.g.
  `portalFade`: objects the camera passes through dissolve over the last N units of the approach, a pure function of
  the pose). With no options the 16:9 code path is byte-identical: prove it with `frame_hash.py` on the 16:9 draft.
Real footage enters through `sam_separate.py clip.mp4 --points "x,y;x,y" --labels "1,0" --out footage/<clip>-sep`
(masks, green preview, VP9-alpha cutout); the composition stacks background video, graphics, cutout, captions in
the order declared in `shots[].footage_layer.depth_order`, and the subject video and the cutout follow the same `t`.

### 4. Camera
`shots[].camera.poses` keyed as `{t, pos, look, fov}` (rail parameters may be kept beside them); `move` names the
phrase, `velocity_peak_s` is where blur and whoosh cues belong, `settle_s` is where reading holds start. Dial
grammar: 1 Locked (hard cuts only) · 2 Anchored (one slow single-axis push per scene) · 3 Motivated (push on a
reveal, settle after, rest with micro-drift; the default) · 4 Flowing (always moving between named poses, momentum
handed shot to shot) · 5 Perpetual (never still; every move pairs zoom with a rotation axis). A per-shot exception
(`shots[].camera.dial`) exists only if MOTION.md names it with its reason.
- Rest drift is elliptical (the rule; `project.camera.rest_drift` carries the numbers, MOTION.md repeats them):
  `dz = A·(L·sin(ωt) + Ls·sin(ωs·t + 1))`, `dy = As·V·cos(ωt)` with L 0.05, V 0.04, ω 1.7 rad/s, Ls 0.03, ωs 0.61
  (world units: scale to the world). A is 1 plus sine-windowed boosts (x4 at a designed stop); As is A without the
  boosts marked `axes: "lateral"`, so an ending that must settle a framing target keeps its big sway lateral. A
  one-axis sine is still at every turning point (every π/ω s) and the frozen_time gate reads those instants as
  frozen: Block Space's NOW stop and 19.3 s read as frozen until the height moved in quadrature.
- Any shot with a framing target (the horizon in the top fifth, the edge of a plane at 4.5 %) is solved from the
  target, not keyed by hand: `shots[].camera.framing_target` names the world point and its screen keys at most
  0.1 s apart, the pose is derived from them (`film/camera.js`), and `tools/sweep.mjs` asserts the projected quantity
  (`settle`: one direction, then hold). The sweep is the proof; the stills are the illustration.
- The camera checklist goes to the critic: a move per shot that differs from the last, focus on the words, no
  constant speed, a settle before every reading hold, no copy-pasted move.

### 5. Timing
Voiceover first when there is one: shotspec-film's rule (real voice length wins; the spec is retimed). Music:
`beatgrid_fit.py` (shotspec-film) for the phase-exact grid; `beats_drop.py track.wav [--duration D --start auto
--drop-at 0.4] -o audiomap.json` for the song map and the drop, so the drop lands on the key visual moment. A
synthesized score uses the project's own beat grid. The silence window is decided here and written once as numbers
that `audio/cues.json`, `shotspec.json audio.silence` and `build.sh SILENCE` all repeat.

### 6. Build
HyperFrames root with one paused GSAP timeline registered as `window.__timelines.main`, the driver's clock as a
method (`{ t(v) {...} }`, never an accessor property), `render(t)` called from the tween's `onUpdate`, and
`window.__worldfilm.seek(t)` exposed for the Playwright route. Sub-compositions per shot only when the film is
DOM-built; a single world is one root. Morph carry between shots: one object survives every boundary (the camera
itself at dial 4-5; a declared `carry` box at dial 1-2). `hyperframes lint` and `check` to zero findings.
- Label placement (a requirement; one pure function, `film/place_label.js` from `templates/film/`, that
  `film/main.js` draws with and `tools/sweep.mjs` asserts with, so the rule lives once): a plate sits ABOVE its
  anchor; if that puts it on the object (a gate's top bar) it moves BESIDE the right post past the post's outer face
  with a leader; if that side belongs to the corner readout, beside the LEFT post; then clamped to the safe area,
  never over the readout, never in the caption zone; a later label that collides is pushed up deterministically.
  A plate stops following its anchor below the hold line (`world_anchors[].hold_line_frac`: 0.76 at 16:9, 0.60 in
  portrait) so it never races a passing object out of the frame (that is a one-frame pop). No plate touches the
  object it names, any frame it is up (`sweep_lib labelsClear`); labels of one family never overlap in time.
- Every extra aspect is `compositions/<id>.html` with root-relative paths (`hyperframes render -c
  compositions/vertical.html`) and a `project.variants[]` entry: its `fov_scale` (portrait: tan(fov/2) x 1.6, capped
  at 100°), its `label_hold_frac`, its `world_options` (portrait Block Space: `portalFade: 14`, because the wider
  vertical field keeps a portal's ground bar on screen until the camera is over it, and a solid bar leaving the
  frame in one frame is a pop). The variant is a different film at the gates (stage 7 and 9); the 16:9 draft's
  frame hashes must not change when a variant option is added.
- `tools/sweep.mjs` (from `templates/sweep.template.mjs`, library `scripts/sweep_lib.mjs`) is configured here:
  every displayed number recomputed independently, readouts monotone except declared swings, readouts exact at
  declared stops, framing targets settle, labels clear their targets, nothing declared gone is visible. It exits 2
  while any check is still TODO; stage 7 cannot pass with a TODO or a violation.

### 7. Draft gates
`hyperframes render --quality draft` (no blur). Pass criteria, all of them, on every draft:
- `node tools/sweep.mjs`: N frames, 0 violations, 0 TODO.
- `run_gates.py --spec shotspec.json --video draft.mp4 --composition-dir . --hyperframes-cmd "npx hyperframes"`
  (never a path: run_gates splits the command on spaces, and a studio path with a space skipped the contrast gate
  for a whole Gauntlet while every report read PASS). Then `check_gate_report.py gates/draft-N/gate-report.json
  --allow-skip <gates the spec cannot feed> --frozen-margin-samples 2`: a SKIP is not a pass, and frozen_time must sit
  two samples under its limit because the gate quantises at one 10 fps sample (0.1 s x 30 / analysed window =
  0.11 s/30 s on a 30 s film) and a blur master or a Docker render reads ±1 sample from a draft (Block Space passed
  at exactly 1.00 on draft 19 and failed at 1.11 on the master). Know which frozen samples are design before touching
  the camera: a 1,400 unit/s flight over sub-pixel hairlines or a slow drift over empty ground reads "frozen" because
  the frame has no features, not because the camera is still.
- `detect_pops.py draft.mp4 [--cuts ...] [--allow ...]`, `loop_seam.py` for loops, `frame_hash.py draft.mp4 --out
  gates/draft-N/hashes.json` (baseline), and the full-frame sweep when the film is canvas-drawn (shotspec-film).
Every FAIL is fixed or waived in the ledger before a critic is asked.

### 8. Sound
Generate the cue sheet from the event table (`audio/make_cues.py` -> `audio/cues.json`): groups `score` and
`sfx`, `align: "peak"` for sounds that must land their loudest sample on the event, exact `silence` windows. The
documented sequence (`build.sh`): `synth_sfx.py audio/cues.json --out assets/mix.wav --stems assets/stems --report
gates/audio-synth.json` (K-weighted -14 LUFS master, true peak under the ceiling, stems with the same gain) ·
`prove_audible.py --mix assets/mix.wav --cues gates/audio-synth.json --bed assets/stems/score.wav --silence a,b`
(every sfx cue +4 dB in its band over the score, 6 dB for the hero hit, peak not late, zeros in the window) ·
`synth_sfx.py --master-stem assets/stems/score.wav --out assets/music-only.wav` (a stem carries the MIX's gain, so a
single-stem export goes through --master-stem before any mux: Block Space's raw score read -16.3 LUFS, -14.3 after)
· the delivered files are proven again with `prove_audible.py --mix renders/<master>.mp4`. Nobody has heard the film
until a human listens: write "listened by:" in PROGRESS.md.

### 9. Master and Gauntlet
Fresh critics (`claude -p --model opus --allowedTools Read --add-dir .` or `codex exec`) receive only: the render,
`gates/<draft>/contact-sheet.jpg` and cut strips, `gate-report.md`, native stills, BRIEF, REFERENCES, MOTION,
TREATMENT, and the previous report. Prompt: `gates/critic_prompt_full.md` (full-film) then the verification
template. Append every round to `GAUNTLET.jsonl` (`{round, type, model, verdict, critic_findings, changes,
gates_before, gates_after}`). The expected shape, from Block Space's ten rounds: rounds 1-4 fix STRUCTURE (what is
on screen, what the street does, the one accent, the light floor, label sizes), rounds 5-8 fix FRAMING and
placement (compositions solved from targets, labels beside posts, aliasing fixed in the picture), round 9 finds the
NUMBERS (a rounding the facts gate shared), round 10 ships. Budget: ten rounds, three minimum; a round that changes
nothing the previous one asked for is a wasted round; stop at SHIP or at diminishing returns, and write the
remaining notes into PROGRESS.md as known misses. A picture change after SHIP gets a verification round or a
documented gap in PROGRESS.md and README; it never ships silently.
Master: `hyperframes render --docker` twice for pixel-stable masters compared with `frame_hash.py --compare` (Mac
GPU renders differ run to run; `--psnr-min 46` tolerates that, Docker does not need it), and
`capture_subframes.mjs --dir . --out renders/picture-blur.mp4 --fps 60 --duration D --samples 4 --shutter 180
--cuts <hard cuts>` (Playwright route; use the engine's `motionBlur` when the CLI exposes it: 0.8.143 does not). Mux
the mastered mix and the --master-stem music-only, poster, SRT. Then every variant: its own Docker render, mux,
and `gate` (run_gates + check_gate_report + pops + luma into `gates/master-<slug>-<WxH>/`), its own PROGRESS.md
row. Deliver with `gates/`, `GAUNTLET.jsonl`, `PROGRESS.md` (known misses and limits filled in) and `build.sh`.

## Scripts (workflow/scripts; studio/.venv for the Python ones, studio/node_modules for the Node ones)
| script | does | stage |
|---|---|---|
| `measure_reference.py` | palette, accents, line weight, grain, luma, motion shape, cut rhythm of a reference | 1 |
| `compare_frames.mjs` | styleframe vs reference sheet with palette distance, luma, saturation, edge density | 1 |
| `capture_subframes.mjs` | frame-exact Playwright capture; N samples over a shutter; never across a cut; `--stills` sheets | 2 (stills), 9 (blur master) |
| `detect_pops.py` | one-frame pops (frame and block level) and flashes; cuts never false-positive | 7, 9 |
| `loop_seam.py` | position and velocity continuity across the loop point | 7 (loops) |
| `frame_hash.py` | per-frame MD5 of decoded frames; compare with optional PSNR tolerance | 7, 9 |
| `luma_floor.py` | per-frame luminance floor (a black tunnel on a phone fails below 35) | 7, 9 |
| `check_gate_report.py` | reads a run_gates report: SKIP is not a pass, frozen_time keeps N samples of margin, required gates present | 7, 9 |
| `sweep_lib.mjs` + `templates/sweep.template.mjs` | per-frame assertions on the project's pure functions: independent recomputation, monotone readouts, settle of a framing target, labels clear their targets, time overlaps, invisibility | 6, 7 |
| `templates/film/place_label.js` | the label placement rule as one pure function (`placeLabel`, `plateBox`) shared by the HUD and the sweep: above, beside right, beside left, safe area, readout, caption zone, hold line, collisions | 3, 6 |
| `synth_sfx.py` | generators, mixer, K-weighted master, stems, exact silence, peak alignment; `--master-stem` normalises one stem with a linear gain | 8 |
| `beats_drop.py` | tempo, grid, downbeats, kicks, bar energy, drop by band energy, auto window | 5 |
| `prove_audible.py` | per-cue in-band lift over the bed and peak timing in the delivered file; silence windows | 8, 9 |
| `sam_separate.py` | SAM 2.1 local separation: masks, preview, alpha cutout | 3 |
| `validate_spec.py` | schema + cross-reference validation of a worldfilm spec (anchors, poses, framing targets, drift, silence, gate runner command, variants) | 2 |
| `doctor.sh` | readiness: Node 22, Chrome, ffmpeg, venv, SAM cache, HyperFrames CLI, blur route, the gate-runner command in every build.sh, self-tests (pops, loop, sweep, gate reader) | setup |
| `templates/build.sh` | the whole sequence stages 2-9 for a project: build.py, validate, static gates, sweep, cues, mix, --master-stem, lint/check, Docker A/B + hash compare, blur master, masters, gates with check_gate_report, every variant on its own | 2-9 |

## Lessons already paid for (keep)
- A 1 mm gap between two coplanar planes z-fights at 300 units and flickers one frame in ten: the pops gate found
  it, the eye did not. Separate planes by a visible margin or use polygonOffset.
- Playwright's `waitForFunction` never fired on a GSAP + WebGL page while `evaluate` saw it ready: poll with
  evaluate. Heavy WebGL pages also starve rAF polling.
- Mean gradient cannot see motion blur (a smeared step keeps its summed gradient); gradient energy can.
- A chroma-only pop is invisible in luma: analyse RGB.
- Per-slice band filters measure their own transients: decode the band once with pre-roll, then slice.
- Newer three.js ships `three.module.js` + `three.core.js`; vendor both.
- HyperFrames serves `compositions/*.html` with the project root as base URL; paths stay root-relative.
- The earlier house film stored supply "through the tip" under a column called `coins_issued_before`; say which you
  mean (before vs through the tip) in the fact's claim.
- A shutter does not remove temporal aliasing. The s02 dolly crossed 0.75 slabs per frame and strobed; a 180
  degree, 4-sample shutter smears half a frame of travel, so 20 shimmer frames survived on the blur master. Keep
  periodic structure under about 0.5 period per frame (slower, higher, or further) and prove it on a re-capture of
  the stretch, sharp and blurred (`gates/draft16/s02-*-pops.json`).
- Lessons that became requirements or checks (do not re-learn them from this list): integer money and the
  independent recomputation -> stage 3 and the sweep; the label placement rule and hold line -> stage 6 and
  `labelsClear`; the elliptical rest drift -> stage 4 and `validate_spec`; frozen_time's quantisation and margin ->
  `check_gate_report.py`; a skipped gate reading as green and the path with a space -> `check_gate_report.py` and
  `doctor.sh`; a stem carrying the mix's gain -> `--master-stem` in `build.sh`; a portrait cut needing its own
  dissolve, hold line and gates -> stage 6, 9 and `project.variants`.
