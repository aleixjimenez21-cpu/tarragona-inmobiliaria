import React from 'react';
import { Easing, interpolate, useCurrentFrame } from 'remotion';
import { Odometer } from '../components/Odometer';
import { Stack, Txt } from '../components/Txt';
import { BEBAS } from '../fonts';
import { C, CX, glowFor } from '../theme';
import { rel } from '../timeline';

// 8,0–10,0 · Calendario: en cada beat se arranca una hoja (DAY 1 → 2 → 5 → 12) mientras los cofres suben
const Page: React.FC<{ day: number; style?: React.CSSProperties }> = ({ day, style }) => (
  <div style={{ position: 'absolute', left: CX - 280, top: 260, width: 560, height: 640, borderRadius: 30, background: 'linear-gradient(180deg, #FAFAFA 0%, #E2E2E2 100%)', boxShadow: '0 30px 80px rgba(0,0,0,0.6)', overflow: 'hidden', ...style }}>
    <div style={{ height: 150, background: C.red, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: BEBAS, fontSize: 110, letterSpacing: 26, color: '#fff', paddingLeft: 26 }}>DAY</div>
    <div style={{ height: 490, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: BEBAS, fontSize: 400, color: C.ink, lineHeight: 1, paddingTop: 30 }}>{day}</div>
  </div>
);

export const S07Days: React.FC = () => {
  const c = rel('days');
  const f = useCurrentFrame();
  const cues = [c.d1, c.d2, c.d3, c.d4];
  const days = [1, 2, 5, 12];
  const chests = [40, 95, 260, 731];
  const i = Math.max(0, cues.filter((x) => f >= x).length - 1);
  const at = cues[i];
  const ease = { easing: Easing.out(Easing.cubic), extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;
  const v = interpolate(f, [at, at + 9], [i === 0 ? 0 : chests[i - 1], chests[i]], ease);
  const vel = Math.abs(interpolate(f + 1, [at, at + 9], [i === 0 ? 0 : chests[i - 1], chests[i]], ease) - v);
  const tear = interpolate(f, [at, at + 13], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.in(Easing.quad) });
  const redPulse = 0.7 + 0.3 * Math.abs(Math.sin((f - c.d1) / 4.8));
  return (
    <>
      {/* anillas */}
      <Page day={days[i]} />
      {i > 0 && tear < 1 ? (
        <Page
          day={days[i - 1]}
          style={{
            transformOrigin: '0 0',
            transform: `translate(${tear * 160}px, ${tear * tear * 1300}px) rotate(${tear * 55}deg)`,
            opacity: 1 - tear * 0.6,
            clipPath: `polygon(0 0, 100% 0, 100% 100%, 0 100%)`,
          }}
        />
      ) : null}
      {[CX - 150, CX + 150].map((x) => (
        <div key={x} style={{ position: 'absolute', left: x - 20, top: 228, width: 40, height: 70, borderRadius: 20, background: 'linear-gradient(90deg, #555, #ddd, #555)', boxShadow: '0 4px 10px rgba(0,0,0,0.5)' }} />
      ))}
      <Stack top={970} gap={30} style={{ height: 520 }}>
        <div style={{ fontFamily: BEBAS, fontSize: 160, color: C.white, textShadow: glowFor(C.white), display: 'flex', alignItems: 'flex-start' }}>
          <Odometer value={v} size={160} color={C.gold} velocity={vel} />
          &nbsp;CHESTS
        </div>
        <div style={{ opacity: redPulse }}>
          <Txt at={c.d1 + 3} size={150} color={C.red} spacing={4}>0 TOKENS</Txt>
        </div>
      </Stack>
    </>
  );
};
