"""Prepara el logo de la marca para los gráficos: versión blanca (para fondos oscuros: tarjeta final) y oscura
(para la palabra grande detrás de la cabeza sobre pared clara), con fondo transparente y bordes nítidos a 4x.
Acepta un PNG con transparencia o una imagen con el logo oscuro sobre fondo claro (se recorta y se "desmata").
El color de acento del logo (p. ej. un punto de color) se conserva.
Uso: python3 <skill>/scripts/prep_logo.py <logo.png|jpg>   ->  input/brand/logo_blanco_hd.png, input/brand/logo_negro_hd.png"""
import sys, os
import numpy as np, cv2
from PIL import Image

src = sys.argv[1]
im = Image.open(src)
os.makedirs("input/brand", exist_ok=True)
if im.mode == "RGBA" and np.asarray(im)[..., 3].min() < 250:
    arr = np.asarray(im).astype(np.float32)
    rgb, a = arr[..., :3], arr[..., 3] / 255
else:
    c = np.asarray(im.convert("RGB")).astype(np.float32)
    H, W, _ = c.shape
    mn = c.min(2); sat = c.max(2) - mn
    mask = (mn < 120) | ((sat > 120) & (c.max(2) > 150))
    ys, xs = np.where(mask)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    pad = int((y1 - y0) * 0.12)
    c = c[max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad]
    bg = np.median(np.concatenate([c[:3].reshape(-1, 3), c[-3:].reshape(-1, 3)]), 0)
    a = np.clip((bg.min() - c.min(2)) / max(1, bg.min()), 0, 1)
    rgb = np.clip((c - (1 - a[..., None]) * bg) / np.maximum(a[..., None], 1e-3), 0, 255)
sat = rgb.max(2) - rgb.min(2)
accent = (sat > 80) & (a > 0.05)
acc_col = np.median(rgb[accent], 0) if accent.sum() > 20 else None
S = 4
A = cv2.GaussianBlur(cv2.resize(a, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC), (0, 0), 1.2)
A = np.clip((A - 0.5) * 2.2 + 0.5, 0, 1)                           # bordes tipo vector
ACC = cv2.resize(accent.astype(np.float32), None, fx=S, fy=S, interpolation=cv2.INTER_LINEAR) > 0.5
for name, base in [("logo_blanco_hd.png", (255, 255, 255)), ("logo_negro_hd.png", (20, 20, 22))]:
    out = np.zeros(A.shape + (3,), np.float32); out[:] = base
    if acc_col is not None: out[ACC] = acc_col
    Image.fromarray(np.dstack([out, A * 255]).astype(np.uint8), "RGBA").save(f"input/brand/{name}")
    print("input/brand/" + name, A.shape[::-1])
