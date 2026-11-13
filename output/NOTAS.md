# Reel «Un piso en Madrid o un pueblo entero en Galicia» — notas de producción

## Estado de esta versión

- **Sin voz ni clips.** En la carpeta no había `input/voz.wav` ni `input/clips/*.mp4`, así que:
  - Los tiempos salen del guion exacto (sílabas por palabra, locución ajustada a ~38,9 s, con los silencios de 0,3 s antes de «Pero espera», «CERO euros» y «Pero hay trampa»). Están en `timings.json`.
  - Los planos de Google Earth se sustituyen por **maquetas 3D propias** (calle de Madrid, Candelago con el mar, A Barca junto al Miño) y **mapas estilizados**. En pantalla aparece «Recreación 3D ilustrativa».
  - `madrid_vs_pueblo_final.mp4` y `madrid_vs_pueblo_sin_voz.mp4` tienen hoy el mismo audio (música + efectos). Cuando grabes la voz, regenera con el comando de abajo y el «final» llevará la voz con la música en *ducking*.
- Formato: 1080×1920, 30 fps, H.264 High 4.2, AAC 48 kHz, -14 LUFS integrados, pico real ≤ -1 dBTP.

## Regenerar con otra voz (un solo comando)

1. Copia la locución a `input/voz.wav` (cualquier frecuencia de muestreo; la velocidad no se toca nunca).
2. (Opcional) Copia los clips a `input/clips/madrid.mp4`, `input/clips/candelago.mp4`, `input/clips/a_barca.mp4`.
3. Ejecuta, desde la raíz de la carpeta:

```bash
python3 reel/make.py
```

Hace todo: transcribe la voz palabra a palabra con faster-whisper (modelo `large-v3`; la primera vez lo descarga),
la alinea con el guion exacto, recalcula todos los tiempos (cada efecto visual y sonoro está anclado a una palabra),
renderiza las 6 escenas en paralelo, las une con `ffmpeg concat`, etalona (sombras frías, luces cálidas, viñeta, grano),
mezcla a -14 LUFS y regenera vídeos, portada, `subtitulos.srt` y `timings.json`. La duración la marca la voz.

Otras opciones:

```bash
python3 reel/make.py --voz ruta/otra_toma.wav      # otra toma
python3 reel/make.py --timings output/timings.json # reutiliza/corrige a mano los tiempos sin volver a transcribir
python3 reel/make.py --preview                     # render rápido para revisar (sin supermuestreo)
```

Instalación (una vez): `ffmpeg` en el sistema y `pip install -r reel/requirements.txt`
(en Linux, skia necesita `libegl1 libgl1`). Si prefieres WhisperX, se usa automáticamente cuando faster-whisper no está instalado.

Con clips reales, cada escena usa el clip en lugar de la maqueta: se recorta un 10 % por cada borde para quitar la interfaz,
se reencuadra a 9:16 y se rotula «Imágenes: Google Earth» mientras se ve.

## Estructura del montaje (tiempos de esta versión)

| Escena | Tramo | Qué pasa |
|---|---|---|
| 1 Gancho | 0,0–5,6 s | Calle de Madrid. Fotograma 0: cota naranja + planta azul de 60 m² a escala real sobre la calzada, «390.000 €» con golpe grave. Whip pan a Galicia en «En Galicia», «UN PUEBLO ENTERO» en verde; la planta queda en la esquina. |
| 2 Primer impacto | 5,6–11,9 s | Candelago con el mar, cota naranja alrededor de la aldea, contador a 150.000 € con 200.000 € tachado. La planta vuela al centro y encoge de 60 a 23 m². |
| 3 Escalada | 11,9–18,3 s | «PERO ESPERA» con parada seca. Mapa de Galicia, se enciende Lugo, dos casas de piedra, 59.000 €. La planta encoge a 9 m² (cuadrado con bañera). |
| 4 Efecto wow | 18,3–28,4 s | Pregunta gigante con *riser*, bajada desde el cielo a A Barca, 12 casas que se encienden. «0 €» con flash, temblor e impacto; la planta desaparece con un *pop*. Disco rayado: el 0 € se agrieta, «CONCESIÓN DE 50 AÑOS» y «HASTA 3 M€ PARA PONERLA EN MARCHA». |
| 5 Contraste | 28,4–34,4 s | Mapa de España, puntos verdes sobre todo en Galicia, Asturias y Castilla y León, «≈ 3.000 PUEBLOS ABANDONADOS». Zoom a Madrid: la planta vuelve a 60 m², «CASI 400.000 €». |
| 6 CTA | 34,4–41,2 s | Pantalla partida (Madrid arriba / Candelago abajo), botones «MADRID» y «PUEBLO», «¿QUÉ ELIGES?», firma «ALEIX JIMÉNEZ» en el último segundo. |

## Datos y cálculos (solo cifras del encargo)

| Cifra en pantalla | Fuente rotulada | Cálculo |
|---|---|---|
| 390.000 € / casi 400.000 € (60 m² en Madrid) | idealista, precio medio de Madrid, ago. 2026 | 6.471 €/m² × 60 m² = 388.260 € ≈ 388.000 € |
| 150.000 € (antes 200.000 €), Candelago | anuncio en idealista; prensa, feb. 2026 | 150.000 ÷ 6.471 ≈ 23,2 m² → «23 m²» |
| 59.000 €, aldea de Lugo con dos casas de piedra | Xataka, sept. 2026 | 59.000 ÷ 6.471 ≈ 9,1 m² → «9 m²» |
| 0 €, A Barca, 12 casas, concesión 50 años, hasta 3 M€ | anuncio en Aldeas Abandonadas; Ayto. de Cortegada (prensa, oct. 2026) | — |
| ≈ 3.000 pueblos abandonados | Xataka, sept. 2026 | los puntos del mapa son ilustrativos (rotulado), no uno por pueblo |

La aldea de Lugo se señala por provincia (no hay ubicación exacta en los datos), y las maquetas 3D no reproducen los pueblos reales: por eso el rótulo «Recreación 3D ilustrativa».

## Revisión de fotogramas clave

Se exportan 10 fotogramas a `reel/build/fotogramas_clave/` (con `hoja_contacto.png`) en cada render.
Comprobado en esta versión: legibilidad a tamaño móvil, nada importante en los 250 px superiores ni en los 380 px inferiores
ni a menos de 120 px del borde derecho, subtítulos de 76 px (máx. 2 líneas, palabra activa en naranja, con contorno),
y cada cifra con su fuente en IBM Plex Mono de 27 px.

## Licencias

Detalle y textos en `licencias/` (`licencias/LEEME.md`):
Inter Display e IBM Plex Mono (SIL OFL 1.1), mapas es-atlas (MIT; datos © IGN, atribuidos en pantalla) y world-atlas (ISC; Natural Earth, dominio público).
Música y efectos: **creación propia**, sintetizados por código en `reel/audio.py` (sin muestras de terceros).
No se han usado fotos de anuncios ni de prensa.

## Archivos

- `madrid_vs_pueblo_final.mp4`, `madrid_vs_pueblo_sin_voz.mp4`, `portada.jpg`
- `subtitulos.srt`, `timings.json`, `comentario_fijado.txt`, este `NOTAS.md`
- Código: `reel/` (`make.py` orquesta; `timing.py` guion y sincronía; `scenes.py` montaje; `engine3d.py` maquetas; `maps.py`; `audio.py`; `subs.py`)
