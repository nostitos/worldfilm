# worldfilm skill

Start with [SKILL.md](SKILL.md). It describes the production stages and the boundaries between reusable mechanics
and project choices. `schema/` extends the Shot Spec; `scripts/` contains tools and gates; `templates/` holds the
starter documents, build sequence, sweep and shared label placement helper.

The studio is `../studio`. It provides `env.sh`, `new-project.sh`, package requirements and the shotspec-film
dependency location. Install the skill links with `bash studio/install-skill.sh` from the repository root.
Run `bash workflow/scripts/doctor.sh`, then `bash workflow/tests/run.sh` to check the installation.

`tests/` uses synthetic fixtures. No example film, production data, soundtrack or archived render is needed.
