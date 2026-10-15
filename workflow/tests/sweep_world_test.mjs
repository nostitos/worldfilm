// sweep_world_test.mjs — the sweep library on a whole synthetic world (fixtures/synthetic_world.mjs): the clean world
// passes every check with 0 violations, and each known defect is caught by the check written for it.
// Every displayed number is recomputed independently each frame (integer frame arithmetic for the count, an exact
// BigInt area, hand-written digit grouping for the text), so a readout that is wrong on screen fails even when its
// own formula agrees with itself.
// Run: node workflow/tests/sweep_world_test.mjs                  (exit 0 when every expectation holds)
//      node workflow/tests/sweep_world_test.mjs --sweep [defect]  (runSweep on that world: exit 0 clean, 1 violations)
import { everyFrame, monotone, settle, noTimeOverlap, labelsClear, invisibleWhile, runSweep } from '../scripts/sweep_lib.mjs';
import { plateBox } from '../templates/film/place_label.js';
import { makeWorld, DEFECTS } from './fixtures/synthetic_world.mjs';

// independent recomputation: tile i lands on frame 30 + 15 i (0.5 s + 0.25 s i at 60 fps)
const exactCount = (frame, D) => { let c = 0; for (let i = 0; i < D.tiles.n; i++) if (frame >= Math.round(D.tiles.first_s * D.fps) + i * Math.round(D.tiles.every_s * D.fps)) c++; return c; };
const groupDigits = (n) => { const s = String(n); let out = ''; for (let i = 0; i < s.length; i++) { if (i && (s.length - i) % 3 === 0) out += ','; out += s[i]; } return out; };
const exactText = (c, D) => { const a = BigInt(c) * BigInt(D.tiles.side_cm) * BigInt(D.tiles.side_cm); return c + (c === 1 ? ' tile · ' : ' tiles · ') + groupDigits(a) + ' cm²'; };

export function checksFor(world, { plateOffset } = {}) {
  const { DATA: D } = world, base = { fps: D.fps, duration: D.dur };
  const L = D.label, offset = plateOffset || L.offset_px;
  const plate = world.usesSharedRule
    ? (t) => plateBox(world.anchorsAt(t), L.anchor, L.content, { offset, width: D.width, height: D.height })
    : (t) => world.handPlate(t, L.content.length * 18 + 36, 50);
  const edge = (t) => world.project(world.cameraAt(t), [0, D.subject.y0, D.subject.z]);
  return [
    everyFrame('displayed count and area equal an independent recomputation', (t, f) => {
      const r = world.readoutAt(t), c = exactCount(f, D), want = exactText(c, D);
      if (r.count !== c) return 'frame ' + f + ': shows ' + r.count + ' tiles, exact ' + c;
      if (r.text !== want) return 'frame ' + f + ': shows "' + r.text + '", exact "' + want + '"';
      return null;
    }, base),
    monotone('tile count runs forward', (t) => world.readoutAt(t).count, { ...base, direction: 'up' }),
    settle("square's bottom edge settles down the frame, then holds", {
      valueAt: (t) => edge(t).y, visibleAt: (t) => { const e = edge(t); return e.visible && e.y >= 0 && e.y <= D.height; },
      from: D.push.from, to: D.push.to, holdFrom: D.push.to, holdTo: D.dur, direction: 'down', slack: 0.6, holdSlack: 1.5, fps: D.fps }),
    noTimeOverlap('captions', D.captions.map((c) => ({ id: c.id, a: c.at_s, b: c.until_s }))),
    labelsClear('label plate clears the square', [{ id: L.id, at: L.at_s, until: L.until_s, plate, target: (t) => world.subjectBox(t) }], { fps: D.fps }),
    invisibleWhile('grid overlay gone for the final hold', (t) => world.overlayOpacityAt(t), { from: D.overlay.fade_to, to: D.dur, fps: D.fps }),
  ];
}

// the check each defect must trip (others may fire too: the stale frame is also a wrong value)
const TARGET = {
  'count-early': 'displayed count and area equal an independent recomputation',
  'format': 'displayed count and area equal an independent recomputation',
  'stale-frame': 'tile count runs forward',
  'overshoot': "square's bottom edge settles down the frame, then holds",
  'plate-on-subject': 'label plate clears the square',
  'overlay-residue': 'grid overlay gone for the final hold',
  'caption-overlap': 'captions',
};
const run = (world, name, opts) => checksFor(world, opts).find((c) => c.name === name).run();

const argv = process.argv.slice(2);
if (argv[0] === '--sweep') {
  const w = makeWorld(argv[1] && argv[1] !== 'clean' ? [argv[1]] : []);
  runSweep(checksFor(w), { fps: w.DATA.fps, duration: w.DATA.dur });
} else {
  const results = [];
  const expect = (name, ok, detail = '') => results.push([ok, name, detail]);
  const clean = makeWorld();
  for (const c of checksFor(clean)) { const e = c.run(); expect('clean world: ' + c.name, e.length === 0, e[0] || ''); }
  // asked to sit below its anchor (onto the square), the shared rule moves the plate beside the square's right side
  const moved = run(clean, TARGET['plate-on-subject'], { plateOffset: [0, 20] });
  expect('the shared rule keeps a low-offset plate off the square', moved.length === 0, moved[0] || '');
  for (const d of DEFECTS) expect(d + ' is caught by "' + TARGET[d] + '"', run(makeWorld([d]), TARGET[d]).length > 0, 'no violation');
  // rounding shows the first tile from frame 23 instead of 30; the lost separator is invisible under 1,000 cm² and caught at 1,250
  const early = run(makeWorld(['count-early']), TARGET['count-early']);
  expect('count-early first fails at frame 23 (half an interval before the first tile)', /frame 23: shows 1 tiles, exact 0/.test(early[0] || ''), early[0] || 'none');
  const fmt = run(makeWorld(['format']), TARGET.format);
  expect('format first fails at frame 45 ("1250 cm²" vs "1,250 cm²")', /frame 45: .*1250 cm².*1,250 cm²/.test(fmt[0] || ''), fmt[0] || 'none');
  const stale = run(makeWorld(['stale-frame']), TARGET['stale-frame']);
  expect('stale-frame reads as one step back at frame 91', stale.length === 1 && /frame 91 /.test(stale[0]), stale.join(' | '));
  let bad = 0;
  for (const [ok, name, detail] of results) { console.log((ok ? 'ok   ' : 'FAIL ') + name + (ok ? '' : '  ' + String(detail).slice(0, 160))); if (!ok) bad++; }
  console.log('sweep_world_test: ' + (results.length - bad) + '/' + results.length + ' expectations hold');
  process.exit(bad ? 1 : 0);
}
