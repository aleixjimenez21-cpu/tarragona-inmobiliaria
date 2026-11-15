import React from 'react';
import { useSvgId } from './ids';

/** Cofre de tesoro original con remaches y calavera estilizada. variant gray = "apagado". */
export const Chest: React.FC<{
  width: number;
  variant?: 'gold' | 'gray';
  glow?: boolean;
  style?: React.CSSProperties;
}> = ({ width, variant = 'gold', glow = false, style }) => {
  const id = useSvgId('chest');
  const gold = variant === 'gold';
  const P = gold
    ? { hi: '#FFE38A', mid: '#FFC93C', lo: '#E08600', band: '#B86A00', bandHi: '#E39A1B', line: '#3A2200', rivet: '#FFF0B8', skull: '#FFF6DC', dark: '#2A1700' }
    : { hi: '#CFCFCF', mid: '#A9A9A9', lo: '#7C7C7C', band: '#5E5E5E', bandHi: '#8A8A8A', line: '#262626', rivet: '#D9D9D9', skull: '#E4E4E4', dark: '#2B2B2B' };
  const h = width * 0.88;
  const rivets = (x: number, ys: number[]) => ys.map((y) => <circle key={`${x}-${y}`} cx={x} cy={y} r="4.2" fill={P.rivet} stroke={P.line} strokeWidth="2" />);
  return (
    <div style={{ width, height: h, filter: glow ? 'drop-shadow(0 0 22px rgba(255,201,60,0.7)) drop-shadow(0 0 70px rgba(255,159,28,0.35))' : undefined, ...style }}>
      <svg viewBox="0 0 200 176" width={width} height={h}>
        <defs>
          <linearGradient id={`${id}body`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={P.mid} />
            <stop offset="1" stopColor={P.lo} />
          </linearGradient>
          <linearGradient id={`${id}lid`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={P.hi} />
            <stop offset="1" stopColor={P.mid} />
          </linearGradient>
        </defs>
        {/* sombra */}
        <ellipse cx="100" cy="168" rx="92" ry="7" fill="#000" opacity="0.28" />
        {/* cuerpo */}
        <rect x="12" y="74" width="176" height="88" rx="8" fill={`url(#${id}body)`} stroke={P.line} strokeWidth="5" />
        {/* tapa */}
        <path d="M12 76 L12 48 Q12 14 48 14 L152 14 Q188 14 188 48 L188 76 Z" fill={`url(#${id}lid)`} stroke={P.line} strokeWidth="5" strokeLinejoin="round" />
        <path d="M24 44 Q26 24 50 24 L150 24" fill="none" stroke="#fff" strokeOpacity="0.45" strokeWidth="5" strokeLinecap="round" />
        {/* bandas */}
        {[38, 146].map((x) => (
          <g key={x}>
            <path d={`M${x} 16 L${x + 16} 16 L${x + 16} 162 L${x} 162 Z`} fill={P.band} stroke={P.line} strokeWidth="3.5" />
            <rect x={x + 3} y="18" width="4" height="142" fill={P.bandHi} opacity="0.7" />
          </g>
        ))}
        <rect x="12" y="68" width="176" height="14" fill={P.band} stroke={P.line} strokeWidth="3.5" />
        {rivets(46, [30, 54, 96, 120, 146])}
        {rivets(154, [30, 54, 96, 120, 146])}
        {rivets(24, [75])}
        {rivets(176, [75])}
        {/* placa + calavera estilizada propia */}
        <g transform="translate(100 112)">
          <path d="M-30 -30 L30 -30 L34 22 Q0 40 -34 22 Z" fill={P.dark} stroke={P.line} strokeWidth="3" />
          <path d="M0 -24 C17 -24 24 -13 24 -2 C24 7 19 12 15 14 L15 22 L-15 22 L-15 14 C-19 12 -24 7 -24 -2 C-24 -13 -17 -24 0 -24Z" fill={P.skull} />
          {/* ojos en forma de rombo (estilo propio) */}
          <path d="M-12 -6 L-5 -1 L-12 5 L-19 -1Z" fill={P.dark} />
          <path d="M12 -6 L19 -1 L12 5 L5 -1Z" fill={P.dark} />
          <path d="M0 4 L3.5 10 L-3.5 10Z" fill={P.dark} />
          <path d="M-8 16 V22 M0 16 V22 M8 16 V22" stroke={P.dark} strokeWidth="2.6" />
          {/* rayo / grieta */}
          <path d="M5 -24 L2 -16 L6 -13 L3 -8" fill="none" stroke={P.dark} strokeWidth="1.8" strokeLinecap="round" />
        </g>
      </svg>
    </div>
  );
};
