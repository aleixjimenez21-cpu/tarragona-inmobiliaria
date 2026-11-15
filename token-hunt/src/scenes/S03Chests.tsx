import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { bounce, countSteps } from '../anim';
import { Chest } from '../components/Chest';
import { Particles } from '../components/Fx';
import { Stack, Txt } from '../components/Txt';
import { C } from '../theme';
import { rel } from '../timeline';

// 2,0–4,0 · "0 TOKENS" + "CHEST #2861" → 2891 → 2921 → 2951, el cofre rebota en cada cambio
export const S03Chests: React.FC = () => {
  const c = rel('chests');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const n = countSteps(f, [[c.c1, 2861], [c.c2, 2891], [c.c3, 2921], [c.c4, 2951]], 7);
  const last = [c.c4, c.c3, c.c2, c.c1].find((x) => f >= x) ?? c.c1;
  const b = bounce(f, last, fps);
  return (
    <>
      <Particles count={18} seed="ch" opacity={0.5} />
      <Stack gap={40}>
        <Txt at={c.c1} size={175} spacing={2}>
          CHEST <span style={{ color: C.gold }}>#{n}</span>
        </Txt>
        <div style={{ transform: `translateY(${b.y}px) scale(${b.sx}, ${b.sy})`, transformOrigin: '50% 100%', margin: '20px 0' }}>
          <Chest width={470} glow />
        </div>
        <Txt at={c.c1 + 3} size={130} spacing={6} color="#D0D0D0" glow={0.6}>
          <span style={{ color: C.red, textShadow: 'inherit' }}>0</span> TOKENS
        </Txt>
      </Stack>
    </>
  );
};
