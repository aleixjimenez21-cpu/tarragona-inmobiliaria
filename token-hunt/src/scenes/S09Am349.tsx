import React from 'react';
import { useCurrentFrame } from 'remotion';
import { countUp } from '../anim';
import { Desk } from '../components/Desk';
import { Stack, Txt } from '../components/Txt';
import { rel } from '../timeline';

// 12,0–13,0 · "3:49 AM", "ok. ONE more."
export const S09Am349: React.FC = () => {
  const c = rel('am349');
  const f = useCurrentFrame();
  const min = countUp(f, c.time, 8, 47, 49);
  return (
    <>
      <Stack top={190} style={{ height: 230 }}>
        <Txt at={c.time} size={250} spacing={4} from={1.1}>
          3:{min} AM
        </Txt>
      </Stack>
      <div style={{ position: 'absolute', inset: 0, transform: 'scale(1.12)', transformOrigin: '480px 1000px' }}>
        <Desk bubbleAt={-30} coinFrom={0.85} coinTo={1} typingSpeed={1.8} growFrames={60} />
      </div>
      <Stack top={1500} style={{ height: 120 }}>
        <Txt at={c.sub} size={60} font="montSemi" color="#3A3A3A" from={1.15} style={{ fontStyle: 'italic' }}>
          ok. <span style={{ fontWeight: 900, fontStyle: 'normal', color: '#0A0A0A' }}>ONE</span> more.
        </Txt>
      </Stack>
    </>
  );
};
