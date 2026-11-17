# Test a ciegas 29-N · «La urna» — notas de producción

Reel 1080×1920, 30 fps, H.264 + AAC, mezcla a −14 LUFS (pico ≤ −1 dBTP).
Todo el material visual y sonoro está generado por código en este proyecto (escena 3D, texturas de papel y madera, sello de lacre, polvo, diseño sonoro). No hay logos, colores corporativos ni imágenes de partidos o de políticos.

## Regenerar con otra voz (un solo comando)

```bash
cd reel-29n
cp /ruta/a/tu/narracion.wav input/voz.wav
python3 tools/build.py            # o: python3 tools/build.py --voz /ruta/a/otra.wav
```

Qué hace `build.py`:

1. `tools/timings.py`: transcribe la voz con **faster-whisper** (tiempos palabra a palabra) y la alinea con el guion exacto. Si faster-whisper o su modelo no están disponibles (sin internet, por ejemplo), usa un **alineador por silencios** que no necesita modelos: busca las 12 pausas que separan las 13 frases del guion. Probado con una voz de prueba: error máximo de 14 ms.
2. Corta la voz en 13 clips (intro, 5 propuestas, pregunta, «y ahora mira de quién es» y 5 revelaciones) y los coloca en sus bloques. **La voz nunca cambia de velocidad**: solo se añaden silencios entre frases.
3. `tools/audio.py`: sintetiza el dron y los efectos, aplica *ducking* del dron bajo la voz y normaliza a −14 LUFS.
4. `tools/render.js`: renderiza las 6 escenas en Chromium sin GPU (Three.js + posprocesado propio), cada una a su `.mp4` en `build/scenes/`, y las une con `ffmpeg concat`.
5. Exporta `test_29N_final.mp4` (con voz), `test_29N_sin_voz.mp4`, `subtitulos.srt`, `timings.json` y `portada.jpg`.

Requisitos: Node 18+ con Playwright y Chromium, Python 3 con `numpy scipy soundfile pyloudnorm` (y opcionalmente `faster-whisper`), y `ffmpeg`. Las dependencias JS se instalan con `npm install` dentro de `reel-29n/`.
El render completo tarda alrededor de una hora en un portátil de 4 núcleos sin GPU (≈3 s por fotograma). Con voz nueva hay que renderizar todo, porque cambian los tiempos.

**Con tarjeta gráfica (recomendado en tu PC):** `RENDER_GPU=1 python3 tools/build.py` (en Windows PowerShell: `$env:RENDER_GPU=1; python tools/build.py`). Usa la GPU en lugar de la emulación por software; el render baja de ~6 s a una fracción de segundo por fotograma. Si tu Chrome sin ventana no detecta la GPU, añade `RENDER_HEADLESS=0` para que abra una ventana durante el render.

Atajos:

- `python3 tools/build.py --solo-audio`: rehace la mezcla y el montaje sin volver a renderizar la imagen (para retocar sonido).
- `python3 tools/build.py --escenas s3`: re-renderiza solo esa escena (s1…s6) y vuelve a montar.
- `node tools/render.js stills 10.5 45`: exporta fotogramas sueltos a `build/stills/` para revisar.

## Duración y neutralidad

- Sin `input/voz.wav` el vídeo se monta con un ritmo sintético del guion (≈7 sílabas/s) y dura **51,8 s**. Con tu voz, la duración la marca la voz.
- **Cada propuesta dura lo que dura su frase** más el mismo margen antes (0,3 s) y después (0,6 s). Así las cortas no se hacen largas. Con el ritmo sintético salen 3,8 s · 5,0 s · 7,0 s · 4,9 s · 3,6 s. Esto sustituye la regla inicial de «mismo tiempo en pantalla», que obligaba a que las cinco durasen lo que la más larga.
- Todo lo demás es **idéntico** para los cinco números: encuadre, luz, movimiento de cámara, deslizamiento de la papeleta, momento en que entra la voz, velocidad de tecleo (32 caracteres/s, el mismo patrón de sonido) y barrido de luz entre propuestas.
- Las 5 revelaciones sí duran exactamente lo mismo, con el golpe en el mismo instante de cada bloque.
- Los sobres están dispuestos en pentágono alrededor de la urna, a la misma distancia del foco cenital: reciben exactamente la misma luz. La cámara gira 72° para pasar de uno a otro, así que cada sobre se ve con el mismo encuadre. En las revelaciones la urna queda fuera de cuadro para que el fondo también sea igual.
- Los nombres de los partidos van en la misma tipografía (Courier Prime Bold), el mismo tamaño y la misma tinta negra. El rojo lacre (#B3261E) solo aparece en el sello «29-N» del arranque.
- En los subtítulos, la palabra que se está diciendo va en ámbar. Esto se aplica igual a todas las palabras y a todos los partidos.

## Cambiar el texto de una propuesta

Si algún partido publica su programa con cambios:

1. Edita la frase en `tools/timings.py`, lista `CLIPS` (por ejemplo, `("p3", "Tres: …")`). La papeleta y los subtítulos se generan desde ahí. Las revelaciones están en `("r1", "Uno, Vox.")`, etc.
2. Graba de nuevo la voz con el guion actualizado y ejecuta `python3 tools/build.py`.
3. Actualiza la línea de fuente si cambia la fecha: búscala en `src/main.js` (función `sourceLine`), y también `output/comentario_fijado.txt`.

La papeleta admite unas 7 líneas de 15 caracteres; si un texto nuevo fuera más largo, reduce el tamaño de letra en `prepareTexts()` (`src/main.js`). Ese cambio se aplica igual a las cinco papeletas.

## Estructura

```
reel-29n/
  input/            voz.wav (opcional)
  src/              escena 3D, posprocesado y rótulos (index.html, main.js)
  tools/            timings.py, audio.py, render.js, build.py
  build/            intermedios (escenas .mp4, audio, fotogramas de revisión)
  output/           entregables
  licencias/        licencias de las tipografías y de three.js
```

## Licencias usadas

| Recurso | Uso | Licencia |
|---|---|---|
| IBM Plex Mono | línea de fuente, cabecera de papeleta | SIL Open Font License 1.1 (`licencias/OFL_IBM-Plex-Mono.txt`) |
| Courier Prime | números, papeletas, nombres en los sobres | SIL OFL 1.1 (`licencias/OFL_Courier-Prime.txt`) |
| Fraunces | títulos grandes y sello «29-N» | SIL OFL 1.1 (`licencias/OFL_Fraunces.txt`) |
| Inter Display SemiBold | subtítulos y firma | SIL OFL 1.1 (`licencias/OFL_Inter-Display.txt`) |
| three.js | motor 3D | MIT (`licencias/MIT_three.js.txt`) |
| Sonido (dron, sello, papel, tecleo, reloj, golpes) | sintetizado en `tools/audio.py` | obra propia, sin muestras de terceros |
| Texturas (papel, madera, cera, persiana) | generadas por código en `src/main.js` | obra propia |

## Datos para el comentario fijado

Brains Real Estate News (26 de octubre de 2026; posiciones a 16 de octubre, salvo el programa del PP, publicado después):
1. Vox: IVA del 0 % en la compra de la primera vivienda.
2. PSOE: préstamos ICO sin intereses de hasta 50.000 € para la entrada de la primera vivienda.
3. PP: objetivo de un millón de viviendas; silencio administrativo positivo para las licencias de obra a los 90 días.
4. Podemos: rebajas legales del alquiler para que ningún hogar destine más del 30 % de sus ingresos.
5. Sumar (hoy dentro de Frente Amplio): prohibición de que empresas y fondos compren viviendas.

Texto listo para pegar en `comentario_fijado.txt`.
