import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { springAt } from '../anim';
import { Desk } from '../components/Desk';
import { LedClock } from '../components/LedClock';
import { Typewriter } from '../components/Typewriter';
import { Stack } from '../components/Txt';
import { rel } from '../timeline';

// 10,0–12,0 · 3:47 AM en una habitación a oscuras, reloj LED, monigote tecleando, la moneda crece en su cabeza
export const S08Am347: React.FC = () => {
  const c = rel('am347');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const z = interpolate(springAt(f, c.zoom, fps, { damping: 18 }), [0, 1], [1, 1.12]);
  const clock = springAt(f, c.time, fps, { damping: 12 });
  return (
    <>
      <div style={{ position: 'absolute', inset: 0, transform: `scale(${z})`, transformOrigin: '480px 1000px' }}>
        <Desk bubbleAt={c.bubble} coinFrom={0.25} coinTo={0.85} growFrames={45} />
      </div>
      <Stack top={180} style={{ height: 300, transform: `scale(${interpolate(clock, [0, 1], [1.4, 1])})`, opacity: Math.min(1, clock * 2) }}>
        <LedClock hour={3} minutes={47} />
      </Stack>
      <Stack top={1500} style={{ height: 120 }}>
        <Typewriter at={c.sub} plain="one more chest..." text="one more chest..." size={58} cps={2} color="#A8B4C8" />
      </Stack>
    </>
  );
};
