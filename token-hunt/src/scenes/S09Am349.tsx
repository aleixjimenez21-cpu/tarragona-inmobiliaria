import React from 'react';
import { Easing, interpolate, useCurrentFrame } from 'remotion';
import { Desk } from '../components/Desk';
import { LedClock } from '../components/LedClock';
import { Typewriter } from '../components/Typewriter';
import { Stack } from '../components/Txt';
import { rel } from '../timeline';

// 12,0–13,0 · 3:49 AM (los minutos ruedan), "ok. ONE more."
export const S09Am349: React.FC = () => {
  const c = rel('am349');
  const f = useCurrentFrame();
  const ease = { easing: Easing.out(Easing.cubic), extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;
  const m = interpolate(f, [c.time, c.time + 9], [47, 49], ease);
  const vel = Math.abs(interpolate(f + 1, [c.time, c.time + 9], [47, 49], ease) - m);
  return (
    <>
      <div style={{ position: 'absolute', inset: 0, transform: 'scale(1.12)', transformOrigin: '540px 1000px' }}>
        <Desk bubbleAt={-30} coinFrom={0.85} coinTo={1} typingSpeed={1.8} growFrames={60} />
      </div>
      <Stack top={180} style={{ height: 300 }}>
        <LedClock hour={3} minutes={m} velocity={vel} />
      </Stack>
      <Stack top={1500} style={{ height: 120 }}>
        <Typewriter
          at={c.sub}
          plain="ok. ONE more."
          text={<>ok. <span style={{ fontWeight: 900, fontStyle: 'normal', color: '#fff' }}>ONE</span> more.</>}
          size={58}
          cps={2.5}
          color="#A8B4C8"
        />
      </Stack>
    </>
  );
};
