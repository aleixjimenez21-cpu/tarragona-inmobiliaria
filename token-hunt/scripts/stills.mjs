// Renderiza fotogramas de prueba (mismo motor que `npx remotion still`, pero con un
// solo bundle y un solo navegador) y monta una hoja de contactos para revisarlos.
// Uso: node scripts/stills.mjs <frame> <frame> ...   -> out/stills/fNNN.png + out/stills/sheet.jpg
import { bundle } from '@remotion/bundler';
import { renderStill, selectComposition, openBrowser } from '@remotion/renderer';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const frames = process.argv.slice(2).map(Number);
const outDir = path.join(root, 'out/stills');
fs.mkdirSync(outDir, { recursive: true });
const shell = process.env.REMOTION_CHROME ?? '/opt/pw-browsers/chromium';
const browserExecutable = fs.existsSync(shell) ? shell : null;

const serveUrl = await bundle({ entryPoint: path.join(root, 'src/index.ts'), publicDir: path.join(root, 'public') });
const browser = await openBrowser('chrome', { browserExecutable });
const composition = await selectComposition({ serveUrl, id: 'TokenHunt', puppeteerInstance: browser, browserExecutable });
const files = [];
for (const frame of frames) {
  const output = path.join(outDir, `f${String(frame).padStart(3, '0')}.png`);
  await renderStill({ composition, serveUrl, frame, output, puppeteerInstance: browser, browserExecutable, scale: 0.5 });
  files.push(output);
}
await browser.close({ silent: true });
const cols = Math.min(6, files.length);
const args = ['-y', '-loglevel', 'error'];
files.forEach((f) => args.push('-i', f));
const labels = files
  .map((f, i) => `[${i}:v]drawtext=text='${frames[i]}':x=10:y=10:fontsize=36:fontcolor=red:box=1:boxcolor=white@0.8[v${i}]`)
  .join(';');
const pads = files.length % cols ? cols - (files.length % cols) : 0;
let filter = labels + ';';
let inputs = files.map((_, i) => `[v${i}]`).join('');
for (let p = 0; p < pads; p++) {
  filter += `color=c=gray:s=540x960:d=1[pad${p}];`;
  inputs += `[pad${p}]`;
}
filter += `${inputs}xstack=inputs=${files.length + pads}:layout=${Array.from({ length: files.length + pads }, (_, i) => {
  const c = i % cols, r = Math.floor(i / cols);
  return `${c ? Array.from({ length: c }, () => 'w0').join('+') : '0'}_${r ? Array.from({ length: r }, () => 'h0').join('+') : '0'}`;
}).join('|')}`;
if (files.length > 1) {
  execFileSync('ffmpeg', [...args, '-filter_complex', filter, '-frames:v', '1', '-q:v', '3', path.join(outDir, 'sheet.jpg')]);
  console.log('sheet -> out/stills/sheet.jpg');
}
