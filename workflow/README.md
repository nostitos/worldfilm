# worldfilm — the skill

`SKILL.md` is the skill: start here, non-negotiables 7-15, stages 0-9 with the rules written as requirements, the
script table, and the lessons still kept as prose. `schema/worldfilm.schema.json` extends the shotspec-film Shot Spec
(camera dial and rest drift, framing targets, label placement and hold line, aspect variants with their own world
options, the gate reader's settings, the music-only export). `scripts/` holds the gates and tools, including
`check_gate_report.py` (a skipped gate is not a passed gate) and `sweep_lib.mjs` (per-frame assertions).
`templates/` holds the project documents plus `build.sh` (stages 2-9 in order), `sweep.template.mjs` and
`film/place_label.js` (the label placement rule as one function shared by the HUD and the sweep). `tests/` holds the
fixtures and `run.sh` (19 expectations against known defects; `--full` adds the Playwright blur A/B).

The studio that runs it is `../studio` (`env.sh`, `.venv`, `node_modules` with the HyperFrames CLI and Playwright,
`new-project.sh`, `projects/_template`; shotspec-film is found as described in `../studio/kits/README.md`). The
worked example is `../studio/projects/block-space`.

Install the skill links with `bash studio/install-skill.sh` (shotspec-film must be installed); check readiness with
`bash workflow/scripts/doctor.sh`; validate the skill with `bash workflow/tests/run.sh`.

