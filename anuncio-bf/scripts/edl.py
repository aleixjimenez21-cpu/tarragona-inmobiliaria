# Lista de cortes (EDL) del anuncio. Tiempos en segundos dentro de cada toma.
# Orden según lo que se dice (transcripción Whisper large-v3), no según el nombre de archivo.
TAKES = {
    "A": "take_eb7c3ce3",  # gancho
    "B": "take_43493248",  # oferta
    "C": "take_9ba76478",  # qué hacemos  (se elimina "Lo veo bien" del final)
    "D": "take_a54f3308",  # cierre
}
# (toma, entrada, salida)
SEGMENTS = [
    ("A", 0.34, 4.46),
    ("B", 0.46, 5.78),
    ("C", 0.84, 3.98),   # "En Prospectus convertimos ... tour virtual."
    ("C", 4.16, 8.72),   # "Tu comprador entra ... y reserva."  (pausa recortada)
    ("D", 0.30, 5.66),
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
