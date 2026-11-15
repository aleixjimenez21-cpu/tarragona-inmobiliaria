import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { springAt } from '../anim';
import { Coin } from '../components/Coin';
import { Particles } from '../components/Fx';
import { Stack, Txt } from '../components/Txt';
import { C, CX } from '../theme';
import { rel } from '../timeline';

// 17,0–18,0 · "I'LL" → "I'LL FIND IT" en rojo, moneda pequeña abajo
export const S14IllFind: React.FC = () => {
  const c = rel('illFind');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const coin = springAt(f, c.coin, fps);
  return (
    <>
      <Stack top={300} style={{ height: 760 }}>
        <Txt at={c.ill} size={340}>I'LL</Txt>
        <Txt at={c.find} size={340} color={C.red} from={1.9}>FIND IT</Txt>
      </Stack>
      <Particles count={14} area={{ x: CX - 200, y: 1150, w: 400, h: 450 }} seed="ill" opacity={coin} />
      <div style={{ position: 'absolute', left: CX - 85, top: 1280 + Math.sin(f / 8) * 10, transform: `scale(${coin})`, opacity: coin }}>
        <Coin size={170} glow={1.2} />
      </div>
    </>
  );
};
