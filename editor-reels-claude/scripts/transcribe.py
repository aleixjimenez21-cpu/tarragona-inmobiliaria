"""Transcribe cada toma con Whisper large-v3 (faster-whisper, CPU) con marcas de tiempo por palabra.
Salida: work/transcript.json {id: {"text", "words": [{w, s, e, p}]}} y el texto de cada toma por pantalla,
para ordenar las tomas por lo que se dice (gancho, oferta, qué hacemos, cierre).
Uso (desde la carpeta del proyecto, después de prep_audio.py): python3 <skill>/scripts/transcribe.py [modelo]"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import edl, TAKES, tid
import soundfile as sf
from faster_whisper import WhisperModel

model = sys.argv[1] if len(sys.argv) > 1 else "large-v3"
prompt = getattr(edl, "VOCAB", "")     # nombres propios para ayudar a Whisper (marca, producto…)
m = WhisperModel(model, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
out = {}
for k in TAKES:
    t = tid(k)
    x = sf.read(f"work/audio/w16_{t}.wav", dtype="float32")[0]
    segs, _ = m.transcribe(x, language=getattr(edl, "LANG", "es"), word_timestamps=True, beam_size=5, initial_prompt=prompt or None)
    words, text = [], ""
    for s in segs:
        text += s.text
        words += [{"w": w.word, "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)} for w in s.words]
    out[t] = {"text": text.strip(), "words": words}
    print(f"{k} {t} | {text.strip()}", flush=True)
json.dump(out, open("work/transcript.json", "w"), ensure_ascii=False, indent=1)
