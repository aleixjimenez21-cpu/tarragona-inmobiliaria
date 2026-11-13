"""Convierte una captura fija de Google Earth en un plano vertical con movimiento lento
(zoom + leve giro alrededor de un punto de anclaje), para usarla como clip."""
from __future__ import annotations

import json
import math
import os
import subprocess

from PIL import Image, ImageFilter

FW, FH, FPS = 1080, 1920, 30
ANCHOR_FRAME = (440.0, 900.0)   # dónde queda el punto de anclaje (la aldea) en el encuadre
DURATION = 45.0                 # cubre todo el vídeo; el montaje lee el tramo que necesita


def zoom_at(t):
    return 1.0 + 0.012 * t


def angle_at(t):
    return math.radians(0.06 * t)


def load_settings(img_path):
    side = os.path.splitext(img_path)[0] + ".json"
    if os.path.exists(side):
        with open(side, encoding="utf-8") as f:
            return json.load(f)
    return {}


def still_to_clip(img_path, out_path, log=print):
    cfg = load_settings(img_path)
    im = Image.open(img_path).convert("RGB")
    w0, h0 = im.size
    ax, ay = cfg.get("ancla", [w0 / 2, h0 / 2])
    if cfg.get("girar"):  # vista cenital apaisada -> se gira 90° para el vertical
        im = im.transpose(Image.Transpose.ROTATE_270)  # horario
        ax, ay = h0 - 1 - ay, ax
    W, H = im.size
    up = 2
    big = im.resize((W * up, H * up), Image.Resampling.LANCZOS)
    fx, fy = ANCHOR_FRAME
    # escala mínima para cubrir el encuadre alrededor del ancla (con margen para el giro)
    need = max(fx / max(ax, 1), (FW - fx) / max(W - ax, 1), fy / max(ay, 1), (FH - fy) / max(H - ay, 1))
    base = need * 1.06
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{FW}x{FH}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", out_path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(DURATION * FPS)
    for i in range(n):
        t = i / FPS
        s = base * zoom_at(t)
        th = angle_at(t)
        c, si = math.cos(th) / s, math.sin(th) / s
        # fuente = ancla + R(th) * (F - Fv) / s   (en coordenadas de la imagen ampliada)
        a, b = c * up, -si * up
        d, e = si * up, c * up
        cx = ax * up - a * fx - b * fy
        cy = ay * up - d * fx - e * fy
        fr = big.transform((FW, FH), Image.Transform.AFFINE, (a, b, cx, d, e, cy), Image.Resampling.BICUBIC)
        if s > 1.4:
            fr = fr.filter(ImageFilter.UnsharpMask(radius=1.4, percent=55, threshold=2))
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()
    log(f"captura fija {os.path.basename(img_path)} -> plano de {DURATION:.0f} s (escala base {base:.2f}x)")
