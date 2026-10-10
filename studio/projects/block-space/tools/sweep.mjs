// tools/sweep.mjs — every frame's readout must be self-consistent: the subsidy shown is the subsidy of the block shown
// (critic r3 caught block 210,000 next to 50 BTC), the block never runs backwards except at the designed profile
// swing, labels never overlap in time, and the readout stops exactly at 970,440 while the camera rests at NOW.
// Usage: node tools/sweep.mjs   (exit 1 on any violation)
import { readoutAt, subsidyAt, cameraAt, project, ladderOpacityAt, fmtSats } from '../film/camera.js';
const satsExact = (h) => { const k = BigInt(Math.floor(h / 210000)); return k >= 64n ? 0n : (5000000000n >> k); };   // independent of camera.js: BigInt right shift
import { DATA } from '../film/data.js';
const FPS = DATA.fps, N = Math.round(DATA.dur * FPS);
const errors = [];
let prev = -1;
for (let f = 0; f <= N; f++) {
  const t = f / FPS, r = readoutAt(t);
  if (BigInt(r.sats) !== satsExact(r.h)) errors.push('frame ' + f + ': subsidy ' + r.sats + ' sat does not match block ' + r.h + ' (exact ' + satsExact(r.h) + ')');
  if (fmtSats(r.sats) !== (satsExact(r.h) / 100000000n) + '.' + String(satsExact(r.h) % 100000000n).padStart(8, '0')) errors.push('frame ' + f + ': subsidy text ' + fmtSats(r.sats) + ' is not the exact satoshi text');
  if (r.h < prev - 2016 * 3 && !(t > 5.4 && t < 8.4)) errors.push('frame ' + f + ' (' + t.toFixed(2) + 's): block runs backwards ' + prev + ' -> ' + r.h);
  if (t >= 17.5 && t <= 19.2 && r.h !== DATA.tip) errors.push('frame ' + f + ': at NOW the readout is ' + r.h + ', not ' + DATA.tip);
  if (t >= 25.2 && t <= 26.9 && r.h !== DATA.last) errors.push('frame ' + f + ': at the end the readout is ' + r.h + ', not ' + DATA.last);
  prev = r.h;
}
const labels = DATA.shots.flatMap((s) => s.text.filter((x) => s.world_anchors.some((a) => a.text_id === x.id)).map((x) => ({ id: x.id, a: x.at_s, b: x.until_s }))).sort((p, q) => p.a - q.a);
for (let i = 1; i < labels.length; i++) if (labels[i].a < labels[i - 1].b - 1e-6) errors.push('labels overlap in time: ' + labels[i - 1].id + ' until ' + labels[i - 1].b + ' vs ' + labels[i].id + ' at ' + labels[i].a);
const caps = DATA.shots.flatMap((s) => s.text.filter((x) => x.role === 'caption').map((x) => ({ id: x.id, a: x.at_s, b: x.until_s }))).sort((p, q) => p.a - q.a);
for (let i = 1; i < caps.length; i++) if (caps[i].a < caps[i - 1].b - 1e-6) errors.push('captions overlap in time: ' + caps[i - 1].id + ' / ' + caps[i].id);
// the ground's end edge must settle in one direction (down the frame) from 23.0 to 27.0 and hold still under the number
let prevEdge = -1;
for (let f = Math.round(22.6 * FPS); f <= Math.round(30.0 * FPS); f++) {
  const t = f / FPS, cam = cameraAt(t, 16 / 9), e = project(cam, [DATA.end_x, 0, 0]);
  if (!e.visible || e.y < 0 || e.y > 1080) errors.push('frame ' + f + ' (' + t.toFixed(2) + 's): the end edge is out of frame (y ' + e.y.toFixed(0) + ')');
  if (t <= 27.0 && prevEdge >= 0 && e.y < prevEdge - 0.6) errors.push('frame ' + f + ' (' + t.toFixed(2) + 's): the end edge reverses ' + prevEdge.toFixed(1) + ' -> ' + e.y.toFixed(1));
  if (t > 27.0 && Math.abs(e.y - prevEdge) > 1.5) errors.push('frame ' + f + ' (' + t.toFixed(2) + 's): the end edge moves under the number ' + prevEdge.toFixed(1) + ' -> ' + e.y.toFixed(1));
  prevEdge = e.y;
}
// no label plate may touch the gate it names, any frame it is up (plate width estimated from the mono type: 18 px per glyph + 36 px padding; 50 px tall)
const ROADH = 2.1 - 0.1, GATES = {};
for (let k = 1; k <= 4; k++) GATES['halving-' + k] = { x: DATA.halving_x[String(k)], h: (50 / Math.pow(2, k - 1)) * DATA.hs * 1.12, thick: 0.35 };
GATES['now'] = { x: DATA.now_x, h: 3.0, thick: 0.3 };
GATES['halving-5'] = { x: DATA.halving_x['5'], h: Math.max(0.6, (50 / 32) * DATA.hs), thick: 0.1 };
GATES['last'] = { x: DATA.end_x, h: 0.3, thick: 0.3 };
const labelsAll = DATA.shots.flatMap((s) => s.world_anchors.map((a) => ({ anchor: a.anchor, text: s.text.find((x) => x.id === a.text_id), offset: a.offset_px || [0, 0] })));
for (const L of labelsAll) {
  const g = GATES[L.anchor]; if (!g || !L.text) continue;
  const w = L.text.content.length * 18 + 36, hgt = 50;
  for (let f = Math.ceil(L.text.at_s * FPS); f <= Math.floor(L.text.until_s * FPS); f++) {
    const t = f / FPS, cam = cameraAt(t, 16 / 9);
    const corners = [[g.x, 0, -ROADH], [g.x, 0, ROADH], [g.x, g.h, -ROADH], [g.x, g.h, ROADH], [g.x, g.h, ROADH + g.thick / 2], [g.x, g.h, -ROADH - g.thick / 2]].map((p) => project(cam, p));
    if (corners.some((c) => !c.visible)) continue;
    const gx0 = Math.min(...corners.map((c) => c.x)) - 4, gx1 = Math.max(...corners.map((c) => c.x)) + 4, gy0 = Math.min(...corners.map((c) => c.y)) - 4, gy1 = Math.max(...corners.map((c) => c.y)) + 4;
    const an = project(cam, [g.x, g.h + 0.6, L.anchor === 'last' ? 0 : 0]);
    const right = project(cam, [g.x, g.h, ROADH]), outer = project(cam, [g.x, g.h, ROADH + g.thick / 2]);
    let x = an.x + L.offset[0] - w / 2, y = an.y + L.offset[1] - hgt;
    let yc = Math.max(72, y);
    if (yc + hgt > right.y - 8) { x = outer.x + Math.abs(outer.x - right.x) + 24; yc = Math.max(72, right.y - hgt / 2); }   // the flip rule in film/main.js
    x = Math.max(96, Math.min(1920 - 96 - w, x)); yc = Math.max(72, Math.min(1080 - 260, yc));
    const hit = x < gx1 && x + w > gx0 && yc < gy1 && yc + hgt > gy0;
    if (hit && (gy1 - gy0) > 6) { errors.push('frame ' + f + ' (' + t.toFixed(2) + 's): label ' + L.text.id + ' [' + x.toFixed(0) + ',' + yc.toFixed(0) + ' ' + w + 'x' + hgt + '] touches gate ' + L.anchor + ' [' + gx0.toFixed(0) + '-' + gx1.toFixed(0) + ', ' + gy0.toFixed(0) + '-' + gy1.toFixed(0) + ']'); break; }
  }
}
const head = DATA.shots[8].text.find((x) => x.id === 'H-cap');
for (let f = Math.ceil(head.at_s * FPS); f <= Math.floor(head.until_s * FPS); f++) if (ladderOpacityAt(f / FPS) > 0.01) errors.push('frame ' + f + ': the ladder is visible (' + ladderOpacityAt(f / FPS).toFixed(2) + ') under the headline');
// the scheduled year model, stated once and tested: ten-minute blocks from the tip's header time, 365.25-day years, floored (facts F-FUTURE)
for (let f = 0; f <= N; f += 6) { const r = readoutAt(f / FPS); if (r.h > DATA.tip) { const y = Math.floor(2026.76766 + (r.h - DATA.tip) * 10 / 60 / 24 / 365.25); if (Math.floor(r.year) !== y) errors.push('frame ' + f + ': scheduled year ' + Math.floor(r.year) + ' for block ' + r.h + ' is not the stated model (' + y + ')'); } }
console.log('sweep: ' + (N + 1) + ' frames, ' + errors.length + ' violations');
for (const e of errors.slice(0, 20)) console.log('  ' + e);
process.exit(errors.length ? 1 : 0);
