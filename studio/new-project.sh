#!/bin/bash
# studio/new-project.sh <slug> — start a film from the template. Example: bash studio/new-project.sh block-space
set -eu
[ $# -ge 1 ] || { echo "usage: new-project.sh <kebab-case-slug>"; exit 2; }
STUDIO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dst="$STUDIO_DIR/projects/$1"
[ -e "$dst" ] && { echo "exists: $dst"; exit 1; }
cp -R "$STUDIO_DIR/projects/_template" "$dst"
for f in BRIEF.md brand.md MOTION.md PROGRESS.md README.md shotspec.json facts.json build.sh tools/build.py tools/srt.py audio/make_cues.py tools/sweep.mjs; do
  [ -f "$dst/$f" ] && sed -i '' "s/__PROJECT_SLUG__/$1/g" "$dst/$f"
done
echo "created $dst"
echo "next: 1) fill BRIEF.md, brand.md, MOTION.md (dial, rest drift, label hold line, variants) and facts.json"
echo "      2) references into references/, footage into footage/, data into data/, music into assets/music/"
echo "      3) open the project in Codex/Claude Code and say: use worldfilm on this brief"
echo "      build.sh runs stages 2-9 (fill its header: SILENCE, VARIANTS, POSTER_T); tools/sweep.mjs exits 2 until its checks are configured"

