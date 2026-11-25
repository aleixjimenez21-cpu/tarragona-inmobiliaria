"""Compositor: genera el vídeo final fotograma a fotograma.
- Planos míos: se decodifican desde el original 4K, reencuadre/zoom (punch-in) con escalado de calidad,
  corrección de color suave (contraste algo más alto, piel natural) y enfoque ligero.
- Clips del tour con transiciones (whip, zoom, fundido) y el cambio a noche en el plano aéreo.
- PiP mío redondeado mientras el tour ocupa la pantalla.
- Capa de gráficos (PNG con alfa renderizados desde overlay.html).
Uso: python3 compose.py <9x16|4x5> [--test t1,t2,...]"""
import json, subprocess, sys, os, math
import numpy as np, cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
P = json.load(open("work/plan.json"))
FPS = P["fps"]; TOTAL = P["total"]; NF = int(round(TOTAL * FPS))
FMT = sys.argv[1] if len(sys.argv) > 1 else "9x16"
OW, OH = 1080, (1920 if FMT == "9x16" else 1350)
TEST = None
if "--test" in sys.argv:
    TEST = [float(x) for x in sys.argv[sys.argv.index("--test") + 1].split(",")]
INTER = (2160, 3840)   # mis planos se decodifican a 4K nativo


def ease_out(x):
    x = min(1, max(0, x)); return 1 - (1 - x) ** 3


def smooth(x):
    x = min(1, max(0, x)); return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ lectores de vídeo secuenciales
class Reader:
    """Lee fotogramas a 30 fps desde un archivo; reabre ffmpeg si hay que saltar hacia atrás o lejos."""
    def __init__(self, path, size, prefilter=""):
        self.path, self.size, self.pre = path, size, prefilter
        self.proc = None; self.start = None; self.idx = -1; self.frame = None
        d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]))
        self.dur = d

    def _open(self, t):
        if self.proc: self.proc.kill()
        w, h = self.size
        vf = f"fps={FPS},{self.pre}scale={w}:{h}:flags=lanczos"
        self.proc = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{max(0, t):.4f}", "-i", self.path, "-vf", vf,
                                      "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, bufsize=10 ** 8)
        self.start = max(0, t); self.idx = -1; self.frame = None

    def get(self, t):
        t = min(max(0, t), self.dur - 1.5 / FPS)
        want = None
        if self.proc is not None:
            want = int(round((t - self.start) * FPS))
        if self.proc is None or want < self.idx or want - self.idx > 45:
            self._open(t); want = 0
        w, h = self.size
        while self.idx < want:
            buf = self.proc.stdout.read(w * h * 3)
            if len(buf) < w * h * 3:
                break  # fin del archivo: se congela el último fotograma
            self.frame = np.frombuffer(buf, np.uint8).reshape(h, w, 3); self.idx += 1
        return self.frame


readers = {}
def reader(key, path, size, pre=""):
    if key not in readers: readers[key] = Reader(path, size, pre)
    return readers[key]


# ------------------------------------------------------------------ color de mis planos
def build_lut():
    x = np.arange(256) / 255.0
    s = x * x * (3 - 2 * x)                       # curva en S
    y = x + 0.16 * (s - x)                         # contraste ligeramente más alto
    y = 0.012 + y * (1 - 0.012)                    # negros sin aplastar
    return np.clip(y * 255, 0, 255).astype(np.uint8)
LUT = build_lut()
# equilibrio por toma (las dos tomas comprimidas vienen algo más frías/planas): ganancias RGB
WB = {k: (1.025, 1.0, 0.97) for k in "ABCD"}   # un punto más cálido: piel natural frente a la luz fría de la oficina
if os.path.exists("work/wb.json"): WB.update({k: tuple(v) for k, v in json.load(open("work/wb.json")).items()})


def grade(img, take):
    f = img.astype(np.float32)
    g = WB.get(take, (1, 1, 1))
    f *= np.array(g, np.float32)
    f = np.clip(f, 0, 255).astype(np.uint8)
    f = cv2.LUT(f, LUT)
    # saturación +6 % (vibrance suave)
    hsv = cv2.cvtColor(f, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.06, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)


def sharpen(img, amount=0.28, sigma=1.1):
    b = cv2.GaussianBlur(img, (0, 0), sigma)
    return cv2.addWeighted(img, 1 + amount, b, -amount, 0)


# ------------------------------------------------------------------ fuentes
def take_src_time(take, t):
    """tiempo de la toma original para el instante t de la línea de tiempo (continúa más allá del corte si hace falta)"""
    best = None
    for k, a, b, t0 in P["segments"]:
        if k != take: continue
        if t0 - 0.001 <= t <= t0 + (b - a) + 0.001: return a + (t - t0)
        if best is None or t > t0: best = (a, t0)
    a, t0 = best
    return a + (t - t0)


TRACKS = json.load(open("work/face_tracks.json"))


def face_of(take, src=None):
    """posición de la cara (seguimiento suavizado) en el instante src de la toma"""
    if src is None or take not in TRACKS:
        return P["faces"][take]
    tr = TRACKS[take]; tt = np.array(tr["t"])
    # suavizado extra (±0,4 s) para que el reencuadre se mueva como un operador, no a tirones
    ts = np.linspace(src - 0.4, src + 0.4, 9)
    return tuple(float(np.mean(np.interp(ts, tt, tr[c]))) for c in ("x", "y", "w"))


def a_frame(entry, t, zoom_mul=1.0):
    take = entry["take"]
    path = f"input/{P['takes'][take]}.mov"
    r = reader("A" + take, path, INTER, "hqdn3d=1.2:1.2:4:4," if take in ("B", "C") else "")
    src = take_src_time(take, t)
    img = r.get(src)
    k = (t - entry["t0"]) / max(0.001, entry["t1"] - entry["t0"])
    fx, fy, fw = face_of(take, src)
    fwt = (entry["fw0"] + (entry["fw1"] - entry["fw0"]) * smooth(k)) * (1.0 if FMT == "9x16" else 0.82)
    z = min(2.0, max(1.0, fwt / fw))
    if entry.get("punch"):
        z *= 1 + 0.05 * (1 - ease_out((t - entry["t0"]) / 0.22))
    z = min(2.0, z * zoom_mul)
    s = INTER[0] / 1080.0                           # base 1080x1920 -> intermedia
    # ventana de recorte en coordenadas base: ancho OW/z, alto OH/z, con la cara en (540, face_y)
    face_y = entry["face_y"] if FMT == "9x16" else entry.get("face_y45", entry["face_y"] * OH / 1920 * 0.86)
    cw, ch = OW / z, OH / z
    x0 = fx - 540 / z; y0 = fy - face_y / z
    x0 = min(max(0, x0), 1080 - cw); y0 = min(max(0, y0), 1920 - ch)
    # reducción de calidad: primero INTER_AREA a la escala justa, luego desplazamiento subpíxel
    scale = z / s
    small = cv2.resize(img, (int(math.ceil(INTER[0] * scale)) + 2, int(math.ceil(INTER[1] * scale)) + 2), interpolation=cv2.INTER_AREA)
    M2 = np.array([[1, 0, -x0 * z], [0, 1, -y0 * z]], np.float32)
    out = cv2.warpAffine(small, M2, (OW, OH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return sharpen(grade(out, take))


def b_frame(entry, t, clip=None):
    clip = clip or entry["clip"]
    r = reader("B" + clip, f"work/clips/{clip}.mp4", (1080, 1920))
    src = entry["src"] + (t - entry["t0"]) * entry["speed"]
    img = r.get(src)
    if entry.get("shift_y"):
        img = cv2.warpAffine(img, np.float32([[1, 0, 0], [0, 1, entry["shift_y"]]]), (1080, 1920), borderMode=cv2.BORDER_REPLICATE)
    if FMT == "4x5":
        # reencuadre 4:5: recorte vertical centrado algo por encima del centro (horizonte/arquitectura)
        y0 = int((1920 - 1350) * 0.42)
        img = img[y0:y0 + 1350]
    return img


def entry_at(t):
    for e in P["video"]:
        if e["t0"] - 1e-6 <= t < e["t1"] - 1e-6: return e
    return P["video"][-1]


def render_entry(e, t):
    if e["kind"] == "a": return a_frame(e, t)
    img = b_frame(e, t)
    n = P["night"]
    if e["clip"] == "v01_aire_atardecer" and t >= n["t0"]:
        k = smooth((t - n["t0"]) / n["dur"])
        night = b_frame(e, t, n["clip"])
        img = cv2.addWeighted(img, 1 - k, night, k, 0)
    return img


def hblur(img, k, shift):
    k = int(k)
    if k > 1: img = cv2.blur(img, (k, 1))
    if shift: img = cv2.warpAffine(img, np.float32([[1, 0, shift], [0, 1, 0]]), (img.shape[1], img.shape[0]), borderMode=cv2.BORDER_REFLECT)
    return img


def zoomblur(img, amt):
    if amt <= 0.001: return img
    h, w = img.shape[:2]; acc = img.astype(np.float32); n = 1
    for i in range(1, 9):
        z = 1 + amt * i / 8
        M = cv2.getRotationMatrix2D((w / 2, h / 2), 0, z)
        acc += cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT); n += 1
    return (acc / n).astype(np.uint8)


def base_frame(t):
    e = entry_at(t)
    img = render_entry(e, t)
    i = P["video"].index(e)
    nxt = P["video"][i + 1] if i + 1 < len(P["video"]) else None
    TR = 5 / FPS
    # transición de entrada de este plano
    dt = t - e["t0"]
    if e.get("trans") == "whip" and dt < TR:
        k = 1 - dt / TR
        img = hblur(img, 120 * k, 140 * k)
    if e.get("trans") == "zoom" and dt < TR:
        k = 1 - dt / TR
        img = zoomblur(img, 0.22 * k)
    if e.get("trans") == "dissolve" and dt < 8 / FPS and i > 0:
        prev = P["video"][i - 1]
        k = smooth(dt / (8 / FPS))
        img = cv2.addWeighted(render_entry(prev, t), 1 - k, img, k, 0)
    # transición de salida hacia el siguiente plano
    if nxt is not None:
        rem = nxt["t0"] - t
        if nxt.get("trans") == "whip" and rem < TR:
            k = 1 - rem / TR
            img = hblur(img, 120 * k, -140 * k)
        if nxt.get("trans") == "zoom" and rem < TR:
            k = 1 - rem / TR
            img = zoomblur(img, 0.22 * k)
    return img


# ------------------------------------------------------------------ PiP
PIP_BOX = dict(x=1080 - 48 - 270, y=372, w=270, h=360, r=30) if FMT == "9x16" else dict(x=1080 - 40 - 230, y=40, w=230, h=306, r=26)


def pip_layer(t):
    for p in P["pip"]:
        if p["t0"] <= t < p["t1"]:
            take = p["take"]
            r = reader("P" + take, f"input/{P['takes'][take]}.mov", (1080, 1920), "hqdn3d=1.2:1.2:4:4,")
            src = take_src_time(take, t)
            img = r.get(src)
            fx, fy, fw = face_of(take, src)
            B = PIP_BOX
            cw = 2.9 * fw; ch = cw * B["h"] / B["w"]
            x0 = int(min(max(0, fx - cw / 2), 1080 - cw)); y0 = int(min(max(0, fy - ch * 0.38), 1920 - ch))
            crop = img[y0:int(y0 + ch), x0:int(x0 + cw)]
            crop = sharpen(grade(cv2.resize(crop, (B["w"], B["h"]), interpolation=cv2.INTER_AREA), take), 0.2)
            k = ease_out((t - p["t0"]) / 0.25) * min(1, (p["t1"] - t) / 0.12)
            return crop, k
    return None, 0


def rounded_mask(w, h, r):
    m = np.zeros((h * 4, w * 4), np.uint8)
    R = r * 4
    cv2.rectangle(m, (R, 0), (w * 4 - R, h * 4), 255, -1); cv2.rectangle(m, (0, R), (w * 4, h * 4 - R), 255, -1)
    for cx, cy in ((R, R), (w * 4 - R, R), (R, h * 4 - R), (w * 4 - R, h * 4 - R)):
        cv2.circle(m, (cx, cy), R, 255, -1)
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255


PMASK = rounded_mask(PIP_BOX["w"], PIP_BOX["h"], PIP_BOX["r"])
BW = 5
PMASK_OUT = rounded_mask(PIP_BOX["w"] + 2 * BW, PIP_BOX["h"] + 2 * BW, PIP_BOX["r"] + BW)


def composite_pip(img, crop, k):
    if crop is None or k <= 0: return img
    B = PIP_BOX
    s = 0.85 + 0.15 * k
    w, h = int(B["w"] * s), int(B["h"] * s)
    cx, cy = B["x"] + B["w"] / 2, B["y"] + B["h"] / 2
    out = img.astype(np.float32)
    # sombra suave
    sh = np.zeros(img.shape[:2], np.float32)
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    m_out = cv2.resize(PMASK_OUT, (w + 2 * BW, h + 2 * BW))
    sh[y0 - BW + 14:y0 + h + BW + 14, x0 - BW:x0 + w + BW] = m_out
    sh = cv2.GaussianBlur(sh, (0, 0), 18) * 0.45 * k
    out *= (1 - sh[..., None])
    # borde blanco
    a = m_out * k
    reg = out[y0 - BW:y0 + h + BW, x0 - BW:x0 + w + BW]
    reg[:] = reg * (1 - a[..., None]) + 245 * a[..., None]
    # imagen
    c = cv2.resize(crop, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)
    m = cv2.resize(PMASK, (w, h)) * k
    reg = out[y0:y0 + h, x0:x0 + w]
    reg[:] = reg * (1 - m[..., None]) + c * m[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ tarjeta final: fondo desenfocado
def end_bg(img, t):
    a = P["cues"]["end_full"]
    if t < a: return img
    k = smooth((t - a) / 0.35)
    bl = cv2.GaussianBlur(img, (0, 0), 6 + 22 * k)
    return cv2.addWeighted(img, 1 - k, bl, k, 0)


def overlay(img, i):
    path = f"work/ovl_{FMT}/o_{i:04d}.png"
    o = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if o is None: return img
    o = cv2.cvtColor(o, cv2.COLOR_BGRA2RGBA).astype(np.float32)
    a = o[..., 3:4] / 255.0
    return np.clip(img.astype(np.float32) * (1 - a) + o[..., :3] * a, 0, 255).astype(np.uint8)


def frame(i):
    t = i / FPS
    img = base_frame(t)
    crop, k = pip_layer(t)
    img = composite_pip(img, crop, k)
    img = end_bg(img, t)
    return overlay(img, i)


if __name__ == "__main__":
    if TEST:
        os.makedirs("work/test_frames", exist_ok=True)
        for t in TEST:
            i = int(round(t * FPS))
            cv2.imwrite(f"work/test_frames/{FMT}_{t:05.2f}.jpg", cv2.cvtColor(frame(i), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
            for r in readers.values():
                if r.proc: r.proc.kill(); r.proc = None
        print("test ok")
        sys.exit()
    out = f"work/video_{FMT}.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                            "-i", "work/audio/final_audio.wav",
                            "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-profile:v", "high",
                            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
                            "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
    for i in range(NF):
        enc.stdin.write(frame(i).tobytes())
        if i % 60 == 0: print(f"{i}/{NF}", flush=True)
    enc.stdin.close(); enc.wait()
    print("ok", out)
