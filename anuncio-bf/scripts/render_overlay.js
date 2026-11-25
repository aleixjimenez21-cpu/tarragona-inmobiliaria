// Renderiza overlay.html fotograma a fotograma con fondo transparente.
// Uso: node render_overlay.js <plan.json> <9x16|4x5> <outDir> [t1,t2,... para pruebas]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const plan = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const fmt = process.argv[3], out = process.argv[4];
  const only = process.argv[5] ? process.argv[5].split(',').map(Number) : null;
  const H = fmt === '4x5' ? 1350 : 1920;
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: H }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.resolve(__dirname, 'overlay.html'));
  await p.evaluate(([pl, f]) => window.setup(pl, f), [plan, fmt]);
  await p.waitForFunction(() => window.__ready === true);
  const n = Math.round(plan.total * plan.fps);
  const frames = only ? only.map(t => Math.round(t * plan.fps)) : [...Array(n).keys()];
  for (const i of frames) {
    await p.evaluate((t) => window.render(t), i / plan.fps);
    await p.screenshot({ path: path.join(out, `o_${String(i).padStart(4, '0')}.png`), omitBackground: true });
  }
  await b.close();
  console.log('overlay', fmt, frames.length, 'frames');
})();
