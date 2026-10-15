// fixtures/synthetic_world.mjs — a small neutral world for the sweep tests: tiles placed on a schedule along a row,
// a corner readout that counts them and reports their covered area, a camera that pushes in on a unit square and
// settles, a label anchored to the square's top edge, captions, and a grid overlay that must fade out before the
// final hold. Every function is a pure function of t (no DOM, no renderer), the shape a film's camera.js/data.js has.
//
// makeWorld(defects) returns the world; each defect name switches on ONE known bug the sweep must catch:
//   'count-early'      the readout rounds instead of flooring, so it shows the next tile half an interval early
//   'format'           the area loses its thousands separator ("1250 cm²" for "1,250 cm²")
//   'stale-frame'      one frame shows the count from two tiles ago (the readout steps backwards)
//   'overshoot'        the push-in eases with an overshoot, so the square's bottom edge reverses on screen
//   'plate-on-subject' the HUD draws the plate under its anchor by hand instead of calling the shared rule
//   'overlay-residue'  the grid overlay fades to 3 % instead of 0
//   'caption-overlap'  the second caption comes up before the first one leaves
const W = 1920, H = 1080;

export function makeWorld(defects = []) {
  const bug = new Set(defects);
  const DATA = {
    fps: 60, dur: 4, width: W, height: H,
    tiles: { first_s: 0.5, every_s: 0.25, n: 10, side_cm: 25 },        // tile i lands at 0.5 + 0.25 i s; 25 x 25 cm
    push: { from: 0.5, to: 2.5, z0: 12, z1: 6 },                       // camera z from 12 to 6, then holds (lateral drift only)
    subject: { x0: -0.5, x1: 0.5, y0: 0.5, y1: 1.5, z: 0 },            // the unit square the camera frames
    overlay: { fade_from: 2.5, fade_to: 3.0 },
    label: { id: 'L-square', anchor: 'square', content: 'SQUARE A · 1 M', offset_px: [0, -60], at_s: 0.8, until_s: 3.8 },
    captions: [{ id: 'C1', at_s: 0.2, until_s: 1.9 }, { id: 'C2', at_s: bug.has('caption-overlap') ? 1.6 : 2.0, until_s: 3.9 }],
  };

  const tilesAt = (t) => {
    const { first_s, every_s, n } = DATA.tiles, k = (t - first_s) / every_s;
    const c = bug.has('count-early') ? Math.round(k) + 1 : Math.floor(k + 1e-9) + 1;
    return Math.max(0, Math.min(n, c));
  };
  const group = new Intl.NumberFormat('en-US');
  function readoutAt(t) {
    let count = tilesAt(t);
    if (bug.has('stale-frame') && Math.round(t * DATA.fps) === 91) count = Math.max(0, count - 2);
    const area = count * DATA.tiles.side_cm * DATA.tiles.side_cm;      // cm²
    const areaText = bug.has('format') ? String(area) : group.format(area);
    return { count, area_cm2: area, text: count + (count === 1 ? ' tile · ' : ' tiles · ') + areaText + ' cm²' };
  }

  const easeOutCubic = (u) => 1 - Math.pow(1 - u, 3);
  const easeOutBack = (u) => { const s = 1.70158; return 1 + (s + 1) * Math.pow(u - 1, 3) + s * Math.pow(u - 1, 2); };
  function cameraAt(t, aspect = W / H) {
    const { from, to, z0, z1 } = DATA.push;
    const u = Math.max(0, Math.min(1, (t - from) / (to - from)));
    const e = bug.has('overshoot') ? easeOutBack(u) : easeOutCubic(u);
    const drift = t > to ? 0.02 * Math.sin(1.7 * (t - to)) : 0;        // lateral rest drift: x only, so screen y holds
    return { pos: [drift, 1.5, z0 + (z1 - z0) * e], fov: 40, aspect };
  }
  function project(cam, [x, y, z]) {                                    // pinhole camera looking down -z
    const f = (H / 2) / Math.tan((cam.fov * Math.PI / 180) / 2), d = cam.pos[2] - z;
    if (d <= 1e-6) return { x: 0, y: 0, visible: false };
    return { x: W / 2 + f * (x - cam.pos[0]) / d, y: H / 2 - f * (y - cam.pos[1]) / d, visible: true };
  }
  function anchorsAt(t) {                                               // the anchor and its side variants (the square's top corners)
    const c = cameraAt(t), s = DATA.subject, top = s.y1;
    return {
      square: project(c, [0, top, s.z]),
      'square-right': project(c, [s.x1, top, s.z]), 'square-right-outer': project(c, [s.x1 + 0.05, top, s.z]),
      'square-left': project(c, [s.x0, top, s.z]), 'square-left-outer': project(c, [s.x0 - 0.05, top, s.z]),
    };
  }
  function subjectBox(t) {                                              // the projected box of the square
    const c = cameraAt(t), s = DATA.subject;
    const a = project(c, [s.x0, s.y1, s.z]), b = project(c, [s.x1, s.y0, s.z]);
    return { x0: a.x, y0: a.y, x1: b.x, y1: b.y };
  }
  const overlayOpacityAt = (t) => {
    const { fade_from, fade_to } = DATA.overlay, u = Math.max(0, Math.min(1, (t - fade_from) / (fade_to - fade_from)));
    return Math.max(bug.has('overlay-residue') ? 0.03 : 0, 1 - u);
  };
  // the HUD's own placement for the defect: centred UNDER the anchor, without the shared rule
  const handPlate = (t, w, h) => { const p = anchorsAt(t).square; return { x: p.x - w / 2, y: p.y + 10, w, h }; };

  return { DATA, readoutAt, cameraAt, project, anchorsAt, subjectBox, overlayOpacityAt, handPlate, usesSharedRule: !bug.has('plate-on-subject') };
}

export const DEFECTS = ['count-early', 'format', 'stale-frame', 'overshoot', 'plate-on-subject', 'overlay-residue', 'caption-overlap'];
