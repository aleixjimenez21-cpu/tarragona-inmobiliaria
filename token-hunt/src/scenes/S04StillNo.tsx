import React from 'react';
import { useCurrentFrame } from 'remotion';
import { Chest } from '../components/Chest';
import { EmptyPuff } from '../components/Fx';
import { Kinetic } from '../components/Kinetic';
import { Typewriter } from '../components/Typewriter';
import { Stack } from '../components/Txt';
import { CX } from '../theme';
import { rel } from '../timeline';

// 4,0–5,0 · "STILL NO TOKEN" + cofre abierto y vacío (sale una polilla) + "1 in 137,500, they said" a máquina
export const S04StillNo: React.FC = () => {
  const c = rel('stillNo');
  const f = useCurrentFrame();
  return (
    <>
      <Stack top={240} style={{ height: 520 }}>
        <Kinetic text="STILL NO" at={c.title} size={280} mode="rise" stagger={1} />
        <Kinetic text="TOKEN" at={c.title + 3} size={280} mode="rise" stagger={1} />
      </Stack>
      <div style={{ position: 'absolute', left: CX - 200, top: 860, transform: `rotate(${Math.sin(f / 3) * 1.2}deg)` }}>
        <Chest width={400} variant="gray" open={1} />
      </div>
      <EmptyPuff x={CX} y={920} at={2} moths={1} seed="still" />
      <Stack top={1300} style={{ height: 120 }}>
        <Typewriter at={c.sub} plain="1 in 137,500, they said" text="1 in 137,500, they said" color="#4A4A4A" cps={2.6} />
      </Stack>
    </>
  );
};
