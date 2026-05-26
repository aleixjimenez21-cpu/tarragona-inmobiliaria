# Aleix Jiménez — Real Estate Operator

Landing page personal para operador inmobiliario privado en Tarragona.

## Stack

- HTML + CSS + JavaScript vanilla
- Tailwind CSS via CDN (sin build)
- Google Fonts: Space Grotesk + Inter
- Sin frameworks, sin dependencias npm

## Archivos

| Archivo | Descripción |
|---|---|
| `index.html` | Landing completa (7 secciones) |
| `styles.css` | Sistema de diseño oscuro premium |
| `calculator.js` | Lógica de calculadora con recomendaciones |

## Publicar en Netlify

1. Ve a [app.netlify.com](https://app.netlify.com)
2. Arrastra la carpeta `tarragona-inmobiliaria` al área de deploy
3. Tu URL pública estará lista en ~30 segundos

## Publicar en Vercel

```bash
npx vercel --prod
```

O arrastra la carpeta en [vercel.com/new](https://vercel.com/new).

## Personalizar

### Datos de contacto
Busca en `index.html`:
- `+34 600 000 000` → tu número real
- `aleix@aleixjimenez.com` → tu email real
- El link de WhatsApp: `https://wa.me/34600000000` → `https://wa.me/34TUNUMERO`

### Calculadora · Precios por zona
Edita `calculator.js`, objeto `ZONES` (líneas 6-13). Valores en €/m² construido.

### Colores
Edita `styles.css`, bloque `:root` (líneas 8-38).

## Secciones

1. **Hero** — Titular + CTAs + stats animados
2. **Diferencial** — 3 cards de propuesta de valor + quote
3. **Método** — 4 pasos del proceso
4. **Calculadora** — Formulario con selector de intención + resultado con recomendación personalizada
5. **Zonas** — Precios orientativos por barrio
6. **Contacto** — WhatsApp, email + formulario
7. **Footer** — Mínimal
