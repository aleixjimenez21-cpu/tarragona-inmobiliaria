import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { springAt } from '../anim';
import { Coin } from '../components/Coin';
import { GodRays, Particles } from '../components/Fx';
import { poses, Stickman } from '../components/Stickman';
import { Kinetic } from '../components/Kinetic';
import { Stack } from '../components/Txt';
import { CX } from '../theme';
import { BEAT_FRAMES, rel } from '../timeline';

// 26,0–28,0 · Escaleras en perspectiva, monigote subiendo hacia la moneda, "KEEP CLIMBING"
const VP = { x: CX, y: 400 };
const K = 1320;
const W0 = 1250;

export const S20Climb: React.FC = () => {
  const c = rel('climb');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scroll = f / BEAT_FRAMES; // un escalón por beat
  const frac = scroll % 1;
  const yAt = (d: number) => VP.y + K / d;
  const wAt = (d: number) => W0 / d;
  const steps = [];
  for (let i = 40; i >= 0; i--) {
    const d = i + 1 - frac + 0.35;
    if (d < 0.4) continue;
    const yb = yAt(d), ym = yAt(d + 0.5), yt = yAt(d + 1);
    const wb = wAt(d), wm = wAt(d + 0.5), wt = wAt(d + 1);
    const lit = Math.min(1, 2.2 / d);
    const fade = Math.min(1, (d - 0.4) * 2);
    steps.push(
      <g key={i} opacity={fade}>
        {/* huella (horizontal) */}
        <path d={`M${VP.x - wm / 2} ${ym} L${VP.x + wm / 2} ${ym} L${VP.x + wt / 2} ${yt} L${VP.x - wt / 2} ${yt} Z`} fill="#17140F" />
        {/* tabica (vertical) */}
        <path d={`M${VP.x - wb / 2} ${yb} L${VP.x + wb / 2} ${yb} L${VP.x + wm / 2} ${ym} L${VP.x - wm / 2} ${ym} Z`} fill="#0D0D0D" />
        <path d={`M${VP.x - wm / 2} ${ym} L${VP.x + wm / 2} ${ym}`} stroke="#FFC93C" strokeOpacity={0.25 + 0.55 * (1 - lit * 0.4)} strokeWidth={Math.max(1.5, 7 / d)} />
      </g>
    );
  }
  const textIn = springAt(f, c.keep, fps);
  return (
    <>
      <GodRays x={VP.x} y={VP.y - 60} radius={1000} opacity={0.55} speed={0.4} />
      <svg width="1080" height="1920" style={{ position: 'absolute', inset: 0 }}>
        {steps}
      </svg>
      <div style={{ position: 'absolute', left: VP.x - 90, top: VP.y - 150 + Math.sin(f / 9) * 6 }}>
        <Coin size={180} glow={1.6} />
      </div>
      <Particles count={24} area={{ x: CX - 260, y: 200, w: 520, h: 800 }} seed="climb" />
      <Stickman pose={poses.climb(f, BEAT_FRAMES * 2)} x={CX + 10} y={1010} scale={1.05} rim="#FFC93C" />
      <div style={{ position: 'absolute', left: 0, right: 0, top: 1240, height: 680, background: 'linear-gradient(180deg, rgba(10,10,10,0) 0%, rgba(10,10,10,0.75) 35%)', opacity: textIn }} />
      <Stack top={1270} style={{ height: 400 }}>
        <Kinetic text="KEEP" at={c.keep} size={210} mode="rise" />
        <Kinetic text="CLIMBING" at={c.climbing} size={220} mode="rise" stagger={0.8} spacing={2} echo={2} />
      </Stack>
    </>
  );
};
