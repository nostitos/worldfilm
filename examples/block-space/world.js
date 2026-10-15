// world.js — "Block Space": the simulated world. One building per 2,016-block difficulty period along a boulevard,
// height = the block subsidy; the past is concrete, the future is wireframe; halving gates and the NOW gate are the
// only orange. Everything is laid out ONCE at load into instanced geometry (worldfilm stage 3): render(t, cam) only
// moves the camera, anchors(cam) projects the label points, events come from film/data.js. No timers, no Math.random.
import * as THREE from './vendor/three.module.js';
import { DATA } from './film/data.js';

const C = DATA.colors;
const ROAD = 4.2, DEPTH = 2.0, WIDTH = 0.8, MIN_H = 0.045;
const HAIR_H = 0.2, HAIR_SUB = 0.78125;   // from halving 6 (0.78125 BTC, about 2032) a slab is a rung: the schedule thins to a hairline
const hexNum = (h) => parseInt(h.slice(1), 16);

// portalFade (world units, 0 = off): the portrait cut only. Its wider vertical field keeps a portal's ground bar on screen until
// the camera is almost over it, so the bar left the bottom of the frame in one frame (a pop, measured by detect_pops on the
// 1080x1920 Docker render at 13.17 s and 15.62 s). With portalFade > 0 each portal dissolves over the last portalFade units of the
// approach, a pure function of the pose. The 16:9 master passes 0 and keeps the shared material: its frames do not change.
export function createWorld(canvas, { width, height, portalFade = 0 }) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(1);
  renderer.setSize(width, height, false);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.7;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  // sky: a vertical gradient (dark zenith -> ink-grey horizon) so a frame with sky is never a flat black wall (critic r4)
  const skyCanvas = document.createElement('canvas'); skyCanvas.width = 1; skyCanvas.height = 256;
  const sg = skyCanvas.getContext('2d'); const grad = sg.createLinearGradient(0, 0, 0, 256); grad.addColorStop(0, '#0e1013'); grad.addColorStop(0.55, '#181b1f'); grad.addColorStop(1, '#2a2f35'); sg.fillStyle = grad; sg.fillRect(0, 0, 1, 256);
  const skyTex = new THREE.CanvasTexture(skyCanvas); skyTex.colorSpace = THREE.SRGBColorSpace; skyTex.minFilter = THREE.LinearFilter; skyTex.magFilter = THREE.LinearFilter;
  scene.background = skyTex;
  scene.fog = new THREE.FogExp2(0x1d2126, 0.008);
  const camera = new THREE.PerspectiveCamera(40, width / height, 0.2, 2000);

  // light: one key from the past side, a cold hemisphere, no shadows (software GL in Docker)
  scene.add(new THREE.HemisphereLight(0x8f939a, 0x23262b, 2.3));
  const key = new THREE.DirectionalLight(0xfff1dc, 3.0);
  key.position.set(-40, 60, 30);
  scene.add(key);
  const rim = new THREE.DirectionalLight(0xe4e6ea, 1.2);
  rim.position.set(60, 30, -40);
  scene.add(rim);

  // ground + road: both END at the last subsidy block (critic r1: "the street does not end"); beyond it, the void
  const GROUND_LEN = DATA.end_x + 200;
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(GROUND_LEN, 400), new THREE.MeshStandardMaterial({ color: 0x23272d, roughness: 1, metalness: 0 }));
  ground.rotation.x = -Math.PI / 2;
  ground.position.set(DATA.end_x - GROUND_LEN / 2, -0.06, 0);   // well below the road: a 1 mm gap z-fought at 300 units (pops gate, draft3)
  scene.add(ground);
  // the road is the mined street: it ends at NOW. The scheduled future is bare ground with the drawn schedule on it.
  const ROAD_LEN = DATA.now_x + 20;
  const road = new THREE.Mesh(new THREE.PlaneGeometry(ROAD_LEN, ROAD), new THREE.MeshStandardMaterial({ color: 0x2e333a, roughness: 1 }));
  road.rotation.x = -Math.PI / 2;
  road.position.set(DATA.now_x - ROAD_LEN / 2, 0.0, 0);
  road.material.polygonOffset = true; road.material.polygonOffsetFactor = -1; road.material.polygonOffsetUnits = -1;
  scene.add(road);

  // buildings: solids for the past (instanced), edges for all (one merged LineSegments per class)
  const periods = DATA.periods; // [i, subsidy, past]
  const past = periods.filter((p) => p[2] === 1);
  const box = new THREE.BoxGeometry(1, 1, 1);
  box.translate(0, 0.5, 0);
  const solidMat = new THREE.MeshStandardMaterial({ color: 0x444a52, roughness: 0.8, metalness: 0.0 });
  const solids = new THREE.InstancedMesh(box, solidMat, past.length);
  const m = new THREE.Matrix4();
  // seeded per-period variation of depth and setback (never of pitch or height): a periodic street strobes when the
  // camera moves near one slab per frame (pops gate, draft5) and reads as standing still at other speeds (critic r1)
  const rng = (i) => { let x = (i + 1) * 2654435761 + DATA.world_seed * 97; x = (x ^ (x >>> 13)) * 1274126177; return ((x ^ (x >>> 16)) >>> 0) / 4294967296; };
  const place = (p) => { const i = p[0]; const h = Math.max(MIN_H, (p[1] / 1e8) * DATA.hs); const side = i % 2 === 0 ? 1 : -1; const d = DEPTH * (0.7 + 0.6 * rng(i)); const back = 0.9 * rng(i + 7919); return { x: i * DATA.u, h, z: side * (ROAD / 2 + d / 2 + back), d, w: WIDTH * (0.86 + 0.14 * rng(i + 104729)) }; };
  past.forEach((p, k) => { const { x, h, z, d, w } = place(p); m.makeScale(w, h, d); m.setPosition(x, 0, z); solids.setMatrixAt(k, m); });
  solids.instanceMatrix.needsUpdate = true;
  scene.add(solids);
  const edgeOf = (list, color, opacity) => {
    const pos = [];
    const e = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]];
    for (const p of list) {
      const { x, h, z, d, w } = place(p);
      if ((p[1] / 1e8) * DATA.hs < HAIR_H) continue;   // thinner than a line can show: drawn as a solid rung by the ladder below
      const v = [[-w / 2, 0, -d / 2], [w / 2, 0, -d / 2], [w / 2, 0, d / 2], [-w / 2, 0, d / 2], [-w / 2, h, -d / 2], [w / 2, h, -d / 2], [w / 2, h, d / 2], [-w / 2, h, d / 2]];
      for (const [a, b] of e) pos.push(x + v[a][0], v[a][1], z + v[a][2], x + v[b][0], v[b][1], z + v[b][2]);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    return new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color, transparent: true, opacity, fog: true }));
  };
  scene.add(edgeOf(past, hexNum(C.ink), 0.9));
  const futureEdges = edgeOf(periods.filter((p) => p[2] === 0), hexNum(C.ink), 0.6);
  scene.add(futureEdges);
  // the ladder: from halving 6 the schedule is one line down the street axis. Each period is a solid rung (an unlit
  // strip, so it stays visible at phone scale) whose length is a log scale of its subsidy, joined by a spine that
  // tapers to the last block. Ink, 0.9 opacity (critic r7: a line that thins out, not dotted road marking).
  const hair = periods.filter((p) => p[2] === 0 && (p[1] / 1e8) * DATA.hs < HAIR_H);
  const rungMat = new THREE.MeshBasicMaterial({ color: hexNum(C.ink), transparent: true, opacity: 0.9, fog: true });
  const rungGeo = new THREE.BoxGeometry(1, 1, 1); rungGeo.translate(0, 0.5, 0);
  const rungs = new THREE.InstancedMesh(rungGeo, rungMat, hair.length);
  hair.forEach((p, k) => { const u = Math.max(0, Math.min(1, Math.log2(Math.max(1, p[1])) / Math.log2(HAIR_SUB * 1e8))); const len = 0.35 + (ROAD - 0.35) * u; m.makeScale(0.08, 0.03, len); m.setPosition(p[0] * DATA.u, 0.0, 0); rungs.setMatrixAt(k, m); });
  rungs.instanceMatrix.needsUpdate = true;
  scene.add(rungs);
  const x0 = hair.length ? hair[0][0] * DATA.u : DATA.end_x, x1 = DATA.end_x;
  const spineGeo = new THREE.BufferGeometry();
  spineGeo.setAttribute('position', new THREE.Float32BufferAttribute([x0, 0.012, -0.08, x0, 0.012, 0.08, x1, 0.012, 0.012, x1, 0.012, -0.012], 3));
  spineGeo.setIndex([0, 1, 2, 0, 2, 3]);
  scene.add(new THREE.Mesh(spineGeo, rungMat));
  const ladderMats = [rungMat];

  // gates: a thin orange post pair + ground line at each halving, a taller one at NOW, a marker at the last block.
  // Unlit and exempt from tone mapping so the rendered pixel IS the brand orange (critic r1: ACES made it yellow).
  const gateMat = new THREE.MeshBasicMaterial({ color: hexNum(C.accent), fog: true, toneMapped: false });
  const gates = new THREE.Group();
  const portals = [];   // { x, mat } for the portals that dissolve (portalFade > 0 only)
  const addGate = (x, h, thick, mat = gateMat) => {
    for (const s of [-1, 1]) { const post = new THREE.Mesh(new THREE.BoxGeometry(thick, h, thick), mat); post.position.set(x, h / 2, s * (ROAD / 2 - 0.1)); gates.add(post); }
    const bar = new THREE.Mesh(new THREE.BoxGeometry(thick, thick, ROAD), mat); bar.position.set(x, 0.02, 0); gates.add(bar);
  };
  // the first four gates and NOW are portals: posts taller than the roof line they halve, with a top bar (critic r4: a gate, not a tick)
  const addPortal = (x, h, thick) => {
    let mat = gateMat;
    if (portalFade > 0) { mat = gateMat.clone(); mat.transparent = true; portals.push({ x, mat }); }
    addGate(x, h, thick, mat);
    const top = new THREE.Mesh(new THREE.BoxGeometry(thick, thick, ROAD - 0.2 + thick), mat); top.position.set(x, h, 0); gates.add(top);
  };
  for (let k = 1; k <= 33; k++) { const x = DATA.halving_x[String(k)]; const roofOld = (50 / Math.pow(2, k - 1)) * DATA.hs; if (k <= 4) addPortal(x, roofOld * 1.12, 0.35); else addGate(x, Math.max(0.6, (50 / Math.pow(2, k)) * DATA.hs), 0.1); }
  addPortal(DATA.now_x, 3.0, 0.3);
  const last = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.3, 0.3), gateMat); last.position.set(DATA.end_x, 0.15, 0); gates.add(last);

  scene.add(gates);

  // the camera rig: pos / look come from film.js; fog density follows height (a pure function of the pose)
  const anchorsWorld = {
    'period-0': new THREE.Vector3(0, Math.max(MIN_H, 50 * DATA.hs) + 0.3, ROAD / 2 + DEPTH / 2),
    'now': new THREE.Vector3(DATA.now_x, 3.7, 0),
    'last': new THREE.Vector3(DATA.end_x, 0.6, 0),
  };
  for (let k = 1; k <= 33; k++) {
    const gh = k <= 4 ? (50 / Math.pow(2, k - 1)) * DATA.hs * 1.12 : Math.max(0.6, (50 / Math.pow(2, k)) * DATA.hs);
    anchorsWorld['halving-' + k] = new THREE.Vector3(DATA.halving_x[String(k)], gh + 0.6, 0);
    anchorsWorld['halving-' + k + '-right'] = new THREE.Vector3(DATA.halving_x[String(k)], gh, ROAD / 2 - 0.1);   // the right post's top: where a label goes when it cannot sit above
    anchorsWorld['halving-' + k + '-right-outer'] = new THREE.Vector3(DATA.halving_x[String(k)], gh, ROAD / 2 - 0.1 + (k <= 4 ? 0.175 : 0.05));
    anchorsWorld['halving-' + k + '-left'] = new THREE.Vector3(DATA.halving_x[String(k)], gh, -(ROAD / 2 - 0.1));
    anchorsWorld['halving-' + k + '-left-outer'] = new THREE.Vector3(DATA.halving_x[String(k)], gh, -(ROAD / 2 - 0.1 + (k <= 4 ? 0.175 : 0.05)));
  }
  anchorsWorld['now-left'] = new THREE.Vector3(DATA.now_x, 3.0, -(ROAD / 2 - 0.1));
  anchorsWorld['now-left-outer'] = new THREE.Vector3(DATA.now_x, 3.0, -(ROAD / 2 - 0.1 + 0.15));
  anchorsWorld['now-right'] = new THREE.Vector3(DATA.now_x, 3.0, ROAD / 2 - 0.1);
  anchorsWorld['now-right-outer'] = new THREE.Vector3(DATA.now_x, 3.0, ROAD / 2 - 0.1 + 0.15);
  const tmp = new THREE.Vector3();

  function render(cam) {
    camera.fov = cam.fov;
    camera.aspect = width / height;
    camera.position.set(cam.pos[0], cam.pos[1], cam.pos[2]);
    camera.up.set(0, 1, 0);
    camera.lookAt(cam.look[0], cam.look[1], cam.look[2]);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld();
    scene.fog.density = 0.0085 * Math.pow(Math.max(0.1, 6 / Math.max(6, cam.pos[1])), 0.8);
    for (const P of portals) {   // dissolve over the last portalFade units of the approach (smoothstep), gone once the camera is past the plane
      const d = (P.x - cam.pos[0]) / portalFade;
      const a = d <= 0 ? 0 : d >= 1 ? 1 : d * d * (3 - 2 * d);
      P.mat.opacity = a; P.mat.visible = a > 0;
    }
    renderer.render(scene, camera);
  }
  function anchors(cam) {
    const out = {};
    for (const [id, v] of Object.entries(anchorsWorld)) {
      tmp.copy(v).project(camera);
      const behind = tmp.z > 1 || tmp.z < -1;
      const sx = (tmp.x + 1) / 2 * width, sy = (1 - tmp.y) / 2 * height;
      const dist = camera.position.distanceTo(v);
      out[id] = { x: sx, y: sy, visible: !behind && sx > -200 && sx < width + 200 && sy > -200 && sy < height + 200, dist };
    }
    return out;
  }
  const setFutureOpacity = (a) => { futureEdges.material.opacity = 0.6 * a; for (const mm of ladderMats) mm.opacity = 0.9 * a; };
  return { render, anchors, setFutureOpacity, dispose: () => renderer.dispose(), renderer, scene, camera };
}
