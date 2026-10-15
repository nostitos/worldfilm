// film/place_label.js — the label placement rule (worldfilm stage 6), ONE pure function shared by the HUD
// (film/main.js draws the plate where it says) and the sweep (tools/sweep.mjs asserts the plate never touches the
// object it names). Keep them on the same function: a rule that lives twice drifts twice.
//
// The rule: a plate sits ABOVE its anchor. When that would overlap the object it names and the world supplies side
// candidates, it moves BESIDE the object: right of the right candidate, past its outer edge (beside = 1); if that
// lands in the reserved readout box, left of the left candidate (beside = 2). Side candidates are optional: without
// them the plate stays above. Then it is clamped to the safe area, kept out of the caption zone and the readout box,
// held at the hold line (holdFrac of the frame height) so it never races a passing object out of frame, and pushed
// up deterministically when it collides with a plate already placed this frame.
//
// placeLabel({ p, right, outer, left, louter, w, h, offset, width, height, safeW, readout, captionZone, holdFrac, placed })
//   p: the projected anchor { x, y, visible } (screen px)
//   right / outer / left / louter: optional projected attachment points <a>-right, <a>-right-outer, <a>-left,
//     <a>-left-outer from anchors(cam): the top of the object's right / left side and the outer edge to clear
//   w, h: the plate's size in px; offset: [dx, dy] with dy < 0 = the gap above the anchor
//   readout: { x, y } = a reserved top-right box measured from the right edge and the top, or null for none
//   captionZone: px reserved at the bottom for captions; safeW: side margin in px; holdFrac: hold line (0-1)
//   placed: plates already placed this frame [{ x, y, w, h }] (collision pushes this one up)
// returns { x, y, beside } — the plate's top-left and which side it took (0 above, 1 right, 2 left).
// Defaults are 1080p starting points; pass the project's own values per composition.
export function placeLabel({ p, right, outer, left, louter, w, h, offset = [0, 0], width = 1920, height = 1080, safeW = 96,
                             readout = { x: 460, y: 330 }, captionZone = 260, holdFrac = 0.76, placed = [] }) {
  let x = Math.round(p.x + offset[0] - w / 2), y = Math.round(p.y + offset[1] - h);
  let beside = 0;
  const inReadout = (px, py) => readout && px + w > width - readout.x && py < readout.y;
  if (right && right.visible && Math.max(72, y) + h > right.y - 8) {                       // above would overlap the object
    x = Math.round((outer ? outer.x + Math.abs(outer.x - right.x) : right.x) + 24);
    y = Math.round(Math.max(72, right.y - h / 2)); beside = 1;
    if (inReadout(x, y) && left && left.visible) {                                         // right side is reserved
      x = Math.round((louter ? louter.x - Math.abs(louter.x - left.x) : left.x) - 24 - w); beside = 2;
    }
  }
  x = Math.max(safeW, Math.min(width - safeW - w, x));                                      // inside the safe area
  const holdY = Math.round(height * holdFrac) - h;                                          // the hold line
  y = Math.max(72, Math.min(height - captionZone, holdY, y));                               // never in the caption zone, never past the hold line
  if (inReadout(x, y)) y = readout.y;                                                       // never over the readout box
  for (let guard = 0; guard < 6; guard++) {                                                 // collision: pushed up, deterministic
    const hit = placed.find((b) => x < b.x + b.w + 12 && x + w + 12 > b.x && y < b.y + b.h + 8 && y + h + 8 > b.y);
    if (!hit) break;
    y = hit.y - h - 10;
  }
  return { x, y, beside };
}

// plateBox(anchorsAt(t), anchorName, text, opts) — the sweep's plate(t): the same rule on the same projections.
// The plate size defaults to an estimate for a monospaced face (18 px per glyph + 36 px padding, 50 px tall at
// 1080p); pass opts.w / opts.h measured from the project's type for exact boxes.
export function plateBox(an, name, content, opts = {}) {
  const p = an[name]; if (!p || !p.visible) return null;
  const w = opts.w || content.length * 18 + 36, h = opts.h || 50;
  const r = placeLabel({ p, right: an[name + '-right'], outer: an[name + '-right-outer'], left: an[name + '-left'], louter: an[name + '-left-outer'], w, h, ...opts });
  return { x: r.x, y: r.y, w, h, beside: r.beside };
}
