#!/usr/bin/env python3
"""luma_floor.py — per-frame mean luma must stay above a floor (worldfilm gate `luma`): a film that measures well on
styleframes can still be a black tunnel on a phone for seconds at a time. Uses ffmpeg signalstats YAVG per frame.

usage: luma_floor.py video.mp4 [--min 35] [--window 0.5] [--tail 0] [--out gates/luma.json]
  A frame fails when the mean luma of the `--window`-second window around it is below --min; --tail seconds at the end
  are reported but exempt (a fade to black). Choose the floor to match the approved look and delivery requirements.
exit 0 = every window above the floor, 1 = dark stretches found, 2 = usage error
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wf_common import FFMPEG, probe, write_report  # noqa: E402


def yavg_series(path):
    r = subprocess.run([FFMPEG, "-v", "info", "-i", path, "-vf", "scale=320:-2,signalstats,metadata=print:file=-", "-f", "null", "-"], capture_output=True, text=True)
    vals = []
    for line in r.stdout.splitlines():
        if "lavfi.signalstats.YAVG=" in line:
            vals.append(float(line.split("=")[-1]))
    return vals


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--min", type=float, default=35.0)
    ap.add_argument("--window", type=float, default=0.5)
    ap.add_argument("--tail", type=float, default=0.0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    info = probe(a.video)
    fps = info["fps"]
    y = yavg_series(a.video)
    n = len(y)
    if n == 0:
        print("no frames measured")
        sys.exit(2)
    w = max(1, int(round(a.window * fps)))
    half = w // 2
    cs = [0.0]
    for v in y:
        cs.append(cs[-1] + v)
    means = [(cs[min(n, i + half + 1)] - cs[max(0, i - half)]) / (min(n, i + half + 1) - max(0, i - half)) for i in range(n)]
    limit = n - int(a.tail * fps)
    dark = [i for i in range(n) if means[i] < a.min and i < limit]
    stretches = []
    for i in dark:
        if stretches and i == stretches[-1][1] + 1:
            stretches[-1][1] = i
        else:
            stretches.append([i, i])
    status = "PASS" if not dark else "FAIL"
    report = {"gate": "luma", "status": status, "video": os.path.abspath(a.video), "fps": fps, "frames": n,
              "measured": {"min_window_mean": round(min(means), 2), "min_at_s": round(means.index(min(means)) / fps, 3), "mean": round(sum(y) / n, 2),
                           "dark_seconds": round(len(dark) / fps, 2), "stretches": [{"from_s": round(s / fps, 2), "to_s": round((e + 1) / fps, 2), "min": round(min(means[s:e + 1]), 1)} for s, e in stretches][:50]},
              "threshold": {"min": a.min, "window_s": a.window, "tail_exempt_s": a.tail}}
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.video)), "gates", "luma.json")
    write_report(out, report)
    print("luma gate: %s — min window mean %.1f at %.2fs (floor %.0f), film mean %.1f, %.2fs dark -> %s" % (
        status, min(means), means.index(min(means)) / fps, a.min, sum(y) / n, len(dark) / fps, out))
    for s in report["measured"]["stretches"][:10]:
        print("  dark %.2f-%.2fs (min %.1f)" % (s["from_s"], s["to_s"], s["min"]))
    sys.exit(0 if status == "PASS" else 1)


if __name__ == "__main__":
    main()
