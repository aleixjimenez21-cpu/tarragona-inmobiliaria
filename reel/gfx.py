"""Utilidades 2D con skia: paleta, tipografía, easing, textos, planta del piso, iconos."""
from __future__ import annotations

import math
import os

import numpy as np
import skia

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))

# Zonas seguras de Reels
SAFE_TOP, SAFE_BOTTOM, SAFE_RIGHT, SAFE_LEFT = 250, H - 380, W - 120, 70
CX = (SAFE_LEFT + SAFE_RIGHT) / 2  # centro óptico de la zona segura (515)
SAFE_W = SAFE_RIGHT - SAFE_LEFT    # 890

# Paleta
GRAPHITE = (0x16, 0x18, 0x1B)
PAPER = (0xF2, 0xEF, 0xEA)
ORANGE = (0xFF, 0x5A, 0x1F)
BLUE = (0x2F, 0x6B, 0xFF)
GREEN = (0x7F, 0xA5, 0x8A)
GREY = (0x8A, 0x8F, 0x98)


def col(rgb, a=1.0) -> int:
    r, g, b = rgb[:3]
    return skia.ColorSetARGB(int(max(0, min(1, a)) * 255), int(r), int(g), int(b))


def mix(c1, c2, t):
    return tuple(a + (b - a) * t for a, b in zip(c1, c2))


# --------------------------------------------------------------------------------------
# Easing
# --------------------------------------------------------------------------------------
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def prog(t, t0, t1):
    if t1 <= t0:
        return 1.0 if t >= t0 else 0.0
    return clamp((t - t0) / (t1 - t0))


def lerp(a, b, t):
    return a + (b - a) * t


def ease_out(t):
    return 1 - (1 - t) ** 3


def ease_in(t):
    return t ** 3


def ease_io(t):
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out_expo(t):
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def back_out(t, s=1.9):
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def elastic_out(t):
    if t <= 0 or t >= 1:
        return clamp(t)
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1


def punch_curve(dt, attack=0.05, decay=0.16):
    """0 -> 1 rápido y vuelta exponencial (golpe de zoom)."""
    if dt < 0:
        return 0.0
    if dt < attack:
        return ease_out(dt / attack)
    return math.exp(-(dt - attack) / decay)


# --------------------------------------------------------------------------------------
# Tipografía
# --------------------------------------------------------------------------------------
_TF = {}
FONT_FILES = {
    "xb": "InterDisplay-ExtraBold.otf",
    "b": "InterDisplay-Bold.otf",
    "sb": "InterDisplay-SemiBold.otf",
    "mono": "IBMPlexMono-Bold.ttf",
    "mono_sb": "IBMPlexMono-SemiBold.ttf",
    "mono_m": "IBMPlexMono-Medium.ttf",
}


def font(kind: str, size: float) -> skia.Font:
    if kind not in _TF:
        _TF[kind] = skia.Typeface.MakeFromFile(os.path.join(HERE, "fonts", FONT_FILES[kind]))
    f = skia.Font(_TF[kind], size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    f.setHinting(skia.FontHinting.kNone)
    return f


def text_width(text, f: skia.Font, tracking=0.0):
    if not tracking:
        return f.measureText(text)
    return sum(f.measureText(ch) for ch in text) + tracking * f.getSize() * (len(text) - 1)


def draw_text(c: skia.Canvas, text, x, y, f: skia.Font, color, alpha=1.0, align="center",
              tracking=0.0, stroke=0.0, stroke_color=GRAPHITE, stroke_alpha=None, shadow=0.0):
    """y = línea base. tracking en em."""
    w = text_width(text, f, tracking)
    if align == "center":
        x0 = x - w / 2
    elif align == "right":
        x0 = x - w
    else:
        x0 = x

    def _draw(paint):
        if not tracking:
            c.drawString(text, x0, y, f, paint)
        else:
            xx = x0
            for ch in text:
                c.drawString(ch, xx, y, f, paint)
                xx += f.measureText(ch) + tracking * f.getSize()

    if shadow > 0:
        sp = skia.Paint(AntiAlias=True, Color=col(GRAPHITE, 0.55 * alpha))
        sp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, shadow))
        _draw(sp)
    if stroke > 0:
        sp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=stroke,
                        StrokeJoin=skia.Paint.kRound_Join, Color=col(stroke_color, (stroke_alpha if stroke_alpha is not None else 1.0) * alpha))
        _draw(sp)
    _draw(skia.Paint(AntiAlias=True, Color=col(color, alpha)))
    return w


def text_bounds_h(f: skia.Font):
    m = f.getMetrics()
    return -m.fAscent, m.fDescent


def rrect(c, x, y, w, h, r, color, alpha=1.0, stroke=0.0, stroke_color=None, blur=0.0):
    p = skia.Paint(AntiAlias=True, Color=col(color, alpha))
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), p)
    if stroke:
        p2 = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=stroke,
                        Color=col(stroke_color or PAPER, alpha))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), p2)


def pill_label(c, text, x, y, f, fg, bg, alpha=1.0, pad_x=26, pad_y=16, align="center", stroke=0.0,
               stroke_color=None, radius=None, tracking=0.0):
    """Etiqueta con fondo. (x, y) = centro (align=center) o borde izq; y = centro vertical."""
    tw = text_width(text, f, tracking)
    asc, desc = text_bounds_h(f)
    cap = f.getSize() * 0.72
    w, h = tw + 2 * pad_x, cap + 2 * pad_y
    x0 = x - w / 2 if align == "center" else x
    rrect(c, x0, y - h / 2, w, h, radius if radius is not None else h / 2, bg, alpha, stroke, stroke_color)
    draw_text(c, text, x0 + pad_x, y + cap / 2, f, fg, alpha, align="left", tracking=tracking)
    return w, h


def glow_paint(color, alpha, sigma, width=None):
    p = skia.Paint(AntiAlias=True, Color=col(color, alpha))
    if width is not None:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(width)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma))
    return p


def stroke_paint(color, alpha, width, cap=skia.Paint.kRound_Cap, dash=None):
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width, Color=col(color, alpha))
    p.setStrokeCap(cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    if dash:
        p.setPathEffect(skia.DashPathEffect.Make(dash, 0))
    return p


def fill_paint(color, alpha=1.0):
    return skia.Paint(AntiAlias=True, Color=col(color, alpha))


def poly_path(pts, close=True):
    p = skia.Path()
    if len(pts) == 0:
        return p
    p.moveTo(float(pts[0][0]), float(pts[0][1]))
    for q in pts[1:]:
        p.lineTo(float(q[0]), float(q[1]))
    if close:
        p.close()
    return p


def partial_polyline(pts, frac):
    """Devuelve el tramo inicial de una polilínea (para animar el dibujado)."""
    pts = np.asarray(pts, float)
    if frac >= 1 or len(pts) < 2:
        return pts
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    L = seg.sum() * max(0.0, frac)
    out = [pts[0]]
    acc = 0.0
    for i, s in enumerate(seg):
        if acc + s >= L:
            f = (L - acc) / s if s > 0 else 0
            out.append(pts[i] + (pts[i + 1] - pts[i]) * f)
            return np.array(out)
        acc += s
        out.append(pts[i + 1])
    return np.array(out)


# --------------------------------------------------------------------------------------
# Planta del piso de Madrid (60 m²: 7,5 x 8 m) en metros locales
# --------------------------------------------------------------------------------------
PLAN_W, PLAN_D = 7.5, 8.0


def _arc(cx, cy, r, a0, a1, n=8):
    return [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in np.linspace(a0, a1, n)]


def plan_geometry():
    """Polilíneas de la planta: (exterior, tabiques, puertas). Origen en el centro."""
    w, d = PLAN_W, PLAN_D
    ox, oy = -w / 2, -d / 2

    def P(pts):
        return [(x + ox, y + oy) for x, y in pts]

    outer = P([(0, 0), (w, 0), (w, d), (0, d), (0, 0)])
    walls = [
        # tabique salón / zona de noche (y = 4.6), con hueco de paso 3.0–3.9
        P([(0, 4.6), (3.0, 4.6)]), P([(3.9, 4.6), (w, 4.6)]),
        # dormitorio 1 | dormitorio 2 (x = 3.6)
        P([(3.6, 4.6), (3.6, d)]),
        # baño (x 5.3–7.5, y 4.6–6.4)
        P([(5.3, 4.6), (5.3, 5.5)]), P([(5.3, 6.3), (5.3, 6.4)]), P([(5.3, 6.4), (w, 6.4)]),
        # cocina abierta: barra
        P([(5.2, 0.0), (5.2, 1.9)]),
    ]
    doors = [
        P(_arc(3.0, 4.6, 0.9, 0, math.pi / 2)),
        P(_arc(5.3, 5.5, 0.8, math.pi / 2, math.pi)),
        P([(3.0, 4.6), (3.0, 5.5)]),
    ]
    # ventanas (marcas dobles en fachada)
    windows = [P([(1.0, 0.0), (2.6, 0.0)]), P([(1.0, d), (2.6, d)]), P([(4.6, d), (6.4, d)])]
    return outer, walls, doors, windows


def square_geometry(side):
    s = side / 2
    return [(-s, -s), (s, -s), (s, s), (-s, s), (-s, -s)]


def draw_plan(c, mapf, alpha=1.0, draw=1.0, width=6.0, tabiques=1.0, glow=True, morph_sq=0.0,
              sq_side=3.0, color=BLUE, fill_alpha=0.16, scale=1.0):
    """Dibuja la planta. `mapf(x, y)` (metros reales, origen en el centro) -> píxeles.
    scale: factor lineal (sqrt(m2/60)). draw: progreso del trazado (0..1).
    morph_sq: 0 = planta, 1 = cuadrado de sq_side metros."""
    outer, walls, doors, windows = plan_geometry()
    S = lambda pts: [(x * scale, y * scale) for x, y in pts]
    outer, walls, doors, windows = S(outer), [S(w) for w in walls], [S(d) for d in doors], [S(w) for w in windows]
    if morph_sq > 0:
        sq = square_geometry(sq_side)
        outer = [(lerp(ox, sx, morph_sq), lerp(oy, sy, morph_sq)) for (ox, oy), (sx, sy) in zip(outer, sq)]
        tabiques *= 1 - morph_sq
    ptsO = np.array([mapf(x, y) for x, y in outer])
    if fill_alpha > 0 and draw > 0.6:
        c.drawPath(poly_path(ptsO), fill_paint(color, fill_alpha * alpha * prog(draw, 0.6, 1.0)))
    if glow:
        c.drawPath(poly_path(partial_polyline(ptsO, draw), close=False), glow_paint(color, 0.55 * alpha, width * 1.4, width * 2.2))
    c.drawPath(poly_path(partial_polyline(ptsO, draw), close=False), stroke_paint(color, alpha, width, cap=skia.Paint.kSquare_Cap))
    ta = alpha * tabiques * prog(draw, 0.35, 1.0)
    if ta > 0.01:
        for wl in walls:
            pts = np.array([mapf(x, y) for x, y in wl])
            c.drawPath(poly_path(partial_polyline(pts, prog(draw, 0.35, 1.0)), close=False),
                       stroke_paint(color, ta, width * 0.62, cap=skia.Paint.kSquare_Cap))
        for dr in doors:
            pts = np.array([mapf(x, y) for x, y in dr])
            c.drawPath(poly_path(pts, close=False), stroke_paint(color, ta * 0.7, max(1.5, width * 0.3)))
        for wn in windows:
            pts = np.array([mapf(x, y) for x, y in wn])
            c.drawPath(poly_path(pts, close=False), stroke_paint(PAPER, ta * 0.85, max(2.0, width * 0.55), cap=skia.Paint.kButt_Cap))


def draw_bathtub(c, cx, cy, s, color=BLUE, alpha=1.0):
    """Icono de bañera (s = ancho en px)."""
    w, h = s, s * 0.42
    p = stroke_paint(color, alpha, max(2.5, s * 0.06))
    r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx - w / 2, cy - h / 2, w, h), h * 0.45, h * 0.45)
    c.drawRRect(r, p)
    # grifo
    path = skia.Path()
    path.moveTo(cx - w * 0.36, cy - h / 2)
    path.lineTo(cx - w * 0.36, cy - h * 1.15)
    path.lineTo(cx - w * 0.22, cy - h * 1.15)
    c.drawPath(path, p)
    # patas
    c.drawLine(cx - w * 0.3, cy + h / 2, cx - w * 0.34, cy + h * 0.8, p)
    c.drawLine(cx + w * 0.3, cy + h / 2, cx + w * 0.34, cy + h * 0.8, p)
    # burbujas
    bp = stroke_paint(color, alpha * 0.8, max(1.5, s * 0.03))
    for dx, dy, rr in ((0.1, -0.85, 0.06), (0.22, -1.05, 0.045), (0.32, -0.8, 0.035)):
        c.drawCircle(cx + w * dx, cy + h * dy, s * rr, bp)


def draw_house_icon(c, cx, cy, s, fill=GREEN, line=PAPER, alpha=1.0, stone=True):
    """Casa de piedra estilizada (s = ancho)."""
    w, h = s, s * 0.62
    body = skia.Rect.MakeXYWH(cx - w / 2, cy - h * 0.1, w, h * 0.75)
    roof = poly_path([(cx - w * 0.6, cy - h * 0.06), (cx, cy - h * 0.62), (cx + w * 0.6, cy - h * 0.06)])
    c.drawRect(body, fill_paint(fill, alpha))
    c.drawPath(roof, fill_paint(mix(fill, GRAPHITE, 0.35), alpha))
    lp = stroke_paint(line, alpha * 0.9, max(2, s * 0.035))
    c.drawRect(body, lp)
    c.drawPath(roof, lp)
    if stone:
        sp = stroke_paint(mix(fill, GRAPHITE, 0.45), alpha * 0.8, max(1.2, s * 0.018))
        for row in range(3):
            yy = cy - h * 0.1 + h * 0.75 * (row + 1) / 4
            c.drawLine(cx - w / 2, yy, cx + w / 2, yy, sp)
            for k in range(4):
                xx = cx - w / 2 + w * (k + (0.5 if row % 2 else 0.25)) / 4
                c.drawLine(xx, yy - h * 0.75 / 4, xx, yy, sp)
    # puerta
    c.drawRect(skia.Rect.MakeXYWH(cx - w * 0.1, cy + h * 0.3, w * 0.2, h * 0.35), fill_paint(GRAPHITE, alpha * 0.85))


def draw_pin(c, x, y, r, color, alpha=1.0, pulse=0.0):
    if pulse > 0:
        c.drawCircle(x, y, r * (1 + 2.2 * pulse), stroke_paint(color, alpha * (1 - pulse) * 0.9, 3))
    c.drawCircle(x, y, r * 1.9, glow_paint(color, 0.5 * alpha, r))
    c.drawCircle(x, y, r, fill_paint(color, alpha))
    c.drawCircle(x, y, r * 0.42, fill_paint(PAPER, alpha))


def fmt_es(n: int) -> str:
    return f"{int(round(n)):,}".replace(",", ".")


# --------------------------------------------------------------------------------------
# Imagen <-> numpy
# --------------------------------------------------------------------------------------
def surface_to_rgba(surf: skia.Surface) -> np.ndarray:
    return surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)


def image_from_rgba(arr: np.ndarray) -> skia.Image:
    return skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kRGBA_8888_ColorType)
