"""Plan de montaje: qué se ve en cada momento (planos míos, clips del tour, PiP, rótulos).
Genera work/plan.json, que leen compose.py (vídeo) y overlay.html (gráficos).
Todos los tiempos en segundos de la línea de tiempo final (30 fps)."""
import json, sys
sys.path.insert(0, "scripts")
from edl import TAKES, SEGMENTS, END_HOLD, FPS, timeline

ACCENT = "#9CC3E2"          # acento único: azul suave desaturado (versión clara, sobre fondos oscuros)
ACCENT_DEEP = "#5A8BB5"     # mismo tono, más profundo, para texto grande sobre la pared blanca
CTA = "ESCRÍBENOS YA"        # lo que digo en la toma es "escríbenos" (el brief decía "ESCRÍBEME YA")
DEADLINE = "2026-11-30T23:59:00+01:00"   # lunes 30 a las 23:59 (Madrid)
PUBLISH = "2026-11-25T10:00:00+01:00"    # momento de publicación supuesto para la cuenta atrás

# Cara (centro x, centro y, ancho) en coordenadas del fotograma completo a 1080x1920, por toma
FACES = {"A": (583, 800, 150), "B": (616, 864, 162), "C": (583, 820, 120), "D": (600, 929, 140)}

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


seg_start = {f"{k}{i}": t0 for i, (k, a, b, t0) in enumerate(tl)}
T_B = tl[1][3]; T_C = tl[2][3]; T_D = tl[4][3]

# ---------------------------------------------------------------- vídeo base
# a-roll: plano mío (toma, zoom inicial, zoom final, y objetivo de la cara en pantalla)
# b-roll: clip del tour (archivo, segundo de inicio en el clip, velocidad)
V = []
# face_y45: dónde cae la cara en el 4:5 (1080x1350), reencuadre propio
FY45 = {"A": 600, "B": 770, "C": 560, "D": 470}
def aroll(t0, t1, take, fw0, fw1, face_y, punch=False, trans=None):
    """fw0/fw1: ancho de cara en pantalla (px) al principio/final del plano; el zoom se calcula con el seguimiento de cara"""
    V.append(dict(kind="a", t0=round(t0, 3), t1=round(t1, 3), take=take, fw0=fw0, fw1=fw1, face_y=face_y, punch=punch, face_y45=FY45[take], trans=trans))
def broll(t0, t1, clip, src, speed=1.0, trans=None, shift_y=0):
    V.append(dict(kind="b", t0=round(t0, 3), t1=round(t1, 3), clip=clip, src=src, speed=speed, trans=trans, shift_y=shift_y))

# GANCHO 0 – B: punch-in sutil + golpe de zoom en "cientos de miles"
aroll(0.0, W("cientos"), "A", 365, 375, 1010)
aroll(W("cientos"), T_B, "A", 380, 395, 1045, punch=True, trans="flashlite")
# OFERTA
aroll(T_B, W("tour"), "B", 340, 350, 1035, punch=True, trans="flash")
broll(W("tour"), W("cuesta"), "v07_piscina", 0.6, 1.0, trans="whip")          # "el tour virtual de tu promoción"
aroll(W("cuesta"), T_C, "B", 365, 380, 1065, punch=True, trans="whipr")                        # "te cuesta la mitad, solo para…"
# QUÉ HACEMOS
aroll(T_C, W("tu", 2) , "C", 420, 440, 900, punch=True, trans="zoom")                         # "En Prospectus convertimos"
broll(W("tu", 2), W("tour", 2), "s04_descenso", 0.2, 1.0, trans="zoom")          # "tu promoción" (edificio real)
broll(W("tour", 2), W("entra"), "v01_aire_atardecer", 1.2, 1.0, trans="dissolve") # "en un tour virtual" (+ paso a noche)
broll(W("entra"), W("lo"), "v04_salon", 0.5, 1.0, trans="whip")                   # "entra en el piso antes de que exista"
broll(W("lo"), W("móvil"), "v05_cocina", 1.0, 1.15, trans="whipr")                               # "lo recorre"
broll(W("móvil"), W("reserva"), "v06_dormitorio", 1.6, 1.25, trans="zoom")                      # "desde el móvil"
broll(W("reserva"), T_D, "s03_fachada", 4.6, 1.0, shift_y=200, trans="flash")                               # "y reserva" (vivienda DISPONIBLE)
# CIERRE: plano cerrado
aroll(T_D, TOTAL, "D", 500, 520, 720, punch=True, trans="zoom")

# noche sobre el plano aéreo (cambio de hora del tour)
NIGHT = dict(clip="v02_aire_noche", t0=round(W("tour", 2) + 0.55, 3), dur=0.45)

# PiP mío mientras el tour ocupa la pantalla en "qué hacemos"
# (desactivado: el tour va a pantalla completa con mi voz en off, sin mi imagen en pequeño)
PIP = []

# ---------------------------------------------------------------- subtítulos (frases cortas)
def chunks(maxc=17):
    out, cur = [], []
    for i, w in enumerate(words):
        cand = " ".join(x["w"] for x in cur + [w])
        gap = w["s"] - cur[-1]["e"] if cur else 0
        if cur and (len(cand) > maxc or gap > 0.28 or cur[-1]["w"][-1] in ",.?" ):
            out.append(cur); cur = []
        cur.append(w)
    if cur: out.append(cur)
    res = []
    for i, c in enumerate(out):
        t0 = c[0]["s"]; t1 = c[-1]["e"] + 0.12
        if i + 1 < len(out): t1 = min(max(t1, out[i + 1][0]["s"] - 0.02 if out[i + 1][0]["s"] - c[-1]["e"] < 0.45 else t1), out[i + 1][0]["s"] - 0.02)
        res.append(dict(t0=round(t0 - 0.04, 3), t1=round(t1, 3), words=[dict(w=x["w"], s=x["s"], e=x["e"]) for x in c]))
    return res

# Frases cortas por sentido (nº de palabras por bloque, en orden)
SIZES = [2, 2, 3, 2, 2, 2, 2,  2, 3, 3, 4, 2, 3, 2,  2, 1, 2, 4, 2, 4, 4, 2, 3, 2,  3, 4, 2, 4, 2, 2, 1]


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
# palabras que van en el color de acento
HIGHLIGHT = ["cientos", "miles", "mitad", "primera", "prospectus", "tour", "virtual", "móvil", "reserva", "sola", "plaza", "acabó", "escríbenos"]

# ---------------------------------------------------------------- palabras detrás de la cabeza (estilo "words behind his head")
# frase pequeña (fina, minúsculas) + palabra grande que la cabeza tapa en parte
BEHIND = [
    dict(id="hook", t0=0.0, t1=T_B, small="¿cansado de pagar cientos de miles a", big="inmobiliarias?"),
    dict(id="offer", t0=W("esta") - 0.05, t1=T_C - 0.05, small="black friday", small2=(W("solo"), "black friday · solo 1 promotora"), big="-50 %"),
    dict(id="brand", t0=W("prospectus") - 0.08, t1=W("tu", 2) - 0.02, small="en", big="@logo"),
    dict(id="plaza", t0=T_D + 0.04, t1=W("así") - 0.02, small="solo queda", big="1 plaza"),
]

# ---------------------------------------------------------------- rótulos
CUES = dict(
    hook=[0.0, T_B],
    offer_in=W("esta"), offer_pulse=W("mitad"), offer_solo=W("solo"), offer_out=T_C - 0.05,
    brand_in=W("prospectus") - 0.05, brand_out=W("tu", 2) - 0.02,
    chip=[[W("tu", 2), W("tour", 2), "Serra Residencial · obra nueva"],
          [W("tour", 2), W("reserva"), "Villa Aurea · tour 360°"],
          [W("reserva"), T_D, "Serra Residencial · elige vivienda"]],
    end_panel=W("así"), end_full=round(VDUR - 0.05, 3), total=TOTAL,
)

plan = dict(fps=FPS, total=TOTAL, vdur=VDUR, accent=ACCENT, accent_deep=ACCENT_DEEP, behind=BEHIND, cta=CTA, deadline=DEADLINE, publish=PUBLISH,
            faces=FACES, video=V, pip=PIP, night=NIGHT, subs=SUBS, highlight=HIGHLIGHT, cues=CUES,
            takes={k: TAKES[k] for k in TAKES}, segments=[list(s) + [t0] for s, (_, _, _, t0) in zip(SEGMENTS, tl)])
json.dump(plan, open("work/plan.json", "w"), ensure_ascii=False, indent=1)
# transiciones con whoosh
json.dump([v["t0"] for v in V if v.get("trans") in ("whip", "zoom")], open("work/transitions.json", "w"))

# ---------------------------------------------------------------- efectos de sonido y sacudidas de cámara
# (tipo, instante en s, ganancia relativa en dB, parámetro opcional)
T_END = CUES["end_full"]
# Sonidos del pack (sfx/, Wyzowl SFX Kit CC0). "at" = instante que debe coincidir con el punto de sincronía del sonido.
def S(id, at, db=0, pan=0): return dict(id=id, at=round(at, 3), db=db, pan=pan)
SFX = [S("cinematic-drum-big", 0.0, -2),                                 # apertura del gancho
       S("swish-medium", W("cientos") - 0.02),                           # punch en "cientos de miles"
       S("whoosh-fast-medium", T_B, 0, 1),                               # destello hacia la oferta
       S("money-register", W("esta") + 0.05, 2), S("boom-hit-medium", W("esta"), -2),   # aparece el -50 %
       S("whoosh-fast-soft", W("tour"), 0, 1), S("whoosh-fast-soft", W("cuesta"), 0, -1), # whip pans de la piscina
       S("swish-medium", T_C + 0.02),                                    # zoom a "En Prospectus"
       S("pop-medium-in", W("prospectus") + 0.2),                        # el logo llega a su tamaño
       S("whoosh-fast-soft", W("tu", 2), 0, -1),                         # al edificio real
       S("shimmer-short-soft", W("tour", 2)), S("shimmer-short-soft", NIGHT["t0"]),     # al tour / paso a noche
       S("whoosh-fast-soft", W("entra"), 0, 1),                          # whip al salón
       S("swish-medium", W("lo"), -4, -1), S("swish-medium", W("móvil"), -3, 1), S("swish-medium", W("reserva"), -3),
       S("notification-success-soft", W("reserva") + 0.48),              # "DISPONIBLE"
       S("swish-medium", T_D + 0.02), S("boom-hit-medium", T_D + 0.06),  # "1 plaza"
       S("pop-medium-in", CUES["end_panel"] + 0.25),                     # panel de cierre
       S("swish-medium", T_END + 0.02), S("sting-minimal-short", T_END + 0.12), S("cinematic-drum-big", T_END + 0.05, -4)]
SHAKES = [(W("esta") + 0.02, 9, 0.35), (T_D + 0.06, 8, 0.32), (T_END + 0.03, 10, 0.4)]
json.dump(SFX, open("work/sfx.json", "w"))
plan["shakes"] = SHAKES
json.dump(plan, open("work/plan.json", "w"), ensure_ascii=False, indent=1)
if __name__ == "__main__":
    for v in V: print(v)
    print("subs:", len(SUBS)); [print(round(s["t0"], 2), round(s["t1"], 2), " ".join(w["w"] for w in s["words"])) for s in SUBS]
    print(CUES); print("total", TOTAL)
