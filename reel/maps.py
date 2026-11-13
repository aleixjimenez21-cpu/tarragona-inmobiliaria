"""Mapas estilizados (TopoJSON de es-atlas © IGN / world-atlas © Natural Earth)."""
from __future__ import annotations

import json
import math
import os

import numpy as np
import skia

from gfx import (BLUE, GRAPHITE, GREEN, GREY, PAPER, col, fill_paint, glow_paint, stroke_paint)

HERE = os.path.dirname(os.path.abspath(__file__))
COS0 = math.cos(math.radians(40.5))


def _decode(path, obj_names=None):
    d = json.load(open(os.path.join(HERE, "data", path)))
    tr = d.get("transform")
    arcs = []
    for a in d["arcs"]:
        a = np.array(a, float)
        if tr:
            a = np.cumsum(a, axis=0) * tr["scale"] + tr["translate"]
        arcs.append(a)

    def ring(ix):
        pts = []
        for i in ix:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts.append(a if not pts else a[1:])
        return np.vstack(pts)

    out = {}
    for name, o in d["objects"].items():
        if obj_names and name not in obj_names:
            continue
        feats = []
        for g in o["geometries"]:
            polys = []
            if g["type"] == "Polygon":
                polys = [[ring(r) for r in g["arcs"]]]
            elif g["type"] == "MultiPolygon":
                polys = [[ring(r) for r in p] for p in g["arcs"]]
            feats.append({"id": g.get("id"), "name": (g.get("properties") or {}).get("name", ""), "polys": polys})
        out[name] = feats
    return out


class Atlas:
    def __init__(self):
        es = _decode("es_provinces.json")
        self.provinces = {f["name"]: f for f in es["provinces"]}
        self.regions = {f["name"]: f for f in es["autonomous_regions"]}
        w = _decode("world_countries_50m.json", ["countries"])["countries"]
        self.countries = {f["name"]: f for f in w if f["name"] in ("Portugal", "France", "Andorra", "Morocco")}
        # sin Canarias (fuera de encuadre) ni Ceuta/Melilla
        for k in list(self.regions):
            if k in ("Canarias", "Ciudad Autónoma de Ceuta", "Ciudad Autónoma de Melilla") or k.startswith("Gibraltar"):
                self.regions.pop(k)

    def find(self, table, *keys):
        for k, v in table.items():
            if all(x.lower() in k.lower() for x in keys):
                return v
        raise KeyError(keys)


class View:
    """lon/lat -> píxeles. (lon0, lat0) en (sx, sy), escala en px por grado de latitud."""

    def __init__(self, lon0, lat0, scale, sx, sy):
        self.lon0, self.lat0, self.k, self.sx, self.sy = lon0, lat0, scale, sx, sy

    def __call__(self, lon, lat):
        return (self.sx + (np.asarray(lon) - self.lon0) * COS0 * self.k,
                self.sy - (np.asarray(lat) - self.lat0) * self.k)

    @staticmethod
    def lerp(a: "View", b: "View", t):
        # interpolación logarítmica de la escala (zoom natural)
        k = math.exp(math.log(a.k) * (1 - t) + math.log(b.k) * t)
        f = (k - a.k) / (b.k - a.k) if abs(b.k - a.k) > 1e-9 else t
        return View(a.lon0 + (b.lon0 - a.lon0) * f, a.lat0 + (b.lat0 - a.lat0) * f, k,
                    a.sx + (b.sx - a.sx) * t, a.sy + (b.sy - a.sy) * t)


def feature_path(feat, view: View):
    p = skia.Path()
    for poly in feat["polys"]:
        for r in poly:
            x, y = view(r[:, 0], r[:, 1])
            p.moveTo(float(x[0]), float(y[0]))
            for xx, yy in zip(x[1:].tolist(), y[1:].tolist()):
                p.lineTo(xx, yy)
            p.close()
    return p


def draw_feature(c, feat, view, fill=None, fill_alpha=1.0, line=None, line_alpha=1.0, width=2.0, glow=0.0):
    p = feature_path(feat, view)
    if fill is not None and fill_alpha > 0:
        c.drawPath(p, fill_paint(fill, fill_alpha))
    if glow > 0 and line is not None:
        c.drawPath(p, glow_paint(line, 0.6 * glow * line_alpha, 10, width * 3))
    if line is not None and line_alpha > 0:
        c.drawPath(p, stroke_paint(line, line_alpha, width))


def points_in_feature(feat, pts):
    """Ray casting vectorizado (lon, lat)."""
    pts = np.asarray(pts)
    inside = np.zeros(len(pts), bool)
    for poly in feat["polys"]:
        for r in poly:
            x, y = r[:, 0], r[:, 1]
            x2, y2 = np.roll(x, -1), np.roll(y, -1)
            px, py = pts[:, 0:1], pts[:, 1:2]
            cond = ((y > py) != (y2 > py)) & (px < (x2 - x) * (py - y) / (y2 - y + 1e-12) + x)
            inside ^= (cond.sum(1) % 2 == 1)
    return inside


def sample_points(feat, n, seed, min_dist=0.0):
    rs = np.random.RandomState(seed)
    allp = np.vstack([r for poly in feat["polys"] for r in poly])
    lo, hi = allp.min(0), allp.max(0)
    out = []
    for _ in range(60):
        if len(out) >= n:
            break
        cand = rs.uniform(lo, hi, (n * 4, 2))
        cand = cand[points_in_feature(feat, cand)]
        for q in cand:
            if min_dist and out and np.min(np.hypot(*(np.array(out) - q).T)) < min_dist:
                continue
            out.append(q)
            if len(out) >= n:
                break
    return np.array(out)


def feature_centroid(feat):
    allp = np.vstack([poly[0] for poly in feat["polys"]])
    big = max((poly[0] for poly in feat["polys"]), key=len)
    return big.mean(0)


def map_background(c, w, h):
    """Fondo grafito con retícula muy sutil."""
    c.drawRect(skia.Rect.MakeWH(w, h), fill_paint(GRAPHITE))
    p = stroke_paint((0x22, 0x25, 0x2A), 1.0, 1.2)
    for x in range(0, w + 1, 60):
        c.drawLine(x, 0, x, h, p)
    for y in range(0, h + 1, 60):
        c.drawLine(0, y, w, y, p)
