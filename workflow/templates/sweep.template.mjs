// tools/sweep.mjs — the full-frame sweep (worldfilm stage 7 pass criterion). Every displayed number is recomputed
// independently every frame, no label plate touches what it names, every framing target settles in one direction,
// and nothing declared gone is visible. Pure functions only (film/camera.js, film/data.js): no DOM, no renderer.
// Usage: node tools/sweep.mjs    exit 0 clean · 1 violations · 2 while a check below is still TODO
// Worked example: studio/projects/block-space/tools/sweep.mjs (each check there caught a real defect).
import { everyFrame, monotone, settle, noTimeOverlap, labelsClear, invisibleWhile, runSweep } from '../../../worldfilm/scripts/sweep_lib.mjs';
import { plateBox } from '../film/place_label.js';                   // the SAME placement rule film/main.js draws with

// ---- ADAPT: the project's pure functions ----------------------------------------------------------------------
let DATA, cam;
try {
  ({ DATA } = await import('../film/data.js'));                       // tools/build.py writes it: shots, anchors, constants
  cam = await import('../film/camera.js');                            // cameraAt(t, aspect), readoutAt(t), project(cam, [x,y,z]), ...
} catch (e) { console.log('sweep: film/data.js or film/camera.js not importable yet (' + e.message + '); build stages 3-4 first'); process.exit(2); }
const FPS = DATA.fps, DUR = DATA.dur, W = 1920, H = 1080, ASPECT = W / H;
const base = { fps: FPS, duration: DUR };

// ---- CHECKS: configure each one, then set todo: false; delete the ones this film has no use for ----------------
const CHECKS = [
  // 1. Money is integers: every number on screen equals an INDEPENDENT recomputation (a different formula, BigInt
  //    where the protocol uses integers), every frame. The facts gate cannot see a rounding error that facts.json shares.
  everyFrame('displayed value equals an exact recomputation', (t, f) => {
    const r = cam.readoutAt(t);                                        // { h, value, text, ... } as the HUD prints it
    const exact = null;                                                // TODO e.g. (5000000000n >> BigInt(Math.floor(r.h / 210000))).toString()
    return exact === null || String(r.value) === String(exact) ? null : 'frame ' + f + ': shows ' + r.value + ', exact ' + exact;
  }, { ...base, todo: true }),

  // 2. The readout never runs backwards, except inside a designed swing written in the spec.
  monotone('readout runs forward', (t) => cam.readoutAt(t).h, { ...base, direction: 'up', slack: 0, except: [/* [5.4, 8.4] */], todo: true }),

  // 3. The readout is exactly the declared value while the camera rests on a declared stop (NOW, the end).
  everyFrame('readout at the stop', (t, f) => {
    const stops = [/* { from: 17.5, to: 19.2, h: DATA.tip } */];
    for (const s of stops) if (t >= s.from && t <= s.to && cam.readoutAt(t).h !== s.h) return 'frame ' + f + ': ' + cam.readoutAt(t).h + ' at the stop, not ' + s.h;
    return null;
  }, { ...base, todo: true }),

  // 4. A framing target (the projected screen position of a world point) settles in one direction, then holds.
  //    This is the proof for any shot whose camera is solved from a framing target (stage 4): key the pose every
  //    0.1 s, assert the projected quantity here.
  settle('end edge settles down the frame, then holds under the headline', {
    valueAt: (t) => cam.project(cam.cameraAt(t, ASPECT), [/* DATA.end_x */ 0, 0, 0]).y,
    visibleAt: (t) => { const e = cam.project(cam.cameraAt(t, ASPECT), [0, 0, 0]); return e.visible && e.y >= 0 && e.y <= H; },
    from: 22.6, to: 27.0, holdFrom: 27.0, holdTo: DUR, direction: 'down', slack: 0.6, holdSlack: 1.5, fps: FPS, todo: true }),

  // 5. Labels of one family never overlap in time; captions never overlap in time.
  noTimeOverlap('anchored labels', DATA.shots.flatMap((s) => (s.text || []).filter((x) => (s.world_anchors || []).some((a) => a.text_id === x.id)).map((x) => ({ id: x.id, a: x.at_s, b: x.until_s }))), { todo: false }),
  noTimeOverlap('captions', DATA.shots.flatMap((s) => (s.text || []).filter((x) => x.role === 'caption').map((x) => ({ id: x.id, a: x.at_s, b: x.until_s }))), { todo: false }),

  // 6. No label plate touches the thing it names, any frame it is up. plate(t) applies the SAME placement rule as
  //    film/main.js by calling plateBox on the same projections (film/place_label.js: above the anchor, else beside the
  //    right post past its outer face, else the left; safe area; readout; caption zone; hold line). target(t) is the
  //    projected box of the object. ANCHORS maps every anchor and its -right/-right-outer/-left/-left-outer variants to
  //    world points (export the table world.js builds from film/data.js so both read one source).
  // const ANCHORS = { 'gate-1': [x, y, z], 'gate-1-right': [...], 'gate-1-right-outer': [...], 'gate-1-left': [...], 'gate-1-left-outer': [...] };
  // const projectAll = (t) => { const c = cam.cameraAt(t, ASPECT), out = {}; for (const [k, v] of Object.entries(ANCHORS)) out[k] = cam.project(c, v); return out; };
  labelsClear('label plates clear their gates', DATA.shots.flatMap((s) => (s.world_anchors || []).map((a) => {
    const text = (s.text || []).find((x) => x.id === a.text_id);
    return {
      id: a.text_id, at: text ? text.at_s : 0, until: text ? text.until_s : 0,
      plate: (t) => null,                                              // TODO -> plateBox(projectAll(t), a.anchor, text.content, { offset: a.offset_px, width: W, height: H, holdFrac: a.hold_line_frac || 0.76 })
      target: (t) => null,                                             // TODO -> { x0, y0, x1, y1 }: the projected corners of the object (posts, bars) it names
    };
  })), { fps: FPS, todo: true }),

  // 7. Something declared gone stays gone (the ladder under the headline; a concept layer after its label).
  invisibleWhile('ladder invisible under the headline', (t) => 0 /* TODO cam.ladderOpacityAt(t) */, { from: 27.0, to: DUR, fps: FPS, todo: true }),
];

runSweep(CHECKS, base);
