#!/usr/bin/env python3
"""Genera el Reel completo con un solo comando.

    python3 reel/make.py                 # usa input/voz.wav si existe; si no, tiempos del guion
    python3 reel/make.py --voz otra.wav  # otra locución (se transcribe palabra a palabra)
    python3 reel/make.py --timings output/timings.json   # reutiliza tiempos ya calculados
    python3 reel/make.py --preview       # render rápido (sin supermuestreo) para revisar

Salida en output/: vídeo final, vídeo sin voz, portada, SRT, timings.json.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

from gfx import FPS, H, W  # noqa: E402
from timing import build_timeline, Timeline  # noqa: E402

BUILD = os.path.join(HERE, "build")
OUT = os.path.join(ROOT, "output")

GRADE = ("eq=contrast=0.96:saturation=1.05,"
         "colorbalance=rs=-0.035:gs=-0.008:bs=0.045:rm=0.0:rh=0.03:gh=0.006:bh=-0.035,"
         "vignette=angle=0.52:mode=forward,"
         "noise=c0s=5:c0f=t+u,format=yuv420p")


def log(*a):
    print(time.strftime("[%H:%M:%S]"), *a, flush=True)


# --------------------------------------------------------------------------------------
def _render_scene(args):
    idx, tl_json, ss, clips_dir, f0, f1 = args
    from scenes import Reel
    tl = Timeline.from_json(tl_json)
    reel = Reel(tl, ss=ss, clips_dir=clips_dir)
    path = os.path.join(BUILD, f"escena_{idx + 1}.mp4")
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p", "-r", str(FPS), path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(f0, f1):
        p.stdin.write(reel.frame(f / FPS).tobytes())
    p.stdin.close()
    p.wait()
    return idx, f1 - f0, time.time() - t0


def scene_ranges(tl):
    from scenes import Reel
    s = tl.s
    b = [0.0, s("candelago") - 0.08, s("espera"), s("sabes"), s("espana"), s("elegir"), tl.duration]
    n = int(round(tl.duration * FPS))
    fr = [int(round(x * FPS)) for x in b]
    fr[-1] = n
    return [(i, fr[i], fr[i + 1]) for i in range(6)]


def render_video(tl, ss, clips_dir, jobs):
    os.makedirs(BUILD, exist_ok=True)
    tl_json = tl.to_json()
    tasks = [(i, tl_json, ss, clips_dir, a, b) for i, a, b in scene_ranges(tl)]
    tasks.sort(key=lambda x: -(x[5] - x[4]))
    with mp.get_context("spawn").Pool(jobs) as pool:
        for idx, n, dt in pool.imap_unordered(_render_scene, tasks):
            log(f"escena {idx + 1}: {n} fotogramas en {dt:.0f} s")
    lst = os.path.join(BUILD, "escenas.txt")
    with open(lst, "w") as f:
        for i in range(6):
            f.write(f"file 'escena_{i + 1}.mp4'\n")
    montage = os.path.join(BUILD, "montaje.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", montage], check=True)
    graded = os.path.join(BUILD, "video_etalonado.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", montage, "-vf", GRADE, "-c:v", "libx264", "-preset", "slow",
                    "-crf", "17", "-profile:v", "high", "-level", "4.2", "-r", str(FPS), "-an", graded], check=True)
    return graded


def render_audio(tl, voice_path):
    import soundfile as sf
    import audio
    voice = None
    if voice_path:
        v, sr = sf.read(voice_path, always_2d=True)
        if sr != audio.SR:
            from scipy.signal import resample_poly
            from math import gcd
            g = gcd(sr, audio.SR)
            v = resample_poly(v, audio.SR // g, sr // g, axis=0)  # sólo cambia la frecuencia de muestreo, no la velocidad
        voice = v
    full, no_voice, lf, lnv = audio.mix(tl, tl.duration, voice)
    pf = os.path.join(BUILD, "mezcla_final.wav")
    pn = os.path.join(BUILD, "mezcla_sin_voz.wav")
    sf.write(pf, full, audio.SR, subtype="PCM_24")
    sf.write(pn, no_voice, audio.SR, subtype="PCM_24")
    log(f"audio: final {lf:.1f} LUFS, sin voz {lnv:.1f} LUFS")
    return pf, pn


def mux(video, wav, out):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", video, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out], check=True)


def keyframes(tl, video, n=10):
    s = tl.s
    picks = [("gancho", 0.12), ("galicia", "pueblo", 0.35), ("candelago", "p150", 0.8), ("23 m²", "m23end", 0.3),
             ("pero espera", "espera2", 0.15), ("59.000 / 9 m²", "nueve", 0.8), ("12 casas", "casas", 0.45),
             ("trampa", "ponerla", 0.7), ("3.000 / 400.000", "p400", 0.6), ("CTA", "leo", 0.5)]
    d = os.path.join(BUILD, "fotogramas_clave")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    out = []
    for i, p in enumerate(picks[:n]):
        t = p[1] if len(p) == 2 else s(p[1]) + p[2]
        f = os.path.join(d, f"{i + 1:02d}_{t:05.2f}s.png")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", f], check=True)
        out.append(f)
    # hoja de contacto
    from PIL import Image
    ims = [Image.open(f).resize((360, 640)) for f in out]
    sheet = Image.new("RGB", (360 * 5, 640 * 2))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % 5) * 360, (i // 5) * 640))
    sheet.save(os.path.join(d, "hoja_contacto.png"))
    return out


def cover(tl, ss, clips_dir):
    from scenes import Reel
    r = Reel(tl, ss=ss, clips_dir=clips_dir)
    arr = r.cover()
    from PIL import Image
    Image.fromarray(arr[..., :3]).save(os.path.join(OUT, "portada.jpg"), quality=93)


def prepare_clips(clips_dir):
    """Acepta lo que exporta Google Earth Studio (ZIP o carpeta de fotogramas JPG)
    y lo convierte en <nombre>.mp4 a 30 fps. Un .mp4 ya existente tiene prioridad."""
    import glob
    import zipfile
    if not clips_dir or not os.path.isdir(clips_dir):
        return
    for name in ("madrid", "candelago", "a_barca"):
        mp4 = os.path.join(clips_dir, name + ".mp4")
        if os.path.exists(mp4):
            continue
        src = os.path.join(clips_dir, name)
        z = os.path.join(clips_dir, name + ".zip")
        if os.path.exists(z):
            src = os.path.join(BUILD, "fotogramas_" + name)
            shutil.rmtree(src, ignore_errors=True)
            with zipfile.ZipFile(z) as zf:
                zf.extractall(src)
        if not os.path.isdir(src):
            continue
        frames = sorted(f for ext in ("jpg", "jpeg", "png")
                        for f in glob.glob(os.path.join(src, "**", f"*.{ext}"), recursive=True))
        if not frames:
            continue
        lst = os.path.join(BUILD, f"fotogramas_{name}.txt")
        with open(lst, "w") as f:
            for fr in frames:
                f.write(f"file '{os.path.abspath(fr)}'\nduration {1 / FPS:.6f}\n")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-r", str(FPS),
                        "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", mp4], check=True)
        log(f"clip {name}: {len(frames)} fotogramas de Earth Studio -> {mp4}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voz", default=None, help="locución (por defecto input/voz.wav si existe)")
    ap.add_argument("--timings", default=None, help="timings.json a reutilizar (no transcribe)")
    ap.add_argument("--clips", default=os.path.join(ROOT, "input", "clips"))
    ap.add_argument("--ss", type=float, default=2.0, help="supermuestreo del 3D (2 = máxima calidad)")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--modelo", default=os.environ.get("WHISPER_MODEL", "small"),
                    help="modelo de faster-whisper (nombre o carpeta)")
    ap.add_argument("--sin-edicion", action="store_true", help="usa la voz tal cual, sin cortar tomas ni silencios")
    ap.add_argument("--jobs", type=int, default=max(1, min(6, os.cpu_count() or 2)))
    a = ap.parse_args()
    voice = a.voz
    if not voice:
        for ext in (".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"):
            p = os.path.join(ROOT, "input", "voz" + ext)
            if os.path.exists(p):
                voice = p
                break
    if a.preview:
        a.ss = 1.0
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(BUILD, exist_ok=True)
    log("voz:", voice or "no hay voz -> tiempos del guion")
    if voice and not a.timings and not a.sin_edicion:
        import voice as vz
        from timing import align, tokens
        edited, kept, bounds = vz.process(voice, BUILD, a.modelo, log=log)
        toks = vz.apply_phrase_bounds(align(tokens(), kept), bounds)
        import soundfile as sf
        dur = sf.info(edited).duration
        tl = Timeline(toks, max(dur, toks[-1]["end"]) + 2.2, f"voz editada de {os.path.basename(voice)} (faster-whisper, palabra a palabra)")
        voice = edited
    elif voice and a.timings:
        tl = build_timeline(None, a.timings)
        edited = os.path.join(BUILD, "voz_editada.wav")
        if not a.sin_edicion and os.path.exists(edited):
            voice = edited
    else:
        tl = build_timeline(voice, a.timings)
    log(f"duración: {tl.duration:.2f} s ({tl.source})")
    with open(os.path.join(OUT, "timings.json"), "w", encoding="utf-8") as f:
        json.dump(tl.to_json(), f, ensure_ascii=False, indent=1)
    from subs import build_pages, srt
    with open(os.path.join(OUT, "subtitulos.srt"), "w", encoding="utf-8") as f:
        f.write(srt(build_pages(tl.toks)))
    prepare_clips(a.clips)
    clips = a.clips if os.path.isdir(a.clips) else None
    from stills import find_still
    found = [n + (" (vídeo)" if os.path.exists(os.path.join(clips, n + ".mp4")) else " (captura animada)")
             for n in ("madrid", "candelago", "a_barca")
             if clips and (os.path.exists(os.path.join(clips, n + ".mp4")) or find_still(clips, n))]
    log("Google Earth:", ", ".join(found) or "nada -> maquetas 3D propias")
    video = render_video(tl, a.ss, clips, a.jobs)
    pf, pn = render_audio(tl, voice)
    mux(video, pf, os.path.join(OUT, "madrid_vs_pueblo_final.mp4"))
    mux(video, pn, os.path.join(OUT, "madrid_vs_pueblo_sin_voz.mp4"))
    cover(tl, a.ss, clips)
    kf = keyframes(tl, os.path.join(OUT, "madrid_vs_pueblo_final.mp4"))
    log("fotogramas clave en", os.path.dirname(kf[0]))
    log("listo:", OUT)


if __name__ == "__main__":
    main()
