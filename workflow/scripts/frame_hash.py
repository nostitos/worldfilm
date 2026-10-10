#!/usr/bin/env python3
"""frame_hash.py — per-frame hashes of decoded video, to prove a change left a film pixel-identical
(worldfilm gate `frame_hash`): the same proof as comparing two masters' ffmpeg framemd5 output.

usage:
  frame_hash.py video.mp4 --out gates/hashes.json                 # MD5 per decoded frame (ffmpeg -f framemd5)
  frame_hash.py --compare a.json b.json [--psnr-min 46 --video-a a.mp4 --video-b b.mp4] [--out gates/hash-compare.json]
     exact: lists the first differing frames; with --psnr-min and both videos, frames that differ only below
     the PSNR threshold are reported as "tolerated" (Mac GPU renders differ at >= 46 dB run to run) and the
     gate passes when every differing frame is tolerated.
exit 0 = identical / within tolerance, 1 = differences, 2 = usage error
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wf_common import FFMPEG, die, probe, write_report  # noqa: E402


def framemd5(path):
    r = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-map", "0:v:0", "-f", "framemd5", "-"], capture_output=True, text=True)
    if r.returncode != 0:
        die("ffmpeg framemd5 failed: " + r.stderr.strip())
    hashes = []
    for line in r.stdout.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        hashes.append(parts[-1])
    return hashes


def psnr_per_frame(a, b):
    r = subprocess.run([FFMPEG, "-v", "error", "-i", a, "-i", b, "-lavfi", "psnr=stats_file=-", "-f", "null", "-"], capture_output=True, text=True)
    vals = []
    for line in r.stdout.splitlines():
        kv = dict(p.split(":", 1) for p in line.split() if ":" in p)
        if "psnr_avg" in kv:
            v = kv["psnr_avg"]
            vals.append(float("inf") if v == "inf" else float(v))
    return vals


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", nargs="?")
    ap.add_argument("--out", default=None)
    ap.add_argument("--compare", nargs=2, metavar=("A_JSON", "B_JSON"))
    ap.add_argument("--psnr-min", type=float, default=None)
    ap.add_argument("--video-a", default=None)
    ap.add_argument("--video-b", default=None)
    a = ap.parse_args()

    if a.compare:
        A = json.load(open(a.compare[0]))
        B = json.load(open(a.compare[1]))
        ha, hb = A["hashes"], B["hashes"]
        n = min(len(ha), len(hb))
        diff = [i for i in range(n) if ha[i] != hb[i]]
        length_diff = len(ha) != len(hb)
        tolerated, below = [], []
        if diff and a.psnr_min is not None and a.video_a and a.video_b:
            ps = psnr_per_frame(a.video_a, a.video_b)
            for i in diff:
                v = ps[i] if i < len(ps) else 0.0
                (tolerated if v >= a.psnr_min else below).append({"frame": i, "psnr": None if v == float("inf") else round(v, 2)})
        else:
            below = [{"frame": i, "psnr": None} for i in diff]
        ok = not length_diff and not below
        status = "PASS" if ok else "FAIL"
        fps = A.get("fps") or 30
        report = {"gate": "frame_hash", "status": status, "a": A["video"], "b": B["video"], "frames": [len(ha), len(hb)],
                  "measured": {"differing_frames": len(diff), "tolerated": len(tolerated), "beyond_tolerance": len(below),
                               "first_differences": [{"frame": i, "t": round(i / fps, 4)} for i in diff[:20]]},
                  "threshold": {"psnr_min": a.psnr_min}, "beyond_tolerance": below[:200], "tolerated_sample": tolerated[:50]}
        out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.compare[0])), "hash-compare.json")
        write_report(out, report)
        print("frame_hash gate: %s — %d/%d frames differ (%d tolerated, %d beyond) -> %s" % (status, len(diff), n, len(tolerated), len(below), out))
        for d in report["measured"]["first_differences"][:10]:
            print("  frame %5d  t=%.3fs" % (d["frame"], d["t"]))
        sys.exit(0 if ok else 1)

    if not a.video:
        ap.error("pass a video, or --compare a.json b.json")
    info = probe(a.video)
    hashes = framemd5(a.video)
    with open(a.video, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    report = {"video": os.path.abspath(a.video), "sha256": sha, "fps": info["fps"], "frames": len(hashes),
              "size": [info["width"], info["height"]], "method": "ffmpeg -f framemd5 (decoded frames)", "hashes": hashes}
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.video)), "gates", "hashes.json")
    write_report(out, report)
    print("frame_hash: %d frames hashed -> %s" % (len(hashes), out))


if __name__ == "__main__":
    main()
