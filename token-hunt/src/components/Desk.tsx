import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { springAt } from '../anim';
import { Coin } from './Coin';
import { poses, Stickman } from './Stickman';

/** Monigote al ordenador de madrugada + bocadillo con la moneda que crece. */
export const Desk: React.FC<{ bubbleAt: number; coinFrom: number; coinTo: number; typingSpeed?: number; growFrames?: number }> = ({
  bubbleAt,
  coinFrom,
  coinTo,
  typingSpeed = 1,
  growFrames = 45,
}) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const ink = '#0A0A0A';
  const b = springAt(f, bubbleAt, fps, { damping: 12 });
  const grow = interpolate(f, [bubbleAt, bubbleAt + growFrames], [coinFrom, coinTo], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const pulse = 1 + 0.04 * Math.sin(f / 4);
  const scr = 0.85 + 0.15 * Math.sin(f / 2.3) * Math.sin(f / 5.7);
  return (
    <div style={{ position: 'absolute', inset: 0, transform: 'translateY(150px)' }}>
      {/* luz del monitor sobre la cara */}
      <div style={{ position: 'absolute', left: 260, top: 760, width: 620, height: 560, borderRadius: '50%', background: 'radial-gradient(circle, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0) 65%)', opacity: scr }} />
      <svg width="1080" height="1920" style={{ position: 'absolute', inset: 0 }}>
        <g stroke={ink} strokeWidth="12" strokeLinecap="round" strokeLinejoin="round" fill="none">
          {/* suelo */}
          <path d="M90 1262 H860" strokeWidth="8" opacity="0.35" />
          {/* silla */}
          <path d="M230 1186 H345 M250 1186 L236 1258 M330 1186 L344 1258 M232 1186 L214 1030" />
          {/* mesa */}
          <path d="M410 1122 H850 M440 1122 V1258 M820 1122 V1258" />
          {/* monitor */}
          <rect x="560" y="880" width="250" height="180" rx="14" fill={ink} />
          <path d="M685 1060 V1112 M640 1116 H730" />
          {/* teclado */}
          <path d="M440 1112 H540" strokeWidth="10" />
        </g>
        {/* pantalla con un cofre pequeño */}
        <rect x="574" y="894" width="222" height="152" rx="8" fill="#F4F4F4" opacity={scr} />
        <g transform="translate(655 935)" opacity={0.8}>
          <path d="M0 22 V10 Q0 0 10 0 H50 Q60 0 60 10 V22 Z" fill="#0A0A0A" />
          <rect x="0" y="22" width="60" height="38" rx="3" fill="#0A0A0A" />
          <rect x="24" y="30" width="12" height="16" rx="2" fill="#F4F4F4" />
        </g>
      </svg>
      <Stickman pose={poses.sitTyping(f, typingSpeed)} x={300} y={1180} scale={1.5} />
      {/* bocadillo de pensamiento */}
      <div style={{ position: 'absolute', left: 0, top: 0, width: 1080, height: 1920, transform: `scale(${b})`, transformOrigin: '360px 960px', opacity: Math.min(1, b * 2) }}>
        {[
          [372, 930, 14],
          [392, 875, 22],
          [412, 805, 32],
        ].map(([x, y, r], i) => (
          <div key={i} style={{ position: 'absolute', left: x - r, top: y - r, width: r * 2, height: r * 2, borderRadius: '50%', background: '#fff', border: '8px solid #0A0A0A', boxSizing: 'border-box' }} />
        ))}
        <div style={{ position: 'absolute', left: 250, top: 380, width: 420, height: 380, borderRadius: '50%', background: '#fff', border: '10px solid #0A0A0A', boxSizing: 'border-box', boxShadow: '0 20px 50px rgba(0,0,0,0.12)' }} />
        <div style={{ position: 'absolute', left: 460 - 150, top: 570 - 150, width: 300, height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Coin size={300 * grow * pulse} glow={0.6} />
        </div>
      </div>
    </div>
  );
};
