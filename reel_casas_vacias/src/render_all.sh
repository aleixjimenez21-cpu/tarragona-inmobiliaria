#!/bin/bash
# Renderiza en calidad final los planos indicados (o todos).
cd "$(dirname "$0")/.."
PY=${PY:-/opt/reel/venv/bin/python}
SHOTS=${@:-A_hook B_contraste C_pregunta D_ourense E_provincias F_pueblos G_sintesis H_dilema}
# instantánea del código para poder seguir editando mientras renderiza
rm -rf .snap && cp -r src .snap
for s in $SHOTS; do
  echo "== $s $(date +%T)"
  $PY .snap/render.py -- $s --q final 2>&1 | grep -E "render total|Error|Traceback" 
done
echo "== fin $(date +%T)"
