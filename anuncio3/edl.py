# EDL del proyecto: qué tomas hay, en qué orden van y qué trozo de cada una se usa.
# Tiempos en segundos DENTRO de cada toma. Rellénalo después de transcribe.py y cut_finder.py.
# (Los valores de ejemplo son de un anuncio real de 4 tomas: gancho, oferta, qué hacemos, cierre.)

# Letra -> archivo dentro de input/. El ORDEN lo decide lo que se dice (transcripción), no el nombre del archivo.
TAKES = {
    "A": "take_af32471c.mov",  # gancho: "¿Te cuesta vender la preventa de tu promoción? … uno de estos tres errores."
    "B": "take_454b37f5.mov",  # error 1: "Uno. Vendes con planos y un render…"
    "C": "take_91aefcf0.mov",  # error 2: "Dos. Solo puede verla si va a tu sala de ventas…"
    "D": "take_d87cd4fa.mov",  # error 3 + cierre: "Tres, no estás en contacto con nosotros… contáctanos."
}

# (toma, entrada, salida). Una toma puede aparecer en varios tramos seguidos para recortar pausas internas.
SEGMENTS = [
    ("A", 1.04, 2.78),   # ¿Te cuesta vender la preventa de tu promoción?
    ("A", 2.98, 5.42),   # Seguro que estás cometiendo uno de estos tres errores.
    ("B", 1.06, 3.08),   # Uno. Vendes con planos y un render.
    ("B", 3.30, 6.74),   # El comprador no se imagina su casa. Y si no se la imagina, no reserva.
    ("C", 1.04, 3.54),   # Dos. Solo puede verla si va a tu sala de ventas.
    ("C", 3.76, 6.58),   # El comprador hoy decide desde el sofá y con su móvil.
    ("D", 1.12, 5.02),   # Tres, no estás en contacto con nosotros, así que si tienes alguna promoción activa,
    ("D", 5.46, 6.28),   # contáctanos.
]
END_HOLD = 2.0     # segundos de tarjeta final después de la última palabra
FPS = 30
XF = 0.010         # microfundido de audio en cada corte (10 ms): evita clics

LANG = "es"                                                   # idioma para Whisper
VOCAB = "Prospectus, preventa, promoción, sala de ventas, sofá, móvil, contáctanos."   # nombres propios para ayudar a Whisper

# Tomas grabadas SIN pared clara detrás (p. ej. en una mesa con pared de madera): su exposición se calibra
# por tono de piel en vez de por la pared (si no, el balance de blancos se va).
SKIN_REF = []

# Correcciones de tiempos de palabras comprobadas con la envolvente (cut_finder.py --detalle):
# {(id_toma, índice_de_palabra_en_la_toma): (inicio, fin)}. Whisper suele equivocarse en la primera palabra
# de una toma y en las palabras pegadas a una pausa que se recorta (salen duplicadas o desaparecen).
WORD_OVERRIDES = {("take_d87cd4fa", 14): (5.54, 6.22),
                  ("take_454b37f5", 0): (1.10, 1.40), ("take_91aefcf0", 0): (1.08, 1.42),   # "uno" / "dos"
                  ("take_91aefcf0", 11): (3.82, 3.92)}                                            # "El" tras la pausa recortada
# Whisper oyó "hobby" (es "móvil") y partió "contáctanos" en "contacta a nosotros" (comprobado con una segunda transcripción)
WORD_TEXT = {("take_91aefcf0", 21): "móvil.", ("take_d87cd4fa", 14): "contáctanos.", ("take_d87cd4fa", 15): "", ("take_d87cd4fa", 16): ""}


def timeline():
    """[(toma, entrada, salida, inicio_en_el_montaje)] y duración total de voz"""
    t, out = 0.0, []
    for k, a, b in SEGMENTS:
        out.append((k, a, b, t))
        t += b - a
    return out, t
