"""Etalonaje de las fotografías para la destacada «About».

Convierte cada foto a un monocromo cinematográfico con la paleta de la marca:
sombras en negro cálido, luces en hueso. Recorta a 9:16 con margen para el
movimiento de cámara (Ken Burns) que se aplica en la animación.

Uso: python3 grade.py <carpeta_fotos_origen> <carpeta_salida>
"""
import sys
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

SHADOW = (16, 15, 14)     # negro cálido, abierto: look natural
MID = (124, 121, 116)     # gris piedra
HIGH = (242, 239, 233)    # blanco roto

# nombre_salida: (archivo, x0 del recorte 9:16, exposición, contraste, gamma)
PHOTOS = {
    "corridor": ("736a76bc-image.jpg", 70, 0.98, 1.06, 1.00),
    "workshop": ("b7993196-image.jpg", None, 0.98, 1.12, 1.02),
    "hardhat": ("0516d47e-image.jpg", "portrait", 1.00, 1.06, 0.98),
    "galleria": ("da50a4d5-image.jpg", 190, 1.00, 1.08, 1.02),
    "window": ("95b6ce37-image.jpg", 130, 0.96, 1.06, 1.02),
    "duomo": ("f5376582-image.jpg", 170, 0.98, 1.10, 1.02),
    "night": ("599ed169-image.jpg", None, 1.12, 1.04, 0.95),
}


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def tone_lut(exposure, contrast, gamma):
    lut = []
    for v in range(256):
        x = v / 255.0
        x = min(1.0, x * exposure)
        x = x ** gamma
        # curva S suave alrededor del gris medio
        x = 0.5 + (x - 0.5) * contrast
        x = max(0.0, min(1.0, x))
        lut.append(x)
    return lut


def colorize(gray, lut):
    r, g, b = [], [], []
    for v in range(256):
        t = lut[v]
        c = lerp(SHADOW, MID, t / 0.5) if t < 0.5 else lerp(MID, HIGH, (t - 0.5) / 0.5)
        r.append(c[0]); g.append(c[1]); b.append(c[2])
    return Image.merge("RGB", (gray.point(r), gray.point(g), gray.point(b)))


def crop_916(img, x0):
    w, h = img.size
    target = 9 / 16
    if w / h > target:
        cw = int(h * target)
        if x0 is None:
            x0 = (w - cw) // 2
        return img.crop((x0, 0, x0 + cw, h))
    ch = int(w / target)
    y0 = (h - ch) // 2
    return img.crop((0, y0, w, y0 + ch))


for name, (fn, x0, exp, con, gam) in PHOTOS.items():
    img = ImageOps.exif_transpose(Image.open(SRC / fn)).convert("RGB")
    if x0 == "portrait":
        # retrato en obra: encuadre 4:5 sobre cara y casco
        img = img.crop((110, 190, 1830, 2340))
    else:
        img = crop_916(img, x0)
    gray = ImageOps.grayscale(img)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=2, percent=40, threshold=2))
    out = colorize(gray, tone_lut(exp, con, gam))
    if x0 == "portrait":
        out = out.resize((900, int(900 * out.height / out.width)), Image.LANCZOS)
    else:
        out = out.resize((1188, 2112), Image.LANCZOS)  # 110 % del lienzo
    out.save(OUT / f"{name}.jpg", quality=95, subsampling=0)
    print(name, out.size)
