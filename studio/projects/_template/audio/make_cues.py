#!/usr/bin/env python3
"""audio/make_cues.py — the cue sheet for __PROJECT_SLUG__, generated from the event table in film/data.js so the
sound is locked to the picture's events (worldfilm stage 8). Writes audio/cues.json for synth_sfx.py.

Rules the sheet must honour: every sfx cue names the event it sits on (the audible gate checks its in-band lift in
the delivered file); whooshes sit on camera velocity peaks (shots[].camera.velocity_peak_s) with align "peak";
one riser and one impact per film; the silence window precedes the loudest moment and is written here AND in
shotspec.json audio.silence; the music-only export is mastered separately (synth_sfx.py --master-stem).
Worked example: studio/projects/block-space/audio/make_cues.py.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
src = open(os.path.join(ROOT, "film", "data.js")).read()
DATA = json.loads(re.search(r"export const DATA = (\{.*\});", src, re.S).group(1))
EV = {e["id"]: e for e in DATA["events"]}

cues = []
score = lambda **k: cues.append(dict(group="score", **k))
sfx = lambda **k: cues.append(dict(group="sfx", **k))

# the bed: chords per section (TODO), ducked under every hit so the hit is heard; gone before the silence
A2, E3, A3, C4 = 110.0, 164.81, 220.0, 261.63
pad = {"group": "score", "gain": 0.3, "chords": [[0.0, [A2, E3, A3, C4]]], "volume": [[0, 0.0], [0.6, 0.5], [DATA["dur"] - 3.0, 0.5], [DATA["dur"] - 2.0, 0.0]]}

# cues on events (TODO): one per event that the picture makes visible
sfx(id="whoosh-open", t=EV["open"]["t"] + 0.3, gen="whoosh", args={"dur": 0.8, "f0": 240, "f1": 2600, "peak": 0.5}, gain=0.4, align="peak", audibility_db=4)
# for e in DATA["events"]:
#     if e["kind"] == "halving": sfx(id="kick-" + e["id"], t=e["t"], gen="kick", args={"f0": 55, "dur": 0.6, "punch": 170}, gain=1.0, audibility_db=6)

SILENCE = []                                                   # e.g. [[25.0, 27.0]]: exact zeros; also in shotspec.json audio.silence and build.sh SILENCE
sheet = {"duration": DATA["dur"], "seed": DATA.get("world_seed", 1), "target_lufs": -14.0, "ceiling_db": -2.0, "fade_out": 0.4, "silence": SILENCE, "pad": pad, "cues": cues}
json.dump(sheet, open(os.path.join(HERE, "cues.json"), "w"), indent=1)
print("cues.json: %d cues, silence %s" % (len(cues), SILENCE))

