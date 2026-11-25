# Anuncio Black Friday · Prospectus — notas de edición

## Resultado (`output/`)
| Archivo | Qué es |
|---|---|
| `prospectus_bf_9x16.mp4` | Reels/Stories, 1080x1920, 30 fps, H.264 CRF 18 preset medium, AAC 320 kbps |
| `prospectus_bf_4x5.mp4` | Feed, 1080x1350, reencuadre propio (no recorte del 9:16) |
| `portada.jpg` | Fotograma del gancho |
| `subtitulos.srt` | Subtítulos con los tiempos del montaje |
| `antes_despues_10s.wav` | 10 s de voz original → 0,8 s de silencio → mismos 10 s procesados (igualados a -14 LUFS para comparar) |
| `hoja_contactos_clips.jpg` | Un fotograma por clip de las webs |

## Orden de las tomas (por lo que digo, transcrito con Whisper large-v3)
| Bloque | Toma | Lo que se dice |
|---|---|---|
| Gancho | `eb7c3ce3` (.mov HEVC 4K) | ¿Estás cansado de pagar cientos de miles de euros en inmobiliarias para vender sobre plano? |
| Oferta | `43493248` (h264 4K) | Esta semana el tour virtual de tu promoción te cuesta la mitad, solo para la primera promotora que firme. |
| Qué hacemos | `9ba76478` (h264 4K) | En Prospectus convertimos tu promoción en un tour virtual. Tu comprador entra en el piso antes de que exista, lo recorre desde el móvil y reserva. *(se corta "Lo veo bien" y se acorta la pausa antes de "Tu comprador")* |
| Cierre | `a54f3308` (.mov HEVC 4K) | Una sola plaza. Cuando alguien la coja, se acabó. Así que si tienes alguna promoción en venta, escríbenos. |

Diferencias con el guion: dices "**en** inmobiliarias", "entra en **el** piso", "**así que** si tienes **alguna** promoción" y "**escríbenos**". Los subtítulos dicen exactamente eso. Por coherencia, el botón final dice **ESCRÍBENOS YA** (el brief pedía "ESCRÍBEME YA"; se cambia en `scripts/plan.py`, variable `CTA`).

## Herramientas
- **ffmpeg 6.1**, **Python 3.13** (numpy, scipy, OpenCV, soundfile, pyloudnorm), **Node 22 + Playwright/Chromium**.
- **Transcripción**: faster-whisper con `large-v3` (int8, CPU), español, marcas por palabra. Los inicios de palabra se ajustan con la envolvente de energía de la voz limpia (`scripts/words.py`); hay una corrección manual documentada ("Tu" estaba fundido con "comprador").
- **Audio** (`scripts/build_audio.py`):
  - **Análisis de la sala** (`scripts/reverb_analysis.py`): la oficina vacía tiene mucha reverberación: **RT60 equivalente ≈ 1,0 s** y cola de solo −12,7 dB tras cada frase en la grabación original.
  - **Aislamiento y desreverberación** (`scripts/dereverb.py`): **WPE multicanal** (nara_wpe, 20 taps, 3 iteraciones) sobre el **estéreo original del iPhone** (2 micrófonos) → **DeepFilterNet 3** sin límite de atenuación y con **post-filtro** (`deep-filter -D -a 100 --pf`).

    | Cadena | Cola tras frase | RT60 equiv. | Inteligibilidad (Whisper) |
    |---|---|---|---|
    | Original | −12,7 dB | 0,99 s | 0,972 |
    | Versión anterior (DeepFilterNet −40 dB) | −33,9 dB | 0,28 s | 0,972 |
    | **Actual: WPE + DeepFilterNet + post-filtro** | **−48,2 dB** | **0,20 s** | 0,969 (texto idéntico en las 4 tomas, desfase 0 ms) |
    - Se probó **resemble-enhance** primero (como pedía el orden): el modo *enhance* alucinaba en CPU (Whisper oía frases que no existen, p. ej. "Gracias por ver este vídeo") → descartado; el modo *denoise* funcionaba pero hacía que Whisper confundiera "tour" con "course" → peor inteligibilidad que DeepFilterNet (confianza media 0,98). Se eligió DeepFilterNet.
  - Cadena: paso alto 80 Hz (24 dB/oct) → EQ −3 dB a 320 Hz (caja), +1 dB a 140 Hz, +3 dB a 3,6 kHz (presencia), +1,5 dB shelf 9,5 kHz → etapa de ganancia a −20 LUFS → de-esser → compresión 2,5:1 (≈3 dB de reducción) → limitador → loudnorm lineal en dos pasadas a **−14 LUFS / TP ≤ −1,5 dBTP**.
  - **Música**: generada por código (pad cálido + bajo + arpegio + percusión suave, 100 BPM, Am9–Fmaj7–Cmaj7–G6). Sin derechos de terceros. Queda **23 dB por debajo de la voz** con ducking (sidechain).
  - Whooshes suaves sintetizados en las transiciones whip/zoom.
- **Clips de las webs**:
  - Villa Aurea y Serra (visita 360) usan Photo Sphere Viewer: captura **fotograma a fotograma** (`scripts/capture_360.js`): en cada fotograma se fija yaw/pitch/zoom con una curva suave (como un arrastre lento) y se captura a 1080x1920 → movimiento perfectamente fluido, sin tirones aunque el render sea por software. Interfaz, flechas y cursor ocultos; se espera a la textura de máxima calidad (4096 px en Villa Aurea).
  - En Serra, jsDelivr está bloqueado en este entorno: se sirven las mismas versiones de three.js y Photo Sphere Viewer desde npm con `page.route`.
  - Fachada interactiva de Serra (elegir planta → vivienda "P2 B · DISPONIBLE"): grabada en tiempo real con Chromium en pantalla virtual (Xvfb) + `ffmpeg x11grab` a 30 fps, sin cursor ni menús (`scripts/capture_serra_fachada.js`).
  - Descenso con dron de Serra: es el vídeo vertical que la web usa como intro en móvil (1080x1936).
  - Villa Aurea: hora **atardecer** en todas las estancias; el plano aéreo pasa a **noche** (función "HORA" de la web).
- **Montaje** (`scripts/plan.py` → `work/plan.json`, `scripts/compose.py`): mis planos se decodifican del original 4K y se reencuadran con **seguimiento de cara** (`scripts/track_faces.py`, Haar de OpenCV + suavizado): en las tomas A, C y D te acercas a cámara, así que el zoom se calcula para mantener el tamaño de cara objetivo (como un travelling) y el encuadre te sigue suavemente; punch-in (escalado INTER_AREA desde 4K, nunca se amplía por encima de la resolución original), etalonaje por toma (`scripts/grade_params.py`): balance de blancos medido sobre la pared blanca (venía con dominante verde/cian), exposición corregida en lineal (C y D venían ~1 paso subexpuestas), hombro suave en altas, curva fílmica y +8 % de saturación con un punto cálido para la piel; después claridad (contraste local) y nitidez solo en luminancia y un grano muy fino para quitar el aspecto "plástico" del procesado del iPhone. El zoom se limita a 1,6× en las tomas comprimidas y 1,75× en las .mov para mantener siempre sobremuestreo desde 4K; desruido ligero (hqdn3d) antes de escalar.
- **Gráficos** (`scripts/overlay.html`), estilo del reel de referencia:
  - **Palabra grande detrás de la cabeza**: Inter Display SemiBold en minúsculas con una frase pequeña encima ("inmobiliarias?", "-50 %", el logo "Prospectus.", "1 plaza"). La cabeza la tapa en parte gracias a una **segmentación de persona fotograma a fotograma** (rembg `u2net_human_seg`, suavizado temporal, erosión de 2 px + difuminado contra el halo del pelo). La altura de la palabra se calcula midiendo dónde queda tu cabeza en cada rótulo (`scripts/head_tops.py`).
  - **Tarjetas de cristal**: subtítulos, cuenta atrás, rótulos del tour y panel de cierre con **desenfoque real del vídeo** debajo (compose.py desenfoca esa zona) y un tinte oscuro translúcido.
  - Un solo color de acento: **azul suave desaturado** (`#5A8BB5` sobre la pared blanca, `#9CC3E2` sobre fondos oscuros). Logo real en "En Prospectus" (grande, detrás de la cabeza) y en la tarjeta final.

## Decisiones
- **Duración**: 24,5 s (22,5 s de voz + 2 s de tarjeta final).
- **Zonas seguras 9:16**: todo lo importante entre y = 286 px y y = 1536 px (nada en el 14 % superior ni el 20 % inferior).
- **Rótulo de plazo** (arriba a la derecha): "⏳ hasta el 30 de noviembre", fijo (ya no depende del día de publicación), coherente con "acaba el lunes 30 a las 23:59" del cierre.
- Mientras hablo del tour, el tour ocupa toda la pantalla con mi voz en off (se probó un PiP mío en pequeño y se quitó porque restaba calidad).
- Serra: sus panorámicas 360 son de 1774 px (se ven blandas a 1080x1920), así que de Serra se usan el dron y la fachada interactiva, que sí son nítidos.
- Las transiciones son cortes; whip en la entrada a la piscina y al salón, zoom en la entrada al edificio real y fundido de "tu promoción" a "tour virtual".
- **4:5**: reencuadre propio: cara más arriba, titular y tarjeta arriba, cuenta atrás y rótulos abajo y clips del tour recortados algo por encima del centro.

## Cómo regenerarlo
```bash
cd anuncio-bf
# 0) requisitos: ffmpeg, python3 (pip install faster-whisper soundfile scipy opencv-python-headless pyloudnorm),
#    node + playwright (Chromium), xvfb; binario deep-filter en work/tools/
#    y en work/: npm i three@0.185.1 @photo-sphere-viewer/*@5.15.1 @fontsource/montserrat@5
# 1) transcripción
python3 scripts/transcribe.py large-v3          # desde work/
# 2) limpieza de voz
work/tools/deep-filter -D -a 40 -o work/audio/df_final work/audio/re_in/*.wav
# 3) clips
node scripts/capture_360.js scripts/shots.json work/frames_360        # + codificar a work/clips/*.mp4
xvfb-run -s "-screen 0 1080x2100x24" node scripts/capture_serra_fachada.js work/clips/s03_fachada_raw.mp4
# 4) plan, audio y vídeo
python3 scripts/words.py && python3 scripts/plan.py
python3 scripts/build_audio.py with_whoosh
node scripts/render_overlay.js work/plan.json 9x16 work/ovl_9x16 && python3 scripts/compose.py 9x16
node scripts/render_overlay.js work/plan.json 4x5 work/ovl_4x5  && python3 scripts/compose.py 4x5
python3 scripts/qc.py output/prospectus_bf_9x16.mp4
```
Los textos (CTA, fechas, color de acento) están en `scripts/plan.py`; los cortes, en `scripts/edl.py`.

## Efectos de sonido y transiciones (`sfx/`, `scripts/sfx.py`, `compose.py`)
Los efectos son del **Wyzowl SFX Kit** (licencia **CC0**, uso comercial sin atribución), sacados del pack que me pasaste (`github.com/juantoc7755-alt/sfx-pack-editores`). Los 10 que se usan están copiados en `sfx/` con su metadato (`sfx_meta.json`).
Cada sonido se coloca según su **punto de sincronía** del kit (el pico del whoosh en el centro del movimiento, el golpe en el fotograma exacto, la campana de la caja registradora cuando aparece el precio) y, si cae sobre una palabra, con la **reducción "bajo voz" que recomienda el kit**. Nivel general: el del kit (referencia: voz a −16 LUFS) +4 dB para dar más energía de reel. Los whooshes se panean izquierda↔derecha siguiendo el movimiento de cámara. Ningún efecto pisa el final de una frase.

| Momento | Transición de vídeo | Sonido (Wyzowl SFX Kit) |
|---|---|---|
| 0,0 s gancho | — | `cinematic-drum-big` |
| "cientos de miles" | destello suave + punch-in | `swish-medium` |
| → oferta | destello blanco + zoom | `whoosh-fast-medium` |
| aparece "-50 %" | sacudida de cámara | `money-register` + `boom-hit-medium` |
| piscina (ida / vuelta) | whip pan / whip pan inverso | `whoosh-fast-soft` L→R / R→L |
| "En Prospectus" | zoom de paso | `swish-medium` antes de la frase (sin pop: caía en mitad de la palabra) |
| edificio real | zoom con desenfoque | `whoosh-fast-soft` |
| → tour 360 / paso a noche | fundido | `shimmer-short-soft` ×2 |
| estancias | whip / whip inverso / zoom | `whoosh-fast-soft`, `swish-medium` |
| "y reserva" → "DISPONIBLE" | destello | `swish-medium` + `notification-success-soft` |
| "1 plaza" | zoom + sacudida | `swish-medium` + `boom-hit-medium` |
| panel de cierre | — | `pop-medium-in` |
| tarjeta final | golpe de zoom + sacudida | `swish-medium` + `sting-minimal-short` (sting de logo) + `cinematic-drum-big` |

## Revisión final (QC)
| Comprobación | 9:16 | 4:5 |
|---|---|---|
| Duración | 24,50 s | 24,50 s |
| Loudness integrado | −14,0 LUFS | −14,0 LUFS |
| True peak | −1,5 dBTP | −1,5 dBTP |
| Clics en cortes / en todo el archivo | ninguno | ninguno |
| Subtítulos vs. audio final (Whisper large-v3 sobre el mp4) | 98 % de coincidencia; la única diferencia es "sobreplano" (Whisper lo junta) | — |
| Sincronía de subtítulos | mediana 0 ms, p90 55 ms | — |

Fotogramas revisados: 0,5 s, oferta, mitad, cierre y tarjeta final, además de todas las transiciones. Se corrigió: espaciado entre palabras de los subtítulos, PiP eliminado, panel de cierre que rozaba la barbilla y encuadres que no seguían tu movimiento.

## Qué conviene que revises
1. **CTA**: "escríbenos ya" (lo que dices) frente a "ESCRÍBEME YA" (brief).
2. **Plazo**: arriba pone "hasta el 30 de noviembre" y en el cierre "acaba el lunes 30 a las 23:59". Si cambiáis la fecha, se cambia en `scripts/overlay.html` y `scripts/plan.py`.
3. **Música**: generada por código (discreta, −23 dB bajo la voz). Si preferís una pista de librería, se cambia `work/audio/music.wav` y se vuelve a ejecutar `build_audio.py`.
4. **Logo**: se usa el logo real que me pasaste, extraído con fondo transparente y en versión blanca con el punto morado (`input/brand/`, no versionado). Es un PNG de 618 px de ancho: si tienes el SVG, el logo de la tarjeta final quedará aún más nítido.
5. **Precio visible**: en el plano de "y reserva" sale la ficha real de Serra (Vivienda P2 B · 450.000 € · DISPONIBLE). Confirma que se puede enseñar.
6. **Tomas B y C** (oferta y "En Prospectus") me llegaron comprimidas (h264 a 5 Mbps, `_compressed_by_happyscribe`). Si me pasas los .mov originales del iPhone, esos planos ganarán bastante nitidez.
7. Escucha el antes/después (`antes_despues_10s.wav`) en auriculares: la reverberación de la sala baja mucho; si notas la voz algo "seca", se puede subir el límite de atenuación de DeepFilterNet (`-a 40` → `-a 30`).
