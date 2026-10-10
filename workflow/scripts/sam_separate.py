#!/usr/bin/env python3
"""sam_separate.py — separate one subject (a person, product, hand) from the background of a video with SAM 2.1,
locally (worldfilm stage 3, the footage layer). Writes a hard mask per frame, a green-highlight preview to check
what was picked up, and an RGBA cutout (VP9 WebM with alpha, which Chrome plays inside a HyperFrames
composition) so graphics can be placed between the subject and the background.

Adapted from MIT-licensed code (see THIRD_PARTY_NOTICES.md): scan the machine, pick the model size, click points
on the first frame, propagate in 60-frame chunks seeded by the previous chunk's last mask. Needs studio/.venv
(torch, transformers >= 5, opencv-python-headless, numpy) and ffmpeg; the first run downloads the model
(~156-898 MB) into ~/.cache/huggingface.

usage: sam_separate.py clip.mp4 --points "480,270;100,60" --labels "1,0" [--start 0] [--end 89] [--width 960]
                       [--out footage/clip-sep] [--model auto|tiny|small|base-plus|large] [--chunk 60] [--no-cutout]
  --points are pixel coordinates on the --start frame at --width (the analysis width; a grid preview is written
  first: <out>/pick-frame.jpg). Label 1 = subject, 0 = leave out. Output: <out>/masks/%05d.png (white = subject),
  <out>/preview.mp4 (green subject), <out>/cutout.webm (alpha), <out>/separation.json (coverage per frame).
exit 0 = done, 2 = usage / dependency error
"""
import argparse
import json
import os
import platform
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--points", default=None, help='"x,y;x,y" on the start frame at --width')
    ap.add_argument("--labels", default=None, help='"1,0" matching --points')
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=None, help="last frame (inclusive); default: last frame of the clip")
    ap.add_argument("--width", type=int, default=960, help="analysis width (masks are upscaled to the source)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--model", default="auto")
    ap.add_argument("--chunk", type=int, default=60)
    ap.add_argument("--no-cutout", action="store_true")
    ap.add_argument("--pick-only", action="store_true", help="write the grid preview of the start frame and exit")
    a = ap.parse_args()
    try:
        import cv2
        import numpy as np
    except Exception as e:
        print("missing dependency: %s (uv pip install opencv-python-headless numpy into studio/.venv)" % e)
        sys.exit(2)
    out = a.out or os.path.splitext(a.video)[0] + "-sep"
    os.makedirs(out, exist_ok=True)
    cap = cv2.VideoCapture(a.video)
    if not cap.isOpened():
        sys.exit("cannot open " + a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    src_w, src_h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    end = a.end if a.end is not None else total - 1
    W = a.width
    H = int(round(src_h * W / src_w))

    def read_frames(s, e):
        cap.set(cv2.CAP_PROP_POS_FRAMES, s)
        fr = []
        for _ in range(s, e + 1):
            ok, im = cap.read()
            if not ok:
                break
            fr.append(cv2.cvtColor(cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB))
        return fr

    first = read_frames(a.start, a.start)[0]
    grid = cv2.cvtColor(first, cv2.COLOR_RGB2BGR).copy()
    for x in range(0, W, 80):
        cv2.line(grid, (x, 0), (x, H), (0, 255, 255), 1)
        cv2.putText(grid, str(x), (x + 2, 12), 0, 0.4, (0, 255, 255), 1)
    for y in range(0, H, 60):
        cv2.line(grid, (0, y), (W, y), (0, 255, 255), 1)
        cv2.putText(grid, str(y), (2, y - 2), 0, 0.4, (0, 255, 255), 1)
    cv2.imwrite(os.path.join(out, "pick-frame.jpg"), grid)
    if a.pick_only or not a.points:
        print("pick points on %s (analysis size %dx%d), then rerun with --points/--labels" % (os.path.join(out, "pick-frame.jpg"), W, H))
        return
    pts = [[int(v) for v in p.split(",")] for p in a.points.split(";") if p.strip()]
    lbl = [int(v) for v in (a.labels or ",".join("1" for _ in pts)).split(",")]
    if len(lbl) != len(pts):
        sys.exit("--labels must match --points")

    try:
        import torch
        from transformers import Sam2VideoModel, Sam2VideoProcessor
    except Exception as e:
        print("missing dependency: %s (uv pip install torch transformers into studio/.venv)" % e)
        sys.exit(2)
    if torch.cuda.is_available():
        gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        dev, auto = "cuda", "large" if gb >= 12 else "base-plus"
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        dev, auto = "mps", "base-plus"
    else:
        dev, auto = "cpu", "tiny"
    size = auto if a.model == "auto" else a.model
    model_id = "facebook/sam2.1-hiera-" + size
    print("system %s %s | device %s | model %s | frames %d-%d of %d at %dx%d" % (platform.system(), platform.machine(), dev, model_id, a.start, end, total, W, H))
    model = Sam2VideoModel.from_pretrained(model_id).to(dev)
    proc = Sam2VideoProcessor.from_pretrained(model_id)

    def separate_chunk(frames, points=None, labels=None, mask=None):
        s = proc.init_video_session(video=frames, inference_device=dev, video_storage_device="cpu", inference_state_device="cpu", dtype=torch.float32)
        if mask is None:
            proc.add_inputs_to_inference_session(inference_session=s, frame_idx=0, obj_ids=1, input_points=[[points]], input_labels=[[labels]])
        else:
            proc.add_inputs_to_inference_session(inference_session=s, frame_idx=0, obj_ids=1, input_masks=mask.astype(np.uint8))
        res = {}
        with torch.inference_mode():
            model(inference_session=s, frame_idx=0)
            for o in model.propagate_in_video_iterator(s, start_frame_idx=0):
                m = proc.post_process_masks([o.pred_masks], original_sizes=[[H, W]], binarize=True)[0]
                res[o.frame_idx] = m.squeeze().cpu().numpy().astype(bool)
        return res

    masks = {}
    seed = None
    s = a.start
    while s <= end:
        e = min(end, s + a.chunk - 1)
        fr = read_frames(s, e)
        if not fr:
            break
        r = separate_chunk(fr, points=pts, labels=lbl) if seed is None else separate_chunk(fr, mask=seed)
        for k, m in r.items():
            masks[s + k] = m
        seed = r[len(fr) - 1]
        print("  frames %d-%d done" % (s, s + len(fr) - 1), flush=True)
        s = e + 1
    mdir = os.path.join(out, "masks")
    os.makedirs(mdir, exist_ok=True)
    coverage = {}
    for f, m in masks.items():
        cv2.imwrite(os.path.join(mdir, "%05d.png" % f), cv2.resize(m.astype(np.uint8) * 255, (src_w, src_h), interpolation=cv2.INTER_NEAREST))
        coverage[f] = round(float(m.mean()), 4)

    # preview (green subject, original size) and the RGBA cutout
    n = end - a.start + 1
    cap.set(cv2.CAP_PROP_POS_FRAMES, a.start)
    prev = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (src_w, src_h), "-r", str(fps), "-i", "-",
                             "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", os.path.join(out, "preview.mp4")], stdin=subprocess.PIPE)
    cut = None
    if not a.no_cutout:
        cut = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", "%dx%d" % (src_w, src_h), "-r", str(fps), "-i", "-",
                                "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "24", "-auto-alt-ref", "0", os.path.join(out, "cutout.webm")], stdin=subprocess.PIPE)
    col = np.array([20, 255, 57], np.float32)
    for f in range(a.start, end + 1):
        ok, img = cap.read()
        if not ok or f not in masks:
            break
        m = cv2.resize(masks[f].astype(np.float32), (src_w, src_h), interpolation=cv2.INTER_LINEAR)
        mb = cv2.GaussianBlur(m, (5, 5), 0)
        edge = cv2.morphologyEx((mb > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((7, 7), np.uint8)).astype(np.float32)
        glow = np.clip(cv2.GaussianBlur(edge, (37, 37), 0) * 2.5, 0, 1)[..., None]
        im = img.astype(np.float32)
        g = im * (1 - mb[..., None] * 0.35) + col * mb[..., None] * 0.35 + col * glow * 0.9
        g = g * (1 - edge[..., None]) + np.array([220, 255, 200], np.float32) * edge[..., None]
        prev.stdin.write(np.clip(g, 0, 255).astype(np.uint8).tobytes())
        if cut is not None:
            rgba = np.dstack([cv2.cvtColor(img, cv2.COLOR_BGR2RGB), (mb * 255).astype(np.uint8)])
            cut.stdin.write(np.ascontiguousarray(rgba).tobytes())
    prev.stdin.close()
    prev.wait()
    if cut is not None:
        cut.stdin.close()
        cut.wait()
    rep = {"video": os.path.abspath(a.video), "frames": [a.start, end], "fps": fps, "size": [src_w, src_h], "analysis_size": [W, H], "device": dev, "model": model_id,
           "points": pts, "labels": lbl, "coverage": coverage, "coverage_mean": round(sum(coverage.values()) / max(1, len(coverage)), 4),
           "outputs": {"masks": mdir, "preview": os.path.join(out, "preview.mp4"), "cutout": None if a.no_cutout else os.path.join(out, "cutout.webm")}}
    json.dump(rep, open(os.path.join(out, "separation.json"), "w"), indent=1)
    print("separated %d frames; subject covers %.1f%% of the frame on average -> %s" % (len(masks), rep["coverage_mean"] * 100, out))


if __name__ == "__main__":
    main()
