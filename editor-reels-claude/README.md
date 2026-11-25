# editor-reels-claude 🎬

Skill para que **Claude** edite anuncios y reels verticales (Instagram Reels, Stories, TikTok, Shorts) de una
persona hablando a cámara, con acabado profesional, a partir de las tomas en bruto grabadas con el móvil.

**Qué hace**
- Transcribe las tomas (Whisper large-v3), las ordena por lo que se dice y quita silencios, muletillas y pausas.
- Voz de estudio: quita el eco de la sala (WPE con los 2 micrófonos del móvil + DeepFilterNet), EQ, de-esser,
  compresión suave, música de fondo generada (sin derechos) con ducking y −14 LUFS.
- Imagen: etalonaje por toma (balance en la pared o en la piel), reencuadre que sigue la cara, punch-ins.
- Estilo "palabra detrás de la cabeza" + subtítulos en tarjetas de cristal, un solo color de acento, Inter Display.
- Clips de apoyo a pantalla completa, transiciones de reel (whip pan, zoom, destello, sacudida) y **efectos de sonido
  sincronizados** (44 sonidos CC0 del SFX Kit de Wyzowl incluidos).
- Exporta **9:16 y 4:5**, portada, subtítulos .srt y antes/después de la voz, con control de calidad automático
  (duración, loudness, clics, y que Whisper entienda el 100 % de las palabras sobre los efectos).

## Cómo usarla

### Claude Code (recomendado)
```bash
git clone --depth 1 -b claude/beautiful-lamport-j4rpkp https://github.com/aleixjimenez21-cpu/tarragona-inmobiliaria /tmp/editor-reels
mkdir -p ~/.claude/skills && cp -r /tmp/editor-reels/editor-reels-claude ~/.claude/skills/
bash ~/.claude/skills/editor-reels-claude/scripts/setup.sh
```
Luego, en Claude Code: *"Edita estas 4 tomas como un anuncio de reel: …"* (pasa los vídeos o la ruta de la carpeta).

También puedes pasarle el enlace a tu Claude:
*"Instala y usa la skill de https://github.com/aleixjimenez21-cpu/tarragona-inmobiliaria/tree/claude/beautiful-lamport-j4rpkp/editor-reels-claude
para editar mis vídeos"*: la descargará y seguirá `SKILL.md`.

### Claude en la web (claude.ai) / app
Descarga el repo como ZIP y súbelo en **Ajustes → Capacidades → Skills**. Necesita un entorno con ejecución de código
y acceso a internet (para instalar dependencias y descargar los modelos).

## Qué necesitas pasarle a Claude
- Las **tomas originales** del móvil (no comprimidas). Si pesan mucho, súbelas a Google Drive y pasa el enlace.
- El **logo** (PNG) y el brief: qué anuncias, la oferta, la fecha límite y la llamada a la acción.
- Opcional: clips de apoyo (producto, local, pantalla…) o la web de la que sacar clips.

## Requisitos
ffmpeg, Python 3.10+, Node 18+ (Playwright + Chromium), fuente Inter Display. Funciona en CPU (sin GPU).
Detalles y problemas conocidos: [`references/entorno.md`](references/entorno.md).

## Créditos y licencias
- Código: MIT (ver `LICENSE`).
- Efectos de sonido: **SFX Kit de Wyzowl**, CC0 (dominio público, uso comercial sin atribución), seleccionados del pack
  [juantoc7755-alt/sfx-pack-editores](https://github.com/juantoc7755-alt/sfx-pack-editores). Licencias en `assets/licencias/`.
- Modelos y herramientas de terceros que se descargan al usarla: Whisper (MIT), DeepFilterNet (MIT/Apache-2.0),
  nara_wpe (MIT), rembg / U²-Net (MIT/Apache-2.0).
