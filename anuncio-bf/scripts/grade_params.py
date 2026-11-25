"""Calcula la corrección de color por toma midiendo la pared blanca (neutra) y la piel.
Salida: work/grade.json  {toma: {"gain": [r,g,b], "expo": x}}"""
import subprocess, json, sys
import numpy as np
sys.path.insert(0, "scripts")
from edl import TAKES
tr = json.load(open("work/face_tracks.json"))
WALL_TARGET = 0.70      # pared blanca en lineal (~ 218/255 en sRGB)
WARM = np.array([1.035, 1.0, 0.955])   # un punto cálido para la piel
lin = lambda x: (x / 255.0) ** 2.2
out = {}
for k, n in TAKES.items():
    walls = []
    for t in [0.8, 1.6, 2.4, 3.2, 4.0, 4.8]:
        b = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", f"input/{n}.mov", "-frames:v", "1", "-vf", "scale=540:960",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        im = np.frombuffer(b, np.uint8).reshape(960, 540, 3).astype(float)
        i = min(int(t * 10), len(tr[k]["x"]) - 1)
        fx, fy, fw = tr[k]["x"][i] / 2, tr[k]["y"][i] / 2, tr[k]["w"][i] / 2
        wx = int(min(530, fx + fw * 1.6))
        walls.append(lin(im[int(fy - fw):int(fy), wx - 16:wx]).reshape(-1, 3).mean(0))
    w = np.mean(walls, 0)
    gain = w.mean() / w * WARM
    expo = WALL_TARGET / w.mean()
    out[k] = dict(gain=gain.round(4).tolist(), expo=round(float(expo), 3))
    print(k, out[k])
json.dump(out, open("work/grade.json", "w"), indent=1)
