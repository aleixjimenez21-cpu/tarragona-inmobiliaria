// Renderiza overlay.html fotograma a fotograma, en dos capas con fondo transparente:
//   o_XXXX.png = capa delantera (subtítulos, tarjetas, cuenta atrás)
//   b_XXXX.png = capa trasera (palabras que van DETRÁS de la cabeza; solo si hay contenido)
// y glass.json con los rectángulos de las tarjetas de cristal de cada fotograma (compose.py desenfoca el vídeo debajo).
// Uso: node render_overlay.js <plan.json> <9x16|4x5> <outDir> [t1,t2,... para pruebas]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const plan = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const fmt = process.argv[3], out = process.argv[4];
  const only = process.argv[5] ? process.argv[5].split(',').map(Number) : null;
  const H = fmt === '4x5' ? 1350 : 1920;
  const htFile = path.resolve(__dirname, `../work/head_tops_${fmt}.json`);
  const ht = fs.existsSync(htFile) ? JSON.parse(fs.readFileSync(htFile, 'utf8')) : {};
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: H }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.resolve(__dirname, 'overlay.html'));
  await p.evaluate(([pl, f, h]) => window.setup(pl, f, h), [plan, fmt, ht]);
  await p.waitForFunction(() => window.__ready === true);
  const n = Math.round(plan.total * plan.fps);
  const frames = only ? only.map(t => Math.round(t * plan.fps)) : [...Array(n).keys()];
  const glassFile = path.join(out, 'glass.json');
  const glass = fs.existsSync(glassFile) ? JSON.parse(fs.readFileSync(glassFile, 'utf8')) : {};
  for (const i of frames) {
    const t = i / plan.fps, id = String(i).padStart(4, '0');
    const hasBack = plan.behind.some(c => t >= c.t0 && t < c.t1);
    const bp = path.join(out, `b_${id}.png`);
    if (hasBack) {
      await p.evaluate((t) => window.render(t, 'back'), t);
      await p.screenshot({ path: bp, omitBackground: true });
    } else if (fs.existsSync(bp)) fs.unlinkSync(bp);
    glass[i] = await p.evaluate((t) => window.render(t, 'front'), t);
    await p.screenshot({ path: path.join(out, `o_${id}.png`), omitBackground: true });
  }
  fs.writeFileSync(glassFile, JSON.stringify(glass));
  await b.close();
  console.log('overlay', fmt, frames.length, 'frames');
})();
