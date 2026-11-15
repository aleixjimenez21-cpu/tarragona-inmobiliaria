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
