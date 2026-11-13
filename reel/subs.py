"""Subtítulos palabra a palabra (máx. 2 líneas, palabra activa en naranja) y SRT."""
from __future__ import annotations

import skia

from gfx import CX, GRAPHITE, ORANGE, PAPER, draw_text, ease_out, font, prog

SUB_SIZE = 76
LINE_H = 90
MAX_W = 840
SUB_CENTER_Y = 1300  # centro del bloque de subtítulos (zona segura: 250..1540)
ENDERS = (".", "?", ":", "…", "!")


def build_pages(toks):
    f = font("sb", SUB_SIZE)
    space = f.measureText(" ")
    pages, cur, lines, line_w = [], [], [[]], 0.0

    def flush():
        nonlocal cur, lines, line_w
        if cur:
            pages.append({"lines": [l for l in lines if l]})
        cur, lines, line_w = [], [[]], 0.0

    for tk in toks:
        w = f.measureText(tk["text"])
        if lines[-1] and line_w + space + w > MAX_W:
            if len(lines) == 2:
                flush()
            else:
                lines.append([])
                line_w = 0.0
        lines[-1].append(tk)
        line_w = (line_w + space + w) if len(lines[-1]) > 1 else w
        cur.append(tk)
        if tk["text"].endswith(ENDERS):
            flush()
    flush()
    for i, p in enumerate(pages):
        words = [w for l in p["lines"] for w in l]
        p["words"] = words
        p["start"] = words[0]["start"] - 0.06
        nxt = pages[i + 1]["lines"][0][0]["start"] - 0.06 if i + 1 < len(pages) else None
        p["end"] = min(nxt, words[-1]["end"] + 0.7) if nxt is not None else words[-1]["end"] + 1.2
        p["keys"] = {w["key"] for w in words if w["key"]}
    return pages


def draw_subs(c: skia.Canvas, pages, t, hidden_keys=(), center_y=SUB_CENTER_Y, alpha=1.0):
    f = font("sb", SUB_SIZE)
    space = f.measureText(" ")
    for p in pages:
        if not (p["start"] <= t < p["end"]):
            continue
        if p["keys"] & set(hidden_keys):
            return
        n = len(p["lines"])
        y0 = center_y - (n - 1) * LINE_H / 2 + SUB_SIZE * 0.36
        words = p["words"]
        active = None
        for w in words:
            if w["start"] - 0.03 <= t:
                active = w
        for li, line in enumerate(p["lines"]):
            widths = [f.measureText(w["text"]) for w in line]
            total = sum(widths) + space * (len(line) - 1)
            x = CX - total / 2
            y = y0 + li * LINE_H
            for w, ww in zip(line, widths):
                if t >= w["start"] - 0.03:
                    k = ease_out(prog(t, w["start"] - 0.03, w["start"] + 0.09))
                    sc = 0.82 + 0.18 * k
                    is_act = w is active and t < max(w["end"] + 0.25, w["start"] + 0.3)
                    colr = ORANGE if is_act else PAPER
                    c.save()
                    c.translate(x + ww / 2, y - SUB_SIZE * 0.35)
                    c.scale(sc, sc)
                    draw_text(c, w["text"], -ww / 2, SUB_SIZE * 0.35, f, colr, alpha * (0.35 + 0.65 * k), align="left",
                              stroke=11, stroke_color=GRAPHITE, stroke_alpha=0.92, shadow=10)
                    c.restore()
                x += ww + space
        return


def srt(pages) -> str:
    def ts(x):
        x = max(0.0, x)
        h, r = divmod(x, 3600)
        m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)) % 1000:03d}"
    out = []
    for i, p in enumerate(pages, 1):
        text = "\n".join(" ".join(w["text"] for w in l) for l in p["lines"])
        out.append(f"{i}\n{ts(p['start'] + 0.06)} --> {ts(p['end'])}\n{text}\n")
    return "\n".join(out)
