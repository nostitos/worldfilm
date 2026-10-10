// sweep_lib.mjs — the per-frame assertions a worldfilm project runs on its pure functions (no DOM, no renderer).
// A project's tools/sweep.mjs (from templates/sweep.template.mjs) wires its camera/readout/projector into these
// checks and runs them every frame. Lineage: block-space/tools/sweep.mjs, where each check first caught a real
// defect (block 210,000 shown beside 50 BTC; a float subsidy where Bitcoin pays integer satoshi; a label plate on
// the gate it named; an end edge that crept back up during the settle).
//
// Every check returns { name, todo, run() -> string[] }. runSweep() prints one line per violation (max 20),
// exits 1 on violations and 2 while any check is still marked todo (a new project cannot pass stage 7 on the
// template's placeholders).

export function everyFrame(name, fn, { fps = 60, duration = 30, step = 1, from = 0, to = null, todo = false } = {}) {
  // fn(t, frame) returns null when the frame is fine, else a message. Independent recomputation of displayed numbers goes here.
  return { name, todo, run() {
    const errs = [], N = Math.round((to == null ? duration : to) * fps);
    for (let f = Math.round(from * fps); f <= N; f += step) { const m = fn(f / fps, f); if (m) errs.push(name + ': ' + m); }
    return errs;
  } };
}

export function monotone(name, valueAt, { fps = 60, duration = 30, direction = 'up', slack = 0, except = [], from = 0, to = null, todo = false } = {}) {
  // valueAt(t) must not move against `direction` by more than `slack` between consecutive frames, except inside the
  // declared [t0, t1] windows (a designed swing, written in the spec). Readouts, counters, progress bars.
  return { name, todo, run() {
    const errs = [], N = Math.round((to == null ? duration : to) * fps), sign = direction === 'up' ? 1 : -1;
    let prev = null;
    for (let f = Math.round(from * fps); f <= N; f++) {
      const t = f / fps, v = valueAt(t);
      const excepted = except.some(([a, b]) => t > a && t < b);
      if (prev != null && !excepted && sign * (v - prev) < -slack) errs.push(name + ': frame ' + f + ' (' + t.toFixed(2) + 's) runs ' + (direction === 'up' ? 'backwards' : 'up') + ' ' + prev + ' -> ' + v);
      prev = v;
    }
    return errs;
  } };
}

export function settle(name, { valueAt, from, to, holdFrom = null, holdTo = null, direction = 'down', slack = 0.6, holdSlack = 1.5, fps = 60, visibleAt = null, todo = false }) {
  // A framing target (the projected screen position of a world point) moves in ONE direction from `from` to `to`
  // (slack px of reversal allowed per frame) and then holds within holdSlack px per frame from holdFrom to holdTo.
  // This is how a camera solved from a framing target is proven: key the pose densely, assert the projected quantity.
  return { name, todo, run() {
    const errs = []; let prev = null; const sign = direction === 'down' ? 1 : -1;
    const end = holdTo != null ? holdTo : to;
    for (let f = Math.round(from * fps); f <= Math.round(end * fps); f++) {
      const t = f / fps, v = valueAt(t);
      if (visibleAt && !visibleAt(t)) errs.push(name + ': frame ' + f + ' (' + t.toFixed(2) + 's): the target is out of frame');
      if (prev != null) {
        if (t <= to + 1e-9 && sign * (v - prev) < -slack) errs.push(name + ': frame ' + f + ' (' + t.toFixed(2) + 's): reverses ' + prev.toFixed(1) + ' -> ' + v.toFixed(1));
        if (holdFrom != null && t > holdFrom && Math.abs(v - prev) > holdSlack) errs.push(name + ': frame ' + f + ' (' + t.toFixed(2) + 's): moves during the hold ' + prev.toFixed(1) + ' -> ' + v.toFixed(1));
      }
      prev = v;
    }
    return errs;
  } };
}

export function noTimeOverlap(name, intervals, { todo = false } = {}) {
  // intervals: [{ id, a, b }] — labels of one family may not be up at the same time (they share one place on screen).
  return { name, todo, run() {
    const errs = [], s = [...intervals].sort((p, q) => p.a - q.a);
    for (let i = 1; i < s.length; i++) if (s[i].a < s[i - 1].b - 1e-6) errs.push(name + ': ' + s[i - 1].id + ' until ' + s[i - 1].b + ' overlaps ' + s[i].id + ' at ' + s[i].a);
    return errs;
  } };
}

export function labelsClear(name, labels, { fps = 60, pad = 4, minTargetPx = 6, todo = false } = {}) {
  // labels: [{ id, at, until, plate(t) -> {x, y, w, h} | null, target(t) -> {x0, y0, x1, y1} | null }]
  // The plate (same placement rule as the HUD: above, then beside the right post, then the left, clamped to the safe
  // area) may never overlap the thing it names while it is up; targets smaller than minTargetPx are ignored (far away).
  return { name, todo, run() {
    const errs = [];
    for (const L of labels) {
      for (let f = Math.ceil(L.at * fps); f <= Math.floor(L.until * fps); f++) {
        const t = f / fps, p = L.plate(t), g = L.target(t);
        if (!p || !g) continue;
        if ((g.y1 - g.y0) <= minTargetPx) continue;
        const hit = p.x < g.x1 + pad && p.x + p.w > g.x0 - pad && p.y < g.y1 + pad && p.y + p.h > g.y0 - pad;
        if (hit) errs.push(name + ': frame ' + f + ' (' + t.toFixed(2) + 's): ' + L.id + ' [' + p.x.toFixed(0) + ',' + p.y.toFixed(0) + ' ' + p.w + 'x' + p.h + '] touches its target [' + g.x0.toFixed(0) + '-' + g.x1.toFixed(0) + ' x ' + g.y0.toFixed(0) + '-' + g.y1.toFixed(0) + ']');
      }
    }
    return errs;
  } };
}

export function invisibleWhile(name, opacityAt, { from, to, fps = 60, max = 0.01, todo = false }) {
  // Something that must be gone (a ladder under the headline, a concept layer after its label) stays under `max` opacity.
  return { name, todo, run() {
    const errs = [];
    for (let f = Math.ceil(from * fps); f <= Math.floor(to * fps); f++) { const o = opacityAt(f / fps); if (o > max) errs.push(name + ': frame ' + f + ': visible (' + o.toFixed(2) + ')'); }
    return errs;
  } };
}

export function runSweep(checks, { fps = 60, duration = 30, maxPrint = 20 } = {}) {
  const todo = checks.filter((c) => c.todo).map((c) => c.name);
  const errors = [];
  for (const c of checks) if (!c.todo) errors.push(...c.run());
  const N = Math.round(duration * fps) + 1;
  console.log('sweep: ' + N + ' frames, ' + (checks.length - todo.length) + ' checks, ' + errors.length + ' violations' + (todo.length ? ', ' + todo.length + ' checks still TODO' : ''));
  for (const e of errors.slice(0, maxPrint)) console.log('  ' + e);
  if (errors.length > maxPrint) console.log('  ... ' + (errors.length - maxPrint) + ' more');
  for (const n of todo) console.log('  TODO: ' + n + ' (configure it or delete it from CHECKS)');
  if (!checks.length) { console.log('  no checks configured: a sweep with nothing in it proves nothing'); process.exit(2); }
  process.exit(errors.length ? 1 : todo.length ? 2 : 0);
}

