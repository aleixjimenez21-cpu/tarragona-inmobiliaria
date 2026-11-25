"""Mide dónde queda la parte alta de la cabeza en cada rótulo "detrás de la cabeza" para colocar
la palabra grande de forma que la cabeza la tape en parte. Uso: python3 scripts/head_tops.py <9x16|4x5>"""
import sys, json
import numpy as np
fmt = sys.argv[1]
sys.argv = ["compose.py", fmt]
sys.path.insert(0, "scripts")
import compose as C
from segment import person_mask, head_box
out = {}
for b in C.P["behind"]:
    tops = []; lefts = []; rights = []
    for t in np.linspace(b["t0"] + 0.1, b["t1"] - 0.1, 6):
        e = C.entry_at(t)
        if e["kind"] != "a": continue
        img = C.a_frame(e, t)
        hb = head_box(person_mask(img))
        if hb: tops.append(hb[0]); lefts.append(hb[1]); rights.append(hb[2])
    out[b["id"]] = dict(top=int(np.median(tops)), left=int(np.median(lefts)), right=int(np.median(rights)), n=len(tops)) if tops else None
    print(fmt, b["id"], out[b["id"]], "rango tops", (min(tops), max(tops)) if tops else None, flush=True)
json.dump(out, open(f"work/head_tops_{fmt}.json", "w"), indent=1)
