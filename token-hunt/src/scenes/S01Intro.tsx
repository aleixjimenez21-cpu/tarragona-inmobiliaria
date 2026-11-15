import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { IntroArt } from '../components/IntroArt';

// 0,0–0,5 · Moneda en lo alto de las escaleras, monigote pequeño abajo (negro)
export const S01Intro: React.FC = () => {
  const f = useCurrentFrame();
  return <IntroArt t={f} zoom={interpolate(f, [0, 15], [1, 1.07])} />;
};
