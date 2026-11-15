import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { countSteps } from '../anim';
import { Stack, Txt } from '../components/Txt';
import { C, glowFor } from '../theme';
import { rel } from '../timeline';

// 8,0–10,0 · DAY 1 / 40 CHESTS → DAY 2 / 95 → DAY 5 / 260 → DAY 12 / 731, "0 TOKENS" en rojo
export const S07Days: React.FC = () => {
  const c = rel('days');
  const f = useCurrentFrame();
  const cues = [c.d1, c.d2, c.d3, c.d4];
  const day = countSteps(f, [[c.d1 - 1, 0], [c.d1, 1], [c.d2, 2], [c.d3, 5], [c.d4, 12]], 7);
  const chests = countSteps(f, [[c.d1 - 1, 0], [c.d1, 40], [c.d2, 95], [c.d3, 260], [c.d4, 731]], 10);
  const last = [...cues].reverse().find((x) => f >= x) ?? c.d1;
  const kick = interpolate(f - last, [0, 6], [1.12, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const redPulse = 0.75 + 0.25 * Math.abs(Math.sin((f - c.d1) / 4.8));
  return (
    <Stack gap={10}>
      <Txt at={c.d1} size={130} spacing={14} color="#BDBDBD">DAY</Txt>
      <div style={{ transform: `scale(${kick})` }}>
        <Txt at={c.d1} size={400} style={{ fontVariantNumeric: 'tabular-nums' }}>{day}</Txt>
      </div>
      <Txt at={c.d1 + 2} size={150} spacing={3} style={{ marginTop: 20 }}>
        <span style={{ color: C.gold, textShadow: glowFor(C.gold), fontVariantNumeric: 'tabular-nums' }}>{chests}</span> CHESTS
      </Txt>
      <div style={{ height: 6, width: 520, background: '#2A2A2A', borderRadius: 3, margin: '40px 0 30px' }} />
      <div style={{ opacity: redPulse }}>
        <Txt at={c.d1 + 4} size={150} color={C.red} spacing={4}>0 TOKENS</Txt>
      </div>
    </Stack>
  );
};
