import React from 'react';
import { useCurrentFrame } from 'remotion';
import { Stack, Txt } from '../components/Txt';
import { rel } from '../timeline';
import { C } from '../theme';

// 0,5–2,0 · "GIVE UP" → aparece la "?" en un golpe
export const S02GiveUp: React.FC = () => {
  const c = rel('giveUp');
  const f = useCurrentFrame();
  const breathe = 1 + 0.012 * Math.sin(f / 5);
  return (
    <Stack>
      <div style={{ transform: `scale(${breathe})`, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Txt at={c.giveUp} size={420}>GIVE</Txt>
        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
          <Txt at={c.giveUp + 3} size={420}>UP</Txt>
          <Txt at={c.q} size={420} color={C.red} from={2.6}>?</Txt>
        </div>
      </div>
    </Stack>
  );
};
