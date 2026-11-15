// Genera src/timeline.ts a partir de scripts/timeline.spec.json + beats.json.
// Cada inicio de escena y cada cue se mueve al beat más cercano de la rejilla
// (o a la corchea más cercana si sub=true). Informe en out/timeline_report.md
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const spec = JSON.parse(fs.readFileSync(path.join(root, 'scripts/timeline.spec.json'), 'utf8'));
const beats = JSON.parse(fs.readFileSync(path.join(root, 'beats.json'), 'utf8'));
const fps = spec.fps;

const nearest = (arr, t) => arr.reduce((b, x) => (Math.abs(x - t) < Math.abs(b - t) ? x : b), arr[0]);
const snap = (t, sub) => (t === 0 ? 0 : nearest(sub ? beats.half_grid : beats.grid, t));
const toF = (t) => Math.round(t * fps);
// Fin del contenido: el beat más cercano a contentEnd, sin pasarse de la duración del audio
const contentEnd = Math.min(snap(spec.contentEnd, false), beats.duration);
const totalFrames = toF(contentEnd);

const rows = [];
const scenes = spec.scenes.map((s, i) => {
  const start = snap(s.start, false);
  const cues = {};
  const hits = [];
  for (const [name, raw] of Object.entries(s.cues)) {
    const c = typeof raw === 'number' ? { t: raw } : raw;
    const t = snap(c.t, !!c.sub);
    cues[name] = toF(t);
    if (c.hit) hits.push(toF(t));
    rows.push([s.id, name, c.t, t, toF(t), c.sub ? '1/8' : 'beat']);
  }
  return { id: s.id, bg: s.bg, transition: s.transition, startT: start, start: toF(start), cues, hits };
});
scenes.forEach((s, i) => {
  s.end = i + 1 < scenes.length ? scenes[i + 1].start : totalFrames;
  s.duration = s.end - s.start;
  rows.unshift([s.id, '(inicio)', spec.scenes[i].start, s.startT, s.start, 'beat']);
});

const beatFrames = beats.grid.filter((t) => t <= contentEnd).map(toF);
const out = `// ⚠️ ARCHIVO GENERADO por scripts/build_timeline.mjs — no editar a mano.
// Fuente de audio: ${beats.source} · ${beats.tempo} BPM · offset ${beats.grid_offset}s
export const FPS = ${fps};
export const WIDTH = 1080;
export const HEIGHT = 1920;
export const TOTAL_FRAMES = ${totalFrames};
export const BPM = ${beats.tempo};
export const BEAT_FRAMES = ${(beats.period * fps).toFixed(4)};
export const BEATS: number[] = ${JSON.stringify(beatFrames)};

export type Bg = 'black' | 'gray';
export type TransitionKind = 'cut' | 'flash' | 'glitch' | 'whip';
export interface SceneTiming {
  id: string;
  bg: Bg;
  transition: TransitionKind;
  /** frames absolutos */
  start: number;
  end: number;
  duration: number;
  /** cues en frames ABSOLUTOS */
  cues: Record<string, number>;
  /** golpes (zoom-punch + shake), frames absolutos */
  hits: number[];
}

export const SCENES: SceneTiming[] = ${JSON.stringify(
  scenes.map(({ startT, ...s }) => s),
  null,
  1
)};

export const sceneById = (id: string): SceneTiming => {
  const s = SCENES.find((x) => x.id === id);
  if (!s) throw new Error('Escena desconocida: ' + id);
  return s;
};
/** cues relativos al inicio de la escena (para usar dentro de <Sequence>) */
export const rel = (id: string): Record<string, number> => {
  const s = sceneById(id);
  return Object.fromEntries(Object.entries(s.cues).map(([k, v]) => [k, v - s.start]));
};
/** Energía de la música por frame (0..1): RMS total y graves. */
export const ENERGY: number[] = ${JSON.stringify((beats.energy ?? []).slice(0, totalFrames + 1))};
export const BASS: number[] = ${JSON.stringify((beats.bass ?? []).slice(0, totalFrames + 1))};
export const energyAt = (f: number) => ENERGY[Math.max(0, Math.min(ENERGY.length - 1, Math.round(f)))] ?? 0;
export const bassAt = (f: number) => BASS[Math.max(0, Math.min(BASS.length - 1, Math.round(f)))] ?? 0;
/** Pulso que decae tras cada beat (1 en el beat → 0). */
export const beatPulse = (f: number, decay = 4) => {
  let last = -999;
  for (const b of BEATS) { if (b <= f) last = b; else break; }
  return Math.exp(-(f - last) / decay);
};
export const ALL_HITS: number[] = SCENES.flatMap((s) => s.hits);
`;
fs.writeFileSync(path.join(root, 'src/timeline.ts'), out);

fs.mkdirSync(path.join(root, 'out'), { recursive: true });
const md = [
  `# Timeline ajustado a beats`,
  ``,
  `Audio: \`${beats.source}\` · ${beats.tempo} BPM · rejilla desde ${beats.grid_offset}s · ${fps} fps · total ${totalFrames} frames (${(totalFrames / fps).toFixed(3)} s)`,
  ``,
  `| Escena | Cue | Guion (s) | Beat (s) | Frame | Rejilla | Δ ms |`,
  `|---|---|---|---|---|---|---|`,
  ...rows
    .sort((a, b) => a[4] - b[4] || (a[1] === '(inicio)' ? -1 : 1))
    .map((r) => `| ${r[0]} | ${r[1]} | ${r[2].toFixed(3)} | ${r[3].toFixed(3)} | ${r[4]} | ${r[5]} | ${Math.round((r[3] - r[2]) * 1000)} |`),
].join('\n');
fs.writeFileSync(path.join(root, 'out/timeline_report.md'), md + '\n');
console.log(`timeline.ts: ${scenes.length} escenas, ${totalFrames} frames, ${beats.tempo} BPM`);
