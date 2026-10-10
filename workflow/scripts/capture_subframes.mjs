#!/usr/bin/env node
// capture_subframes.mjs — frame-exact capture of a seekable composition with sub-frame motion blur
// (worldfilm stage 9, the Playwright route). The HyperFrames engine has the same model (`motionBlur`:
// shutterAngle 180, shutterPhase -90, samplesPerFrame) but the CLI does not expose it yet, so this script owns
// the shutter: for every output frame it seeks N sample times across the shutter window, screenshots each, and
// ffmpeg's tmix averages them (default 4 sub-frames over a 180 degree shutter). Samples never cross a hard cut: a
// cut listed in --cuts clamps the window to the side the frame instant is on.
//
// usage:
//   node capture_subframes.mjs --dir <composition dir> [--entry index.html] --out renders/master-blur.mp4
//        [--fps 60] [--duration 30] [--from 0] [--to 30] [--width 1920] [--height 1080] [--dpr 1]
//        [--samples 4] [--shutter 180] [--phase -90] [--cuts 9.0,13.0,17.0]
//        [--ready "<js expr that is truthy when the page can seek>"] [--seek "<js function (t)=>...>"]
//        [--format jpeg|png] [--quality 95] [--crf 16] [--preset slow] [--gpu] [--chromium /path/to/chrome]
//   node capture_subframes.mjs --dir <dir> --stills 0,4,8,12 --out gates/stills.png [--cols 4]   (review sheet, no blur)
//
// The page contract (same as HyperFrames): a paused GSAP timeline registered as window.__timelines.main, or a
// window.__worldfilm.seek(t) / window.SIM.seek(t) / window.seek(t) function; every frame a pure function of t.
import { spawn, spawnSync } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
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
const has = (k) => argv.includes("--" + k);
const num = (k, d) => { const v = flag(k, null); return v === null ? d : Number(v); };

const dir = flag("dir", null);
if (!dir || !fs.existsSync(dir)) { console.error("--dir <composition dir> is required"); process.exit(2); }
const entry = flag("entry", "index.html");
const out = flag("out", "renders/blur.mp4");
const fps = num("fps", 60), width = num("width", 1920), height = num("height", 1080), dpr = num("dpr", 1);
const samples = Math.max(1, Math.round(num("samples", 4)));
const shutter = num("shutter", 180), phase = num("phase", -90);
const format = flag("format", "jpeg"), quality = num("quality", 95), crf = num("crf", 16), preset = flag("preset", "slow");
const cuts = (flag("cuts", "") || "").split(",").filter(Boolean).map(Number).sort((a, b) => a - b);
const readyExpr = flag("ready", "(window.__timelines && (window.__timelines.main || Object.keys(window.__timelines).length)) || (window.__worldfilm && window.__worldfilm.seek) || (window.SIM && window.SIM.seek) || window.seek");
const seekSrc = flag("seek", "(t) => { const T = window.__timelines; const tl = T && (T.main || Object.values(T)[0]); if (tl) { tl.pause(); tl.time(t, false); } if (window.__worldfilm && window.__worldfilm.seek) window.__worldfilm.seek(t); if (window.SIM && window.SIM.seek) window.SIM.seek(t); if (typeof window.seek === 'function') window.seek(t); }");
const stills = flag("stills", null);
const cols = num("cols", 4);

// --- tiny static server for the composition dir (ES modules do not load over file://)
const MIME = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css", ".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".svg": "image/svg+xml", ".wav": "audio/wav", ".mp3": "audio/mpeg", ".mp4": "video/mp4", ".webm": "video/webm", ".ttf": "font/ttf", ".otf": "font/otf", ".woff": "font/woff", ".woff2": "font/woff2", ".csv": "text/csv", ".glb": "model/gltf-binary", ".hdr": "application/octet-stream" };
const root = path.resolve(dir);
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(new URL(req.url, "http://x").pathname);
  let p = u === "/__entry__.html" ? path.join(root, entry) : path.join(root, u);   // HyperFrames serves sub-compositions with the project root as base URL; so do we
  if (!p.startsWith(root)) { res.writeHead(403); return res.end(); }
  if (fs.existsSync(p) && fs.statSync(p).isDirectory()) p = path.join(p, "index.html");
  if (!fs.existsSync(p)) { res.writeHead(404); return res.end("not found: " + u); }
  const range = req.headers.range, size = fs.statSync(p).size, type = MIME[path.extname(p).toLowerCase()] || "application/octet-stream";
  if (range) { const m = /bytes=(\d*)-(\d*)/.exec(range); const a = m[1] ? +m[1] : 0, b = m[2] ? +m[2] : size - 1; res.writeHead(206, { "Content-Type": type, "Content-Range": `bytes ${a}-${b}/${size}`, "Content-Length": b - a + 1, "Accept-Ranges": "bytes" }); fs.createReadStream(p, { start: a, end: b }).pipe(res); return; }
  res.writeHead(200, { "Content-Type": type, "Content-Length": size, "Accept-Ranges": "bytes", "Cache-Control": "no-store" });
  fs.createReadStream(p).pipe(res);
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const url = `http://127.0.0.1:${server.address().port}/${entry.includes("/") ? "__entry__.html" : entry}`;

const launchArgs = ["--autoplay-policy=no-user-gesture-required", "--disable-background-timer-throttling", "--force-device-scale-factor=" + dpr];
if (has("gpu")) launchArgs.push("--use-angle=metal", "--ignore-gpu-blocklist", "--enable-gpu-rasterization");
else launchArgs.push("--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader");
const browser = await chromium.launch({ args: launchArgs, executablePath: flag("chromium", undefined) });
const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: dpr });
const errs = [];
page.on("pageerror", (e) => errs.push(String(e)));
page.on("console", (m) => { if (m.type() === "error") errs.push("console: " + m.text()); if (has("verbose")) console.log("[page]", m.type(), m.text().slice(0, 200)); });
page.on("response", (r) => { if (r.status() >= 400) errs.push("HTTP " + r.status() + " " + r.url()); });
if (has("verbose")) page.on("requestfinished", (r) => console.log("[req]", r.url().slice(-60)));
await page.goto(url, { waitUntil: "load", timeout: 120000 });
// readiness: poll with evaluate (Playwright's waitForFunction never fired on a GSAP + WebGL page even though evaluate saw it ready)
{
  const deadline = Date.now() + num("ready-timeout", 180000);
  let ready = false;
  while (Date.now() < deadline) { try { ready = !!(await page.evaluate("!!(" + readyExpr + ")")); } catch {} if (ready) break; await new Promise((r) => setTimeout(r, 250)); }
  if (!ready) { console.error("page never became ready (" + readyExpr + ")"); if (errs.length) console.error("PAGE ERRORS:", errs.slice(0, 10)); await browser.close(); server.close(); process.exit(1); }
}
await page.evaluate("document.fonts && document.fonts.ready");
const seekFn = `(t) => { (${seekSrc})(t); return new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))); }`;
async function seek(t) { await page.evaluate("(" + seekFn + ")(" + t + ")"); }
async function shot() { return page.screenshot({ type: format, ...(format === "jpeg" ? { quality } : {}), clip: { x: 0, y: 0, width, height }, animations: "disabled", caret: "hide" }); }

if (stills) {
  const times = stills.split(",").map(Number);
  const tmp = fs.mkdtempSync(path.join(require("node:os").tmpdir(), "wf-stills-"));
  for (let i = 0; i < times.length; i++) { await seek(times[i]); fs.writeFileSync(path.join(tmp, `s_${String(i).padStart(3, "0")}.png`), await page.screenshot({ type: "png", clip: { x: 0, y: 0, width, height } })); }
  await browser.close(); server.close();
  const rows = Math.ceil(times.length / cols);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  const r = spawnSync("ffmpeg", ["-v", "error", "-y", "-i", path.join(tmp, "s_%03d.png"), "-vf", `scale=480:-1,tile=${cols}x${rows}:padding=6:color=white`, "-frames:v", "1", out]);
  if (r.status !== 0) { console.error(r.stderr.toString()); process.exit(1); }
  fs.writeFileSync(out.replace(/\.[^.]+$/, ".json"), JSON.stringify({ times, cols, tiles: times.map((t, i) => ({ t, col: i % cols, row: Math.floor(i / cols) })) }, null, 2));
  console.log(`stills: ${times.length} -> ${out}`); if (errs.length) console.log("PAGE ERRORS:", errs.slice(0, 8));
  process.exit(0);
}

const duration = num("duration", NaN);
const tFrom = num("from", 0), tTo = num("to", Number.isFinite(duration) ? duration : NaN);
if (!Number.isFinite(tTo)) { console.error("--duration or --to is required"); process.exit(2); }
const f0 = Math.round(tFrom * fps), f1 = Math.round(tTo * fps);
const nFrames = f1 - f0;
const shutterTime = shutter / 360 / fps, windowStart = phase / 360 / fps;
function sampleTimes(frame) {
  const tf = frame / fps;
  const times = [];
  for (let k = 0; k < samples; k++) {
    let t = tf + windowStart + (k + 0.5) / samples * shutterTime;
    for (const c of cuts) { if (t >= c && tf < c) t = Math.max(tf, c - 1e-4); if (t < c && tf >= c) t = c; }  // never across a cut
    times.push(Math.min(Math.max(0, t), Math.max(0, tTo - 1e-4)));
  }
  return times;
}
fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
const vf = samples > 1 ? [`tmix=frames=${samples}`, `select='eq(mod(n\\,${samples})\\,${samples - 1})'`, `setpts=N/${fps}/TB`] : [];
const ffArgs = ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(fps * samples), "-i", "pipe:0", ...(vf.length ? ["-vf", vf.join(",")] : []), "-r", String(fps), "-c:v", "libx264", "-crf", String(crf), "-preset", preset, "-pix_fmt", "yuv420p", "-movflags", "+faststart", out];
const ff = spawn("ffmpeg", ffArgs, { stdio: ["pipe", "inherit", "inherit"] });
let ffClosed = false; ff.on("close", (code) => { ffClosed = true; if (code !== 0) { console.error("ffmpeg exited " + code); process.exit(1); } });
const write = (buf) => new Promise((resolve) => { if (!ff.stdin.write(buf)) ff.stdin.once("drain", resolve); else resolve(); });
const t0 = Date.now();
for (let i = 0; i < nFrames; i++) {
  for (const t of sampleTimes(f0 + i)) { await seek(t); await write(await shot()); }
  if (i % 60 === 0 || i === nFrames - 1) {
    const el = (Date.now() - t0) / 1000, rate = (i + 1) / Math.max(el, 1e-3);
    process.stdout.write(`frame ${i + 1}/${nFrames}  ${rate.toFixed(1)} f/s  eta ${((nFrames - i - 1) / Math.max(rate, 1e-3)).toFixed(0)} s\n`);
  }
}
ff.stdin.end();
await new Promise((r) => { if (ffClosed) r(); else ff.on("close", r); });
await browser.close(); server.close();
const meta = { out, fps, frames: nFrames, from: tFrom, to: tTo, width, height, dpr, samples, shutter, phase, cuts, format, crf, seconds: (Date.now() - t0) / 1000, page_errors: errs.slice(0, 20) };
fs.writeFileSync(out.replace(/\.[^.]+$/, ".capture.json"), JSON.stringify(meta, null, 2));
console.log(`wrote ${out}: ${nFrames} frames x ${samples} samples (${shutter} deg shutter) in ${meta.seconds.toFixed(0)} s`);
if (errs.length) console.log("PAGE ERRORS:", errs.slice(0, 8));
