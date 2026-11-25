#!/usr/bin/env bash
# Instala lo que necesita la skill (Linux / macOS). Uso: bash <skill>/scripts/setup.sh
# Necesita red hacia: pypi.org, registry.npmjs.org, github.com (+ release-assets.githubusercontent.com),
# huggingface.co (+ su CDN, p. ej. us.aws.cdn.hf.co / cas-bridge.xethub.hf.co) para el modelo Whisper large-v3.
set -e
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
command -v ffmpeg >/dev/null || { echo "Falta ffmpeg (apt install ffmpeg / brew install ffmpeg)"; exit 1; }
command -v node >/dev/null || { echo "Falta Node.js 18+"; exit 1; }
pip install -q faster-whisper soundfile scipy numpy pillow "opencv-python-headless<5" nara_wpe "rembg[cpu]" onnxruntime matplotlib
# Playwright + Chromium (gráficos y captura de webs). Si ya hay un Chromium de Playwright instalado, se reutiliza.
node -e "require('playwright')" 2>/dev/null || (npm i -g playwright && npx playwright install chromium)
# DeepFilterNet (binario estático) para limpiar la voz
mkdir -p "$SKILL/bin"
if [ ! -x "$SKILL/bin/deep-filter" ]; then
  case "$(uname -s)-$(uname -m)" in
    Linux-x86_64)  F=deep-filter-0.5.6-x86_64-unknown-linux-musl ;;
    Linux-aarch64) F=deep-filter-0.5.6-aarch64-unknown-linux-gnu ;;
    Darwin-arm64)  F=deep-filter-0.5.6-aarch64-apple-darwin ;;
    Darwin-x86_64) F=deep-filter-0.5.6-x86_64-apple-darwin ;;
    *) echo "Descarga deep-filter a mano desde github.com/Rikorose/DeepFilterNet/releases a $SKILL/bin/"; exit 1 ;;
  esac
  curl -L -o "$SKILL/bin/deep-filter" "https://github.com/Rikorose/DeepFilterNet/releases/download/v0.5.6/$F"
  chmod +x "$SKILL/bin/deep-filter"
fi
# Fuente Inter Display (la usan los gráficos). En Linux suele estar en el paquete fonts-inter.
fc-list 2>/dev/null | grep -qi "Inter Display" || echo "AVISO: instala la fuente Inter Display (apt install fonts-inter, o desde rsms.me/inter) para que los rótulos salgan con la tipografía correcta."
echo "Listo. Modelos que se descargan solos la primera vez: Whisper large-v3 (Hugging Face) y u2net_human_seg (GitHub)."
