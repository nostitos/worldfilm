// film/place_label.js — the label placement rule (worldfilm stage 6), ONE pure function shared by the HUD
// (film/main.js draws the plate where it says) and the sweep (tools/sweep.mjs asserts the plate never touches the
// object it names). Keep them on the same function: a rule that lives twice drifts twice.
//
// The rule: a plate sits ABOVE its anchor; if that puts it on the object (a gate's top bar) it moves BESIDE the
// right post, past the post's outer face, with a leader (beside = 1); if that side belongs to the corner readout,
// beside the LEFT post (beside = 2). Then: clamped to the safe area; never over the corner readout; never in the
// caption zone; it stops following its anchor below the hold line (holdFrac of the frame height: 0.76 at 16:9,
// 0.60 in portrait) so it never races a passing object out of the frame; a later plate that collides is pushed up.
// Lineage: block-space/film/main.js (critic rounds 6-8), where the hold line was found on the portrait cut.
//
// placeLabel({ p, right, outer, left, louter, w, h, offset, width, height, safeW, readout, captionZone, holdFrac, placed })
//   p: the projected anchor { x, y, visible } (screen px); right / outer / left / louter: the projected post variants
//   <a>-right, <a>-right-outer, <a>-left, <a>-left-outer from anchors(cam) (undefined when the object has no posts)
//   w, h: the plate's size in px; offset: [dx, dy] with dy < 0 = the gap above the anchor
//   readout: { x, y } = the corner readout's reserved box measured from the right edge and the top
//   placed: plates already placed this frame [{ x, y, w, h }] (collision pushes this one up)
// returns { x, y, beside } — the plate's top-left and which side it took.
export function placeLabel({ p, right, outer, left, louter, w, h, offset = [0, 0], width = 1920, height = 1080, safeW = 96,
                             readout = { x: 460, y: 330 }, captionZone = 260, holdFrac = 0.76, placed = [] }) {
  let x = Math.round(p.x + offset[0] - w / 2), y = Math.round(p.y + offset[1] - h);
  let beside = 0;
  if (right && right.visible && Math.max(72, y) + h > right.y - 8) {                       // it would sit on the top bar
    x = Math.round((outer ? outer.x + Math.abs(outer.x - right.x) : right.x) + 24);
    y = Math.round(Math.max(72, right.y - h / 2)); beside = 1;
    if (x + w > width - readout.x && y < readout.y && left && left.visible) {              // that side is the readout's
      x = Math.round((louter ? louter.x - Math.abs(louter.x - left.x) : left.x) - 24 - w); beside = 2;
    }
  }
  x = Math.max(safeW, Math.min(width - safeW - w, x));                                      // inside the safe area
  const holdY = Math.round(height * holdFrac) - h;                                          // the hold line
  y = Math.max(72, Math.min(height - captionZone, holdY, y));                               // never in the caption zone, never past the hold line
  if (x + w > width - readout.x && y < readout.y) y = readout.y;                            // never over the corner readout
  for (let guard = 0; guard < 6; guard++) {                                                 // collision: pushed up, deterministic
    const hit = placed.find((b) => x < b.x + b.w + 12 && x + w + 12 > b.x && y < b.y + b.h + 8 && y + h + 8 > b.y);
    if (!hit) break;
    y = hit.y - h - 10;
  }
  return { x, y, beside };
}

// plateBox(anchorsAt(t), anchorName, text, opts) — the sweep's plate(t): the same rule on the same projections,
// with the plate size estimated from the mono type (18 px per glyph + 36 px padding, 50 px tall at 1080p).
export function plateBox(an, name, content, opts = {}) {
  const p = an[name]; if (!p || !p.visible) return null;
  const w = opts.w || content.length * 18 + 36, h = opts.h || 50;
  const r = placeLabel({ p, right: an[name + '-right'], outer: an[name + '-right-outer'], left: an[name + '-left'], louter: an[name + '-left-outer'], w, h, ...opts });
  return { x: r.x, y: r.y, w, h, beside: r.beside };
}

