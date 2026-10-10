#!/usr/bin/env python3
"""blur_ab.py — compare a sharp capture with a sub-frame-blurred capture of the same page (tests/README.md).

Edge sharpness = mean squared gradient (gradient energy) of the gray frame; a step of height H smeared over k
pixels keeps its summed gradient but loses energy (H^2/k vs H^2), so energy sees the blur that mean magnitude
cannot. The blurred render must be softer on moving frames (ratio < 0.85 on the fast pass), the frames on both
sides of the hard cut must contain no content from the other side (mean abs RGB difference to the sharp capture
< 4 levels; a leak across the flipped background would be tens of levels), and both captures must have the same
frame count.
usage: blur_ab.py sharp.mp4 blurred.mp4 --cut 0.97
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from wf_common import gray_frames, mean_abs_diff, probe, rgb_frames  # noqa: E402


def sharpness(f):
    f = f.astype(np.float32)
    gx = np.abs(f[:, 2:] - f[:, :-2])[1:-1, :]
    gy = np.abs(f[2:, :] - f[:-2, :])[:, 1:-1]
    return float((gx ** 2 + gy ** 2).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sharp")
    ap.add_argument("blurred")
    ap.add_argument("--cut", type=float, default=0.97)
    a = ap.parse_args()
    fps = probe(a.sharp)["fps"]
    A, w, h = gray_frames(a.sharp, size=320)
    B, _, _ = gray_frames(a.blurred, size=320)
    Ac, _, _ = rgb_frames(a.sharp, size=320)
    Bc, _, _ = rgb_frames(a.blurred, size=320)
    n = min(len(A), len(B))
    sa = np.array([sharpness(x) for x in A[:n]])
    sb = np.array([sharpness(x) for x in B[:n]])
    moving = [i for i in range(n) if 0.1 < (i / fps) < 0.7]                  # the square is crossing, before the cut
    ratio_moving = float(sb[moving].mean() / sa[moving].mean())
    ci = int(np.ceil(a.cut * fps - 1e-9))                                   # first frame at/after the cut
    leak_after = mean_abs_diff(Ac[ci], Bc[ci])
    leak_before = mean_abs_diff(Ac[ci - 1], Bc[ci - 1])
    ok = len(A) == len(B) and ratio_moving < 0.85 and leak_after < 4 and leak_before < 4
    print("frames %d/%d  sharpness moving: sharp %.1f blurred %.1f (x%.2f)  cut at frame %d: leak before %.2f after %.2f levels  -> %s" % (
        len(A), len(B), sa[moving].mean(), sb[moving].mean(), ratio_moving, ci, leak_before, leak_after, "PASS" if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
