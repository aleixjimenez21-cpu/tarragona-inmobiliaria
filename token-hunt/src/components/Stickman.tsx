import React from 'react';

/**
 * Monigote negro de trazo grueso y redondeado, con esqueleto y poses animadas.
 * Ángulos en grados, absolutos en el mundo: 0 = hacia abajo, 90 = hacia delante (+x), 180 = arriba.
 */
export type Limb = [number, number]; // [segmento superior, segmento inferior]
export interface Pose {
  hipY: number; // desplazamiento vertical de la cadera
  torso: number; // inclinación (0 = recto, + = hacia delante)
  head?: number; // inclinación extra de la cabeza
  armBack: Limb;
  armFront: Limb;
  legBack: Limb;
  legFront: Limb;
}

const L = { torso: 78, neck: 9, head: 21, upper: 42, fore: 40, thigh: 50, shin: 50 };
const rad = (d: number) => (d * Math.PI) / 180;
const dir = (a: number): [number, number] => [Math.sin(rad(a)), Math.cos(rad(a))];
const add = (p: [number, number], a: number, len: number): [number, number] => {
  const [dx, dy] = dir(a);
  return [p[0] + dx * len, p[1] + dy * len];
};

// ---------- poses (funciones del frame) ----------
export const poses = {
  armsUp: (f: number): Pose => {
    const br = Math.sin(f / 9);
    const w = Math.sin(f / 6);
    return {
      hipY: -2 * br,
      torso: 1.5 * br,
      head: -6,
      armBack: [160 + 6 * w, 172 + 6 * w],
      armFront: [-160 - 6 * w, -172 - 6 * w],
      legBack: [-12, -6],
      legFront: [12, 6],
    };
  },
  standLookUp: (f: number): Pose => {
    const br = Math.sin(f / 10);
    return {
      hipY: -1.5 * br,
      torso: -4 + br,
      head: -18,
      armBack: [-8, -4],
      armFront: [10 + br * 2, 18],
      legBack: [-9, -4],
      legFront: [9, 4],
    };
  },
  sitTyping: (f: number, speed = 1): Pose => {
    const br = Math.sin(f / 11);
    const t1 = Math.sin(f * 1.3 * speed);
    const t2 = Math.sin(f * 1.3 * speed + 2.1);
    return {
      hipY: 0,
      torso: 14 + 2 * br,
      head: 10,
      armBack: [38 + 3 * t2, 96 + 9 * t2],
      armFront: [34 + 3 * t1, 92 + 9 * t1],
      legBack: [84, 4],
      legFront: [90, 0],
    };
  },
  climb: (f: number, period = 20): Pose => {
    const p = (2 * Math.PI * f) / period;
    const leg = (ph: number): Limb => {
      const th = 32 + 42 * Math.sin(ph);
      const flex = 10 + 62 * Math.max(0, Math.sin(ph + 0.35));
      return [th, th - flex];
    };
    const arm = (ph: number): Limb => {
      const u = 10 - 38 * Math.sin(ph);
      return [u, u + 55];
    };
    return {
      hipY: -7 * Math.abs(Math.sin(p)),
      torso: 14,
      head: -14,
      legFront: leg(p),
      legBack: leg(p + Math.PI),
      armFront: arm(p + Math.PI),
      armBack: arm(p),
    };
  },
  push: (f: number, period = 24): Pose => {
    const p = (2 * Math.PI * f) / period;
    const leg = (ph: number): Limb => {
      const th = -18 + 34 * Math.sin(ph);
      const flex = 12 + 40 * Math.max(0, Math.sin(ph + 1.2));
      return [th, th - flex];
    };
    const strain = Math.sin(f / 4) * 2;
    return {
      hipY: -4 * Math.abs(Math.sin(p)),
      torso: 52 + strain,
      head: -24,
      armFront: [104 + strain, 96],
      armBack: [112 + strain, 104],
      legFront: leg(p),
      legBack: leg(p + Math.PI),
    };
  },
};

export const Stickman: React.FC<{
  pose: Pose;
  x: number; // posición de la cadera (px)
  y: number;
  scale?: number;
  color?: string;
  rim?: string; // color de luz de contorno (para fondos negros)
  flip?: boolean; // mirar a la izquierda
  style?: React.CSSProperties;
}> = ({ pose, x, y, scale = 1, color = '#0A0A0A', rim, flip = false, style }) => {
  const hip: [number, number] = [0, pose.hipY];
  const shoulder = add(hip, 180 + pose.torso, L.torso);
  const neck = add(shoulder, 180 + pose.torso + (pose.head ?? 0) * 0.3, L.neck);
  const headC = add(neck, 180 + pose.torso + (pose.head ?? 0), L.head);
  const limb = (o: [number, number], [a1, a2]: Limb, l1: number, l2: number) => {
    const k = add(o, a1, l1);
    const e = add(k, a2, l2);
    return `M${o[0]} ${o[1]} L${k[0]} ${k[1]} L${e[0]} ${e[1]}`;
  };
  const parts = [
    limb(shoulder, pose.armBack, L.upper, L.fore),
    limb(hip, pose.legBack, L.thigh, L.shin),
    `M${hip[0]} ${hip[1]} L${shoulder[0]} ${shoulder[1]} L${neck[0]} ${neck[1]}`,
    limb(hip, pose.legFront, L.thigh, L.shin),
    limb(shoulder, pose.armFront, L.upper, L.fore),
  ];
  const sw = 14;
  const S = 400;
  const draw = (stroke: string, w: number, op = 1) => (
    <g opacity={op}>
      {parts.map((d, i) => (
        <path key={i} d={d} fill="none" stroke={stroke} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round" />
      ))}
      <circle cx={headC[0]} cy={headC[1]} r={L.head + (w - sw) / 2} fill={stroke} />
    </g>
  );
  return (
    <div
      style={{
        position: 'absolute',
        left: x - (S / 2) * scale,
        top: y - (S / 2) * scale,
        width: S * scale,
        height: S * scale,
        transform: flip ? 'scaleX(-1)' : undefined,
        filter: rim ? `drop-shadow(0 0 10px ${rim}99)` : undefined,
        ...style,
      }}
    >
      <svg viewBox={`${-S / 2} ${-S / 2} ${S} ${S}`} width={S * scale} height={S * scale} style={{ overflow: 'visible' }}>
        {rim ? draw(rim, sw + 7, 0.95) : null}
        {draw(color, sw)}
      </svg>
    </div>
  );
};
