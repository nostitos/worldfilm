#!/usr/bin/env python3
"""tools/srt.py — captions and the final card as an SRT, straight from shotspec.json (the same text the facts gate checked).
usage: python3 tools/srt.py renders/<slug>.srt
"""
import json
import sys

spec = json.load(open("shotspec.json"))
rows = []
for s in spec["shots"]:
    for t in s.get("text", []):
        if t.get("role") in ("caption", "headline", "kicker", "note") and t.get("at_s") is not None and t.get("until_s") is not None:
            rows.append((t["at_s"], t["until_s"], t["content"], t["role"]))
ORDER = {"caption": 0, "headline": 1, "kicker": 2, "note": 3}
rows.sort(key=lambda r: (r[0], ORDER[r[3]]))
merged = []                                                    # a final card's stacked lines become one cue
for r in rows:
    if merged and r[3] in ("kicker", "note") and merged[-1][3] in ("headline", "kicker") and r[0] - merged[-1][0] < 1.0:
        a = merged[-1]
        merged[-1] = (a[0], max(a[1], r[1]), a[2] + "\n" + r[2], r[3])
    else:
        merged.append(r)


def ts(x):
    ms_total = int(round(x * 1000))
    h, rem = divmod(ms_total, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


out = sys.argv[1] if len(sys.argv) > 1 else "renders/captions.srt"
with open(out, "w") as f:
    for i, (a, b, text, _) in enumerate(merged, 1):
        f.write("%d\n%s --> %s\n%s\n\n" % (i, ts(a), ts(b), text))
print("%s: %d cues" % (out, len(merged)))
