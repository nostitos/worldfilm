#!/bin/bash
# build.sh — rebuild __PROJECT_SLUG__ from its sources to the delivered masters, in the worldfilm order (stages 2-9).
# Every setting comes from shotspec.json: project.fps / duration / sizes[0] (the primary master), project.gates (gate
# options and limits), project.blur, project.delivery, project.variants, audio. Nothing film-specific is set here.
#
# Usage: bash build.sh                     full build: Docker master (twice + frame-hash compare when gates.frame_hash_ab),
#                                          blur master per project.blur.route, variants with deliver: true
#        DRAFT=1 bash build.sh             one fast local render of the primary composition through the same gates
#        VARIANTS=all|id,id bash build.sh  render these variants as well (default: only those with deliver: true)
#        PRINT_CONFIG=1 bash build.sh      print the settings read from shotspec.json and exit
# Needs studio/env.sh sourced (Node 22, studio/.venv, ffmpeg) and Docker for the full build. Every step that can fail
# fails the build: a skipped gate is not a passed gate (check_gate_report.py), and the sweep must be configured.
set -euo pipefail
cd "$(dirname "$0")"
STUDIO="$(cd ../.. && pwd)"
PY="$STUDIO/.venv/bin/python"; [ -x "$PY" ] || PY=python3
WF="$STUDIO/worldfilm/scripts"
SS="${SHOTSPEC_HOME:-$STUDIO/kits/shotspec-film}/scripts"; [ -f "$SS/run_gates.py" ] || SS="$HOME/.codex/skills/shotspec-film/scripts"   # shotspec-film (required)
HF="$STUDIO/node_modules/.bin/hyperframes"   # lint / check / render only. run_gates always gets the literal "npx hyperframes" (a path would split on spaces)
export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_NO_UPDATE_CHECK=1
SLUG="__PROJECT_SLUG__"

# ---- settings, read from shotspec.json (shell-quoted). The parse is assigned before eval so a bad spec or an
# unknown VARIANTS id stops the build. Real builds read it after tools/build.py has regenerated shotspec.json.
load_config() {
  local CONFIG
  CONFIG="$("$PY" - <<'EOF_CFG'
import json, os, shlex, sys
s = json.load(open("shotspec.json"))
p, a = s["project"], s.get("audio") or {}
g, d, b = p.get("gates") or {}, p.get("delivery") or {}, p.get("blur") or {}
if g.get("hyperframes_cmd", "npx hyperframes") != "npx hyperframes":
    sys.exit("shotspec.json: project.gates.hyperframes_cmd must be 'npx hyperframes'")
size = p["sizes"][0]
lst = lambda xs: ",".join(str(x) for x in xs or [])
mo = a.get("music_only") or {}
want = os.environ.get("VARIANTS", "")
pick = set(want.split(",")) if want and want != "all" else set()
variants = [v for v in p.get("variants") or [] if want == "all" or v.get("deliver") or v["id"] in pick]
unknown = pick - {v["id"] for v in p.get("variants") or []}
if unknown:
    sys.exit("VARIANTS names unknown variant ids: %s" % ", ".join(sorted(unknown)))
cfg = {
    "FPS": p["fps"], "DURATION": p["duration"], "WIDTH": size["w"], "HEIGHT": size["h"],
    "CTA_TAIL": g.get("cta_tail_s", ""), "ALLOW_SKIP": lst(g.get("allow_skip")), "REQUIRE": lst(g.get("require")),
    "FROZEN_MARGIN": g.get("frozen_margin_samples", 2), "HARD_CUTS": lst(g.get("hard_cuts_s")), "POPS_ALLOW": lst(g.get("pops_allow_s")),
    "LUMA_MIN": g.get("luma_min", 35), "LUMA_WINDOW": g.get("luma_window_s", ""), "LUMA_TAIL": g.get("luma_tail_s", ""),
    "LOOP_SEAM": int(bool(g.get("loop_seam", False))), "FRAME_HASH_AB": int(bool(g.get("frame_hash_ab", True))),
    "POSTER_T": d.get("poster_t", ""), "SRT": int(bool(d.get("srt", True))),
    "BLUR_ROUTE": b.get("route", "playwright"), "BLUR_SAMPLES": b.get("samples_per_frame", 4),
    "BLUR_SHUTTER": b.get("shutter_angle", 180), "BLUR_PHASE": b.get("shutter_phase", -90),
    "CUE_SHEET": a.get("cue_sheet", ""), "SPEC_CUES": int(bool(a.get("cues"))), "MUSIC_SRC": (p.get("music") or {}).get("src", ""),
    "SILENCE": ";".join("%s,%s" % (w[0], w[1]) for w in a.get("silence") or []),
    "MO_STEM": mo.get("stem", ""), "MO_OUT": mo.get("out", "assets/music-only.wav"), "MO_REPORT": mo.get("report", "gates/music-only-master.json"),
    "LUFS_TARGET": (p.get("quality_bar") or {}).get("lufs_target", -14),
    "VARIANT_LIST": " ".join("%s:%s:%dx%d" % (v["id"], v["composition"], v["width"], v["height"]) for v in variants),
}
for k, v in cfg.items():
    print("%s=%s" % (k, shlex.quote(str(v))))
EOF_CFG
)"
  eval "$CONFIG"
}
if [ "${PRINT_CONFIG:-0}" = "1" ]; then   # inspect the settings of the current shotspec.json without building
  load_config
  for k in FPS DURATION WIDTH HEIGHT CTA_TAIL ALLOW_SKIP REQUIRE FROZEN_MARGIN HARD_CUTS POPS_ALLOW LUMA_MIN LUMA_WINDOW LUMA_TAIL LOOP_SEAM FRAME_HASH_AB POSTER_T SRT BLUR_ROUTE BLUR_SAMPLES BLUR_SHUTTER BLUR_PHASE CUE_SHEET SPEC_CUES MUSIC_SRC SILENCE MO_STEM MO_OUT MO_REPORT LUFS_TARGET VARIANT_LIST; do
    printf '%s=%s\n' "$k" "${!k}"
  done
  exit 0
fi

quiet() {  # quiet <log> <cmd...>: keep the full output in <log>, print its first line, fail with the whole log on error
  local log="$1"; shift
  mkdir -p "$(dirname "$log")"
  if "$@" > "$log" 2>&1; then head -n 1 "$log"; else cat "$log"; return 1; fi
}
gate() {  # gate <video> <out-dir>: run_gates + the reader + pops + luma (+ loop seam), on THIS render only
  mkdir -p "$2"
  quiet "$2/run_gates.log" python3 "$SS/run_gates.py" --spec shotspec.json --video "$1" --composition-dir . --out "$2" \
    --hyperframes-cmd "npx hyperframes" ${CTA_TAIL:+--cta-tail-s "$CTA_TAIL"}
  "$PY" "$WF/check_gate_report.py" "$2/gate-report.json" --allow-skip "$ALLOW_SKIP" --frozen-margin-samples "$FROZEN_MARGIN" ${REQUIRE:+--require "$REQUIRE"}
  quiet "$2/pops.log" "$PY" "$WF/detect_pops.py" "$1" ${HARD_CUTS:+--cuts "$HARD_CUTS"} ${POPS_ALLOW:+--allow "$POPS_ALLOW"} --out "$2/pops.json"
  quiet "$2/luma.log" "$PY" "$WF/luma_floor.py" "$1" --min "$LUMA_MIN" ${LUMA_WINDOW:+--window "$LUMA_WINDOW"} ${LUMA_TAIL:+--tail "$LUMA_TAIL"} --out "$2/luma.json"
  if [ "$LOOP_SEAM" = "1" ]; then quiet "$2/loop-seam.log" "$PY" "$WF/loop_seam.py" "$1" --out "$2/loop-seam.json"; fi
}
deliver() {  # deliver <picture> <audio or ""> <out.mp4>: mux when there is audio, else copy the picture
  if [ -n "$2" ]; then
    ffmpeg -v error -y -i "$1" -i "$2" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 320k -ar 48000 -movflags +faststart -shortest "$3"
  else
    ffmpeg -v error -y -i "$1" -map 0:v:0 -c:v copy -an -movflags +faststart "$3"
  fi
}
mkdir -p gates renders assets

# stage 2-3: one source of truth -> data, facts, spec, browser constants; then the settings; the spec validates; static gates
python3 tools/build.py
load_config
PRIMARY="$SLUG-${WIDTH}x${HEIGHT}"
"$PY" "$WF/validate_spec.py" shotspec.json
quiet gates/static/run_gates.log python3 "$SS/run_gates.py" --spec shotspec.json --static --out gates/static --hyperframes-cmd "npx hyperframes"
# stage 6-7: the sweep (displayed values recomputed independently, labels clear their targets, framing targets settle)
node tools/sweep.mjs

# stage 8: audio, by the route shotspec.json declares (audio.cue_sheet = synthesized; project.music.src = supplied; neither = picture only)
MIX=""; BED=""
if [ -n "$CUE_SHEET" ]; then
  python3 audio/make_cues.py
  "$PY" "$WF/synth_sfx.py" "$CUE_SHEET" --out assets/mix.wav --stems assets/stems --report gates/audio-synth.json
  MIX=assets/mix.wav; CUES=gates/audio-synth.json
  [ -f assets/stems/score.wav ] && BED=assets/stems/score.wav
elif [ -n "$MUSIC_SRC" ]; then
  [ -f "$MUSIC_SRC" ] || { echo "project.music.src $MUSIC_SRC does not exist"; exit 1; }
  MIX="$MUSIC_SRC"; CUES=""
  if [ "$SPEC_CUES" = "1" ]; then   # cues declared in the spec are proven against the supplied track
    "$PY" -c 'import json; json.dump(json.load(open("shotspec.json"))["audio"]["cues"], open("gates/audio-cues.json", "w"), indent=1)'
    CUES=gates/audio-cues.json
  fi
else
  echo "audio: none configured (picture-only masters)"
  CUES=""
fi
if [ -n "$MIX" ] && [ -n "$CUES" ]; then
  quiet gates/audible-mix.log "$PY" "$WF/prove_audible.py" --mix "$MIX" --cues "$CUES" ${BED:+--bed "$BED"} ${SILENCE:+--silence "$SILENCE"} --out gates/audible-mix.json
fi
MUSIC_ONLY=""
if [ -n "$MO_STEM" ]; then   # a stem carries the mix's gain: alone it reads under the target, so it is mastered on its own
  "$PY" "$WF/synth_sfx.py" --master-stem "$MO_STEM" --out "$MO_OUT" --report "$MO_REPORT" --target-lufs "$LUFS_TARGET"
  MUSIC_ONLY="$MO_OUT"
fi

"$HF" lint && "$HF" check --json > gates/hyperframes-check.json
if [ "${DRAFT:-0}" = "1" ]; then
  "$HF" render --quality draft --fps "$FPS" --output renders/draft.mp4
  V=renders/draft.mp4; OUT=gates/draft
else
  # stage 9: the sharp picture in Docker (pinned Chrome, software GL); twice + decoded frame-hash compare when configured
  mkdir -p gates/master
  "$HF" render --docker --quality high --fps "$FPS" --output renders/picture-a.mp4
  if [ "$FRAME_HASH_AB" = "1" ]; then
    "$HF" render --docker --quality high --fps "$FPS" --output renders/picture-b.mp4
    "$PY" "$WF/frame_hash.py" renders/picture-a.mp4 --out gates/master/hashes-a.json
    "$PY" "$WF/frame_hash.py" renders/picture-b.mp4 --out gates/master/hashes-b.json
    "$PY" "$WF/frame_hash.py" --compare gates/master/hashes-a.json gates/master/hashes-b.json --out gates/master/hash-compare.json
  fi
  case "$BLUR_ROUTE" in
    playwright)   # sub-frame blur from project.blur; samples never cross a declared hard cut
      node "$WF/capture_subframes.mjs" --dir . --out renders/picture-blur.mp4 --fps "$FPS" --duration "$DURATION" --width "$WIDTH" --height "$HEIGHT" \
        --samples "$BLUR_SAMPLES" --shutter "$BLUR_SHUTTER" --phase "$BLUR_PHASE" ${HARD_CUTS:+--cuts "$HARD_CUTS"} --format png --crf 16
      V=renders/picture-blur.mp4 ;;
    none) V=renders/picture-a.mp4 ;;
    *) echo "project.blur.route '$BLUR_ROUTE' is not available to this build (use playwright or none)"; exit 1 ;;
  esac
  OUT=gates/master
fi

# masters: the primary picture with its audio (and the music-only export when configured); poster; SRT
deliver "$V" "$MIX" "renders/$PRIMARY.mp4"
MASTERS="$PRIMARY"
if [ -n "$MUSIC_ONLY" ]; then deliver "$V" "$MUSIC_ONLY" "renders/$PRIMARY-music-only.mp4"; MASTERS="$MASTERS $PRIMARY-music-only"; fi
if [ -n "$POSTER_T" ]; then ffmpeg -v error -y -ss "$POSTER_T" -i "renders/$PRIMARY.mp4" -frames:v 1 renders/poster.png; else echo "poster: skipped (project.delivery.poster_t not set)"; fi
if [ "$SRT" = "1" ]; then python3 tools/srt.py "renders/$SLUG.srt"; fi
for M in $MASTERS; do gate "renders/$M.mp4" "$OUT-$M"; done
if [ -n "$MIX" ] && [ -n "$CUES" ]; then
  quiet "$OUT-$PRIMARY/audible.log" "$PY" "$WF/prove_audible.py" --mix "renders/$PRIMARY.mp4" --cues "$CUES" ${BED:+--bed "$BED"} ${SILENCE:+--silence "$SILENCE"} --out "$OUT-$PRIMARY/audible.json"
fi

# selected variants: each is its own film at the gates (own render, own pops / luma / run_gates); drafts skip them
if [ "${DRAFT:-0}" != "1" ]; then
  for VAR in $VARIANT_LIST; do
    ID="${VAR%%:*}"; REST="${VAR#*:}"; COMP="${REST%%:*}"; SIZE="${REST#*:}"
    "$HF" render --docker --quality high --fps "$FPS" -c "$COMP" --output "renders/picture-$ID.mp4"
    deliver "renders/picture-$ID.mp4" "$MIX" "renders/$SLUG-$ID-$SIZE.mp4"
    gate "renders/$SLUG-$ID-$SIZE.mp4" "gates/master-$SLUG-$ID-$SIZE"
  done
fi
echo "done: renders/  (next: a person reviews picture and sound; critics judge; update PROGRESS.md and GAUNTLET.jsonl)"
