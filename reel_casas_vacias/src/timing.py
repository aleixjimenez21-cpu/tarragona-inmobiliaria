"""Genera timings.json: tiempos de cada palabra del guion y de cada plano.

- Si existe input/voz.wav: alinea con faster-whisper (word_timestamps) y casa
  las palabras reconocidas con las del guion (difflib), interpolando las que falten.
- Si no: reparte el guion con un ritmo de locución natural (≈3 palabras/s) y
  los silencios marcados en el storyboard.
"""
import json, os, re, sys, difflib, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VOZ = os.path.join(ROOT, 'input', 'voz.wav')
OUT = os.path.join(ROOT, 'output', 'timings.json')

SENTENCES = [
    "España tiene casi cuatro millones de viviendas vacías.",
    "Y aun así… faltan unas setecientas cincuenta mil.",
    "¿Cómo es posible?",
    "Mira este dato.",
    "En la provincia de Ourense, más del cuarenta por ciento de las viviendas están vacías.",
    "Mientras tanto, seis provincias concentran más de la mitad del déficit.",
    "Y aquí está el problema: casi la mitad de las viviendas vacías están en municipios de menos de diez mil habitantes.",
    "Tenemos millones de casas vacías… pero no necesariamente donde hacen falta.",
    "¿La solución es construir más o recuperar las que ya tenemos?",
]
# ventanas por defecto (s) sin voz: inicio, fin
DEFAULT_WIN = [(0.15, 2.40), (2.60, 4.95), (5.40, 6.30), (6.55, 7.35), (7.60, 11.90),
               (12.10, 16.80), (17.10, 23.00), (23.30, 27.50), (28.40, 31.60)]
TAIL = 2.4  # segundos tras la última palabra (CTA + bucle)


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    w = ''.join(c for c in w if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]', '', w)


def syl(w):
    return max(1, len(re.findall(r'[aeiouáéíóúü]+', w.lower())))


def split_words(s):
    return s.split()


def fallback():
    words = []
    for si, (s, (a, b)) in enumerate(zip(SENTENCES, DEFAULT_WIN)):
        ws = split_words(s)
        # peso = sílabas + pausa tras coma / puntos suspensivos
        wt = [syl(w) + (1.6 if w.endswith((',', ':')) else 0) + (3.0 if w.endswith('…') else 0) for w in ws]
        tot = sum(wt)
        t = a
        for w, k in zip(ws, wt):
            d = (b - a) * k / tot
            pause = (1.6 if w.endswith((',', ':')) else 0) + (3.0 if w.endswith('…') else 0)
            speak = d * (k - pause) / k
            words.append(dict(w=w, s=round(t, 3), e=round(t + speak, 3), sent=si))
            t += d
    return words


def from_voice():
    from faster_whisper import WhisperModel
    model = WhisperModel(os.environ.get('WHISPER_MODEL', 'small'), device='cpu', compute_type='int8')
    segs, _ = model.transcribe(VOZ, language='es', word_timestamps=True, vad_filter=False,
                               initial_prompt=' '.join(SENTENCES))
    rec = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
    script = [(w, si) for si, s in enumerate(SENTENCES) for w in split_words(s)]
    A = [norm(w) for w, _ in script]
    B = [norm(w) for w, _, _ in rec]
    sm = difflib.SequenceMatcher(a=A, b=B, autojunk=False)
    t = [None] * len(script)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            t[blk.a + k] = (rec[blk.b + k][1], rec[blk.b + k][2])
    # interpolar huecos
    known = [i for i, x in enumerate(t) if x]
    for i in range(len(t)):
        if t[i]:
            continue
        prv = max([k for k in known if k < i], default=None)
        nxt = min([k for k in known if k > i], default=None)
        s0 = t[prv][1] if prv is not None else 0.0
        s1 = t[nxt][0] if nxt is not None else s0 + 0.4
        n = (nxt if nxt is not None else i + 1) - (prv if prv is not None else -1)
        k = i - (prv if prv is not None else -1)
        a = s0 + (s1 - s0) * (k - 1) / n
        b = s0 + (s1 - s0) * k / n
        t[i] = (a, b)
    return [dict(w=w, s=round(x[0], 3), e=round(x[1], 3), sent=si) for (w, si), x in zip(script, t)]


def shots(words):
    S = [(min(w['s'] for w in words if w['sent'] == i), max(w['e'] for w in words if w['sent'] == i))
         for i in range(len(SENTENCES))]
    end = S[8][1] + TAIL
    cuts = [0.0,
            S[1][0] - 0.15,          # B contraste
            S[1][1] + 0.05,          # C pregunta (silencio 0,4 s antes de «¿Cómo…»)
            S[4][0] - 0.10,          # D Ourense
            S[5][0] - 0.10,          # E seis provincias
            S[6][0] - 0.10,          # F pueblos
            S[7][0] - 0.30,          # G síntesis
            S[8][0] - 0.40,          # H dilema + CTA
            end]
    # redondear a fotograma
    cuts = [round(c * 30) / 30 for c in cuts]
    names = ['A_hook', 'B_contraste', 'C_pregunta', 'D_ourense', 'E_provincias', 'F_pueblos', 'G_sintesis', 'H_dilema']
    return [dict(name=n, start=cuts[i], end=cuts[i + 1]) for i, n in enumerate(names)], S, end


def main():
    voice = os.path.exists(VOZ)
    words = from_voice() if voice else fallback()
    sh, S, end = shots(words)
    data = dict(source='voz.wav (faster-whisper)' if voice else 'guion (ritmo estimado, sin voz)',
                fps=30, duration=round(end, 3), sentences=[dict(text=t, s=round(a, 3), e=round(b, 3))
                                                         for t, (a, b) in zip(SENTENCES, S)],
                shots=sh, words=words)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, 'w'), ensure_ascii=False, indent=1)
    print('timings ->', OUT, 'duración', round(end, 2), 's', '(voz)' if voice else '(sin voz)')
    for s in sh:
        print('  %-13s %6.2f – %6.2f' % (s['name'], s['start'], s['end']))


if __name__ == '__main__':
    main()
