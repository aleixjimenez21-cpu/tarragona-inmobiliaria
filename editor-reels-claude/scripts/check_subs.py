"""Verifica los subtítulos contra el audio FINAL: transcribe el mp4 con Whisper large-v3 y compara
texto y tiempos palabra a palabra con los subtítulos quemados (plan.json)."""
import json, subprocess, sys, unicodedata, re
import numpy as np
from faster_whisper import WhisperModel
f = sys.argv[1]
P = json.load(open("work/plan.json"))
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
x = np.frombuffer(raw, np.float32)
m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4)
segs, _ = m.transcribe(x, language="es", word_timestamps=True, beam_size=5,
                       initial_prompt="Prospectus, tour virtual, promotora, Black Friday.")
heard = [w for s in segs for w in s.words]
norm = lambda s: re.sub(r"[^a-zñ]", "", unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode())
subs = [w for s in P["subs"] for w in s["words"]]
H = [norm(w.word) for w in heard]; S = [norm(w["w"]) for w in subs]
import difflib
sm = difflib.SequenceMatcher(a=S, b=H, autojunk=False)
diffs = [op for op in sm.get_opcodes() if op[0] != "equal"]
print(f"Palabras subtítulo: {len(S)} | oídas en el final: {len(H)} | coincidencia: {sm.ratio()*100:.1f} %")
for tag, a0, a1, b0, b1 in diffs:
    print(f"  {tag}: subtítulo={' '.join(w['w'] for w in subs[a0:a1])!r}  audio={' '.join(w.word for w in heard[b0:b1])!r}")
offs = []
for tag, a0, a1, b0, b1 in sm.get_opcodes():
    if tag == "equal":
        for i, j in zip(range(a0, a1), range(b0, b1)):
            offs.append(subs[i]["s"] - heard[j].start)
offs = np.array(offs)
print(f"Desfase inicio de palabra (subtítulo − audio): mediana {np.median(offs)*1000:+.0f} ms, |p90| {np.percentile(np.abs(offs),90)*1000:.0f} ms, máx {np.abs(offs).max()*1000:.0f} ms")
