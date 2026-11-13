"""Composición de las 6 escenas. Todo se ancla a los tiempos de la voz (Timeline)."""
from __future__ import annotations

import math
import os
import subprocess

import numpy as np
import skia

import maps
from engine3d import ABarca, Camera, Candelago, Madrid
from gfx import (BLUE, CX, FPS, GRAPHITE, GREEN, GREY, H, ORANGE, PAPER, SAFE_LEFT, SAFE_RIGHT, W, back_out, clamp,
                 col, draw_bathtub, draw_house_icon, draw_pin, draw_plan, draw_text, ease_in, ease_io, ease_out,
                 fill_paint, fmt_es, font, glow_paint, lerp, mix, partial_polyline, pill_label, poly_path, prog,
                 punch_curve, rrect, stroke_paint, text_width, PLAN_W, PLAN_D)
from subs import build_pages, draw_subs
from stills import StillSource, find_still
import aerial as AE

CANDELAGO_LONLAT = (-8.9621, 43.2710)   # de la captura de Google Earth del autor (43°16'15.6"N 8°57'43.6"W)
MADRID_LONLAT = (-3.7038, 40.4168)
MADRID_ROOF = (-3.68300, 40.42620)       # manzana del barrio de Salamanca (PNOA)


def dms(v, pos, neg):
    h = pos if v >= 0 else neg
    v = abs(v)
    d = int(v)
    m = int((v - d) * 60)
    sec = (v - d - m / 60) * 3600
    return f"{d}°{m:02d}'{sec:04.1f}\"{h}"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORNER = (890.0, 368.0)
CORNER_PPM = 14.0
CENTER = (CX, 850.0)
CENTER_PPM = 52.0
LIGHT_GREY = (0xB9, 0xBD, 0xC4)


# --------------------------------------------------------------------------------------
class Track:
    """Valor animado: .to(t0, dur, valor, easing)."""

    def __init__(self, v0):
        self.keys = [(-1e9, 0.0, v0, ease_io)]

    def to(self, t0, dur, v, ease=ease_io):
        self.keys.append((t0, dur, v, ease))
        return self

    def __call__(self, t):
        v = self.keys[0][2]
        for t0, dur, tgt, e in self.keys[1:]:
            if t < t0:
                break
            k = e(prog(t, t0, t0 + dur)) if dur > 0 else 1.0
            v = v + (tgt - v) * k
        return v


class ClipReader:
    """Lee un clip de Google Earth (si existe) recortando la interfaz y en bucle."""

    def __init__(self, path, start=0.0, w=W, h=H, ui_crop=0.10):
        vf = (f"crop=iw*{1 - 2 * ui_crop}:ih*{1 - 2 * ui_crop},scale={w}:{h}:force_original_aspect_ratio=increase,"
              f"crop={w}:{h},fps={FPS},format=rgba")
        self.w, self.h = w, h
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-stream_loop", "-1", "-ss", f"{start:.3f}", "-i", path,
                                   "-vf", vf, "-f", "rawvideo", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.last = None

    def next(self):
        buf = self.p.stdout.read(self.w * self.h * 4)
        if len(buf) == self.w * self.h * 4:
            self.last = np.frombuffer(buf, np.uint8).reshape(self.h, self.w, 4)
        return self.last


# --------------------------------------------------------------------------------------
class Reel:
    def __init__(self, tl, ss=2.0, clips_dir=None):
        self.tl, self.ss = tl, ss
        s, e = tl.s, tl.e
        self.b = [0.0, s("candelago") - 0.08, s("espera"), s("sabes"), s("espana"), s("elegir"), tl.duration]
        self.tw = s("galicia") - 0.10           # inicio del whip pan
        self.tw_end = self.tw + 0.34
        self.pages = build_pages(tl.toks)
        self.clips_dir = clips_dir
        self.clip_paths = {}
        if clips_dir:
            for name in ("madrid", "candelago", "a_barca"):
                p = os.path.join(clips_dir, f"{name}.mp4")
                if os.path.exists(p):
                    self.clip_paths[name] = p
        self.stills = {}
        for name in ("candelago", "a_barca"):
            if name not in self.clip_paths:
                p = find_still(clips_dir, name)
                if p:
                    self.stills[name] = p
        self._still_obj = {}
        self.aer = None
        if os.environ.get("REEL_SIN_PNOA") != "1":
            try:
                r = AE.AerialRenderer()
                if r.cache.check_online():
                    self.aer = r
            except Exception:
                self.aer = None
        self._models = {}
        self._readers = {}
        # gancho: whip (tw) -> vuelo por el mapa -> zoom a la imagen real (tc)
        self.tc = max(self.tw + 1.0, s("pueblo") - 0.42)
        self._build_tracks()
        self.punches = [(0.0, 0.07), (s("p390"), 0.05), (s("p150"), 0.06), (s("m23"), 0.05), (s("espera"), 0.05),
                        (s("p59"), 0.06), (s("nueve"), 0.05), (s("cero"), 0.15), (s("trampa"), 0.04),
                        (s("miles"), 0.04), (s("m60"), 0.05), (s("p400"), 0.07)]
        self.shakes = [(s("cero"), 22.0, 0.55), (s("espera"), 7.0, 0.3), (s("trampa"), 10.0, 0.35),
                       (s("pueblo"), 9.0, 0.3), (s("p390"), 6.0, 0.25)]
        self.punches += [(s("pueblo"), 0.06), (self.tc, 0.05)]
        # desdoble RGB en los golpes fuertes
        self.rgb_hits = [(0.0, 5.0), (s("p390"), 9.0), (self.tc, 12.0), (s("pueblo"), 10.0), (s("espera"), 8.0),
                         (s("cero"), 16.0), (s("trampa"), 9.0), (s("p400"), 8.0)]

    # ---- recursos perezosos ---------------------------------------------------------
    def still(self, name):
        if name not in self._still_obj:
            self._still_obj[name] = StillSource(self.stills[name])
        return self._still_obj[name]

    def still_image(self, name, zoom, angle, anchor_frame=(440.0, 900.0), vp=(0, 0, W, H)):
        surf = skia.Surface(W, H)
        c = surf.getCanvas()
        c.clear(col(GRAPHITE))
        self.still(name).draw(c, zoom, angle, anchor_frame, vp)
        return surf.makeImageSnapshot().withDefaultMipmaps()

    def model(self, name):
        if name not in self._models:
            self._models[name] = {"madrid": Madrid, "cand": Candelago, "abarca": ABarca, "atlas": maps.Atlas}[name]()
        return self._models[name]

    def clip_frame(self, name, t_start):
        if name not in self.clip_paths:
            return None
        if name not in self._readers:
            self._readers[name] = ClipReader(self.clip_paths[name], start=max(0.0, t_start))
        return self._readers[name].next()

    # ---- pistas de la planta ----------------------------------------------------------
    def _build_tracks(self):
        s, e, b = self.tl.s, self.tl.e, self.b
        cx = Track(CORNER[0]); cy = Track(CORNER[1]); ppm = Track(CORNER_PPM)
        area = Track(60.0); morph = Track(0.0); alpha = Track(1.0)
        # escena 2: al centro y de 60 a 23 m²
        for tr, v in ((cx, CENTER[0]), (cy, CENTER[1]), (ppm, CENTER_PPM)):
            tr.to(s("madrid2"), 0.55, v)
        area.to(s("m23"), 0.6, 23.0, ease_out)
        # escena 3: a la esquina, vuelve al centro y de 23 a 9 m² (bañera)
        for tr, v in ((cx, CORNER[0]), (cy, CORNER[1]), (ppm, CORNER_PPM)):
            tr.to(b[2], 0.3, v)
        for tr, v in ((cx, CENTER[0]), (cy, CENTER[1]), (ppm, CENTER_PPM)):
            tr.to(s("loque"), 0.5, v)
        area.to(s("nueve"), 0.6, 9.0, ease_out)
        morph.to(s("nueve") + 0.15, 0.5, 1.0)
        # escena 4: a la esquina; desaparece con un pop en "CERO"
        for tr, v in ((cx, CORNER[0]), (cy, CORNER[1]), (ppm, CORNER_PPM)):
            tr.to(b[3], 0.35, v)
        alpha.to(s("cero"), 0.2, 0.0, ease_in)
        # escena 5: vuelve a 60 m²
        for tr, v in ((cx, CENTER[0]), (cy, 880.0), (ppm, CENTER_PPM)):
            tr.to(s("m60") - 0.45, 0.01, v)
        alpha.to(s("m60") - 0.4, 0.3, 1.0, ease_out)
        area.to(s("m60"), 0.75, 60.0, ease_out)
        morph.to(s("m60"), 0.5, 0.0)
        alpha.to(b[5], 0.15, 0.0)
        self.plan = dict(cx=cx, cy=cy, ppm=ppm, area=area, morph=morph, alpha=alpha)

    def plan_state(self, t):
        return {k: v(t) for k, v in self.plan.items()}

    # ---- utilidades de dibujo --------------------------------------------------------
    def render3d(self, fn):
        ss = self.ss
        surf = skia.Surface(int(W * ss), int(H * ss))
        c = surf.getCanvas()
        c.clear(col(GRAPHITE))
        fn(c, ss)
        return surf.makeImageSnapshot().withDefaultMipmaps()

    def blit(self, c, img, scale_from=None, alpha=1.0, blur=(0, 0), dark=0.0, desat=0.0, dx=0.0):
        sf = self.ss if scale_from is None else scale_from
        p = skia.Paint(AntiAlias=True)
        p.setAlphaf(alpha)
        filters = []
        if desat > 0 or dark > 0:
            s_ = 1 - desat
            lum = [0.2126, 0.7152, 0.0722]
            m = []
            for i in range(3):
                row = [(lum[j] * (1 - s_) + (s_ if i == j else 0)) * (1 - dark) for j in range(3)]
                m += row + [0, 0]
            m += [0, 0, 0, 1, 0]
            filters.append(skia.ColorFilters.Matrix(m))
        if filters:
            p.setColorFilter(filters[0])
        if blur[0] > 0 or blur[1] > 0:
            p.setImageFilter(skia.ImageFilters.Blur(blur[0], blur[1], skia.TileMode.kClamp))
        c.save()
        c.translate(dx, 0)
        c.scale(1 / sf, 1 / sf)
        c.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), p)
        c.restore()

    def rgba_image(self, arr):
        return skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kRGBA_8888_ColorType).withDefaultMipmaps()

    def cam_xform(self, c, t, scene_t0, scene_t1):
        """Zoom lento constante + golpes de zoom en cada cifra + temblor."""
        z = 1.0 + 0.045 * prog(t, scene_t0, scene_t1)
        for tp, amp in self.punches:
            z += amp * punch_curve(t - tp)
        dx = dy = 0.0
        for ts, amp, dur in self.shakes:
            if 0 <= t - ts < dur:
                k = (1 - (t - ts) / dur) ** 2
                dx += amp * k * math.sin((t - ts) * 93.0)
                dy += amp * k * math.cos((t - ts) * 71.0 + 1.3)
        c.translate(W / 2 + dx, H * 0.45 + dy)
        c.scale(z, z)
        c.translate(-W / 2, -H * 0.45)

    def scrim(self, c, top=0.55, bottom=0.65):
        """Degradados oscuros arriba y abajo para legibilidad."""
        g = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, 700)],
                                           [col(GRAPHITE, top), col(GRAPHITE, 0)])
        c.drawRect(skia.Rect.MakeWH(W, 700), skia.Paint(Shader=g))
        g = skia.GradientShader.MakeLinear([skia.Point(0, 1080), skia.Point(0, H)],
                                           [col(GRAPHITE, 0), col(GRAPHITE, bottom)])
        c.drawRect(skia.Rect.MakeXYWH(0, 1080, W, H - 1080), skia.Paint(Shader=g))

    def big_figure(self, c, text, x, y, size, color, t, t0, kind="mono", pop=True, alpha=1.0, glow=True):
        if t < t0:
            return
        k = prog(t, t0, t0 + 0.22)
        sc = (1.0 + 0.5 * (1 - back_out(k))) if pop else 1.0
        a = alpha * clamp((t - t0) / 0.06)
        f = font(kind, size)
        c.save()
        c.translate(x, y - size * 0.36)
        c.scale(sc, sc)
        if glow:
            gp = glow_paint(color, 0.45 * a, size * 0.12)
            w = text_width(text, f)
            c.drawString(text, -w / 2, size * 0.36, f, gp)
        draw_text(c, text, 0, size * 0.36, f, color, a, stroke=size * 0.06, stroke_alpha=0.8, shadow=size * 0.08)
        c.restore()

    def tag(self, c, t, t0, title, sub, dot=GREEN, t1=1e9):
        a = prog(t, t0, t0 + 0.25) * (1 - prog(t, t1, t1 + 0.2))
        if a <= 0:
            return
        x = SAFE_LEFT + 8 + (1 - ease_out(prog(t, t0, t0 + 0.3))) * -40
        draw_pin(c, x + 14, 318, 11, dot, a)
        draw_text(c, title, x + 40, 340, font("xb", 58), PAPER, a, align="left", stroke=6, stroke_alpha=0.6, shadow=8)
        draw_text(c, sub, x + 2, 392, font("sb", 32), LIGHT_GREY, a, align="left", stroke=5, stroke_alpha=0.6, shadow=6)

    def source(self, c, text, alpha=1.0):
        if alpha <= 0.01 or not text:
            return
        f = font("mono_m", 27)
        maxw = SAFE_RIGHT - SAFE_LEFT - 30
        words, lines, cur = text.split(), [], ""
        for w in words:
            nxt = (cur + " " + w).strip()
            if text_width(nxt, f) > maxw and cur:
                lines.append(cur)
                cur = w
            else:
                cur = nxt
        lines.append(cur)
        lh = 35
        y_last = 1522
        y0 = y_last - (len(lines) - 1) * lh
        rrect(c, SAFE_LEFT - 14, y0 - 30, maxw + 28, (len(lines) - 1) * lh + 44, 10, GRAPHITE, 0.62 * alpha)
        for i, ln in enumerate(lines):
            draw_text(c, ln, SAFE_LEFT, y0 + i * lh, f, LIGHT_GREY, alpha, align="left")

    def disclaimer(self, c, text, alpha=1.0):
        if alpha > 0:
            draw_text(c, text, SAFE_LEFT, 268, font("mono_m", 22), LIGHT_GREY, 0.85 * alpha, align="left",
                      stroke=4, stroke_alpha=0.5)

    def draw_plan_overlay(self, c, t, label=None, show_label=True):
        st = self.plan_state(t)
        if st["alpha"] <= 0.01 and t < self.tl.s("cero") + 0.6 and t > self.tl.s("cero"):
            self._plan_pop(c, t)
            return
        a = st["alpha"]
        if a <= 0.01:
            return
        if self.tl.s("cero") <= t < self.tl.s("cero") + 0.6:
            self._plan_pop(c, t)
        cx, cy, ppm = st["cx"], st["cy"], st["ppm"]
        sc = math.sqrt(st["area"] / 60.0)
        width = max(2.5, ppm * 0.17)
        sq_side = 3.0
        c.save()
        if self.tl.s("cero") <= t < self.tl.s("cero") + 0.25:
            k = prog(t, self.tl.s("cero"), self.tl.s("cero") + 0.2)
            c.translate(cx, cy)
            c.scale(1 + 0.6 * k, 1 + 0.6 * k)
            c.translate(-cx, -cy)
        # halo oscuro detrás para contraste
        half = max(PLAN_W, PLAN_D) * sc * ppm / 2
        c.drawCircle(cx, cy, half * 1.5 + 30, glow_paint(GRAPHITE, 0.55 * a, half * 0.5 + 20))
        draw_plan(c, lambda x, y: (cx + x * ppm, cy - y * ppm), alpha=a, width=width, scale=sc,
                  morph_sq=st["morph"], sq_side=sq_side)
        if st["morph"] > 0.4:
            draw_bathtub(c, cx, cy + ppm * 0.25, ppm * 1.9, BLUE, a * prog(st["morph"], 0.4, 1.0))
        c.restore()
        if not show_label:
            return
        n = int(round(st["area"]))
        hh = PLAN_D * sc * ppm / 2 if st["morph"] < 0.5 else sq_side * ppm / 2
        if ppm < 25:
            draw_text(c, f"{n} m²", cx, cy + hh + 36, font("mono", 28), PAPER, a, stroke=5, stroke_alpha=0.7)
            draw_text(c, "MADRID", cx, cy - hh - 16, font("mono_sb", 22), (0x9D, 0xB8, 0xFF), a, stroke=4, stroke_alpha=0.7)
        else:
            y = cy + hh + 78
            if label and t >= label[1]:
                la = prog(t, label[1], label[1] + 0.25)
                f = font("mono", 54)
                parts = [("= ", PAPER), (f"{n} m²", (0x8F, 0xB0, 0xFF)), (" en Madrid", PAPER)]
                tw = sum(text_width(p, f) for p, _ in parts)
                x = cx - tw / 2
                for p, colr in parts:
                    draw_text(c, p, x, y, f, colr, a * la, align="left", stroke=8, stroke_alpha=0.85, shadow=10)
                    x += text_width(p, f)
            else:
                draw_text(c, f"{n} m²", cx, y, font("mono", 64), (0x8F, 0xB0, 0xFF), a, stroke=8, stroke_alpha=0.85, shadow=10)

    def _plan_pop(self, c, t):
        t0 = self.tl.s("cero")
        k = prog(t, t0, t0 + 0.55)
        if k <= 0 or k >= 1:
            return
        cx, cy = CORNER
        rs = np.random.RandomState(4)
        for i in range(14):
            ang = rs.uniform(0, 2 * math.pi)
            d = ease_out(k) * rs.uniform(60, 190)
            s_ = 14 * (1 - k)
            x, y = cx + math.cos(ang) * d, cy + math.sin(ang) * d
            c.drawRect(skia.Rect.MakeXYWH(x - s_ / 2, y - s_ / 2, s_, s_), fill_paint(BLUE, 1 - k))
        c.drawCircle(cx, cy, 30 + 150 * ease_out(k), stroke_paint(BLUE, (1 - k) * 0.9, 6 * (1 - k) + 1))

    # ---- fotograma ------------------------------------------------------------------
    def scene_index(self, t):
        for i in range(6):
            if t < self.b[i + 1]:
                return i
        return 5

    def frame(self, t):
        surf = skia.Surface(W, H)
        c = surf.getCanvas()
        c.clear(col(GRAPHITE))
        i = self.scene_index(t)
        hidden, src, disc = getattr(self, f"scene{i + 1}")(c, t)
        # flash en "CERO"
        fa = 0.9 * (1 - prog(t, self.tl.s("cero"), self.tl.s("cero") + 0.28)) if t >= self.tl.s("cero") else 0
        if fa > 0:
            c.drawRect(skia.Rect.MakeWH(W, H), fill_paint(PAPER, fa))
        if disc:
            self.disclaimer(c, disc[0], disc[1])
        if src:
            for text, a in src:
                self.source(c, text, a)
        draw_subs(c, self.pages, t, hidden_keys=hidden, center_y=1300)
        # firma en el último segundo
        ta = prog(t, self.tl.duration - 1.1, self.tl.duration - 0.8)
        if ta > 0:
            draw_text(c, "ALEIX JIMÉNEZ", CX, 1515, font("sb", 32), PAPER, ta, tracking=0.32, stroke=5, stroke_alpha=0.6)
        arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
        d = 0.0
        for th, amp in self.rgb_hits:
            d = max(d, amp * punch_curve(t - th, 0.02, 0.09))
        d = int(round(d))
        if d >= 1:
            arr = arr.copy()
            arr[:, :, 0] = np.roll(arr[:, :, 0], d, axis=1)
            arr[:, :, 2] = np.roll(arr[:, :, 2], -d, axis=1)
        return arr

    def disc3d(self, name):
        if name in self.clip_paths or name in self.stills:
            return ("Imágenes: Google Earth", 1.0)
        return ("Recreación 3D ilustrativa", 1.0)

    # ================================================================================
    # ESCENA 1 · GANCHO: Madrid + planta de 60 m² sobre la calle -> whip a Galicia
    # ================================================================================
    def madrid_bg(self, t, vp=(0, 0, W, H), clip_t0=0.0):
        fr = self.clip_frame("madrid", clip_t0) if "madrid" in self.clip_paths else None
        M = self.model("madrid")
        dolly = -15.0 * (1 - ease_out(prog(t, 0.0, 1.3))) if vp == (0, 0, W, H) else 0.0
        cam = M.camera(t, vp=vp, dolly=dolly)
        if fr is not None:
            return self.rgba_image(fr), 1.0, cam
        return self.render3d(lambda cc, ss: M.render(cc, cam, ss)), self.ss, cam

    def cand_cam_t(self, t):
        return t - self.tw

    def cand_still_params(self, t, zoom=0.0):
        k = ease_out(prog(t, self.tc, self.tc + 0.5))
        z = (1.0 + 0.028 * max(0.0, t - self.tc)) * (1 + 0.55 * zoom) * (1 + 0.9 * (1 - k))
        ang = 2.0 + 0.35 * (t - self.tc) - 6.0 * (1 - k)
        return z, ang

    def cand_bg(self, t, vp=(0, 0, W, H), zoom=0.0, clip_t0=None, anchor_frame=(440.0, 900.0)):
        if "candelago" in self.stills:
            z, ang = self.cand_still_params(t, zoom)
            self._cand_view = (z, ang, anchor_frame, vp)
            return self.still_image("candelago", z, ang, anchor_frame, vp), 1.0, None
        C = self.model("cand")
        ct = self.cand_cam_t(t)
        cam = C.camera(ct, vp=vp, zoom=zoom)
        if "candelago" in self.clip_paths:
            fr = self.clip_frame("candelago", clip_t0 if clip_t0 is not None else 0.0)
            return self.rgba_image(fr), 1.0, cam
        return self.render3d(lambda cc, ss: C.render(cc, cam, ss, ct)), self.ss, cam

    def plan3d_map(self, cam):
        M = self.model("madrid")
        return lambda x, y: cam.p2(x, M.PLAN_Y + y, 0.08)

    def draw_cota(self, c, p0, p1, text, k, a=1.0, offset_px=0.0):
        if k <= 0:
            return
        p0, p1 = np.array(p0), np.array(p1)
        d = p1 - p0
        L = np.linalg.norm(d) + 1e-9
        n = np.array([-d[1], d[0]]) / L
        q1 = p0 + d * ease_out(k)
        pp = stroke_paint(ORANGE, a, 4)
        c.drawLine(*p0, *q1, pp)
        for q in (p0, q1):
            c.drawLine(*(q + n * 14), *(q - n * 14), pp)
            c.drawLine(*(q + n * 9 + d / L * 9), *(q - n * 9 - d / L * 9), stroke_paint(ORANGE, a, 3))
        if k > 0.6:
            mid = (p0 + p1) / 2 + n * offset_px
            f = font("mono", 30)
            tw = text_width(text, f)
            rrect(c, mid[0] - tw / 2 - 10, mid[1] - 22, tw + 20, 42, 8, GRAPHITE, 0.8 * a * prog(k, 0.6, 1))
            draw_text(c, text, mid[0], mid[1] + 10, f, ORANGE, a * prog(k, 0.6, 1))

    def route_point(self, u):
        """Arco Madrid -> Candelago (lon, lat) en el parámetro u."""
        p0 = np.array(MADRID_LONLAT)
        p2 = np.array(CANDELAGO_LONLAT)
        p1 = (p0 + p2) / 2 + np.array([0.9, 1.6])
        return (1 - u) ** 2 * p0 + 2 * (1 - u) * u * p1 + u ** 2 * p2

    def journey_view(self, t):
        """Vuelo de cámara sobre el mapa: sale de Madrid, se aleja y aterriza en Candelago."""
        t0, t1 = self.tw + 0.08, self.tc
        u = ease_io(prog(t, t0, t1))
        head = self.route_point(u)
        lk = math.log(230) * (1 - u) + math.log(2600) * u - 1.15 * math.sin(math.pi * u)
        k = math.exp(lk)
        # remate final acelerado (zoom de transición)
        k *= 1 + 2.5 * ease_in(prog(t, t1 - 0.22, t1))
        return maps.View(head[0], head[1], k, CX, 880), u

    def draw_journey(self, c, t, alpha=1.0):
        A = self.model("atlas")
        v, u = self.journey_view(t)
        maps.map_background(c, W, H)
        for nm in ("Portugal", "France", "Morocco"):
            maps.draw_feature(c, A.countries[nm], v, fill=(0x1B, 0x1D, 0x21), line=GREY, line_alpha=0.3, width=1.3)
        for nm, reg in A.regions.items():
            gal = "Galicia" in nm
            maps.draw_feature(c, reg, v, fill=(0x2A, 0x33, 0x2E) if gal else (0x26, 0x29, 0x2E),
                              line=GREEN if gal else PAPER, line_alpha=0.85 if gal else 0.28, width=2.4 if gal else 1.2)
        # ruta
        us = np.linspace(0, u, 90)
        pts = np.array([v(*self.route_point(x)) for x in us], float)
        if len(pts) > 1:
            c.drawPath(poly_path(pts, close=False), glow_paint(ORANGE, 0.6, 8, 10))
            c.drawPath(poly_path(pts, close=False), stroke_paint(ORANGE, 1.0, 6, dash=[24, 14]))
        mx, my = v(*MADRID_LONLAT)
        draw_pin(c, float(mx), float(my), 15, BLUE, 1.0)
        draw_text(c, "MADRID", float(mx), float(my) - 40, font("xb", 46), (0x8F, 0xB0, 0xFF), 1 - prog(u, 0.25, 0.45),
                  stroke=6, stroke_alpha=0.7)
        gx, gy = v(*CANDELAGO_LONLAT)
        ka = prog(u, 0.55, 0.8)
        if ka > 0:
            draw_pin(c, float(gx), float(gy), 15, GREEN, ka, pulse=(t * 1.6) % 1)
        hx, hy = pts[-1]
        c.drawCircle(float(hx), float(hy), 13, glow_paint(ORANGE, 0.9, 10))
        c.drawCircle(float(hx), float(hy), 9, fill_paint(PAPER))

    def scene1_legacy(self, c, t):
        s = self.tl.s
        tw, tc = self.tw, self.tc
        tw_end = tw + 0.24
        src = []
        # ---------- A · Madrid: acelerón de cámara, planta a escala y 390.000 € ----------
        if t < tw_end:
            img, sf, cam = self.madrid_bg(t)
        if t < tw:
            c.save()
            self.cam_xform(c, t, 0, tw)
            self.blit(c, img, sf)
            self.scrim(c, 0.55, 0.55)
            mp = self.plan3d_map(cam if "madrid" not in self.clip_paths else self.model("madrid").camera(0))
            kc = prog(t, 0.0, 0.22)
            hw, hd = PLAN_W / 2, PLAN_D / 2
            self.draw_cota(c, mp(-hw, -hd - 1.1), mp(hw, -hd - 1.1), "7,5 m", kc, offset_px=34)
            self.draw_cota(c, mp(-hw - 1.1, -hd), mp(-hw - 1.1, hd), "8 m", prog(t, 0.04, 0.3), offset_px=-46)
            draw_plan(c, mp, alpha=1.0, draw=0.6 + 0.4 * prog(t, 0.0, 0.35), width=5.0)
            if t > 0.3:
                ctr = mp(0, 0.4)
                draw_text(c, "60 m²", ctr[0], ctr[1] + 14, font("mono", 46), PAPER, prog(t, 0.3, 0.5), stroke=7, stroke_alpha=0.85)
            draw_text(c, "UN PISO DE 60 m² EN MADRID", CX, 470, font("sb", 40), PAPER, 1.0, stroke=6, stroke_alpha=0.6, shadow=8)
            # el precio está ya en el fotograma 0 (miniatura) y asienta con un pequeño golpe
            k0 = ease_out(prog(t, 0.0, 0.18))
            sc = 1.08 - 0.08 * k0
            c.save()
            c.translate(CX, 600 - 54)
            c.scale(sc, sc)
            f = font("mono", 150)
            pulse = punch_curve(t - s("p390"), 0.04, 0.2)
            c.drawString("390.000 €", -text_width("390.000 €", f) / 2, 54, f, glow_paint(ORANGE, 0.45 + 0.4 * pulse, 18 + 14 * pulse))
            draw_text(c, "390.000 €", 0, 54, f, ORANGE, 1.0, stroke=9, stroke_alpha=0.8, shadow=12)
            c.restore()
            c.restore()
            src = [("Fuente: idealista, precio medio de Madrid (ago. 2026): 6.471 €/m² × 60 m² ≈ 388.000 €", 1.0)]
            return (), src, self.disc3d("madrid")
        # ---------- B · whip pan al mapa ----------
        if t < tw_end:
            k = ease_io(prog(t, tw, tw_end))
            blur = 80 * math.sin(math.pi * k)
            self.blit(c, img, sf, blur=(blur, 0), dx=-W * k)
            surf = skia.Surface(W, H)
            self.draw_journey(surf.getCanvas(), t)
            mimg = surf.makeImageSnapshot()
            self.blit(c, mimg, 1.0, blur=(blur, 0), dx=W * (1 - k))
            M = self.model("madrid")
            mcam = M.camera(tw)
            mp3 = lambda x, y: mcam.p2(x, M.PLAN_Y + y, 0.08)
            mp2 = lambda x, y: (CORNER[0] + x * CORNER_PPM, CORNER[1] - y * CORNER_PPM)
            mpm = lambda x, y: tuple(np.array(mp3(x, y)) * (1 - k) + np.array(mp2(x, y)) * k)
            draw_plan(c, mpm, width=lerp(5.0, 3.0, k))
            return (), [], ("Mapa: IGN (es-atlas) · Natural Earth", 1.0)
        # ---------- C · vuelo Madrid -> Candelago sobre el mapa ----------
        if t < tc:
            c.save()
            self.cam_xform(c, t, tw_end, tc)
            kb = prog(t, tc - 0.22, tc)
            if kb > 0:
                surf = skia.Surface(W, H)
                self.draw_journey(surf.getCanvas(), t)
                self.blit(c, surf.makeImageSnapshot(), 1.0, blur=(14 * kb, 14 * kb))
                c.drawRect(skia.Rect.MakeWH(W, H), fill_paint(PAPER, 0.35 * kb ** 2))
            else:
                self.draw_journey(c, t)
            self.scrim(c, 0.45, 0.5)
            a1 = prog(t, s("menos") - 0.05, s("menos") + 0.15)
            if a1 > 0:
                c.save()
                c.translate(CX, 540)
                sc = 0.9 + 0.1 * back_out(a1)
                c.scale(sc, sc)
                draw_text(c, "POR MENOS DE LA MITAD…", 0, 0, font("xb", 64), PAPER, a1, stroke=8, stroke_alpha=0.75, shadow=12)
                c.restore()
            c.restore()
            self.tag(c, t, tw_end + 0.1, "GALICIA", "Costa da Morte, A Coruña", GREEN)
            self.draw_plan_overlay(c, t)
            return (), [], ("Mapa: IGN (es-atlas) · Natural Earth", 1.0)
        # ---------- D · aterrizaje en Candelago (imagen real) + UN PUEBLO ENTERO ----------
        cimg, csf, ccam = self.cand_bg(t)
        c.save()
        self.cam_xform(c, t, tc, self.b[1] + 4)
        kz = prog(t, tc, tc + 0.3)
        self.blit(c, cimg, csf, blur=(16 * (1 - kz), 16 * (1 - kz)))
        if kz < 1:
            c.drawRect(skia.Rect.MakeWH(W, H), fill_paint(PAPER, 0.35 * (1 - kz) ** 2))
        self.scrim(c, 0.55, 0.55)
        a1 = prog(t, s("menos"), s("menos") + 0.15) * (1 - prog(t, s("pueblo") - 0.12, s("pueblo") + 0.02))
        if a1 > 0:
            draw_text(c, "POR MENOS DE LA MITAD…", CX, 540, font("xb", 64), PAPER, a1, stroke=8, stroke_alpha=0.75, shadow=12)
        if t >= s("pueblo"):
            rrect(c, CX - 420, 460, 840, 340, 60, GRAPHITE, 0.72 * prog(t, s("pueblo"), s("pueblo") + 0.2), blur=40)
            self.big_figure(c, "UN PUEBLO", CX, 610, 128, GREEN, t, s("pueblo"), kind="xb")
            self.big_figure(c, "ENTERO", CX, 745, 128, GREEN, t, s("entero"), kind="xb")
        c.restore()
        self.tag(c, t, tw_end + 0.1, "GALICIA", "Costa da Morte, A Coruña", GREEN)
        self.draw_plan_overlay(c, t)
        return (), [("Fuente: anuncio de Candelago en idealista (prensa, feb. 2026)", prog(t, tc, tc + 0.3))], self.disc3d("candelago")


    # ================================================================================
    # GANCHO con ortofotos reales (PNOA): del espacio a una azotea de Madrid -> vuelo a Galicia
    # ================================================================================
    def hook_cams(self):
        if hasattr(self, "_hook"):
            return self._hook
        s = self.tl.s
        tA = 1.22
        c_space = AE.Cam(MADRID_ROOF[0] + 0.6, MADRID_ROOF[1] - 0.4, 5.7, -32.0)
        c_roof = AE.Cam(MADRID_ROOF[0], MADRID_ROOF[1], 19.6, 0.0)
        dive, _ = AE.van_wijk(c_space, c_roof)
        c_roof2 = AE.Cam(MADRID_ROOF[0], MADRID_ROOF[1], 19.85, 0.0)
        c_cand = AE.Cam(CANDELAGO_LONLAT[0], CANDELAGO_LONLAT[1], 14.6, 18.0)
        fly, _ = AE.van_wijk(c_roof2, c_cand, rho=1.6)
        self._hook = dict(tA=tA, dive=dive, fly=fly, roof=c_roof, roof2=c_roof2, cand=c_cand)
        return self._hook

    def hook_cam(self, t):
        h = self.hook_cams()
        if t < h["tA"]:
            u = prog(t, 0, h["tA"])
            u = 1 - (1 - u) ** 2.6 if u > 0.0 else 0.0        # rampa: rapidísimo y frena al llegar
            return h["dive"](u), u
        if t < self.tw:
            k = prog(t, h["tA"], self.tw)
            c = AE.Cam(MADRID_ROOF[0], MADRID_ROOF[1], lerp(19.6, 19.85, ease_out(k)), 0.0)
            return c, 1.0
        u = ease_io(prog(t, self.tw, self.tc))
        return h["fly"](u), u

    def zoom_blur(self, c, img, amount, center=(W / 2, H * 0.45)):
        """Desenfoque de movimiento radial (zoom) a partir de una imagen."""
        if amount < 0.004:
            c.drawImage(img, 0, 0)
            return
        n = 5
        samp = skia.SamplingOptions(skia.FilterMode.kLinear)
        for i in range(n):
            sc = 1 + amount * i / (n - 1)
            p = skia.Paint()
            p.setAlphaf(1.0 / (i + 1))
            c.save()
            c.translate(center[0], center[1])
            c.scale(sc, sc)
            c.translate(-center[0], -center[1])
            c.drawImage(img, 0, 0, samp, p)
            c.restore()

    def aerial_top(self, cam):
        surf = skia.Surface(W, H)
        self.aer.draw(surf.getCanvas(), cam, vp=(0, -250, W, H))
        return surf.makeImageSnapshot().withDefaultMipmaps()

    def aerial_img(self, cam):
        surf = skia.Surface(W, H)
        self.aer.draw(surf.getCanvas(), cam)
        return surf.makeImageSnapshot()

    def hud(self, c, cam, alpha):
        if alpha <= 0.01:
            return
        f = font("mono_sb", 26)
        txt = f"{dms(cam.lat, 'N', 'S')}  {dms(cam.lon, 'E', 'O')}"
        draw_text(c, txt, SAFE_LEFT, 312, f, PAPER, alpha * 0.9, align="left", stroke=5, stroke_alpha=0.7)
        alt_km = AE.meters_per_px(cam.lat, cam.zoom) * 1920 / 1000
        lab = f"VISTA DE {alt_km:,.1f} KM".replace(",", "X").replace(".", ",").replace("X", ".") if alt_km >= 1 else f"VISTA DE {alt_km * 1000:.0f} M"
        draw_text(c, lab, SAFE_LEFT, 348, font("mono_m", 24), LIGHT_GREY, alpha * 0.85, align="left", stroke=5, stroke_alpha=0.7)

    def roof_plan_map(self, cam):
        mpp = AE.meters_per_px(MADRID_ROOF[1], cam.zoom)
        cx, cy = self.aer.to_screen(cam, (0, 0, W, H), *MADRID_ROOF)
        th = math.radians(cam.rot)

        def f(x, y):
            px, py = x / mpp, -y / mpp
            return (cx + px * math.cos(th) - py * math.sin(th), cy + px * math.sin(th) + py * math.cos(th))
        return f, 1 / mpp

    def scene1(self, c, t):
        if self.aer is None:
            return self.scene1_legacy(c, t)
        s = self.tl.s
        h = self.hook_cams()
        tA, tw, tc = h["tA"], self.tw, self.tc
        disc = (AE.ATTRIBUTION, 1.0)
        # ----------------------- D · aterrizaje en la captura de Candelago -----------------------
        if t >= tc:
            cam_end = h["fly"](1.0)
            k = prog(t, tc, tc + 0.4)
            c.save()
            self.cam_xform(c, t, tc, self.b[1] + 4)
            if k < 1:
                cam_d = AE.Cam(cam_end.lon, cam_end.lat, cam_end.zoom + 1.6 * ease_in(k), cam_end.rot)
                self.zoom_blur(c, self.aerial_img(cam_d), 0.08 * (1 - k))
            cimg, csf, _ = self.cand_bg(t)
            self.blit(c, cimg, csf, alpha=ease_out(k), blur=(10 * (1 - k), 10 * (1 - k)))
            if k < 1:
                c.drawRect(skia.Rect.MakeWH(W, H), fill_paint(PAPER, 0.45 * math.sin(math.pi * k)))
            self.scrim(c, 0.55, 0.55)
            a1 = prog(t, s("menos"), s("menos") + 0.15) * (1 - prog(t, s("pueblo") - 0.12, s("pueblo") + 0.02))
            if a1 > 0:
                draw_text(c, "POR MENOS DE LA MITAD…", CX, 560, font("xb", 66), PAPER, a1, stroke=8, stroke_alpha=0.75, shadow=12)
            if t >= s("pueblo"):
                rrect(c, CX - 430, 460, 860, 350, 60, GRAPHITE, 0.72 * prog(t, s("pueblo"), s("pueblo") + 0.2), blur=40)
                self.big_figure(c, "UN PUEBLO", CX, 615, 132, GREEN, t, s("pueblo"), kind="xb")
                self.big_figure(c, "ENTERO", CX, 752, 132, GREEN, t, s("entero"), kind="xb")
            c.restore()
            self.tag(c, t, tc + 0.15, "GALICIA", "Costa da Morte, A Coruña", GREEN)
            self.draw_plan_overlay(c, t)
            return (), [("Fuente: anuncio de Candelago en idealista (prensa, feb. 2026)", prog(t, tc, tc + 0.3))], \
                (("Imágenes: Google Earth" if k > 0.5 else AE.ATTRIBUTION), 1.0)
        cam, u = self.hook_cam(t)
        img = self.aerial_img(cam)
        # velocidad de zoom -> desenfoque de movimiento
        cam2, _ = self.hook_cam(t + 1 / FPS)
        vz = abs(cam2.zoom - cam.zoom)
        c.save()
        self.cam_xform(c, t, 0, tw if t < tw else tc)
        self.zoom_blur(c, img, min(0.12, vz * 0.09))
        if t < tw:
            # ----------------------- A+B · del espacio a la azotea -----------------------
            kl = prog(t, tA - 0.05, tA + 0.25)
            # foco: oscurece la ciudad alrededor del edificio
            mp, ppm = self.roof_plan_map(cam)
            cx_, cy_ = mp(0, 0)
            if kl > 0:
                g = skia.GradientShader.MakeRadial(skia.Point(cx_, cy_), 520,
                                                   [col(GRAPHITE, 0.0), col(GRAPHITE, 0.0), col(GRAPHITE, 0.55 * kl)], [0.0, 0.25, 1.0])
                c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=g))
            self.scrim(c, 0.5, 0.45)
            if kl > 0:
                hw, hd = PLAN_W / 2, PLAN_D / 2
                ca = 1 - prog(t, tA + 0.45, tA + 0.65)
                self.draw_cota(c, mp(-hw, -hd - 1.6), mp(hw, -hd - 1.6), "7,5 m", prog(t, tA, tA + 0.25), a=ca, offset_px=34)
                self.draw_cota(c, mp(-hw - 1.6, -hd), mp(-hw - 1.6, hd), "8 m", prog(t, tA + 0.05, tA + 0.3), a=ca, offset_px=-46)
                draw_plan(c, mp, alpha=1.0 - 0.6 * prog(t, tA + 0.55, tA + 0.8), draw=prog(t, tA, tA + 0.4), width=4.0)
                # la planta "se levanta" del tejado y crece para leerse (holograma)
                kg = ease_io(prog(t, tA + 0.5, tA + 0.95))
                if kg > 0:
                    big_ppm = 40.0
                    bx, by = cx_, cy_ - 150 * kg
                    ppm_ = lerp(ppm, big_ppm, kg)
                    mpb = lambda x, y: (bx + x * ppm_, by - y * ppm_)
                    # haz de luz entre el tejado y la planta flotante
                    hw_, hd_ = PLAN_W / 2, PLAN_D / 2
                    beam = skia.Path()
                    for (x0_, y0_), (x1_, y1_) in (((-hw_, -hd_), (hw_, -hd_)),):
                        pass
                    a0, a1_, a2, a3 = mp(-hw_, -hd_), mp(hw_, -hd_), mpb(hw_, -hd_), mpb(-hw_, -hd_)
                    beam.moveTo(*a0); beam.lineTo(*a1_); beam.lineTo(*a2); beam.lineTo(*a3); beam.close()
                    c.drawPath(beam, fill_paint(BLUE, 0.18 * kg))
                    c.drawRect(skia.Rect.MakeLTRB(bx - hw_ * ppm_ - 26, by - hd_ * ppm_ - 26, bx + hw_ * ppm_ + 26, by + hd_ * ppm_ + 26),
                               glow_paint(GRAPHITE, 0.55 * kg, 30))
                    draw_plan(c, mpb, alpha=kg, width=lerp(4.0, 7.0, kg))
                    draw_text(c, "60 m²", bx + hw_ * ppm_ + 28, by + 20, font("mono", 58), PAPER, kg, align="left",
                              stroke=8, stroke_alpha=0.85, shadow=10)
            # pin de Madrid durante la caída
            km = 1 - prog(t, tA - 0.35, tA - 0.1)
            if km > 0:
                px_, py_ = self.aer.to_screen(cam, (0, 0, W, H), *MADRID_ROOF)
                draw_pin(c, px_, py_, 14, BLUE, km, pulse=(t * 1.4) % 1)
                draw_text(c, "MADRID", px_, py_ - 34, font("xb", 48), PAPER, km, stroke=7, stroke_alpha=0.8)
            draw_text(c, "UN PISO DE 60 m² EN MADRID", CX, 470, font("sb", 42), PAPER, 1.0, stroke=6, stroke_alpha=0.7, shadow=8)
            k0 = ease_out(prog(t, 0.0, 0.18))
            sc = 1.1 - 0.1 * k0
            c.save()
            c.translate(CX, 546)
            c.scale(sc, sc)
            f = font("mono", 150)
            pulse = punch_curve(t - s("p390"), 0.04, 0.2)
            c.drawString("390.000 €", -text_width("390.000 €", f) / 2, 54, f, glow_paint(ORANGE, 0.45 + 0.4 * pulse, 18 + 14 * pulse))
            draw_text(c, "390.000 €", 0, 54, f, ORANGE, 1.0, stroke=9, stroke_alpha=0.85, shadow=12)
            c.restore()
            c.restore()
            self.hud(c, cam, 1 - prog(t, tA, tA + 0.2))
            return (), [("Fuente: idealista, precio medio de Madrid (ago. 2026): 6.471 €/m² × 60 m² ≈ 388.000 €", 1.0)], disc
        # ----------------------- C · vuelo Madrid -> Galicia -----------------------
        self.scrim(c, 0.45, 0.45)
        # estela de la ruta
        us = np.linspace(0, 1, 60)
        p0 = AE.lonlat_to_world(*MADRID_ROOF)
        p1 = AE.lonlat_to_world(*CANDELAGO_LONLAT)
        pts = []
        for x in us[: max(2, int(60 * u))]:
            w_ = p0 + (p1 - p0) * x
            lon, lat = AE.world_to_lonlat(*w_)
            pts.append(self.aer.to_screen(cam, (0, 0, W, H), lon, lat))
        ka = prog(t, tw + 0.15, tw + 0.35) * (1 - prog(t, tc - 0.3, tc - 0.1))
        if len(pts) > 1 and ka > 0:
            c.drawPath(poly_path(pts, close=False), glow_paint(ORANGE, 0.6 * ka, 8, 10))
            c.drawPath(poly_path(pts, close=False), stroke_paint(ORANGE, ka, 6, dash=[24, 14]))
        mx_, my_ = self.aer.to_screen(cam, (0, 0, W, H), *MADRID_ROOF)
        draw_pin(c, mx_, my_, 14, BLUE, ka)
        gx_, gy_ = self.aer.to_screen(cam, (0, 0, W, H), *CANDELAGO_LONLAT)
        kg = prog(u, 0.55, 0.75) * (1 - prog(t, tc - 0.25, tc - 0.05))
        if kg > 0:
            draw_pin(c, gx_, gy_, 15, GREEN, kg, pulse=(t * 1.6) % 1)
            draw_text(c, "GALICIA", gx_, gy_ - 36, font("xb", 50), PAPER, kg, stroke=7, stroke_alpha=0.8)
        a1 = prog(t, s("menos") - 0.05, s("menos") + 0.15)
        if a1 > 0:
            c.save()
            c.translate(CX, 560)
            sc = 0.9 + 0.1 * back_out(a1)
            c.scale(sc, sc)
            draw_text(c, "POR MENOS DE LA MITAD…", 0, 0, font("xb", 66), PAPER, a1, stroke=8, stroke_alpha=0.75, shadow=12)
            c.restore()
        c.restore()
        # la planta vuela a la esquina al despegar
        kf = prog(t, tw, tw + 0.3)
        if kf < 1:
            cr = h["roof2"]
            rx, ry = self.aer.to_screen(cr, (0, 0, W, H), *MADRID_ROOF)
            mp = lambda x, y: (rx + x * 40.0, ry - 150 - y * 40.0)
            mp2 = lambda x, y: (CORNER[0] + x * CORNER_PPM, CORNER[1] - y * CORNER_PPM)
            e = ease_io(kf)
            draw_plan(c, lambda x, y: tuple(np.array(mp(x, y)) * (1 - e) + np.array(mp2(x, y)) * e), width=lerp(4.5, 3.0, e))
        else:
            self.draw_plan_overlay(c, t)
        self.hud(c, cam, prog(t, tw + 0.1, tw + 0.3) * (1 - prog(t, tc - 0.3, tc - 0.1)))
        return (), [], disc

    # ================================================================================
    # ESCENA 2 · PRIMER IMPACTO: Candelago, 150.000 €, la planta encoge a 23 m²
    # ================================================================================
    def scene2(self, c, t):
        s = self.tl.s
        zoom = 0.35 * ease_io(prog(t, self.b[1], self.b[2]))
        img, sf, cam = self.cand_bg(t, zoom=zoom, clip_t0=self.b[1] - self.tw)
        C = self.model("cand")
        c.save()
        self.cam_xform(c, t, self.b[1], self.b[2])
        self.blit(c, img, sf)
        self.scrim(c, 0.6, 0.6)
        if t >= s("madrid2"):  # oscurece para la planta
            c.drawRect(skia.Rect.MakeWH(W, H), fill_paint(GRAPHITE, 0.35 * prog(t, s("madrid2"), s("madrid2") + 0.4)))
        # cota naranja alrededor de la aldea
        kc = prog(t, s("candelago"), s("candelago") + 0.7)
        if kc > 0:
            if "candelago" in self.stills:
                z_, ang_, af_, vp_ = self._cand_view
                ctr_, rr = self.still("candelago").village_screen(z_, ang_, af_, vp_)
                th_ = math.radians(ang_)
                ring = []
                for a in np.linspace(0, 2 * math.pi, 80):
                    wob = 1 + 0.05 * math.sin(a * 3 + 1)
                    x0, y0 = rr[0] * 1.15 * wob * math.cos(a), rr[1] * 1.15 * wob * math.sin(a)
                    ring.append((ctr_[0] + x0 * math.cos(th_) - y0 * math.sin(th_), ctr_[1] + x0 * math.sin(th_) + y0 * math.cos(th_)))
            elif "candelago" in self.clip_paths:
                ring = [(CX + 300 * math.cos(a), 900 + 200 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 64)]
            else:
                hx = [p for _, p in C.houses]
                ctr = np.mean([[p[0], p[1]] for p in hx], 0)
                ring = []
                for a in np.linspace(0, 2 * math.pi, 72):
                    r = 50 + 6 * math.sin(a * 3)
                    x, y = ctr[0] + r * math.cos(a), ctr[1] + r * 0.9 * math.sin(a)
                    ring.append(cam.p2(x, y, float(C.h(np.array(x), np.array(y))) + 0.5))
            pts = partial_polyline(np.array(ring), ease_io(kc))
            a_ring = 1 - 0.6 * prog(t, s("madrid2"), s("madrid2") + 0.4)
            c.drawPath(poly_path(pts, close=False), glow_paint(ORANGE, 0.5 * a_ring, 6, 8))
            c.drawPath(poly_path(pts, close=False), stroke_paint(ORANGE, a_ring, 5, dash=[22, 12]))
        # vistas al mar
        kv = prog(t, s("vistas"), s("vistas") + 0.25) * (1 - prog(t, s("p150"), s("p150") + 0.25))
        if kv > 0 and ("candelago" in self.stills or "candelago" in self.clip_paths):
            c.save()
            c.translate(CX, 520)
            c.scale(0.85 + 0.15 * back_out(min(1, kv * 1.4)), 0.85 + 0.15 * back_out(min(1, kv * 1.4)))
            pill_label(c, "VISTAS AL MAR", 0, 0, font("xb", 48), GRAPHITE, PAPER, kv, pad_x=34, pad_y=22)
            c.restore()
        elif kv > 0:
            sp = cam.p2(*C.sea_point)
            sp = (clamp(sp[0], 110, 700), clamp(sp[1], 700, 1120))
            draw_pin(c, sp[0], sp[1], 12, PAPER, kv, pulse=(t * 1.5) % 1)
            pill_label(c, "VISTAS AL MAR", sp[0] + 30, sp[1] - 60, font("xb", 40), GRAPHITE, PAPER, kv, align="left")
        # precio
        if t >= s("p150"):
            k = ease_out(prog(t, s("p150"), s("p150") + 0.55))
            val = fmt_es(round(150000 * k / 1000) * 1000)
            y_price = 600
            old_a = prog(t, s("p150") + 0.35, s("p150") + 0.55)
            if old_a > 0:
                f = font("mono_sb", 52)
                txt = "200.000 €"
                tw_ = text_width(txt, f)
                draw_text(c, txt, CX, 468, f, LIGHT_GREY, old_a, stroke=6, stroke_alpha=0.7)
                ks = prog(t, s("p150") + 0.45, s("p150") + 0.65)
                c.drawLine(CX - tw_ / 2 - 8, 452, CX - tw_ / 2 - 8 + (tw_ + 16) * ks, 452, stroke_paint(ORANGE, old_a, 7))
            self.big_figure(c, f"{val} €", CX, y_price, 150, ORANGE, t, s("p150"))
        c.restore()
        self.tag(c, t, s("candelago"), "CANDELAGO", "Ponteceso · A Coruña · Costa da Morte", GREEN)
        self.draw_plan_overlay(c, t, label=("23", s("m23") + 0.65))
        src = [("Fuente: idealista (prensa, feb. 2026). 150.000 € ÷ 6.471 €/m² ≈ 23 m² (cálculo propio)", 1.0)]
        return (), src, self.disc3d("candelago")

    # ================================================================================
    # ESCENA 3 · ESCALADA: PERO ESPERA -> mapa de Galicia, Lugo, 59.000 €, 9 m²
    # ================================================================================
    def galicia_view(self, t):
        return maps.View(-7.95, 42.78, 300, CX + 10, 905)

    def scene3(self, c, t):
        s, e = self.tl.s, self.tl.e
        if t < s("lugo"):
            # imagen congelada de Candelago, oscurecida
            if not hasattr(self, "_freeze"):
                img, sf, _ = self.cand_bg(self.b[2], zoom=0.35, clip_t0=self.b[2] - self.tw)
                self._freeze = (img, sf)
            img, sf = self._freeze
            c.save()
            self.cam_xform(c, t, self.b[2], s("lugo"))
            self.blit(c, img, sf, dark=0.62, desat=0.8, blur=(6, 6))
            self.big_figure(c, "PERO", CX, 700, 200, PAPER, t, s("espera"), kind="xb", glow=False)
            self.big_figure(c, "ESPERA", CX, 900, 200, ORANGE, t, s("espera2"), kind="xb")
            c.restore()
            self.draw_plan_overlay(c, t)
            return ("espera",), [], None
        A = self.model("atlas")
        v = self.galicia_view(t)
        c.save()
        self.cam_xform(c, t, s("lugo"), self.b[3])
        maps.map_background(c, W, H)
        dim = 1 - 0.9 * prog(t, s("loque"), s("loque") + 0.4)
        intro = ease_out(prog(t, s("lugo") - 0.05, s("lugo") + 0.35))
        for name in ("Portugal",):
            maps.draw_feature(c, A.countries[name], v, fill=(0x1C, 0x1F, 0x23), line=GREY, line_alpha=0.35 * intro * dim, width=1.5)
        for nm in ("Asturias", "Castilla y León"):
            maps.draw_feature(c, A.find(A.regions, nm), v, fill=(0x1C, 0x1F, 0x23), line=GREY, line_alpha=0.35 * intro * dim, width=1.5)
        lugo = A.find(A.provinces, "Lugo")
        for nm in ("Coruña", "Lugo", "Ourense", "Pontevedra"):
            f_ = A.find(A.provinces, nm)
            maps.draw_feature(c, f_, v, fill=(0x25, 0x29, 0x2E), fill_alpha=intro, line=PAPER, line_alpha=0.55 * intro * dim, width=2.2)
        kl = prog(t, s("lugo"), s("lugo") + 0.3)
        if kl > 0:
            maps.draw_feature(c, lugo, v, fill=GREEN, fill_alpha=0.55 * kl * dim, line=GREEN, line_alpha=kl * dim, width=4, glow=kl)
        ctr = maps.feature_centroid(lugo)
        px, py = v(ctr[0], ctr[1])
        px, py = float(px), float(py)
        for nm, lab in (("Coruña", "A CORUÑA"), ("Ourense", "OURENSE"), ("Pontevedra", "PONTEVEDRA")):
            cc = maps.feature_centroid(A.find(A.provinces, nm))
            qx, qy = v(cc[0], cc[1])
            draw_text(c, lab, float(qx), float(qy) + 10, font("mono_sb", 26), GREY, 0.8 * intro * dim)
        if kl > 0:
            draw_text(c, "LUGO", px, py - 120, font("mono", 44), PAPER, kl * dim, stroke=6, stroke_alpha=0.7)
            draw_pin(c, px, py + 70, 12, GREEN, kl * dim, pulse=((t - s("lugo")) * 1.2) % 1)
        kh = prog(t, s("dos"), s("dos") + 0.3)
        if kh > 0:
            sc = back_out(kh)
            c.save()
            c.translate(px, py - 10)
            c.scale(sc, sc)
            draw_house_icon(c, -46, 0, 84, fill=(0xA8, 0x9C, 0x8A), alpha=dim)
            draw_house_icon(c, 44, 8, 76, fill=(0x9A, 0x8E, 0x7C), alpha=dim)
            c.restore()
        if t >= s("p59"):
            draw_text(c, "SE VENDIÓ POR", CX, 455, font("xb", 44), PAPER, prog(t, s("p59"), s("p59") + 0.15), stroke=6, stroke_alpha=0.7)
            k = ease_out(prog(t, s("p59"), s("p59") + 0.5))
            self.big_figure(c, f"{fmt_es(round(59000 * k / 1000) * 1000)} €", CX, 600, 150, ORANGE, t, s("p59"))
        c.restore()
        self.draw_plan_overlay(c, t, label=("9", s("nueve") + 0.7))
        src = [("Fuente: Xataka (sept. 2026). 59.000 € ÷ 6.471 €/m² ≈ 9 m² (cálculo propio)", 1.0)]
        return (), src, ("Mapa: IGN (es-atlas) · Natural Earth", 1.0)

    # ================================================================================
    # ESCENA 4 · EFECTO WOW: A Barca, 12 casas, 0 €, la trampa
    # ================================================================================
    def abarca_img(self, t, descend, lit=None):
        if "a_barca" in self.stills:
            z = 1.0 + 0.25 * descend + 0.01 * max(0.0, t - self.tl.s("doce"))
            ang = -14.0 * (1 - descend) + 0.12 * (t - self.b[3])
            return self.still_image("a_barca", z, ang, (540.0, 900.0)), 1.0, None
        Bm = self.model("abarca")
        cam = Bm.camera(t - self.b[3], descend=descend)
        if "a_barca" in self.clip_paths:
            return self.rgba_image(self.clip_frame("a_barca", 0.0)), 1.0, cam
        colors = Bm.colors_with_glow(t, lit) if lit is not None else None
        return self.render3d(lambda cc, ss: Bm.render(cc, cam, ss, t, colors=colors)), self.ss, cam

    def scene4(self, c, t):
        s = self.tl.s
        Bm = self.model("abarca")
        t_doce = s("doce")
        lit = [prog(t, t_doce + i * 0.08, t_doce + i * 0.08 + 0.12) for i in range(12)]
        if t < s("ourense"):
            img, sf, _ = self.abarca_img(t, 0.0)
            c.save()
            self.cam_xform(c, t, self.b[3], s("ourense"))
            self.blit(c, img, sf, dark=0.7, desat=0.4, blur=(10, 10))
            # pregunta gigante palabra a palabra (hace de subtítulo)
            words = [w for w in self.tl.toks if self.tl.s("sabes") <= w["start"] < s("ourense")]
            lines = [words[:4], words[4:]]
            f = font("xb", 104)
            widest = max(sum(text_width(w["text"].upper(), f) for w in ln) + 26 * (len(ln) - 1) for ln in lines)
            if widest > 860:
                f = font("xb", 104 * 860 / widest)
            for li, line in enumerate(lines):
                txts = [w["text"].upper() for w in line]
                tot = sum(text_width(x, f) for x in txts) + 26 * (len(txts) - 1)
                x = CX - tot / 2
                for w, tx in zip(line, txts):
                    if t >= w["start"] - 0.03:
                        k = prog(t, w["start"] - 0.03, w["start"] + 0.12)
                        colr = ORANGE if "INCRE" in tx else PAPER
                        c.save()
                        ww = text_width(tx, f)
                        c.translate(x + ww / 2, 700 + li * 130)
                        sc = 0.7 + 0.3 * back_out(k)
                        c.scale(sc, sc)
                        draw_text(c, tx, 0, 0, f, colr, k, stroke=8, stroke_alpha=0.6, shadow=12)
                        c.restore()
                    x += text_width(tx, f) + 26
            c.restore()
            self.draw_plan_overlay(c, t)
            return ("sabes",), [], None
        descend = 0.85 * ease_io(prog(t, s("ourense") - 0.1, s("doce"))) + 0.15 * prog(t, s("doce"), self.b[4])
        img, sf, cam = self.abarca_img(t, descend, lit)
        crack = t >= s("trampa")
        c.save()
        self.cam_xform(c, t, s("ourense"), self.b[4])
        kh = prog(t, s("ourense") - 0.05, s("ourense") + 0.9)
        haze = (1 - ease_out(kh)) if "a_barca" in self.stills else 0.0
        self.blit(c, img, sf, desat=0.6 * prog(t, s("trampa"), s("trampa") + 0.3), dark=0.35 * prog(t, s("cero"), s("cero") + 0.3),
                  blur=(14 * haze, 14 * haze))
        if haze > 0:
            c.drawRect(skia.Rect.MakeWH(W, H), fill_paint((0xE8, 0xEC, 0xF0), 0.55 * haze))
        self.scrim(c, 0.6, 0.6)
        # casas que se iluminan (sólo en la maqueta 3D: en la imagen real no se marcan casas concretas)
        if "a_barca" not in self.clip_paths and "a_barca" not in self.stills:
            for (o, p), a in zip(Bm.houses, lit):
                if a > 0:
                    x, y = cam.p2(*p)
                    c.drawCircle(x, y, 26 + 10 * a, glow_paint(GREEN, 0.9 * a * (1 - 0.7 * prog(t, s("cero"), s("cero") + 0.3)), 14))
                    if a < 1:
                        c.drawCircle(x, y, 12 + 40 * a, stroke_paint(GREEN, 1 - a, 3))
        # contador de casas
        ka = prog(t, t_doce, t_doce + 0.1) * (1 - prog(t, s("cero") - 0.05, s("cero") + 0.1))
        if ka > 0:
            n = sum(1 for a in lit if a > 0)
            draw_text(c, f"{n} CASAS", CX, 505, font("mono", 64), GREEN, ka, stroke=8, stroke_alpha=0.8, shadow=10)
            for i in range(12):
                x = CX - 11 * 34 + i * 68
                draw_house_icon(c, x, 575, 50, fill=GREEN if lit[i] > 0 else (0x44, 0x48, 0x4E), line=PAPER,
                                alpha=ka * (0.5 + 0.5 * lit[i]), stone=False)
        # 0 €
        if t >= s("cero"):
            k_up = ease_io(prog(t, s("concesion") - 0.1, s("concesion") + 0.35))
            size = lerp(440, 250, k_up)
            y = lerp(840, 610, k_up)
            if not crack:
                self.big_figure(c, "0 €", CX, y, size, ORANGE, t, s("cero"), kind="xb")
            else:
                self._cracked(c, "0 €", CX, y, size, t - s("trampa"))
        if t >= s("concesion"):
            ka = prog(t, s("concesion"), s("concesion") + 0.2)
            sc = back_out(ka)
            c.save()
            c.translate(CX, 765)
            c.scale(sc, sc)
            pill_label(c, "CONCESIÓN DE 50 AÑOS", 0, 0, font("xb", 54), GRAPHITE, PAPER, ka, pad_x=34, pad_y=24)
            c.restore()
        if t >= s("ponerla"):
            kb = prog(t, s("ponerla"), s("ponerla") + 0.2)
            self.big_figure(c, "HASTA 3 M€", CX, 935, 112, ORANGE, t, s("ponerla"))
            draw_text(c, "PARA PONERLA EN MARCHA", CX, 1010, font("xb", 50), PAPER, kb, stroke=6, stroke_alpha=0.7, shadow=8)
            draw_text(c, "(accesos, agua y luz)", CX, 1062, font("sb", 36), LIGHT_GREY, kb, stroke=5, stroke_alpha=0.7)
        c.restore()
        self.tag(c, t, s("ourense"), "A BARCA", "Cortegada · Ourense · junto al Miño", GREEN, t1=s("concesion") - 0.2)
        self.draw_plan_overlay(c, t)
        src = [("Fuentes: Aldeas Abandonadas (anuncio); Ayto. de Cortegada, estimación (prensa, oct. 2026)", 1.0)]
        return (), src, self.disc3d("a_barca")

    def _cracked(self, c, text, x, y, size, dt):
        f = font("xb", size)
        k = ease_out(clamp(dt / 0.25))
        rs = np.random.RandomState(9)
        top, bot = y - size * 0.75, y + size * 0.1
        xs = np.linspace(top, bot, 9)
        crack = [(x + 18 + rs.uniform(-34, 34), yy) for yy in xs]
        crack[0] = (x + 30, top - 30)
        crack[-1] = (x - 10, bot + 30)
        sep = 16 * k
        for side in (-1, 1):
            path = skia.Path()
            far = -2000 if side < 0 else 2000
            path.moveTo(far + x, top - 200)
            for px, py in crack:
                path.lineTo(px, py)
            path.lineTo(far + x, bot + 200)
            path.close()
            c.save()
            c.clipPath(path, skia.ClipOp.kIntersect, True)
            c.translate(side * sep, side * 6 * k)
            c.rotate(side * 2.5 * k, x, y)
            draw_text(c, text, x, y + size * 0.0, f, mix(ORANGE, GREY, 0.35 * k), 1.0, stroke=size * 0.06, stroke_alpha=0.8)
            c.restore()
        c.drawPath(poly_path(crack, close=False), stroke_paint(GRAPHITE, k, 7))

    # ================================================================================
    # ESCENA 5 · CONTRASTE: ≈3.000 pueblos abandonados -> Madrid, 60 m², casi 400.000 €
    # ================================================================================
    def spain_dots(self):
        if hasattr(self, "_dots"):
            return self._dots
        A = self.model("atlas")
        pts = []
        for nm, n in (("Galicia", 150), ("Asturias", 70), ("Castilla y León", 160)):
            f_ = A.find(A.regions, nm)
            pts += [(p, 1) for p in maps.sample_points(f_, n, seed=len(nm), min_dist=0.07)]
        others = [r for k, r in A.regions.items() if not any(x in k for x in ("Galicia", "Asturias", "Castilla y León", "Balears"))]
        rs = np.random.RandomState(5)
        for r in others:
            pts += [(p, 0) for p in maps.sample_points(r, 9, seed=rs.randint(1000), min_dist=0.15)]
        order = rs.permutation(len(pts))
        self._dots = [pts[i] for i in order]
        return self._dots

    def scene5(self, c, t):
        s = self.tl.s
        A = self.model("atlas")
        v0 = maps.View(-3.65, 40.15, 92, CX, 860)
        v1 = maps.View(-3.70, 40.42, 520, CX, 860)
        kz = ease_io(prog(t, s("mientras"), s("madrid3") + 0.15))
        v = maps.View.lerp(v0, v1, kz)
        c.save()
        self.cam_xform(c, t, self.b[4], self.b[5])
        maps.map_background(c, W, H)
        intro = ease_out(prog(t, self.b[4], self.b[4] + 0.4))
        for nm in ("Portugal", "France", "Morocco"):
            maps.draw_feature(c, A.countries[nm], v, fill=(0x1B, 0x1D, 0x21), line=GREY, line_alpha=0.25 * intro, width=1.2)
        for nm, reg in A.regions.items():
            hi = any(x in nm for x in ("Galicia", "Asturias", "Castilla y León"))
            maps.draw_feature(c, reg, v, fill=(0x27, 0x2B, 0x30), fill_alpha=intro, line=GREEN if hi else PAPER,
                              line_alpha=(0.7 if hi else 0.3) * intro * prog(t, s("miles") - 0.2, s("miles")) if hi else 0.3 * intro,
                              width=2.2 if hi else 1.2)
        dots = self.spain_dots()
        dur = 1.0
        da = 1 - 0.75 * kz
        for i, (p, main) in enumerate(dots):
            td = s("miles") + dur * i / len(dots)
            if t < td:
                continue
            k = prog(t, td, td + 0.15)
            x, y = v(p[0], p[1])
            r = (5.0 if main else 4.0) * (0.6 + 0.4 * back_out(k)) * lerp(1, 2.2, kz)
            c.drawCircle(float(x), float(y), r, fill_paint(GREEN if main else (0x6B, 0x86, 0x72), da * k))
        ka = prog(t, s("miles"), s("miles") + 0.25) * (1 - prog(t, s("mientras"), s("mientras") + 0.3))
        if ka > 0:
            self.big_figure(c, "≈ 3.000", CX, 420, 130, GREEN, t, s("miles"), alpha=ka)
            draw_text(c, "PUEBLOS ABANDONADOS", CX, 525, font("xb", 60), PAPER, ka, stroke=7, stroke_alpha=0.7, shadow=10)
            draw_text(c, "la mayoría en Galicia, Asturias y Castilla y León", CX, 1170, font("sb", 34), LIGHT_GREY,
                      ka * prog(t, s("miles") + 0.5, s("miles") + 0.8), stroke=5, stroke_alpha=0.7)
        if self.aer is not None and t >= s("mientras"):
            if not hasattr(self, "_dive5"):
                self._dive5, _ = AE.van_wijk(AE.Cam(-3.70, 40.30, 6.3, 0.0), AE.Cam(MADRID_ROOF[0], MADRID_ROOF[1], 18.9, 0.0))
            u5 = prog(t, s("mientras"), s("madrid3") + 0.4)
            u5 = 1 - (1 - u5) ** 2.4
            cam5 = self._dive5(u5)
            cam5b = self._dive5(min(1.0, 1 - (1 - prog(t + 1 / FPS, s("mientras"), s("madrid3") + 0.4)) ** 2.4))
            cam5.zoom += 0.25 * prog(t, s("madrid3") + 0.4, self.b[5])
            ka5 = prog(t, s("mientras"), s("mientras") + 0.3)
            surf5 = skia.Surface(W, H)
            self.zoom_blur(surf5.getCanvas(), self.aerial_img(cam5), min(0.12, abs(cam5b.zoom - cam5.zoom) * 0.09))
            self.blit(c, surf5.makeImageSnapshot(), 1.0, alpha=ka5)
            g = skia.GradientShader.MakeRadial(skia.Point(CX, 880), 700, [col(GRAPHITE, 0.15), col(GRAPHITE, 0.6)])
            c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=g, Alphaf=ka5))
            self.scrim(c, 0.5 * ka5, 0.5 * ka5)
        km = prog(t, s("madrid3") - 0.15, s("madrid3") + 0.15)
        if km > 0 and self.aer is None:
            mx, my = v(-3.7038, 40.4168)
            draw_pin(c, float(mx), float(my), 16, BLUE, km, pulse=((t - s("madrid3")) * 1.3) % 1)
            draw_text(c, "MADRID", float(mx), float(my) - 210 - 40 * (1 - km), font("xb", 64), (0x8F, 0xB0, 0xFF),
                      km * (1 - prog(t, s("m60") - 0.5, s("m60") - 0.2)), stroke=7, stroke_alpha=0.7)
        if t >= s("p400"):
            draw_text(c, "CASI", CX, 395, font("xb", 56), PAPER, prog(t, s("casi"), s("casi") + 0.15), stroke=6, stroke_alpha=0.7)
            k = ease_out(prog(t, s("p400"), s("p400") + 0.5))
            self.big_figure(c, f"{fmt_es(round(400000 * k / 1000) * 1000)} €", CX, 525, 150, ORANGE, t, s("p400"))
        elif t >= s("casi"):
            draw_text(c, "CASI", CX, 395, font("xb", 56), PAPER, prog(t, s("casi"), s("casi") + 0.15), stroke=6, stroke_alpha=0.7)
        c.restore()
        self.draw_plan_overlay(c, t)
        if t < s("mientras") + 0.2:
            src = [("Fuente: Xataka (sept. 2026). Puntos ilustrativos, no uno por pueblo", 1 - prog(t, s("mientras"), s("mientras") + 0.2))]
        else:
            src = [("Fuente: idealista, precio medio de Madrid (ago. 2026): 6.471 €/m² × 60 m² ≈ 388.000 €", prog(t, s("mientras"), s("mientras") + 0.25))]
        disc5 = (AE.ATTRIBUTION, 1.0) if (self.aer is not None and t >= s("mientras") + 0.2) else ("Mapa: IGN (es-atlas) · Natural Earth", 1.0)
        return (), src, disc5

    # ================================================================================
    # ESCENA 6 · CTA: pantalla partida + encuesta
    # ================================================================================
    def scene6(self, c, t):
        s = self.tl.s
        t0 = self.b[5]
        half = H // 2
        kin = ease_out(prog(t, t0, t0 + 0.35))
        hi_top = prog(t, s("piso"), s("piso") + 0.2) * (1 - prog(t, s("o"), s("o") + 0.2))
        hi_bot = prog(t, s("o"), s("o") + 0.2) * (1 - prog(t, s("leo"), s("leo") + 0.25))
        # arriba: Madrid con la planta de 60 m²
        M = self.model("madrid")
        mcam = M.camera(t - t0, vp=(0, -420, W, H))
        real_top = self.aer is not None
        if real_top:
            camt = AE.Cam(MADRID_ROOF[0], MADRID_ROOF[1], 18.7 + 0.04 * (t - t0), -6.0 + 0.6 * (t - t0))
            mimg, msf = self.aerial_top(camt), 1.0
        elif "madrid" in self.clip_paths:
            mimg, msf = self.rgba_image(self.clip_frame("madrid", 0.0)), 1.0
        else:
            mimg, msf = self.render3d(lambda cc, ss: M.render(cc, mcam, ss)), self.ss
        C = self.model("cand")
        ccam = C.camera(t - self.tw, vp=(0, 260, W, H), zoom=0.05)
        if "candelago" in self.stills:
            cimg, csf = self.still_image("candelago", 1.05 + 0.02 * (t - t0), 4.0 + 0.4 * (t - t0), (440.0, 1430.0), (0, half, W, half)), 1.0
        elif "candelago" in self.clip_paths:
            cimg, csf = self.rgba_image(self.clip_frame("candelago", 4.0)), 1.0
        else:
            cimg, csf = self.render3d(lambda cc, ss: C.render(cc, ccam, ss, t - self.tw)), self.ss
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(0, 0, W, half))
        c.translate(0, -half * (1 - kin))
        self.blit(c, mimg, msf, dark=0.35 * hi_bot)
        if real_top:
            mp = lambda x, y: (CX + x * 30, 650 - y * 30)
            c.drawCircle(CX, 650, 230, glow_paint(GRAPHITE, 0.5, 60))
        else:
            mp = (lambda x, y: mcam.p2(x, M.PLAN_Y + y, 0.08)) if "madrid" not in self.clip_paths else \
                (lambda x, y: (CX + x * 40, 640 - y * 40))
        draw_plan(c, mp, width=5)
        self.scrim(c, 0.6, 0.0)
        rrect(c, CX - 250, 262, 500, 172, 26, GRAPHITE, 0.6)
        draw_text(c, "UN PISO", CX, 345, font("xb", 92), PAPER, 1, stroke=8, stroke_alpha=0.7, shadow=12)
        draw_text(c, "60 m² · 390.000 €", CX, 410, font("mono", 46), ORANGE, 1, stroke=6, stroke_alpha=0.8)
        c.restore()
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(0, half, W, half))
        c.translate(0, half * (1 - kin))
        self.blit(c, cimg, csf, dark=0.35 * hi_top)
        g = skia.GradientShader.MakeLinear([skia.Point(0, half), skia.Point(0, half + 380)], [col(GRAPHITE, 0.7), col(GRAPHITE, 0)])
        c.drawRect(skia.Rect.MakeXYWH(0, half, W, 380), skia.Paint(Shader=g))
        g = skia.GradientShader.MakeLinear([skia.Point(0, 1150), skia.Point(0, H)], [col(GRAPHITE, 0), col(GRAPHITE, 0.75)])
        c.drawRect(skia.Rect.MakeXYWH(0, 1150, W, H - 1150), skia.Paint(Shader=g))
        rrect(c, CX - 330, 1040, 660, 158, 26, GRAPHITE, 0.72)
        draw_text(c, "UN PUEBLO ENTERO", CX, 1110, font("xb", 74), GREEN, 1, stroke=8, stroke_alpha=0.7, shadow=12)
        draw_text(c, "150.000 €", CX, 1172, font("mono", 46), ORANGE, 1, stroke=6, stroke_alpha=0.8)
        c.restore()
        c.drawRect(skia.Rect.MakeXYWH(0, half - 3, W, 6), fill_paint(PAPER, kin))
        # botones de encuesta
        kb = prog(t, t0 + 0.2, t0 + 0.45)
        for i, (lab, colr, hl) in enumerate((("MADRID", BLUE, hi_top), ("PUEBLO", GREEN, hi_bot))):
            bx = CX - 222 if i == 0 else CX + 222
            sc = back_out(kb) * (1 + 0.08 * hl)
            if t >= s("leo"):
                ph = (t - s("leo")) * 2.2 + i * 0.5
                sc *= 1 + 0.05 * max(0, math.sin(ph * math.pi * 2))
            c.save()
            c.translate(bx, half)
            c.scale(sc, sc)
            rrect(c, -205, -68, 410, 136, 68, GRAPHITE, 0.6 * kb, blur=18)
            rrect(c, -200, -64, 400, 128, 64, colr, kb, stroke=4, stroke_color=PAPER)
            draw_text(c, lab, 0, 22, font("xb", 64), PAPER, kb)
            c.restore()
            if t >= s("leo"):
                rp = ((t - s("leo")) * 1.1 + i * 0.5) % 1
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(bx - 200 - 40 * rp, half - 64 - 40 * rp, 400 + 80 * rp, 128 + 80 * rp),
                                                  64 + 40 * rp, 64 + 40 * rp), stroke_paint(colr, (1 - rp) * 0.8, 4))
        kq = prog(t, t0 + 0.1, t0 + 0.35)
        pill_label(c, "¿QUÉ ELIGES?", CX, half - 130, font("xb", 46), GRAPHITE, PAPER, kq)
        fa = 1 - prog(t, self.tl.duration - 1.3, self.tl.duration - 1.0)
        src = [("Fuentes: idealista (ago. 2026); anuncio de Candelago en idealista (feb. 2026)", fa)]
        return (), src, ((("PNOA © IGN · Imágenes: Google Earth" if self.aer is not None else "Recreación 3D · Imágenes: Google Earth") if self.stills else "Recreación 3D ilustrativa"), 1.0)

    # ================================================================================
    # PORTADA (1080x1920): MADRID arriba, PUEBLO abajo, ¿QUÉ ELIGES? en el centro
    # ================================================================================
    def cover(self):
        surf = skia.Surface(W, H)
        c = surf.getCanvas()
        half = H // 2
        M = self.model("madrid")
        mcam = M.camera(1.0, vp=(0, -260, W, H))
        real_top = self.aer is not None
        if real_top:
            mimg, msf = self.aerial_top(AE.Cam(MADRID_ROOF[0], MADRID_ROOF[1], 18.6, -6.0)), 1.0
        elif "madrid" in self.clip_paths:
            mimg, msf = self.rgba_image(self.clip_frame("madrid", 1.0)), 1.0
        else:
            mimg, msf = self.render3d(lambda cc, ss: M.render(cc, mcam, ss)), self.ss
        C = self.model("cand")
        ccam = C.camera(3.0, vp=(0, 380, W, H), zoom=0.15)
        if "candelago" in self.stills:
            cimg, csf = self.still_image("candelago", 1.08, 3.0, (440.0, 1300.0), (0, half, W, half)), 1.0
        elif "candelago" in self.clip_paths:
            cimg, csf = self.rgba_image(self.clip_frame("candelago", 3.0)), 1.0
        else:
            cimg, csf = self.render3d(lambda cc, ss: C.render(cc, ccam, ss, 3.0)), self.ss
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(0, 0, W, half))
        self.blit(c, mimg, msf)
        if real_top:
            mp = lambda x, y: (CX + x * 30, 735 - y * 30)
            c.drawCircle(CX, 735, 200, glow_paint(GRAPHITE, 0.55, 60))
        else:
            mp = (lambda x, y: mcam.p2(x, M.PLAN_Y + y, 0.08)) if "madrid" not in self.clip_paths else \
                (lambda x, y: (CX + x * 40, 700 - y * 40))
        draw_plan(c, mp, width=6)
        g = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, 640)], [col(GRAPHITE, 0.85), col(GRAPHITE, 0)])
        c.drawRect(skia.Rect.MakeWH(W, 640), skia.Paint(Shader=g))
        draw_text(c, "MADRID · 60 m²", CX, 405, font("xb", 100), PAPER, 1, stroke=8, stroke_alpha=0.7, shadow=14)
        draw_text(c, "390.000 €", CX, 545, font("mono", 136), ORANGE, 1, stroke=9, stroke_alpha=0.8, shadow=14)
        c.restore()
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(0, half, W, half))
        self.blit(c, cimg, csf)
        g = skia.GradientShader.MakeLinear([skia.Point(0, half + 150), skia.Point(0, H - 300)], [col(GRAPHITE, 0), col(GRAPHITE, 0.85)])
        c.drawRect(skia.Rect.MakeXYWH(0, half + 150, W, H - half - 150), skia.Paint(Shader=g))
        draw_text(c, "UN PUEBLO ENTERO", CX, 1385, font("xb", 84), GREEN, 1, stroke=8, stroke_alpha=0.8, shadow=14)
        draw_text(c, "150.000 €", CX, 1520, font("mono", 136), ORANGE, 1, stroke=9, stroke_alpha=0.8, shadow=14)
        c.restore()
        c.drawRect(skia.Rect.MakeXYWH(0, half - 4, W, 8), fill_paint(PAPER))
        f = font("xb", 96)
        tw = text_width("¿QUÉ ELIGES?", f)
        rrect(c, CX - tw / 2 - 50, half - 92, tw + 100, 184, 92, GRAPHITE, 0.7, blur=24)
        rrect(c, CX - tw / 2 - 44, half - 84, tw + 88, 168, 84, ORANGE)
        draw_text(c, "¿QUÉ ELIGES?", CX, half + 35, f, PAPER)
        draw_text(c, ("PNOA © IGN · Imágenes: Google Earth" if self.aer is not None else "Recreación 3D · Imágenes: Google Earth") if self.stills else "Recreación 3D ilustrativa", SAFE_LEFT, 268,
                  font("mono_m", 22), LIGHT_GREY, 0.85, align="left")
        return surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
