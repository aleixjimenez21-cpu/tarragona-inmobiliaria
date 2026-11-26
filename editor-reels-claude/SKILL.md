---
name: editor-reels-claude
description: Edita anuncios y reels verticales (Instagram Reels, Stories, TikTok, Shorts) de una persona hablando a cámara a partir de las tomas en bruto del móvil, con acabado profesional - ordena las tomas por lo que se dice, quita silencios y muletillas, limpia la voz (quita eco de la sala y ruido, EQ, -14 LUFS), etalona y reencuadra siguiendo la cara, pone la palabra grande detrás de la cabeza, subtítulos en tarjetas de cristal, clips de apoyo a pantalla completa, transiciones de reel (whip pan, zoom, destello, sacudida) y efectos de sonido sincronizados (pack CC0 incluido), y exporta 9:16 y 4:5 con portada y SRT. Úsala siempre que alguien quiera editar, montar o mejorar un vídeo hablado a cámara, un anuncio para Meta/Instagram/TikTok, "edita mis tomas", "hazme un reel", "mejora la voz", "ponle subtítulos y efectos", "que se vea profesional" o pase vídeos grabados con el móvil para convertirlos en un anuncio, aunque no diga "reel".
---

# Editor de reels y anuncios a cámara

Convierte 2-6 tomas grabadas con el móvil (una persona hablando a cámara) en un anuncio vertical de ≤30 s con
aspecto profesional. Es el flujo que salió de editar anuncios reales y de las correcciones del cliente; las
decisiones de estilo y los errores que ya se cometieron están explicados para no repetirlos.

Todos los scripts están en `scripts/` de esta skill y **se ejecutan desde la carpeta del proyecto**:
`python3 <skill>/scripts/x.py`. El proyecto tiene `edl.py` (tomas y cortes), `plan.py` (montaje),
`input/` (tomas, `brand/` logo, `broll/` clips), `work/` y `output/`.

## Antes de empezar

1. **Entorno**: ejecuta `bash <skill>/scripts/setup.sh` (pip, Playwright, binario DeepFilterNet). Si algo falla
   por red o falta una fuente, lee `references/entorno.md` (hosts que hay que permitir, modelos, Windows/macOS).
2. **Material**: pide las tomas ORIGINALES del móvil (.mov/.mp4 4K). Las versiones "comprimidas" por webs o por
   WhatsApp se ven blandas; si pesan mucho, que las suban a Google Drive/Dropbox y pasen el enlace
   (`references/entorno.md` → descargar de Drive). Pide también el logo (PNG) y, si los hay, clips de apoyo.
3. **Brief**: qué se anuncia, oferta, fecha límite, llamada a la acción. Si el usuario pasa un reel de referencia
   y no puedes abrirlo (Instagram pide login), pide capturas de pantalla.

## Flujo

```
new_project.py → prep_audio.py → transcribe.py → (ordenar tomas) edl.py → cut_finder.py → words.py
→ track_faces.py + grade_params.py → (clips) prep_broll.py / capture_360.js → prep_logo.py
→ plan.py → build_audio.py → head_tops.py → render_overlay.js + compose.py --test (revisar) → render_all.sh → QC
```

### 1. Proyecto, voz y transcripción
```bash
python3 <skill>/scripts/new_project.py proyecto input1.mov input2.mov ...   # copia plantillas y tomas
cd proyecto
# rellena TAKES en edl.py con los archivos (letras A, B, C… en cualquier orden por ahora)
python3 <skill>/scripts/prep_audio.py        # extrae audio, WPE + DeepFilterNet (voz sin eco)
python3 <skill>/scripts/transcribe.py        # Whisper large-v3 con tiempos por palabra
```
**Ordena las tomas por lo que se dice**, no por el nombre del archivo: gancho → oferta/problema → qué hacemos /
cómo → cierre con llamada a la acción. Reasigna las letras en `edl.py` (A = gancho, B, C, D…). Si una toma tiene
una frase que sobra ("lo veo bien", repeticiones), se deja fuera con los cortes.

### 2. Cortes
`python3 <skill>/scripts/cut_finder.py` muestra palabras, inicio/fin real de la voz y pausas de cada toma.
Escribe `SEGMENTS` en `edl.py`: entra ~0,04 s antes de la voz y sal ~0,08 s después; recorta pausas internas
>0,2 s partiendo la toma en dos tramos (deja ~0,05-0,1 s). Objetivo: ≤30 s en total con 2 s de tarjeta final.
Luego `python3 <skill>/scripts/words.py`: pasa las palabras a la línea de tiempo final. **Revisa la salida**:
si una palabra sale duplicada, desaparece o empieza en un silencio, corrige con `WORD_OVERRIDES` en `edl.py`
mirando la envolvente (`cut_finder.py --detalle <toma> <ini> <fin>`). Pasa casi siempre con la primera palabra de
una toma y con las palabras pegadas a una pausa recortada. Si Whisper oye mal una palabra ("hobby" por "móvil",
"contacta a nosotros" por "contáctanos"), compruébalo con una segunda transcripción con `VOCAB` y corrígela con
`WORD_TEXT` en `edl.py` ("" borra una palabra, para juntar dos en una).

### 3. Cara y color
```bash
python3 <skill>/scripts/track_faces.py     # seguimiento de cara (la gente se acerca a cámara mientras habla)
python3 <skill>/scripts/grade_params.py    # balance de blancos en la pared clara + exposición
```
Si una toma no tiene pared clara detrás (mesa, pared de madera), ponla en `SKIN_REF` de `edl.py`: se calibra
por tono de piel. Revisa que ninguna exposición salga disparatada (>4) y que el seguimiento no salte.

### 4. Clips de apoyo, logo
- Clips propios en `input/broll/` → `python3 <skill>/scripts/prep_broll.py` (1080x1920, 30 fps + hoja de contactos).
- Captura de una web/tour 360: `references/broll.md` (captura fotograma a fotograma, fluida y sin interfaz).
- Imágenes fijas (planos, renders, capturas, PDF) → `python3 <skill>/scripts/make_stills.py <nombre> <seg> img1 img2…`:
  tarjetas con sombra sobre fondo desenfocado. Muy útil para enseñar "lo de antes" frente al producto en movimiento.
- Logo → `python3 <skill>/scripts/prep_logo.py logo.png` (versión blanca y oscura, transparentes y nítidas). Sin él no
  sale el logo en la tarjeta final ni detrás de la cabeza.

### 5. Plan de montaje (`plan.py`)
Es el guion del montaje: planos, clips, palabras detrás de la cabeza, subtítulos, textos finales y efectos. La
plantilla es un anuncio real comentado: cámbialo entero para tu proyecto anclando todo a palabras con `W()`.
Lee `references/estilo.md` (cómo se ve) y `references/montaje.md` (ritmo, transiciones, efectos) antes de
escribirlo. Ejecuta `python3 plan.py` y después:
```bash
python3 <skill>/scripts/build_audio.py     # voz final + música generada + efectos + -14 LUFS
python3 <skill>/scripts/head_tops.py 9x16  # dónde queda la cabeza en cada palabra grande (y 4x5)
```

### 6. Prueba antes de renderizar
Renderiza fotogramas sueltos en los momentos clave y míralos (gancho en 0 s, cada palabra grande, transiciones,
clips, panel de cierre, tarjeta final):
```bash
node <skill>/scripts/render_overlay.js work/plan.json 9x16 work/ovl_9x16 0,2.1,3.0,9.2,16.8,19,23
python3 <skill>/scripts/compose.py 9x16 --test 0,2.1,3.0,9.2,16.8,19,23    # -> work/test_frames/
```
Comprueba: la palabra grande se lee y la cabeza tapa solo una parte; ningún texto tapa la cara; nada importante en
el 14 % superior ni el 20 % inferior (9:16); subtítulos legibles; el primer fotograma ya engancha.

### 7. Render final y control de calidad
`bash <skill>/scripts/render_all.sh` → `output/<nombre>_9x16.mp4`, `_4x5.mp4`, `portada.jpg`, `subtitulos.srt`
y el informe de calidad. **No lo des por terminado** sin:
- duración ≤ 30 s, −14 LUFS integrados, true peak ≤ −1 dBTP, sin clics (`qc.py`);
- `check_subs.py`: Whisper sobre el vídeo FINAL reconoce el 100 % de las palabras de los subtítulos (si no,
  un efecto pisa la voz: muévelo a una pausa) y la sincronía mediana es ~0 ms;
- fotogramas revisados del vídeo final.
Para el antes/después de la voz y el análisis de eco: `references/audio.md`.

## Decisiones de estilo que el cliente ya pidió (no las cambies sin motivo)
- **Nada de PiP** (la persona en pequeño sobre el producto "queda cutre"): el producto va a pantalla completa con la voz en off.
- **Palabra grande detrás de la cabeza** + frase pequeña fina encima, minúsculas, Inter Display; una por idea.
- **Subtítulos en tarjeta de cristal** abajo (desenfoque real del vídeo), palabra que suena resaltada.
- **Un solo color de acento, desaturado** (azul suave por defecto). Imagen natural, sin sobresaturar la piel.
- **Rótulo fijo** tipo "hasta el 30 de noviembre" en vez de una cuenta atrás que depende del día de publicación.
- **Efectos de sonido del pack** con energía de reel, pero **nunca encima del final de una frase ni de una
  palabra clave** (se notó al oído en "Prospectus": un pop en mitad de la palabra).
- La llamada a la acción del botón dice lo mismo que la persona en el vídeo.

## Referencias (léelas cuando toque)
- `references/estilo.md`: tipografía, colores, capas, posiciones 9:16 y 4:5, zonas seguras, tarjeta final.
- `references/montaje.md`: estructura, ritmo, encuadres, transiciones, catálogo de efectos y dónde poner cada uno.
- `references/audio.md`: cadena de voz, análisis de eco (RT60), música, niveles, antes/después.
- `references/broll.md`: clips de apoyo propios y captura de webs / tours 360.
- `references/entorno.md`: instalación, red y descarga de modelos/vídeos, problemas conocidos.
- `references/errores.md`: lo que salió mal en proyectos reales y cómo se arregló (léelo una vez).
