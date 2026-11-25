"""Análisis de reverberación de la voz.
Para cada final de frase seguido de pausa (>= 250 ms) mide:
  - cola: energía 40-200 ms después del final respecto al nivel de los últimos 150 ms de voz (dB)
  - EDT/RT60 equivalente: pendiente de caída en los primeros 150 ms (s para caer 60 dB)
y la inteligibilidad (confianza media de Whisper large-v3) para detectar artefactos.
Uso: python3 scripts/reverb_analysis.py variante1=dir1 variante2=dir2 ..."""
import sys, json
import numpy as np, soundfile as sf
from scipy.signal import resample_poly

TAKES = ["eb7c3ce3", "43493248", "9ba76478", "a54f3308"]
HOP = 0.005


def env_db(x, sr):
    h = int(sr * HOP); w = int(sr * 0.02)
    p = np.convolve(x ** 2, np.ones(w) / w, "same")[::h]
    return 10 * np.log10(p + 1e-12)


def load(path):
    x, sr = sf.read(path, dtype="float64")
    if x.ndim > 1: x = x.mean(1)
    return x, sr


# finales de frase: a partir de la voz limpia actual
offsets = {}
for t in TAKES:
    x, sr = load(f"work/audio/df_final/{t}.wav")
    e = env_db(x, sr); thr = e.max() - 32
    sp = e > thr
    offs = []
    i = 0
    while i < len(sp) - 1:
        if sp[i] and not sp[i + 1]:
            j = i + 1
            while j < len(sp) and not sp[j]: j += 1
            if (j - i) * HOP >= 0.25 and i * HOP > 0.3: offs.append(i * HOP)
            i = j
        else:
            i += 1
    offsets[t] = offs


def analyse(d):
    tails, rts = [], []
    for t in TAKES:
        x, sr = load(f"{d}/{t}.wav")
        e = env_db(x, sr)
        for o in offsets[t]:
            k = int(o / HOP)
            if k + 45 >= len(e): continue
            ref = np.median(e[k - 30:k])
            tail = np.mean(e[k + 8:k + 40]) - ref
            seg = e[k:k + 30]
            slope = np.polyfit(np.arange(len(seg)) * HOP, seg, 1)[0]   # dB/s (negativo)
            tails.append(tail); rts.append(60 / max(1e-3, -slope))
    return np.mean(tails), np.median(rts)


def intelligibility(d, model):
    ps = []; txt = []
    for t in TAKES:
        x, sr = load(f"{d}/{t}.wav")
        x16 = resample_poly(x, 1, 3).astype(np.float32) if sr == 48000 else resample_poly(x, 160, 441).astype(np.float32)
        segs, _ = model.transcribe(x16, language="es", word_timestamps=True, beam_size=5)
        ws = [w for s in segs for w in s.words]
        ps += [w.probability for w in ws]; txt.append("".join(w.word for w in ws).strip())
    return float(np.mean(ps)), txt


if __name__ == "__main__":
    from faster_whisper import WhisperModel
    m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4)
    print("finales de frase analizados:", sum(len(v) for v in offsets.values()))
    res = {}
    for arg in sys.argv[1:]:
        name, d = arg.split("=")
        tail, rt = analyse(d)
        p, txt = intelligibility(d, m)
        res[name] = dict(cola_db=round(tail, 1), rt60_equiv_s=round(rt, 3), whisper_conf=round(p, 3), texto=txt)
        print(f"{name:14s} cola {tail:6.1f} dB | RT60 equiv. {rt:5.2f} s | Whisper {p:.3f} | {txt[2][:70]}")
    json.dump(res, open("work/audio/reverb_analysis.json", "w"), ensure_ascii=False, indent=1)
