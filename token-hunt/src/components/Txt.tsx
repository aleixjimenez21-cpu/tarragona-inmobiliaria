import React, { createContext, useContext } from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { popIn } from '../anim';
import { BEBAS, MONT } from '../fonts';
import { C, glowFor } from '../theme';
import type { Bg } from '../timeline';

/** El fondo actual: los textos sobre negro llevan SIEMPRE el mismo glow. */
export const BgContext = createContext<Bg>('black');

export const Txt: React.FC<{
  children: React.ReactNode;
  at?: number; // frame relativo de aparición (spring + blur)
  size: number;
  color?: string;
  font?: 'bebas' | 'mont' | 'montSemi';
  spacing?: number; // letter-spacing px
  from?: number; // escala inicial
  glow?: number; // multiplicador del glow (0 = sin glow)
  style?: React.CSSProperties;
  lineHeight?: number;
}> = ({ children, at = 0, size, color, font = 'bebas', spacing = 0, from, glow, style, lineHeight = 0.9 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const bg = useContext(BgContext);
  const col = color ?? (bg === 'black' ? C.white : C.ink);
  const g = glow ?? (bg === 'black' ? 1 : 0);
  return (
    <div
      style={{
        fontFamily: font === 'bebas' ? BEBAS : MONT,
        fontWeight: font === 'mont' ? 900 : font === 'montSemi' ? 600 : 400,
        fontSize: size,
        lineHeight,
        letterSpacing: spacing,
        color: col,
        textAlign: 'center',
        whiteSpace: 'nowrap',
        textShadow: g > 0 ? glowFor(col, g) : undefined,
        ...popIn(frame, at, fps, { from }),
        ...style,
      }}
    >
      {children}
    </div>
  );
};

/** Columna centrada en la zona segura. */
export const Stack: React.FC<{ children: React.ReactNode; top?: number; gap?: number; style?: React.CSSProperties }> = ({
  children,
  top,
  gap = 0,
  style,
}) => (
  <div
    style={{
      position: 'absolute',
      left: 60,
      width: 840,
      top: top ?? 170,
      bottom: top === undefined ? 250 : undefined,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap,
      ...style,
    }}
  >
    {children}
  </div>
);
