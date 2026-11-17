#!/usr/bin/env python3
"""Calcula la línea de tiempo del reel.

- Si existe input/voz.wav: transcribe con faster-whisper (tiempos por palabra) y
  alinea con el guion exacto. Si faster-whisper o su modelo no están disponibles,
  usa un alineador por silencios (no necesita modelos).
- Si no hay voz: genera tiempos sintéticos con el ritmo del guion.

La voz se corta en "clips" (intro, p1..p5, q1, q2, r1..r5) y cada clip se coloca
en su bloque. Los 5 bloques de propuestas y los 5 de revelación tienen la MISMA
duración y el clip de voz cae en el MISMO desplazamiento dentro de su bloque
(neutralidad). La voz nunca cambia de velocidad: solo se insertan silencios.

Salida: output/timings.json (+ output/subtitulos.srt)
"""
import json, math, os, re, sys, unicodedata, difflib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30

CLIPS = [
    ("intro", "Elecciones del 29 de noviembre. Cinco propuestas de vivienda. No te digo de qué partido son. Elige una."),
    ("p1", "Uno: IVA cero en la compra de tu primera vivienda."),
    ("p2", "Dos: préstamos sin intereses de hasta cincuenta mil euros para pagar la entrada."),
    ("p3", "Tres: un millón de viviendas, y si el ayuntamiento no responde a una licencia en noventa días, queda aprobada."),
    ("p4", "Cuatro: que ningún hogar pague más del treinta por ciento de sus ingresos en alquiler."),
    ("p5", "Cinco: prohibir que fondos y empresas compren viviendas."),
    ("q1", "¿Ya tienes la tuya? Comenta el número…"),
    ("q2", "y ahora mira de quién es."),
    ("r1", "Uno, Vox."),
    ("r2", "Dos, PSOE."),
    ("r3", "Tres, PP."),
    ("r4", "Cuatro, Podemos."),
    ("r5", "Cinco, Sumar."),
]

# ---------------------------------------------------------------- utilidades
SPOKEN = {"29": "veintinueve", "iva": "iva", "psoe": "pesoe", "pp": "pepé", "vox": "vox"}


def norm(w):
    w = w.lower()
    w = unicodedata.normalize("NFD", w)
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9ñ]", "", w)


def syllables(word):
    w = norm(word)
    w = SPOKEN.get(w, w)
    if w.isdigit():
        return 3 * len(w)
    raw = unicodedata.normalize("NFC", word.lower())
    strong, weak_acc = set("aeoáéó"), set("íú")
    vowels = set("aeiouáéíóúü")
    n, prev_v, grp = 0, False, ""
    for ch in raw + " ":
        if ch in vowels:
            grp += ch
            prev_v = True
        else:
            if grp:
                k = sum(1 for c in grp if c in strong or c in weak_acc)
                n += max(1, k)
                grp = ""
            prev_v = False
    if n == 0:
        n = 1
    if w == "y":
        n = 1
    return n


def tokens(text):
    return text.split()


# ------------------------------------------------- tiempos sintéticos (sin voz)
SYL_RATE = 7.0  # sílabas por segundo, narración de reel enérgica pero clara


def synth_clip(text):
    t, out = 0.0, []
    for tok in tokens(text):
        d = syllables(tok) / SYL_RATE + 0.015
        out.append({"text": tok, "start": round(t, 3), "end": round(t + d, 3)})
        t += d
        if tok.endswith((",",)):
            t += 0.12
        elif tok.endswith((":",)):
            t += 0.16
        elif tok.endswith((".", "?")):
            t += 0.24
        elif tok.endswith("…"):
            t += 0.10
    return out, out[-1]["end"]


# ---------------------------------------------------- alineación con voz real
def load_wav_mono(path):
    import soundfile as sf
    import numpy as np
    x, sr = sf.read(path, always_2d=True)
    return x.mean(axis=1).astype("float32"), sr


def whisper_words(path):
    from faster_whisper import WhisperModel
    model_name = os.environ.get("WHISPER_MODEL", "small")
    m = WhisperModel(model_name, device="cpu", compute_type="int8")
    prompt = " ".join(t for _, t in CLIPS)
    segs, _ = m.transcribe(path, language="es", word_timestamps=True, initial_prompt=prompt, vad_filter=False)
    words = []
    for s in segs:
        for w in s.words:
            words.append({"text": w.word.strip(), "start": w.start, "end": w.end})
    return words


def align_script(words):
    """Asigna a cada palabra del guion un tiempo usando las palabras de whisper."""
    script = [(cid, tok) for cid, text in CLIPS for tok in tokens(text)]
    a = [SPOKEN.get(norm(t), norm(t)) for _, t in script]
    b = [SPOKEN.get(norm(w["text"]), norm(w["text"])) for w in words]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    times = [None] * len(script)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            w = words[blk.b + k]
            times[blk.a + k] = (w["start"], w["end"])
    # aproximaciones difusas para huecos
    for i in range(len(script)):
        if times[i] is None:
            best, bj = 0.0, None
            for j, wb in enumerate(b):
                r = difflib.SequenceMatcher(a=a[i], b=wb).ratio()
                if r > best:
                    best, bj = r, j
            prev = next((times[k][1] for k in range(i - 1, -1, -1) if times[k]), 0.0)
            if bj is not None and best > 0.6 and words[bj]["start"] >= prev - 0.05:
                times[i] = (words[bj]["start"], words[bj]["end"])
    # interpolación lineal por sílabas para lo que quede
    i = 0
    n = len(script)
    while i < n:
        if times[i] is None:
            j = i
            while j < n and times[j] is None:
                j += 1
            t0 = times[i - 1][1] if i > 0 else (words[0]["start"] if words else 0.0)
            t1 = times[j][0] if j < n else (words[-1]["end"] if words else t0 + 1)
            syl = [syllables(script[k][1]) for k in range(i, j)]
            tot = sum(syl) or 1
            acc = t0
            for k, s in zip(range(i, j), syl):
                d = (t1 - t0) * s / tot
                times[k] = (acc, acc + d)
                acc += d
            i = j
        else:
            i += 1
    return script, times


def silence_align(x, sr):
    """Alineador sin modelos: busca los 12 silencios que separan los 13 clips."""
    import numpy as np
    hop = int(sr * 0.01)
    n = len(x) // hop
    rms = np.sqrt(np.array([np.mean(x[i * hop:(i + 1) * hop] ** 2) for i in range(n)]) + 1e-12)
    db = 20 * np.log10(rms)
    thr = max(np.percentile(db, 95) - 30, np.percentile(db, 10) + 6)
    voiced = db > thr
    idx = np.where(voiced)[0]
    s0, s1 = idx[0] * 0.01, (idx[-1] + 1) * 0.01
    gaps, i = [], 0
    while i < n:
        if not voiced[i]:
            j = i
            while j < n and not voiced[j]:
                j += 1
            a, b = i * 0.01, j * 0.01
            if a > s0 and b < s1 and b - a >= 0.08:
                gaps.append((a, b))
            i = j
        else:
            i += 1
    syl = [sum(syllables(t) for t in tokens(txt)) for _, txt in CLIPS]
    cum, c = [], 0
    for s in syl[:-1]:
        c += s
        cum.append(c / sum(syl))
    exp = [s0 + (s1 - s0) * f for f in cum]
    G, B = len(gaps), len(exp)
    if G < B:
        raise RuntimeError("No encuentro suficientes pausas entre frases")
    NEG = -1e9
    score = [[NEG] * G for _ in range(B)]
    back = [[-1] * G for _ in range(B)]
    span = s1 - s0
    for bi in range(B):
        for g in range(G):
            a, b = gaps[g]
            sc = 2.5 * math.log(1 + (b - a) * 10) - 4 * abs((a + b) / 2 - exp[bi]) / span
            if bi == 0:
                score[bi][g] = sc
            else:
                best, bk = NEG, -1
                for h in range(g):
                    if score[bi - 1][h] > best:
                        best, bk = score[bi - 1][h], h
                if bk >= 0:
                    score[bi][g] = best + sc
                    back[bi][g] = bk
    g = max(range(G), key=lambda k: score[B - 1][k])
    chosen = []
    for bi in range(B - 1, -1, -1):
        chosen.append(gaps[g])
        g = back[bi][g]
    chosen.reverse()
    bounds = [s0] + [x for gp in chosen for x in gp] + [s1]
    script, times = [], []
    for k, (cid, text) in enumerate(CLIPS):
        a, b = bounds[2 * k], bounds[2 * k + 1]
        toks = tokens(text)
        sy = [syllables(t) for t in toks]
        tot = sum(sy)
        acc = a
        for t, s in zip(toks, sy):
            d = (b - a) * s / tot
            script.append((cid, t))
            times.append((acc, acc + d))
            acc += d
    return script, times


# ------------------------------------------------------------------- layout
def build(voice_path=None):
    clips = {}
    method = "sintetico"
    if voice_path and os.path.exists(voice_path):
        x, sr = load_wav_mono(voice_path)
        script = times = None
        try:
            words = whisper_words(voice_path)
            script, times = align_script(words)
            method = "faster-whisper"
        except Exception as e:  # noqa
            print("[timings] faster-whisper no disponible (%s). Uso alineador por silencios." % e)
            script, times = silence_align(x, sr)
            method = "silencios"
        dur_total = len(x) / sr
        for cid, _ in CLIPS:
            ws = [(t, tm) for (c, t), tm in zip(script, times) if c == cid]
            a = ws[0][1][0]
            b = ws[-1][1][1]
            clips[cid] = {"src_start": a, "src_end": b, "words": [
                {"text": t, "start": tm[0] - a, "end": tm[1] - a} for t, tm in ws]}
        # márgenes de corte: hasta medio camino con el clip vecino (máx 0.12 s)
        ids = [c for c, _ in CLIPS]
        for k, cid in enumerate(ids):
            c = clips[cid]
            prev_end = clips[ids[k - 1]]["src_end"] if k > 0 else 0.0
            next_start = clips[ids[k + 1]]["src_start"] if k + 1 < len(ids) else dur_total
            pre = min(0.12, max(0.0, (c["src_start"] - prev_end) / 2))
            post = min(0.15, max(0.0, (next_start - c["src_end"]) / 2))
            c["pad_pre"], c["pad_post"] = pre, post
    else:
        for cid, text in CLIPS:
            ws, d = synth_clip(text)
            clips[cid] = {"src_start": None, "src_end": None, "words": ws, "pad_pre": 0.0, "pad_post": 0.0}
    for c in clips.values():
        c["dur"] = c["words"][-1]["end"]

    def wstart(cid, i):
        return clips[cid]["words"][i]["start"]

    T = {}
    place = {}
    # Escena 1 — apertura
    seal_hit = 0.62
    v0 = 0.70
    place["intro"] = v0
    i_cinco = 5  # "Cinco"
    i_no = 9     # "No"
    s2 = max(2.6, v0 + wstart("intro", i_cinco) - 0.12)
    T["s1"] = [0.0, s2]
    T["seal_hit"] = seal_hit
    T["cut_to_urn"] = 1.30
    s3 = max(s2 + 3.7, v0 + clips["intro"]["dur"] + 0.40)
    T["s2"] = [s2, s3]
    T["title_rules"] = v0 + wstart("intro", i_no)
    # Escena 3 — propuestas: cada bloque dura lo que su frase + el MISMO margen
    # antes y después (mismo tratamiento; la duración se adapta al texto)
    lead = 0.30
    tail = 0.60
    T["blocks_p"] = []
    b0 = s3
    for k in range(1, 6):
        Pk = max(3.6, clips["p%d" % k]["dur"] + lead + tail)
        Pk = math.ceil(Pk * FPS) / FPS
        T["blocks_p"].append([b0, b0 + Pk])
        place["p%d" % k] = b0 + lead
        b0 += Pk
    T["P"] = max(b[1] - b[0] for b in T["blocks_p"])
    s4 = b0
    # Escena 4 — la elección
    place["q1"] = s4 + 0.55
    quiet = 2.2
    s5 = max(s4 + 4.2, place["q1"] + clips["q1"]["dur"] + quiet)
    T["s3"] = [s3, s4]
    T["s4"] = [s4, s5]
    T["quiet"] = [place["q1"] + clips["q1"]["dur"], s5]
    # Escena 5 — revelación
    place["q2"] = s5 + 0.15
    r0 = max(s5 + 1.9, place["q2"] + clips["q2"]["dur"] + 0.15)
    party_off = [wstart("r%d" % k, 1) for k in range(1, 6)]
    L = max(0.80, max(party_off) + 0.10)        # aterrizaje del sobre (golpe)
    after = max(clips["r%d" % k]["dur"] - party_off[k - 1] for k in range(1, 6))
    R = max(1.95, L + after + 0.30)
    R = math.ceil(R * FPS) / FPS
    T["R"] = R
    T["flip_land"] = L
    T["flip_dur"] = 0.55
    T["blocks_r"] = []
    for k in range(1, 6):
        b0 = r0 + (k - 1) * R
        T["blocks_r"].append([b0, b0 + R])
        place["r%d" % k] = b0 + L - party_off[k - 1]
    s6 = r0 + 5 * R + 0.6
    T["s5"] = [s5, s6]
    end = s6 + 3.2
    end = math.ceil(end * FPS) / FPS
    T["s6"] = [s6, end]
    T["duration"] = end
    T["frames"] = int(round(end * FPS))

    # palabras absolutas
    words = []
    for cid, text in CLIPS:
        for w in clips[cid]["words"]:
            words.append({"clip": cid, "text": w["text"], "start": round(place[cid] + w["start"], 3),
                          "end": round(place[cid] + w["end"], 3)})
    voice = []
    for cid, _ in CLIPS:
        c = clips[cid]
        voice.append({"clip": cid, "dst": round(place[cid], 4), "dur": round(c["dur"], 4),
                      "src_start": c["src_start"], "src_end": c["src_end"],
                      "pad_pre": c["pad_pre"], "pad_post": c["pad_post"]})
    subs = chunk_subs(words)
    out = {"fps": FPS, "width": 1080, "height": 1920, "method": method, "voice_file": voice_path if method != "sintetico" else None,
           "timeline": T, "voice_clips": voice, "words": words, "subtitles": subs,
           "proposals": [t.split(":", 1)[1].strip() for c, t in CLIPS if c.startswith("p")],
           "parties": [t.split(",", 1)[1].strip().rstrip(".") for c, t in CLIPS if c.startswith("r")]}
    return out


def chunk_subs(words, max_chars=20):
    """Agrupa palabras en bloques cortos (1–2 líneas) para subtítulos palabra a palabra."""
    chunks, cur = [], []

    def flush():
        if cur:
            chunks.append({"words": list(cur), "start": cur[0]["start"], "end": cur[-1]["end"]})
            cur.clear()

    for w in words:
        if cur and (cur[-1]["clip"] != w["clip"]):
            flush()
        cur.append(w)
        txt = " ".join(x["text"] for x in cur)
        if w["text"].endswith((".", "?", "…", ":")) or len(txt) > max_chars * 1.55:
            flush()
        elif w["text"].endswith(",") and len(txt) > 10:
            flush()
    flush()
    # cada bloque se mantiene hasta que empieza el siguiente (máx +0.5 s)
    for i, c in enumerate(chunks):
        nxt = chunks[i + 1]["start"] if i + 1 < len(chunks) else c["end"] + 0.6
        c["hold"] = round(min(nxt, c["end"] + 0.5), 3)
        # partir en líneas (índices de palabra)
        fixed, buf = [], []
        for k, w in enumerate(c["words"]):
            cand = " ".join(c["words"][j]["text"] for j in buf + [k])
            if buf and len(cand) > max_chars:
                fixed.append(buf)
                buf = []
            buf.append(k)
        if buf:
            fixed.append(buf)
        c["lines"] = fixed
    return chunks


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def write_srt(data, path):
    out = []
    for i, c in enumerate(data["subtitles"], 1):
        txt = "\n".join(" ".join(c["words"][j]["text"] for j in ln) for ln in c["lines"])
        out.append("%d\n%s --> %s\n%s\n" % (i, srt_time(c["start"]), srt_time(c["hold"]), txt))
    T = data["timeline"]
    end = T["duration"]
    out.append("%d\n%s --> %s\n%s\n" % (len(data["subtitles"]) + 1, srt_time(T["s6"][0] + 0.9), srt_time(end - 0.5),
                                       "¿Te ha sorprendido?"))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))


if __name__ == "__main__":
    voice = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "input", "voz.wav")
    data = build(voice if os.path.exists(voice) else None)
    od = os.environ.get("OUT_DIR", os.path.join(ROOT, "output"))
    os.makedirs(od, exist_ok=True)
    with open(os.path.join(od, "timings.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    write_srt(data, os.path.join(od, "subtitulos.srt"))
    T = data["timeline"]
    print("[timings] método=%s duración=%.2fs frames=%d P=%.2f R=%.2f" % (data["method"], T["duration"], T["frames"], T["P"], T["R"]))
    for k in ("s1", "s2", "s3", "s4", "s5", "s6"):
        print("  %s %.2f – %.2f" % (k, *T[k]))
