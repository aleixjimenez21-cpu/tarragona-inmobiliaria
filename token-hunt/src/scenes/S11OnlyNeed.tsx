import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { springAt } from '../anim';
import { Kinetic } from '../components/Kinetic';
import { Stack } from '../components/Txt';
import { CX } from '../theme';
import { rel } from '../timeline';

// 14,5–15,5 · "I ONLY NEED" → "ONE." cae con eco y un rotulador lo rodea
export const S11OnlyNeed: React.FC = () => {
  const c = rel('onlyNeed');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const draw = springAt(f, c.one + 2, fps, { damping: 22, stiffness: 160 });
  const R = 345;
  const len = 2 * Math.PI * R * 1.1;
  const cy = 1080;
  return (
    <>
      <Stack top={250} style={{ height: 200 }}>
        <Kinetic text="I ONLY NEED" at={c.need} size={190} mode="flip" stagger={0.8} spacing={3} />
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
            stroke={k ? '#E10600' : '#0A0A0A'}
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
        <Kinetic text="ONE." at={c.one} size={430} mode="slam" stagger={0.7} echo />
      </Stack>
    </>
  );
};
