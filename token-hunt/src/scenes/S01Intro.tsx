import React from 'react';
import { Easing, interpolate, useCurrentFrame } from 'remotion';
import { IntroArt, LOOP_ZOOM } from '../components/IntroArt';

// 0,0–0,5 · Zoom-out desde dentro de la moneda hasta revelar las escaleras y el monigote.
// El final del vídeo hace el zoom-in contrario: bucle infinito.
export const S01Intro: React.FC = () => {
  const f = useCurrentFrame();
  const zoom = interpolate(f, [0, 15], [LOOP_ZOOM, 1.0], { easing: Easing.out(Easing.cubic), extrapolateRight: 'clamp' });
  return <IntroArt t={f} zoom={zoom} />;
};
