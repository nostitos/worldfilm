#!/usr/bin/env python3
"""audio/make_cues.py — the cue sheet for "Block Space", generated from the event table in film/data.js so the sound
is locked to the picture's events (worldfilm stage 8). Serious, cold, monumental: a low A-minor drone that thins as
the subsidy thins, a kick on every past halving, a sub note under the present, a riser into the end, exact digital
silence 25.0-27.0 s, then the loudest moment of the film (impact + chime) on 21,000,000. Writes audio/cues.json.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
src = open(os.path.join(ROOT, "film", "data.js")).read()
DATA = json.loads(re.search(r"export const DATA = (\{.*\});", src, re.S).group(1))
EV = {e["id"]: e for e in DATA["events"]}
A1, C2, E2, A2, E3, A3, C4, E4 = 55.0, 65.41, 82.41, 110.0, 164.81, 220.0, 261.63, 329.63

cues = []
score = lambda **k: cues.append(dict(group="score", **k))
sfx = lambda **k: cues.append(dict(group="sfx", **k))

# drone chords: the bed thins with the subsidy (fewer voices after each halving), gone before the silence
chords = [[0.0, [A1, E2, A2, C4]], [7.0, [A1, E2, A2]], [10.0, [A1, E2, C4]], [13.0, [A1, A2]], [15.5, [A1, E2]], [19.5, [A1]], [23.0, [A1]]]
vol = [[0, 0.0], [0.6, 0.55]]
for ht in (7.0, 10.0, 13.0, 15.5):                     # the drone ducks under every halving kick so the hit is heard
    vol += [[ht - 0.04, 0.55], [ht, 0.18], [ht + 0.45, 0.55]]
vol += [[17.4, 0.55], [19.5, 0.35], [23.0, 0.45], [24.8, 0.0], [27.0, 0.0], [27.1, 0.0]]
pad = {"group": "score", "gain": 0.34, "chords": chords, "volume": vol, "detune": 0.5, "tremolo": 0.12}

# the pulse: a hat on every beat under the street (0.5 s), a soft kick every bar, so the halving kicks land on a grid
for i in range(0, 47):
    t = i * 0.5
    if t >= 24.5:
        break
    if i % 4 == 0 and 3.0 <= t < 23.0 and not (17.4 <= t < 19.3) and t not in (7.0, 10.0, 13.0, 15.5):   # the pulse rests at NOW and yields to the halving kicks
        score(id="pulse-%02d" % i, t=t, gen="kick", args={"f0": 48, "dur": 0.3, "punch": 110}, gain=0.22)
    if i % 2 == 1 and 3.0 <= t < 17.4:
        score(id="hat-%02d" % i, t=t, gen="hat", args={"fc": 7000}, gain=0.08)

# the four halvings so far: a hard kick with a sub under it (each one deeper, each one a little quieter: thinning)
HALVING_T = [e["t"] for e in DATA["events"] if e["kind"] == "halving"]
for k, (t, f) in enumerate(zip(HALVING_T, (55.0, 51.9, 49.0, 46.2)), start=1):
    sfx(id="kick-h%d" % k, t=t, gen="kick", args={"f0": f, "dur": 0.6, "punch": 170}, gain=1.0 - 0.04 * (k - 1), audibility_db=6)
    sfx(id="sub-h%d" % k, t=t + 0.02, gen="sub", args={"freq": f, "dur": 1.6, "attack": 0.01, "release": 0.6}, gain=0.5)
# the present: a sustained A440 marker with a blip when the camera settles
NOW_T = EV["now"]["t"]
score(id="tone-now", t=NOW_T, gen="tone", args={"freq": 440.0, "dur": 2.2, "attack": 0.4, "release": 1.0, "harmonics": [1.0, 0.2, 0.05]}, gain=0.14)
sfx(id="arrive-now", t=NOW_T, gen="blip", args={"freq": 880.0, "dur": 0.5, "tau": 0.18}, gain=0.42, align="peak")
# the future race: 28 halvings as accelerating ticks, quieter as they thin; the riser carries into the end
for e in DATA["events"]:
    if e["kind"] == "halving-future":
        k = int(e["id"].split("-")[1])
        score(id="tick-h%d" % k, t=e["t"], gen="click", args={"freq": 1400 + 40 * k, "dur": 0.05}, gain=max(0.08, 0.34 - 0.009 * (k - 5)))
sfx(id="riser", t=24.95, gen="riser", args={"dur": 2.4, "f0": 220, "f1": 4800}, gain=0.55, align="peak")
# camera whooshes on velocity peaks (whoosh peaks ON the peak time)
for s in DATA["shots"]:
    vp = s["camera"].get("velocity_peak_s")
    if vp and s["id"] in ("s01", "s07", "s08"):
        sfx(id="whoosh-" + s["id"], t=vp, gen="whoosh", args={"dur": 0.9, "f0": 240, "f1": 2600, "peak": 0.55}, gain=0.4, align="peak")
# the payoff: the loudest moment after the silence
sfx(id="impact-cap", t=27.0, gen="impact", args={"dur": 1.6}, gain=1.0, align="peak")
score(id="chime-cap", t=27.02, gen="chime", args={"freqs": [A3, E4, A2 * 4], "dur": 2.4, "tau": 0.9}, gain=0.5)
sfx(id="sub-cap", t=27.0, gen="sub", args={"freq": 55.0, "dur": 2.4, "attack": 0.02, "release": 0.8}, gain=0.6)   # the body of the hit, not bed

sheet = {"duration": DATA["dur"], "seed": 21, "target_lufs": -14.0, "ceiling_db": -2.0, "fade_out": 0.4, "silence": [[25.0, 27.0]], "pad": pad, "cues": cues}
json.dump(sheet, open(os.path.join(HERE, "cues.json"), "w"), indent=1)
print("cues.json: %d cues, silence %s" % (len(cues), sheet["silence"]))
