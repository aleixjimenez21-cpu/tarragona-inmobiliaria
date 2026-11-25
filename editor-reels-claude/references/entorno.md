# Entorno, instalación y problemas conocidos

## Requisitos
ffmpeg, Python 3.10+, Node 18+ con Playwright/Chromium, fuente Inter Display, ~4 GB de RAM libres, CPU (no hace
falta GPU). `bash scripts/setup.sh` instala lo demás. Primera ejecución: descarga Whisper large-v3 (~3 GB) y el
modelo de segmentación u2net_human_seg (~170 MB).

## Red (si el entorno tiene una lista de hosts permitidos)
- pypi.org / files.pythonhosted.org y registry.npmjs.org (paquetes)
- github.com y release-assets.githubusercontent.com / objects.githubusercontent.com (DeepFilterNet, rembg)
- huggingface.co y su CDN (`us.aws.cdn.hf.co`, `cas-bridge.xethub.hf.co`, `cdn-lfs.hf.co`) para Whisper; si la
  descarga con Xet falla, prueba `HF_HUB_DISABLE_XET=1`.
- Vídeos en Google Drive: `drive.google.com` y `drive.usercontent.google.com`. Descarga directa por archivo:
  `curl -L "https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t" -o toma.mov`
  (los IDs de una carpeta compartida se listan con `gdown.download_folder(url, skip_download=True)`). La descarga
  "clásica" de gdown redirige a hosts `doc-XX-docs.googleusercontent.com` que cambian y suelen estar bloqueados.

## Rendimiento (4 núcleos)
Whisper large-v3 int8 ≈ 1 min para 30 s de tomas; WPE+DeepFilterNet ≈ 30 s; gráficos ≈ 4 min por formato;
compositor ≈ 6-8 min por formato (segmentación de persona incluida). Render completo de los dos formatos ≈ 25 min.

## Problemas conocidos
- `faster-whisper` + PyAV reciente: `open() got an unexpected keyword argument 'metadata_errors'` → pasa el audio
  como array (ya lo hace `transcribe.py`).
- OpenCV 5 no trae los clasificadores Haar → `pip install "opencv-python-headless<5"`.
- Haar con `equalizeHist` falla en tomas con pared blanca: no lo uses (ya está quitado).
- BiRefNet (segmentación mejor) se queda sin memoria en CPU: usa u2net_human_seg.
- La fuente Inter Display tiene que estar instalada en el sistema; si no, los rótulos salen con otra fuente.
- Las tomas del iPhone vienen en HEVC 10 bits con rotación: ffmpeg las gira solo; no las conviertas antes.
