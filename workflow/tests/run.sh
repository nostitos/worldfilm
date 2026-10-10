#!/bin/bash
# tests/run.sh — validate the worldfilm skill the way code is validated: every check must catch its known defect and
# stay quiet on clean input. Usage: bash workflow/tests/run.sh [--full]   (--full adds the Playwright blur A/B, ~2 min)
# Exit 0 when every expectation holds. Writes into tests/out/ (ignored by git).
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
SC="$ROOT/workflow/scripts"
STUDIO="$ROOT/studio"
PY="$STUDIO/.venv/bin/python"; [ -x "$PY" ] || PY=python3
case ":$PATH:" in *":/opt/homebrew/bin:"*) ;; *) export PATH="/opt/homebrew/bin:$PATH" ;; esac   # homebrew first, then nvm in front of it
if [ -s "$HOME/.nvm/nvm.sh" ]; then . "$HOME/.nvm/nvm.sh" >/dev/null 2>&1; nvm use 22 >/dev/null 2>&1 || true; fi   # nvm prepends its node 22
export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_NO_UPDATE_CHECK=1
FULL=0; [ "${1:-}" = "--full" ] && FULL=1
pass=0; fail=0
ok()  { printf '  \033[32mok\033[0m   %s\n' "$1"; pass=$((pass+1)); }
bad() { printf '  \033[31mFAIL\033[0m %s\n' "$1"; fail=$((fail+1)); }
want() {  # want <expected exit> <name> <cmd...>
  local exp="$1" name="$2"; shift 2
  "$@" >/dev/null 2>&1; local rc=$?
  if [ "$rc" -eq "$exp" ]; then ok "$name (exit $rc)"; else bad "$name (exit $rc, wanted $exp)"; fi
}
cd "$HERE" && mkdir -p out out/gates
echo "worldfilm tests — $ROOT"
echo "synthetic clips"
"$PY" synth_clips.py --out out >/dev/null 2>&1 && ok "synth_clips.py wrote out/*.mp4" || bad "synth_clips.py"
cd out
echo "gates"
want 1 "detect_pops fails on a one-frame flash + a 40 px jump (cut at 2.0 s excluded)" "$PY" "$SC/detect_pops.py" pop.mp4 --cuts 2.0 --out gates/pops.json
want 0 "loop_seam passes a closed loop"           "$PY" "$SC/loop_seam.py" loop-good.mp4 --out gates/loop-good.json
want 1 "loop_seam fails a 4 px seam"              "$PY" "$SC/loop_seam.py" loop-seam.mp4 --out gates/loop-seam.json
"$PY" "$SC/frame_hash.py" base.mp4 --out gates/h-base.json >/dev/null 2>&1; "$PY" "$SC/frame_hash.py" base-copy.mp4 --out gates/h-copy.json >/dev/null 2>&1; "$PY" "$SC/frame_hash.py" eased.mp4 --out gates/h-eased.json >/dev/null 2>&1
want 0 "frame_hash: an identical re-render hashes identical"   "$PY" "$SC/frame_hash.py" --compare gates/h-base.json gates/h-copy.json --out gates/h-cmp-copy.json
want 1 "frame_hash: one easing change flags the exact frames"  "$PY" "$SC/frame_hash.py" --compare gates/h-base.json gates/h-eased.json --out gates/h-cmp-eased.json
echo "gate reader"
want 1 "check_gate_report: a skipped contrast gate is not a pass"      "$PY" "$SC/check_gate_report.py" ../fixtures/gate-report-skip.json --allow-skip handoff,swatch --quiet
want 0 "check_gate_report: two samples of frozen margin pass"           "$PY" "$SC/check_gate_report.py" ../fixtures/gate-report-margin.json --allow-skip handoff,swatch --quiet
want 1 "check_gate_report: an unallowed skip (handoff) is not a pass"   "$PY" "$SC/check_gate_report.py" ../fixtures/gate-report-margin.json --quiet
echo "sweep"
want 0 "sweep_lib: every check catches its defect (14 expectations)"    node ../sweep_lib_test.mjs
want 0 "place_label: the shared placement rule takes the right side, holds at the hold line (9 expectations)" node ../place_label_test.mjs
want 0 "sweep_lib on Block Space's pure functions: 0 violations"       node ../sweep_blockspace.mjs
want 2 "sweep template exits 2 in a project with no film yet"          node "$STUDIO/projects/_template/tools/sweep.mjs"
echo "sound"
cat > gates/quiet.json <<'EOF2'
{"duration": 4.0, "seed": 3, "target_lufs": -14.0, "ceiling_db": -2.0, "fade_out": 0.2, "silence": [[3.0, 3.5]],
 "pad": {"group": "score", "gain": 0.4, "chords": [[0.0, [110, 164.81, 220]]], "volume": [[0, 0.6], [2.9, 0.6], [3.0, 0.0]]},
 "cues": [{"id": "pop-quiet", "t": 1.5, "gen": "pop", "gain": 0.02, "group": "sfx", "align": "peak"}]}
EOF2
sed 's/"gain": 0.02/"gain": 0.9/; s/pop-quiet/pop-loud/' gates/quiet.json > gates/loud.json
"$PY" "$SC/synth_sfx.py" gates/quiet.json --out gates/quiet.wav --stems gates/quiet-stems --report gates/quiet-synth.json >/dev/null 2>&1
"$PY" "$SC/synth_sfx.py" gates/loud.json --out gates/loud.wav --stems gates/loud-stems --report gates/loud-synth.json >/dev/null 2>&1
want 1 "prove_audible fails a cue 20 dB under the bed"       "$PY" "$SC/prove_audible.py" --mix gates/quiet.wav --cues gates/quiet-synth.json --bed gates/quiet-stems/score.wav --silence 3.0,3.5 --out gates/quiet-audible.json
want 0 "prove_audible passes the same cue in-band above the bed; silence window is zeros" "$PY" "$SC/prove_audible.py" --mix gates/loud.wav --cues gates/loud-synth.json --bed gates/loud-stems/score.wav --silence 3.0,3.5 --out gates/loud-audible.json
"$PY" "$SC/synth_sfx.py" --master-stem gates/loud-stems/score.wav --out gates/music-only.wav --report gates/music-only.json >/dev/null 2>&1
if "$PY" - <<'EOF3'
import json; r = json.load(open("gates/music-only.json")); assert r["lufs"] > r["source_lufs"] and abs(r["lufs"] - (-14.0)) <= 1.5 and r["peak_db"] <= -1.99, r
EOF3
then ok "--master-stem lifts a stem to -14 +-1.5 LUFS under the -2 dBTP ceiling"; else bad "--master-stem"; fi
echo "spec"
want 0 "validate_spec: the template spec is valid against the updated schema"   "$PY" "$SC/validate_spec.py" "$STUDIO/projects/_template/shotspec.json"
want 0 "validate_spec: the Block Space spec is valid against the updated schema" "$PY" "$SC/validate_spec.py" "$STUDIO/projects/block-space/shotspec.json"
TPL_SPEC="$STUDIO/projects/_template/shotspec.json" "$PY" - <<'EOF4' > gates/bad-spec.json
import json, os; s = json.load(open(os.environ["TPL_SPEC"]))
s["project"]["gates"]["hyperframes_cmd"] = "/opt/some path/hyperframes"; s["project"]["camera"]["rest_drift"]["vertical_units"] = 0
s["audio"]["silence"] = [[27.0, 25.0]]; print(json.dumps(s))
EOF4
want 1 "validate_spec rejects a path as the gate runner, a one-axis drift and a reversed silence window" "$PY" "$SC/validate_spec.py" gates/bad-spec.json
if [ "$FULL" -eq 1 ]; then
  echo "blur A/B (Playwright)"
  node "$SC/capture_subframes.mjs" --dir ../blur-page --out blur-sharp.mp4 --fps 30 --duration 2 --width 640 --height 360 --samples 1 --cuts 0.97 >/dev/null 2>&1
  node "$SC/capture_subframes.mjs" --dir ../blur-page --out blur-4.mp4 --fps 30 --duration 2 --width 640 --height 360 --samples 4 --shutter 180 --cuts 0.97 >/dev/null 2>&1
  want 0 "blur_ab: 4 samples soften moving frames and never leak across the cut" "$PY" ../blur_ab.py blur-sharp.mp4 blur-4.mp4 --cut 0.97
fi
echo "tests: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
