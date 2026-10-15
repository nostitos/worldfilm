#!/usr/bin/env python3
"""audio/make_cues.py — the synthesized cue sheet for __PROJECT_SLUG__, generated from the event table in film/data.js so
the sound is locked to the picture's events (worldfilm stage 8). build.sh runs it only when shotspec.json sets
audio.cue_sheet; it writes that path for synth_sfx.py (run synth_sfx.py --list for the generators).

Guidance: each sfx cue names the event it sits on (the audible gate checks its in-band lift in the delivered file);
motion cues sit on camera velocity peaks (shots[].camera.velocity_peak_s) with align "peak". Optional silence
windows come from shotspec.json audio.silence (one source). Any music-only export is mastered separately
(synth_sfx.py --master-stem, driven by audio.music_only). Exits 2 while nothing is configured.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
spec = json.load(open(os.path.join(ROOT, "shotspec.json")))
audio = spec.get("audio") or {}
src = open(os.path.join(ROOT, "film", "data.js")).read()
DATA = json.loads(re.search(r"export const DATA = (\{.*\});", src, re.S).group(1))
EV = {e["id"]: e for e in DATA["events"]}

cues = []
score = lambda **k: cues.append(dict(group="score", **k))
sfx = lambda **k: cues.append(dict(group="sfx", **k))

# the bed (optional): a synthesized score, or None when the film has no bed
pad = None   # e.g. {"group": "score", "gain": 0.3, "chords": [[0.0, [freqs...]]], "volume": [[0, 0.0], [0.6, 0.5], ...]}

# cues on events: one per event the picture makes audible, e.g.
# for e in DATA["events"]:
#     if e["kind"] == "reveal": sfx(id="hit-" + e["id"], t=e["t"], gen="kick", args={...}, gain=0.8, event=e["id"], audibility_db=4)

if not cues and pad is None:
    print("make_cues: no cues and no bed configured (edit audio/make_cues.py, or remove audio.cue_sheet from shotspec.json for a picture-only film)")
    sys.exit(2)
qb = spec["project"].get("quality_bar") or {}
sheet = {"duration": DATA["dur"], "seed": DATA.get("world_seed", 1), "target_lufs": qb.get("lufs_target", -14.0),
         "ceiling_db": -2.0, "fade_out": 0.4, "silence": audio.get("silence") or [], "cues": cues}
if pad is not None:
    sheet["pad"] = pad
out = os.path.join(ROOT, audio.get("cue_sheet") or "audio/cues.json")
json.dump(sheet, open(out, "w"), indent=1)
print("%s: %d cues, silence %s" % (os.path.relpath(out, ROOT), len(cues), sheet["silence"]))
