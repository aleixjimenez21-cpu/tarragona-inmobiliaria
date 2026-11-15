# The Token Hunt — vídeo motivacional vertical (Remotion)

1080×1920 · 30 fps · H.264 · 32,5 s · todo el arte es original (SVG/código), sin assets de Fortnite/Epic.

## Uso rápido

```bash
cd token-hunt
npm install
pip install librosa soundfile
# (opcional) copia aquí referencia.mp4 y/o musica.mp3
npm run render         # pipeline completo
npm run studio         # previsualizar en Remotion Studio
```

`scripts/render_all.sh` hace, en orden:

1. **Audio** (`prepare_audio.sh`) → `public/audio.mp3`, usando `musica.mp3`, si no la pista de `referencia.mp4`, y si no la pista provisional `assets/musica_provisional.mp3`.
2. **Beats** (`analyze_beats.py`, librosa) → `beats.json`: beats, rejilla regular ajustada (tempo + fase corregida al ataque real del golpe), corcheas, onsets y onsets fuertes.
3. **Timeline** (`build_timeline.mjs`) → `src/timeline.ts` (generado). Lee `scripts/timeline.spec.json` (los tiempos del guion) y mueve cada corte y cada palabra al beat más cercano (o a la corchea si `sub: true`). El informe queda en `out/timeline_report.md`.
4. **Cortes del original** (`detect_cuts.sh`, `ffmpeg select='gt(scene,0.25)',showinfo`) → `out/cortes_referencia.txt`.
5. **Render** → `out/video.mp4`, `out/video_con_audio.mp4` y `out/video_sin_audio.mp4`.
6. **Verificación**: cortes detectados en el vídeo nuevo frente a beats/guion/original (`out/cuts_report.md`) y `out/comparacion.mp4` (original | nuevo | sync monitor con forma de onda, beats y cues).

> Si cambias la música, basta con volver a ejecutar `npm run render`: todo el timeline se recalcula desde los beats.
> Si el original no dura 32,5 s de contenido, cambia `contentEnd` en `scripts/timeline.spec.json`.

## Estructura

| Ruta | Qué es |
|---|---|
| `src/timeline.ts` | Tiempos en frames (GENERADO desde `beats.json`) |
| `src/scenes/S01…S22*.tsx` | Una escena por archivo (también registradas como composiciones `Escenas/Sxx-id`) |
| `src/components/Coin.tsx` | "THE TOKEN": estrella de 4 puntas, anillo con muescas, barrido especular cada 2 s |
| `src/components/Chest.tsx` | Cofre con remaches y calavera propia; variante gris "apagada" |
| `src/components/Stickman.tsx` | Monigote con esqueleto y poses animadas (sentado tecleando, brazos arriba, subir escaleras, empujar) |
| `src/components/SceneShell.tsx` | Fondo, viñeta, zoom-punch + shake, transiciones (cut, flash 2 f, glitch RGB, whip-pan) |
| `src/components/Fx.tsx` | Partículas, god rays, foco, onda expansiva, grano, viñeta |
| `src/SyncMonitor.tsx` | Panel de verificación para la comparación |
| `scripts/synth_placeholder_music.py` | Genera la pista provisional original (120 BPM) |

## Zonas seguras

Nada importante en los 250 px inferiores ni en los 180 px de la derecha: todo el texto vive en la caja `x 60–900, y 170–1670` (`src/theme.ts`), centrada en x = 480.

## Bucle

La última escena funde a negro y recoloca la moneda en la posición del primer frame; el último frame es el frame 0 (diferencia media medida ≈ 4/255, solo el grano).
