import React from 'react';
import { useCurrentFrame } from 'remotion';
import { Kinetic } from '../components/Kinetic';
import { Stack } from '../components/Txt';
import { C } from '../theme';
import { rel } from '../timeline';

// 15,5–16,0 · "GIVE UP?" — tiembla, a punto de romperse
export const S12GiveUpQ: React.FC = () => {
  const c = rel('giveUpQ');
  const f = useCurrentFrame();
  const jitter = (f % 2 === 0 ? 1 : -1) * (3 + f * 0.4);
  return (
    <Stack>
      <div style={{ display: 'flex', transform: `translateX(${jitter}px)` }}>
        <Kinetic text="GIVE UP" at={c.q} size={300} mode="zoom" stagger={0.5} />
        <Kinetic text="?" at={c.q + 2} size={300} color={C.red} mode="slam" />
      </div>
    </Stack>
  );
};
