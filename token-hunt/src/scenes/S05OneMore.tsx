import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { Particles } from '../components/Fx';
import { Kinetic } from '../components/Kinetic';
import { Stack } from '../components/Txt';
import { C, CX } from '../theme';
import { rel } from '../timeline';

// 5,0–6,0 · "ONE" / "MORE" / "CHEST." — CHEST. cae en dorado con eco y estalla en partículas
export const S05OneMore: React.FC = () => {
  const c = rel('oneMore');
  const f = useCurrentFrame();
  const glow = interpolate(f, [c.chest, c.chest + 4, c.chest + 14], [0, 1, 0.5], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <>
      <div style={{ position: 'absolute', inset: 0, background: `radial-gradient(circle at ${CX}px 1250px, rgba(255,201,60,${0.35 * glow}) 0%, rgba(0,0,0,0) 50%)` }} />
      <Particles count={30} seed="om" opacity={glow} speed={2} area={{ x: 100, y: 900, w: 760, h: 700 }} />
      <Stack>
        <Kinetic text="ONE" at={c.one} size={390} mode="drop" />
        <Kinetic text="MORE" at={c.more} size={390} mode="drop" stagger={1} />
        <Kinetic text="CHEST." at={c.chest} size={390} color={C.gold} mode="slam" stagger={0.8} echo glow={1.3} />
      </Stack>
    </>
  );
};
