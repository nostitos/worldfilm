#!/usr/bin/env python3
"""synth_sfx.py — code-synthesized sound from a JSON cue sheet: generators, mixer, K-weighted mastering, stems.

The generators, the mastering and the BS.1770 loudness meter are adapted from MIT-licensed code (see
THIRD_PARTY_NOTICES.md) and driven by a JSON cue sheet, so the picture's event table (`events(t)`) can be
rendered without writing Python; kick / hat / sub generators were added for scores. numpy is required
(studio/.venv); scipy speeds up the K-weighting filters when present.

Cue sheet (JSON):
{
  "duration": 30.0, "seed": 11, "target_lufs": -14.0, "ceiling_db": -2.0, "fade_out": 0.25,
  "silence": [[26.0, 28.0]],                               # exact digital silence (zeros) in every output
  "pad": {"group": "score", "gain": 0.25, "chords": [[0.0, [110, 164.81, 220]], [9.0, [98, 146.83, 196]]],
          "volume": [[0, 0.3], [20, 0.6], [25.5, 0.0]]},      # optional music bed (piecewise-linear volume)
  "cues": [ {"id": "halving-1", "t": 9.0, "gen": "kick", "args": {"f0": 55}, "gain": 0.9, "pan": 0.0, "group": "score"},
            {"id": "whoosh-s03", "t": 12.6, "gen": "whoosh", "args": {"dur": 0.5, "f0": 400, "f1": 2400}, "gain": 0.35, "group": "sfx",
             "align": "peak"} ]                                 # align "peak": t is where the loudest sample lands (default "start")
}

usage: synth_sfx.py cues.json --out assets/mix.wav [--stems assets/stems] [--list] [--report gates/audio-synth.json]
  --stems writes one mastered WAV per group (same gain as the mix, no soft clip) e.g. score.wav, sfx.wav.
  Every cue's placed peak time is written to the report so prove_audible.py can check it in the delivered file.
       synth_sfx.py --master-stem assets/stems/score.wav --out assets/music-only.wav [--target-lufs -14] [--ceiling-db -2]
  A stem carries the MIX's gain, so on its own it is quieter than the target (a score without its sfx measured -16.3 LUFS).
  --master-stem applies one linear gain to reach the target under the true-peak ceiling: exact zeros stay exact zeros
  (the silence windows survive), nothing is clipped or compressed, and the gain and the result are printed.
"""
import argparse
import json
import math
import os
import struct
import sys
import wave

import numpy as np

try:
    from scipy.signal import lfilter  # type: ignore
except Exception:  # pragma: no cover
    lfilter = None

SR = 48000
_rng = np.random.default_rng(11)


def seed(s):
    global _rng
    _rng = np.random.default_rng(int(s))


def noise(n):
    return _rng.uniform(-1.0, 1.0, n)


def t_axis(n):
    return np.arange(n) / SR


# ----------------------------------------------------------------------------------------------- generators
def bandnoise(n, fc, q=0.8):
    """White noise through a state-variable band-pass; fc is a scalar or an array of cutoffs (Hz) per sample."""
    fc = np.broadcast_to(np.asarray(fc, dtype=float), (n,))
    f = 2 * np.sin(np.pi * np.minimum(fc, SR / 6) / SR)
    x = noise(n)
    out = np.empty(n)
    low = band = 0.0
    for k in range(n):  # recursive filter: a per-sample loop (n is at most a few seconds of audio)
        low += f[k] * band
        high = x[k] - low - q * band
        band += f[k] * high
        out[k] = band
    return out


def click(freq=1800.0, dur=0.05):
    """UI click: a control snapping, a toggle, a tick. Higher freq sounds smaller."""
    t = t_axis(int(dur * SR))
    return np.sin(2 * np.pi * freq * t) * np.exp(-t / 0.012) + noise(len(t)) * np.exp(-t / 0.0015) * 0.6


def key(fc=None):
    """One keystroke; every call differs. Use typing() for a run of them."""
    n = int(0.018 * SR)
    fc = fc or float(_rng.uniform(2400, 4200))
    k = np.arange(n)
    thock = float(_rng.uniform(160, 220))
    return bandnoise(n, fc, q=0.5) * np.exp(-k / (0.0025 * SR)) * 2.2 + np.sin(2 * np.pi * thock * k / SR) * np.exp(-k / (0.006 * SR)) * 0.5


def blip(freq=440.0, dur=0.35, tau=0.12):
    """Soft tonal blip: a word or element landing, one note of a sequence. Keep freq in key."""
    t = t_axis(int(dur * SR))
    ph = 2 * np.pi * freq * t
    a = np.minimum(1, t / 0.003) * np.exp(-t / tau)
    return a * (np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph))


def pop(f0=400.0, f1=900.0, dur=0.16):
    """Pitched pop: a badge, chip or callout popping in. Sweeps f0 to f1."""
    t = t_axis(int(dur * SR))
    f = f0 * (f1 / f0) ** np.minimum(1, t / 0.06)
    ph = np.cumsum(2 * np.pi * f / SR)
    return np.minimum(1, t / 0.002) * np.exp(-t / 0.045) * np.sin(ph)


def chime(freqs=(523.25, 659.25, 783.99), dur=1.8, tau=0.7):
    """Bell chord: success, arrival, a payoff. Pass freqs from the film's key."""
    t = t_axis(int(dur * SR))
    out = np.zeros(len(t))
    for j, f in enumerate(freqs):
        g = 1.0 / (1 + j * 0.35)
        a = np.minimum(1, t / 0.004) * np.exp(-t / tau)
        out += g * a * (np.sin(2 * np.pi * f * t) + 0.18 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 0.15))
    return out


def whoosh(dur=0.6, f0=300.0, f1=2400.0, peak=0.6, q=0.9):
    """Air whoosh: movement, reveals, transitions. f0 to f1 sets direction; peak (0..1) is where it is loudest."""
    n = int(dur * SR)
    k = np.arange(n) / n
    p = math.log(0.5) / math.log(peak)
    return bandnoise(n, f0 * (f1 / f0) ** k, q=q) * np.sin(np.pi * k ** p) ** 2 * 1.6


def riser(dur=2.0, f0=260.0, f1=5200.0):
    """Build-up into a payoff. End it exactly on the hit; one big riser per film."""
    n = int(dur * SR)
    k = np.arange(n) / n
    ph = np.cumsum(2 * np.pi * (180 * 4.0 ** k) / SR)
    tail = np.minimum(1, (n - np.arange(n)) / (0.02 * SR))
    return (bandnoise(n, f0 * (f1 / f0) ** k, q=0.6) * 1.3 + 0.35 * np.sin(ph)) * k ** 2.2 * tail


def impact(dur=1.2):
    """Low impact for the hero moment. One per film."""
    t = t_axis(int(dur * SR))
    f = 38 + 60 * np.exp(-t / 0.07)
    ph = np.cumsum(2 * np.pi * f / SR)
    lp = np.empty(len(t))
    v = 0.0
    nz = noise(len(t))
    for k in range(len(t)):
        v += 0.08 * (nz[k] - v)
        lp[k] = v
    s = np.sin(ph) * np.exp(-t / 0.38) + lp * np.exp(-t / 0.05) * 3.0
    return np.tanh(1.6 * s)


def kick(f0=55.0, dur=0.45, punch=160.0):
    """Electronic kick: pitch drops from punch Hz to f0, short click on top. Beat markers and halvings."""
    t = t_axis(int(dur * SR))
    f = f0 + (punch - f0) * np.exp(-t / 0.03)
    ph = np.cumsum(2 * np.pi * f / SR)
    body = np.sin(ph) * np.exp(-t / 0.12)
    tick = noise(len(t)) * np.exp(-t / 0.002) * 0.5
    return np.tanh(1.8 * (body + tick))


def hat(dur=0.06, fc=8000.0, open_=False):
    """Hi-hat: band-passed noise, closed (short) or open (longer tail)."""
    n = int((0.25 if open_ else dur) * SR)
    t = t_axis(n)
    return bandnoise(n, fc, q=0.4) * np.exp(-t / (0.06 if open_ else 0.012)) * 1.2


def sub(freq=41.2, dur=2.0, attack=0.02, release=0.3):
    """Sub bass note (sine with a touch of 2nd harmonic). Hold under a drop; keep one at a time."""
    t = t_axis(int(dur * SR))
    env = np.minimum(1, t / attack) * np.minimum(1, (dur - t) / release)
    return env * (np.sin(2 * np.pi * freq * t) + 0.15 * np.sin(4 * np.pi * freq * t))


def scratch(dur=0.5):
    """Pencil on paper: a sketch or line drawing itself on."""
    n = int(dur * SR)
    t = t_axis(n)
    nz = bandnoise(n, 3800 + 1400 * np.sin(t * 23), q=0.35)
    stroke = np.maximum(0.0, np.sin(t * 2 * np.pi * 7.5)) ** 3
    return nz * stroke * np.sin(np.pi * np.arange(n) / n) * 1.4


def texture(dur=4.0, fc=900.0, q=0.3, lfo=0.25):
    """Airy noise texture for atmosphere: slow band-pass sweep. Keep it 20 dB under everything."""
    n = int(dur * SR)
    t = t_axis(n)
    return bandnoise(n, fc * (1 + 0.5 * np.sin(2 * np.pi * lfo * t)), q=q) * 0.6


def tone(freq=440.0, dur=1.0, attack=0.01, release=0.2, harmonics=(1.0, 0.3, 0.1)):
    """Held tone with a few harmonics: counters, sustained markers, the A440 schedule tone."""
    t = t_axis(int(dur * SR))
    env = np.minimum(1, t / max(attack, 1e-4)) * np.minimum(1, np.maximum(0, (dur - t) / max(release, 1e-4)))
    out = np.zeros(len(t))
    for i, g in enumerate(harmonics):
        out += g * np.sin(2 * np.pi * freq * (i + 1) * t)
    return out * env / sum(harmonics)


GENERATORS = {f.__name__: f for f in (click, key, blip, pop, chime, whoosh, riser, impact, kick, hat, sub, scratch, texture, tone)}


def envelope(points):
    pts = sorted(points)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    def at(t):
        return float(np.interp(t, xs, ys))
    return at


def pad(duration, chords, volume=None, detune=0.6, tremolo=0.23, xfade=0.35):
    """Music bed: detuned sine stacks per chord with cross-fades; returns (left, right)."""
    n = int(duration * SR)
    t = t_axis(n)
    left = np.zeros(n)
    right = np.zeros(n)
    vol = np.interp(t, [p[0] for p in volume], [p[1] for p in volume]) if volume else np.ones(n)
    trem = 0.85 + 0.15 * np.sin(2 * np.pi * tremolo * t)
    for ci, (t0, freqs) in enumerate(chords):
        t_next = chords[ci + 1][0] if ci + 1 < len(chords) else None
        i0 = int(t0 * SR)
        i1 = n if t_next is None else min(n, int((t_next + xfade) * SR))
        if i1 <= i0:
            continue
        tt = t[i0:i1]
        w = np.ones(i1 - i0) if ci == 0 else np.minimum(1.0, (tt - t0) / xfade)
        if t_next is not None:
            w = w * np.clip(1 - (tt - t_next) / xfade, 0, 1)
        sl = np.zeros(i1 - i0)
        sr_ = np.zeros(i1 - i0)
        for j, f in enumerate(freqs):
            g = 1 / (1 + j * 0.5)
            sl += g * np.sin(2 * np.pi * (f - detune) * tt)
            sr_ += g * np.sin(2 * np.pi * (f + detune) * tt)
        v = w * vol[i0:i1] * trem[i0:i1]
        left[i0:i1] += sl * v
        right[i0:i1] += sr_ * v
    return left, right


# ----------------------------------------------------------------------------------------------- loudness
_SHELF_B = (1.53512485958697, -2.69169618940638, 1.19839281085285)
_SHELF_A = (1.0, -1.69065929318241, 0.73248077421585)
_HP_B = (1.0, -2.0, 1.0)
_HP_A = (1.0, -1.99004745483398, 0.99007225036621)


def _biquad(x, b, a):
    if lfilter is not None:
        return lfilter(b, a, x)
    y = np.empty_like(x)
    x1 = x2 = y1 = y2 = 0.0
    for i in range(len(x)):
        yi = b[0] * x[i] + b[1] * x1 + b[2] * x2 - a[1] * y1 - a[2] * y2
        x2, x1, y2, y1 = x1, x[i], y1, yi
        y[i] = yi
    return y


def integrated_lufs(left, right):
    """ITU-R BS.1770-4 integrated loudness with EBU R128 gating, 48 kHz stereo."""
    kl = _biquad(_biquad(left, _SHELF_B, _SHELF_A), _HP_B, _HP_A)
    kr = _biquad(_biquad(right, _SHELF_B, _SHELF_A), _HP_B, _HP_A)
    p = kl * kl + kr * kr
    block, hop = int(0.4 * SR), int(0.1 * SR)
    if len(p) < block:
        return float("-inf")
    cs = np.concatenate([[0.0], np.cumsum(p)])
    idx = np.arange(0, len(p) - block + 1, hop)
    z = (cs[idx + block] - cs[idx]) / block
    with np.errstate(divide="ignore"):
        l = -0.691 + 10 * np.log10(np.maximum(z, 1e-20))
    above = z[l > -70]
    if len(above) == 0:
        return float("-inf")
    rel = -0.691 + 10 * np.log10(above.mean()) - 10
    gated = above[(-0.691 + 10 * np.log10(above)) > rel]
    if len(gated) == 0:
        return float("-inf")
    return float(-0.691 + 10 * np.log10(gated.mean()))


def true_peak(x):
    """Linear true peak by 4x windowed-sinc interpolation."""
    taps = 8
    j = np.arange(-taps + 1, taps + 1)
    peak = float(np.abs(x).max()) if len(x) else 0.0
    for frac in (0.25, 0.5, 0.75):
        d = j - frac
        k = np.sin(np.pi * d) / (np.pi * d) * 0.5 * (1 + np.cos(np.pi * d / taps))
        peak = max(peak, float(np.abs(np.convolve(x, k[::-1], mode="same")).max()))
    return peak


# ----------------------------------------------------------------------------------------------- mixer
class Mix:
    def __init__(self, duration):
        self.duration = duration
        self.n = int(SR * duration)
        self.groups = {}
        self.placed = []

    def group(self, name):
        if name not in self.groups:
            self.groups[name] = (np.zeros(self.n), np.zeros(self.n))
        return self.groups[name]

    def put(self, t, samples, gain=1.0, pan=0.0, group="sfx", cue_id=None, gen=None, extra=None):
        ang = (pan + 1) * math.pi / 4
        gl, gr = gain * math.cos(ang), gain * math.sin(ang)
        i0 = int(round(t * SR))
        s = np.asarray(samples, dtype=float)
        lo, hi = max(0, i0), min(self.n, i0 + len(s))
        if hi <= lo:
            return
        L, R = self.group(group)
        seg = s[lo - i0:hi - i0]
        L[lo:hi] += seg * gl
        R[lo:hi] += seg * gr
        pk = int(np.abs(seg).argmax())
        rec = {"id": cue_id, "gen": gen, "t": t, "end": hi / SR, "peak_t": (lo + pk) / SR, "gain": gain, "pan": pan, "group": group}
        rec.update(extra or {})
        self.placed.append(rec)

    def put_stereo(self, t, left, right, gain=1.0, group="score"):
        i0 = int(round(t * SR))
        lo, hi = max(0, i0), min(self.n, i0 + len(left))
        L, R = self.group(group)
        L[lo:hi] += np.asarray(left[lo - i0:hi - i0]) * gain
        R[lo:hi] += np.asarray(right[lo - i0:hi - i0]) * gain

    def sum(self):
        L = np.zeros(self.n)
        R = np.zeros(self.n)
        for l, r in self.groups.values():
            L += l
            R += r
        return L, R

    def master(self, target_lufs=-14.0, ceiling_db=-2.0, fade_out=0.25, silence=()):
        """Soft-clip only when the ceiling would be crossed; set the gain for target_lufs; carve silence windows.
        Returns (left, right, stats). Stems get the same linear gain via stems()."""
        L, R = self.sum()
        fade = np.ones(self.n)
        fn = int(fade_out * SR)
        if fn > 0:
            fade[self.n - fn:] = np.linspace(1, 0, fn)
        peak = max(float(np.abs(L).max()), float(np.abs(R).max())) or 1.0
        ceiling = 10 ** (ceiling_db / 20)
        best = None
        for drive in (1.0, 1.2, 1.5, 1.8, 2.0, 2.2, 2.5, 3.0, 4.0):
            norm = math.tanh(drive)
            l = np.tanh(drive * L / peak) / norm * fade
            r = np.tanh(drive * R / peak) / norm * fade
            lufs = integrated_lufs(l, r)
            if lufs == float("-inf"):
                break
            gain = 10 ** ((target_lufs - lufs) / 20)
            tp = max(true_peak(l), true_peak(r))
            fit = min(gain, ceiling / tp)
            if best is None or fit / gain > best[0]:
                best = (fit / gain, drive, l, r, fit, tp, peak)
            if gain * tp <= ceiling:
                break
        if best is None:
            return np.zeros(self.n), np.zeros(self.n), {"lufs": float("-inf"), "peak_db": float("-inf"), "drive": 1.0, "gain": 1.0}
        _, drive, l, r, gain, tp, peak = best
        self._drive, self._peak, self._gain, self._fade = drive, peak, gain, fade
        out_l, out_r = l * gain, r * gain
        self._carve(out_l, out_r, silence)
        stats = {"lufs": integrated_lufs(out_l, out_r), "peak_db": 20 * math.log10(max(1e-9, gain * tp)), "drive": drive, "gain": gain}
        return out_l, out_r, stats

    def _carve(self, l, r, silence):
        edge = int(0.01 * SR)
        for t0, t1 in silence:
            i0, i1 = int(round(t0 * SR)), int(round(t1 * SR))
            a0, a1 = max(0, i0 - edge), min(self.n, i1 + edge)
            if i0 > a0:
                ramp = np.linspace(1, 0, i0 - a0)
                l[a0:i0] *= ramp
                r[a0:i0] *= ramp
            if a1 > i1:
                ramp = np.linspace(0, 1, a1 - i1)
                l[i1:a1] *= ramp
                r[i1:a1] *= ramp
            l[i0:i1] = 0.0
            r[i0:i1] = 0.0

    def stems(self, silence=()):
        """Per-group stereo pairs with the master's linear gain (no soft clip), same fade and silence."""
        out = {}
        for name, (L, R) in self.groups.items():
            norm = math.tanh(self._drive)
            l = np.tanh(self._drive * L / self._peak) / norm * self._fade * self._gain
            r = np.tanh(self._drive * R / self._peak) / norm * self._fade * self._gain
            self._carve(l, r, silence)
            out[name] = (l, r)
        return out


def write_wav(path, left, right):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    l = np.clip(left, -1, 1)
    r = np.clip(right, -1, 1)
    data = np.empty(2 * len(l), dtype="<i2")
    data[0::2] = np.round(l * 32767).astype("<i2")
    data[1::2] = np.round(r * 32767).astype("<i2")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(data.tobytes())


def render(sheet, out, stems_dir=None):
    seed(sheet.get("seed", 11))
    mix = Mix(float(sheet["duration"]))
    if sheet.get("pad"):
        p = sheet["pad"]
        l, r = pad(mix.duration, [(c[0], c[1]) for c in p["chords"]], volume=p.get("volume"), detune=p.get("detune", 0.6), tremolo=p.get("tremolo", 0.23))
        mix.put_stereo(0.0, l, r, gain=p.get("gain", 0.25), group=p.get("group", "score"))
    for cue in sheet.get("cues", []):
        gen = GENERATORS.get(cue["gen"])
        if gen is None:
            sys.exit("unknown generator %r (python3 synth_sfx.py --list)" % cue["gen"])
        s = gen(**cue.get("args", {}))
        t0 = float(cue["t"])
        if cue.get("align", "start") == "peak":
            t0 -= int(np.abs(s).argmax()) / SR
        extra = {k: cue[k] for k in ("audibility_db", "band", "event", "align") if k in cue}
        mix.put(t0, s, gain=float(cue.get("gain", 1.0)), pan=float(cue.get("pan", 0.0)), group=cue.get("group", "sfx"), cue_id=cue.get("id"), gen=cue["gen"], extra=extra)
    silence = [tuple(s) for s in sheet.get("silence", [])]
    l, r, stats = mix.master(target_lufs=float(sheet.get("target_lufs", -14.0)), ceiling_db=float(sheet.get("ceiling_db", -2.0)),
                             fade_out=float(sheet.get("fade_out", 0.25)), silence=silence)
    write_wav(out, l, r)
    written = {"mix": out}
    if stems_dir:
        for name, (sl, sr_) in mix.stems(silence).items():
            pth = os.path.join(stems_dir, name + ".wav")
            write_wav(pth, sl, sr_)
            written[name] = pth
    return {"written": written, "stats": stats, "cues": mix.placed, "silence": silence, "duration": mix.duration}


def read_wav(path):
    with wave.open(path, "rb") as wf:
        if wf.getsampwidth() != 2 or wf.getframerate() != SR:
            raise SystemExit("%s: need 16-bit %d Hz WAV (got %d-byte samples at %d Hz)" % (path, SR, wf.getsampwidth(), wf.getframerate()))
        n, ch = wf.getnframes(), wf.getnchannels()
        data = np.frombuffer(wf.readframes(n), dtype="<i2").astype(np.float64) / 32767.0
    if ch == 1:
        return data, data.copy()
    return data[0::2], data[1::2]


def master_stem(src, out, target_lufs=-14.0, ceiling_db=-2.0):
    """Linear gain only: g = min(target / measured, ceiling / true peak). Returns the stats dict."""
    l, r = read_wav(src)
    lufs = integrated_lufs(l, r)
    if lufs == float("-inf"):
        raise SystemExit("%s is silent" % src)
    tp = max(true_peak(l), true_peak(r)) or 1e-9
    want = 10 ** ((target_lufs - lufs) / 20)
    gain = min(want, 10 ** (ceiling_db / 20) / tp)
    ol, orr = l * gain, r * gain
    st = {"source": src, "out": out, "source_lufs": lufs, "source_peak_db": 20 * math.log10(tp), "gain_db": 20 * math.log10(gain),
          "lufs": integrated_lufs(ol, orr), "peak_db": 20 * math.log10(max(1e-9, gain * tp)), "ceiling_limited": gain < want - 1e-9}
    write_wav(out, ol, orr)
    return st


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cues", nargs="?")
    ap.add_argument("--out", default="assets/mix.wav")
    ap.add_argument("--stems", default=None)
    ap.add_argument("--report", default=None)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--master-stem", default=None, metavar="WAV", help="normalise an existing stem with one linear gain (see above)")
    ap.add_argument("--target-lufs", type=float, default=-14.0)
    ap.add_argument("--ceiling-db", type=float, default=-2.0)
    a = ap.parse_args()
    if a.list:
        for name, f in GENERATORS.items():
            print("%-8s %s" % (name, (f.__doc__ or "").strip().splitlines()[0]))
        return
    if a.master_stem:
        st = master_stem(a.master_stem, a.out, a.target_lufs, a.ceiling_db)
        print("wrote %s: %.1f LUFS, true peak %.1f dBFS (source %.1f LUFS, gain %+.2f dB%s)" % (
            a.out, st["lufs"], st["peak_db"], st["source_lufs"], st["gain_db"], ", ceiling-limited" if st["ceiling_limited"] else ""))
        if a.report:
            os.makedirs(os.path.dirname(os.path.abspath(a.report)) or ".", exist_ok=True)
            json.dump(st, open(a.report, "w"), indent=2)
        return
    if not a.cues:
        ap.error("pass a cue sheet JSON, or --list")
    sheet = json.load(open(a.cues))
    rep = render(sheet, a.out, a.stems)
    st = rep["stats"]
    print("wrote %s: %.1fs, %d cues, %.1f LUFS, true peak %.1f dBFS, drive %s" % (a.out, rep["duration"], len(rep["cues"]), st["lufs"], st["peak_db"], st["drive"]))
    if a.report:
        os.makedirs(os.path.dirname(os.path.abspath(a.report)) or ".", exist_ok=True)
        json.dump(rep, open(a.report, "w"), indent=2)


if __name__ == "__main__":
    main()
