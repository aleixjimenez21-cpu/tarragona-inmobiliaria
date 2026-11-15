import React from 'react';
import { Easing, interpolate, interpolateColors, useCurrentFrame, useVideoConfig } from 'remotion';
import { springAt } from '../anim';
import { Kinetic } from '../components/Kinetic';
import { Odometer } from '../components/Odometer';
import { Stack } from '../components/Txt';
import { C, CX, glowFor } from '../theme';
import { rel } from '../timeline';

// 13,0–14,5 · Las probabilidades ruedan como un cuentakilómetros: suben a 8 / 895,136 y caen a 1 / 137,500
export const S10Odds: React.FC = () => {
  const c = rel('odds');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const e = { easing: Easing.inOut(Easing.cubic), extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;
  const val = (fr: number, a: number, b: number, end: number) => (fr < c.roll ? interpolate(fr, [c.a, c.roll - 1], [0, a], e) : interpolate(fr, [c.roll, c.b], [a, b], e)) || end;
  const num = val(f, 8, 1, 0);
  const den = val(f, 895136, 137500, 0);
  const vNum = Math.abs(val(f + 1, 8, 1, 0) - num);
  const vDen = Math.abs(val(f + 1, 895136, 137500, 0) - den);
  const col = interpolateColors(f, [c.b, c.b + 3], [C.white, C.gold]);
  const bar = springAt(f, c.a, fps, { damping: 20 });
  const ring = interpolate(f, [c.b, c.b + 18], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <>
      {f >= c.b ? (
        <div style={{ position: 'absolute', left: CX - 200 - 500 * ring, top: 700 - 200 - 500 * ring, width: 400 + 1000 * ring, height: 400 + 1000 * ring, borderRadius: '50%', border: `${8 * (1 - ring) + 1}px solid ${C.gold}`, opacity: 1 - ring, boxShadow: `0 0 40px ${C.gold}` }} />
      ) : null}
      <Stack gap={10}>
        <Kinetic text="THE ODDS" at={c.label} size={44} font="mont" spacing={24} color="#BDBDBD" glow={0.4} mode="flip" stagger={0.6} style={{ marginBottom: 40, marginRight: -24 }} />
        <Odometer value={Math.max(0, num)} size={430} color={col} velocity={vNum * 3} style={{ textShadow: glowFor(col) }} />
        <div style={{ width: 620 * bar, height: 12, borderRadius: 6, background: C.white, boxShadow: glowFor(C.white), margin: '0 0 36px' }} />
        <Odometer value={Math.max(0, den)} size={250} separator velocity={vDen} />
      </Stack>
    </>
  );
};
