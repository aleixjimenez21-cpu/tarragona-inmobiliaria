import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { Shockwave } from '../components/Fx';
import { Stack, Txt } from '../components/Txt';
import { C, CX, CY } from '../theme';
import { rel } from '../timeline';

// 16,0–17,0 · "NAH" rojo gigante con onda expansiva
export const S13Nah: React.FC = () => {
  const c = rel('nah');
  const f = useCurrentFrame();
  const glow = interpolate(f - c.nah, [0, 4, 30], [1, 0.8, 0.35], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <>
      <div style={{ position: 'absolute', inset: 0, background: `radial-gradient(circle at ${CX}px ${CY}px, rgba(225,6,0,${0.5 * glow}) 0%, rgba(225,6,0,0) 55%)` }} />
      <Shockwave x={CX} y={CY} at={c.nah} rings={3} />
      <Stack>
        <Txt at={c.nah} size={680} color={C.red} from={2.4} glow={1.6} style={{ letterSpacing: 6 }}>
          NAH
        </Txt>
      </Stack>
    </>
  );
};
