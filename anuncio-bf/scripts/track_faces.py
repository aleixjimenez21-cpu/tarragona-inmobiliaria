"""Seguimiento de cara en cada toma (Haar de OpenCV a 10 fps + suavizado) para que el reencuadre
siga a la persona como lo haría un operador de cámara. Coordenadas en el fotograma completo a 1080x1920.
Salida: work/face_tracks.json  {toma: {"t": [...], "x": [...], "y": [...], "w": [...]}}"""
import json, subprocess, sys
import numpy as np, cv2
sys.path.insert(0, "scripts")
from edl import TAKES

casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
W, H = 540, 960   # detección a media resolución
out = {}
for k, name in TAKES.items():
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", f"input/{name}.mov", "-vf", f"fps=10,scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
    ts, xs, ys, ws = [], [], [], []
    i = 0; prev = None
    while True:
        b = p.stdout.read(W * H)
        if len(b) < W * H: break
        g = np.frombuffer(b, np.uint8).reshape(H, W)
        fs = casc.detectMultiScale(g, 1.05, 4, minSize=(24, 24))
        if len(fs):
            if prev is not None:   # la más cercana a la anterior
                f = min(fs, key=lambda r: (r[0] + r[2] / 2 - prev[0]) ** 2 + (r[1] + r[3] / 2 - prev[1]) ** 2 - 4 * r[2] * r[3])
            else:
                f = max(fs, key=lambda r: r[2] * r[3])
            x, y, w, h = f
            prev = (x + w / 2, y + h / 2)
            ts.append(i / 10); xs.append((x + w / 2) * 2); ys.append((y + h / 2) * 2); ws.append(w * 2)
        i += 1
    ts, xs, ys, ws = map(np.array, (ts, xs, ys, ws))
    # descarta detecciones atípicas y suaviza (media móvil centrada de ~0,9 s)
    keep = np.ones(len(ts), bool)
    for arr in (xs, ys, ws):
        med = np.median(arr); mad = np.median(np.abs(arr - med)) + 1
        keep &= np.abs(arr - med) < 6 * mad
    ts, xs, ys, ws = ts[keep], xs[keep], ys[keep], ws[keep]
    tg = np.arange(0, i / 10, 0.1)
    def sm(a):
        g = np.interp(tg, ts, a)
        k = np.ones(9) / 9
        return np.convolve(np.pad(g, 4, mode="edge"), k, "valid")
    out[k] = dict(t=tg.round(2).tolist(), x=sm(xs).round(1).tolist(), y=sm(ys).round(1).tolist(), w=sm(ws).round(1).tolist())
    print(k, name, f"det {keep.sum()}/{i}", "x %.0f-%.0f" % (min(out[k]['x']), max(out[k]['x'])), "y %.0f-%.0f" % (min(out[k]['y']), max(out[k]['y'])), "w %.0f-%.0f" % (min(out[k]['w']), max(out[k]['w'])))
json.dump(out, open("work/face_tracks.json", "w"))
