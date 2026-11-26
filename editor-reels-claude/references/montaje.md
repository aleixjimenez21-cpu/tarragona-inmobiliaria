# Montaje: estructura, ritmo, transiciones y efectos

## Estructura que funciona (≤30 s)
1. **Gancho (0-3 s)**: el primer fotograma ya muestra la frase y la palabra grande (sin fundido de entrada) y
   arranca con un golpe (`cinematic-drum-big`). Punch-in en la palabra clave.
2. **Oferta**: la cifra grande detrás de la cabeza ("-50 %") con boom + sacudida; un clip corto de apoyo con whip pan
   cuando se nombra el producto.
3. **Qué hacemos**: el producto a pantalla completa con la voz en off, un clip por idea, cambiando al ritmo de las
   palabras (cada 0,7-1,4 s). Etiqueta pequeña con el nombre del proyecto/clip.
4. **Cierre**: vuelta a la persona en plano cerrado, palabra grande con la condición ("1 plaza"), panel de cristal con
   oferta + botón cuando dice la llamada a la acción, y tarjeta final 2 s.

## Formato lista ("3 errores", "5 claves")
Gancho con la pregunta + "uno de estos 3 errores" (palabra grande "3 errores"), y en cada punto: contador arriba
("error 1 de 3"), nota de marimba que sube un paso (`tone-step-1`, `-2`, `-3`), destello + whoosh al entrar y una palabra
grande con la idea clave. Apoyo visual de cada error con su contraste: lo de antes en imágenes fijas
(`make_stills.py`: planos, render, PDF) y la solución en movimiento al final, con el panel de cierre encima.

## Cortes
Sin aire muerto: fuera silencios iniciales/finales, muletillas, repeticiones, tomas falsas y frases tipo "lo veo
bien". Recorta pausas internas >0,2 s. Microfundido de 10 ms en cada corte de audio (`XF`).

## Transiciones (campo `trans` del plano que ENTRA)
| trans | Qué hace | Cuándo |
|---|---|---|
| `flash` | destello blanco 5 fotogramas + zoom que se asienta | cambio de bloque (gancho→oferta, "y reserva") |
| `flashlite` | destello suave + punch | punch-in en la palabra clave dentro del mismo plano |
| `whip` / `whipr` | desenfoque de movimiento horizontal (izq/der) | entrar/salir de un clip con movimiento lateral |
| `zoom` | zoom con desenfoque radial | entrar en el producto, cambio a plano cerrado |
| `dissolve` | fundido de 8 fotogramas | transformación ("tu promoción" → "tour virtual") |
| `None` | corte seco | entre clips del mismo bloque |
Sacudidas (`SHAKES`) solo en 2-3 golpes fuertes. La tarjeta final entra con un golpe de zoom.

## Efectos de sonido (`assets/sfx/sounds.json`, Wyzowl SFX Kit, CC0)
Cada sonido trae su **punto de sincronía** (`sync.at`) y su reducción recomendada **bajo voz**; `sfx.py` los aplica.
En `plan.py`, `at` es el instante que debe coincidir con ese punto (el pico del whoosh en el centro del
movimiento, el golpe en el fotograma exacto, la campana de la caja registradora cuando aparece el precio).
Nivel: el del kit para una voz a −16 LUFS, desplazado al nivel real de la voz, +4 dB de energía de reel.

| Momento | Sonido |
|---|---|
| apertura del gancho, tarjeta final | `cinematic-drum-big` |
| punch-in, cortes cortos | `swish-medium` |
| cambio de bloque con destello | `whoosh-fast-medium` |
| whip pans (panea con `pan=±1` según el movimiento) | `whoosh-fast-soft` |
| cifra/precio que aparece | `boom-hit-medium` + `money-register` en la pausa siguiente |
| cambio de luz / revelación suave | `shimmer-short-soft` |
| algo confirmado ("disponible", "reservado") | `notification-success-soft` |
| tarjeta o panel que aparece | `pop-medium-in` (en una micro-pausa) |
| logo final | `sting-minimal-short` |
| subida antes de una revelación | `riser-1s-soft` (su FINAL en el corte) |
Hay 44 sonidos en la selección; el catálogo completo (320 + 100 de Kenney) está en
github.com/juantoc7755-alt/sfx-pack-editores: clónalo y exporta `SFX_PACK_DIR=<ruta>/wyzowl-sfx-kit`.

**Regla de oro**: un efecto nunca encima del final de una frase ni dentro de una palabra clave. Si al pasar
`check_subs.py` Whisper oye "firmes" por "firme" o "escríbeme" por "escríbenos", hay un efecto pisando la voz:
muévelo a la pausa o cámbialo por uno más corto (swish en vez de whoosh largo, sin riser antes de hablar).

## Música
`build_audio.py` genera una base corporativa discreta (pad + bajo + arpegio + percusión suave, 100 BPM), libre de
derechos, a −23 dB bajo la voz con ducking. Si el cliente da una pista con licencia, sustituye `work/audio/music.wav`.
