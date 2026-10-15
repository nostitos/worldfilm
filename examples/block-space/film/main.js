// film/main.js — "Block Space": the camera pose graph (dial 4, log-space keys, monotone cubic), the HUD (labels
// projected from world anchors at fixed screen size, captions, the final card) and the paused GSAP timeline the
// renderer seeks. Every frame is a pure function of t: frame(t) = camera(t) + world.render + hud(t).
import { createWorld } from '../world.js';
import { DATA } from './data.js';

const DUR = DATA.dur;
const SHOTS = DATA.shots;

import { cameraAt, readoutAt, ladderOpacityAt } from './camera.js';

// ---------------------------------------------------------------------------------------------- HUD
const eo = (u) => (u <= 0 ? 0 : u >= 1 ? 1 : 1 - Math.pow(2, -10 * u));
function alphaIn(t, at, until, fade = 0.3) { return Math.min(at <= 0 ? 1 : eo((t - at) / fade), eo((until - t) / fade)); }   // at 0: frame 0 is already complete

export async function boot({ canvas, hud, width, height, vertical = false }) {
  await document.fonts.ready;
  const world = createWorld(canvas, { width, height, portalFade: vertical ? 14 : 0 });   // portrait only: portals dissolve over the last 14 units (0.3-0.6 s at the pass speeds) instead of leaving the frame in one frame
  const texts = [];
  for (const s of SHOTS) for (const tx of s.text) texts.push({ ...tx, shot: s.id, anchor: (s.world_anchors.find((a) => a.text_id === tx.id) || {}).anchor, offset: (s.world_anchors.find((a) => a.text_id === tx.id) || {}).offset_px });
  const anchored = texts.filter((tx) => tx.anchor).sort((a, b) => a.at_s - b.at_s);
  for (let i = 1; i < anchored.length; i++) anchored[i].at_s = Math.max(anchored[i].at_s, anchored[i - 1].until_s);   // one label at a time (critic r1/r2)
  const els = {};
  for (const tx of texts) {
    const el = document.createElement('div');
    el.className = 'hf-text ' + tx.role + (tx.anchor ? ' anchored' : '');
    el.id = 'tx-' + tx.id;
    el.textContent = tx.content;
    el.style.opacity = '0';
    hud.appendChild(el);
    els[tx.id] = el;
  }
  const corner = document.getElementById('corner');
  const fmt = (n) => Math.round(n).toLocaleString('en-US');
  const SAFE_W = vertical ? 64 : 96;
  let last = -1;
  function frame(t) {
    if (t === last) return;
    last = t;
    const cam = cameraAt(t, width / height);
    world.setFutureOpacity(ladderOpacityAt(t));   // the schedule's lines are gone under the number (film/camera.js, asserted by tools/sweep.mjs)
    world.render(cam);
    const an = world.anchors(cam);
    const placed = [];                                                         // anchored label boxes already on screen this frame
    for (const tx of texts) {
      const el = els[tx.id];
      let a = alphaIn(t, tx.at_s, tx.until_s);
      if (tx.anchor) {
        const p = an[tx.anchor];
        if (!p || !p.visible) a = 0;
        else {
          const ox = (tx.offset && tx.offset[0]) || 0, oy = (tx.offset && tx.offset[1]) || 0;
          const w = el.offsetWidth || 400, hgt = el.offsetHeight || 40;
          let x = Math.round(p.x + ox - w / 2), y = Math.round(p.y + oy - hgt);   // oy < 0: the gap between the label's bottom and the anchor
          const right = an[tx.anchor + '-right'], outer = an[tx.anchor + '-right-outer'], left = an[tx.anchor + '-left'], louter = an[tx.anchor + '-left-outer'];
          let beside = 0;
          if (right && right.visible && Math.max(72, y) + hgt > right.y - 8) {   // the plate would sit on the top bar: beside a post, past its outer face, with a leader to the bar's end (critic r6/r7/r8)
            x = Math.round((outer ? outer.x + Math.abs(outer.x - right.x) : right.x) + 24); y = Math.round(Math.max(72, right.y - hgt / 2)); beside = 1;
            if (x + w > width - (vertical ? 400 : 460) && y < (vertical ? 420 : 330) && left && left.visible) {   // that side is the readout's: the left post
              x = Math.round((louter ? louter.x - Math.abs(louter.x - left.x) : left.x) - 24 - w); beside = 2;
            }
          }
          el.classList.toggle('beside', beside === 1); el.classList.toggle('beside-left', beside === 2);
          x = Math.max(SAFE_W, Math.min(width - SAFE_W - w, x));           // sticky inside the safe area
          y = Math.max(72, Math.min(height - (vertical ? 760 : 260), y));                 // never in the caption zone; portrait holds at 60 % so a label does not race a gate out of the frame (the pass at 15.6 s read as a pop)
          if (x + w > width - (vertical ? 400 : 460) && y < (vertical ? 420 : 330)) y = (vertical ? 420 : 330);   // never over the corner readout
          if (a > 0.01) {                                                      // collision: a later label is pushed up until it is clear (deterministic)
            for (let guard = 0; guard < 6; guard++) {
              const hit = placed.find((b) => x < b.x + b.w + 12 && x + w + 12 > b.x && y < b.y + b.h + 8 && y + hgt + 8 > b.y);
              if (!hit) break;
              y = hit.y - hgt - 10;
            }
            placed.push({ x, y, w, h: hgt });
          }
          el.style.transform = 'translate(' + x + 'px,' + y + 'px)';
          if (p.dist > 160) a *= Math.max(0, 1 - (p.dist - 160) / 120);  // far gates recede into the fog with their labels
        }
      }
      el.style.opacity = a.toFixed(3);
    }
    const ro = readoutAt(t, width / height);
    const h = ro.h, past = ro.past, yr = ro.year, subText = ro.subText;
    corner.innerHTML = '<span class="k">IN VIEW · BLOCK</span>' + fmt(h) + '<span class="k">SUBSIDY</span>' + subText + ' BTC<span class="k">' + (past ? 'MINED' : 'SCHEDULED') + '</span>' + (past ? '' : '≈ ') + Math.floor(yr);
    corner.style.opacity = (t > 26.4 ? eo((26.9 - t) / 0.5) : 1).toFixed(3);   // gone before the headline
  }

  // one paused GSAP timeline; the driver's clock is a method (not an accessor property: see worldfilm SKILL.md)
  const driver = { _t: 0, t(v) { if (v === undefined) return this._t; this._t = v; } };
  const tl = gsap.timeline({ paused: true });
  tl.to(driver, { t: DUR, duration: DUR, ease: 'none', onUpdate: () => frame(driver.t()) }, 0);
  frame(0);
  window.__worldfilm = { seek: (t) => { tl.pause(); tl.time(Math.max(0, Math.min(DUR, t)), false); frame(driver.t()); }, cameraAt, readoutAt, world, DATA };
  window.EV = DATA.events;
  return { tl };
}
