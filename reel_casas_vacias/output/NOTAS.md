# LA MAQUETA: notas de producción

Reel 1080×1920 · 30 fps · H.264 · 34 s · −14 LUFS. España convertida en una maqueta de arquitectura: piezas de madera clara por provincia, ~14.700 casitas blancas cuya densidad sigue la población, casas vacías de vidrio y parcelas que faltan dibujadas a lápiz rojo.

## Regenerar con otra voz (un solo comando)

1. Copia la narración en `input/voz.wav` (mono o estéreo, cualquier frecuencia de muestreo). No se cambia su velocidad.
2. Ejecuta:

```bash
./make.sh
```

Qué hace `make.sh`:

| Paso | Script | Resultado |
|---|---|---|
| 1 | `src/timing.py` | Alinea la voz palabra a palabra con faster-whisper (modelo `small`; otro con `WHISPER_MODEL=medium`) contra el guion exacto y escribe `output/timings.json`. Sin voz, usa el ritmo estimado del guion. |
| 2 | `src/render_all.sh` | Si los tiempos han cambiado, borra los renders y vuelve a renderizar los 8 planos en Blender (Cycles, 720×1280, 10 muestras + OpenImageDenoise). Cada plano se renderiza por separado y se puede relanzar suelto: `src/render_all.sh D_ourense`. |
| 3 | `src/post.py` | Tilt-shift por profundidad, gradación, reescalado a 1080×1920, aberración cromática, viñeta, grano, polvo en los pueblos, subtítulos palabra a palabra, fuente fija y CTA. |
| 4 | `src/audio.py` | Música y efectos sintetizados y colocados en los eventos de cada plano. Ducking de la música bajo la voz y mezcla a −14 LUFS (pico real ≤ −1 dBTP). |
| 5 | `src/deliver.py` | `casas_vacias_final.mp4`, `casas_vacias_sin_voz.mp4`, `subtitulos.srt`, `portada.jpg` y `comentario_fijado.txt`. |

Todos los eventos (cortes, caídas de cifras, golpes, lápiz, focos, cúter) están anclados a palabras del guion, así que se reajustan solos con la voz nueva.

Primera instalación: `./setup.sh` (Python 3.11 + `bpy` 5.0.1 desde PyPI, numpy, scipy, shapely, OpenEXR, OpenCV, pyloudnorm, soundfile y faster-whisper). Tiempo de render en 4 núcleos de CPU sin GPU: unas 5 h. Con GPU (cambia `cy.device` a `'GPU'` en `src/maqueta.py`) son minutos.

> Sin `input/voz.wav`, `casas_vacias_final.mp4` y `casas_vacias_sin_voz.mp4` son el mismo montaje (música + efectos + subtítulos) con el ritmo estimado del guion.

## Planos (`output/timings.json`)

| Plano | Tiempo | Qué pasa |
|---|---|---|
| A_hook | 0,0–2,5 | Calle de casitas en Arévalo. La ola vuelve de vidrio a las vacías («España…»). Caen «3.800.000» y aparece «VACÍAS». |
| B_contraste | 2,5–5,0 | Periferia de Madrid: el lápiz dibuja las parcelas. «750.000» en rojo se levanta de la madera, con «FALTAN». |
| C_pregunta | 5,0–7,5 | 0,4 s de silencio. Grúa rápida a cenital de toda la maqueta y cae «¿CÓMO?». |
| D_ourense | 7,5–12,0 | Picado sobre Galicia. Foco en Ourense, la pieza se eleva, cota roja a lápiz y «+40 %». El vidrio brilla en frío. |
| E_provincias | 12,0–17,0 | Madrid, Barcelona, Valencia, Alicante, Murcia y Málaga se encienden una a una con su número de cartón, y aparece «+50 % DEL DÉFICIT». |
| F_pueblos | 17,0–23,0 | Pueblos de Zamora casi todos de vidrio, con iglesia y polvo en la luz. «45 %» y «EN PUEBLOS DE MENOS DE 10.000 HAB.». |
| G_sintesis | 23,0–28,0 | Cenital con time-lapse de luz. Las líneas rojas salen del interior hacia las ciudades y se cortan a mitad de camino, con golpe sordo y silencio. |
| H_dilema | 28,0–34,0 | Un cúter parte la maqueta. A la izquierda, una grúa baja un edificio a la parcela roja (CONSTRUIR). A la derecha, la sombra de una mano devuelve el blanco a una casa de vidrio (RECUPERAR). Después, el CTA. Los últimos 0,8 s son el plano 0 para el bucle. |

## Datos y maqueta

Las cifras de pantalla son las verificadas del encargo:

- INE, Censo 2021: 3,8 M de viviendas vacías (14,4 %); Ourense, más del 40 %; el 45 % en municipios de menos de 10.000 habitantes.
- Banco de España, Informe Anual 2025: déficit de unas 750.000 viviendas, el 52,5 % en 6 provincias.

Cómo se hizo la maqueta (`src/prep.py`):

- **Contornos:** IGN, vía `es-atlas`. Canarias va en un recuadro al suroeste.
- **Casitas:** cada una equivale a unas 1.500 viviendas del Censo 2021. Se reparten por provincia según la población de 2021 y se agrupan en ~170 ciudades con bloques altos en el centro, más pueblos en los municipios restantes.
- **Casas de vidrio:** la tasa de vacío por provincia es una aproximación visual coherente con los datos. Da un 13 % nacional, ~44 % en Ourense, ~6 % en Madrid, y es mayor en el interior y el noroeste.
- **Parcelas rojas:** cada una equivale a unas 2.000 viviendas del déficit. El 53 % está en las 6 provincias, en la periferia de sus ciudades.
- **Escenas puntuales:** en la calle del plano 0, los pueblos de Zamora del plano F y la casa que se recupera en H, el reparto es ilustrativo.

## Comprobaciones hechas

- Fotogramas clave exportados con el brillo al 60 %, simulando un móvil a bajo brillo (`output/control_brillo60/`). Ahí se comprobó que las cifras y los subtítulos se leen.
- Zonas seguras:
  - los subtítulos van centrados en y≈1350, por encima de los 380 px inferiores;
  - la fuente queda en y≈1505–1530;
  - las cifras van entre y≈450 y 1100;
  - nada importante en los 250 px superiores ni a menos de 120 px del borde derecho.
- Sonoridad integrada de −14 LUFS medida con pyloudnorm (ITU-R BS.1770-4).

## Licencias

Ver `licencias/LEEME.md`. La música y los efectos son originales (síntesis por código, CC0). Las tipografías tienen licencia OFL y los contornos son del IGN (CC BY 4.0).
