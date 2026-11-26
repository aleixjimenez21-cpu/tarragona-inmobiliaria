"""Crea un clip vertical (1080x1920, 30 fps) a partir de imágenes fijas (planos, renders, capturas, fotos):
tarjetas redondeadas con sombra que van entrando una tras otra sobre un fondo desenfocado y oscuro, con un empuje
lento de cámara. Sirve para enseñar "lo de antes" (planos, PDF, renders) frente al producto en movimiento.
Uso: python3 <skill>/scripts/make_stills.py <salida_nombre> <duración_s> img1 [img2 …]
     -> work/clips/<salida_nombre>.mp4 (se usa en plan.py con broll("<salida_nombre>", …))"""
import sys, os, math, subprocess
import numpy as np, cv2
from PIL import Image

name, dur, imgs = sys.argv[1], float(sys.argv[2]), sys.argv[3:]
W, H, FPS = 1080, 1920, 30
N = int(round(dur * FPS))
os.makedirs("work/clips", exist_ok=True)
cards = [np.asarray(Image.open(p).convert("RGB")).astype(np.float32) for p in imgs]

# fondo: la última imagen, a pantalla completa, muy desenfocada y oscurecida
bg = cards[-1]
s = max(W / bg.shape[1], H / bg.shape[0]) * 1.1
bg = cv2.resize(bg, (int(bg.shape[1] * s), int(bg.shape[0] * s)), interpolation=cv2.INTER_AREA)
y0, x0 = (bg.shape[0] - H) // 2, (bg.shape[1] - W) // 2
bg = cv2.GaussianBlur(bg[y0:y0 + H, x0:x0 + W], (0, 0), 40) * 0.42


def rounded(w, h, r):
    m = np.zeros((h, w), np.float32)
    cv2.rectangle(m, (r, 0), (w - r, h), 1, -1); cv2.rectangle(m, (0, r), (w, h - r), 1, -1)
    for cx, cy in ((r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)):
        cv2.circle(m, (cx, cy), r, 1, -1, lineType=cv2.LINE_AA)
    return cv2.GaussianBlur(m, (0, 0), 0.8)


CW = 940
layouts = []   # (imagen escalada, máscara, centro y final, rotación, instante de entrada)
n = len(cards)
for i, c in enumerate(cards):
    h = int(c.shape[0] * CW / c.shape[1])
    img = cv2.resize(c, (CW, h), interpolation=cv2.INTER_AREA)
    cy = H / 2 + (i - (n - 1) / 2) * min(560, h * 0.82)
    rot = (-2.2 if i % 2 == 0 else 2.6)
    layouts.append((img, rounded(CW, h, 26), cy, rot, i * dur / (n + 0.6)))

ease = lambda x: 1 - (1 - min(1, max(0, x))) ** 3
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                      "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p", f"work/clips/{name}.mp4"], stdin=subprocess.PIPE)
for f in range(N):
    t = f / FPS
    frame = bg.copy()
    zoom = 1 + 0.06 * t / dur                                   # empuje lento de cámara
    for li, (img, m, cy, rot, t0) in enumerate(layouts):
        k = ease((t - t0) / 0.45)
        if k <= 0: continue
        h, w = img.shape[:2]
        sc = zoom * (0.9 + 0.1 * k)
        M = cv2.getRotationMatrix2D((w / 2, h / 2), rot * (0.6 + 0.4 * k), sc)
        M[0, 2] += W / 2 - w / 2 + (1 - k) * 380 * (1 if li % 2 else -1)
        M[1, 2] += (cy - H / 2) * zoom + H / 2 - h / 2
        warped = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR)
        mask = cv2.warpAffine(m, M, (W, H), flags=cv2.INTER_LINEAR) * k
        sh = cv2.GaussianBlur(cv2.warpAffine(m, M, (W, H)), (0, 0), 30)
        sh = np.roll(sh, 24, axis=0) * 0.55 * k
        frame = frame * (1 - sh[..., None])
        frame = frame * (1 - mask[..., None]) + warped * mask[..., None]
    p.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
p.stdin.close(); p.wait()
print(f"work/clips/{name}.mp4", N, "fotogramas")
