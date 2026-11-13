"""Vuelos sobre ortofotos reales del PNOA (© Instituto Geográfico Nacional, CC BY 4.0).

Teselas TMS en Web Mercator (https://tms-pnoa-ma.idee.es), con caché en disco y descarga
paralela. La cámara se define por (lon, lat, zoom continuo, giro). Los saltos largos usan la
interpolación zoom+desplazamiento de van Wijk & Nuij (la del «vuelo» de Google Earth)."""
from __future__ import annotations

import math
import os
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "build", "teselas_pnoa")
URL = "https://tms-pnoa-ma.idee.es/1.0.0/pnoa-ma/{z}/{x}/{y}.jpeg"
MAX_Z = 19
SEA = (0x0E, 0x24, 0x33)
ATTRIBUTION = "Imágenes: PNOA © Instituto Geográfico Nacional"


def lonlat_to_world(lon, lat):
    x = (lon + 180.0) / 360.0
    s = math.sin(math.radians(lat))
    y = 0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)
    return np.array([x, y])


def world_to_lonlat(x, y):
    lon = x * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y))))
    return lon, lat


def meters_per_px(lat, zoom):
    return 156543.03392 * math.cos(math.radians(lat)) / 2 ** zoom


class Cam:
    def __init__(self, lon, lat, zoom, rot=0.0):
        self.lon, self.lat, self.zoom, self.rot = lon, lat, zoom, rot

    @property
    def world(self):
        return lonlat_to_world(self.lon, self.lat)


def van_wijk(c0: Cam, c1: Cam, rho=1.42):
    """Devuelve f(u) -> Cam (u en 0..1) y la duración relativa del vuelo."""
    p0, p1 = c0.world, c1.world
    w0 = 1.0 / 2 ** c0.zoom
    w1 = 1.0 / 2 ** c1.zoom
    dx, dy = p1 - p0
    d2 = dx * dx + dy * dy
    d1 = math.sqrt(d2)
    if d1 < 1e-12:
        S = math.log(w1 / w0) / rho

        def f(u):
            w = w0 * math.exp(rho * u * S)
            x, y = p0
            lon, lat = world_to_lonlat(x, y)
            return Cam(lon, lat, -math.log2(w), c0.rot + (c1.rot - c0.rot) * u)
        return f, abs(S)
    b0 = (w1 * w1 - w0 * w0 + rho ** 4 * d2) / (2 * w0 * rho * rho * d1)
    b1 = (w1 * w1 - w0 * w0 - rho ** 4 * d2) / (2 * w1 * rho * rho * d1)
    r0 = math.log(math.sqrt(b0 * b0 + 1) - b0)
    r1 = math.log(math.sqrt(b1 * b1 + 1) - b1)
    S = (r1 - r0) / rho

    def f(u):
        s = u * S
        coshr0 = math.cosh(r0)
        uu = w0 / (rho * rho * d1) * (coshr0 * math.tanh(rho * s + r0) - math.sinh(r0))
        w = w0 * coshr0 / math.cosh(rho * s + r0)
        x, y = p0[0] + uu * dx, p0[1] + uu * dy
        lon, lat = world_to_lonlat(x, y)
        return Cam(lon, lat, -math.log2(w), c0.rot + (c1.rot - c0.rot) * u)
    return f, S


class TileCache:
    _lock = threading.Lock()

    def __init__(self, cache_dir=CACHE):
        self.dir = cache_dir
        os.makedirs(self.dir, exist_ok=True)
        self.mem = {}
        self.missing = set()
        self.pool = ThreadPoolExecutor(16)
        self.online = None

    def path(self, z, x, y):
        return os.path.join(self.dir, str(z), str(x), f"{y}.img")

    def fetch(self, z, x, y):
        p = self.path(z, x, y)
        if os.path.exists(p):
            return p
        os.makedirs(os.path.dirname(p), exist_ok=True)
        ty = 2 ** z - 1 - y
        tmp = p + f".{os.getpid()}.{threading.get_ident()}.tmp"
        r = subprocess.run(["curl", "-sS", "-f", "-o", tmp, "--max-time", "25", "--retry", "2",
                            URL.format(z=z, x=x, y=ty)], capture_output=True)
        if r.returncode == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 0:
            os.replace(tmp, p)
            return p
        if os.path.exists(tmp):
            os.remove(tmp)
        # sin tesela (fuera de cobertura): marcador vacío
        open(p, "wb").close()
        return p

    def image(self, z, x, y):
        key = (z, x, y)
        if key in self.mem:
            return self.mem[key]
        p = self.path(z, x, y)
        img = None
        if os.path.exists(p) and os.path.getsize(p) > 0:
            try:
                from PIL import Image
                a = np.array(Image.open(p).convert("RGBA")).astype(np.float32)
                # el mar sin datos del PNOA viene en morado oscuro (32,26,38): se pasa a azul océano
                d = np.abs(a[..., :3] - np.array([32, 26, 38], np.float32)).sum(-1)
                k = np.clip(1 - (d - 10) / 25, 0, 1)[..., None]
                a[..., :3] = a[..., :3] * (1 - k) + np.array(SEA, np.float32) * k
                if a[..., 3].mean() < 5 or (a[..., :3].std() < 2.0):
                    img = None
                else:
                    a = np.ascontiguousarray(a.astype(np.uint8))
                    img = skia.Image.fromarray(a, colorType=skia.kRGBA_8888_ColorType).withDefaultMipmaps()
            except Exception:
                img = None
        if len(self.mem) > 6000:
            self.mem.clear()
        self.mem[key] = img
        return img

    def ensure(self, keys):
        need = [k for k in keys if not os.path.exists(self.path(*k))]
        if need:
            list(self.pool.map(lambda k: self.fetch(*k), need))

    def check_online(self):
        if self.online is None:
            p = self.fetch(6, 31, 24)
            self.online = os.path.getsize(p) > 0
        return self.online


class AerialRenderer:
    def __init__(self, cache: TileCache | None = None):
        self.cache = cache or TileCache()
        self._land = None

    def to_screen(self, cam: Cam, vp, lon, lat):
        """Proyección en doble precisión (sin pasar por la matriz float32 de skia)."""
        vx, vy, vw, vh = vp
        sc = 256.0 * 2 ** cam.zoom
        d = (lonlat_to_world(lon, lat) - cam.world) * sc
        th = math.radians(cam.rot)
        x = d[0] * math.cos(th) - d[1] * math.sin(th)
        y = d[0] * math.sin(th) + d[1] * math.cos(th)
        return vx + vw / 2 + x, vy + vh / 2 + y

    def screen_to_world(self, cam: Cam, vp, px, py):
        vx, vy, vw, vh = vp
        sc = 256.0 * 2 ** cam.zoom
        dx, dy = px - (vx + vw / 2), py - (vy + vh / 2)
        th = -math.radians(cam.rot)
        x = dx * math.cos(th) - dy * math.sin(th)
        y = dx * math.sin(th) + dy * math.cos(th)
        return cam.world + np.array([x, y]) / sc

    def visible_tiles(self, cam: Cam, vp, level):
        vx, vy, vw, vh = vp
        pts = [self.screen_to_world(cam, vp, a, b) for a, b in ((vx, vy), (vx + vw, vy), (vx, vy + vh), (vx + vw, vy + vh))]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        n = 2 ** level
        x0, x1 = max(0, int(math.floor(min(xs) * n))), min(n - 1, int(math.floor(max(xs) * n)))
        y0, y1 = max(0, int(math.floor(min(ys) * n))), min(n - 1, int(math.floor(max(ys) * n)))
        return [(level, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]

    def draw(self, canvas, cam: Cam, vp=(0, 0, 1080, 1920), sharp_bias=0.35):
        vx, vy, vw, vh = vp
        canvas.save()
        canvas.clipRect(skia.Rect.MakeXYWH(vx, vy, vw, vh))
        canvas.drawRect(skia.Rect.MakeXYWH(vx, vy, vw, vh), skia.Paint(Color=skia.ColorSetRGB(*SEA)))
        level = int(min(MAX_Z, max(3, math.ceil(cam.zoom + sharp_bias))))
        levels = [max(3, level - 3), level] if level - 3 >= 3 else [level]
        keys = []
        for L in levels:
            keys += self.visible_tiles(cam, vp, L)
        self.cache.ensure(keys)
        canvas.translate(vx + vw / 2, vy + vh / 2)
        canvas.rotate(cam.rot)
        sc = 256.0 * 2 ** cam.zoom
        cx, cy = cam.world
        samp = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
        paint = skia.Paint(AntiAlias=False)
        for (z, x, y) in keys:
            img = self.cache.image(z, x, y)
            if img is None:
                continue
            n = 2 ** z
            l, t = (x / n - cx) * sc, (y / n - cy) * sc
            r, bm = ((x + 1) / n - cx) * sc, ((y + 1) / n - cy) * sc
            canvas.drawImageRect(img, skia.Rect.MakeLTRB(l - 0.3, t - 0.3, r + 0.3, bm + 0.3), samp, paint)
        canvas.restore()
