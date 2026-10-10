#!/usr/bin/env python3
"""synth_clips.py — deterministic synthetic clips that exercise the worldfilm gates (see tests/README.md).

Writes into --out (default tests/out):
  pop.mp4         4 s @ 30 fps: a square eases across; a hard cut at 2.0 s (background flips); frame 45 is a
                  one-frame white flash; frame 90 is a one-frame pop (the square jumps 40 px and comes back).
  loop-good.mp4   2 s @ 30 fps: a square on a closed circle (frame 60 == frame 0 in motion).
  loop-seam.mp4   the same loop but the circle stops 4 px short: a visible seam.
  base.mp4        3 s @ 30 fps: a square on an expo.out ease (the baseline for frame_hash).
  base-copy.mp4   the same clip rendered again (must hash identical).
  eased.mp4       the same clip with the ease changed to expo.inOut (frames 1..~80 differ).
Needs numpy and ffmpeg.
"""
import argparse
import math
import os
import subprocess

import numpy as np

W, H, FPS = 320, 180, 30


def write(path, frames):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv444p", path], stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(np.ascontiguousarray(f, dtype=np.uint8).tobytes())
    p.stdin.close()
    p.wait()
    assert p.returncode == 0, path


def square(bg, x, y, size=40, color=(240, 200, 60)):
    f = np.empty((H, W, 3), np.uint8)
    f[:] = bg
    x0, y0 = int(round(x)), int(round(y))
    f[max(0, y0):min(H, y0 + size), max(0, x0):min(W, x0 + size)] = color
    return f


def expo_out(u):
    return 1 - 2 ** (-10 * u) if u < 1 else 1


def expo_inout(u):
    if u <= 0 or u >= 1:
        return min(1, max(0, u))
    return 2 ** (20 * u - 10) / 2 if u < 0.5 else (2 - 2 ** (-20 * u + 10)) / 2


def pop_clip():
    n = 4 * FPS
    frames = []
    for i in range(n):
        t = i / FPS
        bg = (24, 28, 40) if t < 2.0 else (120, 60, 40)
        u = (t % 2.0) / 2.0
        x = 20 + expo_out(u) * (W - 80)
        y = 70 + 10 * math.sin(t * 3)
        if i == 90:
            x += 40
        f = square(bg, x, y)
        if i == 45:
            f[:] = 255
        frames.append(f)
    return frames


def loop_clip(short_px):
    n = 2 * FPS
    frames = []
    for i in range(n):
        u = i / n
        ang = 2 * math.pi * u * (1 - short_px / (2 * math.pi * 50)) if short_px else 2 * math.pi * u
        x = W / 2 - 20 + 50 * math.cos(ang)
        y = H / 2 - 20 + 50 * math.sin(ang)
        frames.append(square((30, 30, 34), x, y))
    return frames


def base_clip(ease):
    n = 3 * FPS
    frames = []
    for i in range(n):
        u = min(1.0, i / (2.5 * FPS))
        x = 20 + ease(u) * (W - 80)
        frames.append(square((18, 20, 26), x, 70))
    return frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    write(os.path.join(a.out, "pop.mp4"), pop_clip())
    write(os.path.join(a.out, "loop-good.mp4"), loop_clip(0))
    write(os.path.join(a.out, "loop-seam.mp4"), loop_clip(4))
    write(os.path.join(a.out, "base.mp4"), base_clip(expo_out))
    write(os.path.join(a.out, "base-copy.mp4"), base_clip(expo_out))
    write(os.path.join(a.out, "eased.mp4"), base_clip(expo_inout))
    print("wrote synthetic clips to", a.out)


if __name__ == "__main__":
    main()
