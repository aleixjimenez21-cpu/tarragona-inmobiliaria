#!/usr/bin/env python3
"""Revisión de legibilidad: oscurece fotogramas un 40 % (móvil a brillo bajo) y monta una hoja de contacto.
uso: python3 tools/check.py salida.jpg img1 img2 ...  (añade las zonas seguras de Reels en rojo)"""
import sys
from PIL import Image, ImageDraw, ImageEnhance
out, fs = sys.argv[1], sys.argv[2:]
cols = 5
tw, th = 432, 768
rows = (len(fs) + cols - 1) // cols
sheet = Image.new('RGB', (tw * cols, th * rows), (40, 40, 40))
for i, f in enumerate(fs):
    im = ImageEnhance.Brightness(Image.open(f).convert('RGB')).enhance(0.6)
    d = ImageDraw.Draw(im)
    d.line([(0, 250), (1080, 250)], fill=(255, 0, 0), width=3)
    d.line([(0, 1540), (1080, 1540)], fill=(255, 0, 0), width=3)
    d.line([(960, 0), (960, 1920)], fill=(255, 0, 0), width=3)
    sheet.paste(im.resize((tw, th), Image.LANCZOS), (tw * (i % cols), th * (i // cols)))
sheet.save(out, quality=90)
