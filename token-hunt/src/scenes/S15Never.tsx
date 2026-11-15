import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { Coin } from '../components/Coin';
import { poses, Stickman } from '../components/Stickman';
import { Stack, Txt } from '../components/Txt';
import { rel, sceneById } from '../timeline';

// 18,0–20,0 · "NEVER GIVING UP" a pantalla completa, monigote empujando la moneda cuesta arriba
const A = { x: 20, y: 1660 };
const B = { x: 1060, y: 1290 };
const slopeY = (x: number) => A.y + ((x - A.x) * (B.y - A.y)) / (B.x - A.x);
const ANG = Math.atan2(B.y - A.y, B.x - A.x); // negativo (sube a la derecha)

export const S15Never: React.FC = () => {
  const c = rel('never');
  const f = useCurrentFrame();
  const dur = sceneById('never').duration;
  const x = interpolate(f, [0, dur], [250, 380]);
  const zoom = interpolate(f, [c.zoom, c.zoom + 8], [1, 1.1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const coinR = 95;
  const coinX = x + 150;
  // centro de la moneda: punto de la pendiente + normal * radio
  const nx = Math.sin(ANG) * coinR; // ANG<0 → nx<0 … normal hacia arriba
  const ny = -Math.cos(ANG) * coinR;
  const cyC = slopeY(coinX) + ny;
  const roll = ((coinX - 400) / (2 * Math.PI * coinR)) * 360;
  return (
    <div style={{ position: 'absolute', inset: 0, transform: `scale(${zoom})`, transformOrigin: '480px 900px' }}>
      <svg width="1080" height="1920" style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <linearGradient id="hill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#BDBDBD" />
            <stop offset="1" stopColor="#9A9A9A" />
          </linearGradient>
        </defs>
        <path d={`M${A.x - 40} ${A.y + 14} L${B.x + 40} ${B.y - 14} L1120 1960 L-40 1960 Z`} fill="url(#hill)" />
        <path d={`M${A.x - 40} ${A.y + 14} L${B.x + 40} ${B.y - 14}`} stroke="#0A0A0A" strokeWidth="10" strokeLinecap="round" />
      </svg>
      <div style={{ position: 'absolute', left: coinX + nx - coinR, top: cyC - coinR }}>
        <Coin size={coinR * 2} glow={0.7} rotate={roll} />
      </div>
      <Stickman pose={poses.push(f, 26)} x={x} y={slopeY(x) - 72} scale={1.05} />
      <Stack top={200} style={{ height: 1060 }}>
        <Txt at={c.never} size={390}>NEVER</Txt>
        <Txt at={c.giving} size={390}>GIVING</Txt>
        <Txt at={c.up} size={390} from={2}>UP</Txt>
      </Stack>
    </div>
  );
};
