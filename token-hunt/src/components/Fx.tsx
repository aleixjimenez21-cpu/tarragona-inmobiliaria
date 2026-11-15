import React from 'react';
import { AbsoluteFill, Img, interpolate, random, staticFile, useCurrentFrame } from 'remotion';
import { C, CX } from '../theme';
import type { Bg } from '../timeline';

export const Background: React.FC<{ bg: Bg }> = ({ bg }) =>
  bg === 'black' ? (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 80% 60% at ${CX}px 45%, #161616 0%, ${C.black} 70%)` }} />
  ) : (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 85% 65% at ${CX}px 46%, #F8F8F8 0%, ${C.gray} 48%, #C9C9C9 100%)` }} />
  );

export const Vignette: React.FC<{ strength?: number }> = ({ strength = 0.6 }) => (
  <AbsoluteFill
    style={{
      pointerEvents: 'none',
      background: `radial-gradient(ellipse 75% 62% at ${CX}px 48%, rgba(0,0,0,0) 55%, rgba(0,0,0,${strength}) 100%)`,
    }}
  />
);

/** Grano de película: 6 texturas de ruido rotando por frame, ~5 % de opacidad. */
export const Grain: React.FC<{ opacity?: number }> = ({ opacity = 0.05 }) => {
  const f = useCurrentFrame();
  const i = f % 6;
  const ox = Math.floor(random(`gx${f}`) * 40) - 20;
  const oy = Math.floor(random(`gy${f}`) * 40) - 20;
  return (
    <AbsoluteFill style={{ pointerEvents: 'none', opacity, overflow: 'hidden' }}>
      <Img
        src={staticFile(`grain/g${i}.jpg`)}
        style={{ position: 'absolute', left: -20 + ox, top: -20 + oy, width: 1120, height: 1960, imageRendering: 'pixelated' }}
      />
    </AbsoluteFill>
  );
};

/** Partículas doradas flotando (deterministas). */
export const Particles: React.FC<{
  count?: number;
  area?: { x: number; y: number; w: number; h: number };
  seed?: string;
  opacity?: number;
  speed?: number;
  t?: number;
}> = ({ count = 36, area = { x: 0, y: 0, w: 1080, h: 1920 }, seed = 'p', opacity = 1, speed = 1, t }) => {
  const cur = useCurrentFrame();
  const f = t ?? cur;
  return (
    <AbsoluteFill style={{ pointerEvents: 'none', opacity }}>
      {Array.from({ length: count }, (_, i) => {
        const r = (k: string) => random(`${seed}-${i}-${k}`);
        const size = 4 + r('s') * 10;
        const v = (0.6 + r('v') * 1.8) * speed;
        const y = area.y + area.h - (((r('y') * area.h + f * v) % area.h) + area.h) % area.h;
        const x = area.x + r('x') * area.w + Math.sin(f / (18 + r('w') * 20) + r('p') * 6) * 14;
        const tw = 0.35 + 0.65 * Math.abs(Math.sin(f / (8 + r('t') * 10) + r('q') * 6));
        const edge = interpolate(y, [area.y, area.y + 120, area.y + area.h - 120, area.y + area.h], [0, 1, 1, 0], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: size,
              height: size,
              borderRadius: '50%',
              opacity: tw * edge,
              background: 'radial-gradient(circle, #FFF4CC 0%, #FFC93C 45%, rgba(255,159,28,0) 72%)',
              boxShadow: `0 0 ${size * 1.6}px rgba(255,201,60,0.8)`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

/** God rays animados que salen de un punto. */
export const GodRays: React.FC<{ x: number; y: number; radius?: number; opacity?: number; color?: string; rays?: number; speed?: number; t?: number }> = ({
  x,
  y,
  radius = 1100,
  opacity = 0.5,
  color = '255,201,60',
  rays = 18,
  speed = 0.25,
  t,
}) => {
  const cur = useCurrentFrame();
  const f = t ?? cur;
  const step = 360 / rays;
  const stops = Array.from({ length: rays }, (_, i) => {
    const a = i * step;
    const w = step * (0.25 + 0.2 * random(`ray${i}`));
    return `rgba(${color},0) ${a}deg, rgba(${color},${0.55 + 0.45 * random(`rb${i}`)}) ${a + w / 2}deg, rgba(${color},0) ${a + w}deg`;
  }).join(', ');
  const pulse = 0.85 + 0.15 * Math.sin(f / 7);
  return (
    <div
      style={{
        position: 'absolute',
        left: x - radius,
        top: y - radius,
        width: radius * 2,
        height: radius * 2,
        opacity: opacity * pulse,
        mixBlendMode: 'screen',
        pointerEvents: 'none',
        WebkitMaskImage: 'radial-gradient(circle, rgba(0,0,0,1) 8%, rgba(0,0,0,0.5) 35%, rgba(0,0,0,0) 70%)',
        maskImage: 'radial-gradient(circle, rgba(0,0,0,1) 8%, rgba(0,0,0,0.5) 35%, rgba(0,0,0,0) 70%)',
      }}
    >
      <div
        style={{
          width: '100%',
          height: '100%',
          borderRadius: '50%',
          background: `conic-gradient(from ${f * speed}deg, ${stops})`,
          filter: 'blur(6px)',
        }}
      />
    </div>
  );
};

/** Foco de luz dorado desde arriba. */
export const Spotlight: React.FC<{ x: number; topW?: number; bottomW?: number; floorY: number; opacity?: number }> = ({
  x,
  topW = 180,
  bottomW = 760,
  floorY,
  opacity = 1,
}) => {
  const f = useCurrentFrame();
  const flick = 0.93 + 0.07 * Math.sin(f / 3.3) * Math.sin(f / 7.1);
  return (
    <AbsoluteFill style={{ opacity: opacity * flick, pointerEvents: 'none' }}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          clipPath: `polygon(${x - topW / 2}px -20px, ${x + topW / 2}px -20px, ${x + bottomW / 2}px ${floorY}px, ${x - bottomW / 2}px ${floorY}px)`,
          background: `linear-gradient(180deg, rgba(255,226,140,0.75) 0%, rgba(255,201,60,0.32) 45%, rgba(255,159,28,0.16) 100%)`,
          filter: 'blur(18px)',
          mixBlendMode: 'screen',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: x - bottomW * 0.62,
          top: floorY - 70,
          width: bottomW * 1.24,
          height: 140,
          borderRadius: '50%',
          background: 'radial-gradient(ellipse, rgba(255,215,110,0.85) 0%, rgba(255,180,50,0.35) 45%, rgba(255,159,28,0) 72%)',
          mixBlendMode: 'screen',
        }}
      />
    </AbsoluteFill>
  );
};

/** Onda expansiva: anillos que salen desde un punto. */
export const Shockwave: React.FC<{ x: number; y: number; at: number; color?: string; rings?: number; maxR?: number }> = ({
  x,
  y,
  at,
  color = C.red,
  rings = 3,
  maxR = 1300,
}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      {Array.from({ length: rings }, (_, i) => {
        const p = f - at - i * 4;
        if (p < 0) return null;
        const t = interpolate(p, [0, 22], [0, 1], { extrapolateRight: 'clamp' });
        const r = 60 + (maxR - 60) * (1 - Math.pow(1 - t, 3));
        const op = (1 - t) * (i === 0 ? 1 : 0.6);
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x - r,
              top: y - r,
              width: r * 2,
              height: r * 2,
              borderRadius: '50%',
              border: `${Math.max(2, 34 * (1 - t))}px solid ${i === 1 ? '#fff' : color}`,
              opacity: op,
              boxShadow: `0 0 40px ${color}, inset 0 0 40px ${color}`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

/** Nube de polvo + polillas: el cofre está VACÍO. Coordenadas absolutas, `at` relativo. */
export const EmptyPuff: React.FC<{ x: number; y: number; at: number; scale?: number; moths?: number; seed?: string }> = ({ x, y, at, scale = 1, moths = 2, seed = 'puff' }) => {
  const f = useCurrentFrame();
  const p = f - at;
  if (p < 0 || p > 40) return null;
  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      {Array.from({ length: 16 }, (_, i) => {
        const r = (k: string) => random(`${seed}${at}-${i}-${k}`);
        const ang = -Math.PI / 2 + (r('a') - 0.5) * 2.2;
        const sp = (6 + r('s') * 10) * scale;
        const t = p;
        const px = x + Math.cos(ang) * sp * t * 0.9;
        const py = y + Math.sin(ang) * sp * t * 0.9 + 0.08 * t * t * scale;
        const sz = (30 + r('z') * 50) * scale * (1 + t / 20);
        const op = interpolate(t, [0, 4, 28], [0, 0.55, 0], { extrapolateRight: 'clamp' });
        return <div key={i} style={{ position: 'absolute', left: px - sz / 2, top: py - sz / 2, width: sz, height: sz, borderRadius: '50%', background: 'radial-gradient(circle, rgba(170,160,150,0.9) 0%, rgba(150,140,130,0) 70%)', opacity: op, filter: 'blur(4px)' }} />;
      })}
      {Array.from({ length: moths }, (_, i) => {
        const r = (k: string) => random(`${seed}m${at}-${i}-${k}`);
        const dir = i % 2 === 0 ? 1 : -1;
        const mx = x + dir * (p * (5 + r('v') * 4) + Math.sin(p / 2 + i) * 18) * scale;
        const my = y - p * (9 + r('u') * 5) * scale + Math.sin(p / 1.5) * 10;
        const flap = Math.abs(Math.sin(p * 1.4 + i));
        const s = 26 * scale;
        return (
          <svg key={`m${i}`} width={s * 2} height={s * 2} viewBox="-20 -20 40 40" style={{ position: 'absolute', left: mx - s, top: my - s, opacity: interpolate(p, [0, 3, 34, 40], [0, 1, 1, 0]) }}>
            <path d={`M0 0 Q-10 ${-14 * flap} -18 ${-4 * flap} Q-10 4 0 2 Q10 4 18 ${-4 * flap} Q10 ${-14 * flap} 0 0Z`} fill="#8A8178" />
            <ellipse cx="0" cy="1" rx="2.5" ry="6" fill="#5E574F" />
          </svg>
        );
      })}
    </AbsoluteFill>
  );
};

/** Destello de luz cálida (light leak) que barre la pantalla. `at` relativo. */
export const LightLeak: React.FC<{ at: number; dur?: number; from?: 'left' | 'right'; strength?: number }> = ({ at, dur = 14, from = 'left', strength = 0.7 }) => {
  const f = useCurrentFrame();
  const p = (f - at) / dur;
  if (p < 0 || p > 1) return null;
  const x = from === 'left' ? -500 + p * 2100 : 1600 - p * 2100;
  const op = Math.sin(p * Math.PI) * strength;
  return (
    <AbsoluteFill style={{ pointerEvents: 'none', mixBlendMode: 'screen', opacity: op }}>
      <div style={{ position: 'absolute', left: x - 600, top: -200, width: 1200, height: 2300, background: 'radial-gradient(ellipse 45% 55% at 50% 40%, rgba(255,214,120,0.95) 0%, rgba(255,140,40,0.55) 40%, rgba(225,60,0,0) 75%)', filter: 'blur(30px)', transform: 'rotate(12deg)' }} />
    </AbsoluteFill>
  );
};

/** Grietas en la pantalla desde un punto de impacto. `at` relativo. */
export const Cracks: React.FC<{ x: number; y: number; at: number; color?: string; seed?: string }> = ({ x, y, at, color = '#ffffff', seed = 'crack' }) => {
  const f = useCurrentFrame();
  const p = f - at;
  if (p < 0) return null;
  const grow = interpolate(p, [0, 4], [0, 1], { extrapolateRight: 'clamp' });
  const fade = interpolate(p, [10, 30], [1, 0.45], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const branches = 11;
  const paths: string[] = [];
  for (let b = 0; b < branches; b++) {
    let ang = (b / branches) * Math.PI * 2 + random(`${seed}a${b}`) * 0.5;
    let px = x, py = y;
    let d = `M${px} ${py}`;
    const segs = 6 + Math.floor(random(`${seed}n${b}`) * 4);
    for (let s = 0; s < segs; s++) {
      const len = 60 + random(`${seed}l${b}-${s}`) * 120;
      ang += (random(`${seed}t${b}-${s}`) - 0.5) * 0.9;
      px += Math.cos(ang) * len;
      py += Math.sin(ang) * len;
      d += ` L${px.toFixed(1)} ${py.toFixed(1)}`;
      if (s === 2 && random(`${seed}f${b}`) > 0.4) {
        const a2 = ang + (random(`${seed}g${b}`) > 0.5 ? 0.8 : -0.8);
        d += ` M${px.toFixed(1)} ${py.toFixed(1)} L${(px + Math.cos(a2) * 160).toFixed(1)} ${(py + Math.sin(a2) * 160).toFixed(1)} M${px.toFixed(1)} ${py.toFixed(1)}`;
      }
    }
    paths.push(d);
  }
  return (
    <svg width="1080" height="1920" style={{ position: 'absolute', inset: 0, pointerEvents: 'none', opacity: fade, filter: `drop-shadow(0 0 6px ${color})` }}>
      {paths.map((d, i) => (
        <path key={i} d={d} fill="none" stroke={color} strokeWidth={i % 3 === 0 ? 5 : 3} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - grow} />
      ))}
      <circle cx={x} cy={y} r={40 * grow} fill="none" stroke={color} strokeWidth="4" />
    </svg>
  );
};
