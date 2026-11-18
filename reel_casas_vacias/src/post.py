"""Posprocesado de LA MAQUETA.

EXR (720x1280, lineal + profundidad) -> tilt-shift por profundidad + banda de
pantalla -> bloom -> tono/gradación -> reescalado 1080x1920 -> aberración
cromática -> viñeta -> grano -> polvo (plano F) -> subtítulos, fuente y CTA.

uso: python post.py [--shots A_hook,...] [--q final] [--frames 1,50,...] [--dim 0.6] [--out DIR]
"""
import os, sys, json, math, argparse, glob, random
import numpy as np
import cv2
import OpenEXR
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONTS = os.path.join(ROOT, 'fonts')
TM = json.load(open(os.path.join(ROOT, 'output', 'timings.json')))
OW, OH = 1080, 1920
FPS = 30
CREAM = (244, 241, 234)
RED = (215, 38, 46)
SRC_TXT = 'INE, Censo 2021 · Banco de España, Informe Anual 2025'


def read_exr(fn):
    f = OpenEXR.File(fn)
    d = {}
    for p in f.parts:
        for k, v in p.channels.items():
            d[k] = v.pixels
    rgb = d['ViewLayer.Combined'][..., :3].astype(np.float32)
    z = d['ViewLayer.Depth.Z'].astype(np.float32)
    ik = [k for k in d if 'IndexOB' in k or 'Object Index' in k]
    idx = d[ik[0]].astype(np.float32) if ik else np.zeros_like(z)
    if idx.ndim == 3:
        idx = idx[..., 0]
    return rgb, z, idx

# ------------------------------------------------------------------ óptica

def tilt_shift(rgb, z, focus_d, fy, strength, rmax, keep=None):
    """Desenfoque variable: círculo de confusión por profundidad + banda de pantalla."""
    h, w = z.shape
    zz = np.minimum(z, focus_d * 40)
    coc = np.abs(zz - focus_d) / np.maximum(zz, 1e-3)          # |z - zf| / z
    r_depth = np.clip((coc - 0.10) * 1.9, 0, 1)
    ys = (np.arange(h) / h)[:, None]
    band = np.clip((np.abs(ys - fy) - 0.20) / 0.30, 0, 1)
    band = band * band * (3 - 2 * band)
    r = np.maximum(r_depth, band * 0.7) * strength
    r = cv2.GaussianBlur(r.astype(np.float32), (0, 0), 3)
    if keep is not None:
        r = r * (1 - keep)
    radii = [0, 1.2, 2.6, 4.5, 7.5, 11.0, 16.0]
    rr = np.clip(r, 0, 1) * rmax
    levels = []
    for k, rad in enumerate(radii):
        if rad == 0:
            levels.append(rgb)
        else:
            # desenfoque de disco (bokeh) aproximado: caja + gauss
            k_ = int(rad * 2) | 1
            b = cv2.blur(rgb, (k_, k_))
            b = cv2.GaussianBlur(b, (0, 0), rad * 0.45)
            levels.append(b)
    out = np.zeros_like(rgb)
    idx = np.interp(rr, radii, np.arange(len(radii)))
    i0 = np.floor(idx).astype(int)
    i1 = np.minimum(i0 + 1, len(radii) - 1)
    f = (idx - i0)[..., None]
    for k in range(len(radii)):
        m0 = (i0 == k)[..., None]
        m1 = (i1 == k)[..., None]
        out += levels[k] * (m0 * (1 - f) + m1 * f)
    return out


def bloom(rgb, thr=1.1, amt=0.10):
    hi = np.maximum(rgb - thr, 0)
    b = cv2.GaussianBlur(hi, (0, 0), 6) * 0.6 + cv2.GaussianBlur(hi, (0, 0), 22) * 0.4
    return rgb + b * amt * 4


def tonemap(x, exposure=1.0):
    x = x * exposure
    # curva fílmica suave (ACES aprox.) con desaturación leve en altas luces
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    y = np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)
    lum = (y * np.array([0.2126, 0.7152, 0.0722])).sum(-1, keepdims=True)
    y = lum + (y - lum) * 0.92
    return np.clip(y, 0, 1)


def grade(y):
    # cálido suave en medios, negros profundos (#070707), crema en altas
    y = np.power(y, 1 / 2.2)
    lift = 7 / 255
    y = lift + y * (1 - lift)
    warm = np.array([1.02, 1.0, 0.965])
    y = y * warm
    # contraste en S
    y = y + 0.06 * np.sin((y - 0.5) * math.pi) * 0.5
    return np.clip(y, 0, 1)


def chroma_ab(img, amt=1.6):
    h, w = img.shape[:2]
    out = img.copy()
    for ch, s in ((0, 1 + amt / w), (2, 1 - amt / w)):
        M = np.float32([[s, 0, (1 - s) * w / 2], [0, s, (1 - s) * h / 2]])
        out[..., ch] = cv2.warpAffine(img[..., ch], M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return out


_VIG = None


def vignette(img, amt=0.38):
    global _VIG
    h, w = img.shape[:2]
    if _VIG is None:
        y, x = np.mgrid[0:h, 0:w]
        r = np.sqrt(((x - w / 2) / (w * 0.62)) ** 2 + ((y - h / 2) / (h * 0.62)) ** 2)
        _VIG = (1 - amt * np.clip(r, 0, 1.4) ** 2.2)[..., None].astype(np.float32)
    return img * _VIG


def grain(img, frame, amt=0.013):
    rng = np.random.default_rng(frame * 7919 + 13)
    h, w = img.shape[:2]
    n = rng.standard_normal((h // 2, w // 2)).astype(np.float32)
    n = cv2.resize(n, (w, h), interpolation=cv2.INTER_LINEAR)
    n = cv2.GaussianBlur(n, (0, 0), 0.6)
    lum = img.mean(-1, keepdims=True)
    k = amt * (0.6 + 0.8 * (1 - lum) * lum * 4) / 1.0
    return np.clip(img + n[..., None] * k, 0, 1)


def dust(img, t, frame):
    """Motas de polvo flotando en la luz (plano de los pueblos)."""
    h, w = img.shape[:2]
    rng = random.Random(42)
    over = np.zeros((h, w), np.float32)
    for i in range(70):
        x0 = rng.uniform(0, w); y0 = rng.uniform(h * 0.05, h * 0.75)
        vx = rng.uniform(-14, 8); vy = rng.uniform(-6, 10)
        size = rng.choice([1.2, 1.5, 2, 3, 5, 9])
        x = (x0 + vx * t + 18 * math.sin(t * 0.7 + i)) % w
        y = (y0 + vy * t + 10 * math.sin(t * 0.9 + i * 1.7)) % h
        a = 0.35 + 0.35 * math.sin(t * 2.1 + i)
        cv2.circle(over, (int(x), int(y)), int(max(1, size)), a * (0.6 if size > 4 else 1.0), -1, cv2.LINE_AA)
    over = cv2.GaussianBlur(over, (0, 0), 1.6)
    # más visibles en la zona iluminada (izquierda/arriba)
    ys = np.linspace(1, 0.5, h)[:, None]
    over = over * ys * 0.28
    return np.clip(img + over[..., None] * np.array([1.0, 0.95, 0.85]), 0, 1)

# ------------------------------------------------------------------ texto


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


F_SUB = None


def chunks():
    """Agrupa las palabras en bloques de subtítulo (≤ 2 líneas cortas)."""
    out = []
    words = TM['words']
    cur = []
    for i, w in enumerate(words):
        cur.append(w)
        txt = ' '.join(x['w'] for x in cur)
        end_sent = i + 1 == len(words) or words[i + 1]['sent'] != w['sent']
        brk = w['w'].endswith((',', ':', '…', '.', '?'))
        if end_sent or len(txt) >= 17 or (brk and len(cur) >= 2):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


CHUNKS = None


def draw_subs(im, t):
    """Subtítulos palabra a palabra, palabra activa en rojo, con sombra suave."""
    global CHUNKS, F_SUB
    if CHUNKS is None:
        CHUNKS = chunks()
        F_SUB = font('InterDisplay-SemiBold.ttf', 76)
    active = None
    for k, ch in enumerate(CHUNKS):
        s = ch[0]['s'] - 0.05
        nxt = CHUNKS[k + 1][0]['s'] - 0.05 if k + 1 < len(CHUNKS) else 1e9
        e = min(ch[-1]['e'] + 0.6, nxt)
        if s <= t < e:
            active = ch
    if not active:
        return im
    words = [w for w in active if w['s'] - 0.05 <= t]
    if not words:
        return im
    # maquetación: siempre la del bloque completo (sin saltos al aparecer palabras)
    full = [w['w'] for w in active]
    space = F_SUB.getlength(' ') + 6
    maxw = 820
    lines, line, lw = [], [], 0
    for i, wd in enumerate(full):
        wl = F_SUB.getlength(wd)
        if line and lw + space + wl > maxw:
            lines.append(line); line, lw = [], 0
        line.append(i); lw += (space if len(line) > 1 else 0) + wl
    lines.append(line)
    lh = 100
    cy = 1350
    y0 = cy - lh * len(lines) / 2
    layer = Image.new('RGBA', im.size, (0, 0, 0, 0))
    shadow = Image.new('RGBA', im.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer); ds = ImageDraw.Draw(shadow)
    cur_i = max(i for i, w in enumerate(active) if w['s'] - 0.05 <= t)
    for li, ln in enumerate(lines):
        tw = sum(F_SUB.getlength(full[i]) for i in ln) + space * (len(ln) - 1)
        x = 540 - tw / 2
        x = min(x, 960 - tw)
        y = y0 + li * lh
        for i in ln:
            wd = full[i]
            wl = F_SUB.getlength(wd)
            if i <= cur_i:
                age = t - (active[i]['s'] - 0.05)
                a = int(255 * min(1, age / 0.05))
                act = (i == cur_i and t < active[i]['e'] + 0.25)
                dy = 6 * max(0, 1 - age / 0.12)
                ds.text((x, y + 6 + dy), wd, font=F_SUB, fill=(0, 0, 0, int(a * 0.7)), stroke_width=8,
                        stroke_fill=(0, 0, 0, int(a * 0.7)))
                if act:
                    # cápsula negra al 60 % + rojo con contorno blanco
                    bb = F_SUB.getbbox(wd)
                    dl.rounded_rectangle((x + bb[0] - 16, y + dy + bb[1] - 12, x + bb[2] + 16, y + dy + bb[3] + 14),
                                         radius=22, fill=(0, 0, 0, int(a * 0.6)))
                    dl.text((x, y + dy), wd, font=F_SUB, fill=RED + (a,), stroke_width=4, stroke_fill=(255, 255, 255, a))
                else:
                    dl.text((x, y + dy), wd, font=F_SUB, fill=(255, 255, 255, a), stroke_width=6, stroke_fill=(0, 0, 0, a))
            x += wl + space
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))
    im = Image.alpha_composite(im, shadow)
    return Image.alpha_composite(im, layer)


_SRC = None


def draw_source(im):
    global _SRC
    if _SRC is None:
        f = font('IBMPlexMono-Regular.ttf', 22)
        lay = Image.new('RGBA', im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        tw = f.getlength(SRC_TXT)
        x = 540 - tw / 2
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x, 1507), SRC_TXT, font=f, fill=(0, 0, 0, 160))
        sh = sh.filter(ImageFilter.GaussianBlur(3))
        d.text((x, 1505), SRC_TXT, font=f, fill=CREAM + (int(255 * 0.55),))
        _SRC = Image.alpha_composite(sh, lay)
    return Image.alpha_composite(im, _SRC)


def ease(x):
    x = min(1, max(0, x))
    return x * x * (3 - 2 * x)


def draw_cta(im, t, t_cta, t_end):
    """Rótulo final: COMENTA: CONSTRUIR O RECUPERAR + firma."""
    a = ease((t - t_cta) / 0.35) * (1 - ease((t - (t_end - 0.12)) / 0.12))
    if a <= 0:
        return im
    dark = Image.new('RGBA', im.size, (7, 7, 7, int(150 * a)))
    im = Image.alpha_composite(im, dark)
    lay = Image.new('RGBA', im.size, (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay); ds = ImageDraw.Draw(sh)
    f1 = font('Anton-Regular.ttf', 64)
    f2 = font('Anton-Regular.ttf', 150)
    f3 = font('Anton-Regular.ttf', 92)
    fs = font('InterDisplay-SemiBold.ttf', 30)
    rows = [('COMENTA:', f1, RED, 640), ('CONSTRUIR', f2, CREAM, 720), ('O', f3, CREAM, 895), ('RECUPERAR', f2, CREAM, 1000)]
    for k, (txt, f, col, y) in enumerate(rows):
        ak = ease((t - t_cta - k * 0.09) / 0.25) * (1 - ease((t - (t_end - 0.12)) / 0.12))
        if ak <= 0:
            continue
        tw = f.getlength(txt)
        x = 525 - tw / 2
        dy = 18 * (1 - ak)
        ds.text((x + 4, y + 8 + dy), txt, font=f, fill=(0, 0, 0, int(200 * ak)))
        d.text((x, y + dy), txt, font=f, fill=col + (int(255 * ak),))
    sig = 'ALEIX JIMÉNEZ'
    spaced = ' '.join(sig).replace('   ', '  ')
    tw = fs.getlength(spaced)
    ak = ease((t - t_cta - 0.5) / 0.3) * (1 - ease((t - (t_end - 0.12)) / 0.12))
    d.text((525 - tw / 2, 1215), spaced, font=fs, fill=CREAM + (int(200 * ak),))
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    im = Image.alpha_composite(im, sh)
    return Image.alpha_composite(im, lay)

# ------------------------------------------------------------------ fotograma


def process(exr, meta, frame, t, shot, dim=1.0, overlays=True, tail=False):
    rgb, z, idx = read_exr(exr)
    # rótulos de cartón: siempre dentro de la franja de foco (sin desenfoque)
    m = (np.abs(idx - 1) < 0.5).astype(np.float32)
    keep = None
    if m.any():
        k = int(max(5, 14 * z.shape[1] / 720)) | 1
        keep = cv2.dilate(m, np.ones((k, k), np.uint8))
        keep = np.clip(cv2.GaussianBlur(keep, (0, 0), k / 3) * 1.6, 0, 1)
    fm = meta['focus'][str(frame)] if str(frame) in meta['focus'] else meta['focus'][str(meta['f0'])]
    h, w = z.shape
    rmax = 12.0 * w / 720
    strength = fm['ts']
    rgb = tilt_shift(rgb, z, fm['d'], fm.get('fy', 0.5), strength, rmax, keep)
    rgb = bloom(rgb)
    y = tonemap(rgb, exposure=EXPO.get(shot, 1.0))
    y = grade(y)
    y = cv2.resize(y, (OW, OH), interpolation=cv2.INTER_LANCZOS4)
    y = np.clip(y, 0, 1)
    bl = cv2.GaussianBlur(y, (0, 0), 1.2)
    y = np.clip(y + (y - bl) * 0.35, 0, 1)
    y = chroma_ab(y, 2.2)
    y = vignette(y)
    if shot == 'F_pueblos':
        y = dust(y, t, frame)
    y = grain(y, frame)
    im = Image.fromarray((y * 255 + 0.5).astype(np.uint8)).convert('RGBA')
    if overlays:
        if not tail:
            im = draw_subs(im, t)
        im = draw_source(im)
        if shot == 'H_dilema':
            im = draw_cta(im, t, CTA_T, CTA_END)
    im = im.convert('RGB')
    if dim != 1.0:
        im = Image.fromarray((np.asarray(im).astype(np.float32) * dim).astype(np.uint8))
    return im


EXPO = dict(A_hook=1.35, B_contraste=1.3, C_pregunta=1.6, D_ourense=1.45, E_provincias=1.5,
            F_pueblos=1.35, G_sintesis=1.6, H_dilema=1.3, P_portada=1.55)
S8 = TM['sentences'][8]
CTA_T = S8['e'] + 0.15
CTA_END = TM['duration'] - 0.8   # los últimos 0,8 s vuelven al plano 0 (bucle)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--shots', default='')
    ap.add_argument('--q', default='final')
    ap.add_argument('--frames', default='')
    ap.add_argument('--times', default='')
    ap.add_argument('--dim', type=float, default=1.0)
    ap.add_argument('--out', default=os.path.join(ROOT, 'post_frames'))
    ap.add_argument('--no-overlays', action='store_true')
    ap.add_argument('--portada', action='store_true')
    a = ap.parse_args()
    if a.portada:
        d = os.path.join(ROOT, 'renders', 'P_portada', 'cover')
        meta = json.load(open(os.path.join(d, 'meta.json')))
        f = meta['f0']
        im = process(os.path.join(d, 'f_%04d.exr' % f), meta, f, 20.0, 'P_portada', 1.0, False)
        od = os.path.join(ROOT, 'post_frames_portada'); os.makedirs(od, exist_ok=True)
        im.save(os.path.join(od, 'portada.png'))
        print('portada ok')
        return
    os.makedirs(a.out, exist_ok=True)
    shots = [s['name'] for s in TM['shots']] if not a.shots else a.shots.split(',')
    want = set(int(x) for x in a.frames.split(',')) if a.frames else None
    if a.times:
        want = set(int(round(float(x) * FPS)) + 1 for x in a.times.split(','))
    total = int(round(TM['duration'] * FPS))
    tail_f0 = int(round(CTA_END * FPS)) + 1
    for s in shots:
        d = os.path.join(ROOT, 'renders', s, a.q)
        meta = json.load(open(os.path.join(d, 'meta.json')))
        for f in range(meta['f0'], meta['f1'] + 1):
            if want and f not in want:
                continue
            out = os.path.join(a.out, 'f_%04d.png' % f)
            if os.path.exists(out) and not want:
                continue
            t = (f - 1) / FPS
            tail = s == 'H_dilema' and f >= tail_f0
            if tail:
                # bucle: vuelve el plano 0 de la calle
                dA = os.path.join(ROOT, 'renders', 'A_hook', a.q)
                mA = json.load(open(os.path.join(dA, 'meta.json')))
                exr = os.path.join(dA, 'f_%04d.exr' % mA['f0'])
                im = process(exr, mA, mA['f0'], t, 'A_hook', a.dim, not a.no_overlays, tail=True)
            else:
                exr = os.path.join(d, 'f_%04d.exr' % f)
                if not os.path.exists(exr) or os.path.getsize(exr) == 0:
                    print('falta', exr)
                    continue
                im = process(exr, meta, f, t, s, a.dim, not a.no_overlays)
            im.save(out, compress_level=1)
            print(s, f, flush=True)


if __name__ == '__main__':
    main()
