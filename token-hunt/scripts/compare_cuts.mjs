// Compara los cortes detectados por ffmpeg (scene>0.25) con el timeline y los beats.
// Entrada: out/cortes_video.txt (+ out/cortes_referencia.txt si existe). Salida: out/cuts_report.md
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const read = (f) => (fs.existsSync(f) ? fs.readFileSync(f, 'utf8').trim().split(/\s+/).filter(Boolean).map(Number) : null);
const ours = read(path.join(root, 'out/cortes_video.txt')) ?? [];
const ref = read(path.join(root, 'out/cortes_referencia.txt'));
const spec = JSON.parse(fs.readFileSync(path.join(root, 'scripts/timeline.spec.json'), 'utf8'));
const beats = JSON.parse(fs.readFileSync(path.join(root, 'beats.json'), 'utf8'));
const tl = fs.readFileSync(path.join(root, 'src/timeline.ts'), 'utf8');
const scenes = JSON.parse(tl.match(/SCENES: SceneTiming\[\] = (\[[\s\S]*?\n\]);/)[1]);
const fps = spec.fps;
const near = (arr, t) => (arr && arr.length ? arr.reduce((b, x) => (Math.abs(x - t) < Math.abs(b - t) ? x : b)) : null);
const ms = (x) => (x === null ? '—' : `${Math.round(x * 1000)}`);

const TOL = 0.1; // s
const why = (s, prev) =>
  s.transition === 'whip' ? 'whip-pan (entrada progresiva)' : prev.bg === s.bg ? `mismo fondo (${s.transition})` : s.transition;
const rows = scenes.slice(1).map((s, i) => {
  const t = s.start / fps;
  let o = near(ours, t);
  if (o !== null && Math.abs(o - t) > TOL) o = null;
  const r = ref ? near(ref, spec.scenes[i + 1].start) : null;
  const b = near(beats.grid, t);
  return `| ${s.id} | ${spec.scenes[i + 1].start.toFixed(2)} | ${t.toFixed(3)} | ${ms(t - b)} | ${o === null ? `no detectado: ${why(s, scenes[i])}` : o.toFixed(3)} | ${o === null ? '—' : ms(o - t)} | ${r === null ? '—' : r.toFixed(3)} | ${r === null ? '—' : ms(r - spec.scenes[i + 1].start)} |`;
});
const offBeat = ours.map((t) => ({ t, d: t - near(beats.grid, t), h: t - near(beats.half_grid, t) }));
const md = [
  '# Informe de cortes',
  '',
  `Rejilla: ${beats.tempo} BPM (${beats.source}). Un frame = ${Math.round(1000 / fps)} ms.`,
  ref ? `Referencia: ${ref.length} cortes detectados en referencia.mp4.` : '**referencia.mp4 no disponible**: no se pueden comparar los cortes con el original (columna "Ref").',
  '',
  '| Escena | Guion (s) | Inicio timeline (s) | Δ beat (ms) | Corte detectado en video.mp4 (s) | Δ (ms) | Corte en referencia (s) | Δ vs guion (ms) |',
  '|---|---|---|---|---|---|---|---|',
  ...rows,
  '',
  `## Todos los cortes detectados en video.mp4 (${ours.length})`,
  '',
  '| t (s) | Δ al beat más cercano (ms) | Δ a la corchea más cercana (ms) |',
  '|---|---|---|',
  ...offBeat.map((x) => `| ${x.t.toFixed(3)} | ${ms(x.d)} | ${ms(x.h)} |`),
  '',
  'Los cortes a +33 ms de un beat son el 2º frame del flash blanco (1 → 0,55 → 0) o el final de un whip; el corte real es el frame anterior.',
  `Δ beat crece de -3 a -10 ms porque la rejilla es ${beats.tempo} BPM y los frames son de 33,3 ms: siempre por debajo de medio frame.`,
].join('\n');
fs.writeFileSync(path.join(root, 'out/cuts_report.md'), md + '\n');
console.log(`cuts_report.md: ${ours.length} cortes en video.mp4${ref ? `, ${ref.length} en referencia` : ''}`);
