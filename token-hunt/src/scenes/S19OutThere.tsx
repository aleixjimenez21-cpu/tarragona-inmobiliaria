import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { springAt } from '../anim';
import { Coin } from '../components/Coin';
import { GodRays, Particles } from '../components/Fx';
import { Stack, Txt } from '../components/Txt';
import { CX } from '../theme';
import { rel, BEATS, sceneById } from '../timeline';

// 24,0–26,0 · Moneda grande con rayos y anillo de pulso, "IT'S OUT THERE."
export const S19OutThere: React.FC = () => {
  const c = rel('outThere');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const start = sceneById('outThere').start;
  const s = springAt(f, c.coin, fps, { damping: 11 });
  const cy = 790;
  const beats = BEATS.map((b) => b - start).filter((b) => b >= 0 && b <= f);
  return (
    <>
      <GodRays x={CX} y={cy} radius={1150} opacity={0.75 * s} speed={0.6} />
      <Particles count={40} seed="out" opacity={s} speed={1.4} />
      {beats.slice(-2).map((b) => {
        const t = interpolate(f - b, [0, 20], [0, 1], { extrapolateRight: 'clamp' });
        const r = 270 + 330 * t;
        return (
          <div
            key={b}
            style={{
              position: 'absolute',
              left: CX - r,
              top: cy - r,
              width: r * 2,
              height: r * 2,
              borderRadius: '50%',
              border: `${10 * (1 - t) + 2}px solid rgba(255,201,60,${0.9 * (1 - t)})`,
              boxShadow: `0 0 40px rgba(255,201,60,${0.6 * (1 - t)})`,
            }}
          />
        );
      })}
      <div style={{ position: 'absolute', left: CX - 260, top: cy - 260, transform: `scale(${interpolate(s, [0, 1], [0.3, 1])})` }}>
        <Coin size={520} glow={1.5} spin />
      </div>
      <Stack top={1230} style={{ height: 400 }}>
        <Txt at={c.its} size={170}>IT'S</Txt>
        <Txt at={c.out} size={210} spacing={2}>OUT THERE.</Txt>
      </Stack>
    </>
  );
};
