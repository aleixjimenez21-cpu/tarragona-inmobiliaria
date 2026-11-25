"""Crea la carpeta de un proyecto de edición nuevo.
Uso: python3 <skill>/scripts/new_project.py <carpeta_proyecto> [videos...]
Crea input/ (tomas), input/brand/ (logo), input/broll/ (clips propios), work/, output/ y copia las plantillas edl.py y plan.py."""
import os, sys, shutil
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv) < 2:
    sys.exit(__doc__)
p = sys.argv[1]
for d in ["input/brand", "input/broll", "work/audio", "work/clips", "output"]:
    os.makedirs(os.path.join(p, d), exist_ok=True)
for f in ["edl.py", "plan.py"]:
    dst = os.path.join(p, f)
    if not os.path.exists(dst):
        shutil.copy(os.path.join(SKILL, "templates", f), dst)
for v in sys.argv[2:]:
    shutil.copy(v, os.path.join(p, "input", os.path.basename(v)))
with open(os.path.join(p, ".gitignore"), "w") as fh:
    fh.write("input/\nwork/\noutput/*.mp4\noutput/*.wav\noutput/*.jpg\n__pycache__/\n")
print("Proyecto creado en", p)
print("Siguiente: copia las tomas a input/, rellena TAKES en edl.py y ejecuta prep_audio.py y transcribe.py desde esa carpeta.")
