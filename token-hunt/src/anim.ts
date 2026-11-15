import { Easing, interpolate, random, spring } from 'remotion';

const clamp = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;

/** Muelle estándar de entrada (rápido, con un pelín de rebote). */
export const springAt = (frame: number, at: number, fps: number, config?: Partial<{ damping: number; stiffness: number; mass: number }>) =>
  spring({ frame: frame - at, fps, config: { damping: 13, stiffness: 190, mass: 0.6, ...config } });

/** Entrada escala + desenfoque → nítido. Devuelve estilos CSS. */
export const popIn = (
  frame: number,
  at: number,
  fps: number,
  opts: { from?: number; blur?: number; y?: number; config?: Parameters<typeof springAt>[3] } = {}
): React.CSSProperties => {
  const { from = 1.45, blur = 26, y = 0 } = opts;
  if (frame < at) return { opacity: 0 };
  const s = springAt(frame, at, fps, opts.config);
  const b = interpolate(s, [0, 1], [blur, 0], clamp);
  return {
    opacity: interpolate(frame - at, [0, 2], [0, 1], clamp),
    transform: `translateY(${interpolate(s, [0, 1], [y, 0])}px) scale(${interpolate(s, [0, 1], [from, 1])})`,
    filter: b > 0.3 ? `blur(${b.toFixed(2)}px)` : undefined,
  };
};

/** Contador con easing (cuenta en vez de saltar). */
export const countUp = (frame: number, at: number, dur: number, from: number, to: number) =>
  Math.round(
    interpolate(frame, [at, at + dur], [from, to], { ...clamp, easing: Easing.out(Easing.cubic) })
  );

/** Encadena varios tramos de contador: [[frame, valor], ...]. */
export const countSteps = (frame: number, steps: [number, number][], dur = 9) => {
  let v = steps[0][1];
  for (let i = 1; i < steps.length; i++) {
    if (frame >= steps[i][0]) v = countUp(frame, steps[i][0], dur, steps[i - 1][1], steps[i][1]);
  }
  return v;
};

export const fmt = (n: number) => n.toLocaleString('en-US');

/**
 * Zoom-punch (1.15 → 1 en 6 frames) + camera shake amortiguado en cada golpe.
 */
export const punch = (frame: number, hits: number[], shakeAmp = 1) => {
  let scale = 1, x = 0, y = 0, rot = 0;
  for (const h of hits) {
    const p = frame - h;
    if (p < 0 || p > 12) continue;
    scale *= interpolate(p, [0, 6], [1.15, 1], { ...clamp, easing: Easing.out(Easing.quad) });
    const a = interpolate(p, [0, 10], [22 * shakeAmp, 0], clamp);
    x += (random(`sx${h}-${p}`) - 0.5) * 2 * a;
    y += (random(`sy${h}-${p}`) - 0.5) * 2 * a;
    rot += (random(`sr${h}-${p}`) - 0.5) * 1.2 * (a / 22);
  }
  return { scale, x, y, rot, transform: `translate(${x}px, ${y}px) rotate(${rot}deg) scale(${scale})` };
};

/** Rebote de "squash & stretch" tras un cambio (para el cofre). */
export const bounce = (frame: number, at: number, fps: number) => {
  if (frame < at) return { sx: 1, sy: 1, y: 0 };
  const s = spring({ frame: frame - at, fps, config: { damping: 7, stiffness: 260, mass: 0.5 } });
  const k = 1 - s; // 1 → 0 con oscilación
  return { sx: 1 + 0.16 * k, sy: 1 - 0.18 * k, y: -60 * Math.sin(Math.min(1, (frame - at) / 7) * Math.PI) * (1 - s * 0.5) };
};

export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export { clamp };
