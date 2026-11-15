import React from 'react';
import { Easing, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { springAt } from '../anim';
import { Chest } from '../components/Chest';
import { EmptyPuff } from '../components/Fx';
import { Odometer } from '../components/Odometer';
import { Stack } from '../components/Txt';
import { BEBAS } from '../fonts';
import { C, CX } from '../theme';
import { rel } from '../timeline';

// 20,0–22,0 · CHEST #3001 → 3008 → 3015 → 3022: cae el cofre, se abre, y el sello "EMPTY" lo aplasta en la corchea
export const S16Empty: React.FC = () => {
  const c = rel('empty');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const changes = [c.c1, c.c2, c.c3, c.c4];
  const stamps = [c.s1, c.s2, c.s3, c.s4];
  const vals = [3001, 3008, 3015, 3022];
  const idx = Math.max(0, changes.filter((x) => f >= x).length - 1);
  const at = changes[idx];
  const ease = { easing: Easing.out(Easing.cubic), extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;
  const v = idx === 0 ? vals[0] : interpolate(f, [at, at + 6], [vals[idx - 1], vals[idx]], ease);
  const vel = idx === 0 ? 0 : Math.abs(interpolate(f + 1, [at, at + 6], [vals[idx - 1], vals[idx]], ease) - v);
  const drop = idx === 0 ? 1 : springAt(f, at, fps, { damping: 11, stiffness: 300 });
  const open = springAt(f, at + 2, fps, { damping: 10, stiffness: 260 });
  const s = stamps[idx];
  const k = interpolate(f, [s - 5, s], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.in(Easing.quad) });
  const stampScale = interpolate(k, [0, 1], [3.2, 1]);
  const settle = f >= s ? 1 + 0.06 * Math.exp(-(f - s) / 2) * Math.cos((f - s) * 1.6) : 1;
  const squash = f >= s ? 1 - 0.08 * Math.exp(-(f - s) / 2.5) : 1;
  const rot = [-14, 9, -8, 12][idx];
  const chestY = 820;
  return (
    <>
      <div style={{ position: 'absolute', left: CX - 260, top: chestY, transform: `translateY(${(1 - drop) * -800}px) scaleY(${squash})`, transformOrigin: '50% 100%' }}>
        <Chest width={520} open={f >= at + 2 ? open : 0} />
      </div>
      <Stack top={250} style={{ height: 210 }}>
        <div style={{ fontFamily: BEBAS, fontSize: 190, color: C.ink, display: 'flex', alignItems: 'flex-start' }}>
          CHEST&nbsp;#<Odometer value={v} size={190} velocity={vel} />
        </div>
      </Stack>
      <EmptyPuff x={CX} y={chestY + 70} at={s} moths={idx % 2 ? 2 : 1} seed="emp" />
      {f >= s - 5 ? (
        <div style={{ position: 'absolute', left: CX - 300, top: chestY + 110, width: 600, display: 'flex', justifyContent: 'center', opacity: k, transform: `rotate(${rot}deg) scale(${stampScale * settle})`, filter: k < 1 ? `blur(${(1 - k) * 8}px)` : undefined }}>
          <div style={{ border: `16px solid ${C.red}`, borderRadius: 26, padding: '6px 40px 0', fontFamily: BEBAS, fontSize: 220, lineHeight: 1, color: C.red, letterSpacing: 10, background: 'rgba(230,230,230,0.18)', boxShadow: '0 8px 30px rgba(225,6,0,0.25)', WebkitMaskImage: 'radial-gradient(circle at 30% 40%, #000 60%, rgba(0,0,0,0.8) 100%)' }}>
            EMPTY
          </div>
        </div>
      ) : null}
    </>
  );
};
