# Reel «Un piso en Madrid o un pueblo entero en Galicia»: notas de producción

## Esta versión

- **Voz:** `input/voz.mp3` (63,8 s en bruto) editada automáticamente a **44,6 s**. Vídeo final: **46,8 s**.
  - Tomas repetidas: «Y ponerla en marcha puede costar millones» estaba grabada 3 veces; se usa la última.
  - Se quitan los silencios muertos (3,9 s al inicio, huecos de 2–3 s) y las pausas internas largas se dejan en ≤ 0,17 s.
  - Pausas dramáticas añadidas de ~0,36–0,40 s antes de «Pero espera», «CERO euros» y «Pero hay una trampa». En la toma original «por cero» iba seguido; el corte se hace en el silencio real entre las dos palabras.
  - **La velocidad de la voz no se toca:** solo se cortan silencios y tomas.
  - Realce de voz: filtro de graves, reducción de ruido, menos «barro» (200–420 Hz), más presencia (3,2 kHz) y aire, de-esser, compresión y limitador.
  - Comprobación: la voz editada se vuelve a transcribir y sale el guion completo y en orden. Además, todos los cortes caen en silencio.
- **Subtítulos:** siguen el guion exacto, salvo «Pero hay **una** trampa», que es lo que dices en la grabación.
- **Imagen:**
  - Madrid: maqueta 3D propia.
  - Candelago y A Barca: tus capturas de Google Earth, giradas a vertical, sin los rótulos de Google y con movimiento de cámara. En pantalla se rotula «Imágenes: Google Earth».
  - En A Barca no se marcan casas concretas (no se sabe cuál es exactamente cada una): solo el rótulo del lugar y el contador de 12 casas.
- **Gancho rehecho:**
  1. Acelerón de cámara por la calle de Madrid, con «390.000 €» ya en el fotograma 0.
  2. Barrido al mapa de España.
  3. Vuelo trazado Madrid → Candelago.
  4. Zoom de transición a la imagen real y golpe «UN PUEBLO ENTERO».
  5. Desdoble de color (RGB) en los golpes fuertes.
- **Formato:** 1080×1920, 30 fps, H.264 High. Final: −14,1 LUFS, pico real −1,7 dBTP. Sin voz: −14,2 LUFS.
  - En la versión con voz, la música va unos 9 dB por debajo de la voz y los efectos unos 10 dB.

## Regenerar (un solo comando)

```bash
python3 reel/make.py
```

Ese comando:
1. Coge `input/voz.(wav|mp3|m4a…)` y la edita (elige tomas, quita silencios, mete las pausas y la limpia).
2. La sincroniza palabra a palabra con faster-whisper.
3. Renderiza las 6 escenas en paralelo y las une con `ffmpeg concat`.
4. Etalona, mezcla a −14 LUFS y regenera los vídeos, la portada, `subtitulos.srt` y `timings.json`.

Opciones:

```bash
python3 reel/make.py --voz otra_toma.mp3          # otra locución
python3 reel/make.py --modelo large-v3             # modelo de Whisper (por defecto "small"; acepta una carpeta)
python3 reel/make.py --sin-edicion                # usa la voz tal cual, sin cortar tomas ni silencios
python3 reel/make.py --timings output/timings.json  # reutiliza tiempos (sin volver a transcribir)
python3 reel/make.py --preview                    # render rápido para revisar
```

Imágenes de Google Earth en `input/clips/` con los nombres `madrid`, `candelago` y `a_barca`. Valen tres formatos:
- `.mp4`.
- El `.zip` de fotogramas de Google Earth Studio.
- Una captura fija (`.jpg`, `.png` o `.webp`). Puede llevar un `.json` al lado con `girar`, `ancla` y `tapar` (zonas de rótulos a borrar); ver `reel/stills.py`.

Instalación: `ffmpeg` y `pip install -r reel/requirements.txt` (más `opencv-python-headless` para borrar rótulos). En Linux, skia necesita `libegl1 libgl1`.

## Datos y cálculos (solo cifras del encargo)

| Cifra en pantalla | Fuente rotulada | Cálculo |
|---|---|---|
| 390.000 € / casi 400.000 € (60 m² en Madrid) | idealista, precio medio de Madrid, ago. 2026 | 6.471 €/m² × 60 m² = 388.260 € ≈ 388.000 € |
| 150.000 € (antes 200.000 €), Candelago | anuncio en idealista; prensa, feb. 2026 | 150.000 ÷ 6.471 ≈ 23,2 m² → «23 m²» |
| 59.000 €, aldea de Lugo con dos casas de piedra | Xataka, sept. 2026 | 59.000 ÷ 6.471 ≈ 9,1 m² → «9 m²» |
| 0 €, A Barca, 12 casas, concesión de 50 años, hasta 3 M€ | anuncio en Aldeas Abandonadas; Ayto. de Cortegada (prensa, oct. 2026) | — |
| ≈ 3.000 pueblos abandonados | Xataka, sept. 2026 | Los puntos del mapa son ilustrativos (rotulado) |

- Las coordenadas de Candelago para el vuelo del mapa salen de tu captura de Google Earth (43°16'15,6"N 8°57'43,6"W).
- La aldea de Lugo se señala por provincia.

## Revisión

En cada render se exportan 10 fotogramas clave a `reel/build/fotogramas_clave/` (con `hoja_contacto.png`).

Comprobado en esta versión:
- Legibilidad en móvil.
- Zonas seguras: nada importante en los 250 px superiores, en los 380 px inferiores ni a menos de 120 px del borde derecho.
- Subtítulos de 76 px, con un máximo de 2 líneas y la palabra activa en naranja.
- Cada cifra con su fuente en IBM Plex Mono de 27 px.

## Licencias

Detalle en `licencias/LEEME.md`:
- Tipografías: Inter Display e IBM Plex Mono (OFL).
- Mapas: es-atlas (© IGN) y Natural Earth.
- Capturas de Google Earth: con atribución en pantalla.
- Música y efectos: sintetizados por código (creación propia).
- Whisper: solo para sincronizar la voz.
