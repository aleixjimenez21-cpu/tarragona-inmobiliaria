import React from 'react';
import { Easing, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { springAt } from '../anim';
import { Chest } from '../components/Chest';
import { EmptyPuff, Particles } from '../components/Fx';
import { Odometer } from '../components/Odometer';
import { Stack, Txt } from '../components/Txt';
import { BEBAS } from '../fonts';
import { C, CX, glowFor } from '../theme';
import { rel } from '../timeline';

// 2,0–4,0 · CHEST #2861 → 2891 → 2921 → 2951: en cada beat cae un cofre nuevo, se abre… y está VACÍO.
export const S03Chests: React.FC = () => {
  const c = rel('chests');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const cues = [c.c1, c.c2, c.c3, c.c4];
  const vals = [2861, 2891, 2921, 2951];
  const i = Math.max(0, cues.filter((x) => f >= x).length - 1);
  const at = cues[i];
  const v = i === 0 ? vals[0] : interpolate(f, [at, at + 7], [vals[i - 1], vals[i]], { easing: Easing.out(Easing.cubic), extrapolateRight: 'clamp' });
  const vel = i === 0 ? 0 : Math.abs(interpolate(f + 1, [at, at + 7], [vals[i - 1], vals[i]], { easing: Easing.out(Easing.cubic), extrapolateRight: 'clamp' }) - v);
  const drop = springAt(f, at, fps, { damping: 10, stiffness: 260 });
  const open = springAt(f, at + 4, fps, { damping: 9, stiffness: 220 });
  const chestY = 700;
  return (
    <>
      <Particles count={14} seed="ch" opacity={0.4} />
      <div style={{ position: 'absolute', left: CX - 250, top: chestY, transform: `translateY(${(1 - drop) * -700}px) rotate(${(1 - drop) * 8}deg)` }}>
        <Chest width={500} glow open={f >= at + 4 ? open : 0} />
      </div>
      <Stack top={250} style={{ height: 220 }}>
        <div style={{ fontFamily: BEBAS, fontSize: 190, color: C.white, textShadow: glowFor(C.white), display: 'flex', alignItems: 'flex-start' }}>
          CHEST&nbsp;<span style={{ color: C.gold, textShadow: glowFor(C.gold) }}>#</span>
          <Odometer value={v} size={190} color={C.gold} velocity={vel} />
        </div>
      </Stack>
      <EmptyPuff x={CX} y={chestY + 70} at={at + 5} moths={i % 2 === 0 ? 1 : 2} />
      <Stack top={1230} style={{ height: 160 }}>
        <Txt at={c.c1 + 2} size={130} spacing={6} color="#CFCFCF" glow={0.5}>
          <span style={{ color: C.red, textShadow: glowFor(C.red) }}>0</span> TOKENS
        </Txt>
      </Stack>
    </>
  );
};
