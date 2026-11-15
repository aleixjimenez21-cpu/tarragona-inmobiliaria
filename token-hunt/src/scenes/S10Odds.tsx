import React from 'react';
import { interpolateColors, useCurrentFrame } from 'remotion';
import { countUp, fmt } from '../anim';
import { Stack, Txt } from '../components/Txt';
import { C, glowFor } from '../theme';
import { rel } from '../timeline';

// 13,0–14,5 · "8 / 895,136" → "1 / 137,500", con "THE ODDS" pequeño y espaciado
export const S10Odds: React.FC = () => {
  const c = rel('odds');
  const f = useCurrentFrame();
  const num = countUp(f, c.b - 6, 6, 8, 1);
  const den = countUp(f, c.b - 6, 8, 895136, 137500);
  const col = interpolateColors(f, [c.b, c.b + 4], [C.white, C.gold]);
  return (
    <Stack gap={10}>
      <Txt at={c.label} size={40} font="mont" spacing={22} color="#BDBDBD" glow={0.5} from={1.1} style={{ marginBottom: 40, marginRight: -22 }}>
        THE ODDS
      </Txt>
      <Txt at={c.a} size={420} color={col} style={{ fontVariantNumeric: 'tabular-nums', textShadow: glowFor(col) }}>
        {num}
      </Txt>
      <div style={{ width: 600, height: 12, borderRadius: 6, background: C.white, boxShadow: glowFor(C.white), margin: '0 0 36px' }} />
      <Txt at={c.a + 2} size={250} style={{ fontVariantNumeric: 'tabular-nums' }}>
        {fmt(den)}
      </Txt>
    </Stack>
  );
};
