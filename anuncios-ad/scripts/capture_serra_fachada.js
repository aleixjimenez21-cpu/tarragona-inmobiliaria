// Graba en tiempo real (Xvfb + ffmpeg x11grab) la fachada interactiva de Serra: se elige una planta
// y se despliegan sus viviendas. El cursor y los menús se ocultan.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const out = process.argv[2] || 'clips/s03_fachada_raw.mp4';
(async () => {
  const b = await chromium.launch({ headless: false, args: ['--window-position=0,0', '--window-size=1080,2100', '--disable-features=Translate,TranslateUI', '--lang=es-ES', '--hide-scrollbars', '--disable-infobars', '--force-device-scale-factor=1'] });
  const ctx = await b.newContext({ viewport: null });
  const p = await ctx.newPage();
  await p.goto('https://serraresidencial.netlify.app/index.html?vista=edificio', { waitUntil: 'load' });
  await p.waitForTimeout(5000);
  for (const sel of ['#tutorial-skip', 'text=SALTAR VISITA', 'text=Saltar']) { try { await p.click(sel, { timeout: 1500 }); } catch (e) {} }
  await p.waitForTimeout(1500);
  await p.addStyleTag({ content: `*{cursor:none!important}
    .top-action-btn,#top-contact-btn,.sidebar-toggle,[class*=sidebar],#help-btn,.help-btn,#explore-hint,.explore-hint,.zoom-controls,[class*=zoom-btn],[class*=zoom-control],#ai-widget-btn,.ai-widget-btn,[class*=tutorial],[class*=onboarding],.floor-selector,#floor-selector,[class*=controls]{display:none!important}` });
  await p.waitForTimeout(800);
  const win = await p.evaluate(() => [window.innerWidth, window.innerHeight, window.outerHeight - window.innerHeight]);
  console.log('window', win);
  const top = win[2];
  const ff = spawn('ffmpeg', ['-y', '-f', 'x11grab', '-draw_mouse', '0', '-framerate', '30', '-video_size', '1080x1920', '-i', process.env.DISPLAY + '+0,' + top, '-t', '7.5', '-c:v', 'libx264', '-crf', '12', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', out], { stdio: ['ignore', 'ignore', 'pipe'] });
  let err = ''; ff.stderr.on('data', d => err += d);
  await p.waitForTimeout(1200);
  // movimiento de dedo/ratón lento hasta la planta 2 y clic
  await p.mouse.move(300, 1500);
  const steps = 40;
  for (let i = 0; i <= steps; i++) { const t = i / steps, e = 0.5 - 0.5 * Math.cos(Math.PI * t); await p.mouse.move(300 + (560 - 300) * e, 1500 + (840 - 1500) * e); await p.waitForTimeout(20); }
  await p.waitForTimeout(400);
  await p.mouse.click(560, 840);
  await p.waitForTimeout(2600);
  // pasa por encima de una vivienda y la selecciona
  for (let i = 0; i <= 30; i++) { const t = i / 30, e = 0.5 - 0.5 * Math.cos(Math.PI * t); await p.mouse.move(560 + (380 - 560) * e, 840); await p.waitForTimeout(20); }
  await p.waitForTimeout(500);
  await p.mouse.click(380, 840);
  await new Promise(r => ff.on('close', r));
  console.log(err.split('\n').filter(l => /frame=|error/i.test(l)).slice(-2).join('\n'));
  await p.screenshot({ path: 'explore/sf_after.jpg', quality: 70 });
  await b.close();
})();
