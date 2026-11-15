import React, { useContext } from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { BEBAS, MONT } from '../fonts';
import { C, glowFor } from '../theme';
import { BgContext } from './Txt';

type Seg = [string, string?]; // [texto, color]
export type KineticMode = 'drop' | 'rise' | 'slam' | 'flip' | 'zoom';

/**
 * Tipografía cinética letra a letra: cada carácter entra con su propio muelle
 * (desfase en frames), desenfoque → nítido y, opcionalmente, ecos de contorno
 * que se expanden desde el golpe.
 */
export const Kinetic: React.FC<{
  text: string | Seg[];
  at: number;
  size: number;
  color?: string;
  font?: 'bebas' | 'mont';
  mode?: KineticMode;
  stagger?: number;
  spacing?: number;
  glow?: number;
  echo?: boolean | number; // nº de ecos
  lineHeight?: number;
  style?: React.CSSProperties;
}> = ({ text, at, size, color, font = 'bebas', mode = 'drop', stagger = 1.2, spacing = 0, glow, echo = false, lineHeight = 0.9, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const bg = useContext(BgContext);
  const base = color ?? (bg === 'black' ? C.white : C.ink);
  const g = glow ?? (bg === 'black' ? 1 : 0);
  const segs: Seg[] = typeof text === 'string' ? [[text]] : text;
  const chars: { ch: string; col: string }[] = [];
  segs.forEach(([t, c]) => [...t].forEach((ch) => chars.push({ ch, col: c ?? base })));
  const n = chars.length;
  const fontFamily = font === 'bebas' ? BEBAS : MONT;
  const fontWeight = font === 'mont' ? 900 : 400;

  const letters = (outline?: string) =>
    chars.map(({ ch, col }, i) => {
      const d = at + i * stagger;
      if (frame < d) return <span key={i} style={{ display: 'inline-block', opacity: 0, whiteSpace: 'pre' }}>{ch}</span>;
      const s = spring({ frame: frame - d, fps, config: mode === 'slam' ? { damping: 11, stiffness: 320, mass: 0.6 } : { damping: 13, stiffness: 200, mass: 0.55 } });
      const k = mode === 'slam' || mode === 'zoom' ? Math.max(-0.05, 1 - s) : 1 - s;
      const side = i % 2 === 0 ? 1 : -1;
      const tf =
        mode === 'drop'
          ? `translateY(${-k * size * 0.7}px) rotate(${k * 18 * side}deg) scale(${1 + k * 0.4})`
          : mode === 'rise'
            ? `translateY(${k * size * 0.6}px) scaleY(${1 + k * 0.6})`
            : mode === 'slam'
              ? `scale(${1 + k * 2.2}) translateY(${k * -20}px)`
              : mode === 'flip'
                ? `perspective(800px) rotateX(${k * 95}deg)`
                : `scale(${0.2 + 0.8 * s})`;
      const blur = interpolate(s, [0, 1], [mode === 'slam' ? 16 : 12, 0], { extrapolateRight: 'clamp' });
      return (
        <span
          key={i}
          style={{
            display: 'inline-block',
            whiteSpace: 'pre',
            transform: tf,
            transformOrigin: mode === 'flip' ? '50% 100%' : '50% 60%',
            opacity: interpolate(frame - d, [0, 2], [0, 1], { extrapolateRight: 'clamp' }),
            filter: !outline && blur > 0.4 ? `blur(${blur.toFixed(1)}px)` : undefined,
            color: outline ? 'transparent' : col,
            WebkitTextStroke: outline ? `${Math.max(2, size / 90)}px ${outline}` : undefined,
            textShadow: !outline && g > 0 ? glowFor(col, g) : undefined,
          }}
        >
          {ch}
        </span>
      );
    });

  const echoes = echo === true ? 3 : echo || 0;
  const done = at + (n - 1) * stagger; // la última letra llega aquí
  return (
    <div style={{ position: 'relative', fontFamily, fontWeight, fontSize: size, lineHeight, letterSpacing: spacing, whiteSpace: 'nowrap', textAlign: 'center', ...style }}>
      {Array.from({ length: echoes }, (_, e) => {
        const p = frame - (done + e * 2);
        if (p < 0) return null;
        const t = interpolate(p, [0, 16], [0, 1], { extrapolateRight: 'clamp' });
        return (
          <div key={e} style={{ position: 'absolute', inset: 0, transform: `scale(${1 + t * (0.18 + e * 0.1)})`, opacity: (1 - t) * (0.55 - e * 0.12), pointerEvents: 'none' }}>
            {letters(chars[0]?.col ?? base)}
          </div>
        );
      })}
      <div style={{ position: 'relative' }}>{letters()}</div>
    </div>
  );
};
