import React from 'react';
import { AbsoluteFill } from 'remotion';
import { CX } from '../theme';
import { Coin } from './Coin';
import { GodRays, Particles } from './Fx';
import { poses, Stickman } from './Stickman';

/** Primer plano del vídeo: la moneda brillando en lo alto de unas escaleras, monigote pequeño abajo.
 *  Se usa también al final para que el bucle de TikTok sea invisible. `t` = tiempo propio. */
export const COIN_INTRO = { x: CX, y: 770, size: 270 };
/** Zoom del primer frame (dentro de la estrella de la moneda) = zoom del último frame. */
export const LOOP_ZOOM = 3.4;
export const STEPS = Array.from({ length: 6 }, (_, i) => ({
  y: 1640 - (i + 1) * 118,
  h: 118,
  w: 790 - i * 122,
}));

export const Stairs2D: React.FC<{ opacity?: number }> = ({ opacity = 1 }) => (
  <svg width="1080" height="1920" style={{ position: 'absolute', inset: 0, opacity }}>
    <defs>
      <linearGradient id="stepTop" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#FFC93C" stopOpacity="0.9" />
        <stop offset="1" stopColor="#FFC93C" stopOpacity="0" />
      </linearGradient>
      <linearGradient id="stepFace" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#262019" />
        <stop offset="1" stopColor="#0E0E0E" />
      </linearGradient>
    </defs>
    {STEPS.map((s, i) => {
      const x = CX - s.w / 2;
      const lit = 0.35 + 0.65 * (i / (STEPS.length - 1));
      return (
        <g key={i}>
          <rect x={x} y={s.y} width={s.w} height={s.h} fill="url(#stepFace)" />
          <rect x={x} y={s.y} width={s.w} height={26} fill="url(#stepTop)" opacity={lit} />
          <rect x={x} y={s.y} width={s.w} height={4} fill="#FFE08A" opacity={lit} />
        </g>
      );
    })}
  </svg>
);

export const IntroArt: React.FC<{ t: number; zoom?: number }> = ({ t, zoom = 1 }) => (
  <AbsoluteFill style={{ transform: `scale(${zoom})`, transformOrigin: `${COIN_INTRO.x}px ${COIN_INTRO.y}px` }}>
    <GodRays x={COIN_INTRO.x} y={COIN_INTRO.y} radius={900} opacity={0.45} t={t} />
    <Particles count={26} area={{ x: 160, y: 300, w: 640, h: 1000 }} seed="intro" t={t} />
    <Stairs2D />
    <div style={{ position: 'absolute', left: COIN_INTRO.x - COIN_INTRO.size / 2, top: COIN_INTRO.y - COIN_INTRO.size / 2 + Math.sin(t / 12) * 8 }}>
      <Coin size={COIN_INTRO.size} glow={1.2} t={t} />
    </div>
    <Stickman pose={poses.standLookUp(t)} x={190} y={STEPS[0].y - 50} scale={0.5} rim="#FFC93C" />
  </AbsoluteFill>
);
