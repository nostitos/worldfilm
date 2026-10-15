#!/usr/bin/env python3
"""tools/srt.py — captions and the final card as an SRT, straight from shotspec.json (the same text the facts gate checked).
usage: python3 tools/srt.py renders/block-space.srt
"""
import json
import sys

spec = json.load(open("shotspec.json"))
rows = []
for s in spec["shots"]:
    for t in s.get("text", []):
        if t.get("role") in ("caption", "headline", "kicker", "note"):
            rows.append((t["at_s"], t["until_s"], t["content"], t["role"]))
ORDER = {"caption": 0, "headline": 1, "kicker": 2, "note": 3}
rows.sort(key=lambda r: (r[0], ORDER[r[3]]))
# merge the final card's three lines into one cue
merged = []
for r in rows:
    if merged and r[3] in ("kicker", "note") and merged[-1][3] in ("headline", "kicker") and r[0] - merged[-1][0] < 1.0:
        a = merged[-1]
        merged[-1] = (a[0], max(a[1], r[1]), a[2] + "\n" + r[2], r[3])
    else:
        merged.append(r)


def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = int(x % 60); ms = int(round((x - int(x)) * 1000))
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


out = sys.argv[1] if len(sys.argv) > 1 else "renders/block-space.srt"
with open(out, "w") as f:
    for i, (a, b, text, _) in enumerate(merged, 1):
        f.write("%d\n%s --> %s\n%s\n\n" % (i, ts(a), ts(b), text))
print("wrote %s (%d cues)" % (out, len(merged)))
