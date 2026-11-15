import React from 'react';
import { Stack, Txt } from '../components/Txt';
import { rel } from '../timeline';

// 22,0–22,5 · "NOW" con glow blanco
export const S17Now: React.FC = () => {
  const c = rel('now');
  return (
    <Stack>
      <Txt at={c.now} size={560} from={2.2} glow={2} spacing={8}>
        NOW
      </Txt>
    </Stack>
  );
};
