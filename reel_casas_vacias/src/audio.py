"""Banda sonora de LA MAQUETA, sintetizada desde cero (material original, CC0).

- Piano grave minimalista con pulso tenso (Re menor), reverberación de estudio.
- Efectos táctiles: cristal, golpes de cartón, grafito, foco, cúter, grúa...
- Silencios del storyboard, ducking bajo la voz (si existe input/voz.wav).
- Mezcla a -14 LUFS integrados, pico real <= -1 dBTP.

Salida: output/audio_sin_voz.wav y output/audio_con_voz.wav (si hay voz).
"""
import os, json, math, glob, random
import numpy as np
import soundfile as sf
import pyloudnorm as pyln
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TM = json.load(open(os.path.join(ROOT, 'output', 'timings.json')))
SR = 48000
DUR = TM['duration']
N = int(DUR * SR) + SR
rng = np.random.default_rng(11)


def W(word, n=1, k='s'):
    import unicodedata, re
    def nn(w):
        w = unicodedata.normalize('NFD', w.lower())
        return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))
    c = 0
    for w in TM['words']:
        if nn(w['w']) == nn(word):
            c += 1
            if c == n:
                return w[k]
    raise KeyError(word)


def meta(shot):
    for q in ('final', 'still', 'preview'):
        p = os.path.join(ROOT, 'renders', shot, q, 'meta.json')
        if os.path.exists(p):
            return json.load(open(p))['events']
    return {}


def buf():
    return np.zeros((N, 2), np.float32)


def place(dst, x, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= len(dst) or i + len(x) <= 0:
        return
    if x.ndim == 1:
        l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
        x = np.stack([x * l * 1.414, x * r * 1.414], 1)
    j0 = max(0, -i)
    n = min(len(x) - j0, len(dst) - max(i, 0))
    dst[max(i, 0):max(i, 0) + n] += x[j0:j0 + n] * gain


def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def lp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), 'low')
    return signal.lfilter(b, a, x, axis=0)


def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), 'high')
    return signal.lfilter(b, a, x, axis=0)


def bp(x, f1, f2, order=2):
    b, a = signal.butter(order, [f1 / (SR / 2), f2 / (SR / 2)], 'band')
    return signal.lfilter(b, a, x, axis=0)

# ------------------------------------------------------------------ piano


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def piano(m, dur, vel=0.5):
    f = midi(m)
    L = int((dur + 2.5) * SR)
    t = np.arange(L) / SR
    out = np.zeros(L, np.float32)
    B = 0.00012 * (f / 110) ** 0.5
    tau0 = 3.2 * (110 / f) ** 0.35
    for n in range(1, 13):
        fn = n * f * math.sqrt(1 + B * n * n)
        if fn > 9000:
            break
        a = vel * n ** -1.25 * (1.0 if n > 1 else 1.2)
        if n == 1 and f < 80:
            a *= 0.8
        tau = tau0 / (1 + 0.55 * (n - 1))
        e = 0.65 * np.exp(-t / (tau * 0.25)) + 0.35 * np.exp(-t / tau)
        for det in (-0.6, 0.6):
            ph = rng.uniform(0, 2 * math.pi)
            out += (a * 0.5 * e * np.sin(2 * math.pi * fn * (1 + det / 1730) * t + ph)).astype(np.float32)
    # martillo
    hn = int(0.012 * SR)
    ham = rng.standard_normal(hn) * np.exp(-np.arange(hn) / (0.003 * SR)) * vel * 0.25
    out[:hn] += lp(ham, min(4000, f * 8))
    # apagado
    rel = int(dur * SR)
    if rel < L:
        out[rel:] *= np.exp(-np.arange(L - rel) / (0.18 * SR))
    att = int(0.003 * SR)
    out[:att] *= np.linspace(0, 1, att)
    return out


def reverb_ir(rt=2.4, pre=0.02):
    n = int(rt * SR)
    ir = np.zeros((n + int(pre * SR), 2), np.float32)
    for c in range(2):
        x = rng.standard_normal(n) * np.exp(-6.9 * np.arange(n) / n)
        x = lp(x, 5200)
        ir[int(pre * SR):, c] = x
    ir /= np.abs(ir).sum(0).max() ** 0.5 * 6
    return ir


def apply_reverb(x, ir, wet=0.28):
    y = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[:len(x)] for c in range(2)], 1)
    return x * (1 - wet * 0.4) + y * wet


def music():
    m = buf()
    bpm = 92.0
    beat = 60 / bpm
    bar = beat * 4
    # progresión (2 compases cada acorde): Dm, Bb, Gm, A
    prog = [([38, 50], [62, 65, 69]), ([34, 46], [58, 62, 65]), ([31, 43], [55, 58, 62]), ([33, 45], [57, 61, 64])]
    t = 0.0
    k = 0
    motif = [69, 65, 64, 62, 69, 70, 69, 65]
    while t < DUR + 2:
        bass, chord = prog[(k // 2) % 4]
        # pulso tenso: corcheas en el bajo, acento en 1 y 3
        for i in range(8):
            tt = t + i * beat / 2
            v = 0.34 if i in (0, 4) else (0.2 if i % 2 == 0 else 0.13)
            place(m, piano(bass[1] if i % 2 else bass[0] + 12, beat * 0.45, v), tt, 0.55)
        if k % 2 == 0:
            for j, n in enumerate(chord):
                place(m, piano(n, bar * 2 - 0.1, 0.16), t + j * 0.012, 0.5, pan=(j - 1) * 0.35)
            place(m, piano(bass[0], bar * 2, 0.32), t, 0.6)
        # motivo agudo esporádico
        if k % 2 == 1:
            place(m, piano(motif[(k // 2) % len(motif)] + 12, beat * 1.5, 0.12), t + beat * 2.5, 0.45, pan=0.3)
        t += bar
        k += 1
    return m


def music_gain():
    """Envolvente de la música: silencios, intensidad, final."""
    g = np.ones(N, np.float32)
    t = np.arange(N) / SR

    def dip(a, b, fade_in=0.04, fade_out=0.25, floor=0.0):
        nonlocal g
        e = np.ones(N, np.float32)
        e[(t >= a) & (t < b)] = floor
        m1 = (t >= a - fade_in) & (t < a)
        e[m1] = 1 - (1 - floor) * (t[m1] - (a - fade_in)) / fade_in
        m2 = (t >= b) & (t < b + fade_out)
        e[m2] = floor + (1 - floor) * (t[m2] - b) / fade_out
        g *= e
    S = TM['sentences']
    dip(S[1]['e'] + 0.02, S[2]['s'] - 0.02, 0.05, 0.5)        # silencio antes de «¿Cómo…?»
    dip(S[7]['e'] + 0.15, S[8]['s'] - 0.05, 0.08, 0.6)        # silencio y golpe sordo antes de la pregunta final
    # crece en las provincias y en el problema
    ramp = np.interp(t, [0, S[4]['s'], S[5]['s'], S[6]['s'], S[7]['s'], DUR - 2.4, DUR - 0.8, DUR],
                     [0.85, 0.9, 1.0, 1.08, 1.0, 0.95, 0.5, 0.0])
    return g * ramp

# ------------------------------------------------------------------ efectos


def tink(f0=None, dur=0.35, amp=0.2):
    f0 = f0 or rng.uniform(2600, 6500)
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for r, a, tau in ((1, 1, dur * .5), (2.32, .5, dur * .3), (4.25, .3, dur * .18), (5.4, .2, dur * .12)):
        if f0 * r < 18000:
            x += a * np.sin(2 * math.pi * f0 * r * t) * np.exp(-t / tau)
    x[:48] *= np.linspace(0, 1, 48)
    return (x * amp).astype(np.float32)


def boom(dur=1.6, amp=0.9):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 55 * np.exp(-t * 0.8) + 30
    ph = 2 * math.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t / 0.55)
    x += lp(rng.standard_normal(n), 180) * np.exp(-t / 0.08) * 0.6
    x[:96] *= np.linspace(0, 1, 96)
    return (x * amp).astype(np.float32)


def card_thud(amp=0.6, pitch=1.0):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for f, a, tau in ((95, 1.0, .07), (170, .6, .05), (265, .35, .035), (410, .2, .02)):
        x += a * np.sin(2 * math.pi * f * pitch * t) * np.exp(-t / tau)
    nz = lp(rng.standard_normal(n), 1600) * np.exp(-t / 0.012) * 0.9
    click = hp(rng.standard_normal(n), 2500) * np.exp(-t / 0.002) * 0.25
    x = x + nz + click
    return (x * amp / np.abs(x).max()).astype(np.float32)


def paper_tap(amp=0.25):
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 900, 5000) * np.exp(-t / 0.01) + np.sin(2 * math.pi * 320 * t) * np.exp(-t / 0.02) * 0.4
    return (x * amp / np.abs(x).max()).astype(np.float32)


def pencil(dur, amp=0.2, density=9.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    base = bp(rng.standard_normal(n), 1800, 7500)
    grit = (rng.random(n) < 0.02) * rng.standard_normal(n) * 1.5
    x = base + hp(grit, 3000)
    e = np.zeros(n)
    tt = 0
    while tt < dur:
        L = rng.uniform(0.06, 0.2)
        a = rng.uniform(0.5, 1.0)
        i0 = int(tt * SR); i1 = min(n, int((tt + L) * SR))
        seg = np.sin(np.linspace(0, math.pi, i1 - i0)) ** 0.6 * a
        e[i0:i1] = np.maximum(e[i0:i1], seg)
        tt += L * rng.uniform(0.8, 1.3) + 1 / density * rng.uniform(0, 0.6)
    e = lp(e, 60)
    x = x * e
    return (x * amp / (np.abs(x).max() + 1e-9)).astype(np.float32)


def whoosh(dur=0.7, amp=0.35, f0=300, f1=2600):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    out = np.zeros(n)
    blk = 1024
    for i in range(0, n, blk):
        u = i / n
        fc = f0 * (f1 / f0) ** u
        seg = x[max(0, i - 2048):i + blk]
        y = bp(seg, fc * 0.6, min(fc * 1.6, 20000))
        out[i:i + blk] = y[-len(out[i:i + blk]):]
    e = np.sin(np.linspace(0, math.pi, n)) ** 1.5
    out = out * e
    return (out * amp / np.abs(out).max()).astype(np.float32)


def light_clack(amp=0.35):
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    click = hp(rng.standard_normal(n), 3000) * np.exp(-t / 0.003)
    thunk = np.sin(2 * math.pi * 85 * t) * np.exp(-t / 0.05)
    hum = (np.sin(2 * math.pi * 100 * t) + .4 * np.sin(2 * math.pi * 200 * t)) * np.exp(-t / 0.25) * 0.08
    x = click * 0.5 + thunk + hum
    return (x * amp / np.abs(x).max()).astype(np.float32)


def cutter(amp=0.5, dur=0.45):
    n = int(dur * SR)
    t = np.arange(n) / SR
    snick = hp(rng.standard_normal(n), 4000) * np.exp(-t / 0.004) * 1.2
    slide = bp(rng.standard_normal(n), 3000, 11000) * np.clip(t / 0.05, 0, 1) * np.exp(-np.clip(t - 0.25, 0, None) / 0.06)
    crack = (rng.random(n) < 0.004) * rng.standard_normal(n) * 3
    x = snick + slide * 0.7 + hp(crack, 1500) * 0.4
    return (x * amp / np.abs(x).max()).astype(np.float32)


def motor(dur, amp=0.08):
    n = int(dur * SR)
    t = np.arange(n) / SR
    saw = signal.sawtooth(2 * math.pi * 118 * t) * (0.6 + 0.4 * np.sin(2 * math.pi * 7 * t))
    x = lp(saw, 900) + bp(rng.standard_normal(n), 400, 1800) * 0.2
    e = np.clip(t / 0.15, 0, 1) * np.clip((dur - t) / 0.2, 0, 1)
    return (x * e * amp / np.abs(x).max()).astype(np.float32)


def swell(amp=0.18, dur=2.2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for f in (587.3, 740.0, 880.0, 1174.7):
        x += np.sin(2 * math.pi * f * t + rng.uniform(0, 6)) / (1 + f / 900)
    e = np.clip(t / 0.7, 0, 1) ** 2 * np.exp(-np.clip(t - 0.7, 0, None) / 0.5)
    return (x * e * amp / np.abs(x).max()).astype(np.float32)


def sordo(amp=0.9):
    n = int(2.0 * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * math.pi * (42 + 10 * np.exp(-t * 6)) * t) * np.exp(-t / 0.6)
    x += lp(rng.standard_normal(n), 220) * np.exp(-t / 0.05) * 0.8
    return (x * amp / np.abs(x).max()).astype(np.float32)


def sfx():
    s = buf()
    S = TM['sentences']
    eA, eB, eC, eD = meta('A_hook'), meta('B_contraste'), meta('C_pregunta'), meta('D_ourense')
    eE, eF, eG, eH = meta('E_provincias'), meta('F_pueblos'), meta('G_sintesis'), meta('H_dilema')
    # A: ola de cristal + golpe grave + cifras
    tg = eA.get('glass', W('España') + 0.1)
    place(s, boom(), tg - 0.02, 0.85)
    for i in range(90):
        dt = abs(rng.normal(0, 0.35)) + rng.uniform(0, 0.08)
        place(s, tink(amp=rng.uniform(0.04, 0.12) * (1.3 - min(dt, 1.2) * 0.6)), tg + dt, 1.0, pan=rng.uniform(-.8, .8))
    for k, ti in enumerate(eA.get('impacts', [])):
        place(s, card_thud(0.75 if k == 0 else 0.45, rng.uniform(.9, 1.1)), ti, 1.0, pan=(k - 4) * 0.08)
    for ti in eA.get('pop', []):
        place(s, paper_tap(0.3), ti + 0.12, 1.0)
    # B: grafito + letras que se levantan
    if eB.get('pencil'):
        a, b = eB['pencil']
        place(s, pencil(b - a + 0.2, 0.32), a, 1.0, pan=-0.15)
        place(s, pencil(b - a, 0.18), a + 0.13, 1.0, pan=0.25)
    for k, ti in enumerate(eB.get('rise', [])):
        place(s, card_thud(0.35, 1.3), ti, 1.0, pan=(k - 3) * 0.1)
    # C: grúa rápida + ¿CÓMO?
    place(s, whoosh(0.75, 0.3, 250, 2200), eC.get('whoosh', SHOT('C_pregunta') + 0.05), 1.0)
    for k, ti in enumerate(eC.get('impacts', [])):
        place(s, card_thud(0.7 if k == 0 else 0.35, 0.9), ti, 1.0)
    # D: picado, foco, cota a lápiz, +40 %
    place(s, whoosh(1.1, 0.25, 2400, 300), SHOT('D_ourense') + 0.05, 1.0)
    if eD.get('spot'):
        place(s, light_clack(0.5), eD['spot'], 1.0)
    if eD.get('pencil'):
        a, b = eD['pencil']
        place(s, pencil(b - a, 0.3, density=4), a, 1.0)
    for k, ti in enumerate(eD.get('impacts', [])):
        place(s, card_thud(0.8 if k == 0 else 0.4), ti, 1.0)
    for i in range(14):
        place(s, tink(rng.uniform(4000, 7000), 0.6, 0.03), W('vacías', 2) + rng.uniform(0, 0.8), 1.0, pan=rng.uniform(-.6, .6))
    # E: cada provincia, foco + golpe
    for k, ti in enumerate(eE.get('spots', [])):
        place(s, light_clack(0.42), ti, 1.0, pan=(k - 2.5) * 0.2)
    for k, ti in enumerate(eE.get('impacts', [])):
        place(s, card_thud(0.55, 1.0 + 0.04 * (k % 6)), ti, 1.0)
    # F: pueblos — aire, cifras, rótulos
    for k, ti in enumerate(eF.get('impacts', [])):
        place(s, card_thud(0.7 if k == 0 else 0.4), ti, 1.0)
    for ti in eF.get('pops', []):
        place(s, paper_tap(0.25), ti, 1.0)
    air = lp(rng.standard_normal(int(6 * SR)), 900) * 0.012
    place(s, air.astype(np.float32), SHOT('F_pueblos'), 1.0)
    # G: líneas de lápiz que no llegan + golpe sordo
    if eG.get('pencil'):
        a, b = eG['pencil']
        place(s, pencil(b - a, 0.28, density=6), a, 1.0, pan=-0.2)
        place(s, pencil(b - a - 0.3, 0.2, density=5), a + 0.3, 1.0, pan=0.3)
    place(s, sordo(0.95), eG.get('thud', S[7]['e'] + 0.1), 1.0)
    # H: cúter, separación, grúa, recuperar
    if eH:
        place(s, cutter(0.6), eH['cut'] - 0.1, 1.0)
        place(s, card_thud(0.4, 0.7), eH['open'] - 0.05, 1.0)
        place(s, motor(1.4, 0.07), eH['crane'], 1.0, pan=-0.4)
        place(s, card_thud(0.45, 1.2), eH['crane'] + 1.4, 1.0, pan=-0.4)
        place(s, swell(0.2), eH['recover'] - 0.3, 1.0, pan=0.35)
        for i in range(6):
            place(s, tink(rng.uniform(3000, 5000), 0.5, 0.04), eH['recover'] + 0.1 * i, 1.0, pan=0.4)
    # CTA
    place(s, card_thud(0.35, 0.8), S[8]['e'] + 0.15, 1.0)
    return s


def SHOT(name):
    for s in TM['shots']:
        if s['name'] == name:
            return s['start']
    return 0.0


def limiter(x, ceil_db=-1.2):
    ceil = 10 ** (ceil_db / 20)
    # pico real aproximado con sobremuestreo x4
    up = signal.resample_poly(x, 4, 1, axis=0)
    env = np.abs(up).max(1)
    env = env.reshape(-1, 4).max(1)[:len(x)]
    g = np.minimum(1.0, ceil / np.maximum(env, 1e-9))
    # suavizado: ataque instantáneo (mínimo móvil), relajación 80 ms
    win = int(0.004 * SR)
    g = -signal.convolve(-g, np.ones(1), mode='same')
    from scipy.ndimage import minimum_filter1d
    g = minimum_filter1d(g, win)
    a = math.exp(-1 / (0.08 * SR))
    out = np.empty_like(g)
    cur = 1.0
    for i in range(len(g)):
        cur = g[i] if g[i] < cur else a * cur + (1 - a) * g[i]
        out[i] = cur
    return x * out[:, None]


def master(x, target=-14.0):
    meter = pyln.Meter(SR)
    for _ in range(6):
        l = meter.integrated_loudness(x)
        x = x * 10 ** ((target - l) / 20)
        x = limiter(x)
    return x, meter.integrated_loudness(x)


def main():
    voz_p = os.path.join(ROOT, 'input', 'voz.wav')
    ir = reverb_ir()
    mus = music() * music_gain()[:, None]
    mus = apply_reverb(mus, ir, 0.3)
    fx = sfx()
    fx = apply_reverb(fx, reverb_ir(1.2, 0.01), 0.18)
    voice = None
    if os.path.exists(voz_p):
        v, sr = sf.read(voz_p, always_2d=True)
        if sr != SR:
            v = signal.resample_poly(v, SR, sr, axis=0)
        v = v.mean(1)
        v = hp(v, 80)
        voice = np.zeros(N, np.float32)
        voice[:min(N, len(v))] = v[:N]
        # ducking: envolvente de la voz
        e = np.abs(voice)
        e = signal.lfilter([1 - math.exp(-1 / (0.25 * SR))], [1, -math.exp(-1 / (0.25 * SR))], e)
        e = e / (e.max() + 1e-9)
        duck = 1 - 0.72 * np.clip(e * 4, 0, 1)
        mus_d = mus * duck[:, None]
    n = int(DUR * SR)
    # fundido de las colas al final del bucle
    fade = np.ones(n, np.float32)
    fade[-int(0.25 * SR):] = np.linspace(1, 0, int(0.25 * SR))
    os.makedirs(os.path.join(ROOT, 'output'), exist_ok=True)
    mix = (mus * 0.55 + fx * 0.9)[:n] * fade[:, None]
    mix, lufs = master(mix)
    sf.write(os.path.join(ROOT, 'output', 'audio_sin_voz.wav'), mix, SR, subtype='PCM_24')
    print('audio sin voz: %.2f LUFS' % lufs)
    if voice is not None:
        vm = np.stack([voice, voice], 1)
        mix = (mus_d * 0.42 + fx * 0.7 + vm * 1.0)[:n] * fade[:, None]
        mix, lufs = master(mix)
        sf.write(os.path.join(ROOT, 'output', 'audio_con_voz.wav'), mix, SR, subtype='PCM_24')
        print('audio con voz: %.2f LUFS' % lufs)


if __name__ == '__main__':
    main()
