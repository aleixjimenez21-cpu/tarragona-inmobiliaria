# Lecciones de proyectos reales (qué falló y cómo se arregló)

| Problema | Causa | Solución |
|---|---|---|
| "Queda muy cutre que se me vea así en pequeño" | PiP de la persona sobre el producto | Producto a pantalla completa con voz en off |
| La persona "se ve un poco mal" | Imagen plana gris-verdosa, pared subexpuesta, piel cerosa, zoom 2x de una toma comprimida | Balance en la pared, exposición en lineal, curva fílmica, claridad, grano fino; zoom ≤1,9x desde 4K; pedir los originales |
| "Sin tanta saturación" | Saturación +8 % y tono cálido | Saturación −8 %, calidez mínima, contraste 0,24 |
| Eco de sala | Oficina vacía, RT60 ~1 s | WPE estéreo + DeepFilterNet con post-filtro |
| resemble-enhance inventaba frases | Modelo generativo en CPU | Descartado; DeepFilterNet |
| "Prospectus suena raro" | Un pop en mitad de la palabra | Ningún efecto dentro de una palabra clave; quitarlo o moverlo a una pausa |
| Whisper oía "firmes"/"escríbeme" en el final | Whoosh/riser antes de un corte pisaba el final de la frase | Swish corto que empieza después de la palabra; comprobar con check_subs.py |
| Palabras duplicadas o perdidas en los subtítulos | Whisper pone la palabra en la pausa recortada o funde dos | `WORD_OVERRIDES` mirando la envolvente |
| Encuadre que salta | El detector confunde pliegues de la chaqueta con caras | Detección de mayor confianza + continuidad + mediana (track_faces.py) |
| Color disparatado en una toma | Balance medido en una pared de madera | `SKIN_REF`: calibrar por piel |
| Palabra grande casi invisible | La cabeza la tapaba entera (plano muy cerrado o palabra corta) | `cover` más bajo, palabra más grande, o quitar esa palabra |
| Textos que chocan con la cuenta atrás | Todo en la franja superior | Plazo fijo arriba a la derecha y el resto desde y≥362 |
| Auto-tamaño de la palabra grande diminuto | Medía el ancho del contenedor, no del texto | Medir el ancho real del texto (inline-block) |
| Halo de la cuenta atrás / textos ilegibles sobre persiana oscura | Texto oscuro sobre fondo oscuro | Halo claro suave en la frase pequeña |
| Cuenta atrás con segundos | Depende del día de publicación | Rótulo fijo "hasta el …" |
