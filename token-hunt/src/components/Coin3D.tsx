import React from 'react';
import { useCurrentFrame } from 'remotion';
import { Coin } from './Coin';

/** Moneda en 3D real: cara, reverso y canto con grosor (discos apilados en Z). */
export const Coin3D: React.FC<{
  size: number;
  angle: number; // rotación Y en grados
  tilt?: number; // rotación X
  glow?: number;
  thickness?: number; // fracción del tamaño
  style?: React.CSSProperties;
}> = ({ size, angle, tilt = 0, glow = 1, thickness = 0.085, style }) => {
  const f = useCurrentFrame();
  const T = size * thickness;
  const layers = 14;
  return (
    <div
      style={{
        width: size,
        height: size,
        filter: `drop-shadow(0 0 ${size * 0.06 * glow}px rgba(255,201,60,${0.8 * Math.min(1, glow)})) drop-shadow(0 0 ${size * 0.2 * glow}px rgba(255,159,28,${0.5 * Math.min(1, glow)}))`,
        ...style,
      }}
    >
      <div style={{ width: size, height: size, perspective: size * 4 }}>
        <div style={{ position: 'relative', width: size, height: size, transformStyle: 'preserve-3d', transform: `rotateX(${tilt}deg) rotateY(${angle}deg)` }}>
          {Array.from({ length: layers }, (_, i) => {
            const z = -T / 2 + (T * i) / (layers - 1);
            const shade = 0.75 + 0.25 * Math.sin((i / (layers - 1)) * Math.PI);
            return (
              <div
                key={i}
                style={{
                  position: 'absolute',
                  inset: size * 0.015,
                  borderRadius: '50%',
                  transform: `translateZ(${z}px)`,
                  background: `repeating-conic-gradient(rgb(${Math.round(196 * shade)},${Math.round(110 * shade)},0) 0deg 5deg, rgb(${Math.round(240 * shade)},${Math.round(160 * shade)},${Math.round(30 * shade)}) 5deg 10deg)`,
                }}
              />
            );
          })}
          <div style={{ position: 'absolute', inset: 0, transform: `translateZ(${T / 2 + 0.5}px)`, backfaceVisibility: 'hidden' }}>
            <Coin size={size} glow={0} t={f} />
          </div>
          <div style={{ position: 'absolute', inset: 0, transform: `translateZ(${-T / 2 - 0.5}px) rotateY(180deg)`, backfaceVisibility: 'hidden' }}>
            <Coin size={size} glow={0} t={f + 30} />
          </div>
        </div>
      </div>
    </div>
  );
};
