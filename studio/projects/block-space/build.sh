#!/bin/bash
# build.sh — rebuild "Block Space" from its sources to the delivered masters, in the worldfilm order (stages 2-9).
# Usage: bash build.sh            full build: Docker masters twice (pinned Chrome) + framemd5 compare, blur master, every variant
#        DRAFT=1 bash build.sh    one fast local render, all gates, no blur / Docker
# Needs studio/env.sh sourced (Node 22, studio/.venv, ffmpeg) and Docker for the full build. Every step that can fail
# fails the build: a skipped gate is not a passed gate (check_gate_report.py), and the sweep must be configured.
set -euo pipefail
cd "$(dirname "$0")"
STUDIO="$(cd ../.. && pwd)"
PY="$STUDIO/.venv/bin/python"
WF="$STUDIO/worldfilm/scripts"
SS="${SHOTSPEC_HOME:-$STUDIO/kits/shotspec-film}/scripts"; [ -f "$SS/run_gates.py" ] || SS="$HOME/.codex/skills/shotspec-film/scripts"   # shotspec-film (required)
HF="$STUDIO/node_modules/.bin/hyperframes"          # for lint / check / render only. run_gates gets "npx hyperframes" (never a path: a space in it splits)
export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_NO_UPDATE_CHECK=1

# ---- fill these once (stage 0-5) ----
SLUG="block-space"
DURATION=30                                            # seconds (also in shotspec.json project.duration)
CTA_TAIL=3.0                                           # final seconds excluded from frozen_time as the end card
SILENCE="25.0,27.0"                                    # the exact digital-silence window(s) from audio/cues.json, or "" when none
ALLOW_SKIP="handoff,swatch"                            # gates the spec legitimately cannot feed (write the reason in GAUNTLET.jsonl)
HARD_CUTS=""                                           # e.g. "9.0,13.0" so the shutter never crosses a cut
POSTER_T=18.3                                          # the poster frame (a signature moment)
VARIANTS="vertical:compositions/vertical.html:1080x1920"   # id:composition:WxH per extra aspect, space-separated; "" when none

gate() {  # gate <video> <out-dir>: run_gates + the reader + pops + luma, on THIS render (variants never inherit the 16:9 pass)
  python3 "$SS/run_gates.py" --spec shotspec.json --video "$1" --composition-dir . --out "$2" --cta-tail-s "$CTA_TAIL" --hyperframes-cmd "npx hyperframes" | tail -1
  "$PY" "$WF/check_gate_report.py" "$2/gate-report.json" --allow-skip "$ALLOW_SKIP" --frozen-margin-samples 2
  "$PY" "$WF/detect_pops.py" "$1" ${HARD_CUTS:+--cuts "$HARD_CUTS"} --out "$2/pops.json" | head -1
  "$PY" "$WF/luma_floor.py" "$1" --min 35 --out "$2/luma.json" | head -1
}
mux() { ffmpeg -v error -y -i "$1" -i "$2" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 320k -ar 48000 -movflags +faststart -shortest "$3"; }

# stage 2-3: one source of truth -> data, facts, spec, browser constants; the spec validates; static gates
python3 tools/build.py
"$PY" "$WF/validate_spec.py" shotspec.json
python3 "$SS/run_gates.py" --spec shotspec.json --static --out gates/static | tail -1
# stage 6-7: the sweep (every displayed number recomputed independently, labels clear their targets, framing targets settle)
node tools/sweep.mjs
# stage 8: the cue sheet from the event table; the mix and its stems; audibility; the music-only export mastered on its own
python3 audio/make_cues.py && "$PY" "$WF/synth_sfx.py" audio/cues.json --out assets/mix.wav --stems assets/stems --report gates/audio-synth.json
"$PY" "$WF/prove_audible.py" --mix assets/mix.wav --cues gates/audio-synth.json --bed assets/stems/score.wav ${SILENCE:+--silence "$SILENCE"} --out gates/audible-mix.json | head -1
"$PY" "$WF/synth_sfx.py" --master-stem assets/stems/score.wav --out assets/music-only.wav --report gates/music-only-master.json   # a stem carries the mix's gain: alone it is under the target
"$HF" lint && "$HF" check --json > gates/hyperframes-check.json
if [ "${DRAFT:-0}" = "1" ]; then
  "$HF" render --quality draft --output renders/draft.mp4
  V=renders/draft.mp4; OUT=gates/draft
else
  # stage 9: the sharp picture twice in Docker (pinned Chrome, software GL): decoded frames must be identical
  "$HF" render --docker --quality high --output renders/picture-a.mp4
  "$HF" render --docker --quality high --output renders/picture-b.mp4
  "$PY" "$WF/frame_hash.py" renders/picture-a.mp4 --out gates/master/hashes-a.json
  "$PY" "$WF/frame_hash.py" renders/picture-b.mp4 --out gates/master/hashes-b.json
  "$PY" "$WF/frame_hash.py" --compare gates/master/hashes-a.json gates/master/hashes-b.json --out gates/master/hash-compare.json
  # the blur master: 4 samples over a 180 degree shutter, never across a cut (Playwright route until the CLI exposes motionBlur)
  node "$WF/capture_subframes.mjs" --dir . --out renders/picture-blur.mp4 --fps 60 --duration "$DURATION" --width 1920 --height 1080 --samples 4 --shutter 180 ${HARD_CUTS:+--cuts "$HARD_CUTS"} --format png --crf 16
  V=renders/picture-blur.mp4; OUT=gates/master
fi
# masters: the picture with the full mix, and with the score only (mastered to the same target); poster; SRT
mux "$V" assets/mix.wav "renders/$SLUG-1080p60.mp4"
mux "$V" assets/music-only.wav "renders/$SLUG-1080p60-music-only.mp4"
ffmpeg -v error -y -ss "$POSTER_T" -i "renders/$SLUG-1080p60.mp4" -frames:v 1 renders/poster.png
python3 tools/srt.py "renders/$SLUG.srt"
for M in "$SLUG-1080p60" "$SLUG-1080p60-music-only"; do gate "renders/$M.mp4" "$OUT-$M"; done
"$PY" "$WF/prove_audible.py" --mix "renders/$SLUG-1080p60.mp4" --cues gates/audio-synth.json --bed assets/stems/score.wav ${SILENCE:+--silence "$SILENCE"} --out "$OUT-$SLUG-1080p60/audible.json" | head -1
# every other aspect is its own film at the gates: its own render, its own pops / luma / run_gates
if [ "${DRAFT:-0}" != "1" ]; then
  for VAR in $VARIANTS; do
    ID="${VAR%%:*}"; REST="${VAR#*:}"; COMP="${REST%%:*}"; SIZE="${REST#*:}"
    "$HF" render --docker --quality high -c "$COMP" --output "renders/picture-$ID.mp4"
    mux "renders/picture-$ID.mp4" assets/mix.wav "renders/$SLUG-$SIZE.mp4"
    gate "renders/$SLUG-$SIZE.mp4" "gates/master-$SLUG-$SIZE"
  done
fi
echo "done: renders/  (now: a human listens; critics judge; PROGRESS.md and GAUNTLET.jsonl are updated)"

