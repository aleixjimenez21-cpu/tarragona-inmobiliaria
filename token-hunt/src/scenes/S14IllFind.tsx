import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { springAt } from '../anim';
import { Coin3D } from '../components/Coin3D';
import { Particles } from '../components/Fx';
import { Kinetic } from '../components/Kinetic';
import { Stack } from '../components/Txt';
import { C, CX } from '../theme';
import { rel } from '../timeline';

// 17,0–18,0 · "I'LL" → "FIND IT" en rojo; abajo la moneda gira, esperando
export const S14IllFind: React.FC = () => {
  const c = rel('illFind');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const coin = springAt(f, c.coin, fps);
  return (
    <>
      <Stack top={300} style={{ height: 760 }}>
        <Kinetic text="I'LL" at={c.ill} size={340} mode="drop" />
        <Kinetic text="FIND IT" at={c.find} size={340} color={C.red} mode="slam" stagger={0.8} echo />
      </Stack>
      <Particles count={16} area={{ x: CX - 220, y: 1120, w: 440, h: 480 }} seed="ill" opacity={coin} />
      <div style={{ position: 'absolute', left: CX - 95, top: 1250 + Math.sin(f / 8) * 10, transform: `scale(${coin})`, opacity: coin }}>
        <Coin3D size={190} angle={f * 9} glow={1.3} />
      </div>
    </>
  );
};
