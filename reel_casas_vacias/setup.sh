#!/bin/bash
# Entorno: Python 3.11 + Blender como módulo (bpy) y librerías de imagen/audio.
set -e
python3.11 -m venv /opt/reel/venv
/opt/reel/venv/bin/pip install bpy==5.0.1 numpy pillow scipy shapely pyloudnorm soundfile OpenEXR opencv-python-headless fonttools brotli
# opcional, solo si hay voz: alineado palabra a palabra
/opt/reel/venv/bin/pip install faster-whisper || true
# Linux sin pantalla: ffmpeg
command -v ffmpeg >/dev/null || sudo apt-get install -y ffmpeg
