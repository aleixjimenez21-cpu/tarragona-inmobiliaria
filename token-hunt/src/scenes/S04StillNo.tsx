import React from 'react';
import { useCurrentFrame } from 'remotion';
import { Chest } from '../components/Chest';
import { Stack, Txt } from '../components/Txt';
import { C } from '../theme';
import { rel } from '../timeline';

// 4,0–5,0 · "STILL NO TOKEN" + cofre + "1 in 137,500, they said" (gris claro)
export const S04StillNo: React.FC = () => {
  const c = rel('stillNo');
  const f = useCurrentFrame();
  return (
    <Stack gap={34}>
      <Txt at={c.title} size={280}>STILL NO</Txt>
      <Txt at={c.title + 2} size={280} style={{ marginTop: -44 }}>TOKEN</Txt>
      <div style={{ transform: `rotate(${Math.sin(f / 3) * 1.2}deg)` }}>
        <Chest width={380} variant="gray" />
      </div>
      <Txt at={c.sub} size={54} font="montSemi" color="#4A4A4A" style={{ fontStyle: 'italic' }} from={1.15}>
        1 in 137,500, they said
      </Txt>
      <div style={{ height: 1, color: C.ink }} />
    </Stack>
  );
};
