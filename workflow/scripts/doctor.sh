#!/bin/bash
# doctor.sh — readiness check for the worldfilm studio. Usage: bash workflow/scripts/doctor.sh [--quick]
# Exit 0 when every required check passes; optional checks never fail the run.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
STUDIO="$ROOT/studio"
QUICK=0; [ "${1:-}" = "--quick" ] && QUICK=1
case ":$PATH:" in *":/opt/homebrew/bin:"*) ;; *) export PATH="/opt/homebrew/bin:$PATH" ;; esac   # homebrew first, then nvm in front of it
if [ -s "$HOME/.nvm/nvm.sh" ]; then . "$HOME/.nvm/nvm.sh" >/dev/null 2>&1; nvm use 22 >/dev/null 2>&1 || true; fi   # nvm prepends its node 22
export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_NO_UPDATE_CHECK=1
fail=0
ok()  { printf '  \033[32m✓\033[0m %-30s %s\n' "$1" "$2"; }
bad() { printf '  \033[31m✗\033[0m %-30s %s\n' "$1" "$2"; fail=1; }
opt() { printf '  \033[33m○\033[0m %-30s %s\n' "$1" "$2"; }

echo "worldfilm doctor — $ROOT"
echo "Required"
NV="$(node --version 2>/dev/null | sed 's/^v//')"; NMAJ="${NV%%.*}"
if [ -n "$NV" ] && [ "${NMAJ:-0}" -ge 22 ]; then ok "node >= 22" "v$NV ($(command -v node))"; else bad "node >= 22" "found '${NV:-none}' (source studio/env.sh)"; fi
for exe in npx ffmpeg ffprobe python3 git; do command -v "$exe" >/dev/null 2>&1 && ok "$exe" "$(command -v $exe)" || bad "$exe" "not on PATH"; done
FFV="$(ffmpeg -version 2>/dev/null | head -1 | awk '{print $3}')"; [ -n "$FFV" ] && ok "ffmpeg version" "$FFV (8.x tested)"
SSF=""; for c in "${SHOTSPEC_HOME:-}" "$STUDIO/kits/shotspec-film" "$HOME/.codex/skills/shotspec-film" "$HOME/.claude/skills/shotspec-film"; do
  if [ -n "$c" ] && [ -f "$c/scripts/run_gates.py" ] && [ -f "$c/schema/shotspec.schema.json" ]; then SSF="$c"; break; fi
done
[ -n "$SSF" ] && ok "shotspec-film" "$SSF (run_gates.py, base schema)" || bad "shotspec-film" "not found: set SHOTSPEC_HOME, link it at studio/kits/shotspec-film, or install the skill"
for f in SKILL.md schema/worldfilm.schema.json scripts/capture_subframes.mjs scripts/detect_pops.py scripts/synth_sfx.py; do [ -f "$ROOT/workflow/$f" ] && ok "workflow/$f" present || bad "workflow/$f" missing; done
for d in "$HOME/.codex/skills/worldfilm" "$HOME/.claude/skills/worldfilm"; do [ -e "$d/SKILL.md" ] && ok "skill link" "$d" || opt "skill link" "$d not installed (studio/install-skill.sh)"; done
for d in "$HOME/.codex/skills/shotspec-film" "$HOME/.claude/skills/shotspec-film"; do [ -e "$d/SKILL.md" ] && ok "shotspec-film (required)" "$d" || bad "shotspec-film (required)" "$d missing"; done
if [ -x "$STUDIO/node_modules/.bin/hyperframes" ]; then ok "hyperframes CLI" "$("$STUDIO/node_modules/.bin/hyperframes" --version 2>/dev/null | tail -1) (studio/node_modules)"; else bad "hyperframes CLI" "npm i hyperframes in studio/"; fi
if "$STUDIO/node_modules/.bin/hyperframes" render --help 2>/dev/null | grep -qi 'motion-blur'; then ok "blur route" "CLI exposes motion blur: use the engine route"; else opt "blur route" "CLI has no motion-blur flag: capture_subframes.mjs (Playwright) is the master route"; fi
if [ -d "$STUDIO/node_modules/playwright" ]; then ok "playwright" "studio/node_modules"; else bad "playwright" "npm i playwright && npx playwright install chromium (in studio/)"; fi
ls "$HOME/Library/Caches/ms-playwright" 2>/dev/null | grep -q chromium && ok "playwright chromium" "cached" || opt "playwright chromium" "npx playwright install chromium"
(ls "$HOME/.cache/hyperframes/chrome" >/dev/null 2>&1 || ls "$HOME/.cache/puppeteer" >/dev/null 2>&1) && ok "hyperframes chrome" "cached" || opt "hyperframes chrome" "first render downloads it"
if [ -x "$STUDIO/.venv/bin/python" ]; then
  ok "studio/.venv" "python $("$STUDIO/.venv/bin/python" -c 'import sys;print("%d.%d"%sys.version_info[:2])')"
  for mod in numpy scipy soundfile librosa jsonschema; do "$STUDIO/.venv/bin/python" -c "import $mod" 2>/dev/null && ok "  $mod" ok || bad "  $mod" "uv pip install $mod --python studio/.venv/bin/python"; done
  for mod in torch torchvision transformers cv2; do "$STUDIO/.venv/bin/python" -c "import $mod" 2>/dev/null && ok "  $mod (SAM)" ok || opt "  $mod (SAM)" "needed only for sam_separate.py"; done
else bad "studio/.venv" "uv venv --python 3.13 studio/.venv"; fi
ls "$HOME/.cache/huggingface/hub" 2>/dev/null | grep -q sam2.1 && ok "SAM 2.1 weights" "cached in ~/.cache/huggingface" || opt "SAM 2.1 weights" "first sam_separate.py run downloads them (156-898 MB)"
command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1 && ok "docker" "running (pixel-stable masters)" || opt "docker" "not running (needed for --docker masters)"
command -v claude >/dev/null 2>&1 && ok "claude CLI (critics)" "$(claude --version 2>/dev/null | head -1)" || opt "claude CLI (critics)" "fresh critics need claude -p or codex exec"
echo "Gate runner"
# run_gates.py splits --hyperframes-cmd on whitespace: a path with a space in it is "executable not found" and the
# contrast gate SKIPs (Block Space ran a whole Gauntlet that way). The command must be "npx hyperframes", never a path.
case "$STUDIO" in *" "*) opt "studio path has a space" "never pass \$HF or a path to run_gates --hyperframes-cmd";; esac
hfbad=0
for b in "$STUDIO"/projects/*/build.sh; do
  [ -f "$b" ] || continue
  if grep -q -- '--hyperframes-cmd' "$b" && grep -- '--hyperframes-cmd' "$b" | grep -v '^ *#' | grep -qv -- '--hyperframes-cmd "npx hyperframes"'; then
    bad "run_gates command" "$b passes something other than \"npx hyperframes\" to --hyperframes-cmd"; hfbad=1
  fi
  if grep -q -- 'run_gates.py' "$b" && ! grep -q -- 'check_gate_report.py' "$b"; then
    bad "gate-report reader" "$b runs run_gates.py without check_gate_report.py (a SKIP would read as green)"; hfbad=1
  fi
done
[ "$hfbad" -eq 0 ] && ok "run_gates command" "every build.sh passes \"npx hyperframes\" and reads the report with check_gate_report.py"
if (cd "$STUDIO" && npx --no-install hyperframes --version >/dev/null 2>&1); then ok "npx hyperframes" "resolves from studio/node_modules"; else bad "npx hyperframes" "does not resolve: npm i hyperframes in studio/"; fi
if [ "$QUICK" -eq 0 ]; then
  echo "Self-tests"
  PY="$STUDIO/.venv/bin/python"; [ -x "$PY" ] || PY=python3
  if (cd "$ROOT/workflow/tests" && "$PY" synth_clips.py >/dev/null 2>&1 && cd out && "$PY" "$HERE/detect_pops.py" pop.mp4 --out gates/pops.json >/dev/null 2>&1; [ $? -eq 1 ]) && (cd "$ROOT/workflow/tests/out" && "$PY" "$HERE/loop_seam.py" loop-good.mp4 --out gates/loop-good.json >/dev/null 2>&1) && ! (cd "$ROOT/workflow/tests/out" && "$PY" "$HERE/loop_seam.py" loop-seam.mp4 --out gates/loop-seam.json >/dev/null 2>&1); then ok "gate self-test" "pops catches the flash+pop, loop_seam separates good/bad"; else bad "gate self-test" "see workflow/tests/README.md"; fi
  if (cd "$ROOT/workflow" && node tests/sweep_lib_test.mjs >/dev/null 2>&1); then ok "sweep self-test" "every sweep check catches its defect"; else bad "sweep self-test" "node workflow/tests/sweep_lib_test.mjs"; fi
  if (cd "$ROOT/workflow/tests" && "$PY" synth_clips.py >/dev/null 2>&1 && cd out && "$PY" "$HERE/check_gate_report.py" ../fixtures/gate-report-skip.json --quiet >/dev/null 2>&1; [ $? -eq 1 ]) && (cd "$ROOT/workflow/tests/out" && "$PY" "$HERE/check_gate_report.py" ../fixtures/gate-report-margin.json --allow-skip handoff,swatch --quiet >/dev/null 2>&1); then ok "gate-report self-test" "a SKIP is not a pass; two samples of frozen margin pass"; else bad "gate-report self-test" "see workflow/tests/README.md"; fi
fi
[ "$fail" -eq 0 ] && echo "READY — every required check passed." || echo "NOT READY — fix the ✗ items above."
exit $fail
