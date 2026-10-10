# studio/kits

Dependencies the studio links instead of copying. worldfilm needs one: the **shotspec-film** skill, which provides
the base Shot Spec schema and `run_gates.py` with its gates. `env.sh`, `doctor.sh`, `validate_spec.py` and every
`build.sh` look for it in this order:

1. `$SHOTSPEC_HOME`
2. `studio/kits/shotspec-film` (a symlink: `ln -s /path/to/shotspec-film studio/kits/shotspec-film`)
3. `~/.codex/skills/shotspec-film`, then `~/.claude/skills/shotspec-film`

Everything else in this folder is ignored by git.

