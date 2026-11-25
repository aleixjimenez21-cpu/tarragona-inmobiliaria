"""Utilidades comunes de la skill.
Todos los scripts se ejecutan DESDE LA CARPETA DEL PROYECTO (la que contiene edl.py, plan.py, input/, work/, output/)
y se llaman con la ruta de la skill:  python3 <skill>/scripts/xxx.py
Este módulo carga edl.py del proyecto y da las rutas de cada toma."""
import os, sys, shutil

PROJECT = os.getcwd()
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)
try:
    import edl  # noqa: E402  (edl.py del proyecto)
except ImportError:
    sys.exit("No encuentro edl.py en la carpeta actual. Ejecuta los scripts desde la carpeta del proyecto "
             "(crea una con: python3 <skill>/scripts/new_project.py <carpeta>).")

TAKES = edl.TAKES                      # {"A": "IMG_0001.MOV", ...}  archivos dentro de input/


def tid(k):
    """identificador de la toma (nombre del archivo sin extensión)"""
    return os.path.splitext(os.path.basename(TAKES[k]))[0]


def tpath(k):
    return os.path.join("input", TAKES[k])


IDS = [tid(k) for k in TAKES]


def deep_filter_bin():
    for p in [os.environ.get("DEEP_FILTER", ""), os.path.join(SKILL, "bin", "deep-filter"), shutil.which("deep-filter") or ""]:
        if p and os.path.exists(p):
            return p
    sys.exit("No encuentro el binario deep-filter. Ejecuta primero: bash <skill>/scripts/setup.sh")
