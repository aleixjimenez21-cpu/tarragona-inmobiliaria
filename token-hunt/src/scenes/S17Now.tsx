import React from 'react';
import { Kinetic } from '../components/Kinetic';
import { Stack } from '../components/Txt';
import { rel } from '../timeline';

// 22,0–22,5 · "NOW" con glow blanco y ecos
export const S17Now: React.FC = () => {
  const c = rel('now');
  return (
    <Stack>
      <Kinetic text="NOW" at={c.now} size={580} mode="slam" stagger={0.6} glow={2} echo spacing={8} />
    </Stack>
  );
};
