# EDL del proyecto: qué tomas hay, en qué orden van y qué trozo de cada una se usa.
# Tiempos en segundos DENTRO de cada toma. Rellénalo después de transcribe.py y cut_finder.py.
# (Los valores de ejemplo son de un anuncio real de 4 tomas: gancho, oferta, qué hacemos, cierre.)

# Letra -> archivo dentro de input/. El ORDEN lo decide lo que se dice (transcripción), no el nombre del archivo.
TAKES = {
    "A": "take_b4c4d0fd.mov",  # gancho: "Promotor, deja de vender pisos con PDF."
    "B": "take_f770c468.mov",  # oferta: "Por Black Friday, la primera promotora que cierre con nosotros…"
    "C": "take_e8b41a7e.mov",  # qué hacemos: "Convertimos tu promoción en un tour virtual…"
    "D": "take_69dcd5d3.mov",  # cierre: "Solo una plaza, así que ya sabes…"
}

# (toma, entrada, salida). Una toma puede aparecer en varios tramos seguidos para recortar pausas internas.
SEGMENTS = [
    ("A", 1.85, 4.60),
    ("B", 1.80, 5.10),
    ("B", 5.28, 7.20),   # pausa recortada
    ("C", 0.68, 6.36),
    ("C", 6.66, 9.28),   # pausa recortada
    ("D", 1.04, 5.24),
    ("D", 5.50, 7.22),   # pausa recortada
]
END_HOLD = 2.0     # segundos de tarjeta final después de la última palabra
FPS = 30
XF = 0.010         # microfundido de audio en cada corte (10 ms): evita clics

LANG = "es"                                                   # idioma para Whisper
VOCAB = "Prospectus, tour virtual, promotora, promoción, Black Friday."   # nombres propios para ayudar a Whisper

# Tomas grabadas SIN pared clara detrás (p. ej. en una mesa con pared de madera): su exposición se calibra
# por tono de piel en vez de por la pared (si no, el balance de blancos se va).
SKIN_REF = ["A"]

# Correcciones de tiempos de palabras comprobadas con la envolvente (cut_finder.py --detalle):
# {(id_toma, índice_de_palabra_en_la_toma): (inicio, fin)}. Whisper suele equivocarse en la primera palabra
# de una toma y en las palabras pegadas a una pausa que se recorta (salen duplicadas o desaparecen).
WORD_OVERRIDES = {
    ("take_f770c468", 0): (1.83, 2.02), ("take_f770c468", 1): (2.03, 2.30), ("take_f770c468", 2): (2.33, 2.68),
    ("take_f770c468", 3): (2.86, 2.95), ("take_f770c468", 4): (2.95, 3.14),
    ("take_f770c468", 10): (4.62, 5.06),
    ("take_e8b41a7e", 14): (5.40, 6.29), ("take_e8b41a7e", 15): (6.72, 6.94), ("take_e8b41a7e", 16): (6.95, 7.18),
}


def timeline():
    """[(toma, entrada, salida, inicio_en_el_montaje)] y duración total de voz"""
    t, out = 0.0, []
    for k, a, b in SEGMENTS:
        out.append((k, a, b, t))
        t += b - a
    return out, t
