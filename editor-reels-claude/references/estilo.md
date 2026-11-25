# Estilo visual

Estética sobria y premium: negro, blanco y **un único color de acento desaturado**. Nada chillón. La referencia es
el estilo "words behind his head" (palabra enorme detrás de la cabeza) con tarjetas de cristal tipo interfaz.

## Capas (de atrás a delante)
1. **Vídeo base**: plano a cámara (reencuadrado y etalonado) o clip de apoyo a pantalla completa.
2. **Palabra grande** (`BEHIND.big`): se compone DETRÁS de la persona con una máscara de segmentación
   (rembg `u2net_human_seg`, suavizado temporal, erosión 2 px + difuminado contra el halo del pelo).
3. **Sacudida de cámara** (si toca) y difuminado de fondo de la tarjeta final.
4. **Cristal**: subtítulos, rótulo de plazo, etiqueta del clip y panel de cierre. `compose.py` desenfoca el vídeo
   real debajo de cada tarjeta (σ≈22) y encima va un tinte oscuro translúcido con borde fino claro.
5. **Capa delantera** (overlay.html): frase pequeña, textos, subtítulos, tarjeta final.

## Tipografía
- **Inter Display** (sistema). Palabra grande: SemiBold 600, minúsculas, tracking −0,045 em, hasta 400 px y ajustada
  a 980 px de ancho. Frase pequeña: Regular 400, 54 px, minúsculas, con un halo claro suave (se lee sobre fondos
  oscuros sin que se note en paredes claras).
- Subtítulos: Medium 500, 46 px, minúsculas; palabras ya dichas en blanco, la que suena en el acento, las
  siguientes en blanco al 62 %. Bloques de 1-4 palabras por sentido, nunca cortando una idea.

## Color
- Acento claro `#9CC3E2` (sobre fondos oscuros) y profundo `#5A8BB5` (palabras grandes sobre pared clara).
  Mismo tono en todo el vídeo. Si la marca tiene un color propio muy saturado, úsalo solo en el logo.
- Etalonaje de los planos a cámara (`grade_params.py` + `compose.py`): balance de blancos en la pared (o piel),
  exposición en lineal con hombro suave, curva S ligera (0,24), saturación −8 %, un punto cálido (1,015/1/0,98),
  claridad (contraste local σ 14, 0,28), nitidez solo en luminancia (σ 0,9, 0,6) y grano fino (σ 1,8) para quitar el
  aspecto "plástico" del procesado del móvil. Clips de apoyo: sin tocar el color.

## Posiciones (9:16, 1080x1920)
- Zonas seguras de Reels: nada importante por encima de y=269 (14 %) ni por debajo de y=1536 (20 %).
- Rótulo de plazo: cristal arriba a la derecha (y≈286). Todo lo demás empieza en y≥362.
- Palabra grande: su altura se calcula con la posición de la cabeza (`head_tops.py`) para que la cabeza tape
  ~45 % (`cover`); con palabras cortas y clave (gancho) baja a ~0,3 para que se lean desde el primer fotograma.
- Subtítulos: centro en y=1440. Etiqueta del clip: izquierda, y≈1290. Panel de cierre: y≈1075 (bajo la barbilla).
- 4:5 (1080x1350, feed): reencuadre propio (`face_y45`), plazo arriba a la derecha, subtítulos en y≈1225, la tarjeta
  final y el panel más compactos. No es un recorte del 9:16.

## Encuadre de la persona
- Zoom calculado por **tamaño de cara objetivo** con seguimiento de cara: si la persona se acerca a cámara, el
  plano se mantiene (como un travelling). Máximo 1,9x desde 4K (siempre reducción de escala); 1,25x si es 1080p.
- Punch-in al cambiar de plano (empieza un 5 % más cerca y se asienta en 0,22 s).
- Cierre en plano más cerrado. Comprueba que ningún texto tapa la boca o la barbilla.

## Tarjeta final (últimos ~2 s)
Fondo: el último plano desenfocado y oscurecido. Logo blanco, línea descriptiva fina, etiqueta de campaña,
cifra grande en el acento, condición ("solo 1 plaza"), plazo, y botón blanco tipo píldora con la llamada a la
acción que late suavemente. Todo en minúsculas y centrado.
