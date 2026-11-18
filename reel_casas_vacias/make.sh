#!/bin/bash
# LA MAQUETA — regenera el reel completo con un solo comando.
#   ./make.sh            (usa input/voz.wav si existe; si no, el ritmo del guion)
# Si cambian los tiempos (otra voz), se vuelven a renderizar los planos.
set -e
cd "$(dirname "$0")"
PY=${PY:-/opt/reel/venv/bin/python}
[ -f data/maqueta.json ] || $PY src/prep.py
$PY src/timing.py
H=$(sha1sum output/timings.json | cut -c1-12)
if [ "$(cat renders/.timings 2>/dev/null)" != "$H" ]; then
  echo "Tiempos nuevos: se borran renders y fotogramas anteriores"
  rm -rf renders post_frames; mkdir -p renders; echo "$H" > renders/.timings
fi
src/render_all.sh
[ -f renders/P_portada/cover/f_0601.exr ] || $PY src/render.py -- P_portada --q cover --times 20
$PY src/post.py
$PY src/post.py --portada
$PY src/audio.py
$PY src/deliver.py
echo "Listo: output/"
