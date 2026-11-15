import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { useSvgId } from './ids';

/**
 * "THE TOKEN": moneda dorada original.
 * Anillo exterior con muescas, estrella de 4 puntas, brillo especular que la recorre cada 2 s.
 */
export const Coin: React.FC<{
  size: number;
  glow?: number; // 0..1.5
  shineOffset?: number; // desfase del barrido en frames
  spin?: boolean; // giro 3D sutil
  rotate?: number; // rotación plana (rodando)
  style?: React.CSSProperties;
  t?: number; // tiempo explícito (para el bucle final)
}> = ({ size, glow = 1, shineOffset = 0, spin = false, rotate = 0, style, t }) => {
  const cur = useCurrentFrame();
  const frame = t ?? cur;
  const id = useSvgId('coin');
  // barrido especular: 16 frames de cada 60 (2 s a 30 fps)
  const cyc = (((frame + shineOffset) % 60) + 60) % 60;
  const sweepX = interpolate(cyc, [0, 16], [-170, 170], { extrapolateRight: 'clamp' });
  const flip = spin ? 0.82 + 0.18 * Math.cos(frame / 22) : 1;
  const notches = Array.from({ length: 36 }, (_, i) => i * 10);
  const g = Math.max(0, glow);
  return (
    <div
      style={{
        width: size,
        height: size,
        filter:
          g > 0
            ? `drop-shadow(0 0 ${size * 0.06 * g}px rgba(255,201,60,${0.85 * Math.min(1, g)})) drop-shadow(0 0 ${size * 0.22 * g}px rgba(255,159,28,${0.55 * Math.min(1, g)}))`
            : undefined,
        transform: `scaleX(${flip}) rotate(${rotate}deg)`,
        ...style,
      }}
    >
      <svg viewBox="-100 -100 200 200" width={size} height={size}>
        <defs>
          <linearGradient id={`${id}rim`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#FFE9A6" />
            <stop offset="0.45" stopColor="#FFC93C" />
            <stop offset="1" stopColor="#E07800" />
          </linearGradient>
          <radialGradient id={`${id}face`} cx="0.4" cy="0.35" r="0.75">
            <stop offset="0" stopColor="#FFE58F" />
            <stop offset="0.55" stopColor="#FFC93C" />
            <stop offset="1" stopColor="#FF9F1C" />
          </radialGradient>
          <linearGradient id={`${id}star`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#FFFFFF" />
            <stop offset="1" stopColor="#FFE7A0" />
          </linearGradient>
          <linearGradient id={`${id}shine`} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="#fff" stopOpacity="0" />
            <stop offset="0.5" stopColor="#fff" stopOpacity="0.85" />
            <stop offset="1" stopColor="#fff" stopOpacity="0" />
          </linearGradient>
          <clipPath id={`${id}clip`}>
            <circle r="96" />
          </clipPath>
        </defs>
        {/* canto */}
        <circle r="97" fill="#B85F00" />
        <circle r="95" fill={`url(#${id}rim)`} />
        {/* muescas del anillo exterior */}
        {notches.map((a) => (
          <rect key={a} x="-2.6" y="-95" width="5.2" height="9" rx="1.5" fill="#B86A00" opacity="0.85" transform={`rotate(${a})`} />
        ))}
        <circle r="83" fill="#C46E00" />
        <circle r="80" fill={`url(#${id}face)`} />
        <circle r="70" fill="none" stroke="#E08A10" strokeWidth="2.5" opacity="0.7" />
        <circle r="80" fill="none" stroke="#FFF1C4" strokeWidth="2" opacity="0.8" />
        {/* estrella de 4 puntas: sombra + cara */}
        <path d="M0,-54 C5,-14 14,-5 54,0 C14,5 5,14 0,54 C-5,14 -14,5 -54,0 C-14,-5 -5,-14 0,-54Z" fill="#B86A00" transform="translate(3,4)" opacity="0.7" />
        <path d="M0,-54 C5,-14 14,-5 54,0 C14,5 5,14 0,54 C-5,14 -14,5 -54,0 C-14,-5 -5,-14 0,-54Z" fill={`url(#${id}star)`} />
        <path d="M0,-54 C5,-14 14,-5 54,0 L0,0Z" fill="#FFFFFF" opacity="0.55" />
        {/* barrido especular */}
        <g clipPath={`url(#${id}clip)`}>
          <rect x={sweepX - 22} y="-140" width="44" height="280" fill={`url(#${id}shine)`} transform="rotate(24)" />
          <rect x={sweepX + 30} y="-140" width="12" height="280" fill={`url(#${id}shine)`} opacity="0.6" transform="rotate(24)" />
        </g>
        {/* brillo fijo superior */}
        <ellipse cx="-30" cy="-52" rx="30" ry="11" fill="#fff" opacity="0.35" transform="rotate(-30 -30 -52)" />
      </svg>
    </div>
  );
};
