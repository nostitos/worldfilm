"""wf_common.py — shared helpers for the worldfilm gate scripts (ffprobe/ffmpeg frame access, JSON reports).

Pixel work uses numpy when it is importable (studio/.venv) and falls back to the stdlib `array` module at a
smaller analysis size, so every gate still runs on a bare Python 3 with ffmpeg on PATH.
"""
import json
import os
import shutil
import subprocess
import sys
from array import array

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - stdlib fallback
    np = None

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"


def die(msg, code=2):
    print("error: " + msg, file=sys.stderr)
    sys.exit(code)


def probe(path):
    """Video stream facts: fps (float), nb_frames (int, counted when the container does not say), w, h, duration."""
    if not os.path.exists(path):
        die("no such file: " + path)
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=r_frame_rate,avg_frame_rate,nb_frames,width,height,duration:format=duration",
                        "-of", "json", path], capture_output=True, text=True)
    if r.returncode != 0:
        die("ffprobe failed on " + path + ": " + r.stderr.strip())
    d = json.loads(r.stdout)
    s = d["streams"][0]
    num, den = (s.get("avg_frame_rate") or s.get("r_frame_rate") or "30/1").split("/")
    fps = float(num) / float(den or 1)
    dur = float(s.get("duration") or d.get("format", {}).get("duration") or 0)
    nb = int(s.get("nb_frames") or 0)
    if nb <= 0:
        c = subprocess.run([FFPROBE, "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                            "stream=nb_read_frames", "-of", "csv=p=0", path], capture_output=True, text=True)
        try:
            nb = int(c.stdout.strip() or 0)
        except ValueError:
            nb = 0
    return {"fps": fps, "nb_frames": nb, "width": int(s["width"]), "height": int(s["height"]), "duration": dur}


def gray_frames(path, size=180, fps=None, start=None, duration=None):
    """Decode the video to 8-bit gray frames of `size` px on the long side (see rgb_frames for colour)."""
    return _frames(path, size, fps, start, duration, "gray", 1)


def rgb_frames(path, size=180, fps=None, start=None, duration=None):
    """Decode the video to 8-bit RGB frames of `size` px on the long side: (N, h, w, 3) with numpy, else
    a list of array('B') of length w*h*3. Colour matters: a chroma-only pop is invisible in luma."""
    return _frames(path, size, fps, start, duration, "rgb24", 3)


def _frames(path, size, fps, start, duration, pix_fmt, channels):
    """Decode the video to small frames.

    Returns (frames, w, h): frames is a numpy uint8 array (N, h, w) when numpy is available, else a list of
    `array('B')` rows of length w*h. `fps` resamples (None = native frames). `start`/`duration` trim in seconds.
    """
    info = probe(path)
    w0, h0 = info["width"], info["height"]
    if w0 >= h0:
        w, h = size, max(2, round(size * h0 / w0 / 2) * 2)
    else:
        h, w = size, max(2, round(size * w0 / h0 / 2) * 2)
    vf = []
    if fps:
        vf.append("fps=%s" % fps)
    vf.append("scale=%d:%d:flags=area" % (w, h))
    vf.append("format=" + pix_fmt)
    cmd = [FFMPEG, "-v", "error"]
    if start is not None:
        cmd += ["-ss", "%.6f" % start]
    cmd += ["-i", path]
    if duration is not None:
        cmd += ["-t", "%.6f" % duration]
    cmd += ["-vf", ",".join(vf), "-f", "rawvideo", "-pix_fmt", pix_fmt, "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        die("ffmpeg decode failed: " + r.stderr.decode(errors="replace").strip())
    raw = r.stdout
    fsz = w * h * channels
    n = len(raw) // fsz
    if np is not None:
        fr = np.frombuffer(raw[: n * fsz], dtype=np.uint8)
        fr = fr.reshape(n, h, w) if channels == 1 else fr.reshape(n, h, w, channels)
        return fr, w, h
    frames = []
    for i in range(n):
        a = array("B")
        a.frombytes(raw[i * fsz:(i + 1) * fsz])
        frames.append(a)
    return frames, w, h


def mean_abs_diff(a, b):
    """Mean absolute difference of two frames (0-255), over every channel present."""
    if np is not None:
        return float(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean())
    s = 0
    for x, y in zip(a, b):
        s += x - y if x >= y else y - x
    return s / len(a)


def mean_luma(a):
    """Mean luma (Rec.601 weights for RGB frames, plain mean for gray)."""
    if np is not None:
        if a.ndim == 3 and a.shape[-1] == 3:
            return float(0.299 * a[..., 0].mean() + 0.587 * a[..., 1].mean() + 0.114 * a[..., 2].mean())
        return float(a.mean())
    return sum(a) / len(a)


def percentile(xs, q):
    xs = sorted(xs)
    if not xs:
        return 0.0
    k = (len(xs) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def median(xs):
    xs = sorted(xs)
    if not xs:
        return 0.0
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2


def write_report(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path
