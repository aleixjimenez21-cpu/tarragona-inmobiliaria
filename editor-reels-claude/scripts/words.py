"""Pasa las palabras de Whisper (por toma) a la línea de tiempo final.
Ajusta inicios/finales con la energía real de la voz limpia (Whisper suele adelantar
el inicio de la palabra que sigue a una pausa) y asigna cada palabra al tramo que la contiene."""
import json, sys
import numpy as np, soundfile as sf
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import edl, TAKES, tid
from edl import timeline

THR = -52.0  # dBFS (ventanas de 10 ms) para considerar que hay voz

# Correcciones manuales comprobadas con la envolvente de energía (toma, índice de palabra) -> (inicio, fin)
# Whisper coloca "Tu" dentro de la pausa y lo funde con "comprador".
OVERRIDES = getattr(edl, "WORD_OVERRIDES", {})   # {(id_toma, índice_palabra): (inicio, fin)} definidos en edl.py


def envelope(take):
    x, sr = sf.read(f"work/audio/df_final/{take}.wav", dtype="float64")
    hop = sr // 100
    e = np.array([20 * np.log10(np.sqrt(np.mean(x[i:i + hop] ** 2)) + 1e-9) for i in range(0, len(x) - hop, hop)])
    return e


def refine(words, env):
    out = []
    for w in words:
        s, e = w["s"], w["e"]
        i = int(s * 100)
        while i < int(e * 100) - 4 and i < len(env) and env[i] < THR:
            i += 1
        j = int(e * 100)
        while j > i + 4 and j < len(env) and env[j] < THR:
            j -= 1
        out.append({**w, "s": i / 100, "e": (j + 1) / 100})
    return out


def build():
    d = json.load(open("work/transcript.json"))
    tl, vdur = timeline()
    res = []
    for k, a, b, t0 in tl:
        take = tid(k)
        ws = refine(d[take]["words"], envelope(take))
        for (tk, idx), (s0, e0) in OVERRIDES.items():
            if tk == take:
                ws[idx] = {**ws[idx], "s": s0, "e": e0}
        for w in ws:
            ov = min(w["e"], b) - max(w["s"], a)
            if ov <= 0.04 and not (w["s"] >= a and w["e"] <= b):
                continue
            s, e = max(w["s"], a), min(w["e"], b)
            res.append({"w": w["w"].strip(), "s": round(t0 + s - a, 3), "e": round(t0 + e - a, 3), "seg": k})
    json.dump(res, open("work/words_tl.json", "w"), ensure_ascii=False, indent=0)
    return res


if __name__ == "__main__":
    r = build()
    print(" ".join(f"{w['w']}@{w['s']:.2f}-{w['e']:.2f}" for w in r))
