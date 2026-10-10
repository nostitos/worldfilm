#!/usr/bin/env python3
"""measure_reference.py — measure a reference video (or stills) before anything is drawn: palette, accents, line
weight, texture, luminance, the motion-shape series and the cut rhythm. Output is the `project.reference` block of
a worldfilm spec plus a Markdown summary, so the look is matched against numbers, not adjectives.

Method: 16-level palette buckets with accent hue families (flat borders trimmed); line weight, texture and
luminance per sampled frame; shotspec-film's frame-difference series (ffmpeg signalstats YAVG) for the motion
shape; every frame analysed for cuts.
Reference pixels are study material: nothing here is copied into a film.

usage: measure_reference.py <video | image | folder> [--out references/<name>.json] [--frames 24] [--size 320]
                            [--cut-min-gap 0.25]
"""
import argparse
import json
import math
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wf_common import FFMPEG, percentile, probe, rgb_frames  # noqa: E402

IMG_EXT = (".png", ".jpg", ".jpeg", ".webp")
HUE_NAMES = ["red-orange", "yellow", "yellow-green", "green", "green", "green-cyan", "cyan", "azure", "blue", "violet", "magenta", "pink-red"]


def hexrgb(c):
    return "#" + "".join("%02x" % int(round(v)) for v in c)


def load_image(path, size):
    r = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-vf", "scale=%d:-2:flags=area,format=rgb24" % size, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip().split(",")
    w0, h0 = int(p[0]), int(p[1])
    w = size
    h = int(round(h0 * size / w0 / 2)) * 2
    arr = np.frombuffer(r.stdout, np.uint8)
    return arr[: w * h * 3].reshape(h, w, 3)


def trim_flat(frame, tol=42):
    """Drop letterboxing / flat borders: rows and columns within tol (sum of channel diffs) of the corner colour."""
    h, w, _ = frame.shape
    corner = frame[0, 0].astype(int)
    near = (np.abs(frame.astype(int) - corner).sum(axis=2) < tol)
    rows = near.all(axis=1)
    cols = near.all(axis=0)
    y0 = 0
    while y0 < h - 1 and rows[y0]:
        y0 += 1
    y1 = h - 1
    while y1 > y0 and rows[y1]:
        y1 -= 1
    x0 = 0
    while x0 < w - 1 and cols[x0]:
        x0 += 1
    x1 = w - 1
    while x1 > x0 and cols[x1]:
        x1 -= 1
    return frame[y0:y1 + 1, x0:x1 + 1], (x0, y0, x1 - x0 + 1, y1 - y0 + 1)


def palette(frames, top=8):
    px = np.concatenate([f.reshape(-1, 3) for f in frames]).astype(np.int64)
    key = (px[:, 0] >> 4) * 256 + (px[:, 1] >> 4) * 16 + (px[:, 2] >> 4)
    uniq, inv, counts = np.unique(key, return_inverse=True, return_counts=True)
    order = np.argsort(-counts)[:top]
    out = []
    n = len(px)
    for o in order:
        sel = px[inv == o]
        mean = sel.mean(axis=0)
        out.append({"hex": hexrgb(mean), "rgb": [int(round(v)) for v in mean], "share": round(float(counts[o]) / n, 4)})
    return out


def accents(frames):
    px = np.concatenate([f.reshape(-1, 3) for f in frames]).astype(float)
    mx = px.max(axis=1)
    mn = px.min(axis=1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    sel = (mx >= 120) & (sat >= 0.35)
    if not sel.any():
        return {"share": 0.0, "families": []}
    p = px[sel]
    r, g, b = p[:, 0], p[:, 1], p[:, 2]
    m, n_ = p.max(axis=1), p.min(axis=1)
    d = np.maximum(m - n_, 1e-9)
    hue = np.where(m == r, ((g - b) / d) % 6, np.where(m == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    hue = (hue + 360) % 360
    fam = (hue // 30).astype(int) % 12
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    fams = []
    tot = len(p)
    for k in range(12):
        idx = np.where(fam == k)[0]
        if len(idx) < max(1, tot * 0.02):
            continue
        order = idx[np.argsort(-lum[idx])]
        cut = max(1, len(order) // 5)
        core = np.median(p[order[:cut]], axis=0)
        halo = np.median(p[order[cut:]], axis=0) if len(order) > cut else core
        fams.append({"family": HUE_NAMES[k], "share": round(len(idx) / tot, 3), "core": hexrgb(core), "halo": hexrgb(halo)})
    fams.sort(key=lambda f: -f["share"])
    return {"share": round(tot / len(px), 4), "families": fams}


def gray(f):
    return (0.299 * f[..., 0] + 0.587 * f[..., 1] + 0.114 * f[..., 2]).astype(np.float32)


def line_weight(frames, ref_width):
    """Median run length of edge pixels along rows and columns, scaled to 1080p-width pixels.
    Edges: gradient magnitude above 2x the frame's mean gradient (so flat paper and busy ink both work)."""
    runs = []
    for f in frames:
        g = gray(f)
        gx = np.abs(np.diff(g, axis=1))
        gy = np.abs(np.diff(g, axis=0))
        mag = np.zeros_like(g)
        mag[:, 1:] += gx
        mag[1:, :] += gy
        thr = max(12.0, 2.0 * float(mag.mean()))
        e = mag > thr
        for axis in (0, 1):
            arr = e if axis == 1 else e.T
            for row in arr[:: max(1, arr.shape[0] // 60)]:
                run = 0
                for v in row:
                    if v:
                        run += 1
                    elif run:
                        runs.append(run)
                        run = 0
    if not runs:
        return {"px_at_1080p": None, "note": "no edges found"}
    scale = 1920.0 / ref_width
    r = np.array(runs, dtype=float) * scale
    return {"px_at_1080p": round(float(np.median(r)), 2), "p25": round(float(np.percentile(r, 25)), 2), "p75": round(float(np.percentile(r, 75)), 2), "samples": int(len(runs))}


def texture(frames):
    """Grain / high-frequency index: mean |pixel - 3x3 box mean| relative to the mean luma, plus local variance."""
    vals, lv = [], []
    for f in frames:
        g = gray(f)
        box = (g[:-2, :-2] + g[:-2, 1:-1] + g[:-2, 2:] + g[1:-1, :-2] + g[1:-1, 1:-1] + g[1:-1, 2:] + g[2:, :-2] + g[2:, 1:-1] + g[2:, 2:]) / 9
        vals.append(float(np.abs(g[1:-1, 1:-1] - box).mean()) / max(1.0, float(g.mean())))
        blocks = g[: g.shape[0] // 8 * 8, : g.shape[1] // 8 * 8].reshape(-1, 8, g.shape[1] // 8, 8).transpose(0, 2, 1, 3).reshape(-1, 64)
        lv.append(float(np.median(blocks.var(axis=1))))
    return {"grain_index": round(float(np.mean(vals)), 4), "block_variance_median": round(float(np.median(lv)), 1)}


def luminance(frames):
    g = np.concatenate([gray(f).ravel() for f in frames])
    return {"mean": round(float(g.mean()), 1), "deciles": [round(float(np.percentile(g, q)), 1) for q in range(10, 100, 10)],
            "dark_share": round(float((g < 40).mean()), 3), "light_share": round(float((g > 215).mean()), 3), "contrast_std": round(float(g.std()), 1)}


def motion_and_cuts(path, fps_native, min_gap):
    fr, w, h = rgb_frames(path, size=160)
    n = len(fr)
    if n < 3:
        return {"series_fps": fps_native, "mean": 0, "cv": 0}, {"count": 0}
    d = np.abs(fr[1:].astype(np.int16) - fr[:-1].astype(np.int16)).reshape(n - 1, -1).mean(axis=1)
    med = float(np.median(d))
    p95 = float(np.percentile(d, 95))
    # cuts: a frame difference far above its neighbourhood, at least min_gap apart
    cuts = []
    last = -1e9
    for i in range(1, len(d) - 1):
        local = max(float(np.median(d[max(0, i - 15):i])) if i > 0 else 0.0, float(np.median(d[i + 1:i + 16])) if i + 1 < len(d) else 0.0, 0.5)
        if d[i] > max(4.0, 4.0 * local) and d[i] > 2.5 * max(d[i - 1], d[i + 1], 0.5):  # floor 4: a paper-to-paper cut measured 7.4
            t = (i + 1) / fps_native
            if t - last >= min_gap:
                cuts.append(round(t, 3))
                last = t
    shots = np.diff([0.0] + cuts + [n / fps_native]) if cuts else np.array([n / fps_native])
    dd = d[d < max(10.0, 4.0 * med)] if len(d) else d  # motion series without the cut spikes
    motion = {"series_fps": round(fps_native, 3), "mean_diff": round(float(dd.mean()), 3), "median_diff": round(med, 3), "p95_diff": round(p95, 3),
              "cv": round(float(dd.std() / max(dd.mean(), 1e-6)), 3), "still_share": round(float((dd < 0.35).mean()), 3),
              "histogram": [int(x) for x in np.histogram(dd, bins=[0, 0.35, 1, 2, 4, 8, 16, 1e9])[0]]}
    rhythm = {"count": len(cuts), "cuts_per_30s": round(len(cuts) / max(n / fps_native, 1e-6) * 30, 2), "times": cuts[:400],
              "shot_s": {"mean": round(float(shots.mean()), 3), "median": round(float(np.median(shots)), 3), "min": round(float(shots.min()), 3), "max": round(float(shots.max()), 3),
                         "cv": round(float(shots.std() / max(shots.mean(), 1e-6)), 3)}}
    return motion, rhythm


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("--out", default=None)
    ap.add_argument("--frames", type=int, default=24, help="frames sampled for palette/line/texture")
    ap.add_argument("--size", type=int, default=320)
    ap.add_argument("--cut-min-gap", type=float, default=0.25)
    a = ap.parse_args()
    src = a.source
    name = os.path.splitext(os.path.basename(src.rstrip("/")))[0]
    frames, info, motion, rhythm = [], None, None, None
    if os.path.isdir(src):
        paths = sorted(os.path.join(src, f) for f in os.listdir(src) if f.lower().endswith(IMG_EXT))
        frames = [trim_flat(load_image(p, a.size))[0] for p in paths]
        kind = "stills"
        ref_w = a.size
    elif src.lower().endswith(IMG_EXT):
        frames = [trim_flat(load_image(src, a.size))[0]]
        kind, ref_w = "still", a.size
    else:
        info = probe(src)
        fr, w, h = rgb_frames(src, size=a.size)
        idx = np.linspace(0, len(fr) - 1, min(a.frames, len(fr))).astype(int)
        frames = [trim_flat(fr[i])[0] for i in idx]
        kind, ref_w = "video", w
        motion, rhythm = motion_and_cuts(src, info["fps"], a.cut_min_gap)
    if not frames:
        sys.exit("no frames found in " + src)
    out = {
        "source": os.path.abspath(src), "kind": kind, "measured_at_width": ref_w,
        "video": {"fps": info["fps"], "duration": round(info["duration"], 3), "size": [info["width"], info["height"]]} if info else None,
        "palette": palette(frames), "accents": accents(frames), "line_weight": line_weight(frames, ref_w), "texture": texture(frames),
        "luminance": luminance(frames), "motion": motion, "cut_rhythm": rhythm,
        "note": "reference pixels are study material; derive tokens, never copy frames",
    }
    path = a.out or os.path.join(os.path.dirname(os.path.abspath(src)) if not os.path.isdir(src) else src, name + ".reference.json")
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    json.dump(out, open(path, "w"), indent=1)
    md = path[:-5] + ".md" if path.endswith(".json") else path + ".md"
    lines = ["# Reference measure: " + name, "", "Source: " + out["source"], ""]
    if info:
        lines.append("Video: %dx%d, %.3f fps, %.1f s" % (info["width"], info["height"], info["fps"], info["duration"]))
    lines += ["", "## Palette (16-level buckets, means are exact colours)", ""] + ["- %s rgb(%s) %.1f%%" % (p["hex"], ",".join(map(str, p["rgb"])), p["share"] * 100) for p in out["palette"]]
    lines += ["", "## Accents (bright + saturated, %.1f%% of pixels)" % (out["accents"]["share"] * 100), ""] + ["- %s %d%% core %s halo %s" % (f["family"], f["share"] * 100, f["core"], f["halo"]) for f in out["accents"]["families"]]
    lw, tx, lu = out["line_weight"], out["texture"], out["luminance"]
    lines += ["", "## Line, texture, light", "", "- line weight (median edge run at 1080p width): %s px (p25 %s, p75 %s)" % (lw.get("px_at_1080p"), lw.get("p25"), lw.get("p75")),
              "- grain index %.4f, block variance median %.1f" % (tx["grain_index"], tx["block_variance_median"]),
              "- luma mean %.1f, std %.1f, dark share %.1f%%, light share %.1f%%" % (lu["mean"], lu["contrast_std"], lu["dark_share"] * 100, lu["light_share"] * 100)]
    if motion:
        lines += ["", "## Motion shape (per-frame RGB mean abs diff at native fps)", "", "- mean %.2f, median %.2f, p95 %.2f, CV %.2f, still share %.1f%%" % (motion["mean_diff"], motion["median_diff"], motion["p95_diff"], motion["cv"], motion["still_share"] * 100),
                  "- histogram [<0.35, <1, <2, <4, <8, <16, more]: %s" % motion["histogram"]]
    if rhythm:
        lines += ["", "## Cut rhythm", "", "- %d cuts, %.2f per 30 s; shot length mean %.2f s, median %.2f s, min %.2f, max %.2f, CV %.2f" % (
            rhythm["count"], rhythm["cuts_per_30s"], rhythm["shot_s"]["mean"], rhythm["shot_s"]["median"], rhythm["shot_s"]["min"], rhythm["shot_s"]["max"], rhythm["shot_s"]["cv"]),
            "- first cuts: %s" % rhythm["times"][:12]]
    open(md, "w").write("\n".join(lines) + "\n")
    print("measured %s -> %s (+ .md)" % (name, path))
    print("  palette:", ", ".join("%s %.0f%%" % (p["hex"], p["share"] * 100) for p in out["palette"][:5]))
    print("  accents:", ", ".join("%s %s" % (f["family"], f["core"]) for f in out["accents"]["families"][:4]) or "none")
    print("  line %s px @1080p, grain %.4f, luma %.0f; motion mean %s, cuts %s" % (lw.get("px_at_1080p"), tx["grain_index"], lu["mean"],
          motion["mean_diff"] if motion else "-", rhythm["count"] if rhythm else "-"))


if __name__ == "__main__":
    main()
