# Destacada «About» — Aleix Jiménez

Siete historias estáticas de 1080 × 1920 (JPG, máxima calidad), más la portada de la destacada.

## Orden de publicación

| # | Archivo | Qué cuenta |
|---|---|---|
| 00 | `00-portada-destacada.jpg` | Icono circular de la destacada |
| 01 | `01-portada.jpg` | Quién soy: del taller familiar a la comercialización inmobiliaria |
| 02 | `02-origen.jpg` | Taller y obra: la empresa familiar de carpintería de aluminio |
| 03 | `03-lo-que-vi.jpg` | La oportunidad: el producto evoluciona, la forma de venderlo no tanto |
| 04 | `04-prospectus.jpg` | Hoy: cofundador de Prospectus, con Villa Aurea como caso real |
| 05 | `05-enfoque.jpg` | Qué hago y para quién |
| 06 | `06-hacia-donde.jpg` | Visión y ambición, sin aparentar una trayectoria que aún no existe |
| 07 | `07-hablemos.jpg` | Contacto |

## Al publicar

1. Sube las historias **en orden, de la 01 a la 07**, y añádelas a una destacada nueva llamada **About**.
2. Como portada de la destacada, elige `00-portada-destacada.jpg` y céntrala en el círculo.
3. **Historia 07**: añade un sticker de enlace (WhatsApp `https://wa.me/34633716169` o tu web)
   y colócalo justo debajo de la lista de contactos, sobre el negro. Sin más stickers: el diseño ya respira.
4. Sin música de tendencia ni GIFs: el silencio forma parte de la estética.
5. Las zonas superior (≈ 230 px) e inferior (≈ 260 px) se dejaron libres para la interfaz de Instagram.

## Sistema visual

- **Tipografía**: Instrument Serif (titulares; la cursiva marca la palabra clave) + Switzer (texto y etiquetas).
  La misma pareja que la landing de promotoras, para que perfil y web se reconozcan como una sola marca.
- **Color**: monocromo cálido. Negro `#090908`, hueso `#E8E3D9`, gris piedra `#706D67`. Todas las fotos
  pasan por el mismo etalonaje (`_source/grade.py`).
- **Textura**: grano de película sutil y viñeteado en todas las piezas.
- **Hilo narrativo**: vidrio y metal. Perfil de aluminio en el taller → cúpula de vidrio de la Galleria →
  Villa Aurea en 3D.

## Regenerar o editar

Los textos están en `_source/story.html` (objeto `STORIES`). Tras editarlos:

```bash
cd highlight-about/_source
python3 grade.py <carpeta-con-fotos-originales> img   # solo si cambian las fotos
node render.js stills          # todas las historias
node render.js stills 4        # solo una
```

Requiere Node con Playwright (Chromium) y ffmpeg.
