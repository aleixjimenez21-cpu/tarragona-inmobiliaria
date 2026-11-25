"""Desreverberación con WPE multicanal (nara_wpe) sobre el estéreo original del iPhone (2 micrófonos).
Uso: python3 scripts/dereverb.py <taps> <delay> <iteraciones> <dir_salida>
Salida: <dir_salida>/<toma>.wav (mono 48 kHz, 16 bit, para DeepFilterNet)"""
import sys, os
sys.path.insert(0, "scripts")
from edl import IDS
import numpy as np, soundfile as sf
from nara_wpe.wpe import wpe
from nara_wpe.utils import stft, istft

taps, delay, iters, out = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
os.makedirs(out, exist_ok=True)
SIZE, SHIFT = 1536, 384            # 32 ms / 8 ms a 48 kHz (equivale a 512/128 a 16 kHz)
for t in IDS:
    x, sr = sf.read(f"work/audio/st/{t}.wav", dtype="float64")
    X = stft(x.T, size=SIZE, shift=SHIFT)                 # (canales, frames, bins)
    Y = wpe(X.transpose(2, 0, 1), taps=taps, delay=delay, iterations=iters, statistics_mode="full").transpose(1, 2, 0)
    y = istft(Y, size=SIZE, shift=SHIFT)[:, :x.shape[0]]
    m = y.mean(0)
    m = m / max(1e-9, np.max(np.abs(m))) * 0.5
    sf.write(f"{out}/{t}.wav", m, sr, subtype="PCM_16")
    print(t, "ok")
