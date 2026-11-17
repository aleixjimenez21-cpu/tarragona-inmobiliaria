#!/usr/bin/env node
// Render determinista del reel con Chromium headless (WebGL por software).
// Uso:
//   node tools/render.js scenes            -> build/scenes/s*.mp4 (una por escena)
//   node tools/render.js stills t1 t2 ...  -> build/stills/t_<t>.jpg
//   node tools/render.js cover             -> output/portada.jpg
//   node tools/render.js scenes --only s3  -> solo una escena
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require(path.join(require('child_process').execSync('npm root -g').toString().trim(), 'playwright'))); }

const ROOT = path.resolve(__dirname, '..');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.woff2': 'font/woff2', '.json': 'application/json', '.css': 'text/css' };

function serve() {
  return new Promise((res) => {
    const srv = http.createServer((req, rsp) => {
      const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { rsp.writeHead(404); return rsp.end(); }
      rsp.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
      fs.createReadStream(p).pipe(rsp);
    });
    srv.listen(0, '127.0.0.1', () => res(srv));
  });
}

async function open() {
  const srv = await serve();
  const port = srv.address().port;
  // RENDER_GPU=1 usa la tarjeta gráfica del equipo (mucho más rápido); por defecto, WebGL por software
  const gpu = process.env.RENDER_GPU === '1';
  const args = gpu ? ['--ignore-gpu-blocklist', '--enable-gpu', '--use-angle=default'] : ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-gpu-sandbox'];
  const browser = await chromium.launch({ args, headless: !gpu ? true : (process.env.RENDER_HEADLESS !== '0') });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('console', (m) => { const t = m.text(); if (!/GPU stall|GL Driver Message/.test(t)) console.log('[page]', t); });
  page.on('pageerror', (e) => console.error('[page error]', e.message));
  await page.goto(`http://127.0.0.1:${port}/src/index.html`);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
  const timings = JSON.parse(fs.readFileSync(path.join(ROOT, 'output', 'timings.json'), 'utf8'));
  const t0 = Date.now();
  await page.evaluate((tl) => window.setup(tl), timings);
  console.log(`[render] setup ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  return { srv, browser, page, timings };
}

const b64 = (d) => Buffer.from(d.slice(d.indexOf(',') + 1), 'base64');

async function stills(times) {
  const { srv, browser, page } = await open();
  const dir = path.join(ROOT, 'build', 'stills'); fs.mkdirSync(dir, { recursive: true });
  if (process.env.DBGBEAM) await page.evaluate(() => { window.dbgBeam = true; });
  if (process.env.DEBUGCAM) await page.evaluate((d) => { window.debugCam = JSON.parse(d); }, process.env.DEBUGCAM);
  for (const t of times) {
    const t0 = Date.now();
    const d = await page.evaluate((tt) => window.renderAt(tt, 'jpeg', 0.93), Number(t));
    fs.writeFileSync(path.join(dir, `t_${Number(t).toFixed(2)}.jpg`), b64(d));
    console.log(`[still] t=${t} ${(Date.now() - t0)} ms`);
  }
  await browser.close(); srv.close();
}

function sceneRanges(tl) {
  const T = tl.timeline, fps = tl.fps;
  const f = (x) => Math.round(x * fps);
  const names = ['s1', 's2', 's3', 's4', 's5', 's6'];
  return names.map((n) => ({ name: n, a: f(T[n][0]), b: f(T[n][1]) }));
}

async function scenes(only) {
  const { srv, browser, page, timings } = await open();
  const dir = path.join(ROOT, 'build', 'scenes'); fs.mkdirSync(dir, { recursive: true });
  // "s3#1/2" renderiza la primera mitad de la escena 3 en s3_p1.mp4 (para repartir entre procesos)
  let ranges = [];
  for (const r of sceneRanges(timings)) {
    const specs = only ? only.filter((o) => o.split('#')[0] === r.name) : [r.name];
    for (const sp of specs) {
      const m = sp.match(/#(\d+)\/(\d+)$/);
      if (!m) { ranges.push(r); continue; }
      const i = +m[1], n = +m[2], len = r.b - r.a;
      ranges.push({ name: `${r.name}_p${i}`, a: r.a + Math.floor(len * (i - 1) / n), b: r.a + Math.floor(len * i / n) });
    }
  }
  for (const r of ranges) {
    const out = path.join(dir, `${r.name}.mp4`);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(timings.fps), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', '-tune', 'grain', '-r', String(timings.fps), out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let n = r.a; n < r.b; n++) {
      const d = await page.evaluate((nn) => window.renderFrame(nn, 'jpeg', 0.96), n);
      if (!ff.stdin.write(b64(d))) await new Promise((res) => ff.stdin.once('drain', res));
      if ((n - r.a) % 30 === 0) {
        const el = (Date.now() - t0) / 1000, done = n - r.a + 1;
        console.log(`[${r.name}] ${done}/${r.b - r.a}  ${(el / done).toFixed(2)} s/frame`);
      }
    }
    ff.stdin.end();
    await new Promise((res) => ff.on('close', res));
    console.log(`[render] ${r.name} -> ${out} (${((Date.now() - t0) / 1000).toFixed(0)} s)`);
  }
  await browser.close(); srv.close();
}

async function cover() {
  const { srv, browser, page } = await open();
  const d = await page.evaluate(() => window.renderCover());
  fs.mkdirSync(path.join(ROOT, 'output'), { recursive: true });
  fs.writeFileSync(path.join(ROOT, 'output', 'portada.jpg'), b64(d));
  console.log('[render] output/portada.jpg');
  await browser.close(); srv.close();
}

(async () => {
  const [cmd, ...rest] = process.argv.slice(2);
  if (cmd === 'stills') await stills(rest);
  else if (cmd === 'scenes') { const i = rest.indexOf('--only'); await scenes(i >= 0 ? rest.slice(i + 1) : null); }
  else if (cmd === 'cover') await cover();
  else { console.log('uso: render.js scenes|stills|cover'); process.exit(1); }
})().catch((e) => { console.error(e); process.exit(1); });
