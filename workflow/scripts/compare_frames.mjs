#!/usr/bin/env node
// compare_frames.mjs — styleframe vs reference, side by side, with numbers (worldfilm stage 1 "reference lock").
// Each pair is rendered as one row: the styleframe, the reference frame (a still, or a video at @seconds), and a
// caption with the measured distance between them: palette (mean nearest-colour distance of the top buckets),
// luma mean/std, saturation, edge density. The sheet is for the human and the storyboard critic; the JSON is
// for the ledger.
//
// usage: node compare_frames.mjs --pairs "styleframes/s01.png=references/ref.mp4@12.5;styleframes/s02.png=references/still.png"
//                                --out gates/compare-sheet.png [--tile 640] [--json gates/compare.json]
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
function loadPlaywright() {
  const roots = [process.cwd(), path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "studio"), process.env.WORLDFILM_STUDIO || ""];
  for (const r of roots) { try { return require(path.join(r, "node_modules", "playwright")); } catch {} }
  try { return require("playwright"); } catch {}
  console.error("playwright not found: run 'npm i playwright && npx playwright install chromium' in studio/"); process.exit(2);
}
const { chromium } = loadPlaywright();
const argv = process.argv.slice(2);
const flag = (k, d) => { const i = argv.indexOf("--" + k); return i === -1 ? d : argv[i + 1]; };
const pairsArg = flag("pairs", null), out = flag("out", "gates/compare-sheet.png"), tile = Number(flag("tile", 640));
if (!pairsArg) { console.error("--pairs \"a.png=ref.mp4@12.5;b.png=still.png\" is required"); process.exit(2); }
const jsonOut = flag("json", out.replace(/\.[^.]+$/, ".json"));
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "wf-compare-"));

function frameOf(spec, i) {   // "ref.mp4@12.5" -> extracted PNG; stills pass through
  const m = /^(.*)@([0-9.]+)$/.exec(spec);
  if (!m) { if (!fs.existsSync(spec)) { console.error("no such file: " + spec); process.exit(2); } return { file: path.resolve(spec), label: path.basename(spec) }; }
  const [, vid, t] = m;
  const png = path.join(tmp, `ref_${i}.png`);
  const r = spawnSync("ffmpeg", ["-v", "error", "-y", "-ss", t, "-i", vid, "-frames:v", "1", png]);
  if (r.status !== 0 || !fs.existsSync(png)) { console.error(`could not extract a frame at ${t}s from ${vid} (past the end?)${r.stderr.toString() ? ": " + r.stderr.toString() : ""}`); process.exit(1); }
  return { file: png, label: `${path.basename(vid)} @ ${t}s` };
}
const pairs = pairsArg.split(";").filter(Boolean).map((p, i) => {
  const [a, b] = p.split("=");
  if (!fs.existsSync(a)) { console.error("no such file: " + a); process.exit(2); }
  return { style: { file: path.resolve(a), label: path.basename(a) }, ref: frameOf(b, i) };
});
const dataUrl = (f) => `data:image/${/\.jpe?g$/i.test(f) ? "jpeg" : "png"};base64,` + fs.readFileSync(f).toString("base64");

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: tile * 2 + 60, height: 800 }, deviceScaleFactor: 1 });
const html = `<!doctype html><meta charset="utf-8"><style>
body{margin:0;background:#15171b;color:#e8e6e1;font:14px/1.4 -apple-system,Helvetica,Arial,sans-serif;padding:20px}
.row{display:grid;grid-template-columns:${tile}px ${tile}px;gap:20px;margin-bottom:26px}
img{width:${tile}px;display:block;background:#000} .cap{color:#9aa0a6;font-size:12px;margin-top:4px}
.m{grid-column:1/3;font:12px/1.5 ui-monospace,Menlo,monospace;color:#cfd3d8;white-space:pre}
h1{font-size:15px;margin:0 0 14px;color:#fff} .k{color:#f2b134}</style>
<h1>worldfilm reference lock — styleframe (left) vs reference (right)</h1>
${pairs.map((p, i) => `<div class="row" data-i="${i}"><div><img id="a${i}" src="${dataUrl(p.style.file)}"><div class="cap">styleframe: ${p.style.label}</div></div><div><img id="b${i}" src="${dataUrl(p.ref.file)}"><div class="cap">reference: ${p.ref.label}</div></div><div class="m" id="m${i}">measuring…</div></div>`).join("")}`;
await page.setContent(html);
const metrics = await page.evaluate(async (n) => {
  const stats = (img) => {
    const W = 192, H = Math.max(2, Math.round(192 * img.naturalHeight / img.naturalWidth));
    const c = document.createElement("canvas"); c.width = W; c.height = H; const g = c.getContext("2d"); g.drawImage(img, 0, 0, W, H);
    const d = g.getImageData(0, 0, W, H).data, N = W * H;
    let lum = 0, lum2 = 0, sat = 0; const buckets = new Map(); let edges = 0;
    const L = new Float32Array(N);
    for (let i = 0; i < N; i++) {
      const r = d[i * 4], gg = d[i * 4 + 1], b = d[i * 4 + 2];
      const l = 0.2126 * r + 0.7152 * gg + 0.0722 * b; L[i] = l; lum += l; lum2 += l * l;
      const mx = Math.max(r, gg, b), mn = Math.min(r, gg, b); sat += mx ? (mx - mn) / mx : 0;
      const k = ((r >> 4) << 8) | ((gg >> 4) << 4) | (b >> 4); const v = buckets.get(k) || [0, 0, 0, 0]; v[0] += r; v[1] += gg; v[2] += b; v[3]++; buckets.set(k, v);
    }
    for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) { const i = y * W + x; const gx = L[i + 1] - L[i - 1], gy = L[i + W] - L[i - W]; if (Math.sqrt(gx * gx + gy * gy) > 40) edges++; }
    const pal = [...buckets.values()].sort((a, b) => b[3] - a[3]).slice(0, 6).map(([r, gg, b, k]) => ({ rgb: [r / k, gg / k, b / k], share: k / N }));
    const mean = lum / N;
    return { luma_mean: mean, luma_std: Math.sqrt(Math.max(0, lum2 / N - mean * mean)), saturation: sat / N, edge_density: edges / N, palette: pal };
  };
  const dist = (a, b) => Math.sqrt(a.reduce((s, v, i) => s + (v - b[i]) ** 2, 0));
  const hex = (c) => "#" + c.map((v) => Math.round(v).toString(16).padStart(2, "0")).join("");
  const outAll = [];
  for (let i = 0; i < n; i++) {
    const A = document.getElementById("a" + i), B = document.getElementById("b" + i);
    await A.decode(); await B.decode();
    const sa = stats(A), sb = stats(B);
    const palDist = sa.palette.reduce((s, p) => s + p.share * Math.min(...sb.palette.map((q) => dist(p.rgb, q.rgb))), 0) / sa.palette.reduce((s, p) => s + p.share, 0);
    const m = { palette_distance: palDist, luma_mean: [sa.luma_mean, sb.luma_mean], luma_std: [sa.luma_std, sb.luma_std], saturation: [sa.saturation, sb.saturation], edge_density: [sa.edge_density, sb.edge_density],
      palette_style: sa.palette.map((p) => hex(p.rgb)), palette_ref: sb.palette.map((p) => hex(p.rgb)) };
    const verdict = palDist < 24 && Math.abs(sa.luma_mean - sb.luma_mean) < 30 && Math.abs(sa.edge_density - sb.edge_density) < 0.08 ? "close" : palDist < 48 ? "near" : "far";
    document.getElementById("m" + i).innerHTML = `<span class="k">${verdict}</span>  palette distance ${palDist.toFixed(1)}  (style ${m.palette_style.slice(0, 4).join(" ")} | ref ${m.palette_ref.slice(0, 4).join(" ")})\nluma mean ${sa.luma_mean.toFixed(0)} vs ${sb.luma_mean.toFixed(0)}   luma std ${sa.luma_std.toFixed(0)} vs ${sb.luma_std.toFixed(0)}   saturation ${sa.saturation.toFixed(2)} vs ${sb.saturation.toFixed(2)}   edge density ${(sa.edge_density * 100).toFixed(1)}% vs ${(sb.edge_density * 100).toFixed(1)}%`;
    m.verdict = verdict; outAll.push(m);
  }
  return outAll;
}, pairs.length);
await page.setViewportSize({ width: tile * 2 + 60, height: Math.max(400, await page.evaluate(() => document.body.scrollHeight) + 40) });
fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
await page.screenshot({ path: out, fullPage: true });
await browser.close();
fs.writeFileSync(jsonOut, JSON.stringify({ sheet: path.resolve(out), pairs: pairs.map((p, i) => ({ styleframe: p.style.file, reference: p.ref.label, ...metrics[i] })) }, null, 2));
console.log(`compare sheet: ${pairs.length} pairs -> ${out}`);
for (let i = 0; i < pairs.length; i++) console.log(`  ${metrics[i].verdict.padEnd(5)} ${path.basename(pairs[i].style.file)} vs ${pairs[i].ref.label}: palette distance ${metrics[i].palette_distance.toFixed(1)}, luma ${metrics[i].luma_mean[0].toFixed(0)}/${metrics[i].luma_mean[1].toFixed(0)}`);
