import React from 'react';
import { useCurrentFrame } from 'remotion';
import { Stack, Txt } from '../components/Txt';
import { C } from '../theme';
import { rel } from '../timeline';

// 15,5–16,0 · "GIVE UP?"
export const S12GiveUpQ: React.FC = () => {
  const c = rel('giveUpQ');
  const f = useCurrentFrame();
  const jitter = f % 2 === 0 ? 3 : -3;
  return (
    <Stack>
      <div style={{ display: 'flex', transform: `translateX(${jitter}px)` }}>
        <Txt at={c.q} size={300} from={1.8}>GIVE UP</Txt>
        <Txt at={c.q} size={300} color={C.red} from={2.6}>?</Txt>
      </div>
    </Stack>
  );
};
