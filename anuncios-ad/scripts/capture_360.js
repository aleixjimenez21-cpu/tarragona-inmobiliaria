// Captura frame a frame de los tours 360 (Photo Sphere Viewer) de Villa Aurea y Serra.
// Cada fotograma fija la cámara (yaw/pitch/zoom) con una curva suave y hace una captura:
// el movimiento sale perfectamente fluido aunque el render por software sea lento.
// Uso: node capture_360.js <shots.json> <outDir> [soloId]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const VILLA = 'https://villa-aurea-planta-baja-git-redisenar-experiencia-aurea6-ef7a.vercel.app/?hora=atardecer&perfil=completo#ext_aire';
const SERRA = 'https://serraresidencial.netlify.app/showroom/index.html?vivienda=demo';
const NPM = path.resolve(__dirname, '../work/npmcdn/node_modules');

const HIDE_CSS = `
  *{cursor:none!important}
  .psv-navbar,.psv-loader-container,.psv-tooltip,.psv-marker,.psv-markers,.psv-virtual-tour-arrows,.psv-notification,.psv-overlay,.psv-panel{display:none!important}
`;
const VILLA_CSS = `body > *:not(#visor){visibility:hidden!important}
  #visor{position:fixed!important;inset:0!important;z-index:99999!important;visibility:visible!important}
  #visor *:not(.sr-stage):not(.sr-stage *){visibility:hidden!important}`;
const SERRA_CSS = `#showroom *:not(.psv-container):not(.psv-container *){visibility:hidden!important}
  .psv-container, .psv-container canvas{visibility:visible!important}`;

const ease = (t) => 0.5 - 0.5 * Math.cos(Math.PI * t); // ease-in-out, como un arrastre de dedo
const lerp = (a, b, t) => a + (b - a) * t;
const rad = (d) => (d * Math.PI) / 180;

async function openSite(browser, site) {
  const ctx = await browser.newContext({ viewport: { width: 1080, height: 1920 }, screen: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => console.log('PAGEERR', e.message.slice(0, 160)));
  if (site === 'serra') {
    // jsdelivr no está permitido en este entorno: se sirven las mismas versiones desde npm
    await page.route('https://cdn.jsdelivr.net/npm/**', (route) => {
      const u = new URL(route.request().url());
      let rel = decodeURIComponent(u.pathname.replace('/npm/', '')); // three@0.185.1/build/three.module.js
      const m = rel.match(/^(@[^/]+\/[^@/]+|[^@/]+)@[^/]+\/(.*)$/);
      const file = path.join(NPM, m[1], m[2]);
      if (!fs.existsSync(file)) { console.log('MISSING', file); return route.fulfill({ status: 404, body: '' }); }
      const ct = file.endsWith('.css') ? 'text/css' : 'application/javascript';
      route.fulfill({ status: 200, contentType: ct, body: fs.readFileSync(file), headers: { 'access-control-allow-origin': '*' } });
    });
    await page.route('https://fonts.googleapis.com/**', (r) => r.fulfill({ status: 200, contentType: 'text/css', body: '' }));
    await page.goto(SERRA, { waitUntil: 'load', timeout: 120000 });
    await page.waitForFunction(() => window.showroom && window.showroom.viewer, null, { timeout: 120000 });
    await page.addStyleTag({ content: HIDE_CSS + SERRA_CSS });
  } else {
    await page.goto(VILLA, { waitUntil: 'load', timeout: 120000 });
    await page.waitForFunction(() => window.__showroom && window.__showroom.viewer, null, { timeout: 180000 });
    await page.addStyleTag({ content: HIDE_CSS + VILLA_CSS });
  }
  await page.waitForTimeout(3000);
  // sin autorrotación ni interferencias
  await page.evaluate(() => {
    const s = window.__showroom || window.showroom;
    const a = s.auto || s.autorotate;
    if (a) { try { a.stop(); } catch (e) {} a.start = () => {}; }
    window.__v = s.viewer;
  });
  return { ctx, page };
}

async function goStation(page, site, shot) {
  if (site === 'villa') {
    await page.evaluate(([st, h]) => window.__showroom.ir(st, h), [shot.station, shot.hora || 'atardecer']);
  } else {
    await page.evaluate((st) => window.showroom.tour.setCurrentNode(st), shot.station);
  }
  // espera a que esté cargada la textura buena y termine el fundido
  await page.waitForFunction((file) => String(window.__v.config.panorama).includes(file), shot.file, { timeout: 120000 });
  await page.waitForTimeout(4000);
  await page.evaluate(() => { const s = window.__showroom || window.showroom; const a = s.auto || s.autorotate; try { a && a.stop(); } catch (e) {} try { window.__v.stopAll(); } catch (e) {} });
}

(async () => {
  const shots = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const outDir = process.argv[3];
  const only = process.argv[4];
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--hide-scrollbars'] });
  const sites = {};
  for (const shot of shots) {
    if (only && shot.id !== only) continue;
    if (!sites[shot.site]) sites[shot.site] = await openSite(browser, shot.site);
    const { page } = sites[shot.site];
    await goStation(page, shot.site, shot);
    const dir = path.join(outDir, shot.id);
    fs.mkdirSync(dir, { recursive: true });
    const n = Math.round(shot.dur * shot.fps);
    const t0 = Date.now();
    for (let i = 0; i < n; i++) {
      const t = ease(i / (n - 1));
      const pos = { yaw: rad(lerp(shot.yaw[0], shot.yaw[1], t)), pitch: rad(lerp(shot.pitch[0], shot.pitch[1], t)) };
      const z = lerp(shot.zoom[0], shot.zoom[1], t);
      await page.evaluate(([p, z]) => new Promise((res) => {
        if (window.__v.state.animation) { try { window.__v.stopAnimation(); } catch (e) {} } window.__v.rotate(p); window.__v.zoom(z); window.__v.needsUpdate && window.__v.needsUpdate();
        requestAnimationFrame(() => requestAnimationFrame(() => res()));
      }), [pos, z]);
      await page.screenshot({ path: path.join(dir, `f_${String(i).padStart(4, '0')}.png`) });
    }
    console.log(`${shot.id}: ${n} frames en ${((Date.now() - t0) / 1000).toFixed(0)} s`);
  }
  await browser.close();
})();
