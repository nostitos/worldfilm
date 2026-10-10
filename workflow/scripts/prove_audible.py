#!/usr/bin/env python3
"""prove_audible.py — prove each sound cue is audible in the delivered file (worldfilm gate `audible`).

The rule, measured: a cue can exist in the source and contribute nothing to the mix. For
every cue this measures the delivered file's level in the cue's own band around its peak time and compares it
with the bed (the music-only stem at the same time when given, else the same band just before the cue). A cue
passes when it rises at least `audibility_db` above the bed (default +4 dB in-band lift) and
its peak lands on the event: sound may lag the picture by at most 125 ms or lead it by 45 ms (ITU-R BT.1359
detectability, plus half the measurement window); sustained cues are timed by onset instead of peak.

usage: prove_audible.py --mix renders/master.mp4 --cues gates/audio-synth.json [--bed assets/stems/score.wav]
                        [--default-db 4] [--window 0.12] [--tol 0.03] [--silence 25.5,27.5[;a,b]] [--out gates/audible.json]
  --cues: the report synth_sfx.py wrote (cues with t, end, peak_t, group), or a list [{id, t, peak_t?, band?:[lo,hi], audibility_db?}].
  Cues in group "score" are skipped unless they carry "audibility_db" themselves (the bed cannot be louder than itself).
  --silence: windows that must be silence in the delivered file (peak below -60 dBFS, 50 ms inside each edge: AAC
  pre-echo at the ramps measures around -75 dBFS and is inaudible; the WAV master measures -inf).
exit 0 = every cue audible, 1 = one or more inaudible or late, 2 = usage error
"""
import argparse
import json
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wf_common import FFMPEG, write_report  # noqa: E402

BANDS = {  # default analysis band per generator family (Hz)
    "kick": (30, 180), "sub": (25, 120), "impact": (30, 250), "click": (900, 4000), "key": (1500, 6000), "blip": (200, 2000),
    "pop": (250, 2500), "chime": (400, 6000), "whoosh": (300, 5000), "riser": (300, 7000), "scratch": (2000, 8000),
    "texture": (300, 3000), "hat": (4000, 12000), "tone": (200, 3000),
}


SR = 48000
PREROLL = 0.5   # seconds decoded before the window so the band filters have settled


def band_signal(path, t0, dur, lo, hi):
    """Mono f32 samples of the band [lo, hi] Hz over [t0, t0+dur], decoded once with pre-roll (filter transients
    at a slice edge must never be measured as the cue)."""
    s0 = max(0.0, t0 - PREROLL)
    af = "aformat=channel_layouts=mono" if lo is None else "aformat=channel_layouts=mono,highpass=f=%d:poles=2,lowpass=f=%d:poles=2" % (lo, hi)
    r = subprocess.run([FFMPEG, "-v", "error", "-ss", "%.4f" % s0, "-t", "%.4f" % (t0 - s0 + dur), "-i", path, "-vn", "-af", af, "-ar", str(SR), "-f", "f32le", "-"], capture_output=True)
    import array
    a = array.array("f")
    a.frombytes(r.stdout[: len(r.stdout) // 4 * 4])
    skip = int(round((t0 - s0) * SR))
    return a[skip:]


def rms_db(samples):
    n = len(samples)
    if n == 0:
        return float("-inf")
    s = 0.0
    for v in samples:
        s += v * v
    return float("-inf") if s <= 0 else 10 * math.log10(s / n)


def band_rms_db(path, t0, dur, lo, hi):
    """RMS level (dBFS) of the band [lo, hi] Hz in [t0, t0+dur]."""
    if t0 < 0:
        dur += t0
        t0 = 0
    if dur <= 0.005:
        return float("-inf")
    return rms_db(band_signal(path, t0, dur, lo, hi))


def onset_time(path, t0, dur, lo, hi):
    """First 10 ms slice (hop 5 ms) of the cue's band that rises within 6 dB of the band's maximum over [t0, t0+dur]:
    where a sustained cue starts, independent of where its loudest sample happens to fall."""
    t0 = max(0.0, t0)
    sig = band_signal(path, t0, dur, lo, hi)
    w = int(0.01 * SR)
    hop = int(0.005 * SR)
    levels = [(k, rms_db(sig[k:k + w])) for k in range(0, max(1, len(sig) - w + 1), hop)]
    mx = max((v for _, v in levels), default=float("-inf"))
    for k, v in levels:
        if v >= mx - 6:
            return t0 + k / SR
    return t0


def peak_time(path, t0, dur, lo=20, hi=20000, win=0.01):
    """Start time of the loudest `win`-second window (hop 5 ms) of the cue's own band in [t0, t0+dur]: a mid-band
    whoosh must not be timed by the bed's kick, and a broad envelope must not be timed by one lucky noise burst.
    The window start is the onset for a decaying sound (click, blip, impact) and sits before the peak for a swell,
    so only a genuinely late arrival reads as late."""
    t0 = max(0.0, t0)
    sig = band_signal(path, t0, dur, lo, hi)
    w = max(1, int(win * SR))
    hop = max(1, int(0.005 * SR))
    best_t, best = t0, float("-inf")
    for k in range(0, max(1, len(sig) - w + 1), hop):
        v = rms_db(sig[k:k + w])
        if v > best:
            best, best_t = v, t0 + k / SR
    return best_t


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mix", required=True)
    ap.add_argument("--cues", required=True)
    ap.add_argument("--bed", default=None)
    ap.add_argument("--default-db", type=float, default=4.0)
    ap.add_argument("--window", type=float, default=0.12, help="analysis window around the peak (s)")
    ap.add_argument("--tol", type=float, default=0.03, help="allowed peak timing error (s)")
    ap.add_argument("--silence", default="", help="digital-silence windows 'a,b;c,d' that must measure as zero")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    data = json.load(open(a.cues))
    cues = data["cues"] if isinstance(data, dict) else data
    results = []
    for c in cues:
        need = c.get("audibility_db")
        if c.get("group") == "score" and need is None:
            continue
        need = a.default_db if need is None else float(need)
        band = c.get("band") or BANDS.get(str(c.get("gen", c.get("id", ""))).split("-")[0], (200, 6000))
        pk = float(c.get("peak_t", c["t"]))
        w = a.window
        level = band_rms_db(a.mix, pk - w / 2, w, *band)
        if a.bed:
            bed = band_rms_db(a.bed, pk - w / 2, w, *band)
        else:
            bed = band_rms_db(a.mix, pk - w / 2 - 0.5, 0.4, *band)
        bed_floor = bed < -79.9                       # a silent bed: no lift can be measured; the cue passes on its own level (critic r6/r8)
        lift = (level - bed) if (level > float("-inf") and not bed_floor) else float("-inf")
        cue_len = float(c.get("end", c["t"] + 0.1)) - float(c["t"])
        win = 0.1 if cue_len > 0.5 else 0.03         # the loudest short window; its centre is the cue's peak
        measured_peak = peak_time(a.mix, pk - 0.25, 0.5, *band, win=win) + win / 2
        sustained = c.get("align", "start") != "peak" and (pk - float(c["t"])) > 0.1   # a held note's loudest sample is arbitrary: time it by its onset; peak-aligned cues are timed by their peak
        onset = None
        if sustained:
            onset = onset_time(a.mix, float(c["t"]) - 0.1, min(1.0, cue_len + 0.1), *band)
            late = (onset - float(c["t"])) > a.tol + 0.02
        else:
            delta = measured_peak - pk
            late = delta > 0.125 + win / 2 or delta < -(0.045 + win / 2)   # ITU-R BT.1359 detectability: sound may lag the picture by 125 ms or lead it by 45 ms (plus half the measurement window)
        ok = ((lift >= need) if not bed_floor else (level >= -40.0)) and not late
        results.append({"id": c.get("id"), "t": c.get("t"), "peak_t": pk, "timing": "onset" if sustained else "peak", "measured_onset_t": None if onset is None else round(onset, 3), "band_hz": list(band), "level_db": None if level == float("-inf") else round(level, 1),
                        "bed_db": None if bed_floor else round(bed, 1), "bed_floor": bed_floor, "lift_db": None if (bed_floor or lift == float("-inf")) else round(lift, 1),
                        "need_db": need, "measured_peak_t": round(measured_peak, 3), "delta_s": round(measured_peak - pk, 3), "late": late, "status": "PASS" if ok else "FAIL"})
    bad = [r for r in results if r["status"] == "FAIL"]
    silences = []
    for win in [w for w in a.silence.split(";") if w.strip()]:
        t0, t1 = [float(v) for v in win.split(",")]
        sig = band_signal(a.mix, t0 + 0.05, max(0.01, t1 - t0 - 0.1), None, None)   # raw: a band filter rings into the window
        pk = max((abs(v) for v in sig), default=0.0)
        pk_db = float("-inf") if pk <= 0 else 20 * math.log10(pk)
        ok_s = pk_db < -60
        silences.append({"from_s": t0, "to_s": t1, "peak_dbfs": None if pk_db == float("-inf") else round(pk_db, 1), "status": "PASS" if ok_s else "FAIL"})
    bad_sil = [s for s in silences if s["status"] == "FAIL"]
    status = "PASS" if not bad and not bad_sil else "FAIL"
    report = {"gate": "audible", "status": status, "mix": os.path.abspath(a.mix), "bed": os.path.abspath(a.bed) if a.bed else None,
              "measured": {"cues": len(results), "inaudible_or_late": len(bad), "silence_windows": len(silences), "silence_broken": len(bad_sil)},
              "threshold": {"default_db": a.default_db, "tol_s": a.tol, "silence_peak_dbfs_max": -60}, "cues": results, "silence": silences}
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.mix)), "gates", "audible.json")
    write_report(out, report)
    print("audible gate: %s — %d cues, %d inaudible/late; %d silence windows, %d broken -> %s" % (status, len(results), len(bad), len(silences), len(bad_sil), out))
    for s in silences:
        print("  %-5s silence %.2f-%.2fs peak %s dBFS" % (s["status"], s["from_s"], s["to_s"], s["peak_dbfs"] if s["peak_dbfs"] is not None else "-inf"))
    for r in results:
        print("  %-5s %-16s t=%7.3f  band %5d-%5d Hz  level %6s  bed %6s  lift %5s dB (need %+.1f)%s" % (
            r["status"], str(r["id"])[:16], r["peak_t"], r["band_hz"][0], r["band_hz"][1], r["level_db"], r["bed_db"], r["lift_db"], r["need_db"], "  LATE" if r["late"] else ""))
    sys.exit(0 if status == "PASS" else 1)


if __name__ == "__main__":
    main()
