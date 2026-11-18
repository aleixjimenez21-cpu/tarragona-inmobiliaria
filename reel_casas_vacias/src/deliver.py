"""Entregables: subtitulos.srt, vídeo final y sin voz (H.264 30 fps), portada.jpg,
comentario_fijado.txt y comprobaciones (fotogramas al 60 % de brillo)."""
import os, sys, json, subprocess, argparse, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
OUT = os.path.join(ROOT, 'output')
TM = json.load(open(os.path.join(OUT, 'timings.json')))

COMENTARIO = ("Fuentes: INE (Censo de Población y Viviendas 2021, la última cifra oficial; mide la vivienda vacía "
              "por consumo eléctrico, así que incluye casas en mal estado) y Banco de España (Informe Anual 2025, "
              "déficit acumulado 2021-2025). Yo no te digo el mío: ¿CONSTRUIR o RECUPERAR?")


def srt_time(t):
    t = max(0, t)
    h = int(t // 3600); m = int(t % 3600 // 60); s = int(t % 60); ms = int(round((t - int(t)) * 1000))
    if ms == 1000:
        s += 1; ms = 0
    return '%02d:%02d:%02d,%03d' % (h, m, s, ms)


def write_srt():
    import post
    ch = post.chunks()
    lines = []
    for k, c in enumerate(ch):
        s = c[0]['s'] - 0.05
        nxt = ch[k + 1][0]['s'] - 0.05 if k + 1 < len(ch) else 1e9
        e = min(c[-1]['e'] + 0.6, nxt)
        lines.append('%d\n%s --> %s\n%s\n' % (k + 1, srt_time(s), srt_time(e), ' '.join(w['w'] for w in c)))
    open(os.path.join(OUT, 'subtitulos.srt'), 'w', encoding='utf-8').write('\n'.join(lines))


def encode(frames_dir, audio, out):
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-i', os.path.join(frames_dir, 'f_%04d.png'),
           '-i', audio, '-map', '0:v', '-map', '1:a',
           '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
           '-level', '4.2', '-r', '30', '-g', '30', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000',
           '-movflags', '+faststart', '-shortest', '-color_primaries', 'bt709', '-color_trc', 'bt709',
           '-colorspace', 'bt709', out]
    subprocess.run(cmd, check=True)
    print('->', out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames', default=os.path.join(ROOT, 'post_frames'))
    a = ap.parse_args()
    write_srt()
    open(os.path.join(OUT, 'comentario_fijado.txt'), 'w', encoding='utf-8').write(COMENTARIO + '\n')
    sin = os.path.join(OUT, 'audio_sin_voz.wav')
    con = os.path.join(OUT, 'audio_con_voz.wav')
    encode(a.frames, sin, os.path.join(OUT, 'casas_vacias_sin_voz.mp4'))
    encode(a.frames, con if os.path.exists(con) else sin, os.path.join(OUT, 'casas_vacias_final.mp4'))
    port = os.path.join(ROOT, 'post_frames_portada', 'portada.png')
    if os.path.exists(port):
        from PIL import Image
        Image.open(port).convert('RGB').save(os.path.join(OUT, 'portada.jpg'), quality=94)


if __name__ == '__main__':
    main()
