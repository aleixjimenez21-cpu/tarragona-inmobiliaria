"""
Analiza public/audio.mp3 con librosa -> beats.json
- beats: beats detectados por librosa.beat.beat_track
- grid: rejilla regular ajustada por mínimos cuadrados (tempo + fase) a los beats
        detectados; cubre también los tramos tranquilos donde el tracker se pierde
- half_grid: corcheas de la rejilla
- onsets / strong_onsets: ataques (strong = percentil 75 de fuerza)
"""
import json, sys
import numpy as np
import librosa

path = sys.argv[1] if len(sys.argv) > 1 else "public/audio.mp3"
out = sys.argv[2] if len(sys.argv) > 2 else "beats.json"

y, sr = librosa.load(path, sr=22050, mono=True)
dur = len(y) / sr
hop = 256
env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop, aggregate=np.median)
tempo, beat_frames = librosa.beat.beat_track(onset_envelope=env, sr=sr, hop_length=hop, tightness=400)
tempo = float(np.atleast_1d(tempo)[0])
beats = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop)

# Ajuste lineal t_k = t0 + k*period sobre los beats detectados
period0 = 60.0 / tempo
k = np.round((beats - beats[0]) / period0)
A = np.vstack([np.ones_like(k), k]).T
(t0, period), *_ = np.linalg.lstsq(A, beats, rcond=None)
t0 = t0 - np.floor(t0 / period) * period  # primer beat >= 0
# El pico de onset_strength llega ~20 ms después del ataque real del golpe.
# Corregimos la fase con los onsets "backtracked" (inicio real del ataque).
bt_frames = librosa.onset.onset_detect(onset_envelope=env, sr=sr, hop_length=hop, backtrack=True)
bt = librosa.frames_to_time(bt_frames, sr=sr, hop_length=hop)
dev = bt - (t0 + np.round((bt - t0) / period) * period)
dev = dev[np.abs(dev) < 0.06]
phase_fix = float(np.median(dev)) if len(dev) else 0.0
t0 = t0 + phase_fix
t0 = t0 - np.floor(t0 / period) * period
grid = np.arange(t0, dur + 1e-6, period)
resid = beats - (t0 + np.round((beats - t0) / period) * period)

peak_frames = librosa.onset.onset_detect(onset_envelope=env, sr=sr, hop_length=hop, backtrack=False)
onset_frames = librosa.onset.onset_backtrack(peak_frames, env)  # tiempo = inicio del ataque
onsets = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop)
strengths = env[peak_frames]  # fuerza = altura del pico
thr = np.percentile(strengths, 75) if len(strengths) else 0
strong = onsets[strengths >= thr]

# Energía por frame de vídeo (30 fps): RMS total y graves (<150 Hz), normalizadas 0..1
FPS_V = 30
hop_v = int(round(sr / FPS_V))
rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop_v, center=True)[0]
S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop_v))
freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
bass = S[freqs < 150].mean(axis=0)
norm = lambda v: np.clip(v / (np.percentile(v, 98) + 1e-9), 0, 1)
data_energy = norm(rms)
data_bass = norm(bass)

data = {
    "source": path,
    "duration": round(dur, 4),
    "tempo": round(60.0 / period, 3),
    "tempo_librosa": round(tempo, 3),
    "period": round(float(period), 5),
    "grid_offset": round(float(t0), 5),
    "attack_phase_fix_ms": round(phase_fix * 1000, 1),
    "grid_fit_max_residual_ms": round(float(np.max(np.abs(resid))) * 1000, 1),
    "beats": [round(float(b), 4) for b in beats],
    "grid": [round(float(b), 4) for b in grid],
    "half_grid": [round(float(b), 4) for b in np.arange(t0, dur + 1e-6, period / 2)],
    "onsets": [round(float(o), 4) for o in onsets],
    "strong_onsets": [round(float(o), 4) for o in strong],
    "energy_fps": FPS_V,
    "energy": [round(float(v), 3) for v in data_energy],
    "bass": [round(float(v), 3) for v in data_bass],
}
json.dump(data, open(out, "w"), indent=1)
print(f"tempo={data['tempo']} BPM (librosa {tempo:.2f}) offset={t0:.3f}s "
      f"beats={len(beats)} grid={len(grid)} onsets={len(onsets)} strong={len(strong)} "
      f"max_resid={data['grid_fit_max_residual_ms']}ms -> {out}")
