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
        self._models = {}
        self._readers = {}
        self._build_tracks()
        self.punches = [(0.0, 0.07), (s("p390"), 0.05), (s("p150"), 0.06), (s("m23"), 0.05), (s("espera"), 0.05),
                        (s("p59"), 0.06), (s("nueve"), 0.05), (s("cero"), 0.15), (s("trampa"), 0.04),
                        (s("miles"), 0.04), (s("m60"), 0.05), (s("p400"), 0.07)]
        self.shakes = [(s("cero"), 22.0, 0.55), (s("espera"), 7.0, 0.3), (s("trampa"), 10.0, 0.35)]

    # ---- recursos perezosos ---------------------------------------------------------
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
            draw_text(c, text, SAFE_RIGHT, 278, font("mono_m", 22), LIGHT_GREY, 0.85 * alpha, align="right",
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
        return surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)

    def disc3d(self, name):
        return ("Imágenes: Google Earth", 1.0) if name in self.clip_paths else ("Recreación 3D ilustrativa", 1.0)

    # ================================================================================
    # ESCENA 1 · GANCHO: Madrid + planta de 60 m² sobre la calle -> whip a Galicia
    # ================================================================================
    def madrid_bg(self, t, vp=(0, 0, W, H), clip_t0=0.0):
        fr = self.clip_frame("madrid", clip_t0) if "madrid" in self.clip_paths else None
        M = self.model("madrid")
        cam = M.camera(t, vp=vp)
        if fr is not None:
            return self.rgba_image(fr), 1.0, cam
        return self.render3d(lambda cc, ss: M.render(cc, cam, ss)), self.ss, cam

    def cand_cam_t(self, t):
        return t - self.tw

    def cand_bg(self, t, vp=(0, 0, W, H), zoom=0.0, clip_t0=None):
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

    def scene1(self, c, t):
        s = self.tl.s
        tw, twe = self.tw, self.tw_end
        disc = None
        src = []
        if t < tw + 0.17:
            img, sf, cam = self.madrid_bg(t)
        if t < tw:
            c.save()
            self.cam_xform(c, t, 0, self.b[1])
            self.blit(c, img, sf)
            self.scrim(c, 0.5, 0.55)
            mp = self.plan3d_map(cam if "madrid" not in self.clip_paths else self.model("madrid").camera(0))
            # cota naranja (fotograma 0) y planta azul a escala real
            kc = prog(t, 0.0, 0.22)
            hw, hd = PLAN_W / 2, PLAN_D / 2
            self.draw_cota(c, mp(-hw, -hd - 1.1), mp(hw, -hd - 1.1), "7,5 m", kc, offset_px=34)
            self.draw_cota(c, mp(-hw - 1.1, -hd), mp(-hw - 1.1, hd), "8 m", prog(t, 0.04, 0.3), offset_px=-46)
            draw_plan(c, mp, alpha=1.0, draw=prog(t, 0.0, 0.5), width=5.0)
            if t > 0.35:
                ctr = mp(0, 0.4)
                draw_text(c, "60 m²", ctr[0], ctr[1] + 14, font("mono", 46), PAPER, prog(t, 0.35, 0.55), stroke=7, stroke_alpha=0.85)
            # etiqueta 390.000 €
            draw_text(c, "UN PISO DE 60 m² EN MADRID", CX, 470, font("sb", 40), PAPER, prog(t, 0.0, 0.12),
                      stroke=6, stroke_alpha=0.6, shadow=8)
            self.big_figure(c, "390.000 €", CX, 600, 150, ORANGE, t, 0.0)
            c.restore()
            disc = self.disc3d("madrid")
            src = [("Fuente: idealista, precio medio de Madrid (ago. 2026): 6.471 €/m² × 60 m² ≈ 388.000 €", 1.0)]
            return (), src, disc
        # ---- whip pan a Galicia ----
        cimg, csf, ccam = self.cand_bg(t)
        if t < twe:
            k = ease_io(prog(t, tw, twe))
            blur = 70 * math.sin(math.pi * k)
            if t < tw + 0.17:
                self.blit(c, img, sf, blur=(blur, 0), dx=-W * k)
            self.blit(c, cimg, csf, blur=(blur, 0), dx=W * (1 - k))
            # la planta vuela a la esquina
            M = self.model("madrid")
            mcam = M.camera(tw)
            mp3 = lambda x, y: mcam.p2(x, M.PLAN_Y + y, 0.08)
            mp2 = lambda x, y: (CORNER[0] + x * CORNER_PPM, CORNER[1] - y * CORNER_PPM)
            mpm = lambda x, y: tuple(np.array(mp3(x, y)) * (1 - k) + np.array(mp2(x, y)) * k)
            draw_plan(c, mpm, width=lerp(5.0, 3.0, k))
            disc = self.disc3d("candelago")
            return (), [], disc
        c.save()
        self.cam_xform(c, t, twe, self.b[1] + 6)
        self.blit(c, cimg, csf)
        self.scrim(c, 0.55, 0.55)
        a1 = prog(t, s("menos"), s("menos") + 0.2)
        if a1 > 0:
            a1 *= 1 - prog(t, s("pueblo") - 0.1, s("pueblo") + 0.1)
            draw_text(c, "POR MENOS DE LA MITAD…", CX, 560, font("xb", 60), PAPER, a1, stroke=7, stroke_alpha=0.7, shadow=10)
        if t >= s("pueblo"):
            rrect(c, CX - 420, 460, 840, 340, 60, GRAPHITE, 0.72 * prog(t, s("pueblo"), s("pueblo") + 0.2), blur=40)
            self.big_figure(c, "UN PUEBLO", CX, 610, 124, GREEN, t, s("pueblo"), kind="xb")
            self.big_figure(c, "ENTERO", CX, 740, 124, GREEN, t, s("pueblo") + 0.1, kind="xb")
        c.restore()
        self.tag(c, t, twe, "GALICIA", "Costa da Morte, A Coruña", GREEN)
        self.draw_plan_overlay(c, t)
        return (), [("Fuente: anuncio de Candelago en idealista (prensa, feb. 2026)", prog(t, twe, twe + 0.3))], self.disc3d("candelago")

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
            if "candelago" in self.clip_paths:
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
        if kv > 0:
            sp = (260, 1010) if "candelago" in self.clip_paths else cam.p2(*C.sea_point)
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
        self.blit(c, img, sf, desat=0.6 * prog(t, s("trampa"), s("trampa") + 0.3), dark=0.35 * prog(t, s("cero"), s("cero") + 0.3))
        self.scrim(c, 0.6, 0.6)
        # casas que se iluminan
        if "a_barca" not in self.clip_paths:
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
        km = prog(t, s("madrid3") - 0.15, s("madrid3") + 0.15)
        if km > 0:
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
        return (), src, ("Mapa: IGN (es-atlas) · Natural Earth", 1.0)

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
        if "madrid" in self.clip_paths:
            mimg, msf = self.rgba_image(self.clip_frame("madrid", 0.0)), 1.0
        else:
            mimg, msf = self.render3d(lambda cc, ss: M.render(cc, mcam, ss)), self.ss
        C = self.model("cand")
        ccam = C.camera(t - self.tw, vp=(0, 260, W, H), zoom=0.05)
        if "candelago" in self.clip_paths:
            cimg, csf = self.rgba_image(self.clip_frame("candelago", 4.0)), 1.0
        else:
            cimg, csf = self.render3d(lambda cc, ss: C.render(cc, ccam, ss, t - self.tw)), self.ss
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(0, 0, W, half))
        c.translate(0, -half * (1 - kin))
        self.blit(c, mimg, msf, dark=0.35 * hi_bot)
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
        return (), src, None

    # ================================================================================
    # PORTADA (1080x1920): MADRID arriba, PUEBLO abajo, ¿QUÉ ELIGES? en el centro
    # ================================================================================
    def cover(self):
        surf = skia.Surface(W, H)
        c = surf.getCanvas()
        half = H // 2
        M = self.model("madrid")
        mcam = M.camera(1.0, vp=(0, -260, W, H))
        if "madrid" in self.clip_paths:
            mimg, msf = self.rgba_image(self.clip_frame("madrid", 1.0)), 1.0
        else:
            mimg, msf = self.render3d(lambda cc, ss: M.render(cc, mcam, ss)), self.ss
        C = self.model("cand")
        ccam = C.camera(3.0, vp=(0, 380, W, H), zoom=0.15)
        if "candelago" in self.clip_paths:
            cimg, csf = self.rgba_image(self.clip_frame("candelago", 3.0)), 1.0
        else:
            cimg, csf = self.render3d(lambda cc, ss: C.render(cc, ccam, ss, 3.0)), self.ss
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(0, 0, W, half))
        self.blit(c, mimg, msf)
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
        draw_text(c, "Recreación 3D ilustrativa" if not self.clip_paths else "Imágenes: Google Earth", SAFE_RIGHT, 278,
                  font("mono_m", 22), LIGHT_GREY, 0.85, align="right")
        return surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
