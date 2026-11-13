"""Guion, tiempos palabra a palabra y alineado con la voz real.

- Sin voz: tiempos sintéticos a partir de las sílabas habladas de cada palabra.
- Con voz: faster-whisper (o WhisperX si está instalado) con marcas por palabra,
  alineadas contra el guion exacto (el texto de pantalla SIEMPRE es el del guion).

Cada token puede llevar una clave (`texto|clave`) para anclar eventos visuales y
sonoros. Todo el montaje se calcula a partir de estas claves, así que una voz nueva
reajusta el vídeo entero sin tocar código.
"""
from __future__ import annotations

import difflib
import json
import os
import re
import unicodedata

# --------------------------------------------------------------------------------------
# Guion exacto (no se cambia). `|clave` = ancla para eventos. `/` separa frases (pausa).
# --------------------------------------------------------------------------------------
SCRIPT = [
    ("gancho", "En|madrid Madrid, esto cuesta 390.000|p390 euros."),
    ("gancho", "En|galicia Galicia, por menos|menos de la mitad… te compras un pueblo|pueblo entero.|entero"),
    ("impacto", "Candelago.|candelago Vistas|vistas al mar.|mar 150.000|p150 euros."),
    ("impacto", "En|madrid2 Madrid, con ese dinero compras apenas 23|m23 metros cuadrados.|m23end"),
    ("escalada", "Pero|espera espera.|espera2"),
    ("escalada", "En|lugo Lugo se vendió una aldea con dos|dos casas de piedra por 59.000|p59 euros."),
    ("escalada", "Lo|loque que cuestan nueve|nueve metros en Madrid.|m9end"),
    ("wow", "¿Y|sabes sabes qué es lo más increíble?|increible"),
    ("wow", "En|ourense Ourense hay una aldea con doce|doce casas|casas por…|por CERO|cero euros.|euros0"),
    ("wow", "Pero|trampa hay una trampa:|trampa2 es una concesión|concesion de 50 años.|anos Y|ponerla ponerla en marcha puede costar millones.|millones"),
    ("contraste", "En|espana España hay miles|miles de pueblos abandonados.|abandonados"),
    ("contraste", "Y|mientras mientras tanto, en Madrid,|madrid3 60|m60 metros cuadrados cuestan casi|casi 400.000|p400 euros.|p400end"),
    ("cta", "Te|elegir doy a elegir:"),
    ("cta", "¿Un|piso piso en Madrid|madrid4 o|o un pueblo entero en Galicia?|galicia2"),
    ("cta", "Te|leo leo en comentarios.|fin"),
]

# Pausas extra (s) ANTES de ciertas claves: 0,3 s de casi silencio pedidos en el encargo.
SILENCE_BEFORE = {"espera": 0.36, "cero": 0.34, "trampa": 0.34}

# --------------------------------------------------------------------------------------
# Números en español (para sílabas y para alinear con lo que transcribe Whisper)
# --------------------------------------------------------------------------------------
_U = "cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciséis diecisiete dieciocho diecinueve veinte".split()
_V = {21: "veintiuno", 22: "veintidós", 23: "veintitrés", 24: "veinticuatro", 25: "veinticinco",
      26: "veintiséis", 27: "veintisiete", 28: "veintiocho", 29: "veintinueve"}
_D = {30: "treinta", 40: "cuarenta", 50: "cincuenta", 60: "sesenta", 70: "setenta", 80: "ochenta", 90: "noventa"}
_C = {100: "ciento", 200: "doscientos", 300: "trescientos", 400: "cuatrocientos", 500: "quinientos",
      600: "seiscientos", 700: "setecientos", 800: "ochocientos", 900: "novecientos"}


def num_es(n: int) -> str:
    if n <= 20:
        return _U[n]
    if n < 30:
        return _V[n]
    if n < 100:
        d, u = divmod(n, 10)
        return _D[d * 10] + ("" if u == 0 else " y " + _U[u])
    if n < 1000:
        if n == 100:
            return "cien"
        c, r = divmod(n, 100)
        return _C[c * 100] + ("" if r == 0 else " " + num_es(r))
    if n < 1_000_000:
        m, r = divmod(n, 1000)
        head = "mil" if m == 1 else num_es(m) + " mil"
        return head + ("" if r == 0 else " " + num_es(r))
    m, r = divmod(n, 1_000_000)
    head = "un millón" if m == 1 else num_es(m) + " millones"
    return head + ("" if r == 0 else " " + num_es(r))


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def spoken_words(text: str) -> list[str]:
    """Texto -> lista de palabras habladas normalizadas (números expandidos)."""
    out = []
    for raw in re.split(r"\s+", text.strip()):
        w = raw.lower().strip("¿?¡!.,:;…\"'()«»-—")
        if not w:
            continue
        digits = w.replace(".", "").replace(",", "").replace(" ", "")
        if digits.isdigit():
            out += [strip_accents(x) for x in num_es(int(digits)).split()]
        else:
            out.append(strip_accents(w))
    return out


def syllables(word: str) -> int:
    """Sílabas aproximadas de una palabra española normalizada."""
    w = word.lower()
    w = re.sub(r"y$", "i", w)
    if w == "y":
        return 1
    strong = set("aeoáéíóú")
    vowels = set("aeiouáéíóúü")
    n, prev_v, prev_strong = 0, False, False
    for ch in w:
        if ch in vowels:
            s = ch in strong
            if not prev_v:
                n += 1
            elif s and prev_strong:
                n += 1  # hiato
            prev_v, prev_strong = True, s
        else:
            prev_v = prev_strong = False
    return max(1, n)


# --------------------------------------------------------------------------------------
# Tokens
# --------------------------------------------------------------------------------------
def tokens() -> list[dict]:
    toks = []
    for si, (section, line) in enumerate(SCRIPT):
        parts = line.split()
        for pi, p in enumerate(parts):
            text, _, key = p.partition("|")
            toks.append({
                "i": len(toks), "text": text, "key": key or None, "section": section,
                "line": si, "spoken": spoken_words(text),
                "last_in_line": pi == len(parts) - 1,
            })
    return toks


def _pause_after(text: str, last_in_line: bool) -> float:
    if text.endswith("…"):
        return 0.42
    if text.endswith("?"):
        return 0.38
    if text.endswith("."):
        return 0.30
    if text.endswith(":"):
        return 0.24
    if text.endswith(","):
        return 0.13
    return 0.0 if not last_in_line else 0.25


def synthetic_timings(speech_end: float = 38.9, start: float = 0.05) -> list[dict]:
    """Tiempos de lectura natural (sin voz), escalados para que la locución acabe en
    `speech_end` (ritmo de Reel, ~4 palabras/s). Los silencios de 0,3 s se respetan."""
    toks = tokens()
    flex, fixed = [], 0.0  # (duración, pausa) escalables; silencios fijos
    for tk in toks:
        syl = sum(syllables(w) for w in tk["spoken"])
        k = 1.15 if (any(ch.isdigit() for ch in tk["text"]) or tk["text"].strip("….,") == "CERO") else 1.0
        flex.append((0.05 + syl / 6.6 * k, _pause_after(tk["text"], tk["last_in_line"])))
        fixed += SILENCE_BEFORE.get(tk["key"], 0.0)
    total_flex = sum(d + p for d, p in flex) - flex[-1][1]
    scale = (speech_end - start - fixed) / total_flex
    t = start
    for tk, (d, p) in zip(toks, flex):
        t += SILENCE_BEFORE.get(tk["key"], 0.0)
        tk["start"], tk["end"] = round(t, 3), round(t + d * scale, 3)
        t += (d + p) * scale
    return toks


# --------------------------------------------------------------------------------------
# Alineado con transcripción (lista de {"word","start","end"})
# --------------------------------------------------------------------------------------
def align(toks: list[dict], asr_words: list[dict]) -> list[dict]:
    script_sp, owner = [], []
    for tk in toks:
        for w in tk["spoken"]:
            script_sp.append(w)
            owner.append(tk["i"])
    # Whisper a veces parte las cifras ("390" + "000"): se vuelven a unir
    merged = []
    for aw in asr_words:
        w = aw["word"].strip()
        if merged and re.fullmatch(r"[.,]?\d{3}[.,]?", w) and re.fullmatch(r"\d{1,3}([.,]\d{3})*", merged[-1]["word"].strip().rstrip(".,")):
            merged[-1] = {"word": merged[-1]["word"].strip().rstrip(".,") + "." + w.strip(".,"), "start": merged[-1]["start"], "end": aw["end"]}
        else:
            merged.append(dict(aw))
    asr_sp, asr_t = [], []
    for aw in merged:
        for w in spoken_words(aw["word"]):
            asr_sp.append(w)
            asr_t.append((aw["start"], aw["end"]))
    sm = difflib.SequenceMatcher(a=script_sp, b=asr_sp, autojunk=False)
    times = [None] * len(script_sp)
    for a0, b0, n in sm.get_matching_blocks():
        for k in range(n):
            times[a0 + k] = asr_t[b0 + k]
    # interpolar huecos
    known = [i for i, x in enumerate(times) if x is not None]
    if not known:
        raise RuntimeError("La transcripción no coincide con el guion.")
    for i in range(len(times)):
        if times[i] is None:
            prev = max([k for k in known if k < i], default=None)
            nxt = min([k for k in known if k > i], default=None)
            if prev is None:
                times[i] = (max(0.0, times[nxt][0] - 0.3 * (nxt - i)),) * 2
            elif nxt is None:
                times[i] = (times[prev][1] + 0.3 * (i - prev),) * 2
            else:
                a, b = times[prev][1], times[nxt][0]
                f0 = (i - prev) / (nxt - prev)
                f1 = (i - prev + 1) / (nxt - prev)
                times[i] = (a + (b - a) * f0, a + (b - a) * f1 if b > a else a)
    for tk in toks:
        idx = [j for j, o in enumerate(owner) if o == tk["i"]]
        tk["start"] = round(min(times[j][0] for j in idx), 3)
        tk["end"] = round(max(times[j][1] for j in idx), 3)
    # monotonía
    for a, b in zip(toks, toks[1:]):
        if b["start"] < a["start"]:
            b["start"] = a["start"]
        if b["end"] < b["start"] + 0.06:
            b["end"] = b["start"] + 0.06
    return toks


def transcribe(wav_path: str) -> list[dict]:
    """Marcas por palabra con faster-whisper (preferido) o WhisperX."""
    try:
        from faster_whisper import WhisperModel  # type: ignore
        model = WhisperModel(os.environ.get("WHISPER_MODEL", "small"), device="auto", compute_type="auto")
        segs, _ = model.transcribe(wav_path, language="es", word_timestamps=True,
                                   initial_prompt=" ".join(" ".join(p.split("|")[0] for p in l.split()) for _, l in SCRIPT),
                                   vad_filter=False)
        return [{"word": w.word, "start": w.start, "end": w.end} for s in segs for w in s.words]
    except ImportError:
        import whisperx  # type: ignore
        model = whisperx.load_model("large-v3", "cpu", compute_type="int8", language="es")
        audio = whisperx.load_audio(wav_path)
        res = model.transcribe(audio, language="es")
        am, meta = whisperx.load_align_model(language_code="es", device="cpu")
        res = whisperx.align(res["segments"], am, meta, audio, "cpu")
        return [{"word": w["word"], "start": w["start"], "end": w["end"]}
                for s in res["segments"] for w in s.get("words", []) if "start" in w]


class Timeline:
    """Acceso cómodo a tiempos por clave."""

    def __init__(self, toks: list[dict], duration: float, source: str):
        self.toks = toks
        self.duration = duration
        self.source = source
        self.by_key = {t["key"]: t for t in toks if t["key"]}

    def s(self, key: str) -> float:
        return self.by_key[key]["start"]

    def e(self, key: str) -> float:
        return self.by_key[key]["end"]

    def to_json(self) -> dict:
        return {
            "fuente_tiempos": self.source,
            "duracion_s": round(self.duration, 3),
            "fps": 30,
            "anclas": {k: {"start": v["start"], "end": v["end"], "texto": v["text"]} for k, v in self.by_key.items()},
            "palabras": [{"i": t["i"], "texto": t["text"], "start": t["start"], "end": t["end"],
                          "seccion": t["section"], "clave": t["key"]} for t in self.toks],
        }

    @staticmethod
    def from_json(d: dict) -> "Timeline":
        toks = tokens()
        if len(d["palabras"]) != len(toks):
            raise ValueError("timings.json no corresponde a este guion")
        for tk, w in zip(toks, d["palabras"]):
            tk["start"], tk["end"] = w["start"], w["end"]
        return Timeline(toks, d["duracion_s"], d.get("fuente_tiempos", "json"))


def build_timeline(voice_path: str | None, timings_path: str | None = None, tail: float = 2.3) -> Timeline:
    if timings_path:
        with open(timings_path, encoding="utf-8") as f:
            return Timeline.from_json(json.load(f))
    if voice_path:
        import soundfile as sf  # type: ignore
        info = sf.info(voice_path)
        toks = align(tokens(), transcribe(voice_path))
        dur = max(info.duration, toks[-1]["end"] + tail)
        return Timeline(toks, dur, f"voz: {voice_path} (faster-whisper, palabra a palabra)")
    toks = synthetic_timings()
    return Timeline(toks, toks[-1]["end"] + tail, "sintético (sin voz): sílabas del guion, locución ajustada a 38,9 s")


if __name__ == "__main__":
    tl = build_timeline(None)
    for t in tl.toks:
        print(f'{t["start"]:6.2f} {t["end"]:6.2f} {t["section"]:10s} {t["text"]:14s} {t["key"] or ""}')
    print("duración", tl.duration)
