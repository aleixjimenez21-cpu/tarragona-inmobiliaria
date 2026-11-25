# Clips de apoyo (b-roll)

Todos los clips viven en `work/clips/<nombre>.mp4` a 1080x1920 y 30 fps; en `plan.py` se usan por nombre.

## Clips propios
Copia vídeos a `input/broll/` y ejecuta `python3 <skill>/scripts/prep_broll.py`: recorte centrado, 30 fps, nitidez
suave y `work/clips/hoja_contactos.jpg` para elegir. Revisa nitidez al 100 %: un clip blando a 1080x1920 baja la
calidad de todo el anuncio; mejor usarlo poco o no usarlo.

## Captura de webs y tours virtuales 360
- **Visores 360 (Photo Sphere Viewer, p. ej. tours inmobiliarios)**: `scripts/capture_360.js` captura **fotograma a
  fotograma**: en cada fotograma fija yaw/pitch/zoom con una curva suave (como un arrastre lento de dedo) y hace
  una captura a 1080x1920, así el movimiento sale perfecto aunque el render sea por software. Oculta la interfaz,
  espera a la textura de máxima calidad y para la autorrotación. Hay que adaptar al visor concreto: cómo acceder
  al objeto viewer en la página (`window.__showroom.viewer`, `window.showroom.viewer`…), cómo cambiar de estancia
  y qué CSS oculta la interfaz. Los planos se definen en un JSON (estación, yaw/pitch/zoom inicial y final en
  grados, duración); elige ángulos mirando las panorámicas (descárgalas y pinta una rejilla de yaw).
  Después codifica: `ffmpeg -framerate 30 -i frames/<id>/f_%04d.png -c:v libx264 -crf 12 -pix_fmt yuv420p work/clips/<id>.mp4`.
- **Webs con animaciones CSS / interacción** (selector de plantas, fichas): graba en tiempo real con Chromium en
  pantalla virtual (Xvfb) + `ffmpeg -f x11grab -draw_mouse 0 -framerate 30`; ventana más alta que la pantalla y
  captura desplazada para quitar la barra del navegador; `--disable-features=Translate` para que no salga el aviso
  de traducción; oculta menús con CSS y mueve el ratón con curvas suaves.
- Si una librería viene de un CDN bloqueado (jsDelivr…), instala la misma versión con npm y sírvela con `page.route`.
- Comprueba la resolución de las panorámicas: por debajo de ~4000 px de ancho se ven blandas a 1080x1920. Usa poco
  esos planos y prioriza vídeos (drones, intros) y vistas nítidas.

## Uso en el montaje
Un clip por idea, cambiando con las palabras, 0,7-1,5 s cada uno. Un cruce de dos versiones del mismo movimiento
(día → noche) queda muy bien para "tour virtual". `shift_y` en `broll()` baja un clip si su información importante
cae en el 14 % superior (rellena el hueco con el cielo).
