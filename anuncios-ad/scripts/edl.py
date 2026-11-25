# Lista de cortes (EDL) del anuncio. Tiempos en segundos dentro de cada toma.
# Orden según lo que se dice (transcripción Whisper large-v3), no según el nombre de archivo.
TAKES = {
    "A": "take_b4c4d0fd",  # gancho: "Promotor, deja de vender pisos con PDF."
    "B": "take_f770c468",  # oferta: "Por Black Friday, la primera promotora que cierre con nosotros…"
    "C": "take_e8b41a7e",  # qué hacemos: "Convertimos tu promoción en un tour virtual…"
    "D": "take_69dcd5d3",  # cierre: "Solo una plaza, así que ya sabes…"
}
IDS = [v.replace("take_", "") for v in TAKES.values()]
# (toma, entrada, salida)
SEGMENTS = [
    ("A", 1.85, 4.60),   # "Promotor, deja de vender pisos con PDF."
    ("B", 1.80, 5.10),   # "Por Black Friday, la primera promotora que cierre con nosotros tiene"
    ("B", 5.28, 7.20),   # "el tour virtual a mitad de precio."   (pausa recortada)
    ("C", 0.68, 6.36),   # "Convertimos tu promoción en un tour virtual para que tu comprador pueda verlo y recorrerlo"
    ("C", 6.66, 9.28),   # "mucho antes de que tu promoción esté creada."   (pausa recortada)
    ("D", 1.04, 5.24),   # "Solo una plaza, así que ya sabes, si tienes una promoción, escríbenos hoy, o"
    ("D", 5.50, 7.22),   # "mañana puede ser muy tarde."   (pausa recortada)
]
END_HOLD = 2.0     # segundos de tarjeta final tras la última palabra
FPS = 30
XF = 0.010         # microfundido de audio en cada corte (10 ms)


def timeline():
    """Devuelve [(toma, in, out, t_inicio_en_timeline)] y duración de voz."""
    t = 0.0
    out = []
    for k, a, b in SEGMENTS:
        out.append((k, a, b, t))
        t += b - a
    return out, t


def src_to_tl(take_key, ts):
    """Convierte un tiempo de la toma original a tiempo de timeline (None si se cortó)."""
    for k, a, b, t0 in timeline()[0]:
        if k == take_key and a - 0.03 <= ts <= b + 0.03:
            return t0 + min(max(ts, a), b) - a
    return None
