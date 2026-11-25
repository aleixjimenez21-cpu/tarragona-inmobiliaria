"""Efectos de sonido sintetizados (sin derechos de terceros) para transiciones de reel:
whoosh, swish, impact, riser, pop, ding y shimmer. Todos estéreo a 48 kHz con una pequeña reverb."""
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
RNG = np.random.default_rng(11)


def _bp_sweep(noise, f0, f1, q=0.7, blk=256):
    """filtro paso banda que barre de f0 a f1 (exponencial)"""
    n = len(noise); y = np.zeros(n)
    zi = None
    for i in range(0, n, blk):
        fc = f0 * (f1 / f0) ** (i / n)
        lo, hi = fc * (1 - q / 2), min(fc * (1 + q), SR / 2 * 0.95)
        sos = butter(2, [max(20, lo) / (SR / 2), hi / (SR / 2)], "band", output="sos")
        y[i:i + blk] = sosfilt(sos, noise[i:i + blk])
    return y


def _reverb(x, dur=0.45, mix=0.18):
    n = int(dur * SR)
    ir = RNG.standard_normal(n) * np.exp(-np.linspace(0, 7, n))
    ir = sosfilt(butter(2, 6000 / (SR / 2), "low", output="sos"), ir)
    wet = np.zeros(len(x) + n); c = fftconvolve(x, ir); wet[:min(len(c), len(wet))] = c[:len(wet)]
    wet /= max(1e-9, np.max(np.abs(wet))) / max(1e-9, np.max(np.abs(x)))
    out = np.zeros(len(x) + n); out[:len(x)] += x
    return out * (1 - mix) + wet * mix


def _pan(x, p0, p1):
    """paneo de p0 a p1 (-1 izq .. 1 der), ley de potencia constante"""
    p = np.linspace(p0, p1, len(x))
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)


def whoosh(direction=1, dur=0.55):
    n = int(dur * SR); t = np.linspace(0, 1, n)
    y = _bp_sweep(RNG.standard_normal(n), 300, 4200, 0.9)
    tone = np.sin(2 * np.pi * np.cumsum(120 + 500 * t ** 2) / SR) * 0.12      # cuerpo tonal que sube
    env = np.where(t < 0.62, (t / 0.62) ** 2.2, np.exp(-(t - 0.62) * 14))     # pico al 62 % (= el corte)
    y = (y / np.max(np.abs(y)) + tone) * env
    st = _pan(y, -0.7 * direction, 0.7 * direction)
    return np.stack([_reverb(st[:, 0], 0.35, 0.15), _reverb(st[:, 1], 0.35, 0.15)], 1), 0.62 * dur


def swish(direction=1, dur=0.28):
    n = int(dur * SR); t = np.linspace(0, 1, n)
    y = _bp_sweep(RNG.standard_normal(n), 1200, 7000, 0.8)
    env = np.where(t < 0.5, (t / 0.5) ** 2, np.exp(-(t - 0.5) * 16))
    y = y / np.max(np.abs(y)) * env
    return _pan(y, -0.5 * direction, 0.5 * direction), 0.5 * dur


def impact(dur=1.2):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 38 + 34 * np.exp(-t * 9)                                               # caída de tono (sub)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    thump = sosfilt(butter(2, 180 / (SR / 2), "low", output="sos"), RNG.standard_normal(n)) * np.exp(-t * 28) * 3
    click = sosfilt(butter(2, 2500 / (SR / 2), "high", output="sos"), RNG.standard_normal(n)) * np.exp(-t * 160) * 0.35
    y = sub + thump + click
    y = np.tanh(y * 1.4) / np.tanh(1.4)
    y = _reverb(y, 0.7, 0.12)
    return np.stack([y, y], 1), 0.0


def riser(dur=0.7):
    n = int(dur * SR); t = np.linspace(0, 1, n)
    y = _bp_sweep(RNG.standard_normal(n), 400, 6000, 0.6)
    tone = np.sin(2 * np.pi * np.cumsum(220 * 2 ** (2 * t)) / SR) * 0.25
    y = (y / np.max(np.abs(y)) + tone) * t ** 2.5
    y[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))
    return np.stack([y, y], 1), dur                                            # termina justo en el instante


def pop(dur=0.18):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 900 + 900 * np.exp(-t * 60)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30)
    y += sosfilt(butter(2, 3000 / (SR / 2), "high", output="sos"), RNG.standard_normal(n)) * np.exp(-t * 250) * 0.3
    return np.stack([y, y], 1), 0.0


def ding(dur=1.1):
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for f, a, d in [(1318.5, 1.0, 4.5), (1975.5, 0.6, 5.5), (2637, 0.25, 7), (3951, 0.12, 9)]:   # E6 + B6 + armónicos
        y += a * np.sin(2 * np.pi * f * t) * np.exp(-t * d)
    y *= np.minimum(1, t / 0.004)
    y = _reverb(y, 0.6, 0.2)
    return _pan(y, 0.15, 0.15), 0.0


def shimmer(dur=1.2):
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for _ in range(14):
        f = RNG.uniform(3000, 9000); t0 = RNG.uniform(0, 0.35)
        e = np.where(t > t0, np.exp(-(t - t0) * RNG.uniform(5, 9)), 0)
        y += np.sin(2 * np.pi * f * t + RNG.uniform(0, 6)) * e * RNG.uniform(0.3, 1)
    y *= np.minimum(1, t / 0.03)
    st = np.stack([_reverb(y, 0.8, 0.3), _reverb(np.roll(y, 240), 0.8, 0.3)], 1)
    return st, 0.0


GEN = dict(whoosh=whoosh, swish=swish, impact=impact, riser=riser, pop=pop, ding=ding, shimmer=shimmer)


def render(events, total):
    """events: [(tipo, instante, dB, [dirección])] -> pista estéreo normalizada a pico 0,5"""
    N = int(total * SR) + SR
    out = np.zeros((N, 2))
    for ev in events:
        kind, at, db = ev[0], ev[1], ev[2]
        args = ev[3:] if len(ev) > 3 else []
        y, anchor = GEN[kind](*args)
        y = y / max(1e-9, np.max(np.abs(y))) * 10 ** (db / 20)
        s0 = int((at - anchor) * SR)
        if s0 < 0: y = y[-s0:]; s0 = 0
        e = min(N, s0 + len(y)); out[s0:e] += y[:e - s0]
    out = out[:int(total * SR)]
    return out / max(1e-9, np.max(np.abs(out))) * 0.5
