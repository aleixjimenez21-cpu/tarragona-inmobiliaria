#!/usr/bin/env python3
"""Regenera el reel completo con un solo comando.

    python3 tools/build.py                 # usa input/voz.wav si existe
    python3 tools/build.py --voz otra.wav  # con otra narración
    python3 tools/build.py --solo-audio    # rehace audio y montaje sin volver a renderizar imagen
    python3 tools/build.py --escenas s3    # re-renderiza solo esas escenas (s1..s6) y vuelve a montar

Pasos: tiempos -> audio -> render 3D por escenas (2 procesos) -> concat -> mezcla -> portada.
"""
import argparse, json, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
BUILD = os.path.join(ROOT, "build")


def run(cmd, **kw):
    print("$", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voz", default=os.path.join(ROOT, "input", "voz.wav"))
    ap.add_argument("--solo-audio", action="store_true")
    ap.add_argument("--escenas", nargs="*")
    ap.add_argument("--sin-portada", action="store_true")
    a = ap.parse_args()

    voz = a.voz if os.path.exists(a.voz) else None
    if voz:
        # la voz se copia como referencia; nunca se cambia su velocidad
        run([sys.executable, "tools/timings.py", voz])
    else:
        print("[build] no hay voz: ritmo sintético del guion")
        run([sys.executable, "tools/timings.py", "/nonexistent"])
    run([sys.executable, "tools/audio.py"] + ([voz] if voz else []))

    tl = json.load(open(os.path.join(OUT, "timings.json"), encoding="utf-8"))
    scenes = ["s1", "s2", "s3", "s4", "s5", "s6"]
    os.makedirs(os.path.join(BUILD, "scenes"), exist_ok=True)
    if not a.solo_audio:
        todo = a.escenas or scenes
        # reparto en dos procesos: la escena 3 (propuestas) se parte en dos mitades
        g1 = [x for x in todo if x in ("s1", "s2", "s6")] + (["s3#1/2"] if "s3" in todo else [])
        g2 = [x for x in todo if x in ("s4", "s5")] + (["s3#2/2"] if "s3" in todo else [])
        procs = []
        for g in (g1, g2):
            if g:
                procs.append(subprocess.Popen(["node", "tools/render.js", "scenes", "--only"] + g, cwd=ROOT))
        for p in procs:
            if p.wait() != 0:
                sys.exit("[build] fallo en el render")
    lst = os.path.join(BUILD, "scenes", "lista.txt")
    with open(lst, "w") as f:
        for s in ["s1", "s2", "s3_p1", "s3_p2", "s4", "s5", "s6"]:
            f.write("file '%s.mp4'\n" % s)
    mudo = os.path.join(BUILD, "video_mudo.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", mudo])
    dur = "%.3f" % tl["timeline"]["duration"]
    # loudnorm en dos pasadas: -14 LUFS integrados y techo de pico verdadero -1,5 dBTP
    for wav in ("mezcla_con_voz.wav", "mezcla_sin_voz.wav"):
        src = os.path.join(BUILD, "audio", wav)
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True, cwd=ROOT)
        js = r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1]
        m = json.loads(js)
        af = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
              "aresample=48000" % (m["input_i"], m["input_tp"], m["input_lra"], m["input_thresh"], m["target_offset"]))
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", af, "-ar", "48000", "-c:a", "pcm_s24le", src.replace(".wav", "_master.wav")])
    # vídeo de entrega: H.264 High, ~11 Mbps (Reels recomprime; el archivo queda < 100 MB)
    entrega = os.path.join(BUILD, "video_entrega.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", mudo, "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "11M", "-bufsize", "22M",
         "-profile:v", "high", "-pix_fmt", "yuv420p", "-tune", "grain", "-r", "30", entrega])
    for wav, name in (("mezcla_con_voz_master.wav", "test_29N_final.mp4"), ("mezcla_sin_voz_master.wav", "test_29N_sin_voz.mp4")):
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", entrega, "-i", os.path.join(BUILD, "audio", wav),
             "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
             "-t", dur, "-movflags", "+faststart", os.path.join(OUT, name)])
    if not a.sin_portada and not a.solo_audio:
        run(["node", "tools/render.js", "cover"])
    print("[build] listo ->", OUT)


if __name__ == "__main__":
    main()
