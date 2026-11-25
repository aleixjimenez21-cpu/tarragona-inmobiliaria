"""Plan de montaje del anuncio 2 ("Promotor, deja de vender pisos con PDF"): planos, clips del tour, rótulos,
palabras detrás de la cabeza, efectos de sonido y sacudidas. Genera work/plan.json y work/sfx.json.
Todos los tiempos en segundos de la línea de tiempo final (30 fps)."""
import json, sys
sys.path.insert(0, "scripts")
from edl import TAKES, SEGMENTS, END_HOLD, FPS, timeline

ACCENT = "#9CC3E2"          # acento único: azul suave desaturado (versión clara, sobre fondos oscuros)
ACCENT_DEEP = "#5A8BB5"     # mismo tono, más profundo, para texto grande sobre la pared blanca
CTA = "ESCRÍBENOS YA"        # en la toma se dice "escríbenos hoy"
DEADLINE = "2026-11-30T23:59:00+01:00"
PUBLISH = "2026-11-25T10:00:00+01:00"

# Cara de respaldo (si falla el seguimiento): centro x, centro y, ancho (fotograma completo a 1080x1920)
FACES = {"A": (560, 820, 220), "B": (560, 680, 180), "C": (560, 780, 200), "D": (520, 800, 200)}

tl, VDUR = timeline()
TOTAL = round(VDUR + END_HOLD, 3)
words = json.load(open("work/words_tl.json"))


def W(text, n=1):
    """tiempo de inicio de la n-ésima aparición de una palabra"""
    c = 0
    for w in words:
        if w["w"].lower().strip("¿?,.") == text.lower():
            c += 1
            if c == n:
                return w["s"]
    raise KeyError(text)


def first_seg(take):
    return next(t0 for k, a, b, t0 in tl if k == take)


T_B, T_C, T_D = first_seg("B"), first_seg("C"), first_seg("D")

# ---------------------------------------------------------------- vídeo base
V = []
FY45 = {"A": 640, "B": 760, "C": 560, "D": 500}      # dónde cae la cara en el 4:5


def aroll(t0, t1, take, fw0, fw1, face_y, punch=False, trans=None):
    """fw0/fw1: ancho de cara en pantalla (px, unidades del detector) al principio/final; el zoom sale del seguimiento de cara"""
    V.append(dict(kind="a", t0=round(t0, 3), t1=round(t1, 3), take=take, fw0=fw0, fw1=fw1, face_y=face_y, punch=punch, face_y45=FY45[take], trans=trans))


def broll(t0, t1, clip, src, speed=1.0, trans=None, shift_y=0):
    V.append(dict(kind="b", t0=round(t0, 3), t1=round(t1, 3), clip=clip, src=src, speed=speed, trans=trans, shift_y=shift_y))


# GANCHO: "Promotor, deja de vender pisos con PDF."  (punch en "PDF")
aroll(0.0, W("pdf"), "A", 360, 372, 1010)
aroll(W("pdf"), T_B, "A", 400, 410, 1040, punch=True, trans="flashlite")
# OFERTA: "Por Black Friday, la primera promotora que cierre con nosotros tiene | el tour virtual | a mitad de precio."
aroll(T_B, W("el"), "B", 330, 345, 1035, punch=True, trans="flash")
broll(W("el"), W("a"), "v07_piscina", 0.6, 1.0, trans="whip")
aroll(W("a"), T_C, "B", 370, 385, 1060, punch=True, trans="whipr")
# QUÉ HACEMOS: tour a pantalla completa con la voz en off
aroll(T_C, W("promoción"), "C", 400, 410, 900, punch=True, trans="zoom")          # "Convertimos tu"
broll(W("promoción"), W("tour", 2), "s04_descenso", 0.2, 1.0, trans="zoom")       # "promoción en un" (edificio real)
broll(W("tour", 2), W("comprador"), "v01_aire_atardecer", 1.0, 1.0, trans="dissolve")  # "tour virtual para que tu" (+ noche)
broll(W("comprador"), W("verlo"), "v04_salon", 0.5, 1.0, trans="whip")           # "comprador pueda"
broll(W("verlo"), W("recorrerlo"), "v05_cocina", 1.0, 1.15, trans="whipr")       # "verlo y"
broll(W("recorrerlo"), W("mucho"), "v06_dormitorio", 1.6, 1.15, trans="zoom")    # "recorrerlo"
aroll(W("mucho"), T_D, "C", 420, 440, 900, punch=True, trans="flash")            # "mucho antes de que tu promoción esté creada."
# CIERRE: plano cerrado
aroll(T_D, TOTAL, "D", 470, 500, 720, punch=True, trans="zoom")

NIGHT = dict(clip="v02_aire_noche", t0=round(W("tour", 2) + 0.55, 3), dur=0.45)
PIP = []

# ---------------------------------------------------------------- subtítulos: frases cortas por sentido
SIZES = [1, 3, 3,                       # Promotor, | deja de vender | pisos con PDF.
         3, 3, 4, 4, 4,                 # Por Black Friday, | la primera promotora | que cierre con nosotros | tiene el tour virtual | a mitad de precio.
         1, 2, 4, 4, 2, 2, 2, 4, 2,     # Convertimos | tu promoción | en un tour virtual | para que tu comprador | pueda verlo | y recorrerlo | mucho antes | de que tu promoción | esté creada.
         3, 4, 4, 2, 2, 4]              # Solo una plaza, | así que ya sabes, | si tienes una promoción, | escríbenos hoy, | o mañana | puede ser muy tarde.


def chunks_by_size():
    assert sum(SIZES) == len(words), (sum(SIZES), len(words))
    out, i = [], 0
    for n in SIZES:
        out.append(words[i:i + n]); i += n
    res = []
    for i, c in enumerate(out):
        t0 = c[0]["s"] - 0.05
        t1 = c[-1]["e"] + 0.15
        if i + 1 < len(out):
            nxt = out[i + 1][0]["s"] - 0.05
            t1 = nxt if nxt - c[-1]["e"] < 0.5 else min(t1, nxt)
        res.append(dict(t0=round(t0, 3), t1=round(t1, 3), words=[dict(w=x["w"], s=x["s"], e=x["e"]) for x in c]))
    return res


SUBS = chunks_by_size()
HIGHLIGHT = ["pdf", "mitad", "tour", "virtual", "antes", "plaza", "escríbenos", "hoy"]

# ---------------------------------------------------------------- palabras detrás de la cabeza
BEHIND = [
    dict(id="hook", t0=0.0, t1=T_B, small="promotor, deja de vender pisos con", big="pdf.", cover=0.28),
    dict(id="offer", t0=W("por") - 0.03, t1=W("el") - 0.03, small="black friday", small2=(W("primera"), "black friday · la primera promotora"), big="-50 %"),
    dict(id="offer2", t0=W("a") + 0.02, t1=T_C - 0.05, small="el tour virtual a", big="mitad"),
    dict(id="antes", t0=W("mucho") + 0.04, t1=T_D - 0.05, small="mucho antes de que tu promoción esté", big="creada."),
    dict(id="plaza", t0=T_D + 0.04, t1=W("así") - 0.02, small="solo queda", big="1 plaza"),
]

# ---------------------------------------------------------------- rótulos
CUES = dict(
    hook=[0.0, T_B],
    chip=[[W("promoción"), W("tour", 2), "Serra Residencial · obra nueva"],
          [W("tour", 2), W("mucho"), "Villa Aurea · tour 360°"]],
    end_panel=W("si"), end_full=round(VDUR - 0.05, 3), total=TOTAL,
)

plan = dict(fps=FPS, total=TOTAL, vdur=VDUR, accent=ACCENT, accent_deep=ACCENT_DEEP, behind=BEHIND, cta=CTA, deadline=DEADLINE, publish=PUBLISH,
            faces=FACES, video=V, pip=PIP, night=NIGHT, subs=SUBS, highlight=HIGHLIGHT, cues=CUES,
            takes={k: TAKES[k] for k in TAKES}, segments=[list(s) + [t0] for s, (_, _, _, t0) in zip(SEGMENTS, tl)])

# ---------------------------------------------------------------- efectos de sonido (Wyzowl SFX Kit, CC0) y sacudidas
T_END = CUES["end_full"]


def S(id, at, db=0, pan=0): return dict(id=id, at=round(at, 3), db=db, pan=pan)


SFX = [S("cinematic-drum-big", 0.0, -2),                                 # apertura del gancho
       S("swish-medium", W("pdf") - 0.02),                               # punch en "PDF"
       S("whoosh-fast-medium", T_B, 0, 1),                               # destello hacia la oferta
       S("boom-hit-medium", W("por") + 0.02, -2),                        # aparece el -50 %
       S("whoosh-fast-soft", W("el"), 0, 1), S("whoosh-fast-soft", W("a"), 0, -1),     # whip pans de la piscina
       S("money-register", 7.58, 2),                                     # justo después de "a mitad de precio."
       S("swish-medium", T_C - 0.03, -3),                               # zoom a "Convertimos"
       S("whoosh-fast-soft", W("promoción"), 0, -1),                     # al edificio real
       S("shimmer-short-soft", W("tour", 2)), S("shimmer-short-soft", NIGHT["t0"]),     # al tour / paso a noche
       S("whoosh-fast-soft", W("comprador"), 0, 1),                      # whip al salón
       S("swish-medium", W("verlo"), -4, -1), S("swish-medium", W("recorrerlo"), -3, 1),
       S("swish-medium", W("mucho") - 0.02, -2),                         # destello de vuelta al plano
       S("swish-medium", T_D + 0.02), S("boom-hit-medium", T_D + 0.06),  # "1 plaza"
       S("pop-medium-in", CUES["end_panel"] - 0.04, -4),                # panel de cierre (en la micro-pausa tras "ya sabes,")
       S("swish-medium", T_END + 0.02), S("sting-minimal-short", T_END + 0.12), S("cinematic-drum-big", T_END + 0.05, -4)]
SHAKES = [(W("por") + 0.02, 9, 0.35), (T_D + 0.06, 8, 0.32), (T_END + 0.03, 10, 0.4)]
plan["shakes"] = SHAKES
json.dump(SFX, open("work/sfx.json", "w"))
json.dump(plan, open("work/plan.json", "w"), ensure_ascii=False, indent=1)
json.dump([v["t0"] for v in V if v.get("trans") in ("whip", "zoom")], open("work/transitions.json", "w"))
if __name__ == "__main__":
    for v in V: print(v)
    print("subs:", len(SUBS)); [print(round(s["t0"], 2), round(s["t1"], 2), " ".join(w["w"] for w in s["words"])) for s in SUBS]
    print(CUES); print("total", TOTAL)
