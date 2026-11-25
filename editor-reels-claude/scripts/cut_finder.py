"""Ayuda a escribir SEGMENTS en edl.py: para cada toma muestra las palabras (Whisper), dónde empieza y acaba la voz
y las pausas internas, medidas con la energía de la voz limpia (más fiable que Whisper en el inicio y el final).
Uso: python3 <skill>/scripts/cut_finder.py [--detalle toma inicio fin]"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import TAKES, tid
import numpy as np, soundfile as sf


def env(t, hop_s=0.01):
    x, sr = sf.read(f"work/audio/df_final/{t}.wav"); hop = int(sr * hop_s)
    return np.array([20 * np.log10(np.sqrt(np.mean(x[i:i + hop] ** 2)) + 1e-9) for i in range(0, len(x) - hop, hop)])


if "--detalle" in sys.argv:
    i = sys.argv.index("--detalle"); k, a, b = sys.argv[i + 1], float(sys.argv[i + 2]), float(sys.argv[i + 3])
    e = env(tid(k)); print(" ".join(f"{a + j * 0.01:.2f}:{v:.0f}" for j, v in enumerate(e[int(a * 100):int(b * 100)])))
    sys.exit()
d = json.load(open("work/transcript.json"))
for k in TAKES:
    t = tid(k); e = env(t, 0.02)
    print(f"== {k} {t}")
    print("   " + " ".join(f"{w['w'].strip()}[{w['s']:.2f}-{w['e']:.2f}]" for w in d[t]["words"]))
    sp = np.where(e > e.max() - 35)[0]
    gaps, prev = [], sp[0]
    for i in sp[1:]:
        if (i - prev) * 0.02 > 0.2: gaps.append((round(prev * 0.02 + 0.02, 2), round(i * 0.02, 2)))
        prev = i
    print(f"   voz de {sp[0] * 0.02:.2f} a {sp[-1] * 0.02 + 0.02:.2f} s (toma de {len(e) * 0.02:.2f} s); pausas > 0,2 s: {gaps}")
print("\nConsejo: entra ~0,04 s antes del inicio de voz y sal ~0,08 s después del final; para afinar usa --detalle <toma> <ini> <fin>.")
