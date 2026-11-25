# Inference-only wrapper for resemble-enhance (loads audio with soundfile instead of torchaudio)
import sys, torch, soundfile as sf, numpy as np
from resemble_enhance.enhancer.inference import denoise, enhance
mode, inp, out = sys.argv[1], sys.argv[2], sys.argv[3]
nfe = int(sys.argv[4]) if len(sys.argv) > 4 else 64
lam = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
tau = float(sys.argv[6]) if len(sys.argv) > 6 else 0.5
torch.set_num_threads(4)
wav, sr = sf.read(inp, dtype="float32")
if wav.ndim > 1: wav = wav.mean(1)
dwav = torch.from_numpy(wav)
if mode == "denoise":
    y, nsr = denoise(dwav, sr, "cpu")
else:
    y, nsr = enhance(dwav, sr, "cpu", nfe=nfe, solver="midpoint", lambd=lam, tau=tau)
sf.write(out, y.cpu().numpy(), nsr, subtype="PCM_24")
print("ok", out, nsr)
