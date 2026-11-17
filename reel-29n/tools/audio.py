#!/usr/bin/env python3
"""Diseño sonoro sintetizado (sin muestras de terceros) + mezcla a -14 LUFS.

Todo el sonido se genera aquí con numpy/scipy: dron grave, sello de lacre,
papel, tecleo, reloj, barridos y golpes. Los sonidos de las 5 propuestas y de
las 5 revelaciones son LA MISMA muestra (neutralidad).

Uso: python3 tools/audio.py [input/voz.wav]
Salida: build/audio/mezcla_con_voz.wav, build/audio/mezcla_sin_voz.wav
"""
import json, os, sys
import numpy as np
from scipy import signal
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
VOICE_DB = -7.0   # nivel de la voz en la mezcla
SFX_DB = 7.0      # nivel de los efectos de sonido
RNG = np.random.default_rng(29)


def t_(d):
    return np.arange(int(d * SR)) / SR


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="high", fs=SR, output="sos"), x)


def noise(d):
    return RNG.standard_normal(int(d * SR))


def env_ad(n, a, d, curve=4.0):
    """envolvente ataque (s) + caída exponencial (s)"""
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-4), np.exp(-(t - a) / max(d, 1e-4) * 1.0))
    return e


def norm(x, peak=1.0):
    m = np.max(np.abs(x)) + 1e-9
    return x / m * peak


def stereo(x, width=0.0, pan=0.0):
    l = x * np.sqrt(0.5 * (1 - pan))
    r = x * np.sqrt(0.5 * (1 + pan))
    if width > 0:
        d = int(0.011 * SR)
        r = np.concatenate([np.zeros(d), r])[: len(x)] * (1 - width) + r * width
    return np.stack([l, r], axis=1)


# ------------------------------------------------------------------ efectos
def sfx_seal_whoosh(d=0.62):
    n = noise(d + 0.1)
    tt = t_(d + 0.1)
    out = np.zeros_like(n)
    # barrido de filtro ascendente lento (cámara lenta)
    for k, (f0, f1) in enumerate([(150, 900)]):
        seg = 64
        for i in range(0, len(n), len(n) // seg):
            j = min(len(n), i + len(n) // seg)
            u = i / len(n)
            f = f0 + (f1 - f0) * u ** 2
            out[i:j] = bp(n, f * 0.6, f * 1.6)[i:j]
    e = (tt / (d + 0.1)) ** 2.2
    return norm(out * e, 0.25)


def sfx_riser(d):
    """Subida de tensión hasta el impacto (ruido + tono ascendentes que se cortan en seco)."""
    tt = t_(d)
    u = tt / d
    n = noise(d)
    out = np.zeros_like(n)
    seg = 40
    L = len(n)
    for i in range(seg):
        a, b = i * L // seg, (i + 1) * L // seg
        f = 400 + 5200 * (i / seg) ** 2
        out[a:b] = bp(n, f * 0.7, f * 1.4)[a:b]
    f = 80 + 140 * u ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5
    e = u ** 2.5
    return norm((out * 0.7 + tone) * e, 0.6)


def sfx_switch():
    d = 0.25
    tt = t_(d)
    click = hp(noise(d), 2500) * np.exp(-tt * 260)
    body = bp(noise(d), 300, 2000) * np.exp(-tt * 60) * 0.7
    thunk = np.sin(2 * np.pi * 95 * tt) * np.exp(-tt * 35) * 0.8
    return norm(click + body + thunk, 0.7)


def sfx_hum(d):
    tt = t_(d)
    x = sum(np.sin(2 * np.pi * 50 * k * tt) / k for k in (1, 2, 3, 4)) * 0.4
    x += bp(noise(d), 2000, 6000) * 0.05
    e = np.minimum(1, tt / 0.05) * np.exp(-tt * 1.5)
    return norm(x * e, 0.4)


def sfx_seal_hit():
    d = 2.2
    tt = t_(d)
    f = 38 + 70 * np.exp(-tt * 18)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-tt * 3.2)
    sub = np.sin(2 * np.pi * 31 * tt) * np.exp(-tt * 1.6) * 0.6
    slap = bp(noise(d), 250, 2400) * np.exp(-tt * 45) * 0.9
    crack = hp(noise(d), 3000) * np.exp(-tt * 120) * 0.35
    room = lp(noise(d), 400) * np.exp(-tt * 2.2) * 0.12
    x = body * 1.0 + sub + slap + crack + room
    return norm(np.tanh(x * 1.4), 0.95)


def sfx_paper_slide(d=0.75, bright=1.0):
    n = noise(d)
    tt = t_(d)
    x = bp(n, 900, 6500) * 0.6 + bp(n, 2500, 9000) * 0.4 * bright
    # textura granular de fibras
    grains = (RNG.random(len(n)) < 0.004).astype(float) * RNG.standard_normal(len(n))
    grains = bp(grains, 1500, 7000) * 3
    e = np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 1.6
    return norm((x + grains) * e, 0.5)


def sfx_paper_land():
    d = 0.35
    tt = t_(d)
    thump = np.sin(2 * np.pi * (120 + 80 * np.exp(-tt * 40)) * tt) * np.exp(-tt * 28)
    rustle = bp(noise(d), 1200, 6000) * np.exp(-tt * 30)
    return norm(thump * 0.8 + rustle * 0.5, 0.55)


def sfx_whoosh_light(d=0.84):
    n = noise(d)
    tt = t_(d)
    out = np.zeros_like(n)
    seg = 48
    L = len(n)
    for i in range(seg):
        a, b = i * L // seg, (i + 1) * L // seg
        u = i / seg
        f = 300 + 2200 * np.sin(np.pi * u) ** 2
        out[a:b] = bp(n, f * 0.5, f * 1.5)[a:b]
    e = np.sin(np.pi * tt / d) ** 2
    air = lp(n, 220) * e * 0.5
    return norm(out * e + air, 0.35)


def typing_bed(d=2.6, seed=7):
    """Tecleo suave: patrón fijo (idéntico para las cinco propuestas)."""
    r = np.random.default_rng(seed)
    out = np.zeros(int((d + 0.3) * SR))
    t = 0.05
    while t < d:
        n = int(0.06 * SR)
        tt = np.arange(n) / SR
        click = hp(r.standard_normal(n), 2500) * np.exp(-tt * 260) * 0.6
        body = (np.sin(2 * np.pi * 2100 * tt) * 0.25 + np.sin(2 * np.pi * 820 * tt) * 0.35) * np.exp(-tt * 90)
        thock = np.sin(2 * np.pi * 180 * tt) * np.exp(-tt * 70) * 0.5
        hit = (click + body + thock) * (0.6 + 0.4 * r.random())
        i = int(t * SR)
        out[i:i + n] += hit[: len(out) - i]
        t += 0.085 + r.random() * 0.06 + (0.12 if r.random() < 0.12 else 0)
    return norm(out, 0.32)


def sfx_clock(kind):
    d = 0.18
    tt = t_(d)
    f1, f2 = (3400, 1700) if kind == 0 else (2700, 1350)
    x = (np.sin(2 * np.pi * f1 * tt) * 0.5 + np.sin(2 * np.pi * f2 * tt) * 0.5) * np.exp(-tt * 70)
    x += hp(noise(d), 4000) * np.exp(-tt * 300) * 0.5
    x += np.sin(2 * np.pi * 420 * tt) * np.exp(-tt * 40) * 0.3
    return norm(x, 0.42)


def sfx_reveal_hit():
    d = 1.4
    tt = t_(d)
    f = 46 + 50 * np.exp(-tt * 22)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 4.5)
    knock = bp(noise(d), 120, 900) * np.exp(-tt * 38) * 0.8
    paper = bp(noise(d), 1500, 6000) * np.exp(-tt * 55) * 0.35
    return norm(np.tanh((body + knock + paper) * 1.3), 0.8)


def sfx_light_off():
    d = 1.6
    tt = t_(d)
    clunk = bp(noise(d), 200, 1800) * np.exp(-tt * 40) * 0.8 + np.sin(2 * np.pi * 70 * tt) * np.exp(-tt * 9) * 0.7
    tail = lp(noise(d), 300) * np.exp(-tt * 3) * 0.15
    return norm(clunk + tail, 0.6)


def drone(total):
    tt = t_(total)
    n = len(tt)
    x = np.zeros(n)
    # capas tonales graves con batido lento (re menor, sin resolución)
    for f, a in [(36.71, 0.6), (36.83, 0.18), (55.0, 0.35), (73.42, 0.24), (73.55, 0.08), (110.0, 0.06)]:
        lfo = 1 + 0.15 * np.sin(2 * np.pi * (0.05 + f * 0.0007) * tt + f)
        x += np.sin(2 * np.pi * f * tt + 3 * np.sin(2 * np.pi * 0.03 * tt)) * a * lfo
    # sierra filtrada (cuerdas graves sintéticas)
    saw = signal.sawtooth(2 * np.pi * 36.71 * tt) * 0.3 + signal.sawtooth(2 * np.pi * 55.07 * tt) * 0.2
    x += lp(saw, 180, 4) * 0.8
    # aire / ruido marrón
    br = np.cumsum(RNG.standard_normal(n)); br = hp(br, 20); br = lp(br, 260)
    x += norm(br, 0.25) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.07 * tt))
    # brillo tenso muy bajo
    sh = np.sin(2 * np.pi * 1174.7 * tt) * 0.012 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * tt)) + np.sin(2 * np.pi * 1760.0 * tt) * 0.006
    x += sh
    return norm(x, 0.5)


# ------------------------------------------------------------------ mezcla
def place(bus, x, t, gain=1.0, pan=0.0, width=0.0):
    if t < 0:
        return
    s = x if x.ndim == 2 else stereo(x, width, pan)
    i = int(round(t * SR))
    j = min(len(bus), i + len(s))
    if j > i:
        bus[i:j] += s[: j - i] * gain


def db(x):
    return 10 ** (x / 20)


def build(timings, voice_path=None):
    T = timings["timeline"]
    total = T["duration"]
    N = int(np.ceil(total * SR)) + SR // 10
    sfx = np.zeros((N, 2))
    bed = np.zeros((N, 2))   # papel y tecleo: bajan bajo la voz para que se entienda
    # sello
    place(sfx, sfx_seal_whoosh(), T["seal_hit"] - 0.62, db(-14))
    place(sfx, sfx_riser(T["seal_hit"]), 0.0, db(-9), width=0.7)
    place(sfx, sfx_seal_hit(), T["seal_hit"], db(-2))
    # encendido del foco: interruptor con parpadeo
    sw = sfx_switch()
    place(sfx, sw, T["cut_to_urn"] + 0.10, db(-9))
    place(sfx, sw * 0.6, T["cut_to_urn"] + 0.21, db(-11))
    place(sfx, sfx_hum(1.6), T["cut_to_urn"] + 0.21, db(-20))
    # sobres saliendo de la urna y posándose (misma muestra)
    slide = sfx_paper_slide(1.2, 0.8)
    land = sfx_paper_land()
    s2 = T["s2"][0]
    for k in range(5):
        f0 = s2 + 0.15 + k * 0.62
        place(bed, slide, f0 + 0.35, db(-17), pan=0.0, width=0.6)
        place(sfx, land, f0 + 1.70, db(-15))
    # propuestas: barrido + papel + tecleo IDÉNTICOS
    whoosh = sfx_whoosh_light()
    pslide = sfx_paper_slide(0.75)
    cuts = [b[0] for b in T["blocks_p"]] + [T["blocks_p"][4][1]]
    for c in cuts:
        place(sfx, whoosh, c - 0.42, db(-16), width=0.8)
    for k in range(5):
        b0 = T["blocks_p"][k][0]
        place(bed, pslide, b0 + 0.30, db(-16), width=0.4)
        # mismo patrón y misma velocidad de tecleo; dura lo que dura el texto
        nchar = sum(1 for ch in timings["proposals"][k] if ch != " ")
        typing = typing_bed(nchar / 32.0)
        place(bed, typing, b0 + 1.0, db(-17), width=0.3)
    # reloj durante la elección
    tick, tock = sfx_clock(0), sfx_clock(1)
    t = T["s4"][0] + 0.5
    i = 0
    while t < T["s5"][0] - 0.05:
        quiet = T["quiet"][0] - 0.2 <= t
        place(sfx, tick if i % 2 == 0 else tock, t, db(-19 if not quiet else -15), pan=0.15)
        t += 0.5
        i += 1
    # revelación: volteo + golpe idénticos
    flip = sfx_paper_slide(0.5, 1.0)
    hit = sfx_reveal_hit()
    for k in range(5):
        b0 = T["blocks_r"][k][0]
        place(bed, flip, b0 + T["flip_land"] - T["flip_dur"], db(-20), width=0.4)
        place(sfx, hit, b0 + T["flip_land"], db(-6))
    # apagado del foco
    place(sfx, sfx_light_off(), T["s6"][0] + 0.25, db(-12))

    # dron con curva dramática
    dr = drone(N / SR + 0.01)[:N]
    tt = np.arange(N) / SR
    curve = np.interp(tt, [0, T["cut_to_urn"] + 0.2, T["cut_to_urn"] + 0.9, T["s3"][0], T["s4"][0], T["quiet"][0], T["s5"][0], T["s6"][0] + 0.3, T["s6"][0] + 1.2, total - 0.4, total],
                      [0, 0, 0.75, 0.8, 0.85, 0.55, 0.95, 0.9, 0.35, 0.0, 0.0])
    dr = dr * curve
    dr_st = np.stack([dr, np.concatenate([np.zeros(240), dr])[:N] * 0.95 + dr * 0.05], axis=1)

    # voz
    voice = np.zeros((N, 2))
    if voice_path and os.path.exists(voice_path):
        v, vsr = sf.read(voice_path, always_2d=True)
        v = v.mean(axis=1)
        if vsr != SR:
            v = signal.resample_poly(v, SR, vsr)
        v = hp(v, 70)
        for c in timings["voice_clips"]:
            if c["src_start"] is None:
                continue
            a = int((c["src_start"] - c["pad_pre"]) * SR)
            b = int((c["src_end"] + c["pad_post"]) * SR)
            clip = v[max(0, a):b].copy()
            fl = min(int(0.012 * SR), len(clip) // 4)
            if fl > 0:
                clip[:fl] *= np.linspace(0, 1, fl); clip[-fl:] *= np.linspace(1, 0, fl)
            place(voice, stereo(clip), c["dst"] - c["pad_pre"], 1.0)
        # normalizar voz a nivel de diálogo (~-16 LUFS antes de mezcla)
        try:
            import pyloudnorm as pyln
            m = pyln.Meter(SR)
            lv = m.integrated_loudness(voice)
            if np.isfinite(lv):
                voice *= db(-16 - lv)
        except Exception:
            pass

    def master(with_voice):
        d = dr_st.copy()
        if with_voice and np.any(voice):
            # ducking: el dron baja ~8 dB bajo la voz
            envv = np.abs(voice).mean(axis=1)
            envv = lp(envv, 6)
            g = 1 - 0.6 * np.clip(envv / (np.percentile(envv[envv > 1e-4], 70) + 1e-9), 0, 1)
            g = lp(g, 3)
            d *= g[:, None]
        # equilibrio: voz -4 dB, efectos +4 dB respecto a la mezcla anterior
        b = bed.copy()
        if with_voice and np.any(voice):
            # el papel y el tecleo bajan ~10 dB mientras hablas (la voz siempre se entiende)
            ev = lp(np.abs(voice).mean(axis=1), 8)
            gv = 1 - 0.68 * np.clip(ev / (np.percentile(ev[ev > 1e-4], 60) + 1e-9), 0, 1)
            b *= lp(gv, 4)[:, None]
        mix = d * db(-7) + (sfx + b) * db(SFX_DB) + (voice * db(VOICE_DB) if with_voice else 0)
        mix = hp(mix.T, 25).T
        return loudness(mix)

    return master(True), master(False)


def loudness(x, target=-14.0, ceiling=-1.0):
    import pyloudnorm as pyln
    m = pyln.Meter(SR)
    for _ in range(3):
        l = m.integrated_loudness(x)
        x = x * db(target - l)
        # limitador suave de picos
        c = db(ceiling - 0.3)
        x = np.where(np.abs(x) > c * 0.8, np.sign(x) * (c * 0.8 + (c * 0.2) * np.tanh((np.abs(x) - c * 0.8) / (c * 0.2))), x)
    return x


if __name__ == "__main__":
    timings = json.load(open(os.path.join(os.environ.get("OUT_DIR", os.path.join(ROOT, "output")), "timings.json"), encoding="utf-8"))
    vp = timings.get("voice_file")
    if len(sys.argv) > 1:
        vp = sys.argv[1]
    con, sin = build(timings, vp)
    d = os.environ.get("AUDIO_DIR", os.path.join(ROOT, "build", "audio"))
    os.makedirs(d, exist_ok=True)
    sf.write(os.path.join(d, "mezcla_con_voz.wav"), con.astype(np.float32), SR, subtype="PCM_24")
    sf.write(os.path.join(d, "mezcla_sin_voz.wav"), sin.astype(np.float32), SR, subtype="PCM_24")
    import pyloudnorm as pyln
    print("[audio] LUFS con voz %.2f / sin voz %.2f" % (pyln.Meter(SR).integrated_loudness(con), pyln.Meter(SR).integrated_loudness(sin)))
