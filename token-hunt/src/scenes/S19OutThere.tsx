import React from 'react';
import { Easing, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { springAt } from '../anim';
import { Coin3D } from '../components/Coin3D';
import { GodRays, Particles } from '../components/Fx';
import { Kinetic } from '../components/Kinetic';
import { Stack } from '../components/Txt';
import { CX } from '../theme';
import { rel, BEATS, sceneById } from '../timeline';

// 24,0–26,0 · La moneda 3D entra girando y se planta de frente: rayos, anillos en cada beat y destello anamórfico
export const S19OutThere: React.FC = () => {
  const c = rel('outThere');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const start = sceneById('outThere').start;
  const s = springAt(f, c.coin, fps, { damping: 11 });
  const angle = interpolate(f, [c.coin, c.coin + 24], [720 + 180, 0], { easing: Easing.out(Easing.cubic), extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) + Math.sin(f / 9) * 10;
  const cy = 790;
  const beats = BEATS.map((b) => b - start).filter((b) => b >= 0 && b <= f);
  const flare = 0.6 + 0.4 * Math.sin(f / 5);
  return (
    <>
      <GodRays x={CX} y={cy} radius={1150} opacity={0.8 * s} speed={0.6} />
      <Particles count={44} seed="out" opacity={s} speed={1.4} />
      {beats.slice(-2).map((b) => {
        const t = interpolate(f - b, [0, 20], [0, 1], { extrapolateRight: 'clamp' });
        const r = 270 + 360 * t;
        return <div key={b} style={{ position: 'absolute', left: CX - r, top: cy - r, width: r * 2, height: r * 2, borderRadius: '50%', border: `${10 * (1 - t) + 2}px solid rgba(255,201,60,${0.9 * (1 - t)})`, boxShadow: `0 0 40px rgba(255,201,60,${0.6 * (1 - t)})` }} />;
      })}
      <div style={{ position: 'absolute', left: CX - 260, top: cy - 260, transform: `scale(${interpolate(s, [0, 1], [0.3, 1])})` }}>
        <Coin3D size={520} angle={angle} tilt={-6} glow={1.5} />
      </div>
      {/* destello anamórfico horizontal */}
      <div style={{ position: 'absolute', left: -200, width: 1480, top: cy - 6, height: 12, background: 'linear-gradient(90deg, rgba(255,201,60,0) 0%, rgba(255,240,200,0.95) 50%, rgba(255,201,60,0) 100%)', filter: 'blur(3px)', opacity: s * flare, mixBlendMode: 'screen' }} />
      <div style={{ position: 'absolute', left: CX - 90, top: cy - 90, width: 180, height: 180, borderRadius: '50%', background: 'radial-gradient(circle, rgba(255,255,255,0.9) 0%, rgba(255,230,160,0) 70%)', opacity: s * flare * 0.7, mixBlendMode: 'screen' }} />
      <Stack top={1230} style={{ height: 400 }}>
        <Kinetic text="IT'S" at={c.its} size={170} mode="rise" />
        <Kinetic text="OUT THERE." at={c.out} size={220} mode="rise" stagger={0.8} spacing={2} echo={2} />
      </Stack>
    </>
  );
};
