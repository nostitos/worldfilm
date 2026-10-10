// sweep_blockspace.mjs — the sweep library on real data: Block Space's pure functions must pass the generic checks
// its hand-written tools/sweep.mjs asserts (readout forward except the designed swing, exact satoshi recomputation,
// end edge settles then holds, ladder gone under the headline). Run: node workflow/tests/sweep_blockspace.mjs
import { everyFrame, monotone, settle, invisibleWhile, runSweep } from '../scripts/sweep_lib.mjs';
const P = '../../studio/projects/block-space/';
const { DATA } = await import(P + 'film/data.js');
const cam = await import(P + 'film/camera.js');
const FPS = DATA.fps, DUR = DATA.dur, ASPECT = 16 / 9, base = { fps: FPS, duration: DUR };
const satsExact = (h) => { const k = BigInt(Math.floor(h / 210000)); return k >= 64n ? 0n : (5000000000n >> k); };
runSweep([
  everyFrame('subsidy equals BigInt recomputation', (t, f) => { const r = cam.readoutAt(t); return BigInt(r.sats) === satsExact(r.h) ? null : 'frame ' + f + ': ' + r.sats + ' vs ' + satsExact(r.h); }, base),
  monotone('readout runs forward', (t) => cam.readoutAt(t).h, { ...base, direction: 'up', slack: 2016 * 3, except: [[5.4, 8.4]] }),
  everyFrame('readout at NOW and at the end', (t, f) => { const h = cam.readoutAt(t).h; if (t >= 17.5 && t <= 19.2 && h !== DATA.tip) return 'frame ' + f + ': ' + h + ' at NOW'; if (t >= 25.2 && t <= 26.9 && h !== DATA.last) return 'frame ' + f + ': ' + h + ' at the end'; return null; }, base),
  settle('end edge settles down the frame then holds', { valueAt: (t) => cam.project(cam.cameraAt(t, ASPECT), [DATA.end_x, 0, 0]).y, visibleAt: (t) => { const e = cam.project(cam.cameraAt(t, ASPECT), [DATA.end_x, 0, 0]); return e.visible && e.y >= 0 && e.y <= 1080; }, from: 22.6, to: 27.0, holdFrom: 27.0, holdTo: DUR, direction: 'down', slack: 0.6, holdSlack: 1.5, fps: FPS }),
  invisibleWhile('ladder invisible under the headline', (t) => cam.ladderOpacityAt(t), { from: DATA.shots[8].text.find((x) => x.id === 'H-cap').at_s, to: DUR, fps: FPS }),
], base);

