#!/usr/bin/env python3
"""loop_seam.py — position and velocity continuity across the loop point (worldfilm gate `loop_seam`).

For a loop, the last frame must flow into the first the way any frame flows into the next. Position: the seam
difference (last -> first, RGB mean abs) must sit inside the distribution of the loop's own inter-frame
differences (<= 1.25 x its 95th percentile; the largest jump in the loop being the seam is the signature of a
short circle). Velocity: the change in difference magnitude at the seam (|seam - last|, |seam - first|) must
look like an ordinary frame-to-frame change (<= 1.5 x the 95th percentile of |d[i+1]-d[i]|).

usage: loop_seam.py loop.mp4 [--out gates/loop-seam.json] [--size 180] [--pos-ratio 1.25] [--vel-ratio 1.5] [--max-abs 12]
exit 0 = seam within tolerance, 1 = seam visible, 2 = usage error
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wf_common import mean_abs_diff, median, percentile, probe, rgb_frames, write_report  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--out", default=None)
    ap.add_argument("--size", type=int, default=180)
    ap.add_argument("--pos-ratio", type=float, default=1.25, help="seam diff / p95 of inner diffs must be <= this")
    ap.add_argument("--vel-ratio", type=float, default=1.5, help="seam diff change / p95 of inner diff changes must be <= this")
    ap.add_argument("--max-abs", type=float, default=12.0, help="seam diff must also be <= this many gray levels")
    a = ap.parse_args()
    info = probe(a.video)
    frames, w, h = rgb_frames(a.video, size=a.size)
    n = len(frames)
    if n < 4:
        print("too few frames: %d" % n)
        sys.exit(2)
    inner = [mean_abs_diff(frames[i], frames[i + 1]) for i in range(n - 1)]
    med = median(inner)
    p95 = percentile(inner, 0.95)
    mx = max(inner)
    seam = mean_abs_diff(frames[n - 1], frames[0])
    changes = [abs(inner[i + 1] - inner[i]) for i in range(len(inner) - 1)]
    chg95 = percentile(changes, 0.95)
    jump = max(abs(seam - inner[-1]), abs(seam - inner[0]))
    floor = 0.5
    pos_ratio = seam / max(p95, floor)
    vel_ratio = jump / max(chg95, floor * 0.5)
    pos_fail = seam > a.max_abs or (pos_ratio > a.pos_ratio and seam >= mx)
    vel_fail = vel_ratio > a.vel_ratio and jump > floor
    ok = not pos_fail and not vel_fail
    status = "PASS" if ok else "FAIL"
    report = {"gate": "loop_seam", "status": status, "video": os.path.abspath(a.video), "frames": n, "fps": info["fps"],
              "measured": {"seam_diff": round(seam, 3), "inner_median": round(med, 3), "inner_p95": round(p95, 3), "inner_max": round(mx, 3),
                           "position_ratio": round(pos_ratio, 2), "position_fail": pos_fail,
                           "seam_change": round(jump, 3), "inner_change_p95": round(chg95, 3), "velocity_ratio": round(vel_ratio, 2), "velocity_fail": vel_fail},
              "threshold": {"pos_ratio": a.pos_ratio, "vel_ratio": a.vel_ratio, "max_abs": a.max_abs}}
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.video)), "gates", "loop-seam.json")
    write_report(out, report)
    print("loop_seam gate: %s — position: seam %.2f vs inner p95 %.2f / max %.2f (x%.2f%s); velocity: change %.2f vs p95 %.2f (x%.2f%s) -> %s" % (
        status, seam, p95, mx, pos_ratio, " FAIL" if pos_fail else "", jump, chg95, vel_ratio, " FAIL" if vel_fail else "", out))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
