#!/usr/bin/env python3
"""detect_pops.py — one-frame pops and flashes in a rendered video (worldfilm gate `pops`).

A pop is a frame that differs from both neighbours while its neighbours agree with each other: the render
dropped a stage, a font swapped for one frame, a seek landed on the wrong state. A flash is a single-frame
luminance spike or black frame. Hard cuts are not pops (the frame after a cut agrees with the frame after it),
so a cut list is only used for the report. The test runs on the whole frame (RGB mean abs diff) and on a grid
of blocks, so a one-frame flicker of a corner label is caught even when the global mean barely moves.
A frame is a pop when it differs from each neighbour by more than 3x what the neighbours differ from each other;
a skip-frame test keeps cuts from false-positiving, and the block grid exists because a 40 px pop on a 320 px
frame slipped under a global floor.

usage: detect_pops.py video.mp4 [--out gates/pops.json] [--size 180] [--ratio 3.0] [--floor 0.75] [--block 16]
                               [--block-floor 6] [--block-min 2] [--flash 40] [--cuts 9.0,13.0] [--allow 27.5,29.0] [--allow-tol 0.05]
  The block test needs --block-min blocks to agree, and a block hit is discarded when the feature travelled: a bright
  edge that crosses a block in two frames lights a neighbouring block one frame later (quiet at i, lit at i+1), while a
  real one-frame glitch of a label or element does not move. Block-only hits below --block-fail blocks are reported as
  shimmer (WARN): thin lines crawling across pixels; the shutter blur of the master removes it. Frame-level pops,
  flashes and block clusters of --block-fail or more FAIL.
exit 0 = no defects (WARN allowed), 1 = pops or flashes found, 2 = usage error
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wf_common import mean_abs_diff, mean_luma, median, probe, rgb_frames, write_report  # noqa: E402

try:
    import numpy as np
except Exception:
    np = None


def block_diffs(frames, block):
    """Per-block mean abs diff for consecutive pairs and skip pairs: (pair[N-1, bh, bw], skip[N-2, bh, bw]). numpy only."""
    n, h, w = frames.shape[0], frames.shape[1], frames.shape[2]
    bh, bw = max(1, h // block), max(1, w // block)
    hh, ww = bh * block, bw * block
    f = frames[:, :hh, :ww].astype(np.int16).reshape(n, bh, block, bw, block, -1)
    f = f.transpose(0, 1, 3, 2, 4, 5).reshape(n, bh, bw, -1)
    pair = np.abs(f[1:] - f[:-1]).mean(axis=3)
    skip = np.abs(f[2:] - f[:-2]).mean(axis=3)
    return pair, skip


def travelled(bpair, i, y, x):
    """True when a neighbouring block was quiet at pair i and lit at pair i+1 (or lit at i-1, quiet at i): the feature moved."""
    n, bh, bw = bpair.shape
    hit = bpair[i, y, x]
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            yy, xx = y + dy, x + dx
            if not (0 <= yy < bh and 0 <= xx < bw):
                continue
            quiet_now = bpair[i, yy, xx] < 0.5 * hit
            lit_next = i + 1 < n and bpair[i + 1, yy, xx] > 0.5 * hit
            lit_prev = i - 1 >= 0 and bpair[i - 1, yy, xx] > 0.5 * hit
            if quiet_now and (lit_next or lit_prev):
                return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--out", default=None, help="JSON report (default: <video dir>/gates/pops.json)")
    ap.add_argument("--size", type=int, default=180, help="analysis width in px (default 180)")
    ap.add_argument("--ratio", type=float, default=3.0, help="a pop's diffs must exceed ratio x the skip diff")
    ap.add_argument("--floor", type=float, default=0.75, help="ignore whole-frame diffs below this many levels")
    ap.add_argument("--block", type=int, default=16, help="block size in analysis px for the local test (0 = off)")
    ap.add_argument("--block-floor", type=float, default=6.0, help="ignore block diffs below this many levels")
    ap.add_argument("--block-min", type=int, default=2, help="blocks that must agree before the local test fires")
    ap.add_argument("--block-fail", type=int, default=6, help="block hits of this size or more FAIL; smaller ones WARN as shimmer")
    ap.add_argument("--flash", type=float, default=40.0, help="single-frame mean-luma spike that counts as a flash")
    ap.add_argument("--cuts", default="", help="comma list of intended cut times (s), reported only")
    ap.add_argument("--allow", default="", help="comma list of intended one-frame hits (s), e.g. a designed flash")
    ap.add_argument("--allow-tol", type=float, default=0.05, help="tolerance around --allow times (s)")
    a = ap.parse_args()

    info = probe(a.video)
    fps = info["fps"]
    frames, w, h = rgb_frames(a.video, size=a.size)
    n = len(frames)
    if n < 3:
        print("too few frames: %d" % n)
        sys.exit(2)
    d = [mean_abs_diff(frames[i], frames[i + 1]) for i in range(n - 1)]      # d[i]: frame i -> i+1
    skip = [mean_abs_diff(frames[i], frames[i + 2]) for i in range(n - 2)]  # skip[i]: frame i -> i+2
    luma = [mean_luma(f) for f in frames]
    allow = [float(x) for x in a.allow.split(",") if x.strip()]
    cuts = [float(x) for x in a.cuts.split(",") if x.strip()]

    def allowed(t):
        return any(abs(t - x) <= a.allow_tol for x in allow)

    pops, flashes, cut_frames, shimmer = [], [], [], []
    bpair = bskip = None
    if np is not None and a.block > 0:
        bpair, bskip = block_diffs(frames, a.block)
    for i in range(n - 2):
        mid = i + 1
        t = mid / fps
        ref = max(skip[i], a.floor)
        hit = d[i] > a.ratio * ref and d[i + 1] > a.ratio * ref
        where = "frame"
        if not hit and bpair is not None:
            bref = np.maximum(bskip[i], a.block_floor)
            mask = (bpair[i] > a.ratio * bref) & (bpair[i + 1] > a.ratio * bref)
            ys, xs = np.where(mask)
            stuck = [(y, x) for y, x in zip(ys, xs) if not travelled(bpair, i, int(y), int(x))]
            if a.block_min <= len(stuck) < a.block_fail:
                shimmer.append({"frame": mid, "t": round(t, 4), "blocks": len(stuck)})
            elif len(stuck) >= a.block_fail:
                hit, where = True, "blocks:%d" % len(stuck)
        if hit:
            pops.append({"frame": mid, "t": round(t, 4), "diff_in": round(d[i], 2), "diff_out": round(d[i + 1], 2),
                         "skip_diff": round(skip[i], 2), "where": where, "allowed": allowed(t)})
        spike = luma[mid] - max(luma[i], luma[i + 2])
        dip = min(luma[i], luma[i + 2]) - luma[mid]
        if spike > a.flash or dip > a.flash:
            flashes.append({"frame": mid, "t": round(t, 4), "luma": round(luma[mid], 1),
                            "neighbours": [round(luma[i], 1), round(luma[i + 2], 1)],
                            "kind": "white" if spike > a.flash else "black", "allowed": allowed(t)})
    med = median(d)
    for i in range(1, n - 2):
        if d[i] > max(12.0, 6 * med) and d[i] > 3 * max(d[i - 1], d[i + 1], a.floor):
            cut_frames.append({"frame": i + 1, "t": round((i + 1) / fps, 4), "diff": round(d[i], 2)})

    bad_pops = [p for p in pops if not p["allowed"]]
    bad_flash = [f for f in flashes if not f["allowed"]]
    status = "FAIL" if (bad_pops or bad_flash) else ("WARN" if shimmer else "PASS")
    report = {
        "gate": "pops", "status": status, "video": os.path.abspath(a.video), "fps": fps, "frames": n,
        "analysis_size": [w, h], "thresholds": {"ratio": a.ratio, "floor": a.floor, "block": a.block, "block_floor": a.block_floor, "block_min": a.block_min, "block_fail": a.block_fail, "flash": a.flash},
        "measured": {"pops": len(bad_pops), "flashes": len(bad_flash), "allowed_hits": len(pops) + len(flashes) - len(bad_pops) - len(bad_flash),
                     "shimmer_frames": len(shimmer), "median_frame_diff": round(med, 3), "detected_cuts": len(cut_frames)},
        "pops": pops, "flashes": flashes, "shimmer": shimmer[:400], "detected_cuts": cut_frames, "intended_cuts": cuts,
    }
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.video)), "gates", "pops.json")
    write_report(out, report)
    print("pops gate: %s — %d pops, %d flashes, %d shimmer frames (median frame diff %.2f, %d cuts detected) -> %s" % (
        status, len(bad_pops), len(bad_flash), len(shimmer), med, len(cut_frames), out))
    if shimmer:
        print("  shimmer (thin-line crawl; the blur master removes it): %s" % ", ".join("%.2fs" % s["t"] for s in shimmer[:12]) + (" ..." if len(shimmer) > 12 else ""))
    for p in bad_pops[:20]:
        print("  POP   frame %5d  t=%7.3fs  in %.2f out %.2f skip %.2f (%s)" % (p["frame"], p["t"], p["diff_in"], p["diff_out"], p["skip_diff"], p["where"]))
    for f in bad_flash[:20]:
        print("  FLASH frame %5d  t=%7.3fs  %s luma %.0f (neighbours %.0f/%.0f)" % (f["frame"], f["t"], f["kind"], f["luma"], *f["neighbours"]))
    sys.exit(1 if status == "FAIL" else 0)


if __name__ == "__main__":
    main()
