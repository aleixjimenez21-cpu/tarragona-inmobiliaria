import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { springAt } from '../anim';
import { Desk } from '../components/Desk';
import { Stack, Txt } from '../components/Txt';
import { rel } from '../timeline';

// 10,0–12,0 · "3:47 AM", monigote al ordenador, bocadillo con la moneda creciendo, "one more chest..."
export const S08Am347: React.FC = () => {
  const c = rel('am347');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const z = interpolate(springAt(f, c.zoom, fps, { damping: 18 }), [0, 1], [1, 1.12]);
  return (
    <>
      <Stack top={190} style={{ height: 230 }}>
        <Txt at={c.time} size={250} spacing={4}>3:47 AM</Txt>
      </Stack>
      <div style={{ position: 'absolute', inset: 0, transform: `scale(${z})`, transformOrigin: '480px 1000px' }}>
        <Desk bubbleAt={c.bubble} coinFrom={0.25} coinTo={0.85} growFrames={45} />
      </div>
      <Stack top={1500} style={{ height: 120 }}>
        <Txt at={c.sub} size={60} font="montSemi" color="#3A3A3A" from={1.15} style={{ fontStyle: 'italic' }}>
          one more chest...
        </Txt>
      </Stack>
    </>
  );
};
