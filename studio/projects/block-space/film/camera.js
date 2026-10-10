// film/camera.js — the pose graph (pure; no DOM): all poses of all shots form one key list, consecutive shots share
// their boundary pose (C1 across shots), pos and look are explicit channels, height in log space, monotone cubic.
import { DATA } from './data.js';

const keys = [];
for (const s of DATA.shots) for (const p of s.camera.poses) if (!keys.length || p.t > keys[keys.length - 1].t + 1e-6) keys.push(p);
const T = keys.map((k) => k.t);
const chan = (f) => keys.map(f);
const CH = { x: chan((k) => k.pos[0]), z: chan((k) => k.pos[2]), fov: chan((k) => k.fov), ly: chan((k) => Math.log(k.pos[1])), lx: chan((k) => k.look[0]), lyy: chan((k) => k.look[1]), lz: chan((k) => k.look[2]) };

// Fritsch-Carlson monotone cubic: no overshoot between keys, C1 at keys
export function monotone(xs, ys) {
  const n = xs.length, d = [], ms = [];
  for (let i = 0; i < n - 1; i++) d.push((ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]));
  ms.push(d[0]);
  for (let i = 1; i < n - 1; i++) ms.push(d[i - 1] * d[i] <= 0 ? 0 : (d[i - 1] + d[i]) / 2);
  ms.push(d[n - 2]);
  for (let i = 0; i < n - 1; i++) {
    if (d[i] === 0) { ms[i] = 0; ms[i + 1] = 0; continue; }
    const a = ms[i] / d[i], b = ms[i + 1] / d[i], s = a * a + b * b;
    if (s > 9) { const t = 3 / Math.sqrt(s); ms[i] = t * a * d[i]; ms[i + 1] = t * b * d[i]; }
  }
  return (x) => {
    if (x <= xs[0]) return ys[0];
    if (x >= xs[n - 1]) return ys[n - 1];
    let i = 0; while (x > xs[i + 1]) i++;
    const h = xs[i + 1] - xs[i], u = (x - xs[i]) / h;
    const h00 = 2 * u ** 3 - 3 * u ** 2 + 1, h10 = u ** 3 - 2 * u ** 2 + u, h01 = -2 * u ** 3 + 3 * u ** 2, h11 = u ** 3 - u ** 2;
    return h00 * ys[i] + h10 * h * ms[i] + h01 * ys[i + 1] + h11 * h * ms[i + 1];
  };
}
const F = { x: monotone(T, CH.x), z: monotone(T, CH.z), fov: monotone(T, CH.fov), ly: monotone(T, CH.ly), lx: monotone(T, CH.lx), lyy: monotone(T, CH.lyy), lz: monotone(T, CH.lz) };

export function cameraAt(t, aspect) {
  const x = F.x(t), z = F.z(t), y = Math.exp(F.ly(t));
  // dial 4: rests carry micro-drift (deterministic), never a still frame; stronger where the pose graph is stopped.
  // The drift is elliptical: height moves in quadrature with the lateral sway, so its velocity never passes through zero
  // (a one-axis sway is still at every turning point, every 1.85 s; the frozen_time gate read those instants as frozen
  // at 19.3, 21.2-21.3 and 23.0-23.3 s on the blur master). The ending's larger sway stays lateral so the end edge settles
  // monotonically (tools/sweep.mjs).
  const stopped = (t >= 17.4 && t <= 19.3) ? 1 : 0, ending = (t >= 24.6 && t <= 27.2) ? 1 : 0;
  const ampStop = 1 + 3 * stopped * Math.sin(Math.PI * Math.min(1, Math.max(0, (t - 17.4) / 1.9)));
  const amp = ampStop + 9 * ending * Math.sin(Math.PI * Math.min(1, Math.max(0, (t - 24.6) / 2.6)));
  const dz = amp * (0.05 * Math.sin(t * 1.7) + 0.03 * Math.sin(t * 0.61 + 1.0)), dy = ampStop * 0.04 * Math.cos(t * 1.7);
  let fov = F.fov(t);
  if (aspect < 1) fov = Math.min(100, 2 * Math.atan(Math.tan(fov * Math.PI / 360) * 1.6) * 180 / Math.PI); // keep the street in a portrait frame
  return { pos: [x, y + dy, z + dz], look: [F.lx(t), F.lyy(t), F.lz(t)], fov };
}

// the corner readout: the block at the centre of the frame (the look point); subsidy and year derive from THAT block
export function yearAt(h) {
  const ks = Object.keys(DATA.years).map(Number).sort((a, b) => a - b);
  let i = 0; while (i < ks.length - 2 && h > ks[i + 1]) i++;
  const a = ks[i], b = ks[i + 1];
  return DATA.years[String(a)] + (DATA.years[String(b)] - DATA.years[String(a)]) * Math.min(1, Math.max(0, (h - a) / (b - a)));
}
export function subsidySats(h) { const k = Math.floor(h / 210000); return k >= 33 ? 0 : Math.floor(5000000000 / Math.pow(2, k)); }   // GetBlockSubsidy: 5e9 >> era, truncating (exact below 2^53)
export function subsidyAt(h) { return subsidySats(h) / 1e8; }
export function fmtSats(sats) { const w = Math.floor(sats / 1e8), f = sats - w * 1e8; return w + '.' + String(f).padStart(8, '0'); }
export function subText(sats) { const t = fmtSats(sats); return t.indexOf('.') >= 0 ? t.replace(/0+$/, '').replace(/\.$/, '') : t; }
export function readoutAt(t, aspect = 16 / 9) {
  const cam = cameraAt(t, aspect);
  const lx = Math.max(0, Math.min(DATA.end_x, cam.look[0]));
  const h = Math.max(0, Math.min(DATA.last, Math.round(lx / DATA.u * DATA.period)));
  return { h, sub: subsidyAt(h), sats: subsidySats(h), subText: subText(subsidySats(h)), past: h <= DATA.tip, year: yearAt(h), cam };
}

// screen projection of a world point for a camera (pos, look, fov in degrees, up = +y): {x, y, visible}
export function project(cam, pt, width = 1920, height = 1080) {
  const f = [cam.look[0] - cam.pos[0], cam.look[1] - cam.pos[1], cam.look[2] - cam.pos[2]];
  const fl = Math.hypot(...f); f[0] /= fl; f[1] /= fl; f[2] /= fl;
  const r = [f[1] * 0 - f[2] * 1, f[2] * 0 - f[0] * 0, f[0] * 1 - f[1] * 0];   // f x up
  const rl = Math.hypot(...r) || 1; r[0] /= rl; r[1] /= rl; r[2] /= rl;
  const u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]];   // r x f
  const d = [pt[0] - cam.pos[0], pt[1] - cam.pos[1], pt[2] - cam.pos[2]];
  const z = d[0] * f[0] + d[1] * f[1] + d[2] * f[2];
  const x = d[0] * r[0] + d[1] * r[1] + d[2] * r[2];
  const y = d[0] * u[0] + d[1] * u[1] + d[2] * u[2];
  const tanv = Math.tan(cam.fov * Math.PI / 360), aspect = width / height;
  const nx = (x / z) / (tanv * aspect), ny = (y / z) / tanv;
  return { x: (nx + 1) / 2 * width, y: (1 - ny) / 2 * height, visible: z > 0.2 };
}

// the schedule's lines under the end card: gone by 27.4 s so no rung or spine crosses the type (critic r8)
export function ladderOpacityAt(t) { if (t < 26.5) return 1; if (t >= 27.0) return 0; const u = (t - 26.5) / 0.5; return 1 - (1 - Math.pow(2, -10 * u)) / (1 - Math.pow(2, -10)); }
