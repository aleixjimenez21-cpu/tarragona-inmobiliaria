import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { springAt } from '../anim';
import { Coin3D } from '../components/Coin3D';
import { Particles, Spotlight } from '../components/Fx';
import { Kinetic } from '../components/Kinetic';
import { poses, Stickman } from '../components/Stickman';
import { Typewriter } from '../components/Typewriter';
import { Stack } from '../components/Txt';
import { CX } from '../theme';
import { rel } from '../timeline';

// 6,0–8,0 · Foco dorado desde arriba, moneda 3D girando en el haz, monigote con los brazos arriba
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
      <Particles count={36} area={{ x: CX - 320, y: 150, w: 640, h: 1100 }} seed="spot" opacity={light} speed={0.7} />
      <div style={{ position: 'absolute', left: CX - 140, top: 430 + Math.sin(f / 10) * 14, transform: `scale(${interpolate(light, [0, 1], [0.4, 1])})`, opacity: light }}>
        <Coin3D size={280} angle={f * 7} tilt={-8} glow={1.4} />
      </div>
      <div style={{ opacity: Math.min(1, man * 1.5), transform: `translateY(${(1 - man) * 80}px)` }}>
        <Stickman pose={poses.armsUp(f)} x={CX} y={floorY - 125} scale={1.25} rim="#FFC93C" />
      </div>
      <Stack top={1290} gap={26}>
        <Kinetic text="DON'T GIVE UP" at={c.title} size={190} mode="rise" stagger={0.8} spacing={2} />
        <Typewriter at={c.sub} plain="chest after chest after chest" text="chest after chest after chest" size={48} cps={3} color="#D9D9D9" />
      </Stack>
    </>
  );
};
