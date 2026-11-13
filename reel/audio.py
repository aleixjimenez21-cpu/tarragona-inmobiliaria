"""Música y efectos 100 % sintetizados aquí (sin muestras de terceros), ducking bajo la voz
y mezcla final a -14 LUFS / -1 dBTP."""
from __future__ import annotations

import numpy as np
from scipy import signal

SR = 48000
RS = np.random.RandomState(1234)


# --------------------------------------------------------------------------------------
# utilidades
# --------------------------------------------------------------------------------------
def secs(n):
    return np.arange(int(n * SR)) / SR


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def lp(x, fc, order=2):
    b, a = signal.butter(order, min(fc, SR * 0.45) / (SR / 2), "low")
    return signal.lfilter(b, a, x, axis=0)


def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x, axis=0)


def bp(x, f0, f1, order=2):
    b, a = signal.butter(order, [f0 / (SR / 2), min(f1, SR * 0.45) / (SR / 2)], "band")
    return signal.lfilter(b, a, x, axis=0)


def sweep_filter(x, f_start, f_end, q=1.2, kind="band"):
    """Filtro variable por bloques (SVF sencillo)."""
    n = len(x)
    out = np.zeros(n)
    low = band = 0.0
    fs = np.geomspace(max(f_start, 20), max(f_end, 20), n)
    damp = 1 / q
    for i in range(n):
        f = 2 * np.sin(np.pi * min(fs[i], SR / 6) / SR)
        low += f * band
        high = x[i] - low - damp * band
        band += f * high
        out[i] = band if kind == "band" else low if kind == "low" else high
    return out


def env_adsr(n, a, d, s, r, sustain_len=None):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    hold = max(0, n - a - d - r) if sustain_len is None else int(sustain_len * SR)
    e = np.concatenate([np.linspace(0, 1, max(a, 1)), np.linspace(1, s, max(d, 1)), np.full(hold, s),
                        np.linspace(s, 0, max(r, 1))])
    return np.pad(e, (0, max(0, n - len(e))))[:n]


def saw(f, t, phase=0.0):
    return 2 * ((f * t + phase) % 1.0) - 1


def pan(x, p):
    """p en [-1, 1] -> estéreo con ley de potencia constante."""
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)


def reverb_ir(seconds=2.2, damp=3.0, seed=7):
    r = np.random.RandomState(seed)
    t = secs(seconds)
    ir = r.randn(len(t), 2) * np.exp(-damp * t)[:, None]
    ir[:, 0] = lp(ir[:, 0], 6000)
    ir[:, 1] = lp(ir[:, 1], 6000)
    return ir / np.sqrt((ir ** 2).sum(0))


IR = None


def reverb(x, wet=0.25):
    global IR
    if IR is None:
        IR = reverb_ir()
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    y = np.stack([signal.fftconvolve(x[:, c], IR[:, c])[:len(x)] for c in range(2)], 1)
    return x * (1 - wet) + y * wet


def place(buf, x, t0, gain=1.0):
    i0 = int(round(t0 * SR))
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    x = x.copy()
    fi = min(len(x), int(0.003 * SR))  # ataque de 3 ms: evita picos del códec en golpes tras silencio
    x[:fi] *= np.linspace(0, 1, fi)[:, None]
    if i0 < 0:
        x = x[-i0:]
        i0 = 0
    i1 = min(len(buf), i0 + len(x))
    if i1 > i0:
        buf[i0:i1] += x[:i1 - i0] * gain


# --------------------------------------------------------------------------------------
# instrumentos
# --------------------------------------------------------------------------------------
def kick(dur=0.45, f0=150, f1=44, click=0.5):
    t = secs(dur)
    f = f1 + (f0 - f1) * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t * 7.5)
    x[: int(0.004 * SR)] += click * RS.randn(int(0.004 * SR)) * np.linspace(1, 0, int(0.004 * SR))
    return np.tanh(x * 1.6) * 0.9


def hat(dur=0.05, open_=False):
    t = secs(dur if not open_ else 0.22)
    x = hp(RS.randn(len(t)), 7500) * np.exp(-t * (70 if not open_ else 16))
    return x * 0.35


def snare(dur=0.22):
    t = secs(dur)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)
    nz = bp(RS.randn(len(t)), 1500, 9000) * np.exp(-t * 16)
    return (tone * 0.5 + nz * 0.8) * 0.6


def bass_note(f, dur, cutoff=900):
    t = secs(dur)
    x = 0.6 * saw(f, t) + 0.5 * np.sin(2 * np.pi * f * t)
    x = lp(x, cutoff, 2)
    return x * env_adsr(len(t), 0.004, 0.08, 0.65, 0.05) * 0.55


def pad_chord(notes, dur, cutoff=1800, detune=0.11):
    t = secs(dur)
    out = np.zeros((len(t), 2))
    for i, n in enumerate(notes):
        for k, dt in enumerate((-detune, 0, detune)):
            f = midi(n + dt)
            v = saw(f, t, phase=RS.rand())
            out += pan(v, (k - 1) * 0.6) * 0.08
    out = np.stack([lp(out[:, c], cutoff, 2) for c in range(2)], 1)
    return out * env_adsr(len(t), min(0.4, dur / 3), 0.3, 0.8, min(0.5, dur / 3))[:, None]


def pluck(f, dur=0.35, cutoff=3200):
    t = secs(dur)
    x = 0.5 * saw(f, t) + 0.4 * np.sign(np.sin(2 * np.pi * f * t)) * 0.5
    x = lp(x, cutoff, 2) * np.exp(-t * 9)
    return x * 0.22


# --------------------------------------------------------------------------------------
# efectos
# --------------------------------------------------------------------------------------
def sfx_boom():
    t = secs(1.6)
    f = 38 + 90 * np.exp(-t * 9)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.6)
    nz = lp(RS.randn(len(t)), 900) * np.exp(-t * 9) * 0.5
    x = np.tanh((sub + nz) * 1.8) * 0.95
    return reverb(x, 0.18)


def sfx_whip(dur=0.38):
    n = int(dur * SR)
    t = secs(dur)
    x = RS.randn(n)
    y = sweep_filter(x, 500, 6500, q=3.0)
    e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    y = y * e
    L = y * np.linspace(1.0, 0.2, n)
    R = y * np.linspace(0.2, 1.0, n)
    return np.stack([L, R], 1) * 0.9


def sfx_tick(f=2600):
    t = secs(0.03)
    return (np.sin(2 * np.pi * f * t) * np.exp(-t * 220) + hp(RS.randn(len(t)), 5000) * np.exp(-t * 400) * 0.4) * 0.45


def sfx_shrink(dur=0.55, f0=880, f1=170):
    t = secs(dur)
    f = f0 * (f1 / f0) ** (t / dur)
    ph = 2 * np.pi * np.cumsum(f * (1 + 0.04 * np.sin(2 * np.pi * 18 * t))) / SR
    x = (np.sin(ph) + 0.3 * np.sign(np.sin(ph))) * env_adsr(len(t), 0.01, 0.1, 0.8, 0.15)
    return reverb(lp(x, 4000) * 0.35, 0.2)


def sfx_grow(dur=0.7):
    return sfx_shrink(dur, 170, 900)


def sfx_pop():
    t = secs(0.12)
    f = 500 + 1600 * (t / 0.12)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 35)
    return x * 0.5


def sfx_riser(dur):
    n = int(dur * SR)
    t = secs(dur)
    nz = sweep_filter(RS.randn(n), 300, 9000, q=2.0) * (t / dur) ** 2
    f = 110 * 2 ** (3 * t / dur)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / dur) ** 2.2 * 0.25
    tone2 = np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR) * (t / dur) ** 2.5 * 0.15
    x = (nz * 0.6 + tone + tone2)
    return reverb(x, 0.3) * 0.75


def sfx_impact():
    t = secs(2.4)
    f = 32 + 120 * np.exp(-t * 7)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.8)
    crash = hp(RS.randn(len(t)), 2500) * np.exp(-t * 3.2) * 0.35
    body = lp(RS.randn(len(t)), 1200) * np.exp(-t * 14) * 0.7
    x = np.tanh((sub * 1.2 + crash + body) * 1.5)
    return reverb(x, 0.3) * 0.95


def sfx_flash():
    t = secs(1.2)
    x = np.zeros(len(t))
    for f in (2093, 2637, 3136, 4186):
        x += np.sin(2 * np.pi * f * t + RS.rand() * 6) * np.exp(-t * 4)
    return reverb(x * 0.06, 0.5)


def sfx_scratch():
    dur = 0.55
    t = secs(dur)
    # velocidad del "disco": adelante-atrás
    v = np.sin(2 * np.pi * 5.5 * t) * np.exp(-t * 1.5)
    ph = np.cumsum(np.abs(v)) / SR
    src = np.sin(2 * np.pi * 220 * ph * 6) + 0.6 * saw(1, ph * 900)
    nz = bp(RS.randn(len(t)), 800, 5000) * np.abs(v)
    x = (src * 0.4 + nz * 0.6) * np.abs(v) ** 0.5
    x = bp(x, 300, 6000)
    return np.tanh(x * 2.0) * 0.55


def sfx_stop():
    """Golpe seco + "chas" para la parada de "Pero espera"."""
    t = secs(0.5)
    x = np.sin(2 * np.pi * np.cumsum(60 + 200 * np.exp(-t * 30)) / SR) * np.exp(-t * 10)
    x += bp(RS.randn(len(t)), 1500, 6000) * np.exp(-t * 30) * 0.5
    return np.tanh(x * 1.4) * 0.8


def sfx_whoosh(dur=0.45):
    t = secs(dur)
    x = sweep_filter(RS.randn(len(t)), 300, 3000, q=1.5) * np.sin(np.pi * t / dur) ** 2
    return x * 0.5


def sfx_soft_hit():
    t = secs(1.8)
    x = np.zeros(len(t))
    for n in (62, 69, 74, 77):
        x += np.sin(2 * np.pi * midi(n) * t) * np.exp(-t * 2.2)
    x += np.sin(2 * np.pi * 73 * t) * np.exp(-t * 3) * 1.2
    return reverb(x * 0.12, 0.45)


# --------------------------------------------------------------------------------------
# música por segmentos (la rejilla rítmica se reinicia en cada giro del guion)
# --------------------------------------------------------------------------------------
PROG_A = [(50, [62, 65, 69]), (46, [62, 65, 70]), (41, [60, 65, 69]), (48, [60, 64, 67])]  # Dm Bb F C
PROG_B = [(50, [62, 65, 69]), (46, [62, 65, 70]), (43, [62, 67, 70]), (45, [61, 64, 69])]  # Dm Bb Gm A
PROG_F = [(41, [60, 65, 69]), (48, [60, 64, 67]), (50, [62, 65, 69]), (46, [62, 65, 70])]  # F C Dm Bb


def segment(t0, t1, bpm, prog, layers, total, cutoff=2000, energy=1.0):
    """Devuelve buffer estéreo (longitud total) con la música entre t0 y t1."""
    buf = np.zeros((int(total * SR) + SR, 2))
    beat = 60.0 / bpm
    nbeats = int(np.ceil((t1 - t0) / beat)) + 1
    for b in range(nbeats):
        tb = t0 + b * beat
        if tb >= t1:
            break
        bar, pos = divmod(b, 4)
        root, chord = prog[bar % len(prog)]
        if pos == 0 and "pad" in layers:
            place(buf, pad_chord(chord, min(4 * beat, t1 - tb) + 0.4, cutoff=cutoff), tb, 0.9 * energy)
        if "bass" in layers:
            for k in range(2):
                place(buf, bass_note(midi(root - 12 + (12 if (b * 2 + k) % 4 == 3 else 0)), beat / 2 * 0.9,
                                     cutoff=500 + 700 * energy), tb + k * beat / 2, 0.8)
        if "kick" in layers:
            place(buf, kick(), tb, 0.5)
        if "halfkick" in layers and pos in (0, 2):
            place(buf, kick(0.6, 120, 40), tb, 0.5)
        if "snare" in layers and pos in (1, 3):
            place(buf, snare(), tb, 0.35)
        if "hats" in layers:
            for k in range(4 if energy > 0.8 else 2):
                sub = beat / (4 if energy > 0.8 else 2)
                place(buf, pan(hat(), 0.3), tb + k * sub, 0.5 if k % 2 == 0 else 0.3)
        if "arp" in layers:
            seq = chord + [chord[1] + 12, chord[2] + 12]
            for k in range(4):
                n = seq[(b * 4 + k) % len(seq)] + 12
                place(buf, pan(pluck(midi(n)), -0.4 + 0.8 * ((b * 4 + k) % 3) / 2), tb + k * beat / 4, 0.55 * energy)
    i0, i1 = int(t0 * SR), int(t1 * SR)
    out = np.zeros_like(buf)
    out[i0:i1] = buf[i0:i1]
    # micro-fundidos para evitar clics
    f = int(0.008 * SR)
    out[i0:i0 + f] *= np.linspace(0, 1, f)[:, None]
    out[max(i0, i1 - f):i1] *= np.linspace(1, 0, min(f, i1 - i0))[:, None]
    return out


def tape_stop(buf, t_end, dur=0.35):
    """Aplica un "tape stop" al final [t_end-dur, t_end] y silencia después."""
    i1 = int(t_end * SR)
    n = int(dur * SR)
    i0 = i1 - n
    speed = np.linspace(1, 0, n) ** 1.5
    pos = i0 + np.cumsum(speed)
    seg = np.stack([np.interp(pos, np.arange(len(buf)), buf[:, c]) for c in range(2)], 1)
    seg *= np.linspace(1, 0.2, n)[:, None]
    buf[i0:i1] = seg
    return buf


def build_music(tl, total):
    s = tl.s
    n = int(total * SR) + SR
    mus = np.zeros((n, 2))
    # A: gancho + Candelago (crece)
    mus += segment(0.0, s("candelago") - 0.08, 120, PROG_A, {"pad", "bass", "halfkick"}, total, cutoff=1500, energy=0.85)
    mus += segment(s("galicia") - 0.1, s("candelago") - 0.08, 120, PROG_A, {"hats", "arp"}, total, energy=0.75)
    mus += segment(s("candelago") - 0.08, s("espera") - 0.36, 120, PROG_A, {"pad", "bass", "hats", "arp", "kick"}, total, cutoff=1700, energy=0.85)
    mus = tape_stop(mus, s("espera") - 0.36 + 0.02, 0.4)
    # B: Lugo (más energía)
    mus += segment(s("lugo") - 0.05, s("sabes"), 124, PROG_B, {"pad", "bass", "hats", "arp", "kick", "snare"}, total, cutoff=2300, energy=1.0)
    # C: subida hasta "por…" y silencio
    c_end = s("cero") - 0.34
    mus += segment(s("sabes"), c_end, 128, PROG_B, {"pad", "bass", "hats", "kick"}, total, cutoff=2600, energy=1.0)
    # redoble acelerado en C
    t = s("ourense")
    step = 0.25
    while t < c_end - 0.05:
        place(mus, snare(0.12), t, 0.25 + 0.4 * (t - s("ourense")) / max(0.1, c_end - s("ourense")))
        step = max(0.06, step * 0.9)
        t += step
    # D: el "drop" de CERO
    d_end = s("trampa") - 0.34
    mus += segment(s("cero"), d_end, 128, PROG_A, {"pad", "bass", "kick", "hats", "arp"}, total, cutoff=4000, energy=1.1)
    # E: la trampa (oscuro, a medio tiempo) hasta el contraste de Madrid
    mus += segment(s("trampa") + 0.25, s("elegir"), 100, PROG_B, {"pad", "bass", "halfkick", "hats", "arp"}, total, cutoff=1400, energy=0.8)
    # F: CTA resuelto
    mus += segment(s("elegir"), total - 0.2, 100, PROG_F, {"pad", "arp", "bass", "halfkick", "hats"}, total, cutoff=2200, energy=0.8)
    fade = int(1.4 * SR)
    end = int((total - 0.15) * SR)
    mus[end - fade:end] *= np.linspace(1, 0, fade)[:, None]
    mus[end:] = 0
    mus = reverb(mus, 0.12)
    return mus[:int(total * SR)]


def build_sfx(tl, total):
    s, e = tl.s, tl.e
    n = int(total * SR) + 3 * SR
    fx = np.zeros((n, 2))
    place(fx, sfx_boom(), 0.0, 1.0)
    place(fx, sfx_whoosh(1.2), 0.0, 0.9)  # caída desde el espacio
    place(fx, sfx_boom()[: int(0.9 * SR)], 1.22, 0.55)                                                                    # aterrizaje en la azotea
    place(fx, sfx_grow(0.5), 1.72, 0.35)                                                                                   # la planta se levanta
    place(fx, sfx_whoosh(1.3), s("mientras") - 0.05, 0.6)                                                                  # picado sobre Madrid
    place(fx, sfx_whip(), s("galicia") - 0.12, 0.9)
    tc = max(s("galicia") - 0.1 + 1.0, s("pueblo") - 0.42)
    place(fx, sfx_whoosh(0.9), s("galicia") + 0.1, 0.45)          # vuelo sobre el mapa
    place(fx, sfx_whoosh(0.45), tc - 0.35, 0.7)                     # zoom de transición
    place(fx, sfx_boom()[: int(0.7 * SR)], tc, 0.35)
    place(fx, sfx_impact()[: int(1.2 * SR)], s("pueblo"), 0.45)     # UN PUEBLO ENTERO
    # contadores: tic en cada cifra
    for key, dur, nt in (("p150", 0.55, 9), ("p59", 0.5, 8), ("p400", 0.5, 8), ("m23", 0.6, 7), ("nueve", 0.6, 6), ("m60", 0.75, 7)):
        for k in range(nt):
            place(fx, sfx_tick(2400 + 90 * k), s(key) + dur * (k / nt) ** 0.6, 0.5)
    place(fx, sfx_boom()[: int(0.8 * SR)], s("p390"), 0.35)
    place(fx, sfx_shrink(), s("m23"), 0.8)
    place(fx, sfx_whoosh(0.35), s("madrid2") - 0.05, 0.5)
    place(fx, sfx_stop(), s("espera"), 0.9)
    place(fx, sfx_whoosh(0.3), s("lugo") - 0.15, 0.4)
    place(fx, sfx_pop(), s("dos"), 0.5)
    place(fx, sfx_whoosh(0.35), s("loque") - 0.05, 0.45)
    place(fx, sfx_shrink(0.6, 700, 120), s("nueve"), 0.85)
    # casas que se encienden
    for k in range(12):
        place(fx, sfx_tick(1800 + 120 * k), s("doce") + k * 0.08, 0.4)
    r_dur = s("cero") - 0.34 - s("sabes")
    place(fx, sfx_riser(r_dur), s("sabes"), 0.8)
    place(fx, sfx_impact(), s("cero"), 1.0)
    place(fx, sfx_flash(), s("cero"), 0.7)
    place(fx, sfx_pop(), s("cero") + 0.02, 0.6)
    place(fx, sfx_scratch(), s("trampa") - 0.06, 0.85)
    place(fx, sfx_stop()[: int(0.25 * SR)], s("concesion"), 0.35)
    place(fx, sfx_stop()[: int(0.25 * SR)], s("ponerla"), 0.35)
    place(fx, sfx_whoosh(0.4), s("espana") - 0.15, 0.4)
    for k in range(10):
        place(fx, sfx_tick(3000 + 60 * k), s("miles") + k * 0.1, 0.25)
    place(fx, sfx_grow(), s("m60"), 0.8)
    place(fx, sfx_boom()[: int(0.8 * SR)], s("p400"), 0.4)
    place(fx, sfx_whip(0.3), s("elegir") - 0.1, 0.6)
    place(fx, sfx_pop(), s("piso"), 0.35)
    place(fx, sfx_pop(), s("o"), 0.35)
    place(fx, sfx_soft_hit(), total - 1.05, 0.8)
    return fx[:int(total * SR)]


# --------------------------------------------------------------------------------------
# ducking + mezcla
# --------------------------------------------------------------------------------------
def speech_envelope_from_timings(tl, total):
    n = int(total * SR)
    env = np.zeros(n)
    for w in tl.toks:
        env[int(w["start"] * SR):int((w["end"] + 0.12) * SR)] = 1.0
    return env


def speech_envelope_from_voice(voice, thr_db=-38):
    mono = voice.mean(1) if voice.ndim > 1 else voice
    win = int(0.02 * SR)
    rms = np.sqrt(np.convolve(mono ** 2, np.ones(win) / win, "same") + 1e-12)
    return (20 * np.log10(rms) > thr_db).astype(float)


def smooth_env(env, attack=0.04, release=0.28):
    out = np.zeros_like(env)
    a = np.exp(-1 / (attack * SR))
    r = np.exp(-1 / (release * SR))
    y = 0.0
    # versión vectorizada aproximada por bloques de 1 ms
    blk = int(SR / 1000)
    e = env[: len(env) // blk * blk].reshape(-1, blk).max(1)
    ys = np.zeros(len(e))
    ab, rb = a ** blk, r ** blk
    for i, x in enumerate(e):
        y = (ab * y + (1 - ab) * x) if x > y else (rb * y + (1 - rb) * x)
        ys[i] = y
    out[: len(ys) * blk] = np.repeat(ys, blk)
    return out


def limiter(x, ceiling_db=-2.0, lookahead=0.005, release=0.08):
    ceil = 10 ** (ceiling_db / 20)
    # sobremuestreo x4 para aproximar true peak
    peak = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(1).reshape(-1, 4).max(1)[: len(x)]
    need = np.minimum(1.0, ceil / np.maximum(peak, 1e-9))
    la = int(lookahead * SR)
    g = _win_min(need, la)
    out_g = np.zeros_like(g)
    r = np.exp(-1 / (release * SR))
    blk = 48
    gb = g[: len(g) // blk * blk].reshape(-1, blk).min(1)
    yb = np.zeros(len(gb))
    y = 1.0
    for i, v in enumerate(gb):
        y = v if v < y else r ** blk * y + (1 - r ** blk) * v
        yb[i] = y
    out_g[: len(yb) * blk] = np.repeat(yb, blk)
    out_g[len(yb) * blk:] = 1.0
    return x * np.minimum(out_g, g)[:, None]


def _win_min(a, w):
    from scipy.ndimage import minimum_filter1d
    return minimum_filter1d(a, size=2 * w + 1, mode="nearest")


def loudness_normalize(x, target=-14.0):
    import pyloudnorm as pyln
    meter = pyln.Meter(SR)
    for _ in range(6):
        L = meter.integrated_loudness(x)
        if abs(L - target) < 0.05:
            break
        x = x * 10 ** ((target - L) / 20)
        x = limiter(x)
    return x, meter.integrated_loudness(x)


def mix(tl, total, voice=None):
    """Devuelve (mezcla_final, mezcla_sin_voz, lufs_final, lufs_sin_voz)."""
    mus = build_music(tl, total)
    fx = build_sfx(tl, total)
    if voice is not None:
        venv = speech_envelope_from_voice(voice)
        depth_db = -10.0
    else:
        venv = speech_envelope_from_timings(tl, total)
        depth_db = -4.5
    venv = np.pad(venv, (0, max(0, len(mus) - len(venv))))[: len(mus)]
    duck = 10 ** (depth_db * smooth_env(venv) / 20)
    bed = mus * 0.55 * duck[:, None] + fx * 0.8
    no_voice, l_nv = loudness_normalize(bed.copy())
    if voice is None:
        return no_voice, no_voice, l_nv, l_nv
    v = voice if voice.ndim > 1 else np.stack([voice, voice], 1)
    v = np.pad(v, ((0, max(0, len(bed) - len(v))), (0, 0)))[: len(bed)]
    v = hp(v, 80)
    # con voz: música -9 dB y efectos ~-10 dB por debajo de la voz mientras habla
    full = mus * 0.55 * duck[:, None] * 0.55 + fx * 0.8 * 0.4 + v * 1.0
    full, l_f = loudness_normalize(full)
    return full, no_voice, l_f, l_nv
