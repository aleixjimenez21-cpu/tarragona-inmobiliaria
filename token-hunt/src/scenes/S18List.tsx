import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { popIn, springAt } from '../anim';
import { Chest } from '../components/Chest';
import { GodRays, Particles } from '../components/Fx';
import { Kinetic } from '../components/Kinetic';
import { C } from '../theme';
import { rel } from '../timeline';

// 22,5–24,0 · MOTIVATION (tachada) → DISCIPLINE (tachada) → OBSESSION: el único cofre que se abre LLENO de luz
export const S18List: React.FC = () => {
  const c = rel('list');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const rows = [
    { at: c.m, label: 'MOTIVATION', gold: false, strike: c.d },
    { at: c.d, label: 'DISCIPLINE', gold: false, strike: c.o },
    { at: c.o, label: 'OBSESSION', gold: true, strike: 9999 },
  ];
  const open = springAt(f, c.o + 3, fps, { damping: 10 });
  const beam = interpolate(f, [c.o + 3, c.o + 10], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const top = 560;
  const rowH = 250;
  return (
    <>
      <GodRays x={190} y={top + 2 * rowH + 60} radius={900} opacity={0.7 * beam} speed={0.8} />
      <Particles count={26} seed="list" opacity={beam} area={{ x: 60, y: top + rowH, w: 840, h: 700 }} speed={1.6} />
      <div style={{ position: 'absolute', left: 90, top, width: 800 }}>
        {rows.map((r, i) => {
          const st = springAt(f, r.strike, fps, { damping: 20, stiffness: 220 });
          const dim = f >= r.strike ? 0.45 : 1;
          return (
            <div key={r.label} style={{ position: 'absolute', top: i * rowH, left: 0, display: 'flex', alignItems: 'center', gap: 30, ...popIn(f, r.at, fps, { from: r.gold ? 1.5 : 1.25 }) }}>
              <div style={{ width: 190, display: 'flex', justifyContent: 'center', opacity: dim }}>
                <Chest width={r.gold ? 190 : 150} variant={r.gold ? 'gold' : 'gray'} glow={r.gold} open={r.gold ? open : 0} />
              </div>
              <div style={{ position: 'relative', opacity: dim }}>
                <Kinetic text={r.label} at={r.at} size={r.gold ? 168 : 150} color={r.gold ? C.gold : '#8A8A8A'} glow={r.gold ? 1.4 : 0} mode={r.gold ? 'slam' : 'rise'} stagger={0.5} echo={r.gold} spacing={3} style={{ textAlign: 'left' }} />
                {f >= r.strike ? <div style={{ position: 'absolute', left: -10, top: '48%', height: 12, width: `${(100 + 6) * st}%`, background: C.red, borderRadius: 6, transform: 'rotate(-3deg)', boxShadow: `0 0 18px ${C.red}` }} /> : null}
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
};
