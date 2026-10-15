#!/bin/bash
# studio/new-project.sh <slug> — start a film from the template project (studio/projects/_template).
# The slug is lowercase kebab-case (letters, digits, single hyphens); it becomes the folder name and replaces
# __PROJECT_SLUG__ in every text file of the copy. Example: bash studio/new-project.sh my-film
set -euo pipefail
[ $# -eq 1 ] || { echo "usage: new-project.sh <kebab-case-slug>"; exit 2; }
SLUG_IN="$1"
if ! [[ "$SLUG_IN" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || [ "${#SLUG_IN}" -gt 64 ]; then
  echo "invalid slug '$SLUG_IN': use lowercase letters, digits and single hyphens (max 64 chars), e.g. my-film"; exit 2
fi
STUDIO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$STUDIO_DIR/projects/_template"
DST="$STUDIO_DIR/projects/$SLUG_IN"
[ -d "$SRC" ] || { echo "template missing: $SRC"; exit 1; }
[ -e "$DST" ] && { echo "exists: $DST"; exit 1; }
TMP="$(mktemp -d "$STUDIO_DIR/projects/.new-$SLUG_IN.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
cp -R "$SRC/." "$TMP/"
rm -f "$TMP/.DS_Store"
# substitute in every text file (binary files are left alone); the slug is validated above, so it is sed-safe
while IFS= read -r -d '' f; do
  if LC_ALL=C grep -Iq . "$f" 2>/dev/null && grep -q '__PROJECT_SLUG__' "$f"; then
    sed "s/__PROJECT_SLUG__/$SLUG_IN/g" "$f" > "$f.tmp-slug" && cat "$f.tmp-slug" > "$f" && rm -f "$f.tmp-slug"
  fi
done < <(find "$TMP" -type f -print0)
if grep -rIl '__PROJECT_SLUG__' "$TMP" >/dev/null 2>&1; then echo "slug substitution incomplete"; exit 1; fi
mv "$TMP" "$DST"
trap - EXIT
echo "created $DST"
echo "next: 1) fill BRIEF.md, brand.md, MOTION.md and facts.json; set duration, sizes, fps, gates, delivery, variants and"
echo "         the audio route in shotspec.json (PRINT_CONFIG=1 bash build.sh shows what the build will read)"
echo "      2) references into references/, footage into footage/, data into data/, any supplied music into assets/music/"
echo "      3) open the project in Codex/Claude Code and say: use worldfilm on this brief"
echo "      tools/build.py and tools/sweep.mjs exit 2 until their placeholders are configured"
