import React from 'react';
import { useCurrentFrame } from 'remotion';
import { BEBAS } from '../fonts';
import { C, glowFor } from '../theme';
import { Odometer } from './Odometer';

/** Reloj despertador LED rojo con los dos puntos parpadeando; los minutos ruedan. */
export const LedClock: React.FC<{ hour: number; minutes: number; velocity?: number; size?: number }> = ({ hour, minutes, velocity = 0, size = 260 }) => {
  const f = useCurrentFrame();
  const colon = Math.floor(f / 15) % 2 === 0 ? 1 : 0.15;
  return (
    <div style={{ display: 'inline-flex', alignItems: 'flex-start', fontFamily: BEBAS, fontSize: size, lineHeight: 0.92, color: C.red, textShadow: glowFor(C.red, 1.3), padding: '18px 44px 6px', borderRadius: 36, background: 'linear-gradient(180deg, #1A0A0A 0%, #0E0505 100%)', boxShadow: '0 0 60px rgba(225,6,0,0.25), inset 0 0 30px rgba(0,0,0,0.9)', border: '4px solid #2A1414' }}>
      <span>{hour}</span>
      <span style={{ opacity: colon }}>:</span>
      <Odometer value={minutes} digits={2} size={size} color={C.red} velocity={velocity} glow={1.3} />
      <span style={{ fontSize: size * 0.32, marginLeft: 18, marginTop: size * 0.08, letterSpacing: 4 }}>AM</span>
    </div>
  );
};
