"""Edición automática de la locución:
1. Transcribe la toma bruta palabra a palabra (faster-whisper).
2. Localiza cada frase del guion; si una frase está repetida (varias tomas), se queda con la última.
3. Recorta con precisión (energía), elimina silencios muertos y fija pausas con ritmo de Reel,
   incluidas las pausas dramáticas de ~0,35 s antes de «Pero espera», «CERO euros» y «Pero hay trampa».
4. Limpia y realza la voz (ruido, graves, presencia, sibilantes, compresión).
La velocidad de la voz no se modifica nunca: sólo se cortan silencios y tomas repetidas.
"""
from __future__ import annotations

import difflib
import json
import os
import subprocess
import tempfile

import numpy as np

from timing import SCRIPT, spoken_words, tokens

SR = 48000

# pausa (s) que se deja ANTES de la frase que empieza por la clave indicada
PAUSE_BEFORE = {"espera": 0.36, "cero": 0.38, "trampa": 0.36, "sabes": 0.24, "espana": 0.24,
                "elegir": 0.22, "piso": 0.08, "leo": 0.20, "candelago": 0.14, "lugo": 0.14, "loque": 0.10,
                "madrid2": 0.10, "galicia": 0.10, "vistas": 0.10, "p150": 0.08, "ourense": 0.10,
                "mientras": 0.08, "m60": 0.08, "ponerla": 0.10, "concesion": 0.05}
DEFAULT_PAUSE = 0.10
MAX_INTERNAL_PAUSE = 0.17


# --------------------------------------------------------------------------------------
def load_audio(path):
    """Decodifica cualquier formato a mono 48 kHz float32 con ffmpeg."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def transcribe_words(audio, model_path):
    from faster_whisper import WhisperModel
    from scipy.signal import resample_poly
    a16 = resample_poly(audio, 1, 3).astype(np.float32)
    m = WhisperModel(model_path, device="cpu", compute_type="int8")
    prompt = " ".join(" ".join(p.split("|")[0] for p in line.split()) for _, line in SCRIPT)
    segs, _ = m.transcribe(a16, language="es", word_timestamps=True, beam_size=5, vad_filter=False,
                           condition_on_previous_text=False, initial_prompt=prompt)
    return [{"word": w.word, "start": float(w.start), "end": float(w.end), "p": float(w.probability)}
            for s in segs for w in s.words]


def phrases():
    """Divide los tokens del guion en frases (por . ? : …)."""
    toks = tokens()
    out, cur = [], []
    for tk in toks:
        cur.append(tk)
        if tk["text"].endswith((".", "?", ":", "…", "!")):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def _norm_asr(words):
    """Palabras ASR -> lista plana normalizada con índice a la palabra original (une cifras partidas)."""
    import re
    merged = []
    for i, aw in enumerate(words):
        w = aw["word"].strip()
        if merged and re.fullmatch(r"[.,]\d{3}[.,]?", w):
            merged[-1]["word"] = merged[-1]["word"].strip().rstrip(".,") + w.rstrip(".,")
            merged[-1]["end"] = aw["end"]
            merged[-1]["idx"].append(i)
        else:
            merged.append({"word": aw["word"], "start": aw["start"], "end": aw["end"], "idx": [i]})
    flat, owner = [], []
    for k, m in enumerate(merged):
        for sw in spoken_words(m["word"]):
            flat.append(sw)
            owner.append(k)
    return merged, flat, owner


def find_occurrences(ph_words, flat, start_at, thr=0.72):
    """Busca la frase en la transcripción comparando letras (tolera «vista salmar» = «vistas al mar»)."""
    target = "".join(ph_words)
    L = len(ph_words)
    cands = []
    for j in range(start_at, len(flat)):
        if difflib.SequenceMatcher(a=flat[j][:4], b=ph_words[0][:4]).ratio() < 0.5:
            continue
        best = None
        for k in range(j, min(len(flat), j + L + 3)):
            r = difflib.SequenceMatcher(a=target, b="".join(flat[j:k + 1]), autojunk=False).ratio()
            if best is None or r > best[2]:
                best = (j, k, r)
        if best and best[2] >= thr:
            cands.append(best)
    occ = []
    for c in cands:
        if occ and c[0] <= occ[-1][1]:
            if c[2] > occ[-1][2]:
                occ[-1] = c
        else:
            occ.append(c)
    return occ


def choose_takes(words):
    merged, flat, owner = _norm_asr(words)
    phs = phrases()
    chosen = []
    cursor = 0
    for pi, ph in enumerate(phs):
        pw = [w for tk in ph for w in tk["spoken"]]
        occ = find_occurrences(pw, flat, cursor)
        if not occ:
            raise RuntimeError("No encuentro en la grabación la frase: " + " ".join(t["text"] for t in ph))
        pick = occ[0]
        if pi + 1 < len(phs):
            nw = [w for tk in phs[pi + 1] for w in tk["spoken"]]
            nxt = find_occurrences(nw, flat, occ[0][1] + 1)
            limit = nxt[0][0] if nxt else len(flat)
            valid = [o for o in occ if o[1] < limit]
            pick = valid[-1] if valid else occ[0]
        else:
            pick = occ[-1]
        chosen.append({"phrase": ph, "flat": (pick[0], pick[1]), "takes": len(occ),
                       "start": merged[owner[pick[0]]]["start"], "end": merged[owner[pick[1]]]["end"],
                       "merged": merged[owner[pick[0]]: owner[pick[1]] + 1]})
        cursor = pick[1] + 1
    return chosen


# --------------------------------------------------------------------------------------
def rms_db(x, win=0.01):
    n = int(win * SR)
    m = len(x) // n
    r = np.sqrt((x[: m * n].reshape(m, n) ** 2).mean(1) + 1e-12)
    return 20 * np.log10(r)


def refine(audio, t0, t1, floor_db):
    """Ajusta inicio/fin de un tramo a la energía real de la voz."""
    db = rms_db(audio)
    thr = floor_db
    hop = 0.01
    i0, i1 = int(t0 / hop), int(t1 / hop)
    i0 = max(0, min(i0, len(db) - 1))
    i1 = max(0, min(i1, len(db) - 1))
    # inicio: si cae en silencio, avanza hasta el ataque; si cae en voz, retrocede hasta el silencio
    if db[i0] < thr:
        k = i0
        while k < i1 and db[k] < thr:
            k += 1
        i0 = max(0, k - 3)
    else:
        k = i0
        while k > 0 and db[k] >= thr and (i0 - k) < 25:
            k -= 1
        i0 = max(0, k - 2)
    if db[i1] < thr:
        k = i1
        while k > i0 and db[k] < thr:
            k -= 1
        i1 = k + 6
    else:
        k = i1
        while k < len(db) - 1 and db[k] >= thr and (k - i1) < 30:
            k += 1
        i1 = k + 5
    return i0 * hop, i1 * hop


def internal_cuts(audio, t0, t1, floor_db, max_pause):
    """Dentro de una frase, acorta silencios largos. Devuelve sub-tramos a conservar."""
    db = rms_db(audio)
    thr = floor_db - 3
    hop = 0.01
    i0, i1 = int(t0 / hop), int(t1 / hop)
    keep, run_start = [], None
    segs_start = i0
    for k in range(i0, i1):
        quiet = db[k] < thr
        if quiet and run_start is None:
            run_start = k
        if (not quiet or k == i1 - 1) and run_start is not None:
            run_len = (k - run_start) * hop
            if run_len > max_pause:
                cut_a = run_start + int(max_pause / 2 / hop)
                cut_b = k - int(max_pause / 2 / hop)
                keep.append((segs_start * hop, cut_a * hop))
                segs_start = cut_b
            run_start = None
    keep.append((segs_start * hop, t1))
    return keep


def split_before_key(audio, seg, merged_words, key_word_idx, floor_db):
    """Parte un tramo justo antes de una palabra (para meter una pausa dramática dentro de una frase)."""
    t = merged_words[key_word_idx]["start"]
    db = rms_db(audio)
    hop = 0.01
    lo, hi = int((t - 0.12) / hop), int((t + 0.06) / hop)
    k = lo + int(np.argmin(db[lo:hi]))
    return k * hop


def edit(audio, words):
    """Devuelve (audio_editado, mapa de tiempos [(src0, src1, dst0)], informe)."""
    db = rms_db(audio)
    # umbral voz/silencio relativo al nivel de la voz (la grabadora puede dejar silencio digital)
    floor_db = max(float(np.percentile(db, 8)) + 9, float(np.percentile(db, 95)) - 30)
    chosen = choose_takes(words)
    pieces, report = [], []
    t_out = 0.0
    out = []
    tmap = []
    phrase_bounds = []
    # límites: frases pegadas en la grabación (sin silencio) se separan en el mínimo de energía
    bounds = []
    for ci, ch in enumerate(chosen):
        s0, s1 = refine(audio, ch["start"], ch["end"], floor_db)
        bounds.append([s0, s1])
    for ci in range(len(chosen) - 1):
        a, b = chosen[ci], chosen[ci + 1]
        if b["start"] - a["end"] < 0.15 and b["start"] >= a["end"] - 0.05:
            hop = 0.01
            lo = int((min(a["end"], b["start"]) - 0.12) / hop)
            hi = int((max(a["end"], b["start"]) + 0.35) / hop)
            k = lo + int(np.argmin(db[lo:hi]))
            bounds[ci][1] = k * hop
            bounds[ci + 1][0] = k * hop
        elif bounds[ci][1] > bounds[ci + 1][0]:
            mid = (a["end"] + b["start"]) / 2
            bounds[ci][1] = bounds[ci + 1][0] = mid
    for ci, ch in enumerate(chosen):
        ph = ch["phrase"]
        key = ph[0]["key"]
        s0, s1 = bounds[ci]
        subs = internal_cuts(audio, s0, s1, floor_db, MAX_INTERNAL_PAUSE)
        pause = 0.0 if ci == 0 else PAUSE_BEFORE.get(key, DEFAULT_PAUSE)
        report.append(f"{s0:6.2f}-{s1:6.2f} ({ch['takes']} toma/s) pausa {pause:.2f} | " + " ".join(t["text"] for t in ph))
        if pause:
            out.append(np.zeros(int(pause * SR), np.float32))
            t_out += pause
        ph_start = t_out
        for si_, (a, b) in enumerate(subs):
            last_piece = ci == len(chosen) - 1 and si_ == len(subs) - 1
            if last_piece:
                b += 0.12
            seg = audio[int(a * SR): int(b * SR)].copy()
            fi, fo = int(0.008 * SR), int((0.12 if last_piece else 0.035) * SR)
            if len(seg) > fi + fo:
                seg[:fi] *= np.linspace(0, 1, fi)
                seg[-fo:] *= np.linspace(1, 0, fo) ** 1.5
            tmap.append((a, b, t_out))
            out.append(seg)
            t_out += len(seg) / SR
        phrase_bounds.append((ph_start + 0.05, t_out + 0.05))
    lead = np.zeros(int(0.05 * SR), np.float32)
    tmap = [(a, b, d + 0.05) for a, b, d in tmap]
    edit.phrase_bounds = phrase_bounds
    return np.concatenate([lead] + out), tmap, report, chosen


def map_time(t, tmap):
    for a, b, d in tmap:
        if a - 1e-3 <= t <= b + 1e-3:
            return d + (min(max(t, a), b) - a)
    # fuera de tramo: al tramo más cercano
    best = min(tmap, key=lambda x: min(abs(t - x[0]), abs(t - x[1])))
    a, b, d = best
    return d if abs(t - a) < abs(t - b) else d + (b - a)


def snap_onsets(audio, words):
    db = rms_db(audio)
    thr = max(float(np.percentile(db, 8)) + 9, float(np.percentile(db, 95)) - 30)
    hop = 0.01
    out = []
    for w in words:
        w = dict(w)
        i = int(w["start"] / hop)
        lim = int(min(w["end"] + 0.1, w["start"] + 0.9) / hop)
        if i < len(db) and db[i] < thr:
            k = i
            while k < lim and k < len(db) and db[k] < thr:
                k += 1
            if k < lim:
                w["start"] = max(w["start"], k * hop - 0.02)
        out.append(w)
    return out


def enhance(in_wav, out_wav):
    """Cadena de voz: limpieza de ruido, graves, presencia, sibilantes, compresión."""
    chain = ",".join([
        "highpass=f=85:poles=2",
        "afftdn=nr=10:nf=-42:tn=1",
        "equalizer=f=200:t=q:w=1.0:g=-2.0",
        "equalizer=f=420:t=q:w=1.2:g=-2.0",
        "equalizer=f=3200:t=q:w=1.0:g=3.0",
        "equalizer=f=9000:t=h:w=0.7:g=2.0",
        "deesser=i=0.35:m=0.5:f=0.5:s=o",
        "acompressor=threshold=-22dB:ratio=3.2:attack=6:release=90:makeup=4dB:knee=4",
        "alimiter=limit=0.89:attack=3:release=40:level=disabled",
    ])
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", in_wav, "-af", chain, "-ar", str(SR), "-ac", "1", out_wav], check=True)


def process(raw_path, out_dir, model_path, log=print):
    import soundfile as sf
    audio = load_audio(raw_path)
    log(f"voz bruta: {len(audio) / SR:.1f} s")
    words = transcribe_words(audio, model_path)
    with open(os.path.join(out_dir, "voz_transcripcion_bruta.json"), "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=0)
    edited, tmap, report, chosen = edit(audio, words)
    for r in report:
        log("  " + r)
    tmp = os.path.join(out_dir, "voz_editada_seca.wav")
    sf.write(tmp, edited, SR, subtype="PCM_24")
    final = os.path.join(out_dir, "voz_editada.wav")
    enhance(tmp, final)
    # tiempos finales: se transcribe la voz YA editada y cada inicio se ajusta al ataque real
    kept = transcribe_words(edited, model_path)
    kept = snap_onsets(edited, kept)
    bounds = edit.phrase_bounds
    with open(os.path.join(out_dir, "voz_frases.json"), "w", encoding="utf-8") as f:
        json.dump(bounds, f)
    with open(os.path.join(out_dir, "voz_palabras_editada.json"), "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=0)
    log(f"voz editada: {len(edited) / SR:.1f} s")
    return final, kept, bounds


def apply_phrase_bounds(toks, bounds):
    """Encaja los tokens de cada frase dentro de su tramo real en la voz editada (la edición
    sabe con exactitud dónde empieza y acaba cada frase; Whisper puede desviarse)."""
    phs = phrases()
    by_i = {t["i"]: t for t in toks}
    for ph, (b0, b1) in zip(phs, bounds):
        ts = [by_i[t["i"]] for t in ph]
        # reescala linealmente los tiempos de la frase si se salen del tramo
        lo, hi = ts[0]["start"], max(t["end"] for t in ts)
        if lo < b0 - 0.02 or hi > b1 + 0.05 or lo > b0 + 0.25:
            span = max(hi - lo, 1e-3)
            for t in ts:
                t["start"] = round(b0 + (t["start"] - lo) / span * (b1 - b0), 3)
                t["end"] = round(b0 + (t["end"] - lo) / span * (b1 - b0), 3)
        ts[0]["start"] = round(max(ts[0]["start"], b0), 3)
    for a, b in zip(toks, toks[1:]):
        if b["start"] < a["start"]:
            b["start"] = a["start"] + 0.02
        if b["end"] < b["start"] + 0.06:
            b["end"] = b["start"] + 0.06
    return toks
