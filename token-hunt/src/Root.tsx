import React from 'react';
import { Composition, Folder } from 'remotion';
import './fonts';
import { Main, SceneById } from './Main';
import { SyncMonitor } from './SyncMonitor';
import { FPS, HEIGHT, SCENES, TOTAL_FRAMES, WIDTH } from './timeline';

export const Root: React.FC = () => (
  <>
    <Composition id="TokenHunt" component={Main} durationInFrames={TOTAL_FRAMES} fps={FPS} width={WIDTH} height={HEIGHT} defaultProps={{ withAudio: true }} />
    <Composition id="SyncMonitor" component={SyncMonitor} durationInFrames={TOTAL_FRAMES} fps={FPS} width={540} height={960} />
    {/* Una composición por escena, para previsualizar/renderizar por separado */}
    <Folder name="Escenas">
      {SCENES.map((s, i) => (
        <Composition
          key={s.id}
          id={`S${String(i + 1).padStart(2, '0')}-${s.id}`}
          component={() => <SceneById scene={s} prev={SCENES[i - 1]} />}
          durationInFrames={s.duration}
          fps={FPS}
          width={WIDTH}
          height={HEIGHT}
        />
      ))}
    </Folder>
  </>
);
