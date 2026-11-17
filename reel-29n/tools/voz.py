#!/usr/bin/env python3
"""Prepara la narración: quita tomas falsas, mejora la voz y traduce los cortes.

Entrada: input/voz.(wav|mp3|m4a|...) y, opcional, input/voz_cortes.json
Salida:  build/voz/voz_limpia.wav (48 kHz mono) y build/voz/cortes_limpios.json

Cadena de mejora (ffmpeg): filtro de graves 80 Hz, reducción de ruido suave,
ecualización (calidez 140 Hz, menos «barro» 350 Hz, presencia 3,5 kHz, aire 11 kHz),
de-esser y compresión suave. Nunca se cambia la velocidad ni el tono.
"""
import glob, json, os, subprocess, sys
import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "voz")
SR = 48000
CHAIN = ("highpass=f=80:poles=2,"
         "afftdn=nr=8:nf=-55:tn=1,"
         "equalizer=f=140:t=q:w=1.0:g=2.5,"
         "equalizer=f=350:t=q:w=1.2:g=-3,"
         "equalizer=f=3500:t=q:w=1.0:g=3,"
         "highshelf=f=11000:g=2.5,"
         "deesser=i=0.35:m=0.5:f=0.5,"
         "acompressor=threshold=-22dB:ratio=3:attack=6:release=90:makeup=3:knee=4,"
         "alimiter=limit=0.89:level=false")


def find_input():
    for ext in ("wav", "mp3", "m4a", "aac", "flac", "ogg", "opus", "webm"):
        p = os.path.join(ROOT, "input", "voz." + ext)
        if os.path.exists(p):
            return p
    return None


def prepare(src):
    os.makedirs(OUT, exist_ok=True)
    raw = os.path.join(OUT, "voz_raw.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", str(SR), raw], check=True)
    x, sr = sf.read(raw)
    cortes_p = os.path.join(ROOT, "input", "voz_cortes.json")
    cortes = json.load(open(cortes_p, encoding="utf-8")) if os.path.exists(cortes_p) else {}
    quitar = sorted(cortes.get("quitar", []))
    # quitar tramos con fundido de 15 ms
    keep, t = [], 0.0
    for a, b in quitar:
        keep.append((t, a)); t = b
    keep.append((t, len(x) / sr))
    fade = int(0.015 * sr)
    parts = []
    for a, b in keep:
        seg = x[int(a * sr):int(b * sr)].copy()
        if len(seg) > 2 * fade:
            seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
        parts.append(seg)
    y = np.concatenate(parts)

    def remap(tt):
        shift = 0.0
        for a, b in quitar:
            if tt >= b: shift += b - a
            elif tt > a: return a - shift
        return tt - shift

    cut = os.path.join(OUT, "voz_cortada.wav")
    sf.write(cut, y, sr)
    clean = os.path.join(OUT, "voz_limpia.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", cut, "-af", CHAIN, "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s24le", clean], check=True)
    if "clips" in cortes:
        cl = {k: [remap(v[0]), remap(v[1])] for k, v in cortes["clips"].items()}
        json.dump(cl, open(os.path.join(OUT, "cortes_limpios.json"), "w"), indent=1)
    elif os.path.exists(os.path.join(OUT, "cortes_limpios.json")):
        os.remove(os.path.join(OUT, "cortes_limpios.json"))
    print("[voz] %s -> %s (%.1f s)" % (os.path.basename(src), clean, len(y) / sr))
    return clean


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else find_input()
    if not src:
        sys.exit("[voz] no hay input/voz.*")
    prepare(src)
