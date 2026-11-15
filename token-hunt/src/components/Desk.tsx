import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { springAt } from '../anim';
import { Coin } from './Coin';
import { poses, Stickman } from './Stickman';

/** Habitación a oscuras a las 3 AM: solo la luz fría del monitor. Bocadillo con la moneda que crece. */
export const Desk: React.FC<{ bubbleAt: number; coinFrom: number; coinTo: number; typingSpeed?: number; growFrames?: number }> = ({
  bubbleAt,
  coinFrom,
  coinTo,
  typingSpeed = 1,
  growFrames = 45,
}) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const line = '#8C8C8C';
  const b = springAt(f, bubbleAt, fps, { damping: 12 });
  const grow = interpolate(f, [bubbleAt, bubbleAt + growFrames], [coinFrom, coinTo], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const pulse = 1 + 0.04 * Math.sin(f / 4);
  const scr = 0.82 + 0.18 * Math.sin(f / 2.3) * Math.sin(f / 5.7);
  return (
    <div style={{ position: 'absolute', inset: 0, transform: 'translate(65px, 150px)' }}>
      {/* cono de luz del monitor hacia el monigote */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          clipPath: 'polygon(600px 900px, 600px 1050px, 180px 1300px, 140px 820px)',
          background: 'linear-gradient(270deg, rgba(225,235,255,0.45) 0%, rgba(225,235,255,0.06) 100%)',
          filter: 'blur(14px)',
          opacity: scr,
          mixBlendMode: 'screen',
        }}
      />
      <div style={{ position: 'absolute', left: 430, top: 780, width: 520, height: 420, borderRadius: '50%', background: 'radial-gradient(circle, rgba(220,232,255,0.55) 0%, rgba(220,232,255,0) 65%)', opacity: scr }} />
      <svg width="1080" height="1920" style={{ position: 'absolute', inset: 0 }}>
        <g stroke={line} strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" fill="none">
          <path d="M90 1262 H860" strokeWidth="6" opacity="0.35" />
          <path d="M230 1186 H345 M250 1186 L236 1258 M330 1186 L344 1258 M232 1186 L214 1030" opacity="0.8" />
          <path d="M410 1122 H850 M440 1122 V1258 M820 1122 V1258" />
          <path d="M685 1060 V1112 M640 1116 H730" />
          <path d="M440 1112 H540" strokeWidth="8" stroke="#BFC8D6" />
        </g>
        <rect x="560" y="880" width="250" height="180" rx="14" fill="#161616" stroke={line} strokeWidth="6" />
        <rect x="572" y="892" width="226" height="156" rx="8" fill="#EAF0FF" opacity={scr} style={{ filter: 'drop-shadow(0 0 30px rgba(220,232,255,0.9))' }} />
        <g transform="translate(655 935)" opacity={0.85}>
          <path d="M0 22 V10 Q0 0 10 0 H50 Q60 0 60 10 V22 Z" fill="#0A0A0A" />
          <rect x="0" y="22" width="60" height="38" rx="3" fill="#0A0A0A" />
          <rect x="24" y="30" width="12" height="16" rx="2" fill="#EAF0FF" />
        </g>
      </svg>
      <Stickman pose={poses.sitTyping(f, typingSpeed)} x={300} y={1180} scale={1.5} rim="#DCE6FF" />
      <div style={{ position: 'absolute', left: 0, top: 0, width: 1080, height: 1920, transform: `scale(${b})`, transformOrigin: '360px 960px', opacity: Math.min(1, b * 2) }}>
        {[
          [372, 930, 14],
          [392, 875, 22],
          [412, 805, 32],
        ].map(([x, y, r], i) => (
          <div key={i} style={{ position: 'absolute', left: x - r, top: y - r, width: r * 2, height: r * 2, borderRadius: '50%', background: '#F2F2F2', boxShadow: '0 0 20px rgba(255,255,255,0.35)' }} />
        ))}
        <div style={{ position: 'absolute', left: 250, top: 380, width: 420, height: 380, borderRadius: '50%', background: 'radial-gradient(circle at 45% 40%, #FFFFFF 0%, #E9E9E9 70%, #D4D4D4 100%)', boxShadow: '0 0 60px rgba(255,201,60,0.35)' }} />
        <div style={{ position: 'absolute', left: 460 - 150, top: 570 - 150, width: 300, height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Coin size={300 * grow * pulse} glow={0.8} />
        </div>
      </div>
    </div>
  );
};
