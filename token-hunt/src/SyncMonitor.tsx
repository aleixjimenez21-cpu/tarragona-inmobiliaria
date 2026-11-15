import { getWaveformPortion, useAudioData } from '@remotion/media-utils';
import React from 'react';
import { AbsoluteFill, staticFile, useCurrentFrame } from 'remotion';
import { BEBAS, MONT } from './fonts';
import { BEATS, FPS, SCENES } from './timeline';

/**
 * Panel de verificación (540x960) para out/comparacion.mp4:
 * forma de onda desplazándose, beats, cortes de escena y cues. La línea roja es "ahora".
 */
export const SyncMonitor: React.FC = () => {
  const f = useCurrentFrame();
  const audio = useAudioData(staticFile('audio.mp3'));
  const scene = SCENES.find((s) => f >= s.start && f < s.end) ?? SCENES[SCENES.length - 1];
  const lastBeat = [...BEATS].reverse().find((b) => b <= f) ?? 0;
  const beatAge = f - lastBeat;
  const cueNow = Object.entries(scene.cues).filter(([, v]) => f >= v && f - v < 6);
  const isCut = SCENES.some((s) => s.start === f);
  const W = 540;
  const pxPerFrame = 8; // ventana visible = 540/8 ≈ 67 frames (~2,2 s)
  const xOf = (fr: number) => W / 2 + (fr - f) * pxPerFrame;
  const visible = (fr: number) => xOf(fr) > -20 && xOf(fr) < W + 20;
  const bars = 135;
  const wave =
    audio &&
    getWaveformPortion({
      audioData: audio,
      startTimeInSeconds: Math.max(0, (f - W / 2 / pxPerFrame) / FPS),
      durationInSeconds: W / pxPerFrame / FPS,
      numberOfSamples: bars,
    });
  const offset = f - W / 2 / pxPerFrame < 0 ? (W / 2 / pxPerFrame - f) * pxPerFrame : 0;
  const allCues = SCENES.flatMap((s) => Object.entries(s.cues).map(([k, v]) => ({ k, v, hit: s.hits.includes(v) })));
  return (
    <AbsoluteFill style={{ background: '#111', color: '#eee', fontFamily: MONT }}>
      <div style={{ padding: 24, fontSize: 22, fontWeight: 600, lineHeight: 1.5 }}>
        <div style={{ fontFamily: BEBAS, fontSize: 58, color: '#FFC93C' }}>SYNC MONITOR</div>
        <div>t = {(f / FPS).toFixed(3)} s · frame {f}</div>
        <div>escena: <b style={{ color: '#fff' }}>{scene.id}</b> ({scene.bg}, {scene.transition})</div>
        <div>beat #{BEATS.indexOf(lastBeat)} · +{beatAge} f</div>
      </div>
      {/* indicador de beat */}
      <div style={{ position: 'absolute', left: W / 2 - 70, top: 250, width: 140, height: 140, borderRadius: '50%', background: beatAge < 3 ? '#FFC93C' : '#2a2a2a', boxShadow: beatAge < 3 ? '0 0 50px #FFC93C' : undefined, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: BEBAS, fontSize: 56, color: '#111' }}>
        BEAT
      </div>
      {isCut ? <div style={{ position: 'absolute', left: 40, top: 270, fontFamily: BEBAS, fontSize: 60, color: '#fff', background: '#E10600', padding: '0 14px' }}>CUT</div> : null}
      <div style={{ position: 'absolute', left: 0, top: 420, width: W, textAlign: 'center', fontSize: 26, minHeight: 40, color: '#FFC93C' }}>
        {cueNow.map(([k]) => k).join(' · ')}
      </div>
      {/* timeline con forma de onda */}
      <svg width={W} height={460} style={{ position: 'absolute', left: 0, top: 480 }}>
        <rect width={W} height={460} fill="#0b0b0b" />
        {wave?.map((w, i) => {
          const h = w.amplitude * 300;
          return <rect key={i} x={offset + i * (W / bars)} y={170 - h / 2} width={W / bars - 1} height={h} fill="#555" />;
        })}
        {BEATS.filter(visible).map((b) => (
          <line key={b} x1={xOf(b)} x2={xOf(b)} y1={20} y2={320} stroke="#FFC93C" strokeOpacity={0.5} strokeWidth={2} />
        ))}
        {SCENES.filter((s) => visible(s.start)).map((s) => (
          <g key={s.id}>
            <line x1={xOf(s.start)} x2={xOf(s.start)} y1={0} y2={360} stroke="#fff" strokeWidth={4} />
            <text x={xOf(s.start) + 6} y={352} fill="#fff" fontSize={20} fontFamily={MONT}>{s.id}</text>
          </g>
        ))}
        {allCues.filter((c) => visible(c.v)).map((c) => (
          <g key={c.k + c.v}>
            <circle cx={xOf(c.v)} cy={395} r={c.hit ? 11 : 7} fill={c.hit ? '#E10600' : '#FFC93C'} />
            <text x={xOf(c.v)} y={438} fill="#bbb" fontSize={17} textAnchor="middle">{c.k}</text>
          </g>
        ))}
        <line x1={W / 2} x2={W / 2} y1={0} y2={460} stroke="#E10600" strokeWidth={3} />
      </svg>
    </AbsoluteFill>
  );
};
