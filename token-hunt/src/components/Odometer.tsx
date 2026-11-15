import React, { useContext } from 'react';
import { BEBAS } from '../fonts';
import { C, glowFor } from '../theme';
import { BgContext } from './Txt';

/**
 * Contador tipo cuentakilómetros: cada cifra es una columna 0-9 que rueda.
 * `value` puede ser decimal (se interpola) y `velocity` añade desenfoque de movimiento.
 */
export const Odometer: React.FC<{
  value: number;
  digits?: number; // mínimo de cifras
  size: number;
  color?: string;
  glow?: number;
  separator?: boolean; // separador de miles
  velocity?: number; // |unidades por frame| para el blur
  style?: React.CSSProperties;
}> = ({ value, digits = 1, size, color, glow, separator = false, velocity = 0, style }) => {
  const bg = useContext(BgContext);
  const col = color ?? (bg === 'black' ? C.white : C.ink);
  const g = glow ?? (bg === 'black' ? 1 : 0);
  const v = Math.max(0, value);
  const nDigits = Math.max(digits, Math.floor(v).toString().length);
  const h = size * 0.92;
  const w = size * 0.44;
  const cols: React.ReactNode[] = [];
  for (let k = nDigits - 1; k >= 0; k--) {
    const p = Math.pow(10, k);
    let pos: number;
    if (k === 0) pos = v % 10;
    else {
      const d = Math.floor(v / p) % 10;
      const r = (v % p) / p;
      pos = d + (r > 0.9 ? (r - 0.9) * 10 : 0);
    }
    // ceros a la izquierda invisibles
    const leading = v < p && k > 0 && k >= Math.floor(v).toString().length;
    const blur = Math.min(10, (velocity / p) * 6);
    cols.push(
      <span key={`d${k}`} style={{ display: 'inline-block', width: w, height: h, overflow: 'hidden', position: 'relative', verticalAlign: 'top', opacity: leading ? 0 : 1 }}>
        <span style={{ position: 'absolute', left: 0, right: 0, top: 0, transform: `translateY(${-pos * h}px)` }}>
          {Array.from({ length: 11 }, (_, i) => (
            <span key={i} style={{ display: 'block', height: h, lineHeight: `${h}px`, textAlign: 'center', filter: blur > 0.5 ? `blur(${blur.toFixed(1)}px)` : undefined }}>
              {i % 10}
            </span>
          ))}
        </span>
      </span>
    );
    if (separator && k > 0 && k % 3 === 0 && !leading) cols.push(<span key={`s${k}`} style={{ display: 'inline-block', width: w * 0.45, height: h, lineHeight: `${h}px`, verticalAlign: 'top' }}>,</span>);
  }
  return (
    <span style={{ display: 'inline-block', fontFamily: BEBAS, fontSize: size, color: col, textShadow: g > 0 ? glowFor(col, g) : undefined, whiteSpace: 'nowrap', ...style }}>
      {cols}
    </span>
  );
};
