import React from 'react';
import { AbsoluteFill, Html5Audio, Sequence, staticFile } from 'remotion';
import { Grain } from './components/Fx';
import { SceneShell } from './components/SceneShell';
import { REGISTRY } from './registry';
import { SCENES, type SceneTiming } from './timeline';

export const SceneById: React.FC<{ scene: SceneTiming; prev?: SceneTiming }> = ({ scene, prev }) => {
  const entry = REGISTRY[scene.id];
  if (!entry) {
    return (
      <AbsoluteFill style={{ background: '#300', color: '#fff', fontSize: 80, alignItems: 'center', justifyContent: 'center' }}>
        TODO {scene.id}
      </AbsoluteFill>
    );
  }
  const { C, shake, leak, drift } = entry;
  return (
    <SceneShell scene={scene} prevBg={prev?.bg} shake={shake} leak={leak} drift={drift}>
      <C />
    </SceneShell>
  );
};

export const Main: React.FC<{ withAudio?: boolean }> = ({ withAudio = true }) => (
  <AbsoluteFill style={{ background: '#0A0A0A' }}>
    {withAudio ? <Html5Audio src={staticFile('audio.mp3')} /> : null}
    {SCENES.map((s, i) => (
      <Sequence key={s.id} from={s.start} durationInFrames={s.duration} name={s.id}>
        <SceneById scene={s} prev={SCENES[i - 1]} />
      </Sequence>
    ))}
    <Grain opacity={0.05} />
  </AbsoluteFill>
);
