import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { springAt } from '../anim';
import { Coin } from '../components/Coin';
import { Particles, Spotlight } from '../components/Fx';
import { poses, Stickman } from '../components/Stickman';
import { Stack, Txt } from '../components/Txt';
import { CX } from '../theme';
import { rel } from '../timeline';

// 6,0–8,0 · Foco dorado desde arriba, moneda en el foco, monigote con los brazos arriba,
//           "DON'T GIVE UP" + "chest after chest after chest"
export const S06DontGiveUp: React.FC = () => {
  const c = rel('dontGiveUp');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const light = springAt(f, c.light, fps, { damping: 20 });
  const man = springAt(f, c.man, fps);
  const floorY = 1240;
  return (
    <>
      <Spotlight x={CX} floorY={floorY} opacity={light} />
      <Particles count={30} area={{ x: CX - 300, y: 150, w: 600, h: 1100 }} seed="spot" opacity={light} speed={0.7} />
      <div
        style={{
          position: 'absolute',
          left: CX - 130,
          top: 470 + Math.sin(f / 10) * 14,
          transform: `scale(${interpolate(light, [0, 1], [0.4, 1])})`,
          opacity: light,
        }}
      >
        <Coin size={260} glow={1.3} spin />
      </div>
      <div style={{ opacity: Math.min(1, man * 1.5), transform: `translateY(${(1 - man) * 60}px)` }}>
        <Stickman pose={poses.armsUp(f)} x={CX} y={floorY - 100} scale={1.25} rim="#FFC93C" />
      </div>
      <Stack top={1290} gap={22}>
        <Txt at={c.title} size={190} spacing={2}>DON'T GIVE UP</Txt>
        <Txt at={c.sub} size={50} font="montSemi" color="#D9D9D9" glow={0.4} from={1.15} spacing={1}>
          chest after chest after chest
        </Txt>
      </Stack>
    </>
  );
};
