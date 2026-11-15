import React from 'react';
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { springAt } from '../anim';
import { Coin } from '../components/Coin';
import { Background, Particles, Vignette } from '../components/Fx';
import { COIN_INTRO, IntroArt } from '../components/IntroArt';
import { Stack, Txt } from '../components/Txt';
import { CX } from '../theme';
import { rel, sceneById } from '../timeline';

// 30,0–32,5 · Moneda dentro de un círculo con flechas girando, "AGAIN AND AGAIN", fundido a negro
// y el último frame = primer frame del vídeo (bucle invisible en TikTok).
const Arrows: React.FC<{ r: number; rot: number }> = ({ r, rot }) => {
  const arc = (a0: number, a1: number) => {
    const p = (a: number) => [CX + r * Math.cos((a * Math.PI) / 180), 0 + r * Math.sin((a * Math.PI) / 180)];
    const [x0, y0] = p(a0), [x1, y1] = p(a1);
    return `M${x0} ${y0} A${r} ${r} 0 0 1 ${x1} ${y1}`;
  };
  const head = (a: number) => {
    const rad = (a * Math.PI) / 180;
    const x = CX + r * Math.cos(rad), y = r * Math.sin(rad);
    const tx = -Math.sin(rad), ty = Math.cos(rad); // tangente (sentido horario)
    const nx = Math.cos(rad), ny = Math.sin(rad);
    const L = 46, W = 34;
    return `M${x + tx * L} ${y + ty * L} L${x + nx * W} ${y + ny * W} L${x - nx * W} ${y - ny * W} Z`;
  };
  return (
    <g transform={`rotate(${rot} ${CX} 0)`}>
      {[0, 180].map((o) => (
        <g key={o}>
          <path d={arc(o + 15, o + 150)} fill="none" stroke="#0A0A0A" strokeWidth="22" strokeLinecap="round" />
          <path d={head(o + 150)} fill="#0A0A0A" />
        </g>
      ))}
    </g>
  );
};

export const S22Again: React.FC = () => {
  const c = rel('again');
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = sceneById('again').duration;
  const last = dur - 1;
  const cy = 800;
  const inS = springAt(f, c.coin, fps, { damping: 12 });
  const rot = f * 6 + interpolate(inS, [0, 1], [-120, 0]);
  // fase A: fundido a negro, la moneda viaja a la posición del primer frame
  const a = interpolate(f, [c.fade, c.loop], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) });
  // fase B: aparece el arte del primer frame; en el último frame es idéntico al frame 0
  const b = interpolate(f, [c.loop, last], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.quad) });
  const coinSize = interpolate(a, [0, 1], [320, COIN_INTRO.size]);
  const coinY = interpolate(a, [0, 1], [cy, COIN_INTRO.y]);
  return (
    <>
      <div style={{ opacity: 1 - a }}>
        <svg width="1080" height="1920" viewBox={`0 ${-cy} 1080 1920`} style={{ position: 'absolute', inset: 0, opacity: inS }}>
          <circle cx={CX} cy={0} r={235} fill="none" stroke="#0A0A0A" strokeWidth="6" opacity="0.25" />
          <Arrows r={300} rot={rot} />
        </svg>
        <Stack top={1230} style={{ height: 400 }}>
          <Txt at={c.again1} size={210}>AGAIN</Txt>
          <Txt at={c.again2} size={210}>AND AGAIN</Txt>
        </Stack>
      </div>
      {/* fundido a negro */}
      <AbsoluteFill style={{ opacity: a }}>
        <Background bg="black" />
        <Particles count={16} seed="again" opacity={a * (1 - b)} area={{ x: 200, y: 400, w: 560, h: 800 }} />
        <Vignette strength={0.52} />
      </AbsoluteFill>
      <div style={{ position: 'absolute', left: CX - coinSize / 2, top: coinY - coinSize / 2, transform: `scale(${interpolate(inS, [0, 1], [0.4, 1])})`, opacity: 1 - b }}>
        <Coin size={coinSize} glow={interpolate(a, [0, 1], [0.9, 1.2])} t={f - last} />
      </div>
      {b > 0 ? (
        <AbsoluteFill style={{ opacity: b }}>
          <IntroArt t={f - last} />
        </AbsoluteFill>
      ) : null}
    </>
  );
};
