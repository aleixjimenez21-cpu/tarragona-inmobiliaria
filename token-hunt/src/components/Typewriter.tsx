import React from 'react';
import { useCurrentFrame } from 'remotion';
import { MONT } from '../fonts';

/** Subtítulo que se escribe solo, con cursor parpadeante. */
export const Typewriter: React.FC<{ text: React.ReactNode; plain: string; at: number; cps?: number; size?: number; color?: string; style?: React.CSSProperties }> = ({
  text,
  plain,
  at,
  cps = 2.2,
  size = 52,
  color = '#BDBDBD',
  style,
}) => {
  const f = useCurrentFrame();
  if (f < at) return null;
  const n = Math.min(plain.length, Math.floor((f - at) * cps));
  const done = n >= plain.length;
  const cursor = !done || Math.floor(f / 8) % 2 === 0;
  return (
    <div style={{ fontFamily: MONT, fontWeight: 600, fontSize: size, color, fontStyle: 'italic', whiteSpace: 'nowrap', textAlign: 'center', ...style }}>
      {done ? text : plain.slice(0, n)}
      <span style={{ opacity: cursor ? 0.9 : 0, fontStyle: 'normal', marginLeft: 4 }}>|</span>
    </div>
  );
};
