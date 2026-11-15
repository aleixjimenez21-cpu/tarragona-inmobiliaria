"""
Pista provisional ORIGINAL (120 BPM, La menor) para sincronizar el vídeo
mientras no exista referencia.mp4 / musica.mp3.
Estructura pensada para el guion:
  0.5 golpe "GIVE UP" · 1.5 golpe "?" · 8.0 drop · 10-13 breakdown (3:47 AM)
  13-15.5 riser · 15.5 golpe "GIVE UP?" + hueco · 16.0 IMPACTO "NAH" + drop
  22.0 golpe "NOW" · 24-30 parte épica · 30-32.5 outro
Uso: python3 scripts/synth_placeholder_music.py assets/musica_provisional.wav
"""
import sys
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt

SR = 44100
BPM = 120.0
BEAT = 60.0 / BPM
TOTAL = 34.0
N = int(SR * TOTAL)
rng = np.random.default_rng(7)

L = np.zeros(N)
R = np.zeros(N)


def t_arr(dur):
    return np.arange(int(dur * SR)) / SR


def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    gl = gain * np.cos((pan + 1) * np.pi / 4)
    gr = gain * np.sin((pan + 1) * np.pi / 4)
    L[i : i + len(sig)] += sig * gl
    R[i : i + len(sig)] += sig * gr


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def note(n):  # MIDI -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)


# ---------------- instruments ----------------
def kick(hard=1.0):
    t = t_arr(0.45)
    f = 45 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * (7 - 2 * hard))
    click = hp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 400) * 0.35
    return np.tanh((body + click) * (1.4 + hard))


def clap():
    t = t_arr(0.35)
    n = bp(rng.standard_normal(len(t)), 900, 5000)
    env = np.exp(-t * 18)
    for d in (0.0, 0.012, 0.024):  # flams
        env += 0.6 * np.exp(-np.maximum(t - d, 0) * 120) * (t >= d)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.4
    return (n * env * 0.5 + tone)


def hat(open_=False):
    t = t_arr(0.25 if open_ else 0.06)
    n = hp(rng.standard_normal(len(t)), 7000)
    return n * np.exp(-t * (14 if open_ else 70)) * 0.35


def sub808(n_midi, dur):
    t = t_arr(dur)
    f = note(n_midi) * (1 + 0.6 * np.exp(-t * 40))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.tanh(np.sin(ph) * 2.2 * np.exp(-t * 1.4)) * 0.8


def piano(n_midi, dur=1.6):
    t = t_arr(dur)
    f = note(n_midi)
    s = sum((0.6 ** k) * np.sin(2 * np.pi * f * (k + 1) * t * (1 + 0.0004 * k)) for k in range(6))
    env = np.exp(-t * 2.8) * (1 - np.exp(-t * 300))
    return s * env * 0.25


def pad(midis, dur, bright=1200):
    t = t_arr(dur)
    s = np.zeros(len(t))
    for m in midis:
        for det in (-0.12, 0.0, 0.11):
            f = note(m + det)
            s += 2 * ((f * t + rng.random()) % 1.0) - 1  # saw
    s = lp(s, bright, 2) / (len(midis) * 3)
    a = np.minimum(t / 0.35, 1.0) * np.minimum((dur - t) / 0.3, 1.0)
    return s * np.clip(a, 0, 1) * 0.55


def impact(size=1.0):
    t = t_arr(2.5)
    boom = np.sin(2 * np.pi * (38 + 60 * np.exp(-t * 10)) * t) * np.exp(-t * 2.2)
    noise = lp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 6) * 0.5
    return np.tanh((boom + noise) * 1.8 * size)


def riser(dur):
    t = t_arr(dur)
    x = t / dur
    n = rng.standard_normal(len(t))
    out = np.zeros(len(t))
    # crude sweeping filter: blocks of increasing cutoff
    blocks = 40
    for b in range(blocks):
        a, z = int(len(t) * b / blocks), int(len(t) * (b + 1) / blocks)
        fc = 300 + 9000 * (b / blocks) ** 2
        out[a:z] = bp(n, fc * 0.6, min(fc * 1.6, 18000))[a:z]
    tone = np.sin(2 * np.pi * np.cumsum(200 + 900 * x**2) / SR) * 0.25
    return (out * 0.5 + tone) * x**2


def reverse_cymbal(dur):
    t = t_arr(dur)
    n = hp(rng.standard_normal(len(t)), 5000)
    return n * (t / dur) ** 3 * 0.5


# ---------------- arrangement ----------------
# Am - F - C - G (1 compás = 4 beats = 2 s)
PROG = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [55, 60, 64]), (55, [55, 59, 62])]
BASS = [45, 41, 36, 43]


def chord_at(sec):
    return int(sec // 2.0) % 4


def beat_times(a, b, step=BEAT):
    k = np.arange(np.ceil(a / step - 1e-9), np.floor((b - 1e-9) / step) + 1)
    return [float(x * step) for x in k if a - 1e-9 <= x * step < b - 1e-9]


# intro swell -> 0.5 hit
add(reverse_cymbal(0.5), 0.0, 0.6)
for tt, g in ((0.5, 0.9), (1.5, 1.0)):
    add(impact(0.8), tt, 0.7)

# pads everywhere except gaps
for bar in range(17):
    s = bar * 2.0
    if 15.5 <= s < 16.0:
        continue
    root, ch = PROG[bar % 4]
    bright = 900 if s < 8 else (600 if 10 <= s < 13 else 1800)
    dur = 2.0 if not (14.0 <= s < 16.0) else 1.5
    add(pad([m + 12 for m in ch], dur, bright), s, 0.45 if s < 22 else 0.6, 0)

# piano arps (8ths) on build & breakdown & epic part
for tt in beat_times(0.5, 32.0, BEAT / 2):
    if 15.5 <= tt < 16.0:
        continue
    root, ch = PROG[chord_at(tt)]
    idx = int(round(tt / (BEAT / 2))) % 4
    seq = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 24]
    g = 0.5 if (10 <= tt < 13) else 0.32
    add(piano(seq[idx]), tt, g, pan=(-0.3 if idx % 2 else 0.3))

# drums
for tt in beat_times(0.5, 32.0):
    if 15.75 <= tt < 16.0:
        continue
    section_hard = 1.0 if (8 <= tt < 10 or 16 <= tt < 30) else 0.4
    if 10 <= tt < 13:
        add(kick(0.2), tt, 0.45)  # muffled heartbeat kick in breakdown
    else:
        add(kick(section_hard), tt, 0.85)
    bi = int(round(tt / BEAT))
    if bi % 2 == 1 and not (10 <= tt < 13) and tt >= 2.0:
        add(clap(), tt, 0.55)
for tt in beat_times(2.0, 32.0, BEAT / 2):
    if (10 <= tt < 13) or (15.5 <= tt < 16.0):
        continue
    off = abs((tt / BEAT) % 1 - 0.5) < 1e-6
    add(hat(open_=off and tt >= 16), tt, 0.5 if off else 0.3, pan=0.2)

# extra 8th-note accents (word cues "MORE / CHEST." etc.)
for tt in (5.75, 17.75, 23.75, 29.75):
    add(clap(), tt, 0.45)

# 808 bass on drops
for tt in beat_times(8.0, 30.0, 2 * BEAT):
    if 10 <= tt < 13 or 15.5 <= tt < 16.0:
        continue
    add(sub808(BASS[chord_at(tt)], 0.95), tt, 0.7)

# riser into 15.5, snare roll accelerating 14.5-15.5
add(riser(2.5), 13.0, 0.5)
roll = beat_times(14.5, 15.5, BEAT / 4)
for i, tt in enumerate(roll):
    add(clap(), tt, 0.2 + 0.4 * i / len(roll))
add(impact(0.9), 15.5, 0.6)  # GIVE UP?
add(reverse_cymbal(0.5), 15.5, 0.8)

# big hits
for tt, s in ((16.0, 1.4), (22.0, 1.2), (24.0, 0.9), (28.0, 0.8), (30.0, 1.0)):
    add(impact(s), tt, 0.8)
for tt in (2.0, 4.0, 13.0, 14.5, 18.0, 20.0, 26.0):
    add(impact(0.5), tt, 0.35)
add(riser(2.0), 20.0, 0.35)
add(riser(2.0), 26.0, 0.4)

# outro: final chord ring
add(pad([69, 72, 76, 81], 3.0, 1400), 30.0, 0.5)
add(piano(57, 3.5), 30.0, 0.6)
add(piano(64, 3.5), 30.0, 0.5)

# ---------------- mix / master ----------------
ir_t = t_arr(1.6)
ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 3.5)
ir /= np.sqrt(np.sum(ir**2))
wetL = fftconvolve(L, ir)[:N] * 0.18
wetR = fftconvolve(R, np.roll(ir, 37))[:N] * 0.18
L2, R2 = L + wetL, R + wetR
mx = np.stack([L2, R2], axis=1)
mx = np.tanh(mx / np.max(np.abs(mx)) * 2.2) * 0.9
fade = np.ones(N)
fs = int(32.0 * SR)
fade[fs:] = np.linspace(1, 0, N - fs)
mx *= fade[:, None]

import soundfile as sf

out = sys.argv[1] if len(sys.argv) > 1 else "assets/musica_provisional.wav"
sf.write(out, mx.astype(np.float32), SR)
print("written", out, f"{TOTAL}s")
