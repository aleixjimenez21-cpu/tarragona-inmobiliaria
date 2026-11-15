import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { Coin } from '../components/Coin';
import { Kinetic } from '../components/Kinetic';
import { poses, Stickman } from '../components/Stickman';
import { Stack } from '../components/Txt';
import { rel, sceneById } from '../timeline';

// 18,0–20,0 · "NEVER GIVING UP" gigante DETRÁS de la colina; delante, el monigote empuja la moneda cuesta arriba
const A = { x: 0, y: 1720 };
const B = { x: 1080, y: 1180 };
const slopeY = (x: number) => A.y + ((x - A.x) * (B.y - A.y)) / (B.x - A.x);
const ANG = Math.atan2(B.y - A.y, B.x - A.x);

export const S15Never: React.FC = () => {
  const c = rel('never');
  const f = useCurrentFrame();
  const dur = sceneById('never').duration;
  const x = interpolate(f, [0, dur], [230, 360]);
  const zoom = interpolate(f, [c.zoom, c.zoom + 8], [1, 1.1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const coinR = 95;
  const coinX = x + 150;
  const nx = Math.sin(ANG) * coinR;
  const ny = -Math.cos(ANG) * coinR;
  const roll = ((coinX - 400) / (2 * Math.PI * coinR)) * 360;
  return (
    <div style={{ position: 'absolute', inset: 0, transform: `scale(${zoom})`, transformOrigin: '480px 900px' }}>
      <Stack top={150} style={{ height: 1300 }}>
        <Kinetic text="NEVER" at={c.never} size={420} mode="drop" stagger={1} />
        <Kinetic text="GIVING" at={c.giving} size={420} mode="drop" stagger={1} />
        <Kinetic text="UP" at={c.up} size={560} mode="slam" echo />
      </Stack>
      <svg width="1080" height="1920" style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <linearGradient id="hill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#A9A9A9" />
            <stop offset="1" stopColor="#6E6E6E" />
          </linearGradient>
        </defs>
        <path d={`M${A.x - 40} ${A.y + 22} L${B.x + 40} ${B.y - 22} L1120 1960 L-40 1960 Z`} fill="url(#hill)" />
        <path d={`M${A.x - 40} ${A.y + 22} L${B.x + 40} ${B.y - 22}`} stroke="#0A0A0A" strokeWidth="10" strokeLinecap="round" />
        {/* líneas de esfuerzo/viento */}
        {[0, 1, 2].map((i) => {
          const p = ((f * 9 + i * 120) % 360) / 360;
          const lx = 120 + p * 260;
          const ly = slopeY(lx) - 130 - i * 40;
          return <path key={i} d={`M${lx} ${ly} l${-90} ${-90 * Math.tan(ANG)}`} stroke="#0A0A0A" strokeWidth="5" strokeLinecap="round" opacity={Math.sin(p * Math.PI) * 0.6} />;
        })}
      </svg>
      <div style={{ position: 'absolute', left: coinX + nx - coinR, top: slopeY(coinX) + ny - coinR }}>
        <Coin size={coinR * 2} glow={0.8} rotate={roll} />
      </div>
      <Stickman pose={poses.push(f, 26)} x={x} y={slopeY(x) - 72} scale={1.05} />
    </div>
  );
};
