// sweep_lib_test.mjs — each sweep check must catch its own defect and stay quiet on clean input.
// Run: node workflow/tests/sweep_lib_test.mjs   (exit 0 when every expectation holds)
import { everyFrame, monotone, settle, noTimeOverlap, labelsClear, invisibleWhile } from '../scripts/sweep_lib.mjs';
const base = { fps: 60, duration: 2 };
const results = [];
const expect = (name, check, wantErrors) => { const errs = check.run(); const ok = wantErrors ? errs.length > 0 : errs.length === 0; results.push([ok, name, errs.length, errs[0] || '']); };

// everyFrame: an independent recomputation disagrees on one frame
expect('everyFrame clean', everyFrame('v', (t, f) => null, base), false);
expect('everyFrame catches a mismatch', everyFrame('v', (t, f) => (f === 37 ? 'frame 37: shows 25, exact 25.00000000' : null), base), true);

// monotone: a counter that steps back by one, outside and inside a declared swing
const counter = (t) => (t > 1.0 && t < 1.05 ? Math.round(t * 100) - 3 : Math.round(t * 100));
expect('monotone catches a step back', monotone('counter', counter, { ...base, direction: 'up' }), true);
expect('monotone excepts the declared swing', monotone('counter', counter, { ...base, direction: 'up', except: [[0.98, 1.1]] }), false);
expect('monotone clean', monotone('counter', (t) => Math.round(t * 100), { ...base, direction: 'up' }), false);

// settle: a projected edge (6.7 px/frame down the frame) that creeps back up 20 px for one frame mid-settle, then jumps during the hold
const edge = (t) => (t < 1.0 ? 100 + 400 * t : 500) + (t > 0.5 && t < 0.52 ? -20 : 0) + (t > 1.5 && t < 1.52 ? 3 : 0);
const settleErrs = settle('edge', { valueAt: edge, from: 0, to: 1.0, holdFrom: 1.0, holdTo: 2.0, direction: 'down', slack: 0.6, holdSlack: 1.5, fps: 60 }).run();
results.push([settleErrs.some((e) => e.includes('reverses')) && settleErrs.some((e) => e.includes('during the hold')), 'settle catches a reversal and a hold jump', settleErrs.length, settleErrs[0] || '']);
expect('settle clean', settle('edge', { valueAt: (t) => (t < 1.0 ? 100 + 400 * t : 500), from: 0, to: 1.0, holdFrom: 1.0, holdTo: 2.0, direction: 'down', slack: 0.6, holdSlack: 1.5, fps: 60 }), false);

// noTimeOverlap: two labels up at once
expect('noTimeOverlap catches an overlap', noTimeOverlap('labels', [{ id: 'a', a: 0, b: 1.2 }, { id: 'b', a: 1.0, b: 2 }]), true);
expect('noTimeOverlap clean', noTimeOverlap('labels', [{ id: 'a', a: 0, b: 1.0 }, { id: 'b', a: 1.0, b: 2 }]), false);

// labelsClear: a plate that slides onto its gate for a few frames
const gate = (t) => ({ x0: 900, y0: 400, x1: 1020, y1: 700 });
const plate = (t) => ({ x: 700 + 300 * t, y: 420, w: 180, h: 50 });          // reaches x=880 at t=0.6: touches at ~0.6-1.2 s
expect('labelsClear catches a touch', labelsClear('plates', [{ id: 'L', at: 0, until: 2, plate, target: gate }], { fps: 60 }), true);
expect('labelsClear ignores a far (tiny) target', labelsClear('plates', [{ id: 'L', at: 0, until: 2, plate, target: (t) => ({ x0: 900, y0: 400, x1: 1020, y1: 404 }) }], { fps: 60 }), false);
expect('labelsClear clean', labelsClear('plates', [{ id: 'L', at: 0, until: 2, plate: (t) => ({ x: 100, y: 100, w: 180, h: 50 }), target: gate }], { fps: 60 }), false);

// invisibleWhile: a ladder that is still 3 % visible under the headline
expect('invisibleWhile catches residual opacity', invisibleWhile('ladder', (t) => (t < 1.2 ? 0.03 : 0), { from: 1.0, to: 2.0, fps: 60 }), true);
expect('invisibleWhile clean', invisibleWhile('ladder', (t) => 0, { from: 1.0, to: 2.0, fps: 60 }), false);

let bad = 0;
for (const [ok, name, n, first] of results) { console.log((ok ? 'ok   ' : 'FAIL ') + name + ' (' + n + ' violations' + (first ? ': ' + first.slice(0, 90) : '') + ')'); if (!ok) bad++; }
console.log('sweep_lib_test: ' + (results.length - bad) + '/' + results.length + ' expectations hold');
process.exit(bad ? 1 : 0);
