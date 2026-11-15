#!/usr/bin/env bash
# Detecta cortes de escena en un vídeo (por defecto referencia.mp4)
# Salida: out/cortes_<nombre>.txt (un tiempo en segundos por línea)
set -euo pipefail
cd "$(dirname "$0")/.."
IN="${1:-referencia.mp4}"; THR="${2:-0.25}"
[[ -f "$IN" ]] || { echo "No existe $IN, salto la detección de cortes"; exit 0; }
name=$(basename "${IN%.*}"); mkdir -p out
ffmpeg -hide_banner -i "$IN" -vf "select='gt(scene,$THR)',showinfo" -an -f null - 2>&1 \
  | grep -o 'pts_time:[0-9.]*' | cut -d: -f2 > "out/cortes_${name}.txt"
echo "$(wc -l < out/cortes_${name}.txt) cortes -> out/cortes_${name}.txt"
