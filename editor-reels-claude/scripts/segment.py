"""Máscara de persona (rembg, modelo u2net_human_seg) con suavizado temporal y borde fino."""
import numpy as np, cv2
from PIL import Image
_S = None


def person_mask(rgb):
    """rgb uint8 (H, W, 3) -> máscara float32 0..1 del mismo tamaño"""
    global _S
    if _S is None:
        from rembg import new_session
        _S = new_session("u2net_human_seg")
    from rembg import remove
    h, w = rgb.shape[:2]
    small = cv2.resize(rgb, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    m = np.asarray(remove(Image.fromarray(small), session=_S, only_mask=True)).astype(np.float32) / 255
    # solo la persona: componente conexa más grande (quita falsos positivos del fondo)
    n, lab, stats, _ = cv2.connectedComponentsWithStats((m > 0.35).astype(np.uint8), 8)
    if n > 2:
        keep = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        grow = cv2.dilate((lab == keep).astype(np.uint8), np.ones((9, 9), np.uint8))
        m = m * grow
    m = cv2.resize(m, (w, h), interpolation=cv2.INTER_LINEAR)
    return m


def refine(m, erode_px=2, feather=1.6):
    """quita el halo claro del pelo (erosión ligera) y suaviza el borde"""
    k = np.ones((2 * erode_px + 1, 2 * erode_px + 1), np.uint8)
    m = cv2.erode(m, k)
    return cv2.GaussianBlur(m, (0, 0), feather)


def head_box(m, thr=0.5):
    """(top, left, right) de la cabeza: primera fila con persona y su ancho 80 px más abajo"""
    rows = np.where((m > thr).sum(1) > 25)[0]
    if not len(rows): return None
    top = int(rows[0])
    r = min(m.shape[0] - 1, top + 80)
    cols = np.where(m[r] > thr)[0]
    return top, int(cols.min()), int(cols.max())
