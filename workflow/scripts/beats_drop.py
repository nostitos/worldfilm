#!/usr/bin/env python3
"""beats_drop.py — tempo, beat grid, downbeats, kicks, bar energy and the drop of a music track.

Beat tracking adapted from MIT-licensed code (see THIRD_PARTY_NOTICES.md) and rewritten in numpy. The drop
is found from band energy (low band 20-150 Hz vs full band) rather than trusted from an auto beat grid. For the
phase-exact grid a film is cut on, use shotspec-film's `beatgrid_fit.py`; this script is for the song map: where
the energy phases are, where the drop is, and where to start the song so the drop lands on the key frame.

usage: beats_drop.py track.wav [--duration 30] [--start auto|SECONDS] [--drop-at 0.4] [-o audiomap.json]
  --start auto places a --duration window so the drop lands at --drop-at of the clip (snapped to a downbeat).
Output: {bpm, start, duration, beats, downbeats, kicks:[[t, strength]], bar_energy, low_energy, drop, drop_strength}
with every time relative to `start`.
"""
import argparse
import json
import math
import os
import subprocess
import sys

import numpy as np

SR = 11025
HOP = 256
FPS = SR / HOP


def decode(path, filt=None):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR)]
    if filt:
        cmd += ["-af", filt]
    cmd += ["-f", "f32le", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        sys.exit("ffmpeg failed: " + r.stderr.decode(errors="replace"))
    return np.frombuffer(r.stdout, np.float32).astype(np.float64)


def frame_energy(x):
    n = len(x) // HOP
    return (x[: n * HOP].reshape(n, HOP) ** 2).mean(axis=1)


def onset(env):
    lg = np.log(1e-6 + env)
    d = np.maximum(0.0, np.diff(lg, prepend=lg[0]))
    return 0.5 * d + 0.25 * np.roll(d, 1) + 0.25 * np.roll(d, -1)


def tempo(nov):
    x = nov - nov.mean()
    n = len(x)
    lo, hi = int(FPS * 60 / 190), int(FPS * 60 / 70) + 1
    scores = {}
    best, best_lag = -1e18, lo
    for lag in range(lo, hi):
        s = float(np.dot(x[: n - lag], x[lag:]))
        bpm = 60 * FPS / lag
        w = math.exp(-0.5 * (math.log2(bpm / 126) / 0.6) ** 2)
        scores[lag] = s
        if s * w > best:
            best, best_lag = s * w, lag
    l = best_lag
    if l - 1 in scores and l + 1 in scores:
        a, b, c = scores[l - 1], scores[l], scores[l + 1]
        den = a - 2 * b + c
        if den:
            l = l + 0.5 * (a - c) / den
    return l


def beat_grid(nov, period):
    n = len(nov)
    best, best_off = -1, 0
    for off in range(int(period) + 1):
        idx = np.round(off + np.arange(0, (n - off) / period + 1) * period).astype(int)
        idx = idx[idx < n]
        s = float(nov[idx].sum())
        if s > best:
            best, best_off = s, off
    while best_off - period >= 0:
        best_off -= period
    beats = []
    k = 0
    while True:
        c = best_off + k * period
        if c >= n:
            break
        i = int(round(c))
        lo, hi = max(0, i - 2), min(n - 1, i + 2)
        j = lo + int(np.argmax(nov[lo:hi + 1]))
        beats.append(j if nov[j] > 1.5 * nov[i] + 1e-9 else i)
        k += 1
    return beats


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track")
    ap.add_argument("--duration", type=float, default=None, help="window length (default: the whole track)")
    ap.add_argument("--start", default="0", help="'auto' or seconds")
    ap.add_argument("--drop-at", type=float, default=0.4, help="with --start auto: fraction of the clip where the drop lands")
    ap.add_argument("-o", "--out", default=None)
    a = ap.parse_args()

    full = decode(a.track)
    low = decode(a.track, "lowpass=f=150,lowpass=f=150,highpass=f=20")
    total = len(full) / SR
    env, envl = frame_energy(full), frame_energy(low)
    nov, novl = onset(env), onset(envl)
    comb = nov + 1.5 * novl
    period = tempo(comb)
    bpm = 60 * FPS / period
    beats = beat_grid(comb, period)
    phase = max(range(4), key=lambda p: float(novl[beats[p::4]].sum()) if len(beats) > p else 0)
    downs = beats[phase::4]
    thr = float(np.sort(novl)[int(len(novl) * 0.9)]) if len(novl) else 0
    peak = float(novl.max()) or 1
    kicks = []
    for i in range(1, len(novl) - 1):
        if novl[i] > thr and novl[i] >= novl[i - 1] and novl[i] > novl[i + 1]:
            if not kicks or i - kicks[-1][0] > FPS * 0.18:
                kicks.append((i, float(novl[i] / peak)))
    bar_e, bar_low = [], []
    for b in range(len(downs) - 1):
        seg, segl = env[downs[b]:downs[b + 1]], envl[downs[b]:downs[b + 1]]
        bar_e.append(math.sqrt(float(seg.mean())) if len(seg) else 0.0)
        bar_low.append(math.sqrt(float(segl.mean())) if len(segl) else 0.0)
    mx = max(bar_e) or 1
    mxl = max(bar_low) or 1
    bar_e = [e / mx for e in bar_e]
    bar_low = [e / mxl for e in bar_low]
    # the drop: the biggest sustained jump in energy, weighted by the low band arriving (band energy, not the grid)
    drop_bar, best = None, 0.0
    for b in range(4, len(bar_e) - 2):
        before = sum(bar_e[b - 4:b]) / 4
        after = min(bar_e[b:b + 2])
        before_l = sum(bar_low[b - 4:b]) / 4
        after_l = min(bar_low[b:b + 2])
        j = (after - before) + 0.5 * (after_l - before_l)
        if j > best:
            best, drop_bar = j, b
    drop_t = downs[drop_bar] / FPS if drop_bar is not None else None
    if drop_bar is not None and kicks:
        # snap to the kick where the low band actually arrives: largest low-energy step (0.5 s after vs before)
        lo_i = downs[max(0, drop_bar - 1)]
        hi_i = downs[min(len(downs) - 1, drop_bar + 1)]
        half = int(0.5 * FPS)
        best_k, best_step = None, -1.0
        for i, _s in kicks:
            if lo_i <= i <= hi_i and i - half >= 0 and i + half < len(envl):
                step = float(envl[i:i + half].mean() - envl[i - half:i].mean())
                if step > best_step:
                    best_step, best_k = step, i
        if best_k is not None and best_step > 0:
            drop_t = best_k / FPS

    D = a.duration if a.duration else total
    if a.start == "auto":
        if drop_t is not None and best > 0.12:
            want = drop_t - a.drop_at * D
        else:
            nb = max(1, int(D / (240 / bpm)))
            want_bar = max(range(max(1, len(bar_e) - nb)), key=lambda b: sum(bar_e[b:b + nb]))
            want = downs[want_bar] / FPS
        want = min(max(0.0, want), max(0.0, total - D))
        start = min((d / FPS for d in downs), key=lambda d: abs(d - want)) if downs else 0.0
        if start + D > total:
            start = max(0.0, total - D)
    else:
        start = float(a.start)
    end = start + D
    rel = lambda f: round(f / FPS - start, 3)
    inwin = lambda f: start - 1e-6 <= f / FPS < end
    bar_starts = [d for d in downs if inwin(d)]
    out = {
        "track": os.path.abspath(a.track), "track_duration": round(total, 3), "start": round(start, 3), "duration": round(D, 3),
        "bpm": round(bpm, 2), "beats": [rel(b) for b in beats if inwin(b)], "downbeats": [rel(d) for d in bar_starts],
        "kicks": [[rel(i), round(s, 3)] for i, s in kicks if inwin(i)],
        "bar_energy": [round(bar_e[downs.index(d)], 3) for d in bar_starts if downs.index(d) < len(bar_e)],
        "low_energy": [round(bar_low[downs.index(d)], 3) for d in bar_starts if downs.index(d) < len(bar_low)],
        "drop": round(drop_t - start, 3) if drop_t is not None and start <= drop_t < end else None,
        "drop_strength": round(best, 3),
        "note": "bpm/beats are an autocorrelation estimate for the song map; cut on beatgrid_fit.py's phase-exact grid",
    }
    s = json.dumps(out, indent=1)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        open(a.out, "w").write(s)
    print("bpm %.2f  start %.3f  drop %s (strength %.3f)  beats %d  kicks %d%s" % (
        out["bpm"], out["start"], out["drop"], out["drop_strength"], len(out["beats"]), len(out["kicks"]), "  -> " + a.out if a.out else ""))


if __name__ == "__main__":
    main()
