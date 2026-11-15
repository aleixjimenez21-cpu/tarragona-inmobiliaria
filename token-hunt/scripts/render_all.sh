#!/usr/bin/env bash
# Pipeline completo: audio -> beats.json -> timeline.ts -> render -> versiones -> comparación
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/prepare_audio.sh
python3 scripts/analyze_beats.py public/audio.mp3 beats.json
node scripts/build_timeline.mjs
bash scripts/detect_cuts.sh referencia.mp4 0.25 || true
mkdir -p out
# máster casi sin pérdidas y codificación final (el grano por frame dispara el bitrate a CRF 16)
npx remotion render src/index.ts TokenHunt out/master.mp4 --codec=h264 --crf=16 --audio-bitrate=192k
ffmpeg -y -loglevel error -i out/master.mp4 -c:v libx264 -preset slow -crf 23 -pix_fmt yuv420p -movflags +faststart -c:a copy out/video_con_audio.mp4
cp out/video_con_audio.mp4 out/video.mp4
ffmpeg -y -loglevel error -i out/video_con_audio.mp4 -map 0:v -c copy out/video_sin_audio.mp4
bash scripts/detect_cuts.sh out/video.mp4 0.25
node scripts/compare_cuts.mjs || true
bash scripts/comparison.sh
