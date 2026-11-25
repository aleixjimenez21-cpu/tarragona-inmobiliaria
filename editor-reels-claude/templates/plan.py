"""PLAN DE MONTAJE (se edita en cada proyecto). Ejecutar desde la carpeta del proyecto: python3 plan.py
Genera work/plan.json (lo leen compose.py y overlay.html) y work/sfx.json (efectos de sonido).
Todos los tiempos son segundos de la línea de tiempo FINAL. Usa W("palabra") para anclar todo a lo que se dice:
así, si cambian los cortes, el montaje se recoloca solo.

El ejemplo es un anuncio real ("Promotor, deja de vender pisos con PDF"): gancho + oferta + qué hacemos + cierre.
Sustituye textos, palabras ancla y clips por los de tu proyecto."""
import json, sys
sys.path.insert(0, ".")
from edl import TAKES, SEGMENTS, END_HOLD, FPS, timeline

NAME = "anuncio"                 # nombre de los archivos finales: output/<NAME>_9x16.mp4 / _4x5.mp4
ACCENT = "#9CC3E2"               # color de acento ÚNICO, versión clara (sobre fondos oscuros: tarjetas, subtítulos)
ACCENT_DEEP = "#5A8BB5"          # mismo tono, más profundo (palabras grandes sobre pared clara)
CTA = "escríbenos ya"            # botón final: que coincida con lo que se dice en el vídeo

# Textos de la tarjeta final, el panel de cierre y el rótulo de arriba. Admiten HTML corto (<b>, <span class="acc">).
# Un texto vacío oculta su elemento.
TEXTS = dict(
    brand="Prospectus",                                    # si no hay logo en input/brand/, se escribe esto
    badge_label="hasta el", badge_value="30 de noviembre",  # rótulo fijo arriba a la derecha (mejor que una cuenta atrás)
    panel_l1='<span style="color:var(--acc)">-50 %</span> · solo 1 plaza',
    panel_l2="acaba el lunes 30 a las 23:59",
    end_sub="tours virtuales 3d para obra nueva",
    end_tag="black friday", end_big="-50 %", end_line="solo 1 plaza",
    end_deadline="acaba el <b>lunes 30</b> a las <b>23:59</b>",
)

# Cara de respaldo si falla el seguimiento: (centro x, centro y, ancho) en el fotograma completo a 1080x1920
FACES = {k: (540, 800, 200) for k in TAKES}

tl, VDUR = timeline()
TOTAL = round(VDUR + END_HOLD, 3)
words = json.load(open("work/words_tl.json"))


def W(text, n=1):
    """instante en que empieza la n-ésima aparición de una palabra (sin tildes de puntuación, minúsculas)"""
    c = 0
    for w in words:
        if w["w"].lower().strip("¿?¡!,.") == text.lower():
            c += 1
            if c == n:
                return w["s"]
    raise KeyError(f"'{text}' (aparición {n}) no está en work/words_tl.json")


def first_seg(take):
    return next(t0 for k, a, b, t0 in tl if k == take)


T_B, T_C, T_D = first_seg("B"), first_seg("C"), first_seg("D")

# ---------------------------------------------------------------- vídeo base
# aroll = plano a cámara. fw0/fw1 = tamaño de cara objetivo (ancho en px del detector, aprox. 1,35x el ancho real
#   de la cara) al principio/final del plano: el zoom se calcula solo con el seguimiento de cara. face_y = altura
#   del centro de la cara en pantalla (9:16). Valores típicos: gancho 360-400 / 1000-1040, plano cerrado 470-520 / 720.
#   Deja la cabeza por debajo de y≈700 si encima va una palabra grande.
# broll = clip de apoyo de work/clips (src = segundo de inicio dentro del clip, speed = velocidad).
# trans = transición de ENTRADA: "flash", "flashlite", "whip", "whipr", "zoom", "dissolve" o None (corte).
V = []
FY45 = {"A": 640, "B": 760, "C": 560, "D": 500}      # altura de la cara en el 4:5


def aroll(t0, t1, take, fw0, fw1, face_y, punch=False, trans=None):
    V.append(dict(kind="a", t0=round(t0, 3), t1=round(t1, 3), take=take, fw0=fw0, fw1=fw1, face_y=face_y, punch=punch,
                  face_y45=FY45.get(take, 600), trans=trans))


def broll(t0, t1, clip, src, speed=1.0, trans=None, shift_y=0):
    V.append(dict(kind="b", t0=round(t0, 3), t1=round(t1, 3), clip=clip, src=src, speed=speed, trans=trans, shift_y=shift_y))


# GANCHO
aroll(0.0, W("pdf"), "A", 360, 372, 1010)
aroll(W("pdf"), T_B, "A", 400, 410, 1040, punch=True, trans="flashlite")          # punch-in en la palabra clave
# OFERTA
aroll(T_B, W("el"), "B", 330, 345, 1035, punch=True, trans="flash")
broll(W("el"), W("a"), "v07_piscina", 0.6, 1.0, trans="whip")                     # "el tour virtual"
aroll(W("a"), T_C, "B", 370, 385, 1060, punch=True, trans="whipr")
# QUÉ HACEMOS: el producto a pantalla completa con la voz en off (sin PiP: queda pobre)
aroll(T_C, W("promoción"), "C", 400, 410, 900, punch=True, trans="zoom")
broll(W("promoción"), W("tour", 2), "s04_descenso", 0.2, 1.0, trans="zoom")
broll(W("tour", 2), W("comprador"), "v01_aire_atardecer", 1.0, 1.0, trans="dissolve")
broll(W("comprador"), W("verlo"), "v04_salon", 0.5, 1.0, trans="whip")
broll(W("verlo"), W("recorrerlo"), "v05_cocina", 1.0, 1.15, trans="whipr")
broll(W("recorrerlo"), W("mucho"), "v06_dormitorio", 1.6, 1.15, trans="zoom")
aroll(W("mucho"), T_D, "C", 420, 440, 900, punch=True, trans="flash")
# CIERRE: plano cerrado hasta el final (la tarjeta final va encima)
aroll(T_D, TOTAL, "D", 470, 500, 720, punch=True, trans="zoom")

# Cruce opcional entre dos clips con el mismo movimiento (p. ej. día -> noche). None para no usarlo.
NIGHT = dict(over="v01_aire_atardecer", clip="v02_aire_noche", t0=round(W("tour", 2) + 0.55, 3), dur=0.45)

# ---------------------------------------------------------------- subtítulos: bloques cortos POR SENTIDO
# Nº de palabras de cada bloque, en orden (la suma = nº de palabras de work/words_tl.json). 1-4 palabras por bloque.
SIZES = [1, 3, 3,
         3, 3, 4, 4, 4,
         1, 2, 4, 4, 2, 2, 2, 4, 2,
         3, 4, 4, 2, 2, 4]


def chunks_by_size():
    assert sum(SIZES) == len(words), f"SIZES suma {sum(SIZES)} pero hay {len(words)} palabras"
    out, i = [], 0
    for n in SIZES:
        out.append(words[i:i + n]); i += n
    res = []
    for i, c in enumerate(out):
        t0, t1 = c[0]["s"] - 0.05, c[-1]["e"] + 0.15
        if i + 1 < len(out):
            nxt = out[i + 1][0]["s"] - 0.05
            t1 = nxt if nxt - c[-1]["e"] < 0.5 else min(t1, nxt)
        res.append(dict(t0=round(t0, 3), t1=round(t1, 3), words=[dict(w=x["w"], s=x["s"], e=x["e"]) for x in c]))
    return res


SUBS = chunks_by_size()
# Icono de la tarjeta de subtítulos por tramo: house, tag, cube, clock, chat
ICONS = [[0.0, "house"], [T_B, "tag"], [T_C, "cube"], [T_D, "clock"]]

# ---------------------------------------------------------------- palabras DETRÁS de la cabeza
# small = frase fina encima (va delante, nunca se tapa); big = palabra enorme que la cabeza tapa en parte
# ("@logo" = el logo de la marca). cover = fracción de la palabra que tapa la cabeza (0,45 por defecto;
# baja a ~0,3 si la palabra es corta y clave, como en el gancho). Una palabra por idea, con lo que se dice.
BEHIND = [
    dict(id="hook", t0=0.0, t1=T_B, small="promotor, deja de vender pisos con", big="pdf.", cover=0.28),
    dict(id="offer", t0=W("por") - 0.03, t1=W("el") - 0.03, small="black friday",
         small2=(W("primera"), "black friday · la primera promotora"), big="-50 %"),
    dict(id="offer2", t0=W("a") + 0.02, t1=T_C - 0.05, small="el tour virtual a", big="mitad"),
    dict(id="antes", t0=W("mucho") + 0.04, t1=T_D - 0.05, small="mucho antes de que tu promoción esté", big="creada."),
    dict(id="plaza", t0=T_D + 0.04, t1=W("así") - 0.02, small="solo queda", big="1 plaza"),
]

# ---------------------------------------------------------------- rótulos
CUES = dict(
    hook=[0.0, T_B],
    chip=[[W("promoción"), W("tour", 2), "Serra Residencial · obra nueva"],     # etiqueta del clip de apoyo
          [W("tour", 2), W("mucho"), "Villa Aurea · tour 360°"]],
    end_panel=W("si"),                    # panel de cristal con oferta + botón, desde aquí hasta la tarjeta final
    end_full=round(VDUR - 0.05, 3),       # tarjeta final a pantalla completa
    total=TOTAL,
)

# ---------------------------------------------------------------- efectos de sonido (catálogo assets/sfx/sounds.json)
# "at" = instante que debe coincidir con el punto de sincronía del sonido (el script aplica sync.at y baja el
# efecto si cae sobre voz). NUNCA sobre el final de una frase ni en mitad de una palabra clave: compruébalo con
# check_subs.py (Whisper sobre el vídeo final tiene que reconocer el 100 % de las palabras).
T_END = CUES["end_full"]


def S(id, at, db=0, pan=0):
    return dict(id=id, at=round(at, 3), db=db, pan=pan)


SFX = [S("cinematic-drum-big", 0.0, -2),                                 # apertura del gancho
       S("swish-medium", W("pdf") - 0.02),                               # punch en la palabra clave
       S("whoosh-fast-medium", T_B, 0, 1),                               # destello hacia la oferta
       S("boom-hit-medium", W("por") + 0.02, -2),                        # aparece el -50 %
       S("whoosh-fast-soft", W("el"), 0, 1), S("whoosh-fast-soft", W("a"), 0, -1),   # whip pans (paneados)
       S("money-register", 7.58, 2),                                     # tras "a mitad de precio." (en la pausa)
       S("swish-medium", T_C - 0.03, -3),
       S("whoosh-fast-soft", W("promoción"), 0, -1),
       S("shimmer-short-soft", W("tour", 2)), S("shimmer-short-soft", NIGHT["t0"]),
       S("whoosh-fast-soft", W("comprador"), 0, 1),
       S("swish-medium", W("verlo"), -4, -1), S("swish-medium", W("recorrerlo"), -3, 1),
       S("swish-medium", W("mucho") - 0.02, -2),
       S("swish-medium", T_D + 0.02), S("boom-hit-medium", T_D + 0.06),  # "1 plaza"
       S("pop-medium-in", CUES["end_panel"] - 0.04, -4),                 # panel de cierre (en una micro-pausa)
       S("swish-medium", T_END + 0.02), S("sting-minimal-short", T_END + 0.12), S("cinematic-drum-big", T_END + 0.05, -4)]
# Sacudidas de cámara en los golpes fuertes: (instante, amplitud px, duración s)
SHAKES = [(W("por") + 0.02, 9, 0.35), (T_D + 0.06, 8, 0.32), (T_END + 0.03, 10, 0.4)]

plan = dict(name=NAME, fps=FPS, total=TOTAL, vdur=VDUR, accent=ACCENT, accent_deep=ACCENT_DEEP, cta=CTA, texts=TEXTS,
            behind=BEHIND, faces=FACES, video=V, pip=[], night=NIGHT, subs=SUBS, icons=ICONS, highlight=[], cues=CUES,
            shakes=SHAKES, zoom_cap=1.9, cover_t=0.0, deadline="", publish="",
            takes={k: TAKES[k] for k in TAKES}, segments=[list(s) + [t0] for s, (_, _, _, t0) in zip(SEGMENTS, tl)])
json.dump(SFX, open("work/sfx.json", "w"))
json.dump(plan, open("work/plan.json", "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    for v in V: print(v)
    print("subtítulos:"); [print(f"  {s['t0']:6.2f}-{s['t1']:6.2f}  " + " ".join(w["w"] for w in s["words"])) for s in SUBS]
    print("duración total", TOTAL, "s")
