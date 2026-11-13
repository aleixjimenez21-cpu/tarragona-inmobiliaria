"""Capturas fijas de Google Earth convertidas en planos con movimiento.

Cada captura (`input/clips/<nombre>.jpg|png|webp`) puede llevar un `<nombre>.json` con:
  "girar": true            -> vista cenital apaisada: se gira 90° para el formato vertical
  "ancla": [x, y]          -> punto de interés (la aldea) en píxeles de la imagen original
  "radio": [rx, ry]        -> tamaño aproximado de la aldea (píxeles originales), para la cota
  "tapar": [[x0,y0,x1,y1]] -> rótulos de Google a borrar (sólo los trazos de las letras)
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
import skia

EXTS = (".jpg", ".jpeg", ".png", ".webp")


def find_still(clips_dir, name):
    if not clips_dir:
        return None
    for e in EXTS:
        p = os.path.join(clips_dir, name + e)
        if os.path.exists(p):
            return p
    return None


def _remove_labels(img, boxes):
    """Borra rótulos: máscara de trazos claros/saturados dentro de cada caja + inpainting."""
    import cv2
    if not boxes:
        return img
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = np.zeros(img.shape[:2], np.uint8)
    for x0, y0, x1, y1 in boxes:
        sub_v = hsv[y0:y1, x0:x1, 2].astype(int)
        sub_s = hsv[y0:y1, x0:x1, 1].astype(int)
        sub_h = hsv[y0:y1, x0:x1, 0].astype(int)
        white = (sub_v > 175) & (sub_s < 70)
        teal = (sub_h > 55) & (sub_h < 95) & (sub_s > 90) & (sub_v > 90)   # texto/chincheta verdes de Google
        m = (white | teal).astype(np.uint8) * 255
        m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=2)
        mask[y0:y1, x0:x1] = np.maximum(mask[y0:y1, x0:x1], m)
    out = cv2.inpaint(bgr, mask, 5, cv2.INPAINT_TELEA)
    return cv2.cvtColor(out, cv2.COLOR_BGR2RGB)


class StillSource:
    def __init__(self, path):
        from PIL import Image
        side = os.path.splitext(path)[0] + ".json"
        cfg = json.load(open(side, encoding="utf-8")) if os.path.exists(side) else {}
        img = np.array(Image.open(path).convert("RGB"))
        img = _remove_labels(img, cfg.get("tapar", []))
        h0, w0 = img.shape[:2]
        ax, ay = cfg.get("ancla", [w0 / 2, h0 / 2])
        rx, ry = cfg.get("radio", [w0 * 0.12, h0 * 0.12])
        if cfg.get("girar"):
            img = np.ascontiguousarray(np.rot90(img, k=-1))  # 90° horario
            ax, ay = h0 - 1 - ay, ax
            rx, ry = ry, rx
        pil = Image.fromarray(img)
        self.up = 2
        pil = pil.resize((pil.width * self.up, pil.height * self.up), Image.Resampling.LANCZOS)
        arr = np.dstack([np.array(pil), np.full((pil.height, pil.width), 255, np.uint8)])
        self.image = skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kRGBA_8888_ColorType).withDefaultMipmaps()
        self.w, self.h = pil.width, pil.height
        self.anchor = np.array([ax, ay], float) * self.up
        self.radius = np.array([rx, ry], float) * self.up
        self.path = path

    def scale_for(self, zoom, angle_deg, anchor_frame, vp):
        """Escala = zoom x mínima que cubre el viewport sin dejar bordes."""
        vx, vy, vw, vh = vp
        F = np.array(anchor_frame, float)
        th = math.radians(angle_deg)
        c, s = math.cos(th), math.sin(th)
        smin = 0.0
        for cx, cy in ((vx, vy), (vx + vw, vy), (vx, vy + vh), (vx + vw, vy + vh)):
            d = np.array([cx, cy]) - F
            v = np.array([c * d[0] + s * d[1], -s * d[0] + c * d[1]])  # R^-1 d
            for k, lim in ((0, self.w), (1, self.h)):
                A = self.anchor[k]
                if v[k] > 0:
                    smin = max(smin, v[k] / max(lim - A, 1e-3))
                elif v[k] < 0:
                    smin = max(smin, -v[k] / max(A, 1e-3))
        return max(smin * 1.01, 1e-3) * zoom

    def matrix(self, zoom, angle_deg, anchor_frame, vp):
        s = self.scale_for(zoom, angle_deg, anchor_frame, vp)
        m = skia.Matrix()
        m.setTranslate(-self.anchor[0], -self.anchor[1])
        m.postScale(s, s)
        m.postRotate(angle_deg)
        m.postTranslate(anchor_frame[0], anchor_frame[1])
        return m, s

    def draw(self, canvas, zoom=1.0, angle_deg=0.0, anchor_frame=(440.0, 900.0), vp=(0, 0, 1080, 1920)):
        m, _ = self.matrix(zoom, angle_deg, anchor_frame, vp)
        canvas.save()
        canvas.clipRect(skia.Rect.MakeXYWH(*vp))
        canvas.concat(m)
        canvas.drawImage(self.image, 0, 0, skia.SamplingOptions(skia.CubicResampler.Mitchell()))
        canvas.restore()

    def village_screen(self, zoom, angle_deg, anchor_frame, vp):
        """Centro y radios de la aldea en pantalla."""
        _, s = self.matrix(zoom, angle_deg, anchor_frame, vp)
        return np.array(anchor_frame, float), self.radius * s
