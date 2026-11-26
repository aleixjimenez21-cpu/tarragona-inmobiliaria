"""PLAN DE MONTAJE (se edita en cada proyecto). Ejecutar desde la carpeta del proyecto: python3 plan.py
Genera work/plan.json (lo leen compose.py y overlay.html) y work/sfx.json (efectos de sonido).
Todos los tiempos son segundos de la línea de tiempo FINAL. Usa W("palabra") para anclar todo a lo que se dice:
así, si cambian los cortes, el montaje se recoloca solo.

El ejemplo es un anuncio real ("Promotor, deja de vender pisos con PDF"): gancho + oferta + qué hacemos + cierre.
Sustituye textos, palabras ancla y clips por los de tu proyecto."""
import json, sys
sys.path.insert(0, ".")
from edl import TAKES, SEGMENTS, END_HOLD, FPS, timeline

NAME = "prospectus_3errores"                 # nombre de los archivos finales: output/<NAME>_9x16.mp4 / _4x5.mp4
ACCENT = "#9CC3E2"               # color de acento ÚNICO, versión clara (sobre fondos oscuros: tarjetas, subtítulos)
ACCENT_DEEP = "#5A8BB5"          # mismo tono, más profundo (palabras grandes sobre pared clara)
CTA = "contáctanos"             # lo que se dice al final del vídeo

# Textos de la tarjeta final, el panel de cierre y el rótulo de arriba. Admiten HTML corto (<b>, <span class="acc">).
# Un texto vacío oculta su elemento.
TEXTS = dict(
    brand="Prospectus",
    badge_label="", badge_value="",              # el rótulo de arriba va por pasos (badge_steps, más abajo)
    panel_l1='tu preventa, en <span style="color:var(--acc)">tour&nbsp;3d</span>',
    panel_l2="tu comprador la recorre desde el móvil",
    end_sub="tours virtuales 3d para obra nueva",
    end_tag="vende tu preventa con un", end_big="tour 3d", end_line="que tu comprador recorre desde el sofá",
    end_deadline="",
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


# GANCHO: "¿Te cuesta vender la preventa de tu promoción? | Seguro que estás cometiendo uno de estos tres errores."
aroll(0.0, W("seguro"), "A", 360, 372, 1010)
aroll(W("seguro"), T_B, "A", 400, 410, 1040, punch=True, trans="flashlite")
# ERROR 1: "Uno. Vendes con | planos y un render. | El comprador no se imagina su casa. Y si no se la imagina, no reserva."
aroll(T_B, W("planos"), "B", 380, 390, 1020, punch=True, trans="flash")
broll(W("planos"), W("el"), "planos_render", 0.25, 1.0, trans="zoom")           # plano + render como tarjetas: "así se vende hoy"
aroll(W("el"), T_C, "B", 400, 415, 1030, punch=True, trans="whipr")
# ERROR 2: "Dos. Solo puede verla si va a tu sala de ventas. | El comprador hoy decide desde el sofá | y con su móvil."
aroll(T_C, W("el", 2), "C", 380, 390, 1020, punch=True, trans="flash")
broll(W("el", 2), W("y", 3), "v04_salon", 0.3, 1.0, trans="whip")               # "desde el sofá": el salón del tour, con su sofá
broll(W("y", 3), T_D, "s03_fachada", 4.0, 1.25, shift_y=200, trans="whipr")      # "con su móvil": la web eligiendo vivienda
# ERROR 3 + CIERRE: "Tres, no estás en contacto con nosotros, | así que si tienes alguna promoción activa, | contáctanos."
aroll(T_D, W("así"), "D", 420, 440, 900, punch=True, trans="flash")
broll(W("así"), W("promoción", 2), "v01_aire_atardecer", 1.0, 1.0, trans="zoom")  # la solución: el tour
broll(W("promoción", 2), W("contáctanos"), "v08_mirador", 0.6, 1.0, trans="whip")
aroll(W("contáctanos"), TOTAL, "D", 480, 500, 760, punch=True, trans="zoom")

# Cruce opcional entre dos clips con el mismo movimiento (p. ej. día -> noche). None para no usarlo.
NIGHT = dict(over="v01_aire_atardecer", clip="v02_aire_noche", t0=round(W("así") + 0.45, 3), dur=0.45)

# ---------------------------------------------------------------- subtítulos: bloques cortos POR SENTIDO
# Nº de palabras de cada bloque, en orden (la suma = nº de palabras de work/words_tl.json). 1-4 palabras por bloque.
SIZES = [3, 2, 3, 4, 3, 2,                    # ¿Te cuesta vender | la preventa | de tu promoción? | Seguro que estás cometiendo | uno de estos | tres errores.
         4, 3, 2, 3, 2, 3, 3, 2,                 # 1. Vendes con planos | y un render. | El comprador | no se imagina | su casa. | Y si no | se la imagina, | no reserva.
         4, 4, 3, 2, 2, 3, 4,                    # 2. Solo puede verla | si va a tu | sala de ventas. | El comprador | hoy decide | desde el sofá | y con su móvil.
         1, 4, 2, 4, 3, 1]                       # Tres, | no estás en contacto | con nosotros, | así que si tienes | alguna promoción activa, | contáctanos.


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
ICONS = [[0.0, "house"], [T_B, "tag"], [W("así"), "chat"]]

# ---------------------------------------------------------------- palabras DETRÁS de la cabeza
# small = frase fina encima (va delante, nunca se tapa); big = palabra enorme que la cabeza tapa en parte
# ("@logo" = el logo de la marca). cover = fracción de la palabra que tapa la cabeza (0,45 por defecto;
# baja a ~0,3 si la palabra es corta y clave, como en el gancho). Una palabra por idea, con lo que se dice.
BEHIND = [
    dict(id="hook", t0=0.0, t1=W("seguro") - 0.03, small="¿te cuesta vender la", big="preventa?", cover=0.3),
    dict(id="hook2", t0=W("seguro") + 0.02, t1=T_B - 0.05, small="seguro que estás cometiendo uno de estos", big="3 errores", cover=0.35),
    dict(id="e1", t0=T_B + 0.02, t1=W("planos") - 0.03, small="error 1 · vendes con", big="planos", cover=0.35),
    dict(id="e1b", t0=W("y", 2) - 0.03, t1=T_C - 0.05, small="y si no se la imagina,", big="no reserva."),
    dict(id="e2", t0=T_C + 0.02, t1=W("el", 2) - 0.03, small="error 2 · solo la ve si va a tu", big="sala de ventas"),
    dict(id="e3", t0=T_D + 0.02, t1=W("así") - 0.03, small="error 3 · no estás en contacto con", big="@logo"),

]

# ---------------------------------------------------------------- rótulos
CUES = dict(
    hook=[0.0, T_B],
    chip=[[W("planos"), W("el"), "así se vende hoy: planos + render"],
          [W("el", 2), W("y", 3), "villa aurea · tour 360°"],
          [W("y", 3), T_D, "serra residencial · desde el móvil"]],
    end_panel=W("así"),
    end_full=round(VDUR - 0.05, 3),
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
       S("swish-medium", W("seguro") - 0.02), S("boom-hit-medium", W("seguro") + 0.02, -4),   # "3 errores"
       S("whoosh-fast-medium", T_B, 0, 1), S("tone-step-1", W("1") + 0.02, -1),             # error 1 (nota de marimba)
       S("swish-medium", W("planos") - 0.02, -2), S("whoosh-fast-soft", W("el"), 0, -1),
       S("whoosh-fast-medium", T_C, 0, -1), S("tone-step-2", W("2") + 0.02, -1),            # error 2 (una nota más alta)
       S("whoosh-fast-soft", W("el", 2), 0, 1), S("swish-medium", W("y", 3), -3, -1),
       S("whoosh-fast-medium", T_D, 0, 1), S("tone-step-3", W("tres", 2) + 0.02, -1),          # error 3
       S("pop-medium-in", 16.62, -4),                                                   # panel (pausa tras "nosotros,")
       S("whoosh-fast-soft", W("así"), 0, -1), S("shimmer-short-soft", NIGHT["t0"]),
       S("swish-medium", W("promoción", 2), -4, 1), S("swish-medium", W("contáctanos") - 0.05, -2),
       S("swish-medium", T_END + 0.02), S("sting-minimal-short", T_END + 0.12), S("cinematic-drum-big", T_END + 0.05, -4)]
# Sacudidas de cámara en los golpes fuertes: (instante, amplitud px, duración s)
SHAKES = [(W("seguro") + 0.02, 8, 0.3), (T_END + 0.03, 10, 0.4)]

TEXTS["badge_steps"] = [[0.0, "3 errores en tu preventa"], [T_B, "error 1 de 3"], [T_C, "error 2 de 3"], [T_D, "error 3 de 3"], [W("así"), "la solución"]]
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
