#!/usr/bin/env bash
# out/comparacion.mp4: [referencia | nuestro vídeo | sync monitor] (sin referencia: [vídeo | monitor])
set -euo pipefail
cd "$(dirname "$0")/.."
npx remotion render src/index.ts SyncMonitor out/sync_monitor.mp4 --muted --codec=h264 --crf=22
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 out/video.mp4)
LBL="drawtext=fontcolor=white:fontsize=28:box=1:boxcolor=black@0.6:x=12:y=12:text"
if [[ -f referencia.mp4 ]]; then
  ffmpeg -y -loglevel error -i referencia.mp4 -i out/video.mp4 -i out/sync_monitor.mp4 -filter_complex \
    "[0:v]trim=0:${DUR},setpts=PTS-STARTPTS,fps=30,scale=540:960:force_original_aspect_ratio=decrease,pad=540:960:(ow-iw)/2:(oh-ih)/2,${LBL}='ORIGINAL'[a];\
     [1:v]scale=540:960,${LBL}='NUEVO'[b];[2:v]scale=540:960[c];[a][b][c]hstack=inputs=3[v]" \
    -map "[v]" -map 1:a -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac -b:a 160k -t "$DUR" out/comparacion.mp4
else
  ffmpeg -y -loglevel error -i out/video.mp4 -i out/sync_monitor.mp4 -filter_complex \
    "[0:v]scale=540:960,${LBL}='NUEVO'[b];[1:v]scale=540:960[c];[b][c]hstack=inputs=2[v]" \
    -map "[v]" -map 0:a -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac -b:a 160k -t "$DUR" out/comparacion.mp4
fi
echo "-> out/comparacion.mp4"
