# Destacada «About» — Aleix Jiménez

Siete historias estáticas de 1080 × 1920 (JPG, máxima calidad), más la portada de la destacada.

## Orden de publicación

| # | Archivo | Qué cuenta |
|---|---|---|
| 00 | `00-portada-destacada.jpg` | Icono circular de la destacada |
| 01 | `01-portada.jpg` | Quién soy: del taller familiar a la comercialización inmobiliaria |
| 02 | `02-origen.jpg` | Crecí entre aluminio y obra (taller arriba, obra abajo) |
| 03 | `03-lo-que-vi.jpg` | Años de obra. Y se vende con un render. |
| 04 | `04-prospectus.jpg` | Hoy, Prospectus: la experiencia 3D real de Villa Aurea |
| 05 | `05-enfoque.jpg` | Primero, entender el negocio |
| 06 | `06-hacia-donde.jpg` | Vender mejor lo que se construye |
| 07 | `07-hablemos.jpg` | Hablemos: DM y WhatsApp |

## Al publicar

1. Sube las historias **en orden, de la 01 a la 07**, y añádelas a una destacada nueva llamada **About**.
2. Como portada de la destacada, elige `00-portada-destacada.jpg` y céntrala en el círculo.
3. **Historia 07**: añade un sticker de enlace (WhatsApp `https://wa.me/34633716169` o tu web)
   y colócalo bajo los datos de contacto, sobre el fondo oscuro. Sin más stickers: el diseño ya respira.
4. Sin música de tendencia ni GIFs: el silencio forma parte de la estética.
5. Las zonas superior (≈ 230 px) e inferior (≈ 260 px) se dejaron libres para la interfaz de Instagram.

## Sistema visual

- **Una foto, una frase.** Cada historia es una fotografía a sangre con una sola frase grande. Sin párrafos,
  etiquetas ni numeraciones: se entiende en un segundo.
- **Tipografía**: Instrument Serif (la cursiva marca la palabra clave) + Switzer para las líneas pequeñas.
  La misma pareja que la landing de promotoras, para que perfil y web se reconozcan como una sola marca.
- **Color**: blanco y negro natural (sombras abiertas, contraste moderado) en las fotos personales; la
  experiencia de Villa Aurea mantiene su color para que el producto destaque.
- **Ritmo**: tinta sobre fondo claro en la portada y en Prospectus; blanco sobre foto en el resto.

## Regenerar o editar

Los textos están en `_source/story.html` (objeto `STORIES`, una entrada por historia). Tras editarlos:

```bash
cd highlight-about/_source
python3 grade.py <carpeta-con-fotos-originales> img   # solo si cambian las fotos
node render.js stills          # todas las historias
node render.js stills 4        # solo una
```

Requiere Node con Playwright (Chromium) y ffmpeg.
