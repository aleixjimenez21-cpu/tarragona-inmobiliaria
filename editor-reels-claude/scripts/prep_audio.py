"""Prepara el audio de todas las tomas y limpia la voz.
- work/audio/raw_<id>.wav    mono 48 kHz (original, para el antes/después)
- work/audio/w16_<id>.wav    mono 16 kHz (para Whisper)
- work/audio/st/<id>.wav     estéreo (los 2 micrófonos del móvil) para WPE
- work/audio/df_final/       DeepFilterNet suave (-40 dB): SOLO para medir tiempos de palabras y cortes
- work/audio/wpe20/          WPE multicanal (quita reflexiones de la sala)
- work/audio/df_wpe20_pf/    WPE + DeepFilterNet + post-filtro: LA VOZ QUE SE USA EN EL MONTAJE
Uso (desde la carpeta del proyecto): python3 <skill>/scripts/prep_audio.py"""
import os, subprocess, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import TAKES, tid, tpath, deep_filter_bin

A = "work/audio"
for d in ["st", "re_in", "wpe20", "df_final", "df_wpe20_pf"]:
    os.makedirs(f"{A}/{d}", exist_ok=True)


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


for k in TAKES:
    t, src = tid(k), tpath(k)
    ff("-i", src, "-vn", "-ac", "1", "-ar", "48000", "-c:a", "pcm_s24le", f"{A}/raw_{t}.wav")
    ff("-i", src, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", f"{A}/w16_{t}.wav")
    ff("-i", src, "-vn", "-ac", "2", "-ar", "48000", "-c:a", "pcm_f32le", f"{A}/st/{t}.wav")
    ff("-i", f"{A}/raw_{t}.wav", "-c:a", "pcm_s16le", f"{A}/re_in/{t}.wav")
    print("audio extraído:", k, t)

here = os.path.dirname(os.path.abspath(__file__))
subprocess.run([sys.executable, os.path.join(here, "dereverb.py"), "20", "3", "3", f"{A}/wpe20"], check=True)
df = deep_filter_bin()
subprocess.run([df, "-D", "-a", "100", "--pf", "-o", f"{A}/df_wpe20_pf", *sorted(glob.glob(f"{A}/wpe20/*.wav"))], check=True, capture_output=True)
subprocess.run([df, "-D", "-a", "40", "-o", f"{A}/df_final", *sorted(glob.glob(f"{A}/re_in/*.wav"))], check=True, capture_output=True)
print("voz limpia en", f"{A}/df_wpe20_pf")
