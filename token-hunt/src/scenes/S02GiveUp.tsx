import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { Kinetic } from '../components/Kinetic';
import { Stack } from '../components/Txt';
import { BEBAS } from '../fonts';
import { C, CX } from '../theme';
import { rel } from '../timeline';

// 0,5–2,0 · "GIVE UP" letra a letra → la "?" cae como un mazazo; un "?" gigante respira al fondo
export const S02GiveUp: React.FC = () => {
  const c = rel('giveUp');
  const f = useCurrentFrame();
  const bgQ = interpolate(f, [c.q, c.q + 8], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <>
      <div style={{ position: 'absolute', left: CX - 700, top: 120, width: 1400, textAlign: 'center', fontFamily: BEBAS, fontSize: 1700, lineHeight: 1, color: 'transparent', WebkitTextStroke: '6px rgba(225,6,0,0.35)', opacity: bgQ, transform: `rotate(${-8 + f * 0.15}deg) scale(${1.25 - 0.25 * bgQ})` }}>
        ?
      </div>
      <Stack>
        <Kinetic text="GIVE" at={c.giveUp} size={430} mode="drop" />
        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
          <Kinetic text="UP" at={c.giveUp + 4} size={430} mode="drop" />
          <Kinetic text="?" at={c.q} size={430} color={C.red} mode="slam" echo />
        </div>
      </Stack>
    </>
  );
};
