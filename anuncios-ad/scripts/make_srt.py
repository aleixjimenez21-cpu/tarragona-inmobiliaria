"""Genera output/subtitulos.srt a partir de los bloques de subtítulos del plan (mismos tiempos que los quemados)."""
import json
P = json.load(open("work/plan.json"))
def ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
out = []
for i, s in enumerate(P["subs"], 1):
    txt = " ".join(w["w"] for w in s["words"])
    out.append(f"{i}\n{ts(max(0, s['t0']))} --> {ts(s['t1'])}\n{txt}\n")
open("output/subtitulos.srt", "w", encoding="utf-8").write("\n".join(out))
print(len(out), "bloques")
