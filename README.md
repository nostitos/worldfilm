# worldfilm

A content-neutral workflow for films built in code.

Create a deterministic world, film it through a camera pose graph, and drive the picture, labels and sound from one
clock. HyperFrames renders the compositions; measured gates and frame-level assertions check the results.

The subject, palette, typography, camera energy, pacing, duration, soundtrack and delivery sizes are chosen in each
project. A worked example is optional material, and never supplies the starter defaults or required test data.

## What it provides

- An agent skill in [workflow/SKILL.md](workflow/SKILL.md) for Codex and Claude Code.
- A [schema extension](workflow/schema/worldfilm.schema.json) for worlds, cameras, framing targets, label anchors,
  footage depth, blur, audio cues and per-aspect settings.
- Tools to measure reference images and videos, compare styleframes, separate real footage, synthesize sound,
  capture subframes and verify rendered output.
- Starter documents and a build script that takes production settings from the project's spec.
- Synthetic test fixtures that exercise gates without downloading or building a film.

worldfilm builds on shotspec-film's base Shot Spec and gate runner. It is suitable for simulations, product
explainers, spatial diagrams, data visualizations and footage with graphics in depth.

## Production stages

| stage | purpose | principal artifacts |
|---|---|---|
| 0. Intake | Choose the subject, audience, brand, motion language, formats, audio and review budget. | `BRIEF.md`, `brand.md`, `MOTION.md`, `facts.json` |
| 1. Reference lock | Measure references and compare actual styleframes before motion work. | Reference measurements and comparison sheet |
| 2. Direction | Choose a treatment and compile one source of data into the spec and browser constants. | `TREATMENT.md`, `shotspec.json`, static gate report |
| 3. World | Precompute state once; expose deterministic rendering and projected attachment points. | `world.js`, input data, `film/data.js` |
| 4. Camera | Set the camera dial, interpolate pose graphs, and solve any framing targets. | `film/camera.js`, projected-position assertions |
| 5. Timing | Fit voice and music when used; align events to the chosen clock. | Timing grid, event table, optional silence windows |
| 6. Build | Draw the compositions and labels; configure the sweep and delivery variants. | HyperFrames composition, layout helpers, `tools/sweep.mjs` |
| 7. Draft checks | Measure a draft and inspect frame-level assertions. | Gate reports, frame hashes and review stills |
| 8. Sound | Mix or synthesize the requested sound, check cue audibility, and master separate exports. | Mix, stems, audibility and loudness reports |
| 9. Master and review | Render requested outputs, check every aspect and mix, review within the agreed budget. | Masters, subtitles, poster, `GAUNTLET.jsonl`, `PROGRESS.md` |

Each stage records evidence and remaining work in the project. A fresh session resumes from `PROGRESS.md`.
See [the skill](workflow/SKILL.md) for the detailed procedure.

## Reusable principles

**Determinism.** A frame depends on its time and declared inputs. Precompute stateful behavior with seeded
randomness; seeking frames in another order must produce the same result.

**Source fidelity.** Preserve units, precision, rounding policy and provenance. Independently recompute displayed
values where appropriate. Discrete counts may require integer arithmetic; exact decimals may require decimal
arithmetic; measurements need explicit tolerances. Checking an erroneous formula against a copied fact proves
nothing.

**Camera intent.** The dial runs from 1 (Locked) to 5 (Perpetual). Intentional holds are valid. If a moving rest is
desired, elliptical drift uses quadrature components so a single-axis sway does not stop at its turning points.
Choose amplitudes in the scene's scale.

**Framing and labels.** Solve screen-space framing constraints from their targets and assert the projected result.
Use subject-appropriate attachment points and one placement function for both drawing and collision checks.
Validate layouts in every delivered aspect.

**Honest verification.** A skipped gate is unverified until explained and accepted. Record waivers. A metric cannot
establish that a human watched or listened. Examples' creative choices and review histories are not production
requirements.

## Gates and tools

| tool | checks or produces |
|---|---|
| `measure_reference.py`, `compare_frames.mjs` | Palette, line weight, texture, luminance, motion and cuts; styleframe comparison |
| shotspec-film `run_gates.py` | Facts, read time, beat alignment, loudness, contrast, holds and applicable handoffs |
| `check_gate_report.py` | Failed/skipped/missing gates and configurable frozen-time sampling margin |
| `detect_pops.py` | Single-frame pops and flashes, including localized changes |
| `luma_floor.py` | Luminance against the project's approved viewing target |
| `loop_seam.py` | Position and velocity discontinuities, for loops |
| `frame_hash.py` | Decoded-frame equality, with optional PSNR tolerance |
| `sweep_lib.mjs` | Per-frame data consistency, monotonicity, framing, label clearance and visibility assertions |
| `synth_sfx.py`, `prove_audible.py` | Sound generation/mastering and cue-band audibility/timing |
| `beats_drop.py` | Track tempo, energy and candidate drop positions |
| `sam_separate.py` | Optional subject masks, preview and alpha footage |
| `validate_spec.py`, `doctor.sh` | Schema/cross-reference validation and environment checks |

A single-stem export carries the mix's gain, so pass it through `synth_sfx.py --master-stem` before muxing.
When the frozen-time gate is used, its 10 fps samples are normalised by the actual analysis window; keeping two
samples of margin is the default policy. Thresholds and exemptions must reflect the current brief.

HyperFrames remains the renderer. For a reproducibility check, render twice in Docker and compare decoded frames.
For requested motion blur, use engine support when available or the Playwright subframe capture tool. Shutter
samples must stay on the correct side of each hard cut. Document the environment used for each master.

## Installation

Tested on Apple silicon macOS with Node 22, Python 3.13 and ffmpeg 8. Docker is used for reproducible masters.
Core checks do not require optional film examples or stock footage.

```bash
git clone https://github.com/nostitos/worldfilm.git
cd worldfilm
nvm install 22
(cd studio && npm ci && npx playwright install chromium)
uv venv --python 3.13 studio/.venv
uv pip install -r studio/requirements.txt --python studio/.venv/bin/python
```

shotspec-film must be available separately: set `SHOTSPEC_HOME`, link it at `studio/kits/shotspec-film`, or use an
installed skill at `~/.codex/skills/shotspec-film` or `~/.claude/skills/shotspec-film`. The repository does not bundle
that dependency. See [dependency resolution](studio/kits/README.md).

```bash
bash studio/install-skill.sh
source studio/env.sh
bash workflow/scripts/doctor.sh
bash workflow/tests/run.sh
```

The installer links `workflow/` into the existing Codex and Claude Code skill directories.
For SAM footage separation, also install `studio/requirements-sam.txt`; model weights are downloaded on first use.

## Start a project

```bash
bash studio/new-project.sh my-film
```

Fill in the new project's brief, brand and motion documents, add its references and data, then ask the agent to
use worldfilm on that brief. The starter includes:

- `tools/build.py` for shared data, facts, spec and browser constants.
- `tools/sweep.mjs` for project-required assertions; unconfigured checks cannot pass.
- `film/place_label.js` for shared label placement.
- `audio/make_cues.py` for sound events, if requested.
- `build.sh` for the configured build and gate sequence.

Production duration, frame rate, size, aspect variants, silence windows and audio exports come from the project's
spec. Configure what the film needs; the starter does not prescribe a subject, a dramatic silence or a portrait cut.

Run `DRAFT=1 bash build.sh` for a draft, or `bash build.sh` for the master sequence once the project is implemented.
`doctor.sh --project /path/to/project` can check a selected project's build wiring.

## Tests

`bash workflow/tests/run.sh` exercises synthetic clean and defective inputs: frame flashes and jumps, loop seams,
frame hashes, skipped gates, sample margins, independently recomputed data, label placement, framing, audibility
and spec validation. `--full` adds a small Playwright blur test. These checks require no files from `examples/`.
See [the test guide](workflow/tests/README.md).

## Layout

| path | role |
|---|---|
| [workflow/](workflow/) | Installed skill, schema, tools, templates and synthetic tests |
| [studio/](studio/) | Environment setup, dependency requirements and project scaffolding |
| [studio/projects/_template/](studio/projects/_template/) | Reusable starter copied by `new-project.sh` |
| [examples/](examples/) | Optional archived productions, with their own content, assets and evidence |
| [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) | Applicable notices for adapted code |

Optional productions and historical releases are documented inside `examples/`. Their outcomes and unfinished
observations do not determine whether the general workflow's tests pass.

No licence has been selected for worldfilm's own code. Third-party components retain their stated licences.
