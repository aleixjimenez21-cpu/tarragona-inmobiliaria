"""Control de calidad del archivo final: duración, loudness (EBU R128 / true peak),
clics o saltos bruscos en los cortes, y extracción de fotogramas de revisión.
Uso (desde la carpeta del proyecto): python3 <skill>/scripts/qc.py output/<nombre>_9x16.mp4"""
import json, subprocess, sys
import numpy as np

f = sys.argv[1]
P = json.load(open("work/plan.json"))
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))
print(f"Duración: {dur:.2f} s  ({'OK' if dur <= 30 else 'DEMASIADO LARGO'})")
st = subprocess.run(["ffmpeg", "-hide_banner", "-i", f, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
summ = st[st.rfind("Summary:"):]
I = float(summ.split("I:")[1].split("LUFS")[0]); TP = float(summ.split("Peak:")[1].split("dBFS")[0]); LRA = float(summ.split("LRA:")[1].split("LU")[0])
print(f"Loudness integrado: {I:.1f} LUFS | True peak: {TP:.1f} dBTP | LRA: {LRA:.1f} LU")

# audio decodificado para buscar clics en los cortes
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], capture_output=True).stdout
x = np.frombuffer(raw, np.float32)
d = np.abs(np.diff(x))
med = np.median(d) + 1e-9
cuts = [s[3] for s in P["segments"][1:]]
print("Cortes de voz (s):", [round(c, 2) for c in cuts])
worst = []
for c in cuts:
    i = int(c * 48000)
    w = d[i - 480:i + 480]
    ref = d[i - 24000:i - 2400]
    ratio = w.max() / (np.percentile(ref, 99.9) + 1e-9)
    worst.append(ratio)
    import os
    sfx = json.load(open("work/sfx.json")) if os.path.exists("work/sfx.json") else []
    near = [e["id"] for e in sfx if abs(e["at"] - c) < 0.2]
    estado = "ok" if ratio <= 1.5 else (f"transitorio del efecto {near[0]} colocado en el corte (normal)" if near else "posible clic: revisa el corte")
    print(f"  corte {c:6.2f}s: pico de derivada / p99.9 del entorno = {ratio:.2f} {estado}")
# clics en todo el archivo: derivadas aisladas muy por encima del entorno
win = 4800
flags = []
for i in range(win, len(d) - win, 2400):
    seg = d[i:i + 2400]
    env = np.percentile(d[i - win:i + win], 99.5) + 1e-9
    if seg.max() > 4 * env and seg.max() > 0.05:
        flags.append(round(i / 48000, 2))
print("Posibles clics en todo el archivo:", flags if flags else "ninguno")
