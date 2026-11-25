"""Monta la pista de voz según la EDL, la procesa (EQ, de-esser, compresión, limitador),
genera la música de fondo (sintetizada, libre de derechos), hace ducking y normaliza a -14 LUFS / -1 dBTP.
Uso: python3 build_audio.py  (desde anuncio-bf/)"""
import json, subprocess, sys, os
import numpy as np, soundfile as sf
sys.path.insert(0, "scripts")
from edl import TAKES, SEGMENTS, END_HOLD, XF, timeline

W = "work/audio"
SR = 48000


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-2000:]); raise SystemExit(1)
    return r.stderr


# ---------------------------------------------------------------- 1. voz cortada
def cut_voice():
    parts = []
    for k, a, b in SEGMENTS:
        x, sr = sf.read(f"{W}/df_wpe20_pf/{TAKES[k].replace('take_', '')}.wav", dtype="float64")
        assert sr == SR
        seg = x[int(round(a * SR)):int(round(b * SR))].copy()
        n = int(XF * SR)
        ramp = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n))
        seg[:n] *= ramp; seg[-n:] *= ramp[::-1]
        parts.append(seg)
    v = np.concatenate(parts)
    tl, vdur = timeline()
    total = vdur + END_HOLD
    v = np.concatenate([v, np.zeros(int(round((total - vdur) * SR)))])
    sf.write(f"{W}/voice_cut.wav", v, SR, subtype="PCM_24")
    # antes/después de 10 s (mismo tramo, original sin procesar vs. final de voz)
    raw = []
    for k, a, b in SEGMENTS:
        x, _ = sf.read(f"{W}/raw_{TAKES[k].replace('take_', '')}.wav", dtype="float64")
        raw.append(x[int(a * SR):int(b * SR)])
    sf.write(f"{W}/voice_cut_raw.wav", np.concatenate(raw), SR, subtype="PCM_24")
    return total


# ---------------------------------------------------------------- 2. cadena de voz
EQ_CHAIN = ",".join([
    "highpass=f=80:poles=2", "highpass=f=80:poles=2",          # 24 dB/oct a 80 Hz
    "equalizer=f=320:t=q:w=1.1:g=-3",                           # quita "caja" 200-400 Hz
    "equalizer=f=140:t=q:w=0.9:g=1",                            # un poco de cuerpo
    "equalizer=f=3600:t=q:w=0.9:g=3",                           # presencia 3-5 kHz
    "highshelf=f=9500:g=1.5",                                   # aire
])
DYN_CHAIN = ",".join([
    "deesser=i=0.45:m=0.5:f=0.5:s=o",                           # de-esser
    "acompressor=threshold=-18dB:ratio=2.5:attack=8:release=120:knee=4:makeup=1dB",  # compresión suave (~3-5 dB GR)
    "alimiter=limit=0.84:attack=3:release=40:level=disabled",   # limitador (~ -1.5 dBFS)
])


def lufs(path):
    st = sh(f"ffmpeg -hide_banner -i {path} -af ebur128 -f null -")
    return float(st.rsplit("I:", 1)[1].split("LUFS")[0])


def process_voice():
    sh(f"ffmpeg -v error -y -i {W}/voice_cut.wav -af '{EQ_CHAIN}' -c:a pcm_s24le {W}/voice_eq.wav")
    g = -20.0 - lufs(f"{W}/voice_eq.wav")      # etapa de ganancia: voz a -20 LUFS antes de la dinámica
    sh(f"ffmpeg -v error -y -i {W}/voice_eq.wav -af 'volume={g:.2f}dB,{DYN_CHAIN}' -c:a pcm_s24le {W}/voice_proc.wav")


# ---------------------------------------------------------------- 3. música generada
def adsr(n, a, r):
    e = np.ones(n)
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e


def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    from scipy.signal import lfilter
    return lfilter([1 - a], [1, -a], x)


def make_music(total):
    from scipy.signal import lfilter, butter
    rng = np.random.default_rng(7)
    bpm = 100.0
    beat = 60 / bpm
    bar = 4 * beat
    N = int(total * SR)
    t = np.arange(N) / SR
    mus = np.zeros(N); bass = np.zeros(N); perc = np.zeros(N); arp = np.zeros(N)
    midi = lambda m: 440 * 2 ** ((m - 69) / 12)
    # progresión sobria: Am9 - Fmaj7 - Cmaj7 - G6  (un acorde por compás)
    chords = [[57, 60, 64, 67, 71], [53, 57, 60, 64, 69], [48, 55, 59, 64, 67], [55, 59, 62, 64, 71]]
    roots = [45, 41, 48, 43]
    nb = int(np.ceil(total / bar)) + 1
    for b in range(nb):
        c = chords[b % 4]; s0 = int(b * bar * SR); s1 = min(N, int((b + 1) * bar * SR + 0.6 * SR))
        if s0 >= N: break
        n = s1 - s0; tt = np.arange(n) / SR
        pad = np.zeros(n)
        for m in c:
            for det in (-0.07, 0.0, 0.07):              # pad cálido (senos/triangulares desafinados)
                f = midi(m) * 2 ** (det / 12)
                ph = rng.uniform(0, 2 * np.pi)
                pad += np.sin(2 * np.pi * f * tt + ph) + 0.25 * np.sin(2 * np.pi * 2 * f * tt + ph)
        pad *= adsr(n, 0.6, 0.6) / 18
        mus[s0:s1] += pad
        # bajo: negras suaves sobre la raíz
        for q in range(4):
            q0 = s0 + int(q * beat * SR); q1 = min(N, q0 + int(beat * 0.9 * SR))
            if q0 >= N: break
            tq = np.arange(q1 - q0) / SR
            f = midi(roots[b % 4] - 12)
            bass[q0:q1] += np.sin(2 * np.pi * f * tq) * np.exp(-tq * 3.5) * adsr(q1 - q0, 0.008, 0.05) * 0.5
        # arpegio en corcheas (pluck con decaimiento)
        seq = [c[1] + 12, c[2] + 12, c[3] + 12, c[2] + 12, c[4] + 12, c[3] + 12, c[2] + 12, c[0] + 24]
        for e8 in range(8):
            q0 = s0 + int(e8 * beat / 2 * SR); q1 = min(N, q0 + int(0.5 * SR))
            if q0 >= N: break
            tq = np.arange(q1 - q0) / SR
            f = midi(seq[e8])
            arp[q0:q1] += (np.sin(2 * np.pi * f * tq) + 0.3 * np.sin(2 * np.pi * 2 * f * tq)) * np.exp(-tq * 9) * adsr(q1 - q0, 0.004, 0.02) * 0.09
        # percusión: kick suave en 1 y 3, hat en contratiempo
        for q in range(4):
            q0 = s0 + int(q * beat * SR)
            if q0 >= N: break
            if q in (0, 2):
                n2 = min(N - q0, int(0.35 * SR)); tq = np.arange(n2) / SR
                fk = 48 + 70 * np.exp(-tq * 30)
                perc[q0:q0 + n2] += np.sin(2 * np.pi * np.cumsum(fk) / SR) * np.exp(-tq * 9) * 0.55
            h0 = q0 + int(beat / 2 * SR); n3 = min(N - h0, int(0.05 * SR))
            if n3 > 0:
                tq = np.arange(n3) / SR
                perc[h0:h0 + n3] += rng.standard_normal(n3) * np.exp(-tq * 90) * 0.05
    bh, ba = butter(2, 5000 / (SR / 2), 'high'); perc_h = perc.copy()
    arp = onepole_lp(arp, 3500)
    # delay estéreo en el arpegio
    d = int(beat * 0.75 * SR)
    arpL = arp + 0.35 * np.concatenate([np.zeros(d), arp[:-d]])
    arpR = arp + 0.35 * np.concatenate([np.zeros(int(d * 1.5)), arp[:-int(d * 1.5)]])
    mus = onepole_lp(mus, 2200)
    L = mus * 0.9 + bass + perc_h * 0.6 + arpL
    R = mus * 1.1 + bass + perc_h * 0.6 + arpR
    st = np.stack([L, R], 1)
    # intro suave y final con resolución
    fade_in = int(0.25 * SR); st[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
    fo = int(1.2 * SR); st[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
    st /= np.max(np.abs(st)) * 1.12
    sf.write(f"{W}/music.wav", st, SR, subtype="PCM_24")


# ---------------------------------------------------------------- 4. whooshes para transiciones
def make_whoosh(times, total):
    from scipy.signal import butter, sosfilt
    rng = np.random.default_rng(3)
    N = int(total * SR); out = np.zeros(N)
    dur = 0.45
    n = int(dur * SR); tt = np.arange(n) / SR
    for t0 in times:
        noise = rng.standard_normal(n)
        # barrido de filtro paso banda 600 -> 5000 Hz, envolvente asimétrica
        y = np.zeros(n); blk = 480
        for i in range(0, n, blk):
            fc = 600 * (5000 / 600) ** (i / n)
            sos = butter(2, [fc * 0.6 / (SR / 2), min(0.99, fc * 1.6 / (SR / 2))], 'band', output='sos')
            y[i:i + blk] = sosfilt(sos, noise[i:i + blk])
        env = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 2
        y *= env
        s0 = int((t0 - dur * 0.55) * SR)
        if s0 < 0: y = y[-s0:]; s0 = 0
        e = min(N, s0 + len(y)); out[s0:e] += y[:e - s0]
    out /= max(1e-9, np.max(np.abs(out))) / 0.25
    sf.write(f"{W}/whoosh.wav", np.stack([out, out], 1), SR, subtype="PCM_24")


# ---------------------------------------------------------------- 5. mezcla + ducking + loudnorm
def mix(music_below=23.0, sfx_below_peak=7.0):
    """La música queda `music_below` dB por debajo de la voz (medido en LUFS, ya con ducking)."""
    v_l = lufs(f"{W}/voice_proc.wav")
    duck = ("[m][scs]sidechaincompress=threshold=0.03:ratio=3:attack=80:release=500:makeup=1[md]")
    def render_music(gain, out):
        fc = (f"[1:a]volume={gain:.2f}dB[m];[0:a]aformat=channel_layouts=stereo[scs];" + duck)
        sh(f"ffmpeg -v error -y -i {W}/voice_proc.wav -i {W}/music.wav -filter_complex '{fc}' -map '[md]' -c:a pcm_s24le {out}")
    # calibración en dos pasos (el ducking no es lineal)
    gain = (v_l - music_below) - lufs(f"{W}/music.wav")
    for _ in range(2):
        render_music(gain, f"{W}/music_ducked.wav")
        gain += (v_l - music_below) - lufs(f"{W}/music_ducked.wav")
    render_music(gain, f"{W}/music_ducked.wav")
    print(f"voz {v_l:.1f} LUFS | música con ducking {lufs(W + '/music_ducked.wav'):.1f} LUFS (ganancia {gain:.1f} dB)")
    # efectos: su pico queda `sfx_below_peak` dB por debajo del pico de la voz
    vx, _ = sf.read(f"{W}/voice_proc.wav")
    vpk = 20 * np.log10(np.max(np.abs(vx)) + 1e-9)
    whoosh_db = (vpk - sfx_below_peak) - 20 * np.log10(0.5)
    fc = (f"[2:a]volume={whoosh_db:.2f}dB[w];[0:a]aformat=channel_layouts=stereo[vs];"
          "[vs][1:a][w]amix=inputs=3:normalize=0:duration=first[mx]")
    sh(f"ffmpeg -v error -y -i {W}/voice_proc.wav -i {W}/music_ducked.wav -i {W}/sfx.wav -filter_complex '{fc}' -map '[mx]' -c:a pcm_s24le {W}/mix_pre.wav")
    # loudnorm en dos pasadas (lineal) -> -14 LUFS, TP <= -1
    st = sh(f"ffmpeg -hide_banner -y -i {W}/mix_pre.wav -af loudnorm=I=-14:TP=-1.5:LRA=7:print_format=json -f null -")
    js = json.loads(st[st.rfind('{'):st.rfind('}') + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=7:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    sh(f"ffmpeg -v error -y -i {W}/mix_pre.wav -af '{ln},aresample=48000' -c:a pcm_s24le {W}/final_audio.wav")
    return js


if __name__ == "__main__":
    total = cut_voice()
    process_voice()
    make_music(total)
    # efectos de sonido de las transiciones (scripts/sfx.py, eventos en work/sfx.json)
    from sfx import render as render_sfx
    ev = json.load(open("work/sfx.json")) if os.path.exists("work/sfx.json") else []
    sf.write(f"{W}/sfx.wav", render_sfx(ev, total), SR, subtype="PCM_24")
    js = mix()
    print("total", round(total, 2), "s; pre-loudnorm", js["input_i"], "LUFS")
