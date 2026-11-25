"""Pasa las palabras de Whisper (por toma) a la línea de tiempo final.
Ajusta inicios/finales con la energía real de la voz limpia (Whisper suele adelantar
el inicio de la palabra que sigue a una pausa) y asigna cada palabra al tramo que la contiene."""
import json, sys
import numpy as np, soundfile as sf
sys.path.insert(0, "scripts")
from edl import TAKES, timeline

THR = -52.0  # dBFS (ventanas de 10 ms) para considerar que hay voz

# Correcciones manuales comprobadas con la envolvente de energía (toma, índice de palabra) -> (inicio, fin)
# Whisper coloca "Tu" dentro de la pausa y lo funde con "comprador".
OVERRIDES = {
    # oferta: Whisper adelanta ~0,2 s el arranque ("Por" caía en el silencio) -> sílabas según la envolvente
    ("f770c468", 0): (1.83, 2.02), ("f770c468", 1): (2.03, 2.30), ("f770c468", 2): (2.33, 2.68),
    ("f770c468", 3): (2.86, 2.95), ("f770c468", 4): (2.95, 3.14),
    ("f770c468", 10): (4.62, 5.06),                                   # "tiene" (antes de la pausa recortada)
    # qué hacemos: "recorrerlo | mucho antes" (la pausa se recorta)
    ("e8b41a7e", 14): (5.40, 6.29), ("e8b41a7e", 15): (6.72, 6.94), ("e8b41a7e", 16): (6.95, 7.18),
}


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
    d = json.load(open("work/transcript_large-v3.json"))
    tl, vdur = timeline()
    res = []
    for k, a, b, t0 in tl:
        take = TAKES[k].replace("take_", "")
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
