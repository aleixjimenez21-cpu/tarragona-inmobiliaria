import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { springAt } from '../anim';
import { Stack, Txt } from '../components/Txt';
import { CX } from '../theme';
import { rel } from '../timeline';

// 14,5–15,5 · "I ONLY NEED" → "ONE." enorme dentro de un círculo (trazo de rotulador)
export const S11OnlyNeed: React.FC = () => {
  const c = rel('onlyNeed');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const draw = springAt(f, c.one, fps, { damping: 22, stiffness: 140 });
  const R = 345;
  const len = 2 * Math.PI * R * 1.1;
  const cy = 1080;
  return (
    <>
      <Stack top={250} style={{ height: 200 }}>
        <Txt at={c.need} size={190} spacing={3}>I ONLY NEED</Txt>
      </Stack>
      <svg width="1080" height="1920" style={{ position: 'absolute', inset: 0 }}>
        {[0, 1].map((k) => (
          <ellipse
            key={k}
            cx={CX + k * 6}
            cy={cy - k * 4}
            rx={R + k * 10}
            ry={R - 12 + k * 6}
            fill="none"
            stroke="#0A0A0A"
            strokeWidth={k ? 7 : 16}
            strokeLinecap="round"
            transform={`rotate(${-80 + k * 14} ${CX} ${cy})`}
            strokeDasharray={len}
            strokeDashoffset={len * (1 - draw * (k ? 0.92 : 1.05))}
            opacity={f >= c.one ? 1 : 0}
          />
        ))}
      </svg>
      <Stack top={cy - 260} style={{ height: 520 }}>
        <Txt at={c.one} size={430} from={2.2}>ONE.</Txt>
      </Stack>
    </>
  );
};
