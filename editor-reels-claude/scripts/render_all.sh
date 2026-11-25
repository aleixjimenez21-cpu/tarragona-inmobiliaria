#!/usr/bin/env bash
# Render final de los dos formatos + controles de calidad. Ejecutar desde la carpeta del proyecto.
# Uso: bash <skill>/scripts/render_all.sh [9x16|4x5|ambos]
set -e
SK="$(cd "$(dirname "$0")" && pwd)"
FMTS="${1:-ambos}"; [ "$FMTS" = "ambos" ] && FMTS="9x16 4x5"
NAME=$(python3 -c "import json;print(json.load(open('work/plan.json')).get('name','anuncio'))")
export NODE_PATH="${NODE_PATH:-$(npm root -g)}"
for F in $FMTS; do
  python3 "$SK/head_tops.py" "$F"
  rm -rf "work/ovl_$F"
  node "$SK/render_overlay.js" work/plan.json "$F" "work/ovl_$F"
  python3 "$SK/compose.py" "$F"
  cp "work/video_$F.mp4" "output/${NAME}_$F.mp4"
  python3 "$SK/qc.py" "output/${NAME}_$F.mp4"
done
ffmpeg -v error -y -ss "$(python3 -c "import json;print(json.load(open('work/plan.json')).get('cover_t',0.0))")" -i "output/${NAME}_9x16.mp4" -frames:v 1 -q:v 2 output/portada.jpg 2>/dev/null || true
python3 "$SK/make_srt.py"
python3 "$SK/check_subs.py" "output/${NAME}_9x16.mp4" 2>/dev/null || python3 "$SK/check_subs.py" "output/${NAME}_$F.mp4"
