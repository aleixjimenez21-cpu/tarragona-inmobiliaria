import React from 'react';
import { AbsoluteFill, interpolate, random, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { punch } from '../anim';
import { CX, CY } from '../theme';
import type { Bg, SceneTiming } from '../timeline';
import { Background, Vignette } from './Fx';
import { useSvgId } from './ids';
import { BgContext } from './Txt';

/**
 * Envoltorio común de cada escena (frames RELATIVOS):
 * fondo + viñeta, zoom-punch/shake en los golpes, y transición de entrada
 * (cut seco, flash blanco de 2 frames, glitch RGB o whip-pan).
 */
export const SceneShell: React.FC<{
  scene: SceneTiming;
  prevBg?: Bg;
  shake?: number;
  vignette?: number;
  extraHits?: number[]; // relativos
  children: React.ReactNode;
}> = ({ scene, prevBg, shake = 1, vignette, extraHits = [], children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const id = useSvgId('fx');
  const hits = [...scene.hits.map((h) => h - scene.start), ...extraHits];
  const p = punch(frame, hits, shake);

  const inner = (
    <BgContext.Provider value={scene.bg}>
      <AbsoluteFill>
        <Background bg={scene.bg} />
        <AbsoluteFill style={{ transform: p.transform, transformOrigin: `${CX}px ${CY}px` }}>{children}</AbsoluteFill>
        <Vignette strength={vignette ?? (scene.bg === 'black' ? 0.7 : 0.38)} />
      </AbsoluteFill>
    </BgContext.Provider>
  );

  // ---------- glitch RGB (4 frames) ----------
  if (scene.transition === 'glitch' && frame < 4) {
    const k = (4 - frame) / 4;
    const d = 26 * k;
    const slices = 7;
    return (
      <AbsoluteFill>
        <svg width="0" height="0" style={{ position: 'absolute' }}>
          <filter id={id} x="-5%" y="0" width="110%" height="100%" colorInterpolationFilters="sRGB">
            <feColorMatrix in="SourceGraphic" type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="r" />
            <feOffset in="r" dx={d} dy="0" result="ro" />
            <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0" result="g" />
            <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0" result="b" />
            <feOffset in="b" dx={-d} dy="0" result="bo" />
            <feBlend in="ro" in2="g" mode="screen" result="rg" />
            <feBlend in="rg" in2="bo" mode="screen" />
          </filter>
        </svg>
        <AbsoluteFill style={{ filter: `url(#${id})` }}>
          {Array.from({ length: slices }, (_, i) => {
            const y0 = (1920 / slices) * i + (random(`gy${scene.id}${i}${frame}`) - 0.5) * 120;
            const y1 = y0 + 1920 / slices + 40;
            const dx = (random(`gx${scene.id}${i}${frame}`) - 0.5) * 160 * k;
            return (
              <AbsoluteFill key={i} style={{ clipPath: `inset(${Math.max(0, y0)}px 0 ${Math.max(0, 1920 - y1)}px 0)`, transform: `translateX(${dx}px)` }}>
                {inner}
              </AbsoluteFill>
            );
          })}
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }

  // ---------- whip-pan (6 frames) ----------
  if (scene.transition === 'whip' && frame < 6) {
    const s = spring({ frame, fps, config: { damping: 20, stiffness: 320, mass: 0.5 } });
    const x = interpolate(s, [0, 1], [1080, 0]);
    const blur = interpolate(frame, [0, 5], [70, 0], { extrapolateRight: 'clamp' });
    return (
      <AbsoluteFill>
        {prevBg ? <Background bg={prevBg} /> : null}
        <svg width="0" height="0" style={{ position: 'absolute' }}>
          <filter id={id} x="-20%" y="0" width="140%" height="100%">
            <feGaussianBlur stdDeviation={`${blur} 0`} />
          </filter>
        </svg>
        <AbsoluteFill style={{ transform: `translateX(${x}px)`, filter: blur > 0.5 ? `url(#${id})` : undefined }}>{inner}</AbsoluteFill>
      </AbsoluteFill>
    );
  }

  // ---------- flash blanco (2 frames) ----------
  return (
    <AbsoluteFill>
      {inner}
      {scene.transition === 'flash' && frame < 2 ? <AbsoluteFill style={{ background: '#fff', opacity: frame === 0 ? 1 : 0.55 }} /> : null}
    </AbsoluteFill>
  );
};
