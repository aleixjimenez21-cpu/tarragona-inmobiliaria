import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { springAt } from '../anim';
import { Kinetic } from '../components/Kinetic';
import { Stack } from '../components/Txt';
import { C } from '../theme';
import { rel } from '../timeline';

// 28,0–30,0 · "I CAN" → "I WILL" → "I MUST" (cada línea más oscura y más grande) + subrayado rojo en el golpe final
export const S21ICan: React.FC = () => {
  const c = rel('iCan');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const u = springAt(f, c.mustPunch, fps, { damping: 18, stiffness: 240 });
  return (
    <Stack gap={46}>
      <Kinetic text="I CAN" at={c.can} size={110} font="mont" color="#A3A3A3" mode="flip" stagger={0.8} lineHeight={1} />
      <Kinetic text="I WILL" at={c.will} size={142} font="mont" color="#5C5C5C" mode="flip" stagger={0.8} lineHeight={1} />
      <div style={{ position: 'relative' }}>
        <Kinetic text="I MUST" at={c.must} size={180} font="mont" color={C.ink} mode="slam" stagger={0.6} lineHeight={1} echo={2} />
        {f >= c.mustPunch ? <div style={{ position: 'absolute', left: 0, bottom: -26, height: 18, width: `${100 * u}%`, background: C.red, borderRadius: 9, transform: 'rotate(-1.5deg)' }} /> : null}
      </div>
    </Stack>
  );
};
