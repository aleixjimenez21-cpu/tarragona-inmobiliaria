#!/usr/bin/env bash
# Elige la fuente de audio y la deja en public/audio.mp3
#   1) ./musica.mp3   2) pista de ./referencia.mp4   3) assets/musica_provisional.mp3
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p public
if [[ -f musica.mp3 ]]; then
  echo "Audio: musica.mp3"; cp musica.mp3 public/audio.mp3
elif [[ -f referencia.mp4 ]]; then
  echo "Audio: pista extraída de referencia.mp4"
  ffmpeg -y -loglevel error -i referencia.mp4 -vn -ac 2 -ar 44100 -b:a 192k public/audio.mp3
else
  echo "AVISO: no hay musica.mp3 ni referencia.mp4 -> uso assets/musica_provisional.mp3"
  cp assets/musica_provisional.mp3 public/audio.mp3
fi
