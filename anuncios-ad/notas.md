# Anuncio 2 Black Friday · Prospectus ("Promotor, deja de vender pisos con PDF")

Editado con el mismo sistema y estilo que el primer anuncio (`../anuncio-bf/notas.md`, donde está el detalle de cada herramienta).

## Resultado (`output/`)
| Archivo | Qué es |
|---|---|
| `prospectus_bf2_9x16.mp4` | Reels/Stories, 1080x1920, 30 fps, H.264 CRF 18, AAC 320 kbps, −14 LUFS |
| `prospectus_bf2_4x5.mp4` | Feed, 1080x1350, reencuadre propio |
| `portada.jpg` | Fotograma del gancho |
| `subtitulos.srt` | Subtítulos con los tiempos del montaje |
| `antes_despues_10s.wav` | Voz original → voz final (10 s cada una, igualadas en volumen) |

## Tomas (descargadas de Google Drive en calidad original: 4K HEVC del iPhone, 2 micrófonos)
| Bloque | Toma | Lo que se dice |
|---|---|---|
| Gancho | `b4c4d0fd` (en la mesa) | Promotor, deja de vender pisos con PDF. |
| Oferta | `f770c468` | Por Black Friday, la primera promotora que cierre con nosotros tiene el tour virtual a mitad de precio. |
| Qué hacemos | `e8b41a7e` | Convertimos tu promoción en un tour virtual para que tu comprador pueda verlo y recorrerlo mucho antes de que tu promoción esté creada. |
| Cierre | `69dcd5d3` | Solo una plaza, así que ya sabes, si tienes una promoción, escríbenos hoy, o mañana puede ser muy tarde. |

Cortes (`scripts/edl.py`): se quitan silencios iniciales/finales y tres pausas internas ("tiene… el tour", "recorrerlo… mucho", "o… mañana"). Duración final: 24,2 s.

## Lo específico de este anuncio
- **Voz**: misma cadena (WPE multicanal + DeepFilterNet + post-filtro, EQ, de-esser, compresión suave, −14 LUFS). La sala tiene el mismo eco: RT60 equivalente 0,95 s → 0,28 s; cola tras frase −13,4 dB → −43,5 dB.
- **Color**: balance de blancos medido en la pared blanca; el gancho (en la mesa, con pared de madera detrás) se calibra por **tono de piel** para que case con las otras tomas.
- **Seguimiento de cara** más robusto: detección de mayor confianza + continuidad temporal + mediana (en el cierre el detector confundía pliegues de la chaqueta con caras).
- **Palabras detrás de la cabeza**: "pdf." (la cabeza tapa poco para que se lea desde el primer fotograma), "-50 %", "mitad", "creada." y "1 plaza".
- **Tour a pantalla completa** con voz en off: edificio real de Serra en "tu promoción", aéreo de Villa Aurea con paso a noche en "tour virtual", salón / cocina / dormitorio en "comprador pueda verlo y recorrerlo".
- **Efectos** (Wyzowl SFX Kit, CC0): tambor de apertura, swish en "PDF", whoosh + boom en "-50 %", whip pans de la piscina, caja registradora justo tras "a mitad de precio.", shimmers, boom en "1 plaza", pop del panel y sting de logo + tambor en la tarjeta final.
- Rótulo arriba: "⏳ hasta el 30 de noviembre". CTA: "escríbenos ya".

## Cómo regenerarlo
Igual que el primer anuncio, desde `anuncios-ad/` (los clips del tour, la herramienta deep-filter y las fuentes se comparten con `anuncio-bf/work`).
