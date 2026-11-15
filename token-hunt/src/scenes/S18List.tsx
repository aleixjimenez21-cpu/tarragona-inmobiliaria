import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { popIn } from '../anim';
import { Chest } from '../components/Chest';
import { Particles } from '../components/Fx';
import { Txt } from '../components/Txt';
import { C } from '../theme';
import { rel } from '../timeline';

// 22,5–24,0 · MOTIVATION (gris) → DISCIPLINE (gris) → OBSESSION (cofre dorado, texto dorado)
export const S18List: React.FC = () => {
  const c = rel('list');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const rows = [
    { at: c.m, label: 'MOTIVATION', gold: false },
    { at: c.d, label: 'DISCIPLINE', gold: false },
    { at: c.o, label: 'OBSESSION', gold: true },
  ];
  return (
    <>
      <Particles count={20} seed="list" opacity={f >= c.o ? 0.8 : 0} area={{ x: 60, y: 1050, w: 840, h: 600 }} />
      <div style={{ position: 'absolute', left: 90, top: 600, width: 780, display: 'flex', flexDirection: 'column', gap: 110 }}>
        {rows.map((r) => (
          <div key={r.label} style={{ display: 'flex', alignItems: 'center', gap: 44, ...popIn(f, r.at, fps, { from: r.gold ? 1.5 : 1.25 }) }}>
            <Chest width={r.gold ? 170 : 150} variant={r.gold ? 'gold' : 'gray'} glow={r.gold} />
            <Txt size={r.gold ? 190 : 165} color={r.gold ? C.gold : '#6E6E6E'} glow={r.gold ? 1.3 : 0} spacing={3} style={{ textAlign: 'left' }}>
              {r.label}
            </Txt>
          </div>
        ))}
      </div>
    </>
  );
};
