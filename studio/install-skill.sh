#!/bin/bash
# studio/install-skill.sh — link the worldfilm skill where Codex and Claude Code discover skills. Re-runnable; reversible (delete the links).
# worldfilm requires shotspec-film; that link is checked, never replaced.
set -eu
STUDIO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$(cd "$STUDIO_DIR/../workflow" && pwd)"
for base in "$HOME/.codex/skills" "$HOME/.claude/skills"; do
  [ -d "$base" ] || continue
  dst="$base/worldfilm"
  if [ -L "$dst" ] || [ ! -e "$dst" ]; then ln -sfn "$SKILL_SRC" "$dst"; echo "linked $dst -> $SKILL_SRC"; else echo "skip: $dst exists and is not a symlink"; fi
  if [ -e "$base/shotspec-film/SKILL.md" ]; then echo "ok: $base/shotspec-film present (required)"; else echo "MISSING: $base/shotspec-film — install the shotspec-film skill there first (worldfilm builds on it)"; fi
done
