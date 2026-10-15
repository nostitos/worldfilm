// tools/sweep.mjs — the full-frame sweep (worldfilm stage 7 pass criterion). Each configured check runs on every frame:
// displayed values equal an independent recomputation, readouts move only as declared, framing targets settle,
// label plates never touch what they name, and layers declared hidden stay hidden. Pure functions only
// (film/camera.js, film/data.js): no DOM, no renderer.
// Usage: node tools/sweep.mjs    exit 0 clean · 1 violations · 2 while any check below is still TODO or none is configured
import { everyFrame, monotone, settle, noTimeOverlap, labelsClear, invisibleWhile, runSweep } from '../../../worldfilm/scripts/sweep_lib.mjs';
import { plateBox } from '../film/place_label.js';                   // the SAME placement rule film/main.js draws with

// ---- ADAPT: the project's pure functions ----------------------------------------------------------------------
let DATA, cam;
try {
  ({ DATA } = await import('../film/data.js'));                       // tools/build.py writes it: fps, dur, sizes, shots, events
  cam = await import('../film/camera.js');                            // e.g. cameraAt(t, aspect), readoutAt(t), project(cam, [x,y,z])
} catch (e) { console.log('sweep: film/data.js or film/camera.js not importable yet (' + e.message + '); build stages 3-4 first'); process.exit(2); }
const FPS = DATA.fps, DUR = DATA.dur, W = DATA.sizes[0].w, H = DATA.sizes[0].h, ASPECT = W / H;
const base = { fps: FPS, duration: DUR };
const texts = DATA.shots.flatMap((s) => s.text || []);

// ---- CHECKS: configure each one and set todo: false, or delete the ones this film has no use for ---------------
const CHECKS = [
  // 1. Every displayed value equals an INDEPENDENT recomputation (a different code path from the HUD), every frame,
  //    at the source's precision: integers (BigInt if large) for discrete units, an exact decimal representation for
  //    exact decimal quantities, a stated tolerance for measured values; then the same rounding the display declares.
  //    The facts gate cannot see a rounding or unit error that facts.json shares with the HUD.
  everyFrame('displayed value equals an independent recomputation', (t, f) => {
    const shown = null;                                                // TODO the value as the HUD prints it at t
    const exact = null;                                                // TODO the same value recomputed independently from the data
    return shown === null || exact === null || String(shown) === String(exact) ? null : 'frame ' + f + ': shows ' + shown + ', expected ' + exact;
  }, { ...base, todo: true }),

  // 2. A readout or counter only moves in its declared direction, except inside designed windows written in the spec.
  monotone('readout moves in its declared direction', (t) => 0 /* TODO e.g. cam.readoutAt(t).value */, { ...base, direction: 'up', slack: 0, except: [], todo: true }),

  // 3. Every shot whose camera is solved from a framing target settles in one direction, then holds. Generated from
  //    shots[].camera.framing_target; resolve each target's world point (TODO) to make these checks real.
  ...DATA.shots.filter((s) => s.camera && s.camera.framing_target).map((s) => {
    const ft = s.camera.framing_target, keys = ft.keys, axis = ft.axis || 'y';
    const point = null;                                                // TODO [x, y, z] for ft.point (an anchor name or 'x,y,z')
    const at = (t) => cam.project(cam.cameraAt(t, ASPECT), point);
    return settle(s.id + ': framing target ' + ft.point + ' settles', {
      valueAt: (t) => at(t)[axis], visibleAt: (t) => { const e = at(t); return e.visible && e.x >= 0 && e.x <= W && e.y >= 0 && e.y <= H; },
      from: keys[0][0], to: ft.hold_from_s ?? keys[keys.length - 1][0], holdFrom: ft.hold_from_s ?? null, holdTo: ft.hold_from_s != null ? s.t_out : null,
      direction: ft.assert === 'monotone_up' ? 'up' : 'down', slack: ft.slack_px ?? 0.6, holdSlack: ft.hold_slack_px ?? 1.5, fps: FPS, todo: point === null });
  }),

  // 4. Labels of one family never overlap in time; captions never overlap in time. Derived from the spec.
  noTimeOverlap('anchored labels', DATA.shots.flatMap((s) => (s.text || []).filter((x) => (s.world_anchors || []).some((a) => a.text_id === x.id)).map((x) => ({ id: x.id, a: x.at_s, b: x.until_s }))), { todo: false }),
  noTimeOverlap('captions', texts.filter((x) => x.role === 'caption').map((x) => ({ id: x.id, a: x.at_s, b: x.until_s })), { todo: false }),

  // 5. No label plate touches the object it names, any frame it is up. plate(t) applies the SAME placement rule as
  //    film/main.js (plateBox on the same projections); target(t) is the projected box of the named object. ANCHORS
  //    maps anchor names to world points; side candidates (<a>-right, <a>-right-outer, <a>-left, <a>-left-outer) are
  //    optional and only needed for objects a plate may have to sit beside.
  // const ANCHORS = { 'subject': [x, y, z] };
  // const projectAll = (t) => { const c = cam.cameraAt(t, ASPECT), out = {}; for (const [k, v] of Object.entries(ANCHORS)) out[k] = cam.project(c, v); return out; };
  labelsClear('label plates clear their objects', DATA.shots.flatMap((s) => (s.world_anchors || []).map((a) => {
    const text = (s.text || []).find((x) => x.id === a.text_id);
    return {
      id: a.text_id, at: text ? text.at_s : 0, until: text ? text.until_s : 0,
      plate: (t) => null,      // TODO -> plateBox(projectAll(t), a.anchor, text.content, { offset: a.offset_px, width: W, height: H, holdFrac: a.hold_line_frac ?? 0.76 })
      target: (t) => null,     // TODO -> { x0, y0, x1, y1 }: the projected bounds of the object the label names
    };
  })), { fps: FPS, todo: true }),

  // 6. A layer the spec declares hidden stays hidden for its window (add one per declaration, or delete).
  invisibleWhile('declared-hidden layer stays hidden', (t) => 0 /* TODO opacity at t */, { from: 0, to: 0, fps: FPS, todo: true }),
];

runSweep(CHECKS, base);
