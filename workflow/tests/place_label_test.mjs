// place_label_test.mjs — the shared placement rule takes the side the rule says, honours the hold line, and the
// sweep's plateBox reproduces the HUD's placement. Run: node workflow/tests/place_label_test.mjs
import { placeLabel, plateBox } from '../templates/film/place_label.js';
const results = [];
const expect = (name, ok, detail = '') => results.push([ok, name, detail]);
const W = 1920, H = 1080, w = 300, h = 50;
// 1. room above the anchor: the plate sits above, centred
let r = placeLabel({ p: { x: 960, y: 500, visible: true }, right: { x: 1100, y: 480, visible: true }, w, h, offset: [0, -60], width: W, height: H });
expect('above the anchor when there is room', r.beside === 0 && r.x === 810 && r.y === 390, JSON.stringify(r));
// 2. the plate would sit on the top bar (right.y - 8 is above the plate's bottom): beside the right post, past its outer face
r = placeLabel({ p: { x: 960, y: 120, visible: true }, right: { x: 1100, y: 100, visible: true }, outer: { x: 1110, y: 100, visible: true }, w, h, offset: [0, -60], width: W, height: H });
expect('beside the right post past its outer face', r.beside === 1 && r.x === 1144 && r.y === 75, JSON.stringify(r));
// 3. the right side is the readout's (x + w > width - 460 and y < 330): beside the left post
r = placeLabel({ p: { x: 1500, y: 120, visible: true }, right: { x: 1600, y: 100, visible: true }, outer: { x: 1610, y: 100, visible: true }, left: { x: 1300, y: 100, visible: true }, louter: { x: 1290, y: 100, visible: true }, w, h, offset: [0, -60], width: W, height: H });
expect('beside the left post when the right is the readout side', r.beside === 2 && r.x === 956 && r.y === 75, JSON.stringify(r));
// 4. the hold line: an anchor low in the frame does not drag the plate past holdFrac
r = placeLabel({ p: { x: 960, y: 1000, visible: true }, w, h, offset: [0, -60], width: W, height: H, holdFrac: 0.76 });
expect('holds at the hold line (0.76 x 1080 - h = 771)', r.y === 771, JSON.stringify(r));
r = placeLabel({ p: { x: 540, y: 1700, visible: true }, w, h, offset: [0, -60], width: 1080, height: 1920, safeW: 64, readout: { x: 400, y: 420 }, captionZone: 420, holdFrac: 0.6 });
expect('portrait hold line (0.60 x 1920 - h = 1102)', r.y === 1102, JSON.stringify(r));
// 5. collision: a later plate is pushed above an earlier one
r = placeLabel({ p: { x: 960, y: 500, visible: true }, w, h, offset: [0, -60], width: W, height: H, placed: [{ x: 810, y: 380, w, h }] });
expect('a colliding plate is pushed up', r.y === 380 - h - 10, JSON.stringify(r));
// 6. plateBox reproduces placeLabel from an anchors() map
const an = { g: { x: 960, y: 120, visible: true }, 'g-right': { x: 1100, y: 100, visible: true }, 'g-right-outer': { x: 1110, y: 100, visible: true } };
const b = plateBox(an, 'g', 'HALVING 1 · 25 BTC', { offset: [0, -60], width: W, height: H });   // 360 px wide: reaches the readout's box, so it drops to y = 330
expect('plateBox = placeLabel on the same projections (and the readout rule applies)', b && b.beside === 1 && b.x === 1144 && b.y === 330 && b.w === 360, JSON.stringify(b));
const b2 = plateBox(an, 'g', 'HALVING 1', { offset: [0, -60], width: W, height: H });             // 198 px wide: clear of the readout, beside the post at y 75
expect('plateBox: a narrower plate stays beside the post', b2 && b2.beside === 1 && b2.x === 1144 && b2.y === 75, JSON.stringify(b2));
expect('plateBox is null when the anchor is not visible', plateBox({ g: { x: 0, y: 0, visible: false } }, 'g', 'X') === null);
let bad = 0;
for (const [ok, name, detail] of results) { console.log((ok ? 'ok   ' : 'FAIL ') + name + (ok ? '' : '  ' + detail)); if (!ok) bad++; }
console.log('place_label_test: ' + (results.length - bad) + '/' + results.length + ' expectations hold');
process.exit(bad ? 1 : 0);
