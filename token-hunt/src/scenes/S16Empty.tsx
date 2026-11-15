import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { bounce, countSteps } from '../anim';
import { Chest } from '../components/Chest';
import { Stack, Txt } from '../components/Txt';
import { BEBAS } from '../fonts';
import { C, CX } from '../theme';
import { rel } from '../timeline';

// 20,0–22,0 · CHEST #3001 → 3008 → 3015 → 3022, sello rojo "EMPTY" que cae de golpe en cada uno
export const S16Empty: React.FC = () => {
  const c = rel('empty');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const changes = [c.c1, c.c2, c.c3, c.c4];
  const stamps = [c.s1, c.s2, c.s3, c.s4];
  const n = countSteps(f, [[c.c1, 3001], [c.c2, 3008], [c.c3, 3015], [c.c4, 3022]], 6);
  const idx = Math.max(0, changes.filter((x) => f >= x).length - 1);
  const b = bounce(f, changes[idx], fps);
  const s = stamps[idx];
  // el sello cae en 5 frames y aterriza exactamente en su corchea
  const k = interpolate(f, [s - 5, s], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const stampScale = interpolate(k, [0, 1], [3.2, 1]);
  const settle = f >= s ? 1 + 0.06 * Math.exp(-(f - s) / 2) * Math.cos((f - s) * 1.6) : 1;
  const rot = [-14, 9, -8, 12][idx];
  const chestY = 820;
  return (
    <>
      <Stack top={250} style={{ height: 200 }}>
        <Txt at={0} size={190} spacing={2}>
          CHEST <span style={{ fontVariantNumeric: 'tabular-nums' }}>#{n}</span>
        </Txt>
      </Stack>
      <div style={{ position: 'absolute', left: CX - 260, top: chestY, transform: `translateY(${b.y}px) scale(${b.sx}, ${b.sy})`, transformOrigin: '50% 100%' }}>
        <Chest width={520} />
      </div>
      {f >= s - 5 ? (
        <div
          style={{
            position: 'absolute',
            left: CX - 300,
            top: chestY + 100,
            width: 600,
            display: 'flex',
            justifyContent: 'center',
            opacity: k,
            transform: `rotate(${rot}deg) scale(${stampScale * settle})`,
            filter: k < 1 ? `blur(${(1 - k) * 8}px)` : undefined,
          }}
        >
          <div
            style={{
              border: `16px solid ${C.red}`,
              borderRadius: 26,
              padding: '6px 40px 0',
              fontFamily: BEBAS,
              fontSize: 220,
              lineHeight: 1,
              color: C.red,
              letterSpacing: 10,
              background: 'rgba(230,230,230,0.15)',
              boxShadow: '0 8px 30px rgba(225,6,0,0.25)',
              WebkitMaskImage: 'radial-gradient(circle at 30% 40%, #000 60%, rgba(0,0,0,0.82) 100%)',
            }}
          >
            EMPTY
          </div>
        </div>
      ) : null}
    </>
  );
};
